"""Run the counting of limits_figures (re-implemented here) on the records of the release of 1.1,
to check the claim that it gives back the figures of 1.1 (read-only)."""
import json, glob, sys
from collections import defaultdict
paths = sys.argv[1:]
for p in paths:
    recs = [json.loads(l) for l in open(p) if l.strip()]
    kinds = set(r["kind"] for r in recs)
    rr = [r for r in recs if r["kind"] in ("real", "realraw")]
    tt = [r for r in recs if r["kind"] in ("tr", "trraw")]
    ood = [r for r in rr if r["split"] == "ood"]
    tf = defaultdict(int)
    for r in recs:
        if r["kind"] == "tf":
            tf[r["problem"]] += r.get("status") == "EXACT"
    print(p.split("/")[-1], recs[0].get("engine_version"), len(recs),
          "fe False bench", sum(r.get("formula_exact") is False for r in rr), "of", len(rr),
          "| test set", sum(r.get("formula_exact") is False for r in tt), "of", len(tt),
          "| collapses", sum(r["r2"] < 0 for r in ood), "of", len(ood),
          "| struct n1/n10", sum(bool(r.get("structure")) for r in recs if r["kind"] == "feyn_n1"), sum(bool(r.get("structure")) for r in recs if r["kind"] == "feyn_n10"),
          "| TS14 test exact", sum(r.get("status") == "EXACT" for r in recs if r["kind"] == "ts" and r["split"] == "test"),
          "| TF78 exact", sum(tf.values()), "never", sum(n == 0 for n in tf.values()))
