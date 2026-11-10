"""Second review of M5: I.18.12 in M2 and in the examination m2/examine (E1)."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import A_PATH, B_PATH, M2, load, median
a, _ = load(A_PATH); b, _ = load(B_PATH)
for kd in ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10"):
    ks = sorted(k for k in a if k[0] == kd and k[1] == "I.18.12")
    print(kd, "struct A", sum(bool(a[k]["structure"]) for k in ks), "B", sum(bool(b[k]["structure"]) for k in ks),
          "budget A/B", sum(a[k]["time_limit_reached"] for k in ks), sum(b[k]["time_limit_reached"] for k in ks))
    if kd == "ufeyn_n10":
        for k in ks:
            print("   seed", k[3], "A:", a[k]["expr"][:70], "| B:", b[k]["expr"][:70])
E = os.path.join(M2, "examine")
ea, _ = load(os.path.join(E, "e1_1.2.0.jsonl")); eb, _ = load(os.path.join(E, "e1_1.3.0.jsonl"))
print("E1 records", len(ea), len(eb), set(ea) == set(eb))
print("E1 first/last dates:", min(r["date"] for r in list(ea.values()) + list(eb.values())),
      max(r["date"] for r in list(ea.values()) + list(eb.values())))
print("E1 seeds", sorted({k[3] for k in ea}))
for kd in ("ufeyn_n10", "feyn_n10"):
    ks = sorted(k for k in ea if k[0] == kd)
    for nm, R in (("1.2.0", ea), ("1.3.0", eb)):
        g = [R[k]["generations"] for k in ks]
        print(" ", kd, nm, "struct", sum(bool(R[k]["structure"]) for k in ks), "of", len(ks),
              "budget", sum(R[k]["time_limit_reached"] for k in ks), "median gens", median(g),
              "arcsin", sum("arcsin" in R[k]["expr"] for k in ks),
              "units_ok", sum(R[k].get("units_ok") is True for k in ks))
t = np.linspace(0, 3.14, 200001)
p = 1.24557 * t - 0.397444 * t ** 2
d = p - np.sin(t)
print("parabola vs sin on [0,3.14]: max |d| %.4f, rms d %.4f, rms sin %.4f, ratio %.3f" % (
    abs(d).max(), np.sqrt((d ** 2).mean()), np.sqrt((np.sin(t) ** 2).mean()),
    np.sqrt((d ** 2).mean()) / np.sqrt((np.sin(t) ** 2).mean())))
