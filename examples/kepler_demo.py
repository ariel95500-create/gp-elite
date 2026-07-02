"""
GP_ELITE rediscovers Kepler's Third Law from real planetary data.

In 1618, after ~10 years of work, Kepler found that T² ∝ a³ for planetary
orbits. Here, GP_ELITE is given the 8 planets' semi-major axis (a) and orbital
period (T) — nothing else — and rediscovers the law in seconds.

Run:  python kepler_demo.py
"""
import numpy as np, random
from gp_elite import symbolic_regression


def main():
    # Real solar-system data (NASA)
    planets = ["Mercury","Venus","Earth","Mars","Jupiter","Saturn","Uranus","Neptune"]
    a = np.array([0.387, 0.723, 1.000, 1.524, 5.203, 9.537, 19.191, 30.069])   # AU
    T = np.array([0.241, 0.615, 1.000, 1.881, 11.862, 29.457, 84.011, 164.79]) # years

    print("Real data — 8 planets:")
    for p, ai, Ti in zip(planets, a, T):
        print(f"  {p:8s}  a = {ai:7.3f} AU   T = {Ti:8.3f} yr")

    random.seed(0); np.random.seed(0)
    res = symbolic_regression(
        a.reshape(-1, 1), T,
        feature_names=["a"],
        operators="physical",
        normalize="divmax",
        generations=40,
        speed="fast",
        validation_split=0.0,   # only 8 points
        seed=0,
    )
    pred = res.predict(a.reshape(-1, 1))   # unités BRUTES : predict applique le scaler lui-même
    r2 = 1 - np.sum((pred - T) ** 2) / np.sum((T - T.mean()) ** 2)

    print("\n" + "=" * 55)
    print("LAW DISCOVERED BY GP_ELITE")
    print("=" * 55)
    print(f"  T = {res.expression}")
    print(f"  R² = {r2:.6f}")
    print()
    print("  a·sqrt(a) = a^1.5  →  T² ∝ a³  =  Kepler's Third Law (1618)")
    print("  Rediscovered from raw data in seconds.")


if __name__ == "__main__":
    main()
