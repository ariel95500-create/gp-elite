"""M2 of benchmarks/results_0.9/PLAN_RELEASE_0.9.md: campaign R of 0.9.0
paired with 0.8.0 (benchmarks/phase1_bench.py run-paired), and the criteria
the plan wrote before it ran.

  python benchmarks/release_claims/compare_m2.py <0.8.0.jsonl> <0.9.0.jsonl>
"""
import json
import sys

import numpy as np


def load(path):
    out = {}
    for line in open(path):
        if line.strip():
            r = json.loads(line)
            out[(r["kind"], r["problem"], r["split"], r["seed"])] = r
    return out


def indicators(recs):
    rr = list(recs.values())

    def sel(kind, pred=lambda s: True):
        return [r for r in rr if r["kind"] == kind and pred(r["split"])]

    folds = lambda s: s.startswith("fold")
    ood = lambda s: s == "ood"
    ind = {}
    ind["F41 exact"] = sum(r.get("status") == "EXACT" for r in sel("feyn"))
    for k, name in (("feyn_n1", "F41N1"), ("feyn_n10", "F41N10")):
        ind[name + " structure retrieved"] = sum(bool(r.get("structure")) for r in sel(k))
    ind["TF78 exact"] = sum(r.get("status") == "EXACT" for r in sel("tf"))
    ind["TS14 test exact"] = sum(r.get("status") == "EXACT"
                                 for r in sel("ts", lambda s: s == "test"))
    for k, name in (("real", "R6"), ("realraw", "R7raw"), ("tr", "TR25"),
                    ("trraw", "TR25raw")):
        r2 = [r["r2"] for r in sel(k, folds)]
        ind[name + " folds median R²"] = round(float(np.median(r2)), 4)
        o = [r["r2"] for r in sel(k, ood)]
        ind[name + " out-of-domain collapses"] = int(sum(x < 0 for x in o))
        ind[name + " worst out-of-domain R²"] = float("%.4g" % min(o))
    ind["R6 + R7raw out-of-domain collapses"] = (
        ind["R6 out-of-domain collapses"] + ind["R7raw out-of-domain collapses"])
    ind["formula_exact False, R6 + R7raw folds and test"] = sum(
        r.get("formula_exact") is False for r in rr
        if r["kind"] in ("real", "realraw") and not ood(r["split"]))
    ind["crashes"] = sum(r.get("status") == "CRASH" for r in rr)
    ind["fits"] = len(rr)
    return ind


def main(a_path, b_path):
    a, b = load(a_path), load(b_path)
    ia, ib = indicators(a), indicators(b)
    print("| indicator | 0.8.0 | 0.9.0 |\n|---|---|---|")
    for k in ia:
        print("| %s | %s | %s |" % (k, ia[k], ib[k]))
    common = sorted(set(a) & set(b))
    same = [k for k in common if a[k].get("expr") == b[k].get("expr")]
    print("\nPaired: %d jobs in both files, %d with the same returned "
          "expression (%d differ)." % (len(common), len(same),
                                       len(common) - len(same)))
    by_kind = {}
    for k in common:
        d = by_kind.setdefault(k[0], [0, 0])
        d[0] += 1
        d[1] += a[k].get("expr") == b[k].get("expr")
    print("Same expression by suite: " + ", ".join(
        "%s %d/%d" % (k, v[1], v[0]) for k, v in sorted(by_kind.items())))
    print("\nCriteria written before the run (PLAN_RELEASE_0.9.md, M2):")
    checks = [
        ("F41 not more than 6 exact laws below 0.8.0",
         ib["F41 exact"] >= ia["F41 exact"] - 6),
        ("R6 folds median R² not more than 0.005 below",
         ib["R6 folds median R²"] >= ia["R6 folds median R²"] - 0.005),
        ("TR25 folds median R² not more than 0.005 below",
         ib["TR25 folds median R²"] >= ia["TR25 folds median R²"] - 0.005),
        ("R6 + R7raw collapses out of domain not more than 0.8.0 plus 2",
         ib["R6 + R7raw out-of-domain collapses"]
         <= ia["R6 + R7raw out-of-domain collapses"] + 2),
    ]
    for name, ok in checks:
        print("  [%s] %s" % ("met" if ok else "NOT MET", name))
    print("ALL MET" if all(ok for _, ok in checks) else "A CRITERION IS NOT MET")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
