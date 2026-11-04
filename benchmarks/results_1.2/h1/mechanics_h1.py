"""Mechanics 3 and 4 of H1 (plan 1.2), on the candidate engine (PYTHONPATH).

3. Default calls on the TP diagnostic, draw 0, both arms (80 fits, among
   them the gas law at 10 points and 2 % noise): the loop ends on the
   patience, at the generation prototype 4 recorded for that fit at P = 30,
   and the model is the one prototype 4 recorded (its printed expression).
   Prototype 4 applied the same rule from outside the 1.1.0 wheel
   (prototype/patience_try.py).
4. The gas law call with parallel=True: the stop acts in the parallel loop.

One process per fit, PYTHONHASHSEED=0.

  PYTHONPATH=<repo> python benchmarks/results_1.2/h1/mechanics_h1.py run --python /venv11p/bin/python
  python benchmarks/results_1.2/h1/mechanics_h1.py compare
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
PROTO = os.path.join(HERE, "..", "prototype", "patience.jsonl")


def one(job):
    import gp_elite
    import gp_elite.core as C
    import tp_diagnostic as TP
    gens = [0]
    orig_isl = C.evolve_island

    def counted(*a, **k):
        g = a[3] if len(a) > 3 else k.get("generation", 0)
        gens[0] = max(gens[0], int(g) + 1)
        return orig_isl(*a, **k)
    C.evolve_island = counted
    orig = gp_elite.symbolic_regression

    def call(X, y, **kw):
        if job.get("parallel"):
            kw["parallel"] = True
        return orig(X, y, **kw)
    gp_elite.symbolic_regression = call       # tp_diagnostic imports it in worker()
    t0 = time.time()
    rec = TP.worker({k: job[k] for k in ("exp", "n", "noise", "draw", "arm")})
    rec.pop("front", None)
    rec.update(job, time=round(time.time() - t0, 2), generations=gens[0],
               patience_trace=C.TRACE.value.get("patience"),
               engine_file=gp_elite.__file__,
               pythonhashseed=os.environ.get("PYTHONHASHSEED"),
               date=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    return rec


def jobs():
    import tp_diagnostic as TP
    out = [dict(j) for j in TP.all_jobs() if j["draw"] == 0]
    out.append(dict(exp="gaz", n=10, noise=0.02, draw=0, arm="plain",
                    parallel=True))
    return out


def key(j):
    return json.dumps({k: j.get(k) for k in ("exp", "n", "noise", "draw", "arm",
                                              "parallel")}, sort_keys=True)


def drive(python, workers):
    out = os.path.join(HERE, "mechanics_h1.jsonl")
    done = set()
    if os.path.exists(out):
        done = {key(json.loads(l)) for l in open(out) if l.strip()}
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
    with ThreadPoolExecutor(workers) as ex, open(out, "a") as fh:
        for f in as_completed([ex.submit(run, j) for j in todo]):
            fh.write(json.dumps(f.result()) + "\n")
            fh.flush()
    print("all done", flush=True)


def compare():
    R = [json.loads(l) for l in open(os.path.join(HERE, "mechanics_h1.jsonl"))]
    P = {key(dict(r, parallel=None)): r for r in map(json.loads, open(PROTO))
         if r["patience"] == 30}
    crash = [r for r in R if r.get("status") == "CRASH"]
    print("%d records, %d crashes" % (len(R), len(crash)))
    seq = [r for r in R if not r.get("parallel") and r.get("status") != "CRASH"]
    same_model = same_stop = 0
    bad = []
    for r in seq:
        p = P[key(dict(r, parallel=None))]
        ge = r["patience_trace"]
        stop = int(ge.rsplit(" ", 1)[1].rstrip(")")) if ge else None
        sm = r["expr"] == p["expr"]
        ss = stop == p["stop_gen"]
        same_model += sm
        same_stop += ss
        if not (sm and ss):
            bad.append((r, p, stop))
    print("\nMechanic 3: %d default fits of the TP diagnostic at draw 0" % len(seq))
    print("  same model as prototype 4 at P = 30: %d of %d" % (same_model, len(seq)))
    print("  stop at the same generation: %d of %d" % (same_stop, len(seq)))
    for r, p, stop in bad:
        print("  differs: %s %s %d pts %.2f: engine stop %s, %s | prototype stop %s, %s"
              % (r["arm"], r["exp"], r["n"], r["noise"], stop, r["expr"][:50],
                 p["stop_gen"], p["expr"][:50]))
    gas = [r for r in seq if (r["exp"], r["n"], r["noise"], r["arm"]) ==
           ("gaz", 10, 0.02, "plain")]
    for r in gas:
        p = P[key(dict(r, parallel=None))]
        print("  gas law, plain, 10 pts, 2 %%, draw 0: stop %s (last gain at "
              "generation %s in prototype 4), %d generations run, %s" % (
                  r["patience_trace"], p["best_gen"], r["generations"], r["expr"]))
    print("  mechanic 3 %s" % ("HOLDS" if not bad and not crash else "FAILS"))
    par = [r for r in R if r.get("parallel") and r.get("status") != "CRASH"]
    for r in par:
        ok = bool(r["patience_trace"]) and "parallele" in r["patience_trace"]
        print("\nMechanic 4, gas law with parallel=True: trace %s, %.1f s, %s\n"
              "  mechanic 4 %s" % (r["patience_trace"], r["time"], r["expr"],
                                   "HOLDS" if ok else "FAILS"))


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
