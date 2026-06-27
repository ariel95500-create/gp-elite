"""
Robust symbolic regression — finding the true law despite outliers.

Real-world data has outliers: faulty sensors, data-entry errors, glitches.
Ordinary least-squares (MSE) regression is dominated by them — a handful of
bad points drags the fitted curve away from the real trend. GP_ELITE's
`robust=True` mode fits the coefficients with a Huber criterion (via iteratively
reweighted least squares), so outliers get down-weighted and the engine
recovers the genuine relationship.

This is something most symbolic-regression libraries don't expose in one switch.

WHAT THIS SHOWS:
  Ground-truth law: y = 2x + 1, with light Gaussian noise, then a fraction of
  points corrupted into large outliers. We measure how well each mode recovers
  the TRUE law (RMSE on the clean points only, vs the ground truth).

  - 0% outliers : ordinary MSE is (slightly) better — robustness has a small
    cost when there's nothing to be robust against. Expected.
  - 10-20% outliers : MSE derails; robust mode stays close to y = 2x + 1.

HONEST NOTE:
  Robustness trades a little efficiency on clean data for large gains on dirty
  data. Use `robust=True` when you suspect outliers, not by default. The fitted
  expression may look bushy (the coefficient scaling is materialised into the
  tree), but predict() gives the right values.

Requires: pip install gp-elite
Usage:    python examples/robust_regression.py
"""
import numpy as np
from gp_elite import symbolic_regression


def make_data(outlier_frac, seed=42):
    """y = 2x + 1 + light noise, with a fraction of large outliers injected."""
    rng = np.random.RandomState(seed)
    n = 80
    x = np.linspace(0, 10, n)
    y_true = 2.0 * x + 1.0
    y = y_true + rng.normal(0, 0.5, n)
    if outlier_frac > 0:
        n_out = int(outlier_frac * n)
        idx = rng.choice(n, n_out, replace=False)
        y[idx] += rng.choice([-1, 1], n_out) * rng.uniform(15, 30, n_out)
        clean = np.setdiff1d(np.arange(n), idx)
    else:
        clean = np.arange(n)
    return x.reshape(-1, 1), y, y_true, clean


def best_rmse(X, y, y_true, clean, robust, n_starts=3):
    """Best (over a few starts) RMSE vs the TRUE law on the clean points."""
    best = np.inf
    for s in range(n_starts):
        r = symbolic_regression(
            X, y, feature_names=["x"], operators="poly",
            generations=35, speed="fast", validation_split=0.0,
            seed=s, robust=robust,
        )
        p = r.predict(X)
        rmse = np.sqrt(np.mean((p[clean] - y_true[clean]) ** 2))
        best = min(best, rmse)
    return best


def main():
    print("Recovering y = 2x + 1 from data with outliers")
    print("(RMSE vs the TRUE law on clean points — lower is better)\n")
    print(f"  {'outliers':>9} | {'MSE (normal)':>12} | {'robust=True':>12} | winner")
    print("  " + "-" * 52)
    for frac in [0.0, 0.10, 0.20]:
        X, y, y_true, clean = make_data(frac)
        rmse_normal = best_rmse(X, y, y_true, clean, robust=False)
        rmse_robust = best_rmse(X, y, y_true, clean, robust=True)
        winner = ("robust" if rmse_robust < rmse_normal else
                  "normal" if rmse_normal < rmse_robust else "tie")
        print(f"  {int(frac*100):>8}% | {rmse_normal:>12.3f} | {rmse_robust:>12.3f} | {winner}")
    print("\n  → With clean data, ordinary MSE wins by a hair (robustness isn't free).")
    print("  → With 10-20% outliers, robust mode recovers the true law; MSE derails.")
    print("  → Use robust=True when you suspect your data is dirty.")


if __name__ == "__main__":
    main()
