"""Mechanics 1 and 3 of C1 (plan 1.2), on the candidate engine (PYTHONPATH).

1. Under units, the model returned, its formula, predict() on the training
   rows and check_dimensions are the same with units_check True and False,
   on the units arm of the TP diagnostic (draw 0, 40 fits) and on U41 seed 0
   (41 fits), both under the API defaults; a fit run after another in the
   same process returns the same as alone. Each job runs in two processes:
   "alone" fits with units_check=False; "pair" fits with units_check=True,
   then with units_check=False in the same process.
3. Default calls (units_check not given) on the capacitor and the pendulum
   of the TP diagnostic (units arm, 10 points, 2 %, draw 0): the warning
   comes on the capacitor and names an exponential formula; on the pendulum
   it does not.

Every fit goes through the bench's own worker (tp_diagnostic.worker,
phase1_bench.run_one); one process per job, PYTHONHASHSEED=0. The run
writes outside the repository (/home/user/c1_records); compare reads the
copy in this folder.

  python benchmarks/results_1.2/c1/mechanics_c1.py run --python /venv11p/bin/python
  python benchmarks/results_1.2/c1/mechanics_c1.py compare
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", ".."))
ROOT = os.path.dirname(BENCH)
sys.path.insert(0, BENCH)
OUT = os.path.join(HERE, "mechanics_c1.jsonl")          # the copy compared
RUN_OUT = "/home/user/c1_records/mechanics_c1.jsonl"    # written by run, outside the repo


def fit(job, units_check):
    """One fit through the bench's worker, with units_check passed (None:
    not passed), and what the mechanics compare."""
    import warnings
    import numpy as np
    import gp_elite
    from gp_elite.dimensions import check_dimensions
    orig = gp_elite.symbolic_regression
    cap = {}

    def call(X, y, **kw):
        if units_check is not None:
            kw["units_check"] = units_check
        with warnings.catch_warnings(record=True) as W:
            warnings.simplefilter("always")
            r = orig(X, y, **kw)
        cap.update(r=r, X=X, kw=kw, warns=[str(w.message) for w in W
                                           if "under units" in str(w.message)])
        return r
    gp_elite.symbolic_regression = call       # the workers import it per call
    try:
        if job["bench"] == "tp":
            import tp_diagnostic as TP
            rec = TP.worker({k: job[k] for k in ("exp", "n", "noise", "draw", "arm")})
            rec.pop("front", None)
        else:
            import phase1_bench as P1
            rec = P1.run_one({k: job[k] for k in ("kind", "problem", "index",
                                                  "split", "seed", "defaults")})
    finally:
        gp_elite.symbolic_regression = orig
    r, kw = cap["r"], cap["kw"]
    names = kw["feature_names"]
    ok, msg = check_dimensions(r.node, {i: kw["units"][n] for i, n in
                                        enumerate(names)}, kw["target_units"])
    with np.errstate(all="ignore"):
        p = np.asarray(r.predict(cap["X"]), dtype=float)
    uc = r.units_check
    return dict(units_check=units_check, expression=r.expression,
                formula_exact=r.formula_exact, sympy=r.sympy(),
                predictions=[float(v).hex() for v in p],
                dims_ok=bool(ok), dims_msg=msg,
                check_ran=uc is not None,
                warned=None if uc is None else uc.warned,
                expression_without_units=None if uc is None else uc.expression,
                error_units=None if uc is None else uc.error_units,
                error_without_units=None if uc is None else uc.error_without_units,
                warnings=cap["warns"], time=rec.get("time"))


def one(job):
    t0 = time.time()
    fits = [fit(job, uc) for uc in job["sequence"]]
    import gp_elite
    return dict(job, fits=fits, total_time=round(time.time() - t0, 2),
                engine_file=gp_elite.__file__,
                pythonhashseed=os.environ.get("PYTHONHASHSEED"),
                date=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


def jobs():
    import tp_diagnostic as TP
    import phase1_bench as P1
    base = []
    for j in TP.all_jobs(draws=(0,)):
        if j["arm"] == "units":
            base.append(dict(j, bench="tp"))
    for j in P1.all_jobs(with_units=True):
        if j["kind"] == "ufeyn" and j["seed"] == 0:
            base.append(dict(j, bench="d", defaults=True))
    out = []
    for j in base:
        out.append(dict(j, mode="alone", sequence=[False]))
        out.append(dict(j, mode="pair", sequence=[True, False]))
    for exp in ("rc", "pendule"):
        out.append(dict(bench="tp", exp=exp, n=10, noise=0.02, draw=0,
                        arm="units", mode="default", sequence=[None]))
    return out


def key(j):
    return json.dumps({k: j.get(k) for k in ("bench", "exp", "n", "noise", "draw",
                                              "arm", "kind", "problem", "seed",
                                              "mode")}, sort_keys=True)


def drive(python, workers):
    os.makedirs(os.path.dirname(RUN_OUT), exist_ok=True)
    done = set()
    if os.path.exists(RUN_OUT):
        done = {key(json.loads(l)) for l in open(RUN_OUT) if l.strip()}
    todo = [j for j in jobs() if key(j) not in done]
    print("%d jobs to run" % len(todo), flush=True)
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=ROOT)

    def run(j):
        p = subprocess.run([python, os.path.abspath(__file__), "one",
                            json.dumps(j)], capture_output=True, text=True,
                           env=env, cwd=BENCH)
        lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
        return json.loads(lines[-1]) if (p.returncode == 0 and lines) else \
            dict(j, status="CRASH", error=(p.stderr or p.stdout)[-400:])
    n = 0
    with ThreadPoolExecutor(workers) as ex, open(RUN_OUT, "a") as fh:
        for f in as_completed([ex.submit(run, j) for j in todo]):
            fh.write(json.dumps(f.result()) + "\n")
            fh.flush()
            n += 1
            if n % 20 == 0:
                print("%d done" % n, flush=True)
    print("all done", flush=True)


SAME = ("expression", "formula_exact", "sympy", "predictions", "dims_ok", "dims_msg")


def name(j):
    if j["bench"] == "tp":
        return "TP %s %d pts %d %%" % (j["exp"], j["n"], round(100 * j["noise"]))
    return "U41 %s" % j["problem"]


def compare():
    R = [json.loads(l) for l in open(OUT) if l.strip()]
    crash = [r for r in R if r.get("status") == "CRASH"]
    print("%d records, %d crashes" % (len(R), len(crash)))
    for r in crash:
        print("  crash: %s %s: %s" % (name(r), r["mode"], r["error"][-200:]))
    R = [r for r in R if r.get("status") != "CRASH"]
    base = lambda r: key(dict(r, mode=None))
    alone = {base(r): r["fits"][0] for r in R if r["mode"] == "alone"}
    pair = {base(r): r["fits"] for r in R if r["mode"] == "pair"}
    jobs_ = {base(r): r for r in R if r["mode"] == "pair"}
    a_same = b_same = ran = 0
    bad = []
    for k, (t, f) in pair.items():
        a = alone.get(k)
        if a is None:
            continue
        sa = all(t[x] == a[x] for x in SAME)
        sb = all(f[x] == a[x] for x in SAME)
        a_same += sa
        b_same += sb
        ran += t["check_ran"] and not f["check_ran"] and not a["check_ran"]
        if not (sa and sb):
            bad.append((jobs_[k], [x for x in SAME if t[x] != a[x]],
                        [x for x in SAME if f[x] != a[x]]))
    n = len(pair)
    print("\nMechanic 1, on %d jobs (TP units arm draw 0, U41 seed 0):" % n)
    print("  units_check=True returns the model of units_check=False alone "
          "(formula, sympy, predictions on the training rows, check_dimensions): "
          "%d of %d" % (a_same, n))
    print("  units_check=False run after it in the same process returns the "
          "same as alone: %d of %d" % (b_same, n))
    print("  the check runs with True and not with False: %d of %d" % (ran, n))
    for j, da, db in bad:
        print("  differs: %s: True vs alone %s; after vs alone %s" % (name(j), da, db))
    ok1 = not crash and a_same == b_same == ran == n and n == 81
    print("  mechanic 1 %s" % ("HOLDS" if ok1 else "FAILS"))
    print("\nBeside: the warnings of units_check=True on these fits:")
    for k in sorted(pair, key=lambda k: name(jobs_[k])):
        t = pair[k][0]
        if t["warned"]:
            print("  %s: %.3g under units, %.3g without: %s" % (
                name(jobs_[k]), t["error_units"], t["error_without_units"],
                t["expression_without_units"][:90]))
    print("  (%d of %d fits)" % (sum(bool(p[0]["warned"]) for p in pair.values()), n))
    D = {r["exp"]: r["fits"][0] for r in R if r["mode"] == "default"}
    rc, pe = D.get("rc"), D.get("pendule")
    ok3 = bool(rc and pe and rc["warned"] and rc["warnings"]
               and "exp(" in rc["expression_without_units"]
               and rc["expression_without_units"][:40] in rc["warnings"][0]
               and pe["check_ran"] and not pe["warned"] and not pe["warnings"])
    print("\nMechanic 3, default calls, units arm, 10 points, 2 %, draw 0:")
    for nm, d in (("capacitor", rc), ("pendulum", pe)):
        if d:
            print("  %s: model %s; check ran %s, warned %s (%.3g under units, "
                  "%.3g without); formula without units %s" % (
                      nm, d["expression"], d["check_ran"], d["warned"],
                      d["error_units"], d["error_without_units"],
                      d["expression_without_units"]))
    if rc and rc["warnings"]:
        print("  the warning: %s" % rc["warnings"][0])
    print("  mechanic 3 %s" % ("HOLDS" if ok3 else "FAILS"))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--python", required=True)
    r.add_argument("--workers", type=int, default=4)
    o = sub.add_parser("one")
    o.add_argument("job")
    sub.add_parser("compare")
    a = ap.parse_args()
    if a.cmd == "one":
        buf = io.StringIO()
        with redirect_stdout(buf):
            rec = one(json.loads(a.job))
        print(json.dumps(rec, default=str))
    elif a.cmd == "compare":
        compare()
    else:
        drive(a.python, a.workers)


if __name__ == "__main__":
    main()
