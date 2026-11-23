"""Second review of M5 (1.4.0): the benches of M2 against those of campaign
N2b, same engines (1.3.0 from PyPI on both sides; the candidate of N2b and
1.4.0, which have the same engine), on the 1,360 jobs they share.

  python3 -I m2_vs_n2b.py

Prints, by version and kind, the fits whose status or structure differs
between the two campaigns, with whether each reached its time budget.
"""
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REL = os.path.normpath(os.path.join(HERE, "..", ".."))
N2B = os.path.normpath(os.path.join(REL, "..", "n2b", "campaign"))


def load(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out[(r["kind"], r["problem"], r["split"], r["seed"])] = r
    return out


for lab, pc, pm in (("1.3.0", "bench_1.3.0.jsonl", "campaignR_1.3.0.jsonl"),
                    ("candidate N2b / 1.4.0", "bench_n2b.jsonl", "campaignR_1.4.0.jsonl")):
    c, m = load(os.path.join(N2B, pc)), load(os.path.join(REL, "m2", pm))
    common = sorted(set(c) & set(m))
    print("== %s: %d jobs in the campaign, %d shared with M2; kinds %s" % (
        lab, len(c), len(common), dict(Counter(k[0] for k in common))))
    nd = 0
    for k in common:
        a, b = c[k], m[k]
        if a.get("status") != b.get("status") or bool(a.get("structure")) != bool(b.get("structure")):
            nd += 1
            print("   %s: status %s -> %s, structure %s -> %s, budget %s / %s, same seeds %s,"
                  " same expr %s" % (k, a.get("status"), b.get("status"), bool(a.get("structure")),
                                     bool(b.get("structure")), a.get("time_limit_reached"),
                                     b.get("time_limit_reached"),
                                     (a.get("tolerant_seed") or None) == (b.get("tolerant_seed") or None),
                                     a.get("expr") == b.get("expr")))
    print("   fits whose status or structure differs: %d; same expr in %d of %d" % (
        nd, sum(c[k].get("expr") == m[k].get("expr") for k in common), len(common)))
