"""Mechanics 1 and 2 of the correction of the typed start (plan 1.2, D0 done).

1. III.19.51 under units, as the U41 campaign runs it (time_limit=30), seed
   0, on the corrected engine: the fit ends within the limit, its model
   passes check_dimensions, and the law is exact.
2. U41 at seed 0 with 20 generations and no time limit, and the units arm of
   the TP diagnostic at draw 0 under the API defaults, on the 1.1.0 wheel and
   on the corrected engine: every model but III.19.51 the same (the printed
   expression and the predictions, bit for bit).

The engine is chosen by PYTHONPATH: the wheel of /venv11p without it, the
repository with it. One process per fit, PYTHONHASHSEED=0.

  python benchmarks/results_1.2/fix/mechanics_fix.py run --python /venv11p/bin/python
  python benchmarks/results_1.2/fix/mechanics_fix.py compare
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

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", ".."))
ROOT = os.path.dirname(BENCH)
sys.path.insert(0, BENCH)


def one(job):
    import warnings
    import numpy as np
    import gp_elite
    if job["test"] == "m1":
        import phase1_bench as P1
        rec = P1.run_one(dict(kind="ufeyn", problem=job["problem"],
                              index=job["index"], split="test", seed=0))
        rec.update(test="m1", engine=job["engine"])
        return rec
    holder = {}
    if job["test"] == "u41":
        import decision_bench as D
        import units_table as U
        Xtr, ytr, Xte, _yte, _a, _b, names, pool = D.feyn_data(job["index"])
        units, tunits = U.units_of(job["problem"], names)
        t0 = time.time()
        with redirect_stdout(io.StringIO()), warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = gp_elite.symbolic_regression(
                Xtr, ytr, generations=20, seed=0, parallel=False,
                verbose=False, operators=pool, feature_names=names,
                units=units, target_units=tunits)
        holder.update(r=r, X=Xte)
    else:
        import tp_diagnostic as TP
        orig = gp_elite.symbolic_regression

        def keep(X, y, **kw):
            r = orig(X, y, **kw)
            holder.update(r=r, X=X)
            return r
        gp_elite.symbolic_regression = keep    # tp_diagnostic imports it in worker()
        t0 = time.time()
        TP.worker({k: job[k] for k in ("exp", "n", "noise", "draw", "arm")})
    r = holder["r"]
    with np.errstate(all="ignore"):
        p = np.asarray(r.predict(holder["X"]), dtype=float)
    return dict(job, time=round(time.time() - t0, 2), expr=r.expression,
                pred=[float(v).hex() for v in p],
                engine_file=gp_elite.__file__,
                engine_version=gp_elite.__version__,
                pythonhashseed=os.environ.get("PYTHONHASHSEED"),
                date=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


def jobs():
    import feynman_bench as F
    import tp_diagnostic as TP
    out = []
    i19 = [i for i, p in enumerate(F.PROBS) if p[0] == "III.19.51"][0]
    out.append(dict(test="m1", engine="fix", problem="III.19.51", index=i19))
    for eng in ("wheel", "fix"):
        out += [dict(test="u41", engine=eng, problem=p[0], index=i)
                for i, p in enumerate(F.PROBS)]
        out += [dict(test="tp", engine=eng, **j) for j in TP.all_jobs()
                if j["arm"] == "units" and j["draw"] == 0]
    out.sort(key=lambda j: j.get("problem") != "III.19.51")   # the slow one first
    return out


def key(j):
    return json.dumps({k: j.get(k) for k in ("test", "engine", "problem", "exp",
                                              "n", "noise", "draw")},
                      sort_keys=True)


def drive(python, workers):
    out = os.path.join(HERE, "mechanics_fix.jsonl")
    done = set()
    if os.path.exists(out):
        done = {key(json.loads(l)) for l in open(out) if l.strip()}
    todo = [j for j in jobs() if key(j) not in done]
    print("%d jobs to run" % len(todo), flush=True)

    def run(j):
        env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
                   OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
                   PYTHONDONTWRITEBYTECODE="1")
        env.pop("PYTHONPATH", None)
        if j["engine"] == "fix":
            env["PYTHONPATH"] = ROOT
        p = subprocess.run([python, os.path.abspath(__file__), "one",
                            json.dumps(j)], capture_output=True, text=True,
                           env=env, cwd=BENCH)
        lines = [l for l in p.stdout.splitlines() if l.startswith("{")]
        return json.loads(lines[-1]) if (p.returncode == 0 and lines) else \
            dict(j, status="CRASH", error=(p.stderr or p.stdout)[-400:])
    n = 0
    with ThreadPoolExecutor(workers) as ex:
        futs = [ex.submit(run, j) for j in todo]
        with open(out, "a") as fh:
            from concurrent.futures import as_completed
            for f in as_completed(futs):
                fh.write(json.dumps(f.result()) + "\n")
                fh.flush()
                n += 1
                if n % 20 == 0:
                    print("%d done" % n, flush=True)
    print("all done", flush=True)


def compare():
    R = [json.loads(l) for l in open(os.path.join(HERE, "mechanics_fix.jsonl"))]
    crash = [r for r in R if r.get("status") == "CRASH"]
    print("%d records, %d crashes" % (len(R), len(crash)))
    for r in crash:
        print("  CRASH", key(r), r["error"][-200:])
    m1 = [r for r in R if r["test"] == "m1" and r.get("status") != "CRASH"]
    for r in m1:
        print("\nMechanic 1, III.19.51 under units, time_limit=30, seed 0, "
              "corrected engine: %s, %.1f s, %d generations, units ok %s, "
              "time limit reached %s\n  %s" % (
                  r["status"], r["time"], r["generations"], r["units_ok"],
                  r["time_limit_reached"], r["expr"]))
        print("  mechanic 1 %s" % ("HOLDS" if (r["status"] == "EXACT" and
                                             r["units_ok"] and r["time"] < 40)
                                   else "FAILS"))
    for test in ("u41", "tp"):
        A = {key(dict(r, engine="")): r for r in R if r["test"] == test
             and r["engine"] == "wheel" and r.get("status") != "CRASH"}
        B = {key(dict(r, engine="")): r for r in R if r["test"] == test
             and r["engine"] == "fix" and r.get("status") != "CRASH"}
        same, diff = 0, []
        for k in sorted(set(A) & set(B)):
            a, b = A[k], B[k]
            if a["expr"] == b["expr"] and a["pred"] == b["pred"]:
                same += 1
            else:
                diff.append((a, b))
        print("\nMechanic 2, %s: %d pairs, %d the same, %d different" % (
            test, len(set(A) & set(B)), same, len(diff)))
        for a, b in diff:
            print("  %s: wheel %s (%.1f s) | corrected %s (%.1f s)" % (
                a.get("problem") or "%s %d %.2f" % (a["exp"], a["n"], a["noise"]),
                a["expr"][:60], a["time"], b["expr"][:60], b["time"]))
        others = [a for a, b in diff if a.get("problem") != "III.19.51"]
        print("  mechanic 2 (%s) %s" % (test, "HOLDS" if not others and
                                        len(set(A) & set(B)) == len(A) == len(B)
                                        else "FAILS"))


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
