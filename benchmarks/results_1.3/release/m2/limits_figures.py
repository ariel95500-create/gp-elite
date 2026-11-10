"""The figures of the pages of the limits (LIMITATIONS.md, LIMITATIONS.fr.md),
read from the records of M2 for each version:

  python limits_figures.py campaignR_1.1.0.jsonl campaignR_1.2.0.jsonl

Points 1 to 4, 6 and 8 of the pages; the points give the figures of 1.0.0
(release_1.0) and the introduction those of later campaigns.
"""
import json
import sys
from collections import defaultdict


def load(path):
    return [json.loads(line) for line in open(path)]


def exact_by_problem(recs, kind):
    per = defaultdict(int)
    for r in recs:
        if r["kind"] == kind:
            per[r["problem"]] += r.get("status") == "EXACT"
    return per


def figures(recs):
    out = {}
    f41 = exact_by_problem(recs, "feyn")
    out["1. F41 exact fits of 205"] = sum(f41.values())
    out["1. F41 equations never exact"] = sorted(p for p, n in f41.items() if n == 0)
    out["1. F41 equations exact once in five"] = sorted(p for p, n in f41.items() if n == 1)
    tf = exact_by_problem(recs, "tf")
    out["1. TF78 equations never exact (of %d)" % len(tf)] = sum(n == 0 for n in tf.values())
    out["2. TF78 exact fits of 390"] = sum(tf.values())
    for fam in ("main", "bonus"):
        rr = [r for r in recs if r["kind"] == "tf" and r.get("family") == fam]
        out["2. TF78 %s exact fits of %d" % (fam, len(rr))] = sum(r.get("status") == "EXACT" for r in rr)
    ts = [r for r in recs if r["kind"] == "ts" and r["split"] == "test"]
    out["2. TS14 exact on the test rows, of %d" % len(ts)] = sum(r.get("status") == "EXACT" for r in ts)
    for k, name in (("feyn_n1", "1 %"), ("feyn_n10", "10 %")):
        out["3. structure retrieved with %s noise, of 205" % name] = sum(
            bool(r.get("structure")) for r in recs if r["kind"] == k)
    ood = [r for r in recs if r["kind"] in ("real", "realraw") and r["split"] == "ood"]
    out["4. bench, collapses out of domain, of %d" % len(ood)] = sum(r["r2"] < 0 for r in ood)
    out["4. bench, worst out-of-domain R2"] = min(r["r2"] for r in ood)
    for kind in ("tr", "trraw"):
        rr = [r for r in recs if r["kind"] == kind and r["split"] == "ood"]
        out["4. test set %s, collapses of %d" % (kind, len(rr))] = sum(r["r2"] < 0 for r in rr)
        per = defaultdict(int)
        for r in rr:
            per[r["problem"]] += r["r2"] < 0
        top = sorted(per.values(), reverse=True)[:6]
        out["4. test set %s, collapses on the six datasets with most" % kind] = sum(top)
    for label, kinds in (("bench", ("real", "realraw")), ("test set", ("tr", "trraw"))):
        rr = [r for r in recs if r["kind"] in kinds]
        out["6. %s real data, formula_exact False, of %d" % (label, len(rr))] = sum(
            r.get("formula_exact") is False for r in rr)
    u41 = exact_by_problem(recs, "ufeyn")
    out["8. U41 exact fits of 205"] = sum(u41.values())
    out["8. U41 equations never exact"] = sum(n == 0 for n in u41.values())
    return out


def main(a_path, b_path):
    a, b = load(a_path), load(b_path)
    va, vb = a[0]["engine_version"], b[0]["engine_version"]
    fa, fb = figures(a), figures(b)
    print("| figure | %s | %s |\n|---|---|---|" % (va, vb))
    for k in fa:
        print("| %s | %s | %s |" % (k, fa[k], fb[k]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
