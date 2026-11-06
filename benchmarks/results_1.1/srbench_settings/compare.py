"""The criteria of PLAN.md (amended: S = W1 against W0), read from the records.

python compare.py DIR   (DIR holds W0.jsonl and W1.jsonl)
"""
import json
import os
import sys
from statistics import median


def load(path):
    out = {}
    for line in open(path):
        if line.strip():
            r = json.loads(line)
            out[(r["kind"], r["problem"], r["split"], r["seed"])] = r
    return out


def figures(recs):
    rs = list(recs.values())
    f = {}
    f["fits"] = len(rs)
    f["crashes"] = sum(1 for r in rs if r.get("status") == "CRASH")
    f["F41 exact"] = sum(1 for r in rs if r["kind"] == "feyn" and r.get("status") == "EXACT")
    for k, name in (("feyn_n1", "F41N1"), ("feyn_n10", "F41N10")):
        f[name + " structures"] = sum(1 for r in rs if r["kind"] == k and r.get("structure"))
    folds6 = [r for r in rs if r["kind"] == "real" and r["split"].startswith("fold")]
    f["R6 folds median R2"] = median(r["r2"] for r in folds6) if folds6 else float("nan")
    ood = [r for r in rs if r["kind"] in ("real", "realraw") and r["split"] == "ood"]
    f["R6+R7raw collapses"] = sum(1 for r in ood if r["r2"] < 0)
    folds = [r for r in rs if r["kind"] in ("real", "realraw") and r["split"].startswith("fold")]
    f["R6+R7raw folds median size"] = median(r["size"] for r in folds) if folds else float("nan")
    for k in ("feyn", "feyn_n1", "feyn_n10", "real", "realraw"):
        t = [r["time"] for r in rs if r["kind"] == k and "time" in r]
        if t:
            f["median time %s (s)" % k] = median(t)
    return f


def main(d):
    w0, w1 = load(os.path.join(d, "W0.jsonl")), load(os.path.join(d, "W1.jsonl"))
    assert w0.keys() == w1.keys(), "the records are not paired"
    a, b = figures(w0), figures(w1)
    print("| figure | W0 | W1 |\n|---|---|---|")
    for k in a:
        fa, fb = a[k], b[k]
        fmt = "%.4f" if isinstance(fa, float) and k.endswith("R2") else "%s"
        print("| %s | %s | %s |" % (k, fmt % fa, fmt % fb))
    c = [
        ("F41 exact laws of W1 not fewer than W0's minus 3",
         b["F41 exact"] >= a["F41 exact"] - 3),
        ("F41N1 structures not fewer than W0's minus 3",
         b["F41N1 structures"] >= a["F41N1 structures"] - 3),
        ("F41N10 structures not fewer than W0's minus 3",
         b["F41N10 structures"] >= a["F41N10 structures"] - 3),
        ("R6 folds median R2 not below W0's minus 0.005",
         b["R6 folds median R2"] >= a["R6 folds median R2"] - 0.005),
        ("R6 + R7raw collapses out of domain not more than W0's plus 2",
         b["R6+R7raw collapses"] <= a["R6+R7raw collapses"] + 2),
        ("R6 + R7raw folds median size not above 1.25 times W0's",
         b["R6+R7raw folds median size"] <= 1.25 * a["R6+R7raw folds median size"]),
    ]
    gain = (b["F41 exact"] >= a["F41 exact"] + 10
            or (b["F41N1 structures"] + b["F41N10 structures"])
            >= (a["F41N1 structures"] + a["F41N10 structures"]) + 10
            or b["R6 folds median R2"] >= a["R6 folds median R2"] + 0.01)
    c.append(("a gain: F41 exact +10, or structures +10, or R6 median R2 +0.01", gain))
    print("\nCriteria of PLAN.md, S = W1:")
    for text, ok in c:
        print("  [%s] %s" % ("met" if ok else "NOT met", text))
    print("W1 is better than W0" if all(ok for _, ok in c) else "W0 stays")


if __name__ == "__main__":
    main(sys.argv[1])
