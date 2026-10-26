# -*- coding: utf-8 -*-
"""Campaign U1 against its criteria (benchmarks/results_1.1/PLAN.md).

    python compare_u1.py campaign/U41_A_1.0.0.jsonl campaign/U41_U1.jsonl

Criteria 1, 2, 3 and 5 are read here; criterion 4 (real data under units) is
read by units_real.py summary.
"""
import json
import sys
from collections import Counter, defaultdict

FIVE = ("racine", "rationnelle", "trig", "exponentielle", "logarithme")


def load(path):
    out = {}
    for ln in open(path):
        if ln.strip():
            r = json.loads(ln)
            out[(r["kind"], r["problem"], r["split"], r["seed"])] = r
    return out


def main(pa, pb, min_exact_gain=10, min_family_gain=5):
    A, B = load(pa), load(pb)
    keys = sorted(set(A) & set(B))
    print("%d jobs in A, %d in U1, %d in both" % (len(A), len(B), len(keys)))
    crashes = [(k, n) for n, D in (("A", A), ("U1", B)) for k in keys
               if D[k].get("status") == "CRASH"]
    print("crashes: %d" % len(crashes))
    eng = {n: Counter((D[k].get("engine_file", "?")[:45],
                       D[k].get("seeds_under_units")) for k in keys)
           for n, D in (("A", A), ("U1", B))}
    print("engines: A %s; U1 %s" % (dict(eng["A"]), dict(eng["U1"])))
    ok = True

    # 1. exact laws under units
    u = [k for k in keys if k[0] == "ufeyn"]
    ex = {n: sum(D[k].get("status") == "EXACT" for k in u)
          for n, D in (("A", A), ("U1", B))}
    fam = {n: sum(D[k].get("status") == "EXACT" for k in u
                  if D[k].get("family") in FIVE)
           for n, D in (("A", A), ("U1", B))}
    nfam = sum(1 for k in u if A[k].get("family") in FIVE)
    per = defaultdict(lambda: [0, 0])
    for k in u:
        per[k[1]][0] += A[k].get("status") == "EXACT"
        per[k[1]][1] += B[k].get("status") == "EXACT"
    fallen = [(p, a, b) for p, (a, b) in per.items() if a >= 3 and b <= 1]
    c1 = (ex["U1"] - ex["A"] >= min_exact_gain
          and fam["U1"] - fam["A"] >= min_family_gain and not fallen)
    ok &= c1
    print("\n1. U41 exact: A %d, U1 %d of %d (gain %+d, at least %+d asked); "
          "five families A %d, U1 %d of %d (gain %+d, at least %+d asked); "
          "equations exact in A at >= 3 seeds falling to <= 1: %s  -> %s"
          % (ex["A"], ex["U1"], len(u), ex["U1"] - ex["A"], min_exact_gain,
             fam["A"], fam["U1"], nfam, fam["U1"] - fam["A"], min_family_gain,
             fallen or "none", "met" if c1 else "NOT MET"))
    gained = sorted((p, a, b) for p, (a, b) in per.items() if b > a)
    lost = sorted((p, a, b) for p, (a, b) in per.items() if b < a)
    print("   equations with more exact fits in U1: %d %s" % (len(gained), gained))
    print("   equations with fewer: %d %s" % (len(lost), lost))
    print("   never exact (A, U1): %d, %d" % (
        sum(1 for a, b in per.values() if a == 0),
        sum(1 for a, b in per.values() if b == 0)))

    # 2. structure under noise
    for kind in ("ufeyn_n1", "ufeyn_n10"):
        kk = [k for k in keys if k[0] == kind]
        sa = sum(bool(A[k].get("structure")) for k in kk)
        sb = sum(bool(B[k].get("structure")) for k in kk)
        c2 = sb >= sa - 2
        ok &= c2
        print("\n2. %s structure retrieved: A %d, U1 %d of %d (at least A - 2)"
              "  -> %s" % (kind, sa, sb, len(kk), "met" if c2 else "NOT MET"))

    # 3. the guarantee of units
    for n, D in (("A", A), ("U1", B)):
        bad = [k for k in keys if D[k].get("units_ok") is not True]
        print("\n3. %s: models failing the units audit: %d of %d%s"
              % (n, len(bad), len(keys), (" " + str(bad[:5])) if bad else ""))
        if n == "U1":
            ok &= not bad
    print("   -> %s" % ("met" if not [k for k in keys
                                     if B[k].get("units_ok") is not True]
                        else "NOT MET"))

    # 5. formulas flagged inexact
    fa = sum(A[k].get("formula_exact") is False for k in keys)
    fb = sum(B[k].get("formula_exact") is False for k in keys)
    c5 = fb <= fa + 3
    ok &= c5
    print("\n5. formulas flagged inexact: A %d, U1 %d (at most A + 3)  -> %s"
          % (fa, fb, "met" if c5 else "NOT MET"))

    # beside the criteria
    import statistics as st
    for kind in ("ufeyn", "ufeyn_n1", "ufeyn_n10"):
        kk = [k for k in keys if k[0] == kind]
        print("\n   %s median time: A %.1f s, U1 %.1f s" % (
            kind, st.median(A[k]["time"] for k in kk),
            st.median(B[k]["time"] for k in kk)))
    k3 = [k for k in u if k[1] == "II.11.3"]
    print("   II.11.3 exact: A %d, U1 %d of %d; times A %s, U1 %s" % (
        sum(A[k].get("status") == "EXACT" for k in k3),
        sum(B[k].get("status") == "EXACT" for k in k3), len(k3),
        [A[k]["time"] for k in k3], [B[k]["time"] for k in k3]))
    print("\ncriteria 1, 2, 3 and 5: %s (criterion 4: units_real.py summary)"
          % ("all met" if ok else "NOT all met"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
