"""Review 1: the laws of the frozen test set with an inverse trigonometric
function, and the pool trig of TF78 and F41. /venv12b/bin/python -I r7_frozen_inverse_trig.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_pair, pools  # noqa: E402

FP, MAN, PROBS = pools()
A, B, _, _ = load_pair()
for n, e in sorted(MAN.items()):
    f = e.get("formula", "")
    if any(s in f for s in ("arc", "asin", "acos", "atan")):
        ks = sorted(k for k in A if k[1] == n)
        print(n, e["group"], e["pool"], f)
        print("   ", [(k[0], k[3], A[k].get("status"), B[k].get("status")) for k in ks])
print("TF78 equations of the pool trig:", sum(1 for e in MAN.values() if e["group"] == "TF78" and e["pool"] == "trig"))
print("TS14 systems of the pool trig:", sorted(n for n, e in MAN.items() if e["group"] == "TS14" and e["pool"] == "trig"))
print("F41 equations of the pool trig:", [p[0] for p in PROBS if p[5] == "trig"])
