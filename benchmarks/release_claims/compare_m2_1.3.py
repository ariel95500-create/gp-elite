"""M2 of benchmarks/results_1.3/PLAN_RELEASE_1.3.md: campaign R of 1.3.0
paired with 1.2.0 (benchmarks/phase1_bench.py run-paired), and the criteria
the plan wrote before it ran.

  python benchmarks/release_claims/compare_m2_1.3.py <1.2.0.jsonl> <1.3.0.jsonl>
"""
import io
import os
import sys
from collections import Counter
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from compare_m2 import load, indicators  # noqa: E402
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location(
    "compare_m2_1_2", os.path.join(HERE, "compare_m2_1.2.py"))
_m12 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_m12)
units, SUITE, UNIT_KINDS, FROZEN = _m12.units, _m12.SUITE, _m12.UNIT_KINDS, _m12.FROZEN

ARCSIN = ("I.26.2", "I.30.5")


def pools():
    """The operator pool of each problem, as the bench gives it."""
    with redirect_stdout(io.StringIO()):
        import feynman_bench as F
        import test_set as T
    out = {p[0]: p[5] for p in F.PROBS}
    m = T.manifest()["datasets"]
    for g in ("TF78", "TS14"):
        for n in T.names(g):
            out[n] = m[n]["pool"]
    return out


def pool_of(k, P):
    if k[0] in ("real", "realraw", "tr", "trraw"):
        return "physical"
    return P.get(k[1], "?")


def main(a_path, b_path):
    a, b = load(a_path), load(b_path)
    P = pools()
    ia, ib = indicators(a), indicators(b)
    ua, ub = units(a), units(b)
    print("| indicator | 1.2.0 | 1.3.0 |\n|---|---|---|")
    for k in ia:
        print("| %s | %s | %s |" % (k, ia[k], ib[k]))
    for k in ua:
        print("| %s | %s | %s |" % (k, ua[k], ub[k]))

    common = sorted(set(a) & set(b))
    print("\nPaired: %d jobs in A, %d in B, %d in both; the same jobs: %s"
          % (len(a), len(b), len(common), set(a) == set(b)))
    flags = sorted({(r.get("engine_version"), r.get("engine_file")) for r in a.values()}
                   | {(r.get("engine_version"), r.get("engine_file")) for r in b.values()})
    print("Engines: %s" % flags)
    print("Pools of the jobs: %s" % dict(Counter(pool_of(k, P) for k in common)))

    # the pool physical: the same model at equal work
    phys = [k for k in common if pool_of(k, P) == "physical"]
    det = [k for k in phys if not a[k].get("time_limit_reached")
           and not b[k].get("time_limit_reached")
           and a[k].get("status") != "CRASH" and b[k].get("status") != "CRASH"]
    differs = [k for k in det if a[k].get("expr") != b[k].get("expr")
               or a[k].get("err") != b[k].get("err")
               or a[k].get("formula_exact") != b[k].get("formula_exact")]
    same_expr = sum(a[k].get("expr") == b[k].get("expr") for k in phys)
    print("\nThe pool physical: %d fits; neither version at its time budget: %d, of "
          "which differing in formula, test error or formula_exact: %d; the same "
          "formula in %d of the %d" % (len(phys), len(det), len(differs), same_expr,
                                       len(phys)))
    for k in differs[:20]:
        print("    %s: %s | %s" % (k, a[k].get("expr", "")[:60], b[k].get("expr", "")[:60]))
    phys_status = [k for k in phys if a[k].get("status") != b[k].get("status")
                   or bool(a[k].get("structure")) != bool(b[k].get("structure"))]
    print("  status or structure changed in the pool physical: %d" % len(phys_status))
    for k in phys_status:
        print("    %s: %s -> %s (budget reached %s, %s)" % (
            k, a[k].get("status", a[k].get("structure")), b[k].get("status", b[k].get("structure")),
            a[k].get("time_limit_reached"), b[k].get("time_limit_reached")))

    # the pool trig (and full): what changes
    trig = [k for k in common if pool_of(k, P) != "physical"]
    print("\nThe pools with the arcsine: %d fits (%s)"
          % (len(trig), dict(Counter(pool_of(k, P) for k in trig))))
    by = {}
    for k in trig:
        s = SUITE.get(k[0], k[0])
        d = by.setdefault(s, Counter())
        d["fits"] += 1
        d["status changed"] += a[k].get("status") != b[k].get("status")
        d["exact A"] += a[k].get("status") == "EXACT"
        d["exact B"] += b[k].get("status") == "EXACT"
        d["arcsine in B"] += "arcsin" in (b[k].get("expr") or "")
    for s, d in sorted(by.items()):
        print("  %s: %s" % (s, dict(d)))

    arc = [k for k in common if k[0] == "feyn" and k[1] in ARCSIN]
    arc_ok = [k for k in arc if b[k].get("status") == "EXACT"
              and "arcsin" in (b[k].get("expr") or "")]
    print("\nThe arcsine laws of F41 in 1.3.0:")
    for k in sorted(arc):
        print("  %s seed %d: %s, %s" % (k[1], k[3], b[k].get("status"),
                                       (b[k].get("expr") or "")[:90]))

    print("\nformula_exact False, by suite: | suite | 1.2.0 | 1.3.0 |")
    fe = {}
    for k in common:
        s = SUITE.get(k[0], k[0])
        d = fe.setdefault(s, [0, 0])
        d[0] += a[k].get("formula_exact") is False
        d[1] += b[k].get("formula_exact") is False
    for s, (x, y) in sorted(fe.items()):
        print("  | %s | %d | %d |" % (s, x, y))

    print("\nCriteria written before the run (PLAN_RELEASE_1.3.md, M2):")
    checks = [
        ("the pool physical: where neither version reached its time budget, the "
         "formula, the test error and formula_exact are those of 1.2.0 (%d fits, "
         "%d differ)" % (len(det), len(differs)), not differs),
        ("F41: not more than 3 fewer exact laws than 1.2.0 (%d -> %d)"
         % (ia["F41 exact"], ib["F41 exact"]), ib["F41 exact"] >= ia["F41 exact"] - 3),
        ("F41N1: not more than 3 fewer structures than 1.2.0",
         ib["F41N1 structure retrieved"] >= ia["F41N1 structure retrieved"] - 3),
        ("F41N10: not more than 3 fewer structures than 1.2.0",
         ib["F41N10 structure retrieved"] >= ia["F41N10 structure retrieved"] - 3),
        ("R6 folds median R² not more than 0.005 below 1.2.0",
         ib["R6 folds median R²"] >= ia["R6 folds median R²"] - 0.005),
        ("R6 + R7raw collapses out of domain not more than 1.2.0 plus 2",
         ib["R6 + R7raw out-of-domain collapses"]
         <= ia["R6 + R7raw out-of-domain collapses"] + 2),
        ("the arcsine laws of F41 exact with the arcsine in at least 5 of 10 (%d)"
         % len(arc_ok), len(arc_ok) >= 5),
        ("U41: not more than 3 fewer exact laws than 1.2.0 (%d -> %d)"
         % (ua["U41 exact"], ub["U41 exact"]), ub["U41 exact"] >= ua["U41 exact"] - 3),
        ("U41N1: not more than 3 fewer structures than 1.2.0",
         ub["U41N1 structure retrieved"] >= ua["U41N1 structure retrieved"] - 3),
        ("U41N10: not more than 3 fewer structures than 1.2.0",
         ub["U41N10 structure retrieved"] >= ua["U41N10 structure retrieved"] - 3),
        ("every model returned under units passes check_dimensions (%d of %d)"
         % (ub["fits under units passing the audit"], ub["fits under units"]),
         ub["fits under units passing the audit"] == ub["fits under units"]),
    ]
    for name, ok in checks:
        print("  [%s] %s" % ("met" if ok else "NOT MET", name))
    print("ALL MET" if all(ok for _, ok in checks) else "A CRITERION IS NOT MET")

    tf_trig = [k for k in common if k[0] == "tf" and pool_of(k, P) != "physical"]
    print("\nFrozen test set, published as measured, deciding nothing: "
          "TF78 exact %d -> %d (its 17 equations of the pool trig: %d -> %d), "
          "TS14 test exact %d -> %d, TR25 folds median R² %s -> %s, TF78 under "
          "units exact %d -> %d."
          % (ia["TF78 exact"], ib["TF78 exact"],
             sum(a[k].get("status") == "EXACT" for k in tf_trig),
             sum(b[k].get("status") == "EXACT" for k in tf_trig),
             ia["TS14 test exact"], ib["TS14 test exact"], ia["TR25 folds median R²"],
             ib["TR25 folds median R²"], ua["TF78 under units exact"],
             ub["TF78 under units exact"]))
    for k in sorted(k for k in common if k[1] == "feynman_test_10"):
        print("  %s feynman_test_10 seed %d: %s -> %s, %s" % (
            k[0], k[3], a[k].get("status"), b[k].get("status"),
            (b[k].get("expr") or "")[:70]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
