"""E2 of PLAN.md in this folder: the fits of parts 1 and 2 of
examples/tp_regression_symbolique.ipynb, ten seeds, 1.2.0 against 1.3.0.

  python e2.py run <out_dir>         drive: every job, both versions at once
  python e2.py one <g> <s>           one fit (run by the driver)

Run from a folder without the package beside it.
"""
import json
import os
import subprocess
import sys
import time

ENGINES = (("1.2.0", "/venv12bx/bin/python"), ("1.3.0", "/venv13rx/bin/python"))
GENS = (10, 30, 60)
SEEDS = range(10)


def one(g, s):
    import warnings
    import numpy as np
    import gp_elite
    from gp_elite import symbolic_regression
    rng = np.random.RandomState(s)
    x = rng.uniform(-3, 3, 200)
    X, y = np.column_stack([x]), x * np.sin(x**2) * np.cos(x / 2)
    t = time.time()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        r = symbolic_regression(X, y, feature_names=['x'], operators='full',
                                generations=g, speed='fast', seed=s, parallel=False)
    t = time.time() - t
    expr = r.expression
    return dict(engine_version=gp_elite.__version__, engine_file=gp_elite.__file__,
                generations=g, seed=s, mse=float(np.mean((y - r.predict(X))**2)),
                size=int(r.size), formula_exact=getattr(r, "formula_exact", None),
                arcsin="arcsin" in expr, warnings=[str(m.message)[:200] for m in w],
                time=round(t, 2), expr=expr)


def run(out):
    os.makedirs(out, exist_ok=True)
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    paths = {v: os.path.join(out, "e2_%s.jsonl" % v) for v, _ in ENGINES}
    done = {v: set() for v, _ in ENGINES}
    for v, _ in ENGINES:
        if os.path.exists(paths[v]):
            for line in open(paths[v]):
                r = json.loads(line)
                done[v].add((r["generations"], r["seed"]))
    for g in GENS:
        for s in SEEDS:
            procs = []
            for v, py in ENGINES:
                if (g, s) in done[v]:
                    continue
                p = subprocess.Popen([py, "-I", os.path.abspath(__file__), "one", str(g), str(s)],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     env=env, text=True)
                procs.append((v, p))
            for v, p in procs:
                o, e = p.communicate()
                lines = [ln for ln in o.splitlines() if ln.startswith("{")]
                rec = json.loads(lines[-1]) if lines else dict(
                    generations=g, seed=s, status="CRASH", stderr=e[-500:])
                with open(paths[v], "a") as fh:
                    fh.write(json.dumps(rec) + "\n")
            print("g=%d s=%d done" % (g, s), flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "one":
        print(json.dumps(one(int(sys.argv[2]), int(sys.argv[3]))))
    else:
        run(sys.argv[2])
