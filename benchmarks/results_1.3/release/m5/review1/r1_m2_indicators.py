"""Review 1: the M2 indicators recomputed from the records, without the
compare scripts. python3 -I r1_m2_indicators.py"""
import os
import statistics as st
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_pair, pools, pool_of, SUITE, UNIT_KINDS  # noqa: E402

A, B, na, nb = load_pair()
FP, MAN, PROBS = pools()
print("lines A %d, B %d; keys A %d, B %d; same keys %s" % (na, nb, len(A), len(B), set(A) == set(B)))
print("kinds:", dict(Counter(k[0] for k in A)))
print("versions A:", Counter(r.get("engine_version") for r in A.values()),
      "B:", Counter(r.get("engine_version") for r in B.values()))
print("status A:", Counter(r.get("status") for r in A.values()))
print("status B:", Counter(r.get("status") for r in B.values()))
print("seeds by kind:", {s: sorted({k[3] for k in A if k[0] == s}) for s in SUITE})
pc = Counter(pool_of(k, FP, MAN) for k in A)
print("pools:", dict(pc))
dates = sorted(r["date"] for r in list(A.values()) + list(B.values()))
print("first and last record date:", dates[0], dates[-1])

for V, R in (("1.2.0", A), ("1.3.0", B)):
    rr = list(R.values())
    def sel(kind, pred=lambda s: True):
        return [r for r in rr if r["kind"] == kind and pred(r["split"])]
    print("\n==", V)
    for kind in ("feyn", "ufeyn", "tf", "utf"):
        s = sel(kind)
        print("  %s exact %d of %d, near %d, miss %d" % (
            SUITE[kind], sum(r["status"] == "EXACT" for r in s), len(s),
            sum(r["status"] == "NEAR" for r in s), sum(r["status"] == "MISS" for r in s)))
    for kind in ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10"):
        s = sel(kind)
        print("  %s structure %d of %d" % (SUITE[kind], sum(bool(r.get("structure")) for r in s), len(s)))
    ts = sel("ts", lambda s: s == "test")
    print("  TS14 test exact %d of %d (with status %d)" % (
        sum(r.get("status") == "EXACT" for r in ts), len(ts), sum("status" in r for r in ts)))
    ts_all = sel("ts")
    print("  TS14 splits:", Counter(r["split"] for r in ts_all))
    tsood = [r for r in ts_all if r["split"] == "ood"]
    print("  TS14 ood collapses (r2<0): %d of %d" % (sum(r["r2"] < 0 for r in tsood), len(tsood)))
    for kind in ("real", "realraw", "tr", "trraw"):
        f = [r["r2"] for r in sel(kind, lambda s: s.startswith("fold"))]
        o = [r["r2"] for r in sel(kind, lambda s: s == "ood")]
        print("  %s folds %d median %.6f; ood %d collapses %d worst %.4g" % (
            SUITE[kind], len(f), st.median(f), len(o), sum(x < 0 for x in o), min(o)))
    u = [r for r in rr if r["kind"] in UNIT_KINDS]
    t = sorted(r["time"] for r in u)
    print("  under units: %d fits, units_ok True %d, median time %.3f (statistics.median %.3f), max %.2f" % (
        len(u), sum(r.get("units_ok") is True for r in u), t[len(t) // 2], st.median(t), t[-1]))
    fe = Counter(SUITE[r["kind"]] for r in rr if r.get("formula_exact") is False)
    print("  formula_exact False by suite:", dict(sorted(fe.items())))
    fpool = Counter(pool_of(k, FP, MAN) for k, r in R.items() if r.get("formula_exact") is False)
    print("  formula_exact False by pool:", dict(fpool))
    fna = Counter(pool_of(k, FP, MAN) for k, r in R.items() if r.get("formula_exact") is None)
    print("  formula_exact None by pool:", dict(fna))
    trig_arc = sum(1 for k, r in R.items() if pool_of(k, FP, MAN) == "trig"
                   and r.get("formula_exact") is False and "arcsin" in (r.get("expr") or ""))
    print("  trig, formula_exact False with arcsin in expr:", trig_arc)
    print("  R6+R7raw folds and test formula_exact False:",
          sum(r.get("formula_exact") is False for r in rr if r["kind"] in ("real", "realraw") and r["split"] != "ood"))
    print("  time_limit_reached:", sum(bool(r.get("time_limit_reached")) for r in rr))
    print("  crashes:", sum(r.get("status") == "CRASH" for r in rr))
