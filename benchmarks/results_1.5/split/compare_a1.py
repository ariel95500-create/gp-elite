"""A1 of ../PLAN.md: do two engines return the same models? Compares the
outputs of run_a1.sh for two engines, field by field, every field but the
time, the date and the path and version of the engine.

  - the 13 configurations, by speed_equivalence.compare (everything but the
    time: the tree with its constants in float.hex, the printed formula, the
    errors, the size, formula_exact, the Pareto front);
  - the records of phase1_bench.py --defaults, job by job;
  - the records of the TP diagnostic, job by job;
  - the console example: the lines of its result (the formula it prints and
    the constant it deduces) and the formula it writes (gp_elite_best.txt);
    the console fixes no seed, so its other lines (the islands' prints, the
    statistics of the memory, the times) are not compared.

    python compare_a1.py <dir of engine A> <dir of engine B>
"""
import json
import os
import re
import sys

BENCH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      "..", ".."))
sys.path.insert(0, BENCH)

EXCLUDE = {"time", "date", "engine_file", "engine_version"}


def records(path, key):
    out = {}
    if os.path.exists(path):
        for line in open(path):
            if line.strip():
                r = json.loads(line)
                out[key(r)] = r
    return out


def compare_records(name, a, b, key):
    ra, rb = records(a, key), records(b, key)
    if not ra and not rb:
        print("%-8s no records" % name)
        return True
    keys = sorted(set(ra) | set(rb), key=str)
    missing = [k for k in keys if k not in ra or k not in rb]
    diff = []
    for k in keys:
        if k in ra and k in rb:
            fa = {f: v for f, v in ra[k].items() if f not in EXCLUDE}
            fb = {f: v for f, v in rb[k].items() if f not in EXCLUDE}
            fields = sorted(f for f in set(fa) | set(fb) if fa.get(f) != fb.get(f))
            if fields:
                diff.append((k, fields))
    print("%-8s %d jobs in A, %d in B, %d in one only, %d different" % (
        name, len(ra), len(rb), len(missing), len(diff)))
    for k, fields in diff[:20]:
        print("   DIFFERENT %s: %s" % (k, fields))
    for k in missing[:20]:
        print("   MISSING %s" % (k,))
    return not diff and not missing


RESULT = re.compile(r"^\s*(force\s*=|.*[Cc]onstant|.*constante|.*kg)", re.M)


def console_result(d):
    path = os.path.join(d, "console", "console.txt")
    if not os.path.exists(path):
        return None
    text = open(path, encoding="utf-8", errors="replace").read()
    lines = [l.strip() for l in RESULT.findall(text)]
    best = os.path.join(d, "console", "gp_elite_best.txt")
    return lines, (open(best, encoding="utf-8").read() if os.path.exists(best) else None)


def main(a, b):
    import speed_equivalence as SE
    ok = True
    print("== the 13 configurations")
    ok &= SE.compare(os.path.join(a, "equiv"), os.path.join(b, "equiv"))
    print("== the records")
    ok &= compare_records("phase1", os.path.join(a, "phase1_defaults.jsonl"),
                          os.path.join(b, "phase1_defaults.jsonl"),
                          lambda r: (r["kind"], r["problem"], r["split"], r["seed"]))
    ok &= compare_records("tp", os.path.join(a, "tp.jsonl"), os.path.join(b, "tp.jsonl"),
                          lambda r: (r["arm"], r["exp"], r["n"], r["noise"], r["draw"]))
    ca, cb = console_result(a), console_result(b)
    if ca is not None or cb is not None:
        same = ca == cb
        print("== the console: %s" % ("same result" if same else "DIFFERENT"))
        if not same:
            print("   A: %s" % (ca,))
            print("   B: %s" % (cb,))
        ok &= same
    print("ALL IDENTICAL" if ok else "DIFFERENCES")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1], sys.argv[2]) else 1)
