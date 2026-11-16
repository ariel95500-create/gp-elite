# -*- coding: utf-8 -*-
"""M4 of the release of 1.4.0, beside its criteria: the passes of N2b on
noisy data whose first input column is negative throughout (sgn -1) or
positive (sgn 1), six laws, 1 % and 10 % noise, one generation; the
exceptions raised inside the passes are recorded (count._wrap). With 1.4.0
as measured, the scan of the logarithm raises on 11 cases of the 12 with a
negative column, and LAPACK prints "On entry to DLASCL ..." 114 times;
none with positive columns. It decides nothing.

  /venv14rx/bin/python negative.py
"""
import io, sys, warnings, contextlib
import numpy as np
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import count as K
import gp_elite.core as C
from gp_elite import symbolic_regression
rec = []
K._wrap(C, rec)
rng = np.random.RandomState(0)
cases = {}
for sgn in (1, -1):
    x0 = sgn * rng.uniform(1, 5, 60); x1 = rng.uniform(1, 5, 60); x2 = rng.uniform(-3, 3, 60)
    X = np.c_[x0, x1, x2]
    for name, y in (("product", x0 * x1), ("ratio", x1 / x0), ("log", x1 * np.log(np.abs(x0))),
                    ("sin", x1 * np.sin(x0)), ("exp", np.exp(-np.abs(x0) / 3)), ("sum", x0 + 2 * x1)):
        for nz in (0.01, 0.10):
            cases[(sgn, name, nz)] = (X, y * (1 + nz * rng.randn(60)))
hits = {}
for k, (X, y) in cases.items():
    rec.clear()
    with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        symbolic_regression(X, y, generations=1, seed=0, parallel=False, verbose=False)
    if rec:
        hits[k] = sorted(set(rec))
print("%d cases, %d with a pass of N2b raising" % (len(cases), len(hits)))
for k, v in hits.items():
    print(" ", k, v)
