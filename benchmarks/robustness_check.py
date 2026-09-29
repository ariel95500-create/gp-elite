"""Unusual but legitimate data: does a fit finish, say what it did, and
deliver a model that reproduces what it fitted?

Each case runs in its own process (the engine keeps module state between
fits; one process per measurement). For each case the record says whether
the fit ended with a model or with an error, the message of the error, the
training R² of the returned model, whether its formula reproduces predict()
(`formula_exact`) and whether its predictions are finite.

Usage:
    PYTHONHASHSEED=0 python benchmarks/robustness_check.py --out records.jsonl
    python benchmarks/robustness_check.py --summary records.jsonl
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time
import warnings
from contextlib import redirect_stdout

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def _u(rng, lo, hi, n):
    return rng.uniform(lo, hi, n)


def case_data(name):
    """(X, y, kwargs, what is expected) for one case."""
    rng = np.random.RandomState(0)
    n = 120
    x = _u(rng, 1, 5, n)
    if name == "constant_column":
        return np.c_[x, np.full(n, 5.0)], 2 * x + 1, {}, "model"
    if name == "zero_column":
        return np.c_[x, np.zeros(n)], 2 * x + 1, {}, "model"
    if name == "constant_target":
        return np.c_[x, _u(rng, 1, 5, n)], np.full(n, 3.0), {}, "model or clear error"
    if name == "duplicated_columns":
        return np.c_[x, x], x ** 2, {}, "model"
    if name == "three_rows":
        X = np.array([[1.0], [2.0], [3.0]])
        return X, 2 * X[:, 0], {}, "model or clear error"
    if name == "ten_rows":
        X = _u(rng, 1, 5, 10).reshape(-1, 1)
        return X, X[:, 0] ** 2, {}, "model"
    if name == "huge_inputs":
        X = _u(rng, 1e150, 5e150, n).reshape(-1, 1)
        return X, X[:, 0] * 1e-150, {}, "model"
    if name == "tiny_inputs":
        X = _u(rng, 1e-150, 5e-150, n).reshape(-1, 1)
        return X, X[:, 0] * 1e150, {}, "model"
    if name == "huge_target":
        return x.reshape(-1, 1), 1e200 * x, {}, "model"
    if name == "tiny_target":
        return x.reshape(-1, 1), 1e-200 * x, {}, "model"
    if name == "wide_dynamic_range":
        z = np.exp(_u(rng, np.log(1e-3), np.log(1e6), n))
        return np.c_[z, x], np.log(z) * x, {}, "model"
    if name == "integer_and_boolean_columns":
        k = rng.randint(1, 6, n)
        b = rng.rand(n) > 0.5
        return np.c_[k, b], 3 * k + 2 * b, {}, "model"
    if name == "twenty_columns_two_used":
        X = _u(rng, 1, 5, (n, 20))
        return X, X[:, 3] * X[:, 7], {}, "model"
    if name == "negative_target_power_law":
        X = np.c_[x, _u(rng, 1, 3, n)]
        return X, -X[:, 0] / X[:, 1] ** 2, {}, "model"
    if name == "one_outlier":
        y = 2 * x + 1
        y[5] = 1e6
        return x.reshape(-1, 1), y, {}, "model"
    if name == "no_holdout_small_signed":
        X = _u(rng, -2, 2, 20).reshape(-1, 1)
        return X, np.sin(2 * X[:, 0]) + 0.5, {"operators": "trig"}, "model"
    raise KeyError(name)


CASES = ["constant_column", "zero_column", "constant_target",
         "duplicated_columns", "three_rows", "ten_rows", "huge_inputs",
         "tiny_inputs", "huge_target", "tiny_target", "wide_dynamic_range",
         "integer_and_boolean_columns", "twenty_columns_two_used",
         "negative_target_power_law", "one_outlier", "no_holdout_small_signed"]


def one(name):
    from gp_elite import symbolic_regression
    import gp_elite
    X, y, kw, expected = case_data(name)
    rec = dict(case=name, expected=expected, engine=gp_elite.__file__,
               pythonhashseed=os.environ.get("PYTHONHASHSEED"))
    t0 = time.time()
    caught = []
    try:
        with redirect_stdout(io.StringIO()), warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            r = symbolic_regression(X, y, generations=20, seed=0, parallel=False, **kw)
            caught = [str(m.message)[:200] for m in w]
        p = np.asarray(r.predict(X), dtype=float)
        finite = bool(np.all(np.isfinite(p)))
        v = float(np.var(y))
        with np.errstate(all="ignore"):
            r2 = (1.0 - float(np.mean((p - y) ** 2)) / v) if v > 0 else None
        rec.update(outcome="model", expression=r.expression[:200],
                   size=int(r.size), formula_exact=bool(r.formula_exact),
                   finite=finite, r2_train=r2)
    except Exception as e:                           # noqa: BLE001
        rec.update(outcome="error", error="%s: %s" % (type(e).__name__, str(e)[:300]))
    rec["warnings"] = caught[:5]
    rec["time"] = round(time.time() - t0, 2)
    return rec


def run(out):
    for name in CASES:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        p = subprocess.run([sys.executable, os.path.abspath(__file__), "one", name],
                           capture_output=True, text=True, env=env, timeout=900)
        lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
        if p.returncode == 0 and lines:
            rec = json.loads(lines[-1])
        else:
            rec = dict(case=name, outcome="crash", error=p.stderr[-600:])
        with open(out, "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print("%-30s %-6s %s" % (name, rec["outcome"],
                                 rec.get("expression") or rec.get("error", "")[:100]),
              flush=True)


def summary(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    for r in rows:
        if r["outcome"] == "model":
            print("%-30s model  R2 train %s  exact formula %s  finite %s  %s"
                  % (r["case"], "%.6f" % r["r2_train"] if r["r2_train"] is not None
                     else "n/a", r["formula_exact"], r["finite"], r["expression"][:70]))
        else:
            print("%-30s %-6s %s" % (r["case"], r["outcome"], r.get("error", "")[:110]))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "one":
        print(json.dumps(one(sys.argv[2])))
        sys.exit(0)
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--summary")
    a = ap.parse_args()
    if a.summary:
        summary(a.summary)
    else:
        run(a.out)
