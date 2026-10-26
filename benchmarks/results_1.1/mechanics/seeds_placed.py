# -*- coding: utf-8 -*-
"""Mechanics of U1, step 3 (benchmarks/results_1.1/PLAN.md): with the flag on,
on the training rows of U41, the seeds the engine places are those the
prototype found valid (prototype/seeds_under_units.json).

For each of the 41 equations, one fit with units, generations=1, seed 0, the
flag _SEEDS_UNDER_UNITS on. The four finders are wrapped only to record what
they return at the top level (the engine's own calls go through unchanged).
Expected: the power-law, B1 and E1 seeds are the prototype's valid ones; the
N1 seeds are the prototype's valid tolerant ones when B1 and E1 kept none,
and none otherwise. When the power law placed a seed, the engine runs N1
without the power law (power_done, as in 1.0), which the prototype did not
do (its wrappers placed nothing): the tolerant seeds equal to a power-law
seed of the prototype are then not expected. (This last rule was added after
a first run, whose output is kept in seeds_placed_first_run.txt: 15
equations differed by exactly such a seed.)

    PYTHONHASHSEED=0 PYTHONPATH=<repo> python seeds_placed.py > seeds_placed.txt
"""
import io
import json
import os
import sys
import warnings
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, BENCH)

import gp_elite                                   # noqa: E402
import gp_elite.core as C                         # noqa: E402
from gp_elite import symbolic_regression          # noqa: E402
import decision_bench as D                        # noqa: E402
import feynman_bench as F                         # noqa: E402
import units_table as T                           # noqa: E402

C._SEEDS_UNDER_UNITS = True
NAMES = {"_make_power_law_seeds": "power_law", "_make_binomial_seeds": "binomial",
         "_make_elementary_seeds": "elementary",
         "_make_tolerant_seeds": "tolerant"}
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

proto = {r["name"]: r for r in json.load(open(os.path.join(
    os.path.dirname(HERE), "prototype", "seeds_under_units.json")))}
print("gp_elite", gp_elite.__version__, gp_elite.__file__)
n_ok = 0
for i, p in enumerate(F.PROBS):
    name = p[0]
    Xtr, ytr, _a, _b, _c, _d, names, pool = D.feyn_data(i)
    units, tunits = T.units_of(name, names)
    del REC[:]
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        symbolic_regression(Xtr, ytr, feature_names=names, operators=pool,
                            units=units, target_units=tunits, generations=1,
                            seed=0, parallel=False, verbose=False)
    pr = proto[name]["seeds"]
    exact = [(s["finder"], s["tree"]) for s in pr
             if s["finder"] != "tolerant" and s["valid"]]
    b1e1 = any(f in ("binomial", "elementary") for f, _t in exact)
    plaw = {s["tree"] for s in pr if s["finder"] == "power_law"}
    placed_plaw = any(f == "power_law" for f, _t in exact)
    tol = [] if b1e1 else [(s["finder"], s["tree"]) for s in pr
                           if s["finder"] == "tolerant" and s["valid"]
                           and not (placed_plaw and s["tree"] in plaw)]
    expected = sorted(exact + tol)
    got = sorted(REC)
    same = got == expected
    n_ok += same
    print("%-10s %s  placed %d, expected %d" % (name, "same" if same
                                                else "DIFFERENT", len(got),
                                                len(expected)))
    if not same:
        print("   placed:  ", got)
        print("   expected:", expected)
    sys.stdout.flush()
print("\n%d of %d equations: the seeds placed are those expected" % (n_ok, len(F.PROBS)))
