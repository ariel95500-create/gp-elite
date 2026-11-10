"""The reading of E2 written in PLAN.md in this folder.

  python e2_read.py e2_1.2.0.jsonl e2_1.3.0.jsonl
"""
import json
import sys
from math import comb


def load(path):
    return {(r["generations"], r["seed"]): r for r in map(json.loads, open(path))}


def sign_test(wins, n):
    """The test of part 3 of the notebook."""
    k = min(wins, n - wins)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2**n)


def med(v):
    v = sorted(v)
    n = len(v)
    return v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])


def main(a_path, b_path):
    a, b = load(a_path), load(b_path)
    print("fits: %d and %d, the same: %s; crashes: %d and %d; engines %s" % (
        len(a), len(b), set(a) == set(b),
        sum(r.get("status") == "CRASH" for r in a.values()),
        sum(r.get("status") == "CRASH" for r in b.values()),
        sorted({r.get("engine_version") for r in list(a.values()) + list(b.values())})))
    for g in sorted({k[0] for k in a}):
        ks = sorted(k for k in a if k[0] == g)
        higher = sum(b[k]["mse"] > a[k]["mse"] for k in ks)
        lower = sum(b[k]["mse"] < a[k]["mse"] for k in ks)
        n = higher + lower
        p = sign_test(lower, n) if n else 1.0
        verdict = ("1.3.0 worse" if higher > lower and p < 0.05 else
                   "1.3.0 better" if lower > higher and p < 0.05 else
                   "no difference shown")
        print("\n%d generations, %d seeds: 1.3.0 higher MSE in %d, lower in %d, "
              "equal in %d; sign test p = %.3f: %s" % (g, len(ks), higher, lower,
                                                       len(ks) - n, p, verdict))
        for v, d in (("1.2.0", a), ("1.3.0", b)):
            print("  %s: median MSE %.3e, median size %s, formula departs in %d, "
                  "arcsine in %d, median time %.1f s" % (
                      v, med([d[k]["mse"] for k in ks]), med([d[k]["size"] for k in ks]),
                      sum(d[k].get("formula_exact") is False for k in ks),
                      sum(bool(d[k].get("arcsin")) for k in ks),
                      med([d[k]["time"] for k in ks])))
        for k in ks:
            print("    seed %d: %.3e (%d) | %.3e (%d)%s" % (
                k[1], a[k]["mse"], a[k]["size"], b[k]["mse"], b[k]["size"],
                "  arcsine" if b[k].get("arcsin") else ""))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
