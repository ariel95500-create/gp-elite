"""Review 1: the 160-character truncation of `expr` in the M2 records and
the counts that read the formula (arcsine counts, the identity of the pool
physical). /venv12b/bin/python -I r11_truncation.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_pair, pools, pool_of  # noqa: E402

A, B, _, _ = load_pair()
FP, MAN, _ = pools()
trig = [k for k in B if pool_of(k, FP, MAN) == "trig"]
fe = [k for k in trig if B[k]["formula_exact"] is False]
cut = [k for k in fe if len(B[k]["expr"]) >= 160]
print("pool trig, 1.3.0, formula_exact False: %d; with 'arcsin' in the recorded text: %d; "
      "recorded text cut at 160 characters: %d, of which without 'arcsin' in the visible part: %d"
      % (len(fe), sum("arcsin" in B[k]["expr"] for k in fe), len(cut),
         sum("arcsin" not in B[k]["expr"] for k in cut)))
print("pool trig, 1.3.0, all fits with the text cut at 160: %d of %d" % (
    sum(len(B[k]["expr"]) >= 160 for k in trig), len(trig)))
phys = [k for k in A if pool_of(k, FP, MAN) == "physical"]
det = [k for k in phys if not A[k]["time_limit_reached"] and not B[k]["time_limit_reached"]]
print("pool physical, neither at budget: %d; text cut at 160 in either version: %s" % (
    len(det), [k for k in det if len(A[k]["expr"]) >= 160 or len(B[k]["expr"]) >= 160]))
a_fe = {k for k in trig if A[k]["formula_exact"] is False}
b_fe = set(fe)
print("pool trig: departing with 1.2.0 %d, with 1.3.0 %d, in both %d; 1.3.0 departing without "
      "'arcsin' in the text %d" % (len(a_fe), len(b_fe), len(a_fe & b_fe),
                                   sum("arcsin" not in B[k]["expr"] for k in b_fe)))
