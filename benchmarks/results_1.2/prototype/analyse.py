"""Figures of the prototypes of plan 1.2, from their records (decides
nothing). Output: analysis.txt.

  python benchmarks/results_1.2/prototype/analyse.py > analysis.txt
"""
import collections
import json
import os
import statistics as S

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p) if l.strip()]


def q(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(p * len(v)))] if v else None


def replay(changes, n_gens, P, eps):
    """Replay a stop on patience on the champion's error recorded at each
    change of its form: the generation the loop would end at, and the
    champion it would hold then. A gain is an error below (1 - eps) times
    the best so far. Changes of the constants alone are not in the record,
    so the replay is approximate."""
    best = None
    last = 0
    cur = None
    for g, t, s, m in changes:
        if best is None or m < best * (1 - eps):
            if best is not None and g - last > P:
                return last + P, cur
            best, last, cur = m, g, (g, t, s, m)
    return min(last + P, n_gens - 1), cur


def trace_section(R):
    print("## Prototype 1: when the champion reaches its final form "
          "(trace.jsonl)\n")
    print("%d records, %d crashes\n" % (len(R), sum(r.get("status") == "CRASH" for r in R)))
    tp = [r for r in R if r["bench"] == "tp"]
    for arm in ("plain", "units"):
        A = [r for r in tp if r["arm"] == arm]
        if not A:
            continue
        print("TP, %s arm, %d fits, 100 generations each:" % (arm, len(A)))
        print("- the first generation's champion has the final form in %d"
              % sum(r["gen0_is_final"] for r in A))
        print("- generation from which the form is final: median %s, 90th "
              "percentile %s, largest %s" % (S.median(r["gen_stable"] for r in A),
                                             q([r["gen_stable"] for r in A], .9),
                                             max(r["gen_stable"] for r in A)))
        print("- time of the fit: median %.1f s; the final form is there at a "
              "median of %.1f s" % (S.median(r["time"] for r in A),
                                    S.median(r["t_stable"] for r in A)))
        print("\n| experiment | fits | law | gen. of final form (5 largest) | time, median | final form at, median |")
        print("|---|---|---|---|---|---|")
        by = collections.defaultdict(list)
        for r in A:
            by[r["exp"]].append(r)
        for e, L in by.items():
            gs = sorted(r["gen_stable"] for r in L)
            print("| %s | %d | %d | %s | %.0f s | %.1f s |" % (
                e, len(L), sum(r["law"] for r in L), ", ".join(map(str, gs[-5:])),
                S.median(r["time"] for r in L), S.median(r["t_stable"] for r in L)))
        print()
    print("Replay of a stop on patience on the TP traces (error gain of more "
          "than 1 %, approximate):\n")
    print("| P | generations run, median fraction | fits where a later gain "
          "of error is cut | of which the final model has the law |")
    print("|---|---|---|---|")
    for P in (10, 20, 30):
        frac, cut, cut_law = [], 0, 0
        for r in tp:
            stop, cur = replay(r["changes"], r["n_gens"], P, 0.01)
            frac.append((stop + 1) / r["n_gens"])
            later = [c for c in r["changes"] if c[0] > stop and c[3] < cur[3] * 0.99]
            if later:
                cut += 1
                cut_law += bool(r["law"])
        print("| %d | %.2f | %d | %d |" % (P, S.median(frac), cut, cut_law))
    print()
    p1 = [r for r in R if r["bench"] == "p1" and r.get("status") != "CRASH"]
    if p1:
        print("Decision bench kinds (30 s and 1,000 generations per fit):\n")
        print("| kind | fits | generations run, median | time limit reached | "
              "gen. of final form, median | 90th pct | final form at, median "
              "fraction of the generations run |")
        print("|---|---|---|---|---|---|---|")
        for k in ("feyn_n1", "feyn_n10", "real", "realraw"):
            A = [r for r in p1 if r["kind"] == k]
            if not A:
                continue
            print("| %s | %d | %s | %d | %s | %s | %.2f |" % (
                k, len(A), S.median(r["n_gens"] for r in A),
                sum(bool(r.get("time_limit_reached")) for r in A),
                S.median(r["gen_stable"] for r in A),
                q([r["gen_stable"] for r in A], .9),
                S.median(r["gen_stable"] / max(r["n_gens"], 1) for r in A)))
        print()
        print("Replay of a stop on patience on these traces (as above; "
              "structure: the structure retrieved at the end of the fit):\n")
        print("| P | kind | generations run, median fraction | fits where a "
              "later gain is cut | of which with the structure retrieved |")
        print("|---|---|---|---|---|")
        for P in (10, 20, 30):
            for k in ("feyn_n1", "feyn_n10", "real", "realraw"):
                A = [r for r in p1 if r["kind"] == k]
                if not A:
                    continue
                frac, cut, cut_s = [], 0, 0
                for r in A:
                    stop, cur = replay(r["changes"], r["n_gens"], P, 0.01)
                    frac.append(min(1.0, (stop + 1) / r["n_gens"]))
                    if [c for c in r["changes"] if c[0] > stop and c[3] < cur[3] * 0.99]:
                        cut += 1
                        cut_s += bool(r.get("structure"))
                print("| %d | %s | %.2f | %d | %s |" % (
                    P, k, S.median(frac), cut,
                    cut_s if k.startswith("feyn") else "-"))
        print()


def main():
    trace_section(load("trace.jsonl"))


if __name__ == "__main__":
    main()
