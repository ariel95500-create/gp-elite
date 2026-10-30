# The free fall of the TP notebook (cell 5: t at 10 points, 2 % noise, units and
# unknown_constant=True, parallel=False, seed=0), alone, with its trace.
import time
import numpy as np
import gp_elite
import gp_elite.core as C
from gp_elite import symbolic_regression
rng = np.random.default_rng(0)
X = np.linspace(0.10, 0.60, 10).reshape(-1, 1)
y = 0.5 * 9.81 * X[:, 0] ** 2 * (1 + 0.02 * rng.standard_normal(10))
t0 = time.time()
r = symbolic_regression(X, y, feature_names=['t'], units={'t': 's'}, target_units='m',
                        unknown_constant=True, parallel=False, seed=0)
print(gp_elite.__version__, r.expression, "%.1f s" % (time.time() - t0))
tr = C.TRACE
print({k: v for k, v in sorted(vars(tr).items()) if not callable(v)})
