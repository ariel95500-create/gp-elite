"""The formulas with the arcsine of M2 (PLAN_RELEASE_1.3.md, M2, "Reported"),
by suite: every fit of 1.3.0 whose recorded formula has an arcsine, with its
status and that of 1.2.0. Written after the first review of M5, which found
that compare.txt gives their count only. The records keep the first 160
characters of a formula, so a formula cut before its first arcsine is not
listed; the number of fits of the pool trig whose text is cut with no
arcsine visible bounds them. For the noisy kinds, the status is that of the
test rows and the structure is printed beside it.

  python arcsine_formulas.py campaignR_1.2.0.jsonl campaignR_1.3.0.jsonl
"""
import json
import sys
from collections import defaultdict

SUITE = {"feyn": "F41", "feyn_n1": "F41N1", "feyn_n10": "F41N10", "ufeyn": "U41",
         "ufeyn_n1": "U41N1", "ufeyn_n10": "U41N10", "tf": "TF78",
         "utf": "TF78 under units", "ts": "TS14", "real": "R6", "realraw": "R7raw",
         "tr": "TR25", "trraw": "TR25raw"}


def pools():
    """The operator pool of each problem, as the bench gives it."""
    import io
    import os
    from contextlib import redirect_stdout
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", ".."))
    with redirect_stdout(io.StringIO()):
        import feynman_bench as F
        import test_set as T
    out = {p[0]: p[5] for p in F.PROBS}
    m = T.manifest()["datasets"]
    for g in ("TF78", "TS14"):
        for n in T.names(g):
            out[n] = m[n]["pool"]
    return out


def load(path):
    return {(r["kind"], r["problem"], r["split"], r["seed"]): r
            for r in map(json.loads, open(path))}


def main(a_path, b_path):
    global POOLS
    POOLS = pools()
    a, b = load(a_path), load(b_path)
    by = defaultdict(list)
    for k in sorted(b):
        if "arcsin" in (b[k].get("expr") or ""):
            by[SUITE.get(k[0], k[0])].append(k)
    trig = [k for k in b if k[0] not in ("real", "realraw", "tr", "trraw")
            and POOLS.get(k[1], "?") != "physical"]
    hidden = [k for k in trig if len(b[k].get("expr") or "") >= 160
              and "arcsin" not in b[k]["expr"]]
    print("fits of 1.3.0 whose recorded formula has an arcsine: %d of %d. Fits of "
          "the pool trig whose recorded formula is cut at 160 characters with no "
          "arcsine in its visible part: %d of %d, the most that could hide one" % (
              sum(len(v) for v in by.values()), len(b), len(hidden), len(trig)))
    for s in sorted(by):
        print("\n%s: %d" % (s, len(by[s])))
        for k in by[s]:
            st = "%s, structure %s" % (b[k].get("status"), b[k].get("structure"))
            sa = "%s, structure %s" % (a[k].get("status"), a[k].get("structure"))
            print("  %s %s seed %d (1.2.0 %s, 1.3.0 %s, formula_exact %s): %s" % (
                k[1], k[2], k[3], sa, st, b[k].get("formula_exact"), b[k].get("expr")))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
