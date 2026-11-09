"""Shared, read-only helpers of the second review of M5 (1.3.0).

No import of the engine, of feynman_bench or of test_set: the pools are
read from the source with ast and from the manifest JSON.
"""
import ast
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 5))
M2 = os.path.join(ROOT, "benchmarks/results_1.3/release/m2")
A_PATH = os.path.join(M2, "campaignR_1.2.0.jsonl")
B_PATH = os.path.join(M2, "campaignR_1.3.0.jsonl")

SUITE = {"feyn": "F41", "feyn_n1": "F41N1", "feyn_n10": "F41N10", "real": "R6",
         "realraw": "R7raw", "tf": "TF78", "ts": "TS14", "tr": "TR25",
         "trraw": "TR25raw", "ufeyn": "U41", "ufeyn_n1": "U41N1",
         "ufeyn_n10": "U41N10", "utf": "TF78 under units"}
UNIT_KINDS = ("ufeyn", "ufeyn_n1", "ufeyn_n10", "utf")


def load(path):
    out = {}
    dup = 0
    for line in open(path):
        if line.strip():
            r = json.loads(line)
            k = (r["kind"], r["problem"], r["split"], r["seed"])
            dup += k in out
            out[k] = r
    return out, dup


def feyn_pools():
    """name -> pool, parsed from the first PROBS literal of feynman_bench.py."""
    src = open(os.path.join(ROOT, "benchmarks/feynman_bench.py")).read()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "PROBS" \
                and isinstance(node.value, ast.List):
            out = {}
            for elt in node.value.elts:
                name = elt.elts[0].value
                pool = elt.elts[5].value
                out[name] = pool
            return out
    raise RuntimeError("PROBS not found")


def manifest():
    return json.load(open(os.path.join(ROOT, "benchmarks/test_set/MANIFEST.json")))


def pools():
    out = dict(feyn_pools())
    m = manifest()["datasets"]
    for n, e in m.items():
        if e.get("group") in ("TF78", "TS14"):
            out[n] = e.get("pool")
    return out


def pool_of(k, P):
    if k[0] in ("real", "realraw", "tr", "trraw"):
        return "physical"
    return P.get(k[1], "?")


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if n == 0:
        return None
    return xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2])
