"""Second review of M5: the figures of the pages of the limits, recomputed."""
import os, sys
from collections import defaultdict, Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import A_PATH, B_PATH, load, pools, pool_of

a, _ = load(A_PATH); b, _ = load(B_PATH); P = pools()
for name, R in (("1.2.0", a), ("1.3.0", b)):
    print("==", name)
    for kd in ("feyn", "ufeyn", "tf", "utf"):
        per = defaultdict(int)
        for k, r in R.items():
            if k[0] == kd:
                per[k[1]] += r["status"] == "EXACT"
        never = sorted(p for p, n in per.items() if n == 0)
        print("  %s: %d problems, exact %d, never exact %d %s" % (
            kd, len(per), sum(per.values()), len(never), never if len(never) < 10 else ""))
        if kd in ("feyn", "ufeyn"):
            print("     once in five:", sorted(p for p, n in per.items() if n == 1))
    fam = Counter()
    nfam = Counter()
    for k, r in R.items():
        if k[0] == "tf":
            fam[r["family"]] += r["status"] == "EXACT"
            nfam[r["family"]] += 1
    print("  TF78 by family:", dict(fam), dict(nfam))
    fe = lambda kinds: (sum(r["formula_exact"] is False for k, r in R.items() if k[0] in kinds),
                        sum(1 for k in R if k[0] in kinds))
    print("  formula_exact False, real+realraw (all splits):", fe(("real", "realraw")))
    print("  formula_exact False, tr+trraw (all splits):", fe(("tr", "trraw")))
    print("  formula_exact False, real+realraw folds only:",
          sum(r["formula_exact"] is False for k, r in R.items() if k[0] in ("real", "realraw") and k[2] != "ood"))
    oo = [r["r2"] for k, r in R.items() if k[0] in ("real", "realraw") and k[2] == "ood"]
    print("  bench collapses %d of %d, worst %.1f" % (sum(x < 0 for x in oo), len(oo), min(oo)))
    for kd in ("tr", "trraw"):
        per = defaultdict(int)
        for k, r in R.items():
            if k[0] == kd and k[2] == "ood":
                per[k[1]] += r["r2"] < 0
        print("  %s collapses %d, top six %d" % (kd, sum(per.values()),
                                                 sum(sorted(per.values(), reverse=True)[:6])))
# U41 never exact names
for name, R in (("1.2.0", a), ("1.3.0", b)):
    per = defaultdict(int)
    for k, r in R.items():
        if k[0] == "ufeyn":
            per[k[1]] += r["status"] == "EXACT"
    print(name, "U41 never:", sorted(p for p, n in per.items() if n == 0))
# I.26.2 exact with arcsine at seeds 0-4 in M2
for kd in ("feyn", "ufeyn"):
    print(kd, "I.26.2 exact with arcsin seeds:", [k[3] for k, r in sorted(b.items())
          if k[0] == kd and k[1] == "I.26.2" and r["status"] == "EXACT" and "arcsin" in r["expr"]])
