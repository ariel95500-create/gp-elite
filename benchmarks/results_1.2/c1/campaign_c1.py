"""Campaign C1 of plan 1.2: the candidate with H1 and C1 (PYTHONPATH),
under the API defaults, against the records of campaign H1 for the same
fits (the candidate with H1 alone, h1/campaign/).

Fits: the units arm of the TP diagnostic, draws 0 to 9 (400 fits), and the
kinds ufeyn, ufeyn_n1 and ufeyn_n10 of bench D, seeds 0 to 4 (615 fits).
Each fit goes through the bench's own worker (tp_diagnostic.worker,
phase1_bench.run_one) and records beside the bench's own fields:
  - expr_11: the formula of the model as the candidate with H1 alone prints
    it (X1 switched off for that one call of formula.raw_formula), to compare
    with the records of campaign H1;
  - the units check kept on the result: whether it warned, the two errors,
    the formula without units, and (TP) whether that formula is the law by
    the diagnostic's test.

One process per fit, PYTHONHASHSEED=0. Records outside the repository
(/home/user/c1_records), copied in at checkpoints.

  python benchmarks/results_1.2/c1/campaign_c1.py run --python /venv11p/bin/python --part tp|d
  python benchmarks/results_1.2/c1/campaign_c1.py compare
"""
import argparse
import collections
import io
import json
import os
import statistics as S
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
RECORDS = "/home/user/c1_records"
WITHIN_REACH = ("chute", "pendule", "puissance", "gaz", "eclairement", "ressort")
LIMITED = ("rc", "refroidissement", "lentille")


def one(job):
    import warnings
    import gp_elite
    import gp_elite.api as API
    import gp_elite.formula as FM
    orig_b = API._build_raw_formula
    calls = []

    def both(node, scaler, X_raw, names, predictions=None):
        new = orig_b(node, scaler, X_raw, names, predictions=predictions)
        keep = FM._exponentials_as_such
        FM._exponentials_as_such = lambda t, X: None
        try:
            old = orig_b(node, scaler, X_raw, names, predictions=predictions)
        finally:
            FM._exponentials_as_such = keep
        calls.append(old[1])
        return new
    API._build_raw_formula = both
    orig = gp_elite.symbolic_regression
    cap = {}

    def call(X, y, **kw):
        with warnings.catch_warnings(record=True) as W:
            warnings.simplefilter("always")
            r = orig(X, y, **kw)
        cap.update(r=r, warns=[str(w.message) for w in W
                               if "under units" in str(w.message)])
        return r
    gp_elite.symbolic_regression = call       # the workers import it per call
    if job["bench"] == "tp":
        import tp_diagnostic as TP
        j = {k: job[k] for k in ("exp", "n", "noise", "draw", "arm")}
        rec = TP.worker(j)
        rec.pop("front", None)
    else:
        import phase1_bench as P1
        rec = P1.run_one({k: job[k] for k in ("kind", "problem", "index",
                                              "split", "seed", "defaults")})
    r = cap["r"]
    uc = r.units_check
    rec.update(bench=job["bench"], expr_11=calls[0][:200],
               expr_full=r.expression, check_ran=uc is not None,
               warned=None if uc is None else uc.warned,
               warnings=cap["warns"],
               expression_without_units=None if uc is None else uc.expression,
               error_units=None if uc is None else uc.error_units,
               error_without_units=None if uc is None else uc.error_without_units,
               engine_file=gp_elite.__file__)
    if job["bench"] == "tp" and uc is not None:
        _k, e = TP.experiment(job["exp"])
        X, y, y_clean, Xg, yg = TP.data(job["exp"], job["n"], job["noise"],
                                        job["draw"])
        try:
            se = TP.structure(uc.result, uc.result.scaler, X, y_clean, Xg, yg)
        except Exception as exc:                   # noqa: BLE001
            se, rec["law_without_units_error"] = 1e30, repr(exc)[:200]
        rec["law_without_units"] = bool(se < 1e-9)
    rec["date"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return rec


def jobs(part):
    if part == "tp":
        import tp_diagnostic as TP
        return [dict(j, bench="tp") for j in TP.all_jobs(draws=tuple(range(10)))
                if j["arm"] == "units"]
    import phase1_bench as P1
    return [dict(j, bench="d", defaults=True) for j in P1.all_jobs(with_units=True)
            if j["kind"] in ("ufeyn", "ufeyn_n1", "ufeyn_n10")]


def key(j):
    return json.dumps({k: j.get(k) for k in ("bench", "exp", "n", "noise", "draw",
                                              "arm", "kind", "problem", "split",
                                              "seed")}, sort_keys=True)


def drive(python, workers, part):
    os.makedirs(RECORDS, exist_ok=True)
    out = os.path.join(RECORDS, "%s_C1.jsonl" % part)
    done = set()
    if os.path.exists(out):
        done = {key(json.loads(l)) for l in open(out) if l.strip()}
    todo = [j for j in jobs(part) if key(j) not in done]
    print("%d jobs to run, %d already done" % (len(todo), len(done)), flush=True)
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
    t0, n = time.time(), 0
    with ThreadPoolExecutor(workers) as ex, open(out, "a") as fh:
        for f in as_completed([ex.submit(run, j) for j in todo]):
            fh.write(json.dumps(f.result()) + "\n")
            fh.flush()
            n += 1
            if n % 25 == 0:
                print("%d done, %d s elapsed, %d left" % (n, time.time() - t0,
                                                          len(todo) - n), flush=True)
    print("all done", flush=True)


def load(path):
    return [json.loads(l) for l in open(path) if l.strip()] if os.path.exists(path) else []


def name(r):
    if r["bench"] == "tp":
        return "%s %d pts %d %% draw %d" % (r["exp"], r["n"], round(100 * r["noise"]),
                                            r["draw"])
    return "%s %s seed %d" % (r["kind"], r["problem"], r["seed"])


def compare():
    T = load(os.path.join(HERE, "tp_C1.jsonl"))
    D = load(os.path.join(HERE, "d_C1.jsonl"))
    HT = {}
    for nm in ("tp_H1.jsonl", "tp_H1_conf.jsonl"):
        for r in load(os.path.join(CAMPAIGN, nm)):
            if r["arm"] == "units":
                HT[key(dict(r, bench="tp"))] = r
    HD = {key(dict(r, bench="d")): r for r in load(os.path.join(CAMPAIGN, "D_H1.jsonl"))
          if r["kind"].startswith("ufeyn")}
    A = [r for nm in ("tp_A.jsonl", "tp_A_conf.jsonl")
         for r in load(os.path.join(CAMPAIGN, nm)) if r["arm"] == "units"]
    crash = [r for r in T + D if r.get("status") == "CRASH"]
    print("## Campaign C1 (%d TP fits, %d fits of D); crashes: %d\n"
          % (len(T), len(D), len(crash)))
    for r in crash:
        print("- crash: %s: %s" % (name(r), r.get("error", "")[-200:]))
    T = [r for r in T if r.get("status") != "CRASH"]
    D = [r for r in D if r.get("status") != "CRASH"]

    # 1. same models
    diff = []
    for r in T:
        h = HT.get(key(r))
        if not (h and r["expr_11"] == h["expr"] and r.get("err_train") == h.get("err_train")
                and r["law"] == h["law"]):
            diff.append((r, h))
    for r in D:
        h = HD.get(key(r))
        if not (h and r["expr_11"][:160] == h["expr"] and r.get("err") == h.get("err")
                and r.get("units_ok") == h.get("units_ok")):
            diff.append((r, h))
    c1 = not diff and not crash and len(T) == 400 and len(D) == 615
    print("Criterion 1, same models: the model under units is the one of the "
          "candidate with H1 alone (formula without X1, and the error on the "
          "training rows for TP, on the test rows for D, both computed from "
          "the predictions): %d of %d: %s" % (len(T) + len(D) - len(diff),
                                             len(T) + len(D),
                                             "HOLDS" if c1 else "FAILS"))
    for r, h in diff:
        print("- differs: %s: %s | campaign H1 %s" % (
            name(r), r["expr_11"][:70], (h or {}).get("expr", "(none)")[:70]))
    ran = sum(bool(r["check_ran"]) for r in T + D)
    print("\nThe check ran in %d of %d fits.\n" % (ran, len(T) + len(D)))

    # 2. no message where units hold
    hold = [r for r in T if r["draw"] >= 5 and r["exp"] in WITHIN_REACH + ("snell",)]
    msg_hold = [r for r in hold if r["warned"]]
    exact_msg = [r for r in D if r["kind"] == "ufeyn" and r.get("status") == "EXACT"
                 and r["warned"]]
    c2 = len(hold) == 140 and len(msg_hold) <= 2 and not exact_msg
    print("Criterion 2, no message where units hold: the six laws within reach "
          "and Snell's law, draws 5 to 9: a message in %d of %d fits (at most 2); "
          "U41 without noise, a message on an exact fit: %d: %s"
          % (len(msg_hold), len(hold), len(exact_msg), "HOLDS" if c2 else "FAILS"))
    for r in msg_hold + exact_msg:
        print("- %s: %.3g under units, %.3g without: %s" % (
            name(r), r["error_units"], r["error_without_units"],
            r["expression_without_units"][:90]))

    # 3. a message where units limit
    lim = [r for r in T if r["draw"] >= 5 and r["exp"] in LIMITED]
    with_law = [r for r in lim if r.get("law_without_units")]
    missed = [r for r in with_law if not r["warned"]]
    n_msg = sum(bool(r["warned"]) for r in lim)
    c3 = len(lim) == 60 and not missed and n_msg >= 45
    print("\nCriterion 3, a message where units limit: the capacitor, cooling "
          "and the lens, draws 5 to 9: a message in %d of %d fits (at least 45); "
          "the fit without units returns the law in %d, of which %d without a "
          "message: %s" % (n_msg, len(lim), len(with_law), len(missed),
                           "HOLDS" if c3 else "FAILS"))
    for r in lim:
        if not r["warned"]:
            print("- no message: %s: %.3g under units, %.3g without (law without "
                  "units %s): %s" % (name(r), r["error_units"], r["error_without_units"],
                                     r.get("law_without_units"),
                                     r["expression_without_units"][:80]))

    # 4. time
    tc = S.median(r["time"] for r in T)
    ta = S.median(r["time"] for r in A)
    c4 = tc <= ta / 2
    print("\nCriterion 4, time: median of a units fit of TP with the check %.1f s "
          "against %.1f s for 1.1.0 (campaign H1, arm A, draws 0 to 9; ratio %.2f, "
          "at most 0.5): %s" % (tc, ta, tc / ta, "HOLDS" if c4 else "FAILS"))
    for lo, hi in ((0, 4), (5, 9)):
        a = [r["time"] for r in A if lo <= r["draw"] <= hi]
        c = [r["time"] for r in T if lo <= r["draw"] <= hi]
        print("- draws %d to %d: %.1f s against %.1f s" % (lo, hi, S.median(c),
                                                           S.median(a)))
    h1t = [h["time"] for h in HT.values()]
    print("- the candidate with H1 alone, same fits: %.1f s" % S.median(h1t))

    # beside
    print("\n## Beside the criteria\n")
    print("Messages per experiment of TP (draws 0 to 4 | draws 5 to 9, of 20 each):\n")
    print("| experiment | draws 0-4 | draws 5-9 | fit without units has the law (0-9) |")
    print("|---|---|---|---|")
    for e in WITHIN_REACH + ("snell",) + LIMITED:
        a = sum(bool(r["warned"]) for r in T if r["exp"] == e and r["draw"] <= 4)
        b = sum(bool(r["warned"]) for r in T if r["exp"] == e and r["draw"] >= 5)
        lw = sum(bool(r.get("law_without_units")) for r in T if r["exp"] == e)
        print("| %s | %d | %d | %d of 40 |" % (e, a, b, lw))
    print("\nMessages on D:\n")
    for k in ("ufeyn", "ufeyn_n1", "ufeyn_n10"):
        L = [r for r in D if r["kind"] == k]
        print("- %s: %d of %d" % (k, sum(bool(r["warned"]) for r in L), len(L)))
    print("\nEach message, with the formula without units it names:\n")
    for r in sorted([r for r in T + D if r["warned"]], key=name):
        print("- %s: %.3g under units, %.3g without; under units %s | without %s" % (
            name(r), r["error_units"], r["error_without_units"], r["expr_full"][:60],
            r["expression_without_units"][:80]))
    print("\n## Verdict\n")
    res = dict(c1=c1, c2=c2, c3=c3, c4=c4)
    for k in sorted(res):
        print("- criterion %s: %s" % (k[1:], "HOLDS" if res[k] else "FAILS"))
    print("\nC1 %s" % ("ADOPTED: every criterion holds" if all(res.values())
                       else "NOT ADOPTED"))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--python", required=True)
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--part", choices=("tp", "d"), required=True)
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
        drive(a.python, a.workers, a.part)


if __name__ == "__main__":
    main()
