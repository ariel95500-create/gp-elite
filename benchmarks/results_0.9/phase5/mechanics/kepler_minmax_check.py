"""Outside any measurement (PLAN_PHASE5.md, mechanics of N1): the reference
configuration E_minmax (Kepler a^1.5, normalize="minmax", pool "full"), where
a tolerant seed changed the model, fitted with N1 off and on, seeds 0 to 9,
10 and 40 generations: is the exact law lost systematically?"""
import io, sys, warnings
from contextlib import redirect_stdout
import numpy as np
import gp_elite.core as C
from gp_elite import symbolic_regression
r = np.random.RandomState(5)
a = r.uniform(0.3, 30, 60)
X, y = a.reshape(-1, 1), a ** 1.5
for gens in (10, 40):
    for flag in (False, True):
        C._TOLERANT_SEEDS = flag
        exact = 0
        for seed in range(10):
            with redirect_stdout(io.StringIO()), warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = symbolic_regression(X, y, generations=gens, seed=seed, normalize="minmax",
                                          operators="full", parallel=False, verbose=False)
            p = res.predict(X)
            exact += bool(np.var(y - p) / np.var(y) < 1e-9)
        print("generations %d, N1 %s: exact law in %d of 10" % (gens, "on " if flag else "off", exact), flush=True)
