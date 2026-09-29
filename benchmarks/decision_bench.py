"""Decision bench: A/B comparisons of engine versions at equal time or work.

The hypotheses and decision criteria of each campaign are written, before
any run, in a PLAN.md next to its results (see benchmarks/results_0.8/).

An ARM is an engine: a directory that contains the `gp_elite` package (a git
worktree of the version to measure). Every fit runs in its own process, with
PYTHONPATH pointing at the arm's engine and PYTHONHASHSEED=0.

Problems
  F41  the 41 equations of feynman_bench.py (F15 = the first 15, those of the
       README): same data, split and operator pool as that bench, plus an
       out-of-domain set (each variable's range extended by 30 % above).
  R6   the six frozen PMLB datasets of pmlb_frozen.py, standardised on the
       training part like SRBench: 5 folds, and one out-of-domain split
       (train on the 80 % of rows closest to the centre, test on the rest).

Budgets
  T    time_limit=30 s, generations=1000 (the clock stops the search)
  G    generations=100 (the default of speed="fast"), no time limit

Usage, from the repository root:
  python benchmarks/decision_bench.py run --budget T --arm A=/path/to/engine
         --arm B=/other/engine --out results.jsonl [--workers 2]
  python benchmarks/decision_bench.py summary results.jsonl --budget T
The run command resumes: jobs already in the output file are skipped. With
two arms and the T budget, the two arms of the same job run side by side, so
that both see the same load on the machine.
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time
from contextlib import redirect_stdout

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BUDGETS = {
    "T": dict(time_limit=30.0, generations=1000),
    "G": dict(time_limit=None, generations=100),
}
SEEDS = [0, 1, 2, 3, 4]
REAL = ["210_cloud", "228_elusage", "712_chscase_geyser1", "561_cpu",
        "690_visualizing_galaxy", "547_no2"]


# ─────────────────────────────────────────────────────────────── jobs ──

def jobs_for(budget, seeds=None, feynman_only=False):
    import feynman_bench as F
    n_feyn = len(F.PROBS) if budget == "T" else 15
    seeds = SEEDS if seeds is None else seeds
    out = []
    for i in range(n_feyn):
        for s in seeds:
            out.append(dict(kind="feyn", problem=F.PROBS[i][0], index=i,
                            split="test", seed=s))
    if feynman_only:
        for j in out:
            j["budget"] = budget
        return out
    for name in REAL:
        for k in range(5):
            out.append(dict(kind="real", problem=name, split="fold%d" % k,
                            seed=0))
    if budget == "T":
        for name in REAL:
            for s in seeds:
                out.append(dict(kind="real", problem=name, split="ood",
                                seed=s))
    for j in out:
        j["budget"] = budget
    return out


def job_key(j):
    return (j["arm"], j["budget"], j["kind"], j["problem"], j["split"],
            j["seed"])


# ─────────────────────────────────────────────────────────────── data ──

def _feyn_bounds(i):
    """Per-variable (lo, hi) of equation i, read by recording the calls the
    sampler makes to feynman_bench.U."""
    import feynman_bench as F
    rec = []
    real_u = F.U

    def spy(rng, lo, hi, n):
        rec.append((float(lo), float(hi)))
        return real_u(rng, lo, hi, n)
    F.U = spy
    try:
        F.PROBS[i][3](np.random.RandomState(0), 3)
    finally:
        F.U = real_u
    return rec


def feyn_data(i):
    """Same data and split as feynman_bench.run_range, plus the OOD set."""
    import feynman_bench as F
    p = F.PROBS[i]
    name, formula, nv, sampler, f, pool = p[:6]
    rng = np.random.RandomState(1000 + i)
    X = sampler(rng, 200)
    y = f(X)
    idx = rng.permutation(200)
    tr, te = idx[:140], idx[140:]
    bounds = _feyn_bounds(i)
    r2 = np.random.RandomState(5000 + i)
    Xo = np.column_stack([r2.uniform(lo, hi + 0.3 * (hi - lo), 2000)
                          for lo, hi in bounds])
    beyond = np.any(Xo > np.array([hi for _, hi in bounds]), axis=1)
    with np.errstate(all="ignore"):
        yo = f(Xo)
    keep = beyond & np.isfinite(yo)
    Xo, yo = Xo[keep][:200], yo[keep][:200]
    names = ["v%d" % k for k in range(nv)]
    return X[tr], y[tr], X[te], y[te], Xo, yo, names, pool


def real_data(name, split):
    import pmlb_frozen
    from sklearn.model_selection import KFold
    X, y = pmlb_frozen.load(name)
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    if split.startswith("fold"):
        k = int(split[4:])
        tr, te = list(KFold(5, shuffle=True, random_state=0).split(X))[k]
    else:                                   # "ood": far rows held out
        mu, sd = X.mean(axis=0), X.std(axis=0)
        sd[sd == 0] = 1.0
        d = np.sqrt((((X - mu) / sd) ** 2).sum(axis=1))
        order = np.argsort(d, kind="stable")
        n_te = int(round(0.2 * len(X)))
        tr, te = np.sort(order[:-n_te]), np.sort(order[-n_te:])
    mx, sx = X[tr].mean(axis=0), X[tr].std(axis=0)
    sx[sx == 0] = 1.0
    my, sy = y[tr].mean(), y[tr].std() or 1.0
    return ((X[tr] - mx) / sx, (y[tr] - my) / sy,
            (X[te] - mx) / sx, (y[te] - my) / sy)


def one_minus_r2(y, p):
    v = float(np.var(y)) or 1e-30
    with np.errstate(all="ignore"):
        e = float(np.mean((np.asarray(p, dtype=float) - y) ** 2) / v)
    return e if np.isfinite(e) else 1e30


# ───────────────────────────────────────────────────────────── worker ──

def run_one(job):
    """One fit in this process; returns the record."""
    import gp_elite
    import gp_elite.core as C
    from gp_elite import symbolic_regression

    # Instrumentation, transparent: the last generation index reached.
    gens = [0]
    orig = C.evolve_island

    def counted(*args, **kwargs):
        g = args[3] if len(args) > 3 else kwargs.get("generation", 0)
        gens[0] = max(gens[0], int(g) + 1)
        return orig(*args, **kwargs)
    C.evolve_island = counted

    b = BUDGETS[job["budget"]]
    kw = dict(generations=b["generations"], seed=job["seed"], parallel=False,
              verbose=False)
    if b["time_limit"] is not None:
        kw["time_limit"] = b["time_limit"]
    if job["kind"] == "feyn":
        Xtr, ytr, Xte, yte, Xo, yo, names, pool = feyn_data(job["index"])
        kw.update(feature_names=names, operators=pool)
    else:
        Xtr, ytr, Xte, yte = real_data(job["problem"], job["split"])
        Xo = yo = None
        kw.update(operators="physical")
    import warnings
    t0 = time.time()
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = symbolic_regression(Xtr, ytr, **kw)
    dt = time.time() - t0
    rec = dict(job)
    e = one_minus_r2(yte, r.predict(Xte))
    rec.update(time=round(dt, 2), generations=gens[0], size=int(r.size),
               err=e, r2=1.0 - e, formula_exact=r.formula_exact,
               time_limit_reached=bool(getattr(r, "time_limit_reached", False)),
               expr=r.expression[:160], engine_file=gp_elite.__file__)
    if job["kind"] == "feyn":
        rec["status"] = ("EXACT" if e < 1e-9 else "NEAR" if e < 1e-3
                         else "MISS")
        if Xo is not None and len(yo) >= 20:
            rec["err_ood"] = one_minus_r2(yo, r.predict(Xo))
            rec["n_ood"] = int(len(yo))
    # Growth of the model outside the training box (diagnostic studied in
    # campaign 2 onward; computed after the timing, never fed to the fit).
    try:
        lo, hi = Xtr.min(axis=0), Xtr.max(axis=0)
        w = np.where(hi > lo, hi - lo, 1.0)
        rng = np.random.RandomState(12345)
        Xb = rng.uniform(lo - 0.25 * w, hi + 0.25 * w, (2000, Xtr.shape[1]))
        p_tr = np.asarray(r.predict(Xtr), dtype=float)
        p_b = np.asarray(r.predict(Xb), dtype=float)
        s_tr = float(np.ptp(p_tr)) or 1e-30
        rec["growth_box25"] = float(np.ptp(p_b)) / s_tr
    except Exception:
        pass
    rec["date"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    rec["pythonhashseed"] = os.environ.get("PYTHONHASHSEED")
    return rec


# ───────────────────────────────────────────────────────────── driver ──

def _git_commit(path):
    try:
        r = subprocess.run(["git", "-C", path, "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        c = r.stdout.strip()
        d = subprocess.run(["git", "-C", path, "status", "--porcelain", "--",
                            "gp_elite"], capture_output=True, text=True,
                           timeout=10).stdout.strip()
        return c + ("+modified" if d else "") if c else None
    except Exception:
        return None


def drive(arms, budget, out, workers, seeds=None, feynman_only=False):
    done = set()
    if os.path.exists(out):
        for line in open(out):
            if line.strip():
                done.add(job_key(json.loads(line)))
    commits = {a: _git_commit(p) for a, p in arms.items()}
    todo = []
    for j in jobs_for(budget, seeds, feynman_only):
        group = []
        for a in arms:
            jj = dict(j, arm=a, commit=commits[a])
            if job_key(jj) not in done:
                group.append(jj)
        if group:
            todo.append(group)
    paired = budget == "T" and len(arms) > 1
    queue = [g for g in todo] if paired else [[x] for g in todo for x in g]
    print("%d fits to run (%s)" % (sum(len(g) for g in queue),
                                   "arms side by side" if paired else "free"),
          flush=True)
    running = []

    def launch(j):
        env = dict(os.environ, PYTHONHASHSEED="0",
                   PYTHONPATH=arms[j["arm"]], PYTHONDONTWRITEBYTECODE="1")
        return subprocess.Popen([sys.executable, os.path.abspath(__file__),
                                 "one", json.dumps(j)], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, cwd=HERE)

    def reap(block):
        while running:
            for p, j in list(running):
                if p.poll() is not None:
                    so, se = p.communicate()
                    running.remove((p, j))
                    lines = [l for l in so.splitlines() if l.startswith("{")]
                    if p.returncode == 0 and lines:
                        with open(out, "a") as fh:
                            fh.write(lines[-1] + "\n")
                        r = json.loads(lines[-1])
                        print("%-2s %-3s %-24s %-6s s%d  %6.1fs  gen %4d  %s"
                              % (r["arm"], r["budget"], r["problem"], r["split"],
                                 r["seed"], r["time"], r["generations"],
                                 r.get("status", "R2=%.4f" % r["r2"])),
                              flush=True)
                    else:
                        print("FAILED", j, se[-2000:], flush=True)
                    return
            if not block:
                return
            time.sleep(0.2)

    for group in queue:
        if paired:
            while running:
                reap(True)
            for j in group:
                running.append((launch(j), j))
        else:
            while len(running) >= workers:
                reap(True)
            running.append((launch(group[0]), group[0]))
    while running:
        reap(True)


# ──────────────────────────────────────────────────────────── summary ──

def summary(paths, budget, keep_arms=None):
    import collections
    rows = []
    for p in paths:
        rows += [json.loads(l) for l in open(p) if l.strip()]
    rows = [r for r in rows if r["budget"] == budget]
    if keep_arms:
        rows = [r for r in rows if r["arm"] in keep_arms]
    arms = sorted({r["arm"] for r in rows})
    by = {}
    for r in rows:
        by[(r["arm"], r["kind"], r["problem"], r["split"], r["seed"])] = r
    print("Budget %s, arms %s, %d fits" % (budget, arms, len(rows)))
    if len(arms) != 2:
        return
    A, B = arms

    def pairs(kind, split_pred):
        out = []
        for (a, k, prob, sp, s), ra in by.items():
            if a == A and k == kind and split_pred(sp):
                rb = by.get((B, k, prob, sp, s))
                if rb is not None:
                    out.append((ra, rb))
        return out

    fe = pairs("feyn", lambda sp: True)
    if fe:
        print("\nFeynman: %d paired fits (%d equations)"
              % (len(fe), len({ra["problem"] for ra, _ in fe})))
        for arm, idx in ((A, 0), (B, 1)):
            st = collections.Counter(p[idx]["status"] for p in fe)
            tm = [p[idx]["time"] for p in fe]
            gn = [p[idx]["generations"] for p in fe]
            print("  %s  exact %3d  near %3d  miss %3d   time median %.1f s"
                  "   generations median %d" % (arm, st["EXACT"], st["NEAR"],
                                                st["MISS"], np.median(tm),
                                                np.median(gn)))
        per_eq = collections.defaultdict(lambda: [0, 0])
        for ra, rb in fe:
            per_eq[ra["problem"]][0] += ra["status"] == "EXACT"
            per_eq[ra["problem"]][1] += rb["status"] == "EXACT"
        ahead = [e for e, (a, b) in per_eq.items() if b > a]
        behind = [e for e, (a, b) in per_eq.items() if b < a]
        print("  %s ahead on %d equations, behind on %d" % (B, len(ahead),
                                                             len(behind)))
        print("    ahead :", ", ".join("%s (%d->%d)" % (e, *per_eq[e])
                                        for e in sorted(ahead)))
        print("    behind:", ", ".join("%s (%d->%d)" % (e, *per_eq[e])
                                        for e in sorted(behind)))
        ratio = [rb["time"] / ra["time"] for ra, rb in fe if ra["time"] > 0]
        print("  time ratio %s/%s: median %.2f" % (B, A, np.median(ratio)))
        for arm, idx in ((A, 0), (B, 1)):
            ood = [p[idx]["err_ood"] for p in fe
                   if p[idx]["status"] != "EXACT" and "err_ood" in p[idx]]
            if ood:
                print("  %s out of domain, models not exact: n=%d, median "
                      "1-R2 %.3g, collapses (R2<0) %d"
                      % (arm, len(ood), np.median(ood),
                         sum(1 for o in ood if o > 1.0)))

    for label, pred in (("folds", lambda sp: sp.startswith("fold")),
                        ("out of domain", lambda sp: sp == "ood"),
                        ("folds + out of domain", lambda sp: True)):
        re_ = pairs("real", pred)
        if not re_:
            continue
        d = [rb["r2"] - ra["r2"] for ra, rb in re_]
        print("\nReal data, %s: %d paired fits" % (label, len(re_)))
        for arm, idx in ((A, 0), (B, 1)):
            r2 = [p[idx]["r2"] for p in re_]
            print("  %s  R2 median %.4f  mean %.4f  worst %.4f  collapses %d"
                  "   time median %.1f s   generations median %d"
                  % (arm, np.median(r2), np.mean(r2), np.min(r2),
                     sum(1 for x in r2 if x < 0),
                     np.median([p[idx]["time"] for p in re_]),
                     np.median([p[idx]["generations"] for p in re_])))
        print("  paired difference %s - %s: median %+.4f  mean %+.4f   "
              "%s better on %d, worse on %d"
              % (B, A, np.median(d), np.mean(d), B,
                 sum(1 for x in d if x > 1e-12), sum(1 for x in d if x < -1e-12)))
        ratio = [rb["time"] / ra["time"] for ra, rb in re_ if ra["time"] > 0]
        print("  time ratio %s/%s: median %.2f" % (B, A, np.median(ratio)))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("run")
    r.add_argument("--budget", required=True, choices=sorted(BUDGETS))
    r.add_argument("--arm", action="append", required=True,
                   help="NAME=PATH (directory that contains gp_elite/)")
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, default=2)
    r.add_argument("--seeds", default=None,
                   help="comma-separated engine seeds (default 0,1,2,3,4)")
    r.add_argument("--feynman-only", action="store_true")
    o = sub.add_parser("one")
    o.add_argument("job")
    s = sub.add_parser("summary")
    s.add_argument("paths", nargs="+")
    s.add_argument("--budget", required=True, choices=sorted(BUDGETS))
    s.add_argument("--arms", default=None,
                   help="comma-separated arms to compare (default: all)")
    j = sub.add_parser("jobs")
    j.add_argument("--budget", required=True, choices=sorted(BUDGETS))
    a = ap.parse_args()
    if a.cmd == "one":
        print(json.dumps(run_one(json.loads(a.job))))
    elif a.cmd == "run":
        arms = dict(x.split("=", 1) for x in a.arm)
        drive({k: os.path.abspath(v) for k, v in arms.items()}, a.budget,
              os.path.abspath(a.out), a.workers,
              [int(x) for x in a.seeds.split(",")] if a.seeds else None,
              a.feynman_only)
    elif a.cmd == "summary":
        summary(a.paths, a.budget,
                a.arms.split(",") if a.arms else None)
    elif a.cmd == "jobs":
        for jj in jobs_for(a.budget):
            print(json.dumps(jj))


if __name__ == "__main__":
    main()
