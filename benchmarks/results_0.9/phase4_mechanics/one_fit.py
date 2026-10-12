"""One fit of a F41 equation with the flag of B1 off or on, 30 generations,
seed 0, islands in sequence, outside any measurement (PLAN_PHASE4.md, B1).
Usage: PYTHONHASHSEED=0 PYTHONPATH=. python benchmarks/results_0.9/phase4_mechanics/one_fit.py I.34.1 on 30
"""
import sys, io, time, warnings
from contextlib import redirect_stdout
import numpy as np
sys.path.insert(0, "/home/user/gp-elite/benchmarks")
import gp_elite.core as C
import decision_bench as D, feynman_bench as F
from gp_elite import symbolic_regression
name = sys.argv[1]; flag = sys.argv[2] == "on"; gens = int(sys.argv[3]) if len(sys.argv) > 3 else 30
C._BINOMIAL_SEEDS = flag
i = [p[0] for p in F.PROBS].index(name)
Xtr, ytr, Xte, yte, Xo, yo, names, pool = D.feyn_data(i)
t0 = time.time()
with redirect_stdout(io.StringIO()), warnings.catch_warnings():
    warnings.simplefilter("ignore")
    r = symbolic_regression(Xtr, ytr, generations=gens, seed=0, parallel=False, verbose=False, operators=pool, feature_names=names)
e = D.one_minus_r2(yte, r.predict(Xte))
print(name, "flag", flag, "1-R2 %.2e" % e, "%.1fs" % (time.time() - t0), r.expression[:120])
print("  seed:", C.TRACE.value.get("binomial_seed"), "| search s:", C.TRACE.value.get("binomial_seed_s"))
