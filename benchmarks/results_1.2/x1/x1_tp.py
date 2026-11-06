"""Check of X1 on TP (plan 1.2, "Change X1: the exponential written as such").

Every plain fit of the capacitor (rc) and of Newton's cooling
(refroidissement) of the TP diagnostic, draws 0 to 9, 10 and 20 points, 2 %
and 5 % noise (80 fits), under the API defaults, with the candidate engine
(PYTHONPATH). Each fit records the formula as printed (with X1) and the
formula 1.1 would print for the same model (X1 switched off for that one
call of formula.raw_formula), so that:

  - the model is the one of the H1 campaign: the formula without X1 is the
    one recorded in h1/campaign/tp_H1.jsonl (draws 0 to 4) and
    tp_H1_conf.jsonl (draws 5 to 9), with the same law flag and the same
    error on the training rows;
  - every fit whose model is an exponential of t (a + b * exp(k * t) or
    a + b * c^(k * t)) prints exp(-t / tau) and no power with a numeric base.

One process per fit, PYTHONHASHSEED=0.

  python benchmarks/results_1.2/x1/x1_tp.py run --python /venv11p/bin/python
  python benchmarks/results_1.2/x1/x1_tp.py compare
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", ".."))
ROOT = os.path.dirname(BENCH)
CAMPAIGN = os.path.join(HERE, "..", "h1", "campaign")
sys.path.insert(0, BENCH)
OUT = os.path.join(HERE, "x1_tp.jsonl")

NUM = r"-?[0-9.]+(?:e[-+]?[0-9]+)?"
EXP_OF_T = re.compile(r"^%s [+-] %s \* (?:exp\(%s \* t\)|%s\^\(%s \* t\))$"
                      % (NUM, NUM, NUM, NUM, NUM))
DECAY = re.compile(r"^%s [+-] %s \* exp\(-t / %s\)$" % (NUM, NUM, NUM))
NUMERIC_BASE = re.compile(r"(?<![\w)|.])%s\^" % NUM)


def one(job):
    import gp_elite
    import gp_elite.api as API
    import gp_elite.formula as FM
    import tp_diagnostic as TP
    orig = API._build_raw_formula
    calls = []

    def both(node, scaler, X_raw, names, predictions=None):
        new = orig(node, scaler, X_raw, names, predictions=predictions)
        keep = FM._exponentials_as_such
        FM._exponentials_as_such = lambda t, X: None
        try:
            old = orig(node, scaler, X_raw, names, predictions=predictions)
        finally:
            FM._exponentials_as_such = keep
        calls.append(dict(expr=new[1], expr_11=old[1],
                          exact=None if new[0] is None else new[0].exact,
                          exact_11=None if old[0] is None else old[0].exact))
        return new
    API._build_raw_formula = both
    t0 = time.time()
    rec = TP.worker(job)
    rec.pop("front", None)
    best = calls[0]                       # the returned model comes first
    rec.update(job, expr_full=best["expr"], expr_11=best["expr_11"],
               exact=best["exact"], exact_11=best["exact_11"],
               time=round(time.time() - t0, 2), engine_file=gp_elite.__file__,
               pythonhashseed=os.environ.get("PYTHONHASHSEED"),
               date=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    return rec


def jobs():
    import tp_diagnostic as TP
    return [j for j in TP.all_jobs(draws=tuple(range(10)))
            if j["arm"] == "plain" and j["exp"] in ("rc", "refroidissement")]


def key(j):
    return json.dumps({k: j.get(k) for k in ("exp", "n", "noise", "draw", "arm")},
                      sort_keys=True)


def drive(python, workers):
    done = set()
    if os.path.exists(OUT):
        done = {key(json.loads(l)) for l in open(OUT) if l.strip()}
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
    with ThreadPoolExecutor(workers) as ex, open(OUT, "a") as fh:
        for f in as_completed([ex.submit(run, j) for j in todo]):
            fh.write(json.dumps(f.result()) + "\n")
            fh.flush()
    print("all done", flush=True)


def compare():
    R = [json.loads(l) for l in open(OUT) if l.strip()]
    H = {}
    for name in ("tp_H1.jsonl", "tp_H1_conf.jsonl"):
        for l in open(os.path.join(CAMPAIGN, name)):
            r = json.loads(l)
            H[key(r)] = r
    crash = [r for r in R if r.get("status") == "CRASH"]
    print("%d fits, %d crashes" % (len(R), len(crash)))
    R = [r for r in R if r.get("status") != "CRASH"]
    same = [r for r in R if key(r) in H and r["expr_11"][:200] == H[key(r)]["expr"]
            and r["law"] == H[key(r)]["law"]
            and r.get("err_train") == H[key(r)].get("err_train")]
    print("\nThe model of the H1 campaign (formula without X1, law flag and "
          "training error equal): %d of %d" % (len(same), len(R)))
    for r in R:
        if r not in same:
            h = H.get(key(r), {})
            print("  differs: %s %d pts %d %% draw %d: %s | campaign %s"
                  % (r["exp"], r["n"], round(100 * r["noise"]), r["draw"],
                     r["expr_11"][:70], h.get("expr", "")[:70]))
    expo = [r for r in R if EXP_OF_T.match(r["expr_11"])]
    good = [r for r in expo if DECAY.match(r["expr_full"])
            and not NUMERIC_BASE.search(r["expr_full"])]
    print("\nFits whose model is an exponential of t: %d; they print "
          "exp(-t / tau) with no power of a number: %d of %d"
          % (len(expo), len(good), len(expo)))
    for r in sorted(expo, key=lambda r: (r["exp"], r["draw"], r["n"], r["noise"])):
        print("  %s %s %d pts %d %% draw %d: %s  ->  %s" % (
            "ok " if r in good else "BAD", r["exp"], r["n"],
            round(100 * r["noise"]), r["draw"], r["expr_11"], r["expr_full"]))
    rest = [r for r in R if r not in expo and NUMERIC_BASE.search(r["expr_full"])]
    print("\nOther fits that still print a power of a number: %d" % len(rest))
    for r in rest:
        print("  %s %d pts %d %% draw %d (formula exact %s): %s" % (
            r["exp"], r["n"], round(100 * r["noise"]), r["draw"], r["exact"],
            r["expr_full"]))
    changed = [r for r in R if r not in expo and r["expr_full"] != r["expr_11"]]
    print("\nOther fits whose printed formula changes: %d" % len(changed))
    for r in changed:
        print("  %s %d pts %d %% draw %d: %s  ->  %s" % (
            r["exp"], r["n"], round(100 * r["noise"]), r["draw"], r["expr_11"],
            r["expr_full"]))
    flags = [r for r in R if r["exact"] != r["exact_11"]]
    print("\nformula_exact changed by X1: %d" % len(flags))
    ok = not crash and len(same) == len(R) and len(good) == len(expo) and not flags
    print("\nCheck of X1 on TP %s" % ("HOLDS" if ok else "FAILS"))


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
