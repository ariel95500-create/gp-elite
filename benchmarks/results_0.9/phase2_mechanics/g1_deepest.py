"""Mechanics check 3 of G1 (PLAN_PHASE2.md): on 228_elusage in its own
units, out of domain, seed 4 (the deepest collapse of COLLAPSES.md), the
model returned with the flag on passes the far test.

  PYTHONHASHSEED=0 PYTHONPATH=. python benchmarks/results_0.9/phase2_mechanics/g1_deepest.py
"""
import io
import json
import os
import sys
import warnings
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np

import gp_elite.core as C
import phase1_bench as P
import decision_bench as D
from gp_elite import symbolic_regression

out = []
for flag in (False, True):
    C._FAR_GUARD = flag
    job = dict(kind="realraw", problem="228_elusage", split="ood", seed=4)
    Xtr, ytr, Xo, yo, _, _, _, pool, _ = P._data(job)
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = symbolic_regression(Xtr, ytr, generations=P.GENERATIONS,
                                time_limit=P.TIME_LIMIT, seed=4,
                                parallel=False, verbose=False, operators=pool)
    node = r.eval_node if getattr(r, "eval_node", None) is not None else r.node
    C._FAR_GUARD = True
    if C._FAR_PROBE_XS is None:      # flag off during the fit: build them now
        C._build_far_probes(np.vstack([C._VAL_TRAIN_XS, C._VAL_XS]),
                            np.concatenate([C._VAL_TRAIN_YS, C._VAL_YS]))
        C._FAR_CACHE.clear()
    out.append(dict(flag=flag, passes_far_test=C._far_stable(node),
                    r2_ood=1.0 - D.one_minus_r2(yo, r.predict(Xo)),
                    size=int(r.size), far_rejected=int(C.TRACE.count.get("far_rejets", 0)),
                    expr=r.expression[:120]))
    print(json.dumps(out[-1]))
