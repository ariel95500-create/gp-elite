"""Review 2 of M5, questions 2 and 3: static checks that complete compare_split.py.

  python static_checks.py import_time   -> top-level statements of 1.4.0's core.py
      that execute code at import (calls, and module-level names they read)
  python static_checks.py shadowing     -> in each module of 1.5, a name both
      imported and defined, or imported from two places
  python static_checks.py layering      -> every relative import of the engine
      modules (top level or in a function) against the order of
      docs/architecture.md; absolute imports of api, core, formula, gp_elite
  python static_checks.py package_sets  -> the names the package outside the
      engine sets or deletes on gp_elite.core, state names or not
  python static_checks.py late_names    -> how 1.4.0 reads the three names a fit
      sets later (VAL_R2_TOLERANCE, _CUSTOM_LOSS_ROBUST, _CUSTOM_LOSS_USE_SCALING),
      and any `try` of 1.5 that catches AttributeError around a read of state.X
Paths are those of this checkout; run from this folder.
"""
import ast
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from scopes import resolve  # noqa: E402

PKG = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", "..", "gp_elite"))
OLD = os.path.join(HERE, "core_1.4.0.py")
ORDER = ["state", "numeric", "config", "tree", "simplification", "evaluation", "datasets", "scoring",
         "fitting", "genetic", "memory", "final_choice", "seeds", "islands", "parallel", "search",
         "data", "console", "core"]


def import_time():
    tree = ast.parse(open(OLD, encoding="utf-8").read())
    resolve(tree)
    toplevel = set()
    for st in tree.body:
        if isinstance(st, (ast.FunctionDef, ast.ClassDef)):
            toplevel.add(st.name)
        elif isinstance(st, (ast.Assign, ast.AnnAssign)):
            for t in (st.targets if isinstance(st, ast.Assign) else [st.target]):
                toplevel.update(n.id for n in ast.walk(t) if isinstance(n, ast.Name))

    def nodes_run(st):
        out = []

        def walk(n):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for d in n.decorator_list + n.args.defaults + [x for x in n.args.kw_defaults if x is not None]:
                    walk(d)
                return
            if isinstance(n, ast.Lambda):
                for d in n.args.defaults:
                    walk(d)
                return
            if isinstance(n, ast.ClassDef):
                for d in n.decorator_list + n.bases:
                    walk(d)
                for b in n.body:
                    walk(b)
                return
            out.append(n)
            for c in ast.iter_child_nodes(n):
                walk(c)
        walk(st)
        return out

    for st in tree.body:
        if isinstance(st, (ast.Import, ast.ImportFrom, ast.If)) or (isinstance(st, ast.Expr) and st.lineno == 1):
            continue
        ns = nodes_run(st)
        calls = sorted({ast.unparse(n.func) for n in ns if isinstance(n, ast.Call)})
        reads = sorted({n.id for n in ns if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in toplevel})
        if calls or reads:
            name = getattr(st, "name", None)
            if name is None:
                tg = st.targets if isinstance(st, ast.Assign) else [st.target]
                name = ",".join(sorted({n.id for t in tg for n in ast.walk(t) if isinstance(n, ast.Name)}))
            print("%5d %-28s calls=%s reads=%s" % (st.lineno, name[:28], calls, reads))


def shadowing():
    found = 0
    for m in ORDER:
        tree = ast.parse(open(os.path.join(PKG, m + ".py"), encoding="utf-8").read())
        imported, defined = collections.defaultdict(list), collections.defaultdict(list)
        for st in tree.body:
            if isinstance(st, ast.ImportFrom):
                for a in st.names:
                    imported[a.asname or a.name].append((st.module, st.lineno))
            elif isinstance(st, ast.Import):
                for a in st.names:
                    imported[(a.asname or a.name).split(".")[0]].append((a.name, st.lineno))
            elif isinstance(st, (ast.FunctionDef, ast.ClassDef)):
                defined[st.name].append(st.lineno)
            elif isinstance(st, (ast.Assign, ast.AnnAssign)):
                for t in (st.targets if isinstance(st, ast.Assign) else [st.target]):
                    for n in ast.walk(t):
                        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                            defined[n.id].append(st.lineno)
        for k, v in imported.items():
            if len(v) > 1 and len({x[0] for x in v}) > 1:
                print("%s.py: %s imported from several places %s" % (m, k, v)); found += 1
            if k in defined:
                print("%s.py: %s imported %s and defined at %s" % (m, k, v, defined[k])); found += 1
    print("modules checked: %d; cases: %d" % (len(ORDER), found))


def layering():
    bad, n = [], 0
    for i, m in enumerate(ORDER):
        tree = ast.parse(open(os.path.join(PKG, m + ".py"), encoding="utf-8").read())
        top = {id(s) for s in tree.body}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level >= 1:
                targets = [node.module.split(".")[0]] if node.module else [a.name for a in node.names]
                for t in targets:
                    n += 1
                    where = "top" if id(node) in top else "in a function, line %d" % node.lineno
                    if t not in ORDER:
                        bad.append("%s imports .%s (outside the engine) %s" % (m, t, where))
                    elif ORDER.index(t) >= i:
                        bad.append("%s imports .%s, which is not above it (%s)" % (m, t, where))
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[0] in ("api", "core", "formula", "gp_elite"):
                        bad.append("%s: import %s (line %d)" % (m, a.name, node.lineno))
    print("relative imports checked: %d" % n)
    for b in bad:
        print("  ", b)


def package_sets():
    S = set(json.load(open(os.path.join(HERE, "state_names.json"))))
    for f in ["api", "sklearn_api", "cli", "formula", "stability", "dimensions", "dim_search", "__init__", "__main__"]:
        tree = ast.parse(open(os.path.join(PKG, f + ".py"), encoding="utf-8").read())
        aliases = {"core"}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is None:
                for a in node.names:
                    if a.name == "core" and a.asname:
                        aliases.add(a.asname)
        sets = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in aliases \
                    and isinstance(node.ctx, (ast.Store, ast.Del)):
                sets.setdefault(node.attr, []).append(node.lineno)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("setattr", "delattr") \
                    and node.args and isinstance(node.args[0], ast.Name) and node.args[0].id in aliases:
                sets.setdefault("<%s(core, ...)>" % node.func.id, []).append(node.lineno)
        for k, v in sorted(sets.items()):
            print("%-12s sets core.%-26s %-11s lines %s" % (f + ".py", k, "(state)" if k in S else "(NOT state)", sorted(v)))


def late_names():
    tree = ast.parse(open(OLD, encoding="utf-8").read())
    resolve(tree)
    late = {"VAL_R2_TOLERANCE", "_CUSTOM_LOSS_ROBUST", "_CUSTOM_LOSS_USE_SCALING"}
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and n.id in late:
            print("1.4.0 line %d: %s as a bare name (%s, %s)" % (n.lineno, n.id, type(n.ctx).__name__, n._res))
        if isinstance(n, ast.Constant) and n.value in late:
            print("1.4.0 line %d: %r as a string (globals().get or globals()[...])" % (n.lineno, n.value))
    found = 0
    for p in sorted(glob.glob(os.path.join(PKG, "*.py"))):
        t = ast.parse(open(p, encoding="utf-8").read())
        for node in ast.walk(t):
            if not isinstance(node, ast.Try):
                continue
            catches = set()
            for h in node.handlers:
                if h.type is None:
                    catches.add("<bare except>")
                else:
                    catches.update(x.id for x in ast.walk(h.type) if isinstance(x, ast.Name))
            if "AttributeError" not in catches:
                continue
            reads = sorted({x.attr for b in node.body for x in ast.walk(b)
                            if isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name)
                            and x.value.id == "state" and isinstance(x.ctx, ast.Load)})
            if reads:
                found += 1
                print("%s line %d: a try catching AttributeError reads state.%s" % (os.path.basename(p), node.lineno, reads))
    print("try blocks of 1.5 catching AttributeError around a read of state.X: %d" % found)


if __name__ == "__main__":
    {"import_time": import_time, "shadowing": shadowing, "layering": layering,
     "package_sets": package_sets, "late_names": late_names}[sys.argv[1]]()
