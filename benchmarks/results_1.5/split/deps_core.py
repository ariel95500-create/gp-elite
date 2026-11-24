"""The order of the moves of Part A of ../PLAN.md: which parts of core.py of
1.4.0 use which, read from its symbol tables (symtable, without running
anything).

For each function and class at the top of core.py, and each other statement
at the top (the constants, the caches, the imports), the module-level names
of core.py it uses: in its body (the names the symbol table says are
global), and, for a function or class, in what Python evaluates when it is
defined (decorators, default values, annotations, bases). Each part has the
role of its section in the map (map_core.py, ROLES). A name that a plain
import at the top binds (numpy, math...) is no link: any module imports it
itself; a name bound in a try or if block at the top (an optional
dependency) is one. A module made of a role can import only modules made
before it, never core.py, which imports them all back; so the roles that
use each other in a cycle cannot each be a module as they stand, and the
parts that close the cycle are listed.

    python benchmarks/results_1.5/split/deps_core.py [commit] > deps.txt
"""
import ast
import collections
import os
import symtable
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from map_core import REV, ROLES, git_show, role_of  # noqa: E402


def bound_at_top(tree):
    """name -> the top-level statements that bind it (walking into the
    if/try/with blocks at the top, not into functions and classes)."""
    out = collections.defaultdict(list)

    def names_of(target):
        if isinstance(target, ast.Name):
            yield target.id
        elif isinstance(target, (ast.Tuple, ast.List)):
            for t in target.elts:
                yield from names_of(t)
        elif isinstance(target, ast.Starred):
            yield from names_of(target.value)

    def visit(stmts, top):
        for s in stmts:
            t = top or s
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out[s.name].append(t)
            elif isinstance(s, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = s.targets if isinstance(s, ast.Assign) else [s.target]
                for tg in targets:
                    for n in names_of(tg):
                        out[n].append(t)
            elif isinstance(s, (ast.Import, ast.ImportFrom)):
                for a in s.names:
                    out[(a.asname or a.name).split(".")[0]].append(t)
            elif isinstance(s, (ast.For, ast.AsyncFor)):
                for n in names_of(s.target):
                    out[n].append(t)
                visit(s.body + s.orelse, t)
            elif isinstance(s, (ast.If, ast.While)):
                visit(s.body + s.orelse, t)
            elif isinstance(s, ast.Try):
                visit(s.body + s.orelse + s.finalbody, t)
                for h in s.handlers:
                    if h.name:
                        out[h.name].append(t)
                    visit(h.body, t)
            elif isinstance(s, (ast.With, ast.AsyncWith)):
                for it in s.items:
                    if it.optional_vars is not None:
                        for n in names_of(it.optional_vars):
                            out[n].append(t)
                visit(s.body, t)
    visit(tree.body, None)
    return out


def globals_of(table):
    """The global names a symbol table and the tables under it use."""
    out = set()
    for sym in table.get_symbols():
        if sym.is_global():
            out.add(sym.get_name())
    for child in table.get_children():
        out |= globals_of(child)
    return out


def loads(nodes):
    out = set()
    for node in nodes:
        if node is None:
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                out.add(sub.id)
    return out


def at_definition(node):
    """What Python evaluates when the function or class is defined."""
    parts = list(node.decorator_list)
    if isinstance(node, ast.ClassDef):
        parts += node.bases + [k.value for k in node.keywords]
    else:
        a = node.args
        parts += a.defaults + [d for d in a.kw_defaults if d is not None]
        parts += [x.annotation for x in a.posonlyargs + a.args + a.kwonlyargs]
        parts += [a.vararg.annotation if a.vararg else None,
                  a.kwarg.annotation if a.kwarg else None, node.returns]
    return loads(parts)


def main():
    src = git_show("gp_elite/core.py")
    tree = ast.parse(src)
    top = symtable.symtable(src, "core.py", "exec")
    tables = {(t.get_name(), t.get_lineno()): t for t in top.get_children()}
    future_annotations = any(isinstance(s, ast.ImportFrom) and s.module == "__future__"
                             and any(a.name == "annotations" for a in s.names)
                             for s in tree.body)
    binders = bound_at_top(tree)

    def part_name(s):
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return s.name
        return "line %d (%s)" % (s.lineno, type(s).__name__)

    uses = {}                       # top-level statement -> names it uses
    for s in tree.body:
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            t = tables.get((s.name, s.lineno))
            body = globals_of(t) if t is not None else loads([s])
            at_def = at_definition(s)
            if future_annotations and not isinstance(s, ast.ClassDef):
                at_def = loads(list(s.decorator_list) + s.args.defaults
                               + [d for d in s.args.kw_defaults if d is not None])
            uses[s] = (body | at_def) - {s.name}
        else:
            uses[s] = loads([s])

    edges = collections.defaultdict(lambda: collections.defaultdict(set))
    print("# What the parts of core.py at %s use (Part A of benchmarks/results_1.5/PLAN.md)" % REV)
    print()
    print("from __future__ import annotations: %s" % ("yes" if future_annotations else "no"))
    print()
    print("## Each function and class: the other roles whose names it uses")
    for s in tree.body:
        r = role_of(s.lineno)
        by_role = collections.defaultdict(set)
        for n in uses[s]:
            for b in binders.get(n, []):
                if isinstance(b, (ast.Import, ast.ImportFrom)):
                    continue            # a library: any module imports it itself
                rb = role_of(b.lineno)
                if b is not s and rb != r:
                    by_role[rb].add(n)
                    edges[r][rb].add((part_name(s), n))
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and by_role:
            print("%-6d %-10s %-34s %s" % (s.lineno, r, s.name[:34], "; ".join(
                "%s: %s" % (rb, ", ".join(sorted(ns))) for rb, ns in sorted(by_role.items()))))
    print()
    print("## Roles: which roles each uses (number of uses)")
    roles = sorted({m for _a, _b, m, _w in ROLES})
    for r in roles:
        print("%-10s -> %s" % (r, ", ".join("%s %d" % (rb, len(edges[r][rb]))
                                             for rb in sorted(edges[r])) or "-"))
    print()

    # cycles between roles: strongly connected components (Tarjan)
    index, low, stack, on, comps, counter = {}, {}, [], set(), [], [0]

    def strong(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on.add(v)
        for w in edges[v]:
            if w not in index:
                strong(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            comps.append(sorted(comp))
    for r in roles:
        if r not in index:
            strong(r)
    cycles = [c for c in comps if len(c) > 1]
    print("## Cycles between roles: %d" % len(cycles))
    for c in cycles:
        print("roles %s:" % ", ".join(c))
        for a in c:
            for b in c:
                if b in edges[a]:
                    pairs = sorted(edges[a][b])
                    print("   %s -> %s (%d): %s%s" % (a, b, len(pairs), "; ".join(
                        "%s uses %s" % p for p in pairs[:12]),
                        " ..." if len(pairs) > 12 else ""))
    print()
    order = [c for c in comps]      # Tarjan gives the components dependencies first
    print("## An order of the roles, the used before the users (a cycle as one block)")
    for c in order:
        print("  " + " + ".join(c))


if __name__ == "__main__":
    main()
