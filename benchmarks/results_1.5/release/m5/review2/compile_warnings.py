"""Review 2 of M5, question 5: the warnings Python gives when it compiles the
engine (SyntaxWarning and others), for 1.4.0's core.py and for the modules of
1.5, compiled fresh from source (no .pyc), under the running Python.

Usage: python compile_warnings.py FILE [FILE ...]
Prints each warning as category: message (file and line apart), and the
number per category.
"""
import collections
import sys
import warnings

total = collections.Counter()
msgs = collections.Counter()
for path in sys.argv[1:]:
    src = open(path, encoding="utf-8").read()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        compile(src, path, "exec")
    for x in w:
        total[x.category.__name__] += 1
        msgs["%s: %s" % (x.category.__name__, str(x.message))] += 1
print("python %s, %d files" % (sys.version.split()[0], len(sys.argv) - 1))
print("warnings by category: %s" % dict(total))
for m, c in sorted(msgs.items()):
    print("  %3d x %s" % (c, m))
