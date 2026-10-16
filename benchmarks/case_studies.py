"""The three case studies of phase 6 (examples/case_studies/), run as their
protocol says (benchmarks/results_0.9/PLAN_PHASE6.md): every figure the
notebooks print or state comes from here.

    PYTHONHASHSEED=0 python benchmarks/case_studies.py kepler
    PYTHONHASHSEED=0 python benchmarks/case_studies.py hubble
    PYTHONHASHSEED=0 python benchmarks/case_studies.py nikuradse OUTDIR

kepler and hubble print their figures for the seeds 0 to 4; nikuradse runs
benchmarks/real_nikuradse.py once per seed, one process each, and keeps its
console output and telemetry in OUTDIR. Times depend on the machine; the rest
does not.
"""
import os, sys, io, time, subprocess, contextlib
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "examples", "case_studies", "data")
if os.path.isdir(os.path.join(ROOT, "gp_elite")):
    sys.path.insert(0, ROOT)

import gp_elite
from gp_elite import GPEliteRegressor
from gp_elite import core as C

SEEDS = range(5)
AU = 149597870700.0                  # m, IAU 2012 B2
YEAR = 365.25 * 86400.0              # s, Julian year
GM_SUN = 1.3271244e20                # m^3 s^-2, nominal, IAU 2015 B3

# Seed functions of the engine, wrapped to record what they place; the
# wrapper returns what the function returns, so the fit does not change.
SEED_CALLS = []
for _name in ("_make_power_law_seeds", "_make_binomial_seeds",
              "_make_elementary_seeds", "_make_tolerant_seeds"):
    def _wrap(*a, _f=getattr(C, _name), _n=_name, **k):
        r = _f(*a, **k)
        SEED_CALLS.append((_n, len(r) if r else 0))
        return r
    setattr(C, _name, _wrap)


def fit(est, X, y):
    del SEED_CALLS[:]
    t0 = time.time()
    with contextlib.redirect_stdout(io.StringIO()):
        est.fit(X, y)
    return time.time() - t0


def kepler():
    df = pd.read_csv(os.path.join(DATA, "planets_simon1994.csv"), comment="#")
    a_au = df["a_au"].to_numpy(float)
    p_yr = 1296000000.0 / df["mean_motion"].to_numpy(float)
    a_m, p_s = a_au * AU, p_yr * YEAR
    inner, outer = slice(0, 4), slice(4, 8)
    print("gp_elite", gp_elite.__version__)
    print("periods (years):", " ".join("%s %.6f" % (n, p)
                                        for n, p in zip(df.planet, p_yr)))
    print("a^3/P^2 (au^3/yr^2):", " ".join("%s %.6f" % (n, r) for n, r in
                                           zip(df.planet, a_au**3 / p_yr**2)))
    for s in SEEDS:
        print(f"\n--- seed {s}")
        units = dict(units=["m"], target_units="s", unknown_constant=True,
                     generations=30, speed="fast", parallel=False,
                     random_state=s)
        est = GPEliteRegressor(**units)
        t = fit(est, a_m.reshape(-1, 1), p_s)
        c = est.constant_value_
        gm = (2 * np.pi / c) ** 2 if c else float("nan")
        err = np.max(np.abs(est.predict(a_m.reshape(-1, 1)) / p_s - 1))
        print(f"A  {est.equation_}   ({t:.0f} s)")
        print(f"   constant {est.constant_units_string()} = {c!r}")
        print(f"   G*M_sun = {gm:.6e}  ({gm / GM_SUN - 1:+.2e} from IAU)"
              f"   largest relative error on the 8 periods {err:.2e}")
        est = GPEliteRegressor(**units)
        t = fit(est, a_m[inner].reshape(-1, 1), p_s[inner])
        c = est.constant_value_
        gm = (2 * np.pi / c) ** 2 if c else float("nan")
        rel = est.predict(a_m[outer].reshape(-1, 1)) / p_s[outer] - 1
        print(f"B  {est.equation_}   ({t:.0f} s)")
        print(f"   constant {est.constant_units_string()} = {c!r}"
              f"   G*M_sun = {gm:.6e}  ({gm / GM_SUN - 1:+.2e} from IAU)")
        print("   outer planets, relative error: " +
              " ".join("%s %+.2e" % (n, r)
                       for n, r in zip(df.planet[outer], rel)) +
              f"   largest {np.max(np.abs(rel)):.2e}")
        plain = dict(generations=30, speed="fast", parallel=False,
                     random_state=s)
        est = GPEliteRegressor(**plain)
        t = fit(est, a_au.reshape(-1, 1), p_yr)
        rel = est.predict(a_au.reshape(-1, 1)) / p_yr - 1
        print(f"C8 {est.equation_}   ({t:.0f} s)   seeds placed {SEED_CALLS}")
        print("   relative error: " + " ".join(
            "%s %+.2e" % (n, r) for n, r in zip(df.planet, rel)))
        est = GPEliteRegressor(**plain)
        t = fit(est, a_au[inner].reshape(-1, 1), p_yr[inner])
        rel = est.predict(a_au[outer].reshape(-1, 1)) / p_yr[outer] - 1
        print(f"C4 {est.equation_}   ({t:.0f} s)")
        print("   outer planets, relative error: " +
              " ".join("%s %+.2e" % (n, r)
                       for n, r in zip(df.planet[outer], rel)) +
              f"   largest {np.max(np.abs(rel)):.2e}")


def hubble():
    df = pd.read_csv(os.path.join(DATA, "hubble1929.csv"), comment="#")
    d = df["distance_mpc"].to_numpy(float)
    v = df["velocity_kms"].to_numpy(float)
    v_lmreg = v.copy()
    v_lmreg[9] = -v_lmreg[9]               # the tenth row, 0.63 Mpc
    assert d[9] == 0.63 and v[9] == 200
    near, far = d <= 1.1, d > 1.1
    print("gp_elite", gp_elite.__version__)
    print(f"rows {len(d)}, fit {near.sum()} up to 1.1 Mpc, held out {far.sum()}")

    def rmse(p, t):
        return float(np.sqrt(np.mean((np.asarray(p) - t) ** 2)))

    def r2(p, t):
        return 1 - float(np.mean((np.asarray(p) - t) ** 2) / np.var(t))

    for name, vv in (("case0701", v), ("stars1", v_lmreg)):
        k0 = float(d @ vv / (d @ d))
        b1, b0 = np.polyfit(d, vv, 1)
        print(f"\n{name}: least squares through the origin  v = {k0:.2f} d"
              f"   R2 {r2(k0 * d, vv):.4f}   RMSE {rmse(k0 * d, vv):.1f}")
        print(f"{name}: least squares with intercept    v = {b0:.2f} + "
              f"{b1:.2f} d   R2 {r2(b0 + b1 * d, vv):.4f}"
              f"   RMSE {rmse(b0 + b1 * d, vv):.1f}")
    k_near = float(d[near] @ v[near] / (d[near] @ d[near]))
    b1n, b0n = np.polyfit(d[near], v[near], 1)
    print(f"held out, through the origin fitted on the 18: v = {k_near:.2f} d"
          f"   RMSE on the 6 {rmse(k_near * d[far], v[far]):.1f}")
    print(f"held out, with intercept fitted on the 18:    v = {b0n:.2f} + "
          f"{b1n:.2f} d   RMSE on the 6 {rmse(b0n + b1n * d[far], v[far]):.1f}")

    X = d.reshape(-1, 1)
    for s in SEEDS:
        print(f"\n--- seed {s}")
        units = dict(units=["Mpc"], target_units="km/s", unknown_constant=True,
                     generations=30, speed="fast", parallel=False,
                     random_state=s)
        plain = dict(generations=30, speed="fast", parallel=False,
                     random_state=s)
        for tag, kw in (("A", units), ("B", plain)):
            est = GPEliteRegressor(**kw)
            t = fit(est, X, v)
            p = est.predict(X)
            extra = (f"   constant {est.constant_units_string()} = "
                     f"{est.constant_value_!r}" if tag == "A" else "")
            print(f"{tag}  {est.equation_}   ({t:.0f} s)   R2 {r2(p, v):.4f}"
                  f"   RMSE {rmse(p, v):.1f}{extra}   seeds placed {SEED_CALLS}")
            est = GPEliteRegressor(**kw)
            fit(est, X[near], v[near])
            print(f"C{tag} {est.equation_}   RMSE on the 6 "
                  f"{rmse(est.predict(X[far]), v[far]):.1f}")
            est = GPEliteRegressor(**kw)
            fit(est, X, v_lmreg)
            extra = (f"   constant {est.constant_units_string()} = "
                     f"{est.constant_value_!r}" if tag == "A" else "")
            print(f"D{tag} {est.equation_}   R2 "
                  f"{r2(est.predict(X), v_lmreg):.4f}{extra}")


def nikuradse(outdir):
    os.makedirs(outdir, exist_ok=True)
    env = dict(os.environ, PYTHONHASHSEED="0", PYTHONPATH=ROOT)
    script = os.path.join(HERE, "real_nikuradse.py")
    for s in SEEDS:
        log = os.path.join(outdir, f"nikuradse_seed{s}.txt")
        # The script writes its telemetry next to itself, and with the seed 0
        # over a file the repository keeps: that file is put back afterwards.
        kept = {f: open(os.path.join(HERE, f), "rb").read()
                for f in os.listdir(HERE)
                if f.startswith("real_nikuradse_") and f.endswith(".json")}
        with open(log, "w", encoding="utf-8") as fh:
            subprocess.run([sys.executable, script, "--seed", str(s)],
                           stdout=fh, stderr=subprocess.STDOUT, env=env,
                           check=True)
        for f in os.listdir(HERE):
            if not (f.startswith("real_nikuradse_") and f.endswith(".json")):
                continue
            path = os.path.join(HERE, f)
            new = open(path, "rb").read()
            if kept.get(f) == new:
                continue
            tag = f[:-5] if f[:-5].endswith(f"_seed{s}") else f[:-5] + f"_seed{s}"
            with open(os.path.join(outdir, tag + ".json"), "wb") as out:
                out.write(new)
            if f in kept:
                with open(path, "wb") as back:
                    back.write(kept[f])
            else:
                os.remove(path)
        print(f"seed {s}: {log}")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else ""
    if what == "kepler":
        kepler()
    elif what == "hubble":
        hubble()
    elif what == "nikuradse" and len(sys.argv) > 2:
        nikuradse(sys.argv[2])
    else:
        sys.exit(__doc__)
