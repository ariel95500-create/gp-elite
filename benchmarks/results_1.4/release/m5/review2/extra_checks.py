"""Second review of M5 (1.4.0): the checks that were first run inline, kept
here so that each figure of the report can be found again.

  python3 -I extra_checks.py

1. the TP notebook: the total of each run (the times rounded per fit, as
   the tables of the documents add them), M3 and part c of L1;
2. the examination of the point source (campaign N2b): A and B where the
   law is lost, their training errors and seed counts;
3. the fits on exact data (F41, U41, TF78, TF78 under units, TS14) whose
   exact law is lost or gained, with whether 1.4.0 places other seeds;
4. among the 782 fits "where 1.4 does not act", the recorded formulas cut
   at 160 characters;
5. the count of part b of L1 against the count of M4, job by job;
6. the formula of I.16.6 under units in M3 of 1.3 and 1.4;
7. the seeds examined by m3_examine/seeds.py, by script.
"""
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REL = os.path.normpath(os.path.join(HERE, "..", ".."))
R14 = os.path.normpath(os.path.join(REL, ".."))
R13 = os.path.normpath(os.path.join(R14, "..", "results_1.3", "release"))


def jl(p):
    return [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]


print("1. the TP notebook, seconds per fit and in all")
runs = [("M3 driver, 14 Nov", os.path.join(REL, "m3", "notebook_tp_six_lois_1.4.0.txt"))]
for v in ("1.3.0", "1.4.0"):
    for i in (1, 2):
        runs.append(("M3 pair run %d %s" % (i, v), os.path.join(
            REL, "m3", "tp_timing", "notebook_pair", "run%d_%s.txt" % (i, v))))
runs.append(("L1 part c, 17 Nov (corrected engine)",
             os.path.join(REL, "l1", "m3", "notebook_tp_six_lois_1.4.0.txt")))
for lab, p in runs:
    t = [int(x) for x in re.findall(r"\((\d+) s\)", open(p, encoding="utf-8").read())]
    print("   %-40s %s  in all %d s" % (lab, t, sum(t)))

print("\n2. the point source in campaign N2b, where the law is lost")
by = {}
for r in jl(os.path.join(R14, "n2b", "campaign", "examine", "examine.jsonl")):
    by.setdefault((r["n"], r["noise"], r["draw"]), {})[r["engine"]] = r
for k, d in sorted(by.items()):
    a, b = d["A"], d["B"]
    if a["law"] != b["law"]:
        print("   %s law %s -> %s, training error A %.3g B %.3g, seeds A %d B %d" % (
            k, a["law"], b["law"], a["err_train"], b["err_train"],
            len(a["tolerant_seed"].split(" | ")), len(b["tolerant_seed"].split(" | "))))


def bench(p):
    return {(r["kind"], r["problem"], r["split"], r["seed"]): r for r in jl(p)}


A = bench(os.path.join(REL, "m2", "campaignR_1.3.0.jsonl"))
B = bench(os.path.join(REL, "m2", "campaignR_1.4.0.jsonl"))
seeds = lambda r: r.get("tolerant_seed") or None
print("\n3. exact data: exact law lost or gained, 1.3.0 -> 1.4.0")
for k in sorted(A):
    if k[0] in ("feyn", "ufeyn", "tf", "utf", "ts") and \
            (A[k]["status"] == "EXACT") != (B[k]["status"] == "EXACT"):
        print("   %s %s -> %s, other seeds %s, budget %s / %s" % (
            k, A[k]["status"], B[k]["status"], seeds(A[k]) != seeds(B[k]),
            A[k].get("time_limit_reached"), B[k].get("time_limit_reached")))

print("\n4. the 782 fits where 1.4 does not act: recorded formulas of 160 characters")
det = [k for k in A if seeds(A[k]) == seeds(B[k]) and not A[k].get("time_limit_reached")
       and not B[k].get("time_limit_reached")]
print("   %d fits; cut: %s" % (len(det), [k for k in det if max(len(A[k]["expr"]), len(B[k]["expr"])) >= 160]))

print("\n5. the count of L1 (part b) against that of M4")
c4 = jl(os.path.join(REL, "m4", "log_scan", "count.jsonl"))
c1 = jl(os.path.join(REL, "l1", "count_l1.jsonl"))
print("   %d and %d records, identical job by job: %s; stage runs (benches) %d and %d; errors %d and %d" % (
    len(c4), len(c1), c4 == c1, sum(r["stage_ran"] for r in c4 if r["set"] == "bench"),
    sum(r["stage_ran"] for r in c1 if r["set"] == "bench"),
    sum(bool(r["errors"]) for r in c4), sum(bool(r["errors"]) for r in c1)))

print("\n6. I.16.6 under units (feynman15_units.jsonl)")
for lab, base in (("1.3", R13), ("1.4", REL)):
    for r in jl(os.path.join(base, "m3", "feynman15_units.jsonl")):
        if r.get("name") == "I.16.6":
            print("   %s %s %s" % (lab, r.get("status"), r.get("expr")))

print("\n7. the fits examined by m3_examine/seeds.py, by script")
jobs = [r["job"] for r in jl(os.path.join(REL, "m3_examine", "seeds_1.4.0.jsonl"))]
print("   %d fits: %s" % (len(jobs), dict(Counter(j.split()[0] for j in jobs))))
print("   battery: %s" % [j for j in jobs if j.startswith("battery")])
print("   robustness: %s; units: %s" % ([j for j in jobs if j.startswith("robustness")],
                                       [j for j in jobs if j.startswith("units")]))
