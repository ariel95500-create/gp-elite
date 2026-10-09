"""Counts of the rule table of COLLAPSES.md (described, not chosen).

  python benchmarks/results_0.9/collapses_rules.py benchmarks/results_0.9/collapses_0.8.0.jsonl
"""
import json, sys, numpy as np
R = [json.loads(l) for l in open(sys.argv[1])]
def ret(r):  # the returned model as a pseudo-entry
    return dict(size=r["size"], r2_validation=r["r2_validation"], r2_ood=r["r2_ood"], reach=r["reach"], ops=r["ops"])
def summary(name, pick):
    got = [pick(r) for r in R]
    o = np.array([g["r2_ood"] for g in got]); base = np.array([r["r2_ood"] for r in R])
    v = np.array([g["r2_validation"] if g["r2_validation"] is not None else np.nan for g in got])
    vb = np.array([r["r2_validation"] if r["r2_validation"] is not None else np.nan for r in R])
    changed = sum(1 for g, r in zip(got, R) if g["size"] != r["size"] or abs(g["r2_ood"] - r["r2_ood"]) > 1e-12)
    print("%-44s collapses %2d, worst %9.4g, median R2 ood %.3f, changed %2d, R2 ood lower by >0.05 in %2d, median val R2 change %+.4f" % (
        name, int((o < 0).sum()), o.min(), np.median(o), changed,
        int(((base - o) > 0.05).sum()), np.nanmedian(v - vb)))
summary("returned model (0.8.0)", ret)
for K in (2, 3, 5, 10):
    def pick(r, K=K):
        ok = [e for e in r["pareto"] if e["reach"] <= K and e["r2_validation"] is not None]
        if ret(r)["reach"] <= K: return ret(r)
        return max(ok, key=lambda e: e["r2_validation"]) if ok else ret(r)
    summary("reach on ood inputs <= %g (else best val)" % K, pick)
for d in (0.005, 0.01, 0.02, 0.05):
    def pick(r, d=d):
        es = [e for e in r["pareto"] if e["r2_validation"] is not None]
        if not es: return ret(r)
        best = max(e["r2_validation"] for e in es)
        return min([e for e in es if e["r2_validation"] >= best - d], key=lambda e: e["size"])
    summary("smallest Pareto entry within %g val R2" % d, pick)
for S_ in (20, 30):
    def pick(r, S_=S_):
        if r["size"] <= S_: return ret(r)
        es = [e for e in r["pareto"] if e["size"] <= S_ and e["r2_validation"] is not None]
        return max(es, key=lambda e: e["r2_validation"]) if es else ret(r)
    summary("best val R2 among Pareto entries of size <= %d" % S_, pick)
