# -*- coding: utf-8 -*-
"""Which seeds U1 placed in campaign U1 (reported beside the criteria of
benchmarks/results_1.1/PLAN.md; decides nothing).

The finders are deterministic and see only the training rows, which in the
campaign depend on the equation and the kind, not on the seed (the noise of
ufeyn_n1 and ufeyn_n10 is drawn with RandomState(7000 + index)). So one fit
of one generation per equation and kind, with the flag on, shows what the
finders placed in all five seeds. The wrappers only record what the four
finders return at the top level.

    PYTHONHASHSEED=0 PYTHONPATH=<repo> python seeds_in_campaign.py > seeds_in_campaign.txt
"""
import io
import json
import os
import sys
import warnings
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import gp_elite                                   # noqa: E402
import gp_elite.core as C                         # noqa: E402
from gp_elite import symbolic_regression          # noqa: E402
import feynman_bench as F                         # noqa: E402
import phase1_bench as P                          # noqa: E402
import units_table as T                           # noqa: E402

C._SEEDS_UNDER_UNITS = True
NAMES = {"_make_power_law_seeds": "power_law", "_make_binomial_seeds": "B1",
         "_make_elementary_seeds": "E1", "_make_tolerant_seeds": "N1"}
ORIG = {k: getattr(C, k) for k in NAMES}
REC = []
DEPTH = [0]


def wrap(key):
    def w(*a, **k):
        DEPTH[0] += 1
        try:
            out = ORIG[key](*a, **k)
        finally:
            DEPTH[0] -= 1
        if DEPTH[0] == 0:
            REC.extend((NAMES[key], C.to_string(t)) for t in out)
        return out
    return w


for key in ORIG:
    setattr(C, key, wrap(key))

print("gp_elite", gp_elite.__version__, gp_elite.__file__)
rows = []
for kind in ("ufeyn", "ufeyn_n1", "ufeyn_n10"):
    n_with = 0
    for i, p in enumerate(F.PROBS):
        job = dict(kind=kind, problem=p[0], index=i, split="test", seed=0)
        Xtr, ytr, _a, _b, _c, _d, names, pool, _clean = P._data(job)
        units, tunits = T.units_of(p[0], names)
        del REC[:]
        with redirect_stdout(io.StringIO()), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            symbolic_regression(Xtr, ytr, feature_names=names, operators=pool,
                                units=units, target_units=tunits,
                                generations=1, seed=0, parallel=False)
        n_with += bool(REC)
        rows.append(dict(kind=kind, problem=p[0], seeds=REC[:]))
        print("%-10s %-10s %s" % (kind, p[0], ", ".join(
            "%s %s" % (f, t[:60]) for f, t in REC) or "none"))
        sys.stdout.flush()
    print("== %s: a seed placed on %d equations of 41\n" % (kind, n_with))
json.dump(rows, open(os.path.join(HERE, "seeds_in_campaign.json"), "w"),
          indent=1)
