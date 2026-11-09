"""Review 1: paired comparisons of M2 (pool physical identity, status and
structure changes of the pool trig, arcsine laws, frozen test set).
python3 -I r2_m2_pairs.py"""
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_pair, pools, pool_of, SUITE, UNIT_KINDS  # noqa: E402

A, B, na, nb = load_pair()
FP, MAN, PROBS = pools()
K = sorted(A)
phys = [k for k in K if pool_of(k, FP, MAN) == "physical"]
trig = [k for k in K if pool_of(k, FP, MAN) == "trig"]

print("== pool physical: %d fits" % len(phys))
det = [k for k in phys if not A[k]["time_limit_reached"] and not B[k]["time_limit_reached"]]
dif = [k for k in det if (A[k]["expr"], A[k]["err"], A[k]["formula_exact"]) != (B[k]["expr"], B[k]["err"], B[k]["formula_exact"])]
print("neither at budget %d, differ %d" % (len(det), len(dif)))
# fuller check on the det fits: every result field
fields = ["expr", "err", "formula_exact", "size", "r2", "generations", "status", "structure",
          "err_structure", "err_ood", "units_ok", "elementary_seed", "tolerant_seed", "expr_11"]
fd = Counter()
for k in det:
    for f in fields:
        if A[k].get(f) != B[k].get(f):
            fd[f] += 1
print("on those, any result field differing:", dict(fd))
long_expr = sum(1 for k in det if len(A[k]["expr"]) >= 160 or len(B[k]["expr"]) >= 160)
print("on those, expr at the truncation length 160:", long_expr)
print("expr length >=160 among all fits A %d B %d" % (
    sum(len(r["expr"]) >= 160 for r in A.values()), sum(len(r["expr"]) >= 160 for r in B.values())))
same = sum(A[k]["expr"] == B[k]["expr"] for k in phys)
print("same expr in %d of %d physical" % (same, len(phys)))
budget = Counter((A[k]["time_limit_reached"], B[k]["time_limit_reached"]) for k in phys)
print("physical, (A at budget, B at budget):", dict(budget))
notsame = [k for k in phys if A[k]["expr"] != B[k]["expr"]]
print("physical fits with a different expr:", len(notsame))
for k in notsame:
    print("   ", k, A[k]["time_limit_reached"], B[k]["time_limit_reached"], A[k].get("status"), B[k].get("status"),
          A[k].get("structure"), B[k].get("structure"))
st_ch = [k for k in phys if A[k].get("status") != B[k].get("status")
         or bool(A[k].get("structure")) != bool(B[k].get("structure"))]
print("physical status or structure changed:", st_ch)
for k in st_ch:
    print("   ", k, A[k].get("status"), B[k].get("status"), A[k]["time_limit_reached"], B[k]["time_limit_reached"],
          A[k]["time"], B[k]["time"])
# physical: changes in collapses, TS14 etc
print("physical formula_exact differs:", sum(A[k]["formula_exact"] != B[k]["formula_exact"] for k in phys))
for k in phys:
    if A[k]["formula_exact"] != B[k]["formula_exact"]:
        print("   ", k, A[k]["formula_exact"], B[k]["formula_exact"])

print("\n== pool trig: %d fits" % len(trig))
by = defaultdict(Counter)
for k in trig:
    s = SUITE[k[0]]
    d = by[s]
    d["fits"] += 1
    if "status" in A[k]:
        d["status changed"] += A[k]["status"] != B[k]["status"]
        d["A exact"] += A[k]["status"] == "EXACT"
        d["B exact"] += B[k]["status"] == "EXACT"
        d["gain exact"] += A[k]["status"] != "EXACT" and B[k]["status"] == "EXACT"
        d["lose exact"] += A[k]["status"] == "EXACT" and B[k]["status"] != "EXACT"
    if "structure" in A[k]:
        d["A struct"] += bool(A[k]["structure"])
        d["B struct"] += bool(B[k]["structure"])
        d["gain struct"] += (not A[k]["structure"]) and bool(B[k]["structure"])
        d["lose struct"] += bool(A[k]["structure"]) and not B[k]["structure"]
    d["arcsin in B"] += "arcsin" in B[k]["expr"]
    d["arcsin in A"] += "arcsin" in A[k]["expr"]
    d["fe False A"] += A[k]["formula_exact"] is False
    d["fe False B"] += B[k]["formula_exact"] is False
    d["fe False B arcsin"] += B[k]["formula_exact"] is False and "arcsin" in B[k]["expr"]
for s in sorted(by):
    print(" ", s, dict(by[s]))

print("\n-- structure changes, pool trig, by problem")
for kind in ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10"):
    g = Counter(); l = Counter()
    for k in trig:
        if k[0] == kind:
            if not A[k]["structure"] and B[k]["structure"]:
                g[k[1]] += 1
            if A[k]["structure"] and not B[k]["structure"]:
                l[k[1]] += 1
    print("  %s gains %s loses %s (net %+d)" % (SUITE[kind], dict(g), dict(l), sum(g.values()) - sum(l.values())))
    for p in sorted(set(k[1] for k in trig if k[0] == kind)):
        a = sum(bool(A[k]["structure"]) for k in trig if k[0] == kind and k[1] == p)
        b = sum(bool(B[k]["structure"]) for k in trig if k[0] == kind and k[1] == p)
        if a != b or p in ("I.26.2", "I.30.5"):
            print("     %s %d -> %d" % (p, a, b))

print("\n-- exact changes, pool trig, F41/U41/TF78/TF78u/TS14, by problem")
for kind in ("feyn", "ufeyn", "tf", "utf", "ts"):
    for p in sorted(set(k[1] for k in trig if k[0] == kind)):
        ks = [k for k in trig if k[0] == kind and k[1] == p and "status" in A[k]]
        a = sum(A[k]["status"] == "EXACT" for k in ks)
        b = sum(B[k]["status"] == "EXACT" for k in ks)
        ch = sum(A[k]["status"] != B[k]["status"] for k in ks)
        if a != b or ch:
            print("  %s %s exact %d -> %d, status changed %d: %s" % (
                SUITE[kind], p, a, b, ch, [(k[2], k[3], A[k]["status"], B[k]["status"]) for k in ks if A[k]["status"] != B[k]["status"]]))

print("\n-- the arcsine laws")
for kind in ("feyn", "ufeyn", "feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10"):
    for p in ("I.26.2", "I.30.5"):
        for s in range(5):
            k = (kind, p, "test", s)
            if k in B:
                print("  %s %s s%d A:%s/%s B:%s/%s arcsin=%s seed=%s | %s" % (
                    SUITE[kind], p, s, A[k].get("status"), A[k].get("structure"), B[k].get("status"),
                    B[k].get("structure"), "arcsin" in B[k]["expr"], B[k].get("elementary_seed"),
                    B[k]["expr"][:70]))
arc_ok = {kind: sum(1 for p in ("I.26.2", "I.30.5") for s in range(5)
                    if B[(kind, p, "test", s)]["status"] == "EXACT" and "arcsin" in B[(kind, p, "test", s)]["expr"])
          for kind in ("feyn", "ufeyn")}
print("exact with arcsin:", arc_ok)

print("\n-- frozen test set, pool trig")
tfk = [k for k in trig if k[0] == "tf"]
print("TF78 trig problems:", len({k[1] for k in tfk}), "fits", len(tfk),
      "exact A", sum(A[k]["status"] == "EXACT" for k in tfk), "B", sum(B[k]["status"] == "EXACT" for k in tfk))
utfk = [k for k in trig if k[0] == "utf"]
print("TF78u trig exact A", sum(A[k]["status"] == "EXACT" for k in utfk), "B", sum(B[k]["status"] == "EXACT" for k in utfk))
for kind in ("tf", "utf"):
    for s in range(5, 10):
        k = (kind, "feynman_test_10", "test", s)
        print("  ", kind, s, A[k]["status"], B[k]["status"], A[k]["err"], B[k]["err"])
tsk = [k for k in trig if k[0] == "ts"]
print("TS14 trig systems:", sorted({k[1] for k in tsk}), "fits", len(tsk))
print("TS14 trig test fits:", sum(k[2] == "test" for k in tsk))
print("TS14 trig status changed:", [(k, A[k]["status"], B[k]["status"]) for k in tsk if A[k]["status"] != B[k]["status"]])
print("TS14 trig exact A:", [k for k in tsk if A[k]["status"] == "EXACT"], "B:", [k for k in tsk if B[k]["status"] == "EXACT"])
print("TS14 all exact test A:", [k for k in K if k[0] == "ts" and k[2] == "test" and A[k]["status"] == "EXACT"])
print("TS14 all exact test B:", [k for k in K if k[0] == "ts" and k[2] == "test" and B[k]["status"] == "EXACT"])
print("TS14 pools:", Counter(MAN[n]["pool"] for n in {k[1] for k in K if k[0] == "ts"}))
print("TS14 exact_scorable:", {n: MAN[n].get("exact_scorable") for n in sorted({k[1] for k in K if k[0] == "ts"})})
# III_8_54
for kind in ("tf", "utf"):
    ks = [k for k in K if k[0] == kind and k[1] == "feynman_III_8_54"]
    print("  III_8_54", kind, [(k[3], A[k]["status"], B[k]["status"]) for k in ks], MAN["feynman_III_8_54"]["pool"])
print("feynman_test_10 manifest:", {x: MAN["feynman_test_10"].get(x) for x in MAN["feynman_test_10"] if x not in ("sha256",)})
