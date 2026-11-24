"""Review 2 of M5, question 4: compare the records of door_probe.py.

Usage: python compare_door.py door_A.json door_B.json [more pairs ...]
Prints each observation that differs between A (1.4.0) and B (1.5).
"""
import json
import sys


def main(args):
    for i in range(0, len(args), 2):
        a, b = json.load(open(args[i])), json.load(open(args[i + 1]))
        print("== %s (engine %s, python %s, pytest %s)  vs  %s (engine %s, python %s, pytest %s)" % (
            args[i].rsplit("/", 1)[-1], a["engine"], a["python"], a["pytest"],
            args[i + 1].rsplit("/", 1)[-1], b["engine"], b["python"], b["pytest"]))
        A, B = a["obs"], b["obs"]
        keys = sorted(set(A) | set(B))
        same = [k for k in keys if A.get(k) == B.get(k)]
        diff = [k for k in keys if A.get(k) != B.get(k)]
        print("observations: %d, identical %d, different %d" % (len(keys), len(same), len(diff)))
        for k in diff:
            print("  %-60s 1.4.0 %s | 1.5 %s" % (k, A.get(k), B.get(k)))
        print()


if __name__ == "__main__":
    main(sys.argv[1:])
