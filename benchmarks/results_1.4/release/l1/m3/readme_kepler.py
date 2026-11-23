import numpy as np
from gp_elite import symbolic_regression

a = np.array([0.387, 0.723, 1.000, 1.524, 5.203, 9.537, 19.191, 30.069])   # AU
T = np.array([0.241, 0.615, 1.000, 1.881, 11.862, 29.457, 84.011, 164.79])  # years

result = symbolic_regression(a.reshape(-1, 1), T, feature_names=["a"], generations=40, seed=0)
print(result.expression)     # 0.00279171 + 0.999396 * a * sqrt(a)
print(result.formula_exact)
