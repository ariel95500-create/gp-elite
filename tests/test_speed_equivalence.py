"""The 0.8 speed work must not change a single result.

Each optimised routine is compared here, value for value and bit for bit, with
the 0.7.0 code it replaces (copied below as the reference). The whole engine
is also checked end to end by benchmarks/speed_check.py, which compares the
models returned by two versions at equal seed.
"""
import itertools
import warnings

import numpy as np
import pytest

from gp_elite import core

_SAFE_LIMIT = core._SAFE_LIMIT


# ---------------------------------------------------------------- references
# Verbatim from gp_elite 0.7.0 (gp_elite/core.py).

def _ref_safe_div(a, b):
    a = np.clip(a, -_SAFE_LIMIT, _SAFE_LIMIT)
    b_safe = np.where(np.abs(b) < 1e-8, 1.0, b)
    with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
        r = np.where(np.abs(b) < 1e-8, a, a / b_safe)
    return np.where(np.isfinite(r), r, 0.0)


def _ref_safe_pow(a, b):
    b = np.clip(b, -6.0, 6.0)
    a = np.clip(a, -100.0, 100.0)
    with np.errstate(all='ignore'):
        b_int = np.round(b)
        is_int = np.abs(b - b_int) < 1e-6
        r_int = np.sign(a) * np.power(np.abs(a) + 1e-12, np.abs(b_int))
        r_int = np.where(b_int >= 0, r_int, 1.0 / (np.abs(r_int) + 1e-12) * np.sign(r_int))
        r_real = np.power(np.abs(a) + 1e-12, b)
        r = np.where(is_int, r_int, r_real)
    return np.where(np.isfinite(r) & (np.abs(r) < _SAFE_LIMIT), r, 1.0)


def _ref_safe_pow_var(a, b):
    b = np.clip(b, -6.0, 6.0)
    a = np.clip(a, -100.0, 100.0)
    with np.errstate(all='ignore'):
        r = np.power(np.abs(a) + 1e-12, b)
    return np.where(np.isfinite(r) & (np.abs(r) < _SAFE_LIMIT), r, 1.0)


def _ref_safe_exp(a):
    with np.errstate(over='ignore', invalid='ignore'):
        r = np.exp(np.clip(a, -88.0, 88.0))
    return np.where(np.isfinite(r), r, 0.0)


# ------------------------------------------------------------------ helpers

_SPECIAL = [0.0, -0.0, 1e-9, -1e-9, 1e-8, -1e-8, 9.999999e-9, 1.0000001e-8,
            0.5, -0.5, 1.0, -1.0, 2.0, -2.0, 3.0000001, 2.9999995, 2.5, -2.5,
            6.0, -6.0, 7.5, -7.5, 99.0, 100.0, 101.0, -150.0, 1e6, -1e6, 1e7,
            -1e7, 1e300, -1e300, np.inf, -np.inf, np.nan, 5e-324]


def _same(x, y):
    """Bit-for-bit equality (signed zeros distinguished, NaN == NaN)."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.shape != y.shape:
        return False
    both_nan = np.isnan(x) & np.isnan(y)
    bits = x.view(np.uint64) == y.view(np.uint64)
    return bool(np.all(both_nan | bits))


def _operands(rng):
    """Scalars of every kind and arrays mixing ordinary and special values."""
    sp = np.array(_SPECIAL)
    arr = np.concatenate([sp, rng.normal(0, 3, 200), rng.normal(0, 1e4, 50),
                          rng.uniform(-1e-7, 1e-7, 50)])
    rng.shuffle(arr)
    out = [arr, arr[::3]]                                   # contiguous and strided
    out += [float(v) for v in sp[::4]]                     # Python floats
    out += [np.float64(v) for v in sp[1::5]]               # NumPy scalars
    out += [np.array(v) for v in sp[2::6]]                 # 0-d arrays
    return out


# -------------------------------------------------------------------- tests

@pytest.mark.parametrize("new, ref", [
    (core._np_safe_div, _ref_safe_div),
    (core._np_safe_pow_var, _ref_safe_pow_var),
])
def test_binary_protected_ops_bit_identical(new, ref):
    rng = np.random.RandomState(0)
    ops = _operands(rng)
    n = 0
    for a, b in itertools.product(ops, ops):
        if np.ndim(a) and np.ndim(b) and np.shape(a) != np.shape(b):
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            got = new(a, b)
        assert _same(got, ref(a, b)), (a, b)
        n += 1
    assert n > 300


def test_safe_pow_bit_identical():
    """_safe_pow receives constant exponents (scalar path) but must also keep
    the 0.7 values for array exponents."""
    rng = np.random.RandomState(1)
    ops = _operands(rng)
    exps = [float(v) for v in _SPECIAL] + [np.float64(v) for v in _SPECIAL]
    exps += [np.array(2.0), np.array(-3.0), np.array(np.nan), np.array(0.49999999)]
    exps += [x for x in ops if np.ndim(x)]                 # array exponents too
    n = 0
    for a in ops:
        for b in exps:
            if np.ndim(a) and np.ndim(b) and np.shape(a) != np.shape(b):
                continue
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                got = core._np_safe_pow(a, b)
            assert _same(got, _ref_safe_pow(a, b)), (a, b)
            n += 1
    assert n > 500


def test_safe_exp_bit_identical():
    rng = np.random.RandomState(2)
    for a in _operands(rng):
        assert _same(core._np_safe_exp(a), _ref_safe_exp(a)), a


def _make_selector(E):
    s = object.__new__(core.EpsilonLexicaseSelector)
    s.pop = [core.Node(float(i)) for i in range(E.shape[0])]
    s.E = E
    med = np.median(E, axis=0)
    s.eps = np.median(np.abs(E - med), axis=0)
    s.n_cases = E.shape[1]
    s._case_buf = np.arange(s.n_cases)
    s._ET = np.ascontiguousarray(E.T)
    return s


def test_block_lexicase_matches_case_by_case():
    """select() (blocks of cases) must return the same parent as the 0.7
    case-by-case filter, draw for draw, and consume the random stream the
    same way."""
    rng = np.random.RandomState(0)
    n_checked = 0
    for trial in range(120):
        P = int(rng.choice([1, 2, 3, 10, 60, 200]))
        C = int(rng.choice([1, 2, 7, 50, 140, 700]))
        kind = trial % 4
        if kind == 0:
            E = rng.rand(P, C)
        elif kind == 1:        # duplicated rows (linear-scaling equivalents)
            base = rng.rand(max(1, P // 5), C)
            E = base[rng.randint(0, base.shape[0], P)]
        elif kind == 2:        # near duplicates, within epsilon
            base = rng.rand(max(1, P // 5), C)
            E = base[rng.randint(0, base.shape[0], P)] + 1e-9 * rng.rand(P, C)
        else:                  # many ties and 1e9 sentinels
            E = rng.randint(0, 3, (P, C)).astype(float)
            E[rng.rand(P, C) < 0.05] = 1e9
        s = _make_selector(E)
        for k in range(8):
            seed = trial * 100 + k
            buf0 = s._case_buf.copy()
            np.random.seed(seed)
            a = s.select().value
            state_a = np.random.get_state()
            buf_a = s._case_buf.copy()
            s._case_buf[:] = buf0
            np.random.seed(seed)
            b = s._select_reference().value
            state_b = np.random.get_state()
            assert a == b
            assert np.array_equal(buf_a, s._case_buf)
            assert np.array_equal(state_a[1], state_b[1]) and state_a[2] == state_b[2]
            n_checked += 1
    assert n_checked == 960


def _toy_memories(rng):
    """A fragment library and a co-occurrence graph filled with random
    entries, as the search would leave them."""
    lib = core.FragmentLibrary()
    hashes = []
    for i in range(60):
        node = core.Node("+", core.Node("X[%d]" % (i % 3)), core.Node(float(i)))
        h = 1000 + i
        sig = rng.normal(size=5) if i % 4 else None
        lib.fragments[h] = core.FragmentEntry(
            node=node, tau=float(rng.uniform(0.01, 3.0)), freq=1,
            best_fitness=1.0, last_gen=0, size=int(rng.randint(2, 16)),
            depth=2, root_op=["+", "*", "sin"][i % 3], semantic_signature=sig)
        hashes.append(h)
    cog = core.FragmentCoGraph()
    for _ in range(400):
        a, b = rng.choice(hashes + [5, 6, 7], 2)    # 5, 6, 7: not in the library
        cog.co[cog._key(int(a), int(b))] = float(rng.uniform(0.001, 2.0))
    return lib, cog


def test_frozen_sampling_tables_draw_the_same():
    """Inside begin_sampling()/end_sampling() the library and the graph reuse
    precomputed tables; every draw must equal the draw of the 0.7 path."""
    import random as pyrandom
    rng = np.random.RandomState(3)
    lib, cog = _toy_memories(rng)
    old_sig = core.CURRENT_RESIDUAL_SIG
    try:
        for res_sig in (None, rng.normal(size=5)):
            core.CURRENT_RESIDUAL_SIG = res_sig
            roots = list(lib.fragments)[:12] + [5]
            calls = [("sample", (2, 15, None)), ("sample", (3, 8, "+")),
                     ("sample", (40, 50, None)), ("pair", ())]
            calls += [("comp", (h,)) for h in roots]

            def run(frozen):
                pyrandom.seed(11)
                if frozen:
                    lib.begin_sampling()
                    cog.begin_sampling(lib)
                out = []
                for _ in range(30):
                    for kind, args in calls:
                        if kind == "sample":
                            r = lib.sample(*args)
                            out.append(None if r is None else core.to_string(r))
                        elif kind == "pair":
                            a, b = cog.sample_pair(lib)
                            out.append((core.to_string(a), core.to_string(b)))
                        else:
                            r = cog.sample_companion(args[0], lib)
                            out.append(None if r is None else core.to_string(r))
                lib.end_sampling()
                cog.end_sampling()
                return out, pyrandom.random()

            assert run(False) == run(True)
    finally:
        core.CURRENT_RESIDUAL_SIG = old_sig


def test_memories_never_carry_a_sampling_table_across_processes():
    import pickle
    rng = np.random.RandomState(4)
    lib, cog = _toy_memories(rng)
    lib.begin_sampling()
    cog.begin_sampling(lib)
    old_sig = core.CURRENT_RESIDUAL_SIG
    core.CURRENT_RESIDUAL_SIG = None      # toy signatures have 5 probes
    try:
        lib.sample(2, 15)
        cog.sample_pair(lib)
    finally:
        core.CURRENT_RESIDUAL_SIG = old_sig
    lib2 = pickle.loads(pickle.dumps(lib))
    cog2 = pickle.loads(pickle.dumps(cog))
    assert lib2._sampling is None and cog2._sampling is None
    # any change to a memory closes the window
    lib.evaporate()
    cog.evaporate()
    assert lib._sampling is None and cog._sampling is None
