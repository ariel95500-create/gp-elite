"""Second review: campaign H1 and confirmation, from the records."""
import json
import statistics as st
from collections import Counter

D = "/home/user/gp-elite/benchmarks/results_1.2/h1/campaign/"


def load(p):
    out = {}
    for l in open(D + p):
        if l.strip():
            r = json.loads(l)
            out[(r["kind"], r["problem"], r["split"], r["seed"])] = r
    return out


def loadtp(p):
    out = {}
    for l in open(D + p):
        if l.strip():
            r = json.loads(l)
            out[(r["arm"], r["exp"], r["n"], r["noise"], r["draw"])] = r
    return out


for suf in ("", "_conf"):
    A, H = load("D_A%s.jsonl" % suf), load("D_H1%s.jsonl" % suf)
    print("=== D%s" % suf, len(A), len(H), Counter(r["engine_version"] for r in A.values()), Counter(r["engine_version"] for r in H.values()))
    for kd in sorted({k[0] for k in A}):
        for R, nm in ((A, "A"), (H, "H1")):
            rr = [r for k, r in R.items() if k[0] == kd]
            t = [r["time"] for r in rr]
            g = [r.get("generations") for r in rr]
            print(" ", kd, nm, len(rr), "EXACT", sum(r.get("status") == "EXACT" for r in rr), "NEAR", sum(r.get("status") == "NEAR" for r in rr),
                  "struct", sum(bool(r.get("structure")) for r in rr), "med t %.2f" % st.median(t), "max %.2f" % max(t), "gen med", st.median(g),
                  "units_ok", sum(r.get("units_ok") is True for r in rr))
    for R, nm in ((A, "A"), (H, "H1")):
        f = [r["r2"] for k, r in R.items() if k[0] == "real" and k[2].startswith("fold")]
        if f:
            print(" ", nm, "R6 folds", len(f), "median %.6f" % st.median(f))
            for kd in ("real", "realraw"):
                o = [r["r2"] for k, r in R.items() if k[0] == kd and k[2] == "ood"]
                print("   ", kd, "ood", len(o), "collapses", sum(x < 0 for x in o))
            f7 = [r["r2"] for k, r in R.items() if k[0] == "realraw" and k[2].startswith("fold")]
            print("   R7raw folds median %.6f" % st.median(f7))
    # equations per seeds
    for kd in ("feyn", "ufeyn"):
        if not any(k[0] == kd for k in A):
            continue
        ea, eh = Counter(), Counter()
        for k in A:
            if k[0] == kd:
                ea[k[1]] += A[k]["status"] == "EXACT"
                eh[k[1]] += H[k]["status"] == "EXACT"
        ch = {p: (ea[p], eh[p]) for p in ea if ea[p] != eh[p]}
        print(" ", kd, "changes", ch)
    # max time under units
    for R, nm in ((A, "A"), (H, "H1")):
        u = [(r["time"], k) for k, r in R.items() if k[0].startswith("ufeyn")]
        if u:
            print(" ", nm, "longest under units", max(u))

for suf in ("", "_conf"):
    A, H = loadtp("tp_A%s.jsonl" % suf), loadtp("tp_H1%s.jsonl" % suf)
    print("=== TP%s" % suf, len(A), len(H), sorted({k[4] for k in A}))
    for arm in ("plain", "units"):
        for R, nm in ((A, "A"), (H, "H1")):
            rr = [r for k, r in R.items() if k[0] == arm]
            print(" ", arm, nm, len(rr), "med t %.2f" % st.median(r["time"] for r in rr), "law", sum(r["law"] for r in rr), "useful", sum(r["useful"] for r in rr),
                  "gen med", st.median(r["generations"] for r in rr))
    # ten-point fits: same formula?
    for arm in ("plain", "units"):
        ks = [k for k in A if k[0] == arm and k[2] == 10]
        same = sum(A[k]["expr"] == H[k]["expr"] for k in ks)
        lawdiff = sum(A[k]["law"] != H[k]["law"] for k in ks)
        print(" ", arm, "10 points:", len(ks), "same expr", same, "law differs", lawdiff)
        ks = [k for k in A if k[0] == arm]
        print(" ", arm, "all:", len(ks), "same expr", sum(A[k]["expr"] == H[k]["expr"] for k in ks), "law differs", sum(A[k]["law"] != H[k]["law"] for k in ks))
