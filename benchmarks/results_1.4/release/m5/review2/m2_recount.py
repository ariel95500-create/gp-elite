"""Second review of M5 (1.4.0): the figures of M2 counted again from its
records, by code written for this review (it imports nothing of the
comparison scripts and nothing of gp_elite).

  python3 -I m2_recount.py  [M2_DIR]  [N2B_TP_RECORDS]

M2_DIR defaults to benchmarks/results_1.4/release/m2; N2B_TP_RECORDS to the
TP records of B in campaign N2b. Prints every figure the documents of 1.4.0
quote from M2, and the counts beside them.
"""
import json
import os
import sys
from collections import Counter, defaultdict
from statistics import median

HERE = os.path.dirname(os.path.abspath(__file__))
REL = os.path.normpath(os.path.join(HERE, "..", ".."))
M2 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REL, "m2")


def bench(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            k = (r["kind"], r["problem"], r["split"], r["seed"])
            assert k not in out, k
            out[k] = r
    return out


def tp(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            k = (r["arm"], r["exp"], r["n"], r["noise"], r["draw"])
            assert k not in out, k
            out[k] = r
    return out


def sel(D, kind, split=None):
    return [r for k, r in D.items() if k[0] == kind and (split is None or split(k[2]))]


def exact(rs):
    return sum(r.get("status") == "EXACT" for r in rs)


def struct(rs):
    return sum(bool(r.get("structure")) for r in rs)


def seeds(r):
    return r.get("tolerant_seed") or None


A = bench(os.path.join(M2, "campaignR_1.3.0.jsonl"))
B = bench(os.path.join(M2, "campaignR_1.4.0.jsonl"))
print("bench jobs", len(A), len(B), "same keys", set(A) == set(B))
print("crashes", sum(r.get("status") == "CRASH" or bool(r.get("crash")) for r in A.values()),
      sum(r.get("status") == "CRASH" or bool(r.get("crash")) for r in B.values()))
print("kinds", sorted(Counter(k[0] for k in A).items()))
print("versions", {r.get("engine_version") for r in A.values()},
      {r.get("engine_version") for r in B.values()})

folds = lambda s: s.startswith("fold")
ood = lambda s: s == "ood"
for name, D in (("1.3.0", A), ("1.4.0", B)):
    print("\n==", name)
    print(" F41 exact", exact(sel(D, "feyn")), " U41 exact", exact(sel(D, "ufeyn")))
    print(" F41N1/N10 structure", struct(sel(D, "feyn_n1")), struct(sel(D, "feyn_n10")))
    print(" U41N1/N10 structure", struct(sel(D, "ufeyn_n1")), struct(sel(D, "ufeyn_n10")))
    print(" TF78 exact", exact(sel(D, "tf")), "of", len(sel(D, "tf")),
          " TF78 units exact", exact(sel(D, "utf")), "of", len(sel(D, "utf")))
    ts = sel(D, "ts", lambda s: s == "test")
    print(" TS14 test exact", exact(ts), "of", len(ts), " all TS14 fits", len(sel(D, "ts")),
          " splits", sorted(Counter(k[2] for k in D if k[0] == "ts").items()))
    for kind in ("real", "realraw", "tr", "trraw"):
        f = [r["r2"] for r in sel(D, kind, folds)]
        o = [r["r2"] for r in sel(D, kind, ood)]
        print(" %-8s folds %d median %.4f | ood %d collapses %d worst %.6g" % (
            kind, len(f), median(f), len(o), sum(x < 0 for x in o), min(o)))
    for kind in ("tf_n1", "tf_n10", "utf_n1", "utf_n10"):
        print(" %s structure %d of %d" % (kind, struct(sel(D, kind)), len(sel(D, kind))))
    uk = [r for k, r in D.items() if k[0] in ("ufeyn", "ufeyn_n1", "ufeyn_n10", "utf",
                                                "utf_n1", "utf_n10")]
    print(" under units", len(uk), "units_ok True", sum(r.get("units_ok") is True for r in uk))
    fe = Counter()
    for k, r in D.items():
        fe[k[0]] += r.get("formula_exact") is False
    print(" formula_exact False by kind", dict(sorted(fe.items())))
    print(" formula_exact False real+realraw all splits", fe["real"] + fe["realraw"],
          "of", len(sel(D, "real")) + len(sel(D, "realraw")),
          "| tr+trraw", fe["tr"] + fe["trraw"], "of", len(sel(D, "tr")) + len(sel(D, "trraw")))
    nofold = sum(r.get("formula_exact") is False for k, r in D.items()
                 if k[0] in ("real", "realraw") and k[2] != "ood")
    print(" formula_exact False real+realraw folds and test", nofold)
    # never-exact equations
    for kind, lab in (("feyn", "F41"), ("ufeyn", "U41"), ("tf", "TF78")):
        per = defaultdict(int)
        for k, r in D.items():
            if k[0] == kind:
                per[k[1]] += r.get("status") == "EXACT"
        never = sorted(p for p, n in per.items() if n == 0)
        print(" %s never exact %d %s" % (lab, len(never), never if len(never) < 8 else ""))
    fam = Counter()
    famn = Counter()
    for k, r in D.items():
        if k[0] == "tf":
            famn[r.get("family")] += 1
            fam[r.get("family")] += r.get("status") == "EXACT"
    print(" TF78 by family", dict(fam), "of", dict(famn))
    # budget
    bud = [r["time"] for r in D.values() if r.get("time_limit_reached")]
    bud.sort()
    print(" budget reached: %d fits, median %.3f s, max %.2f s, min %.2f s" % (
        len(bud), median(bud), bud[-1], bud[0]))
    tol = Counter()
    for k, r in D.items():
        tol[k[0]] += bool(seeds(r))
    print(" fits with tolerant seeds by kind", dict(sorted(tol.items())))

# where 1.4 does not act
common = sorted(set(A) & set(B))
same = [k for k in common if seeds(A[k]) == seeds(B[k])]
none = [k for k in same if seeds(A[k]) is None]
det = [k for k in same if not A[k].get("time_limit_reached") and not B[k].get("time_limit_reached")]
diff = [k for k in det if (A[k].get("expr"), A[k].get("err"), A[k].get("formula_exact"))
        != (B[k].get("expr"), B[k].get("err"), B[k].get("formula_exact"))]
long_ = [k for k in det if len(A[k].get("expr") or "") >= 160 or len(B[k].get("expr") or "") >= 160]
print("\nsame tolerant seeds: %d of %d (none: %d); neither at budget: %d; differ: %d;"
      " of those 782, expr of 160 chars or more (truncated): %d" % (
          len(same), len(common), len(none), len(det), len(diff), len(long_)))
print("det by kind", dict(sorted(Counter(k[0] for k in det).items())))
print("det with seeds (not none):", sum(seeds(A[k]) is not None for k in det))
print("same expr in", sum(A[k].get("expr") == B[k].get("expr") for k in common), "of", len(common))
# budget reached in exactly one version
one = [k for k in common if bool(A[k].get("time_limit_reached")) != bool(B[k].get("time_limit_reached"))]
print("budget reached in one version only:", len(one), Counter(k[0] for k in one))

# structures by equation
print("\nstructures by equation where they differ (F41N1, F41N10, U41N1, U41N10)")
probs = sorted({k[1] for k in A if k[0] == "feyn_n1"})
for p in probs:
    cells = []
    for kind in ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10"):
        a = sum(bool(r.get("structure")) for k, r in A.items() if k[0] == kind and k[1] == p)
        b = sum(bool(r.get("structure")) for k, r in B.items() if k[0] == kind and k[1] == p)
        cells.append((a, b))
    if any(a != b for a, b in cells):
        print("  %-10s %s" % (p, "  ".join("%d->%d" % c for c in cells)))

# the fits of I.27.6 and III.15.12 at 10 % noise: seeds and budget
print("\nI.27.6 and III.15.12 at 10 % noise, fit by fit")
for kind in ("feyn_n10", "ufeyn_n10"):
    for p in ("I.27.6", "III.15.12"):
        for s in range(5):
            k = (kind, p, "test", s)
            if k in A:
                print("  %s %s s%d struct %s->%s same seeds %s budget %s/%s nA %d nB %d" % (
                    kind, p, s, bool(A[k].get("structure")), bool(B[k].get("structure")),
                    seeds(A[k]) == seeds(B[k]), A[k].get("time_limit_reached"),
                    B[k].get("time_limit_reached"),
                    len((seeds(A[k]) or "").split(" | ")) if seeds(A[k]) else 0,
                    len((seeds(B[k]) or "").split(" | ")) if seeds(B[k]) else 0))

# status changes on the test set and the bench, with seeds same or not
print("\nstatus changes by kind: (n, of which same seeds, EXACT lost, EXACT gained)")
for kind in sorted({k[0] for k in common}):
    ch = [k for k in common if k[0] == kind and A[k].get("status") != B[k].get("status")]
    if ch:
        print("  %-10s %d same-seeds %d lost %d gained %d" % (
            kind, len(ch), sum(seeds(A[k]) == seeds(B[k]) for k in ch),
            sum(A[k].get("status") == "EXACT" and B[k].get("status") != "EXACT" for k in ch),
            sum(B[k].get("status") == "EXACT" and A[k].get("status") != "EXACT" for k in ch)))
        for k in ch:
            if seeds(A[k]) == seeds(B[k]):
                print("     same seeds:", k, A[k].get("status"), "->", B[k].get("status"),
                      "budget", A[k].get("time_limit_reached"), B[k].get("time_limit_reached"))

# exact lost on exact data with other seeds (TF78, TS14, F41, U41, utf)
print("\nEXACT lost where 1.4.0 places other seeds, exact-data kinds")
for kind in ("feyn", "ufeyn", "tf", "utf", "ts"):
    lost = [k for k in common if k[0] == kind and A[k].get("status") == "EXACT"
            and B[k].get("status") != "EXACT"]
    print("  %-6s lost %d (other seeds %d)  gained %d" % (
        kind, len(lost), sum(seeds(A[k]) != seeds(B[k]) for k in lost),
        sum(1 for k in common if k[0] == kind and B[k].get("status") == "EXACT"
            and A[k].get("status") != "EXACT")))

# TR25raw seeds
print("\nTR25raw fits with tolerant seeds")
for k in common:
    if k[0] == "trraw" and (seeds(A[k]) or seeds(B[k])):
        print("  %s same seeds %s same expr %s r2 %.5f -> %.5f (d %.4f)" % (
            k, seeds(A[k]) == seeds(B[k]), A[k].get("expr") == B[k].get("expr"),
            A[k]["r2"], B[k]["r2"], B[k]["r2"] - A[k]["r2"]))

# was every seed of 1.3.0 still placed by 1.4.0 (as recorded)?
print("\nseeds of 1.3.0 not in the record of 1.4.0 (forms compared without their scores)")


def forms(s):
    out = []
    for part in (s or "").split(" | "):
        part = part.strip()
        if part:
            # drop the trailing score in parentheses
            i = part.rfind(" (")
            out.append(part[:i] if i > 0 else part)
    return out


miss = Counter()
missk = []
for k in common:
    fa, fb = forms(seeds(A[k])), set(forms(seeds(B[k])))
    m = [f for f in fa if f not in fb]
    if m:
        miss[k[0]] += 1
        missk.append((k, m, len(fa), len(fb)))
print("  fits where a seed of 1.3.0 is not in the record of 1.4.0:", sum(miss.values()), dict(miss))
for k, m, na, nb in missk[:15]:
    print("   ", k, "1.3.0 places", na, "1.4.0 places", nb, "missing e.g.", m[0][:90])
cnt = Counter(len(forms(seeds(r))) for r in B.values() if seeds(r))
print("  number of seeds per fit, 1.4.0:", sorted(cnt.items()))
cnta = Counter(len(forms(seeds(r))) for r in A.values() if seeds(r))
print("  number of seeds per fit, 1.3.0:", sorted(cnta.items()))
recl = Counter(len(r.get("tolerant_seed") or "") for r in B.values())
print("  longest tolerant_seed string, 1.4.0:", max(recl))

# TP and TPT10
camp = os.path.join(REL, "..", "n2b", "campaign")
for setname, fa, fb in (("TP", "tp_1.3.0.jsonl", "tp_1.4.0.jsonl"),
                        ("TPT10", "tpt10_1.3.0.jsonl", "tpt10_1.4.0.jsonl")):
    ta, tb = tp(os.path.join(M2, fa)), tp(os.path.join(M2, fb))
    print("\n==", setname, len(ta), len(tb), set(ta) == set(tb))
    for arm in ("plain", "units"):
        xa = [r for k, r in ta.items() if k[0] == arm]
        xb = [r for k, r in tb.items() if k[0] == arm]
        print("  %s law %d -> %d useful %d -> %d median time %.2f -> %.2f (ratio %.3f)" % (
            arm, sum(r["law"] for r in xa), sum(r["law"] for r in xb),
            sum(r["useful"] for r in xa), sum(r["useful"] for r in xb),
            median(r["time"] for r in xa), median(r["time"] for r in xb),
            median(r["time"] for r in xb) / median(r["time"] for r in xa)))
        if arm == "units":
            print("    units_gate True 1.4.0: %d of %d; 1.3.0: %d" % (
                sum(bool(r.get("units_gate")) for r in xb), len(xb),
                sum(bool(r.get("units_gate")) for r in xa)))
    ch = [k for k in ta if ta[k]["law"] != tb[k]["law"]]
    print("  fit by fit, law changes: %d (%s)" % (len(ch), Counter(k[0] for k in ch)))
    for k in sorted(ch):
        print("    %s %s -> %s" % (k, ta[k]["law"], tb[k]["law"]))
    by = defaultdict(lambda: [0, 0, 0, 0])
    for k in ta:
        d = by[k[1]]
        if k[0] == "plain":
            d[0] += ta[k]["law"]
            d[1] += tb[k]["law"]
        else:
            d[2] += ta[k]["law"]
            d[3] += tb[k]["law"]
    for e in sorted(by):
        print("    %-16s plain %d -> %d  units %d -> %d" % ((e,) + tuple(by[e])))
    same_expr = sum(ta[k]["expr"] == tb[k]["expr"] for k in ta)
    print("  same expr 1.3.0 vs 1.4.0:", same_expr)
