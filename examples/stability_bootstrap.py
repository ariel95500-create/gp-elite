"""Structural stability under resampling [v0.3].

Answers the honest question raised at launch: "resample the data and do you
get the same formula?" It refits on bootstrap resamples and reports how often
each structural form recurs, alongside the median fit quality — so you can
tell a real law from noise being read.

Run: python examples/stability_bootstrap.py   (takes a couple of minutes)
"""
import numpy as np
from gp_elite import stability_analysis


def main():
    rng = np.random.RandomState(0)
    x = rng.uniform(1, 5, 80)
    y_true = 2.0 * x ** 1.5

    print("=== Clean data (1% noise) ===")
    stability_analysis(x.reshape(-1, 1), y_true + rng.normal(0, 0.01 * y_true.mean(), 80),
                       feature_names=["x"], operators="physical",
                       n_bootstrap=8, generations=20, speed="fast", seed=0)

    print("\n=== Noisy data (60% noise) ===")
    stability_analysis(x.reshape(-1, 1), y_true + rng.normal(0, 0.60 * y_true.mean(), 80),
                       feature_names=["x"], operators="physical",
                       n_bootstrap=8, generations=20, speed="fast", seed=0)

    print("\nReading it: high recurrence + high R² = trust the form.")
    print("Low recurrence + high R² = several valid forms (pick by parsimony).")
    print("Low R² = signal too weak, don't trust any form.")


if __name__ == "__main__":
    main()
