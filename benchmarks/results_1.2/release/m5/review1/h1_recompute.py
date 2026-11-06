"""Recompute the figures of campaign H1 (bench D and TP) quoted in LIMITATIONS point 10,
the CHANGELOG and DIAGNOSTIC_TP (read-only)."""
import json
from collections import Counter, defaultdict
from statistics import median

C = "/home/user/gp-elite/benchmarks/results_1.2/h1/campaign/"


def load(p):
    return [json.loads(l) for l in open(p) if l.strip()]


for tag in ("", "_conf"):
    A = load(C + "D_A%s.jsonl" % tag)
    H = load(C + "D_H1%s.jsonl" % tag)
    print("== bench D%s" % tag, len(A), len(H))
    print(" engines", Counter((r.get("engine_version"), r.get("engine_file", "")[:30]) for r in A), Counter((r.get("engine_version"), r.get("engine_file", "")[:30]) for r in H))
    for name, R in (("A", A), ("H1", H)):
        out = {}
        for kind in ("feyn", "ufeyn"):
            out[kind + " exact"] = sum(r["kind"] == kind and r.get("status") == "EXACT" for r in R)
        for kind in ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10"):
            out[kind + " struct"] = sum(r["kind"] == kind and bool(r.get("structure")) for r in R)
            out[kind + " NEAR"] = sum(r["kind"] == kind and r.get("status") == "NEAR" for r in R)
        for kind in ("real", "realraw"):
            f = [r["r2"] for r in R if r["kind"] == kind and r["split"].startswith("fold")]
            o = [r["r2"] for r in R if r["kind"] == kind and r["split"] == "ood"]
            if f:
                out[kind + " fold median"] = round(median(f), 4)
                out[kind + " ood collapses"] = sum(x < 0 for x in o)
                out[kind + " n ood"] = len(o)
        for kind in ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10", "real", "realraw", "feyn", "ufeyn"):
            t = [r["time"] for r in R if r["kind"] == kind]
            if t:
                out[kind + " median time"] = round(median(t), 2)
                out[kind + " max time"] = max(t)
        units = [r for r in R if r["kind"].startswith("ufeyn")]
        out["units_ok"] = "%d of %d" % (sum(r.get("units_ok") is True for r in units), len(units))
        print(" ", name, out)

print()
for tag in ("", "_conf"):
    A = load(C + "tp_A%s.jsonl" % tag)
    H = load(C + "tp_H1%s.jsonl" % tag)
    print("== TP%s" % tag, len(A), len(H), sorted(A[0].keys())[:40])
    for name, R in (("A", A), ("H1", H)):
        for arm in ("plain", "units"):
            rr = [r for r in R if r["arm"] == arm]
            t = [r.get("time") for r in rr]
            print(" ", name, arm, len(rr), "median time", round(median(t), 2), "law", sum(bool(r.get("law")) for r in rr))
    # formulas differ between A and H1
    ka = {(r["exp"], r["n"], r["noise"], r["draw"], r["arm"]): r for r in A}
    kh = {(r["exp"], r["n"], r["noise"], r["draw"], r["arm"]): r for r in H}
    same = sum(ka[k]["expr"] == kh[k]["expr"] for k in ka)
    lawdiff = sum(bool(ka[k]["law"]) != bool(kh[k]["law"]) for k in ka)
    print("  same formula A vs H1:", same, "of", len(ka), "; law differs:", lawdiff)
    for arm in ("plain", "units"):
        ks = [k for k in ka if k[4] == arm]
        print("   ", arm, "same formula", sum(ka[k]["expr"] == kh[k]["expr"] for k in ks), "of", len(ks), "law differs", sum(bool(ka[k]["law"]) != bool(kh[k]["law"]) for k in ks))
