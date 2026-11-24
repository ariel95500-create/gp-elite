"""M5 review 1: the figures of the size study recomputed from the raw records.

Reads benchmarks/results_1.5/size/campaign.jsonl and profiles.jsonl only.
Does not import gp_elite and runs no fit.

    python3 -I size_recompute.py <repo root>
"""
import collections
import json
import os
import statistics
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
SIZE = os.path.join(ROOT, "benchmarks/results_1.5/size")
CELLS = ["r100", "r1000", "r10000", "r100000", "r100000_10T",
         "k5", "k10", "k20", "k20_10T"]


def load(name):
    with open(os.path.join(SIZE, name)) as fh:
        return [json.loads(l) for l in fh if l.strip()]


recs = load("campaign.jsonl")
by = collections.defaultdict(list)
for r in recs:
    by[r["cell"]].append(r)

print("== records")
print("records", len(recs))
keys = [(r["eq"], r["seed"], r["cell"]) for r in recs]
print("distinct jobs", len(set(keys)))
print("equations", sorted({r["eq"] for r in recs}) == list(range(41)),
      "seeds", sorted({r["seed"] for r in recs}), "cells", sorted(by) == sorted(CELLS))
print("statuses", collections.Counter(r["status"] for r in recs))
print("min generations", min(r["generations"] for r in recs),
      "fits with generations < 1:", sum(1 for r in recs if r["generations"] < 1))
for f in ("pythonhashseed", "python", "numpy", "engine_version", "engine_file"):
    print(f, collections.Counter(r[f] for r in recs))
dates = sorted(r["date"] for r in recs)
print("first date", dates[0], "last date", dates[-1])
print("time_limit by cell", {c: sorted({r["time_limit"] for r in by[c]}) for c in CELLS})
print("n_train by cell", {c: sorted({r["n_train"] for r in by[c]}) for c in CELLS})
nv = {}
for r in by["r100"]:
    nv[r["eq"]] = r["n_features"]
print("variables per equation (count of equations with 1..6):",
      [sum(1 for v in nv.values() if v == k) for k in range(1, 7)])
print("columns at k20: min", min(r["n_features"] for r in by["k20"]),
      "max", max(r["n_features"] for r in by["k20"]))

print()
print("== the table of reading.txt, recomputed")
print("%-12s %5s %5s %5s %5s %6s %8s %6s %6s %6s %6s" % (
    "cell", "fits", "exact", "near", "crash", "medgen", "medfirst", "elem", "tol",
    "added", "past"))
E = {}
for c in CELLS:
    rs = by[c]
    E[c] = sum(1 for r in rs if r["status"] == "EXACT")
    print("%-12s %5d %5d %5d %5d %6s %8.3f %6d %6d %6d %6d" % (
        c, len(rs), E[c], sum(1 for r in rs if r["status"] == "NEAR"),
        sum(1 for r in rs if r["status"] == "CRASH"),
        statistics.median(r["generations"] for r in rs),
        statistics.median(r["to_first_gen"] for r in rs),
        sum(1 for r in rs if r.get("elementary_seed")),
        sum(1 for r in rs if r.get("tolerant_seed")),
        sum(1 for r in rs if r.get("uses_added")),
        sum(1 for r in rs if r["time"] > 1.1 * r["time_limit"])))

print()
print("== the verdict")
L_rows = E["r100"] - E["r100000"]
R_rows = E["r100000_10T"] - E["r100000"]
L_var = E["r1000"] - E["k20"]
R_var = E["k20_10T"] - E["k20"]


def reading(L, R):
    if L < 10:
        return "size costs little"
    if R >= L / 2:
        return "mostly brute force"
    if R < L / 4:
        return "mostly the algorithm"
    return "both"


print("rows: L = %d, R = %d, L/2 = %.1f -> %s" % (L_rows, R_rows, L_rows / 2, reading(L_rows, R_rows)))
print("variables: L = %d, R = %d, L/4 = %.1f -> %s" % (L_var, R_var, L_var / 4, reading(L_var, R_var)))

print()
print("== the guard: the first ten fits of each cell in the order of the file, median time")
for c in CELLS:
    first = by[c][:10]
    print("%-12s median %.2f s (rounded %.1f); dates %s to %s; equations %s" % (
        c, statistics.median(r["time"] for r in first),
        statistics.median(r["time"] for r in first),
        first[0]["date"], first[-1]["date"], [r["eq"] for r in first]))

print()
print("== exact at the first generation (generations == 1) and after it")
first_sets = {}
for c in CELLS:
    ex = [r for r in by[c] if r["status"] == "EXACT"]
    g1 = {(r["eq"], r["seed"]) for r in ex if r["generations"] == 1}
    first_sets[c] = g1
    print("%-12s exact %3d, at gen 1 %3d, after %3d, generations of exact: %s" % (
        c, len(ex), len(g1), len(ex) - len(g1),
        sorted(collections.Counter(r["generations"] for r in ex).items())[:6]))
print("rows cells: the same fits at the first generation:",
      all(first_sets[c] == first_sets["r100"] for c in
          ["r1000", "r10000", "r100000", "r100000_10T"]))
for c in ["k5", "k10", "k20", "k20_10T"]:
    print("%-8s first-gen set is a subset of r1000's: %s; lost %d; new %d" % (
        c, first_sets[c] <= first_sets["r1000"],
        len(first_sets["r1000"] - first_sets[c]), len(first_sets[c] - first_sets["r1000"])))
print("k20 and k20_10T: the same first-gen set:", first_sets["k20"] == first_sets["k20_10T"])

# fits exact at gen 1 but with generations == 1 and not exact? (a fit that stopped at gen 1 otherwise)
for c in CELLS:
    n1 = sum(1 for r in by[c] if r["generations"] == 1 and r["status"] != "EXACT")
    if n1:
        print("note: %s has %d fits that stopped at generation 1 without an exact law" % (c, n1))

print()
print("== the laws lost at 100,000 rows: fits exact at r100 and not at r100000")
idx = {(r["eq"], r["seed"], r["cell"]): r for r in recs}
lost = [(e, s) for (e, s, c) in idx if c == "r100" and idx[(e, s, c)]["status"] == "EXACT"
        and idx[(e, s, "r100000")]["status"] != "EXACT"]
gained = [(e, s) for (e, s, c) in idx if c == "r100" and idx[(e, s, c)]["status"] != "EXACT"
          and idx[(e, s, "r100000")]["status"] == "EXACT"]
print("lost", len(lost), "gained", len(gained))
print("generations at r100 of the lost ones:", sorted(idx[(e, s, "r100")]["generations"] for e, s in lost))
print("lost by equation:", collections.Counter(idx[(e, s, "r100")]["problem"] for e, s in lost))
print("gained:", [(idx[(e, s, "r100")]["problem"], s) for e, s in gained])

print()
print("== the fits that ran to their budget (time_limit_reached or generations >= 1000 x factor)")
for c in CELLS:
    rs = by[c]
    cap = 1000 * rs[0]["budget_factor"]
    full = [r for r in rs if r.get("time_limit_reached") or r["generations"] >= cap]
    g = [r["generations"] for r in full]
    print("%-12s %3d to budget, median %s, min %s, max %s; time_limit_reached %d" % (
        c, len(full), statistics.median(g), min(g), max(g),
        sum(1 for r in rs if r.get("time_limit_reached"))))

print()
print("== time to the first generation: median, max; fits whose first generation comes after the time limit")
for c in CELLS:
    t = sorted(r["to_first_gen"] for r in by[c])
    late = [r for r in by[c] if r["to_first_gen"] > r["time_limit"]]
    print("%-12s median %.3f max %.3f; past the time limit: %d %s" % (
        c, statistics.median(t), t[-1], len(late),
        collections.Counter(r["problem"] for r in late)))

print()
print("== past the budget (time > 1.1 x time_limit): count, median and largest over")
for c in CELLS:
    rs = [r for r in by[c] if r["time"] > 1.1 * r["time_limit"]]
    if rs:
        over = sorted(r["time"] - r["time_limit"] for r in rs)
        print("%-12s %3d over by %.2f (median), %.2f (largest)" % (
            c, len(rs), statistics.median(over), over[-1]))
for c in CELLS:
    rs = [r for r in by[c] if r["time"] > r["time_limit"]]
    print("%-12s any time over the limit: %d" % (c, len(rs)))

print()
print("== each equation: exact fits of five seeds, by cell")
probs = {r["eq"]: r["problem"] for r in recs}
table = {}
for e in range(41):
    table[e] = [sum(1 for r in by[c] if r["eq"] == e and r["status"] == "EXACT") for c in CELLS]
    if any(x != 5 for x in table[e]):
        print("%-3d %-10s %s" % (e, probs[e], " ".join("%3d" % x for x in table[e])))

print()
print("== rows, the equations lost (r100, r100000, r100000_10T)")
for name in ["I.8.14", "II.2.42", "I.26.2", "I.6.20a"]:
    e = next(k for k, v in probs.items() if v == name)
    print(name, table[e][CELLS.index("r100")], table[e][CELLS.index("r100000")],
          table[e][CELLS.index("r100000_10T")])
print("are the lost-at-100,000 fits found by the search at r100 (generations > 1)?",
      all(idx[(e, s, "r100")]["generations"] > 1 for e, s in lost))

print()
print("== variables: equations exact in 5 of 5 at r1000 that fall to 0 or 1 in a k cell at T")
for e in range(41):
    row = dict(zip(CELLS, table[e]))
    if row["r1000"] == 5:
        ks = [(c, row[c]) for c in ["k5", "k10", "k20"]]
        first_fall = next((c for c, v in ks if v <= 1), None)
        if first_fall:
            print("%-10s r1000 5, k5 %d, k10 %d, k20 %d: falls to <=1 from %s" % (
                probs[e], row["k5"], row["k10"], row["k20"], first_fall))

print()
print("== variables: which seed finder found, at r1000, the first-gen laws lost in the k cells")
for c in ["k5", "k10", "k20"]:
    lostk = sorted(first_sets["r1000"] - first_sets[c])
    kinds = collections.Counter()
    for e, s in lostk:
        t = idx[(e, s, "r1000")]["trace"]
        kind = []
        for k in ("binomial_seed", "elementary_seed", "power_law_seed", "tolerant_seed"):
            if t.get(k):
                kind.append(k)
        kinds[" + ".join(kind) or "none"] += 1
    print(c, len(lostk), dict(kinds))

print()
print("== the binomial seed of I.34.1 and I.27.6 by cell (seed 0)")
for name in ["I.34.1", "I.27.6"]:
    e = next(k for k, v in probs.items() if v == name)
    for c in ["r1000", "k5", "k10", "k20"]:
        r = idx[(e, 0, c)]
        print(name, c, "columns", r["n_features"], "binomial:", r["trace"].get("binomial_seed"),
              "| status", r["status"], "gens", r["generations"])

print()
print("== the formulas that use an added variable, by status")
for c in ["k5", "k10", "k20", "k20_10T"]:
    rs = [r for r in by[c] if r.get("uses_added")]
    print(c, len(rs), dict(collections.Counter(r["status"] for r in rs)))
ex_added = [r for r in recs if r.get("uses_added") and r["status"] == "EXACT"]
for r in ex_added:
    print("  EXACT using an added variable:", r["cell"], r["problem"], r["seed"], len(r["expr"]), r["expr"][:70])

print()
print("== near fits by cell")
print({c: sum(1 for r in by[c] if r["status"] == "NEAR") for c in CELLS})

print()
print("== the profiles")
prof = load("profiles.jsonl")
print("records", len(prof), collections.Counter(r["mode"] for r in prof))
print("dates", sorted(r["date"] for r in prof)[0], "to", sorted(r["date"] for r in prof)[-1])
print("records dated before 02:00:", sum(1 for r in prof if r["date"] < "2026-11-24T02:00"))
for r in sorted(prof, key=lambda r: r["date"]):
    print("  ", r["date"], r["eq"], r["cell"], r["mode"], r["time"])
print("machine", collections.Counter(r.get("machine") for r in prof))
print("engine", collections.Counter(r["engine_version"] for r in prof),
      collections.Counter(r["pythonhashseed"] for r in prof))
pb = {(r["eq"], r["cell"], r["mode"]): r for r in prof}
pairs = {(e, c) for (e, c, m) in pb}
print("pairs", len(pairs), "same formula in all:",
      all(pb[(e, c, "plain")]["expr"] == pb[(e, c, "profiled")]["expr"] for e, c in pairs))
for e in sorted({e for e, c in pairs}):
    for c in ["r100", "r1000", "r10000", "r100000", "k5", "k10", "k20"]:
        a, b = pb[(e, c, "plain")], pb[(e, c, "profiled")]
        tot = b["prof_total"]
        roles = b["roles"]
        print("eq %2d %-8s plain %8.2f s prof %8.2f s ratio %.2f gens %d %s | total %.1f | "
              "eval-group %.0f%% const %.0f%% seeds %.0f%% | incl seeds %.0f%% incl fit %.0f%% | numeric %.0f%%"
              " genetic-like %s" % (
                  e, c, a["time"], b["time"], b["time"] / a["time"], a["generations"], a["status"],
                  tot, 100 * b["groups"]["evaluating formulas"] / tot,
                  100 * b["groups"]["fitting constants"] / tot,
                  100 * b["groups"]["placing seeds"] / tot,
                  100 * b["inclusive"]["seed_makers"] / tot,
                  100 * b["inclusive"]["constant_fitters"] / tot,
                  100 * roles.get("numeric", 0) / tot,
                  {k: "%.0f%%" % (100 * v / tot) for k, v in roles.items() if v / tot > 0.05}))
r = pb[(6, "r100000", "profiled")]
print("I.8.14 r100000 profiled: top functions")
for t in r["top"][:5]:
    print("  ", t)
r = pb[(16, "r100000", "profiled")]
print("I.11.19 r100000 profiled: top functions")
for t in r["top"][:5]:
    print("  ", t)
print("ratios profiled/plain at r100:", [round(pb[(e, "r100", "profiled")]["time"] / pb[(e, "r100", "plain")]["time"], 2) for e in (0, 6, 16)])
print("ratios profiled/plain at r100000:", [round(pb[(e, "r100000", "profiled")]["time"] / pb[(e, "r100000", "plain")]["time"], 2) for e in (0, 6, 16)])
