"""Review 2 of M5, question 5: pickles across 1.4.0 and 1.5.

  python pickle_probe.py dump DIR   -> fits a tiny model (generations=2,
      parallel=False) and pickles: the SRResult, a fitted GPEliteRegressor,
      a Node, a Config; writes DIR/<engine>_<what>.pkl and lists the module
      globals each pickle names.
  python pickle_probe.py load DIR   -> loads every .pkl of DIR and, for the
      estimator, predicts on the same rows; prints what loads and what fails.
"""
import contextlib
import glob
import io
import os
import pickle
import pickletools
import sys

import numpy as np

import gp_elite
import gp_elite.core as core
from gp_elite import GPEliteRegressor, symbolic_regression

X = np.random.RandomState(0).uniform(1, 5, (60, 2))
Y = X[:, 0] * X[:, 1]


def globals_named(data):
    mods = set()
    ops = list(pickletools.genops(data))
    strings = []
    for op, arg, pos in ops:
        if op.name in ("GLOBAL",):
            mods.add(arg.split(" ")[0])
        if op.name in ("SHORT_BINUNICODE", "BINUNICODE", "UNICODE"):
            strings.append(arg)
        if op.name == "STACK_GLOBAL" and len(strings) >= 2:
            mods.add(strings[-2])
    return sorted(m for m in mods if m.startswith("gp_elite"))


def dump(d):
    tag = gp_elite.__version__
    with contextlib.redirect_stdout(io.StringIO()):
        r = symbolic_regression(X, Y, generations=2, seed=0, parallel=False, verbose=False)
        est = GPEliteRegressor(generations=2, random_state=0, parallel=False).fit(X, Y)
    objs = {"result": r, "estimator": est, "node": core.Node("+", core.Node(1.5), core.Node("x0")),
            "config": core.Config()}
    for what, o in objs.items():
        data = pickle.dumps(o, protocol=4)
        open(os.path.join(d, "%s_%s.pkl" % (tag, what)), "wb").write(data)
        print("%s %-9s pickled, names the modules %s" % (tag, what, globals_named(data)))
    np.save(os.path.join(d, "%s_pred.npy" % tag), est.predict(X))


def load(d):
    tag = gp_elite.__version__
    for p in sorted(glob.glob(os.path.join(d, "*.pkl"))):
        name = os.path.basename(p)
        try:
            o = pickle.loads(open(p, "rb").read())
            msg = "loads as %s.%s" % (type(o).__module__, type(o).__qualname__)
            if name.endswith("_estimator.pkl"):
                with contextlib.redirect_stdout(io.StringIO()):
                    pr = o.predict(X)
                ref = np.load(p.replace("_estimator.pkl", "_pred.npy"))
                msg += "; predict equal to the saving engine's: %s" % bool(np.array_equal(pr, ref))
        except Exception as e:
            msg = "FAILS: %s: %s" % (type(e).__name__, e)
        print("engine %s loading %-22s %s" % (tag, name, msg))


if __name__ == "__main__":
    {"dump": dump, "load": load}[sys.argv[1]](sys.argv[2])
