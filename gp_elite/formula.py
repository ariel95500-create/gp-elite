"""The delivered formula, written in the user's own variables.  [v0.7]

Why this module exists
----------------------
The engine searches on rescaled inputs. Every column goes through an affine
map ``x_s = a*x + b`` (division by max|x| by default; min-max, z-score or
identity on request), so the tree it evolves lives in *scaled* space.
Printing that tree with the raw column names gives a formula that is wrong on
raw data: up to 0.6.x, ``y = 3x`` came out as ``15.0*x``, and with min-max or
z-score scaling the exported formula was off by orders of magnitude, while
``predict()`` was right all along.

This module rewrites the tree in the raw variables, folds the rescaling
constants into the formula's own constants, and CHECKS the result: evaluated
on the raw training data, the delivered formula must reproduce ``predict()``.
The outcome of that check is reported (``exact``), never assumed.

Protected operators
-------------------
The engine evaluates ``sqrt(|u|)``, ``log(|u|)`` and a sign-aware power
(``core._np_safe_pow``: ``|u|^p`` for a non-integer ``p``, ``sign(u)*|u|^n``
for an integer ``n``). Where the argument is positive on every training row,
the plain mathematical form is printed (``sqrt(u)``, ``log(u)``, ``u^p``): on
the data domain it is the same function. Elsewhere the explicit form is
printed (``sqrt(|u|)``, ``sign(u)*|u|^2``...). Divisions are printed plainly:
the engine's protection only acts within 1e-8 of a pole.
"""
from __future__ import annotations

import math

import numpy as np

try:                                    # package
    from . import core
except ImportError:                     # loose modules next to each other
    import core

Node = core.Node

_UNARY = ("neg", "abs", "sq", "cube", "sqrt", "log", "exp", "sin", "cos",
          "tan", "tanh", "step", "is_even")
_BINARY = ("+", "-", "*", "/", "pow", "max2", "min2")


# ─────────────────────────────────────────────────────────────────────────────
# 1. The scaler as one affine map per column:  x_s = a*x + b
# ─────────────────────────────────────────────────────────────────────────────

def affine_maps(scaler, X_raw):
    """Return (a, b), arrays with ``scaler.transform(X)[:, i] == a[i]*X[:, i] + b[i]``.

    Known scalers are read from their attributes (exact constants); anything
    else is probed. Either way the map is then CHECKED against
    ``scaler.transform`` on the training data: a non-affine or misread scaler
    raises ValueError instead of producing a wrong formula.
    """
    X_raw = np.asarray(X_raw, dtype=float)
    n = X_raw.shape[1]
    if scaler is None:
        return np.ones(n), np.zeros(n)
    cls = type(scaler).__name__
    a = b = None
    if cls == "_IdentityScaler":
        a, b = np.ones(n), np.zeros(n)
    elif cls == "_ShiftFreeScaler":
        s = np.asarray(scaler.scale_, dtype=float)
        a, b = 1.0 / s, np.zeros(n)
    elif cls == "MinMaxScaler" and hasattr(scaler, "min_"):
        a = np.asarray(scaler.scale_, dtype=float)
        b = np.asarray(scaler.min_, dtype=float)
    elif cls == "StandardScaler":
        sd = getattr(scaler, "scale_", None)
        mu = getattr(scaler, "mean_", None)
        sd = np.ones(n) if sd is None else np.asarray(sd, dtype=float)
        mu = np.zeros(n) if mu is None else np.asarray(mu, dtype=float)
        a, b = 1.0 / sd, -mu / sd
    else:                                   # unknown scaler: probe it
        z = np.asarray(scaler.transform(np.zeros((1, n))), dtype=float)[0]
        o = np.asarray(scaler.transform(np.ones((1, n))), dtype=float)[0]
        a, b = o - z, z
    a = np.broadcast_to(np.asarray(a, dtype=float), (n,)).copy()
    b = np.broadcast_to(np.asarray(b, dtype=float), (n,)).copy()
    # the check that makes the rest trustworthy
    Xs = np.asarray(scaler.transform(X_raw), dtype=float)
    ref = np.max(np.abs(Xs)) if Xs.size else 1.0
    if Xs.shape != X_raw.shape or np.max(np.abs(Xs - (X_raw * a + b))) > 1e-9 * max(1.0, ref):
        raise ValueError("scaler %s is not a per-column affine map" % cls)
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b)) and np.all(a != 0)):
        raise ValueError("degenerate affine map for scaler %s" % cls)
    return a, b


# ─────────────────────────────────────────────────────────────────────────────
# 2. Substitution + exact folding of the scaling constants
# ─────────────────────────────────────────────────────────────────────────────
# Every subtree folds to a pair (c, t) meaning  value = c * t,  with t a Node
# or None (t is None <=> the subtree is the constant c). Each rule below is an
# identity of the ENGINE's operators (protected ones included), so folding
# never changes the function — only where its constants are written.

def _is_num(v):
    return isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool)


def _var_index(v):
    if v == "x":
        return 0
    if isinstance(v, str) and v.startswith("X[") and v.endswith("]"):
        return int(v[2:-1])
    raise ValueError("unknown leaf %r" % (v,))


def _same(t1, t2):
    """Structural equality (exact values)."""
    stack = [(t1, t2)]
    while stack:
        p, q = stack.pop()
        if p is None or q is None:
            if p is not q:
                return False
            continue
        if _is_num(p.value) and _is_num(q.value):
            if float(p.value) != float(q.value):
                return False
        elif p.value != q.value:
            return False
        stack.append((p.left, q.left))
        stack.append((p.right, q.right))
    return True


def _mat(c, t):
    """Materialise (c, t) as a tree."""
    c = float(c)
    if t is None:
        return Node(c)
    if c == 1.0:
        return t
    if c == -1.0:
        return Node("neg", t)
    if t.value == "/" and t.left is not None and _is_num(t.left.value) \
            and float(t.left.value) == 1.0:
        return Node("/", Node(c), t.right)           # c * (1/u)  ->  c / u
    if t.value in ("+", "-") and _all_terms_scaled(t):
        return _distribute(c, t)                     # c*(a*u + b*v) -> ca*u + cb*v
    if t.value == "*" and t.right is not None:       # c*((a*u + b*v)*w) -> (ca*u + cb*v)*w
        for f, other, left in ((t.left, t.right, True), (t.right, t.left, False)):
            if f.value in ("+", "-") and f.right is not None and _all_terms_scaled(f):
                d = _distribute(c, f)
                return Node("*", d, other) if left else Node("*", other, d)
    return Node("*", Node(c), t)


def _const_factor(nd):
    """k if nd is k, k*u, k/u or -(k*u)...; else None."""
    if nd.left is None and nd.right is None:
        return float(nd.value) if _is_num(nd.value) else None
    if nd.value in ("*", "/") and nd.left is not None and _is_num(nd.left.value) \
            and nd.left.left is None and nd.left.right is None:
        return float(nd.left.value)
    if nd.value == "neg" and nd.left is not None:
        k = _const_factor(nd.left)
        return None if k is None else -k
    return None


def _all_terms_scaled(t):
    """Every additive term of the sum t already carries a constant factor, so
    distributing a constant over it adds no constant and removes one."""
    if t.value in ("+", "-") and t.right is not None:
        return _all_terms_scaled(t.left) and _all_terms_scaled(t.right)
    return _const_factor(t) is not None


def _distribute(c, t):
    if t.value in ("+", "-") and t.right is not None:
        return Node(t.value, _distribute(c, t.left), _distribute(c, t.right))
    if t.left is None and t.right is None:           # constant
        return Node(c * float(t.value))
    if t.value == "neg":
        return _distribute(-c, t.left)
    k = float(t.left.value)                          # k*u or k/u
    kc = c * k
    if t.value == "*":
        return _mat(kc, t.right)
    return Node("/", Node(kc), t.right)


def _const_eval(op, *vals):
    """Value of op on constants, with the ENGINE's semantics (protections)."""
    arr = [np.array([float(v)]) for v in vals]
    with np.errstate(all="ignore"):
        if op == "+":    r = arr[0] + arr[1]
        elif op == "-":  r = arr[0] - arr[1]
        elif op == "*":  r = arr[0] * arr[1]
        elif op == "/":  r = core._np_safe_div(arr[0], arr[1])
        elif op == "pow": r = core._np_safe_pow(arr[0], arr[1])
        elif op == "max2": r = np.maximum(arr[0], arr[1])
        elif op == "min2": r = np.minimum(arr[0], arr[1])
        elif op == "neg": r = -arr[0]
        elif op == "abs": r = np.abs(arr[0])
        elif op == "sq":  r = arr[0] ** 2
        elif op == "cube": r = arr[0] ** 3
        elif op == "sqrt": r = core._np_safe_sqrt(arr[0])
        elif op == "log": r = core._np_safe_log(arr[0])
        elif op == "exp": r = core._np_safe_exp(arr[0])
        elif op == "sin": r = np.sin(arr[0])
        elif op == "cos": r = np.cos(arr[0])
        elif op == "tan": r = core._np_safe_tan(arr[0])
        elif op == "tanh": r = np.tanh(arr[0])
        elif op == "step": r = core._np_step(arr[0])
        elif op == "is_even": r = core._np_is_even(arr[0])
        else:
            raise ValueError("unknown operator %r" % (op,))
    return float(np.asarray(r, dtype=float).ravel()[0])


def _fold(node, a, b):
    v = node.value
    if node.left is None and node.right is None:
        if _is_num(v):
            return float(v), None
        i = _var_index(v)
        var = Node("X[%d]" % i)
        if b[i] == 0.0:
            return float(a[i]), var
        # a*x + b  =  a * (x - x0),  x0 = -b/a
        return float(a[i]), Node("-", var, Node(float(-b[i] / a[i])))

    if node.right is None:                                   # unary
        c, t = _fold(node.left, a, b)
        if t is None:
            return _const_eval(v, c), None
        if v == "neg":
            return -c, t
        if v == "abs":
            return abs(c), Node("abs", t)
        if v == "sq":
            return c * c, Node("sq", t)
        if v == "cube":
            return c * c * c, Node("cube", t)
        if v == "sqrt":                                      # sqrt|ct| = sqrt|c| sqrt|t|
            return math.sqrt(abs(c)), Node("sqrt", t)
        if v == "log":                                       # log|ct| = log|c| + log|t|
            if c == 0.0:
                return _const_eval("log", 0.0), None
            k = math.log(abs(c))
            if k == 0.0:
                return 1.0, Node("log", t)
            return 1.0, Node("+", Node("log", t), Node(k))
        if v == "step" and c != 0.0:                         # step(ct) = step(sign(c) t)
            return 1.0, Node("step", t if c > 0 else Node("neg", t))
        return 1.0, Node(v, _mat(c, t))                      # exp, tanh, sin, ...

    c1, t1 = _fold(node.left, a, b)                          # binary
    c2, t2 = _fold(node.right, a, b)
    if t1 is None and t2 is None:
        return _const_eval(v, c1, c2), None
    if v == "*":
        if t1 is None:
            return c1 * c2, t2
        if t2 is None:
            return c1 * c2, t1
        return c1 * c2, Node("*", t1, t2)
    if v == "/":
        if t2 is None:
            if abs(c2) < 1e-8:                               # engine: returns numerator
                return c1, t1
            return c1 / c2, t1
        if c2 == 0.0:                                        # denominator identically 0
            return c1, t1
        if t1 is None:
            return c1 / c2, Node("/", Node(1.0), t2)
        return c1 / c2, Node("/", t1, t2)
    if v in ("+", "-"):
        if t1 is not None and t2 is not None and _same(t1, t2):
            cc = c1 + c2 if v == "+" else c1 - c2
            return (cc, t1) if cc != 0.0 else (0.0, None)
        if t1 is not None and t2 is not None and c1 == c2:
            return c1, Node(v, t1, t2)
        return 1.0, Node(v, _mat(c1, t1), _mat(c2, t2))
    if v == "pow" and t2 is None:                            # constant exponent
        p = min(6.0, max(-6.0, c2))                          # engine clips it
        n = round(p)
        if abs(p - n) < 1e-6:                                # integer: sign-aware
            n = int(n)
            sgn = 1.0 if c1 > 0 else (-1.0 if c1 < 0 else 0.0)
            if sgn == 0.0:
                return 0.0, None
            return sgn * abs(c1) ** n, Node("pow", t1, Node(float(n)))
        return abs(c1) ** p, Node("pow", t1, Node(float(p)))
    if v in ("max2", "min2") and t1 is not None and t2 is not None \
            and c1 == c2 and c1 > 0:
        return c1, Node(v, t1, t2)
    return 1.0, Node(v, _mat(c1, t1), _mat(c2, t2))


def _flatten_sum(nd, sign, out):
    """Additive terms of a sum as (coefficient, core); core None = constant."""
    v = nd.value
    if v == "+" and nd.right is not None:
        _flatten_sum(nd.left, sign, out)
        _flatten_sum(nd.right, sign, out)
    elif v == "-" and nd.right is not None:
        _flatten_sum(nd.left, sign, out)
        _flatten_sum(nd.right, -sign, out)
    elif v == "neg":
        _flatten_sum(nd.left, -sign, out)
    elif nd.left is None and nd.right is None and _is_num(v):
        out.append((sign * float(v), None))
    elif v == "*" and nd.left is not None and nd.left.left is None \
            and nd.left.right is None and _is_num(nd.left.value):
        out.append((sign * float(nd.left.value), nd.right))
    else:
        out.append((sign * 1.0, nd))
    return out


def _tidy(nd):
    """Collect like terms in every sum: 0.32*v + u + 0.33*v -> 0.65*v + u.
    Exact algebra (only coefficients of structurally identical terms are
    added), so the function is unchanged; the fit-time check still applies."""
    if nd is None or (nd.left is None and nd.right is None):
        return nd
    if nd.value in ("+", "-") and nd.right is not None:
        groups = []                                  # [coef, core], first-seen order
        for coef, core in _flatten_sum(nd, 1.0, []):
            core = _tidy(core) if core is not None else None
            for g in groups:
                if (g[1] is None and core is None) or \
                        (g[1] is not None and core is not None and _same(g[1], core)):
                    g[0] += coef
                    break
            else:
                groups.append([coef, core])
        terms = [(c, t) for c, t in groups if c != 0.0]
        if not terms:
            return Node(0.0)
        acc = _mat(terms[0][0], terms[0][1])
        for c, t in terms[1:]:
            if c < 0:
                acc = Node("-", acc, _mat(-c, t))
            else:
                acc = Node("+", acc, _mat(c, t))
        return acc
    return Node(nd.value, _tidy(nd.left), _tidy(nd.right))


def to_raw_tree(node, a, b):
    """Scaled-space tree -> equivalent raw-space tree (engine operators)."""
    c, t = _fold(node, a, b)
    return _tidy(_mat(c, t))


def substitute_only(node, a, b):
    """Raw-space tree WITHOUT folding: each variable replaced by a*x + b.
    Fallback if folding ever failed; same function, less readable."""
    v = node.value
    if node.left is None and node.right is None:
        if _is_num(v):
            return Node(float(v))
        i = _var_index(v)
        x = Node("*", Node(float(a[i])), Node("X[%d]" % i))
        return x if b[i] == 0.0 else Node("+", x, Node(float(b[i])))
    return Node(v, substitute_only(node.left, a, b) if node.left is not None else None,
                substitute_only(node.right, a, b) if node.right is not None else None)


# ─────────────────────────────────────────────────────────────────────────────
# 3. What the printed formula computes, and where arguments are positive
# ─────────────────────────────────────────────────────────────────────────────

def _const_exponent(node):
    """The exponent of a pow node as a float if it is a constant, else None."""
    r = node.right
    if r is not None and r.left is None and r.right is None and _is_num(r.value):
        return float(r.value)
    return None


def evaluate(node, X, positive=None):
    """Evaluate a raw-space tree with the semantics of the PRINTED formula.

    That is the engine's semantics without its numerical safety nets (no
    clipping, no protected division), i.e. the mathematical function the text
    and sympy forms describe. If `positive` (a dict) is given, it is filled
    with id(node) -> True/False: is the argument of this sqrt/log/pow node
    strictly positive on every row of X?
    """
    X = np.asarray(X, dtype=float)
    n = X.shape[0]

    def ev(nd):
        v = nd.value
        if nd.left is None and nd.right is None:
            if _is_num(v):
                return np.full(n, float(v))
            return X[:, _var_index(v)].astype(float)
        if nd.right is None:
            u = ev(nd.left)
            if positive is not None and v in ("sqrt", "log"):
                positive[id(nd)] = bool(np.all(u > 0))
            with np.errstate(all="ignore"):
                if v == "neg":   return -u
                if v == "abs":   return np.abs(u)
                if v == "sq":    return u ** 2
                if v == "cube":  return u ** 3
                if v == "sqrt":  return np.sqrt(np.abs(u))
                if v == "log":   return np.log(np.abs(u))
                if v == "exp":   return np.exp(u)
                if v == "sin":   return np.sin(u)
                if v == "cos":   return np.cos(u)
                if v == "tan":   return np.tan(u)
                if v == "tanh":  return np.tanh(u)
                if v == "step":  return (u > 0).astype(float)
                if v == "is_even":
                    return core._np_is_even(u)
            raise ValueError("unknown unary operator %r" % (v,))
        u = ev(nd.left)
        w = ev(nd.right)
        with np.errstate(all="ignore"):
            if v == "+":   return u + w
            if v == "-":   return u - w
            if v == "*":   return u * w
            if v == "/":   return u / w
            if v == "max2": return np.maximum(u, w)
            if v == "min2": return np.minimum(u, w)
            if v == "pow":
                if positive is not None:
                    positive[id(nd)] = bool(np.all(u > 0))
                p = _const_exponent(nd)
                if p is None:
                    return np.abs(u) ** w
                k = round(p)
                if abs(p - k) < 1e-6:
                    k = int(k)
                    if k == 0:
                        return np.sign(u)
                    mag = np.abs(u) ** abs(k)
                    return np.sign(u) * (mag if k > 0 else 1.0 / mag)
                return np.abs(u) ** p
        raise ValueError("unknown binary operator %r" % (v,))

    return ev(node)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Printing: one tree, two renderings
# ─────────────────────────────────────────────────────────────────────────────

def _name(v, names):
    i = _var_index(v)
    if names and i < len(names):
        return str(names[i])
    return "X%d" % i


def _neg_const(nd):
    return nd.left is None and nd.right is None and _is_num(nd.value) \
        and float(nd.value) < 0


def _atomic(nd):
    return nd.left is None and nd.right is None and not _neg_const(nd)


def to_sympy_string(node, names=None, positive=None):
    """Exact, sympy-parsable string (full float precision, no ²/³)."""
    positive = positive or {}

    def f(nd):
        v = nd.value
        if nd.left is None and nd.right is None:
            if _is_num(v):
                s = repr(float(v))
                return "(%s)" % s if float(v) < 0 else s
            return _name(v, names)
        if nd.right is None:
            A = f(nd.left)
            pos = positive.get(id(nd), False)
            if v == "neg":   return "(-(%s))" % A
            if v == "abs":   return "Abs(%s)" % A
            if v == "sq":    return "((%s)**2)" % A
            if v == "cube":  return "((%s)**3)" % A
            if v == "sqrt":  return "sqrt(%s)" % A if pos else "sqrt(Abs(%s))" % A
            if v == "log":   return "log(%s)" % A if pos else "log(Abs(%s))" % A
            if v in ("exp", "sin", "cos", "tan", "tanh"):
                return "%s(%s)" % (v, A)
            if v == "step":  return "Heaviside(%s, 0)" % A
            if v == "is_even":
                return "(1 - 2*Mod(floor(Abs(%s) + 1/2), 2))" % A
            raise ValueError("unmapped unary operator %r" % (v,))
        A, B = f(nd.left), f(nd.right)
        if v == "+":   return "(%s + %s)" % (A, B)
        if v == "-":   return "(%s - %s)" % (A, B)
        if v == "*":   return "(%s*%s)" % (A, B)
        if v == "/":   return "(%s/%s)" % (A, B)
        if v == "max2": return "Max(%s, %s)" % (A, B)
        if v == "min2": return "Min(%s, %s)" % (A, B)
        if v == "pow":
            pos = positive.get(id(nd), False)
            p = _const_exponent(nd)
            if p is None:
                return "((%s)**(%s))" % (A, B) if pos else "(Abs(%s)**(%s))" % (A, B)
            if pos:
                return "((%s)**%s)" % (A, B)
            k = round(p)
            if abs(p - k) < 1e-6:
                k = int(k)
                if k == 0:
                    return "sign(%s)" % A
                if k % 2:                                    # odd: sign(u)|u|^k = u^k
                    return "((%s)**(%d))" % (A, k)
                return "(sign(%s)*Abs(%s)**(%d))" % (A, A, k)
            return "(Abs(%s)**%s)" % (A, B)
        raise ValueError("unmapped binary operator %r" % (v,))

    return f(node)


def _num_text(c):
    c = float(c)
    if c == int(c) and abs(c) < 1e6:
        return "%d" % int(c)
    return "%.6g" % c


# Precedence levels of the text form: parentheses only where the reading
# would otherwise change.  1: + -   2: * /   3: unary minus   4: ^ ² ³   5: atom
_ATOM, _POW, _UMINUS, _MUL, _ADD = 5, 4, 3, 2, 1


def to_text(node, names=None, positive=None, _parsable=False):
    """Human-readable form: 6 significant digits, minimal parentheses,
    ² ³ ^, and |u| where the engine's protection matters on the data.

    `_parsable=True` emits the SAME layout (same parentheses) with Python
    operators (** and Abs) and full-precision constants: used by the tests to
    check that the minimal parenthesisation never changes the meaning."""
    positive = positive or {}
    if _parsable:
        SQ, CU, POW = "**2", "**3", "**"
        ABS = "Abs(%s)"
        num = lambda c: repr(float(c))
    else:
        SQ, CU, POW = "²", "³", "^"
        ABS = "|%s|"
        num = _num_text

    def par(sp, level):
        s, p = sp
        return "(%s)" % s if p < level else s

    def f(nd):
        v = nd.value
        if nd.left is None and nd.right is None:
            if _is_num(v):
                s = num(v)
                return (s, _UMINUS) if s.startswith("-") else (s, _ATOM)
            return _name(v, names), _ATOM
        if nd.right is None:
            A = f(nd.left)
            pos = positive.get(id(nd), False)
            if v == "neg":
                s = "(%s)" % A[0] if (A[1] < _MUL or A[0].startswith("-")) \
                    else A[0]
                return "-" + s, _UMINUS
            if v == "abs":
                return ABS % A[0], _ATOM
            if v == "sq":
                return par(A, _ATOM) + SQ, _POW
            if v == "cube":
                return par(A, _ATOM) + CU, _POW
            if v in ("sqrt", "log"):
                return ("%s(%s)" % (v, A[0]) if pos
                        else "%s(%s)" % (v, ABS % A[0])), _ATOM
            return "%s(%s)" % (v, A[0]), _ATOM               # exp, sin, step...
        A, B = f(nd.left), f(nd.right)
        if v in ("+", "-"):
            # a + -b -> a - b ; also a + -2 * x -> a - 2 * x (the leading
            # minus of a product or quotient belongs to the whole term)
            if B[1] >= _MUL and B[0].startswith("-"):
                op = "-" if v == "+" else "+"
                return "%s %s %s" % (A[0], op, B[0][1:]), _ADD
            rhs = par(B, _MUL) if v == "-" else B[0]
            return "%s %s %s" % (A[0], v, rhs), _ADD
        if v == "*" and not _parsable and nd.left.left is None \
                and nd.left.right is None and _is_num(nd.left.value) \
                and num(nd.left.value) in ("1", "-1"):
            # a factor that prints as 1 (e.g. 1.0000000002) is noise at the
            # displayed precision: "x * y", not "1 * x * y"
            if num(nd.left.value) == "1":
                return B
            s = "(%s)" % B[0] if (B[1] < _MUL or B[0].startswith("-")) else B[0]
            return "-" + s, _UMINUS
        if v in ("*", "/"):
            lhs = par(A, _MUL)
            # right operand: a sum always needs (); a product only under "/"
            # (a / (b*c)); a leading minus reads badly after an operator
            wrap_r = B[1] < _MUL or B[1] == _UMINUS or (v == "/" and B[1] == _MUL)
            rhs = "(%s)" % B[0] if wrap_r else B[0]
            return "%s %s %s" % (lhs, v, rhs), _MUL
        if v == "max2":
            return "max(%s, %s)" % (A[0], B[0]), _ATOM
        if v == "min2":
            return "min(%s, %s)" % (A[0], B[0]), _ATOM
        if v == "pow":
            pos = positive.get(id(nd), False)
            p = _const_exponent(nd)
            e = par(B, _ATOM)
            if pos:
                return "%s%s%s" % (par(A, _ATOM), POW, e), _POW
            if p is not None:
                k = round(p)
                if abs(p - k) < 1e-6:
                    k = int(k)
                    if k == 0:
                        return "sign(%s)" % A[0], _ATOM
                    if k % 2:
                        return "%s%s%s" % (par(A, _ATOM), POW, e), _POW
                    return "sign(%s) * %s%s%s" % (A[0], ABS % A[0], POW, e), _MUL
            return "%s%s%s" % (ABS % A[0], POW, e), _POW
        return "%s(%s, %s)" % (v, A[0], B[0]), _ATOM

    return f(node)[0]


def _balanced_outer(s):
    """True if the outer parentheses of s enclose the whole string."""
    depth = 0
    for i, ch in enumerate(s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and i != len(s) - 1:
                return False
    return depth == 0


# ─────────────────────────────────────────────────────────────────────────────
# 5. Putting it together
# ─────────────────────────────────────────────────────────────────────────────

class RawFormula:
    """A fitted model's formula in the raw input variables.

    Attributes
    ----------
    tree       : raw-space expression tree
    exact      : True if, on the raw training data, the formula reproduces
                 ``predict()`` (max deviation below 1e-7 of the prediction
                 scale). False means the model relies on a numerical safety
                 net of the engine somewhere on the data (a clipped power, a
                 protected division near a pole...): the formula is then the
                 mathematical function without that safety net.
    max_error  : largest |formula - predict| on the training data
    folded     : False if the readable folding failed and the plain
                 substitution (x -> a*x + b) was used instead
    """

    def __init__(self, tree, names, positive, exact, max_error, folded=True):
        self.tree = tree
        self.names = list(names) if names is not None else None
        self._positive = positive
        self.exact = bool(exact)
        self.max_error = float(max_error)
        self.folded = bool(folded)

    def text(self, names=None):
        return to_text(self.tree, names if names is not None else self.names,
                       self._positive)

    def sympy(self, names=None):
        return to_sympy_string(self.tree, names if names is not None else self.names,
                               self._positive)

    def __repr__(self):
        return "RawFormula(%r, exact=%s)" % (self.text(), self.exact)


def raw_formula(node, scaler, X_raw, feature_names=None, predictions=None):
    """Build and CHECK the raw-variable formula of a scaled-space model.

    node        : the model's tree (scaled space, as the engine evolved it)
    scaler      : the fitted input scaler (None = no scaling)
    X_raw       : the raw training inputs
    predictions : predict(X_raw) if already computed (else computed here)
    """
    X_raw = np.asarray(X_raw, dtype=float)
    if X_raw.ndim == 1:
        X_raw = X_raw.reshape(-1, 1)
    if predictions is None:
        Xs = X_raw if scaler is None else scaler.transform(X_raw)
        predictions = core.evaluate_vector(node, Xs)
    p = np.asarray(predictions, dtype=float)
    a, b = affine_maps(scaler, X_raw)

    def _check(tree):
        pos = {}
        v = evaluate(tree, X_raw, pos)
        scale = max(float(np.max(np.abs(p))) if p.size else 0.0,
                    float(np.std(p)) if p.size else 0.0, 1e-300)
        if not np.all(np.isfinite(v)):
            return pos, False, float("inf")
        err = float(np.max(np.abs(v - p))) if p.size else 0.0
        return pos, err <= 1e-7 * scale, err

    folded = True
    try:
        tree = to_raw_tree(node, a, b)
        pos, ok, err = _check(tree)
        if not ok:                                   # folding must never cost
            alt = substitute_only(node, a, b)        # exactness: compare with
            pos2, ok2, err2 = _check(alt)            # the plain substitution
            if ok2:
                tree, pos, ok, err, folded = alt, pos2, ok2, err2, False
    except (ValueError, RecursionError, OverflowError, ZeroDivisionError):
        tree = substitute_only(node, a, b)
        pos, ok, err = _check(tree)
        folded = False
    return RawFormula(tree, feature_names, pos, ok, err, folded)


def scaled_expression_note(scaler, X_raw, feature_names):
    """Last-resort legend when no raw formula can be built: how each name in
    the (scaled-space) expression relates to the raw column."""
    try:
        a, b = affine_maps(scaler, X_raw)
    except Exception:
        return "variables are internally rescaled"
    parts = []
    for i, nm in enumerate(feature_names):
        if b[i] == 0.0:
            parts.append("%s := %s/%s" % (nm, nm, _num_text(1.0 / a[i])))
        else:
            parts.append("%s := %s*%s %+g" % (nm, _num_text(a[i]), nm, b[i]))
    return "; ".join(parts)
