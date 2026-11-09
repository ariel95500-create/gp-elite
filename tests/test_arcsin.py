"""The arcsine of 1.3 (benchmarks/results_1.3/PLAN.md, change A1).

The operator `arcsin` computes the arcsine of its argument clipped to
[-1, 1]. It is in the pools `trig` and `full`, not in `physical`, `poly` or
`conserve`. Every path of evaluation must agree, the printed formula and its
sympy form must reproduce the model where the clip does not act, and under
units its argument must be dimensionless.

Run: pytest -q   (from the repository root)
"""
import math
import random

import numpy as np
import pytest

from gp_elite import core, formula as F
from gp_elite import dimensions as GD
import gp_elite.dim_search as DS

N = core.Node
_BIN = ["+", "-", "*", "/", "pow"]
_UN = ["arcsin", "arcsin", "sin", "cos", "sqrt", "sq", "neg", "exp", "log"]


def _same(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.shape != y.shape:
        return False
    a, b = x.view(np.int64), y.view(np.int64)
    return bool(np.all((a == b) | (np.isnan(x) & np.isnan(y))))


def _tree(rng, d, nvar, root_arcsin=False):
    if root_arcsin:
        return N("arcsin", _tree(rng, d - 1, nvar))
    if d == 0 or rng.random() < 0.3:
        if rng.random() < 0.45:
            return N(rng.uniform(-2, 2))
        return N("X[%d]" % rng.randrange(nvar))
    if rng.random() < 0.55:
        return N(rng.choice(_BIN), _tree(rng, d - 1, nvar), _tree(rng, d - 1, nvar))
    return N(rng.choice(_UN), _tree(rng, d - 1, nvar))


def _trees(n, seed=0):
    rng = random.Random(seed)
    return [_tree(rng, rng.randint(1, 5), 3, root_arcsin=(k % 2 == 0))
            for k in range(n)]


def test_arcsin_guard():
    a = np.array([-3.0, -1.0, -0.5, 0.0, 0.5, 1.0, 3.0, np.nan])
    got = core._np_safe_arcsin(a)
    want = np.arcsin(np.clip(a, -1.0, 1.0))
    assert _same(got, want)
    for v in (-3.0, -1.0, -0.5, 0.0, 0.5, 1.0, 3.0):
        assert core.safe_arcsin(v) == math.asin(min(max(v, -1.0), 1.0))


def test_arcsin_folds_its_constant():
    t = core.simplify(N("arcsin", N(0.5)))
    assert t.left is None and t.right is None
    assert t.value == 0.5235987755982989
    assert core.simplify(N("arcsin", N(2.0))).value == math.pi / 2


def test_every_path_of_evaluation_agrees():
    """Interpreter, compiled code, scalar evaluation, the parametric compiler
    of the fit of constants and its incremental plan: the same values, with
    arguments inside and outside [-1, 1]."""
    X = np.random.RandomState(0).uniform(-2, 2, (40, 3))
    n_out = n_scal = 0
    for t in _trees(200):
        with np.errstate(all="ignore"):
            core._COMPILE_CACHE.pop(t.exact_hash(), None)
            interp = core._interp(t, X, 0)
            fn = core.compile_to_numpy(t)
            comp = fn(X)
            assert _same(np.broadcast_to(interp, (40,)), np.broadcast_to(comp, (40,))), \
                core.to_string(t)
            ref = np.broadcast_to(np.asarray(comp, dtype=float), (40,))
            # The scalar path (display only) computes a power with a variable
            # exponent otherwise than the vector paths, already in 1.2.0: it
            # is compared on the trees without a power.
            if "pow" not in core.to_string(t):
                scal = np.array([core.evaluate(t, list(row)) for row in X])
                ok = np.isfinite(ref) & np.isfinite(scal)
                assert np.allclose(scal[ok], ref[ok], rtol=1e-12, atol=1e-12), \
                    core.to_string(t)
                n_scal += 1
            consts = core._collect_constants_ordered(t)
            if consts:
                pf, _ = core.compile_parametric(t)
                c = np.array([cn.value for cn in consts])
                assert _same(np.broadcast_to(pf(X, c), (40,)), ref)
                plan = core._lm_build_plan(t, consts)
                if plan is not None:
                    base, _vals = plan.full(X, c)
                    assert _same(np.broadcast_to(base, (40,)), ref)
        if t.value == "arcsin":
            arg = np.broadcast_to(core._interp(t.left, X, 0), (40,))
            n_out += int(np.any(np.abs(arg) > 1))
    assert n_out > 10          # the guard was exercised
    assert n_scal > 100


def test_formula_reproduces_the_model_where_the_clip_does_not_act():
    sympy = pytest.importorskip("sympy")
    X = np.random.RandomState(1).uniform(0.2, 0.9, (30, 2))
    inner = N("arcsin", N("*", X_(0), N("sin", X_(1))))
    t = N("+", N(0.1), N("*", N(2.0), inner))
    model = core.evaluate_vector(t, X)
    printed = F.evaluate(t, X)
    assert np.allclose(model, printed, rtol=1e-12, atol=0)
    assert "arcsin(" in F.to_text(t, names=["n", "th"])
    s = F.to_sympy_string(t, names=["n", "th"])
    assert "asin(" in s
    e = sympy.sympify(s)
    f = sympy.lambdify(sympy.symbols("n th"), e, "numpy")
    assert np.allclose(f(X[:, 0], X[:, 1]), model, rtol=1e-12, atol=0)
    p = F.to_text(t, names=["n", "th"], _parsable=True)
    assert "asin(" in p and np.allclose(
        sympy.lambdify(sympy.symbols("n th"), sympy.sympify(p), "numpy")(X[:, 0], X[:, 1]),
        model, rtol=1e-12)
    # the sympy form of the engine itself (GPEliteRegressor.sympy, SRBench)
    s2 = core.node_to_sympy(t, ["n", "th"])
    assert "asin(" in s2
    f2 = sympy.lambdify(sympy.symbols("n th"), sympy.sympify(s2), "numpy")
    assert np.allclose(f2(X[:, 0], X[:, 1]), model, rtol=1e-12, atol=0)


def test_formula_departs_where_the_clip_acts():
    X = np.array([[0.5], [2.0], [3.0]])
    t = N("arcsin", X_(0))
    model = core.evaluate_vector(t, X)
    printed = F.evaluate(t, X)
    assert model[1] == math.pi / 2 and np.isnan(printed[1])


def test_units_arcsin_needs_a_dimensionless_argument():
    ok, _ = GD.check_dimensions(N("arcsin", N("/", X_(0), X_(1))),
                                {0: {"m": 1}, 1: {"m": 1}}, {})
    assert ok
    ok, msg = GD.check_dimensions(N("arcsin", X_(0)), {0: {"m": 1}}, {})
    assert not ok and "arcsin" in msg
    ok, _ = GD.check_dimensions(N("arcsin", X_(0)), {0: {}}, {"m": 1})
    assert not ok                               # its result is dimensionless


def test_arcsin_only_in_the_pools_trig_and_full():
    for pool in ("physical", "poly", "conserve"):
        assert "arcsin" not in core._GENCSV_POOLS[pool][2]
    for pool in ("trig", "full"):
        u_ops, u_w = core._GENCSV_POOLS[pool][2], core._GENCSV_POOLS[pool][3]
        assert len(u_ops) == len(u_w)
        assert u_w[u_ops.index("arcsin")] == 2
    assert "arcsin" in core.ALL_UNARY_OPS


def test_typed_start_draws_arcsin_only_where_the_pool_has_it():
    feats = [("X[0]", {"m": 1}), ("X[1]", {"m": 1})]
    trig = set(core._GENCSV_POOLS["trig"][0] + core._GENCSV_POOLS["trig"][2])
    phys = set(core._GENCSV_POOLS["physical"][0] + core._GENCSV_POOLS["physical"][2])
    DS._CTX.clear()
    with_it = DS._context(feats, frozenset(trig)).prods[True]
    without = DS._context(feats, frozenset(phys)).prods[True]
    hist = DS._context(feats, None).prods[True]
    assert ("arcsin",) in with_it
    assert ("arcsin",) not in without and ("arcsin",) not in hist


def X_(i):
    return N("X[%d]" % i)


# ── 1.3, A2: the arcsine with its own constant ────────────────────────────

def test_arcsin_carries_its_own_constant():
    cases = [
        (N("arcsin", X_(0)), "arcsin((1.0 * X[0]))"),
        (N("arcsin", N("*", N(2.0), X_(0))), "arcsin((2.0 * X[0]))"),
        (N("arcsin", N("*", X_(0), N(3.0))), "arcsin((X[0] * 3.0))"),
        (N("arcsin", N("/", N(2.0), X_(0))), "arcsin((2.0 / X[0]))"),
        (N("arcsin", N("*", X_(0), N("sin", X_(1)))),
         "arcsin((1.0 * (X[0] * sin(X[1]))))"),
    ]
    for t, want in cases:
        once = core.simplify(t)
        assert core.to_string(once) == want
        twice = core.simplify(once)
        assert twice.exact_hash() == once.exact_hash()
    assert core.simplify(N("arcsin", N(0.5))).value == 0.5235987755982989
    assert core.to_string(core.simplify(N("sin", X_(0)))) == "sin(X[0])"


def _polished_error(tree, xs, ys, xt, yt):
    cfg = core.make_cfg_nd(n_features=xs.shape[1])
    pol = core._refit_scaling(core.optimize_constants_adam(tree.copy(), xs, ys, cfg),
                              xs, ys)
    conv = core._lm_to_convergence(pol, xs, ys, cfg)
    out = core._refit_scaling(conv, xs, ys) if conv is not None else pol
    p = core.evaluate_vector(out, xt)
    return float(np.mean((p - yt) ** 2) / np.var(yt))


def test_the_form_of_the_examination_comes_back_exact(monkeypatch):
    """I.26.2 seed 2 of campaign A1 returned, in the engine's variables
    (each divided by its largest value), arcsin(X0 * sin(4.964 * X1)), one
    constant short of the law. With the arcsine's own constant, the
    engine's polish makes it exact; without it, it cannot."""
    r = np.random.RandomState(3)
    X = np.c_[r.uniform(0, 1, 200), r.uniform(1, 5, 200)]
    y = np.arcsin(X[:, 0] * np.sin(X[:, 1]))
    xs = X / np.abs(X).max(axis=0)
    inner = N("*", X_(0), N("sin", N("*", N(4.964236), X_(1))))
    tree = N("+", N(-0.000573), N("*", N(0.982939), N("arcsin", inner)))
    with np.errstate(all="ignore"):
        e = _polished_error(core.simplify(tree), xs[:140], y[:140], xs[140:], y[140:])
        assert e < 1e-20
        monkeypatch.setattr(core, "_has_own_factor", lambda n: True)   # A1 alone
        core._clear_simplify_caches()
        e1 = _polished_error(core.simplify(tree), xs[:140], y[:140], xs[140:], y[140:])
        assert e1 > 1e-6
