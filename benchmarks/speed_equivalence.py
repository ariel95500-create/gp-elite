"""Do two engines return the same model, bit for bit, at equal seed and work?

The speed work of 0.8 (block lexicase, incremental Jacobian, interpreted
trees, frozen sampling tables, cheaper operators and copies) must not change
a single result. This script runs thirteen reference configurations (Feynman
data, a real dataset, 5,000 rows, units, min-max and z-score normalisation,
robust loss, restarts, parallel islands, the scikit-learn estimator,
extrapolation mode, the thorough preset, and the same fit twice in one
process), each in its own process, and records the exact returned model:
the tree with its constants in float.hex, the printed expression, the MSEs,
the size, formula_exact and the Pareto front. Two engines are then compared
field by field (everything but the time).

Usage (PYTHONPATH selects the engine; PYTHONHASHSEED=0):
    PYTHONHASHSEED=0 PYTHONPATH=<engine A> python benchmarks/speed_equivalence.py run <dirA>
    PYTHONHASHSEED=0 PYTHONPATH=<engine B> python benchmarks/speed_equivalence.py run <dirB>
    python benchmarks/speed_equivalence.py compare <dirA> <dirB>
"""
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CONFIGS = {
    # name: (data, fit arguments)
    "A_feyn": ("feyn", dict(generations=12, seed=0)),
    "B_cpu": ("cpu", dict(generations=12, seed=1)),
    "C_big": ("big", dict(generations=5, seed=0)),
    "D_units": ("feyn", dict(generations=10, seed=2, units=True)),
    "E_minmax": ("kepler", dict(generations=10, seed=3, normalize="minmax",
                                operators="full")),
    "F_robust": ("outliers", dict(generations=10, seed=4, robust=True)),
    "G_restarts": ("signed", dict(generations=6, seed=5, restarts=2,
                                  speed="ultrafast")),
    "H_parallel": ("feyn", dict(generations=6, seed=6, parallel=True)),
    "I_sklearn": ("signed", "estimator"),
    "J_extrap": ("kepler", dict(generations=8, seed=8, extrapolate=True)),
    "K_thorough": ("feyn", dict(generations=4, seed=9, speed="thorough")),
    "L_standard": ("signed", dict(generations=8, seed=10, normalize="standard",
                                  operators="trig")),
    "M_twice": ("signed", "twice"),
}


def data(kind):
    if kind == "feyn":            # I.12.2, q1 q2 / (4 pi eps r^2)
        r = np.random.RandomState(1011)
        X = np.c_[r.uniform(1, 5, 200), r.uniform(1, 5, 200),
                  r.uniform(1, 3, 200), r.uniform(1, 3, 200)]
        y = X[:, 0] * X[:, 1] / (4 * np.pi * X[:, 2] * X[:, 3] ** 2)
        return X[:140], y[:140]
    if kind == "cpu":
        import pmlb_frozen
        from sklearn.preprocessing import StandardScaler
        X, y = pmlb_frozen.load("561_cpu")
        return (StandardScaler().fit_transform(X),
                StandardScaler().fit_transform(y.reshape(-1, 1)).ravel())
    if kind == "big":
        r = np.random.RandomState(0)
        X = r.uniform(1, 4, (5000, 3))
        return X, X[:, 0] * X[:, 1] / X[:, 2] + 0.05 * r.randn(5000)
    if kind == "kepler":
        r = np.random.RandomState(5)
        a = r.uniform(0.3, 30, 60)
        return a.reshape(-1, 1), a ** 1.5
    if kind == "signed":
        r = np.random.RandomState(9)
        X = r.uniform(-3, 3, (150, 2))
        return X, X[:, 0] * X[:, 1] ** 2 - 0.5 * X[:, 0]
    if kind == "outliers":
        r = np.random.RandomState(3)
        X = r.uniform(0, 5, (120, 2))
        y = 2.0 * X[:, 0] + np.sin(X[:, 1])
        y[r.choice(120, 12, replace=False)] += 25.0
        return X, y
    raise KeyError(kind)


def ser(node):
    """Exact prefix serialisation of a tree (constants in float.hex)."""
    out, stack = [], [node]
    while stack:
        nd = stack.pop()
        if nd is None:
            out.append("_")
            continue
        v = nd.value
        out.append(float(v).hex() if isinstance(v, float) else str(v))
        if nd.left is not None or nd.right is not None:
            stack.append(nd.right)
            stack.append(nd.left)
    return " ".join(out)


def hx(v):
    return None if v is None else float(v).hex()


def one(name, out):
    kind, kw = CONFIGS[name]
    X, y = data(kind)
    t0 = time.time()
    if kw == "twice":
        from gp_elite import symbolic_regression
        kw2 = dict(generations=6, seed=12, robust=False)
        r0 = symbolic_regression(X, y, verbose=False, **kw2)
        r = symbolic_regression(X, y, verbose=False, **kw2)
        assert ser(r0.node) == ser(r.node), "two identical fits differ"
    elif kw == "estimator":
        from gp_elite import GPEliteRegressor
        est = GPEliteRegressor(generations=8, random_state=7)
        est.fit(X, y)
        r = est.model_
    else:
        from gp_elite import symbolic_regression
        kw = dict(kw)
        if kw.pop("units", False):
            charge = {"A": 1, "s": 1}
            eps0 = {"A": 2, "s": 4, "kg": -1, "m": -3}
            kw["units"] = [charge, charge, eps0, {"m": 1}]
            kw["target_units"] = {"kg": 1, "m": 1, "s": -2}
        r = symbolic_regression(X, y, verbose=False, **kw)
    rec = dict(config=name, time_s=round(time.time() - t0, 3), node=ser(r.node),
               expression=r.expression, mse_validation=hx(r.mse_validation),
               mse_train=hx(r.mse_train), size=r.size,
               formula_exact=r.formula_exact,
               pareto=[[p.size, ser(p.node), hx(p.mse_validation)]
                       for p in (r.pareto or [])])
    with open(out, "w") as fh:
        fh.write(json.dumps(rec) + "\n")


def run(outdir):
    os.makedirs(outdir, exist_ok=True)
    for name in CONFIGS:
        p = subprocess.run([sys.executable, os.path.abspath(__file__), "one", name,
                            os.path.join(outdir, name + ".json")],
                           capture_output=True, text=True,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        print("%-12s %s" % (name, "ok" if p.returncode == 0 else
                            "FAILED " + p.stderr[-300:]), flush=True)


def compare(a, b):
    same_all = True
    ta = tb = 0.0
    for name in CONFIGS:
        ra = json.load(open(os.path.join(a, name + ".json")))
        rb = json.load(open(os.path.join(b, name + ".json")))
        ta += ra.pop("time_s")
        tb += rb.pop("time_s")
        diff = [k for k in ra if ra.get(k) != rb.get(k)]
        print("%-12s %s" % (name, "same" if not diff else "DIFFERENT: %s" % diff))
        same_all &= not diff
    print("total time %.1f s -> %.1f s" % (ta, tb))
    print("ALL IDENTICAL" if same_all else "DIFFERENCES")
    return same_all


if __name__ == "__main__":
    if sys.argv[1] == "one":
        one(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "run":
        run(sys.argv[2])
    elif sys.argv[1] == "compare":
        sys.exit(0 if compare(sys.argv[2], sys.argv[3]) else 1)
