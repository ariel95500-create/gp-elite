"""The reading of Part B of benchmarks/results_1.5/PLAN.md, written before
the first fit.

E(cell) is the number of exact laws of a cell, of 205. For each axis,
between its reference (100 rows; k = 0, the cell of 1,000 rows) and its
largest size (100,000 rows; k = 20):
  the loss at T          L = E(reference, T) - E(largest, T)
  what 10T gives back    R = E(largest, 10T) - E(largest, T)
and the reading:
  L below 10                      size costs little on this axis
  L at least 10, R at least L/2   mostly brute force
  L at least 10, R below L/4      mostly the algorithm
  otherwise                       both

Beside, deciding nothing: E at every size, the near fits, the crashes, the
generations reached, the time to the first generation, the seeds placed,
the formulas that use an added variable, and the fits past their budget
(more than 10 % over their time_limit).

    python compare_size.py records.jsonl
    python compare_size.py --selftest
"""
import json
import statistics
import sys

AXES = {
    "rows": dict(cells=["r100", "r1000", "r10000", "r100000"],
                 reference="r100", largest="r100000", tenfold="r100000_10T"),
    "variables": dict(cells=["r1000", "k5", "k10", "k20"],
                      reference="r1000", largest="k20", tenfold="k20_10T"),
}
ALL_CELLS = ["r100", "r1000", "r10000", "r100000", "r100000_10T",
             "k5", "k10", "k20", "k20_10T"]
THRESHOLD = 10


def reading(L, R):
    if L < THRESHOLD:
        return "size costs little on this axis"
    if R >= L / 2:
        return "mostly brute force"
    if R < L / 4:
        return "mostly the algorithm"
    return "both"


def exact(recs, cell):
    return sum(1 for r in recs if r["cell"] == cell and r.get("status") == "EXACT")


def compare(recs, out=print):
    by = {c: [r for r in recs if r["cell"] == c] for c in ALL_CELLS}
    out("cell          fits  exact  near  crash  med.gen  med.first  elem.seed  tol.seed  uses.added  past.budget")
    for c in ALL_CELLS:
        rs = by[c]
        if not rs:
            out("%-12s     0" % c)
            continue
        ok = [r for r in rs if r.get("status") != "CRASH"]
        med = lambda k: (statistics.median([r[k] for r in ok if r.get(k) is not None])
                         if any(r.get(k) is not None for r in ok) else float("nan"))
        past = sum(1 for r in ok if r.get("time", 0) > 1.1 * r.get("time_limit", 1e9))
        out("%-12s %5d  %5d  %4d  %5d  %7.0f  %9.2f  %9d  %8d  %10d  %11d" % (
            c, len(rs), exact(rs, c),
            sum(1 for r in rs if r.get("status") == "NEAR"),
            sum(1 for r in rs if r.get("status") == "CRASH"),
            med("generations"), med("to_first_gen"),
            sum(1 for r in ok if r.get("elementary_seed")),
            sum(1 for r in ok if r.get("tolerant_seed")),
            sum(1 for r in ok if r.get("uses_added")), past))
    out("")
    verdicts = {}
    for axis, a in AXES.items():
        missing = [c for c in (a["reference"], a["largest"], a["tenfold"])
                   if len(by[c]) != 205]
        if missing:
            out("%s: incomplete (%s), no reading" % (axis, ", ".join(missing)))
            continue
        L = exact(recs, a["reference"]) - exact(recs, a["largest"])
        R = exact(recs, a["tenfold"]) - exact(recs, a["largest"])
        verdicts[axis] = reading(L, R)
        out("%s: E at T %s; L = %d, R = %d: %s" % (
            axis, ", ".join("%s %d" % (c, exact(recs, c)) for c in a["cells"]),
            L, R, verdicts[axis]))
    return verdicts


def selftest():
    """Made-up records, where the answers are known."""
    def recs(e):                        # e: cell -> number of exact fits of 205
        out = []
        for c in ALL_CELLS:
            for n in range(205):
                out.append(dict(cell=c, status="EXACT" if n < e[c] else "MISS",
                                generations=10, to_first_gen=1.0, time=30.0,
                                time_limit=30.0))
        return out
    base = dict(r100=170, r1000=170, r10000=168, r100000=165, r100000_10T=166,
                k5=169, k10=168, k20=162, k20_10T=163)
    cases = [
        (dict(base), dict(rows="size costs little on this axis",
                          variables="size costs little on this axis")),
        (dict(base, r100000=130, r100000_10T=160, k20=120, k20_10T=125),
         dict(rows="mostly brute force", variables="mostly the algorithm")),
        (dict(base, r100000=140, r100000_10T=150, k20=150, k20_10T=170),
         dict(rows="both", variables="mostly brute force")),
        (dict(base, r100000=161, r100000_10T=161, k20=160, k20_10T=170),
         dict(rows="size costs little on this axis",
              variables="mostly brute force")),
        (dict(base, r100000=160, r100000_10T=160, k20=160, k20_10T=162),
         dict(rows="mostly the algorithm", variables="mostly the algorithm")),
    ]
    for e, want in cases:
        got = compare(recs(e), out=lambda *a: None)
        assert got == want, (e, got, want)
    # the bounds: L = 10 is a loss; R = L/2 is brute force; R = L/4 is both
    assert reading(9, 0) == "size costs little on this axis"
    assert reading(10, 5) == "mostly brute force"
    assert reading(12, 3) == "both"
    assert reading(12, 2) == "mostly the algorithm"
    print("selftest: the four cases and the bounds give the known answers")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
    else:
        compare([json.loads(l) for l in open(sys.argv[1]) if l.strip()])
