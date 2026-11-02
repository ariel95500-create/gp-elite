# -*- coding: utf-8 -*-
"""Mechanics of U1, step 4 (benchmarks/results_1.1/PLAN.md), outside any
measurement: one fit of Feynman II.11.3 with units, 30 generations, seed 0,
on the training rows of the decision bench, flag off (1.0) then on (U1).

    PYTHONHASHSEED=0 PYTHONPATH=<repo> python ii113_fit.py > ii113_fit.txt
"""
import io
import os
import sys
import time
import warnings
from contextlib import redirect_stdout

BENCH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BENCH)
import gp_elite                                   # noqa: E402
import gp_elite.core as C                         # noqa: E402
from gp_elite import symbolic_regression          # noqa: E402
from gp_elite.dimensions import check_dimensions  # noqa: E402
import decision_bench as D                        # noqa: E402
import feynman_bench as F                         # noqa: E402
import units_table as T                           # noqa: E402

i = [p[0] for p in F.PROBS].index("II.11.3")
Xtr, ytr, Xte, yte, _xo, _yo, names, pool = D.feyn_data(i)
units, tunits = T.units_of("II.11.3", names)
print("gp_elite", gp_elite.__version__, gp_elite.__file__)
for flag in (False, True):
    C._SEEDS_UNDER_UNITS = flag
    C.TRACE.value.clear()
    t0 = time.time()
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = symbolic_regression(Xtr, ytr, feature_names=names, operators=pool,
                                units=units, target_units=tunits,
                                generations=30, seed=0, parallel=False)
    dt = time.time() - t0
    e = D.one_minus_r2(yte, r.predict(Xte))
    ok, msg = check_dimensions(r.node, {k: units[n] for k, n in enumerate(names)},
                               tunits)
    print("\nflag %-5s %.1f s  1-R2 test %.3g (%s)  size %d  units %s"
          % (flag, dt, e, "EXACT" if e < 1e-9 else "not exact", r.size,
             "ok" if ok else "VIOLATED: " + msg))
    print("   ", r.expression)
    print("    binomial seed:", C.TRACE.value.get("binomial_seed"))
