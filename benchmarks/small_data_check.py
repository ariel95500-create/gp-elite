"""Small data, no hold-out: is the delivered model the one that was fitted?

Under 30 points the engine keeps no hold-out, and the champion polished at
the end of the fit is delivered as it is. This check fits five simple laws
on 25 points with four seeds and reports, for each fit, the R² of the
returned model on its own training points and on 200 fresh points of the same
domain, and how far the model is from its own best linear rescaling (a model
whose prediction p is better rescaled as a + b·p than left as it is carries
a stale scale or offset).

Usage (one process per engine, PYTHONPATH pointing at it):
    PYTHONHASHSEED=0 PYTHONPATH=<engine> python benchmarks/small_data_check.py \
        --arm NAME --out records.jsonl
    python benchmarks/small_data_check.py --summary records.jsonl
"""
import argparse
import io
import json
import os
import sys
import time
import warnings
from contextlib import redirect_stdout

import numpy as np

LAWS = [
    # name, operators, (lo, hi) per variable, f
    ("3 sin(2x) + 1", "trig", [(0.1, 3.0)],
     lambda X: 3 * np.sin(2 * X[:, 0]) + 1),
    ("x^1.5", "physical", [(0.4, 30.0)],
     lambda X: X[:, 0] ** 1.5),
    ("2.5 exp(-0.7x) + 0.3", "physical", [(0.0, 5.0)],
     lambda X: 2.5 * np.exp(-0.7 * X[:, 0]) + 0.3),
    ("x0 x1^2", "physical", [(1.0, 5.0), (1.0, 5.0)],
     lambda X: X[:, 0] * X[:, 1] ** 2),
    ("x0 / (x0 + x1)", "physical", [(1.0, 5.0), (1.0, 5.0)],
     lambda X: X[:, 0] / (X[:, 0] + X[:, 1])),
]
SEEDS = [0, 1, 2, 3]
N_TRAIN = 25


def data(i, n, seed):
    _, _, bounds, f = LAWS[i]
    rng = np.random.RandomState(seed)
    X = np.column_stack([rng.uniform(lo, hi, n) for lo, hi in bounds])
    return X, f(X)


def r2(y, p):
    with np.errstate(all="ignore"):
        e = float(np.mean((np.asarray(p, dtype=float) - y) ** 2) / np.var(y))
    return 1.0 - e if np.isfinite(e) else -1e30


def run(arm, out):
    from gp_elite import symbolic_regression, core
    import gp_elite
    for i, (name, ops, _, _) in enumerate(LAWS):
        Xtr, ytr = data(i, N_TRAIN, 100 + i)
        Xte, yte = data(i, 200, 200 + i)
        for s in SEEDS:
            t0 = time.time()
            with redirect_stdout(io.StringIO()), warnings.catch_warnings():
                warnings.simplefilter("ignore")
                r = symbolic_regression(Xtr, ytr, operators=ops, generations=40,
                                        seed=s, parallel=False)
            p = np.asarray(r.predict(Xtr), dtype=float)
            a, b, ok = core._linear_scale_params(p, ytr)
            rec = dict(arm=arm, law=name, seed=s, time=round(time.time() - t0, 2),
                       r2_train=r2(ytr, p), r2_test=r2(yte, r.predict(Xte)),
                       r2_train_rescaled=r2(ytr, a + b * p) if ok else None,
                       size=int(r.size), expr=r.expression[:160],
                       engine=gp_elite.__file__,
                       pythonhashseed=os.environ.get("PYTHONHASHSEED"))
            with open(out, "a") as fh:
                fh.write(json.dumps(rec) + "\n")
            print("%-4s %-22s s%d  train R2 %10.4f  (rescaled %10.4f)  test R2 %10.4f"
                  % (arm, name, s, rec["r2_train"], rec["r2_train_rescaled"] or 0,
                     rec["r2_test"]), flush=True)


def summary(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    for arm in sorted({r["arm"] for r in rows}):
        rr = [r for r in rows if r["arm"] == arm]
        tr = [r["r2_train"] for r in rr]
        te = [r["r2_test"] for r in rr]
        stale = sum(1 for r in rr if r["r2_train_rescaled"] is not None
                    and r["r2_train_rescaled"] - r["r2_train"] > 1e-6)
        print("%-4s %d fits  train R2 median %.4f worst %.4g   test R2 median %.4f "
              "worst %.4g   below 0 on test: %d   stale scale/offset: %d"
              % (arm, len(rr), np.median(tr), min(tr), np.median(te), min(te),
                 sum(1 for x in te if x < 0), stale))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm")
    ap.add_argument("--out")
    ap.add_argument("--summary")
    a = ap.parse_args()
    if a.summary:
        summary(a.summary)
    else:
        run(a.arm, a.out)
