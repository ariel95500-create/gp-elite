"""Review 1: the examination of the TP notebook of the pool full (m3/examine/),
recomputed from e2_*.jsonl. python3 -I r4_m3_examine.py"""
import json
import statistics as st
from math import comb

D = "/home/user/gp-elite/benchmarks/results_1.3/release/m3/examine/"
a = {(r["generations"], r["seed"]): r for r in map(json.loads, open(D + "e2_1.2.0.jsonl"))}
b = {(r["generations"], r["seed"]): r for r in map(json.loads, open(D + "e2_1.3.0.jsonl"))}
print("fits", len(a), len(b), set(a) == set(b))
print("versions", {r["engine_version"] for r in a.values()}, {r["engine_version"] for r in b.values()})
dep_b = dep_b_arc = 0
for g in (10, 30, 60):
    ks = [(g, s) for s in range(10)]
    hi = sum(b[k]["mse"] > a[k]["mse"] for k in ks)
    lo = sum(b[k]["mse"] < a[k]["mse"] for k in ks)
    n = hi + lo
    kk = min(hi, lo)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(kk + 1)) / 2 ** n)
    da = sum(a[k]["formula_exact"] is False for k in ks)
    db = sum(b[k]["formula_exact"] is False for k in ks)
    dba = sum(b[k]["formula_exact"] is False and "arcsin" in b[k]["expr"] for k in ks)
    dep_b += db
    dep_b_arc += dba
    arcb = sum("arcsin" in b[k]["expr"] for k in ks)
    print("g=%d: 1.3.0 higher %d lower %d p=%.3f; median mse %.3e vs %.3e; median size %s vs %s; "
          "median time %.2f vs %.2f; departs %d vs %d (of which arcsin %d); arcsin in B %d; arcsin flag %d" % (
              g, hi, lo, p, st.median(a[k]["mse"] for k in ks), st.median(b[k]["mse"] for k in ks),
              st.median(a[k]["size"] for k in ks), st.median(b[k]["size"] for k in ks),
              st.median(a[k]["time"] for k in ks), st.median(b[k]["time"] for k in ks), da, db, dba, arcb,
              sum(bool(b[k]["arcsin"]) for k in ks)))
    for k in ks:
        if b[k]["formula_exact"] is False:
            print("    departs B seed %d: arcsin=%s warn=%s | %s" % (k[1], "arcsin" in b[k]["expr"],
                                                                 [w[:90] for w in b[k]["warnings"]], b[k]["expr"][:140]))
        if a[k]["formula_exact"] is False:
            print("    departs A seed %d: %s" % (k[1], a[k]["expr"][:120]))
print("1.3.0 departing total %d, with arcsin %d" % (dep_b, dep_b_arc))
print("seed 0:", [(g, a[(g, 0)]["mse"], a[(g, 0)]["size"], b[(g, 0)]["mse"], b[(g, 0)]["size"],
                   a[(g, 0)]["formula_exact"], b[(g, 0)]["formula_exact"]) for g in (10, 30, 60)])
