"""F41 of the study, law by law, beside the project's own bench (a diagnostic,
deciding nothing; written on 3 November 2026 after the F41 jobs ended).

For each of the 41 laws: whether its formula holds a sine, cosine or arcsine
(the operators "physical" SRBench gives GP_ELITE hold none), the exact fits of
W0 and W1 here (B = 300 s, operators "physical", columns X0, X1...), the median
time of W1's exact fits, and the exact fits of 1.1.0 in the M2 campaign of the
release (B = 30 s, the pool of each problem, release/m2/campaignR_1.1.0.jsonl).

python benchmarks/results_1.1/srbench_settings/feyn_by_law.py   (repo root)
"""
import json
import os
import sys
from collections import defaultdict
from statistics import median

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, BENCH)

import feynman_bench as F  # noqa: E402
import phase1_bench as P   # noqa: E402

TRIG = ("sin", "cos", "tan")


def load(path, kind="feyn"):
    out = defaultdict(list)
    for line in open(path):
        if line.strip():
            r = json.loads(line)
            if r.get("kind") == kind:
                out[r["problem"]].append(r)
    return out


def main():
    run = os.path.join(HERE, "run")
    w0 = load(os.path.join(run, "W0.jsonl"))
    w1 = load(os.path.join(run, "W1.jsonl"))
    m2 = load(os.path.join(HERE, "..", "release", "m2", "campaignR_1.1.0.jsonl"))
    idx = {j["problem"]: j["index"] for j in P.all_jobs() if j["kind"] == "feyn"}

    def ex(rs):
        return sum(1 for r in rs if r.get("status") == "EXACT")

    print("| law | formula | sine or cosine | pool of the bench | W0 | W1 "
          "| W1 median time of exact fits (s) | 1.1.0, M2 |")
    print("|---|---|---|---|---|---|---|---|")
    tot = defaultdict(int)
    groups = defaultdict(int)
    for p in sorted(idx):
        name, formula, nv, sampler, f, pool = F.PROBS[idx[p]][:6]
        trig = any(t in formula for t in TRIG)
        a, b, c = ex(w0[p]), ex(w1[p]), ex(m2[p])
        t = [r["time"] for r in w1[p] if r.get("status") == "EXACT"]
        print("| %s | `%s` | %s | %s | %d/5 | %d/5 | %s | %d/5 |" % (
            p, formula, "yes" if trig else "no", pool, a, b,
            "%.0f" % median(t) if t else "-", c))
        tot["W0"] += a
        tot["W1"] += b
        tot["M2"] += c
        groups[(trig, a > 0, c > 0)] += 1
    print("\nExact fits: W0 %d, W1 %d (of 205); 1.1.0 in M2: %d (of 205)."
          % (tot["W0"], tot["W1"], tot["M2"]))
    print("\nLaws by (sine or cosine, found here by W0, found in M2):")
    for k in sorted(groups):
        print("  %s: %d" % (k, groups[k]))
    paired = sum(1 for p in idx for r0 in w0[p] for r1 in w1[p]
                 if r0["seed"] == r1["seed"]
                 and (r0.get("status") == "EXACT") == (r1.get("status") == "EXACT"))
    print("\nFits where W0 and W1 agree on exact or not: %d of %d." % (
        paired, sum(len(w0[p]) for p in idx)))


if __name__ == "__main__":
    main()
