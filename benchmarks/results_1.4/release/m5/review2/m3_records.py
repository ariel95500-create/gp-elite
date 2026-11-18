"""Second review of M5 (1.4.0): records of M3 read again, 1.3.0 against 1.4.0.

  python3 -I m3_records.py

- scaling.jsonl: which fits return another model (expr or status), and do
  they coincide with the fits where m3_examine records other seeds?
- small_data_release.jsonl: which records differ, times aside.
- the case-study records of Kepler (C8 seeds count) and the snippet of TP.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REL = os.path.normpath(os.path.join(HERE, "..", ".."))
B13 = os.path.normpath(os.path.join(REL, "..", "..", "results_1.3", "release", "m3"))
B14 = os.path.join(REL, "m3")
SKIP = {"time", "date", "seconds", "engine", "engine_file", "engine_version", "elapsed",
        "t", "wall", "duration", "fit_s", "time_s"}


def jl(path):
    return [json.loads(x) for x in open(path, encoding="utf-8") if x.strip()]


def strip(r):
    return {k: v for k, v in r.items() if k not in SKIP and not k.endswith(("_s", "_t"))}


# scaling
a = jl(os.path.join(B13, "scaling.jsonl"))
b = jl(os.path.join(B14, "scaling.jsonl"))
key = lambda r: (r["name"], r["n_total"], r["rep"], r.get("arm"))
da, db = {key(r): r for r in a}, {key(r): r for r in b}
print("scaling: %d and %d records, same keys %s" % (len(a), len(b), set(da) == set(db)))
moved = []
for k in sorted(da):
    x, y = strip(da[k]), strip(db[k])
    if x != y:
        fields = sorted(f for f in set(x) | set(y) if x.get(f) != y.get(f))
        moved.append((k, fields))
print("  records that differ, times aside: %d" % len(moved))
for k, f in moved:
    print("   ", k, f[:8], da[k].get("status"), "->", db[k].get("status"))
seeds = {}
for line in open(os.path.join(REL, "m3_examine", "seeds_compare.txt"), encoding="utf-8"):
    m = re.match(r"scaling (\S+) N=(\d+) rep=(\d+)\s+(.*?)\s{2,}(.*?)\s{2,}(yes|NO)\s*$", line)
    if m:
        seeds[(m.group(1), int(m.group(2)), int(m.group(3)))] = m.group(6) == "yes"
other = sorted(k for k, v in seeds.items() if not v)
print("  fits with other seeds in m3_examine: %d %s" % (len(other), other))
mk = sorted((k[0], k[1], k[2]) for k, _ in moved)
print("  the moved fits are those with other seeds: %s" % (mk == other))
ex = {}
for v, d in (("1.3.0", da), ("1.4.0", db)):
    ex[v] = sum(1 for k, r in d.items() if k[0] == "I.16.6" and r.get("status") == "EXACT")
print("  I.16.6 exact:", ex)

# small data
a = jl(os.path.join(B13, "small_data_release.jsonl"))
b = jl(os.path.join(B14, "small_data_release.jsonl"))
print("\nsmall_data_release: %d and %d records" % (len(a), len(b)))
for x, y in zip(a, b):
    sx, sy = strip(x), strip(y)
    if sx != sy:
        f = sorted(k for k in set(sx) | set(sy) if sx.get(k) != sy.get(k))
        print("  differs:", x.get("arm"), x.get("law"), x.get("seed"), f,
              x.get("size"), "->", y.get("size"))
print("  arms:", sorted({r.get("arm") for r in b}), " laws:", len({r.get("law") for r in b}))
