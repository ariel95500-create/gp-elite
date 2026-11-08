"""The classes of PLAN.md, read from the records of diag.py.

  python classify.py records.jsonl

A fit that did not return an exact law falls in the first class that holds:
  1 no candidate within reach
  2 every candidate within reach turned away by a guard of the pool
  3 lost by the pool: those that passed the guards were out of it at the end
  4 not a finalist
  5 cut by the grace: a finalist within reach whose fit to convergence the
    deadline skipped
  6 polished and still not exact
"""
import json
import sys
from collections import Counter

NAMES = {1: "no candidate within reach", 2: "turned away by a guard",
         3: "lost by the pool", 4: "not a finalist", 5: "cut by the grace",
         6: "polished and still not exact"}


def klass(rec):
    w = rec["diag"]["within_reach"]
    if not w:
        return 1
    passed = [c for c in w if c["entered"] or c["stable"]]
    if not passed:
        return 2
    in_pool = [c for c in passed if c["in_pool"]]
    if not in_pool:
        return 3
    fin = [c for c in in_pool if c["finalist"]]
    if not fin:
        return 4
    if not any(c["conv_ran"] for c in fin):
        return 5
    return 6


def arm(r):
    return {1: "T", 3: "3T", 10: "10T"}[r["budget_factor"]]


def main(path):
    recs = [json.loads(l) for l in open(path) if l.strip()]
    print("Fits: %d; crashes: %d" % (len(recs), sum(r.get("status") == "CRASH"
                                                    for r in recs)))
    print("\n| fit | arm | status (study, now) | generations (study, now) |"
          " offered | within reach | class |")
    print("|---|---|---|---|---|---|---|")
    counted = Counter()
    for r in sorted(recs, key=lambda r: (r["budget_factor"], r["problem"], r["seed"])):
        if r.get("status") == "CRASH":
            print("| %s seed %d | %s | CRASH | | | | |" % (r["problem"], r["seed"], arm(r)))
            continue
        d = r["diag"]
        same = r["status"] == r["study_status"]
        k = klass(r) if r["status"] != "EXACT" else None
        if k is not None and same and r["study_status"] == "NEAR":
            counted[k] += 1
        print("| %s seed %d | %s | %s, %s%s | %s, %s | %d | %d | %s |" % (
            r["problem"], r["seed"], arm(r), r["study_status"], r["status"],
            "" if same else " (changed)", r["study_generations"],
            r["generations"], d["n_distinct"], len(d["within_reach"]),
            "%d %s" % (k, NAMES[k]) if k else "exact"))
    n = sum(counted.values())
    print("\nNear fits of the budget study that kept their status: %d" % n)
    for k in sorted(NAMES):
        print("  class %d, %s: %d" % (k, NAMES[k], counted[k]))
    lost = sum(counted[k] for k in (2, 3, 4, 5))
    print("Classes 2 to 5 together: %d (PLAN.md: at least 10 means the end of "
          "the search loses laws the search had found)" % lost)

    print("\nI.8.14, read apart:")
    for r in sorted(recs, key=lambda r: (r["budget_factor"], r["seed"])):
        if r["problem"] != "I.8.14" or r.get("status") == "CRASH":
            continue
        d = r["diag"]
        print("  seed %d %s: %s; %d offered, %d within reach; pool %d; polish "
              "began %.2f s after the deadline and took %.2f s; fitted to "
              "convergence: %d of %d finalists; selected size %s"
              % (r["seed"], arm(r), r["status"], d["n_distinct"],
                 len(d["within_reach"]), d["pool_size"],
                 d["after_deadline_s"] or 0.0, d["polish_s"] or 0.0,
                 d["conv_ran"], d["started"], (d["selected"] or {}).get("size")))
        for c in sorted(d["within_reach"], key=lambda c: c["size"]):
            print("    within reach, size %d: in the pool %s, finalist %s, "
                  "fitted to convergence %s, stable %s: %s"
                  % (c["size"], c["in_pool"], c["finalist"], c["conv_ran"],
                     c["stable"], c["expr"][:100]))


if __name__ == "__main__":
    main(sys.argv[1])
