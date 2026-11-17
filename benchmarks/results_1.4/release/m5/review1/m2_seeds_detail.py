"""M5 review 1 (read-only): beside m2_recompute.py, the fits of M2 read
together with their noise-tolerant seeds (the records' tolerant_seed):
- the fits with the same seeds in both versions: how many keep the recorded
  formula, how many change status (and whether a budget was reached);
- the status changes of the exact-data suites, with or without other seeds;
- the suites where 1.4.0 places other seeds than 1.3.0 (none / same / other);
- the real-data fits of TR25raw where a seed is placed;
- the fits that lose the structure at 10 % noise on I.27.6 and III.15.12;
- U41 between campaign N2b and M2 (the exact law that "timing alone moves").

  python3 -I m2_seeds_detail.py benchmarks/results_1.4
"""
import json
import os
import sys
from collections import Counter


def load(path):
    d = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            d[(r["kind"], r["problem"], r["split"], r["seed"])] = r
    return d


def seeds(r):
    return r.get("tolerant_seed") or None


def main(root):
    m2 = os.path.join(root, "release", "m2")
    a = load(os.path.join(m2, "campaignR_1.3.0.jsonl"))
    b = load(os.path.join(m2, "campaignR_1.4.0.jsonl"))
    keys = sorted(set(a) & set(b))

    same = [k for k in keys if seeds(a[k]) == seeds(b[k])]
    other_expr = [k for k in same if a[k].get("expr") != b[k].get("expr")]
    at_budget = [k for k in other_expr if a[k].get("time_limit_reached") or b[k].get("time_limit_reached")]
    print("same seeds: %d fits; another recorded formula in %d of them, %d of which at a "
          "time budget in at least one version" % (len(same), len(other_expr), len(at_budget)))
    for k in same:
        if a[k].get("status") != b[k].get("status"):
            print("   same seeds, status %s -> %s: %s (budget %s / %s)" % (
                a[k].get("status"), b[k].get("status"), k,
                a[k].get("time_limit_reached"), b[k].get("time_limit_reached")))

    print("\nstatus changes on the exact-data suites, with the same or other seeds:")
    for kind in ("feyn", "ufeyn", "tf", "utf", "ts"):
        c = Counter()
        for k in keys:
            if k[0] == kind and a[k].get("status") != b[k].get("status"):
                c["same seeds" if seeds(a[k]) == seeds(b[k]) else "other seeds"] += 1
        print("   %-6s %s" % (kind, dict(c)))

    print("\nnoise-tolerant seeds by suite (none in both / the same / other):")
    for kind in sorted({k[0] for k in keys}):
        c = Counter("none" if not seeds(a[k]) and not seeds(b[k]) else
                    "same" if seeds(a[k]) == seeds(b[k]) else "other"
                    for k in keys if k[0] == kind)
        print("   %-10s none %4d  same %4d  other %4d" % (kind, c["none"], c["same"], c["other"]))

    print("\nTR25raw fits where a seed is placed:")
    for k in keys:
        if k[0] == "trraw" and (seeds(a[k]) or seeds(b[k])):
            print("   %s r2 %.4f -> %.4f, %s, same formula %s" % (
                k, a[k]["r2"], b[k]["r2"],
                "same seeds" if seeds(a[k]) == seeds(b[k]) else "other seeds",
                a[k].get("expr") == b[k].get("expr")))

    print("\nstructure lost at 10 % noise on I.27.6 and III.15.12:")
    for k in keys:
        if k[1] in ("I.27.6", "III.15.12") and k[0] in ("feyn_n10", "ufeyn_n10") \
                and bool(a[k].get("structure")) and not b[k].get("structure"):
            print("   %s %s" % (k, "same seeds" if seeds(a[k]) == seeds(b[k]) else "other seeds"))

    print("\nU41, campaign N2b against M2 (exact laws, and the fits whose status differs):")
    for camp, rel in (("bench_1.3.0.jsonl", "campaignR_1.3.0.jsonl"),
                      ("bench_n2b.jsonl", "campaignR_1.4.0.jsonl")):
        c = load(os.path.join(root, "n2b", "campaign", camp))
        r = load(os.path.join(m2, rel))
        ex = lambda D: sum(v.get("status") == "EXACT" for k, v in D.items() if k[0] == "ufeyn")
        diff = [(k[1], k[3], c[k]["status"], r[k]["status"], c[k].get("time_limit_reached"),
                 r[k].get("time_limit_reached"))
                for k in c if k in r and k[0] == "ufeyn" and c[k]["status"] != r[k]["status"]]
        print("   %s -> %s: %d -> %d; %s" % (camp, rel, ex(c), ex(r), diff))


if __name__ == "__main__":
    main(sys.argv[1])
