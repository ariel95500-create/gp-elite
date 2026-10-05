"""Does the scale of the data decide whether a law is found?

One law, y = s_y · (x0/s_x)² / x1 with x0/s_x in [1, 5] and x1 in [1, 3],
fitted with default settings (15 generations, seed 0) for input scales s_x
and target scales s_y from 1e-34 to 1e30. Prints, per scale, the R² of the
returned model on its training points (in units of s_y) and its formula.

Usage (one process per engine, PYTHONPATH pointing at it if needed):
    PYTHONHASHSEED=0 python benchmarks/scale_check.py
"""
import io
import subprocess
import sys
import warnings
from contextlib import redirect_stdout

import numpy as np

SCALES = [(1, 1), (1e-9, 1), (1e-19, 1), (1e-34, 1), (1, 1e-9), (1, 1e-19),
          (1, 1e-30), (1, 1e20), (1, 1e30), (1e-9, 1e-9), (1e9, 1e30)]


def one(sx, sy):
    from gp_elite import symbolic_regression
    rng = np.random.RandomState(0)
    x = rng.uniform(1, 5, 120) * sx
    X = np.c_[x, rng.uniform(1, 3, 120)]
    y = sy * (x / sx) ** 2 / X[:, 1]
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            r = symbolic_regression(X, y, generations=15, seed=0, parallel=False)
        except Exception as e:                       # noqa: BLE001
            return "ERROR %s: %s" % (type(e).__name__, str(e)[:100])
    p = np.asarray(r.predict(X), dtype=float)
    with np.errstate(all="ignore"):
        r2 = 1 - np.mean(((p - y) / sy) ** 2) / np.var(y / sy)
    return "R2 %10.6f  formula_exact %-5s  %s" % (r2, r.formula_exact, r.expression[:60])


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "one":
        print(one(float(sys.argv[2]), float(sys.argv[3])))
        sys.exit(0)
    import gp_elite
    print("engine:", gp_elite.__file__)
    for sx, sy in SCALES:
        out = subprocess.run([sys.executable, __file__, "one", repr(sx), repr(sy)],
                             capture_output=True, text=True).stdout.strip()
        print("x scale %-7g y scale %-7g  %s" % (sx, sy, out.splitlines()[-1] if out else "?"),
              flush=True)
