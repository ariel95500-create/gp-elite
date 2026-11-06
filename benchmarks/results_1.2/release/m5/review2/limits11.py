"""Second review: the figures of the pages of the limits on the records of the
release of 1.1 and 1.0, with the counting of limits_figures.py (re-implemented)."""
import json
from collections import defaultdict
B = "/home/user/gp-elite/benchmarks/"

def load(p):
    return [json.loads(l) for l in open(B + p) if l.strip()]

def fig(recs, label):
    def ex(kind):
        per = defaultdict(int)
        for r in recs:
            if r["kind"] == kind:
                per[r["problem"]] += r.get("status") == "EXACT"
        return per
    f41 = ex("feyn"); tf = ex("tf"); u = ex("ufeyn")
    ts = [r for r in recs if r["kind"] == "ts" and r["split"] == "test"]
    ood = [r for r in recs if r["kind"] in ("real", "realraw") and r["split"] == "ood"]
    out = dict(F41=sum(f41.values()), F41never=sorted(p for p, n in f41.items() if n == 0),
               once=sorted(p for p, n in f41.items() if n == 1),
               TFnever=sum(n == 0 for n in tf.values()) if tf else None, TF=sum(tf.values()) if tf else None,
               TFmain=sum(r.get("status") == "EXACT" for r in recs if r["kind"] == "tf" and r.get("family") == "main"),
               TFbonus=sum(r.get("status") == "EXACT" for r in recs if r["kind"] == "tf" and r.get("family") == "bonus"),
               TS=sum(r.get("status") == "EXACT" for r in ts), nTS=len(ts),
               N1=sum(bool(r.get("structure")) for r in recs if r["kind"] == "feyn_n1"),
               N10=sum(bool(r.get("structure")) for r in recs if r["kind"] == "feyn_n10"),
               coll=sum(r["r2"] < 0 for r in ood), nood=len(ood), worst=min((r["r2"] for r in ood), default=None))
    for kind in ("tr", "trraw"):
        rr = [r for r in recs if r["kind"] == kind and r["split"] == "ood"]
        per = defaultdict(int)
        for r in rr:
            per[r["problem"]] += r["r2"] < 0
        out[kind] = (sum(r["r2"] < 0 for r in rr), len(rr), sum(sorted(per.values(), reverse=True)[:6]))
    out["fe_bench"] = sum(r.get("formula_exact") is False for r in recs if r["kind"] in ("real", "realraw"))
    out["n_bench"] = sum(1 for r in recs if r["kind"] in ("real", "realraw"))
    out["fe_test"] = sum(r.get("formula_exact") is False for r in recs if r["kind"] in ("tr", "trraw"))
    out["n_test"] = sum(1 for r in recs if r["kind"] in ("tr", "trraw"))
    out["U41"] = sum(u.values()) if u else None
    out["U41never"] = sum(n == 0 for n in u.values()) if u else None
    print(label, out)

for p in ("results_1.1/release/m2/campaignR_1.0.0.jsonl", "results_1.1/release/m2/campaignR_1.1.0.jsonl",
          "results_1.2/release/m2/campaignR_1.1.0.jsonl", "results_1.2/release/m2/campaignR_1.2.0.jsonl"):
    fig(load(p), p)

print("=== release 1.0")
for p in ("results_0.9/release_1.0/m2/campaignR_0.9.0.jsonl", "results_0.9/release_1.0/m2/campaignR_1.0.0.jsonl"):
    fig(load(p), p)
# point 3 example formula and point 4 worst
r10 = load("results_0.9/release_1.0/m2/campaignR_1.0.0.jsonl")
for r in r10:
    if r["kind"] == "feyn_n1" and r["problem"] == "I.34.1":
        print(" I.34.1 n1", r["seed"], r["expr"], r.get("structure"))
