"""Second review of M5, 1.2.0: recompute the M2 figures from the records only."""
import json
import statistics as st
from collections import Counter, defaultdict

D = "/home/user/gp-elite/benchmarks/results_1.2/release/m2/"


def load(p):
    out = {}
    dup = 0
    for line in open(p):
        if line.strip():
            r = json.loads(line)
            k = (r["kind"], r["problem"], r["split"], r["seed"])
            if k in out:
                dup += 1
            out[k] = r
    return out, dup


a, da = load(D + "campaignR_1.1.0.jsonl")
b, db = load(D + "campaignR_1.2.0.jsonl")
print("records", len(a), len(b), "dups", da, db, "same keys", set(a) == set(b))
print("kinds a", Counter(k[0] for k in a))
UNIT = ("ufeyn", "ufeyn_n1", "ufeyn_n10", "utf")
FROZEN = ("tf", "ts", "tr", "trraw", "utf")
phase1 = [k for k in a if k[0] not in UNIT]
print("phase1", len(phase1), "U41*", sum(k[0] in UNIT[:3] for k in a), "utf", sum(k[0] == "utf" for k in a))
print("utf seeds", sorted({k[3] for k in a if k[0] == "utf"}))
print("crash", sum(r.get("status") == "CRASH" for r in a.values()), sum(r.get("status") == "CRASH" for r in b.values()))
print("versions", Counter(r.get("engine_version") for r in a.values()), Counter(r.get("engine_version") for r in b.values()))

def sel(R, kind, pred=lambda s: True):
    return [r for k, r in R.items() if k[0] == kind and pred(k[2])]

for R, nm in ((a, "1.1.0"), (b, "1.2.0")):
    print("==", nm)
    print(" F41 exact", sum(r["status"] == "EXACT" for r in sel(R, "feyn")), len(sel(R, "feyn")))
    for kd in ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10"):
        print(" ", kd, "structure", sum(bool(r.get("structure")) for r in sel(R, kd)), len(sel(R, kd)),
              "NEAR", sum(r.get("status") == "NEAR" for r in sel(R, kd)))
    print(" U41 exact", sum(r["status"] == "EXACT" for r in sel(R, "ufeyn")))
    print(" TF78 exact", sum(r["status"] == "EXACT" for r in sel(R, "tf")), len(sel(R, "tf")))
    print(" TS14 test exact", sum(r["status"] == "EXACT" for r in sel(R, "ts", lambda s: s == "test")),
          len(sel(R, "ts", lambda s: s == "test")), "ts all", len(sel(R, "ts")))
    print(" utf exact", sum(r["status"] == "EXACT" for r in sel(R, "utf")), len(sel(R, "utf")))
    for kd in ("real", "realraw", "tr", "trraw", "ts"):
        f = [r["r2"] for r in sel(R, kd, lambda s: s.startswith("fold"))]
        o = [r["r2"] for r in sel(R, kd, lambda s: s == "ood")]
        print(" ", kd, "folds", len(f), "median %.6f" % st.median(f) if f else None, "ood", len(o), "collapses", sum(x < 0 for x in o),
              "all", len(sel(R, kd)), Counter(k[2][:4] for k in R if k[0] == kd))
    u = [r for k, r in R.items() if k[0] in UNIT]
    print(" units fits", len(u), "audit ok", sum(r.get("units_ok") is True for r in u))
    t = sorted(r["time"] for r in u)
    print(" units median time", t[len(t) // 2], st.median(t), "max", t[-1])
    t2 = sorted(r["time"] for k, r in R.items() if k[0] in UNIT and k[1] != "III.19.51")
    print(" units w/o III.19.51 max", t2[-1])
    tl = [r for r in R.values() if r.get("time_limit_reached")]
    tt = sorted(r["time"] for r in tl)
    print(" time_limit_reached", len(tl), "median", st.median(tt), "max", tt[-1])
    tlu = sorted(r["time"] for k, r in R.items() if r.get("time_limit_reached") and k[0] in UNIT)
    print(" tlr under units", len(tlu), "max", tlu[-1] if tlu else None)
    tln = sorted((r["time"], k) for k, r in R.items() if r.get("time_limit_reached") and k[0] not in UNIT)
    print(" tlr no units", len(tln), "max", tln[-1] if tln else None)

# status changes
chg = [k for k in a if a[k].get("status") != b[k].get("status")]
schg = [k for k in a if bool(a[k].get("structure")) != bool(b[k].get("structure"))]
print("status changes", len(chg), chg[:5], "structure changes", len(schg))
print("status set", Counter(r.get("status") for r in a.values()))
# collapse sets
for kd in ("real", "realraw", "tr", "trraw", "ts"):
    ca = {k for k in a if k[0] == kd and k[2] == "ood" and a[k]["r2"] < 0}
    cb = {k for k in b if k[0] == kd and k[2] == "ood" and b[k]["r2"] < 0}
    print(" collapses", kd, len(ca), len(cb), "same set", ca == cb)

diff = [k for k in a if a[k]["expr"] != b[k]["expr"]]
print("expr differs", len(diff), "no units", sum(k[0] not in UNIT for k in diff), "units", sum(k[0] in UNIT for k in diff))
x1alone = [k for k in diff if b[k].get("expr_11") == a[k]["expr"]]
other = [k for k in diff if b[k].get("expr_11") != a[k]["expr"]]
print("X1 alone", len(x1alone), "no units", sum(k[0] not in UNIT for k in x1alone), "units", sum(k[0] in UNIT for k in x1alone))
print("other model", len(other), "no units", sum(k[0] not in UNIT for k in other), "units", sum(k[0] in UNIT for k in other))
# any where expr same but expr_11 differs from a?
odd = [k for k in a if a[k]["expr"] == b[k]["expr"] and b[k].get("expr_11") != a[k]["expr"]]
print("same expr but expr_11 differs", len(odd), odd[:3])
both = [k for k in other if a[k].get("time_limit_reached") and b[k].get("time_limit_reached")]
iii = [k for k in other if k[1] == "III.19.51" and k[0] in UNIT]
print("other: both at budget", len(both), "III.19.51 units", len(iii), "both-at-budget & not III", len([k for k in both if k not in iii]))
for k in other:
    if k not in both:
        print("  other not both at budget:", k, a[k].get("time_limit_reached"), b[k].get("time_limit_reached"), a[k]["time"], b[k]["time"], a[k].get("generations"), b[k].get("generations"))
for k in iii:
    print("  III:", k, "gen", a[k].get("generations"), b[k].get("generations"), "t", a[k]["time"], b[k]["time"], a[k]["status"], b[k]["status"])
rew = [k for k in b if "expr_11" in b[k] and b[k]["expr_11"] != b[k]["expr"]]
print("X1 rewrites", len(rew), "no units", sum(k[0] not in UNIT for k in rew), "units", sum(k[0] in UNIT for k in rew))
print("  rewrites among other-model", len([k for k in rew if k in other]), "among x1alone", len([k for k in rew if k in x1alone]), "among same expr", len([k for k in rew if k not in diff]))
missing = [k for k in b if "expr_11" not in b[k] or not b[k].get("x1_again")]
print("missing expr_11", len(missing), "outside frozen n", sum(k[0] not in FROZEN for k in b))
fe = [k for k in b if b[k].get("formula_exact_11") != b[k].get("formula_exact")]
print("formula_exact != formula_exact_11", len(fe))
det = [k for k in a if not a[k].get("time_limit_reached") and not b[k].get("time_limit_reached") and not (k[0] in UNIT and k[1] == "III.19.51")]
print("neither at budget (III aside): outside frozen", sum(k[0] not in FROZEN for k in det), "frozen", sum(k[0] in FROZEN for k in det))
md = [k for k in det if b[k].get("expr_11") != a[k]["expr"] or a[k]["err"] != b[k]["err"] or a[k]["formula_exact"] != b[k]["formula_exact"]]
print("  among them differing", len(md))
# I.6.20a example
k = ("feyn", "I.6.20a", "test", 1)
print("I.6.20a s1:", a[k]["expr"], "|", b[k]["expr"], "|", b[k].get("expr_11"))
# III.19.51 table
for kd in ("ufeyn", "ufeyn_n1", "ufeyn_n10"):
    ks = [k for k in a if k[0] == kd and k[1] == "III.19.51"]
    ta = [a[k]["time"] for k in ks]
    tb = [b[k]["time"] for k in ks]
    print(" III.19.51", kd, len(ks), "1.1.0 %.2f-%.2f" % (min(ta), max(ta)), "1.2.0 %.2f-%.2f" % (min(tb), max(tb)),
          Counter(a[k]["status"] for k in ks), Counter(b[k]["status"] for k in ks), "ratio a/30 %.2f-%.2f" % (min(ta) / 30, max(ta) / 30))
    for k in sorted(ks):
        print("    ", k[3], a[k]["time"], b[k]["time"], a[k].get("generations"), b[k].get("generations"), a[k].get("time_limit_reached"), b[k].get("time_limit_reached"))
# fits at budget in both and not
print("time budget reached both:", sum(1 for k in a if a[k].get("time_limit_reached") and b[k].get("time_limit_reached")))
# median time of U41 fits
for R, nm in ((a, "a"), (b, "b")):
    print(nm, "U41 median time", st.median(r["time"] for k, r in R.items() if k[0] == "ufeyn"), "utf median", st.median(r["time"] for k, r in R.items() if k[0] == "utf"))
# details_x1: under units, both at budget
ub = [k for k in other if k[0] in UNIT and a[k].get("time_limit_reached") and b[k].get("time_limit_reached")]
print("units other both-at-budget", len(ub))
