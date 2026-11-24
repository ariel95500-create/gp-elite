"""A plain move of Part A of ../PLAN.md: the parts of gp_elite/core.py that
layout.txt gives to one module go, as they are, to gp_elite/<module>.py, and
core.py imports their names back.

The module of a top-level statement of core.py is the one layout_core.py
gives it on core.py of 1.4.0, found by the names it defines. A statement
that defines no name goes with the one before it (the three memories made
at import go with their classes). The docstring, the imports and the door
stay in core.py, as does any statement whose names 1.4.0 did not have. Each
part moves with the comments and blank lines above it. The modules move in
the order of layout.txt, the lower first, so that a module imports only
from modules already made.

The new module: its docstring (MODULES below), `from __future__ import
annotations`, the imports of core.py's header that bind a name its text
uses, `from . import state` if it uses the shared state, `from .lower
import ...` for the names it takes from the modules already made, then the
parts in the order of core.py. In core.py, `from .<module> import ...`
brings back every name the parts define, after the imports already there,
and the door learns the new module.

Checked before anything is written: the statements of the new module after
its header are the statements taken out of core.py, unchanged (syntax
trees, positions aside); core.py is the old one without them, with the
import added and the door's list of modules grown; no part uses a name of
a module not made yet. After writing, gp_elite is imported in a fresh
process with /venv15s, and every name of gp_elite.core of 1.4.0
(core_names_1.4.0.txt) must be there.

    python move_group.py <module> [--dry]
"""
import ast
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
CORE = os.path.join(ROOT, "gp_elite", "core.py")
PY = "/venv15s/bin/python"
sys.path.insert(0, HERE)
_ARGS = sys.argv[1:]
sys.argv = sys.argv[:1]          # map_core reads a commit from sys.argv
import deps_core as D  # noqa: E402
import layout_core as L  # noqa: E402
import map_core as M  # noqa: E402

MODULES = {
    "numeric": "The protected operators of the engine, scalar and vectorised: the\n"
               "safe forms of the operations formulas use (division, power,\n"
               "logarithm, square root, exponential, tangent, arcsine...).",
    "config": "The configuration of a run: the run trace (TRACE), Config, the pools\n"
              "of operators and how a run draws from them, and the configurations\n"
              "the console makes (make_cfg, make_cfg_nd).",
    "tree": "The tree of a formula: Node, its hashes, its text (to_string) and its\n"
            "sympy form, its size, depth and complexity, and its constants.",
    "simplification": "The simplification of a tree, and its caches.",
    "evaluation": "The evaluation of a tree: the NumPy code it compiles to, the plans of\n"
                  "the Jacobian for Levenberg-Marquardt, the compiled functions and\n"
                  "their caches, the scalar and vector evaluation, Pearson's r, the cache\n"
                  "of predictions, and the safe writing of files.",
    "datasets": "The datasets the console builds: the Collatz (Syracuse) features and\n"
                "data, the decoy features, and build_dataset.",
    "scoring": "The score of a formula: linear and robust scaling, the errors, the\n"
               "scale of the target, the usage of the variables, and fitness.",
    "fitting": "The fitting of the constants of a formula: Levenberg-Marquardt and\n"
               "Adam.",
    "genetic": "The genetic operators: random trees (in one and in n dimensions),\n"
               "deduplication, epsilon-lexicase and tournament selection, crossover,\n"
               "the mutations, Pareto ranks and the stigmergic trees.",
    "memory": "The memories of the search: the fragment library, the probe set and\n"
              "the semantic signatures, the co-graph of fragments, the sequence\n"
              "memory, and what they pass on to the next run (warm_transfer).",
    "final_choice": "The final choice of the model: early stop, patience, the hold-out,\n"
                    "the finalists and their polish, the near domain, the rule of one\n"
                    "standard error, and the small tables.",
    "seeds": "The seeds placed before the first generation: motifs, power laws,\n"
             "binomial forms, elementary forms and noise-tolerant forms.",
    "islands": "The islands: Island, migration, one generation of an island\n"
               "(evolve_island), and the reset of the explorer islands.",
    "parallel": "The islands in parallel: the workers, the pools of processes, and the\n"
                "guard of the main module.",
    "search": "The search: the hold-out split, the linear candidate, and evolve,\n"
              "which runs a fit from the seeds to the final choice.",
    "data": "The data of the console: the scalers, the loading of CSV files and\n"
            "their optional dependencies, and the problems of the console.",
    "console": "The console: the printed result, the decoy report, the plot, run,\n"
               "the benchmark of the console and the interactive menu.",
}
TAIL = "\n\nPart of gp_elite/core.py until 1.4.0, moved without change in 1.5.\n"


def wrap_import(module, names, width=79):
    head = "from .%s import (" % module
    lines, line = [], head
    for i, n in enumerate(names):
        piece = n + ("," if i < len(names) - 1 else ")")
        if len(line) + len(piece) + 1 > width and line != head:
            lines.append(line.rstrip())
            line = " " * len(head) + piece
        else:
            line += ("" if line == head else " ") + piece
    lines.append(line)
    return "\n".join(lines) + "\n"


def main(module, dry):
    order, _moves, _files = L.read_layout(os.path.join(HERE, "layout.txt"))
    if module not in order or module == "core":
        raise SystemExit("not a module of layout.txt: %s" % module)

    # the module of each name, from core.py of 1.4.0
    old_src = M.git_show("gp_elite/core.py")
    old_tree = ast.parse(old_src)
    old_binders = D.bound_at_top(old_tree)
    old_where = L.assignment(old_tree, old_binders, os.path.join(HERE, "layout.txt"))
    module_of_name = {}
    for n, bs in old_binders.items():
        mods = {old_where[id(b)] for b in bs if not L.is_library(b, n)}
        if len(mods) == 1:
            module_of_name[n] = mods.pop()
    state = L.state_names()

    src = open(CORE, encoding="utf-8").read()
    lines = src.splitlines(keepends=True)
    starts = [0]
    for l in lines:
        starts.append(starts[-1] + len(l))
    tree = ast.parse(src)
    binders = D.bound_at_top(tree)
    names_of = {}
    for n, bs in binders.items():
        for b in bs:
            names_of.setdefault(id(b), set()).add(n)

    def is_main_block(s):
        return (isinstance(s, ast.If) and isinstance(s.test, ast.Compare)
                and isinstance(s.test.left, ast.Name) and s.test.left.id == "__name__")

    where, prev = {}, "core"
    for s in tree.body:
        if isinstance(s, (ast.Import, ast.ImportFrom)) or is_main_block(s) or (
                isinstance(s, ast.Expr) and s is tree.body[0]):
            where[id(s)] = "core"          # the docstring, the imports, __main__
            continue
        ns = names_of.get(id(s), set())
        mods = {module_of_name[n] for n in ns if n in module_of_name}
        if len(mods) > 1:
            raise SystemExit("line %d defines names of %s" % (s.lineno, sorted(mods)))
        if ns and not mods:
            where[id(s)] = "core"           # the door, new in 1.5
        else:
            where[id(s)] = mods.pop() if mods else prev
        prev = where[id(s)]

    rank = {m: i for i, m in enumerate(order)}
    left_lower = sorted({where[id(s)] for s in tree.body
                         if where[id(s)] != "core" and rank[where[id(s)]] < rank[module]})
    if left_lower:
        raise SystemExit("move these first: %s" % left_lower)
    moving = [s for s in tree.body if where[id(s)] == module]
    if not moving:
        raise SystemExit("nothing of %s is left in core.py" % module)
    ids = {id(s) for s in moving}

    # the text of each part: from the end of the statement before it
    chunks, cut = [], []
    for i, s in enumerate(tree.body):
        if id(s) not in ids:
            continue
        a = starts[tree.body[i - 1].end_lineno] if i else 0
        b = starts[s.end_lineno]
        chunks.append(src[a:b])
        cut.append((a, b))

    # what the parts use
    used, at_top = set(), set()
    for s in moving:
        for sub in ast.walk(s):
            if isinstance(sub, ast.Name):
                used.add(sub.id)
    uses_state = any(isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name)
                     and sub.value.id == "state" for s in moving for sub in ast.walk(s))
    defined = set()
    for s in moving:
        defined |= names_of.get(id(s), set())
    lib_imports = []
    for s in tree.body:
        if isinstance(s, (ast.Import, ast.ImportFrom)) and not (
                isinstance(s, ast.ImportFrom) and (s.level or s.module == "__future__")):
            bound = {(a.asname or a.name).split(".")[0] for a in s.names}
            if bound & used:
                lib_imports.append(ast.get_source_segment(src, s))
    # the names the parts really read at the top (globals of their scopes,
    # what is evaluated when they are defined), not their locals
    real = set()
    import symtable
    st = symtable.symtable(src, "core.py", "exec")
    tables = {(t.get_name(), t.get_lineno()): t for t in st.get_children()}
    for s in moving:
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            t = tables.get((s.name, s.lineno))
            real |= D.globals_of(t) if t is not None else used
            real |= D.loads(list(s.decorator_list) + (
                s.bases + [k.value for k in s.keywords] if isinstance(s, ast.ClassDef)
                else s.args.defaults + [d for d in s.args.kw_defaults if d is not None]))
        else:
            real |= D.loads([s])
    from_lower = {}
    for n in sorted((used & real) - defined - state - {"state"}):
        m = module_of_name.get(n)
        if m is None or m == module:
            continue
        if m == "core":
            if not any(L.is_library(b, n) for b in binders.get(n, [])):
                raise SystemExit("%s uses %s, which core.py keeps" % (module, n))
            continue
        if rank[m] > rank[module]:
            raise SystemExit("%s uses %s of %s, a module not made yet" % (module, n, m))
        from_lower.setdefault(m, set()).add(n)
    from_lower = {m: sorted(ns) for m, ns in from_lower.items()}

    header = '"""%s%s"""\nfrom __future__ import annotations\n\n' % (MODULES[module], TAIL)
    header += "".join(l + "\n" for l in lib_imports)
    rel = []
    if uses_state:
        rel.append("from . import state\n")
    for m in sorted(from_lower, key=lambda x: rank[x]):
        rel.append(wrap_import(m, from_lower[m]))
    if rel:
        header += "\n" + "".join(rel)
    body = "".join(chunks)
    new_module = header + "\n" + body.lstrip("\n")
    new_module = new_module.rstrip("\n") + "\n"

    # core.py: the parts out, the names back, the door's list grown
    back = wrap_import(module, sorted(defined))
    # after the imports at the head of core.py (those before its first
    # statement that is not an import)
    head = []
    for s in tree.body[1:]:
        if not isinstance(s, (ast.Import, ast.ImportFrom)):
            break
        head.append(s)
    if not any(isinstance(s, ast.ImportFrom) and s.level == 1 for s in head):
        raise SystemExit("no `from . import state` at the head of core.py")
    rel_imports = head
    at = starts[head[-1].end_lineno]
    door = [s for s in tree.body if isinstance(s, ast.Assign) and len(s.targets) == 1
            and isinstance(s.targets[0], ast.Name) and s.targets[0].id == "_ENGINE_MODULES"]
    if len(door) != 1:
        raise SystemExit("no single _ENGINE_MODULES in core.py")
    done = [m for m in order if m != "core" and rank[m] <= rank[module]]
    door_text = ("_ENGINE_MODULES = tuple(sys.modules[__package__ + \".\" + _m] for _m in (\n"
                 + "".join("    %r,\n" % m for m in done) + "))")
    da = starts[door[0].lineno - 1]
    db = starts[door[0].end_lineno]
    edits = sorted(cut + [(at, at), (da, db)])
    out, pos = [], 0
    for a, b in edits:
        out.append(src[pos:a])
        if (a, b) == (at, at):
            out.append(back)
        elif (a, b) == (da, db):
            out.append(door_text + "\n")
        pos = b
    out.append(src[pos:])
    new_core = "".join(out)

    # the checks on the trees
    got_mod = ast.parse(new_module)
    n_head = len(ast.parse(header).body)
    if [ast.dump(s) for s in got_mod.body[n_head:]] != [ast.dump(s) for s in moving]:
        raise SystemExit("the new module does not hold the parts unchanged")
    want_core = [s for s in tree.body if id(s) not in ids]
    i_back = want_core.index(rel_imports[-1]) + 1
    want_core.insert(i_back, ast.parse(back).body[0])
    i_door = next(i for i, s in enumerate(want_core) if s is door[0])
    want_core[i_door] = ast.parse(door_text).body[0]
    got_core = ast.parse(new_core)
    if [ast.dump(s) for s in got_core.body] != [ast.dump(s) for s in want_core]:
        raise SystemExit("the new core.py is not the old one without the parts")

    print("%s: %d statements, %d lines; imports %s; from lower modules: %s" % (
        module, len(moving), new_module.count("\n"),
        "+state" if uses_state else "-state",
        ", ".join("%s (%d)" % (m, len(ns)) for m, ns in from_lower.items()) or "-"))
    print("core.py: %d lines -> %d" % (src.count("\n"), new_core.count("\n")))
    if dry:
        return
    path = os.path.join(ROOT, "gp_elite", module + ".py")
    if os.path.exists(path):
        raise SystemExit("%s exists" % path)
    open(path, "w", encoding="utf-8").write(new_module)
    open(CORE, "w", encoding="utf-8").write(new_core)
    names = os.path.join(HERE, "core_names_1.4.0.txt")
    check = ("import gp_elite.core as C\n"
             "names = [l.strip() for l in open(%r) if l.strip()]\n"
             "missing = [n for n in names if not hasattr(C, n)]\n"
             "print('names of 1.4.0 missing on gp_elite.core:', missing)\n"
             "raise SystemExit(1 if missing else 0)\n" % names)
    r = subprocess.run([PY, "-I", "-c", check], cwd="/tmp", capture_output=True, text=True)
    print((r.stdout + r.stderr).strip()[-2000:])
    if r.returncode:
        raise SystemExit("the import check failed")


if __name__ == "__main__":
    args = [a for a in _ARGS if not a.startswith("--")]
    main(args[0], "--dry" in _ARGS)
