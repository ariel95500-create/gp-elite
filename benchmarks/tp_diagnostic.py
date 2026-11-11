# -*- coding: utf-8 -*-
"""Diagnostic TP: does GP_ELITE return the textbook law on student lab data?

Protocol, written before the run: benchmarks/results_1.1/DIAGNOSTIC_TP.md.
Ten experiments of physics teaching, 10 and 20 points, 2 % and 5 %
multiplicative noise on the target, five draws, two arms (plain defaults,
and units= with target_units=). Each fit in its own process, PYTHONHASHSEED=0,
one BLAS thread; the engine is the gp_elite package of the given Python.

    python benchmarks/tp_diagnostic.py run --python /venv10/bin/python \\
           --out benchmarks/results_1.1/tp/tp_1.0.0.jsonl --workers 4
    python benchmarks/tp_diagnostic.py summary benchmarks/results_1.1/tp/tp_1.0.0.jsonl

[1.3] --experiments snell keeps only the jobs of those experiments (the
bench TPsnell of benchmarks/results_1.3/PLAN.md); without it the jobs are
those of before. The units arm also records units_ok, the check of
dimensions of the model returned.

[1.2] --draws 5,6,7,8,9 runs other draws (the confirmation of plan 1.2); the
default is the draws 0 to 4 of the diagnostic. The record also gives the
generations run, the stop on patience if any, and err_train.

[1.4] --set tpt10 runs TPT10, the frozen test set for teaching
(benchmarks/results_1.4/PLAN.md): ten other experiments under the same
protocol, numbered 10 to 19 in the generator of the data, never used to
decide. Without the option the jobs and the data are those of before.
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

# ── units (SI base units) ───────────────────────────────────────────────────
S = {"s": 1}
M = {"m": 1}
M3 = {"m": 3}
KG = {"kg": 1}
KELVIN = {"K": 1}
MOL = {"mol": 1}
NODIM = {}
STIFFNESS = {"kg": 1, "s": -2}                 # N/m
VOLT = {"kg": 1, "m": 2, "s": -3, "A": -1}
OHM = {"kg": 1, "m": 2, "s": -3, "A": -2}
WATT = {"kg": 1, "m": 2, "s": -3}
PASCAL = {"kg": 1, "m": -1, "s": -2}
IRRADIANCE = {"kg": 1, "s": -3}                # W/m²

PI = np.pi
# key, experiment, law, inputs (name, lo, hi, units), target units,
# unknown_constant in the units arm, pool, f
EXPERIMENTS = [
    dict(key="pendule", name="simple pendulum", law="T = 2*pi*sqrt(L/g)",
         inputs=[("L", 0.10, 1.00, M)], target=S, unknown=True,
         pool="physical", f=lambda X: 2 * PI * np.sqrt(X[:, 0] / 9.81)),
    dict(key="ressort", name="mass on a spring", law="T = 2*pi*sqrt(m/k)",
         inputs=[("m", 0.05, 0.50, KG), ("k", 10.0, 50.0, STIFFNESS)],
         target=S, unknown=False, pool="physical",
         f=lambda X: 2 * PI * np.sqrt(X[:, 0] / X[:, 1])),
    dict(key="chute", name="free fall", law="d = g*t^2/2",
         inputs=[("t", 0.10, 0.60, S)], target=M, unknown=True,
         pool="physical", f=lambda X: 0.5 * 9.81 * X[:, 0] ** 2),
    dict(key="puissance", name="electric power", law="P = U^2/R",
         inputs=[("U", 1.0, 12.0, VOLT), ("R", 10.0, 100.0, OHM)],
         target=WATT, unknown=False, pool="physical",
         f=lambda X: X[:, 0] ** 2 / X[:, 1]),
    dict(key="gaz", name="ideal gas", law="P = n*R*T/V",
         inputs=[("n", 0.01, 0.10, MOL), ("T", 273.0, 373.0, KELVIN),
                 ("V", 1e-3, 5e-3, M3)],
         target=PASCAL, unknown=True, pool="physical",
         f=lambda X: X[:, 0] * 8.314 * X[:, 1] / X[:, 2]),
    dict(key="eclairement", name="point source", law="E = P/(4*pi*d^2)",
         inputs=[("d", 0.2, 2.0, M)], target=IRRADIANCE, unknown=True,
         pool="physical", f=lambda X: 10.0 / (4 * PI * X[:, 0] ** 2)),
    dict(key="rc", name="capacitor discharge", law="u = E*exp(-t/tau)",
         inputs=[("t", 0.0, 5.0, S)], target=VOLT, unknown=True,
         pool="physical", f=lambda X: 5.0 * np.exp(-X[:, 0] / 1.0)),
    dict(key="refroidissement", name="Newton's cooling",
         law="theta = theta_a + (theta_0 - theta_a)*exp(-t/tau)",
         inputs=[("t", 0.0, 1800.0, S)], target=KELVIN, unknown=True,
         pool="physical",
         f=lambda X: 20.0 + 60.0 * np.exp(-X[:, 0] / 600.0)),
    dict(key="lentille", name="thin lens", law="q = p*f/(p - f)",
         inputs=[("p", 0.15, 0.60, M)], target=M, unknown=True,
         pool="physical", f=lambda X: X[:, 0] * 0.10 / (X[:, 0] - 0.10)),
    dict(key="snell", name="refraction", law="i2 = arcsin(sin(i1)/n)",
         inputs=[("i1", 0.1, 1.4, NODIM)], target=NODIM, unknown=False,
         pool="trig", f=lambda X: np.arcsin(np.sin(X[:, 0]) / 1.5)),
]
REACHABLE_PLAIN = [e["key"] for e in EXPERIMENTS if e["key"] != "snell"]

# ── [1.4] TPT10, the frozen test set for teaching ──────────────────────────
# Frozen in benchmarks/results_1.4/PLAN.md before any change of 1.4; measured
# with 1.3.0 first. It never decides, and its records are not read to choose
# a direction: only its table of counts is.
AMPERE = {"A": 1}
SPEED = {"m": 1, "s": -1}
CONCENTRATION = {"mol": 1, "m": -3}
RATE = {"mol": 1, "m": -3, "s": -1}
EXPERIMENTS_T = [
    dict(key="ohm", name="Ohm's law", law="U = R*I",
         inputs=[("I", 0.01, 0.20, AMPERE)], target=VOLT, unknown=True,
         pool="physical", f=lambda X: 47.0 * X[:, 0]),
    dict(key="torricelli", name="draining tank", law="v = sqrt(2*g*h)",
         inputs=[("h", 0.05, 0.50, M)], target=SPEED, unknown=True,
         pool="physical", f=lambda X: np.sqrt(2 * 9.81 * X[:, 0])),
    dict(key="boyle", name="Boyle's law", law="P = k/V",
         inputs=[("V", 2e-5, 6e-5, M3)], target=PASCAL, unknown=True,
         pool="physical", f=lambda X: 6.0 / X[:, 0]),
    dict(key="kepler3", name="Kepler's third law",
         law="T = 2*pi*sqrt(a^3/GM)",
         inputs=[("a", 5.8e10, 1.43e12, M)], target=S, unknown=True,
         pool="physical",
         f=lambda X: 2 * PI * np.sqrt(X[:, 0] ** 3 / 1.32712e20)),
    dict(key="interfrange", name="Young's fringes", law="i = lambda*D/a",
         inputs=[("lam", 4.5e-7, 6.5e-7, M), ("D", 1.0, 2.0, M),
                 ("a", 1e-4, 5e-4, M)],
         target=M, unknown=False, pool="physical",
         f=lambda X: X[:, 0] * X[:, 1] / X[:, 2]),
    dict(key="malus", name="Malus's law", law="I = I0*cos(theta)^2",
         inputs=[("theta", 0.0, 1.5, NODIM)], target=IRRADIANCE,
         unknown=True, pool="trig",
         f=lambda X: 800.0 * np.cos(X[:, 0]) ** 2),
    dict(key="charge", name="capacitor charge",
         law="u = E*(1 - exp(-t/tau))",
         inputs=[("t", 0.0, 5.0, S)], target=VOLT, unknown=True,
         pool="physical", f=lambda X: 5.0 * (1.0 - np.exp(-X[:, 0] / 1.0))),
    dict(key="michaelis", name="enzyme kinetics", law="v = Vmax*S/(Km + S)",
         inputs=[("S", 0.5, 10.0, CONCENTRATION)], target=RATE, unknown=True,
         pool="physical", f=lambda X: 0.01 * X[:, 0] / (2.0 + X[:, 0])),
    dict(key="ph", name="pH of a strong acid", law="pH = -log10(c)",
         inputs=[("c", 0.001, 0.1, CONCENTRATION)], target=NODIM,
         unknown=True, pool="physical", f=lambda X: -np.log10(X[:, 0])),
    dict(key="thermistance", name="thermistor",
         law="R = R0*exp(B*(1/T - 1/T0))",
         inputs=[("T", 283.15, 353.15, KELVIN)], target=OHM, unknown=True,
         pool="physical",
         f=lambda X: 1e4 * np.exp(3950.0 * (1.0 / X[:, 0] - 1.0 / 298.15))),
]
# under units, the laws with no constant inside a function or a sum
REACHABLE_UNITS_T = ["ohm", "torricelli", "boyle", "kepler3", "interfrange",
                     "malus"]
SETS = {"tp": EXPERIMENTS, "tpt10": EXPERIMENTS_T}
SIZES = (10, 20)
NOISES = (0.02, 0.05)
DRAWS = (0, 1, 2, 3, 4)
ARMS = ("plain", "units")


def experiment(key):
    """The number of an experiment in the generator of the data, and its
    entry: 0 to 9 for the diagnostic, [1.4] 10 to 19 for TPT10."""
    for k, e in enumerate(EXPERIMENTS + EXPERIMENTS_T):
        if e["key"] == key:
            return k, e
    raise KeyError(key)


def data(key, n, noise, draw):
    """Training inputs, noisy and noiseless targets, and the noiseless grid
    of 200 points over the same box."""
    k, e = experiment(key)
    rng = np.random.RandomState(100003 * draw + 1009 * n
                                + int(round(1000 * noise)) + 17 * k)
    if len(e["inputs"]) == 1:
        _nm, lo, hi, _u = e["inputs"][0]
        X = np.linspace(lo, hi, n).reshape(-1, 1)
    else:
        X = np.column_stack([rng.uniform(lo, hi, n)
                             for _nm, lo, hi, _u in e["inputs"]])
    y_clean = e["f"](X)
    y = y_clean * (1.0 + noise * rng.standard_normal(n))
    g = np.random.RandomState(999 + k)
    if len(e["inputs"]) == 1:
        _nm, lo, hi, _u = e["inputs"][0]
        Xg = np.linspace(lo, hi, 200).reshape(-1, 1)
    else:
        Xg = np.column_stack([g.uniform(lo, hi, 200)
                              for _nm, lo, hi, _u in e["inputs"]])
    return X, y, y_clean, Xg, e["f"](Xg)


def one_minus_r2(y, p):
    v = float(np.var(y)) or 1e-30
    with np.errstate(all="ignore"):
        e = float(np.mean((np.asarray(p, dtype=float) - y) ** 2) / v)
    return e if np.isfinite(e) else 1e30


def structure(entry, scaler, Xtr, ytr_clean, Xg, yg):
    """1 - R² on the noiseless grid after refitting the entry's constants on
    the noiseless training targets with the engine's own finishing step, in
    the engine's internal variables (phase1_bench._structure)."""
    import gp_elite.core as C
    node = entry.eval_node if (getattr(entry, "eval_node", None) is not None
                               and entry.y_scale != 1.0) else entry.node
    ys = float(getattr(entry, "y_scale", 1.0) or 1.0)
    sc = getattr(entry, "scaler", None) or scaler
    xs_tr = sc.transform(Xtr) if sc is not None else Xtr
    xs_g = sc.transform(Xg) if sc is not None else Xg
    cfg = C.make_cfg_nd(n_features=Xtr.shape[1])
    y_int = np.asarray(ytr_clean, dtype=float) / ys
    with redirect_stdout(io.StringIO()), np.errstate(all="ignore"):
        fitted = C._lm_to_convergence(node.copy(), xs_tr, y_int, cfg)
        tree = fitted if fitted is not None else node.copy()
        tree = C._refit_scaling(tree, xs_tr, y_int)
        p = np.asarray(C.evaluate_vector(tree, xs_g), dtype=float) * ys
    return one_minus_r2(yg, p)


def worker(job):
    import warnings
    import gp_elite
    from gp_elite import symbolic_regression
    _k, e = experiment(job["exp"])
    X, y, y_clean, Xg, yg = data(job["exp"], job["n"], job["noise"],
                                 job["draw"])
    names = [nm for nm, _lo, _hi, _u in e["inputs"]]
    kw = dict(feature_names=names, operators=e["pool"], seed=job["draw"],
              parallel=False)
    if job["arm"] == "units":
        kw.update(units={nm: dict(u) for nm, _lo, _hi, u in e["inputs"]},
                  target_units=dict(e["target"]),
                  unknown_constant=e["unknown"])
    # [1.2] the generations the sequential loop runs, counted from outside
    import gp_elite.core as C
    gens = [0]
    orig_isl = C.evolve_island

    def counted(*a, **k):
        g = a[3] if len(a) > 3 else k.get("generation", 0)
        gens[0] = max(gens[0], int(g) + 1)
        return orig_isl(*a, **k)
    C.evolve_island = counted
    t0 = time.time()
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = symbolic_regression(X, y, **kw)
    dt = time.time() - t0
    C.evolve_island = orig_isl
    rec = dict(job)
    try:
        rec["err_law"] = structure(r, r.scaler, X, y_clean, Xg, yg)
    except Exception as exc:                           # noqa: BLE001
        rec["err_law"], rec["law_error"] = 1e30, repr(exc)[:200]
    front = []
    for ent in list(getattr(r, "pareto", None) or []):
        try:
            se = structure(ent, r.scaler, X, y_clean, Xg, yg)
        except Exception:                              # noqa: BLE001
            se = 1e30
        front.append(dict(size=int(ent.size), err_law=se,
                          expr=str(ent.expression)[:160]))
    passing = [f["size"] for f in front if f["err_law"] < 1e-9]
    rec.update(
        law=bool(rec["err_law"] < 1e-9),
        front_law=bool(rec["err_law"] < 1e-9 or passing),
        front_law_size=min(passing) if passing else None,
        err_grid=one_minus_r2(yg, r.predict(Xg)),
        size=int(r.size), expr=str(r.expression)[:200], time=round(dt, 2),
        front=front, engine_version=gp_elite.__version__,
        engine_file=gp_elite.__file__,
        pythonhashseed=os.environ.get("PYTHONHASHSEED"),
        date=time.strftime("%Y-%m-%dT%H:%M:%S"))
    rec["useful"] = bool(rec["err_grid"] <= 0.01)
    # [1.2] the generations run, the stop on patience if any (H1), and
    # 1 - R² of the model on the training rows (for C1)
    rec["generations"] = gens[0]
    rec["patience_stop"] = getattr(C, "TRACE").value.get("patience")
    with np.errstate(all="ignore"):
        p_tr = np.asarray(r.predict(X), dtype=float)
    e_tr = one_minus_r2(y, p_tr)
    rec["err_train"] = float(e_tr) if np.isfinite(e_tr) else 1e30
    # [1.3] the guarantee of units= on the model returned (campaign A1,
    # benchmarks/results_1.3/PLAN.md), as phase1_bench.py records it
    if job["arm"] == "units":
        from gp_elite.dimensions import check_dimensions
        ok, msg = check_dimensions(
            r.node, {i: dict(u) for i, (_nm, _lo, _hi, u) in enumerate(e["inputs"])},
            dict(e["target"]))
        rec["units_ok"], rec["units_msg"] = bool(ok), msg[:120]
    return rec


def all_jobs(draws=DRAWS, exp_set="tp"):
    """[1.2] `draws` replaces the draws 0 to 4 (--draws), for a confirmation
    on new draws; the default gives the jobs of the diagnostic. [1.4]
    `exp_set` "tpt10" gives those of the frozen test set (--set)."""
    return [dict(exp=e["key"], n=n, noise=nz, draw=d, arm=a)
            for a in ARMS for e in SETS[exp_set] for n in SIZES
            for nz in NOISES for d in draws]


def key(j):
    return (j["arm"], j["exp"], j["n"], j["noise"], j["draw"])


def _done(out):
    done = set()
    if os.path.exists(out):
        with open(out, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    done.add(key(json.loads(line)))
    return done


def _keep(j, arm, exps):
    """The jobs a run keeps: its arm, and [1.3] its experiments."""
    return ((arm is None or j["arm"] == arm)
            and (exps is None or j["exp"] in exps))


def run(python, out, workers, arm=None, draws=DRAWS, exps=None,
        exp_set="tp"):
    done = _done(out)
    jobs = [j for j in all_jobs(draws, exp_set) if key(j) not in done
            and _keep(j, arm, exps)]
    print("%d jobs to run, %d already done" % (len(jobs), len(done)))
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)

    def one(j, python=python):
        p = subprocess.run([python, "-I", os.path.abspath(__file__), "worker",
                            json.dumps(j)], capture_output=True, text=True,
                           env=env, cwd="/")
        lines = [ln for ln in p.stdout.splitlines() if ln.startswith("{")]
        if p.returncode != 0 or not lines:
            return dict(j, crash=True, stderr=p.stderr[-500:])
        return json.loads(lines[-1])

    with ThreadPoolExecutor(workers) as ex, open(out, "a", encoding="utf-8") as fh:
        for i, rec in enumerate(ex.map(one, jobs)):
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            if (i + 1) % 20 == 0:
                print("%d/%d %s" % (i + 1, len(jobs), time.strftime("%H:%M:%S")))
                sys.stdout.flush()


def run_paired(pythons, outs, workers, arm=None, draws=DRAWS, exps=None,
               exp_set="tp"):
    """Each job with every engine at the same time (one process per fit), so
    that their times compare; `workers` jobs at a time."""
    dones = [_done(o) for o in outs]
    jobs = [j for j in all_jobs(draws, exp_set) if _keep(j, arm, exps)
            and any(key(j) not in d for d in dones)]
    print("%d jobs to run with %d engines" % (len(jobs), len(pythons)))
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)

    def one(j, python):
        p = subprocess.run([python, "-I", os.path.abspath(__file__), "worker",
                            json.dumps(j)], capture_output=True, text=True,
                           env=env, cwd="/")
        lines = [ln for ln in p.stdout.splitlines() if ln.startswith("{")]
        if p.returncode != 0 or not lines:
            return dict(j, crash=True, stderr=p.stderr[-500:])
        return json.loads(lines[-1])

    def both(j):
        with ThreadPoolExecutor(len(pythons)) as ex:
            return list(ex.map(lambda py: one(j, py), pythons))

    fhs = [open(o, "a", encoding="utf-8") for o in outs]
    try:
        with ThreadPoolExecutor(workers) as ex:
            for i, recs in enumerate(ex.map(both, jobs)):
                for fh, rec in zip(fhs, recs):
                    fh.write(json.dumps(rec) + "\n")
                    fh.flush()
                if (i + 1) % 10 == 0:
                    print("%d/%d %s" % (i + 1, len(jobs), time.strftime("%H:%M:%S")))
                    sys.stdout.flush()
    finally:
        for fh in fhs:
            fh.close()


def summary(path):
    recs = [json.loads(ln) for ln in open(path, encoding="utf-8") if ln.strip()]
    by = {}
    for r in recs:
        by.setdefault((r["arm"], r["n"], r["noise"], r["exp"]), []).append(r)
    crashes = sum(1 for r in recs if r.get("crash"))
    print("%d fits, %d crashes, engine %s" % (len(recs), crashes, sorted(
        {r.get("engine_version") for r in recs if not r.get("crash")})))
    if recs and recs[0]["exp"] in [e["key"] for e in EXPERIMENTS_T]:
        return summary_t(recs, by)          # [1.4] the frozen test set
    for arm in ARMS:
        for n in SIZES:
            for nz in NOISES:
                print("\n== arm %s, %d points, %d %% noise  (law / front / "
                      "useful, of 5 draws; median size returned / of the law "
                      "on the front; median time)" % (arm, n, round(100 * nz)))
                counted = 0
                for e in EXPERIMENTS:
                    rr = [r for r in by.get((arm, n, nz, e["key"]), [])
                          if not r.get("crash")]
                    if not rr:
                        continue
                    law = sum(r["law"] for r in rr)
                    fr = sum(r["front_law"] for r in rr)
                    us = sum(r["useful"] for r in rr)
                    fs = [r["front_law_size"] for r in rr
                          if r.get("front_law_size")]
                    ok = fr >= 3
                    if ok and e["key"] in REACHABLE_PLAIN:
                        counted += 1
                    print("  %-16s %d / %d / %d   size %4.0f / %-4s  %5.1f s  %s"
                          % (e["key"], law, fr, us,
                             np.median([r["size"] for r in rr]),
                             ("%d" % np.median(fs)) if fs else "-",
                             np.median([r["time"] for r in rr]),
                             "counts" if ok else ""))
                print("  experiments that count (law or front in >= 3 of 5), "
                      "of the 9 reachable without units: %d" % counted)
    for n in SIZES:
        c = 0
        for e in EXPERIMENTS:
            if e["key"] not in REACHABLE_PLAIN:
                continue
            rr = [r for r in by.get(("plain", n, 0.02, e["key"]), [])
                  if not r.get("crash")]
            c += sum(r["front_law"] for r in rr) >= 3
        print("\nreading, plain arm, 2 %% noise, %d points: %d of 9" % (n, c))


def summary_t(recs, by):
    """[1.4] The table of counts of TPT10: by arm, number of points and
    noise, the fits of each experiment with the law / with the law on the
    front / with a useful model; then the law by experiment, and in all."""
    for arm in ARMS:
        for n in SIZES:
            for nz in NOISES:
                print("\n== TPT10, arm %s, %d points, %d %% noise  (law / "
                      "front / useful, of the draws; median size; median "
                      "time)" % (arm, n, round(100 * nz)))
                for e in EXPERIMENTS_T:
                    rr = [r for r in by.get((arm, n, nz, e["key"]), [])
                          if not r.get("crash")]
                    if not rr:
                        continue
                    print("  %-13s %d / %d / %d  of %d   size %4.0f  %5.1f s"
                          % (e["key"], sum(r["law"] for r in rr),
                             sum(r["front_law"] for r in rr),
                             sum(r["useful"] for r in rr), len(rr),
                             np.median([r["size"] for r in rr]),
                             np.median([r["time"] for r in rr])))
    ok = [r for r in recs if not r.get("crash")]
    print("\n== TPT10, the law by experiment (fits with the law, of the "
          "fits run)")
    print("  %-13s %-9s %-9s" % ("experiment", "plain", "units"))
    for e in EXPERIMENTS_T:
        cells = []
        for arm in ARMS:
            rr = [r for r in ok if r["arm"] == arm and r["exp"] == e["key"]]
            cells.append("%d of %d" % (sum(r["law"] for r in rr), len(rr)))
        print("  %-13s %-9s %-9s%s" % (
            e["key"], cells[0], cells[1],
            "" if e["key"] in REACHABLE_UNITS_T
            else "  (not within reach under units)"))
    for arm in ARMS:
        rr = [r for r in ok if r["arm"] == arm]
        t = np.array([r["time"] for r in rr], dtype=float)
        line = "  arm %-5s: law %d, front %d, useful %d, of %d fits" % (
            arm, sum(r["law"] for r in rr), sum(r["front_law"] for r in rr),
            sum(r["useful"] for r in rr), len(rr))
        if len(t):
            line += "; median time %.1f s" % float(np.median(t))
        if arm == "units":
            wr = [r for r in rr if r["exp"] in REACHABLE_UNITS_T]
            line += "; within reach: law %d of %d; units ok %d of %d" % (
                sum(r["law"] for r in wr), len(wr),
                sum(1 for r in rr if r.get("units_ok")),
                sum(1 for r in rr if "units_ok" in r))
        print(line)


def constants(path):
    """The physical constant deduced by the units arm where the law came
    back: g from the pendulum (T = c*sqrt(L), g = (2*pi/c)^2) and from free
    fall (d = c*t^2, g = 2c), R from the ideal gas (P = c*n*T/V). Read off
    the leading coefficient of the returned formula, in the raw variables.
    Added after the run (it decides nothing)."""
    import math
    import re
    recs = [json.loads(ln) for ln in open(path, encoding="utf-8") if ln.strip()]
    out = {}
    for r in recs:
        if r.get("crash") or r["arm"] != "units" or not r["law"] \
                or r["exp"] not in ("pendule", "chute", "gaz"):
            continue
        m = re.match(r"^\s*([0-9.eE+-]+)\s*\*", r["expr"])
        if not m:
            continue
        c = float(m.group(1))
        val, true = {"pendule": ((2 * math.pi / c) ** 2, 9.81),
                     "chute": (2 * c, 9.81),
                     "gaz": (c, 8.314)}[r["exp"]]
        out.setdefault((r["exp"], r["n"], r["noise"]), []).append(
            100.0 * (val / true - 1.0))
    print("\n== constants deduced by the units arm (relative error, %)")
    for k in sorted(out):
        v = [abs(x) for x in out[k]]
        print("  %-8s %2d points %d %% noise: %d fits, median %.1f %%, "
              "largest %.1f %%" % (k[0], k[1], round(100 * k[2]), len(v),
                                   float(np.median(v)), max(v)))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--python", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--arm", choices=ARMS)
    r.add_argument("--draws", default=None)
    r.add_argument("--experiments", default=None)
    r.add_argument("--set", dest="exp_set", choices=sorted(SETS),
                   default="tp")
    rp = sub.add_parser("run-paired")
    rp.add_argument("--python", action="append", required=True)
    rp.add_argument("--out", action="append", required=True)
    rp.add_argument("--workers", type=int, default=2)
    rp.add_argument("--arm", choices=ARMS)
    rp.add_argument("--draws", default=None)
    rp.add_argument("--experiments", default=None)
    rp.add_argument("--set", dest="exp_set", choices=sorted(SETS),
                    default="tp")
    w = sub.add_parser("worker")
    w.add_argument("job")
    s = sub.add_parser("summary")
    s.add_argument("path")
    a = ap.parse_args()
    draws = (tuple(int(x) for x in a.draws.split(","))
             if getattr(a, "draws", None) else DRAWS)
    exps = (a.experiments.split(",") if getattr(a, "experiments", None)
            else None)
    if a.cmd == "run":
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        run(a.python, a.out, a.workers, a.arm, draws, exps, a.exp_set)
    elif a.cmd == "run-paired":
        for o in a.out:
            os.makedirs(os.path.dirname(os.path.abspath(o)), exist_ok=True)
        run_paired(a.python, a.out, a.workers, a.arm, draws, exps,
                   a.exp_set)
    elif a.cmd == "worker":
        sys.path.insert(0, HERE)
        print(json.dumps(worker(json.loads(a.job))))
    else:
        summary(a.path)
        with open(a.path, encoding="utf-8") as fh:
            first = json.loads(fh.readline())
        if first["exp"] in [e["key"] for e in EXPERIMENTS]:
            constants(a.path)


if __name__ == "__main__":
    main()
