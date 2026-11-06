"""Details of M2 of 1.2.0 that compare.txt does not give: python details_x1.py OLD.jsonl NEW.jsonl.

Splits the jobs whose returned expression differs between 1.1.0 and 1.2.0 into
those where X1 alone rewrites the printed formula (the formula of 1.2.0 with X1
switched off is that of 1.1.0) and those whose formula without X1 differs, and
says where the time budget was reached. Then the time of the fits under units
and the number of fits at the budget by version.
"""
import json
import sys
from statistics import median

UNITS = {"ufeyn", "ufeyn_n1", "ufeyn_n10", "utf"}


def load(path):
    out = {}
    for line in open(path):
        r = json.loads(line)
        out[(r["kind"], r["problem"], r.get("split"), r["seed"])] = r
    return out


def main(old_path, new_path):
    old, new = load(old_path), load(new_path)
    assert old.keys() == new.keys(), "the two records are not paired"
    for label, keys in (("Without units", [k for k in old if k[0] not in UNITS]),
                        ("Under units", [k for k in old if k[0] in UNITS])):
        diff = [k for k in keys if old[k]["expr"] != new[k]["expr"]]
        x1_only = [k for k in diff if new[k]["expr_11"] == old[k]["expr"]]
        model = [k for k in diff if new[k]["expr_11"] != old[k]["expr"]]
        both = [k for k in model if old[k]["time_limit_reached"] and new[k]["time_limit_reached"]]
        one = [k for k in model if old[k]["time_limit_reached"] != new[k]["time_limit_reached"]]
        rewritten = [k for k in keys if new[k]["expr_11"] != new[k]["expr"]]
        print("%s: %d jobs, %d return another expression:" % (label, len(keys), len(diff)))
        print("  %d where X1 alone rewrites the printed formula (without X1, that of 1.1.0)"
              % len(x1_only))
        print("  %d whose formula without X1 differs: %d with both versions at the budget,"
              " %d with one of them" % (len(model), len(both), len(one)))
        for k in one:
            print("    %s: %.1f s with 1.1.0, %.1f s with 1.2.0, %s and %s"
                  % (k, old[k]["time"], new[k]["time"], old[k]["status"], new[k]["status"]))
        print("  status changed: %d; X1 rewrites the formula on %d fits of 1.2.0"
              % (sum(old[k].get("status") != new[k].get("status") for k in keys), len(rewritten)))
    print("\nFits at the time budget: %d with 1.1.0, %d with 1.2.0, of %d."
          % (sum(r["time_limit_reached"] for r in old.values()),
             sum(r["time_limit_reached"] for r in new.values()), len(old)))
    for kind in ("ufeyn", "ufeyn_n1", "ufeyn_n10", "utf"):
        keys = [k for k in old if k[0] == kind]
        rest = [k for k in keys if k[1] != "III.19.51"]
        print("%s: median time %.2f s -> %.2f s; without III.19.51, longest %.1f s -> %.1f s"
              % (kind, median(old[k]["time"] for k in keys), median(new[k]["time"] for k in keys),
                 max(old[k]["time"] for k in rest), max(new[k]["time"] for k in rest)))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
