"""Mechanics check of phase 2 (PLAN_PHASE2.md): a target that pushes the power
safety net (x0^7 is beyond the exponent clip of ±6), one fit per arm.

  PYTHONHASHSEED=0 PYTHONPATH=. python benchmarks/results_0.9/phase2_mechanics/power_example.py A

The flags exist in the engine at commit 0038a29 only (PLAN_PHASE2.md).
"""
import json
import sys
import warnings

import numpy as np

import gp_elite.core as C
from gp_elite import symbolic_regression

arm = sys.argv[1]
if not hasattr(C, "_GUARD_STRICT"):
    sys.exit("the phase 2 flags are not in this engine: run from commit 0038a29")
C._GUARD_STRICT = arm in ("F1", "F3", "F3R")
C._GUARD_SEARCH = arm not in ("F3", "F3R")
C._GUARD_CATCHUP = arm == "F3R"
warnings.simplefilter("ignore")
r = np.random.RandomState(3)
X = r.uniform(0.5, 3.0, (150, 2))
y = X[:, 0] ** 7 / (1 + X[:, 1])
res = symbolic_regression(X, y, generations=15, parallel=False, seed=0,
                          verbose=False)
print(json.dumps(dict(
    arm=arm, formula_exact=res.formula_exact,
    pareto=len(res.pareto or []),
    pareto_inexact=sum(1 for e in (res.pareto or []) if e.formula_exact is False),
    removed_from_pool=int(C.TRACE.count.get("pool_rejets_garde", 0)),
    rejected_in_search=int(C.TRACE.count.get("candidats_rejetes_garde", 0)),
    catchup=C.TRACE.value.get("rattrapage"),
    expression=res.expression[:120])))
