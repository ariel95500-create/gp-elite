"""M5 review 1: (1) the SHA-256 of the 29 files of gp_elite/ that
release/environments.txt gives for the wheel, against the files of the
candidate commit (git show 22f5734:gp_elite/...) and of 1.4.0 (6dc1e35);
(2) the names of A4: the two copies of core_names_1.4.0.txt, their count,
and how they compare with the names bound at the top of core.py of 1.4.0
(read with ast, never imported); (3) the tests of tests/test_door.py,
counted with ast (parametrised tests expanded by the length of a literal
list or of the names file).

Does not import gp_elite and runs no fit.

    python3 -I wheel_and_names.py <repo root>
"""
import ast
import hashlib
import os
import re
import subprocess
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."


def git_bytes(rev, path):
    p = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (rev, path)], capture_output=True)
    return p.stdout if p.returncode == 0 else None


print("== (1) the files of the wheel against the candidate 22f5734")
env = open(os.path.join(ROOT, "benchmarks/results_1.5/release/environments.txt")).read()
sec = env.split("== the files of gp_elite/ in the wheel (SHA-256)")[1]
rows = re.findall(r"^([0-9a-f]{64}) (gp_elite/\S+)$", sec, re.M)
print("files listed:", len(rows))
same_cand = same_140 = 0
for h, path in rows:
    b = git_bytes("22f5734", path)
    hc = hashlib.sha256(b).hexdigest() if b is not None else None
    b14 = git_bytes("6dc1e35", path)
    h14 = hashlib.sha256(b14).hexdigest() if b14 is not None else None
    same_cand += h == hc
    same_140 += h == h14
    if h != hc:
        print("  DIFFERENT from 22f5734:", path)
print("same as 22f5734: %d of %d; same as 1.4.0 (6dc1e35): %d" % (same_cand, len(rows), same_140))
print("unchanged since 1.4.0:", [p for h, p in rows if git_bytes("6dc1e35", p) is not None
                                 and hashlib.sha256(git_bytes("6dc1e35", p)).hexdigest() == h])
files_cand = subprocess.run(["git", "-C", ROOT, "ls-tree", "--name-only", "22f5734", "gp_elite/"],
                            capture_output=True, text=True).stdout.split()
print("files of gp_elite/ in the tree of 22f5734:", len(files_cand),
      "not in the list:", sorted(set(files_cand) - {p for _h, p in rows}))

print()
print("== (2) the names of A4")
a = open(os.path.join(ROOT, "benchmarks/results_1.5/split/core_names_1.4.0.txt")).read()
b = open(os.path.join(ROOT, "tests/core_names_1.4.0.txt")).read()
print("the two copies identical:", a == b)
lines = a.splitlines()
comments = [l for l in lines if l.startswith("#")]
names = [l.strip() for l in lines if l.strip() and not l.startswith("#")]
print("comment lines:", comments)
print("names:", len(names), "distinct:", len(set(names)))
src14 = git_bytes("6dc1e35", "gp_elite/core.py").decode("utf-8")
print("core.py of 1.4.0: %d lines" % len(src14.splitlines()))
t = ast.parse(src14)
bound = set()
for node in t.body:
    for sub in ast.walk(node) if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) else [node]:
        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(sub.name)
        elif isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
            bound.add(sub.id)
        elif isinstance(sub, (ast.Import, ast.ImportFrom)):
            for al in sub.names:
                bound.add((al.asname or al.name).split(".")[0])
        if sub is not node and isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            pass
top_defs = [n for n in t.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
print("top-level functions and classes of core.py 1.4.0:", len(top_defs))
dunder = [n for n in names if n.startswith("__")]
print("names of the list that start with __:", dunder)
not_bound = sorted(set(names) - bound - set(dunder))
print("names of the list not bound at the top of core.py 1.4.0 (by ast, a rough check):", not_bound[:30], len(not_bound))

print()
print("== the names of 1.5's gp_elite.core: does core.py at HEAD bind or import each of the 421?")
src15 = open(os.path.join(ROOT, "gp_elite/core.py"), encoding="utf-8").read()
t15 = ast.parse(src15)
bound15 = set()
for node in t15.body:
    if isinstance(node, ast.If):          # the __main__ block binds nothing for an importer
        continue
    for sub in ast.walk(node):
        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and sub in t15.body:
            bound15.add(sub.name)
        elif isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store) and node in t15.body \
                and not isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            bound15.add(sub.id)
        elif isinstance(sub, (ast.Import, ast.ImportFrom)):
            for al in sub.names:
                bound15.add(al.asname or al.name.split(".")[0])
state_names = set(re.findall(r"'([A-Za-z_][A-Za-z0-9_]*)'", src15.split("_STATE_NAMES = frozenset(")[1].split("))")[0]))
print("state names in the door:", len(state_names))
missing = sorted(set(names) - bound15 - state_names - set(dunder))
print("names of 1.4.0 neither bound by core.py at HEAD (outside the __main__ block) nor a state name:", missing)

print()
print("== (3) the tests of tests/test_door.py")
src = open(os.path.join(ROOT, "tests/test_door.py"), encoding="utf-8").read()
tt = ast.parse(src)
for node in tt.body:
    if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
        params = []
        for d in node.decorator_list:
            if isinstance(d, ast.Call) and getattr(d.func, "attr", "") == "parametrize":
                arg = d.args[1] if len(d.args) > 1 else None
                params.append(ast.unparse(arg)[:80] if arg is not None else "?")
        print("  %s %s" % (node.name, params))
