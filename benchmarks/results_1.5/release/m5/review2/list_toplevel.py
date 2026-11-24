"""List the top-level statements of a Python file: line, kind, names bound.

Usage: python list_toplevel.py FILE
"""
import ast
import sys


def bound_names(stmt):
    """Names a top-level statement binds in the module namespace."""
    out = []
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        out.append(stmt.name)
    elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
        for a in stmt.names:
            out.append((a.asname or a.name).split(".")[0])
    else:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                out.append(node.id)
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                # a def nested in an if/try at top level
                out.append(node.name)
    return out


def main(path):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    for st in tree.body:
        kind = type(st).__name__
        names = bound_names(st)
        print("%5d %5d %-14s %s" % (st.lineno, st.end_lineno, kind, ",".join(names)))


if __name__ == "__main__":
    main(sys.argv[1])
