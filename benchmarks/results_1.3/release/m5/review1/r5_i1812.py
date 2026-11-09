"""Review 1: I.18.12 in M2 and in the examination m2/examine/ (E1).
/venv12b/bin/python -I r5_i1812.py"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_pair  # noqa: E402

A, B, na, nb = load_pair()
for kind in ("feyn_n1", "feyn_n10", "ufeyn_n1", "ufeyn_n10"):
    for s in range(5):
        k = (kind, "I.18.12", "test", s)
        print(kind, s, "A", A[k]["structure"], A[k]["time_limit_reached"], A[k]["expr"][:60], "| B",
              B[k]["structure"], B[k]["time_limit_reached"], B[k]["expr"][:60])

D = "/home/user/gp-elite/benchmarks/results_1.3/release/m2/examine/"
for v in ("1.2.0", "1.3.0"):
    rr = [json.loads(l) for l in open(D + "e1_%s.jsonl" % v)]
    for kind in ("ufeyn_n10", "feyn_n10"):
        s = [r for r in rr if r["kind"] == kind]
        print(v, kind, len(s), "struct", sum(r["structure"] for r in s), "budget", sum(r["time_limit_reached"] for r in s),
              "median gens", float(np.median([r["generations"] for r in s])),
              "seeds", sorted({r["seed"] for r in s})[:3], "...", sorted({r["seed"] for r in s})[-1])
        for r in s:
            if not r["structure"]:
                e = r["expr"]
                para = ("v2²" in e or "v2 * v2" in e or e.count("v2") >= 2) and "tanh" not in e and "sin" not in e
                print("    seed %d parabola-like=%s: %s" % (r["seed"], para, e[:90]))

t = np.linspace(0, 3.14, 200001)
d = np.sin(t) - (1.24557 * t - 0.397444 * t ** 2)
print("max |sin - parabola| on [0,3.14]: %.4f; rms diff %.4f; rms sin %.4f; ratio %.3f" % (
    np.abs(d).max(), np.sqrt(np.mean(d ** 2)), np.sqrt(np.mean(np.sin(t) ** 2)),
    np.sqrt(np.mean(d ** 2)) / np.sqrt(np.mean(np.sin(t) ** 2))))
d2 = np.sin(t) - t * np.tanh(np.log(np.maximum(t, 1e-300)) - 1.14229) * -1.06594 / 1.00965
print("seed 11 of 1.2.0 (tanh form) vs sin, rms:", np.sqrt(np.mean(d2[1:] ** 2)))
