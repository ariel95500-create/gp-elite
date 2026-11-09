"""The formulas with the arcsine of M2 (PLAN_RELEASE_1.3.md, M2, "Reported"),
by suite: every fit of 1.3.0 whose recorded formula has an arcsine, with its
status and that of 1.2.0. Written after the first review of M5, which found
that compare.txt gives their count only. The records keep the first 160
characters of a formula, so a formula cut before its first arcsine is not
listed; the count of the fits whose text is cut is given.

  python arcsine_formulas.py campaignR_1.2.0.jsonl campaignR_1.3.0.jsonl
"""
import json
import sys
from collections import defaultdict

SUITE = {"feyn": "F41", "feyn_n1": "F41N1", "feyn_n10": "F41N10", "ufeyn": "U41",
         "ufeyn_n1": "U41N1", "ufeyn_n10": "U41N10", "tf": "TF78",
         "utf": "TF78 under units", "ts": "TS14", "real": "R6", "realraw": "R7raw",
         "tr": "TR25", "trraw": "TR25raw"}


def load(path):
    return {(r["kind"], r["problem"], r["split"], r["seed"]): r
            for r in map(json.loads, open(path))}


def main(a_path, b_path):
    a, b = load(a_path), load(b_path)
    by = defaultdict(list)
    for k in sorted(b):
        if "arcsin" in (b[k].get("expr") or ""):
            by[SUITE.get(k[0], k[0])].append(k)
    print("fits of 1.3.0 whose recorded formula has an arcsine: %d of %d; recorded "
          "formulas cut at 160 characters: %d" % (
              sum(len(v) for v in by.values()), len(b),
              sum(len(b[k].get("expr") or "") >= 160 for k in b)))
    for s in sorted(by):
        print("\n%s: %d" % (s, len(by[s])))
        for k in by[s]:
            st = b[k].get("status") or ("structure" if b[k].get("structure") else "-")
            sa = a[k].get("status") or ("structure" if a[k].get("structure") else "-")
            print("  %s %s seed %d (1.2.0 %s, 1.3.0 %s, formula_exact %s): %s" % (
                k[1], k[2], k[3], sa, st, b[k].get("formula_exact"), b[k].get("expr")))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
