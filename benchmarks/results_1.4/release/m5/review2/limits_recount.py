"""Second review of M5 (1.4.0): the figures of m2/limits_figures.txt counted
again from the records of M2 (the 1.4 folder holds no script for that file).

  python3 -I limits_recount.py
"""
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
M2 = os.path.normpath(os.path.join(HERE, "..", "..", "m2"))

for v in ("1.3.0", "1.4.0"):
    recs = [json.loads(x) for x in open(os.path.join(M2, "campaignR_%s.jsonl" % v), encoding="utf-8")]
    per = defaultdict(int)
    for r in recs:
        if r["kind"] == "feyn":
            per[r["problem"]] += r.get("status") == "EXACT"
    once = sorted(p for p, n in per.items() if n == 1)
    out = ["F41 exact once in five %s" % once]
    for kind in ("tr", "trraw"):
        rr = [r for r in recs if r["kind"] == kind and r["split"] == "ood"]
        c = defaultdict(int)
        for r in rr:
            c[r["problem"]] += r["r2"] < 0
        top = sorted(c.values(), reverse=True)[:6]
        out.append("%s ood %d, collapses %d, on the six with most %d" % (
            kind, len(rr), sum(r["r2"] < 0 for r in rr), sum(top)))
    print(v, "; ".join(out))
