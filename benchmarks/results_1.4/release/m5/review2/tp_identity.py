"""Second review of M5 (1.4.0): are the TP models of 1.4.0 in M2 those of B in
campaign N2b, and those of the corrected engine (L1) those of 1.4.0 in M2?

  python3 -I tp_identity.py

Compares the records field by field, times, dates and paths of the engine
aside, and prints what differs.
"""
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REL = os.path.normpath(os.path.join(HERE, "..", ".."))
N2B = os.path.normpath(os.path.join(REL, "..", "n2b", "campaign"))
SKIP = {"time", "date", "engine_file", "engine_version"}


def load(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out[(r["arm"], r["exp"], r["n"], r["noise"], r["draw"])] = r
    return out


def compare(name, pa, pb):
    a, b = load(pa), load(pb)
    print("== %s: %d and %d records, same keys %s" % (name, len(a), len(b), set(a) == set(b)))
    same_expr = sum(a[k]["expr"] == b[k]["expr"] for k in a if k in b)
    fields = Counter()
    nd = 0
    for k in sorted(a):
        if k not in b:
            continue
        d = [f for f in set(a[k]) | set(b[k]) if f not in SKIP and a[k].get(f) != b[k].get(f)]
        if d:
            nd += 1
            fields.update(d)
    print("   same expr %d; records differing outside time/date/engine: %d; fields %s" % (
        same_expr, nd, dict(fields)))
    ka = set(a[next(iter(a))]) - SKIP
    kb = set(b[next(iter(b))]) - SKIP
    if ka != kb:
        print("   fields only in the first: %s; only in the second: %s" % (sorted(ka - kb), sorted(kb - ka)))


compare("TP, B of campaign N2b vs 1.4.0 in M2", os.path.join(N2B, "tp_n2b.jsonl"),
        os.path.join(REL, "m2", "tp_1.4.0.jsonl"))
compare("TP, A of campaign N2b vs 1.3.0 in M2", os.path.join(N2B, "tp_1.3.0.jsonl"),
        os.path.join(REL, "m2", "tp_1.3.0.jsonl"))
compare("TP, 1.4.0 in M2 vs L1", os.path.join(REL, "m2", "tp_1.4.0.jsonl"),
        os.path.join(REL, "l1", "tp_l1.jsonl"))
compare("TPT10, 1.4.0 in M2 vs L1", os.path.join(REL, "m2", "tpt10_1.4.0.jsonl"),
        os.path.join(REL, "l1", "tpt10_l1.jsonl"))
