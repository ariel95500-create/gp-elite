# -*- coding: utf-8 -*-
"""Campaign E2 (benchmarks/results_1.4/PLAN.md, "Campaign E2"): the four
criteria, written before the run, from the paired records of 1.3.0 from PyPI
(A, the candidate before E2: N2 and S1 are withdrawn) and of the candidate
with E2 (B).

  python compare_e2.py tp_A.jsonl tp_B.jsonl bench_A.jsonl bench_B.jsonl
  python compare_e2.py --confirmation tp_A_conf.jsonl tp_B_conf.jsonl

The bench files hold Dnoise and Dguard, as in campaign N2; criterion 3
reads criteria 3 to 5 of N2 there with the definitions of compare_n2.py.
The confirmation (TP, draws 10 to 14) reads criteria 1 and 2.
"""
import json
import os
import sys
from statistics import median

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "n2", "campaign"))
import compare_n2 as N                                      # noqa: E402


def tload(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out[(r["arm"], r["exp"], r["n"], r["noise"], r["draw"])] = r
    return out


def ok(D, arm):
    return [r for k, r in D.items() if k[0] == arm and not r.get("crash")]


def law(D, arm, exp=None):
    return sum(r["law"] for r in ok(D, arm) if exp is None or r["exp"] == exp)


def main(argv):
    conf = argv[0] == "--confirmation"
    if conf:
        argv = argv[1:]
    TA, TB = tload(argv[0]), tload(argv[1])
    N.header(TA, TB, "TP")
    print("  draws %s" % sorted({k[4] for k in TA}))
    exps = sorted({k[1] for k in TA})
    checks = []
    ca, cb = law(TA, "plain", "refroidissement"), law(TB, "plain", "refroidissement")
    checks.append(("1. Newton's cooling, plain arm: the law in at least 10 of its 20 "
                   "fits in B (A %d, B %d)" % (ca, cb), cb >= 10))
    fell = [(e, law(TA, "plain", e), law(TB, "plain", e)) for e in exps
            if e != "refroidissement" and law(TB, "plain", e) < law(TA, "plain", e) - 2]
    checks.append(("2. plain arm: no other experiment falls by more than 2 of 20 (%s)"
                   % (", ".join("%s %d -> %d" % f for f in fell) or "none"), not fell))
    ua, ub = law(TA, "units"), law(TB, "units")
    checks.append(("2. units arm: the law in B no fewer than A - 3 of 200 (%d, %d)"
                   % (ua, ub), ub >= ua - 3))
    if not conf:
        DA, DB = N.load(argv[2], N.bkey), N.load(argv[3], N.bkey)
        N.header(DA, DB, "Dnoise and Dguard")
        for k, nm in (("feyn_n1", "F41N1"), ("feyn_n10", "F41N10"),
                      ("ufeyn_n1", "U41N1"), ("ufeyn_n10", "U41N10")):
            a, b = N.n_structure(DA, k), N.n_structure(DB, k)
            checks.append(("3. %s: B no fewer structures than A - 3 (%d, %d)" % (nm, a, b),
                           b >= a - 3))
        for k, nm in (("feyn", "F41"), ("ufeyn", "U41")):
            a, b = N.n_exact(DA, k), N.n_exact(DB, k)
            checks.append(("3. %s exact: B no fewer than A - 3 (%d, %d)" % (nm, a, b),
                           b >= a - 3))
            pa, pb = N.per_eq(DA, k, "exact"), N.per_eq(DB, k, "exact")
            f = sorted(p for p in pa if pa[p] >= 3 and pb[p] <= 1)
            checks.append(("3. %s: no equation exact at three seeds or more in A falls to "
                           "one or none (%s)" % (nm, ", ".join(f) or "none"), not f))
        folds = lambda D: [r["r2"] for key, r in D.items()
                           if key[0] == "real" and key[2].startswith("fold")]
        ma, mb = median(folds(DA)), median(folds(DB))
        checks.append(("3. R6 folds, median test R²: B not more than 0.005 below A "
                       "(%.4f, %.4f)" % (ma, mb), mb >= ma - 0.005))
        coll = lambda D: sum(r["r2"] < 0 for key, r in D.items()
                             if key[0] in ("real", "realraw") and key[2] == "ood")
        checks.append(("3. R6 + R7raw, collapses out of domain: B not more than A + 2 "
                       "(%d, %d)" % (coll(DA), coll(DB)), coll(DB) <= coll(DA) + 2))
        ub_ = [r for key, r in DB.items() if key[0] in ("ufeyn", "ufeyn_n1", "ufeyn_n10")]
        tu = ok(TB, "units")
        bad = [r for r in ub_ if not r.get("units_ok")] + [r for r in tu if not r.get("units_gate")]
        checks.append(("3. the units guarantee: every model of B under units passes "
                       "(%d of %d on the bench, %d of %d on TP)"
                       % (sum(bool(r.get("units_ok")) for r in ub_), len(ub_),
                          sum(bool(r.get("units_gate")) for r in tu), len(tu)), not bad))
        for arm in ("plain", "units"):
            ta, tb = median(r["time"] for r in ok(TA, arm)), median(r["time"] for r in ok(TB, arm))
            checks.append(("4. TP, %s arm: median time of B at most 1.5 times A (%.1f s, "
                           "%.1f s, ratio %.2f)" % (arm, ta, tb, tb / ta), tb <= 1.5 * ta))
    print("\nCriteria written before the run (PLAN.md%s):"
          % (", confirmation of E2" if conf else ""))
    for name, holds in checks:
        print("  [%s] %s" % ("holds" if holds else "FAILS", name))
    allok = all(h for _, h in checks)
    print(("E2 KEPT" if allok else "E2 NOT KEPT") if conf else
          ("E2 ADOPTED" if allok else "E2 NOT ADOPTED"))
    print("\nBeside, deciding nothing: the law by experiment and arm, A -> B")
    for e in exps:
        print("  %-16s plain %d -> %d   units %d -> %d" % (
            e, law(TA, "plain", e), law(TB, "plain", e), law(TA, "units", e),
            law(TB, "units", e)))
    for r in sorted(ok(TB, "plain"), key=lambda r: (r["n"], r["noise"], r["draw"])):
        if r["exp"] == "refroidissement":
            print("  B, cooling, %d pts %d %% draw %d: law %s; %s" % (
                r["n"], round(100 * r["noise"]), r["draw"], r["law"], r["expr"][:90]))
    if not conf:
        print("  the structures by equation where they differ (F41N1, F41N10, U41N1, U41N10):")
        for p in sorted({key[1] for key in DA if key[0] == "feyn_n1"}):
            cells = ["%d -> %d" % (N.per_eq(DA, k, "s")[p], N.per_eq(DB, k, "s")[p])
                     for k in ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10")]
            if any(c.split(" -> ")[0] != c.split(" -> ")[1] for c in cells):
                print("    %-10s %s" % (p, "   ".join(cells)))


if __name__ == "__main__":
    main(sys.argv[1:])
