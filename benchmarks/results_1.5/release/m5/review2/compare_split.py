"""Review 2 of M5, question 1 and 2: compare 1.4.0's core.py with the modules of 1.5.

For every top-level statement of 1.4.0's core.py, find the statement of 1.5
that binds the same names, apply the rule of the shared state to the 1.4.0
side, and compare the two syntax trees (ast.dump, without positions).

The rule, as written in the task and in state.py:
- a state name (the 61 "data" names of map.txt) read, set or deleted as a
  module global anywhere in core.py becomes `state.NAME`;
- its `global` declarations go;
- `globals()` uses on a state name become: globals().get("X", d) ->
  getattr(state, "X", d); globals().get("X") -> getattr(state, "X", None);
  globals()["X"] (read, set) -> state.X; "X" in globals() -> hasattr(state, "X");
- the top-level assignments of state names go, unchanged, to state.py; the
  three memories become `state.X = Ctor()` where their class is.

Everything else must be identical. Also checked, on the 1.5 side:
- every name a module reads as a global is bound in that module or a builtin;
- `state` is read only as the module imported at the top;
- no state name is read, set or deleted as a bare global, imported by name,
  or captured at import time where 1.4.0 did not capture it.

Usage: python compare_split.py OLD_CORE NEW_PACKAGE_DIR MAP_TXT
"""
import ast
import builtins
import copy
import difflib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scopes import resolve, check_against_symtable  # noqa: E402

MODULES = ["state", "numeric", "config", "tree", "simplification", "evaluation",
           "datasets", "scoring", "fitting", "genetic", "memory", "final_choice",
           "seeds", "islands", "parallel", "search", "data", "console", "core"]


def load_state_names(map_txt):
    names = []
    lines = open(map_txt, encoding="utf-8").read().splitlines()
    inside = False
    for ln in lines:
        if ln.startswith("## Run-time names"):
            inside = True
            continue
        if inside and ln.startswith("## "):
            break
        if inside:
            parts = ln.split()
            if len(parts) >= 2 and parts[1] == "data":
                names.append(parts[0])
    return set(names)


def door_state_names(core_tree):
    for st in core_tree.body:
        if isinstance(st, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "_STATE_NAMES" for t in st.targets):
            call = st.value
            return set(ast.literal_eval(call.args[0]))
    return None


# ---------------------------------------------------------------- the rule
def _is_globals_call(n):
    return (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "globals" and not n.args and not n.keywords)


def _const_str(n):
    return n.value if isinstance(n, ast.Constant) and isinstance(n.value, str) else None


def _state_attr(name, ctx):
    return ast.Attribute(value=ast.Name(id="state", ctx=ast.Load()), attr=name, ctx=ctx)


class Rule(ast.NodeTransformer):
    """Apply the rewrite to a 1.4.0 statement whose Names carry `_res`."""

    def __init__(self, state_names, module_level_targets=True):
        self.S = state_names
        self.log = []            # (kind, name, line) of each rewrite applied

    def visit_Name(self, node):
        if node.id in self.S and getattr(node, "_res", None) == "global":
            self.log.append(("name", node.id, node.lineno))
            return ast.copy_location(_state_attr(node.id, node.ctx), node)
        return node

    def visit_Global(self, node):
        keep = [n for n in node.names if n not in self.S]
        if not keep:
            self.log.append(("global-dropped", ",".join(node.names), node.lineno))
            return None
        if len(keep) != len(node.names):
            self.log.append(("global-cut", ",".join(n for n in node.names if n in self.S), node.lineno))
        node.names = keep
        return node

    def visit_Call(self, node):
        # globals().get("X"[, d])
        f = node.func
        if (isinstance(f, ast.Attribute) and f.attr == "get" and _is_globals_call(f.value)
                and node.args and _const_str(node.args[0]) in self.S):
            name = _const_str(node.args[0])
            default = node.args[1] if len(node.args) > 1 else ast.Constant(value=None)
            self.log.append(("globals().get", name, node.lineno))
            new = ast.Call(func=ast.Name(id="getattr", ctx=ast.Load()),
                           args=[ast.Name(id="state", ctx=ast.Load()), ast.Constant(value=name),
                                 self.visit(default)], keywords=[])
            return ast.copy_location(new, node)
        self.generic_visit(node)
        return node

    def visit_Subscript(self, node):
        # globals()["X"]  (load or store)
        if _is_globals_call(node.value):
            sl = node.slice
            if isinstance(sl, ast.Index):        # Python < 3.9
                sl = sl.value
            name = _const_str(sl)
            if name in self.S:
                self.log.append(("globals()[]", name, node.lineno))
                return ast.copy_location(_state_attr(name, node.ctx), node)
        self.generic_visit(node)
        return node

    def visit_Compare(self, node):
        # "X" in globals()
        if (len(node.ops) == 1 and isinstance(node.ops[0], ast.In)
                and _is_globals_call(node.comparators[0]) and _const_str(node.left) in self.S):
            name = _const_str(node.left)
            self.log.append(("in globals()", name, node.lineno))
            new = ast.Call(func=ast.Name(id="hasattr", ctx=ast.Load()),
                           args=[ast.Name(id="state", ctx=ast.Load()), ast.Constant(value=name)],
                           keywords=[])
            return ast.copy_location(new, node)
        self.generic_visit(node)
        return node


def fix_empty_bodies(tree):
    """A body left empty by a dropped `global` would need a `pass`; flag it."""
    empties = []
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            b = getattr(node, field, None)
            if isinstance(b, list) and field == "body" and not b and not isinstance(node, ast.Module):
                empties.append(getattr(node, "lineno", 0))
    return empties


# ---------------------------------------------------------------- keys
def stmt_key(st):
    """What a top-level statement binds: ('def', name) or ('assign', targets)."""
    if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return ("def", st.name)
    if isinstance(st, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        tg = st.targets if isinstance(st, ast.Assign) else [st.target]
        return ("assign", tuple(ast.dump(t) for t in tg))
    if isinstance(st, (ast.Import, ast.ImportFrom)):
        return ("import", ast.dump(st))
    if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant) and isinstance(st.value.value, str):
        return ("docstring",)
    if isinstance(st, ast.If):
        return ("if", ast.dump(st.test))
    return ("other", ast.dump(st))


def dump(n):
    return ast.dump(n, include_attributes=False)


def unparse(n):
    try:
        return ast.unparse(n)
    except Exception:
        return dump(n)


def module_bindings(tree):
    """Names bound at the top level of a module (any statement kind)."""
    out = set()
    for st in tree.body:
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(st.name)
        elif isinstance(st, (ast.Import, ast.ImportFrom)):
            for a in st.names:
                out.add((a.asname or a.name).split(".")[0])
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)) \
                and getattr(node, "_res", None) == "global":
            out.add(node.id)
    return out


def main(old_path, new_dir, map_txt):
    out = []
    p = out.append
    S = load_state_names(map_txt)
    p("state names in map.txt (data): %d" % len(S))

    old_src = open(old_path, encoding="utf-8").read()
    old = ast.parse(old_src)
    old_scopes = resolve(old)
    n_checked, probs = check_against_symtable(old_src, old_path, old_scopes)
    p("scope resolver vs symtable on 1.4.0 core.py: %d function scopes compared, %d disagreements"
      % (n_checked, len(probs)))
    for s, a, b in probs[:20]:
        p("   %r: only mine %s; only symtable %s" % (s, a, b))

    new = {}
    new_src = {}
    for m in MODULES:
        path = os.path.join(new_dir, m + ".py")
        new_src[m] = open(path, encoding="utf-8").read()
        new[m] = ast.parse(new_src[m])
        sc = resolve(new[m])
        n2, pr2 = check_against_symtable(new_src[m], path, sc)
        if pr2:
            p("scope resolver vs symtable on %s.py: %d disagreements" % (m, len(pr2)))
    door = door_state_names(new["core"])
    p("state names in core._STATE_NAMES: %d; equal to map.txt: %s" % (len(door), door == S))
    st_bound = {t.id for st in new["state"].body if isinstance(st, (ast.Assign, ast.AnnAssign))
                for t in ([st.target] if isinstance(st, ast.AnnAssign) else st.targets)
                if isinstance(t, ast.Name)}
    p("names bound in state.py: %d; state names not bound there: %s; bound there but not state: %s"
      % (len(st_bound), sorted(S - st_bound), sorted(st_bound - S)))

    # index the top-level statements of 1.5
    index = {}
    for m in MODULES:
        for i, st in enumerate(new[m].body):
            index.setdefault(stmt_key(st), []).append((m, i, st))
    used = set()

    # ------------------------------------------------ statement by statement
    p("")
    p("## Statement by statement (1.4.0 core.py -> 1.5)")
    rewrites = []
    n_same = n_diff = n_missing = 0
    placement = []          # (old line, module, index) for the order check
    main_block_old = None
    for st in old.body:
        k = stmt_key(st)
        if k == ("docstring",):
            cands = [c for c in index.get(k, []) if c[0] == "core"]
            if cands and dump(cands[0][2]) == dump(st):
                p("docstring of core.py: identical in 1.5 core.py")
                used.add(("core", cands[0][1]))
            else:
                p("docstring of core.py: DIFFERENT")
            continue
        if isinstance(st, (ast.Import, ast.ImportFrom)):
            cands = [c for c in index.get(k, []) if c[0] == "core"]
            if cands:
                used.add(("core", cands[0][1]))
            else:
                p("import at line %d not found in 1.5 core.py: %s" % (st.lineno, unparse(st)))
            continue
        if isinstance(st, ast.If):
            main_block_old = st
            continue
        # statements whose targets are state names only, and that stay as they are
        names_bound = None
        if k[0] == "assign":
            tg = st.targets if isinstance(st, ast.Assign) else [st.target]
            names_bound = {n.id for t in tg for n in ast.walk(t) if isinstance(n, ast.Name)}
        if names_bound and names_bound <= S:
            cands = [c for c in index.get(k, []) if c[0] == "state"]
            if cands:
                m, i, nst = cands[0]
                used.add((m, i))
                if dump(nst) == dump(st):
                    n_same += 1
                    continue
                # values may differ only by comments: compare without the annotation strings
                n_diff += 1
                p("DIFF  line %d %s -> state.py: %s  !=  %s" % (st.lineno, sorted(names_bound),
                                                             unparse(st), unparse(nst)))
                continue
        # everything else: apply the rule, then look for the statement
        rule = Rule(S)
        tst = rule.visit(copy.deepcopy(st))
        for e in rule.log:
            rewrites.append((st.lineno, k, e))
        tk = stmt_key(tst)
        cands = [c for c in index.get(tk, []) if (c[0], c[1]) not in used]
        if not cands:
            n_missing += 1
            p("MISSING line %d %s: no statement of 1.5 binds %s" % (st.lineno, type(st).__name__, tk))
            continue
        if len(cands) > 1:
            p("NOTE line %d: %d statements of 1.5 bind %s: %s" % (
                st.lineno, len(cands), tk, [(c[0], c[2].lineno) for c in cands]))
        m, i, nst = cands[0]
        used.add((m, i))
        placement.append((st.lineno, m, i, tk))
        if dump(tst) == dump(nst):
            n_same += 1
        else:
            n_diff += 1
            a = unparse(tst).splitlines()
            b = unparse(nst).splitlines()
            p("DIFF  line %d %s -> %s.py line %d" % (st.lineno, tk, m, nst.lineno))
            for d in difflib.unified_diff(a, b, "1.4.0 after the rule", "1.5", lineterm="", n=1):
                p("      " + d)

    # the __main__ block
    p("")
    nb = [st for st in new["core"].body if isinstance(st, ast.If)
          and dump(st.test) == dump(main_block_old.test)]
    if nb:
        rule = Rule(S)
        tmb = rule.visit(copy.deepcopy(main_block_old))
        for e in rule.log:
            rewrites.append((main_block_old.lineno, ("if", "__main__"), e))
        used.add(("core", new["core"].body.index(nb[0])))
        if dump(tmb) == dump(nb[0]):
            p("the `if __name__ == \"__main__\":` block: identical after the rule")
        else:
            p("the `if __name__ == \"__main__\":` block: DIFFERENT after the rule")
            a, b = unparse(tmb).splitlines(), unparse(nb[0]).splitlines()
            for d in difflib.unified_diff(a, b, "1.4.0", "1.5", lineterm="", n=1):
                p("      " + d)
    else:
        p("the `if __name__ == \"__main__\":` block: NOT FOUND in 1.5 core.py")

    p("")
    p("statements of 1.4.0 (but docstring, imports and the __main__ block): identical %d, "
      "different %d, missing %d" % (n_same, n_diff, n_missing))

    # ------------------------------------------------ statements of 1.5 not mapped
    p("")
    p("## Top-level statements of 1.5 that no statement of 1.4.0 maps to")
    for m in MODULES:
        for i, st in enumerate(new[m].body):
            if (m, i) in used:
                continue
            k = stmt_key(st)
            if k[0] in ("docstring",) and m != "core":
                continue
            if k[0] == "import" and m != "core":
                continue
            txt = unparse(st).splitlines()
            p("  %s.py line %d: %s%s" % (m, st.lineno, txt[0][:110], " ..." if len(txt) > 1 else ""))

    # ------------------------------------------------ the rewrites applied
    p("")
    p("## The rewrites the rule applied to 1.4.0 (by kind)")
    from collections import Counter
    c = Counter(e[0] for (_, _, e) in rewrites)
    for kind, n in sorted(c.items()):
        p("  %-16s %d" % (kind, n))
    mod_level = [(ln, k, e) for (ln, k, e) in rewrites if k[0] != "def"]
    p("  rewrites in top-level statements other than def/class (module scope at import):")
    for ln, k, e in mod_level:
        p("    line %d %s: %s %s (line %d)" % (ln, k[0], e[0], e[1], e[2]))

    # ------------------------------------------------ order of the moved statements
    p("")
    p("## Order: statements of a module of 1.5 in the order of 1.4.0's file?")
    bym = {}
    for ln, m, i, tk in placement:
        bym.setdefault(m, []).append((i, ln, tk))
    for m in MODULES:
        seq = sorted(bym.get(m, []))
        lines = [ln for (_, ln, _) in seq]
        inversions = [(seq[j][2], seq[j][1], seq[j + 1][2], seq[j + 1][1])
                      for j in range(len(seq) - 1) if seq[j][1] > seq[j + 1][1]]
        if inversions:
            p("  %s.py: %d statements, %d out of the 1.4.0 order:" % (m, len(seq), len(inversions)))
            for a, la, b, lb in inversions:
                p("     %s (1.4.0 line %d) before %s (1.4.0 line %d)" % (a[1], la, b[1], lb))
        else:
            p("  %s.py: %d statements, in the order of 1.4.0" % (m, len(seq)))

    # ------------------------------------------------ checks on the 1.5 side
    p("")
    p("## Checks on the modules of 1.5")
    blt = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "__spec__", "__package__",
                                "__loader__", "__builtins__", "__path__", "__annotations__"}
    for m in MODULES:
        tree = new[m]
        scopes = resolve(tree)
        bound = module_bindings(tree)
        # 1. every global read is bound in the module or a builtin
        missing = {}
        for s in scopes:
            for n in s.names:
                if n._res == "global" and isinstance(n.ctx, ast.Load) and n.id not in bound \
                        and n.id not in blt:
                    missing.setdefault(n.id, []).append(n.lineno)
        if missing:
            p("  %s.py: names read as globals and bound nowhere in the module: %s" % (m, missing))
        # 2. `state` only as the module
        bad_state = [(n.lineno, n._res) for s in scopes for n in s.names
                     if n.id == "state" and n._res != "global"]
        st_store = [n.lineno for s in scopes for n in s.names
                    if n.id == "state" and n._res == "global" and not isinstance(n.ctx, ast.Load)]
        if bad_state or st_store:
            p("  %s.py: `state` used as a local %s or rebound at the top %s" % (m, bad_state, st_store))
        # 3. state names as bare globals (in state.py itself they are the definitions)
        if m != "state":
            bare = [(n.id, n.lineno, type(n.ctx).__name__) for s in scopes for n in s.names
                    if n.id in S and n._res == "global"]
            if bare:
                p("  %s.py: state names used as bare globals: %s" % (m, bare))
            local_named = sorted({(n.id, n._res) for s in scopes for n in s.names
                                  if n.id in S and n._res != "global"})
            if local_named:
                p("  %s.py: locals or attributes named like a state name (not globals): %s"
                  % (m, local_named))
        # 4. imports of state names, or of state itself under another name
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for a in node.names:
                    if a.name in S or (a.asname and a.asname in S):
                        p("  %s.py line %d: imports the state name %s" % (m, node.lineno, a.name))
                    if a.name == "state" and (a.asname not in (None, "state") or node.module):
                        p("  %s.py line %d: imports state as %s from %s" % (m, node.lineno, a.asname, node.module))
                if node.module in ("core", "state") and node.level >= 1:
                    p("  %s.py line %d: from .%s import %s" % (m, node.lineno, node.module,
                                                            [a.name for a in node.names]))
        # 5. state.X read at import time (module scope, defaults, decorators, class bodies)
        if m != "state":
            for s in scopes:
                if s.kind not in ("module", "class"):
                    continue
                for n in s.names:
                    pass
            at_import = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
                        and node.value.id == "state" \
                        and getattr(node.value, "_skind", None) in ("module", "class"):
                    at_import.append((node.attr, node.lineno, type(node.ctx).__name__))
            if at_import:
                p("  %s.py: state.X at module or class scope (run at import): %s" % (m, at_import))
        # 6. global / globals() left
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                p("  %s.py line %d: global %s" % (m, node.lineno, node.names))
            if _is_globals_call(node):
                p("  %s.py line %d: globals()" % (m, node.lineno))
    # 7. a name bound at the top of two modules (not by import)
    p("")
    defs = {}
    for m in MODULES:
        for st in new[m].body:
            k = stmt_key(st)
            if k[0] == "def":
                defs.setdefault(k[1], []).append(m)
            elif k[0] == "assign":
                tg = st.targets if isinstance(st, ast.Assign) else [st.target]
                for t in tg:
                    for n in ast.walk(t):
                        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                            defs.setdefault(n.id, []).append(m)
    twice = {k: v for k, v in defs.items() if len(v) > 1}
    p("names defined (not imported) at the top of more than one module of 1.5: %s" % (twice or "none"))
    print("\n".join(out))


if __name__ == "__main__":
    main(*sys.argv[1:4])
