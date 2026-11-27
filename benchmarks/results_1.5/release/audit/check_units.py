"""Reproduce the findings of the audit on units, dimensions and stability."""
import io, contextlib, sys
import numpy as np
import gp_elite
from gp_elite.dim_search import parse_unit_string
from gp_elite.dimensions import check_dimensions
from gp_elite.core import Node
print("engine", gp_elite.__version__)
for s in ("m*2", "10*m", "()", "(m/s)^2", "kg*(m/s)^2", "kg*m^2/s^2", "m/s"):
    try:
        print("  parse_unit_string(%r) = %s" % (s, parse_unit_string(s)))
    except Exception as e:
        print("  parse_unit_string(%r): %s %s" % (s, type(e).__name__, str(e)[:60]))
for feats in ({0: {"m": 1}}, {"mass": {"kg": 1}}, {"X0": {"kg": 1}}):
    try:
        print("  check_dimensions(X[0], %s, target) = %s" % (feats, check_dimensions(Node("X[0]"), feats, list(feats.values())[0])))
    except Exception as e:
        print("  check_dimensions(X[0], %s): %s %s" % (feats, type(e).__name__, str(e)[:60]))
try:
    n = Node("max2"); n.left = Node("X[0]"); n.right = Node("X[1]")
    print("  check_dimensions(max2(X0, X1), both m, target m) =", check_dimensions(n, {0: {"m": 1}, 1: {"m": 1}}, {"m": 1}))
except Exception as e:
    print("  max2:", type(e).__name__, str(e)[:80])
from gp_elite import core
print("  max2 in the pools of operators:", [k for k in ("ALL_BINARY_OPS", "ALL_OPS") if "max2" in str(getattr(core, k, ""))])
from gp_elite.stability import stability_analysis
X = np.random.RandomState(0).uniform(1, 4, (40, 2)); y = X[:, 0] * X[:, 1]
with contextlib.redirect_stdout(io.StringIO()) as out:
    try:
        res = stability_analysis(X, y, n_bootstrap=3, operators="phsyical", generations=2, parallel=False, verbose=False)
    except Exception as e:
        res = "raised %s %s" % (type(e).__name__, e)
print("  stability_analysis with a misspelled operators:", res if isinstance(res, str) else {k: res.get(k) for k in ("n_bootstrap", "median_r2")}, "| printed:", out.getvalue().strip()[-60:])
