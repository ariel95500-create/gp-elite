# -*- coding: utf-8 -*-
"""Mechanics of N2, item 1 (benchmarks/results_1.4/PLAN.md): the exact seed
finders are untouched. Dumps, with full precision, what the finders of the
engine on sys.path return on a set of tables, called as 1.3.0 calls them:

  - with their exact thresholds (the exact seeds);
  - with the thresholds lifted (the first pass of the noise-tolerant stage,
    the one 1.3.0 runs).

Run once with 1.3.0 from PyPI and once with the candidate; the two dumps
must be the same file, byte for byte (compare_dumps.sh).

  python -I finders_dump.py ENGINE_DIR OUT     (ENGINE_DIR first on sys.path;
                                                 a missing folder: the
                                                 installed gp_elite)

Tables: the training rows of F41 without noise and with 1 % and 10 % noise
(123), the tables of the TP diagnostic at draws 0 to 4 (200), and the real
data of R7raw at fold 0 (7). The frozen test sets are not used. Each table
is used raw and with each column divided by its largest |value|, as the
engine scales it.
"""
import io
import os
import sys
from contextlib import redirect_stdout

import numpy as np

sys.path.insert(0, sys.argv[1])
BENCH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "..", "..", ".."))
sys.path.insert(1, BENCH)
with redirect_stdout(io.StringIO()):
    import gp_elite
    import gp_elite.core as C
    import decision_bench as D
    import feynman_bench as F
    import phase1_bench as B
    import tp_diagnostic as T

KINDS = ["exp", "log", "tanh", "sech", "trig", "arcsin"]


def tables():
    names = [p[0] for p in F.PROBS]
    for kind in ("feyn", "feyn_n1", "feyn_n10"):
        for i, p in enumerate(names):
            job = dict(kind=kind, problem=p, index=i, split="test", seed=0)
            d = B._data(job)
            yield "%s %s" % (kind, p), d[0], d[1]
    for e in T.EXPERIMENTS:
        for n in T.SIZES:
            for nz in T.NOISES:
                for dr in range(5):
                    X, y, _yc, _xg, _yg = T.data(e["key"], n, nz, dr)
                    yield "tp %s %d %g %d" % (e["key"], n, nz, dr), X, y
    for nm in D.REAL_RAW:
        d = B._data(dict(kind="realraw", problem=nm, split="fold0", seed=0))
        yield "realraw %s" % nm, d[0], d[1]


def show(v):
    return repr(v)


def main():
    out = open(sys.argv[2], "w", encoding="utf-8")
    out.write("# finders of %s\n" % ("1.3.0" if "site-packages" in gp_elite.__file__
                                     else "the candidate"))
    n = 0
    for label, X, y in tables():
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        for scaled in (False, True):
            Xs = X / np.abs(X).max(axis=0) if scaled else X
            tag = "%s %s" % (label, "scaled" if scaled else "raw")
            with np.errstate(all="ignore"):
                for name, call in (
                        ("power", lambda: C._power_law_exponents(Xs, y)),
                        ("power tol", lambda: C._power_law_exponents(Xs, y, -np.inf)),
                        ("binom", lambda: C._binomial_forms(Xs, y)),
                        ("binom tol", lambda: C._binomial_forms(Xs, y, tol=1.0)),
                        ("elem", lambda: C._elementary_forms(Xs, y, KINDS)),
                        ("elem tol", lambda: C._elementary_forms(Xs, y, KINDS, tol=1.0))):
                    try:
                        res = call()
                    except Exception as exc:          # recorded, never hidden
                        res = "EXCEPTION %r" % exc
                    if isinstance(res, tuple):
                        res = (res[0], [float(a) for a in res[1]])
                    out.write("%s | %s | %s\n" % (tag, name, show(res)))
                    n += 1
    out.write("# %d calls\n" % n)
    out.close()
    print("%d calls written to %s" % (n, sys.argv[2]))


if __name__ == "__main__":
    main()
