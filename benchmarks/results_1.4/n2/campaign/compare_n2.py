# -*- coding: utf-8 -*-
"""Campaign N2 (benchmarks/results_1.4/PLAN.md, "Campaign N2"): the six
criteria, written before the run, read from the paired records of 1.3.0
from PyPI (A) and of the candidate with N2 (B).

  python compare_n2.py bench_1.3.0.jsonl bench_candidate.jsonl \\
         tp_1.3.0.jsonl tp_candidate.jsonl
  python compare_n2.py --confirmation conf_1.3.0.jsonl conf_candidate.jsonl

The bench files hold Dnoise (feyn_n1, feyn_n10, ufeyn_n1, ufeyn_n10) and
Dguard (feyn, ufeyn, real, realraw); the TP files the TP diagnostic, draws 0
to 4. The confirmation holds feyn_n1 and feyn_n10 at seed 0 with the draws
of the noise 1 to 4.

Definitions, as in the campaigns of 1.2 and 1.3:
- a structure: the record's "structure" (its model refitted on the
  noiseless targets leaves less than 1e-9 on the test rows);
- an exact law: status EXACT (1 - R² below 1e-9 on the test rows);
- the folds of R6: kind real, splits fold0 to fold4 (30 fits), their test
  R²;
- a collapse out of domain: a fit of R6 or R7raw on the split ood (65 fits)
  whose test R² is negative;
- the law on TP: the record's "law" (the model refitted on the noiseless
  targets is the law to 1e-9 on the noiseless grid);
- the units guarantee: units_ok on the units kinds of the bench (no unknown
  constant there), units_gate on the units arm of TP (the engine's own
  gate, bench/README.md).
"""
import json
import sys
from collections import Counter
from statistics import median


def load(path, key):
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out[key(r)] = r
    return out


def bkey(r):
    k = (r["kind"], r["problem"], r["split"], r["seed"])
    return k + (r["noise_draw"],) if "noise_draw" in r else k


def tkey(r):
    return (r["arm"], r["exp"], r["n"], r["noise"], r["draw"])


def kind(D, k):
    return [r for key, r in D.items() if key[0] == k]


def n_structure(D, k):
    return sum(bool(r.get("structure")) for r in kind(D, k))


def n_exact(D, k):
    return sum(r.get("status") == "EXACT" for r in kind(D, k))


def per_eq(D, k, field):
    c = Counter()
    for r in kind(D, k):
        c[r["problem"]] += (r.get("status") == "EXACT") if field == "exact" \
            else bool(r.get("structure"))
    return c


def header(DA, DB, name):
    crash = lambda D: sum(r.get("status") == "CRASH" or bool(r.get("crash"))
                          for r in D.values())
    print("%s: %d fits in A, %d in B, the same jobs: %s; crashes A %d, B %d"
          % (name, len(DA), len(DB), set(DA) == set(DB), crash(DA), crash(DB)))
    print("  engines: A %s; B %s" % (
        sorted({r.get("engine_file") for r in DA.values()}),
        sorted({r.get("engine_file") for r in DB.values()})))


def campaign(argv):
    DA, DB = load(argv[0], bkey), load(argv[1], bkey)
    TA, TB = load(argv[2], tkey), load(argv[3], tkey)
    header(DA, DB, "Dnoise and Dguard")
    header(TA, TB, "TP")
    checks = []

    print("\n| kind | A | B |")
    print("|---|---|---|")
    for k, nm, f in (("feyn_n1", "F41N1, structure", n_structure),
                     ("feyn_n10", "F41N10, structure", n_structure),
                     ("ufeyn_n1", "U41N1, structure", n_structure),
                     ("ufeyn_n10", "U41N10, structure", n_structure),
                     ("feyn", "F41, exact", n_exact),
                     ("ufeyn", "U41, exact", n_exact)):
        print("| %s (of %d) | %d | %d |" % (nm, len(kind(DA, k)), f(DA, k), f(DB, k)))

    # 1. structure under noise, without units
    a1, a10 = n_structure(DA, "feyn_n1"), n_structure(DA, "feyn_n10")
    b1, b10 = n_structure(DB, "feyn_n1"), n_structure(DB, "feyn_n10")
    checks.append(("1. F41N1 + F41N10: B at least A + 15 of 410 (%d, %d)"
                   % (a1 + a10, b1 + b10), b1 + b10 >= a1 + a10 + 15))
    checks.append(("1. F41N1: B no fewer than A - 3 (%d, %d)" % (a1, b1), b1 >= a1 - 3))
    checks.append(("1. F41N10: B no fewer than A - 3 (%d, %d)" % (a10, b10),
                   b10 >= a10 - 3))
    # 2. under units
    for k, nm in (("ufeyn_n1", "U41N1"), ("ufeyn_n10", "U41N10")):
        a, b = n_structure(DA, k), n_structure(DB, k)
        checks.append(("2. %s: B no fewer than A - 3 (%d, %d)" % (nm, a, b), b >= a - 3))
    # 3. no loss without noise
    for k, nm in (("feyn", "F41"), ("ufeyn", "U41")):
        a, b = n_exact(DA, k), n_exact(DB, k)
        checks.append(("3. %s exact: B no fewer than A - 3 (%d, %d)" % (nm, a, b),
                       b >= a - 3))
        pa, pb = per_eq(DA, k, "exact"), per_eq(DB, k, "exact")
        fell = sorted(p for p in pa if pa[p] >= 3 and pb[p] <= 1)
        checks.append(("3. %s: no equation exact at three seeds or more in A falls to "
                       "one or none (%s)" % (nm, ", ".join(fell) or "none"), not fell))
    # 4. real data
    folds = lambda D: [r["r2"] for key, r in D.items()
                       if key[0] == "real" and key[2].startswith("fold")]
    ma, mb = median(folds(DA)), median(folds(DB))
    checks.append(("4. R6 folds, median test R²: B not more than 0.005 below A "
                   "(%.4f, %.4f; %d fits)" % (ma, mb, len(folds(DB))), mb >= ma - 0.005))
    coll = lambda D: [r for key, r in D.items()
                      if key[0] in ("real", "realraw") and key[2] == "ood"]
    ca = sum(r["r2"] < 0 for r in coll(DA))
    cb = sum(r["r2"] < 0 for r in coll(DB))
    checks.append(("4. R6 + R7raw, collapses out of domain: B not more than A + 2 "
                   "(%d, %d of %d)" % (ca, cb, len(coll(DB))), cb <= ca + 2))
    # 5. the units guarantee
    ub = [r for key, r in DB.items() if key[0] in ("ufeyn", "ufeyn_n1", "ufeyn_n10")]
    tu = [r for key, r in TB.items() if key[0] == "units" and not r.get("crash")]
    bad = [r for r in ub if not r.get("units_ok")] + \
        [r for r in tu if not r.get("units_gate")]
    checks.append(("5. the units guarantee: every model of B under units passes "
                   "(%d of %d on the bench, %d of %d on TP)"
                   % (sum(bool(r.get("units_ok")) for r in ub), len(ub),
                      sum(bool(r.get("units_gate")) for r in tu), len(tu)), not bad))
    # 6. TP
    tp = lambda D, arm: [r for key, r in D.items() if key[0] == arm and not r.get("crash")]
    print("\nTP: | arm | law A | law B | useful A | useful B | median time A | B |")
    for arm in ("plain", "units"):
        a, b = tp(TA, arm), tp(TB, arm)
        la, lb = sum(r["law"] for r in a), sum(r["law"] for r in b)
        ta, tb = median(r["time"] for r in a), median(r["time"] for r in b)
        print("  | %s | %d | %d | %d | %d | %.1f s | %.1f s |" % (
            arm, la, lb, sum(r["useful"] for r in a), sum(r["useful"] for r in b), ta, tb))
        checks.append(("6. TP, %s: the law in B no fewer than A - 5 of 200 (%d, %d)"
                       % (arm, la, lb), lb >= la - 5))
        checks.append(("6. TP, %s: median time of B at most 1.5 times A (%.1f s, "
                       "%.1f s, ratio %.2f)" % (arm, ta, tb, tb / ta), tb <= 1.5 * ta))

    print("\nCriteria written before the run (PLAN.md):")
    for name, ok in checks:
        print("  [%s] %s" % ("holds" if ok else "FAILS", name))
    print("N2 ADOPTED" if all(ok for _, ok in checks) else "N2 NOT ADOPTED")

    # reported beside, deciding nothing
    print("\nBeside, deciding nothing:")
    print("  structures by equation (F41N1, F41N10, U41N1, U41N10), A -> B, where "
          "they differ:")
    for p in sorted({key[1] for key in DA if key[0] == "feyn_n1"}):
        cells = []
        for k in ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10"):
            a, b = per_eq(DA, k, "s")[p], per_eq(DB, k, "s")[p]
            cells.append("%d -> %d" % (a, b))
        if any(c.split(" -> ")[0] != c.split(" -> ")[1] for c in cells):
            print("    %-10s %s" % (p, "   ".join(cells)))
    print("  exact laws by equation (F41, U41), A -> B, where they differ:")
    for p in sorted({key[1] for key in DA if key[0] == "feyn"}):
        cells = ["%d -> %d" % (per_eq(DA, k, "exact")[p], per_eq(DB, k, "exact")[p])
                 for k in ("feyn", "ufeyn")]
        if any(c.split(" -> ")[0] != c.split(" -> ")[1] for c in cells):
            print("    %-10s %s" % (p, "   ".join(cells)))
    for D, n in ((DA, "A"), (DB, "B")):
        rs = list(D.values())
        noisy = [r for r in rs if r["kind"] in ("feyn_n1", "feyn_n10", "ufeyn_n1",
                                                 "ufeyn_n10")]
        real = [r for r in rs if r["kind"] in ("real", "realraw")]
        print("  %s: noise-tolerant seeds placed in %d of %d noisy fits; in %d of %d "
              "real fits; median size %s; formula_exact False in %d of %d; median "
              "time %.1f s" % (
                  n, sum(bool(r.get("tolerant_seed")) for r in noisy), len(noisy),
                  sum(bool(r.get("tolerant_seed")) for r in real), len(real),
                  median(r["size"] for r in rs if "size" in r),
                  sum(r.get("formula_exact") is False for r in rs), len(rs),
                  median(r["time"] for r in rs if "time" in r)))
    for key in sorted(DB):
        r = DB[key]
        if key[0] in ("real", "realraw") and r.get("tolerant_seed"):
            print("    B places a seed on %s %s %s seed %d: %s" % (
                key[0], key[1], key[2], key[3], r["tolerant_seed"][:120]))
    print("  TP, the law by experiment and arm, A -> B:")
    exps = sorted({key[1] for key in TA})
    for e in exps:
        cells = []
        for arm in ("plain", "units"):
            a = sum(r["law"] for key, r in TA.items() if key[0] == arm and key[1] == e
                    and not r.get("crash"))
            b = sum(r["law"] for key, r in TB.items() if key[0] == arm and key[1] == e
                    and not r.get("crash"))
            cells.append("%s %d -> %d" % (arm, a, b))
        print("    %-16s %s" % (e, "   ".join(cells)))


def confirmation(argv):
    DA, DB = load(argv[0], bkey), load(argv[1], bkey)
    header(DA, DB, "Confirmation, noise draws 1 to 4")
    draws = sorted({key[4] for key in DA if len(key) > 4})
    print("  draws of the noise: %s; seeds %s" % (draws, sorted({key[3] for key in DA})))
    checks = []
    a = sum(n_structure(DA, k) for k in ("feyn_n1", "feyn_n10"))
    b = sum(n_structure(DB, k) for k in ("feyn_n1", "feyn_n10"))
    checks.append(("B at least A + 10 structures over the %d fits (%d, %d)"
                   % (len(DB), a, b), b >= a + 10))
    for k, nm in (("feyn_n1", "F41N1"), ("feyn_n10", "F41N10")):
        x, y = n_structure(DA, k), n_structure(DB, k)
        checks.append(("%s: B no fewer than A - 3 (%d, %d)" % (nm, x, y), y >= x - 3))
    print("\nCriteria written before the run (PLAN.md, confirmation of N2):")
    for name, ok in checks:
        print("  [%s] %s" % ("holds" if ok else "FAILS", name))
    print("N2 KEPT" if all(ok for _, ok in checks) else "N2 NOT KEPT")
    print("\nBeside: structures by draw of the noise, A -> B:")
    for d in draws:
        cells = []
        for k in ("feyn_n1", "feyn_n10"):
            x = sum(bool(r.get("structure")) for key, r in DA.items()
                    if key[0] == k and key[4] == d)
            y = sum(bool(r.get("structure")) for key, r in DB.items()
                    if key[0] == k and key[4] == d)
            cells.append("%s %d -> %d" % (k, x, y))
        print("    draw %d: %s" % (d, "   ".join(cells)))


if __name__ == "__main__":
    if sys.argv[1] == "--confirmation":
        confirmation(sys.argv[2:])
    else:
        campaign(sys.argv[1:])
