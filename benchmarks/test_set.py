"""The frozen test set of phase 1 (see benchmarks/results_0.9/PLAN.md).

It is never used to decide: no targeted trial and no campaign may read it.
It is measured once per version and published as is.

  TF78    the Feynman datasets of PMLB absent from benchmarks/feynman_bench.py
  TS14    the 14 Strogatz systems of PMLB
  TR25    25 real PMLB regression datasets chosen by a written rule

`build` downloads every file once into benchmarks/_pmlb_cache/, checks it and
writes benchmarks/test_set/MANIFEST.json: the SHA-256 of each file's
decompressed content, its shape, and what the rules of the plan need (the
formula of the PMLB metadata, the operator pool, whether a Strogatz target is
exact). The loader then refuses any file whose content differs from the
manifest, so that a change on PMLB's side stops the measurement instead of
silently measuring something else.

Usage, from the repository root:
  python benchmarks/test_set.py build     (once; refuses to overwrite)
  python benchmarks/test_set.py check     (downloads if needed, checks all)
"""
import gzip
import hashlib
import io
import json
import os
import re
import sys
import urllib.request

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "_pmlb_cache")
MANIFEST = os.path.join(HERE, "test_set", "MANIFEST.json")
DATA_URL = ("https://media.githubusercontent.com/media/EpistasisLab/pmlb/"
            "master/datasets/{n}/{n}.tsv.gz")
META_URL = ("https://raw.githubusercontent.com/EpistasisLab/pmlb/master/"
            "datasets/{n}/metadata.yaml")
SUMMARY_URL = ("https://raw.githubusercontent.com/EpistasisLab/pmlb/master/"
               "pmlb/all_summary_stats.tsv")

# TR25: the list the rule of the plan gives (written in PLAN.md before any
# data file was opened).
TR25 = ["1027_ESL", "1028_SWD", "1029_LEV", "1030_ERA",
        "1096_FacultySalaries", "192_vineyard", "229_pwLinear",
        "230_machine_cpu", "519_vinnie", "522_pm10",
        "523_analcatdata_neavote", "529_pollen", "556_analcatdata_apnea2",
        "557_analcatdata_apnea1", "663_rabe_266", "665_sleuth_case2002",
        "666_rmftsa_ladata", "678_visualizing_environmental",
        "687_sleuth_ex1605", "706_sleuth_case1202",
        "first_principles_planck", "first_principles_rydberg",
        "first_principles_supernovae_zg", "first_principles_supernovae_zr",
        "solar_flare"]

_TRIG = re.compile(r"\b(a?sin|a?cos|a?tan|arcsin|arccos|arctan)\s*\(")


# ─────────────────────────────────────────────────────────── files ──

def _fetch(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def _raw(name):
    """Decompressed content of a PMLB file, downloaded once into the cache."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name + ".tsv.gz")
    if not os.path.exists(path):
        data = _fetch(DATA_URL.format(n=name))
        with open(path + ".part", "wb") as fh:
            fh.write(data)
        os.replace(path + ".part", path)
    with gzip.open(path, "rb") as fh:
        return fh.read()


_MAN = None


def manifest():
    global _MAN
    if _MAN is None:
        with open(MANIFEST) as fh:
            _MAN = json.load(fh)
    return _MAN


def load_frame(name):
    """The dataset as a DataFrame, after checking it against the manifest."""
    entry = manifest()["datasets"][name]
    raw = _raw(name)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != entry["sha256"]:
        raise RuntimeError(
            "%s: content differs from the frozen test set (sha256 %s, "
            "expected %s). Delete %s to re-download; if PMLB changed the "
            "file, the test set no longer exists as frozen."
            % (name, digest, entry["sha256"],
               os.path.join(CACHE, name + ".tsv.gz")))
    import pandas as pd
    return pd.read_csv(io.BytesIO(raw), sep="\t")


def _xy(name):
    d = load_frame(name)
    y = d["target"].to_numpy(dtype=float)
    X = d.drop(columns=["target"]).to_numpy(dtype=float)
    return X, y


def names(group):
    return [n for n, e in sorted(manifest()["datasets"].items())
            if e["group"] == group]


# ──────────────────────────────────────────────────────────── splits ──

def _centre_split(X, frac_out=0.2):
    """Train on the rows closest to the centre, test on the farthest."""
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd[sd == 0] = 1.0
    d = np.sqrt((((X - mu) / sd) ** 2).sum(axis=1))
    order = np.argsort(d, kind="stable")
    n_te = int(round(frac_out * len(X)))
    return np.sort(order[:-n_te]), np.sort(order[-n_te:])


def tf_data(name):
    """TF78: 140 training and 60 test rows inside the training box, and up
    to 200 out-of-domain rows above it (PLAN.md)."""
    k = names("TF78").index(name)
    X, y = _xy(name)
    lo, hi = X.min(axis=0), X.max(axis=0)
    box_hi = lo + (hi - lo) / 1.3
    inside = np.flatnonzero(np.all(X <= box_hi, axis=1) & np.isfinite(y))
    take = np.random.RandomState(2000 + k).choice(inside, 200, replace=False)
    tr, te = take[:140], take[140:]
    above = np.flatnonzero(np.any(X > box_hi, axis=1) & np.isfinite(y))
    n_o = min(200, len(above))
    oo = np.random.RandomState(6000 + k).choice(above, n_o, replace=False)
    nv = X.shape[1]
    return (X[tr], y[tr], X[te], y[te], X[oo], y[oo],
            ["v%d" % j for j in range(nv)],
            manifest()["datasets"][name]["pool"])


def ts_data(name, split):
    """TS14: split "test" (280 / 120 random rows) or "ood" (80 % closest to
    the centre / 20 % farthest)."""
    k = names("TS14").index(name)
    X, y = _xy(name)
    if split == "test":
        p = np.random.RandomState(3000 + k).permutation(len(X))
        n_tr = int(round(0.7 * len(X)))
        tr, te = p[:n_tr], p[n_tr:]
    elif split == "ood":
        tr, te = _centre_split(X)
    else:
        raise ValueError(split)
    return (X[tr], y[tr], X[te], y[te],
            ["v%d" % j for j in range(X.shape[1])],
            manifest()["datasets"][name]["pool"])


def tr_data(name, split, raw=False):
    """TR25: five folds or the out-of-domain split, standardised on the
    training part (as SRBench) or in the data's own units (raw)."""
    from sklearn.model_selection import KFold
    X, y = _xy(name)
    if split.startswith("fold"):
        k = int(split[4:])
        tr, te = list(KFold(5, shuffle=True, random_state=0).split(X))[k]
    elif split == "ood":
        tr, te = _centre_split(X)
    else:
        raise ValueError(split)
    if raw:
        return X[tr], y[tr], X[te], y[te]
    mx, sx = X[tr].mean(axis=0), X[tr].std(axis=0)
    sx[sx == 0] = 1.0
    my, sy = y[tr].mean(), y[tr].std() or 1.0
    return ((X[tr] - mx) / sx, (y[tr] - my) / sy,
            (X[te] - mx) / sx, (y[te] - my) / sy)


# ───────────────────────────────────────────────────────────── build ──

def _formula(meta_text):
    """The formula line of a PMLB metadata description (first line with an
    '=' inside the description block)."""
    desc = meta_text.split("description:", 1)[-1].split("\nsource:", 1)[0]
    for line in desc.splitlines():
        s = line.strip()
        if "=" in s and not s.lower().startswith(("note", "#")):
            return s
    return ""


def _strogatz_exact(name, meta_text, X, y, cols):
    """Does the metadata formula reproduce the target to 1e-9 of its scale?"""
    import sympy
    f = _formula(meta_text)
    if "=" not in f:
        return False, f, None
    rhs = f.split("=", 1)[1]
    syms = {c: sympy.Symbol(c) for c in cols}
    try:
        expr = sympy.sympify(rhs, locals=syms)
        fn = sympy.lambdify([syms[c] for c in cols], expr, "numpy")
        p = np.asarray(fn(*[X[:, j] for j in range(X.shape[1])]), dtype=float)
    except Exception:
        return False, f, None
    gap = float(np.max(np.abs(p - y))) / max(float(np.max(np.abs(y))), 1e-300)
    return bool(gap <= 1e-9), f, gap


def build():
    if os.path.exists(MANIFEST):
        sys.exit("%s exists: the test set is frozen. Use `check`." % MANIFEST)
    sys.path.insert(0, HERE)
    import feynman_bench as F
    from concurrent.futures import ThreadPoolExecutor
    import pandas as pd

    summary = _fetch(SUMMARY_URL)
    rows = pd.read_csv(io.BytesIO(summary), sep="\t")
    bench = {"feynman_" + p[0].replace(".", "_") for p in F.PROBS}
    bench.discard("feynman_I_6_20a")
    bench.add("feynman_I_6_2a")             # the bench's I.6.20a
    feyn = sorted(n for n in rows["dataset"] if n.startswith("feynman_"))
    missing = sorted(bench - set(feyn))
    if missing:
        sys.exit("bench equations not found in PMLB: %s" % missing)
    tf = [n for n in feyn if n not in bench]
    ts = sorted(n for n in rows["dataset"] if n.startswith("strogatz_"))
    groups = [("TF78", tf), ("TS14", ts), ("TR25", TR25)]
    for g, lst in groups:
        print("%s: %d datasets" % (g, len(lst)))

    def one(item):
        g, n = item
        raw = _raw(n)
        d = pd.read_csv(io.BytesIO(raw), sep="\t")
        cols = [c for c in d.columns if c != "target"]
        X = d[cols].to_numpy(dtype=float)
        y = d["target"].to_numpy(dtype=float)
        e = dict(group=g, sha256=hashlib.sha256(raw).hexdigest(),
                 rows=int(len(d)), features=len(cols), columns=cols)
        if g in ("TF78", "TS14"):
            meta = _fetch(META_URL.format(n=n)).decode("utf-8", "replace")
            f = _formula(meta)
            e["formula"] = f
            e["pool"] = "trig" if _TRIG.search(f.split("=", 1)[-1]) else "physical"
            if g == "TF78":
                e["family"] = "bonus" if n.startswith("feynman_test_") else "main"
            else:
                ok, f2, gap = _strogatz_exact(n, meta, X, y, cols)
                e["exact_scorable"] = ok
                e["formula_gap"] = gap
        return n, e

    items = [(g, n) for g, lst in groups for n in lst]
    with ThreadPoolExecutor(8) as ex:
        entries = dict(ex.map(one, items))
    man = dict(
        built="by benchmarks/test_set.py build",
        summary_sha256=hashlib.sha256(summary).hexdigest(),
        rules="benchmarks/results_0.9/PLAN.md",
        datasets={n: entries[n] for n in sorted(entries)})
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w") as fh:
        json.dump(man, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote %s (%d datasets)" % (MANIFEST, len(entries)))


def check():
    bad = 0
    for n in sorted(manifest()["datasets"]):
        try:
            load_frame(n)
        except RuntimeError as exc:
            bad += 1
            print(exc)
    print("%d datasets checked, %d differ" % (len(manifest()["datasets"]), bad))
    return bad == 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "build":
        build()
    elif cmd == "check":
        sys.exit(0 if check() else 1)
    else:
        sys.exit(__doc__)
