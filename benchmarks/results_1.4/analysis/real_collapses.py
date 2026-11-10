"""The fits of the real data of the decision bench that collapse out of the
training range (test R² below 0), read from the records of the M2 of 1.3.0
(kinds real and realraw only; the frozen test set is not read), with the
rows each dataset trains on.

  python real_collapses.py > real_collapses.txt
"""
import io
import json
import os
import sys
from collections import defaultdict
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", ".."))
REC = os.path.join(BENCH, "results_1.3", "release", "m2", "campaignR_1.3.0.jsonl")
sys.path.insert(0, BENCH)
with redirect_stdout(io.StringIO()):
    import decision_bench as D


def med(v):
    v = sorted(v)
    return v[len(v) // 2]


def main():
    ood = [r for r in map(json.loads, open(REC))
           if r["kind"] in ("real", "realraw") and r["split"] == "ood"]
    col = [r for r in ood if r["r2"] < 0]
    print("fits out of the training range: %d; collapses: %d; median size of "
          "the collapsing models %d, of the others %d" % (
              len(ood), len(col), med([r["size"] for r in col]),
              med([r["size"] for r in ood if r["r2"] >= 0])))
    by = defaultdict(list)
    for r in ood:
        by[r["problem"]].append(r)
    print("\n%-24s %-14s %-10s %s" % ("dataset", "training rows", "collapses", "sizes of the collapsing models"))
    for name in sorted(by, key=lambda k: -sum(r["r2"] < 0 for r in by[k])):
        Xtr, _ytr, _Xte, _yte = D.real_data(name, "ood", raw=True)
        c = [r for r in by[name] if r["r2"] < 0]
        print("%-24s %-14s %-10s %s" % (
            name, "%d (%d inputs)" % (len(Xtr), Xtr.shape[1]),
            "%d of %d" % (len(c), len(by[name])), sorted(r["size"] for r in c)))
    print("\nwith more time (budget study of 1.2.0, "
          "../../results_1.2/budget_study/README.md): 10 collapses at 30 s, "
          "16 at 90 s, 22 at 300 s.")


if __name__ == "__main__":
    main()
