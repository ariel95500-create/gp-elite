"""Details of M2 read from the two records: python details.py OLD.jsonl NEW.jsonl.

The figures of the M2 section of the README beside the criteria of
compare_m2_1.1.py: jobs that differ without units and whether their status
changes, and under units the equations that gain or lose exact fits.
"""
import json
import sys
from collections import defaultdict
from statistics import median

UNITS = {"ufeyn", "ufeyn_n1", "ufeyn_n10", "utf"}
FAMILIES_1_0 = {"racine", "rationnelle", "trig", "exponentielle", "logarithme"}


def load(path):
    out = {}
    for line in open(path):
        r = json.loads(line)
        out[(r["kind"], r["problem"], r.get("split"), r["seed"])] = r
    return out


def main(old_path, new_path):
    old, new = load(old_path), load(new_path)
    assert old.keys() == new.keys(), "the two records are not paired"
    vo, vn = next(iter(old.values()))["engine_version"], next(iter(new.values()))["engine_version"]

    plain = [k for k in old if k[0] not in UNITS]
    diff = [k for k in plain if old[k]["expr"] != new[k]["expr"]]
    at_budget = [k for k in diff if old[k]["time_limit_reached"] or new[k]["time_limit_reached"]]
    status = [k for k in diff if old[k].get("status") != new[k].get("status")]
    print("Without units: %d jobs, %d return another expression, %d of them reached the"
          " budget in one version or both, %d change status." % (len(plain), len(diff), len(at_budget), len(status)))
    for k in status:
        print("  status %s -> %s: %s" % (old[k].get("status"), new[k].get("status"), k))
    for k in diff:
        if k not in at_budget:
            print("  differs without reaching the budget: %s" % (k,))

    for kind, name in (("ufeyn", "U41"), ("utf", "TF78 under units")):
        keys = [k for k in old if k[0] == kind]
        per = defaultdict(lambda: [0, 0])
        for k in keys:
            per[k[1]][0] += old[k]["status"] == "EXACT"
            per[k[1]][1] += new[k]["status"] == "EXACT"
        gain = sorted(p for p, (a, b) in per.items() if b > a)
        lose = sorted(p for p, (a, b) in per.items() if b < a)
        print("\n%s: %d fits, exact %d -> %d; %d equations gain exact fits, %d lose some."
              % (name, len(keys), sum(a for a, _ in per.values()), sum(b for _, b in per.values()), len(gain), len(lose)))
        for p in lose:
            print("  loses: %s %d -> %d" % (p, per[p][0], per[p][1]))
        lost_fits = [k for k in keys if old[k]["status"] == "EXACT" and new[k]["status"] != "EXACT"]
        for k in lost_fits:
            print("  fit exact with %s, not with %s: %s seed %d (%s)" % (vo, vn, k[1], k[3], new[k]["status"]))
        print("  equations never exact in any seed: %d -> %d of %d"
              % (sum(a == 0 for a, _ in per.values()), sum(b == 0 for _, b in per.values()), len(per)))
        print("  median time of a fit: %.1f s -> %.1f s"
              % (median(old[k]["time"] for k in keys), median(new[k]["time"] for k in keys)))
        if kind == "ufeyn":
            fam = [k for k in keys if old[k].get("family") in FAMILIES_1_0]
            print("  the five families of 1.0: %d fits, exact %d -> %d"
                  % (len(fam), sum(old[k]["status"] == "EXACT" for k in fam), sum(new[k]["status"] == "EXACT" for k in fam)))

    print("\nOut of domain, R6 + R7raw collapses by version:")
    for kind in ("real", "realraw", "tr", "trraw"):
        rows = [k for k in old if k[0] == kind and k[2] == "ood"]
        co = sum(old[k]["r2"] < 0 for k in rows)
        cn = sum(new[k]["r2"] < 0 for k in rows)
        both = sum(old[k]["r2"] < 0 and new[k]["r2"] < 0 for k in rows)
        print("  %s: %d fits out of domain, collapses %d -> %d, %d in both" % (kind, len(rows), co, cn, both))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
