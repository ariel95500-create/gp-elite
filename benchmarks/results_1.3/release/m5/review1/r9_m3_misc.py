"""Review 1: figures of M3 and of the notebooks, recomputed from the records
(scaling, time_limit_check, Kepler min-max, the six laws of the TP notebook,
the TP notebook of the pool full at seed 0, the duration of E2, the clean-data
fits of Snell's law). python3 -I r9_m3_misc.py"""
import json
import os
import re
from collections import defaultdict

REL = "/home/user/gp-elite/benchmarks/results_1.3/release/"
R12 = "/home/user/gp-elite/benchmarks/results_1.2/release/m3/"
M3 = REL + "m3/"

print("== scaling: total time of the five fits")
for p in (M3 + "scaling.jsonl", R12 + "scaling.jsonl"):
    rr = [json.loads(l) for l in open(p)]
    d = defaultdict(list)
    for r in rr:
        d[r["n_total"]].append(r)
    print("  %s: 1,000 points %.1f s, 10,000 points %.1f s; I.16.6 below 1,000: exact %d of %d" % (
        p.split("benchmarks/")[1], sum(r["time"] for r in d[1000]), sum(r["time"] for r in d[10000]),
        sum(r["status"] == "EXACT" for r in rr if r["name"] == "I.16.6" and r["n_total"] < 1000),
        sum(1 for r in rr if r["name"] == "I.16.6" and r["n_total"] < 1000)))
a = [json.loads(l) for l in open(M3 + "scaling.jsonl")]
b = [json.loads(l) for l in open(R12 + "scaling.jsonl")]
print("  same expr_full in %d of %d" % (sum(x["expr_full"] == y["expr_full"] for x, y in zip(a, b)), len(a)))

print("== time_limit_check")
for p in (M3 + "time_limit_check.txt", R12 + "time_limit_check.txt"):
    t = open(p).read()
    print("  ", p.split("benchmarks/")[1], re.findall(r"arret a l'echeance\s+T=15s duree=([\d.]+)s", t),
          re.findall(r"BILAN : (\d+/\d+)", t))

print("== kepler_minmax_check")
for p in (M3 + "kepler_minmax_check.txt", R12 + "kepler_minmax_check.txt"):
    print("  ", p.split("benchmarks/")[1], [l.strip() for l in open(p) if l.startswith("generations")])

print("== the six laws of the TP notebook (m3/tp_timing/notebook_pair)")
tot = {}
for f in sorted(os.listdir(M3 + "tp_timing/notebook_pair")):
    lines = [l for l in open(M3 + "tp_timing/notebook_pair/" + f) if "formule trouv" in l]
    times = [int(re.search(r"\((\d+) s\)", l).group(1)) for l in lines]
    forms = [l.split(":", 1)[1].rsplit("(", 1)[0].strip() for l in lines]
    tot[f] = forms
    print("   %s: times %s, in all %d" % (f, times, sum(times)))
print("   same six formulas in the four runs:", len({tuple(v) for v in tot.values()}) == 1)

print("== deduced constant, 1.2.0 against 1.3.0")
x = open(M3 + "deduced_constant_venv12bx.txt").read().splitlines()
y = open(M3 + "deduced_constant_venv13rx.txt").read().splitlines()
print("   lines differing:", [i for i, (u, v) in enumerate(zip(x, y)) if u != v], len(x), len(y))

print("== E2 (m3/examine): fit time of the 30 pairs, run two at a time")
ea = {(r["generations"], r["seed"]): r for r in map(json.loads, open(M3 + "examine/e2_1.2.0.jsonl"))}
eb = {(r["generations"], r["seed"]): r for r in map(json.loads, open(M3 + "examine/e2_1.3.0.jsonl"))}
print("   sum over the pairs of the longer fit: %.1f s; fields with a date: %s" % (
    sum(max(ea[k]["time"], eb[k]["time"]) for k in ea), [k for k in next(iter(ea.values())) if "date" in k]))

print("== the TP notebook of the pool full, seed 0 (m3/notebook_snippet_tp.txt)")
for l in open(M3 + "notebook_snippet_tp.txt"):
    if "departs from predict()" in l:
        print("   warning:", re.search(r"departs from predict\(\) on (\d+ of \d+) training rows \(largest gap (\S+)\)", l).groups())
    if l.startswith("TP loi") or "générations" in l:
        print("  ", l.rstrip()[:110])
