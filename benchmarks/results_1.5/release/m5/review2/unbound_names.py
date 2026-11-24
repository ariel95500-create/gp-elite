"""Review 2 of M5: names a module of 1.5 reads as globals but does not bind.

A moved function that reads a name its new module neither defines nor
imports raises NameError when it runs: the comparison of syntax trees cannot
see it, since the function's own code is unchanged. Annotations are listed
apart: under `from __future__ import annotations` they are never evaluated,
but typing.get_type_hints() evaluates them in the function's module.

The same check runs on 1.4.0's core.py, for reference (a name unbound there
was already unbound in 1.4.0).

Usage: python unbound_names.py OLD_CORE NEW_PACKAGE_DIR
"""
import ast
import builtins
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scopes import resolve  # noqa: E402

MODULES = ["state", "numeric", "config", "tree", "simplification", "evaluation",
           "datasets", "scoring", "fitting", "genetic", "memory", "final_choice",
           "seeds", "islands", "parallel", "search", "data", "console", "core"]
BUILTIN = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "__spec__", "__package__",
                                "__loader__", "__builtins__", "__path__", "__annotations__"}


def annotation_nodes(tree):
    ids = set()

    def mark(n):
        for x in ast.walk(n):
            ids.add(id(x))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = node.args
            for arg in a.posonlyargs + a.args + a.kwonlyargs + [a.vararg, a.kwarg]:
                if arg is not None and arg.annotation is not None:
                    mark(arg.annotation)
            if node.returns is not None:
                mark(node.returns)
        elif isinstance(node, ast.AnnAssign):
            mark(node.annotation)
    return ids


def module_level_bindings(tree, scopes):
    mod = scopes[0]
    assert mod.kind == "module"
    return set(mod.bound)


def check(path):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    scopes = resolve(tree)
    bound = module_level_bindings(tree, scopes)
    ann = annotation_nodes(tree)
    code, annot = {}, {}
    for s in scopes:
        for n in s.names:
            if n._res != "global" or not isinstance(n.ctx, ast.Load):
                continue
            if n.id in bound or n.id in BUILTIN:
                continue
            (annot if id(n) in ann else code).setdefault(n.id, []).append(n.lineno)
    return code, annot


def main(old_core, new_dir):
    code, annot = check(old_core)
    print("1.4.0 core.py: unbound names read in code: %s" % (code or "none"))
    print("1.4.0 core.py: unbound names in annotations only: %s" % (sorted(annot) or "none"))
    print()
    for m in MODULES:
        code, annot = check(os.path.join(new_dir, m + ".py"))
        print("%-15s code: %s" % (m + ".py", code or "none"))
        print("%-15s annotations only: %s" % ("", sorted(annot) or "none"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
