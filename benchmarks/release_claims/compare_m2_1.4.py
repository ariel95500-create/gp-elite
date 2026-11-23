"""M2 of benchmarks/results_1.4/PLAN_RELEASE_1.4.md: campaign R of 1.4.0
paired with 1.3.0 (benchmarks/phase1_bench.py run-paired), the two sets of
TP paired the same way (benchmarks/tp_diagnostic.py run-paired), and the
criteria the plan wrote before they ran.

  python benchmarks/release_claims/compare_m2_1.4.py BENCH_1.3.0 BENCH_1.4.0 \\
         TP_1.3.0 TP_1.4.0 TPT10_1.3.0 TPT10_1.4.0 TP_OF_B_IN_CAMPAIGN_N2B

Definitions, as in the campaigns of 1.4 (results_1.4/n2/campaign/
compare_n2.py):
- an exact law: status EXACT (1 - R² below 1e-9 on the test rows);
- a structure: the record's "structure";
- the noise-tolerant seeds placed: the record's "tolerant_seed";
- a fit at its time budget: the record's "time_limit_reached";
- the law on TP: the record's "law"; its units guarantee: "units_gate".
"""
import json
import os
import sys
from collections import Counter
from statistics import median

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from compare_m2 import load, indicators  # noqa: E402
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "compare_m2_1_2", os.path.join(HERE, "compare_m2_1.2.py"))
_m12 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m12)
units, SUITE = _m12.units, dict(_m12.SUITE)
SUITE.update({"tf_n1": "TF78N1", "tf_n10": "TF78N10", "utf_n1": "TF78N1 under units",
              "utf_n10": "TF78N10 under units"})
UNIT_KINDS = ("ufeyn", "ufeyn_n1", "ufeyn_n10", "utf", "utf_n1", "utf_n10")


def tload(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out[(r["arm"], r["exp"], r["n"], r["noise"], r["draw"])] = r
    return out


def crashed(r):
    return r.get("status") == "CRASH" or bool(r.get("crash"))


def per_eq_exact(D, kind):
    c = Counter()
    for k, r in D.items():
        if k[0] == kind:
            c[k[1]] += r.get("status") == "EXACT"
    return c


def fell(DA, DB, kind):
    pa, pb = per_eq_exact(DA, kind), per_eq_exact(DB, kind)
    return sorted(p for p in pa if pa[p] >= 3 and pb[p] <= 1)


def n_struct(D, kind):
    return sum(bool(r.get("structure")) for k, r in D.items() if k[0] == kind)


def tp_arm(D, arm):
    return [r for k, r in D.items() if k[0] == arm and not crashed(r)]


def tp_law(D, arm, exp=None):
    return sum(r["law"] for r in tp_arm(D, arm) if exp is None or r["exp"] == exp)


def main(argv):
    a, b = load(argv[0]), load(argv[1])
    ta, tb = tload(argv[2]), tload(argv[3])
    qa, qb = tload(argv[4]), tload(argv[5])
    tcamp = tload(argv[6])
    for name, x, y in (("Benches", a, b), ("TP", ta, tb), ("TPT10", qa, qb)):
        print("%s: %d jobs in 1.3.0, %d in 1.4.0, the same jobs: %s; crashes %d and %d"
              % (name, len(x), len(y), set(x) == set(y),
                 sum(crashed(r) for r in x.values()), sum(crashed(r) for r in y.values())))
        print("  engines: %s; %s" % (
            sorted({(r.get("engine_version"), r.get("engine_file")) for r in x.values()}),
            sorted({(r.get("engine_version"), r.get("engine_file")) for r in y.values()})))

    ia, ib = indicators(a), indicators(b)
    ua, ub = units(a), units(b)
    print("\n| indicator | 1.3.0 | 1.4.0 |\n|---|---|---|")
    for d1, d2 in ((ia, ib), (ua, ub)):
        for k in d1:
            print("| %s | %s | %s |" % (k, d1[k], d2[k]))
    for kind in ("tf_n1", "tf_n10", "utf_n1", "utf_n10"):
        print("| %s structure retrieved | %d | %d |" % (SUITE[kind], n_struct(a, kind),
                                                      n_struct(b, kind)))
    ua_all = [r for k, r in a.items() if k[0] in UNIT_KINDS]
    ub_all = [r for k, r in b.items() if k[0] in UNIT_KINDS]
    print("| every kind under units, TF78N included: fits passing the audit | %d of %d "
          "| %d of %d |" % (sum(r.get("units_ok") is True for r in ua_all), len(ua_all),
                            sum(r.get("units_ok") is True for r in ub_all), len(ub_all)))

    # where 1.4 does not act: the same noise-tolerant seeds, no budget reached
    common = sorted(set(a) & set(b))
    same_seeds = [k for k in common if not crashed(a[k]) and not crashed(b[k])
                  and (a[k].get("tolerant_seed") or None) == (b[k].get("tolerant_seed") or None)]
    det = [k for k in same_seeds if not a[k].get("time_limit_reached")
           and not b[k].get("time_limit_reached")]
    differs = [k for k in det if a[k].get("expr") != b[k].get("expr")
               or a[k].get("err") != b[k].get("err")
               or a[k].get("formula_exact") != b[k].get("formula_exact")]
    print("\nWhere 1.4 does not act: %d fits of %d place the same noise-tolerant seeds "
          "(none included); %d of them reach no time budget in either version, of which "
          "%d differ in formula, test error or formula_exact. The same recorded formula "
          "in %d fits of %d." % (len(same_seeds), len(common), len(det), len(differs),
                                 sum(a[k].get("expr") == b[k].get("expr") for k in common),
                                 len(common)))
    for k in differs[:20]:
        print("    %s: %s | %s" % (k, (a[k].get("expr") or "")[:60], (b[k].get("expr") or "")[:60]))

    # TP
    print("\nTP: | arm | law 1.3.0 | law 1.4.0 | useful | useful | median time | median time |")
    tchecks = []
    for arm in ("plain", "units"):
        xa, xb = tp_arm(ta, arm), tp_arm(tb, arm)
        la, lb = tp_law(ta, arm), tp_law(tb, arm)
        ma, mb = median(r["time"] for r in xa), median(r["time"] for r in xb)
        print("  | %s | %d | %d | %d | %d | %.1f s | %.1f s |" % (
            arm, la, lb, sum(r["useful"] for r in xa), sum(r["useful"] for r in xb), ma, mb))
        tchecks.append(("TP, %s arm: the law in no more than 5 fewer fits than 1.3.0 "
                        "(%d, %d)" % (arm, la, lb), lb >= la - 5))
        tchecks.append(("TP, %s arm: median time at most 1.5 times 1.3.0's (%.1f s, "
                        "%.1f s, ratio %.2f)" % (arm, ma, mb, mb / ma), mb <= 1.5 * ma))
    gu = tp_arm(tb, "units")
    tchecks.append(("TP, units arm: every model of 1.4.0 passes its gate of dimensions "
                    "(%d of %d)" % (sum(bool(r.get("units_gate")) for r in gu), len(gu)),
                    all(r.get("units_gate") for r in gu)))
    same_tp = sum(tb[k]["expr"] == tcamp[k]["expr"] for k in tb if k in tcamp)
    print("  the models of 1.4.0 are those of B in campaign N2b in %d fits of %d "
          "(expected: all)" % (same_tp, len(tb)))
    for k in sorted(tb):
        if k in tcamp and tb[k]["expr"] != tcamp[k]["expr"]:
            print("    differs: %s" % (k,))

    print("\nCriteria written before the run (PLAN_RELEASE_1.4.md, M2):")
    ab = lambda kk: (n_struct(a, kk), n_struct(b, kk))
    s1, s10 = ab("feyn_n1"), ab("feyn_n10")
    u1, u10 = ab("ufeyn_n1"), ab("ufeyn_n10")
    checks = [
        ("where 1.4 does not act (the same noise-tolerant seeds, no time budget "
         "reached), the formula, the test error and formula_exact are those of 1.3.0 "
         "(%d fits, %d differ)" % (len(det), len(differs)), not differs),
    ] + tchecks + [
        ("F41: not more than 3 fewer exact laws than 1.3.0 (%d -> %d)"
         % (ia["F41 exact"], ib["F41 exact"]), ib["F41 exact"] >= ia["F41 exact"] - 3),
        ("F41: no equation exact at three seeds or more falls to one or none (%s)"
         % (", ".join(fell(a, b, "feyn")) or "none"), not fell(a, b, "feyn")),
        ("F41N1: not more than 3 fewer structures than 1.3.0 (%d -> %d)" % s1,
         s1[1] >= s1[0] - 3),
        ("F41N10: not more than 3 fewer structures than 1.3.0 (%d -> %d)" % s10,
         s10[1] >= s10[0] - 3),
        ("F41N1 + F41N10: at least 15 structures more than 1.3.0, the gain of N2b "
         "(%d -> %d)" % (s1[0] + s10[0], s1[1] + s10[1]),
         s1[1] + s10[1] >= s1[0] + s10[0] + 15),
        ("R6 folds median R² not more than 0.005 below 1.3.0 (%s -> %s)"
         % (ia["R6 folds median R²"], ib["R6 folds median R²"]),
         ib["R6 folds median R²"] >= ia["R6 folds median R²"] - 0.005),
        ("R6 + R7raw collapses out of domain not more than 1.3.0 plus 2 (%d -> %d)"
         % (ia["R6 + R7raw out-of-domain collapses"],
            ib["R6 + R7raw out-of-domain collapses"]),
         ib["R6 + R7raw out-of-domain collapses"]
         <= ia["R6 + R7raw out-of-domain collapses"] + 2),
        ("U41: not more than 3 fewer exact laws than 1.3.0 (%d -> %d)"
         % (ua["U41 exact"], ub["U41 exact"]), ub["U41 exact"] >= ua["U41 exact"] - 3),
        ("U41: no equation exact at three seeds or more falls to one or none (%s)"
         % (", ".join(fell(a, b, "ufeyn")) or "none"), not fell(a, b, "ufeyn")),
        ("U41N1: not more than 3 fewer structures than 1.3.0 (%d -> %d)" % u1,
         u1[1] >= u1[0] - 3),
        ("U41N10: not more than 3 fewer structures than 1.3.0 (%d -> %d)" % u10,
         u10[1] >= u10[0] - 3),
        ("every model returned under units passes check_dimensions (%d of %d)"
         % (sum(r.get("units_ok") is True for r in ub_all), len(ub_all)),
         all(r.get("units_ok") is True for r in ub_all)),
    ]
    for name, ok in checks:
        print("  [%s] %s" % ("met" if ok else "NOT MET", name))
    print("ALL MET" if all(ok for _, ok in checks) else "A CRITERION IS NOT MET")

    print("\nReported, deciding nothing:")
    print("  status or structure changed, by suite (1.3.0 -> 1.4.0 counts of exact / "
          "structure):")
    by = {}
    for k in common:
        s = SUITE.get(k[0], k[0])
        d = by.setdefault(s, Counter())
        d["fits"] += 1
        d["status changed"] += a[k].get("status") != b[k].get("status")
        d["structure changed"] += bool(a[k].get("structure")) != bool(b[k].get("structure"))
        d["exact 1.3.0"] += a[k].get("status") == "EXACT"
        d["exact 1.4.0"] += b[k].get("status") == "EXACT"
        d["structure 1.3.0"] += bool(a[k].get("structure"))
        d["structure 1.4.0"] += bool(b[k].get("structure"))
        d["tolerant seeds 1.3.0"] += bool(a[k].get("tolerant_seed"))
        d["tolerant seeds 1.4.0"] += bool(b[k].get("tolerant_seed"))
        d["formula_exact False 1.3.0"] += a[k].get("formula_exact") is False
        d["formula_exact False 1.4.0"] += b[k].get("formula_exact") is False
        d["budget reached 1.3.0"] += bool(a[k].get("time_limit_reached"))
        d["budget reached 1.4.0"] += bool(b[k].get("time_limit_reached"))
    for s, d in sorted(by.items()):
        print("    %s: %s" % (s, dict(d)))
    print("  structures by equation where they differ (F41N1, F41N10, U41N1, U41N10):")
    pe = lambda D, kind: Counter(k[1] for k, r in D.items() if k[0] == kind
                                 and r.get("structure"))
    eqs = sorted({k[1] for k in a if k[0] == "feyn_n1"})
    for p in eqs:
        cells = ["%d -> %d" % (pe(a, kind)[p], pe(b, kind)[p])
                 for kind in ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10")]
        if any(c.split(" -> ")[0] != c.split(" -> ")[1] for c in cells):
            print("    %-10s %s" % (p, "   ".join(cells)))
    print("  TP, the law by experiment and arm, 1.3.0 -> 1.4.0:")
    for e in sorted({k[1] for k in ta}):
        print("    %-16s plain %d -> %d   units %d -> %d" % (
            e, tp_law(ta, "plain", e), tp_law(tb, "plain", e),
            tp_law(ta, "units", e), tp_law(tb, "units", e)))

    print("\nThe frozen test sets, published as measured, deciding nothing:")
    print("  TF78 exact %d -> %d; TS14 test exact %d -> %d; TR25 folds median R² %s -> %s; "
          "TF78 under units exact %d -> %d" % (
              ia["TF78 exact"], ib["TF78 exact"], ia["TS14 test exact"],
              ib["TS14 test exact"], ia["TR25 folds median R²"], ib["TR25 folds median R²"],
              ua["TF78 under units exact"], ub["TF78 under units exact"]))
    print("  TF78N, the structure: " + "; ".join(
        "%s %d -> %d of %d" % (SUITE[kind], n_struct(a, kind), n_struct(b, kind),
                               sum(1 for k in a if k[0] == kind))
        for kind in ("tf_n1", "tf_n10", "utf_n1", "utf_n10")))
    print("  TPT10: | arm | law 1.3.0 | law 1.4.0 | useful | useful |")
    for arm in ("plain", "units"):
        xa, xb = tp_arm(qa, arm), tp_arm(qb, arm)
        print("    | %s | %d | %d | %d | %d |" % (arm, tp_law(qa, arm), tp_law(qb, arm),
                                                 sum(r["useful"] for r in xa),
                                                 sum(r["useful"] for r in xb)))
    print("  TPT10, the law by experiment and arm, 1.3.0 -> 1.4.0:")
    for e in sorted({k[1] for k in qa}):
        print("    %-16s plain %d -> %d   units %d -> %d" % (
            e, tp_law(qa, "plain", e), tp_law(qb, "plain", e),
            tp_law(qa, "units", e), tp_law(qb, "units", e)))


if __name__ == "__main__":
    main(sys.argv[1:])
