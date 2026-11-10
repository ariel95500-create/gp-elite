"""Second review of M5: the arcsine seeds in the records of M2."""
import os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import A_PATH, B_PATH, SUITE, load, pools, pool_of
a, _ = load(A_PATH); b, _ = load(B_PATH); P = pools()
for f in ("elementary_seed", "tolerant_seed"):
    for name, R in (("1.2.0", a), ("1.3.0", b)):
        ks = [k for k, r in R.items() if r[f] and "arcsin" in str(r[f])]
        print("%s %s with arcsin: %d" % (name, f, len(ks)),
              sorted(Counter((SUITE[k[0]], k[1]) for k in ks).items()))
        # first term of the tolerant seed
        if f == "tolerant_seed":
            first = [k for k in ks if str(R[k][f]).startswith("arcsin")]
            print("   ... of which arcsin is the first-listed seed: %d" % len(first))
# what the tolerant seed field looks like for feynman_test_1
for k in sorted(b):
    if k[1] == "feynman_test_1":
        print(k, "B:", str(b[k]["tolerant_seed"])[:200])
        print(k, "A:", str(a[k]["tolerant_seed"])[:200])
        print("   status", a[k]["status"], b[k]["status"], "expr B", b[k]["expr"][:100])
# are seeds placed on noiseless kinds via tolerant_seed?
print(Counter(SUITE[k[0]] for k, r in b.items() if r["tolerant_seed"]))
