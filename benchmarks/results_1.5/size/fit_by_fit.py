"""What ten times the time gives back, fit by fit (written after M5, at the
request of the first review of the release; deciding nothing).

R of the plan is a difference of counts: E(largest, 10T) - E(largest, T).
This script splits it by fit (equation and seed): the fits lost at the
largest size that come back at 10T, the fits exact at 10T that were exact
neither at the reference nor at T, and the fits exact at T and not at 10T.
A fit is exact when its status is EXACT, as in compare_size.py.

    python fit_by_fit.py campaign.jsonl
"""
import json
import sys


def main(path):
    recs = {}
    for line in open(path):
        if line.strip():
            r = json.loads(line)
            recs[(r["cell"], r["problem"], r["seed"])] = r

    def exact(cell):
        return {(p, s) for (c, p, s), r in recs.items() if c == cell and r["status"] == "EXACT"}

    for axis, ref, big, big10 in (("rows", "r100", "r100000", "r100000_10T"),
                                  ("variables", "r1000", "k20", "k20_10T")):
        a, b, c = exact(ref), exact(big), exact(big10)
        lost, gained = sorted(a - b), sorted(b - a)
        back = sorted((a - b) & c)
        new10 = sorted(c - b - a)
        lost10 = sorted(b - c)
        added = [k for k in back + new10 if recs[(big10,) + k].get("uses_added")]
        print("== %s: %s %d, %s %d, %s %d" % (axis, ref, len(a), big, len(b), big10, len(c)))
        print("   at T, lost %d and gained %d (L = %d)" % (len(lost), len(gained), len(a) - len(b)))
        print("   at 10T: %d of the %d lost come back; %d exact neither at %s nor at T; "
              "%d exact at T and not at 10T (R = %d + %d - %d = %d)"
              % (len(back), len(lost), len(new10), ref, len(lost10),
                 len(back), len(new10), len(lost10), len(c) - len(b)))
        print("   come back: %s" % back)
        print("   new at 10T: %s" % new10)
        print("   lost at 10T: %s" % lost10)
        print("   of these, through a formula that uses an added variable: %s" % added)


if __name__ == "__main__":
    main(sys.argv[1])
