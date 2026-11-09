"""Campaign A3 (benchmarks/results_1.3/PLAN.md, change A3): the six criteria
of A2, unchanged, read from the paired records of 1.2.0 (A) and the
candidate with A1, A2 and A3 (B). The readings are those of compare_a2.py,
with, beside, the fits where the arcsine seed was placed.

  python compare_a1.py Dtrig_A.jsonl Dtrig_B.jsonl TPsnell_A.jsonl TPsnell_B.jsonl
  python compare_a1.py --confirmation Dtrig_A_conf.jsonl Dtrig_B_conf.jsonl \
         TPsnell_A_conf.jsonl TPsnell_B_conf.jsonl

The confirmation (seeds 5 to 9, draws 5 to 9) reads criteria 1 to 4 without
the parts under units: Dtrig's kinds feyn, feyn_n1 and feyn_n10 only.
"""
import json
import sys
from collections import Counter
from statistics import median

TRIG = ["II.15.4", "I.18.12", "III.15.12", "I.26.2", "I.30.5", "I.37.4",
        "I.50.26", "II.6.15b", "III.9.52", "III.17.37"]
ARCSIN = ["I.26.2", "I.30.5"]
OTHER = [p for p in TRIG if p not in ARCSIN]


def load(path, key):
    out = {}
    for line in open(path):
        if line.strip():
            r = json.loads(line)
            out[key(r)] = r
    return out


def dkey(r):
    return (r["kind"], r["problem"], r["seed"])


def tkey(r):
    return (r["arm"], r["exp"], r["n"], r["noise"], r["draw"])


def exact(r):
    return r.get("status") == "EXACT"


def has_arcsin(r):
    return "arcsin" in (r.get("expr") or "")


def main(argv):
    conf = argv[0] == "--confirmation"
    if conf:
        argv = argv[1:]
    DA, DB = load(argv[0], dkey), load(argv[1], dkey)
    TA, TB = load(argv[2], tkey), load(argv[3], tkey)
    print("Dtrig: %d fits in A, %d in B, the same jobs: %s; crashes A %d, B %d"
          % (len(DA), len(DB), set(DA) == set(DB),
             sum(r.get("status") == "CRASH" for r in DA.values()),
             sum(r.get("status") == "CRASH" for r in DB.values())))
    print("TPsnell: %d fits in A, %d in B, the same jobs: %s; crashes A %d, B %d"
          % (len(TA), len(TB), set(TA) == set(TB),
             sum(bool(r.get("crash")) for r in TA.values()),
             sum(bool(r.get("crash")) for r in TB.values())))
    print("Engines: A %s; B %s" % (
        sorted({r.get("engine_file") for r in list(DA.values()) + list(TA.values())}),
        sorted({r.get("engine_file") for r in list(DB.values()) + list(TB.values())})))

    def sel(D, kind, probs):
        return [r for k, r in D.items() if k[0] == kind and k[1] in probs]

    def count(D, kind, probs, field):
        rs = sel(D, kind, probs)
        if field == "exact":
            return sum(exact(r) for r in rs)
        return sum(bool(r.get("structure")) for r in rs)

    def per_eq(D, kind, field):
        c = Counter()
        for r in sel(D, kind, TRIG):
            c[r["problem"]] += exact(r) if field == "exact" else bool(r.get("structure"))
        return c

    # the table of the kinds
    kinds = [("feyn", "F41", "exact"), ("feyn_n1", "F41N1", "structure"),
             ("feyn_n10", "F41N10", "structure")]
    if not conf:
        kinds.insert(1, ("ufeyn", "U41", "exact"))
    print("\n| kind | A, ten equations | B | A, the two arcsine laws | B |")
    print("|---|---|---|---|---|")
    for kind, name, field in kinds:
        print("| %s | %d | %d | %d | %d |" % (
            name, count(DA, kind, TRIG, field), count(DB, kind, TRIG, field),
            count(DA, kind, ARCSIN, field), count(DB, kind, ARCSIN, field)))
    print("\nPer equation, %s:" % ", ".join(n for _, n, _ in kinds))
    for p in TRIG:
        print("  %-10s %s" % (p, "  ".join(
            "%s %d -> %d" % (n, per_eq(DA, k, f)[p], per_eq(DB, k, f)[p])
            for k, n, f in kinds)))

    # the exact fits of the arcsine laws, and whether they write the arcsine
    print("\nThe fits of the arcsine laws in B (F41%s):" % ("" if conf else ", U41"))
    for kind in (("feyn",) if conf else ("feyn", "ufeyn")):
        for r in sorted(sel(DB, kind, ARCSIN), key=lambda r: (r["problem"], r["seed"])):
            print("  %s %s seed %d: %s, arcsine in the formula %s, 1 - R² %.3g: %s"
                  % (kind, r["problem"], r["seed"], r.get("status"), has_arcsin(r),
                     r.get("err", float("nan")), (r.get("expr") or "")[:110]))

    # TP
    def tp(D, arm=None):
        return [r for k, r in D.items() if k[1] == "snell" and (arm is None or k[0] == arm)
                and not r.get("crash")]
    print("\nTPsnell: | arm | law A | law B | useful A | useful B | median time A | B |")
    for arm in ("plain", "units"):
        a, b = tp(TA, arm), tp(TB, arm)
        print("  | %s | %d | %d | %d | %d | %.1f s | %.1f s |" % (
            arm, sum(r["law"] for r in a), sum(r["law"] for r in b),
            sum(r["useful"] for r in a), sum(r["useful"] for r in b),
            median(r["time"] for r in a), median(r["time"] for r in b)))
    for r in sorted(tp(TB), key=lambda r: (r["arm"], r["n"], r["noise"], r["draw"])):
        if r["law"]:
            print("  B law: %s %d points %d %% draw %d: %s" % (
                r["arm"], r["n"], round(100 * r["noise"]), r["draw"], r["expr"][:100]))

    # the criteria of change A2, which A3 keeps
    checks = []
    a1 = sum(exact(r) and has_arcsin(r) for r in sel(DB, "feyn", ARCSIN))
    checks.append(("1. the arcsine laws on F41: at least 5 of 10 exact with a formula "
                   "that writes the arcsine, in B (%d; exact in all %d)"
                   % (a1, count(DB, "feyn", ARCSIN, "exact")), a1 >= 5))
    for kind, name in (("feyn", "F41"),) + ((("ufeyn", "U41"),) if not conf else ()):
        a, b = count(DA, kind, OTHER, "exact"), count(DB, kind, OTHER, "exact")
        checks.append(("2. %s, the eight other equations: B no fewer than A - 2 (%d, %d)"
                       % (name, a, b), b >= a - 2))
        pa, pb = per_eq(DA, kind, "exact"), per_eq(DB, kind, "exact")
        fell = [p for p in OTHER if pa[p] >= 3 and pb[p] <= 1]
        checks.append(("2. %s: no equation from three seeds or more to one or none (%s)"
                       % (name, fell or "none"), not fell))
    for kind, name in (("feyn_n1", "F41N1"), ("feyn_n10", "F41N10")):
        a, b = count(DA, kind, TRIG, "structure"), count(DB, kind, TRIG, "structure")
        checks.append(("3. %s: B no fewer than A - 2 (%d, %d)" % (name, a, b), b >= a - 2))
    for arm in ("plain", "units"):
        a, b = sum(r["useful"] for r in tp(TA, arm)), sum(r["useful"] for r in tp(TB, arm))
        checks.append(("4. Snell's law on TP within 1 %%, %s: B no fewer than A - 2 "
                       "(%d, %d)" % (arm, a, b), b >= a - 2))
    if not conf:
        u = sel(DB, "ufeyn", TRIG) + tp(TB, "units")
        bad = [r for r in u if not r.get("units_ok")]
        checks.append(("5. the units guarantee: every model under units of B passes "
                       "(%d of %d)" % (len(u) - len(bad), len(u)), not bad))
        for arm in ("plain", "units"):
            ta = median(r["time"] for r in tp(TA, arm))
            tb = median(r["time"] for r in tp(TB, arm))
            checks.append(("6. time on TP, %s: B at most 1.5 times A (%.1f s, %.1f s, "
                           "ratio %.2f)" % (arm, ta, tb, tb / ta), tb <= 1.5 * ta))
    print("\nCriteria of change A2, kept for A3, written before the run (PLAN.md)%s:"
          % (", confirmation" if conf else ""))
    for name, ok in checks:
        print("  [%s] %s" % ("holds" if ok else "FAILS", name))
    allok = all(ok for _, ok in checks)
    print(("A3 KEPT" if allok else "A3 NOT KEPT") if conf else
          ("A3 ADOPTED" if allok else "A3 NOT ADOPTED"))

    # beside, deciding nothing
    print("\nBeside, deciding nothing:")
    if not conf:
        print("  the arcsine laws under units: A %d, B %d of 10; in B, writing the "
              "arcsine: %d" % (count(DA, "ufeyn", ARCSIN, "exact"),
                               count(DB, "ufeyn", ARCSIN, "exact"),
                               sum(exact(r) and has_arcsin(r) for r in sel(DB, "ufeyn", ARCSIN))))
    print("  Snell's law on TP by the diagnostic's test: A %d, B %d of %d; formulas of B "
          "with the arcsine %d" % (sum(r["law"] for r in tp(TA)), sum(r["law"] for r in tp(TB)),
                                   len(tp(TB)), sum(has_arcsin(r) for r in tp(TB))))
    for D, n in ((DA, "A"), (DB, "B")):
        rs = list(D.values())
        print("  %s: median size %s; formula_exact False in %d of %d; formulas with the "
              "arcsine %d (formula_exact False among them %d); median time %.1f s"
              % (n, median(r["size"] for r in rs if "size" in r),
                 sum(r.get("formula_exact") is False for r in rs), len(rs),
                 sum(has_arcsin(r) for r in rs),
                 sum(has_arcsin(r) and r.get("formula_exact") is False for r in rs),
                 median(r["time"] for r in rs if "time" in r)))
    seeded = Counter(k[0] for k, r in DB.items()
                     if "arcsin" in (r.get("elementary_seed") or "")
                     or "arcsin" in (r.get("tolerant_seed") or ""))
    print("  fits of B where an arcsine seed was placed, by kind: %s"
          % (dict(sorted(seeded.items())) or "none"))
    for k, r in sorted(DB.items()):
        s = r.get("elementary_seed") or r.get("tolerant_seed") or ""
        if "arcsin" in s:
            print("    %s %s seed %d: %s -> %s" % (k[0], k[1], k[2], s[:70], r.get("status")))
    changed = [(k, DA[k].get("status"), DB[k].get("status")) for k in sorted(DA)
               if k in DB and DA[k].get("status") != DB[k].get("status")]
    print("  fits of Dtrig whose status changes: %d" % len(changed))
    for k, a, b in changed:
        print("    %s %s seed %d: %s -> %s" % (k[0], k[1], k[2], a, b))


if __name__ == "__main__":
    main(sys.argv[1:])
