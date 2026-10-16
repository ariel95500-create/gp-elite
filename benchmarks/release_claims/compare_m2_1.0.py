"""M2 of benchmarks/results_0.9/PLAN_RELEASE_1.0.md: campaign R of 1.0.0
paired with 0.9.0 (benchmarks/phase1_bench.py run-paired), the criteria the
plan wrote before it ran, and the targets of gate 2 read both ways (against
the starting values of gate 2, and against 0.9.0 on this machine).

  python benchmarks/release_claims/compare_m2_1.0.py <0.9.0.jsonl> <1.0.0.jsonl>
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare_m2 import load, indicators  # noqa: E402

ZERO_FAMILIES = ("trig", "racine", "rationnelle", "exponentielle", "logarithme")
GATE2 = {"F41 exact": 88, "TF78 exact": 145}   # 0.8.0, phase 1 (PLAN.md, gate 2)


def more(recs):
    rr = list(recs.values())
    feyn = [r for r in rr if r["kind"] == "feyn"]
    ind = {}
    ind["five families at zero in 0.8.0, exact (90 fits)"] = sum(
        r.get("status") == "EXACT" for r in feyn if r.get("family") in ZERO_FAMILIES)
    ind["fits of those families"] = sum(r.get("family") in ZERO_FAMILIES for r in feyn)
    by_problem = {}
    for r in feyn:
        by_problem.setdefault(r["problem"], []).append(r.get("status") == "EXACT")
    ind["F41 equations never exact"] = sorted(p for p, v in by_problem.items() if not any(v))
    ind["F41 exact per equation"] = {p: sum(v) for p, v in sorted(by_problem.items())}
    worst = min(r["r2"] for r in rr
                if r["kind"] in ("real", "realraw") and r["split"] == "ood")
    ind["R6 + R7raw worst out-of-domain R²"] = float("%.4g" % worst)
    return ind


def main(a_path, b_path):
    a, b = load(a_path), load(b_path)
    ia, ib = indicators(a), indicators(b)
    ma, mb = more(a), more(b)
    print("| indicator | 0.9.0 | 1.0.0 |\n|---|---|---|")
    for k in ia:
        print("| %s | %s | %s |" % (k, ia[k], ib[k]))
    for k in ("five families at zero in 0.8.0, exact (90 fits)",
              "fits of those families", "R6 + R7raw worst out-of-domain R²"):
        print("| %s | %s | %s |" % (k, ma[k], mb[k]))
    print("\nF41 equations never exact in 5 seeds: 0.9.0 %d, 1.0.0 %d"
          % (len(ma["F41 equations never exact"]), len(mb["F41 equations never exact"])))
    print("  1.0.0: " + ", ".join(mb["F41 equations never exact"]))
    gained = [p for p in mb["F41 exact per equation"]
              if mb["F41 exact per equation"][p] > ma["F41 exact per equation"].get(p, 0)]
    lost = [p for p in mb["F41 exact per equation"]
            if mb["F41 exact per equation"][p] < ma["F41 exact per equation"].get(p, 0)]
    print("  equations with more exact fits in 1.0.0: %d; with fewer: %d %s"
          % (len(gained), len(lost), lost))
    print("  exact fits per equation, 1.0.0 (0.9.0): " + ", ".join(
        "%s %d (%d)" % (p, n, ma["F41 exact per equation"].get(p, 0))
        for p, n in mb["F41 exact per equation"].items()))

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

    print("\nCriteria written before the run (PLAN_RELEASE_1.0.md, M2):")
    checks = [
        ("F41: not fewer exact laws than 0.9.0", ib["F41 exact"] >= ia["F41 exact"]),
        ("F41N1: not fewer structures than 0.9.0",
         ib["F41N1 structure retrieved"] >= ia["F41N1 structure retrieved"]),
        ("F41N10: not fewer structures than 0.9.0",
         ib["F41N10 structure retrieved"] >= ia["F41N10 structure retrieved"]),
        ("R6 folds median R² not more than 0.005 below 0.9.0",
         ib["R6 folds median R²"] >= ia["R6 folds median R²"] - 0.005),
        ("R6 + R7raw collapses out of domain not more than 0.9.0 plus 2",
         ib["R6 + R7raw out-of-domain collapses"]
         <= ia["R6 + R7raw out-of-domain collapses"] + 2),
    ]
    for name, ok in checks:
        print("  [%s] %s" % ("met" if ok else "NOT MET", name))
    print("ALL MET" if all(ok for _, ok in checks) else "A CRITERION IS NOT MET")

    print("\nTargets of gate 2 (PLAN.md), on the wheel of 1.0.0:")
    g_gate = ib["F41 exact"] / GATE2["F41 exact"] - 1
    g_pair = ib["F41 exact"] / ia["F41 exact"] - 1
    tf_gate = GATE2["TF78 exact"] * (1 + g_gate / 2)
    tf_pair = ia["TF78 exact"] * (1 + g_pair / 2)
    targets = [
        ("F41 exact laws at least 110", ib["F41 exact"], ib["F41 exact"] >= 110),
        ("five families at zero: at least 20 of 90",
         mb["five families at zero in 0.8.0, exact (90 fits)"],
         mb["five families at zero in 0.8.0, exact (90 fits)"] >= 20),
        ("TF78 at least half the relative gain on F41, from gate 2 "
         "(F41 88 -> %d, %+.0f %%: TF78 at least %.1f)" % (ib["F41 exact"], 100 * g_gate, tf_gate),
         ib["TF78 exact"], ib["TF78 exact"] >= tf_gate),
        ("TF78 the same, against 0.9.0 here (F41 %d -> %d, %+.0f %%: TF78 at least %.1f)"
         % (ia["F41 exact"], ib["F41 exact"], 100 * g_pair, tf_pair),
         ib["TF78 exact"], ib["TF78 exact"] >= tf_pair),
        ("F41N1 structure at least 80", ib["F41N1 structure retrieved"],
         ib["F41N1 structure retrieved"] >= 80),
        ("F41N10 structure at least 77", ib["F41N10 structure retrieved"],
         ib["F41N10 structure retrieved"] >= 77),
        ("R6 + R7raw collapses out of domain no more than 10",
         ib["R6 + R7raw out-of-domain collapses"],
         ib["R6 + R7raw out-of-domain collapses"] <= 10),
        ("R6 + R7raw worst out-of-domain R² no deeper than -233",
         mb["R6 + R7raw worst out-of-domain R²"],
         mb["R6 + R7raw worst out-of-domain R²"] >= -233),
        ("R6 folds median R² at least 0.804", ib["R6 folds median R²"],
         ib["R6 folds median R²"] >= 0.804),
        ("TR25 folds median R² at least 0.761 (0.9.0 here: %s)" % ia["TR25 folds median R²"],
         ib["TR25 folds median R²"], ib["TR25 folds median R²"] >= 0.761),
        ("TR25 collapses out of domain fewer than 37 (0.9.0 here: %d)"
         % ia["TR25 out-of-domain collapses"],
         ib["TR25 out-of-domain collapses"], ib["TR25 out-of-domain collapses"] < 37),
    ]
    for name, val, ok in targets:
        print("  [%s] %s: %s" % ("met" if ok else "NOT MET", name, val))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
