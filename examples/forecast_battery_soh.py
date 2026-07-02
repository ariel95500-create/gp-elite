"""Forecast / Prévision — battery SOH beyond observed cycles (v0.2.0).

Uses the validated forecasting configuration: single trending axis, divergence
guard, restarts, frontier meta-selection, Pareto front.
Interactive equivalent: `python -m gp_elite` → mode 7.
"""
import os
import numpy as np
from gp_elite import symbolic_regression

def main():
    path = os.path.join(os.path.dirname(__file__), "nasa_battery_simulation.csv")
    d = np.genfromtxt(path, delimiter=",", names=True)
    X = d["cycle"].reshape(-1, 1)
    y = d["capacity_SOH"]

    r = symbolic_regression(
        X, y, feature_names=["cycle"], operators="physical",
        generations=30, speed="fast", validation_split=0.20, seed=0,
        restarts=4,
        extrapolate_feature="cycle", extrapolate_direction="high",
    )
    print("Model  :", r.expression)
    print(f"R2(val): {r.r2_validation:.4f}")
    print("\nPareto front (each entry = one forecast hypothesis):")
    for e in r.pareto or []:
        print("  ", e)
    hi = float(X.max()); span = hi - float(X.min())
    print("\nProjection beyond data:")
    for fr in (0.10, 0.25, 0.50):
        c = hi + fr * span
        print(f"  cycle {c:6.0f} -> SOH ~ {float(r.predict([[c]])[0]):.4f}")
    print("\nNote: an extrapolation is a hypothesis; compare Pareto entries "
          "(the linear one is the conservative scenario).")

if __name__ == "__main__":
    main()
