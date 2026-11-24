"""A small scope resolver for Python syntax trees (review 2 of M5).

resolve(tree) annotates every ast.Name node with `_res`, one of:
  'global'  the name is looked up in the module's globals at run time
  'local'   a local of a function, lambda or comprehension
  'free'    a variable of an enclosing function (closure)
  'class'   bound in the class body that reads it (LOAD_NAME: class dict, then globals)
and `_scope` (the Scope object it is read or bound in).

The rules are Python's: parameters, assignments, for/with/except targets,
imports, def and class names bind in their scope; `global` and `nonlocal`
declarations; class scopes are skipped when resolving free names; the first
iterable of a comprehension is evaluated in the enclosing scope; the target
of `:=` binds in the nearest enclosing non-comprehension scope; decorators,
defaults and bases are evaluated in the enclosing scope. Annotations are
walked in the enclosing scope as well (under `from __future__ import
annotations` they are never evaluated).

check_against_symtable(src, tree) compares, for every function scope, the set
of names this resolver calls global with what the symtable module says.
"""
import ast
import symtable

COMP = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


class Scope:
    def __init__(self, node, kind, parent, name):
        self.node, self.kind, self.parent, self.name = node, kind, parent, name
        self.bound, self.glob, self.nonloc = set(), set(), set()
        self.names = []          # every Name node read or bound directly here
        self.children = []
        if parent is not None:
            parent.children.append(self)

    def __repr__(self):
        return "<%s %s line %s>" % (self.kind, self.name, getattr(self.node, "lineno", 0))


def _arg_names(args):
    out = [a.arg for a in args.posonlyargs + args.args + args.kwonlyargs]
    if args.vararg:
        out.append(args.vararg.arg)
    if args.kwarg:
        out.append(args.kwarg.arg)
    return out


class _Builder:
    def __init__(self):
        self.scopes = []

    def new(self, node, kind, parent, name):
        s = Scope(node, kind, parent, name)
        self.scopes.append(s)
        return s

    def visit(self, node, scope):
        m = getattr(self, "v_" + type(node).__name__, None)
        if m is not None:
            m(node, scope)
        else:
            self.generic(node, scope)

    def generic(self, node, scope):
        for child in ast.iter_child_nodes(node):
            self.visit(child, scope)

    # bindings and reads
    def v_Name(self, node, scope):
        node._scope = scope
        scope.names.append(node)
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            scope.bound.add(node.id)

    def v_Global(self, node, scope):
        scope.glob.update(node.names)

    def v_Nonlocal(self, node, scope):
        scope.nonloc.update(node.names)

    def v_Import(self, node, scope):
        for a in node.names:
            scope.bound.add((a.asname or a.name).split(".")[0])

    def v_ImportFrom(self, node, scope):
        for a in node.names:
            if a.name != "*":
                scope.bound.add(a.asname or a.name)

    def v_ExceptHandler(self, node, scope):
        if node.name:
            scope.bound.add(node.name)
        self.generic(node, scope)

    def v_NamedExpr(self, node, scope):
        target_scope = scope
        while target_scope.kind == "comprehension":
            target_scope = target_scope.parent
        node.target._scope = target_scope
        target_scope.names.append(node.target)
        target_scope.bound.add(node.target.id)
        self.visit(node.value, scope)

    # scopes
    def _function(self, node, scope, name):
        for d in getattr(node, "decorator_list", []):
            self.visit(d, scope)
        a = node.args
        for d in a.defaults:
            self.visit(d, scope)
        for d in a.kw_defaults:
            if d is not None:
                self.visit(d, scope)
        for arg in a.posonlyargs + a.args + a.kwonlyargs + [a.vararg, a.kwarg]:
            if arg is not None and arg.annotation is not None:
                self.visit(arg.annotation, scope)
        if getattr(node, "returns", None) is not None:
            self.visit(node.returns, scope)
        inner = self.new(node, "function", scope, name)
        inner.bound.update(_arg_names(a))
        body = node.body if isinstance(node.body, list) else [node.body]
        for st in body:
            self.visit(st, inner)

    def v_FunctionDef(self, node, scope):
        scope.bound.add(node.name)
        self._function(node, scope, node.name)

    v_AsyncFunctionDef = v_FunctionDef

    def v_Lambda(self, node, scope):
        self._function(node, scope, "lambda")

    def v_ClassDef(self, node, scope):
        scope.bound.add(node.name)
        for d in node.decorator_list:
            self.visit(d, scope)
        for b in node.bases:
            self.visit(b, scope)
        for k in node.keywords:
            self.visit(k.value, scope)
        inner = self.new(node, "class", scope, node.name)
        for st in node.body:
            self.visit(st, inner)

    def _comp(self, node, scope):
        gens = node.generators
        self.visit(gens[0].iter, scope)
        inner = self.new(node, "comprehension", scope, type(node).__name__.lower())
        for i, g in enumerate(gens):
            self.visit(g.target, inner)
            if i > 0:
                self.visit(g.iter, inner)
            for c in g.ifs:
                self.visit(c, inner)
        if isinstance(node, ast.DictComp):
            self.visit(node.key, inner)
            self.visit(node.value, inner)
        else:
            self.visit(node.elt, inner)

    v_ListComp = v_SetComp = v_DictComp = v_GeneratorExp = _comp


def _resolve_one(name, scope):
    if scope.kind == "module":
        return "global"
    if name in scope.glob:
        return "global"
    if scope.kind == "class":
        if name in scope.bound:
            return "class"
    else:
        if name in scope.nonloc:
            return "free"
        if name in scope.bound:
            return "local"
    s = scope.parent
    while s is not None:
        if s.kind == "module":
            return "global"
        if s.kind == "class":
            s = s.parent
            continue
        if name in s.glob:
            return "global"
        if name in s.bound or name in s.nonloc:
            return "free"
        s = s.parent
    return "global"


def resolve(tree):
    """Annotate the Name nodes of `tree` (an ast.Module); return the scopes."""
    b = _Builder()
    mod = b.new(tree, "module", None, "<module>")
    for st in tree.body:
        b.visit(st, mod)
    for s in b.scopes:
        for n in s.names:
            n._res = _resolve_one(n.id, s)
            n._skind = s.kind
            # keep only strings on the nodes, so that copying a node is cheap
            if hasattr(n, "_scope"):
                del n._scope
    return b.scopes


def check_against_symtable(src, filename, scopes):
    """Compare the global names of each function scope with symtable's.

    Returns a list of disagreements (empty when they agree)."""
    top = symtable.symtable(src, filename, "exec")
    by_key = {}

    def walk(t):
        for c in t.get_children():
            if c.get_type() in ("function",):
                by_key.setdefault((c.get_name(), c.get_lineno()), []).append(c)
            walk(c)
    walk(top)
    problems = []
    checked = 0
    for s in scopes:
        if s.kind != "function" or s.name == "lambda":
            continue
        cands = by_key.get((s.name, s.node.lineno), [])
        if len(cands) != 1:
            continue
        st = cands[0]
        mine = {n.id for n in s.names if n._res == "global"} | (s.glob & {n.id for n in s.names})
        theirs = {sym.get_name() for sym in st.get_symbols()
                  if sym.is_global() and (sym.is_referenced() or sym.is_assigned())}
        checked += 1
        if mine != theirs:
            problems.append((s, sorted(mine - theirs), sorted(theirs - mine)))
    return checked, problems
