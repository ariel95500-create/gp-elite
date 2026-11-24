"""The door of 1.5: gp_elite.core keeps every name it had in 1.4.0, and a
name set on it reaches the engine (criterion A4 of the plan of 1.5).

In 1.4.0 the engine was one file, gp_elite/core.py, and every one of its
functions read its names there: a name set on gp_elite.core reached them
all. In 1.5 the engine is in modules and core.py is a door: the names of
the shared state live in gp_elite.state, and a name set on gp_elite.core
goes there, or to the engine's modules that hold the same object.
"""
import os
import sys

import numpy as np
import pytest

import gp_elite.core as core
import gp_elite.state as state
from gp_elite import symbolic_regression

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = [line.strip() for line in open(os.path.join(HERE, "core_names_1.4.0.txt"))
         if line.strip() and not line.startswith("#")]


def test_every_name_of_core_in_1_4_0_can_be_read():
    assert len(NAMES) == 421
    assert [n for n in NAMES if not hasattr(core, n)] == []


@pytest.mark.parametrize("name", sorted(core._STATE_NAMES))
def test_a_name_of_the_state_set_on_core_is_set_in_the_state(name, monkeypatch):
    missing = object()
    before = getattr(state, name, missing)
    sentinel = object()
    monkeypatch.setattr(core, name, sentinel, raising=False)
    assert getattr(state, name) is sentinel
    assert getattr(core, name) is sentinel
    assert name not in vars(core)           # no copy left on the door
    # set twice and put back, as a test does: the state gets its value back
    # (since pytest 9.2, monkeypatch puts back what it read in the module's
    # own dictionary, unless the name is a data descriptor of its class)
    monkeypatch.setattr(core, name, object(), raising=False)
    monkeypatch.undo()
    assert getattr(state, name, missing) is before
    assert getattr(core, name, missing) is before


def _holders(name, obj):
    return [m for k, m in list(sys.modules.items())
            if k.startswith("gp_elite.") and k != "gp_elite.core"
            and getattr(m, name, None) is obj]


@pytest.mark.parametrize("name", ["_has_own_factor", "_lm_plan", "_refit_inner",
                                  "evolve", "evolve_island"])
def test_a_function_set_on_core_reaches_the_modules_that_hold_it(name, monkeypatch):
    orig = getattr(core, name)
    holders = _holders(name, orig)
    assert holders                          # at least the module that defines it

    def replacement(*args, **kwargs):
        return orig(*args, **kwargs)
    monkeypatch.setattr(core, name, replacement)
    assert all(getattr(m, name) is replacement for m in holders)
    monkeypatch.undo()
    assert all(getattr(m, name) is orig for m in holders)
    assert getattr(core, name) is orig


@pytest.mark.parametrize("name", ["_has_own_factor", "_lm_plan", "_refit_inner",
                                  "evolve", "evolve_island"])
def test_a_function_deleted_on_core_then_put_back_reaches_the_engine_again(name, monkeypatch):
    orig = getattr(core, name)
    holders = _holders(name, orig)
    monkeypatch.delattr(core, name)
    assert not hasattr(core, name)
    assert all(name not in vars(m) for m in holders)
    monkeypatch.undo()
    assert getattr(core, name) is orig
    assert all(getattr(m, name) is orig for m in holders)
    # the same by hand, as a script would do it
    delattr(core, name)
    setattr(core, name, orig)
    assert all(getattr(m, name) is orig for m in holders)


def test_a_fit_runs_after_evolve_island_was_deleted_on_core_and_put_back(monkeypatch):
    monkeypatch.delattr(core, "evolve_island")
    monkeypatch.undo()
    X = np.random.RandomState(2).uniform(1, 5, (60, 2))
    r = symbolic_regression(X, X[:, 0] * X[:, 1], generations=2, seed=0,
                            parallel=False, verbose=False)
    assert r.expression


def test_the_name_state_set_on_core_does_not_replace_the_state_of_the_engine(monkeypatch):
    users = [m for m in core._ENGINE_MODULES if "state" in vars(m)]
    assert len(users) == 15                 # numeric and simplification use none
    monkeypatch.setattr(core, "state", object())
    assert all(m.state is state for m in users)
    assert core._USE_LINEAR_SCALING is state._USE_LINEAR_SCALING
    monkeypatch.setattr(core, "_POLISH_ADMITTED", 3)
    assert state._POLISH_ADMITTED == 3


def test_a_wrap_of_evolve_island_set_on_core_sees_every_generation(monkeypatch):
    calls = []
    orig = core.evolve_island

    def counted(*args, **kwargs):
        calls.append(1)
        return orig(*args, **kwargs)
    monkeypatch.setattr(core, "evolve_island", counted)
    X = np.random.RandomState(0).uniform(1, 5, (60, 2))
    symbolic_regression(X, X[:, 0] * np.sqrt(X[:, 1]), generations=4, seed=0,
                        parallel=False, verbose=False)
    assert calls


def test_the_state_read_on_core_is_the_state_of_the_engine():
    X = np.random.RandomState(1).uniform(1, 5, (60, 2))
    symbolic_regression(X, X[:, 0] + X[:, 1], generations=2, seed=0,
                        parallel=False, verbose=False)
    assert core._VAL_XS is state._VAL_XS
    assert core.VAL_R2_TOLERANCE == state.VAL_R2_TOLERANCE
