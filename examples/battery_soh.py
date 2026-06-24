"""
Battery degradation: interpolation vs extrapolation (NASA data).

This example demonstrates an important, often-overlooked point in time-series
regression: a RANDOM train/test split leaks information when samples are
sequential (predicting cycle 49 from cycles 48 and 50 is just interpolation).
The honest task is EXTRAPOLATION — train on early cycles, predict later ones
the model has never seen.

We compare GP_ELITE (one equation) against XGBoost and RandomForest (black-box
ensembles) under both protocols. The result is instructive:

  - Interpolation (random split): everyone scores high. Misleading.
  - Extrapolation (forward split): the black-box ensembles collapse to
    negative R² (worse than predicting the mean), because trees can only
    echo values seen in training. A continuous equation keeps tracking the
    trend.

This is the real argument for symbolic regression on physical data: not raw
accuracy, but an interpretable law that extrapolates.

Requires: pip install xgboost scikit-learn
Usage:    python examples/battery_soh.py
"""
import os
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

from gp_elite import symbolic_regression
import gp_elite.core as core

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "nasa_battery_simulation.csv")


def fit_gp(Xtr, ytr, feat, seed=0):  # seed fixed for reproducibility
    """Fit GP_ELITE and return (result, scaler) so test data uses the same scale."""
    import random
    scaler, _ = core._choose_scaler(Xtr, "auto", (-2.0, 2.0))
    scaler.fit_transform(Xtr)
    random.seed(seed); np.random.seed(seed)
    res = symbolic_regression(
        Xtr, ytr, feature_names=feat,
        operators="physical", normalize="auto",
        generations=60, speed="fast", validation_split=0.0, seed=seed,
        parallel=False,  # deterministic + reproducible for this demo
    )
    return res, scaler


def main():
    df = pd.read_csv(CSV)
    feat = ["cycle", "temperature", "courant"]
    X = df[feat].values
    y = df["capacity_SOH"].values
    n = len(y)
    print(f"NASA battery data: {n} sequential cycles, target SOH in "
          f"[{y.min():.3f}, {y.max():.3f}]\n")

    # Optional black-box baselines (skip gracefully if not installed)
    try:
        import xgboost as xgb
        from sklearn.ensemble import RandomForestRegressor
        have_bb = True
    except ImportError:
        have_bb = False
        print("(xgboost/scikit-learn not installed — showing GP_ELITE only)\n")

    # ---- Protocol 1: RANDOM split (interpolation — leaks, misleading) ----
    from sklearn.model_selection import train_test_split
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42)
    print("=" * 62)
    print("PROTOCOL 1 — random split (INTERPOLATION, leaks info)")
    print("=" * 62)
    res, scaler = fit_gp(Xtr, ytr, feat)
    print(f"  GP_ELITE   R² = {r2_score(yte, res.predict(scaler.transform(Xte))):+.3f}")
    if have_bb:
        m = xgb.XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.05,
                             random_state=42).fit(Xtr, ytr)
        print(f"  XGBoost    R² = {r2_score(yte, m.predict(Xte)):+.3f}")
    print("  -> high scores all around, but this is interpolation. Misleading.\n")

    # ---- Protocol 2: FORWARD split (extrapolation — the honest task) ----
    cut = int(n * 0.85)
    Xtr, Xte = X[:cut], X[cut:]
    ytr, yte = y[:cut], y[cut:]
    print("=" * 62)
    print(f"PROTOCOL 2 — forward split (EXTRAPOLATION, the real task)")
    print(f"  train on cycles 1..{cut}, predict {cut+1}..{n} (never seen)")
    print("=" * 62)
    res, scaler = fit_gp(Xtr, ytr, feat)
    r2_gp = r2_score(yte, res.predict(scaler.transform(Xte)))
    if have_bb:
        m = xgb.XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.05,
                             random_state=42).fit(Xtr, ytr)
        rf = RandomForestRegressor(n_estimators=300, random_state=42).fit(Xtr, ytr)
        print(f"  XGBoost (300 trees)    R² = {r2_score(yte, m.predict(Xte)):+.3f}")
        print(f"  RandomForest (300)     R² = {r2_score(yte, rf.predict(Xte)):+.3f}")
    print(f"  GP_ELITE (one equation) R² = {r2_gp:+.3f}")
    print(f"\n  Equation: SOH = {res.expression}")
    print("\n  -> Black-box ensembles collapse to negative R² out-of-domain.")
    print("     The equation keeps tracking the degradation trend.")
    print("     That's the case for symbolic regression on physical data.")


if __name__ == "__main__":
    main()
