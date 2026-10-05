"""
Battery degradation: interpolation vs extrapolation (SIMULATED data).

The data file, nasa_battery_simulation.csv, holds 168 simulated charge cycles
(cycle number, temperature, current, capacity state of health). Its origin is
not documented beyond its name: this is a demonstration of a protocol, not a
result on real batteries.

The point it makes holds for any sequential data: a RANDOM train/test split
leaks information (predicting cycle 49 from cycles 48 and 50 is just
interpolation). The honest task is EXTRAPOLATION: train on early cycles,
predict later ones the model has never seen. GP_ELITE (one equation) is
compared with tree ensembles under both protocols; the conclusions printed
are read from the numbers of the run, not written in advance.

Requires: scikit-learn (a dependency of gp-elite); xgboost optional.
Usage:    python examples/battery_soh.py
"""
import os
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

from gp_elite import symbolic_regression

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "nasa_battery_simulation.csv")


def fit_gp(Xtr, ytr, feat, seed=0):  # seed fixed for reproducibility
    """Fit GP_ELITE. result.predict() takes RAW features: the internal scaling
    learned at fit time is applied automatically. (An earlier version of this
    example also scaled the test data itself, so predictions were computed on
    doubly-scaled inputs and the reported R2 was wrong.)"""
    import random
    random.seed(seed); np.random.seed(seed)
    res = symbolic_regression(
        Xtr, ytr, feature_names=feat,
        operators="physical", normalize="auto",
        generations=60, speed="fast", validation_split=0.0, seed=seed,
        parallel=False,  # deterministic + reproducible for this demo
    )
    return res


def main():
    df = pd.read_csv(CSV)
    feat = ["cycle", "temperature", "courant"]
    X = df[feat].values
    y = df["capacity_SOH"].values
    n = len(y)
    print(f"Battery data (SIMULATED, see README): {n} sequential cycles, target SOH in "
          f"[{y.min():.3f}, {y.max():.3f}]\n")

    # Black-box baselines: RandomForest always (scikit-learn is a dependency),
    # XGBoost if installed.
    from sklearn.ensemble import RandomForestRegressor
    try:
        import xgboost as xgb
    except ImportError:
        xgb = None
        print("(xgboost not installed: RandomForest is the only black-box baseline)\n")

    # ---- Protocol 1: RANDOM split (interpolation — leaks, misleading) ----
    from sklearn.model_selection import train_test_split
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42)
    print("=" * 62)
    print("PROTOCOL 1 — random split (INTERPOLATION, leaks info)")
    print("=" * 62)
    res = fit_gp(Xtr, ytr, feat)
    print(f"  GP_ELITE      R² = {r2_score(yte, res.predict(Xte)):+.3f}")
    rf = RandomForestRegressor(n_estimators=300, random_state=42).fit(Xtr, ytr)
    print(f"  RandomForest  R² = {r2_score(yte, rf.predict(Xte)):+.3f}")
    if xgb is not None:
        m = xgb.XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.05,
                             random_state=42).fit(Xtr, ytr)
        print(f"  XGBoost       R² = {r2_score(yte, m.predict(Xte)):+.3f}")
    print("  -> a random split of sequential data is interpolation: it flatters")
    print("     every method.\n")

    # ---- Protocol 2: FORWARD split (extrapolation — the honest task) ----
    cut = int(n * 0.85)
    Xtr, Xte = X[:cut], X[cut:]
    ytr, yte = y[:cut], y[cut:]
    print("=" * 62)
    print(f"PROTOCOL 2 — forward split (EXTRAPOLATION, the real task)")
    print(f"  train on cycles 1..{cut}, predict {cut+1}..{n} (never seen)")
    print("=" * 62)
    res = fit_gp(Xtr, ytr, feat)
    r2_gp = r2_score(yte, res.predict(Xte))
    rf = RandomForestRegressor(n_estimators=300, random_state=42).fit(Xtr, ytr)
    bb = {"RandomForest (300)": r2_score(yte, rf.predict(Xte))}
    if xgb is not None:
        m = xgb.XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.05,
                             random_state=42).fit(Xtr, ytr)
        bb["XGBoost (300 trees)"] = r2_score(yte, m.predict(Xte))
    for name, v in bb.items():
        print(f"  {name:<24}R² = {v:+.3f}")
    print(f"  {'GP_ELITE (one equation)':<24}R² = {r2_gp:+.3f}")
    print(f"\n  Equation: SOH = {res.expression}")
    best = max(bb.values())
    if r2_gp > best:
        print("\n  -> On this split the equation extrapolates better than the tree")
        print("     ensembles, which can only repeat values seen in training.")
    else:
        print("\n  -> On this split the tree ensembles do as well as the equation or")
        print("     better: extrapolation is not won in advance.")


if __name__ == "__main__":
    main()
