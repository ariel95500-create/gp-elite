"""Outside the engine's search: on the noisy training rows of F41 (1 % and
10 %), the seeds of the power law, B1 and E1 with their thresholds lifted:
relative error of each seed after linear scaling, and whether its structure
is the law's (constants refitted on the clean targets, clean test rows)."""
import io, json, sys
from contextlib import redirect_stdout
import numpy as np
sys.path.insert(0, "/home/user/gp-elite/benchmarks")
import gp_elite.core as C
import phase1_bench as P, decision_bench as D, feynman_bench as F

def rel(tree, Xs, y):
    with np.errstate(all="ignore"):
        p = np.asarray(C.evaluate_vector(tree, Xs), dtype=float)
    if not np.all(np.isfinite(p)) or np.var(p) == 0:
        return np.inf
    A = np.column_stack([np.ones_like(p), p]); c = np.linalg.lstsq(A, y, rcond=None)[0]
    return float(np.mean((y - A @ c) ** 2) / np.var(y))

def struct(tree, xs_tr, yc, xs_te, yte, cfg):
    try:
        with redirect_stdout(io.StringIO()), np.errstate(all="ignore"):
            f = C._lm_to_convergence(tree.copy(), xs_tr, yc, cfg)
            t = C._refit_scaling(f if f is not None else tree.copy(), xs_tr, yc)
            p = np.asarray(C.evaluate_vector(t, xs_te), dtype=float)
        return bool(D.one_minus_r2(yte, p) < 1e-9)
    except Exception:
        return False

out = []
for kind in ("feyn_n1", "feyn_n10"):
    for i, p in enumerate(F.PROBS):
        job = dict(kind=kind, problem=p[0], index=i, split="test", seed=0)
        Xtr, ytr, Xte, yte, Xo, yo, names, pool, clean = P._data(job)
        m = np.max(np.abs(Xtr), axis=0); m[m == 0] = 1
        Xs, Xt = Xtr / m, Xte / m
        b_ops, _, u_ops, _ = C._GENCSV_POOLS[pool]
        C._GENERIC_CSV_MODE = True
        C._GENERIC_BINARY_OPS, C._GENERIC_UNARY_OPS = list(b_ops), list(u_ops)
        cfg = C.Config(); cfg.TERMINALS = ["X[%d]" % k for k in range(Xs.shape[1])]
        cfg2 = C.make_cfg_nd(n_features=Xs.shape[1])
        rec = dict(kind=kind, problem=p[0], family=p[6] if len(p) > 6 else "historique")
        C._BINOM_TOL = 1.0
        for name, fn in (("power", C._make_power_law_seeds), ("binomial", C._make_binomial_seeds),
                         ("elementary", C._make_elementary_seeds)):
            try:
                seeds = fn(Xs, ytr, cfg)
            except Exception:
                seeds = []
            res = [(rel(t, Xs, ytr), struct(t, Xs, np.asarray(clean, float), Xt, yte, cfg2)) for t in seeds]
            rec[name] = res
        C._BINOM_TOL = 1e-12
        out.append(rec)
        print(json.dumps(rec), flush=True)
