# -*- coding: utf-8 -*-
"""Beside M1 of the release of 1.4.0, deciding nothing: the noise-tolerant
seeds of C_big, the one configuration of benchmarks/speed_equivalence.py
whose record differs between 1.3.0 and 1.4.0 (in its Pareto front only).

The release README says that, read on a trace, 1.4.0 places twelve
noise-tolerant seeds there, the six of 1.3.0 among them, where 1.3.0 places
six; that trace was not kept. This script records it: it builds the data of
C_big as speed_equivalence.data("big") does (5,000 rows of x0·x1/x2 with
Gaussian noise of 0.05), runs the fit of C_big for one generation, in
sequence so that the seeds are placed in this process, and records each call
of the noise-tolerant stage with the forms it places.

  PYTHONHASHSEED=0 /venv13p/bin/python -I cbig_seeds.py OUT_1.3.0.json
  PYTHONHASHSEED=0 /venv14r/bin/python -I cbig_seeds.py OUT_1.4.0.json
"""
import contextlib
import io
import json
import os
import sys
import warnings

import numpy as np


def main(out):
    import gp_elite
    import gp_elite.core as C
    from gp_elite import symbolic_regression
    calls = []
    orig = C._make_tolerant_seeds

    def wrapped(*a, **kw):
        seeds = orig(*a, **kw)
        calls.append([C.to_string(t) for t in seeds])
        return seeds
    C._make_tolerant_seeds = wrapped
    r = np.random.RandomState(0)                  # speed_equivalence.data("big")
    X = r.uniform(1, 4, (5000, 3))
    y = X[:, 0] * X[:, 1] / X[:, 2] + 0.05 * r.randn(5000)
    with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        symbolic_regression(X, y, generations=1, seed=0, verbose=False, parallel=False)
    rec = dict(config="C_big", engine=gp_elite.__version__, engine_file=gp_elite.__file__,
               pythonhashseed=os.environ.get("PYTHONHASHSEED"),
               tolerant_calls=len(calls), seeds_per_call=[len(c) for c in calls],
               seeds=calls)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(rec["engine"], "calls", rec["tolerant_calls"], "seeds", rec["seeds_per_call"])


if __name__ == "__main__":
    main(sys.argv[1])
