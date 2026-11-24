"""Review 2 of M5, question 4: the door under pytest's monkeypatch and unittest.mock.

A pytest file that runs unchanged on 1.4.0 and on 1.5. For each scenario it
records what the ENGINE sees, not what gp_elite.core answers:
- 1.4.0: the engine reads core's own namespace (vars(gp_elite.core));
- 1.5: the engine reads gp_elite.state for a state name, and, for any other
  name, the modules of the engine that held the original object.
Each observation is written to the JSON file named by $DOOR_OUT; the two
engines' files are then compared (compare_door.py).

Not a test of either engine on its own: every test passes; the records are
what is compared.
"""
import importlib
import json
import os
import sys
from unittest import mock

import numpy as np
import pytest

import gp_elite
import gp_elite.core as core

try:
    import gp_elite.state as STATE
except ImportError:
    STATE = None

MISSING = "<missing>"
OBS = {}
ORIG = dict(vars(core))       # the objects core holds right after import
# 1.5: for each name of core that is not a state name, the engine modules
# that hold the same object at import (the functions there read it)
HOLDERS = {} if STATE is None else {
    n: [m for m in core._ENGINE_MODULES if m.__dict__.get(n, MISSING) is v]
    for n, v in ORIG.items()}
STATE_NAMES = sorted(json.load(open(os.path.join(os.path.dirname(__file__), "state_names.json"))))
FUNCS = ["_has_own_factor", "_lm_plan", "_refit_inner", "evolve", "evolve_island",
         "_build_near_probes", "_make_power_law_seeds", "_make_binomial_seeds",
         "_make_elementary_seeds", "_make_tolerant_seeds", "to_string", "np", "time"]


def engine_value(name):
    """The value the engine's functions would read for `name`."""
    if STATE is not None and name in core._STATE_NAMES:
        return getattr(STATE, name, MISSING)
    if STATE is None:
        return vars(core).get(name, MISSING)
    # 1.5, any other name: what the modules of the engine that held it at import
    # hold now (they must agree, as core's one namespace did in 1.4.0)
    holders = HOLDERS.get(name, [])
    if not holders:
        return MISSING
    seen = {id(m.__dict__.get(name, MISSING)) for m in holders}
    if len(seen) > 1:
        return "<engine modules disagree>"
    return holders[0].__dict__.get(name, MISSING)


STATE_SNAPSHOT = dict(vars(STATE)) if STATE is not None else None


@pytest.fixture(autouse=True)
def restore_engine():
    """After each test (and after monkeypatch's own undo), put the engine back
    as it was at import, so that one scenario cannot leak into the next. The
    observation of a scenario is taken before this runs."""
    yield
    if STATE is None:
        d = vars(core)
        for k in [k for k in d if k not in ORIG]:
            del d[k]
        d.update(ORIG)
    else:
        sd = vars(STATE)
        for k in [k for k in sd if k not in STATE_SNAPSHOT]:
            del sd[k]
        sd.update(STATE_SNAPSHOT)
        for n, mods in HOLDERS.items():
            for m in mods:
                m.__dict__[n] = ORIG[n]
        d = vars(core)
        for k in [k for k in d if k not in ORIG]:
            del d[k]
        d.update(ORIG)


def label(v, sentinels):
    for k, s in sentinels.items():
        if v is s:
            return k
    if v is MISSING:
        return "missing"
    return "other"


def record(key, value):
    OBS[key] = value


def teardown_module(module):
    out = os.environ.get("DOOR_OUT")
    if out:
        json.dump({"engine": gp_elite.__version__, "python": sys.version.split()[0],
                   "pytest": pytest.__version__, "obs": OBS}, open(out, "w"), indent=1, sort_keys=True)


def _original(name):
    return engine_value(name)


@pytest.mark.parametrize("name", STATE_NAMES + FUNCS)
def test_monkeypatch_setattr_and_undo(name, monkeypatch):
    orig = _original(name)
    s1, s2 = object(), object()
    sent = {"orig": orig, "s1": s1, "s2": s2}
    try:
        monkeypatch.setattr(core, name, s1)
        r1 = label(engine_value(name), sent)
    except AttributeError as e:
        r1 = "AttributeError"
    try:
        monkeypatch.setattr(core, name, s2)
        r2 = label(engine_value(name), sent)
    except AttributeError:
        r2 = "AttributeError"
    monkeypatch.undo()
    r3 = label(engine_value(name), sent)
    r4 = label(getattr(core, name, MISSING), sent)
    record("mp.setattr " + name, [r1, r2, r3, r4])


@pytest.mark.parametrize("name", STATE_NAMES + FUNCS)
def test_monkeypatch_setattr_string_target(name, monkeypatch):
    orig = _original(name)
    s1 = object()
    sent = {"orig": orig, "s1": s1}
    try:
        monkeypatch.setattr("gp_elite.core." + name, s1)
        r1 = label(engine_value(name), sent)
    except AttributeError:
        r1 = "AttributeError"
    monkeypatch.undo()
    record("mp.setattr(str) " + name, [r1, label(engine_value(name), sent)])


@pytest.mark.parametrize("name", STATE_NAMES + FUNCS)
def test_monkeypatch_delattr_and_undo(name, monkeypatch):
    orig = _original(name)
    sent = {"orig": orig}
    try:
        monkeypatch.delattr(core, name)
        r1 = label(engine_value(name), sent)
        r2 = hasattr(core, name)
    except AttributeError:
        r1, r2 = "AttributeError", None
    monkeypatch.undo()
    record("mp.delattr " + name, [r1, r2, label(engine_value(name), sent)])


@pytest.mark.parametrize("name", ["VAL_R2_TOLERANCE", "_CUSTOM_LOSS_ROBUST", "_CUSTOM_LOSS_USE_SCALING",
                                  "A_NAME_1_4_0_NEVER_HAD"])
def test_monkeypatch_raising_false_on_a_missing_name(name, monkeypatch):
    s1 = object()
    before = label(engine_value(name), {})
    monkeypatch.setattr(core, name, s1, raising=False)
    r1 = label(engine_value(name), {"s1": s1})
    monkeypatch.undo()
    record("mp.setattr(raising=False) " + name, [before, r1, label(engine_value(name), {"s1": s1}),
                                                 hasattr(core, name)])


@pytest.mark.parametrize("name", STATE_NAMES + FUNCS)
def test_mock_patch_object(name):
    orig = _original(name)
    s1 = object()
    sent = {"orig": orig, "s1": s1}
    try:
        with mock.patch.object(core, name, s1):
            r1 = label(engine_value(name), sent)
    except AttributeError:
        r1 = "AttributeError"
    record("mock.patch.object " + name, [r1, label(engine_value(name), sent), label(getattr(core, name, MISSING), sent)])


@pytest.mark.parametrize("name", STATE_NAMES + FUNCS)
def test_mock_patch_string(name):
    orig = _original(name)
    s1 = object()
    sent = {"orig": orig, "s1": s1}
    try:
        with mock.patch("gp_elite.core." + name, s1):
            r1 = label(engine_value(name), sent)
    except AttributeError:
        r1 = "AttributeError"
    record("mock.patch(str) " + name, [r1, label(engine_value(name), sent)])


@pytest.mark.parametrize("name", ["VAL_R2_TOLERANCE", "_VAL_CANDS", "evolve"])
def test_mock_patch_create(name):
    s1 = object()
    before = label(engine_value(name), {})
    with mock.patch.object(core, name, s1, create=True):
        r1 = label(engine_value(name), {"s1": s1})
    record("mock.patch.object(create=True) " + name, [before, r1, label(engine_value(name), {"s1": s1})])


@pytest.mark.parametrize("name", STATE_NAMES + FUNCS)
def test_plain_set_and_del(name):
    orig = _original(name)
    s1 = object()
    sent = {"orig": orig, "s1": s1}
    setattr(core, name, s1)
    r1 = label(engine_value(name), sent)
    delattr(core, name)
    r2 = label(engine_value(name), sent)
    r3 = hasattr(core, name)
    setattr(core, name, orig)
    r4 = label(engine_value(name), sent)
    record("set/del " + name, [r1, r2, r3, r4])


def test_vars_and_dict_of_core():
    v = vars(core)
    record("vars(core) has state names", sorted(n for n in STATE_NAMES if n in v))
    # a 1.4.0 script that sets several names at once through the module's dictionary
    s1 = object()
    orig = engine_value("_VAL_CANDS")
    core.__dict__["_VAL_CANDS"] = s1
    r = label(engine_value("_VAL_CANDS"), {"s1": s1, "orig": orig})
    r_core = label(getattr(core, "_VAL_CANDS"), {"s1": s1, "orig": orig})
    if STATE is None:
        core.__dict__["_VAL_CANDS"] = orig
    else:
        del core.__dict__["_VAL_CANDS"]
    record("core.__dict__[...] = v reaches the engine", [r, r_core])
    f = core.evolve
    record("core.evolve.__globals__ is vars(core)", f.__globals__ is vars(core))


def test_reload_of_core():
    """importlib.reload(gp_elite.core): 1.4.0 re-runs the engine's top level."""
    orig_cands = engine_value("_VAL_CANDS")
    orig_lib = engine_value("FRAGMENT_LIB")
    core._TIME_LIMIT_HIT = True
    core._VAL_CANDS = ["x"]
    evolve_before = core.evolve
    importlib.reload(core)
    record("after reload: _TIME_LIMIT_HIT, _VAL_CANDS reset; FRAGMENT_LIB new; evolve new",
           [engine_value("_TIME_LIMIT_HIT"), engine_value("_VAL_CANDS") == [],
            engine_value("FRAGMENT_LIB") is not orig_lib, core.evolve is not evolve_before])
    core._TIME_LIMIT_HIT = False
    core._VAL_CANDS = orig_cands if isinstance(orig_cands, list) else []
