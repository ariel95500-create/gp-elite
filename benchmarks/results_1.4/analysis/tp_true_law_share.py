"""On the tables of the TP diagnostic, the share of the variance that the
TRUE law leaves unexplained, after the linear scaling a + b·law on the noisy
training rows. That is the figure the noise-tolerant seeds compare with
their threshold, _TOLERANT_REL = 0.015 (gp_elite/core.py, _seed_rel_error).
No fit is run; the engine is not imported.

  python tp_true_law_share.py > tp_true_law_share.txt
"""
import io
import os
import sys
from contextlib import redirect_stdout

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))
with redirect_stdout(io.StringIO()):
    import tp_diagnostic as T

THRESHOLD = 0.015


def main():
    print("share of the variance left by the true law, median and largest of "
          "the draws 0 to 9; threshold of the noise-tolerant seeds: %g" % THRESHOLD)
    print("%-16s %-22s %-22s %-22s %-22s" % (
        "experiment", "10 points, 2 %", "10 points, 5 %", "20 points, 2 %", "20 points, 5 %"))
    for e in T.EXPERIMENTS:
        cells = []
        for n in (10, 20):
            for noise in (0.02, 0.05):
                v = []
                for draw in range(10):
                    X, y, yc, _Xg, _yg = T.data(e["key"], n, noise, draw)
                    A = np.column_stack([np.ones(len(y)), yc])
                    c = np.linalg.lstsq(A, y, rcond=None)[0]
                    v.append(float(np.mean((y - A @ c) ** 2) / np.var(y)))
                over = sum(x > THRESHOLD for x in v)
                cells.append("%.4f / %.4f (%d>)" % (float(np.median(v)), max(v), over))
        print("%-16s %-22s %-22s %-22s %-22s" % ((e["key"],) + tuple(cells)))
    print("(n>) counts the draws of 10 whose share is above the threshold: on "
          "those tables the true law itself could not be placed as a seed.")


if __name__ == "__main__":
    main()
