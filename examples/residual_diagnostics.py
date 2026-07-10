"""Residual diagnostics [v0.3] — a high R² is not enough.

Same idea a statistician applies by hand: after fitting, look at the residuals.
If they still contain structure, the formula is suspect even at R²=0.999.

Run: python examples/residual_diagnostics.py
"""
import numpy as np
from gp_elite import symbolic_regression


def main():
    rng = np.random.RandomState(0)

    # A clean exponential: residuals should be pure noise.
    x = rng.uniform(0, 3, 200)
    y = 0.3 * np.exp(1.2 * x) + rng.normal(0, 0.01, 200)
    r = symbolic_regression(x.reshape(-1, 1), y, feature_names=["x"],
                            operators="physical", generations=25,
                            speed="fast", seed=0, restarts=4)
    print("Model:", r.expression)
    print(f"R² validation: {r.r2_validation:.6f}\n")
    r.diagnostics(x.reshape(-1, 1), y)

    print("\nTip: for time-series data, add ordered=True to enable the")
    print("Durbin-Watson autocorrelation check.")


if __name__ == "__main__":
    main()
