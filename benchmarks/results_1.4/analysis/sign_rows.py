"""On the noisy kinds of the decision bench, the training rows whose target
changes sign under the noise. The seed finders of the power law, of the
binomial forms and of the functions of a monomial work on log|y| and stop
when the target has not one sign (gp_elite/core.py: _power_law_exponents,
_binomial_forms, _elementary_forms). No fit is run; the engine is not
imported. The noise of the bench is drawn once per equation: the five seeds
of an equation fit the same noisy targets.

  python sign_rows.py > sign_rows.txt
"""
import io
import os
import sys
from contextlib import redirect_stdout

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))
with redirect_stdout(io.StringIO()):
    import feynman_bench as F
    import phase1_bench as B


def one_sign(v):
    return bool(np.all(v > 0) or np.all(v < 0))


def main():
    names = [p[0] for p in F.PROBS]
    print("equations whose clean training target has one sign and whose noisy "
          "target has not (rows of the other sign, of the training rows)")
    print("%-10s %-40s %-14s %-14s" % ("equation", "law", "1 % noise", "10 % noise"))
    count = {"feyn_n1": 0, "feyn_n10": 0}
    never = []
    for i, p in enumerate(names):
        cells, hit = [], False
        for kind in ("feyn_n1", "feyn_n10"):
            job = dict(kind=kind, problem=p, index=i, split="test", seed=0)
            _X, y, _Xte, _yte, _Xo, _yo, _nm, _pool, clean = B._data(job)
            y, clean = np.asarray(y, float), np.asarray(clean, float)
            if not one_sign(clean):
                cells.append("clean: two signs")
                continue
            if one_sign(y):
                cells.append("one sign")
            else:
                hit = True
                count[kind] += 1
                cells.append("%d of %d" % (int(np.sum(np.sign(y) != np.sign(clean))), len(y)))
        if hit:
            print("%-10s %-40s %-14s %-14s" % (p, F.PROBS[i][1][:40], cells[0], cells[1]))
        if cells[0] == "clean: two signs":
            never.append(p)
    print("\n%d equations of 41 at 1 %% noise and %d at 10 %% lose the single "
          "sign of their target." % (count["feyn_n1"], count["feyn_n10"]))
    print("equations whose clean target already has two signs (no such seed, "
          "with or without noise): %s" % ", ".join(never))


if __name__ == "__main__":
    main()
