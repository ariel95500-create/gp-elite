"""Counts of M2 by operator pool, quoted by the release README, the CHANGELOG
and the pages of the limits: how often the printed formula departs from the
model (formula_exact False), how many of those formulas show an arcsine in
their recorded text (cut at 160 characters by the bench), and where the
seeds of the arcsine were placed. Written after the second review of M5,
which found that no file of m2/ printed them.

  python pool_counts.py campaignR_1.2.0.jsonl campaignR_1.3.0.jsonl
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arcsine_formulas import load, pools  # noqa: E402

PHYSICAL_KINDS = ("real", "realraw", "tr", "trraw")


def main(a_path, b_path):
    P = pools()
    a, b = load(a_path), load(b_path)

    def pool(k):
        return "physical" if k[0] in PHYSICAL_KINDS else P.get(k[1], "?")

    print("fits by pool: %s" % dict(Counter(pool(k) for k in b)))
    for name in ("physical", "trig"):
        ks = [k for k in b if pool(k) == name]
        fa = [k for k in ks if a[k].get("formula_exact") is False]
        fb = [k for k in ks if b[k].get("formula_exact") is False]
        cut = [k for k in fb if len(b[k].get("expr") or "") >= 160]
        arc = [k for k in fb if "arcsin" in (b[k].get("expr") or "")]
        print("\npool %s, %d fits: formula_exact False in %d with 1.2.0 and %d with "
              "1.3.0 (%d in both)" % (name, len(ks), len(fa), len(fb),
                                      len(set(fa) & set(fb))))
        print("  of the %d of 1.3.0: an arcsine in the recorded text %d; text cut "
              "at 160 characters %d, of which with no arcsine visible %d" % (
                  len(fb), len(arc), len(cut),
                  sum("arcsin" not in b[k]["expr"] for k in cut)))
    for field, what in (("elementary_seed", "exact"), ("tolerant_seed", "noise-tolerant")):
        for v, d in (("1.2.0", a), ("1.3.0", b)):
            placed = Counter((k[0], k[1]) for k in d
                             if "arcsin" in str(d[k].get(field) or ""))
            print("\n%s: %s arcsine seed placed in %d fits: %s" % (
                v, what, sum(placed.values()), dict(sorted(placed.items()))))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
