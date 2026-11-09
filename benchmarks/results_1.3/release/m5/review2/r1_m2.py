"""Second review of M5: the figures of M2 recomputed from the records.

python3 -I r1_m2.py  (read-only; no engine)
"""
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (A_PATH, B_PATH, SUITE, UNIT_KINDS, load, pools, pool_of,
                    median)

a, da = load(A_PATH)
b, db = load(B_PATH)
P = pools()
print("records: A %d (dup %d), B %d (dup %d), same keys %s" % (
    len(a), da, len(b), db, set(a) == set(b)))
print("pools in P:", Counter(P.values()))
print("crashes:", sum(r["status"] == "CRASH" for r in a.values() if "status" in r),
      sum(r["status"] == "CRASH" for r in b.values() if "status" in r))
print("engine versions:", Counter(r["engine_version"] for r in a.values()),
      Counter(r["engine_version"] for r in b.values()))
keys = sorted(a)
print("pools of jobs:", Counter(pool_of(k, P) for k in keys))
print("pools of jobs by kind:", {s: dict(Counter(pool_of(k, P) for k in keys if k[0] == kd))
                                 for kd, s in SUITE.items()})


def ind(R):
    rr = list(R.values())
    sel = lambda kind, pred=lambda s: True: [r for r in rr if r["kind"] == kind and pred(r["split"])]
    o = {}
    o["F41 exact"] = sum(r.get("status") == "EXACT" for r in sel("feyn"))
    o["U41 exact"] = sum(r.get("status") == "EXACT" for r in sel("ufeyn"))
    for k in ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10"):
        o[SUITE[k] + " struct"] = sum(bool(r.get("structure")) for r in sel(k))
    o["TF78 exact"] = sum(r.get("status") == "EXACT" for r in sel("tf"))
    o["UTF exact"] = sum(r.get("status") == "EXACT" for r in sel("utf"))
    o["TS14 test exact"] = sum(r.get("status") == "EXACT" for r in sel("ts", lambda s: s == "test"))
    o["TS14 ood collapses"] = sum(r["r2"] < 0 for r in sel("ts", lambda s: s == "ood"))
    o["TS14 ood n"] = len(sel("ts", lambda s: s == "ood"))
    for k in ("real", "realraw", "tr", "trraw"):
        f = [r["r2"] for r in sel(k, lambda s: s.startswith("fold"))]
        o[SUITE[k] + " folds median R2"] = (round(median(f), 4), len(f))
        oo = [r["r2"] for r in sel(k, lambda s: s == "ood")]
        o[SUITE[k] + " ood collapses"] = (sum(x < 0 for x in oo), len(oo))
    u = [r for r in rr if r["kind"] in UNIT_KINDS]
    o["units fits"] = len(u)
    o["units audit ok"] = sum(r.get("units_ok") is True for r in u)
    t = sorted(r["time"] for r in u)
    o["units median time (upper median as compare)"] = t[len(t) // 2]
    o["units median time (true)"] = median(t)
    o["units longest"] = t[-1]
    return o


ia, ib = ind(a), ind(b)
for k in ia:
    print("  %-45s %s | %s" % (k, ia[k], ib[k]))

# times of the whole campaign
ta = [r["time"] for r in a.values()]
tb = [r["time"] for r in b.values()]
print("all fits median time:", median(ta), median(tb), "max", max(ta), max(tb))
print("dates: A %s .. %s, B %s .. %s" % (min(r["date"] for r in a.values()),
      max(r["date"] for r in a.values()), min(r["date"] for r in b.values()),
      max(r["date"] for r in b.values())))

# the pool physical
phys = [k for k in keys if pool_of(k, P) == "physical"]
det = [k for k in phys if not a[k]["time_limit_reached"] and not b[k]["time_limit_reached"]]
diff = [k for k in det if a[k]["expr"] != b[k]["expr"] or a[k]["err"] != b[k]["err"]
        or a[k]["formula_exact"] != b[k]["formula_exact"]]
print("\nphysical: %d, det %d, differing %d" % (len(phys), len(det), len(diff)))
long160 = [k for k in det if len(a[k]["expr"]) >= 160 or len(b[k]["expr"]) >= 160]
print("  det with expr of 160 chars (cut):", len(long160), Counter(len(a[k]["expr"]) for k in long160))
skip = {"time", "date", "engine_file", "engine_version"}
full_diff = []
for k in det:
    fa = {x: y for x, y in a[k].items() if x not in skip}
    fb = {x: y for x, y in b[k].items() if x not in skip}
    if fa != fb:
        full_diff.append((k, sorted(x for x in set(fa) | set(fb) if fa.get(x) != fb.get(x))))
print("  det differing in any field but time/date/engine:", len(full_diff), full_diff[:10])
for k in long160:
    fa = {x: y for x, y in a[k].items() if x not in skip}
    fb = {x: y for x, y in b[k].items() if x not in skip}
    print("   long:", k, "fields differ:", sorted(x for x in set(fa) | set(fb) if fa.get(x) != fb.get(x)))
same = sum(a[k]["expr"] == b[k]["expr"] for k in phys)
print("  same recorded formula in physical: %d of %d" % (same, len(phys)))
budget = Counter((a[k]["time_limit_reached"], b[k]["time_limit_reached"]) for k in phys)
print("  budget reached (A,B) in physical:", budget)
for k in phys:
    sa = a[k].get("status"); sb = b[k].get("status")
    st_a = bool(a[k].get("structure")); st_b = bool(b[k].get("structure"))
    if sa != sb or st_a != st_b:
        print("  status/structure change:", k, sa, "->", sb, st_a, "->", st_b,
              "budget", a[k]["time_limit_reached"], b[k]["time_limit_reached"])
# status changes on the ood split of ts? (ts has status on ood)

# the pool trig
trig = [k for k in keys if pool_of(k, P) == "trig"]
print("\ntrig fits:", len(trig), Counter(SUITE[k[0]] for k in trig))
for kd in SUITE:
    ks = [k for k in trig if k[0] == kd]
    if not ks:
        continue
    ex_a = sum(a[k].get("status") == "EXACT" for k in ks)
    ex_b = sum(b[k].get("status") == "EXACT" for k in ks)
    sa = sum(bool(a[k].get("structure")) for k in ks)
    sb = sum(bool(b[k].get("structure")) for k in ks)
    ch = sum(a[k].get("status") != b[k].get("status") for k in ks)
    arc = sum("arcsin" in b[k]["expr"] for k in ks)
    arc_a = sum("arcsin" in a[k]["expr"] for k in ks)
    fe_a = sum(a[k]["formula_exact"] is False for k in ks)
    fe_b = sum(b[k]["formula_exact"] is False for k in ks)
    print("  %-17s n %3d exact %2d->%2d struct %2d->%2d status changed %d arcsin B %d (A %d) fe False %d->%d"
          % (SUITE[kd], len(ks), ex_a, ex_b, sa, sb, ch, arc, arc_a, fe_a, fe_b))

# structure changes by problem in noisy trig suites
print("\nstructure gains/losses by problem (trig):")
for kd in ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10"):
    byp = defaultdict(lambda: [0, 0])
    for k in trig:
        if k[0] != kd:
            continue
        byp[k[1]][0] += bool(a[k].get("structure"))
        byp[k[1]][1] += bool(b[k].get("structure"))
    print("  %s:" % SUITE[kd], {p: tuple(v) for p, v in sorted(byp.items()) if v[0] != v[1]},
          "total", sum(v[0] for v in byp.values()), "->", sum(v[1] for v in byp.values()))
print("exact gains/losses by problem (trig):")
for kd in ("feyn", "ufeyn", "tf", "utf", "ts"):
    byp = defaultdict(lambda: [0, 0])
    for k in trig:
        if k[0] != kd or (kd == "ts" and k[2] != "test"):
            continue
        byp[k[1]][0] += a[k].get("status") == "EXACT"
        byp[k[1]][1] += b[k].get("status") == "EXACT"
    print("  %s:" % SUITE[kd], {p: tuple(v) for p, v in sorted(byp.items()) if v[0] != v[1]})

# the arcsine laws
print("\narcsine laws:")
for kd in ("feyn", "ufeyn", "feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10"):
    for p in ("I.26.2", "I.30.5"):
        for s in range(5):
            k = (kd, p, "test", s)
            r = b[k]
            print("  %s %s s%d: A %s/%s B %s/%s fe %s es %s ts %s | %s" % (
                SUITE[kd], p, s, a[k]["status"], a[k].get("structure"), r["status"],
                r.get("structure"), r["formula_exact"], str(r["elementary_seed"])[:60], str(r["tolerant_seed"])[:60],
                r["expr"][:80]))

# formula_exact False
print("\nformula_exact False by pool:")
for pl in ("physical", "trig"):
    ks = [k for k in keys if pool_of(k, P) == pl]
    fa = [k for k in ks if a[k]["formula_exact"] is False]
    fb = [k for k in ks if b[k]["formula_exact"] is False]
    print("  %s: A %d, B %d (of %d)" % (pl, len(fa), len(fb), len(ks)))
    if pl == "trig":
        arc = [k for k in fb if "arcsin" in b[k]["expr"]]
        cut = [k for k in fb if len(b[k]["expr"]) >= 160]
        cut_noarc = [k for k in cut if "arcsin" not in b[k]["expr"]]
        noarc = [k for k in fb if "arcsin" not in b[k]["expr"]]
        print("    B with arcsin visible: %d; cut at 160: %d; cut and no arcsin: %d; no arcsin: %d;"
              " no arcsin and not cut: %d" % (len(arc), len(cut), len(cut_noarc), len(noarc),
                                              len([k for k in noarc if len(b[k]['expr']) < 160])))
        print("    lengths of expr:", Counter(len(b[k]["expr"]) for k in fb).most_common(5))
        print("    by suite B:", Counter(SUITE[k[0]] for k in fb))
        print("    by suite A:", Counter(SUITE[k[0]] for k in fa))
    print("    by suite A:", sorted(Counter(SUITE[k[0]] for k in fa).items()))
    print("    by suite B:", sorted(Counter(SUITE[k[0]] for k in fb).items()))
print("formula_exact False all: A %d B %d" % (sum(r["formula_exact"] is False for r in a.values()),
                                              sum(r["formula_exact"] is False for r in b.values())))
print("formula_exact None:", sum(r["formula_exact"] is None for r in a.values()),
      sum(r["formula_exact"] is None for r in b.values()))

# arcsine in recorded text, by suite
arcb = [k for k in keys if "arcsin" in b[k]["expr"]]
print("\narcsin in B text: %d" % len(arcb), sorted(Counter(SUITE[k[0]] for k in arcb).items()))
print("arcsin in A text: %d" % sum("arcsin" in a[k]["expr"] for k in keys))
print("arcsin in B text, pool:", Counter(pool_of(k, P) for k in arcb))
print("arcsin in B text, ts split:", Counter(k[2] for k in arcb if k[0] == "ts"))
print("arcsin in B, problems:", sorted(Counter((SUITE[k[0]], k[1]) for k in arcb).items()))

# seeds
for f in ("elementary_seed", "tolerant_seed"):
    print("\n%s: A non-null %d, B non-null %d" % (f, sum(bool(r[f]) for r in a.values()),
                                                  sum(bool(r[f]) for r in b.values())))
    vals = Counter((SUITE[k[0]], k[1], str(b[k][f])[:70]) for k in keys if b[k][f])
    for x, n in sorted(vals.items()):
        print("   ", x, n)
    vals = Counter((SUITE[k[0]], k[1], str(a[k][f])[:70]) for k in keys if a[k][f])
    for x, n in sorted(vals.items()):
        print("   A", x, n)

# frozen
print("\nfeynman_test_10:")
for k in keys:
    if k[1] == "feynman_test_10":
        print("  ", k, a[k]["status"], b[k]["status"])
print("TS14 trig fits:")
ts_trig = [k for k in trig if k[0] == "ts"]
print("  n", len(ts_trig), Counter(k[2] for k in ts_trig), "systems", sorted({k[1] for k in ts_trig}))
chg = [k for k in ts_trig if a[k]["status"] != b[k]["status"]]
print("  status changed:", len(chg))
for k in chg:
    print("    ", k, a[k]["status"], "->", b[k]["status"])
print("  exact A:", [k for k in ts_trig if a[k]["status"] == "EXACT"])
print("  exact B:", [k for k in ts_trig if b[k]["status"] == "EXACT"])
print("TS14 seeds:", sorted({k[3] for k in keys if k[0] == "ts"}))
print("III_8_54:")
for k in keys:
    if k[1] == "feynman_III_8_54":
        print("  ", k, a[k]["status"], b[k]["status"])
print("TF78 seeds:", sorted({k[3] for k in keys if k[0] == "tf"}),
      "UTF seeds:", sorted({k[3] for k in keys if k[0] == "utf"}))
print("TF78 trig problems:", len({k[1] for k in trig if k[0] == "tf"}))
