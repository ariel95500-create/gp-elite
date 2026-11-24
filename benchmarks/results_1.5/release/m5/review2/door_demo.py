"""Review 2 of M5, question 4: what the gaps of the door do to a fit.

Runs on either engine. Three short fits (generations=2, parallel=False):
  A. after `monkeypatch.delattr(core, "evolve_island")` and its undo
     (pytest.MonkeyPatch.context(), the same code as the fixture);
  B. after `unittest.mock.patch.object(core, "_VAL_CANDS", [], create=True)`;
  C. after `unittest.mock.patch("gp_elite.core._USE_LINEAR_SCALING", False, create=True)`.
Prints, for each, whether the fit runs, or the error it raises.
Also: D. importlib.reload(gp_elite.core) after a fit, and what it resets.

Usage: python door_demo.py [A|B|C|D]  (one scenario per process; all if none)
"""
import sys
ONLY = sys.argv[1] if len(sys.argv) > 1 else "ABCD"
import importlib
import io
import contextlib
from unittest import mock

import numpy as np
import pytest

import gp_elite
import gp_elite.core as core
from gp_elite import symbolic_regression

X = np.random.RandomState(0).uniform(1, 5, (60, 2))
Y = X[:, 0] * X[:, 1]


def fit():
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            r = symbolic_regression(X, Y, generations=2, seed=0, parallel=False, verbose=False)
        return "fit runs: %s" % r.expression
    except Exception as e:
        return "fit fails: %s: %s" % (type(e).__name__, e)


print("engine", gp_elite.__version__)
print("0. a fit before anything:", fit())

if "A" in ONLY:
  with pytest.MonkeyPatch.context() as mp:
    mp.delattr(core, "evolve_island")
  print("A. after monkeypatch.delattr(core, 'evolve_island') and undo:")
  print("   hasattr(core, 'evolve_island') =", hasattr(core, "evolve_island"))
  print("  ", fit())

if "B" in ONLY:
  with mock.patch.object(core, "_VAL_CANDS", [], create=True):
    pass
  print("B. after mock.patch.object(core, '_VAL_CANDS', [], create=True):")
  print("   hasattr(core, '_VAL_CANDS') =", hasattr(core, "_VAL_CANDS"))
  print("  ", fit())

if "C" in ONLY:
  with mock.patch("gp_elite.core._USE_LINEAR_SCALING", False, create=True):
    pass
  print("C. after mock.patch('gp_elite.core._USE_LINEAR_SCALING', False, create=True):")
  print("   hasattr(core, '_USE_LINEAR_SCALING') =", hasattr(core, "_USE_LINEAR_SCALING"))
  print("  ", fit())

# D. reload
if "D" in ONLY:
  core._TIME_LIMIT_HIT = True
  core._POLISH_ADMITTED = 7
  lib = core.FRAGMENT_LIB
  importlib.reload(core)
  print("D. importlib.reload(gp_elite.core) after setting _TIME_LIMIT_HIT=True, _POLISH_ADMITTED=7:")
  print("   _TIME_LIMIT_HIT =", core._TIME_LIMIT_HIT, "; _POLISH_ADMITTED =", core._POLISH_ADMITTED,
      "; FRAGMENT_LIB is a new object:", core.FRAGMENT_LIB is not lib)
