import numpy as np
from gp_elite import symbolic_regression

rng = np.random.RandomState(0)
X = rng.uniform(1, 5, (200, 2))
y = 2.0 + 3.0 * np.sqrt(X[:, 0]) - 0.5 * X[:, 1]

if __name__ == "__main__":        # needed in scripts, see the note below
    result = symbolic_regression(
        X, y,
        feature_names=["a", "b"],
        operators="physical",     # 'physical' | 'trig' | 'full' | 'poly' | 'conserve'
        generations=60,
        speed="fast",             # 'ultrafast' | 'fast' | 'normal' | 'thorough'
        seed=0,
        parallel=False,           # the same model on every machine, see below
    )
    print(result.expression)      # 2 + 3 * sqrt(a) - 0.5 * b
    print(result.r2_validation)   # 1.0
    print(result.size)            # 33 (nodes of the engine's tree)
    print(result.sympy())         # the same formula, parsable by sympy
