"""Second review of M5: the examination of the TP notebook of the pool full (m3/examine)."""
import json, os
from math import comb
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "m3", "examine")
L = lambda v: {(r["generations"], r["seed"]): r for r in map(json.loads, open(os.path.join(D, "e2_%s.jsonl" % v)))}
a, b = L("1.2.0"), L("1.3.0")
for g in (10, 30, 60):
    ks = [k for k in sorted(a) if k[0] == g]
    hi = sum(b[k]["mse"] > a[k]["mse"] for k in ks); lo = sum(b[k]["mse"] < a[k]["mse"] for k in ks)
    n = hi + lo; kk = min(hi, lo)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(kk + 1)) / 2 ** n)
    dep_a = [k[1] for k in ks if a[k]["formula_exact"] is False]
    dep_b = [k[1] for k in ks if b[k]["formula_exact"] is False]
    dep_b_arc = [k[1] for k in ks if b[k]["formula_exact"] is False and "arcsin" in b[k]["expr"]]
    warn_b = [k[1] for k in ks if b[k]["warnings"]]
    print("g=%d: 1.3.0 higher %d lower %d p=%.3f; departs A %s B %s; B departs with arcsin %s; B warnings %s; B arcsin %d"
          % (g, hi, lo, p, dep_a, dep_b, dep_b_arc, warn_b, sum("arcsin" in b[k]["expr"] for k in ks)))
for k in sorted(b):
    if b[k]["formula_exact"] is False:
        print(k, b[k]["expr"][:200], "|", (b[k]["warnings"] or [""])[0][:120])
print("seed 0:", [(g, a[(g, 0)]["mse"], b[(g, 0)]["mse"], b[(g, 0)]["formula_exact"], b[(g,0)]["size"]) for g in (10, 30, 60)])
