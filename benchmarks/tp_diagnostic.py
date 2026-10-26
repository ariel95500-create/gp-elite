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
SIZES = (10, 20)
NOISES = (0.02, 0.05)
DRAWS = (0, 1, 2, 3, 4)
ARMS = ("plain", "units")


def experiment(key):
    for k, e in enumerate(EXPERIMENTS):
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
    t0 = time.time()
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = symbolic_regression(X, y, **kw)
    dt = time.time() - t0
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
    return rec


def all_jobs():
    return [dict(exp=e["key"], n=n, noise=nz, draw=d, arm=a)
            for a in ARMS for e in EXPERIMENTS for n in SIZES
            for nz in NOISES for d in DRAWS]


def key(j):
    return (j["arm"], j["exp"], j["n"], j["noise"], j["draw"])


def run(python, out, workers):
    done = set()
    if os.path.exists(out):
        with open(out, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    done.add(key(json.loads(line)))
    jobs = [j for j in all_jobs() if key(j) not in done]
    print("%d jobs to run, %d already done" % (len(jobs), len(done)))
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)

    def one(j):
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


def summary(path):
    recs = [json.loads(ln) for ln in open(path, encoding="utf-8") if ln.strip()]
    by = {}
    for r in recs:
        by.setdefault((r["arm"], r["n"], r["noise"], r["exp"]), []).append(r)
    crashes = sum(1 for r in recs if r.get("crash"))
    print("%d fits, %d crashes, engine %s" % (len(recs), crashes, sorted(
        {r.get("engine_version") for r in recs if not r.get("crash")})))
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


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--python", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, default=4)
    w = sub.add_parser("worker")
    w.add_argument("job")
    s = sub.add_parser("summary")
    s.add_argument("path")
    a = ap.parse_args()
    if a.cmd == "run":
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        run(a.python, a.out, a.workers)
    elif a.cmd == "worker":
        sys.path.insert(0, HERE)
        print(json.dumps(worker(json.loads(a.job))))
    else:
        summary(a.path)


if __name__ == "__main__":
    main()
