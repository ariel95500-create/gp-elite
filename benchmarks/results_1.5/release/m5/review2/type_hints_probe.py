"""Review 2 of M5, question 5: typing.get_type_hints() on the names of gp_elite.core.

Under `from __future__ import annotations` the annotations are strings, which
get_type_hints() evaluates in the globals of the function's module. A moved
function whose new module does not import a name of its annotations (Config,
Node...) now fails there. Prints, per engine, the functions and classes for
which get_type_hints() fails, and the module gp_elite.state itself.

Usage: python type_hints_probe.py
"""
import types
import typing

import gp_elite
import gp_elite.core as core

fails = []
n = 0
for name in sorted(vars(core)):
    v = vars(core)[name]
    if isinstance(v, (types.FunctionType, type)) and getattr(v, "__module__", "").startswith("gp_elite"):
        n += 1
        try:
            typing.get_type_hints(v)
        except Exception as e:
            fails.append("%s (%s: %s)" % (name, type(e).__name__, e))
print("engine %s: get_type_hints() on %d functions and classes of core: %d fail" % (
    gp_elite.__version__, n, len(fails)))
for f in fails:
    print("   ", f)
try:
    import gp_elite.state as st
    typing.get_type_hints(st)
    print("   get_type_hints(gp_elite.state): ok")
except ImportError:
    pass
except Exception as e:
    print("   get_type_hints(gp_elite.state): %s: %s" % (type(e).__name__, e))
try:
    h = typing.get_type_hints(core)
    print("   get_type_hints(gp_elite.core): %d entries" % len(h))
except Exception as e:
    print("   get_type_hints(gp_elite.core): %s: %s" % (type(e).__name__, e))
