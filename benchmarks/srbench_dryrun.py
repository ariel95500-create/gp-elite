"""SRBench-style dry run [v0.3].

This is NOT the official SRBench submission — it's the internal rehearsal we
run first: same protocol shape (proper train/test split, fit through the
sklearn wrapper, report test R2 and model size), on a handful of Feynman
equations, so we know our numbers before anyone else does.

Run with a frozen seed for reproducibility:
    PYTHONHASHSEED=0 python benchmarks/srbench_dryrun.py

The official SRBench harness adds: many more datasets (Feynman + Strogatz +
black-box), noise levels, multiple seeds per problem, and a wall-clock budget.
Passing sklearn's check_estimator (see tests) is the entry ticket; this rehearsal
tells us where we'd land on the ground-truth track.
"""
import json
import sys
import time

import numpy as np

sys.path.insert(0, "benchmarks")
from feynman_bench import PROBS                      # noqa: E402
from gp_elite import GPEliteRegressor                # noqa: E402


def r2(y, yhat):
    ss = float(np.sum((y - y.mean()) ** 2)) or 1e-30
    return 1.0 - float(np.sum((y - yhat) ** 2) / ss)


def dry_run(i0=0, i1=8, generations=30, out="srbench_dryrun.jsonl"):
    rows = []
    for i in range(i0, min(i1, len(PROBS))):
        name, formula, nv, sampler, f, pool = PROBS[i]
        rng = np.random.RandomState(2000 + i)
        X = sampler(rng, 400)
        y = f(X)
        # SRBench-style 75/25 split
        idx = rng.permutation(400)
        tr, te = idx[:300], idx[300:]

        t0 = time.time()
        est = GPEliteRegressor(operators=pool, generations=generations,
                               speed="fast", restarts=4, random_state=0)
        est.fit(X[tr], y[tr])
        dt = time.time() - t0

        yhat = est.predict(X[te])
        r2_test = r2(y[te], yhat)
        # SRBench "solution rate": R2 test > 0.999 counts as solved
        solved = r2_test > 0.999
        size = est.model_.size

        rec = dict(name=name, r2_test=round(r2_test, 6), solved=bool(solved),
                   size=int(size), seconds=round(dt, 1),
                   equation=est.sympy())
        rows.append(rec)
        with open(out, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        flag = "SOLVED" if solved else ("close " if r2_test > 0.99 else "miss  ")
        print(f"  {name:<10} [{flag}] R2_test={r2_test:>9.5f}  "
              f"size={size:>2}  ({dt:>4.0f}s)")
        sys.stdout.flush()

    n = len(rows)
    ns = sum(r["solved"] for r in rows)
    med = float(np.median([r["r2_test"] for r in rows]))
    print(f"\nDry-run summary: {ns}/{n} solved (R2_test>0.999), "
          f"median R2_test={med:.4f}")
    return rows


if __name__ == "__main__":
    a = sys.argv
    dry_run(int(a[1]) if len(a) > 1 else 0,
            int(a[2]) if len(a) > 2 else 8)
