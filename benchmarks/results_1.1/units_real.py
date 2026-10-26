# -*- coding: utf-8 -*-
"""Real data under units, criterion 4 of campaign U1 (benchmarks/results_1.1/PLAN.md).

The typed fits of the two case studies (benchmarks/case_studies.py), seeds 0
to 4, each in its own process, with the settings of the studies
(unknown_constant=True, generations=30, speed "fast", parallel=False):
  kepler_A   the eight planets, in metres and seconds
  kepler_B   fitted on the four inner planets; largest relative error on the
             four outer ones
  hubble_A   the 24 galaxies of 1929, Mpc and km/s
  hubble_CA  fitted on the 18 nearest (up to 1.1 Mpc); RMSE on the 6 farthest

The engine is the gp_elite package of the given Python. For U1 the caller
puts benchmarks/phase2_flags and the repository first on PYTHONPATH with
GP_ELITE_ARM=U1 (see run_u1.sh in this folder).

    python units_real.py run --python PY --out FILE.jsonl
    python units_real.py summary A.jsonl B.jsonl
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time
from contextlib import redirect_stdout

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(os.path.dirname(HERE)), "examples",
                    "case_studies", "data")
AU = 149597870700.0
YEAR = 365.25 * 86400.0
GM_SUN = 1.3271244e20
FITS = ("kepler_A", "kepler_B", "hubble_A", "hubble_CA")
SEEDS = (0, 1, 2, 3, 4)


def one(fit_name, seed):
    import warnings
    import pandas as pd
    import gp_elite
    from gp_elite import GPEliteRegressor
    from gp_elite.dim_search import is_typed_valid, normalize_units_arg
    kw = dict(unknown_constant=True, generations=30, speed="fast",
              parallel=False, random_state=seed)
    import gp_elite.core as C
    rec = dict(fit=fit_name, seed=seed, engine_version=gp_elite.__version__,
               engine_file=gp_elite.__file__,
               seeds_under_units=getattr(C, "_SEEDS_UNDER_UNITS", None))
    if fit_name.startswith("kepler"):
        df = pd.read_csv(os.path.join(DATA, "planets_simon1994.csv"),
                         comment="#")
        a = df["a_au"].to_numpy(float) * AU
        p = 1296000000.0 / df["mean_motion"].to_numpy(float) * YEAR
        tr = slice(0, 8) if fit_name == "kepler_A" else slice(0, 4)
        est = GPEliteRegressor(units=["m"], target_units="s", **kw)
        X, y, Xh, yh = a[tr].reshape(-1, 1), p[tr], a[4:].reshape(-1, 1), p[4:]
    else:
        df = pd.read_csv(os.path.join(DATA, "hubble1929.csv"), comment="#")
        d = df["distance_mpc"].to_numpy(float)
        v = df["velocity_kms"].to_numpy(float)
        near = d <= 1.1
        tr = slice(None) if fit_name == "hubble_A" else near
        est = GPEliteRegressor(units=["Mpc"], target_units="km/s", **kw)
        X, y = d[tr].reshape(-1, 1), v[tr]
        Xh, yh = d[~near].reshape(-1, 1), v[~near]
    t0 = time.time()
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        est.fit(X, y)
    rec["time"] = round(time.time() - t0, 2)
    rec["equation"] = str(est.equation_)[:200]
    rec["constant"] = est.constant_value_
    rec["constant_units"] = est.constant_units_string()
    fd, td = normalize_units_arg(est.units, est.target_units, 1, None)
    rec["units_consistent"] = bool(is_typed_valid(est.model_.node, fd, td,
                                                  unknown_constant=True))
    pred = est.predict(Xh)
    if fit_name == "kepler_A":
        c = est.constant_value_
        rec["gm_rel_error"] = ((2 * np.pi / c) ** 2 / GM_SUN - 1) if c else None
        rec["held_out_error"] = float(np.max(np.abs(
            est.predict(X) / y - 1)))                 # the 8 periods, in-sample
    elif fit_name == "kepler_B":
        rec["held_out_error"] = float(np.max(np.abs(pred / yh - 1)))
    elif fit_name == "hubble_A":
        rec["held_out_error"] = float(np.sqrt(np.mean((est.predict(X) - y) ** 2)))
    else:
        rec["held_out_error"] = float(np.sqrt(np.mean((pred - yh) ** 2)))
    return rec


def run(python, out):
    done = set()
    if os.path.exists(out):
        for ln in open(out):
            if ln.strip():
                r = json.loads(ln)
                done.add((r["fit"], r["seed"]))
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    for f in FITS:
        for s in SEEDS:
            if (f, s) in done:
                continue
            p = subprocess.run([python, os.path.abspath(__file__), "one", f,
                                str(s)], capture_output=True, text=True,
                               env=env, cwd="/")
            lines = [ln for ln in p.stdout.splitlines() if ln.startswith("{")]
            rec = json.loads(lines[-1]) if (p.returncode == 0 and lines) \
                else dict(fit=f, seed=s, crash=True, error=p.stderr[-400:])
            with open(out, "a") as fh:
                fh.write(json.dumps(rec) + "\n")
            print(f, s, rec.get("held_out_error"), rec.get("equation", "")[:70],
                  flush=True)


def summary(path_a, path_b):
    def load(path):
        return {(r["fit"], r["seed"]): r for r in
                (json.loads(ln) for ln in open(path) if ln.strip())}
    A, B = load(path_a), load(path_b)
    print("fit         seed  A error      U1 error     A time  U1 time  "
          "U1 units consistent")
    for f in FITS:
        for s in SEEDS:
            a, b = A.get((f, s), {}), B.get((f, s), {})
            print("%-11s %d  %-12.4g %-12.4g %6.1f  %6.1f   %s" % (
                f, s, a.get("held_out_error", np.nan),
                b.get("held_out_error", np.nan), a.get("time", np.nan),
                b.get("time", np.nan), b.get("units_consistent")))
    print()
    for f in ("kepler_B", "hubble_CA"):
        ea = [A[(f, s)]["held_out_error"] for s in SEEDS if (f, s) in A]
        eb = [B[(f, s)]["held_out_error"] for s in SEEDS if (f, s) in B]
        print("%s: median held-out error A %.4g, U1 %.4g (ratio %.3f; the "
              "plan allows 1.10)" % (f, np.median(ea), np.median(eb),
                                     np.median(eb) / np.median(ea)))
    worst = max(B[k]["held_out_error"] / A[k]["held_out_error"]
                for k in B if k in A and A[k]["held_out_error"] > 0)
    print("largest ratio U1 / A on one fit: %.3f (the plan allows 10)" % worst)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--python", required=True)
    r.add_argument("--out", required=True)
    o = sub.add_parser("one")
    o.add_argument("fit")
    o.add_argument("seed", type=int)
    s = sub.add_parser("summary")
    s.add_argument("a")
    s.add_argument("b")
    a = ap.parse_args()
    if a.cmd == "run":
        run(a.python, os.path.abspath(a.out))
    elif a.cmd == "one":
        print(json.dumps(one(a.fit, a.seed)))
    else:
        summary(a.a, a.b)


if __name__ == "__main__":
    main()
