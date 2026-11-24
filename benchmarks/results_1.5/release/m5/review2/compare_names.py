"""Review 2 of M5, question 4: compare the dumps of names_values.py for 1.4.0 and 1.5.

Usage: python compare_names.py names_values_1.4.0.json names_values_1.5.json CORE_NAMES_TXT
"""
import json
import sys
from collections import Counter


def main(a_path, b_path, names_txt):
    a, b = json.load(open(a_path)), json.load(open(b_path))
    A, B = a["names"], b["names"]
    listed = [l.strip() for l in open(names_txt) if l.strip() and not l.startswith("#")]
    print("1.4.0: python %s, engine %s, %d names in dir(core); 1.5: python %s, engine %s, %d names"
          % (a["python"], a["engine"], len(A), b["python"], b["engine"], len(B)))
    print("core_names_1.4.0.txt: %d names; equal to dir() of 1.4.0's core: %s"
          % (len(listed), sorted(listed) == sorted(A)))
    print("names of 1.4.0 missing on 1.5's core: %s" % (sorted(set(A) - set(B)) or "none"))
    print("names new on 1.5's core: %s" % sorted(set(B) - set(A)))
    diffs = Counter()
    data_diff, func_diff = [], []
    for n in sorted(set(A) & set(B)):
        x, y = A[n], B[n]
        if x == y:
            diffs["identical"] += 1
            continue
        keys = sorted(k for k in set(x) | set(y) if x.get(k) != y.get(k))
        diffs[",".join(keys)] += 1
        if "value" in keys or "type" in keys or "signature" in keys or "defaults" in keys \
                or "kwdefaults" in keys or "doc" in keys or "qualname" in keys:
            (data_diff if "value" in keys else func_diff).append((n, {k: (x.get(k), y.get(k)) for k in keys}))
    print("\nnames present in both, by what differs:")
    for k, c in sorted(diffs.items(), key=lambda kv: -kv[1]):
        print("  %4d  %s" % (c, k))
    print("\ndata whose value differs: %d" % len(data_diff))
    for n, d in data_diff:
        print("  %s: %s" % (n, d))
    print("\nfunctions or classes whose signature, defaults, doc or qualname differ: %d" % len(func_diff))
    for n, d in func_diff:
        print("  %s: %s" % (n, d))
    mods = Counter(y.get("module") for n, y in B.items() if "module" in y and y.get("module") != A.get(n, {}).get("module"))
    print("\n__module__ of functions and classes of 1.4.0's core, in 1.5: %s" % dict(sorted(mods.items())))
    print("functions whose __globals__ is vars(gp_elite.core): 1.4.0 %d, 1.5 %d" % (
        sum(1 for v in A.values() if v.get("globals_is_core_dict")),
        sum(1 for v in B.values() if v.get("globals_is_core_dict"))))
    va, vb = set(a["vars_has"]), set(b["vars_has"])
    print("\nnames in vars(gp_elite.core) in 1.4.0 but not in 1.5: %s" % sorted(va - vb))
    print("names of core.__annotations__: 1.4.0 %d, 1.5 %d" % (len(a["annotations"]), len(b["annotations"])))
    sa, sb = set(a["star_import"]), set(b["star_import"])
    print("`from gp_elite.core import *`: %d names in 1.4.0, %d in 1.5" % (len(sa), len(sb)))
    print("   in 1.4.0 only: %s" % sorted(sa - sb))
    print("   in 1.5 only: %s" % sorted(sb - sa))


if __name__ == "__main__":
    main(*sys.argv[1:4])
