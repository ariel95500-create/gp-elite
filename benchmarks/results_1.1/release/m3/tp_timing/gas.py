import time, sys
import numpy as np
import gp_elite
from gp_elite import symbolic_regression
rng = np.random.default_rng(0)
n = 10
X = np.column_stack([rng.uniform(lo, hi, n) for lo, hi in [(0.01, 0.10), (273.0, 373.0), (1e-3, 5e-3)]])
y = X[:, 0] * 8.314 * X[:, 1] / X[:, 2] * (1 + 0.02 * rng.standard_normal(n))
t0 = time.time()
r = symbolic_regression(X, y, feature_names=['n', 'T', 'V'], units=dict(zip(['n', 'T', 'V'], ['mol', 'K', 'm^3'])),
                        target_units='kg/(m*s^2)', unknown_constant=True, parallel=False, seed=0)
print(gp_elite.__version__, r.expression, "%.1f s" % (time.time() - t0)); import gp_elite.core as C; print({k: v for k, v in sorted(getattr(C.TRACE, "counts", getattr(C.TRACE, "__dict__", {})).items()) if not callable(v)} if hasattr(C, "TRACE") else "no trace"); print(r.diagnostics, r.restarts_completed)
