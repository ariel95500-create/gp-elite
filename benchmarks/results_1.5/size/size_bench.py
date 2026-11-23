"""What size costs: the bench of Part B of benchmarks/results_1.5/PLAN.md.

The 41 equations of F41 (benchmarks/feynman_bench.py), without noise, at
sizes beyond the range where GP_ELITE is measured, at the budgets T (30 s)
and 10T (300 s):

  rows       100, 1,000, 10,000 and 100,000 training rows at T, and
             100,000 at 10T, no variable added
  variables  1,000 training rows with k = 0, 5, 10 and 20 added variables
             at T (k = 0 is the cell of 1,000 rows), and k = 20 at 10T

Each equation and size has one draw of the data, seeded by the equation and
the size, the same for every budget and every seed of the fit: n training
rows and 1,000 test rows drawn the same way. An added column j is drawn
uniformly over the range of the equation's variable j modulo its number of
variables, and the columns are put in an order drawn for the equation and
k; they are named v0, v1, ...

Each fit runs as benchmarks/phase1_bench.py runs one (run_one): its own
process, PYTHONHASHSEED=0, one BLAS thread, parallel=False, one restart, the
pool of operators of its equation, seeds 0 to 4, time_limit = 30 k and
generations = 1000 k for the budget factor k; the generations counted by
wrapping evolve_island; EXACT if 1 - R2 on the test rows is below 1e-9, NEAR
below 1e-3, MISS otherwise. It also records the time from the start of the
fit to its first generation, the seeds placed (elementary_seed and
tolerant_seed, as phase1_bench.py), the times the seed finders report, and
whether the returned formula uses an added variable.

Usage, from the root of a copy of the repository without the package:
  python benchmarks/results_1.5/size/size_bench.py run --python /venv14p/bin/python \\
         --out records.jsonl --workers 4 [--max-seconds 6300]
  python benchmarks/results_1.5/size/size_bench.py data 0 r1000 k20 ...
  python benchmarks/results_1.5/size/size_bench.py guard records.jsonl
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import time
from contextlib import redirect_stdout

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, BENCH)

TIME_LIMIT, GENERATIONS = 30.0, 1000
SEEDS = [0, 1, 2, 3, 4]
N_TEST = 1000

# name: (training rows, added variables, budget factor)
CELLS = {
    "r100": (100, 0, 1),
    "r1000": (1000, 0, 1),          # also k = 0 of the axis of variables
    "r10000": (10000, 0, 1),
    "r100000": (100000, 0, 1),
    "r100000_10T": (100000, 0, 10),
    "k5": (1000, 5, 1),
    "k10": (1000, 10, 1),
    "k20": (1000, 20, 1),
    "k20_10T": (1000, 20, 10),
}
# one draw of data per (training rows, added variables)
DATA_CODE = {(100, 0): 0, (1000, 0): 1, (10000, 0): 2, (100000, 0): 3,
             (1000, 5): 4, (1000, 10): 5, (1000, 20): 6}


def all_jobs():
    """A seed, then the equations, then the cells of a job one after the
    other, so that the cells share the load and the first fits of each cell
    are of different equations."""
    import feynman_bench as F
    return [dict(eq=i, problem=F.PROBS[i][0], seed=s, cell=c)
            for s in SEEDS for i in range(len(F.PROBS)) for c in CELLS]


def key(j):
    return (j["eq"], j["seed"], j["cell"])


# ───────────────────────────────────────────────────────────── data ──

def data(i, cell):
    """(Xtr, ytr, Xte, yte, names, pool, added): added holds the positions
    of the added columns."""
    import feynman_bench as F
    import decision_bench as D
    n, k, _f = CELLS[cell]
    code = DATA_CODE[(n, k)]
    _name, _formula, nv, sampler, f, pool = F.PROBS[i][:6]
    Xtr = sampler(np.random.RandomState(150000 + 10 * i + code), n)
    Xte = sampler(np.random.RandomState(160000 + 10 * i + code), N_TEST)
    with np.errstate(all="ignore"):
        ytr, yte = f(Xtr), f(Xte)
    added = []
    if k:
        bounds = D._feyn_bounds(i)
        ra = np.random.RandomState(170000 + 10 * i + code)
        add_tr = np.column_stack([ra.uniform(*bounds[j % nv], n)
                                  for j in range(k)])
        add_te = np.column_stack([ra.uniform(*bounds[j % nv], N_TEST)
                                  for j in range(k)])
        order = np.random.RandomState(180000 + 10 * i + code).permutation(nv + k)
        Xtr = np.column_stack([Xtr, add_tr])[:, order]
        Xte = np.column_stack([Xte, add_te])[:, order]
        added = [pos for pos, src in enumerate(order) if src >= nv]
    names = ["v%d" % c for c in range(nv + k)]
    return Xtr, ytr, Xte, yte, names, pool, added


# ─────────────────────────────────────────────────────────── worker ──

def run_one(job):
    import warnings
    import gp_elite
    import gp_elite.core as C
    import decision_bench as D
    from gp_elite import symbolic_regression

    _n, _k, factor = CELLS[job["cell"]]
    Xtr, ytr, Xte, yte, names, pool, added = data(job["eq"], job["cell"])

    gens, first = [0], [None]
    orig = C.evolve_island

    def counted(*args, **kwargs):
        if first[0] is None:
            first[0] = time.time()
        g = args[3] if len(args) > 3 else kwargs.get("generation", 0)
        gens[0] = max(gens[0], int(g) + 1)
        return orig(*args, **kwargs)
    C.evolve_island = counted

    kw = dict(generations=GENERATIONS * factor, time_limit=TIME_LIMIT * factor,
              seed=job["seed"], parallel=False, verbose=False, operators=pool,
              feature_names=names)
    t0 = time.time()
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = symbolic_regression(Xtr, ytr, **kw)
    dt = time.time() - t0
    C.evolve_island = orig

    e = D.one_minus_r2(yte, r.predict(Xte))
    uses_added = any(re.search(r"\b%s\b" % names[c], r.expression)
                     for c in added)
    trace = {k: v for k, v in C.TRACE.value.items()
             if isinstance(v, (int, float, str, bool)) or v is None}
    rec = dict(job)
    rec.update(n_train=int(len(ytr)), n_features=len(names),
               budget_factor=factor, time_limit=TIME_LIMIT * factor,
               time=round(dt, 2), generations=gens[0],
               to_first_gen=None if first[0] is None else round(first[0] - t0, 3),
               size=int(r.size), err=e, r2=1.0 - e,
               status="EXACT" if e < 1e-9 else "NEAR" if e < 1e-3 else "MISS",
               formula_exact=r.formula_exact,
               time_limit_reached=bool(getattr(r, "time_limit_reached", False)),
               uses_added=bool(uses_added), expr=r.expression[:160],
               elementary_seed=C.TRACE.value.get("elementary_seed"),
               tolerant_seed=C.TRACE.value.get("tolerant_seed"),
               trace=trace, engine_file=gp_elite.__file__,
               engine_version=getattr(gp_elite, "__version__", "?"),
               date=time.strftime("%Y-%m-%dT%H:%M:%S"),
               pythonhashseed=os.environ.get("PYTHONHASHSEED"),
               python=sys.version.split()[0], numpy=np.__version__)
    return rec


# ─────────────────────────────────────────────────────────── driver ──

def drive(python, out, workers, max_seconds=None):
    """Runs the jobs not yet in `out`, in the order of all_jobs. With
    max_seconds, stops launching fits after that time and returns once the
    running ones are recorded (the next call resumes)."""
    done = set()
    if os.path.exists(out):
        with open(out) as fh:
            for line in fh:
                if line.strip():
                    done.add(key(json.loads(line)))
    todo = [j for j in all_jobs() if key(j) not in done]
    print("%d jobs to run, %d already done" % (len(todo), len(done)), flush=True)
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)
    running, t_start, n_done = [], time.time(), 0
    while todo or running:
        if max_seconds is not None and time.time() - t_start > max_seconds and todo:
            print("time slice over: %d jobs left for the next call" % len(todo),
                  flush=True)
            todo = []
        while todo and len(running) < workers:
            j = todo.pop(0)
            p = subprocess.Popen(
                [python, os.path.abspath(__file__), "one", json.dumps(j)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                env=env, cwd=os.path.dirname(BENCH))
            running.append((j, p))
        time.sleep(0.2)
        still = []
        for j, p in running:
            if p.poll() is None:
                still.append((j, p))
                continue
            so, se = p.communicate()
            lines = [l for l in so.splitlines() if l.startswith("{")]
            if p.returncode == 0 and lines:
                rec = json.loads(lines[-1])
            else:                       # a crash is recorded, never hidden
                rec = dict(j, status="CRASH", err=1e30, r2=-1e30,
                           error=(se or so)[-400:])
            with open(out, "a") as fh:
                fh.write(json.dumps(rec) + "\n")
            n_done += 1
            if n_done % 25 == 0:
                print("%d done, %.0f s elapsed, %d left" % (
                    n_done, time.time() - t_start, len(todo) + len(still)),
                    flush=True)
        running = still


def guard(path):
    """The guard of the plan: the median time of the first ten fits of each
    cell, against twice its budget."""
    recs = [json.loads(l) for l in open(path) if l.strip()]
    stop = False
    for c, (_n, _k, f) in CELLS.items():
        first = [r for r in recs if r["cell"] == c][:10]
        if not first:
            print("%-12s no fit yet" % c)
            continue
        med = float(np.median([r.get("time", 0.0) for r in first]))
        over = len(first) == 10 and med > 2 * TIME_LIMIT * f
        stop = stop or over
        print("%-12s first %2d fits: median %7.1f s, budget %5.0f s%s" % (
            c, len(first), med, TIME_LIMIT * f,
            "   PAST TWICE THE BUDGET: tell the author" if over else ""))
    return stop


def show_data(eq, cells):
    for c in cells:
        Xtr, ytr, Xte, yte, names, pool, added = data(eq, c)
        print("eq %d %s: train %s test %s, finite y %s/%s, pool %s, added %s"
              % (eq, c, Xtr.shape, Xte.shape, bool(np.isfinite(ytr).all()),
                 bool(np.isfinite(yte).all()), pool, added))
        print("   column min %s" % np.round(Xtr.min(axis=0), 2).tolist())
        print("   column max %s" % np.round(Xtr.max(axis=0), 2).tolist())


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--python", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--max-seconds", type=float, default=None)
    o = sub.add_parser("one")
    o.add_argument("job")
    d = sub.add_parser("data")
    d.add_argument("eq", type=int)
    d.add_argument("cells", nargs="+")
    g = sub.add_parser("guard")
    g.add_argument("path")
    a = ap.parse_args()
    if a.cmd == "run":
        drive(a.python, a.out, a.workers, a.max_seconds)
    elif a.cmd == "one":
        print(json.dumps(run_one(json.loads(a.job))))
    elif a.cmd == "data":
        show_data(a.eq, a.cells)
    elif a.cmd == "guard":
        sys.exit(1 if guard(a.path) else 0)


if __name__ == "__main__":
    main()
