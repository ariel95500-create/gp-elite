"""operators= is respected end to end: 48 fits (pools "poly" and "physical",
three laws, with and without units=, four seeds, 10 generations); every
operator of the returned model and of its Pareto front must belong to the
requested pool.

    PYTHONHASHSEED=0 python benchmarks/pools_check.py

Result on 0.7.0: 48 fits, 0 violation.
"""
import numpy as np, gp_elite.core as C
from gp_elite import GPEliteRegressor
def ops_in(t, acc):
    if t.left is not None or t.right is not None:
        acc.add(str(t.value))
        if t.left is not None: ops_in(t.left, acc)
        if t.right is not None: ops_in(t.right, acc)
    return acc
def main():
    r = np.random.RandomState(1)
    probs = {
      "amorti": (r.uniform(1, 3, (150, 2)), lambda X: X[:, 0] * np.exp(-X[:, 1] / 2.0),
                 ["m", "s"], "m"),
      "cinetique": (r.uniform(1, 3, (150, 2)), lambda X: 0.5 * X[:, 0] * X[:, 1] ** 2,
                    ["kg", "m/s"], "J"),
      "pendule": (r.uniform(0.5, 3, (150, 2)), lambda X: 2 * np.pi * np.sqrt(X[:, 0] / X[:, 1]),
                  ["m", "m/s^2"], "s"),
    }
    bad = 0
    for pool in ("poly", "physical"):
        allowed = frozenset(C._GENCSV_POOLS[pool][0]) | frozenset(C._GENCSV_POOLS[pool][2])
        for name, (X, f, u, tu) in probs.items():
            for units in (False, True):
                for seed in (0, 1, 2, 3):
                    kw = dict(units=u, target_units=tu) if units else {}
                    e = GPEliteRegressor(operators=pool, generations=10, random_state=seed, **kw).fit(X, f(X))
                    seen = set()
                    for ent in (e.model_.pareto or []): ops_in(ent.node, seen)
                    ops_in(e.model_.node, seen)
                    extra = seen - allowed
                    bad += bool(extra)
                    if extra:
                        print("  VIOLATION %-8s %-10s units=%s seed=%d : %s" % (pool, name, units, seed, sorted(extra)))
    print("ajustements : 48 | violations :", bad)
if __name__ == "__main__":
    main()
