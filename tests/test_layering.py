"""The order of the modules of the engine (docs/architecture.md, "The
modules"): a module imports only the modules above it in that table, and
none imports gp_elite.core. A few functions import, when they run, modules
of the package outside the engine (dim_search, dimensions, formula, api),
which themselves import gp_elite.core; that is allowed only inside a
function. Read from the syntax tree of each module, without running it.
"""
import ast
import os

import gp_elite
import gp_elite.core as core

ORDER = ["state", "numeric", "config", "tree", "simplification", "evaluation",
         "datasets", "scoring", "fitting", "genetic", "memory", "final_choice",
         "seeds", "islands", "parallel", "search", "data", "console"]
OUTSIDE = {"api", "sklearn_api", "formula", "dimensions", "dim_search",
           "stability", "cli"}
PKG = os.path.dirname(os.path.abspath(gp_elite.__file__))


class _Imports(ast.NodeVisitor):
    """Each import of a module of the package: (name, at import time?, line)."""

    def __init__(self):
        self.depth = 0
        self.found = []

    def visit_FunctionDef(self, node):
        self.depth += 1
        self.generic_visit(node)
        self.depth -= 1

    visit_AsyncFunctionDef = visit_FunctionDef

    def _add(self, name, node):
        if name in ORDER or name in OUTSIDE or name == "core":
            self.found.append((name, self.depth == 0, node.lineno))

    def visit_ImportFrom(self, node):
        if node.level == 1 and node.module:          # from .x import ...
            self._add(node.module.split(".")[0], node)
        elif node.level == 1:                        # from . import x
            for a in node.names:
                self._add(a.name, node)
        elif node.level == 0 and node.module:
            parts = node.module.split(".")
            if parts[0] == "gp_elite" and len(parts) > 1:
                self._add(parts[1], node)
            elif parts[0] == "gp_elite":
                for a in node.names:
                    self._add(a.name, node)
            else:                                    # from api import ... (loose files)
                self._add(parts[0], node)

    def visit_Import(self, node):
        for a in node.names:
            parts = a.name.split(".")
            self._add(parts[1] if parts[0] == "gp_elite" and len(parts) > 1 else parts[0], node)


def _imports(module):
    with open(os.path.join(PKG, module + ".py"), encoding="utf-8") as fh:
        v = _Imports()
        v.visit(ast.parse(fh.read()))
    return v.found


def test_each_module_imports_only_the_modules_above_it_and_never_core():
    bad = []
    for i, module in enumerate(ORDER):
        for name, at_import, line in _imports(module):
            if name == "core":
                bad.append((module, line, name, "imports gp_elite.core"))
            elif name in ORDER and ORDER.index(name) >= i:
                bad.append((module, line, name, "is not above it"))
            elif name in OUTSIDE and at_import:
                bad.append((module, line, name, "outside the engine, at import"))
    assert not bad, "\n".join("%s.py line %d: %s %s" % b for b in bad)


def test_the_order_holds_every_module_of_the_package():
    files = {f[:-3] for f in os.listdir(PKG) if f.endswith(".py")}
    known = set(ORDER) | OUTSIDE | {"core", "__init__", "__main__"}
    assert files == known, "not in the order: %s; missing: %s" % (sorted(files - known), sorted(known - files))


def test_the_door_passes_names_on_to_the_modules_in_this_order():
    assert [m.__name__.split(".")[-1] for m in core._ENGINE_MODULES] == ORDER[1:]
