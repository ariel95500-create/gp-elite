"""What the noise costs, equation by equation, read from the records of the
M2 of 1.3.0 (../../results_1.3/release/m2/campaignR_1.3.0.jsonl). Only the
kinds of the decision bench are read: feyn, ufeyn and their noisy kinds. The
frozen test set is not read.

  python noise_by_equation.py > noise_by_equation.txt
"""
import io
import json
import os
import sys
from collections import Counter, defaultdict
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.normpath(os.path.join(HERE, "..", ".."))
REC = os.path.join(BENCH, "results_1.3", "release", "m2", "campaignR_1.3.0.jsonl")
KINDS = ("feyn", "ufeyn", "feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10")


def main():
    sys.path.insert(0, BENCH)
    with redirect_stdout(io.StringIO()):
        import feynman_bench as F
    law = {p[0]: (p[1], p[5]) for p in F.PROBS}
    recs = [r for r in map(json.loads, open(REC)) if r["kind"] in KINDS]
    n = defaultdict(lambda: defaultdict(int))
    for r in recs:
        ok = r.get("status") == "EXACT" if r["kind"] in ("feyn", "ufeyn") \
            else bool(r.get("structure"))
        n[r["problem"]][r["kind"]] += ok
    tot = {k: sum(n[p][k] for p in n) for k in KINDS}
    print("gp-elite 1.3.0, M2 of its release, 205 fits per kind (41 equations, "
          "seeds 0 to 4, 30 s).")
    print("exact laws: F41 %d, U41 %d; structure retrieved: F41N1 %d, F41N10 %d, "
          "U41N1 %d, U41N10 %d" % tuple(tot[k] for k in KINDS))
    print("\nfits of 5 by equation (exact without noise, structure with noise)")
    print("%-10s %-40s %-8s F41 U41 | N1 N10 | UN1 UN10" % ("equation", "law", "pool"))
    for p in sorted(n, key=lambda p: (sum(n[p][k] for k in KINDS), p)):
        print("%-10s %-40s %-8s %d   %d   | %d  %d   | %d   %d" % (
            (p, law[p][0][:40], law[p][1]) + tuple(n[p][k] for k in KINDS)))

    print("\nthe noisy fits by the seed placed at the start (the records keep "
          "the seeds of phases 4a and 5):")
    for kind in KINDS[2:]:
        c = Counter()
        for r in recs:
            if r["kind"] == kind:
                seeded = "a noise-tolerant seed" if r.get("tolerant_seed") else (
                    "an exact seed" if r.get("elementary_seed") else "none of them")
                c[(seeded, bool(r.get("structure")))] += 1
        for s in ("a noise-tolerant seed", "an exact seed", "none of them"):
            a, b = c[(s, True)], c[(s, False)]
            if a + b:
                print("  %-9s %-22s structure retrieved in %3d fits of %3d" % (
                    kind, s + ":", a, a + b))

    print("\nequations exact in at least 4 fits of 5 without noise and with "
          "the structure in none of the 5 fits:")
    for kind, ref in (("feyn_n1", "feyn"), ("feyn_n10", "feyn")):
        lost = sorted(p for p in n if n[p][ref] >= 4 and n[p][kind] == 0)
        print("  %s (%d): %s" % (kind, len(lost), ", ".join(lost)))
    odd = sorted(p for p in n if n[p]["feyn_n10"] > n[p]["feyn_n1"])
    print("equations with the structure more often at 10 %% noise than at 1 %%: %s"
          % ", ".join("%s (%d and %d)" % (p, n[p]["feyn_n1"], n[p]["feyn_n10"])
                      for p in odd))


if __name__ == "__main__":
    main()
