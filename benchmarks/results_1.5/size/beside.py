"""Beside the reading of the size study (Part B of ../PLAN.md), deciding
nothing. Written after the campaign, from its records alone.

  - each equation: its exact fits (of five seeds) in each cell, for the
    equations that are not exact in all five seeds everywhere;
  - the fits that ran to their budget (the time limit or the count of
    generations) in each cell, and the generations they reached;
  - the formulas that use an added variable, by status;
  - the fits past their budget, and how far past.

    python beside.py campaign.jsonl
"""
import collections
import json
import statistics
import sys

CELLS = ["r100", "r1000", "r10000", "r100000", "r100000_10T",
         "k5", "k10", "k20", "k20_10T"]


def main(path):
    recs = [json.loads(l) for l in open(path) if l.strip()]
    by = collections.defaultdict(list)
    for r in recs:
        by[r["cell"]].append(r)

    print("## Each equation: exact fits of five seeds, by cell")
    print("(only the equations not exact in all five seeds in every cell)")
    eqs = sorted({(r["eq"], r["problem"]) for r in recs})
    print("%-4s %-11s %s" % ("eq", "problem", " ".join("%11s" % c for c in CELLS)))
    for eq, prob in eqs:
        row = [sum(1 for r in by[c] if r["eq"] == eq and r["status"] == "EXACT")
               for c in CELLS]
        if any(x != 5 for x in row):
            print("%-4d %-11s %s" % (eq, prob, " ".join("%11d" % x for x in row)))
    print()

    print("## The fits that ran to their budget, and the generations they reached")
    print("%-12s %6s %8s %9s %9s %9s" % ("cell", "fits", "to limit", "med.gen", "min.gen",
                                       "max.gen"))
    for c in CELLS:
        rs = by[c]
        cap = 1000 * rs[0]["budget_factor"]
        full = [r for r in rs if r.get("time_limit_reached") or r["generations"] >= cap]
        g = [r["generations"] for r in full]
        print("%-12s %6d %8d %9s %9s %9s" % (
            c, len(rs), len(full),
            "%.0f" % statistics.median(g) if g else "-",
            min(g) if g else "-", max(g) if g else "-"))
    print()

    print("## The formulas that use an added variable, by status")
    for c in CELLS:
        rs = [r for r in by[c] if r.get("uses_added")]
        if rs:
            st = collections.Counter(r["status"] for r in rs)
            print("%-12s %3d: %s" % (c, len(rs), ", ".join(
                "%s %d" % (k, st[k]) for k in ("EXACT", "NEAR", "MISS") if st[k])))
    print()

    print("## The fits past their budget (more than 10 % over the time limit)")
    for c in CELLS:
        rs = [r for r in by[c] if r["time"] > 1.1 * r["time_limit"]]
        if rs:
            over = sorted(r["time"] - r["time_limit"] for r in rs)
            print("%-12s %3d, over by %.1f s (median), %.1f s (largest)" % (
                c, len(rs), statistics.median(over), over[-1]))
    print()

    print("## Time to the first generation (s): median and largest")
    for c in CELLS:
        t = sorted(r["to_first_gen"] for r in by[c] if r.get("to_first_gen") is not None)
        print("%-12s %6.2f %7.2f" % (c, statistics.median(t), t[-1]))


if __name__ == "__main__":
    main(sys.argv[1])
