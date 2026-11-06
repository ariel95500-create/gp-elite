"""The 40 jobs whose formula without X1 differs from 1.1.0: which are III.19.51 under units,
and the generations each version ran (read-only)."""
import json
D = "/home/user/gp-elite/benchmarks/results_1.2/release/m2/"
def load(p):
    return {(r["kind"], r["problem"], r["split"], r["seed"]): r for r in map(json.loads, open(p))}
a = load(D + "campaignR_1.1.0.jsonl"); b = load(D + "campaignR_1.2.0.jsonl")
model = [k for k in a if b[k]["expr_11"] != a[k]["expr"]]
print("model differs", len(model))
i19 = [k for k in model if k[1] == "III.19.51"]
print("of which III.19.51 under units", len(i19), sorted((k[0], k[3]) for k in i19))
for k in sorted(model):
    print(k, a[k]["time_limit_reached"], b[k]["time_limit_reached"], "gens", a[k]["generations"], b[k]["generations"], a[k].get("status"), b[k].get("status"))
# III.19.51 noisy: same expression?
for kd in ("ufeyn_n1", "ufeyn_n10"):
    for s in range(5):
        k = (kd, "III.19.51", "test", s)
        print(k, "same expr" if a[k]["expr"] == b[k]["expr"] else "DIFF", "err", a[k]["err"], b[k]["err"])
