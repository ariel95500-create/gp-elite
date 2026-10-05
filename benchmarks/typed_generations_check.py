"""Typed search on Feynman II.11.3: how many generations does a run go through?

Diagnostic D2 of benchmarks/results_0.8 (PLAN.md, RESULTS.md). Runs the typed
arm of ab_ood.py (units=, 40 generations, one restart, speed='fast') for one
seed, with the generation counter of decision_bench.py (the last generation
index passed to evolve_island), and prints one JSON record: time, generations
reached, time per generation, size, test and out-of-domain R².

Usage (PYTHONPATH selects the engine; one process per fit):
    PYTHONHASHSEED=0 PYTHONPATH=<engine> python benchmarks/typed_generations_check.py <seed>
With --verbose, the engine prints its progress, and why it stopped, before the
record.
"""
import io, json, os, sys, time, warnings
from contextlib import redirect_stdout
import numpy as np
sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))   # ab_ood data functions only
import ab_ood
import gp_elite
import gp_elite.core as C
from gp_elite import GPEliteRegressor

VERBOSE = "--verbose" in sys.argv
if VERBOSE:                       # the estimator has no verbose option of its own
    import functools
    import gp_elite.sklearn_api as SK
    SK.symbolic_regression = functools.partial(SK.symbolic_regression, verbose=True)
seed = int([a for a in sys.argv[1:] if a != "--verbose"][0])
gens = [0]; calls = [0]
orig = C.evolve_island
def counted(*args, **kwargs):
    g = args[3] if len(args) > 3 else kwargs.get("generation", 0)
    gens[0] = max(gens[0], int(g) + 1); calls[0] += 1
    return orig(*args, **kwargs)
C.evolve_island = counted

Xtr, ytr = ab_ood.make_data(200, seed)
Xte, yte = ab_ood.make_data(200, seed + 5000)
Xod, yod = ab_ood.make_data_ood(200, seed + 9000)
kw = dict(operators="physical", generations=40, speed="fast", restarts=1,
          random_state=seed, units=ab_ood.UNITS, target_units=ab_ood.TARGET)
t0 = time.time()
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    est = GPEliteRegressor(**kw)
    if VERBOSE:
        est.fit(Xtr, ytr)
    else:
        with redirect_stdout(io.StringIO()):
            est.fit(Xtr, ytr)
dt = time.time() - t0
with np.errstate(all="ignore"):
    r2t = ab_ood._r2(yte, est.predict(Xte)); r2o = ab_ood._r2(yod, est.predict(Xod))
print(json.dumps(dict(engine=gp_elite.__file__, version=gp_elite.__version__, seed=seed,
                      seconds=round(dt, 1), generations_reached=gens[0], island_calls=calls[0],
                      sec_per_gen=round(dt / max(gens[0], 1), 2), size=int(est.model_.size),
                      r2_test=round(r2t, 6), r2_ood=round(r2o, 6))))
