"""Review 2 of M5, question 5: the parallel islands (spawn), the worker's
initializer, and the warning of the guard of the main module.

  python parallel_probe.py init      -> runs the pool's initializer
      (_parallel_worker_init) in this process, as a worker does, and prints the
      names it registers in sys.modules and the file behind each.
  python parallel_probe.py fit       -> one parallel fit (spawn, parallel=True,
      generations=3, seed 0) of a guarded script; prints the model and its
      constants, to compare the two engines.
  python parallel_probe.py unguarded DIR -> writes a script without
      `if __name__ == "__main__":` in DIR and runs it: the pool breaks, the
      engine falls back to sequential and warns once. Prints where the warning
      is attributed (file, line, module) and whether a filter on the module
      "gp_elite.core", the module 1.4.0 attributed it to, still silences it.
"""
import os
import pickle
import subprocess
import sys
import tempfile
import textwrap

import numpy as np


def init():
    import gp_elite.core as core
    before = set(sys.modules)
    fd, path = tempfile.mkstemp(suffix=".pkl")
    os.close(fd)
    xs = np.zeros((4, 1)); ys = np.zeros(4)
    with open(path, "wb") as fh:
        pickle.dump((xs, ys, np.zeros((20, 4)), None, None), fh)
    core._parallel_worker_init(path, True, False)
    os.remove(path)
    new = sorted(set(sys.modules) - before)
    print("registered in sys.modules by the initializer: %s" % new)
    for k in new:
        m = sys.modules[k]
        print("   %-8s -> file %s, executed: %s" % (k, getattr(m, "__file__", None),
                                                  hasattr(m, "evolve") or hasattr(m, "_evolve_parallel")))


def fit():
    from gp_elite import symbolic_regression
    import gp_elite
    r = np.random.RandomState(0)
    X = r.uniform(1, 4, (200, 3)); y = X[:, 0] * X[:, 1] / X[:, 2]
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        res = symbolic_regression(X, y, generations=3, parallel=True, seed=0)
    print("engine %s parallel fit: %s | r2_val %r | size %d" % (gp_elite.__version__, res.expression,
                                                               res.r2_validation, res.size))


SCRIPT = """
import os, warnings, numpy as np
from gp_elite import symbolic_regression
import gp_elite
r = np.random.RandomState(0)
X = r.uniform(1, 4, (120, 3)); y = X[:, 0] * X[:, 1]
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    a = symbolic_regression(X, y, generations=3, parallel=True, seed=0, verbose=False)
rec = [x for x in w if "__main__" in str(x.message)]
print("ENGINE", gp_elite.__version__)
print("WARNING", [(x.category.__name__, x.filename.rsplit(os.sep, 2)[-2:], x.lineno) for x in rec])
import gp_elite.core as core
core._PARALLEL_WARNED = False            # let it warn again, in the same process
core._PARALLEL_BROKEN = False
with warnings.catch_warnings(record=True) as w2:
    warnings.simplefilter("always")
    warnings.filterwarnings("ignore", category=RuntimeWarning, module=r"gp_elite\\.core")
    b = symbolic_regression(X, y, generations=3, parallel=True, seed=0, verbose=False)
rec2 = [x for x in w2 if "__main__" in str(x.message)]
print("WITH A FILTER ON module='gp_elite.core':", "silenced" if not rec2 else "still shown, from %s" % (x.filename.rsplit(os.sep, 1)[-1] for x in rec2).__next__())
print("SAME", a.expression == b.expression, a.expression)
"""


def unguarded(d):
    p = os.path.join(d, "unguarded_%s.py" % os.getpid())
    open(p, "w").write(textwrap.dedent(SCRIPT))
    env = dict(os.environ, PYTHONHASHSEED="0")
    out = subprocess.run([sys.executable, "-P", p] if sys.version_info >= (3, 11) else [sys.executable, p],
                         capture_output=True, text=True, timeout=300, env=env, cwd=d)
    os.remove(p)
    for line in out.stdout.splitlines():
        if line.startswith(("ENGINE", "WARNING", "WITH", "SAME")):
            print(line)
    if out.returncode:
        print("returncode", out.returncode, out.stderr[-1500:])


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "init":
        init()
    elif mode == "fit":
        fit()
    else:
        unguarded(sys.argv[2])
