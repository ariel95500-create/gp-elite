"""Review 2 of M5, question 5: option 7 of the console (FORECAST).

The console runs, before `import api`:
    _sys7.modules.setdefault("core", _sys7.modules[__name__])
In 1.4.0 `__name__` there is gp_elite.core (or __main__, core.py run as a
script); in 1.5 the code is in console.py and `__name__` is gp_elite.console.
When a top-level `api` is importable (the folder of the package, or a folder
of loose modules, on sys.path), api.py falls back to `import core` and gets
the module registered above. This script runs the console's two lines where
the console's code lives, imports a top-level `api` from the package folder,
and lists the names api.py reads on `core` that this module lacks.

Usage: python console_core_alias.py
"""
import ast
import os
import sys

import gp_elite
import gp_elite.core as core

pkg_dir = os.path.dirname(core.__file__)
menu_module = core._interactive_menu.__module__
sys.path.insert(0, pkg_dir)                                  # as when api.py is importable
sys.modules.setdefault("core", sys.modules[menu_module])     # the console's own line
import api as _api7                                          # the console's next line

used = sorted({n.attr for n in ast.walk(ast.parse(open(os.path.join(pkg_dir, "api.py")).read()))
               if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "core"})
missing = [a for a in used if not hasattr(_api7.core, a)]
print("engine %s: the console's code is in %s; sys.modules['core'] = %s" % (
    gp_elite.__version__, menu_module, sys.modules["core"].__name__))
print("  the top-level api imported by the console uses core = %s" % _api7.core.__name__)
print("  names api.py reads on core: %d; missing on that module: %d %s" % (len(used), len(missing), missing))
