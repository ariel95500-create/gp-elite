"""The targeted check of PLAN_U2.md against its three criteria.

    python compare_u2.py tp_units_U1.jsonl tp_units_U2.jsonl
"""
import json
import math
import re
import sys

import numpy as np

REACH = ("pendule", "ressort", "chute", "puissance", "gaz", "eclairement")


def load(p):
    return {(r["exp"], r["n"], r["noise"], r["draw"]): r
            for r in map(json.loads, open(p, encoding="utf-8")) if r}


def constant_err(r):
    if r.get("crash") or not r["law"] or r["exp"] not in ("pendule", "chute", "gaz"):
        return None
    m = re.match(r"^\s*([0-9.eE+-]+)\s*\*", r["expr"])
    if not m:
        return None
    c = float(m.group(1))
    val, true = {"pendule": ((2 * math.pi / c) ** 2, 9.81),
                 "chute": (2 * c, 9.81), "gaz": (c, 8.314)}[r["exp"]]
    return abs(100.0 * (val / true - 1.0))


def main(pa, pb):
    A, B = load(pa), load(pb)
    keys = sorted(set(A) & set(B))
    print("%d fits in both; crashes U1 %d, U2 %d" % (
        len(keys), sum(bool(A[k].get("crash")) for k in keys),
        sum(bool(B[k].get("crash")) for k in keys)))
    print("engines: U1 %s; U2 %s" % ({A[k]["engine_file"] for k in keys},
                                     {B[k]["engine_file"] for k in keys}))
    print("\n| experiment | law U1 | law U2 | median time U1 (s) | U2 (s) | same expression |")
    print("|---|---|---|---|---|---|")
    for e in sorted({k[0] for k in keys}, key=lambda x: (x not in REACH, x)):
        ks = [k for k in keys if k[0] == e]
        print("| %s | %d/%d | %d/%d | %.1f | %.1f | %d/%d |" % (
            e, sum(bool(A[k]["law"]) for k in ks), len(ks),
            sum(bool(B[k]["law"]) for k in ks), len(ks),
            np.median([A[k]["time"] for k in ks]), np.median([B[k]["time"] for k in ks]),
            sum(A[k]["expr"] == B[k]["expr"] for k in ks), len(ks)))
    reach = [k for k in keys if k[0] in REACH]
    other = [k for k in keys if k[0] not in REACH]
    la = sum(bool(A[k]["law"]) for k in reach)
    lb = sum(bool(B[k]["law"]) for k in reach)
    lost = [k for k in other if A[k]["law"] and not B[k]["law"]]
    c1 = lb >= la and not lost
    ta = float(np.median([A[k]["time"] for k in keys]))
    tb = float(np.median([B[k]["time"] for k in keys]))
    c2 = tb < ta
    ea = [x for x in (constant_err(A[k]) for k in keys) if x is not None]
    eb = [x for x in (constant_err(B[k]) for k in keys) if x is not None]
    ma, mb = float(np.median(ea)), float(np.median(eb))
    c3 = abs(mb - ma) <= 0.1
    print("\nCriteria written before the run (PLAN_U2.md):")
    print("  [%s] 1. no law lost: six reachable laws U1 %d, U2 %d of %d; "
          "recovered by U1 and lost by U2 on the four others: %d"
          % ("met" if c1 else "NOT MET", la, lb, len(reach), len(lost)))
    print("  [%s] 2. faster: median time of the %d fits U1 %.1f s, U2 %.1f s"
          % ("met" if c2 else "NOT MET", len(keys), ta, tb))
    print("  [%s] 3. constants g and R: median relative error U1 %.2f %% (%d fits), "
          "U2 %.2f %% (%d fits), within 0.1 point" % ("met" if c3 else "NOT MET",
                                                    ma, len(ea), mb, len(eb)))
    print("ADOPTED" if (c1 and c2 and c3) else "NOT ADOPTED")
    print("\ntotal time of the %d fits: U1 %.0f s, U2 %.0f s" % (
        len(keys), sum(A[k]["time"] for k in keys), sum(B[k]["time"] for k in keys)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
