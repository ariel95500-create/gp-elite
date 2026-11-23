"""Regenerates docs/img/kepler.gif and docs/img/kepler.fr.gif, the animations
at the top of README.md and README.fr.md.

Same data and same call as the example of the README, on one CPU core. All
that the animations write is measured by this run: the formula
(result.expression), the R² on the eight planets and the time of the fit.
The law is the best model from generation 0 of the search on, so the
animations do not show a search converging: they show the data, then the
curve and the formula that come back.

Run:  python examples/kepler_gif.py      (needs matplotlib, which brings Pillow)
"""
import os
import time

import numpy as np

import gp_elite
from gp_elite import symbolic_regression

TEXT = {
    "en": dict(
        out="kepler.gif",
        names=["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"],
        title="8 planets: their distance a to the Sun, their year T",
        search="GP_ELITE looks for the formula...",
        law="a·√a = a^1.5, so T² ∝ a³: Kepler's third law",
        facts="R² = {r2} on the 8 planets · {secs} s on one CPU core · gp-elite {ver}",
        xlabel="semi-major axis a (AU)", ylabel="orbital period T (years)",
        dec=".",
    ),
    "fr": dict(
        out="kepler.fr.gif",
        names=["Mercure", "Vénus", "Terre", "Mars", "Jupiter", "Saturne", "Uranus", "Neptune"],
        title="8 planètes : leur distance a au Soleil, leur année T",
        search="GP_ELITE cherche la formule...",
        law="a·√a = a^1,5, donc T² ∝ a³ : la 3ᵉ loi de Kepler",
        facts="R² = {r2} sur les 8 planètes · {secs} s sur un cœur · gp-elite {ver}",
        xlabel="demi-grand axe a (UA)", ylabel="période orbitale T (années)",
        dec=",",
    ),
}

A = np.array([0.387, 0.723, 1.000, 1.524, 5.203, 9.537, 19.191, 30.069])   # AU
T = np.array([0.241, 0.615, 1.000, 1.881, 11.862, 29.457, 84.011, 164.79])  # years

BG, AX, RED, BLUE, GRID = "#0d0f1a", "#000000", "#ff5a5f", "#4da6ff", "#3a3a3a"


def animate(tx, res, r2, secs, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    from PIL import Image

    formula = "T = " + res.expression.replace("sqrt(a)", "√a").replace(" * ", "·")
    facts = tx["facts"].format(r2=("%.6f" % r2).replace(".", tx["dec"]),
                               secs=("%.1f" % secs).replace(".", tx["dec"]),
                               ver=gp_elite.__version__)
    grid = np.geomspace(0.33, 34, 240)
    curve = res.predict(grid.reshape(-1, 1))

    def frame(n_points, caption=None, curve_frac=0.0, box_alpha=0.0):
        fig = plt.figure(figsize=(8, 4.5), dpi=100, facecolor=BG)
        ax = fig.add_axes([0.105, 0.135, 0.865, 0.735], facecolor=AX)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(0.28, 45)
        ax.set_ylim(0.12, 420)
        ax.grid(True, which="major", color=GRID, lw=0.6)
        for sp in ax.spines.values():
            sp.set_color("#777777")
        ax.tick_params(colors="#cccccc", labelsize=9, which="both")
        ax.set_xlabel(tx["xlabel"], color="#dddddd", fontsize=10.5)
        ax.set_ylabel(tx["ylabel"], color="#dddddd", fontsize=10.5)
        fig.text(0.105, 0.915, tx["title"], color="white", fontsize=14,
                 fontweight="bold")
        if curve_frac > 0:
            k = max(2, int(round(curve_frac * len(grid))))
            ax.plot(grid[:k], curve[:k], color=BLUE, lw=2.6, zorder=2)
        if n_points:
            ax.scatter(A[:n_points], T[:n_points], s=62, color=RED,
                       edgecolor="white", linewidth=1.0, zorder=3)
            for name, x, y in zip(tx["names"][:n_points], A, T):
                ax.annotate(name, (x, y), xytext=(7, -11), textcoords="offset points",
                            color="#d8d8d8", fontsize=8.5)
        if caption:
            ax.text(0.03, 0.93, caption, transform=ax.transAxes, va="top",
                    color="#9fc3ff", fontsize=13, style="italic")
        if box_alpha > 0:
            ax.add_patch(FancyBboxPatch((0.025, 0.635), 0.6, 0.315,
                                        boxstyle="round,pad=0.0,rounding_size=0.025",
                                        transform=ax.transAxes, facecolor="#161a2b",
                                        edgecolor=BLUE, lw=1.3, alpha=box_alpha, zorder=4))
            ax.text(0.05, 0.915, formula, transform=ax.transAxes, va="top",
                    color="white", fontsize=17, fontweight="bold", alpha=box_alpha,
                    zorder=5)
            ax.text(0.05, 0.79, tx["law"], transform=ax.transAxes, va="top",
                    color="#cfe3ff", fontsize=11.5, alpha=box_alpha, zorder=5)
            ax.text(0.05, 0.705, facts, transform=ax.transAxes, va="top",
                    color="#9aa3b5", fontsize=8.5, alpha=box_alpha, zorder=5)
        fig.canvas.draw()
        img = Image.frombuffer("RGBA", fig.canvas.get_width_height(),
                               fig.canvas.buffer_rgba(), "raw", "RGBA", 0, 1).convert("RGB")
        plt.close(fig)
        return img

    frames, durations = [], []

    def add(img, ms):
        frames.append(img)
        durations.append(ms)

    add(frame(0), 700)                                   # the empty axes
    for n in range(1, 9):                                # the planets, one by one
        add(frame(n), 230)
    add(frame(8, caption=tx["search"]), 1100)
    for i in range(1, 11):                               # the curve, left to right
        add(frame(8, curve_frac=i / 10), 60)
    for al in (0.35, 0.7):                               # the formula fades in
        add(frame(8, curve_frac=1.0, box_alpha=al), 70)
    add(frame(8, curve_frac=1.0, box_alpha=1.0), 4500)

    # One palette for all the frames, from a mosaic of the frames that carry
    # every colour, so that nothing flickers from one frame to the next.
    keys = [frames[9], frames[-1]]
    mosaic = Image.new("RGB", (keys[0].width, keys[0].height * len(keys)))
    for i, im in enumerate(keys):
        mosaic.paste(im, (0, i * im.height))
    pal = mosaic.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    pframes = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in frames]
    pframes[0].save(out, save_all=True, append_images=pframes[1:], duration=durations,
                    loop=0, optimize=False, disposal=1)
    print("written:", out)


def main():
    t0 = time.perf_counter()
    res = symbolic_regression(A.reshape(-1, 1), T, feature_names=["a"],
                              generations=40, seed=0, parallel=False)
    secs = time.perf_counter() - t0
    pred = res.predict(A.reshape(-1, 1))
    r2 = 1 - np.sum((pred - T) ** 2) / np.sum((T - T.mean()) ** 2)
    print("T =", res.expression, "  R2 = %.6f   %.2f s" % (r2, secs))
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "docs", "img")
    os.makedirs(out_dir, exist_ok=True)
    for tx in TEXT.values():
        animate(tx, res, r2, secs, os.path.join(out_dir, tx["out"]))


if __name__ == "__main__":
    main()
