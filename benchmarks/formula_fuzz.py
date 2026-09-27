"""Random-tree check of the delivered formula (gp_elite/formula.py).

1,500 random expression trees (1 to 3 variables, the four normalisations,
signed and positive data). For every tree whose formula is reported exact,
the sympy() string is parsed by sympy, evaluated on the raw data and compared
with predict(). The others are the trees where a numerical safety net of the
engine acts on the data; they are reported inexact (formula_exact False).

    PYTHONHASHSEED=0 python benchmarks/formula_fuzz.py

Result on 0.7.0: 1,448 exact, 52 inexact, 0 sympy mismatch among the exact.
"""
import numpy as np, random, sympy as sp, sys
from gp_elite import core, formula as F
N = core.Node
UN = ["neg","abs","sq","cube","sqrt","log","exp","sin","cos","tanh"]
BI = ["+","-","*","/","pow"]
def rand_tree(rng, nf, depth):
    if depth == 0 or rng.random() < 0.25:
        if rng.random() < 0.6: return N("X[%d]" % rng.randrange(nf))
        return N(float(np.round(rng.uniform(-3, 3), 3)))
    if rng.random() < 0.35:
        return N(rng.choice(UN), rand_tree(rng, nf, depth-1))
    op = rng.choice(BI)
    if op == "pow":
        e = rng.choice([2.0, 3.0, -1.0, 0.5, 1.5, -2.0, 0.0])
        return N("pow", rand_tree(rng, nf, depth-1), N(e) if rng.random() < 0.85 else rand_tree(rng, nf, 1))
    return N(op, rand_tree(rng, nf, depth-1), rand_tree(rng, nf, depth-1))
from sklearn.preprocessing import MinMaxScaler, StandardScaler
def scaler_of(kind):
    return {"divmax": core._ShiftFreeScaler(), "minmax": MinMaxScaler(feature_range=(-2,2)),
            "standard": StandardScaler(), "none": core._IdentityScaler()}[kind]
rng = random.Random(1); nrng = np.random.RandomState(1)
stats = {}
bad = []
for trial in range(1500):
    nf = rng.choice([1,2,3])
    kind = rng.choice(["divmax","minmax","standard","none"])
    signed = rng.random() < 0.5
    X = nrng.uniform(-4 if signed else 0.5, 5, (80, nf))
    if kind == "divmax" and signed and rng.random()<0.5: pass
    sc = scaler_of(kind); Xs = sc.fit_transform(X)
    t = rand_tree(rng, nf, rng.choice([2,3,4]))
    p = core.evaluate_vector(t, Xs)
    rf = F.raw_formula(t, sc, X, ["a","b","c"][:nf])
    key = (kind, rf.exact, rf.folded)
    stats[key] = stats.get(key, 0) + 1
    # independent check of the sympy string (only where the formula claims exactness)
    if rf.exact:
        s = rf.sympy()
        e = sp.sympify(s, locals={n: sp.Symbol(n) for n in ["a","b","c"]})
        syms = [sp.Symbol(n) for n in ["a","b","c"][:nf]]
        f = sp.lambdify(syms, e, [{"Heaviside": lambda x, h=0: np.heaviside(x, h)}, "numpy"])
        with np.errstate(all="ignore"):
            v = np.asarray(f(*[X[:, i] for i in range(nf)]), dtype=complex) * np.ones(len(X))
        scale = max(np.max(np.abs(p)), np.std(p), 1e-300)
        err = np.max(np.abs(v - p))
        if not (err <= 1e-6 * scale):
            bad.append((kind, core.to_string(t), s[:200], err, scale))
print(stats)
print("exact:", sum(v for k, v in stats.items() if k[1]),
      "inexact:", sum(v for k, v in stats.items() if not k[1]))
print("sympy mismatches among exact:", len(bad))
for b in bad[:8]: print(b)
