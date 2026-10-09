"""Phase 2 measurements: A (flags off) against a variant of the check.

F1: core._GUARD_STRICT and core._GUARD_SEARCH on (the check in the search and
at the final selection). F3: _GUARD_STRICT on, _GUARD_SEARCH off (the check at
the final selection only). F3R: F3 with _GUARD_CATCHUP on (the catch-up from
the final populations). The flags were removed from the engine after the
decision of 9 October 2026 (PLAN_PHASE2.md): run the F arms from commit
0038a29 and the G arms (G1, G1b) from commit 8330827, where they exist; the
script refuses to run without them. See
benchmarks/results_0.9/PLAN_PHASE2.md. Both
arms run the engine of this checkout (PYTHONPATH = repository root); the arm
only sets the flags. Each fit runs in its own process (data, budget and
records as benchmarks/phase1_bench.py); the two arms of a job run side by side
so that they see the same load. The run resumes.

Usage, from the repository root:
  python benchmarks/phase2_bench.py run trial --python <python> \
         --out benchmarks/results_0.9/phase2_trial_F1.jsonl --pairs 2
  python benchmarks/phase2_bench.py summary trial benchmarks/results_0.9/phase2_trial_F1.jsonl
  (trial3/campaign3: the same with F3, trial3r/campaign3r with F3R;
  run accepts --max-seconds)
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
BUDGET = 30.0


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


def diag_jobs():
    """After the trial (PLAN_PHASE2.md): the ten controls, F1 only, with the
    time F1 needs to reach the generations A reaches in 30 s (61/45)."""
    return [dict(j, time_limit=42.0) for j in trial_jobs()
            if j["group"] == "control"]


def g1_trial_jobs():
    """The targeted trial of G1 (PLAN_PHASE2.md): the 11 collapses of
    COLLAPSES.md, the 3 far-reaching fits of 561_cpu, the controls and the
    R6 folds of 210_cloud and 561_cpu."""
    out = []
    for kind, name, seed in (
            ("realraw", "228_elusage", 4), ("real", "228_elusage", 0),
            ("realraw", "228_elusage", 2), ("realraw", "210_cloud", 3),
            ("real", "561_cpu", 3), ("realraw", "228_elusage", 0),
            ("realraw", "nikuradse_1", 3), ("real", "228_elusage", 1),
            ("realraw", "210_cloud", 4), ("real", "210_cloud", 1),
            ("real", "228_elusage", 3)):
        out.append(dict(kind=kind, problem=name, split="ood", seed=seed,
                        group="collapse"))
    for kind, seed in (("real", 0), ("realraw", 0), ("realraw", 4)):
        out.append(dict(kind=kind, problem="561_cpu", split="ood", seed=seed,
                        group="far"))
    out += [j for j in trial_jobs() if j["group"] in ("control", "real")]
    return out


def confirm_jobs():
    """Confirmation of G1b on seeds never run (PLAN_PHASE2.md): the 65
    out-of-domain fits of R6 and R7raw with seeds 5 to 9, and their 65 folds
    with seed 5."""
    import decision_bench as D
    out = []
    for kind, names in (("real", D.REAL), ("realraw", D.REAL_RAW)):
        for n in names:
            for k in range(5):
                out.append(dict(kind=kind, problem=n, split="fold%d" % k,
                                seed=5, group=kind))
        for n in names:
            for s in range(5, 10):
                out.append(dict(kind=kind, problem=n, split="ood", seed=s,
                                group=kind))
    return out


# name: (jobs, arms)
RUNS = {"trial": (trial_jobs, ("A", "F1")),
        "campaign": (campaign_jobs, ("A", "F1")),
        "diag": (diag_jobs, ("F1",)),
        "trial3": (trial_jobs, ("A", "F3")),
        "campaign3": (campaign_jobs, ("A", "F3")),
        "trial3r": (trial_jobs, ("A", "F3R")),
        "campaign3r": (campaign_jobs, ("A", "F3R")),
        "trialg1": (g1_trial_jobs, ("A", "G1")),
        "campaigng1": (campaign_jobs, ("A", "G1")),
        "trialg1b": (g1_trial_jobs, ("A", "G1b")),
        "campaigng1b": (campaign_jobs, ("A", "G1b")),
        "confirmg1b": (confirm_jobs, ("A", "G1b"))}


def key(j):
    return (j["arm"], j["kind"], j["problem"], j["split"], j["seed"])


def run_arm(job):
    import gp_elite.core as C
    import phase1_bench as P
    if job["arm"] in ("F1", "F3", "F3R") and not hasattr(C, "_GUARD_STRICT"):
        sys.exit("the phase 2 flags are not in this engine: run from commit "
                 "0038a29 (benchmarks/results_0.9/PLAN_PHASE2.md)")
    if job["arm"] in ("G1", "G1b") and not hasattr(C, "_FAR_LINEAR"):
        sys.exit("the flags of G1 and G1b are not in this engine: run from "
                 "commit 8330827 (benchmarks/results_0.9/PLAN_PHASE2.md)")
    if hasattr(C, "_GUARD_STRICT"):
        C._GUARD_STRICT = job["arm"] in ("F1", "F3", "F3R")
        C._GUARD_SEARCH = job["arm"] not in ("F3", "F3R")
        C._GUARD_CATCHUP = job["arm"] == "F3R"
    if hasattr(C, "_FAR_GUARD"):
        C._FAR_GUARD = job["arm"] in ("G1", "G1b")
        C._FAR_EXT = 3.0 if job["arm"] == "G1b" else 1.0
    if hasattr(C, "_FAR_LINEAR"):
        C._FAR_LINEAR = job["arm"] == "G1b"
    if "time_limit" in job:
        P.TIME_LIMIT = float(job["time_limit"])
    rec = P.run_one(job)
    rec["guard_strict"] = bool(getattr(C, "_GUARD_STRICT", False))
    rec["guard_search"] = bool(getattr(C, "_GUARD_STRICT", False)
                               and getattr(C, "_GUARD_SEARCH", False))
    rec["far_guard"] = bool(getattr(C, "_FAR_GUARD", False))
    rec["far_ext"] = float(getattr(C, "_FAR_EXT", 0.0))
    rec["far_linear"] = bool(getattr(C, "_FAR_LINEAR", False))
    rec["far_rejected"] = int(C.TRACE.count.get("far_rejets", 0))
    rec["rejected_by_guard"] = int(C.TRACE.count.get("candidats_rejetes_garde", 0))
    rec["rejected_from_pool"] = int(C.TRACE.count.get("pool_rejets_garde", 0))
    rec["catchups"] = int(C.TRACE.count.get("rattrapages", 0))
    rec["catchup_offered"] = int(C.TRACE.count.get("rattrapage_proposes", 0))
    rec["catchup_s"] = C.TRACE.value.get("rattrapage_s")
    return rec


def drive(which, python, out, pairs, max_seconds=None):
    """Runs the fits not yet in `out`. With max_seconds, stops launching new
    fits after that time and returns once the running ones are recorded (the
    next call resumes)."""
    jobs, arms = RUNS[which]
    done = set()
    if os.path.exists(out):
        for line in open(out):
            if line.strip():
                done.add(key(json.loads(line)))
    todo = []
    for j in jobs():
        for arm in arms:
            jj = dict(j, arm=arm)
            if key(jj) not in done:
                todo.append(jj)
    print("%d fits to run, %d done" % (len(todo), len(done)), flush=True)
    env = dict(os.environ, PYTHONHASHSEED="0", OMP_NUM_THREADS="1",
               OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               PYTHONPATH=ROOT)
    running, n, t0 = [], 0, time.time()
    while todo or running:
        if max_seconds is not None and time.time() - t0 > max_seconds and todo:
            print("time slice over: %d fits left for the next call" % len(todo),
                  flush=True)
            todo = []
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
                print("%d recorded, %d left, %.0f s" % (
                    n, len(todo) + len(still), time.time() - t0), flush=True)
        running = still


def _pairs(recs, arms):
    by = {}
    for r in recs:
        by.setdefault((r["kind"], r["problem"], r["split"], r["seed"]),
                      {})[r["arm"]] = r
    return {k: v for k, v in by.items() if all(a in v for a in arms)}


def _r2(rr):
    return np.array([r["r2"] for r in rr], dtype=float)


def summary_trial(path, arms):
    A, B = arms
    recs = [json.loads(l) for l in open(path) if l.strip()]
    pairs = _pairs(recs, arms)
    print("%d records, %d complete pairs" % (len(recs), len(pairs)))
    for arm in arms:
        rr = [v[arm] for v in pairs.values()]
        print("%-3s median generations %.0f, median time %.1f s, rejected by"
              " the guard (median) %.0f" % (
                  arm, np.median([r.get("generations", 0) for r in rr]),
                  np.median([r.get("time", 0) for r in rr]),
                  np.median([r.get("rejected_by_guard", 0) for r in rr])),
              end="")
        print(", removed from the pool (median) %.0f" % np.median(
            [r["rejected_from_pool"] for r in rr]) if all(
                "rejected_from_pool" in r for r in rr) else "")
    tg = [v for v in pairs.values() if v[A]["group"] == "targeted"]
    inex = {a: sum(1 for v in tg if v[a].get("formula_exact") is False)
            for a in arms}
    c1 = inex[B] <= 2
    print("1. targeted fits (%d): inexact formulas %s %d, %s %d -> %s" % (
        len(tg), A, inex[A], B, inex[B], "PASS" if c1 else "FAIL"))
    ct = [v for v in pairs.values() if v[A]["group"] == "control"]
    lost = [k for k, v in pairs.items() if v[A]["group"] == "control"
            and v[A].get("status") == "EXACT" and v[B].get("status") != "EXACT"]
    exA = sum(1 for v in ct if v[A].get("status") == "EXACT")
    exB = sum(1 for v in ct if v[B].get("status") == "EXACT")
    c2 = not lost
    print("2. controls (%d): exact %s %d, %s %d, lost %s -> %s" % (
        len(ct), A, exA, B, exB, lost, "PASS" if c2 else "FAIL"))
    rl = [v for v in pairs.values() if v[A]["kind"] in ("real", "realraw")]
    d = [v[B]["r2"] - v[A]["r2"] for v in rl]
    new_col = [(v[A]["problem"], v[A]["split"], v[A]["seed"]) for v in rl
               if v[B]["r2"] < 0 <= v[A]["r2"]]
    c3 = np.median(d) >= -0.01 and not new_col
    print("3. real fits (%d): median paired R² difference %+.4f, mean %+.4g,"
          " worst %+.4g; collapses %s %d, %s %d, new in %s %s -> %s" % (
              len(rl), np.median(d), np.mean(d), min(d), A,
              sum(1 for v in rl if v[A]["r2"] < 0), B,
              sum(1 for v in rl if v[B]["r2"] < 0), B, new_col,
              "PASS" if c3 else "FAIL"))
    ok = c1 and c2 and c3
    if B in ("F3", "F3R"):       # the fourth criterion of the F3 plan
        wA, wB = min(v[A]["r2"] for v in rl), min(v[B]["r2"] for v in rl)
        c4 = wB >= wA
        print("4. real fits: worst R² %s %.4g, %s %.4g -> %s" % (
            A, wA, B, wB, "PASS" if c4 else "FAIL"))
        ok = ok and c4
    print("TRIAL %s" % ("CONCLUSIVE" if ok else "NOT CONCLUSIVE"))
    cu = [v[B] for v in pairs.values() if v[B].get("catchups")]
    if cu:
        print("catch-up ran in %d fits: %s" % (len(cu), ", ".join(
            "%s %s s%d (%d offered, %.2f s)" % (
                r["problem"], r["split"], r["seed"], r["catchup_offered"],
                r.get("catchup_s") or 0.0) for r in cu)))
    print("\nper fit (%s | %s): status or R², formula_exact" % (A, B))
    for k in sorted(pairs, key=lambda k: (pairs[k][A]["group"], k)):
        v = pairs[k]

        def cell(r):
            s = r.get("status") or "R² %.4g" % r["r2"]
            return "%s %s" % (s, "exact-formula" if r.get("formula_exact")
                              else "INEXACT" if r.get("formula_exact") is False
                              else "")
        print("  %-9s %-12s %-6s s%d  %-28s | %s" % (
            v[A]["group"], k[1], k[2], k[3], cell(v[A]), cell(v[B])))


def summary_campaign(path, arms):
    """The four adoption criteria of PLAN_PHASE2.md, then the facts reported
    beside them (means, medians, worst cases, time, generations)."""
    A, B = arms
    recs = [json.loads(l) for l in open(path) if l.strip()]
    pairs = _pairs(recs, arms)
    print("%d records, %d complete pairs, crashes %s" % (
        len(recs), len(pairs), {a: sum(1 for r in recs if r["arm"] == a and
                                       r.get("status") == "CRASH")
                                for a in arms}))
    feyn = [v for v in pairs.values() if v[A]["kind"] == "feyn"]
    real = [v for v in pairs.values() if v[A]["kind"] in ("real", "realraw")]
    folds = [v for v in real if v[A]["split"].startswith("fold")]
    ood = [v for v in real if v[A]["split"] == "ood"]
    r6f = [v for v in folds if v[A]["kind"] == "real"]

    fe = {a: sum(1 for v in real + feyn if v[a].get("formula_exact") is True)
          for a in arms}
    c1 = fe[B] == len(real) + len(feyn) == 335
    print("1. formula equal to the model, real %d + F41 %d fits: %s %d, %s %d"
          " -> %s" % (len(real), len(feyn), A, fe[A], B, fe[B],
                      "PASS" if c1 else "FAIL"))

    ex = {a: sum(1 for v in feyn if v[a].get("status") == "EXACT") for a in arms}
    lost = [(v[A]["problem"], v[A]["seed"]) for v in feyn
            if v[A].get("status") == "EXACT" and v[B].get("status") != "EXACT"]
    won = [(v[A]["problem"], v[A]["seed"]) for v in feyn
           if v[B].get("status") == "EXACT" and v[A].get("status") != "EXACT"]
    c2 = len(feyn) == 205 and ex[B] >= 82 and len(lost) <= 3
    print("2. F41 exact: %s %d, %s %d of %d; exact in %s only %d %s; in %s only"
          " %d %s -> %s" % (A, ex[A], B, ex[B], len(feyn), A, len(lost), lost,
                            B, len(won), won, "PASS" if c2 else "FAIL"))

    med6 = float(np.median(_r2([v[B] for v in r6f])))
    d = _r2([v[B] for v in folds]) - _r2([v[A] for v in folds])
    c3 = len(r6f) == 30 and len(folds) == 65 and med6 >= 0.804 \
        and np.median(d) >= -0.005
    print("3. R6 folds median R²: %s %.4f, %s %.4f; paired %s − %s over R6 and"
          " R7raw folds (%d): median %+.4f, mean %+.4g, worst %+.4g -> %s" % (
              A, float(np.median(_r2([v[A] for v in r6f]))), B, med6, B, A,
              len(folds), np.median(d), np.mean(d), d.min(),
              "PASS" if c3 else "FAIL"))

    col = {a: int((_r2([v[a] for v in ood]) < 0).sum()) for a in arms}
    worst = {a: float(_r2([v[a] for v in ood]).min()) for a in arms}
    c4 = len(ood) == 65 and col[B] <= col[A] and worst[B] >= worst[A]
    print("4. out of domain, R6 + R7raw (%d): collapses %s %d, %s %d; worst R²"
          " %s %.4g, %s %.4g -> %s" % (len(ood), A, col[A], B, col[B], A,
                                       worst[A], B, worst[B],
                                       "PASS" if c4 else "FAIL"))
    print("%s %s" % (B, "ADOPTED" if (c1 and c2 and c3 and c4) else "NOT ADOPTED"))

    print("\nper suite (%s | %s)" % (A, B))
    for name, rr in (("F41", feyn),
                     ("R6 folds", r6f),
                     ("R7raw folds", [v for v in folds if v[A]["kind"] == "realraw"]),
                     ("R6 ood", [v for v in ood if v[A]["kind"] == "real"]),
                     ("R7raw ood", [v for v in ood if v[A]["kind"] == "realraw"])):
        print("  %s (%d)" % (name, len(rr)))
        for a in arms:
            x = [v[a] for v in rr]
            r2 = _r2(x)
            over = [r["time"] - BUDGET for r in x if r.get("time_limit_reached")]
            print("    %-3s R² median %.4g mean %.4g worst %.4g, collapses %d,"
                  " formula_exact False %d, generations median %.0f, time"
                  " median %.1f s, beyond budget median %s max %s, removed"
                  " from the pool median %.0f" % (
                      a, np.median(r2), np.mean(r2), r2.min(),
                      int((r2 < 0).sum()),
                      sum(1 for r in x if r.get("formula_exact") is False),
                      np.median([r.get("generations", 0) for r in x]),
                      np.median([r.get("time", 0) for r in x]),
                      "%.2f" % np.median(over) if over else "n/a",
                      "%.2f" % max(over) if over else "n/a",
                      np.median([r.get("rejected_from_pool", 0) for r in x])))
    print("\nreal fits where the two arms differ by more than 0.01 in R²")
    for v in sorted(real, key=lambda v: v[B]["r2"] - v[A]["r2"]):
        dd = v[B]["r2"] - v[A]["r2"]
        if abs(dd) > 0.01:
            print("  %-8s %-24s %-6s s%d  %s %.4g  %s %.4g  (%+.4g)" % (
                v[A]["kind"], v[A]["problem"], v[A]["split"], v[A]["seed"],
                A, v[A]["r2"], B, v[B]["r2"], dd))


def _changed(a, b):
    return a.get("expr") != b.get("expr")


def summary_trial_g1(path, arms):
    A, B = arms
    recs = [json.loads(l) for l in open(path) if l.strip()]
    pairs = _pairs(recs, arms)
    print("%d records, %d complete pairs, crashes %d" % (
        len(recs), len(pairs), sum(1 for r in recs if r.get("status") == "CRASH")))
    for arm in arms:
        rr = [v[arm] for v in pairs.values()]
        print("%-3s median generations %.0f, median time %.1f s, candidates failed"
              " by the far test (median) %.0f" % (
                  arm, np.median([r.get("generations", 0) for r in rr]),
                  np.median([r.get("time", 0) for r in rr]),
                  np.median([r.get("far_rejected", 0) for r in rr])))
    col = [v for v in pairs.values() if v[A]["group"] == "collapse"]
    far = [v for v in pairs.values() if v[A]["group"] == "far"]
    ct = [v for v in pairs.values() if v[A]["group"] == "control"]
    fo = [v for v in pairs.values() if v[A]["group"] == "real"]
    wA, wB = min(v[A]["r2"] for v in col), min(v[B]["r2"] for v in col)
    c1 = wB >= -10
    print("1. the %d collapses: worst R² out of domain %s %.4g, %s %.4g -> %s" % (
        len(col), A, wA, B, wB, "PASS" if c1 else "FAIL"))
    lost = [(v[A]["problem"], v[A]["seed"]) for v in ct
            if v[A].get("status") == "EXACT" and v[B].get("status") != "EXACT"]
    c2 = not lost
    print("2. controls (%d): exact %s %d, %s %d, lost %s -> %s" % (
        len(ct), A, sum(1 for v in ct if v[A].get("status") == "EXACT"), B,
        sum(1 for v in ct if v[B].get("status") == "EXACT"), lost,
        "PASS" if c2 else "FAIL"))
    rl = fo + far
    d = [v[B]["r2"] - v[A]["r2"] for v in rl]
    new_col = [(v[A]["problem"], v[A]["split"], v[A]["seed"]) for v in rl
               if v[B]["r2"] < 0 <= v[A]["r2"]]
    c3 = np.median(d) >= -0.01 and not new_col
    print("3. folds and far-reaching fits (%d): median paired R² difference %+.4f,"
          " worst %+.4g, new collapses %s -> %s" % (
              len(rl), np.median(d), min(d), new_col, "PASS" if c3 else "FAIL"))
    od = col + far
    cA = sum(1 for v in od if v[A]["r2"] < 0)
    cB = sum(1 for v in od if v[B]["r2"] < 0)
    c4 = cB <= cA
    print("4. out of domain (%d): collapses %s %d, %s %d -> %s" % (
        len(od), A, cA, B, cB, "PASS" if c4 else "FAIL"))
    print("TRIAL %s" % ("CONCLUSIVE" if (c1 and c2 and c3 and c4) else "NOT CONCLUSIVE"))
    print("\nper fit (%s | %s): status or R², size; * = another model" % (A, B))
    for k in sorted(pairs, key=lambda k: (pairs[k][A]["group"], k)):
        v = pairs[k]

        def cell(r):
            return "%s, %d nodes" % (r.get("status") or "R² %.4g" % r["r2"],
                                     r.get("size", 0))
        print("  %-8s %-8s %-12s %-6s s%d  %-26s | %-26s %s" % (
            v[A]["group"], k[0], k[1], k[2], k[3], cell(v[A]), cell(v[B]),
            "*" if _changed(v[A], v[B]) else ""))


def summary_campaign_g1(path, arms):
    """The five adoption criteria of G1 (PLAN_PHASE2.md)."""
    A, B = arms
    recs = [json.loads(l) for l in open(path) if l.strip()]
    pairs = _pairs(recs, arms)
    print("%d records, %d complete pairs, crashes %s" % (
        len(recs), len(pairs), {a: sum(1 for r in recs if r["arm"] == a and
                                       r.get("status") == "CRASH")
                                for a in arms}))
    feyn = [v for v in pairs.values() if v[A]["kind"] == "feyn"]
    real = [v for v in pairs.values() if v[A]["kind"] in ("real", "realraw")]
    folds = [v for v in real if v[A]["split"].startswith("fold")]
    ood = [v for v in real if v[A]["split"] == "ood"]
    r6f = [v for v in folds if v[A]["kind"] == "real"]
    col = {a: int((_r2([v[a] for v in ood]) < 0).sum()) for a in arms}
    worst = {a: float(_r2([v[a] for v in ood]).min()) for a in arms}
    c1 = len(ood) == 65 and col[B] <= col[A] and worst[B] >= -10
    print("1. out of domain (%d): collapses %s %d, %s %d; worst R² %s %.4g, %s %.4g"
          " -> %s" % (len(ood), A, col[A], B, col[B], A, worst[A], B, worst[B],
                      "PASS" if c1 else "FAIL"))
    ex = {a: sum(1 for v in feyn if v[a].get("status") == "EXACT") for a in arms}
    lost = [(v[A]["problem"], v[A]["seed"]) for v in feyn
            if v[A].get("status") == "EXACT" and v[B].get("status") != "EXACT"]
    won = [(v[A]["problem"], v[A]["seed"]) for v in feyn
           if v[B].get("status") == "EXACT" and v[A].get("status") != "EXACT"]
    c2 = len(feyn) == 205 and ex[B] >= 82 and len(lost) <= 3
    print("2. F41 exact: %s %d, %s %d of %d; exact in %s only %d %s; in %s only"
          " %d %s -> %s" % (A, ex[A], B, ex[B], len(feyn), A, len(lost), lost,
                            B, len(won), won, "PASS" if c2 else "FAIL"))
    med6 = float(np.median(_r2([v[B] for v in r6f])))
    d = _r2([v[B] for v in folds]) - _r2([v[A] for v in folds])
    c3 = len(r6f) == 30 and len(folds) == 65 and med6 >= 0.804 \
        and np.median(d) >= -0.005
    print("3. R6 folds median R²: %s %.4f, %s %.4f; paired %s − %s over R6 and"
          " R7raw folds (%d): median %+.4f, mean %+.4g, worst %+.4g -> %s" % (
              A, float(np.median(_r2([v[A] for v in r6f]))), B, med6, B, A,
              len(folds), np.median(d), np.mean(d), d.min(),
              "PASS" if c3 else "FAIL"))
    mA = float(np.median(_r2([v[A] for v in ood])))
    mB = float(np.median(_r2([v[B] for v in ood])))
    c4 = mB >= mA - 0.01
    print("4. median R² out of domain: %s %.4f, %s %.4f -> %s" % (
        A, mA, B, mB, "PASS" if c4 else "FAIL"))
    ie = {a: sum(1 for v in real if v[a].get("formula_exact") is False) for a in arms}
    c5 = ie[B] <= ie[A]
    print("5. formulas flagged inexact on the %d real fits: %s %d, %s %d -> %s" % (
        len(real), A, ie[A], B, ie[B], "PASS" if c5 else "FAIL"))
    print("%s %s" % (B, "ADOPTED" if (c1 and c2 and c3 and c4 and c5) else "NOT ADOPTED"))
    print("\nreported beside the criteria")
    for name, rr in (("F41", feyn), ("R6 folds", r6f),
                     ("R7raw folds", [v for v in folds if v[A]["kind"] == "realraw"]),
                     ("R6 ood", [v for v in ood if v[A]["kind"] == "real"]),
                     ("R7raw ood", [v for v in ood if v[A]["kind"] == "realraw"])):
        ch = sum(1 for v in rr if _changed(v[A], v[B]))
        print("  %s (%d): models changed %d" % (name, len(rr), ch))
        for a in arms:
            x = [v[a] for v in rr]
            r2 = _r2(x)
            over = [r["time"] - BUDGET for r in x if r.get("time_limit_reached")]
            print("    %-3s R² median %.4g mean %.4g worst %.4g, collapses %d,"
                  " generations median %.0f, beyond budget median %s max %s,"
                  " candidates failed by the far test median %.0f" % (
                      a, np.median(r2), np.mean(r2), r2.min(), int((r2 < 0).sum()),
                      np.median([r.get("generations", 0) for r in x]),
                      "%.2f" % np.median(over) if over else "n/a",
                      "%.2f" % max(over) if over else "n/a",
                      np.median([r.get("far_rejected", 0) for r in x])))
    print("\nreal fits where the two arms differ by more than 0.01 in R²")
    for v in sorted(real, key=lambda v: v[B]["r2"] - v[A]["r2"]):
        dd = v[B]["r2"] - v[A]["r2"]
        if abs(dd) > 0.01:
            print("  %-8s %-24s %-6s s%d  %s %.4g  %s %.4g  (%+.4g)" % (
                v[A]["kind"], v[A]["problem"], v[A]["split"], v[A]["seed"],
                A, v[A]["r2"], B, v[B]["r2"], dd))


def summary_confirm(path, arms):
    """The three criteria of the confirmation of G1b on new seeds."""
    A, B = arms
    recs = [json.loads(l) for l in open(path) if l.strip()]
    pairs = _pairs(recs, arms)
    print("%d records, %d complete pairs, crashes %d" % (
        len(recs), len(pairs), sum(1 for r in recs if r.get("status") == "CRASH")))
    ood = [v for v in pairs.values() if v[A]["split"] == "ood"]
    folds = [v for v in pairs.values() if v[A]["split"].startswith("fold")]
    col = {a: int((_r2([v[a] for v in ood]) < 0).sum()) for a in arms}
    worst = {a: float(_r2([v[a] for v in ood]).min()) for a in arms}
    c1 = len(ood) == 65 and col[B] <= col[A] and worst[B] >= worst[A]
    print("1. out of domain (%d): collapses %s %d, %s %d; worst R² %s %.4g, %s %.4g"
          " -> %s" % (len(ood), A, col[A], B, col[B], A, worst[A], B, worst[B],
                      "PASS" if c1 else "FAIL"))
    mA = float(np.median(_r2([v[A] for v in ood])))
    mB = float(np.median(_r2([v[B] for v in ood])))
    c2 = mB >= mA - 0.01
    print("2. median R² out of domain: %s %.4f, %s %.4f -> %s" % (
        A, mA, B, mB, "PASS" if c2 else "FAIL"))
    d = _r2([v[B] for v in folds]) - _r2([v[A] for v in folds])
    c3 = len(folds) == 65 and np.median(d) >= -0.005
    print("3. folds (%d): median paired difference %+.4f, mean %+.4g, worst %+.4g"
          " -> %s" % (len(folds), np.median(d), np.mean(d), d.min(),
                      "PASS" if c3 else "FAIL"))
    print("%s %s" % (B, "CONFIRMED" if (c1 and c2 and c3) else "NOT CONFIRMED"))
    print("\nmodels changed: out of domain %d of %d, folds %d of %d" % (
        sum(1 for v in ood if _changed(v[A], v[B])), len(ood),
        sum(1 for v in folds if _changed(v[A], v[B])), len(folds)))
    print("fits where the two arms differ by more than 0.01 in R²")
    for v in sorted(pairs.values(), key=lambda v: v[B]["r2"] - v[A]["r2"]):
        dd = v[B]["r2"] - v[A]["r2"]
        if abs(dd) > 0.01:
            print("  %-8s %-24s %-6s s%d  %s %.4g  %s %.4g  (%+.4g)" % (
                v[A]["kind"], v[A]["problem"], v[A]["split"], v[A]["seed"],
                A, v[A]["r2"], B, v[B]["r2"], dd))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("which", choices=sorted(RUNS))
    r.add_argument("--python", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--pairs", type=int, default=2)
    r.add_argument("--max-seconds", type=float, default=None)
    o = sub.add_parser("one")
    o.add_argument("job")
    s = sub.add_parser("summary")
    s.add_argument("which", choices=sorted(RUNS))
    s.add_argument("path")
    a = ap.parse_args()
    if a.cmd == "run":
        drive(a.which, a.python, a.out, a.pairs, a.max_seconds)
    elif a.cmd == "one":
        print(json.dumps(run_arm(json.loads(a.job))))
    elif a.which in ("trialg1", "trialg1b"):
        summary_trial_g1(a.path, RUNS[a.which][1])
    elif a.which in ("campaigng1", "campaigng1b"):
        summary_campaign_g1(a.path, RUNS[a.which][1])
    elif a.which == "confirmg1b":
        summary_confirm(a.path, RUNS[a.which][1])
    elif a.which.startswith("trial"):
        summary_trial(a.path, RUNS[a.which][1])
    elif a.which.startswith("campaign"):
        summary_campaign(a.path, RUNS[a.which][1])
    else:
        sys.exit("no summary for %s" % a.which)


if __name__ == "__main__":
    main()
