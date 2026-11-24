"""M5 review 1: A3 recomputed from the raw timing records, for the split
(split/a3_timing.jsonl) and for M1 on the wheel (release/M1_A3_timing.jsonl).

Reads JSON lines only. Does not import gp_elite and runs no fit.

    python3 -I a3_recompute.py <repo root>
"""
import json
import os
import statistics
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."


def show(path):
    with open(os.path.join(ROOT, path)) as fh:
        lines = [l for l in fh if l.strip()]
    recs = [json.loads(l) for l in lines]
    print("==", path)
    print("records", len(recs), "distinct i", len({r["i"] for r in recs}),
          "i from", min(r["i"] for r in recs), "to", max(r["i"] for r in recs))
    print("distinct (problem, seed)", len({(r["problem"], r["seed"]) for r in recs}),
          "problems", len({r["problem"] for r in recs}), "seeds", sorted({r["seed"] for r in recs}))
    ta = sum(r["A"] for r in recs)
    tb = sum(r["B"] for r in recs)
    print("total A %.2f s, total B %.2f s, ratio B/A %.5f, (B-A)/A %.3f %%" % (ta, tb, tb / ta, 100 * (tb / ta - 1)))
    same = sum(1 for r in recs if r["A_expr"] == r["B_expr"])
    print("same expr in", same)
    print("longest expr", max(len(r["A_expr"]) for r in recs))
    # the order of the keys is the order the two engines ran in
    order_ok = 0
    for r in recs:
        first = [k for k in r if k in ("A", "B")][0]
        want = "A" if r["i"] % 2 == 0 else "B"
        order_ok += first == want
    print("interleaved as the script says (A first on even i, B first on odd):", order_ok, "of", len(recs))
    ratios = [r["B"] / r["A"] for r in recs]
    print("fit by fit B/A: median %.4f, mean %.4f" % (statistics.median(ratios), statistics.mean(ratios)))
    big = [r for r in recs if r["A"] > 2]
    print("fits over 2 s in A: %d, A %.1f s, B %.1f s, ratio %.4f" % (
        len(big), sum(r["A"] for r in big), sum(r["B"] for r in big),
        sum(r["B"] for r in big) / sum(r["A"] for r in big)))
    print()
    return recs


s = show("benchmarks/results_1.5/split/a3_timing.jsonl")
m = show("benchmarks/results_1.5/release/M1_A3_timing.jsonl")
print("the same jobs in both:", [(r["i"], r["problem"], r["seed"]) for r in s] ==
      [(r["i"], r["problem"], r["seed"]) for r in m])
print("the same 1.4.0 formulas in both campaigns:", sum(1 for a, b in zip(s, m) if a["A_expr"] == b["A_expr"]))
print("1.4.0 total, split campaign %.1f s, M1 campaign %.1f s" % (sum(r["A"] for r in s), sum(r["A"] for r in m)))
