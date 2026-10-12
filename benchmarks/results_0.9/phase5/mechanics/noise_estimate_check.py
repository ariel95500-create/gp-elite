import sys, numpy as np
sys.path.insert(0, "/home/user/gp-elite/benchmarks")
import phase1_bench as P, decision_bench as D, feynman_bench as F

def noise_rel(X, y, k=None):
    """Local linear pseudo-residuals: each y_i against the linear fit of its k
    nearest neighbours (inputs scaled to [0,1] per column); estimate of the
    noise variance relative to var(y)."""
    X = np.asarray(X, float); y = np.asarray(y, float)
    n, d = X.shape
    lo, hi = X.min(0), X.max(0); Z = (X - lo) / np.where(hi > lo, hi - lo, 1)
    k = k or (2 * d + 4)
    D2 = ((Z[:, None, :] - Z[None, :, :]) ** 2).sum(-1); np.fill_diagonal(D2, np.inf)
    r = []
    for i in range(n):
        nb = np.argsort(D2[i])[:k]
        A = np.column_stack([np.ones(k), Z[nb] - Z[i]])
        c, *_ = np.linalg.lstsq(A, y[nb], rcond=None)
        # prediction at Z[i] is c[0]; variance inflation of the prediction
        h = np.linalg.pinv(A.T @ A)[0, 0]
        r.append((y[i] - c[0]) ** 2 / (1.0 + h))
    return float(np.mean(r) / np.var(y))

print("noisy F41 (median over equations):")
for kind in ("feyn_n1", "feyn_n10"):
    v = []
    for i, p in enumerate(F.PROBS):
        Xtr, ytr, *_ = P._data(dict(kind=kind, problem=p[0], index=i, split="test", seed=0))
        v.append(noise_rel(Xtr, ytr))
    print("  %s: quartiles %s" % (kind, np.round(np.percentile(v, [10, 25, 50, 75, 90]), 6)))
print("exact F41 with tolerant seeds and the rest:")
v = {}
for i, p in enumerate(F.PROBS):
    Xtr, ytr, *_ = D.feyn_data(i)
    v[p[0]] = noise_rel(Xtr, ytr)
print("  I.16.6 %.2e  I.26.2 %.2e  I.37.4 %.2e ; all F41 quartiles %s" % (
    v["I.16.6"], v["I.26.2"], v["I.37.4"], np.round(np.percentile(list(v.values()), [10, 25, 50, 75, 90]), 6)))
r = np.random.RandomState(5); a = r.uniform(0.3, 30, 60)
print("  Kepler (60 rows): %.2e" % noise_rel(a.reshape(-1, 1), a ** 1.5))
r = np.random.RandomState(0); X = r.uniform(1, 4, (5000, 3)); y = X[:, 0] * X[:, 1] / X[:, 2] + 0.05 * r.randn(5000)
print("  C_big (first 500 rows; true noise rel %.2e): %.2e" % (0.0025 / np.var(y), noise_rel(X[:500], y[:500])))
