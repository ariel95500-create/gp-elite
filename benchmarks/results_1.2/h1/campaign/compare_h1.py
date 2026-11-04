"""Campaign H1 of plan 1.2: the six criteria, written in PLAN.md before the
run, on the records of A (the 1.1.0 wheel) and H1 (the candidate).

  python benchmarks/results_1.2/h1/campaign/compare_h1.py [--suffix _conf]

Records: tp_A.jsonl, tp_H1.jsonl (TP, draws 0 to 4), D_A.jsonl, D_H1.jsonl
(bench D, the API defaults). With --suffix the same for the confirmation
(tp_A_conf.jsonl ...), where criteria 1 and 2 are judged on TP, and 3 and 4
on the F41 kinds.
"""
import argparse
import collections
import json
import os
import statistics as S

HERE = os.path.dirname(os.path.abspath(__file__))
LIMITED = ("rc", "refroidissement", "lentille")


def load(name):
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p) if l.strip()]


def reading(L, n):
    by = collections.Counter(r["exp"] for r in L if r["n"] == n
                             and abs(r["noise"] - 0.02) < 1e-9 and r.get("law"))
    return sum(v >= 3 for v in by.values())


def verdict(ok):
    return "HOLDS" if ok else "FAILS"


def tp_part(A, B, results):
    print("## TP diagnostic (%d fits of A, %d of H1)\n" % (len(A), len(B)))
    crash = [r for r in A + B if r.get("crash")]
    print("crashes: %d\n" % len(crash))
    ka = {(r["arm"], r["exp"], r["n"], r["noise"], r["draw"]): r for r in A}
    kb = {(r["arm"], r["exp"], r["n"], r["noise"], r["draw"]): r for r in B}
    print("| arm | engine | fits | median time | law | useful | reading 10 / 20 "
          "points | six laws within reach | generations, median |")
    print("|---|---|---|---|---|---|---|---|---|")
    stats = {}
    for arm in ("plain", "units"):
        for name, D in (("A", ka), ("H1", kb)):
            L = [r for k, r in D.items() if k[0] == arm and not r.get("crash")]
            reach = [r for r in L if r["exp"] not in LIMITED + ("snell",)]
            st = dict(n=len(L), time=S.median(r["time"] for r in L) if L else None,
                      law=sum(r["law"] for r in L), useful=sum(r["useful"] for r in L),
                      r10=reading(L, 10), r20=reading(L, 20),
                      reach=sum(r["law"] for r in reach), nreach=len(reach),
                      gens=S.median(r["generations"] for r in L if "generations" in r)
                      if any("generations" in r for r in L) else None)
            stats[(arm, name)] = st
            print("| %s | %s | %d | %.1f s | %d | %d | %d / %d | %d of %d | %s |" % (
                arm, name, st["n"], st["time"] or 0, st["law"], st["useful"],
                st["r10"], st["r20"], st["reach"], st["nreach"], st["gens"]))
    print()
    c1 = all(stats[(a, "H1")]["time"] <= stats[(a, "A")]["time"] / 3
             for a in ("plain", "units"))
    print("Criterion 1, time (median of H1 at most a third of A's, each arm): "
          "plain %.1f s against %.1f s (ratio %.2f), units %.1f s against %.1f s "
          "(ratio %.2f): %s" % (
              stats[("plain", "H1")]["time"], stats[("plain", "A")]["time"],
              stats[("plain", "H1")]["time"] / stats[("plain", "A")]["time"],
              stats[("units", "H1")]["time"], stats[("units", "A")]["time"],
              stats[("units", "H1")]["time"] / stats[("units", "A")]["time"],
              verdict(c1)))
    pa, pb = stats[("plain", "A")], stats[("plain", "H1")]
    ua, ub = stats[("units", "A")], stats[("units", "H1")]
    c2a = pb["law"] >= pa["law"] - 2 and pb["r10"] >= pa["r10"] and pb["r20"] >= pa["r20"]
    c2b = ub["reach"] >= 118
    c2c = pb["useful"] >= pa["useful"] - 3 and ub["useful"] >= ua["useful"] - 3
    print("Criterion 2, the law on TP:")
    print("- plain: law %d against %d (at least %d), reading %d/%d against %d/%d: %s"
          % (pb["law"], pa["law"], pa["law"] - 2, pb["r10"], pb["r20"], pa["r10"],
             pa["r20"], verdict(c2a)))
    print("- units: the six laws within reach in %d of %d (at least 118): %s"
          % (ub["reach"], ub["nreach"], verdict(c2b)))
    print("- useful: plain %d against %d, units %d against %d (at least A's "
          "minus 3): %s" % (pb["useful"], pa["useful"], ub["useful"], ua["useful"],
                            verdict(c2c)))
    results.update(c1=c1, c2=c2a and c2b and c2c)
    print("\nReading per experiment: fits with the law at 2 % noise, of the "
          "draws, at 10 and 20 points (the reading counts an experiment "
          "when 3 draws or more give the law):\n")
    print("| arm | experiment | A, 10 pts | H1, 10 pts | A, 20 pts | H1, 20 pts |")
    print("|---|---|---|---|---|---|")
    for arm in ("plain", "units"):
        exps = sorted({k[1] for k in ka if k[0] == arm})
        for e in exps:
            cell = []
            for n in (10, 20):
                for D in (ka, kb):
                    L = [r for k, r in D.items() if k[0] == arm and k[1] == e
                         and k[2] == n and abs(k[3] - 0.02) < 1e-9]
                    cell.append("%d of %d" % (sum(bool(r.get("law")) for r in L),
                                              len(L)))
            print("| %s | %s | %s | %s | %s | %s |" % ((arm, e) + tuple(cell)))
    print("\nFits where A and H1 differ on the law:\n")
    for k in sorted(set(ka) & set(kb)):
        a, b = ka[k], kb[k]
        if a.get("law") != b.get("law"):
            print("- %s, %s, %d pts, %d %%, draw %d: H1 %s (%s) | A %s (%s)" % (
                k[0], k[1], k[2], round(100 * k[3]), k[4],
                "law" if b["law"] else "lost", b["expr"][:60],
                "law" if a["law"] else "no law", a["expr"][:60]))
    print()


def d_part(A, B, results, feyn_only=False):
    print("## Bench D, the API defaults (%d fits of A, %d of H1)\n" % (len(A), len(B)))
    key = lambda r: (r["kind"], r["problem"], r["split"], r["seed"])
    ka, kb = {key(r): r for r in A}, {key(r): r for r in B}
    crash = [r for r in A + B if r.get("status") == "CRASH"]
    print("crashes: A %d, H1 %d\n" % (sum(r.get("status") == "CRASH" for r in A),
                                      sum(r.get("status") == "CRASH" for r in B)))
    kinds = ["feyn", "feyn_n1", "feyn_n10", "ufeyn", "ufeyn_n1", "ufeyn_n10",
             "real", "realraw"]
    print("| kind | engine | fits | exact | structure | median time | max time "
          "| generations, median | size, median |")
    print("|---|---|---|---|---|---|---|---|---|")
    cnt = {}
    for kind in kinds:
        for name, D in (("A", ka), ("H1", kb)):
            L = [r for k, r in D.items() if k[0] == kind]
            if not L:
                continue
            ex = sum(r.get("status") == "EXACT" for r in L)
            st = sum(bool(r.get("structure")) for r in L)
            cnt[(kind, name)] = dict(exact=ex, structure=st)
            t = [r["time"] for r in L if "time" in r]
            print("| %s | %s | %d | %d | %s | %.1f s | %.1f s | %s | %s |" % (
                kind, name, len(L), ex, st if kind.endswith(("n1", "n10")) else "-",
                S.median(t) if t else 0, max(t) if t else 0,
                S.median(r["generations"] for r in L if "generations" in r),
                S.median(r["size"] for r in L if "size" in r)))
    print()
    print("Statuses on the Feynman kinds (beside the criteria):\n")
    print("| kind | engine | EXACT | NEAR | MISS |")
    print("|---|---|---|---|---|")
    for kind in kinds:
        if kind.startswith("real"):
            continue
        for name, D in (("A", ka), ("H1", kb)):
            c = collections.Counter(r.get("status") for k, r in D.items()
                                    if k[0] == kind)
            if c:
                print("| %s | %s | %d | %d | %d |" % (kind, name, c["EXACT"],
                                                      c["NEAR"], c["MISS"]))
    print()
    ok3 = True
    for kind in (("feyn",) if feyn_only else ("feyn", "ufeyn")):
        a, b = cnt.get((kind, "A")), cnt.get((kind, "H1"))
        if not a or not b:
            continue
        per = collections.defaultdict(lambda: [0, 0])
        for k in set(ka) & set(kb):
            if k[0] == kind:
                per[k[1]][0] += ka[k].get("status") == "EXACT"
                per[k[1]][1] += kb[k].get("status") == "EXACT"
        falls = [(p, x, y) for p, (x, y) in per.items() if x >= 3 and y <= 1]
        ok = b["exact"] >= a["exact"] - 3 and not falls
        ok3 &= ok
        print("Criterion 3, %s: exact %d against %d (at least %d); equations exact "
              "in A at 3 seeds or more that fall to one or none: %s: %s" % (
                  kind, b["exact"], a["exact"], a["exact"] - 3,
                  ", ".join("%s (%d -> %d)" % f for f in falls) or "none", verdict(ok)))
        changed = [(p, x, y) for p, (x, y) in sorted(per.items()) if x != y]
        print("  equations whose exact seeds change: %s" % (
            ", ".join("%s %d -> %d" % c for c in changed) or "none"))
    ok4 = True
    for kind in (("feyn_n1", "feyn_n10") if feyn_only else
                 ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10")):
        a, b = cnt.get((kind, "A")), cnt.get((kind, "H1"))
        if not a or not b:
            continue
        ok = b["structure"] >= a["structure"] - 3
        ok4 &= ok
        print("Criterion 4, %s: structure %d against %d (at least %d): %s" % (
            kind, b["structure"], a["structure"], a["structure"] - 3, verdict(ok)))
    results.update(c3=ok3, c4=ok4)
    if feyn_only:
        return
    fa = [r["r2"] for k, r in ka.items() if k[0] == "real" and k[2].startswith("fold")]
    fb = [r["r2"] for k, r in kb.items() if k[0] == "real" and k[2].startswith("fold")]
    ca = sum(1 for k, r in ka.items() if k[0] in ("real", "realraw") and k[2] == "ood"
             and r["r2"] < 0)
    cb = sum(1 for k, r in kb.items() if k[0] in ("real", "realraw") and k[2] == "ood"
             and r["r2"] < 0)
    ok5 = bool(fa and fb) and S.median(fb) >= S.median(fa) - 0.01 and cb <= ca + 2
    print("Criterion 5, real data: median test R² of the R6 folds %.4f against "
          "%.4f; collapses out of domain (R² < 0, R6 and R7raw) %d against %d: %s"
          % (S.median(fb) if fb else float("nan"), S.median(fa) if fa else float("nan"),
             cb, ca, verdict(ok5)))
    U = [r for k, r in kb.items() if k[0].startswith("ufeyn")]
    bad = [r for r in U if not r.get("units_ok")]
    ok6 = bool(U) and not bad
    print("Criterion 6, the units guarantee: %d of %d models under units pass "
          "check_dimensions: %s" % (len(U) - len(bad), len(U), verdict(ok6)))
    results.update(c5=ok5, c6=ok6)
    print("\nFits of D where the status or the structure differs:\n")
    n = 0
    for k in sorted(set(ka) & set(kb)):
        a, b = ka[k], kb[k]
        if (a.get("status"), a.get("structure")) != (b.get("status"), b.get("structure")):
            n += 1
            print("- %s %s %s seed %d: A %s%s, H1 %s%s" % (
                k[0], k[1], k[2], k[3], a.get("status"),
                "/structure" if a.get("structure") else "", b.get("status"),
                "/structure" if b.get("structure") else ""))
    print("(%d fits)\n" % n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suffix", default="")
    a = ap.parse_args()
    sfx = a.suffix
    results = {}
    tp_part(load("tp_A%s.jsonl" % sfx), load("tp_H1%s.jsonl" % sfx), results)
    DA, DB = load("D_A%s.jsonl" % sfx), load("D_H1%s.jsonl" % sfx)
    if DA and DB:
        d_part(DA, DB, results, feyn_only=bool(sfx))
    print("## Verdict\n")
    for k in sorted(results):
        print("- criterion %s: %s" % (k[1:], verdict(results[k])))
    need = ("c1", "c2", "c3", "c4") if sfx else ("c1", "c2", "c3", "c4", "c5", "c6")
    if all(k in results for k in need):
        print("\nH1 %s" % ("ADOPTED: every criterion holds" if all(results[k] for k in need)
                           else "NOT ADOPTED"))
    else:
        print("\n(records incomplete: no verdict)")


if __name__ == "__main__":
    main()
