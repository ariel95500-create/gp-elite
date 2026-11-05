"""Independent recomputation of the M2 figures of release 1.2.0 (read-only)."""
import json
import sys
from collections import Counter, defaultdict
from statistics import median

D = "/home/user/gp-elite/benchmarks/results_1.2/release/m2/"
UNITS = {"ufeyn", "ufeyn_n1", "ufeyn_n10", "utf"}
FROZEN = {"tf", "ts", "tr", "trraw", "utf"}


def load(p):
    out = {}
    n = 0
    for line in open(p):
        if not line.strip():
            continue
        r = json.loads(line)
        k = (r["kind"], r["problem"], r["split"], r["seed"])
        assert k not in out, ("dup", k)
        out[k] = r
        n += 1
    return out, n


a, na = load(D + "campaignR_1.1.0.jsonl")
b, nb = load(D + "campaignR_1.2.0.jsonl")
print("lines", na, nb, "keys equal", set(a) == set(b))
print("versions", Counter(r["engine_version"] for r in a.values()), Counter(r["engine_version"] for r in b.values()))
print("crashes", sum(r.get("status") == "CRASH" for r in a.values()), sum(r.get("status") == "CRASH" for r in b.values()))
print("dates a", min(r["date"] for r in a.values()), max(r["date"] for r in a.values()))
print("dates b", min(r["date"] for r in b.values()), max(r["date"] for r in b.values()))


def cnt(recs, kind, pred):
    return sum(1 for k, r in recs.items() if k[0] == kind and pred(r))


for name, R in (("1.1.0", a), ("1.2.0", b)):
    print("==", name)
    print(" F41 exact", cnt(R, "feyn", lambda r: r["status"] == "EXACT"))
    print(" F41N1/N10 structure", cnt(R, "feyn_n1", lambda r: bool(r.get("structure"))), cnt(R, "feyn_n10", lambda r: bool(r.get("structure"))))
    print(" U41 exact", cnt(R, "ufeyn", lambda r: r["status"] == "EXACT"))
    print(" U41N1/N10 structure", cnt(R, "ufeyn_n1", lambda r: bool(r.get("structure"))), cnt(R, "ufeyn_n10", lambda r: bool(r.get("structure"))))
    print(" TF78 exact", cnt(R, "tf", lambda r: r["status"] == "EXACT"), " utf exact", cnt(R, "utf", lambda r: r["status"] == "EXACT"))
    print(" TS14 test exact", sum(1 for k, r in R.items() if k[0] == "ts" and k[2] == "test" and r["status"] == "EXACT"))
    for kind in ("real", "realraw", "tr", "trraw", "ts"):
        f = sorted(r["r2"] for k, r in R.items() if k[0] == kind and k[2].startswith("fold"))
        o = [r["r2"] for k, r in R.items() if k[0] == kind and k[2] == "ood"]
        med = median(f) if f else None
        print(" ", kind, "folds", len(f), "median R2", None if med is None else round(med, 4), "ood", len(o), "collapses", sum(x < 0 for x in o), "worst", min(o) if o else None)
    u = [r for k, r in R.items() if k[0] in UNITS]
    t = sorted(r["time"] for r in u)
    print(" units fits", len(u), "units_ok", sum(r.get("units_ok") is True for r in u), "median", median(t), "lower-median", t[len(t) // 2], "max", t[-1])
    rest = [r["time"] for k, r in R.items() if k[0] in UNITS and k[1] != "III.19.51"]
    print(" units w/o III.19.51 longest", max(rest))
    tl = [r for r in R.values() if r["time_limit_reached"]]
    tt = sorted(r["time"] for r in tl)
    print(" at budget", len(tl), "median", median(tt), "max", max(tt), "min", min(tt))
    # by kind
    byk = defaultdict(list)
    for r in tl:
        byk[r["kind"]].append(r["time"])
    print("  at budget by kind max", {k: max(v) for k, v in sorted(byk.items())})
    alltimes = [r["time"] for r in R.values()]
    print(" all fits max time", max(alltimes))
    # longest fit without units
    print(" longest fit without units", max(r["time"] for k, r in R.items() if k[0] not in UNITS))
    print(" formula_exact False real+realraw non-ood", sum(r.get("formula_exact") is False for k, r in R.items() if k[0] in ("real", "realraw") and k[2] != "ood"))
    print(" formula_exact False real+realraw all", sum(r.get("formula_exact") is False for k, r in R.items() if k[0] in ("real", "realraw")))
    print(" formula_exact False tr+trraw all", sum(r.get("formula_exact") is False for k, r in R.items() if k[0] in ("tr", "trraw")))
    # never exact
    per = defaultdict(int)
    for k, r in R.items():
        if k[0] == "feyn":
            per[k[1]] += r["status"] == "EXACT"
    print(" F41 never exact", sorted(p for p, n in per.items() if n == 0), "once", sorted(p for p, n in per.items() if n == 1))
    per = defaultdict(int)
    for k, r in R.items():
        if k[0] == "ufeyn":
            per[k[1]] += r["status"] == "EXACT"
    print(" U41 never exact", sum(n == 0 for n in per.values()), sorted(p for p, n in per.items() if n == 0))
    per = defaultdict(int)
    for k, r in R.items():
        if k[0] == "tf":
            per[k[1]] += r["status"] == "EXACT"
    print(" TF78 never exact", sum(n == 0 for n in per.values()), "of", len(per))
    per = defaultdict(int)
    for k, r in R.items():
        if k[0] == "utf":
            per[k[1]] += r["status"] == "EXACT"
    print(" utf never exact", sum(n == 0 for n in per.values()), "of", len(per))
    for kind in ("ufeyn", "ufeyn_n1", "ufeyn_n10", "utf", "feyn", "feyn_n1", "feyn_n10", "tf"):
        tk = [r["time"] for k, r in R.items() if k[0] == kind]
        print("  median time", kind, round(median(tk), 3), "max", max(tk))

# pairing comparisons
keys = sorted(a)
diff = [k for k in keys if a[k]["expr"] != b[k]["expr"]]
print("\nexpr differ", len(diff), "without units", sum(k[0] not in UNITS for k in diff), "units", sum(k[0] in UNITS for k in diff))
x1only = [k for k in diff if b[k]["expr_11"] == a[k]["expr"]]
model = [k for k in diff if b[k]["expr_11"] != a[k]["expr"]]
print("x1 only", len(x1only), "no units", sum(k[0] not in UNITS for k in x1only), "units", sum(k[0] in UNITS for k in x1only))
print("other model", len(model), "no units", sum(k[0] not in UNITS for k in model), "units", sum(k[0] in UNITS for k in model))
both = [k for k in model if a[k]["time_limit_reached"] and b[k]["time_limit_reached"]]
print(" both at budget", len(both), "others", [(k, a[k]["time"], b[k]["time"], a[k]["status"], b[k]["status"]) for k in model if k not in both])
print(" model-differ in frozen", sum(k[0] in FROZEN for k in model))
rew = [k for k in keys if b[k]["expr_11"] != b[k]["expr"]]
print("x1 rewrites", len(rew), "no units", sum(k[0] not in UNITS for k in rew), "units", sum(k[0] in UNITS for k in rew), "frozen", sum(k[0] in FROZEN for k in rew))
print(" rewrites by kind", Counter(k[0] for k in rew))
print("status changed", sum(a[k].get("status") != b[k].get("status") for k in keys))
print("structure changed", sum(bool(a[k].get("structure")) != bool(b[k].get("structure")) for k in keys))
fe = [k for k in keys if b[k]["formula_exact"] != b[k]["formula_exact_11"]]
print("formula_exact != formula_exact_11", len(fe))
print("x1_again false", sum(not b[k].get("x1_again") for k in keys))
det = [k for k in keys if not a[k]["time_limit_reached"] and not b[k]["time_limit_reached"] and not (k[0] in UNITS and k[1] == "III.19.51")]
detd = [k for k in det if k[0] not in FROZEN]
detf = [k for k in det if k[0] in FROZEN]
md = [k for k in det if b[k]["expr_11"] != a[k]["expr"] or a[k]["err"] != b[k]["err"] or a[k]["formula_exact"] != b[k]["formula_exact"]]
print("neither at budget: deciding", len(detd), "frozen", len(detf), "differ", len(md))
print("III.19.51 units:")
for k in keys:
    if k[0] in ("ufeyn", "ufeyn_n1", "ufeyn_n10") and k[1] == "III.19.51":
        print("  ", k, a[k]["time"], b[k]["time"], a[k]["status"], b[k]["status"], a[k]["time_limit_reached"], b[k]["time_limit_reached"], b[k].get("units_ok"), b[k]["expr"][:60], "|", a[k]["expr"][:60])
# 1.2.0 per kind count of time_limit
print("at budget by kind 1.1/1.2", {kd: (sum(a[k]["time_limit_reached"] for k in keys if k[0] == kd), sum(b[k]["time_limit_reached"] for k in keys if k[0] == kd)) for kd in sorted(set(k[0] for k in keys))})
print("at budget: deciding fits a/b", sum(a[k]["time_limit_reached"] for k in keys if k[0] not in FROZEN), sum(b[k]["time_limit_reached"] for k in keys if k[0] not in FROZEN))
# time budget fits of 1.2.0 whose time > 31
big = sorted(((b[k]["time"], k) for k in keys if b[k]["time_limit_reached"]), reverse=True)[:5]
print("top times 1.2 at budget", big)
big = sorted(((a[k]["time"], k) for k in keys if a[k]["time_limit_reached"] and not (k[0] in UNITS and k[1] == 'III.19.51')), reverse=True)[:5]
print("top times 1.1 at budget (no III.19.51)", big)
tt = sorted(a[k]["time"] for k in keys if a[k]["time_limit_reached"])
print("1.1 at budget median", median(tt))
tt = sorted(a[k]["time"] for k in keys if a[k]["time_limit_reached"] and not (k[0] in UNITS and k[1] == 'III.19.51'))
print("1.1 at budget (no III.19.51) median, max", median(tt), max(tt))
# fits not at budget in 1.2.0 that took > 30s
print("1.2 not at budget >30s", [(k, b[k]["time"]) for k in keys if not b[k]["time_limit_reached"] and b[k]["time"] > 29])
# example I.6.20a seed1
k = ("feyn", "I.6.20a", "test", 1)
print(k, a[k]["expr"], "||", b[k]["expr"], "||", b[k]["expr_11"])
