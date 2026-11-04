"""M2 of benchmarks/results_1.2/PLAN_RELEASE_1.2.md: campaign R of 1.2.0
paired with 1.1.0 (benchmarks/phase1_bench.py run-paired), and the criteria
the plan wrote before it ran.

  python benchmarks/release_claims/compare_m2_1.2.py <1.1.0.jsonl> <1.2.0.jsonl>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare_m2 import load, indicators  # noqa: E402

UNIT_KINDS = ("ufeyn", "ufeyn_n1", "ufeyn_n10", "utf")
FROZEN = ("tf", "ts", "tr", "trraw", "utf")
SUITE = {"feyn": "F41", "feyn_n1": "F41N1", "feyn_n10": "F41N10", "real": "R6",
         "realraw": "R7raw", "tf": "TF78", "ts": "TS14", "tr": "TR25",
         "trraw": "TR25raw", "ufeyn": "U41", "ufeyn_n1": "U41N1",
         "ufeyn_n10": "U41N10", "utf": "TF78 under units"}


def units(recs):
    rr = list(recs.values())

    def sel(kind):
        return [r for r in rr if r["kind"] == kind]

    ind = {}
    ind["U41 exact"] = sum(r.get("status") == "EXACT" for r in sel("ufeyn"))
    for k, name in (("ufeyn_n1", "U41N1"), ("ufeyn_n10", "U41N10")):
        ind[name + " structure retrieved"] = sum(bool(r.get("structure")) for r in sel(k))
    ind["TF78 under units exact"] = sum(r.get("status") == "EXACT" for r in sel("utf"))
    u = [r for r in rr if r["kind"] in UNIT_KINDS]
    ind["fits under units"] = len(u)
    ind["fits under units passing the audit"] = sum(r.get("units_ok") is True for r in u)
    ind["crashes under units"] = sum(r.get("status") == "CRASH" for r in u)
    t = sorted(r["time"] for r in u if "time" in r)
    ind["under units, median time of a fit (s)"] = t[len(t) // 2] if t else None
    ind["under units, longest fit (s)"] = t[-1] if t else None
    return ind


def iii_19_51(recs):
    return sorted((r for r in recs.values() if r["kind"] in ("ufeyn", "ufeyn_n1",
                                                             "ufeyn_n10")
                   and r["problem"] == "III.19.51"),
                  key=lambda r: (r["kind"], r["seed"]))


def main(a_path, b_path):
    a, b = load(a_path), load(b_path)
    ia, ib = indicators(a), indicators(b)
    ua, ub = units(a), units(b)
    print("| indicator | 1.1.0 | 1.2.0 |\n|---|---|---|")
    for k in ia:
        print("| %s | %s | %s |" % (k, ia[k], ib[k]))
    for k in ua:
        print("| %s | %s | %s |" % (k, ua[k], ub[k]))

    common = sorted(set(a) & set(b))
    same = [k for k in common if a[k].get("expr") == b[k].get("expr")]
    print("\nPaired: %d jobs in both files, %d with the same returned "
          "expression (%d differ)." % (len(common), len(same), len(common) - len(same)))
    flags = sorted({(r.get("engine_version"), r.get("engine_file")) for r in a.values()}
                   | {(r.get("engine_version"), r.get("engine_file")) for r in b.values()})
    print("Engines: %s" % flags)

    # X1: the formula of 1.2.0 with X1 switched off, against 1.1.0. Decides
    # on the suites outside the frozen test set; the frozen ones are reported.
    def x1_checks(keys):
        bb = [k for k in keys if b[k].get("status") != "CRASH"]
        missing = [k for k in bb if "expr_11" not in b[k] or not b[k].get("x1_again")]
        exact_differs = [k for k in bb if "expr_11" in b[k]
                         and b[k]["formula_exact_11"] != b[k].get("formula_exact")]
        det = [k for k in bb if not a[k].get("time_limit_reached")
               and not b[k].get("time_limit_reached")
               and not (k[0] in UNIT_KINDS and k[1] == "III.19.51")]
        model_differs = [k for k in det if b[k].get("expr_11") != a[k].get("expr")
                         or a[k].get("err") != b[k].get("err")
                         or a[k].get("formula_exact") != b[k].get("formula_exact")]
        return bb, missing, exact_differs, det, model_differs

    frozen = [k for k in common if k[0] in FROZEN]
    deciding = [k for k in common if k[0] not in FROZEN]
    bb, missing, exact_differs, det, model_differs = x1_checks(deciding)
    print("\nX1 on the %d fits of 1.2.0 outside the frozen test set that did not "
          "crash:" % len(bb))
    print("  formula without X1 computed and X1 giving back the expression: %d "
          "(missing or not given back: %d)" % (len(bb) - len(missing), len(missing)))
    for k in missing[:10]:
        print("    missing: %s" % (k,))
    print("  formula_exact differs from formula_exact_11: %d" % len(exact_differs))
    for k in exact_differs[:10]:
        print("    %s" % (k,))
    print("  neither version at its time budget (III.19.51 under units aside): %d; "
          "among them the formula without X1, the test error or formula_exact "
          "differs from 1.1.0: %d" % (len(det), len(model_differs)))
    for k in model_differs[:20]:
        print("    %s: err %r vs %r, formula_exact %r vs %r, %s | %s" % (
            k, a[k].get("err"), b[k].get("err"), a[k].get("formula_exact"),
            b[k].get("formula_exact"), a[k].get("expr", "")[:50],
            b[k].get("expr_11", "")[:50]))
    fb, fm, fe, fd, fmd = x1_checks(frozen)
    print("  beside, the frozen test set (%d fits): missing %d, formula_exact "
          "differs %d, neither at its budget %d of which differing from 1.1.0 %d"
          % (len(fb), len(fm), len(fe), len(fd), len(fmd)))
    allb = [k for k in common if b[k].get("status") != "CRASH"]
    same11 = {k for k in allb if b[k].get("expr_11") == a[k].get("expr")}
    other = [k for k in allb if "expr_11" in b[k] and k not in same11]
    rewritten = [k for k in allb if "expr_11" in b[k] and b[k]["expr_11"] != b[k].get("expr")]
    print("  every suite: formula without X1 differs from 1.1.0: %d, by suite:"
          % len(other))
    by = {}
    for k in other:
        d = by.setdefault(SUITE.get(k[0], k[0]), [0, 0, 0])
        d[0] += 1
        d[1] += bool(a[k].get("time_limit_reached") and b[k].get("time_limit_reached"))
        d[2] += a[k].get("status") != b[k].get("status")
    for s, (n, both, st) in sorted(by.items()):
        print("    %s: %d (both at the time budget: %d; status changed: %d)" % (s, n, both, st))
    print("  X1 rewrites the formula: %d, by suite: %s" % (len(rewritten), ", ".join(
        "%s %d" % (s, n) for s, n in sorted(
            {SUITE.get(k[0], k[0]): sum(1 for j in rewritten if j[0] == k[0])
             for k in rewritten}.items()))))
    for k in rewritten[:12]:
        print("    %s: %s  ->  %s" % (k, b[k]["expr_11"][:70], b[k]["expr"][:70]))

    print("\nIII.19.51 under units:")
    t5 = iii_19_51(b)
    for r in t5:
        ra = a.get((r["kind"], r["problem"], r["split"], r["seed"]), {})
        print("  %s seed %s: %s s, %s, units_ok %s (1.1.0: %s s, %s)" % (
            r["kind"], r["seed"], r.get("time"), r.get("status", r.get("structure")),
            r.get("units_ok"), ra.get("time"), ra.get("status", ra.get("structure"))))

    print("\nCriteria written before the run (PLAN_RELEASE_1.2.md, M2):")
    checks = [
        ("F41: not more than 3 fewer exact laws than 1.1.0",
         ib["F41 exact"] >= ia["F41 exact"] - 3),
        ("F41N1: not more than 3 fewer structures than 1.1.0",
         ib["F41N1 structure retrieved"] >= ia["F41N1 structure retrieved"] - 3),
        ("F41N10: not more than 3 fewer structures than 1.1.0",
         ib["F41N10 structure retrieved"] >= ia["F41N10 structure retrieved"] - 3),
        ("R6 folds median R² not more than 0.005 below 1.1.0",
         ib["R6 folds median R²"] >= ia["R6 folds median R²"] - 0.005),
        ("R6 + R7raw collapses out of domain not more than 1.1.0 plus 2",
         ib["R6 + R7raw out-of-domain collapses"]
         <= ia["R6 + R7raw out-of-domain collapses"] + 2),
        ("U41: not more than 3 fewer exact laws than 1.1.0 (%d -> %d)"
         % (ua["U41 exact"], ub["U41 exact"]),
         ub["U41 exact"] >= ua["U41 exact"] - 3),
        ("U41N1: not more than 3 fewer structures than 1.1.0",
         ub["U41N1 structure retrieved"] >= ua["U41N1 structure retrieved"] - 3),
        ("U41N10: not more than 3 fewer structures than 1.1.0",
         ub["U41N10 structure retrieved"] >= ua["U41N10 structure retrieved"] - 3),
        ("every model returned under units passes check_dimensions (%d of %d)"
         % (ub["fits under units passing the audit"], ub["fits under units"]),
         ub["fits under units passing the audit"] == ub["fits under units"]),
        ("III.19.51 under units: 15 fits, each within 60 s (%d fits, longest %s s)"
         % (len(t5), max((r.get("time", 1e9) for r in t5), default=None)),
         len(t5) == 15 and all(r.get("time", 1e9) <= 60 for r in t5)),
        ("X1: the formula without X1 is computed on every fit (%d missing)"
         % len(missing), not missing),
        ("X1: formula_exact is that of the formula without X1 on every fit",
         not exact_differs),
        ("X1: where neither version reached its time budget, the formula without "
         "X1, the test error and formula_exact are those of 1.1.0 (%d fits)"
         % len(det), not model_differs),
    ]
    for name, ok in checks:
        print("  [%s] %s" % ("met" if ok else "NOT MET", name))
    print("ALL MET" if all(ok for _, ok in checks) else "A CRITERION IS NOT MET")

    print("\nFrozen test set, published as measured, deciding nothing: "
          "TF78 exact %d -> %d, TS14 test exact %d -> %d, TR25 folds median R² "
          "%s -> %s, TF78 under units exact %d -> %d."
          % (ia["TF78 exact"], ib["TF78 exact"], ia["TS14 test exact"],
             ib["TS14 test exact"], ia["TR25 folds median R²"],
             ib["TR25 folds median R²"], ua["TF78 under units exact"],
             ub["TF78 under units exact"]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
