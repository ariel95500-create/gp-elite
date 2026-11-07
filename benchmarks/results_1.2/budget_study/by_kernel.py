"""The budget study, its records told apart by the kernel of the container.

Written after the run had started, when the container came back from a restart
on another kernel (driver.log): it reads nothing the plan decides on. The
processor stayed the same (lscpu identical at every slice); the kernel of the
container changed twice, and the jobs of a triple (one job at T, 3T and 10T)
can fall on both sides of a change when a restart came between them.

  python by_kernel.py campaign.jsonl

Prints, for each period, the records of each arm, and the triples whose three
records do not all fall in one period; then the criteria of PLAN.md read again
on the triples that ran wholly within one period, beside the criteria on all.
"""
import json
import sys
from collections import defaultdict
from statistics import median

# The restarts that came back on another kernel (driver.log): the first record
# written after each of these times was run on the new kernel.
PERIODS = (
    ("6.18.44-fc-v242", "0000"),
    ("6.18.44-fc-v260", "2026-11-06T21:05:00"),
    ("6.18.44-fc-v310", "2026-11-07T02:52:10"),
)
ARMS = (1, 3, 10)


def period(date):
    name = PERIODS[0][0]
    for n, start in PERIODS:
        if date >= start:
            name = n
    return name


def main(path):
    recs = [json.loads(l) for l in open(path) if l.strip()]
    triples = defaultdict(dict)
    for r in recs:
        triples[(r["kind"], r["problem"], r["split"], r["seed"])][r["budget_factor"]] = r
    count = defaultdict(lambda: defaultdict(int))
    for r in recs:
        count[period(r["date"])][r["budget_factor"]] += 1
    print("Records per kernel and arm:")
    for n, _ in PERIODS:
        print("  %s: %s" % (n, ", ".join("%dT %d" % (a, count[n][a]) for a in ARMS)))
    whole = {k: t for k, t in triples.items()
             if len(t) == 3 and len({period(r["date"]) for r in t.values()}) == 1}
    split = [k for k, t in triples.items() if len(t) == 3 and k not in whole]
    print("Triples complete: %d; within one kernel: %d; across a change: %d"
          % (sum(len(t) == 3 for t in triples.values()), len(whole), len(split)))
    for k in sorted(split):
        print("  across: %s %s %s %s: %s" % (k + (", ".join(
            "%dT %s" % (a, period(triples[k][a]["date"])[-4:]) for a in ARMS),)))

    def crit(ts):
        def n(kind, a, field):
            rs = [t[a] for k, t in ts.items() if k[0] == kind]
            if field == "exact":
                return sum(r.get("status") == "EXACT" for r in rs)
            return sum(bool(r.get("structure")) for r in rs)

        def r2(a):
            v = [t[a]["r2"] for k, t in ts.items() if k[0] == "real" and k[2].startswith("fold")]
            return round(median(v), 4) if v else None
        out = []
        for kind, name, field in (("feyn", "F41", "exact"), ("ufeyn", "U41", "exact"),
                                  ("feyn_n1", "F41N1", "structure"),
                                  ("feyn_n10", "F41N10", "structure")):
            out.append("%s %s %d -> %d (of %d)" % (name, field, n(kind, 1, field),
                                                   n(kind, 10, field),
                                                   sum(k[0] == kind for k in ts)))
        out.append("R6 folds median R² %s -> %s" % (r2(1), r2(10)))
        return out

    full = {k: t for k, t in triples.items() if len(t) == 3}
    print("\nT -> 10T on all complete triples:")
    for line in crit(full):
        print("  " + line)
    print("T -> 10T on the triples within one kernel:")
    for line in crit(whole):
        print("  " + line)


if __name__ == "__main__":
    main(sys.argv[1])
