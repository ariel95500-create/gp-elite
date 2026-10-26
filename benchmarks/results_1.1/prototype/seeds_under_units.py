# -*- coding: utf-8 -*-
"""Prototype of phase 7, before its plan (decides nothing, no measurement).

For each of the 41 equations of the decision bench, on its training rows
(decision_bench.feyn_data), one fit of gp-elite 1.0.0 with units= and
target_units= (benchmarks/units_table.py), generations=1, seed 0. The four
seed finders of 1.0 (power law, B1, E1, N1) are wrapped: each is called as
it would be without units (FEAT_DIMS removed from a copy of the
configuration, so that its guard lets it run), on the rows and columns the
engine gives it, and the trees it returns are recorded with their verdict
by the engine's own gate, dim_search.is_typed_valid. The wrappers return
nothing, so the fit itself is that of 1.0.0 and its result is not used.

    PYTHONHASHSEED=0 python seeds_under_units.py > seeds_under_units.txt

Run on 26 October 2026 with the repository at commit 9b669a4 (gp-elite
1.0.0, the code of the published wheel), Python 3.11, NumPy 2.4, on the
machine of PLAN.md; nothing was written to stderr.
"""
import copy
import io
import json
import os
import sys
import warnings
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(BENCH)
sys.path.insert(0, ROOT)
sys.path.insert(0, BENCH)

import gp_elite                                   # noqa: E402
import gp_elite.core as C                         # noqa: E402
from gp_elite import symbolic_regression          # noqa: E402
from gp_elite.dim_search import is_typed_valid    # noqa: E402
import decision_bench as D                        # noqa: E402
import feynman_bench as F                         # noqa: E402
import units_table as T                           # noqa: E402

ORIG = {k: getattr(C, k) for k in ("_make_power_law_seeds",
                                   "_make_binomial_seeds",
                                   "_make_elementary_seeds",
                                   "_make_tolerant_seeds")}
REC = []
STATE = {"inner": False}


def wrap(key):
    def w(xs, ys, cfg, *a, **k):
        if STATE["inner"]:                        # called by the N1 finder
            return ORIG[key](xs, ys, cfg, *a, **k)
        c2 = copy.copy(cfg)
        c2.FEAT_DIMS = None
        if key == "_make_tolerant_seeds":
            STATE["inner"] = True
        try:
            out = ORIG[key](xs, ys, c2, *a, **k)
        finally:
            STATE["inner"] = False
        for t in out:
            REC.append(dict(
                finder=key.replace("_make_", "").replace("_seeds", ""),
                tree=C.to_string(t),
                valid=bool(is_typed_valid(t, cfg.FEAT_DIMS, cfg.TARGET_DIM,
                                          bool(getattr(cfg, "UNKNOWN_CONST",
                                                       False))))))
        return []
    return w


for key in ORIG:
    setattr(C, key, wrap(key))

print("gp_elite", gp_elite.__version__, gp_elite.__file__)
rows = []
for i, p in enumerate(F.PROBS):
    name = p[0]
    Xtr, ytr, _xte, _yte, _xo, _yo, names, pool = D.feyn_data(i)
    units, tunits = T.units_of(name, names)
    del REC[:]
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        symbolic_regression(Xtr, ytr, feature_names=names, operators=pool,
                            units=units, target_units=tunits, generations=1,
                            seed=0, parallel=False, verbose=False)
    exact = [r for r in REC if r["finder"] != "tolerant"]
    tol = [r for r in REC if r["finder"] == "tolerant"]
    row = dict(name=name, family=F._fam(p), pool=pool,
               found={f: sum(1 for r in REC if r["finder"] == f)
                      for f in ("power_law", "binomial", "elementary",
                                "tolerant")},
               valid={f: sum(1 for r in REC if r["finder"] == f and r["valid"])
                      for f in ("power_law", "binomial", "elementary",
                                "tolerant")},
               seeds=REC[:])
    rows.append(row)
    print("%-10s %-16s exact found %d valid %d | tolerant found %d valid %d"
          % (name, row["family"], len(exact), sum(r["valid"] for r in exact),
             len(tol), sum(r["valid"] for r in tol)))
    for r in REC:
        print("    %-11s %-5s %s" % (r["finder"], "ok" if r["valid"] else "NO",
                                     r["tree"][:110]))
    sys.stdout.flush()

with open(os.path.join(HERE, "seeds_under_units.json"), "w") as fh:
    json.dump(rows, fh, indent=1)
n_ex = sum(1 for r in rows if any(s["valid"] and s["finder"] != "tolerant"
                                  for s in r["seeds"]))
n_any = sum(1 for r in rows if any(s["finder"] != "tolerant" for s in r["seeds"]))
print("\nequations with an exact seed without units: %d; of them with one "
      "valid under units: %d" % (n_any, n_ex))
