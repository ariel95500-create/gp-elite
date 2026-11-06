"""Second review: the smaller recomputations (TP notebook pair, scaling sums,
import medians, X1 arithmetic, H1 R6 difference, Nikuradse sizes)."""
import json, math, re, statistics as st
B = "/home/user/gp-elite/benchmarks/"
# TP notebook pair
for f in ("run1_1.1.0", "run2_1.1.0", "run1_1.2.0", "run2_1.2.0"):
    t = [int(x) for x in re.findall(r"formule trouv.e : .*\((\d+) s\)", open(B + "results_1.2/release/m3/tp_timing/notebook_pair/%s.txt" % f).read())]
    print(f, t, sum(t))
t = [int(x) for x in re.findall(r"formule trouv.e : .*\((\d+) s\)", open(B + "results_1.2/release/m3/notebook_tp_six_lois_1.2.0.txt").read())]
print("M3 notebook run", t, sum(t))
# scaling sums
for v in ("1.1", "1.2"):
    rs = [json.loads(l) for l in open(B + "results_%s/release/m3/scaling.jsonl" % v)]
    print(v, "scaling 1000:", round(sum(r["time"] for r in rs if r["n_total"] == 1000), 1), "10000:", round(sum(r["time"] for r in rs if r["n_total"] == 10000), 1))
# import medians
for v in ("1.1", "1.2"):
    xs = [float(x) for x in open(B + "results_%s/release/m3/import_time.txt" % v).read().split("\n")[1].split()]
    print(v, "import median", st.median(xs))
# X1 arithmetic
print("tau rc10/2%/d1", 1 / (-0.2 * math.log(0.00783301)), "tau rc20/2%/d1", 1 / (-0.2 * math.log(0.00784758)),
      "README", 1 / (-0.2 * math.log(0.00614708)), "battery", 1 / 0.51573, "I.6.20a", 0.11194 * math.log(0.0114856))
# notebook constants
print("g pendulum", (2 * math.pi / 2.00564) ** 2, "spring gap", 6.30042 / (2 * math.pi) - 1, "g fall", 2 * 4.87056, (2 * 4.87056) / 9.81 - 1,
      "R", 8.24992 / 8.314 - 1, "P", 4 * math.pi * 0.797624)
# H1 R6 medians
def med(p):
    rs = [json.loads(l) for l in open(B + "results_1.2/h1/campaign/" + p)]
    return st.median(r["r2"] for r in rs if r["kind"] == "real" and r["split"].startswith("fold"))
a, h = med("D_A.jsonl"), med("D_H1.jsonl")
print("R6 median A %.6f H1 %.6f diff %.5f" % (a, h, a - h))
