# -*- coding: utf-8 -*-
"""Campaign S1 (benchmarks/results_1.4/PLAN.md, "Campaign S1"): the four
criteria, written before the run, read from the paired records of the TP
diagnostic of the candidate before S1 (A) and of the candidate with S1 (B).

  python compare_s1.py tp_A.jsonl tp_B.jsonl                    (draws 0 to 4)
  python compare_s1.py --confirmation tp_A_conf.jsonl tp_B_conf.jsonl
                                                                (draws 10 to 14)

The confirmation reads criteria 1 to 3.

Definitions:
- the law: the record's "law" (the model refitted on the noiseless targets
  is the law to 1e-9 on the noiseless grid);
- the units guarantee: units_gate on the units arm (bench/README.md);
- printed without an additive constant: additive_constant False;
- the law on the front: front_law;
- the origin of the model of B: the label of S1 in small_cv ("champion",
  "family", "search", "band", with "exponents rounded" and "without the
  constant" for the variants).
"""
import json
import re
import sys
from collections import Counter
from statistics import median


def load(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out[(r["arm"], r["exp"], r["n"], r["noise"], r["draw"])] = r
    return out


def ok(D, arm=None):
    return [r for k, r in D.items() if (arm is None or k[0] == arm)
            and not r.get("crash")]


def law(D, arm, exp=None, n=None, noise=None):
    return sum(r["law"] for r in ok(D, arm) if (exp is None or r["exp"] == exp)
               and (n is None or r["n"] == n) and (noise is None or r["noise"] == noise))


def origin(r):
    m = re.search(r"choisi : (.*?), erreur croisée", r.get("small_cv") or "")
    return m.group(1) if m else "none"


def main(argv):
    conf = argv[0] == "--confirmation"
    if conf:
        argv = argv[1:]
    A, B = load(argv[0]), load(argv[1])
    crash = lambda D: sum(bool(r.get("crash")) for r in D.values())
    print("TP: %d fits in A, %d in B, the same jobs: %s; crashes A %d, B %d"
          % (len(A), len(B), set(A) == set(B), crash(A), crash(B)))
    print("  engines: A %s; B %s" % (
        sorted({r.get("engine_file") for r in A.values()}),
        sorted({r.get("engine_file") for r in B.values()})))
    print("  draws %s" % sorted({k[4] for k in A}))
    exps = sorted({k[1] for k in A})

    print("\n| arm | law A | law B | useful A | useful B | median time A | B |")
    print("|---|---|---|---|---|---|---|")
    for arm in ("plain", "units"):
        a, b = ok(A, arm), ok(B, arm)
        print("| %s | %d | %d | %d | %d | %.1f s | %.1f s |" % (
            arm, law(A, arm), law(B, arm), sum(r["useful"] for r in a),
            sum(r["useful"] for r in b), median(r["time"] for r in a),
            median(r["time"] for r in b)))

    checks = []
    la, lb = law(A, "plain"), law(B, "plain")
    checks.append(("1. TP, plain arm: the law in B at least A + 15 of 200 (%d, %d)"
                   % (la, lb), lb >= la + 15))
    fell = [(e, law(A, "plain", e), law(B, "plain", e)) for e in exps
            if law(B, "plain", e) < law(A, "plain", e) - 2]
    checks.append(("2. no experiment falls by more than 2 of 20 in the plain arm (%s)"
                   % (", ".join("%s %d -> %d" % f for f in fell) or "none"), not fell))
    ua, ub = law(A, "units"), law(B, "units")
    checks.append(("3. TP, units arm: the law in B no fewer than A - 3 of 200 (%d, %d)"
                   % (ua, ub), ub >= ua - 3))
    bu = ok(B, "units")
    bad = [r for r in bu if not r.get("units_gate")]
    checks.append(("3. every model of B under units passes its gate of dimensions "
                   "(%d of %d)" % (len(bu) - len(bad), len(bu)), not bad))
    if not conf:
        for arm in ("plain", "units"):
            ta = median(r["time"] for r in ok(A, arm))
            tb = median(r["time"] for r in ok(B, arm))
            checks.append(("4. time, %s arm: median of B at most 1.5 times A "
                           "(%.1f s, %.1f s, ratio %.2f)" % (arm, ta, tb, tb / ta),
                           tb <= 1.5 * ta))
    print("\nCriteria written before the run (PLAN.md%s):"
          % (", confirmation of S1" if conf else ""))
    for name, holds in checks:
        print("  [%s] %s" % ("holds" if holds else "FAILS", name))
    allok = all(h for _, h in checks)
    print(("S1 KEPT" if allok else "S1 NOT KEPT") if conf else
          ("S1 ADOPTED" if allok else "S1 NOT ADOPTED"))

    print("\nBeside, deciding nothing:")
    print("  the law by experiment, points and noise, plain arm, A -> B:")
    for e in exps:
        cells = ["%d pts %d %%: %d -> %d" % (n, round(100 * nz), law(A, "plain", e, n, nz),
                                            law(B, "plain", e, n, nz))
                 for n in (10, 20) for nz in (0.02, 0.05)]
        print("    %-16s %s" % (e, "   ".join(cells)))
    print("  the law by experiment, units arm, A -> B:")
    for e in exps:
        print("    %-16s %d -> %d" % (e, law(A, "units", e), law(B, "units", e)))
    for D, nm in ((A, "A"), (B, "B")):
        wl = [r for r in ok(D, "plain") if r["law"]]
        print("  %s, plain arm: of the %d fits with the law, %d printed without an "
              "additive constant; the law on the front returned in %d of 200 fits"
              % (nm, len(wl), sum(not r.get("additive_constant") for r in wl),
                 sum(r["front_law"] for r in ok(D, "plain"))))
    for arm in ("plain", "units"):
        c = Counter(origin(r) for r in ok(B, arm))
        cl = Counter(origin(r) for r in ok(B, arm) if r["law"])
        print("  B, %s arm, the origin of the model returned (with the law): %s" % (
            arm, "; ".join("%s %d (%d)" % (k, v, cl[k]) for k, v in c.most_common())))


if __name__ == "__main__":
    main(sys.argv[1:])
