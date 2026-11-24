"""M5 review 1: the counts of run-time names, recounted from the table of
split/map.txt (as committed now, and at 0a0090e, 81ed9c3 and c7e00fa through
`git show`), and the names of gp_elite/state.py read with the ast module.

Does not import gp_elite and runs no fit.

    python3 -I map_counts.py <repo root>
"""
import ast
import os
import re
import subprocess
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."


def git_show(rev, path):
    p = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (rev, path)],
                       capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else None


def count(text, label):
    print("==", label)
    head = [l for l in text.splitlines()[:8] if l.strip()]
    for l in head:
        if "run-time" in l or "lines" in l or "functions" in l:
            print("  header:", l)
    lines = text.splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if l.startswith("## Run-time names"))
    except StopIteration:
        print("  no table of run-time names")
        return None
    rows = []
    # the corrected map has a line of column headings under the heading; the first map has none
    first = start + 2 if lines[start + 1].startswith("name ") else start + 1
    for l in lines[first:]:
        if not l.strip() or l.startswith("#"):
            break
        rows.append(l)
    names = []
    kinds = {"data": 0, "function": 0}
    rebound = set_pkg = set_tests = 0
    for l in rows:
        parts = l.split(None, 2)
        name, kind = parts[0], parts[1]
        rest = parts[2] if len(parts) > 2 else ""
        names.append(name)
        if kind in kinds:
            kinds[kind] += 1
        if kind.startswith("rebound"):      # the first map has no column "holds"
            rest = l.split(None, 1)[1]
        m = re.search(r"rebound by ([^;\s]*)[;\s]", rest)
        if m and m.group(1).strip() != "-":
            rebound += 1
        m = re.search(r"set by ([^;\s]*)", rest)
        if m:
            s = m.group(1)
            if "gp_elite/" in s:
                set_pkg += 1
            if "tests/" in s:
                set_tests += 1
    print("  rows %d, data %d, function %d, rebound inside core %d, set by the package %d, set by the tests %d"
          % (len(rows), kinds["data"], kinds["function"], rebound, set_pkg, set_tests))
    if kinds["function"]:
        print("  functions:", [l.split()[0] for l in rows if l.split()[1] == "function"])
    return names


now = open(os.path.join(ROOT, "benchmarks/results_1.5/split/map.txt")).read()
names_now = count(now, "map.txt at HEAD")
for rev in ("0a0090e", "81ed9c3", "c7e00fa"):
    t = git_show(rev, "benchmarks/results_1.5/split/map.txt")
    if t is None:
        print("==", rev, ": no map.txt")
        continue
    count(t, "map.txt at %s" % rev)

print()
print("== gp_elite/state.py, read with ast")
src = open(os.path.join(ROOT, "gp_elite/state.py")).read()
tree = ast.parse(src)
assigned = []
annotated = []
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            for n in ast.walk(t):
                if isinstance(n, ast.Name):
                    assigned.append(n.id)
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        annotated.append(node.target.id)
print("names assigned at the top of state.py:", len(set(assigned)), "annotated:", len(annotated))
# names listed in a tuple or list (e.g. a list of the state's names)
lists = [n for n in tree.body if isinstance(n, ast.Assign)
         and isinstance(n.value, (ast.Tuple, ast.List, ast.Set))
         and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in n.value.elts)
         and len(n.value.elts) > 10]
for n in lists:
    print("a list of %d strings in state.py, assigned to %s" % (
        len(n.value.elts), [t.id for t in n.targets if isinstance(t, ast.Name)]))
table = now.split("## Run-time names")[1].split("## Names the benches")[0]
data_names = [l.split()[0] for l in table.splitlines() if re.match(r"^\S+\s+data\s", l)]
defined = set(assigned) | set(annotated)
print("data names in the run-time table of map.txt:", len(data_names))
print("defined in state.py (plain or annotated):", len(defined))
print("data names of map.txt not defined in state.py:", sorted(set(data_names) - defined))
print("names defined in state.py that are not data names of map.txt:", sorted(defined - set(data_names)))
print("total lines of state.py:", len(src.splitlines()))
