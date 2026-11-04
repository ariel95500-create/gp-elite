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


UNITS_LIMITED = ("rc", "refroidissement", "lentille")


def units_section(R):
    print("## Prototype 2: under units, the seeds the gate of dimensions sets "
          "aside (units_rejected.jsonl)\n")
    print("%d records, %d crashes\n" % (len(R), sum(r.get("status") == "CRASH" for r in R)))
    tp = [r for r in R if r.get("bench") == "tp"]
    if tp:
        print("TP, units arm (err: 1 - R² on the training rows; a rejected seed "
              "is scored on the rows its finder saw):\n")
        print("| experiment | fits | law | err of the model returned, median | "
              "largest | fits with a rejected seed | best rejected seed, median "
              "err | fits where a rejected seed fits better |")
        print("|---|---|---|---|---|---|---|---|")
        by = collections.defaultdict(list)
        for r in tp:
            by[r["exp"]].append(r)
        for e, L in by.items():
            br = [r["best_rejected_err"] for r in L if r["best_rejected_err"] is not None]
            print("| %s | %d | %d | %.3g | %.3g | %d | %s | %d |" % (
                e, len(L), sum(r["law"] for r in L),
                S.median(r["err_train_returned"] for r in L),
                max(r["err_train_returned"] for r in L),
                sum(r["n_rejected"] > 0 for r in L),
                ("%.3g" % S.median(br)) if br else "-",
                sum(r["best_rejected_err"] is not None
                    and r["best_rejected_err"] < r["err_train_returned"] for r in L)))
        print()
    p1 = [r for r in R if r.get("bench") == "p1" and r.get("status") != "CRASH"]
    if p1:
        print("Decision bench, units kinds (30 s per fit):\n")
        print("| kind | fits | EXACT | NEAR | MISS | fits with a rejected seed | "
              "a rejected seed fits better | ten times better |")
        print("|---|---|---|---|---|---|---|---|")
        for k in ("ufeyn", "ufeyn_n1", "ufeyn_n10"):
            A = [r for r in p1 if r["kind"] == k]
            if not A:
                continue
            W = [r for r in A if r["n_rejected"] > 0]
            print("| %s | %d | %d | %d | %d | %d | %d | %d |" % (
                k, len(A), sum(r["status"] == "EXACT" for r in A),
                sum(r["status"] == "NEAR" for r in A),
                sum(r["status"] == "MISS" for r in A), len(W),
                sum(r["best_rejected_err"] < r["err_train_returned"] for r in W),
                sum(r["best_rejected_err"] < 0.1 * r["err_train_returned"] for r in W)))
        print()


def units_vs_plain_section(U, PT):
    """The comparison a message under units could rest on: the model
    returned under units (prototype 2, 100 generations) against the plain
    fit with the stop on patience (prototype 4), same rows."""
    U = {(r["exp"], r["n"], r["noise"], r["draw"]): r for r in U
         if r.get("bench") == "tp" and r.get("status") != "CRASH"}
    if not U or not any("err_train" in r for r in PT):
        return
    print("## Units arm against the plain arm, same rows (prototypes 2 and 4)\n")
    print("ratio: err under units / err of the plain fit with the stop on "
          "patience (training rows). Groups: within reach under units (the "
          "six laws), limited by units (%s), snell (dimensionless).\n"
          % ", ".join(UNITS_LIMITED))
    for P in sorted({r["patience"] for r in PT}):
        pairs = []
        for r in PT:
            if r["arm"] != "plain" or r["patience"] != P or "err_train" not in r:
                continue
            u = U.get((r["exp"], r["n"], r["noise"], r["draw"]))
            if u is None:
                continue
            g = ("limited" if r["exp"] in UNITS_LIMITED else
                 "snell" if r["exp"] == "snell" else "reach")
            pairs.append((g, r["exp"], u["err_train_returned"],
                          max(r["err_train"], 1e-300), bool(r["law"]), r))
        if not pairs:
            continue
        print("P = %d, %d pairs:\n" % (P, len(pairs)))
        print("| group | fits | ratio, min | 10th pct | median | 90th pct | max |")
        print("|---|---|---|---|---|---|---|")
        for g in ("reach", "limited", "snell"):
            v = sorted(u / p for gg, _e, u, p, _l, _r in pairs if gg == g)
            if v:
                print("| %s | %d | %.3g | %.3g | %.3g | %.3g | %.3g |" % (
                    g, len(v), v[0], q(v, .1), S.median(v), q(v, .9), v[-1]))
        print()
        print("| threshold k (message when ratio >= k) | reach | limited | "
              "snell | limited, plain fit with the law |")
        print("|---|---|---|---|---|")
        for k in (2, 3, 5, 10):
            c = collections.Counter(gg for gg, _e, u, p, _l, _r in pairs if u / p >= k)
            cl = sum(1 for gg, _e, u, p, law, _r in pairs
                     if gg == "limited" and u / p >= k and law)
            print("| %d | %d | %d | %d | %d |" % (k, c["reach"], c["limited"],
                                              c["snell"], cl))
        print()
        print("| experiment | fits | ratio, min | median | max |")
        print("|---|---|---|---|---|")
        by = collections.defaultdict(list)
        for gg, e, u, p, _l, _r in pairs:
            by[e].append(u / p)
        for e, v in by.items():
            print("| %s | %d | %.3g | %.3g | %.3g |" % (e, len(v), min(v),
                                                     S.median(v), max(v)))
        print()


def gaps(errs, eps=0.01, upto=None):
    """Under the rule of patience_try.py, the longest run of generations
    without a gain (error below (1 - eps) times the best) before generation
    `upto`: a stop on patience P cuts the run before `upto` when this is at
    least P."""
    best, best_g, longest = None, 0, 0
    for g, m in enumerate(errs[:upto] if upto is not None else errs):
        if best is None or m < best * (1 - eps):
            best, best_g = m, g
        else:
            longest = max(longest, g - best_g)
    return longest


def plateau_section(R):
    R = [r for r in R if r.get("status") != "CRASH"]
    if not R:
        return
    print("## Prototype 3: the plateaus before the exact laws of F41 "
          "(plateau.jsonl)\n")
    ex = [r for r in R if r["status"] == "EXACT"]
    print("%d fits (30 s and 1,000 generations each), %d EXACT. err: 1 - R² "
          "of the champion in the loop (the error the early stop reads, over "
          "the variance of the target).\n" % (len(R), len(ex)))
    in_loop, after = [], []
    for r in ex:
        e = r["err_by_gen"]
        lg = next((g for g, m in enumerate(e) if m <= 1e-9), None)
        (in_loop if lg is not None else after).append((r, lg))
    print("- the law is the champion in the loop in %d EXACT fits; in %d it "
          "comes only after the loop (polishing and final selection)" % (
              len(in_loop), len(after)))
    if in_loop:
        lgs = [lg for _r, lg in in_loop]
        print("- generation of the law in the loop: median %s, 90th percentile "
              "%s, largest %s" % (S.median(lgs), q(lgs, .9), max(lgs)))
    print("\n| P | EXACT fits whose law, in the loop, comes after a run of P "
          "generations or more without a gain | EXACT fits after the loop "
          "whose loop has such a run |")
    print("|---|---|---|")
    for P in (10, 20, 30, 40):
        a = [r for r, lg in in_loop if gaps(r["err_by_gen"], upto=lg) >= P]
        b = [r for r, _lg in after if gaps(r["err_by_gen"]) >= P]
        print("| %d | %d (%s) | %d |" % (
            P, len(a), ", ".join(sorted({"%s s%d" % (r["problem"], r["seed"])
                                         for r in a}))[:300] or "-", len(b)))
    print()
    print("Replay of the stop on every fit (the error of every generation is "
          "recorded, so the replay is exact up to the loop; what the fit would "
          "return after an earlier stop is not):\n")
    print("| P | fits stopped | generations run when stopped, median "
          "fraction | stopped before the final form: EXACT | NEAR | MISS | "
          "EXACT fits concerned |")
    print("|---|---|---|---|---|---|---|")
    for P in (10, 20, 30, 40):
        stopped, fr, risk, names = 0, [], collections.Counter(), []
        for r in R:
            e = r["err_by_gen"]
            best, bg, s = None, 0, None
            for g, m in enumerate(e):
                if best is None or m < best * 0.99:
                    best, bg = m, g
                elif g - bg >= P:
                    s = g
                    break
            if s is None:
                continue
            stopped += 1
            fr.append(s / len(e))
            if s < r["gen_stable"]:
                risk[r["status"]] += 1
                if r["status"] == "EXACT":
                    names.append("%s s%d" % (r["problem"], r["seed"]))
        print("| %d | %d | %.2f | %d | %d | %d | %s |" % (
            P, stopped, S.median(fr) if fr else 1.0, risk["EXACT"],
            risk["NEAR"], risk["MISS"], ", ".join(names) or "-"))
    print()


def patience_section(PT, TR):
    PT = [r for r in PT if r.get("status") != "CRASH"]
    if not PT:
        return
    base = {(r["arm"], r["exp"], r["n"], r["noise"], r["draw"]): r
            for r in TR if r.get("bench") == "tp"}
    print("## Prototype 4: the stop on patience on the TP fits "
          "(patience.jsonl)\n")
    print("%d records, %d crashes. Baseline: the same fits in prototype 1 "
          "(1.1.0, 100 generations).\n" % (len(PT), 0))
    print("| arm | P | fits | law | useful | reading 10 pts | reading 20 pts | "
          "time, median | baseline time, median | law lost | law gained | "
          "stop generation, median |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")

    def reading(L, n):
        by = collections.defaultdict(int)
        for r in L:
            if r["n"] == n and abs(r["noise"] - 0.02) < 1e-9 and r["law"]:
                by[r["exp"]] += 1
        return sum(v >= 3 for v in by.values())
    for arm in ("plain", "units"):
        B = [r for r in TR if r.get("bench") == "tp" and r["arm"] == arm]
        if B:
            print("| %s | none (1.1.0) | %d | %d | %d | %d | %d | %.1f s | - | - "
                  "| - | - |" % (arm, len(B), sum(r["law"] for r in B),
                                 sum(r["useful"] for r in B), reading(B, 10),
                                 reading(B, 20), S.median(r["time"] for r in B)))
        for P in sorted({r["patience"] for r in PT}):
            A = [r for r in PT if r["arm"] == arm and r["patience"] == P]
            if not A:
                continue
            pb = [base.get((arm, r["exp"], r["n"], r["noise"], r["draw"])) for r in A]
            lost = sum(1 for r, b in zip(A, pb) if b and b["law"] and not r["law"])
            gain = sum(1 for r, b in zip(A, pb) if b and r["law"] and not b["law"])
            sg = [r["stop_gen"] for r in A if r["stop_gen"] is not None]
            print("| %s | %d | %d | %d | %d | %d | %d | %.1f s | %.1f s | %d | %d "
                  "| %s |" % (arm, P, len(A), sum(r["law"] for r in A),
                              sum(r["useful"] for r in A), reading(A, 10),
                              reading(A, 20), S.median(r["time"] for r in A),
                              S.median(b["time"] for b in pb if b),
                              lost, gain, S.median(sg) if sg else "-"))
    print()
    print("Fits where the law is lost or gained against the baseline:\n")
    for P in sorted({r["patience"] for r in PT}):
        for r in PT:
            if r["patience"] != P:
                continue
            b = base.get((r["arm"], r["exp"], r["n"], r["noise"], r["draw"]))
            if b and b["law"] != r["law"]:
                print("- P %d, %s, %s, %d pts, %d %%, draw %d: %s (%s) against "
                      "%s" % (P, r["arm"], r["exp"], r["n"], round(100 * r["noise"]),
                              r["draw"], "law" if r["law"] else "lost",
                              r["expr"][:70], b["expr"][:70]))
    print()


def main():
    TR = load("trace.jsonl")
    trace_section(TR)
    U = load("units_rejected.jsonl")
    units_section(U)
    plateau_section(load("plateau.jsonl"))
    PT = load("patience.jsonl")
    patience_section(PT, TR)
    units_vs_plain_section(U, PT)


if __name__ == "__main__":
    main()
