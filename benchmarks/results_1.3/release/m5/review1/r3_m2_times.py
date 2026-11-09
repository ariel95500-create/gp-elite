"""Review 1: times of the M2 fits stopped by their budget (README,
time_limit=), by version; and the U41 and TF78u indicators of details.txt.
python3 -I r3_m2_times.py"""
import os
import statistics as st
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_pair, pools, pool_of, SUITE  # noqa: E402

A, B, na, nb = load_pair()
for V, R in (("1.2.0", A), ("1.3.0", B)):
    t = sorted(r["time"] for r in R.values() if r.get("time_limit_reached"))
    print("%s: fits at budget %d, median %.3f, max %.2f, min %.2f" % (V, len(t), st.median(t), t[-1], t[0]))
    tall = sorted(r["time"] for r in R.values())
    print("    all fits: median %.2f, max %.2f" % (st.median(tall), tall[-1]))
    for kind in ("ufeyn", "utf"):
        tt = [r["time"] for r in R.values() if r["kind"] == kind]
        print("    %s median time %.3f" % (SUITE[kind], st.median(tt)))
    per = defaultdict(int)
    for r in R.values():
        if r["kind"] == "ufeyn":
            per[r["problem"]] += r["status"] == "EXACT"
    print("    U41 never exact:", sorted(p for p, n in per.items() if n == 0))
    per = defaultdict(int)
    for r in R.values():
        if r["kind"] == "feyn":
            per[r["problem"]] += r["status"] == "EXACT"
    print("    F41 never exact:", sorted(p for p, n in per.items() if n == 0))
    print("    F41 exact once:", sorted(p for p, n in per.items() if n == 1))
    print("    F41 exact per problem (not 5):", {p: n for p, n in sorted(per.items()) if n != 5})
    per = defaultdict(int)
    for r in R.values():
        if r["kind"] == "tf":
            per[r["problem"]] += r["status"] == "EXACT"
    print("    TF78 never exact: %d of %d" % (sum(n == 0 for n in per.values()), len(per)))
    per = defaultdict(int)
    for r in R.values():
        if r["kind"] == "utf":
            per[r["problem"]] += r["status"] == "EXACT"
    print("    TF78u never exact: %d of %d" % (sum(n == 0 for n in per.values()), len(per)))
    # the date span
    d = sorted(r["date"] for r in R.values())
    print("    dates", d[0], d[-1])
