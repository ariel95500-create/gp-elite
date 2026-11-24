"""The modules of the split (Part A of ../PLAN.md), checked before any move.

layout.txt gives the modules in their order, the lower first, and the parts
of core.py that leave the module of their section (map_core.py, ROLES):

    order: numeric config tree ...
    move NAME module          # a function, a class or a name defined at the top

Each top-level statement of core.py (at 6dc1e35) goes to the module of its
section, or to the one layout.txt gives it. The names of the shared state
(map.txt, those that hold data) live in gp_elite.state and are read there
when the code runs, so they make no link between modules; nor does a
library imported at the top. A module may use only the names of modules
before it in the order: then each imports the names it needs from those,
and no module imports core.py, which imports them all back. The script
prints the links that go up the order (none when the layout holds), and,
for each module, its lines and what it imports from which module.

    python layout_core.py [layout.txt] > layout_check.txt
"""
import ast
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ARGS = sys.argv[1:]
sys.argv = sys.argv[:1]          # map_core reads a commit from sys.argv
import deps_core as D  # noqa: E402
import map_core as M  # noqa: E402
import symtable  # noqa: E402


def read_layout(path):
    order, moves, files = [], {}, {}
    for line in open(path, encoding="utf-8"):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("order:"):
            order += line.split(":", 1)[1].split()
        elif line.startswith("move "):
            _m, name, mod = line.split()
            moves[name] = mod
        elif line.startswith("file "):
            _f, role, mod = line.split()
            files[role] = mod
    return order, moves, files


def assignment(tree, binders, path):
    """id(statement) -> module, for the top-level statements of core.py."""
    order, moves, files = read_layout(path)

    def module_of(s):
        for n, bs in binders.items():
            if n in moves and any(b is s for b in bs):
                return moves[n]
        role = M.role_of(s.lineno)
        return files.get(role, role)
    return {id(s): module_of(s) for s in tree.body}


def state_names():
    text = open(os.path.join(HERE, "map.txt"), encoding="utf-8").read()
    sec = text.split("## Run-time names")[1].split("## Names the benches")[0]
    return {l.split()[0] for l in sec.splitlines()
            if len(l.split()) > 1 and l.split()[1] == "data"}


def is_library(stmt, name):
    """A binding made by an import, at the top or in a try or if block."""
    for sub in ast.walk(stmt):
        if isinstance(sub, (ast.Import, ast.ImportFrom)):
            if any((a.asname or a.name).split(".")[0] == name for a in sub.names):
                return True
    return False


def top_loads(s):
    """The names a statement at the top reads, less the names its
    comprehensions and lambdas bind for themselves."""
    own = set()
    for sub in ast.walk(s):
        if isinstance(sub, ast.comprehension):
            own |= {n.id for n in ast.walk(sub.target) if isinstance(n, ast.Name)}
        elif isinstance(sub, ast.Lambda):
            own |= {a.arg for a in sub.args.args + sub.args.kwonlyargs}
    out = set()
    for sub in ast.walk(s):
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load) and sub.id not in own:
            out.add(sub.id)
        elif isinstance(sub, ast.AnnAssign):
            pass
    if isinstance(s, ast.AnnAssign):       # the annotation is not evaluated
        out -= D.loads([s.annotation]) - D.loads([s.value] if s.value else [])
    return out


def main(path):
    order, moves, _files = read_layout(path)
    rank = {m: i for i, m in enumerate(order)}
    state = state_names()
    src = M.git_show("gp_elite/core.py")
    tree = ast.parse(src)
    top = symtable.symtable(src, "core.py", "exec")
    tables = {(t.get_name(), t.get_lineno()): t for t in top.get_children()}
    binders = D.bound_at_top(tree)
    where = assignment(tree, binders, path)
    unknown = sorted({m for m in where.values() if m not in rank})
    if unknown:
        raise SystemExit("modules not in the order: %s" % unknown)
    bad_moves = sorted(n for n in moves if n not in binders)
    if bad_moves:
        raise SystemExit("moved names not defined at the top: %s" % bad_moves)

    # core.py has `from __future__ import annotations`: no annotation is
    # evaluated, so none makes a link
    def at_definition(s):
        parts = list(s.decorator_list)
        if isinstance(s, ast.ClassDef):
            parts += s.bases + [k.value for k in s.keywords]
        else:
            parts += s.args.defaults + [d for d in s.args.kw_defaults if d is not None]
        return D.loads(parts)

    def uses(s):
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            t = tables.get((s.name, s.lineno))
            body = D.globals_of(t) if t is not None else D.loads([s])
            return (body | at_definition(s)) - {s.name}
        return top_loads(s)

    up = []
    imports = collections.defaultdict(lambda: collections.defaultdict(set))
    lines = collections.Counter()
    for s in tree.body:
        m = where[id(s)]
        lines[m] += s.end_lineno - s.lineno + 1
        for n in uses(s) - state:
            for b in binders.get(n, []):
                if b is s or is_library(b, n):
                    continue
                mb = where[id(b)]
                if mb == m:
                    continue
                if rank[mb] > rank[m]:
                    up.append((m, mb, getattr(s, "name", "line %d" % s.lineno), n))
                else:
                    imports[m][mb].add(n)

    print("# The modules of the split, checked on core.py at %s (%s)" % (M.REV, os.path.basename(path)))
    print()
    print("order: %s" % " < ".join(order))
    print("parts moved out of their section: %d" % len(moves))
    print()
    print("## Links that go up the order: %d" % len(up))
    for m, mb, part, n in sorted(up):
        print("  %-10s -> %-10s %s uses %s" % (m, mb, part, n))
    print()
    print("## Each module: its lines, and what it imports")
    for m in order:
        print("%-10s %5d lines" % (m, lines[m]))
        for mb in sorted(imports[m], key=lambda x: rank[x]):
            print("    from %-10s %s" % (mb, ", ".join(sorted(imports[m][mb]))))
    return not up


if __name__ == "__main__":
    path = next((a for a in ARGS if a.endswith(".txt")), os.path.join(HERE, "layout.txt"))
    sys.exit(0 if main(path) else 1)
