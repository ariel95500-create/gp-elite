"""Guarantees that must never silently break again.

Every test here pins down a defect that actually existed and went unnoticed:
the exported formula was wrong on raw data, the dimensional gate and auditor
disagreed, the typed generator ignored `operators=`, the library wrote files
into its own install directory, and so on. Each one was found by hand; these
tests make sure it stays fixed.

Run: pytest -q   (from the repository root)
"""
import os
import random
import subprocess
import sys
import textwrap
import time

import numpy as np
import pytest

from gp_elite import GPEliteRegressor, core, symbolic_regression
import gp_elite.dim_search as DS
from gp_elite import dimensions as GD

N = core.Node


def X(i):
    return N("X[%d]" % i)


def _ops_in(tree, acc):
    if tree.left is not None or tree.right is not None:
        acc.add(str(tree.value))
        if tree.left is not None:
            _ops_in(tree.left, acc)
        if tree.right is not None:
            _ops_in(tree.right, acc)
    return acc


# ── 1. The exported formula IS the model ────────────────────────────────────
# Before v0.6.2, sympy() returned the tree written in the internal scaled
# space but labelled with raw variable names: on y = 3x with x in [1, 5] it
# returned 14.86*X0, off by 58.75 on the raw data.

def _eval_sympy_string(s, cols):
    """Evaluate a formula string with sympy on the columns {name: values}."""
    sympy = pytest.importorskip("sympy")
    loc = {k: sympy.Symbol(k) for k in cols}
    expr = sympy.sympify(s, locals=loc)
    syms = sorted(expr.free_symbols, key=lambda z: z.name)
    fn = sympy.lambdify(syms, expr, [{"Heaviside": lambda t, h=0.5: np.heaviside(t, h)},
                                     "numpy"])
    n = len(next(iter(cols.values())))
    with np.errstate(all="ignore"):
        v = np.asarray(fn(*[cols[z.name] for z in syms]), dtype=complex)
    return v if v.ndim else np.full(n, complex(v))


def _formula_matches_predict(est, Xd):
    cols = {"X%d" % i: Xd[:, i] for i in range(Xd.shape[1])}
    v = _eval_sympy_string(est.sympy(), cols)
    return float(np.max(np.abs(v - est.predict(Xd))))


@pytest.mark.parametrize("case", ["one_var", "scales_x1000", "units"])
def test_exported_formula_equals_predict_on_raw_data(case):
    r = np.random.RandomState(0)
    if case == "one_var":
        Xd = r.uniform(1, 5, (60, 1)); y = 3.0 * Xd[:, 0]; kw = {}
    elif case == "scales_x1000":
        A = r.uniform(2, 6, (60, 2)); Xd = np.column_stack([A[:, 0], A[:, 1] * 1000.0])
        y = A[:, 0] * A[:, 1]; kw = {}
    else:
        Xd = r.uniform(1, 3, (60, 2)); y = 0.5 * Xd[:, 0] * Xd[:, 1] ** 2
        kw = dict(units=["kg", "m/s"], target_units="J")
    est = GPEliteRegressor(generations=6, random_state=0, parallel=False, **kw).fit(Xd, y)
    assert _formula_matches_predict(est, Xd) < 1e-6


# Up to 0.7 only the division-by-max normalisation was folded, and only in
# sympy(): `expression` stayed in scaled space, and with min-max (the default
# for ANY column with a non-positive value, hence every SRBench black-box
# problem, whose inputs are standardised) or z-score the export was off by
# orders of magnitude (89 on a target of amplitude ~20). The review asked for
# exactly this property test: divmax, minmax, standard, one and several
# variables.

from gp_elite import formula as FM                      # noqa: E402
from sklearn.preprocessing import MinMaxScaler, StandardScaler   # noqa: E402

_SCALERS = {
    "divmax": lambda: core._ShiftFreeScaler(),
    "minmax": lambda: MinMaxScaler(feature_range=(-2.0, 2.0)),
    "standard": lambda: StandardScaler(),
    "none": lambda: core._IdentityScaler(),
}

# Trees chosen to hit every folding rule, including the protected operators
# whose engine semantics differ from plain maths on signed arguments.
_FOLD_TREES = [
    N("*", N(2.5), X(0)),
    N("+", N(1.0), N("*", X(0), X(1))),
    N("/", X(0), N("+", X(1), N(3.0))),
    N("pow", X(0), N(2.0)),                       # sign-aware even power
    N("pow", X(0), N(3.0)),
    N("pow", X(1), N(-1.0)),
    N("pow", X(0), N(1.5)),                       # |u|^1.5
    N("pow", X(0), N(0.0)),                       # engine: sign(u)
    N("sqrt", X(1)),
    N("log", N("*", N(0.5), X(0))),
    N("exp", N("neg", X(1))),
    N("tanh", N("-", X(0), X(1))),
    N("sq", N("+", X(0), N(0.25))),
    N("cube", X(1)),
    N("abs", N("-", X(0), N(1.0))),
    N("sin", N("*", N(3.0), X(0))),
    N("-", N("pow", X(0), N(2.0)), N("sq", X(1))),
    N("/", N(1.0), N("sqrt", N("+", N("sq", X(0)), N("sq", X(1))))),
    N("*", N(3.0), N("+", N("sq", X(0)), N("neg", N("sq", X(1))))),   # distribution
    N("*", N(1.0000000002), N("*", X(0), X(1))),                        # "1 *" noise
    N("*", X(1), N("/", N(2.0), N("+", X(0), N(6.0)))),                # a * (1 / b)
]


@pytest.mark.parametrize("kind", sorted(_SCALERS))
@pytest.mark.parametrize("signed", [False, True])
def test_raw_formula_folding_is_exact(kind, signed):
    """Every rule of the folding, for every scaler: text AND sympy forms
    reproduce the engine's predictions on the raw data."""
    r = np.random.RandomState(3)
    Xd = r.uniform(-4.0 if signed else 0.5, 5.0, (70, 2))
    sc = _SCALERS[kind]()
    Xs = sc.fit_transform(Xd)
    cols = {"a": Xd[:, 0], "b": Xd[:, 1]}
    for tree in _FOLD_TREES:
        p = core.evaluate_vector(tree, Xs)
        rf = FM.raw_formula(tree, sc, Xd, ["a", "b"])
        assert rf.exact, (kind, core.to_string(tree), rf.max_error)
        tol = 1e-6 * max(np.max(np.abs(p)), 1e-12)
        for s in (rf.sympy(), FM.to_text(rf.tree, ["a", "b"], rf._positive,
                                         _parsable=True)):
            assert np.max(np.abs(_eval_sympy_string(s, cols) - p)) <= tol, \
                (kind, core.to_string(tree), s)


@pytest.mark.parametrize("normalize", ["divmax", "minmax", "standard", "none", "auto"])
@pytest.mark.parametrize("data", ["positive_1var", "signed_2var"])
def test_delivered_formula_is_the_model(normalize, data):
    """End to end: expression, sympy() and every Pareto entry are written in
    the raw variables and reproduce predict() on the raw data."""
    r = np.random.RandomState(1)
    if data == "positive_1var":
        Xd = r.uniform(1, 5, (80, 1)); y = 3.0 * Xd[:, 0] + 2.0; names = ["x"]
    else:
        Xd = r.uniform(-3, 3, (80, 2)); y = 2.0 * Xd[:, 0] * Xd[:, 1] + Xd[:, 0] ** 2
        names = ["u", "v"]
    res = symbolic_regression(Xd, y, feature_names=names, normalize=normalize,
                              generations=6, parallel=False, seed=0)
    cols = {nm: Xd[:, i] for i, nm in enumerate(names)}
    tol = 1e-6 * max(np.max(np.abs(res.predict(Xd))), 1e-12)
    assert res.formula_exact is True
    assert np.max(np.abs(_eval_sympy_string(res.sympy(), cols)
                         - res.predict(Xd))) <= tol
    for e in res.pareto or []:
        assert np.max(np.abs(_eval_sympy_string(e.sympy(), cols)
                             - e.predict(Xd))) <= \
            1e-6 * max(np.max(np.abs(e.predict(Xd))), 1e-12)
    # the display names the raw columns, never the engine's X[i]
    assert "X[" not in res.expression


def test_product_by_a_reciprocal_prints_as_a_division():
    """The folding writes c/u as c * (1/u); it used to print "v2 * 1 / v1"."""
    tree = N("*", X(1), N("/", N(1.0), N("*", X(0), X(2))))
    assert FM.to_text(tree, ["a", "b", "c"]) == "b / (a * c)"


def test_three_x_is_printed_three_x():
    """The review's example: y = 3x, x in [1, 5], used to print 14.86*x."""
    Xd = np.linspace(1, 5, 40).reshape(-1, 1)
    res = symbolic_regression(Xd, 3.0 * Xd[:, 0], feature_names=["x"],
                              generations=5, parallel=False, seed=0)
    assert res.expression == "3 * x"


# ── 2. Dimensional semantics: one source of truth ───────────────────────────

@pytest.mark.parametrize("tree, fd, tgt", [
    (N("+", N(1.0), N("*", N(2.0), X(0))), {0: {"m": 1}}, {"m": 1}),        # 1 + 2x : invalid
    (N("*", N(2.0), X(0)), {0: {"m": 1}}, {"m": 1}),                         # 2x : valid
    (N("pow", X(0), X(1)), {0: {"m": 1}, 1: {}}, {"m": 1}),                  # x^z : invalid
    (N("pow", X(0), N(2.0)), {0: {"m": 1}}, {"m": 2}),                       # x^2 : valid
    (N("pow", X(0), X(1)), {0: {}, 1: {}}, {}),                              # z^w : valid
])
def test_engine_gate_and_auditor_agree(tree, fd, tgt):
    try:
        audit = GD.check_dimensions(tree, fd, tgt)[0]
    except Exception:
        audit = False
    assert DS.is_typed_valid(tree, fd, tgt) == audit


def test_variable_exponent_on_dimensioned_base_is_rejected():
    ok, _ = GD.check_dimensions(N("pow", X(0), X(1)), {0: {"m": 1}, 1: {}}, {"m": 1})
    assert ok is False


@pytest.mark.parametrize("bad", ["m garbage", "m/(s", "kg**m", "@@@", "m/", "m s", "kg^"])
def test_malformed_unit_strings_are_rejected(bad):
    with pytest.raises(ValueError):
        DS.parse_unit_string(bad)


@pytest.mark.parametrize("good, expected", [
    ("m/s", {"m": 1, "s": -1}), ("J", {"kg": 1, "m": 2, "s": -2}),
    ("kg*m/s^2", {"kg": 1, "m": 1, "s": -2}), ("s^-1", {"s": -1}), ("1", {}),
])
def test_valid_unit_strings_parse(good, expected):
    got = DS.parse_unit_string(good)
    assert {k: float(v) for k, v in got.items()} == {k: float(v) for k, v in expected.items()}


# ── 3. operators= is respected on every generation path ─────────────────────

@pytest.mark.parametrize("pool", sorted(core._GENCSV_POOLS))
def test_typed_generator_respects_pool(pool):
    b, _, u, _ = core._GENCSV_POOLS[pool]
    allowed = frozenset(b) | frozenset(u)
    fd = {0: {"m": 1}, 1: {"s": 1}, 2: {}}
    rng = random.Random(0)
    seen = set()
    for tgt in ({"m": 1, "s": -1}, {}, {"m": 2}):
        for _ in range(60):
            t = DS.typed_random_tree(tgt, 5, fd, rng, ops=allowed)
            if t is not None:
                _ops_in(t, seen)
                _ops_in(DS.typed_mutate(t, fd, 3, rng, ops=allowed), seen)
    assert seen <= allowed, sorted(seen - allowed)


def test_stigmergic_builders_respect_pool(monkeypatch):
    """The stigmergic builders used to wrap trees with a unary drawn from a
    hard-coded ["sin", "cos", "neg", "sq"]: cos reached the Pareto front under
    operators='physical', which has no trig. Checked on the builders directly,
    where the leak is frequent (it only rarely survives to the front)."""
    r = np.random.RandomState(1)
    Xd = r.uniform(0.5, 3, (120, 2)); y = 2 * np.pi * np.sqrt(Xd[:, 0] / Xd[:, 1])
    symbolic_regression(Xd, y, operators="physical", generations=6, parallel=False, seed=0)
    allowed = (frozenset(core._GENCSV_POOLS["physical"][0])
               | frozenset(core._GENCSV_POOLS["physical"][2]))
    # The API switches the engine back to console mode when the fit ends;
    # reproduce the in-fit conditions (active pool) before calling builders.
    b, bw, u, uw = core._GENCSV_POOLS["physical"]
    monkeypatch.setattr(core, "_GENERIC_CSV_MODE", True)
    monkeypatch.setattr(core, "_GENERIC_BINARY_OPS", list(b))
    monkeypatch.setattr(core, "_GENERIC_UNARY_OPS", list(u))
    cfg = core.make_cfg_nd(n_features=2, x_min=-2.0, x_max=2.0, fast=True)
    random.seed(0)
    seen = set()
    for _ in range(300):
        for t in (core.build_stigmergic_tree(core.FRAGMENT_LIB, cfg),
                  core.build_stigmergic_tree_v2(core.FRAGMENT_LIB, core.COGRAPH, cfg)):
            if t is not None:
                _ops_in(t, seen)
    assert seen <= allowed, sorted(seen - allowed)


# ── 4. time_limit: stop on time, always return a model ──────────────────────

@pytest.mark.parametrize("bad", [0, -5, float("nan"), float("inf")])
def test_time_limit_rejects_invalid_values(bad):
    with pytest.raises(ValueError):
        symbolic_regression(np.ones((40, 1)), np.arange(40.0), generations=2, time_limit=bad)


def test_time_limit_stops_and_returns_a_model():
    r = np.random.RandomState(0)
    Xd = r.uniform(1, 4, (400, 3))
    # noisy target: no exact fit exists, so the search cannot end early on a
    # perfect score and must be stopped by the time limit
    y = Xd[:, 0] * Xd[:, 1] / Xd[:, 2] + r.normal(0.0, 0.1, 400)
    t0 = time.time()
    res = symbolic_regression(Xd, y, generations=5000, parallel=False, seed=0, time_limit=3.0)
    dt = time.time() - t0
    assert res.time_limit_reached is True
    assert dt < 3.0 + 10.0                    # generous: CI machines vary a lot
    assert np.all(np.isfinite(res.predict(Xd)))


def test_generous_time_limit_changes_nothing():
    r = np.random.RandomState(0)
    Xd = r.uniform(1, 4, (80, 2)); y = Xd[:, 0] * Xd[:, 1]
    a = symbolic_regression(Xd, y, generations=5, parallel=False, seed=3)
    b = symbolic_regression(Xd, y, generations=5, parallel=False, seed=3, time_limit=3600)
    assert b.time_limit_reached is False
    assert (a.expression, a.size) == (b.expression, b.size)


# ── 5. Near-domain stability guard ──────────────────────────────────────────

def test_near_probes_do_not_consume_engine_randomness():
    random.seed(7); np.random.seed(7)
    before = (random.getstate(), np.random.get_state()[1].copy())
    core._build_near_probes(np.random.RandomState(0).uniform(1, 3, (50, 2)), np.arange(50.0))
    after = (random.getstate(), np.random.get_state()[1])
    assert before[0] == after[0] and np.array_equal(before[1], after[1])


def test_true_relativistic_law_is_judged_stable():
    # m / sqrt(1 - v^2/c^2), v in [1, 2], c in [3, 10]: probing too far out
    # crosses v = c; the guard must not penalise the true law for that.
    r = np.random.RandomState(0)
    Xd = np.column_stack([r.uniform(1, 5, 200), r.uniform(1, 2, 200), r.uniform(3, 10, 200)])
    y = Xd[:, 0] / np.sqrt(1 - Xd[:, 1] ** 2 / Xd[:, 2] ** 2)
    law = N("/", X(0), N("sqrt", N("-", N(1.0), N("/", N("sq", X(1)), N("sq", X(2))))))
    core._build_near_probes(Xd, y)
    core._NEAR_CACHE.clear()
    assert core._near_domain_stable(law)


def test_spurious_pole_inside_the_data_is_detected():
    Xd = np.linspace(1.0, 3.0, 60).reshape(-1, 1)
    y = 2.0 * Xd[:, 0]
    pole = N("/", N(5.0), N("-", X(0), N(2.000123)))      # diverges inside [1, 3]
    core._build_near_probes(Xd, y)
    core._NEAR_CACHE.clear()
    assert not core._near_domain_stable(pole)
    assert core._near_domain_stable(N("*", N(2.0), X(0)))


def test_guard_only_breaks_ties(monkeypatch):
    Xd = np.linspace(1.0, 3.0, 60).reshape(-1, 1); y = 2.0 * Xd[:, 0]
    core._build_near_probes(Xd, y); core._NEAR_CACHE.clear()
    monkeypatch.setattr(core, "_VAL_YS", y[:12])
    unstable_small = N("/", N(5.0), N("-", X(0), N(2.000123)))
    stable_large = N("+", N("*", N(2.0), X(0)), N("*", N(0.0), N("sq", X(0))))
    saved = list(core._VAL_CANDS)
    try:
        # both statistically indistinguishable -> the stable one wins
        core._VAL_CANDS[:] = [(1e-3, 1e-3, core.tree_size(unstable_small), unstable_small),
                              (1e-3, 1e-3, core.tree_size(stable_large), stable_large)]
        node, _ = core._select_one_se(None, float("inf"))
        assert node is stable_large
        # no stable alternative -> historical behaviour (smallest) unchanged
        core._VAL_CANDS[:] = [(1e-3, 1e-3, core.tree_size(unstable_small), unstable_small)]
        node, _ = core._select_one_se(None, float("inf"))
        assert node is unstable_small
    finally:
        core._VAL_CANDS[:] = saved


# ── 6. No side effects ──────────────────────────────────────────────────────

def test_fit_writes_no_file(tmp_path, monkeypatch):
    """The engine used to (re)write gp_elite_log.csv into its own install
    directory on every fit. Checked by modification time, not just by
    presence: a file rewritten in place is a side effect too."""
    monkeypatch.chdir(tmp_path)
    pkg = os.path.dirname(core.__file__)

    def snapshot():
        return {f: os.stat(os.path.join(pkg, f)).st_mtime_ns
                for f in os.listdir(pkg) if f != "__pycache__"}
    before = snapshot()
    time.sleep(0.05)
    Xd = np.random.RandomState(0).uniform(1, 3, (60, 2))
    symbolic_regression(Xd, Xd[:, 0] + Xd[:, 1], generations=3, parallel=False)
    after = snapshot()
    assert os.listdir(tmp_path) == []
    touched = {f for f in after if before.get(f) != after[f]}
    assert touched == set(), touched


@pytest.mark.parametrize("n_rows", [120, 3000])
def test_parallel_fallback_for_scripts_without_main_guard(tmp_path, n_rows):
    """A script without `if __name__ == "__main__":` used to be re-run by every
    worker process (measured: 3 runs, parallel twice slower than sequential).
    It must now fall back to sequential, warn once, and give the sequential
    result. With 3000 rows the data no longer fit in the pipe that starts a
    worker: the parent then blocked forever on it once the worker had exited
    (fixed by handing the data to the workers through a file)."""
    script = tmp_path / "unguarded.py"
    script.write_text(textwrap.dedent("""
        import warnings, numpy as np
        from gp_elite import symbolic_regression
        r = np.random.RandomState(0)
        X = r.uniform(1, 4, (%d, 3)); y = X[:, 0] * X[:, 1]
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            a = symbolic_regression(X, y, generations=3, parallel=True, seed=0)
        b = symbolic_regression(X, y, generations=3, parallel=False, seed=0)
        print("WARNINGS", sum("__main__" in str(x.message) for x in w))
        print("SAME", a.expression == b.expression)
    """) % n_rows)
    env = dict(os.environ, PYTHONHASHSEED="0")
    out = subprocess.run([sys.executable, str(script)], capture_output=True,
                         text=True, timeout=180, env=env, cwd=str(tmp_path))
    assert out.returncode == 0, out.stderr[-2000:]
    lines = [l for l in out.stdout.splitlines() if l.startswith(("WARNINGS", "SAME"))]
    assert "WARNINGS 1" in lines and "SAME True" in lines, out.stdout[-1500:]


def test_parallel_workers_are_quiet_when_the_fit_is(tmp_path):
    """verbose=False silences the fit; its worker processes printed their
    progress anyway (on machines with four cores or more, every fit)."""
    script = tmp_path / "guarded.py"
    script.write_text(textwrap.dedent("""
        import numpy as np
        from gp_elite import symbolic_regression
        if __name__ == "__main__":
            r = np.random.RandomState(0)
            X = r.uniform(1, 4, (400, 5)); y = X[:, 0] * X[:, 1] / X[:, 2] + 0.3 * X[:, 3]
            symbolic_regression(X, y, generations=3, parallel=True, seed=0)
            print("DONE")
    """))
    env = dict(os.environ, PYTHONHASHSEED="0")
    out = subprocess.run([sys.executable, str(script)], capture_output=True,
                         text=True, timeout=180, env=env, cwd=str(tmp_path))
    assert out.returncode == 0, out.stderr[-2000:]
    assert out.stdout.strip() == "DONE", out.stdout[-1500:]


# ── 7. A model is evaluated with its own constants ──────────────────────────
# Compiled functions, predictions, fitness values and simplified forms were
# cached under a hash that rounds constants to 4 decimals. Two trees that
# differ only further down shared one entry: predict() could compute with the
# constants of another model (compiled earlier, possibly in an earlier fit of
# the same process), and two identical fits in a row could diverge.

def test_evaluation_never_reuses_another_trees_constants():
    Xd = np.ones((3, 1))
    a = core.evaluate_vector(N("*", N(1.00001), X(0)), Xd)
    b = core.evaluate_vector(N("*", N(1.00002), X(0)), Xd)
    assert a[0] == 1.00001 and b[0] == 1.00002


def test_simplify_never_merges_different_constants():
    t = N("+", N("*", N(1.00001), X(0)), N("*", N(1.00002), X(0)))
    v = core.evaluate_vector(core.simplify(t), np.array([[2.0]]))[0]
    assert v == pytest.approx(2.0 * (1.00001 + 1.00002), rel=1e-12)


def test_identical_fits_in_one_process_are_identical():
    """Measured before the fix: in robust mode the second of two identical
    fits returned a different model."""
    r = np.random.RandomState(42)
    x = np.linspace(0, 10, 80)
    y = 2.0 * x + 1.0 + r.normal(0, 0.5, 80)
    idx = r.choice(80, 16, replace=False)
    y[idx] += r.choice([-1, 1], 16) * r.uniform(15, 30, 16)
    kw = dict(feature_names=["x"], operators="poly", generations=35,
              validation_split=0.0, seed=0, robust=True, parallel=False)
    first = symbolic_regression(x.reshape(-1, 1), y, **kw).expression
    second = symbolic_regression(x.reshape(-1, 1), y, **kw).expression
    assert first == second


# ── 8. A law found exactly is not traded for a shorter approximation ───────
# The final choice keeps the smallest candidate within 0.3 % of R² of the
# best, to avoid fitting noise. On Feynman I.18.12 that returned
# 0.0776 + 0.9967*r*F*sin(1.0106*th) while r*F*sin(th), exact, was in the
# front. When the best candidate reproduces the hold-out to numerical
# precision there is no noise to avoid: only exact candidates stay eligible.

def _pick(monkeypatch, cands):
    monkeypatch.setattr(core, "_VAL_YS", np.linspace(-1.0, 1.0, 50))
    monkeypatch.setattr(core, "_VAL_CANDS", list(cands))
    monkeypatch.setattr(core, "_NEAR_PROBE_XS", None)
    return core._select_one_se(None, float("inf"))[0]


def test_exact_law_is_not_traded_for_an_approximation(monkeypatch):
    exact = N("*", X(0), X(1))
    approx = X(0)
    got = _pick(monkeypatch, [(1e-31, 0.0, 14, exact), (3e-4, 1e-5, 12, approx)])
    assert got is exact


def test_parsimony_tolerance_unchanged_on_noisy_data(monkeypatch):
    big = N("*", X(0), X(1))
    small = X(0)
    got = _pick(monkeypatch, [(1e-2, 1e-4, 14, big), (1.05e-2, 1e-4, 12, small)])
    assert got is small


# ── 9. A typo is an error, not a silent substitution ────────────────────────

@pytest.mark.parametrize("kw", [dict(operators="phsyical"), dict(speed="fats"),
                                dict(normalize="divmx")])
def test_unknown_option_values_are_rejected(kw):
    Xd = np.random.RandomState(0).uniform(1, 3, (40, 1))
    with pytest.raises(ValueError):
        symbolic_regression(Xd, Xd[:, 0], generations=2, parallel=False, **kw)


# ── 10. A preset does what its documentation announces ─────────────────────
# speed="thorough" was documented as 200 generations, but symbolic_regression
# kept its own default of 100 (only GPEliteRegressor applied the preset).

class _Captured(Exception):
    pass


@pytest.mark.parametrize("kw,expected", [(dict(speed="thorough"), 200),
                                         (dict(), 100),
                                         (dict(speed="thorough", generations=7), 7)])
def test_thorough_preset_runs_its_announced_generations(monkeypatch, kw, expected):
    seen = {}

    def fake_evolve(fn, cfg, **_):
        seen["generations"] = cfg.GENERATIONS
        raise _Captured

    monkeypatch.setattr(core, "evolve", fake_evolve)
    Xd = np.random.RandomState(0).uniform(1, 3, (40, 1))
    with pytest.raises(_Captured):
        symbolic_regression(Xd, Xd[:, 0], parallel=False, **kw)
    assert seen["generations"] == expected


# ── 11. A variable exponent never switches the power to its integer branch ──
# The engine's power is sign-aware for a CONSTANT integer exponent (pow(u, 3)
# keeps the sign of u). Applied row by row to an exponent that depends on the
# variables, that branch made the model jump wherever the exponent landed on
# an integer (with division by max|x| a column is exactly ±1 on its extreme
# row, so it always happened), the search could use the jump as a row
# indicator, and no readable formula reproduced the model: on standardised
# 561_cpu the delivered formula and predict() were 0.97 apart on 2 rows.

def test_variable_exponent_power_is_continuous_and_printed_exactly():
    r = np.random.RandomState(0)
    Xd = np.column_stack([r.uniform(-3.0, -0.5, 60), r.uniform(0.2, 2.0, 60)])
    Xd[7, 1] = 2.0                    # the exponent lands exactly on an integer
    for kind in ("divmax", "none"):
        sc = _SCALERS[kind]()
        Xs = sc.fit_transform(Xd)
        tree = N("pow", X(0), X(1))
        p = core.evaluate_vector(tree, Xs)
        assert p[7] > 0, kind         # |u|^v on that row too, like its neighbours
        rf = FM.raw_formula(tree, sc, Xd, ["a", "b"])
        assert rf.exact, (kind, rf.max_error)
        # an exponent built from constants only keeps the sign-aware branch
        const_tree = N("pow", X(0), N("neg", N(2.0)))
        pc = core.evaluate_vector(const_tree, Xs)
        assert np.all(pc < 0), kind
        assert FM.raw_formula(const_tree, sc, Xd, ["a", "b"]).exact, kind


# ── 12. A formula that departs from the model is never delivered silently ───
# The printed formula is the mathematical function without the engine's
# numerical safety nets. Where one of them acts on the data (a division by a
# near-zero denominator here), the formula departs from predict(): the rows
# are counted and the user is warned; result.formula_exact says False.

def test_rows_where_a_safety_net_acts_are_counted():
    Xd = np.array([[1.0], [2.0], [3.0], [4.0]])
    sc = core._IdentityScaler()
    sc.fit_transform(Xd)
    rf = FM.raw_formula(N("/", N(1.0), N("-", X(0), N(2.0))), sc, Xd, ["x"])
    assert rf.exact is False and rf.rows_off == 1


def test_inexact_formula_triggers_a_warning(monkeypatch):
    import gp_elite.api as API
    real = API._formula.raw_formula

    def inexact(node, scaler, X_raw, feature_names=None, predictions=None):
        rf = real(node, scaler, X_raw, feature_names, predictions)
        rf.exact, rf.rows_off, rf.max_error = False, 2, 0.5
        return rf

    monkeypatch.setattr(API._formula, "raw_formula", inexact)
    Xd = np.random.RandomState(0).uniform(1, 3, (40, 1))
    with pytest.warns(RuntimeWarning, match="departs from predict"):
        res = symbolic_regression(Xd, 2 * Xd[:, 0], generations=2, parallel=False, seed=0)
    assert res.formula_exact is False


# ── 13. Every evaluator of the engine gives a tree the same value ───────────
# Up to 0.7 the vectorised evaluator wrote a negative constant under a square
# as "(-0.5 ** 2)", which Python reads -(0.5 ** 2): sq(-0.5) evaluated to
# -0.25 during the search while the scalar evaluator, the constant optimiser
# and the delivered formula gave +0.25 (0.8 % of the trees evaluated in a
# search contained the pattern).

def test_square_of_a_negative_constant_is_positive_in_every_evaluator():
    t = N("*", N("sq", N(-0.5)), X(0))
    xs = np.array([[1.0], [2.0], [-3.0]])
    expected = np.array([0.25, 0.5, -0.75])
    assert np.array_equal(core.evaluate_vector(t, xs), expected)
    assert [core.evaluate(t, row) for row in xs] == list(expected)
    fn, consts = core.compile_parametric(t)
    assert np.array_equal(fn(xs, np.array([c.value for c in consts])), expected)


def test_prediction_cache_never_serves_another_arrays_predictions():
    """The prediction cache is keyed by id(array). Once an array is freed its
    id can be given to another array of the same size: the cache must not
    serve the old predictions for it."""
    import weakref
    t = N("*", N(2.0), X(0))
    a = np.array([[1.0], [2.0], [3.0]])
    b = np.array([[10.0], [20.0], [30.0]])

    class Dead:
        pass
    ghost = Dead()
    dead_ref = weakref.ref(ghost)
    del ghost                                  # an array that no longer exists
    key = (t.exact_hash(), id(b), b.shape[0])
    core._PRED_CACHE[key] = (dead_ref, np.array([2.0, 4.0, 6.0]))
    try:
        assert np.array_equal(core._predict_cached(t, b), [20.0, 40.0, 60.0])
        assert np.array_equal(core._predict_cached(t, a), [2.0, 4.0, 6.0])
    finally:
        core._PRED_CACHE.pop(key, None)


# ── 14. Bad inputs are refused with a clear message, never fitted silently ──
# Measured on 0.7: a NaN in X or an infinity in y went through, and the fit
# returned an unrelated formula without any warning; predict() took one
# sample given as a 1-D array for a column, accepted a wrong number of
# columns, and returned 0 for a row containing NaN.

def _xy():
    r = np.random.RandomState(0)
    X = r.uniform(1, 5, (40, 2))
    return X, X[:, 0] * X[:, 1] + 1.0


@pytest.mark.parametrize("where", ["X", "y"])
def test_missing_or_infinite_values_are_refused(where):
    X, y = _xy()
    X, y = X.copy(), y.copy()
    if where == "X":
        X[3, 1] = np.nan
    else:
        y[5] = np.inf
    with pytest.raises(ValueError, match="missing or infinite"):
        symbolic_regression(X, y, generations=2, parallel=False, seed=0)


def test_non_numeric_column_is_named():
    pd = pytest.importorskip("pandas")
    X, y = _xy()
    df = pd.DataFrame({"mass": X[:, 0], "label": ["a"] * 40})
    with pytest.raises(ValueError, match="'label' is not numeric"):
        symbolic_regression(df, y, generations=2, parallel=False, seed=0)


def test_dataframe_column_names_become_the_variables():
    pd = pytest.importorskip("pandas")
    X, y = _xy()
    df = pd.DataFrame({"mass": X[:, 0], "speed": X[:, 1]})
    res = symbolic_regression(df, y, generations=5, parallel=False, seed=0)
    assert res.feature_names == ["mass", "speed"]
    assert "mass" in res.expression and "speed" in res.expression


def test_target_as_a_column_and_single_variable_as_1d_are_accepted():
    X, y = _xy()
    res = symbolic_regression(X, y.reshape(-1, 1), generations=2,
                              parallel=False, seed=0)
    assert res.predict(X).shape == (40,)
    res1 = symbolic_regression(X[:, 0], 3.0 * X[:, 0], generations=2,
                               parallel=False, seed=0)
    assert res1.predict(X[:, :1]).shape == (40,)


def test_predict_checks_the_shape_and_propagates_missing_values():
    X, y = _xy()
    res = symbolic_regression(X, y, generations=5, parallel=False, seed=0)
    one = X[:1]
    with pytest.raises(ValueError, match="reshape\\(1, -1\\)"):
        res.predict(one.ravel())                  # one sample given as 1-D
    with pytest.raises(ValueError, match="fitted on 2"):
        res.predict(np.ones((4, 3)))
    with pytest.raises(ValueError, match="fitted on 2"):
        res.predict(np.ones((4, 1)))
    Xm = X[:3].copy()
    Xm[1, 0] = np.nan
    p = res.predict(Xm)
    assert np.isnan(p[1]) and np.isfinite(p[[0, 2]]).all()
    assert np.array_equal(p[[0, 2]], res.predict(X[[0, 2]]))
    for entry in res.pareto or []:
        assert np.isnan(entry.predict(Xm)[1])


def test_sympy_expr_is_right_for_any_column_name():
    sympy = pytest.importorskip("sympy")
    X, y = _xy()
    res = symbolic_regression(X, y, feature_names=["E", "mass (kg)"],
                              generations=5, parallel=False, seed=0)
    with pytest.warns(UserWarning, match="misread"):
        res.sympy()
    e = res.sympy_expr()
    assert {str(s) for s in e.free_symbols} <= {"E", "mass (kg)"}
    f = sympy.lambdify([sympy.Symbol("E"), sympy.Symbol("mass (kg)")], e, "numpy")
    assert np.allclose(f(X[:, 0], X[:, 1]), res.predict(X), rtol=1e-9, atol=1e-9)


# ── 15. seed= alone reproduces a fit, whatever PYTHONHASHSEED is ────────────
# Measured on 0.7: two launches of the same script with seed=0 returned
# different models unless PYTHONHASHSEED was set before starting Python
# (tree hashes carried strings, and their values oriented some draws).

def test_same_seed_same_model_across_python_launches():
    import subprocess
    import sys
    code = (
        "import numpy as np\n"
        "from gp_elite import symbolic_regression\n"
        "r = np.random.RandomState(9)\n"
        "X = r.uniform(-3, 3, (150, 2)); y = X[:, 0] * X[:, 1] ** 2 - 0.5 * X[:, 0]\n"
        "res = symbolic_regression(X, y, generations=6, speed='ultrafast',\n"
        "                          restarts=2, parallel=False, seed=5)\n"
        "print('EXPR', res.expression)\n")
    outs = []
    for hs in ("0", "1", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=hs)
        p = subprocess.run([sys.executable, "-c", code], env=env,
                           capture_output=True, text=True, timeout=600)
        assert p.returncode == 0, p.stderr[-2000:]
        outs.append([l for l in p.stdout.splitlines() if l.startswith("EXPR")][-1])
    assert outs[0] == outs[1] == outs[2]


def test_faithful_formula_preferred_among_equivalent_candidates(monkeypatch):
    """Among candidates the data cannot tell apart, the final choice prefers
    one whose printed formula reproduces the model (no safety net acting on
    the data) over a shorter one that relies on a protected division."""
    Xd = np.array([[1.0, 2.0], [2.0, 3.0], [3.0, 1.0], [4.0, 2.5]] * 10)
    y = Xd[:, 0] * 0.5
    net = N("/", X(0), N("-", X(1), N(2.0)))        # size 5, pole on the data
    plain = N("*", N(0.5), X(0))                    # size 3 ... make it larger
    plain = N("+", N("*", N(0.5), X(0)), N("*", N(0.0), X(1)))   # size 7
    monkeypatch.setattr(core, "_VAL_TRAIN_XS", Xd)
    monkeypatch.setattr(core, "_VAL_XS", None)
    monkeypatch.setattr(core, "_VAL_YS", y)
    monkeypatch.setattr(core, "_NEAR_PROBE_XS", None)
    core._FAITHFUL_CACHE.clear()
    monkeypatch.setattr(core, "_VAL_CANDS", [(1e-3, 0.0, 5, net),
                                             (1e-3, 0.0, 7, plain)])
    chosen = core._select_one_se(None, float("inf"))[0]
    assert chosen is plain
