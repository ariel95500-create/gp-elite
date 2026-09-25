"""Regenerates kepler_plot.png, the figure at the top of the README.

Same fit as examples/kepler_demo.py; the formula, R² and search time printed
on the figure are the ones measured by this run, so the image never claims
more than the code does.

Run:  python examples/kepler_plot.py      (needs matplotlib)
"""
import os
import time

import numpy as np

from gp_elite import symbolic_regression


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    planets = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
    a = np.array([0.387, 0.723, 1.000, 1.524, 5.203, 9.537, 19.191, 30.069])   # AU
    T = np.array([0.241, 0.615, 1.000, 1.881, 11.862, 29.457, 84.011, 164.79])  # years

    t0 = time.time()
    res = symbolic_regression(a.reshape(-1, 1), T, feature_names=["a"],
                              operators="physical", generations=40, speed="fast",
                              validation_split=0.0, seed=0)
    secs = time.time() - t0
    pred = res.predict(a.reshape(-1, 1))
    r2 = 1 - np.sum((pred - T) ** 2) / np.sum((T - T.mean()) ** 2)
    print("T =", res.expression, "  R2 = %.6f   %.1f s" % (r2, secs))

    grid = np.geomspace(a.min() * 0.95, a.max() * 1.05, 200)
    fig, ax = plt.subplots(figsize=(10.7, 6.6), dpi=120)
    fig.patch.set_facecolor("#0d0f1a")
    ax.set_facecolor("black")
    ax.plot(grid, res.predict(grid.reshape(-1, 1)), color="#4da6ff", lw=2.5,
            label="GP_ELITE:  T = " + res.expression.replace("sqrt(a)", "√a"))
    ax.scatter(a, T, s=110, color="#ff5a5f", edgecolor="white", zorder=3,
               label="Planetary data (8 planets)")
    for p, x, y in zip(planets, a, T):
        ax.annotate(p, (x, y), xytext=(8, -12), textcoords="offset points",
                    color="#dddddd", fontsize=10)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.grid(True, which="both", color="#444444", lw=0.5, alpha=0.6)
    for sp in ax.spines.values():
        sp.set_color("#888888")
    ax.tick_params(colors="white")
    ax.set_xlabel("Semi-major axis  a  (AU, log scale)", color="white", fontsize=13)
    ax.set_ylabel("Orbital period  T  (years, log scale)", color="white", fontsize=13)
    ax.set_title("GP_ELITE rediscovered Kepler's Third Law from 8 data points",
                 color="white", fontsize=15, fontweight="bold")
    ax.text(0.04, 0.95, "R² = %.6f\nFound in %.0f seconds\n(gp-elite, one CPU core)"
            % (r2, secs), transform=ax.transAxes, va="top", color="white",
            fontsize=12, bbox=dict(boxstyle="round", facecolor="#1a1d2e",
                                   edgecolor="#4da6ff"))
    leg = ax.legend(loc="lower right", facecolor="#111111", edgecolor="#555555",
                    fontsize=11)
    for txt in leg.get_texts():
        txt.set_color("white")
    fig.tight_layout()
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "kepler_plot.png")
    fig.savefig(out, facecolor=fig.get_facecolor())
    print("written:", out)


if __name__ == "__main__":
    main()
