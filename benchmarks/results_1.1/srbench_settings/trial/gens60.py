# How long one call of the wrapper takes to run its 60 generations, without time limit.
import io, sys, time, json, warnings
from contextlib import redirect_stdout
import numpy as np
sys.path.insert(0, "/home/user/gp-elite/benchmarks")
import phase1_bench as P
from gp_elite import symbolic_regression
import gp_elite.core as C
for job in json.loads(sys.argv[1]):
    Xtr, ytr, Xte, yte, Xo, yo, names, pool, clean = P._data(job)
    gens = [0]; orig = C.evolve_island
    def counted(*a, **k):
        g = a[3] if len(a) > 3 else k.get("generation", 0); gens[0] = max(gens[0], int(g) + 1); return orig(*a, **k)
    C.evolve_island = counted
    t0 = time.time()
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = symbolic_regression(Xtr, ytr, feature_names=["X%d" % i for i in range(Xtr.shape[1])], operators="physical",
                                generations=60, speed="fast", restarts=1, parallel=False, seed=0)
    C.evolve_island = orig
    print(job["kind"], job["problem"], job["split"], "rows", len(ytr), "generations", gens[0], "%.1f s" % (time.time() - t0), flush=True)
