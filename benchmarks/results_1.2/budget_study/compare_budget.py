"""The budget study (PLAN.md in this folder): the arms T, 3T and 10T read from
one campaign of benchmarks/phase1_bench.py run with --budget-factors 1,3,10,
and the criteria the plan wrote before the first fit.

  python compare_budget.py campaign.jsonl
"""
import json
import sys
from collections import defaultdict
from statistics import median

ARMS = (1, 3, 10)


def load(path):
    out = defaultdict(dict)
    for line in open(path):
        if line.strip():
            r = json.loads(line)
            out[r["budget_factor"]][(r["kind"], r["problem"], r["split"], r["seed"])] = r
    return out


def indicators(recs):
    rr = list(recs.values())

    def sel(kind, split=None):
        return [r for r in rr if r["kind"] == kind
                and (split is None or r["split"].startswith(split))]

    ind = {}
    for kind, name in (("feyn", "F41"), ("ufeyn", "U41"), ("tf", "TF78")):
        ind[name + " exact"] = sum(r.get("status") == "EXACT" for r in sel(kind))
    for kind, name in (("feyn_n1", "F41N1"), ("feyn_n10", "F41N10")):
        ind[name + " structure retrieved"] = sum(bool(r.get("structure")) for r in sel(kind))
    folds = [r["r2"] for r in sel("real", "fold")]
    ind["R6 folds median R²"] = round(median(folds), 4) if folds else None
    ood = sel("real", "ood") + sel("realraw", "ood")
    ind["R6 + R7raw out-of-domain collapses"] = sum(r["r2"] < 0 for r in ood)
    ind["crashes"] = sum(r.get("status") == "CRASH" for r in rr)
    ind["fits"] = len(rr)
    ind["fits at the time budget"] = sum(bool(r.get("time_limit_reached")) for r in rr)
    for kind in ("feyn_n1", "feyn_n10", "real"):
        g = [r["generations"] for r in sel(kind) if "generations" in r]
        ind["%s, median generations" % kind] = median(g) if g else None
    t = [r["time"] for r in rr if "time" in r]
    ind["median time of a fit (s)"] = round(median(t), 1) if t else None
    s = [r["size"] for r in rr if "size" in r and r["kind"] in ("feyn_n1", "feyn_n10", "real", "realraw")]
    ind["noisy and real fits, median size"] = median(s) if s else None
    return ind


def per_equation(recs, kind):
    per = defaultdict(int)
    for r in recs.values():
        if r["kind"] == kind:
            per[r["problem"]] += r.get("status") == "EXACT"
    return per


def main(path):
    arms = load(path)
    missing = [a for a in ARMS if a not in arms]
    if missing:
        raise SystemExit("arms missing: %s" % missing)
    keys = [set(arms[a]) for a in ARMS]
    print("Jobs per arm: %s; the same jobs in every arm: %s"
          % ([len(k) for k in keys], keys[0] == keys[1] == keys[2]))
    machines = {(r.get("avx512"), r.get("numpy")) for a in ARMS for r in arms[a].values()}
    print("Engines: %s" % sorted({(r.get("engine_version"), r.get("engine_file"))
                                  for a in ARMS for r in arms[a].values()}))
    print("AVX-512 and NumPy recorded: %s" % sorted(machines, key=str))
    ind = {a: indicators(arms[a]) for a in ARMS}
    print("\n| indicator | T | 3T | 10T |\n|---|---|---|---|")
    for k in ind[1]:
        print("| %s | %s | %s | %s |" % (k, ind[1][k], ind[3][k], ind[10][k]))

    for kind, name in (("feyn", "F41"), ("ufeyn", "U41"), ("tf", "TF78")):
        a, b = per_equation(arms[1], kind), per_equation(arms[10], kind)
        gain = sorted((p, a[p], b[p]) for p in a if b[p] > a[p])
        lose = sorted((p, a[p], b[p]) for p in a if b[p] < a[p])
        print("\n%s, T to 10T: %d equations gain exact fits, %d lose some"
              % (name, len(gain), len(lose)))
        for p, x, y in gain:
            print("  gains: %s %d -> %d" % (p, x, y))
        for p, x, y in lose:
            print("  loses: %s %d -> %d" % (p, x, y))

    t, x = ind[1], ind[10]
    checks = [
        ("F41: at least 10 more exact laws at 10T (%d -> %d)"
         % (t["F41 exact"], x["F41 exact"]), x["F41 exact"] >= t["F41 exact"] + 10),
        ("U41: at least 10 more exact laws at 10T (%d -> %d)"
         % (t["U41 exact"], x["U41 exact"]), x["U41 exact"] >= t["U41 exact"] + 10),
        ("F41N1: at least 10 more structures at 10T (%d -> %d)"
         % (t["F41N1 structure retrieved"], x["F41N1 structure retrieved"]),
         x["F41N1 structure retrieved"] >= t["F41N1 structure retrieved"] + 10),
        ("F41N10: at least 10 more structures at 10T (%d -> %d)"
         % (t["F41N10 structure retrieved"], x["F41N10 structure retrieved"]),
         x["F41N10 structure retrieved"] >= t["F41N10 structure retrieved"] + 10),
        ("R6 folds: median test R² at least 0.01 higher at 10T (%s -> %s)"
         % (t["R6 folds median R²"], x["R6 folds median R²"]),
         x["R6 folds median R²"] >= t["R6 folds median R²"] + 0.01),
    ]
    print("\nCriteria written before the run (PLAN.md): more time adds much if any holds.")
    for name, ok in checks:
        print("  [%s] %s" % ("holds" if ok else "does not hold", name))
    print("MORE TIME ADDS MUCH" if any(ok for _, ok in checks) else "MORE TIME ADDS LITTLE")
    print("\nBeside, deciding nothing: collapses out of domain %d, %d, %d; TF78 exact %d, %d, %d."
          % (ind[1]["R6 + R7raw out-of-domain collapses"],
             ind[3]["R6 + R7raw out-of-domain collapses"],
             ind[10]["R6 + R7raw out-of-domain collapses"],
             ind[1]["TF78 exact"], ind[3]["TF78 exact"], ind[10]["TF78 exact"]))


if __name__ == "__main__":
    main(sys.argv[1])
