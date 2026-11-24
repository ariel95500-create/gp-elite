"""Review 2 of M5, question 4: the names of gp_elite.core and what they hold.

Run under each engine; writes a JSON summary of every name in dir(gp_elite.core)
right after import, and of a few module-level facts:
- for data: type, and a canonical value (repr of lists, dicts, arrays...);
- for functions and classes: qualname, the signature, the defaults, the
  docstring's hash, __module__, and the file of the code;
- for modules: their name.

Usage: python names_values.py OUT.json
"""
import hashlib
import inspect
import json
import sys
import types

import numpy as np

import gp_elite
import gp_elite.core as core


def canon(v, depth=0):
    if depth > 3:
        return "<deep %s>" % type(v).__name__
    if v is None or isinstance(v, (bool, int, float, str)):
        return repr(v)
    if isinstance(v, np.ndarray):
        return "ndarray%s %s %s" % (v.shape, v.dtype, hashlib.sha1(np.ascontiguousarray(v).tobytes()).hexdigest()[:12])
    if isinstance(v, (list, tuple)):
        return "%s[%s]" % (type(v).__name__, ", ".join(canon(x, depth + 1) for x in v))
    if isinstance(v, (set, frozenset)):
        return "%s{%s}" % (type(v).__name__, ", ".join(sorted(canon(x, depth + 1) for x in v)))
    if isinstance(v, dict):
        items = sorted((canon(k, depth + 1), canon(x, depth + 1)) for k, x in v.items())
        return "dict{%s}" % ", ".join("%s: %s" % kv for kv in items)
    if isinstance(v, types.ModuleType):
        return "module %s" % v.__name__
    if isinstance(v, (types.FunctionType, types.BuiltinFunctionType, type)):
        return "%s %s.%s" % (type(v).__name__, getattr(v, "__module__", "?"), getattr(v, "__qualname__", "?"))
    if callable(v):
        return "callable %s" % type(v).__name__
    return "object %s" % type(v).__name__


def describe(name, v):
    d = {"type": type(v).__name__}
    if isinstance(v, (types.FunctionType, type)):
        d["qualname"] = v.__qualname__
        d["module"] = v.__module__
        try:
            d["signature"] = str(inspect.signature(v))
        except (TypeError, ValueError):
            d["signature"] = None
        d["doc"] = hashlib.sha1((v.__doc__ or "").encode()).hexdigest()[:12]
        if isinstance(v, types.FunctionType):
            d["defaults"] = canon(v.__defaults__)
            d["kwdefaults"] = canon(v.__kwdefaults__)
            d["file"] = v.__code__.co_filename.rsplit("/", 1)[-1]
            d["globals_is_core_dict"] = v.__globals__ is vars(core)
        else:
            d["file"] = None
    elif isinstance(v, types.ModuleType):
        d["value"] = v.__name__
    else:
        d["value"] = canon(v)
    return d


def main(out):
    res = {"python": sys.version.split()[0], "engine": gp_elite.__version__,
           "core_file": core.__file__.rsplit("/", 2)[-2:],
           "core_class": type(core).__name__,
           "names": {}}
    for name in dir(core):
        try:
            v = getattr(core, name)
        except AttributeError as e:
            res["names"][name] = {"error": "AttributeError"}
            continue
        res["names"][name] = describe(name, v)
    res["vars_has"] = sorted(vars(core))
    res["annotations"] = sorted(getattr(core, "__annotations__", {}) or {})
    ns = {}
    exec("from gp_elite.core import *", ns)
    res["star_import"] = sorted(k for k in ns if k != "__builtins__")
    json.dump(res, open(out, "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main(sys.argv[1])
