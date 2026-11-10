"""E1 of PLAN.md in this folder: I.18.12 at 10 % noise, twenty new seeds,
1.2.0 against 1.3.0, read as the plan says.

  python examine.py e1_1.2.0.jsonl e1_1.3.0.jsonl
"""
import json
import sys


def load(path):
    out = {}
    for line in open(path):
        r = json.loads(line)
        out[(r["kind"], r["problem"], r["split"], r["seed"])] = r
    return out


def main(a_path, b_path):
    a, b = load(a_path), load(b_path)
    print("jobs: %d in 1.2.0, %d in 1.3.0, the same: %s; crashes: %d and %d"
          % (len(a), len(b), set(a) == set(b),
             sum(r.get("status") == "CRASH" for r in a.values()),
             sum(r.get("status") == "CRASH" for r in b.values())))
    print("engines: %s" % sorted({r.get("engine_version") for r in a.values()}
                                 | {r.get("engine_version") for r in b.values()}))
    verdict = None
    for kind in ("ufeyn_n10", "feyn_n10"):
        ks = sorted(k for k in a if k[0] == kind)
        sa = sum(bool(a[k].get("structure")) for k in ks)
        sb = sum(bool(b[k].get("structure")) for k in ks)
        print("\n%s, %d seeds (%s to %s): structure retrieved %d with 1.2.0, %d "
              "with 1.3.0" % (kind, len(ks), ks[0][3], ks[-1][3], sa, sb))
        print("  budget reached: %d and %d; median generations: %s and %s" % (
            sum(bool(a[k].get("time_limit_reached")) for k in ks),
            sum(bool(b[k].get("time_limit_reached")) for k in ks),
            sorted(a[k].get("generations") or 0 for k in ks)[len(ks) // 2],
            sorted(b[k].get("generations") or 0 for k in ks)[len(ks) // 2]))
        for v, d in (("1.2.0", a), ("1.3.0", b)):
            miss = [k for k in ks if not d[k].get("structure")]
            print("  %s, the %d fits without the structure, %d with the arcsine:"
                  % (v, len(miss), sum("arcsin" in (d[k].get("expr") or "")
                                       for k in miss)))
            for k in miss:
                print("    seed %d, %s, %s generations: %s" % (
                    k[3], d[k].get("status"), d[k].get("generations"),
                    (d[k].get("expr") or "")[:90]))
        if kind == "ufeyn_n10":
            verdict = sa - sb
    print("\nRead as written before (PLAN.md), on U41N10: 1.3.0 retrieves the "
          "structure in %d fewer fits than 1.2.0, so %s." % (
              verdict, "a loss of 1.3.0 (4 or more)" if verdict >= 4
              else "the draw of the seeds of M2 (3 or fewer)"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
