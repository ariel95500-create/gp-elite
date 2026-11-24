import pydoc, re, sys
import gp_elite, gp_elite.core as core
txt = pydoc.render_doc(core, renderer=pydoc.plaintext)
funcs = re.findall(r"^    ([A-Za-z_][A-Za-z0-9_]*)\(", txt, re.M)
classes = re.findall(r"^    class ([A-Za-z_][A-Za-z0-9_]*)", txt, re.M)
print("engine %s, python %s: help(gp_elite.core) documents %d functions and %d classes; lines %d"
      % (gp_elite.__version__, sys.version.split()[0], len(set(funcs)), len(set(classes)), txt.count("\n")))
try:
    print("   core.__annotations__: %d entries" % len(core.__annotations__))
except AttributeError as e:
    print("   core.__annotations__: AttributeError: %s" % e)
