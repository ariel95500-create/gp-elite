"""The one change of code of Part A (../PLAN.md): the run-time names of
core.py that hold data go to gp_elite/state.py, and every function of
core.py reads and sets them there, at the moment it runs.

It reads gp_elite/core.py of the working tree and the run-time names of
map.txt that hold data, and writes:
  - gp_elite/state.py: those names that core.py defines at its top with a
    plain value (a literal, or a NumPy call on literals), in the order of
    core.py;
  - gp_elite/core.py, rewritten:
      * every use of such a name that reaches the module's global (in a
        function, a class, a lambda, a comprehension, or at the top)
        becomes state.NAME;
      * `global NAME` loses the name, and the line goes when no name is
        left;
      * globals()["NAME"] becomes state.NAME, globals().get("NAME", d)
        becomes getattr(state, "NAME", d), and "NAME" in globals() becomes
        hasattr(state, "NAME");
      * the plain definitions moved to state.py go;
      * `from . import state` comes after `from __future__ import ...`;
      * the door comes before `if __name__ == "__main__":` (DOOR below):
        a name of the shared state read on gp_elite.core is read on
        gp_elite.state, and set on gp_elite.core is set there; any other
        name set on gp_elite.core is also set in the engine's modules that
        hold the same object, as every function of core.py saw it in 1.4.0.

The rewrite is made on the text, then checked on the syntax trees: the tree
of the new core.py must equal the tree of the old one transformed node by
node by the rules above (positions aside), and state.py must hold exactly
the definitions taken out. Anything else stops the script, and nothing is
written.

    python state_rewrite.py           # rewrite gp_elite/core.py, write state.py
    python state_rewrite.py --dry     # check only
"""
import ast
import collections
import copy
import os
import symtable
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
CORE = os.path.join(ROOT, "gp_elite", "core.py")
STATE = os.path.join(ROOT, "gp_elite", "state.py")
ALIAS = "state"

STATE_HEADER = '''"""The shared state of the engine: the names of gp_elite.core of 1.4.0
that change while it runs (benchmarks/results_1.5/split/map.txt).

Every function of the engine reads and sets them here, at the moment it
runs (`state.NAME`), never through a copy; gp_elite.core passes on to this
module the names set on it. The values below are those core.py gave them
when it was imported. Three are not defined until a fit sets them, as in
1.4.0: VAL_R2_TOLERANCE, _CUSTOM_LOSS_ROBUST, _CUSTOM_LOSS_USE_SCALING. The
three memories (FRAGMENT_LIB, COGRAPH, SEQ_MEM) are made by gp_elite.core
when it is imported, at the place where 1.4.0 made them.
"""
from __future__ import annotations

import numpy as np

'''

DOOR = '''
# ── The door ─────────────────────────────────────────────────────────────
# gp_elite.core keeps every name it had in 1.4.0. The names of the shared
# state live in gp_elite.state: read on gp_elite.core, they are read there;
# set on it, they are set there. Any other name set on gp_elite.core (a
# test that replaces a function, a bench that wraps one) is also set in the
# engine's modules that hold the same object, as every function of core.py
# saw it in 1.4.0.
_STATE_NAMES = frozenset(%(names)r)
_ENGINE_MODULES = ()          # the modules made of core.py, as they come
_MISSING = object()


def __getattr__(name):
    if name in _STATE_NAMES and hasattr(state, name):
        return getattr(state, name)
    raise AttributeError("module %%r has no attribute %%r" %% (__name__, name))


def __dir__():
    return sorted(set(globals()) | {n for n in _STATE_NAMES if hasattr(state, n)})


class _Door(type(sys)):
    def __setattr__(self, name, value):
        if name in _STATE_NAMES:
            setattr(state, name, value)
            return
        old = self.__dict__.get(name, _MISSING)
        if old is not _MISSING:
            for m in _ENGINE_MODULES:
                if getattr(m, name, _MISSING) is old:
                    setattr(m, name, value)
        super().__setattr__(name, value)

    def __delattr__(self, name):
        if name in _STATE_NAMES:
            delattr(state, name)
            return
        old = self.__dict__.get(name, _MISSING)
        if old is not _MISSING:
            for m in _ENGINE_MODULES:
                if getattr(m, name, _MISSING) is old:
                    delattr(m, name)
        super().__delattr__(name)


sys.modules[__name__].__class__ = _Door

'''


def state_names():
    text = open(os.path.join(HERE, "map.txt"), encoding="utf-8").read()
    sec = text.split("## Run-time names")[1].split("## Names the benches")[0]
    out = set()
    for line in sec.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "data":
            out.add(parts[0])
    return out


def _const_str(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _is_globals_call(node):
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "globals" and not node.args and not node.keywords)


def _comp_name(node):
    return {ast.ListComp: "listcomp", ast.SetComp: "setcomp",
            ast.DictComp: "dictcomp", ast.GeneratorExp: "genexpr"}[type(node)]


class Resolver:
    """Which uses of the names reach the module's global, read from the
    symbol tables, scope by scope."""

    def __init__(self, src, names):
        self.names = names
        self.top = symtable.symtable(src, "core.py", "exec")
        self.taken = collections.defaultdict(int)

    def child(self, table, key):
        found = [c for c in table.get_children()
                 if (c.get_lineno(), c.get_name()) == key]
        i = self.taken[(id(table), key)]
        self.taken[(id(table), key)] += 1
        if i >= len(found):
            raise SystemExit("no symbol table for %s under %s" % (key, table.get_name()))
        return found[i]

    @staticmethod
    def is_global(table, name):
        if table.get_type() == "module":
            return True
        try:
            return table.lookup(name).is_global()
        except KeyError:
            return True

    def scan(self, tree):
        """[(node, kind)]: the Name nodes to rewrite ("name"), the global
        statements to trim ("global"), the globals() forms ("dict")."""
        out = []

        def walk(node, table):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                a = node.args
                for d in node.decorator_list + a.defaults + [x for x in a.kw_defaults if x]:
                    walk(d, table)
                child = self.child(table, (node.lineno, node.name))
                for s in node.body:
                    walk(s, child)
                return
            if isinstance(node, ast.ClassDef):
                for d in node.decorator_list + node.bases + [k.value for k in node.keywords]:
                    walk(d, table)
                child = self.child(table, (node.lineno, node.name))
                for s in node.body:
                    walk(s, child)
                return
            if isinstance(node, ast.Lambda):
                for d in node.args.defaults + [x for x in node.args.kw_defaults if x]:
                    walk(d, table)
                child = self.child(table, (node.lineno, "lambda"))
                walk(node.body, child)
                return
            if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                walk(node.generators[0].iter, table)
                child = self.child(table, (node.lineno, _comp_name(node)))
                for i, g in enumerate(node.generators):
                    walk(g.target, child)
                    if i:
                        walk(g.iter, child)
                    for c in g.ifs:
                        walk(c, child)
                if isinstance(node, ast.DictComp):
                    walk(node.key, child)
                    walk(node.value, child)
                else:
                    walk(node.elt, child)
                return
            if isinstance(node, ast.AnnAssign):
                # annotations are never evaluated (from __future__ import
                # annotations): only the target and the value count
                walk(node.target, table)
                if node.value is not None:
                    walk(node.value, table)
                return
            if isinstance(node, ast.arg):
                return                  # its annotation is not evaluated
            if isinstance(node, ast.Name):
                if node.id in self.names and self.is_global(table, node.id):
                    out.append((node, "name"))
                return
            if isinstance(node, ast.Global):
                if set(node.names) & self.names:
                    out.append((node, "global"))
                return
            form = globals_form(node, self.names)
            if form is not None:
                out.append((node, "dict"))
                for sub in form[2]:     # the default of get(), if any
                    walk(sub, table)
                return
            if isinstance(node, (ast.ExceptHandler,)) and node.name in self.names:
                raise SystemExit("line %d: except ... as %s" % (node.lineno, node.name))
            if isinstance(node, ast.NamedExpr) and node.target.id in self.names:
                raise SystemExit("line %d: %s :=" % (node.lineno, node.target.id))
            for c in ast.iter_child_nodes(node):
                walk(c, table)

        for s in tree.body:
            walk(s, self.top)
        return out


def globals_form(node, names):
    """(kind, name, [default]) for a use of the module's dictionary with a
    name of the state: "item" globals()["N"], "get" globals().get("N"[, d]),
    "in" / "notin" "N" in globals(); None otherwise. Any other use of
    globals() with such a name stops the script."""
    if isinstance(node, ast.Subscript) and _is_globals_call(node.value):
        n = _const_str(node.slice)
        if n in names:
            return ("item", n, [])
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and _is_globals_call(node.func.value)):
        n = _const_str(node.args[0]) if node.args else None
        if n in names:
            if node.func.attr != "get" or node.keywords or len(node.args) > 2:
                raise SystemExit("line %d: globals().%s(%r)" % (node.lineno, node.func.attr, n))
            return ("get", n, node.args[1:])
    if (isinstance(node, ast.Compare) and len(node.ops) == 1
            and isinstance(node.ops[0], (ast.In, ast.NotIn))
            and _is_globals_call(node.comparators[0])):
        n = _const_str(node.left)
        if n in names:
            return ("in" if isinstance(node.ops[0], ast.In) else "notin", n, [])
    return None


def state_attr(name, ctx):
    return ast.Attribute(value=ast.Name(id=ALIAS, ctx=ast.Load()), attr=name, ctx=ctx)


def expected(tree, marks, names):
    """The old tree transformed by the rules, for the check."""
    ids = {id(n): k for n, k in marks}

    class T(ast.NodeTransformer):
        def visit_Name(self, node):
            if ids.get(id(node)) == "name":
                return state_attr(node.id, node.ctx)
            return node

        def visit_Global(self, node):
            if ids.get(id(node)) == "global":
                keep = [n for n in node.names if n not in names]
                return ast.Global(names=keep) if keep else None
            return node

        def generic_visit(self, node):
            if ids.get(id(node)) == "dict":
                kind, n, dflt = globals_form(node, names)
                dflt = [self.visit(d) for d in dflt]
                if kind == "item":
                    return state_attr(n, node.ctx)
                if kind == "get":
                    return ast.Call(func=ast.Name(id="getattr", ctx=ast.Load()),
                                    args=[ast.Name(id=ALIAS, ctx=ast.Load()),
                                          ast.Constant(value=n)] + (dflt or [ast.Constant(value=None)]),
                                    keywords=[])
                call = ast.Call(func=ast.Name(id="hasattr", ctx=ast.Load()),
                                args=[ast.Name(id=ALIAS, ctx=ast.Load()), ast.Constant(value=n)],
                                keywords=[])
                return call if kind == "in" else ast.UnaryOp(op=ast.Not(), operand=call)
            return super().generic_visit(node)

    return T().visit(tree)


def plain_value(node):
    """A value state.py can hold without core.py: literals, and NumPy calls
    on literals."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and sub.id != "np":
            return False
    return True


def main(dry):
    names = state_names()
    src = open(CORE, encoding="utf-8").read()
    lines = src.splitlines(keepends=True)
    starts = [0]
    for l in lines:
        starts.append(starts[-1] + len(l))

    def off(lineno, col):
        # col_offset counts UTF-8 bytes; turn it into characters
        line = lines[lineno - 1]
        return starts[lineno - 1] + len(line.encode("utf-8")[:col].decode("utf-8"))

    def span(node):
        return off(node.lineno, node.col_offset), off(node.end_lineno, node.end_col_offset)

    def seg(node):
        a, b = span(node)
        return src[a:b]

    tree = ast.parse(src)
    marks = Resolver(src, names).scan(tree)

    # the plain definitions at the top that go to state.py: the first
    # definition of each name, whole lines (with a comment at their end)
    moved = []
    for s in tree.body:
        if isinstance(s, ast.Assign) and len(s.targets) == 1:
            t = s.targets[0]
        elif isinstance(s, ast.AnnAssign) and s.value is not None:
            t = s.target
        else:
            continue
        if (isinstance(t, ast.Name) and t.id in names and plain_value(s.value)
                and t.id not in {m[0] for m in moved}):
            moved.append((t.id, s))

    def whole_lines(node):
        a, b = starts[node.lineno - 1], starts[node.end_lineno]
        before = src[a:off(node.lineno, node.col_offset)]
        after = src[off(node.end_lineno, node.end_col_offset):b].strip()
        if before.strip() or (after and not after.startswith("#")):
            raise SystemExit("line %d: the statement shares its line" % node.lineno)
        return a, b

    edits = []                                  # (start, end, text)
    moved_spans = set()
    for _n, s in moved:
        a, b = whole_lines(s)
        edits.append((a, b, ""))
        moved_spans.add((a, b))
    for node, kind in marks:
        if any(a <= span(node)[0] < b for a, b in moved_spans):
            continue
        if kind == "name":
            a, b = span(node)
            edits.append((a, b, "%s.%s" % (ALIAS, node.id)))
        elif kind == "global":
            keep = [n for n in node.names if n not in names]
            if keep:
                a, b = span(node)
                edits.append((a, b, "global " + ", ".join(keep)))
            else:
                a, b = whole_lines(node)
                edits.append((a, b, ""))
        else:
            kind2, n, dflt = globals_form(node, names)
            a, b = span(node)
            if kind2 == "item":
                text = "%s.%s" % (ALIAS, n)
            elif kind2 == "get":
                text = "getattr(%s, %r%s)" % (ALIAS, n, "".join(", " + seg(d) for d in dflt) or ", None")
            elif kind2 == "in":
                text = "hasattr(%s, %r)" % (ALIAS, n)
            else:
                text = "not hasattr(%s, %r)" % (ALIAS, n)
            edits.append((a, b, text))
    # names inside a default of get() are rewritten inside the new text:
    # the default is copied from the old text, so rewrite its names there
    edits.sort(key=lambda e: (e[0], -e[1]))
    flat, last = [], -1
    for a, b, t in edits:
        if a < last:
            # an edit inside a globals().get(...) default: apply it to the
            # text of the enclosing edit
            pa, pb, pt = flat[-1]
            inner = src[a:b]
            old_default_text = src[pa:pb]
            if inner not in pt:
                raise SystemExit("an edit inside an edit at offset %d" % a)
            flat[-1] = (pa, pb, pt.replace(inner, t, 1))
            continue
        flat.append((a, b, t))
        last = b

    # the import and the door
    future = [s for s in tree.body if isinstance(s, ast.ImportFrom) and s.module == "__future__"]
    main_if = [s for s in tree.body if isinstance(s, ast.If) and isinstance(s.test, ast.Compare)
               and isinstance(s.test.left, ast.Name) and s.test.left.id == "__name__"]
    if len(future) != 1 or len(main_if) != 1:
        raise SystemExit("no single __future__ import or __main__ block")
    imp_at = starts[future[0].end_lineno]
    door_at = starts[main_if[0].lineno - 1]
    door = DOOR % dict(names=tuple(sorted(names)))
    flat.append((imp_at, imp_at, "from . import %s\n" % ALIAS))
    flat.append((door_at, door_at, door.lstrip("\n") + "\n"))
    flat.sort(key=lambda e: (e[0], e[1]))

    out, pos = [], 0
    for a, b, t in flat:
        out.append(src[pos:a])
        out.append(t)
        pos = b
    out.append(src[pos:])
    new = "".join(out)

    # the check on the trees
    want = ast.parse(src)
    marks2 = Resolver(src, names).scan(want)
    want = expected(want, marks2, names)
    want.body = [s for s in want.body if not any(
        isinstance(s, type(m)) and getattr(s, "lineno", -1) == m.lineno for _n, m in moved)]
    fut_i = next(i for i, s in enumerate(want.body) if isinstance(s, ast.ImportFrom)
                 and s.module == "__future__")
    want.body.insert(fut_i + 1, ast.parse("from . import %s\n" % ALIAS).body[0])
    main_i = next(i for i, s in enumerate(want.body) if isinstance(s, ast.If)
                  and isinstance(s.test, ast.Compare) and isinstance(s.test.left, ast.Name)
                  and s.test.left.id == "__name__")
    want.body[main_i:main_i] = ast.parse(door).body
    got = ast.parse(new)
    if ast.dump(want, include_attributes=False) != ast.dump(got, include_attributes=False):
        a, b = ast.dump(want, include_attributes=False), ast.dump(got, include_attributes=False)
        i = next(k for k in range(min(len(a), len(b))) if a[k] != b[k])
        raise SystemExit("the new core.py is not the old one transformed:\n  want ...%s\n  got  ...%s"
                         % (a[max(0, i - 200):i + 200], b[max(0, i - 200):i + 200]))

    # no use of a name of the state may still reach a global of core.py
    left = []

    def globals_left(table):
        for sym in table.get_symbols():
            if sym.get_name() in names and (table.get_type() == "module" or sym.is_global()):
                left.append((table.get_name(), table.get_lineno(), sym.get_name()))
        for c in table.get_children():
            globals_left(c)
    globals_left(symtable.symtable(new, "core.py", "exec"))
    if left:
        raise SystemExit("names of the state still used as globals: %s" % left[:10])
    # a name not defined at the top must not be read bare (it would raise
    # AttributeError where 1.4.0 raised NameError)
    defined = {t.id for s in tree.body if isinstance(s, (ast.Assign, ast.AnnAssign))
               for t in (s.targets if isinstance(s, ast.Assign) else [s.target])
               if isinstance(t, ast.Name)}
    for node, kind in marks:
        if kind == "name" and node.id not in defined and isinstance(node.ctx, ast.Load):
            raise SystemExit("line %d: %s is read bare and not defined at the top"
                             % (node.lineno, node.id))

    state_src = STATE_HEADER + "".join(src[a:b] for a, b in sorted(moved_spans))
    st = ast.parse(state_src)
    if [ast.dump(s) for s in st.body[3:]] != [ast.dump(s) for _n, s in moved]:
        raise SystemExit("state.py does not hold exactly the definitions taken out")
    counts = collections.Counter(k for _n, k in marks)
    print("names of the state: %d; moved to state.py: %d; kept in core.py as state.NAME = ...: %s"
          % (len(names), len(moved), sorted(
              {t.id for s in tree.body if isinstance(s, (ast.Assign, ast.AnnAssign))
               for t in (s.targets if isinstance(s, ast.Assign) else [s.target])
               if isinstance(t, ast.Name) and t.id in names} - {n for n, _s in moved})))
    print("rewritten: %d uses, %d global statements, %d uses of globals()"
          % (counts["name"], counts["global"], counts["dict"]))
    print("the check on the trees holds")
    if not dry:
        open(CORE, "w", encoding="utf-8").write(new)
        open(STATE, "w", encoding="utf-8").write(state_src)
        print("written: %s, %s" % (CORE, STATE))


if __name__ == "__main__":
    main("--dry" in sys.argv[1:])
