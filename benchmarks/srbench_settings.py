"""The settings SRBench runs GP_ELITE with (benchmarks/results_1.1/srbench_settings/PLAN.md).

Three settings of the same engine, each given the same budget through the code
path SRBench uses (est.max_time = B, then est.fit(X, y)):

  W0   the wrapper as published, experiment/methods/gp-elite/regressor.py of
       cavalab/srbench at 2aabbb6, imported from a clone (not copied: the file
       is part of SRBench, under its licence); its blob hash is checked first
  W1   one call of symbolic_regression with restarts=10 and the other
       settings of W0, time_limit = 0.9 * B
  W2   the wrapper's loop with generations=1000 per call

All three with parallel=False and random_state = the seed of the job, on the
decision bench of phase1_bench.py (F41, F41N1, F41N10, R6, R7raw), scored as
phase1_bench.py scores its own fits. Each job runs the three settings at the
same time, one process each, PYTHONHASHSEED=0 and one BLAS thread. The run
resumes: jobs already in the output files are skipped.

Usage, from the repository root:
  python benchmarks/srbench_settings.py run --python /venv11p/bin/python \\
         --srbench /home/user/cavalab/srbench --outdir DIR [--max-seconds S]
  python benchmarks/srbench_settings.py trial ...   (the three jobs of the trial)
"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import time
from contextlib import redirect_stdout

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import phase1_bench as P  # noqa: E402  (data, structure, job list)

BUDGET = 120.0
ARMS = ("W0", "W1", "W2")
KINDS = ("feyn", "feyn_n1", "feyn_n10", "real", "realraw")
WRAPPER = "experiment/methods/gp-elite/regressor.py"
WRAPPER_BLOB = "cbf170f9be251dc44169ceba8ff4be3cb0289619"   # at 2aabbb6


def jobs():
    return [j for j in P.all_jobs() if j["kind"] in KINDS]


def trial_jobs():
    js = jobs()
    pick = [("feyn", "I.12.1", 0), ("feyn", "I.16.6", 0)]
    out = [j for j in js if (j["kind"], j["problem"], j["seed"]) in pick
           and j["split"] == "test"]
    out += [j for j in js if j["kind"] == "real" and j["split"] == "fold0"][:1]
    return out


def _git_blob(path):
    data = open(path, "rb").read()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _wrapper(srbench):
    path = os.path.join(srbench, WRAPPER)
    blob = _git_blob(path)
    if blob != WRAPPER_BLOB:
        raise RuntimeError("wrapper %s has blob %s, not %s" % (path, blob, WRAPPER_BLOB))
    spec = importlib.util.spec_from_file_location("srbench_gp_elite_regressor", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fit(arm, Xtr, ytr, seed, srbench, budget):
    """The fitted SRResult of one setting, and the number of calls it made."""
    from gp_elite import symbolic_regression
    if arm == "W1":
        names = ["X%d" % i for i in range(Xtr.shape[1])]
        r = symbolic_regression(
            Xtr, np.ravel(ytr), feature_names=names, operators="physical",
            normalize="auto", generations=60, speed="fast",
            validation_split=0.20, restarts=10, robust=False, parallel=False,
            time_limit=0.90 * budget, seed=seed)
        return r, 1
    mod = _wrapper(srbench)
    params = mod.est.get_params()
    if arm == "W2":
        params["generations"] = 1000
    params.update(parallel=False, random_state=seed)
    est = mod.GPEliteSRBench(**params)
    est.max_time = budget
    calls = [0]
    orig = mod.symbolic_regression

    def counted(*a, **k):
        calls[0] += 1
        return orig(*a, **k)
    mod.symbolic_regression = counted
    est.fit(Xtr, ytr)
    return est.model_, calls[0]


def run_one(job, arm, srbench, budget):
    import warnings
    import gp_elite
    import decision_bench as D

    Xtr, ytr, Xte, yte, Xo, yo, names, pool, clean = P._data(job)
    t0 = time.time()
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r, calls = _fit(arm, Xtr, ytr, job["seed"], srbench, budget)
    dt = time.time() - t0

    rec = dict(job, arm=arm, budget=budget)
    e = D.one_minus_r2(yte, r.predict(Xte))
    rec.update(time=round(dt, 2), calls=calls, size=int(r.size), err=e,
               r2=1.0 - e, formula_exact=r.formula_exact,
               time_limit_reached=bool(getattr(r, "time_limit_reached", False)),
               expr=r.expression[:160], engine_file=gp_elite.__file__,
               engine_version=getattr(gp_elite, "__version__", "?"))
    if job["kind"] in P.FEYN_KINDS:
        rec["status"] = ("EXACT" if e < 1e-9 else "NEAR" if e < 1e-3
                         else "MISS")
    if Xo is not None and yo is not None and len(yo) >= 20:
        rec["err_ood"] = D.one_minus_r2(yo, r.predict(Xo))
        rec["n_ood"] = int(len(yo))
    if job["kind"] in P.NOISE:
        try:
            se = P._structure(r, Xtr, clean, Xte, yte)
        except Exception as exc:              # counted, never hidden
            se, rec["structure_error"] = 1e30, repr(exc)[:200]
        rec["err_structure"] = se
        rec["structure"] = bool(se < 1e-9)
    rec.update(date=time.strftime("%Y-%m-%dT%H:%M:%S"),
               pythonhashseed=os.environ.get("PYTHONHASHSEED"),
               python=sys.version.split()[0], numpy=np.__version__)
    return rec


def _done(path):
    d = set()
    if os.path.exists(path):
        with open(path) as fh:
            for line in fh:
                if line.strip():
                    d.add(P.key(json.loads(line)))
    return d


def drive(python, srbench, outdir, todo_jobs, budget, max_seconds=None):
    """Each job with the three settings at the same time, one job at a time."""
    os.makedirs(outdir, exist_ok=True)
    outs = {a: os.path.join(outdir, "%s.jsonl" % a) for a in ARMS}
    done = {a: _done(outs[a]) for a in ARMS}
    todo = [j for j in todo_jobs if any(P.key(j) not in done[a] for a in ARMS)]
    print("%d jobs to run with %d settings" % (len(todo), len(ARMS)), flush=True)
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)
    t_start = time.time()
    for n, j in enumerate(todo, 1):
        if max_seconds is not None and time.time() - t_start > max_seconds:
            print("time slice over: %d jobs left for the next call"
                  % (len(todo) - n + 1), flush=True)
            return
        procs = [(a, subprocess.Popen(
            [python, os.path.abspath(__file__), "one", json.dumps(j), a,
             srbench, str(budget)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            env=env, cwd=os.path.dirname(HERE)))
            for a in ARMS if P.key(j) not in done[a]]
        for a, p in procs:
            P._record(dict(j, arm=a, budget=budget), p, outs[a])
        if n % 25 == 0:
            print("%d jobs done, %.0f s elapsed, %d left" % (
                n, time.time() - t_start, len(todo) - n), flush=True)
    print("all done", flush=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "trial"):
        r = sub.add_parser(name)
        r.add_argument("--python", required=True)
        r.add_argument("--srbench", required=True)
        r.add_argument("--outdir", required=True)
        r.add_argument("--budget", type=float, default=BUDGET)
        r.add_argument("--max-seconds", type=float, default=None)
    o = sub.add_parser("one")
    o.add_argument("job")
    o.add_argument("arm", choices=ARMS)
    o.add_argument("srbench")
    o.add_argument("budget", type=float)
    a = ap.parse_args()
    if a.cmd == "one":
        print(json.dumps(run_one(json.loads(a.job), a.arm, a.srbench, a.budget)))
    else:
        js = jobs() if a.cmd == "run" else trial_jobs()
        drive(a.python, a.srbench, a.outdir, js, a.budget, a.max_seconds)


if __name__ == "__main__":
    main()
