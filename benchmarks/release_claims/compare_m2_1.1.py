"""M2 of benchmarks/results_1.1/PLAN_RELEASE_1.1.md: campaign R of 1.1.0
paired with 1.0.0 (benchmarks/phase1_bench.py run-paired), and the criteria
the plan wrote before it ran.

  python benchmarks/release_claims/compare_m2_1.1.py <1.0.0.jsonl> <1.1.0.jsonl>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare_m2 import load, indicators  # noqa: E402

UNIT_KINDS = ("ufeyn", "ufeyn_n1", "ufeyn_n10", "utf")


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
    return ind


def main(a_path, b_path):
    a, b = load(a_path), load(b_path)
    ia, ib = indicators(a), indicators(b)
    ua, ub = units(a), units(b)
    print("| indicator | 1.0.0 | 1.1.0 |\n|---|---|---|")
    for k in ia:
        print("| %s | %s | %s |" % (k, ia[k], ib[k]))
    for k in ua:
        print("| %s | %s | %s |" % (k, ua[k], ub[k]))

    common = sorted(set(a) & set(b))
    same = [k for k in common if a[k].get("expr") == b[k].get("expr")]
    print("\nPaired: %d jobs in both files, %d with the same returned "
          "expression (%d differ)." % (len(common), len(same), len(common) - len(same)))
    by_kind = {}
    for k in common:
        d = by_kind.setdefault(k[0], [0, 0])
        d[0] += 1
        d[1] += a[k].get("expr") == b[k].get("expr")
    print("Same expression by suite: " + ", ".join(
        "%s %d/%d" % (k, v[1], v[0]) for k, v in sorted(by_kind.items())))
    flags = sorted({(r.get("engine_version"), r.get("seeds_under_units"))
                    for r in b.values()})
    print("1.1.0 engine and seeds_under_units: %s" % flags)

    print("\nCriteria written before the run (PLAN_RELEASE_1.1.md, M2):")
    checks = [
        ("F41: not more than 3 fewer exact laws than 1.0.0",
         ib["F41 exact"] >= ia["F41 exact"] - 3),
        ("F41N1: not more than 3 fewer structures than 1.0.0",
         ib["F41N1 structure retrieved"] >= ia["F41N1 structure retrieved"] - 3),
        ("F41N10: not more than 3 fewer structures than 1.0.0",
         ib["F41N10 structure retrieved"] >= ia["F41N10 structure retrieved"] - 3),
        ("R6 folds median R² not more than 0.005 below 1.0.0",
         ib["R6 folds median R²"] >= ia["R6 folds median R²"] - 0.005),
        ("R6 + R7raw collapses out of domain not more than 1.0.0 plus 2",
         ib["R6 + R7raw out-of-domain collapses"]
         <= ia["R6 + R7raw out-of-domain collapses"] + 2),
        ("U41: at least 10 more exact laws than 1.0.0 (%d -> %d)"
         % (ua["U41 exact"], ub["U41 exact"]),
         ub["U41 exact"] >= ua["U41 exact"] + 10),
        ("every model returned under units passes check_dimensions (%d of %d)"
         % (ub["fits under units passing the audit"], ub["fits under units"]),
         ub["fits under units passing the audit"] == ub["fits under units"]),
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
