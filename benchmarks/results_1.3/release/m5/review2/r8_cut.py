"""Second review of M5: the cut formulas (160 characters) by pool, 1.3.0, and
what arcsine_formulas.py counts."""
import os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import A_PATH, B_PATH, SUITE, load, pools, pool_of
a, _ = load(A_PATH); b, _ = load(B_PATH); P = pools()
cut = [k for k in b if len(b[k]["expr"]) >= 160]
print("1.3.0 formulas of 160 characters: %d (of which pool trig %d, physical %d)" % (
    len(cut), sum(pool_of(k, P) == "trig" for k in cut), sum(pool_of(k, P) == "physical" for k in cut)))
tc = [k for k in cut if pool_of(k, P) == "trig" and "arcsin" not in b[k]["expr"]]
print("pool trig, cut, no arcsine in the visible part: %d" % len(tc), sorted(Counter(SUITE[k[0]] for k in tc).items()))
print("pool trig fits with a visible arcsine: %d; trig fits cut: %d" % (
    sum("arcsin" in b[k]["expr"] for k in b if pool_of(k, P) == "trig"),
    sum(pool_of(k, P) == "trig" for k in cut)))
# noisy suites: arcsine formulas with structure retrieved
for kd in ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10"):
    ks = [k for k in b if k[0] == kd and "arcsin" in b[k]["expr"]]
    print(SUITE[kd], "arcsine formulas %d, of which structure retrieved %d" % (
        len(ks), sum(bool(b[k]["structure"]) for k in ks)))
