"""Shared helpers of review 1 (M5 of 1.3.0). Read-only: loads the M2
records and the pool of each problem, without importing the engine (a stub
stands in for gp_elite while feynman_bench defines PROBS)."""
import io
import json
import os
import sys
import types
from contextlib import redirect_stdout

ROOT = "/home/user/gp-elite"
BENCH = os.path.join(ROOT, "benchmarks")
REL = os.path.join(BENCH, "results_1.3", "release")
M2 = os.path.join(REL, "m2")

SUITE = {"feyn": "F41", "feyn_n1": "F41N1", "feyn_n10": "F41N10", "real": "R6",
         "realraw": "R7raw", "tf": "TF78", "ts": "TS14", "tr": "TR25",
         "trraw": "TR25raw", "ufeyn": "U41", "ufeyn_n1": "U41N1",
         "ufeyn_n10": "U41N10", "utf": "TF78u"}
UNIT_KINDS = ("ufeyn", "ufeyn_n1", "ufeyn_n10", "utf")


def load(path):
    out = {}
    n = 0
    for line in open(path):
        if line.strip():
            r = json.loads(line)
            n += 1
            out[(r["kind"], r["problem"], r["split"], r["seed"])] = r
    return out, n


def load_pair(a=os.path.join(M2, "campaignR_1.2.0.jsonl"),
              b=os.path.join(M2, "campaignR_1.3.0.jsonl")):
    A, na = load(a)
    B, nb = load(b)
    return A, B, na, nb


def pools():
    stub = types.ModuleType("gp_elite")
    stub.symbolic_regression = None
    saved = sys.modules.get("gp_elite")
    sys.modules["gp_elite"] = stub
    sys.path.insert(0, BENCH)
    try:
        with redirect_stdout(io.StringIO()):
            import feynman_bench as F
            import test_set as T
    finally:
        if saved is None:
            del sys.modules["gp_elite"]
    out = {p[0]: p[5] for p in F.PROBS}
    man = T.manifest()["datasets"]
    tf_ts = {}
    for n, e in man.items():
        if e["group"] in ("TF78", "TS14"):
            tf_ts[n] = e
    return out, man, F.PROBS


def pool_of(k, feyn_pools, man):
    if k[0] in ("real", "realraw", "tr", "trraw"):
        return "physical"
    if k[0] in ("tf", "utf", "ts"):
        return man[k[1]]["pool"]
    return feyn_pools[k[1]]
