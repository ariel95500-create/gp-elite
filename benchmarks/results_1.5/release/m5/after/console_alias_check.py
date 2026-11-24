"""After M5, finding 9 of the second review: what option 7 of the console
(FORECAST) registers as `core`.

Unlike ../review2/console_core_alias.py, which wrote out the console's line,
this script reads the line from gp_elite/console.py as it is, runs it with the
console's globals, imports a top-level `api` from the folder of the package
(api.py then falls back to `import core`), and lists the names api.py reads
on `core` that the registered module lacks. Run it in a fresh process.

Usage: python console_alias_check.py
"""
import ast
import os
import sys

import gp_elite
import gp_elite.console as console
import gp_elite.core as core

pkg_dir = os.path.dirname(core.__file__)
src = open(console.__file__, encoding="utf-8").read().splitlines()
line = [l.strip() for l in src if 'setdefault("core"' in l]
assert len(line) == 1, line
ns = dict(vars(console))
ns["_sys7"] = sys
exec(line[0], ns)                                    # the console's own line
sys.path.insert(0, pkg_dir)                          # as when api.py is importable
import api as _api7                                  # the console's next line

used = sorted({n.attr for n in ast.walk(ast.parse(open(os.path.join(pkg_dir, "api.py")).read()))
               if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "core"})
missing = [a for a in used if not hasattr(_api7.core, a)]
print("engine %s, console.py: %s" % (gp_elite.__version__, line[0]))
print("  sys.modules['core'] = %s" % sys.modules["core"].__name__)
print("  the top-level api imported by the console uses core = %s" % _api7.core.__name__)
print("  names api.py reads on core: %d; missing on that module: %d %s" % (len(used), len(missing), missing))
