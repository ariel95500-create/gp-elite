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
  the TRUE law (RMSE on the clean points only, vs the ground truth), over five
  independent seeds, and report the median and the worst seed.

  Every run is judged on the model it returns. (Up to 0.6 this script kept the
  best of three runs by looking at the error against the true law, a choice no
  user can make, and printed its conclusions whatever the numbers said.)

HONEST NOTE:
  Measured on 0.7.0: robust mode cuts the error six-fold at 10 % outliers,
  and does no better than the default at 20 % on this example. It is a tool
  to try when you suspect outliers, not a guarantee.

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


SEEDS = 5


def rmse_per_seed(X, y, y_true, clean, robust):
    """RMSE vs the TRUE law on the clean points, and the returned formula,
    one of each per seed."""
    out, formulas = [], []
    for s in range(SEEDS):
        r = symbolic_regression(
            X, y, feature_names=["x"], operators="poly",
            generations=35, speed="fast", validation_split=0.0,
            seed=s, robust=robust,
        )
        p = r.predict(X)
        out.append(float(np.sqrt(np.mean((p[clean] - y_true[clean]) ** 2))))
        formulas.append(r.expression)
    return np.array(out), formulas


def _distinct(formulas):
    """Each distinct formula with the number of seeds that returned it."""
    seen = {}
    for f in formulas:
        seen[f] = seen.get(f, 0) + 1
    return sorted(seen.items(), key=lambda kv: -kv[1])


def main():
    print("Recovering y = 2x + 1 from data with outliers")
    print("(RMSE vs the TRUE law on clean points, %d seeds: median [worst])\n" % SEEDS)
    print(f"  {'outliers':>9} | {'MSE (default)':>16} | {'robust=True':>16} | lower median")
    print("  " + "-" * 62)
    returned = []
    for frac in [0.0, 0.10, 0.20]:
        X, y, y_true, clean = make_data(frac)
        a, fa = rmse_per_seed(X, y, y_true, clean, robust=False)
        b, fb = rmse_per_seed(X, y, y_true, clean, robust=True)
        ma, mb = np.median(a), np.median(b)
        # a difference invisible at the printed precision is a tie
        winner = ("tie" if round(ma, 3) == round(mb, 3) else
                  "robust" if mb < ma else "default")
        print(f"  {int(frac*100):>8}% | {ma:>7.3f} [{a.max():>6.3f}] | "
              f"{mb:>7.3f} [{b.max():>6.3f}] | {winner}")
        returned.append((frac, fa, fb))
    print("\n  Formulas returned (distinct formulas, with how many of the %d seeds"
          % SEEDS)
    print("  returned each):")
    for frac, fa, fb in returned:
        for label, fs in (("default", fa), ("robust ", fb)):
            for k, (f, n) in enumerate(_distinct(fs)):
                head = f"  {int(frac*100):>4}% {label}" if k == 0 else " " * 15
                print(f"{head}  [{n}/{SEEDS}]  y = {f}")
    print("\n  robust=True changes the loss, not the search: whether it helps")
    print("  depends on the data. Read the table, and compare both modes on a")
    print("  hold-out of your own before trusting either.")


if __name__ == "__main__":
    main()
