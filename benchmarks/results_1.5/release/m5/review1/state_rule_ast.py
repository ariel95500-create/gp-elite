"""M5 review 1: a static check, with the ast module, of what the documents
say of the shared state ("every function reads and sets them there, at the
moment it runs"): in each module of gp_elite but state.py,
  - a bare name (load or store) that is one of the 61 names of the state;
  - `from .state import ...`, or a `global` statement naming one of them;
  - `state.NAME` read when the module is imported or a function is defined
    (top-level statements, default values of parameters, decorators), which
    would be a copy taken at import.
Also: whether each of the 61 names is read or set somewhere as state.NAME,
and which of them a module of the engine ever sets (state.NAME = ... or
setattr(state, "NAME", ...)), as opposed to names only the tests or the
package set.

Does not import gp_elite and runs no fit.

    python3 -I state_rule_ast.py <repo root>
"""
import ast
import collections
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
PKG = os.path.join(ROOT, "gp_elite")
core_src = open(os.path.join(PKG, "core.py"), encoding="utf-8").read()
STATE = set(re.findall(r"'([A-Za-z_][A-Za-z0-9_]*)'",
                       core_src.split("_STATE_NAMES = frozenset(")[1].split("))")[0]))
print("names of the state in the door:", len(STATE))

mods = sorted(f[:-3] for f in os.listdir(PKG) if f.endswith(".py") and f != "state.py")
bare = []
imports = []
globs = []
at_import = []
uses = collections.Counter()
sets_by_engine = collections.defaultdict(set)


def is_state_attr(node):
    return (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
            and node.value.id in ("state", "_state") and node.attr in STATE)


for m in mods:
    src = open(os.path.join(PKG, m + ".py"), encoding="utf-8").read()
    tree = ast.parse(src)
    # names bound locally in functions shadow nothing at module level; a bare
    # load of a state name is a problem only if the module itself binds it
    # (a copy) or imports it.
    top_bound = set()
    for node in tree.body:
        for sub in ast.walk(node) if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) else []:
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                top_bound.add(sub.id)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            top_bound.add(node.name)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for al in node.names:
                top_bound.add(al.asname or al.name.split(".")[0])
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[-1] == "state":
            imports.append((m, node.lineno, [a.name for a in node.names]))
        if isinstance(node, ast.Global):
            hit = [n for n in node.names if n in STATE]
            if hit:
                globs.append((m, node.lineno, hit))
        if isinstance(node, ast.Name) and node.id in STATE:
            if node.id in top_bound or isinstance(node.ctx, ast.Store):
                bare.append((m, node.lineno, node.id, type(node.ctx).__name__))
        if is_state_attr(node):
            uses[node.attr] += 1
            if isinstance(node.ctx, ast.Store):
                sets_by_engine[node.attr].add(m)
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "setattr" and node.args \
                and isinstance(node.args[0], ast.Name) and node.args[0].id == "state" \
                and len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
            sets_by_engine[node.args[1].value].add(m + " (setattr)")
    # state.NAME evaluated at import: top-level statements (not defs), defaults, decorators
    for node in tree.body:
        exprs = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            exprs += node.args.defaults + [d for d in node.args.kw_defaults if d] + node.decorator_list
        elif isinstance(node, ast.ClassDef):
            exprs += node.decorator_list + node.bases
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    exprs += sub.args.defaults + [d for d in sub.args.kw_defaults if d] + sub.decorator_list
                elif not isinstance(sub, ast.ClassDef):
                    exprs.append(sub)
        elif isinstance(node, ast.If) and "__main__" in ast.unparse(node.test):
            continue
        else:
            exprs.append(node)
        for e in exprs:
            for sub in ast.walk(e):
                if is_state_attr(sub) and isinstance(sub.ctx, ast.Load):
                    at_import.append((m, getattr(sub, "lineno", "?"), sub.attr))

print("bare uses of a state name bound or imported at the top of a module:", bare or "none")
print("from .state import ...:", imports or "none")
print("global statements naming a state name:", globs or "none")
print("state.NAME read at import or at the definition of a function:", at_import or "none")
print("state names never used as state.NAME in the package:", sorted(STATE - set(uses)))
never_set = sorted(STATE - set(sets_by_engine))
print("state names that no module of the package ever sets (only the tests, or set once in state.py):",
      len(never_set), never_set)
