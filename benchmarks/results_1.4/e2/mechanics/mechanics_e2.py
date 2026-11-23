# -*- coding: utf-8 -*-
"""Mechanics of E2, items 2 and 3 (benchmarks/results_1.4/PLAN.md, "Mechanics
of E2"), with the engine of the Python that runs it (the wheel of the
candidate with E2):

  2. on the exact data of the 41 equations of F41 (the training rows of the
     fit at seed 0, in the engine's variables), the finder of E2 returns no
     form with its exact threshold; where the noise-tolerant stage runs, no
     seed of E2 is placed. The 82 bounded fits of F41 and U41 (20
     generations, no time limit) are run with the candidate and compared
     with the records of the base made in the mechanics of N2 (1.3.0, whose
     models the base with S1 returns on these tables, s1/mechanics).
  3. on the 13 real fits (R6 and R7raw at fold 0), the candidates of E2 in
     the noise-tolerant stage, with their scores.

  python mechanics_e2.py run OUT_DIR
  python mechanics_e2.py report OUT_DIR > mechanics_e2.txt
"""
import io
import json
import os
import subprocess
import sys
import warnings
from contextlib import redirect_stdout

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
N2M = os.path.join(BENCH, "results_1.4", "n2", "mechanics", "mechanics.py")


def stage_probe(job):
    """The finder of E2 on the training rows of the fit, and the seeds of E2
    placed (exact or noise-tolerant), read by wrapping the finder."""
    sys.path.insert(0, BENCH)
    import phase1_bench as B
    import gp_elite
    import gp_elite.core as C
    from gp_elite import symbolic_regression
    Xtr, ytr, _a, _b, _c, _d, names, pool, _clean = B._data(job)
    seen = dict(exact=[], tolerant=[], placed_tolerant=[])
    orig = C._elem_aexp_forms

    def noted(X, y, tol=C._BINOM_TOL):
        out = orig(X, y, tol=tol)
        if tol < 1e-3:
            seen["exact"] += [str(f) for f in out]
            seen.setdefault("rows", int(len(y)))
        else:
            seen["tolerant"] += [str(f) for f in out]
        return out
    C._elem_aexp_forms = noted
    kw = dict(generations=1, seed=job["seed"], parallel=False, verbose=False,
              operators=pool)
    if names is not None:
        kw["feature_names"] = names
    if job["kind"] == "ufeyn":
        import units_table as U
        units, tunits = U.units_of(job["problem"], names)
        kw.update(units=units, target_units=tunits)
    with redirect_stdout(io.StringIO()), warnings.catch_warnings():
        warnings.simplefilter("ignore")
        symbolic_regression(Xtr, ytr, **kw)
    tol_text = C.TRACE.value.get("tolerant_seed") or ""
    # a seed of E2 is exp(c·g) alone (f = 1): read in the trace of the stage
    seen["tolerant_seed"] = tol_text
    seen["elementary_seed"] = C.TRACE.value.get("elementary_seed")
    return dict(job, engine=gp_elite.__file__, **seen)


def run(out_dir):
    from concurrent.futures import ThreadPoolExecutor
    os.makedirs(out_dir, exist_ok=True)
    sys.path.insert(0, os.path.dirname(N2M))
    sys.path.insert(1, BENCH)
    with redirect_stdout(io.StringIO()):
        import mechanics as N
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("PYTHONPATH", None)
    bounded = N._jobs_bounded()

    def fit(job):
        p = subprocess.run([sys.executable, "-I", N2M, "one-fit", "/nonexistent",
                            json.dumps(job)], capture_output=True, text=True,
                           env=env, cwd="/")
        lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
        return json.loads(lines[-1]) if p.returncode == 0 and lines else dict(job, crash=True)

    def probe(job):
        p = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "probe",
                            json.dumps(job)], capture_output=True, text=True,
                           env=env, cwd="/")
        lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
        return json.loads(lines[-1]) if p.returncode == 0 and lines else dict(
            job, crash=True, err=p.stderr[-300:])
    with ThreadPoolExecutor(4) as ex:
        fits = list(ex.map(fit, bounded))
        probes = list(ex.map(probe, bounded))
    for name, recs in (("bounded_e2.jsonl", fits), ("probe_e2.jsonl", probes)):
        with open(os.path.join(out_dir, name), "w") as fh:
            for r in recs:
                fh.write(json.dumps(r) + "\n")


def report(out_dir):
    base = {(r["kind"], r["problem"]): r for r in map(json.loads, open(os.path.join(
        BENCH, "results_1.4", "n2", "mechanics", "records", "bounded_1.3.0.jsonl")))}
    fits = {(r["kind"], r["problem"]): r for r in map(json.loads, open(
        os.path.join(out_dir, "bounded_e2.jsonl")))}
    probes = {(r["kind"], r["problem"]): r for r in map(json.loads, open(
        os.path.join(out_dir, "probe_e2.jsonl")))}
    print("engines: base %s; candidate %s" % (sorted({r.get("engine") for r in base.values()}),
                                               sorted({r.get("engine") for r in fits.values()})))
    print("crashes: %d" % sum(bool(r.get("crash")) for r in list(fits.values()) + list(probes.values())))
    print("\n== 2. Exact data")
    for kind in ("feyn", "ufeyn"):
        ks = [k for k in probes if k[0] == kind]
        ex = [k for k in ks if probes[k]["exact"]]
        print("  %s: the finder of E2 returns an exact form on %d of %d tables%s" % (
            kind, len(ex), len(ks), (": " + ", ".join(k[1] for k in ex)) if ex else ""))
        tol = [k for k in ks if probes[k]["tolerant"]]
        print("     noise-tolerant forms of E2 made on %d tables%s" % (
            len(tol), (": " + ", ".join(k[1] for k in tol)) if tol else ""))
    same = [k for k in base if k[0] in ("feyn", "ufeyn") and
            (base[k]["expr"], base[k]["err"]) == (fits[k]["expr"], fits[k]["err"])]
    diff = [k for k in base if k[0] in ("feyn", "ufeyn") and k not in same]
    print("  the 82 bounded fits of F41 and U41: the model of the base in %d of 82" % len(same))
    for k in diff:
        print("    DIFFERS %s %s: %s / %s" % (k[0], k[1], base[k]["expr"][:70], fits[k]["expr"][:70]))
    print("\n== 3. Real data: the candidates of E2 in the noise-tolerant stage")
    for k in sorted(probes):
        if k[0] in ("real", "realraw"):
            r = probes[k]
            print("  %-8s %-24s forms of E2 made: %d; seeds placed by the stage: %s" % (
                k[0], k[1], len(r["tolerant"]), r["tolerant_seed"][:120] or "none"))
    same_real = sum((base[k]["expr"], base[k]["err"]) == (fits[k]["expr"], fits[k]["err"])
                    for k in base if k[0] in ("real", "realraw"))
    print("  the 13 real bounded fits: the model of the base in %d of 13" % same_real)


if __name__ == "__main__":
    if sys.argv[1] == "probe":
        print(json.dumps(stage_probe(json.loads(sys.argv[2]))))
    elif sys.argv[1] == "run":
        run(sys.argv[2])
    else:
        report(sys.argv[2])
