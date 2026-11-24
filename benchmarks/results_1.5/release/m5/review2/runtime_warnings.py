"""Review 2 of M5, question 5: the warnings a fit emits, and the module each is
attributed to (what `warnings.filterwarnings(..., module=...)` matches).

One small fit (generations=5, parallel=False, seed 0) on data with negative
values, all warnings recorded. Prints category, message, and the file the
warning is attributed to, counted.

Usage: python runtime_warnings.py
"""
import collections
import contextlib
import io
import os
import warnings

import numpy as np

import gp_elite
from gp_elite import symbolic_regression

r = np.random.RandomState(3)
X = r.uniform(-3, 3, (80, 2))
y = np.sin(X[:, 0]) * X[:, 1] + 0.1 * X[:, 0] ** 3
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    with contextlib.redirect_stdout(io.StringIO()):
        res = symbolic_regression(X, y, generations=5, seed=0, parallel=False, verbose=False)
c = collections.Counter((x.category.__name__, str(x.message)[:60], os.path.basename(x.filename)) for x in w)
print("engine %s: model %s; %d warnings" % (gp_elite.__version__, res.expression, len(w)))
for (cat, msg, f), n in sorted(c.items()):
    print("  %4d  %-18s %-60s from %s" % (n, cat, msg, f))
