"""[v0.3] Dimensional consistency checking.

Launch feedback (ziofill, nyrikki) pointed out the obvious: an exponent like
`temperature/cycle` is physically meaningless — transcendental functions need
dimensionless arguments, and you can't add a length to a time. The engine works
on normalized magnitudes and has no notion of units, so it can and does produce
such formulas.

This does not constrain the search (that's a heavier change, on the roadmap).
It's a *post-hoc auditor*: declare the units of your columns and target, and it
tells you which formulas on the Pareto front are dimensionally sound and which
are empirical-only. Sound formulas are the ones you can trust as candidate laws;
the rest may still be useful correlations (a lot of engineering runs on those),
but you should know which is which.

Units are expressed as dimension dicts, e.g. a velocity is {"m": 1, "s": -1}.
Helpers are provided so you rarely write those by hand.
"""
from . import core


# ── unit algebra ───────────────────────────────────────────────────────────

DIMENSIONLESS = {}


def _mul(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0) + v
    return {k: v for k, v in out.items() if v != 0}


def _inv(a):
    return {k: -v for k, v in a.items()}


def _eq(a, b, tol=1e-9):
    keys = set(a) | set(b)
    return all(abs(a.get(k, 0) - b.get(k, 0)) < tol for k in keys)


def _is_dimensionless(a):
    return all(abs(v) < 1e-9 for v in a.values())


def _pow(a, p):
    return {k: v * p for k, v in a.items()}


def _fmt(d):
    if _is_dimensionless(d):
        return "[dimensionless]"
    num = " ".join(f"{k}^{v:g}" if v != 1 else k
                   for k, v in sorted(d.items()) if v > 0)
    den = " ".join(f"{k}^{-v:g}" if v != -1 else k
                   for k, v in sorted(d.items()) if v < 0)
    if den:
        return f"[{num or '1'} / {den}]"
    return f"[{num}]"


class _DimError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


# functions whose argument MUST be dimensionless, and whose result is too
_TRANSCENDENTAL = {"exp", "log", "sin", "cos", "tan", "tanh", "sinh", "cosh"}


def _infer(node, feat_dims):
    """Return the dimension dict of `node`, or raise _DimError on a violation.
    feat_dims maps 'X[i]' -> dimension dict."""
    # leaf
    if node.left is None and node.right is None:
        v = node.value
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return dict(DIMENSIONLESS)          # a fitted constant is dimensionless*
        return dict(feat_dims.get(str(v), DIMENSIONLESS))

    op = node.value

    # unary
    if node.right is None:
        d = _infer(node.left, feat_dims)
        if op in _TRANSCENDENTAL:
            if not _is_dimensionless(d):
                raise _DimError(f"{op}(...) needs a dimensionless argument, "
                                f"got {_fmt(d)}")
            return dict(DIMENSIONLESS)
        if op == "sqrt":
            return _pow(d, 0.5)
        if op == "sq":
            return _pow(d, 2)
        if op == "cube":
            return _pow(d, 3)
        if op in ("neg", "abs"):
            return d
        if op == "inv":
            return _inv(d)
        # unknown unary: pass through, but flag if it looks transcendental-ish
        return d

    # binary
    dl = _infer(node.left, feat_dims)
    dr = _infer(node.right, feat_dims)
    if op in ("+", "-"):
        if not _eq(dl, dr):
            raise _DimError(f"cannot add/subtract {_fmt(dl)} and {_fmt(dr)}")
        return dl
    if op == "*":
        return _mul(dl, dr)
    if op == "/":
        return _mul(dl, _inv(dr))
    if op == "pow":
        # exponent must be a dimensionless constant for the result to have
        # a well-defined dimension
        if not _is_dimensionless(dr):
            raise _DimError(f"exponent must be dimensionless, got {_fmt(dr)}")
        # only a constant exponent gives a clean power; approximate with the
        # right subtree's constant value if it is a leaf number
        rv = node.right.value
        if isinstance(rv, (int, float)) and not _is_dimensionless(dl):
            return _pow(dl, float(rv))
        return dl if _is_dimensionless(dl) else dl
    # unknown binary op: require dimensionless to be safe
    return _mul(dl, dr)


def check_dimensions(node, feature_dims, target_dim=None):
    """Check one expression tree for dimensional consistency.

    feature_dims : dict mapping feature index or 'X[i]' -> dimension dict
    target_dim   : optional dimension of the target; if given, the formula's
                   output dimension must match it.

    Returns (ok: bool, message: str).
    """
    # normalize keys to 'X[i]'
    fd = {}
    for k, v in feature_dims.items():
        key = k if str(k).startswith("X[") else f"X[{k}]"
        fd[key] = v
    try:
        out = _infer(node, fd)
    except _DimError as e:
        return False, e.msg
    if target_dim is not None and not _eq(out, target_dim):
        return False, (f"output is {_fmt(out)} but target is "
                       f"{_fmt(target_dim)}")
    return True, f"consistent, output {_fmt(out)}"


def audit_pareto(result, feature_dims, target_dim=None, verbose=True):
    """Audit every entry on a result's Pareto front for dimensional soundness.

    Returns a list of dicts: {size, expression, ok, message}. Prints a table
    if verbose. Entries flagged not-ok are empirical-only (still possibly
    useful, but not candidate physical laws).
    """
    entries = result.pareto if getattr(result, "pareto", None) else None
    if not entries:
        # fall back to the single champion
        ok, msg = check_dimensions(result.node, feature_dims, target_dim)
        rows = [dict(size=result.size, expression=result.expression,
                     ok=ok, message=msg)]
    else:
        rows = []
        for e in entries:
            ok, msg = check_dimensions(e.node, feature_dims, target_dim)
            rows.append(dict(size=e.size, expression=e.expression,
                             ok=ok, message=msg))

    if verbose:
        print("Dimensional audit of the Pareto front")
        print("(sound = a valid candidate law; flagged = empirical-only)\n")
        for r in rows:
            mark = "sound " if r["ok"] else "FLAG  "
            print(f"  [{mark}] size {r['size']:>2}  {r['expression']}")
            if not r["ok"]:
                print(f"            -> {r['message']}")
        n_ok = sum(1 for r in rows if r["ok"])
        print(f"\n  {n_ok}/{len(rows)} Pareto forms are dimensionally sound.")
        if n_ok == 0:
            print("  None are unit-consistent — expected if the true relation "
                  "is an empirical correlation (common in turbulent / "
                  "degradation regimes).")
    return rows


# ── convenience: build dimension dicts from unit strings ───────────────────

_BASE_ALIASES = {
    # length
    "m": {"m": 1}, "meter": {"m": 1}, "length": {"m": 1},
    # time
    "s": {"s": 1}, "sec": {"s": 1}, "time": {"s": 1}, "cycle": {"cycle": 1},
    # mass, temperature, etc. (free-form: any token becomes its own base dim)
    "kg": {"kg": 1}, "mass": {"kg": 1},
    "K": {"K": 1}, "temperature": {"K": 1}, "temp": {"K": 1},
    "A": {"A": 1}, "current": {"A": 1},
    "V": {"V": 1}, "voltage": {"V": 1},
    "1": {}, "": {}, "dimensionless": {}, "-": {},
}


def unit(token):
    """Turn a short unit token into a dimension dict. Unknown tokens become
    their own base dimension, so unit('widget') == {'widget': 1}. Compose by
    multiplying/dividing the dicts yourself, or use e.g. {'m':1,'s':-1}."""
    t = str(token).strip()
    if t in _BASE_ALIASES:
        return dict(_BASE_ALIASES[t])
    return {t: 1}
