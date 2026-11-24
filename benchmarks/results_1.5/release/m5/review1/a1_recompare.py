"""M5 review 1: A1 compared again, by a script of the review, from the raw
records of the runs. These runs are NOT committed: they are in /home/user
(a1_140 for 1.4.0, a1_140b its second run, a1_final for the engine in
modules at eb2eac5, a1_rel for the wheel of M1). Read only.

Field by field, every field but the time, the date and the path and version
of the engine (PLAN.md, A1). For the 13 configurations, every field of the
JSON but the time. For the console, the lines of its result (same pattern
as compare_a1.py) and gp_elite_best.txt; the full console.txt is also
compared, to say how much of it differs.

Does not import gp_elite (nor any bench script) and runs no fit.

    python3 -I a1_recompare.py
"""
import json
import os
import re

BASE = "/home/user"
EXCLUDE = {"time", "date", "engine_file", "engine_version", "time_s"}
CONFIGS = ["A_feyn", "B_cpu", "C_big", "D_units", "E_minmax", "F_robust", "G_restarts",
           "H_parallel", "I_sklearn", "J_extrap", "K_thorough", "L_standard", "M_twice"]
RESULT = re.compile(r"^\s*(force\s*=|.*[Cc]onstant|.*constante|.*kg)", re.M)


def jsonl(path, key):
    out = {}
    with open(path) as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                out[key(r)] = r
    return out


def compare_jsonl(a, b, name, key):
    ra = jsonl(os.path.join(BASE, a, name), key)
    rb = jsonl(os.path.join(BASE, b, name), key)
    diff = []
    for k in set(ra) | set(rb):
        if k not in ra or k not in rb:
            diff.append((k, "missing"))
            continue
        fa = {f: v for f, v in ra[k].items() if f not in EXCLUDE}
        fb = {f: v for f, v in rb[k].items() if f not in EXCLUDE}
        if fa != fb:
            diff.append((k, sorted(f for f in set(fa) | set(fb) if fa.get(f) != fb.get(f))))
    return len(ra), len(rb), diff, ra


def pair(a, b):
    print("== %s against %s" % (a, b))
    same_cfg = 0
    for c in CONFIGS:
        pa = os.path.join(BASE, a, "equiv", c + ".json")
        pb = os.path.join(BASE, b, "equiv", c + ".json")
        if not (os.path.exists(pa) and os.path.exists(pb)):
            print("   %s: missing" % c)
            continue
        ja = {k: v for k, v in json.load(open(pa)).items() if k not in EXCLUDE}
        jb = {k: v for k, v in json.load(open(pb)).items() if k not in EXCLUDE}
        if ja == jb:
            same_cfg += 1
        else:
            print("   %s DIFFERENT: %s" % (c, sorted(k for k in set(ja) | set(jb) if ja.get(k) != jb.get(k))))
    print("   13 configurations: %d identical" % same_cfg)
    na, nb, diff, ra = compare_jsonl(a, b, "phase1_defaults.jsonl",
                                     lambda r: (r["kind"], r["problem"], r["split"], r["seed"]))
    kinds = {}
    for k in ra:
        kinds[k[0]] = kinds.get(k[0], 0) + 1
    long_expr = sum(1 for r in ra.values() if len(r.get("expr", "")) >= 160)
    print("   phase1: %d and %d records %s, %d different; expressions cut at 160 characters: %d"
          % (na, nb, kinds, len(diff), long_expr))
    for d in diff[:5]:
        print("      ", d)
    if os.path.exists(os.path.join(BASE, a, "tp.jsonl")) and os.path.exists(os.path.join(BASE, b, "tp.jsonl")):
        na, nb, diff, ra = compare_jsonl(a, b, "tp.jsonl",
                                         lambda r: (r["arm"], r["exp"], r["n"], r["noise"], r["draw"]))
        print("   tp: %d and %d records, %d different" % (na, nb, len(diff)))
        for d in diff[:5]:
            print("      ", d)
    ca = os.path.join(BASE, a, "console", "console.txt")
    cb = os.path.join(BASE, b, "console", "console.txt")
    if os.path.exists(ca) and os.path.exists(cb):
        ta = open(ca, encoding="utf-8", errors="replace").read()
        tb = open(cb, encoding="utf-8", errors="replace").read()
        la = [l.strip() for l in RESULT.findall(ta)]
        lb = [l.strip() for l in RESULT.findall(tb)]
        ba = open(os.path.join(BASE, a, "console", "gp_elite_best.txt"), encoding="utf-8").read()
        bb = open(os.path.join(BASE, b, "console", "gp_elite_best.txt"), encoding="utf-8").read()
        lines_a, lines_b = ta.splitlines(), tb.splitlines()
        same_lines = sum(1 for x, y in zip(lines_a, lines_b) if x == y)
        print("   console: result lines same %s (%d lines), gp_elite_best.txt same %s; whole console.txt:"
              " %d and %d lines, %d equal line for line" % (la == lb, len(la), ba == bb,
                                                            len(lines_a), len(lines_b), same_lines))
    print()


pair("a1_140", "a1_140b")
pair("a1_140", "a1_final")
pair("a1_140", "a1_rel")
