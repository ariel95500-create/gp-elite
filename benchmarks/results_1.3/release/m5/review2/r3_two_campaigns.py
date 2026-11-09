"""Second review of M5: 1.2.0 in the M2 of 1.2 against 1.2.0 in the M2 of 1.3.

Is the move of TF78 (214 -> 213) and TS14 (10 -> 8) between the two campaigns
the time budget? And the times of the fits stopped by the budget in M2 of 1.3.
"""
import os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, A_PATH, B_PATH, SUITE, load, pools, pool_of, median

old, _ = load(os.path.join(ROOT, "benchmarks/results_1.2/release/m2/campaignR_1.2.0.jsonl"))
old11, _ = load(os.path.join(ROOT, "benchmarks/results_1.2/release/m2/campaignR_1.1.0.jsonl"))
a, _ = load(A_PATH)
b, _ = load(B_PATH)
P = pools()
print("M2 of 1.2, 1.2.0 records:", len(old), "keys equal to M2 of 1.3:", set(old) == set(a))
print("  only in old:", len(set(old) - set(a)), "only in new:", len(set(a) - set(old)))
for kd in ("tf", "ts", "utf", "feyn", "ufeyn"):
    ks = [k for k in old if k[0] == kd and (kd != "ts" or k[2] == "test")]
    print("%s exact: 1.1.0@M2-1.2 %d, 1.2.0@M2-1.2 %d, 1.2.0@M2-1.3 %d, 1.3.0 %d" % (
        SUITE[kd], sum(old11[k]["status"] == "EXACT" for k in ks if k in old11),
        sum(old[k]["status"] == "EXACT" for k in ks),
        sum(a[k]["status"] == "EXACT" for k in ks if k in a),
        sum(b[k]["status"] == "EXACT" for k in ks if k in b)))
for kd in ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10"):
    ks = [k for k in old if k[0] == kd]
    print("%s struct: 1.2.0@M2-1.2 %d, 1.2.0@M2-1.3 %d" % (
        SUITE[kd], sum(bool(old[k].get("structure")) for k in ks),
        sum(bool(a[k].get("structure")) for k in ks)))
print("\nfits of 1.2.0 whose EXACT status differs between the two campaigns (tf, ts test, utf):")
for k in sorted(old):
    if k[0] in ("tf", "utf") or (k[0] == "ts" and k[2] == "test"):
        if k in a and (old[k]["status"] == "EXACT") != (a[k]["status"] == "EXACT"):
            print("  ", k, old[k]["status"], "->", a[k]["status"], "budget old/new",
                  old[k]["time_limit_reached"], a[k]["time_limit_reached"],
                  "same expr", old[k]["expr"] == a[k]["expr"])
det = [k for k in old if k in a and not old[k]["time_limit_reached"] and not a[k]["time_limit_reached"]]
dd = [k for k in det if old[k]["expr"] != a[k]["expr"] or old[k]["err"] != a[k]["err"]]
print("1.2.0 in both campaigns, neither at budget: %d, differing expr/err: %d" % (len(det), len(dd)))
for k in dd[:10]:
    print("   ", k, old[k]["expr"][:60], "|", a[k]["expr"][:60])

# the fits stopped by the budget in M2 of 1.3
for name, R in (("1.2.0", a), ("1.3.0", b)):
    t = [r["time"] for r in R.values() if r["time_limit_reached"]]
    print("%s: fits with time_limit_reached: %d, median time %.2f, max %.2f" % (
        name, len(t), median(t), max(t)))
t = [r["time"] for r in old.values() if r["time_limit_reached"]]
print("1.2.0 at M2 of 1.2: fits with time_limit_reached: %d, median %.2f, max %.2f" % (
    len(t), median(t), max(t)))
t = [r["time"] for r in old.values()]
print("1.2.0 at M2 of 1.2: all fits %d" % len(t))

# context for "as from one campaign to the next": 1.2.0 against itself across
# the two campaigns, pool physical
phys = [k for k in old if pool_of(k, P) == "physical"]
d_expr = sum(old[k]["expr"] != a[k]["expr"] for k in phys)
d_status = sum(old[k].get("status") != a[k].get("status") or
               bool(old[k].get("structure")) != bool(a[k].get("structure")) for k in phys)
print("1.2.0 at M2 of 1.2 against 1.2.0 at M2 of 1.3, pool physical (%d fits): "
      "another formula %d, status or structure changed %d" % (len(phys), d_expr, d_status))
