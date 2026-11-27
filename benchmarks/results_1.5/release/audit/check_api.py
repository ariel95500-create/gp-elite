"""Reproduce the findings of the audit on the API side, one per process."""
import io, contextlib, random, sys
import numpy as np
which = sys.argv[1]
import gp_elite
from gp_elite import symbolic_regression
import gp_elite.core as core
r = np.random.RandomState(0)
X = r.uniform(1, 4, (60, 2)); y = X[:, 0] * X[:, 1]
q = dict(generations=3, parallel=False, verbose=False)
print("engine", gp_elite.__version__, "|", which)
if which == "A":   # validation error after the global state changed
    try:
        symbolic_regression(X, y, robust=True, time_limit=-1, **q)
    except Exception as e:
        print("  call 1 raised:", type(e).__name__, str(e)[:60])
    print("  state after:", {n: getattr(core, n, "<missing>") for n in ("_GENERIC_CSV_MODE", "_CUSTOM_LOSS_ROBUST", "_CUSTOM_LOSS_USE_SCALING", "_CUSTOM_LOSS_PARSIMONY")})
    res = symbolic_regression(X, y, seed=0, **q)
    print("  state after a plain call:", {n: getattr(core, n, "<missing>") for n in ("_GENERIC_CSV_MODE", "_CUSTOM_LOSS_ROBUST", "_CUSTOM_LOSS_USE_SCALING", "_CUSTOM_LOSS_PARSIMONY")})
    print("  plain call after the failed one:", res.expression, res.size)
elif which == "A0":  # the same plain call in a fresh process
    res = symbolic_regression(X, y, seed=0, **q)
    print("  plain call alone:", res.expression, res.size)
elif which == "B":   # mse_train of a constant model
    res = symbolic_regression(X, np.full(60, 3.0), seed=0, **q)
    print("  constant target:", res.expression, "mse_train", res.mse_train, "mse_validation", res.mse_validation)
elif which == "C":   # seed=None and the caller's global RNGs
    a = symbolic_regression(X, y + r.normal(0, 0.5, 60), **q).expression
    random.seed(12345); np.random.seed(12345)
    b = symbolic_regression(X, y + r.normal(0, 0.5, 60), **q).expression
    print("  after the fit, random.random() =", random.random(), "np.random.rand() =", np.random.rand())
    random.seed(12345); np.random.seed(12345); print("  without a fit, the caller would get", random.random(), np.random.rand())
elif which == "C2":  # two calls with seed=None on the same data
    yn = y + np.random.RandomState(5).normal(0, 0.5, 60)
    print("  seed=None twice:", symbolic_regression(X, yn, **q).expression, "|", symbolic_regression(X, yn, **q).expression)
elif which == "D":   # extrapolate_feature out of range
    for k in (3, -1):
        for rs in (1, 2):
            try:
                res = symbolic_regression(X, y, seed=0, extrapolate_feature=k, restarts=rs, **q)
                print("  extrapolate_feature=%d restarts=%d: ran, %s" % (k, rs, res.expression))
            except Exception as e:
                print("  extrapolate_feature=%d restarts=%d: %s %s" % (k, rs, type(e).__name__, str(e)[:70]))
