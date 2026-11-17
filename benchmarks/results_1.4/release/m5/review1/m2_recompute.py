"""M5 review 1 (read-only): the figures of the M2 of 1.4.0 recomputed from
its records, by code written for this review (it does not import the
comparison scripts of the release), to check m2/compare.txt,
m2/limits_figures.txt and the documents that quote them.

  python3 -I m2_recompute.py benchmarks/results_1.4/release/m2

Standard library only (no NumPy): medians by statistics.median, which for
an even count averages the two middle values as np.median does.
"""
import json
import os
import sys
from collections import Counter, defaultdict
from statistics import median


def load(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out[(r["kind"], r["problem"], r["split"], r["seed"])] = r
    return out


def tload(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out[(r["arm"], r["exp"], r["n"], r["noise"], r["draw"])] = r
    return out


def seeds_of(r):
    """The forms of the recorded tolerant_seed, without their scores."""
    s = r.get("tolerant_seed")
    if not s:
        return []
    out = []
    for part in s.split(" | "):
        part = part.strip()
        if part.endswith(")") and " (" in part:
            part = part[:part.rfind(" (")]
        out.append(part)
    return out


def ind(D, tag):
    rr = list(D.values())
    sel = lambda k, p=lambda s: True: [r for r in rr if r["kind"] == k and p(r["split"])]
    folds = lambda s: s.startswith("fold")
    exact = lambda k: sum(r.get("status") == "EXACT" for r in sel(k))
    struct = lambda k: sum(bool(r.get("structure")) for r in sel(k))
    print("[%s]" % tag)
    print("  fits %d, kinds %s" % (len(rr), dict(sorted(Counter(r["kind"] for r in rr).items()))))
    print("  F41 exact %d; F41N1 %d; F41N10 %d; U41 exact %d; U41N1 %d; U41N10 %d"
          % (exact("feyn"), struct("feyn_n1"), struct("feyn_n10"), exact("ufeyn"),
             struct("ufeyn_n1"), struct("ufeyn_n10")))
    print("  TF78 exact %d; TF78 under units exact %d; TS14 exact on test %d (of %d)"
          % (exact("tf"), exact("utf"),
             sum(r.get("status") == "EXACT" for r in sel("ts", lambda s: s == "test")),
             len(sel("ts", lambda s: s == "test"))))
    print("  TF78N1 %d, TF78N10 %d, under units %d, %d (of %d each)"
          % (struct("tf_n1"), struct("tf_n10"), struct("utf_n1"), struct("utf_n10"),
             len(sel("tf_n1"))))
    for k, name in (("real", "R6"), ("realraw", "R7raw"), ("tr", "TR25"), ("trraw", "TR25raw")):
        f = [r["r2"] for r in sel(k, folds)]
        o = [r["r2"] for r in sel(k, lambda s: s == "ood")]
        print("  %s: folds %d median R2 %.4f; ood %d, collapses %d, worst %.6g"
              % (name, len(f), median(f), len(o), sum(x < 0 for x in o), min(o)))
    units_kinds = ("ufeyn", "ufeyn_n1", "ufeyn_n10", "utf", "utf_n1", "utf_n10")
    u = [r for r in rr if r["kind"] in units_kinds]
    print("  under units: %d fits, units_ok True %d" % (len(u), sum(r.get("units_ok") is True for r in u)))
    print("  utf seeds %s" % sorted({r["seed"] for r in sel("utf")}))
    # figures of the pages of the limits
    for k, name in (("feyn", "F41"), ("ufeyn", "U41"), ("tf", "TF78")):
        pe = defaultdict(int)
        for r in sel(k):
            pe[r["problem"]] += r.get("status") == "EXACT"
        never = sorted(p for p, c in pe.items() if c == 0)
        once = sorted(p for p, c in pe.items() if c == 1)
        print("  %s: %d equations, never exact %d %s; exact once %d %s"
              % (name, len(pe), len(never), never if len(never) < 8 else "",
                 len(once), once if len(once) < 8 else ""))
    fam = Counter((r.get("family"), r.get("status") == "EXACT") for r in sel("tf"))
    print("  TF78 by family (family, exact): %s" % dict(sorted(fam.items(), key=str)))
    fe130 = sum(r.get("formula_exact") is False for r in rr if r["kind"] in ("real", "realraw"))
    fe500 = sum(r.get("formula_exact") is False for r in rr if r["kind"] in ("tr", "trraw"))
    n130 = sum(1 for r in rr if r["kind"] in ("real", "realraw"))
    n500 = sum(1 for r in rr if r["kind"] in ("tr", "trraw"))
    print("  formula_exact False: real data of the bench %d of %d; test set %d of %d"
          % (fe130, n130, fe500, n500))
    for k in ("tr", "trraw"):
        c = Counter(r["problem"] for r in sel(k, lambda s: s == "ood") if r["r2"] < 0)
        top6 = sum(v for _, v in c.most_common(6))
        print("  %s: collapses on the six datasets with most: %d (of %d)" % (k, top6, sum(c.values())))
    # time of the fits stopped by their budget
    t = sorted(r["time"] for r in rr if r.get("time_limit_reached"))
    print("  fits at their time budget: %d, time median %.2f s, max %.2f s, min %.2f s"
          % (len(t), median(t), t[-1], t[0]))
    tall = sorted(r["time"] for r in rr)
    print("  every fit: median %.2f s, max %.2f s" % (median(tall), tall[-1]))


def main(folder):
    a = load(os.path.join(folder, "campaignR_1.3.0.jsonl"))
    b = load(os.path.join(folder, "campaignR_1.4.0.jsonl"))
    print("same jobs: %s; %d and %d" % (set(a) == set(b), len(a), len(b)))
    ind(a, "1.3.0")
    ind(b, "1.4.0")

    common = sorted(set(a) & set(b))
    same = [k for k in common if (a[k].get("tolerant_seed") or None) == (b[k].get("tolerant_seed") or None)]
    none_same = [k for k in same if not a[k].get("tolerant_seed")]
    det = [k for k in same if not a[k].get("time_limit_reached") and not b[k].get("time_limit_reached")]
    none_det = [k for k in det if not a[k].get("tolerant_seed")]
    diff = [k for k in det if a[k].get("expr") != b[k].get("expr") or a[k].get("err") != b[k].get("err")
            or a[k].get("formula_exact") != b[k].get("formula_exact")]
    same_expr_same_seeds = sum(a[k].get("expr") == b[k].get("expr") for k in same)
    print("\nwhere 1.4 does not act: same tolerant seeds %d of %d (none in both: %d); "
          "no budget reached %d (none in both: %d); differ %d"
          % (len(same), len(common), len(none_same), len(det), len(none_det), len(diff)))
    print("  among the %d with the same seeds, the same recorded formula in %d; "
          "the same formula over all fits %d"
          % (len(same), same_expr_same_seeds, sum(a[k].get("expr") == b[k].get("expr") for k in common)))
    by_kind = Counter(k[0] for k in same if a[k].get("expr") != b[k].get("expr"))
    print("  same seeds but another formula, by kind: %s" % dict(sorted(by_kind.items())))
    st = Counter(k[0] for k in same if a[k].get("status") != b[k].get("status")
                 or bool(a[k].get("structure")) != bool(b[k].get("structure")))
    print("  same seeds but another status or structure, by kind: %s" % dict(sorted(st.items())))

    # every seed of 1.3.0 still placed; the number of seeds
    lost, dup13, n14 = [], 0, Counter()
    nmax13, nmax14 = 0, 0
    for k in common:
        sa, sb = seeds_of(a[k]), seeds_of(b[k])
        if len(set(sa)) != len(sa):
            dup13 += 1
        if not set(sa) <= set(sb):
            lost.append((k, sorted(set(sa) - set(sb))[:2]))
        nmax13, nmax14 = max(nmax13, len(sa)), max(nmax14, len(sb))
        n14[len(sb)] += 1
    print("\nseeds: fits where a seed of 1.3.0 is not among those of 1.4.0: %d; "
          "fits where 1.3.0 placed one form twice: %d; most seeds in a fit: 1.3.0 %d, 1.4.0 %d"
          % (len(lost), dup13, nmax13, nmax14))
    for x in lost[:8]:
        print("   ", x)
    print("  1.4.0, number of seeds per fit: %s" % dict(sorted(n14.items())))
    tol = Counter((k[0], bool(a[k].get("tolerant_seed")), bool(b[k].get("tolerant_seed"))) for k in common)
    print("  (kind, seeds in 1.3.0, seeds in 1.4.0): %s" % {x: v for x, v in sorted(tol.items()) if x[1] or x[2]})

    # structures by equation
    print("\nstructures by equation where they differ (F41N1, F41N10, U41N1, U41N10):")
    pe = lambda D, kind: Counter(k[1] for k, r in D.items() if k[0] == kind and r.get("structure"))
    for p in sorted({k[1] for k in a if k[0] == "feyn_n1"}):
        cells = [(pe(a, kd)[p], pe(b, kd)[p]) for kd in ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10")]
        if any(x != y for x, y in cells):
            print("   %-10s %s" % (p, "  ".join("%d -> %d" % c for c in cells)))
    print("TF78N structures by equation where they differ (tf_n1, tf_n10, utf_n1, utf_n10):")
    for p in sorted({k[1] for k in a if k[0] == "tf_n1"}):
        cells = [(pe(a, kd)[p], pe(b, kd)[p]) for kd in ("tf_n1", "tf_n10", "utf_n1", "utf_n10")]
        if any(x != y for x, y in cells):
            print("   %-10s %s" % (p, "  ".join("%d -> %d" % c for c in cells)))
    # exact laws by equation where they differ (F41, U41)
    print("exact laws by equation where they differ (F41, U41):")
    ex = lambda D, kind: Counter(k[1] for k, r in D.items() if k[0] == kind and r.get("status") == "EXACT")
    for p in sorted({k[1] for k in a if k[0] == "feyn"}):
        cells = [(ex(a, kd)[p], ex(b, kd)[p]) for kd in ("feyn", "ufeyn")]
        if any(x != y for x, y in cells):
            print("   %-10s %s" % (p, "  ".join("%d -> %d" % c for c in cells)))
    # the formula of I.34.1 at 1 % noise quoted by the pages of the limits
    for D, tag in ((a, "1.3.0"), (b, "1.4.0")):
        f = sorted({r["expr"] for k, r in D.items() if k[0] == "feyn_n1" and k[1] == "I.34.1"})
        print("I.34.1 at 1 %% noise, %s: %s" % (tag, f))

    # TP and TPT10
    for name, fa, fb in (("TP", "tp_1.3.0.jsonl", "tp_1.4.0.jsonl"),
                         ("TPT10", "tpt10_1.3.0.jsonl", "tpt10_1.4.0.jsonl")):
        ta, tb = tload(os.path.join(folder, fa)), tload(os.path.join(folder, fb))
        print("\n%s: %d and %d jobs, same: %s" % (name, len(ta), len(tb), set(ta) == set(tb)))
        for arm in ("plain", "units"):
            xa = [r for k, r in ta.items() if k[0] == arm]
            xb = [r for k, r in tb.items() if k[0] == arm]
            print("  %s: law %d -> %d; useful %d -> %d; median time %.2f -> %.2f s; "
                  "units_gate %s -> %s"
                  % (arm, sum(r["law"] for r in xa), sum(r["law"] for r in xb),
                     sum(r["useful"] for r in xa), sum(r["useful"] for r in xb),
                     median(r["time"] for r in xa), median(r["time"] for r in xb),
                     sum(bool(r.get("units_gate")) for r in xa) if arm == "units" else "-",
                     sum(bool(r.get("units_gate")) for r in xb) if arm == "units" else "-"))
        for e in sorted({k[1] for k in ta}):
            row = []
            for arm in ("plain", "units"):
                la = sum(r["law"] for k, r in ta.items() if k[0] == arm and k[1] == e)
                lb = sum(r["law"] for k, r in tb.items() if k[0] == arm and k[1] == e)
                ua = sum(r["useful"] for k, r in ta.items() if k[0] == arm and k[1] == e)
                ub = sum(r["useful"] for k, r in tb.items() if k[0] == arm and k[1] == e)
                row.append("%s law %d -> %d useful %d -> %d" % (arm, la, lb, ua, ub))
            print("    %-16s %s" % (e, " | ".join(row)))
        lost = [k for k in ta if ta[k]["law"] and not tb[k]["law"]]
        won = [k for k in ta if tb[k]["law"] and not ta[k]["law"]]
        print("  law lost in %d fits, won in %d" % (len(lost), len(won)))
        for k in lost + won:
            print("    %s %s: err_train %.3g -> %.3g; size %s -> %s; %s | %s"
                  % ("lost" if k in lost else "won ", k, ta[k].get("err_train", float("nan")),
                     tb[k].get("err_train", float("nan")), ta[k].get("size"), tb[k].get("size"),
                     ta[k]["expr"][:45], tb[k]["expr"][:45]))
        cells = Counter()
        for k in ta:
            if k[0] == "plain" and k[1] in ("rc",):
                cells[(k[2], k[3])] += tb[k]["law"]
        if cells:
            print("  rc, plain, law with 1.4.0 by (points, noise): %s" % dict(sorted(cells.items())))


if __name__ == "__main__":
    main(sys.argv[1])
