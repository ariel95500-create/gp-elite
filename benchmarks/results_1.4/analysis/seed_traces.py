"""Two traces of the seed stage of gp-elite 1.3.0 (the package installed in
the Python that runs this script), each a fit of ONE generation called as
its bench calls it. They read what the seed finders return; they are not
measurements of the engine.

1. Feynman III.15.12, 2*U*(1 - cos(k*d)), with 1 % and 10 % noise: the form
   the trigonometric finder returns with its threshold lifted, and the best
   form over every argument g of its library, scored as the noise-tolerant
   stage scores a seed (1 - R² after linear scaling).
2. Five tables of the TP diagnostic: the seeds placed.

  python seed_traces.py > seed_traces.txt     (from any folder)
"""
import io
import itertools
import os
import sys
import warnings
from contextlib import redirect_stdout

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))
with redirect_stdout(io.StringIO()):
    import feynman_bench as F
    import phase1_bench as B
    import tp_diagnostic as T
    import gp_elite
    import gp_elite.core as C
    from gp_elite import symbolic_regression

EXPS = (-2, -1, -0.5, 0, 0.5, 1, 2)
LOG = []
ORIG = C._elem_trig_forms


def traced(X, y, cols, tol=C._BINOM_TOL):
    out = ORIG(X, y, cols, tol=tol)
    info = dict(tol=tol, n=len(y), returned=[(f[1], f[2], round(f[3], 3)) for f in out])
    if tol >= 1.0:
        n = len(y)
        sub = np.unique(np.linspace(0, n - 1, min(n, C._BINOM_GRID_ROWS)).astype(int))
        glib = [((j, 1),) for j in range(X.shape[1])]
        for j, k in itertools.combinations(cols, 2):
            for e1, e2 in ((1, 1), (1, -1), (-1, 1)):
                glib.append(((j, e1), (k, e2)))
        rows = []
        for g in glib:
            gv = C._elem_mono(X, g)
            gmax = float(np.max(np.abs(gv)))
            gn = gv / gmax
            others = [j for j in cols if j not in {j for j, _ in g}]
            for ex in itertools.product(EXPS, repeat=len(others)):
                fv = np.ones(n)
                for j, e in zip(others, ex):
                    fv = fv * X[:, j] ** e
                with np.errstate(all="ignore"):
                    val, w, cf = C._elem_trig_exact(y / fv, gn, sub)
                if w is None or not np.isfinite(val):
                    continue
                A = np.column_stack([np.ones(n), np.sin(w * gn), np.cos(w * gn)])
                pred = fv * (A @ cf)
                a = np.column_stack([np.ones(n), pred])
                co = np.linalg.lstsq(a, y, rcond=None)[0]
                rows.append((float(np.mean((y - a @ co) ** 2) / np.var(y)), g, ex))
        rows.sort(key=lambda r: r[0])
        info["best"] = rows[:2]
    LOG.append(info)
    return out


def fit(X, y, **kw):
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return symbolic_regression(X, y, generations=1, parallel=False,
                                   verbose=False, **kw)


def main():
    print("gp-elite %s, %s" % (gp_elite.__version__, gp_elite.__file__))
    names = [p[0] for p in F.PROBS]
    print("\n1. III.15.12, columns (U, k, d) = (0, 1, 2): the true form has "
          "f = U and g = k*d")
    C._elem_trig_forms = traced
    for kind in ("feyn_n1", "feyn_n10"):
        del LOG[:]
        job = dict(kind=kind, problem="III.15.12", index=names.index("III.15.12"),
                   split="test", seed=0)
        Xtr, ytr, _a, _b, _c, _d, nm, pool, _clean = B._data(job)
        fit(Xtr, ytr, time_limit=30, seed=0, operators=pool, feature_names=nm)
        for i in LOG:
            if i["tol"] >= 1.0:
                print("  %s, %d training rows after the hold-out: the finder "
                      "returns f = %s, g = %s" % (kind, i["n"], i["returned"][0][0],
                                                  i["returned"][0][1]))
                for r, g, ex in i["best"][:1]:
                    print("      best of its library: g = %s, exponents of f %s, "
                          "unexplained share %.2e" % (g, ex, r))
        print("      seeds placed: %s" % str(C.TRACE.value.get("tolerant_seed"))[:230])
    C._elem_trig_forms = ORIG

    print("\n2. tables of the TP diagnostic, plain arm: the seeds placed")
    for key, n, noise, draw in (("pendule", 10, 0.05, 3), ("pendule", 10, 0.02, 0),
                                ("ressort", 10, 0.05, 0), ("lentille", 20, 0.02, 0),
                                ("refroidissement", 20, 0.02, 2)):
        X, y, _yc, _Xg, _yg = T.data(key, n, noise, draw)
        _k, e = T.experiment(key)
        fit(X, y, feature_names=[i[0] for i in e["inputs"]], seed=draw,
            operators=e["pool"])
        tr = C.TRACE.value
        print("  %-16s %d points, %g %%, draw %d: exact seeds %s; noise-tolerant: %s" % (
            key, n, 100 * noise, draw,
            [k for k in ("power_law_seed", "binomial_seed", "elementary_seed") if tr.get(k)],
            str(tr.get("tolerant_seed"))[:150]))


if __name__ == "__main__":
    main()
