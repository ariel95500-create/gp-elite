"""Phase 2 measurements: A (flag off) against F1 (core._GUARD_STRICT on).

See benchmarks/results_0.9/PLAN_PHASE2.md. Both arms run the engine of this
checkout (PYTHONPATH = repository root); the arm only sets the flag. Each fit
runs in its own process (data, budget and records as
benchmarks/phase1_bench.py); the two arms of a job run side by side so that
they see the same load. The run resumes.

Usage, from the repository root:
  python benchmarks/phase2_bench.py run trial --python <python> \
         --out benchmarks/results_0.9/phase2_trial_F1.jsonl --pairs 2
  python benchmarks/phase2_bench.py summary trial benchmarks/results_0.9/phase2_trial_F1.jsonl
"""
import argparse
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
ARMS = ("A", "F1")


def trial_jobs():
    out = []
    for s in range(5):
        out.append(dict(kind="feyn", problem="II.35.18", index=35,
                        split="test", seed=s, group="targeted"))
    for k in range(5):
        out.append(dict(kind="realraw", problem="nikuradse_1",
                        split="fold%d" % k, seed=0, group="targeted"))
    for s in range(5):
        out.append(dict(kind="realraw", problem="228_elusage", split="ood",
                        seed=s, group="targeted"))
    for name, i in (("I.8.14", 6), ("II.2.42", 28)):
        for s in range(5):
            out.append(dict(kind="feyn", problem=name, index=i, split="test",
                            seed=s, group="control"))
    for name in ("210_cloud", "561_cpu"):
        for k in range(5):
            out.append(dict(kind="real", problem=name, split="fold%d" % k,
                            seed=0, group="real"))
    return out


def campaign_jobs():
    import phase1_bench as P
    return [dict(j, group=j["kind"]) for j in P.all_jobs()
            if j["kind"] in ("feyn", "real", "realraw")]


JOBS = {"trial": trial_jobs, "campaign": campaign_jobs}


def key(j):
    return (j["arm"], j["kind"], j["problem"], j["split"], j["seed"])


def run_arm(job):
    import gp_elite.core as C
    import phase1_bench as P
    C._GUARD_STRICT = job["arm"] == "F1"
    rec = P.run_one(job)
    rec["guard_strict"] = bool(C._GUARD_STRICT)
    rec["rejected_by_guard"] = int(C.TRACE.count.get("candidats_rejetes_garde", 0))
    return rec


def drive(which, python, out, pairs):
    done = set()
    if os.path.exists(out):
        for line in open(out):
            if line.strip():
                done.add(key(json.loads(line)))
    todo = []
    for j in JOBS[which]():
        for arm in ARMS:
            jj = dict(j, arm=arm)
            if key(jj) not in done:
                todo.append(jj)
    print("%d fits to run, %d done" % (len(todo), len(done)), flush=True)
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               PYTHONPATH=ROOT)
    running, n = [], 0
    while todo or running:
        while todo and len(running) < 2 * pairs:
            j = todo.pop(0)
            p = subprocess.Popen([python, os.path.abspath(__file__), "one",
                                  json.dumps(j)], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True, env=env,
                                 cwd=ROOT)
            running.append((j, p))
        time.sleep(0.2)
        still = []
        for j, p in running:
            if p.poll() is None:
                still.append((j, p))
                continue
            so, se = p.communicate()
            lines = [l for l in so.splitlines() if l.startswith("{")]
            if p.returncode == 0 and lines:
                rec = json.loads(lines[-1])
            else:
                rec = dict(j, status="CRASH", err=1e30, r2=-1e30,
                           error=(se or so)[-400:])
            with open(out, "a") as fh:
                fh.write(json.dumps(rec) + "\n")
            n += 1
            if n % 10 == 0:
                print("%d recorded, %d left" % (n, len(todo) + len(still)),
                      flush=True)
        running = still


def _pairs(recs):
    by = {}
    for r in recs:
        by[(r["kind"], r["problem"], r["split"], r["seed"])] = by.get(
            (r["kind"], r["problem"], r["split"], r["seed"]), {})
        by[(r["kind"], r["problem"], r["split"], r["seed"])][r["arm"]] = r
    return {k: v for k, v in by.items() if all(a in v for a in ARMS)}


def summary_trial(path):
    recs = [json.loads(l) for l in open(path) if l.strip()]
    pairs = _pairs(recs)
    print("%d records, %d complete pairs" % (len(recs), len(pairs)))
    for arm in ARMS:
        rr = [v[arm] for v in pairs.values()]
        print("%-3s median generations %.0f, median time %.1f s, rejected by"
              " the guard (median) %.0f" % (
                  arm, np.median([r.get("generations", 0) for r in rr]),
                  np.median([r.get("time", 0) for r in rr]),
                  np.median([r.get("rejected_by_guard", 0) for r in rr])))
    tg = [v for v in pairs.values() if v["A"]["group"] == "targeted"]
    inex = {a: sum(1 for v in tg if v[a].get("formula_exact") is False)
            for a in ARMS}
    c1 = inex["F1"] <= 2
    print("1. targeted fits (%d): inexact formulas A %d, F1 %d -> %s" % (
        len(tg), inex["A"], inex["F1"], "PASS" if c1 else "FAIL"))
    ct = [v for v in pairs.values() if v["A"]["group"] == "control"]
    lost = [k for k, v in pairs.items() if v["A"]["group"] == "control"
            and v["A"].get("status") == "EXACT" and v["F1"].get("status") != "EXACT"]
    exA = sum(1 for v in ct if v["A"].get("status") == "EXACT")
    exF = sum(1 for v in ct if v["F1"].get("status") == "EXACT")
    c2 = not lost
    print("2. controls (%d): exact A %d, F1 %d, lost %s -> %s" % (
        len(ct), exA, exF, lost, "PASS" if c2 else "FAIL"))
    rl = [v for v in pairs.values() if v["A"]["kind"] in ("real", "realraw")]
    d = [v["F1"]["r2"] - v["A"]["r2"] for v in rl]
    new_col = [(v["A"]["problem"], v["A"]["split"], v["A"]["seed"]) for v in rl
               if v["F1"]["r2"] < 0 <= v["A"]["r2"]]
    c3 = np.median(d) >= -0.01 and not new_col
    print("3. real fits (%d): median paired R² difference %+.4f, mean %+.4g,"
          " worst %+.4g; collapses A %d, F1 %d, new in F1 %s -> %s" % (
              len(rl), np.median(d), np.mean(d), min(d),
              sum(1 for v in rl if v["A"]["r2"] < 0),
              sum(1 for v in rl if v["F1"]["r2"] < 0), new_col,
              "PASS" if c3 else "FAIL"))
    print("TRIAL %s" % ("CONCLUSIVE" if (c1 and c2 and c3) else "NOT CONCLUSIVE"))
    print("\nper fit (A | F1): status or R², formula_exact")
    for k in sorted(pairs, key=lambda k: (pairs[k]["A"]["group"], k)):
        v = pairs[k]
        def cell(r):
            s = r.get("status") or "R² %.4g" % r["r2"]
            return "%s %s" % (s, "exact-formula" if r.get("formula_exact")
                              else "INEXACT" if r.get("formula_exact") is False
                              else "")
        print("  %-9s %-12s %-6s s%d  %-28s | %s" % (
            v["A"]["group"], k[1], k[2], k[3], cell(v["A"]), cell(v["F1"])))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("which", choices=sorted(JOBS))
    r.add_argument("--python", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--pairs", type=int, default=2)
    o = sub.add_parser("one")
    o.add_argument("job")
    s = sub.add_parser("summary")
    s.add_argument("which", choices=sorted(JOBS))
    s.add_argument("path")
    a = ap.parse_args()
    if a.cmd == "run":
        drive(a.which, a.python, a.out, a.pairs)
    elif a.cmd == "one":
        print(json.dumps(run_arm(json.loads(a.job))))
    elif a.which == "trial":
        summary_trial(a.path)
    else:
        sys.exit("campaign summary: see PLAN_PHASE2.md criteria (to write)")


if __name__ == "__main__":
    main()
