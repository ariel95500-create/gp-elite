"""M5 review 1: the modules of gp_elite read with the ast module (never
imported): their lines, their top-level names, and every import of a module
of the package, at the top or inside a function, to check the order of the
table of docs/architecture.md ("a module uses only the modules above it,
never one below it, and none imports core.py").

Does not import gp_elite and runs no fit.

    python3 -I modules_ast.py <repo root>
"""
import ast
import os
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
PKG = os.path.join(ROOT, "gp_elite")
ORDER = ["state", "numeric", "config", "tree", "simplification", "evaluation",
         "datasets", "scoring", "fitting", "genetic", "memory", "final_choice",
         "seeds", "islands", "parallel", "search", "data", "console", "core"]
OTHERS = ["__init__", "__main__", "api", "sklearn_api", "formula", "dimensions",
          "dim_search", "stability", "cli"]


def package_imports(tree, modname):
    """(target module, where, line) for every import of a module of the package."""
    out = []
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    def where(node):
        p = parents.get(node)
        while p is not None and not isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            p = parents.get(p)
        return "top" if p is None else "in %s" % p.name

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level >= 1:
                if node.module:            # from .x import y
                    out.append((node.module.split(".")[0], where(node), node.lineno))
                else:                      # from . import x, y
                    for a in node.names:
                        out.append((a.name, where(node), node.lineno))
            elif node.module and node.module.startswith("gp_elite"):
                parts = node.module.split(".")
                if len(parts) > 1:
                    out.append((parts[1], where(node), node.lineno))
                else:
                    for a in node.names:
                        out.append((a.name, where(node), node.lineno))
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name.startswith("gp_elite."):
                    out.append((a.name.split(".")[1], where(node), node.lineno))
        elif isinstance(node, ast.Call):
            # importlib.import_module("gp_elite.x") or __import__
            f = node.func
            name = getattr(f, "attr", None) or getattr(f, "id", None)
            if name in ("import_module", "__import__") and node.args and \
                    isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                v = node.args[0].value
                if "gp_elite" in v or v.startswith("."):
                    out.append((v, where(node), node.lineno))
    return out


def top_names(tree):
    names = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    names.append(t.id)
                elif isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name):
                    names.append("%s.%s" % (t.value.id, t.attr))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.append(node.target.id)
    return names


print("== lines, and the imports of package modules")
bad = []
for i, m in enumerate(ORDER + OTHERS):
    path = os.path.join(PKG, m + ".py")
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    imps = package_imports(tree, m)
    nlines = len(src.splitlines())
    targets = sorted({t for t, _w, _l in imps})
    print("%-15s %5d lines; imports %s" % (m, nlines, targets))
    if m in ORDER:
        for t, w, line in imps:
            if t in ORDER and ORDER.index(t) >= ORDER.index(m) and t != m:
                bad.append((m, t, w, line))
            if t == "core" and m != "core":
                bad.append((m, t, w, line))
    for t, w, line in imps:
        if w != "top":
            print("     inside a function: %s (%s, line %d)" % (t, w, line))
        if t == "core":
            print("     IMPORTS core: %s, line %d" % (w, line))
print()
print("modules of the table that import a module below them, or core:", bad or "none")

print()
print("== the top-level names of each module of the table")
for m in ORDER:
    tree = ast.parse(open(os.path.join(PKG, m + ".py"), encoding="utf-8").read())
    names = top_names(tree)
    funcs = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    print("%-15s %3d defs/classes: %s" % (m, len(funcs), ", ".join(funcs)))
    other = [n for n in names if n not in funcs]
    if other:
        print("%-15s     other top-level names: %s" % ("", ", ".join(other)))
