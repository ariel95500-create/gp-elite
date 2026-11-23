# -*- coding: utf-8 -*-
"""Beside M3 of the release of 1.4.0, deciding nothing: why do some records
of M3 on data without noise differ from those of 1.3.0?

The noise-tolerant stage (_make_tolerant_seeds) runs on every fit where the
exact finders of binomials and of functions of a monomial place no seed,
whether the data are noisy or not, and N2b adds its forms there. For each
fit of M3 whose record differs from that of 1.3.0 for a reason other than
time or the text of the warning, and for the other fits of the same scripts,
this script builds the data as the script of M3 does, runs the fit for one
generation with the arguments of M3, and records each call of the
noise-tolerant stage: the number of seeds it places and their forms. The
seeds are placed before the first generation, so one generation shows those
of the full fit. Where the data carry a hash in the record of M3, it is
checked.

  PYTHONHASHSEED=0 /venv13rx/bin/python -I seeds.py run OUT_1.3.0.jsonl
  PYTHONHASHSEED=0 /venv14rx/bin/python -I seeds.py run OUT_1.4.0.jsonl
  python3 seeds.py compare OUT_1.3.0.jsonl OUT_1.4.0.jsonl

The data code below is copied from the scripts of M3 at fbe9b00, line for
line where it builds the data: benchmarks/time_limit_check.py,
feynman_scaling.py, feynman_units.py, robustness_check.py,
small_data_check.py and examples/battery_soh.py.
"""
import contextlib
import hashlib
import io
import json
import os
import sys
import warnings

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
M3 = os.path.join(HERE, "..", "m3")
R = np.random.RandomState


def U(rng, lo, hi, n):
    return rng.uniform(lo, hi, n)


VEL = {"m": 1, "s": -1}
SCALING = [   # feynman_scaling.PROBS: (index, name, nv, sampler, f, pool)
    (0, "I.12.1", 2, lambda r, n: np.c_[U(r, 1, 5, n), U(r, 1, 5, n)],
     lambda X: X[:, 0] * X[:, 1], "physical"),
    (6, "I.8.14", 4, lambda r, n: np.c_[U(r, 1, 5, n), U(r, 1, 5, n), U(r, 1, 5, n), U(r, 1, 5, n)],
     lambda X: np.sqrt((X[:, 1] - X[:, 0]) ** 2 + (X[:, 3] - X[:, 2]) ** 2), "physical"),
    (14, "III.15.12", 3, lambda r, n: np.c_[U(r, 1, 5, n), U(r, 0.5, 2, n), U(r, 0.5, 2, n)],
     lambda X: 2 * X[:, 0] * (1 - np.cos(X[:, 1] * X[:, 2])), "trig"),
    (11, "I.12.2", 4, lambda r, n: np.c_[U(r, 1, 5, n), U(r, 1, 5, n), U(r, 1, 3, n), U(r, 1, 3, n)],
     lambda X: X[:, 0] * X[:, 1] / (4 * np.pi * X[:, 2] * X[:, 3] ** 2), "physical"),
    (7, "I.16.6", 3, lambda r, n: np.c_[U(r, 1, 2, n), U(r, 1, 2, n), U(r, 3, 10, n)],
     lambda X: (X[:, 0] + X[:, 1]) / (1 + X[:, 0] * X[:, 1] / X[:, 2] ** 2), "physical"),
]
SIZES = [25, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
SMALL_LAWS = [   # small_data_check.LAWS
    ("3 sin(2x) + 1", "trig", [(0.1, 3.0)], lambda X: 3 * np.sin(2 * X[:, 0]) + 1),
    ("x^1.5", "physical", [(0.4, 30.0)], lambda X: X[:, 0] ** 1.5),
    ("2.5 exp(-0.7x) + 0.3", "physical", [(0.0, 5.0)],
     lambda X: 2.5 * np.exp(-0.7 * X[:, 0]) + 0.3),
    ("x0 x1^2", "physical", [(1.0, 5.0), (1.0, 5.0)], lambda X: X[:, 0] * X[:, 1] ** 2),
    ("x0 / (x0 + x1)", "physical", [(1.0, 5.0), (1.0, 5.0)],
     lambda X: X[:, 0] / (X[:, 0] + X[:, 1])),
]


def jobs():
    """(label, X, y, kwargs of the fit without its budget, hash check)."""
    out = []
    # time_limit_check.py: the fits in sequence, then fits a/b and c
    rng = R(0)
    X = rng.uniform(1, 4, (3000, 5))
    y = X[:, 0] * X[:, 1] / X[:, 2] + 0.3 * X[:, 3]
    out.append(("time_limit sequence (3000 rows, seed 0)", X, y,
                dict(parallel=False, seed=0), None))
    out.append(("time_limit fits a and b (300 rows, seed 5)", X[:300], y[:300],
                dict(parallel=False, seed=5), None))
    out.append(("time_limit fit c (300 rows, seed 1)", X[:300], y[:300],
                dict(parallel=False, seed=1), None))
    # feynman_scaling.py, arm 'none'
    for idx, name, nv, sampler, f, pool in SCALING:
        for N in SIZES:
            for rep in range(3 if N <= 200 else 1):
                rng = R(1000 + idx + 10000 * rep)
                X = sampler(rng, N)
                y = f(X)
                ntr = int(round(0.7 * N))
                perm = rng.permutation(N)
                tr = perm[:ntr]
                hx = hashlib.sha1(X.tobytes()).hexdigest()[:12]
                hy = hashlib.sha1(y.tobytes()).hexdigest()[:12]
                out.append(("scaling %s N=%d rep=%d" % (name, N, rep), X[tr], y[tr],
                            dict(feature_names=["v%d" % k for k in range(nv)],
                                 operators=pool, normalize="none", speed="fast",
                                 validation_split=0.15, seed=0, restarts=4,
                                 parallel=False),
                            ("scaling", name, N, rep, hx, hy)))
    # feynman_units.py, I.16.6 (index 7 of its PROBS)
    rng = R(1000 + 7)
    X = np.c_[U(rng, 1, 2, 200), U(rng, 1, 2, 200), U(rng, 3, 10, 200)]
    y = (X[:, 0] + X[:, 1]) / (1 + X[:, 0] * X[:, 1] / X[:, 2] ** 2)
    idx = rng.permutation(200)
    tr = idx[:140]
    dh = hashlib.sha1(X.tobytes() + y.tobytes()).hexdigest()[:12]
    out.append(("units I.16.6", X[tr], y[tr],
                dict(feature_names=["v0", "v1", "v2"], operators="physical",
                     normalize="none", speed="fast", validation_split=0.15, seed=0,
                     restarts=4, units=[VEL, VEL, VEL], target_units=VEL,
                     parallel=False),
                ("units", "I.16.6", dh)))
    # robustness_check.py, wide_dynamic_range
    rng = R(0)
    n = 120
    x = U(rng, 1, 5, n)
    z = np.exp(U(rng, np.log(1e-3), np.log(1e6), n))
    out.append(("robustness wide_dynamic_range", np.c_[z, x], np.log(z) * x,
                dict(seed=0, parallel=False), None))
    # small_data_check.py, arm F: the five laws on their 25 training points
    for i, (name, ops, bounds, f) in enumerate(SMALL_LAWS):
        rng = R(100 + i)
        X = np.column_stack([rng.uniform(lo, hi, 25) for lo, hi in bounds])
        for s in (0, 1, 2, 3):
            out.append(("small data %s seed %d" % (name, s), X, f(X),
                        dict(operators=ops, seed=s, parallel=False), None))
    # examples/battery_soh.py, the forward split
    import pandas as pd
    df = pd.read_csv(os.path.join(REPO, "examples", "nasa_battery_simulation.csv"))
    feat = ["cycle", "temperature", "courant"]
    X = df[feat].values
    y = df["capacity_SOH"].values
    cut = int(len(y) * 0.85)
    out.append(("battery forward split", X[:cut], y[:cut],
                dict(feature_names=feat, operators="physical", normalize="auto",
                     speed="fast", validation_split=0.0, seed=0, parallel=False),
                None))
    return out


def check_hash(chk):
    """True, False, or None when the record of M3 carries no hash."""
    if chk is None:
        return None
    if chk[0] == "scaling":
        _, name, N, rep, hx, hy = chk
        for ln in open(os.path.join(M3, "scaling.jsonl")):
            r = json.loads(ln)
            if (r["name"], r["n_total"], r["rep"]) == (name, N, rep):
                return r["X_hash"] == hx and r["y_hash"] == hy
        return False
    _, name, dh = chk
    for ln in open(os.path.join(M3, "feynman15_units.jsonl")):
        r = json.loads(ln)
        if r["name"] == name:
            return r["data_hash"] == dh
    return False


def run(path):
    import random
    import gp_elite
    import gp_elite.core as C
    from gp_elite import symbolic_regression
    calls = []
    orig = C._make_tolerant_seeds

    def wrapped(*a, **kw):
        seeds = orig(*a, **kw)
        calls.append([C.to_string(t) for t in seeds])
        return seeds
    C._make_tolerant_seeds = wrapped
    with open(path, "w", encoding="utf-8") as fh:
        for label, X, y, kw, chk in jobs():
            calls.clear()
            if label.startswith("battery"):          # as fit_gp of battery_soh.py
                random.seed(0)
                np.random.seed(0)
            with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
                warnings.simplefilter("ignore")
                symbolic_regression(X, y, generations=1, verbose=False, **kw)
            rec = dict(job=label, engine=gp_elite.__version__, engine_file=gp_elite.__file__,
                       pythonhashseed=os.environ.get("PYTHONHASHSEED"),
                       data_as_m3=check_hash(chk), tolerant_calls=len(calls),
                       seeds_per_call=[len(c) for c in calls],
                       first_call_seeds=calls[0] if calls else [])
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            print("%-48s calls %d  seeds %s" % (label, len(calls), rec["seeds_per_call"]),
                  flush=True)


def compare(p13, p14):
    a = [json.loads(ln) for ln in open(p13)]
    b = [json.loads(ln) for ln in open(p14)]
    assert [r["job"] for r in a] == [r["job"] for r in b], "not the same jobs"
    lines = ["engines: %s / %s" % (a[0]["engine"], b[0]["engine"])]
    bad = [r["job"] for r in a + b if r["data_as_m3"] is False]
    lines.append("data checked against the hashes of M3: %d jobs, %s" % (
        sum(r["data_as_m3"] is not None for r in b),
        "all equal" if not bad else "DIFFER: %s" % bad))
    lines.append("")
    lines.append("%-48s %-28s %-28s %s" % ("fit", "1.3.0 seeds per call",
                                           "1.4.0 seeds per call", "same seeds"))
    for x, z in zip(a, b):
        same = (x["seeds_per_call"] == z["seeds_per_call"]
                and x["first_call_seeds"] == z["first_call_seeds"])
        lines.append("%-48s %-28s %-28s %s" % (
            x["job"], x["seeds_per_call"] or "not run",
            z["seeds_per_call"] or "not run", "yes" if same else "NO"))
    lines.append("")
    lines.append("The seeds of the first call where they differ:")
    for x, z in zip(a, b):
        if x["first_call_seeds"] != z["first_call_seeds"]:
            lines.append("  %s" % x["job"])
            lines.append("    1.3.0: %s" % " | ".join(x["first_call_seeds"]))
            lines.append("    1.4.0: %s" % " | ".join(z["first_call_seeds"]))
    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    return text


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(sys.argv[2])
    else:
        out = compare(sys.argv[2], sys.argv[3])
        with open(os.path.join(HERE, "seeds_compare.txt"), "w", encoding="utf-8") as fh:
            fh.write(out)
