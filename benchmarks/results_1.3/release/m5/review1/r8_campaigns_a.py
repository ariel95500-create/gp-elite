"""Review 1: the campaigns A1, A2, A3 and the confirmation of A3, recomputed
from their Dtrig and e2a records (CHANGELOG lead, DIAGNOSTIC_TP note).
python3 -I r8_campaigns_a.py"""
import json
from collections import defaultdict

R = "/home/user/gp-elite/benchmarks/results_1.3/"
ARC = ("I.26.2", "I.30.5")


def load(p):
    return {(r["kind"], r["problem"], r["seed"]): r for r in map(json.loads, open(R + p))}


for name, a, b in (("A1", "a1/campaign/Dtrig_A.jsonl", "a1/campaign/Dtrig_B.jsonl"),
                   ("A2", "a2/campaign/Dtrig_A.jsonl", "a2/campaign/Dtrig_B.jsonl"),
                   ("A3", "a3/campaign/Dtrig_A.jsonl", "a3/campaign/Dtrig_B.jsonl"),
                   ("A3 conf", "a3/campaign/Dtrig_A_conf.jsonl", "a3/campaign/Dtrig_B_conf.jsonl")):
    A, B = load(a), load(b)
    arc = [k for k in B if k[0] == "feyn" and k[1] in ARC]
    ex = sum(B[k]["status"] == "EXACT" for k in arc)
    exa = sum(B[k]["status"] == "EXACT" and "arcsin" in B[k]["expr"] for k in arc)
    exA = sum(A[k]["status"] == "EXACT" for k in arc)
    print("%s: seeds %s; arcsine laws on F41: exact %d, exact with arcsin %d (1.2.0: %d exact)" % (
        name, sorted({k[2] for k in B}), ex, exa, exA))
    per = defaultdict(lambda: [0, 0])
    for k in B:
        if k[0] == "feyn" and k[1] not in ARC:
            per[k[1]][0] += A[k]["status"] == "EXACT"
            per[k[1]][1] += B[k]["status"] == "EXACT"
    lost = {p: v for p, v in per.items() if v[1] < v[0]}
    gained = {p: v for p, v in per.items() if v[1] > v[0]}
    print("    other eight, F41 exact %d -> %d; equations losing exact fits %s; gaining %s" % (
        sum(v[0] for v in per.values()), sum(v[1] for v in per.values()), lost, gained))
    for k in sorted(B):
        if k[0] == "feyn" and k[1] not in ARC and A[k]["status"] == "EXACT" and B[k]["status"] != "EXACT":
            print("      exact with 1.2.0, not with the candidate:", k, B[k]["status"])
    if any(k[0] == "ufeyn" for k in B):
        u = [k for k in B if k[0] == "ufeyn" and k[1] in ARC]
        print("    U41 arcsine laws: exact %d, with arcsin %d" % (
            sum(B[k]["status"] == "EXACT" for k in u),
            sum(B[k]["status"] == "EXACT" and "arcsin" in B[k]["expr"] for k in u)))
    i262 = sorted(k[2] for k in arc if k[1] == "I.26.2" and B[k]["status"] == "EXACT" and "arcsin" in B[k]["expr"])
    print("    I.26.2 exact with arcsin at seeds", i262)

print("\nSnell on clean data (E2a), the law by the TP test:")
for p in ("a1/examine/e2a_A.jsonl", "a1/examine/e2a_B.jsonl", "a2/campaign/e2a_B.jsonl"):
    rr = [json.loads(l) for l in open(R + p)]
    print("  %s: %d fits, law %d, arcsin in formula %d; %s" % (
        p, len(rr), sum(bool(r["law"]) for r in rr), sum("arcsin" in r["expr"] for r in rr),
        [(r["n"], r["draw"], "%.2g" % r["err_law"]) for r in rr if r["law"]]))
