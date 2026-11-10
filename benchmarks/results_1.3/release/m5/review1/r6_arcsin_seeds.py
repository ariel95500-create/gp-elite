"""Review 1: the fits of M2 where an arcsine seed was placed, exact
(elementary_seed, phase 4a) or noise-tolerant (tolerant_seed, phase 5).
/venv12b/bin/python -I r6_arcsin_seeds.py"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_pair  # noqa: E402

A, B, _, _ = load_pair()
for V, R in (("1.2.0", A), ("1.3.0", B)):
    c, t = Counter(), Counter()
    for k, r in R.items():
        if "arcsin" in str(r.get("elementary_seed")):
            c[(k[0], k[1])] += 1
        if "arcsin" in str(r.get("tolerant_seed")):
            t[(k[0], k[1])] += 1
    print("%s: exact arcsine seed placed %s (%d fits)" % (V, dict(c), sum(c.values())))
    print("%s: noise-tolerant arcsine seed placed %s (%d fits)" % (V, dict(t), sum(t.values())))
