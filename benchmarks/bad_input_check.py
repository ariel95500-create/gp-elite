"""Unusable inputs: does a fit refuse them, or return a formula anyway?

Cases: a missing value (NaN) in the column the law does not use and in the
one it uses, an infinite value in X, a NaN in y, a non-numeric column in a
DataFrame, and predict() on a row with a missing input. The law is
y = 2*x0 + 1 on 60 rows; each case runs in its own process (the engine keeps
module state between fits). For each case the record says whether the fit
raised an error (and its message) or returned a model (its formula and its R²
on 60 clean rows of the true law); for the predict case, what predict()
returns for the row with a NaN.

Usage (PYTHONPATH may point at another engine to compare versions):
    PYTHONHASHSEED=0 python benchmarks/bad_input_check.py
"""
import io
import json
import os
import subprocess
import sys
import warnings
from contextlib import redirect_stdout

import numpy as np

CASES = ["nan_in_X", "nan_in_used_column", "inf_in_X", "nan_in_y", "text_column",
         "predict_nan_row"]


def data():
    rng = np.random.RandomState(0)
    X = rng.uniform(1, 5, (60, 2))
    return X, 2 * X[:, 0] + 1


def one(name):
    import gp_elite
    from gp_elite import symbolic_regression
    X, y = data()
    Xc, yc = X.copy(), y.copy()
    rec = dict(case=name, engine=os.path.dirname(os.path.dirname(gp_elite.__file__)))
    kw = dict(generations=15, seed=0, parallel=False)
    fit_X, fit_y = X, y
    if name == "nan_in_X":
        fit_X = X.copy(); fit_X[7, 1] = np.nan
    elif name == "nan_in_used_column":
        fit_X = X.copy(); fit_X[7, 0] = np.nan
    elif name == "inf_in_X":
        fit_X = X.copy(); fit_X[7, 1] = np.inf
    elif name == "nan_in_y":
        fit_y = y.copy(); fit_y[7] = np.nan
    elif name == "text_column":
        import pandas as pd
        fit_X = pd.DataFrame({"x0": X[:, 0], "x1": X[:, 1],
                              "label": ["a", "b", "c"] * 20})
    try:
        with redirect_stdout(io.StringIO()), warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            r = symbolic_regression(fit_X, fit_y, **kw)
        rec["warnings"] = [str(m.message)[:160] for m in w][:3]
        rec["outcome"] = "model"
        rec["expression"] = r.expression[:160]
        if name != "text_column":
            p = np.asarray(r.predict(Xc), dtype=float)
            rec["r2_true_law"] = float(1 - np.mean((p - yc) ** 2) / np.var(yc))
        if name == "predict_nan_row":
            Xn = Xc[:3].copy(); Xn[1, 0] = np.nan
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    rec["predict_nan_row"] = [None if not np.isfinite(v) else float(v)
                                              for v in np.asarray(r.predict(Xn), float)]
                except Exception as e:                  # noqa: BLE001
                    rec["predict_nan_row"] = "%s: %s" % (type(e).__name__, str(e)[:160])
    except Exception as e:                              # noqa: BLE001
        rec["outcome"] = "error"
        rec["error"] = "%s: %s" % (type(e).__name__, str(e)[:240])
    return rec


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "one":
        print(json.dumps(one(sys.argv[2])))
        sys.exit(0)
    for name in CASES:
        p = subprocess.run([sys.executable, os.path.abspath(__file__), "one", name],
                           capture_output=True, text=True, timeout=600,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
        rec = json.loads(lines[-1]) if (p.returncode == 0 and lines) else dict(
            case=name, outcome="crash", error=p.stderr[-400:])
        print(json.dumps(rec, ensure_ascii=False), flush=True)
