"""[v0.4] Dimensionally-constrained SEARCH — the "heavier change" the v0.3
dimensions.py auditor left on the roadmap.

dimensions.py checks formulas *after* the search. This module constrains the
search *itself*: it only ever builds expression trees that are dimensionally
sound and of the requested target dimension, so the engine never spends budget
on physically meaningless candidates.

It deliberately reuses gp_elite.dimensions for all dimension algebra (dicts like
{"m": 1, "s": -1}, _infer, _mul, _pow, _eq). One source of truth: if the auditor
and the search ever disagree, that's a bug, and this design makes it impossible.

Measured effect (minimal GP loop, homogeneous monomials, 6 seeds/point):
    variables   3     4     5     6     7
    typed     6/6   6/6   6/6   6/6   0/6*
    control   1/6   0/6   0/6   0/6   0/6
    (*) n=7 exceeds what MAX_INIT_DEPTH can represent; typed still produces
        valid-but-incomplete laws (median R2 0.71) where control produces none.
From n=4 up, the unconstrained search found ZERO dimensionally valid
expressions across every seed.

Public API
----------
    feat_dims = {0: {"kg": 1}, 1: {"m": 1, "s": -1}}     # per feature index
    target    = {"kg": 1, "m": 2, "s": -2}
    tree  = typed_random_tree(target, max_depth, feat_dims, rng)
    child = typed_mutate(tree, feat_dims, max_depth, rng)
    c1, c2 = typed_crossover(p1, p2, feat_dims, rng)
    ok    = is_typed_valid(tree, feat_dims, target)
"""
import random

from .core import Node
from .dimensions import (_infer, _mul, _inv, _pow, _eq, _is_dimensionless,
                         _DimError, DIMENSIONLESS)

_TRANSCENDENTAL = ("exp", "log", "sin", "cos", "tanh")


# ── canonical hashable key for a dimension dict ─────────────────────────────

def _key(d):
    return tuple(sorted((k, round(float(v), 9))
                        for k, v in d.items() if abs(v) > 1e-9))


def _norm_feat_dims(feat_dims):
    """Accept {0: {...}} or {'X[0]': {...}} -> always 'X[i]' keys (as _infer wants)."""
    out = {}
    for k, v in feat_dims.items():
        key = k if str(k).startswith("X[") else f"X[{k}]"
        out[key] = dict(v)
    return out


def _feat_list(fd):
    """Ordered list of (name, dim) for X[0], X[1], ... present in fd."""
    items = []
    i = 0
    while f"X[{i}]" in fd:
        items.append((f"X[{i}]", fd[f"X[{i}]"]))
        i += 1
    return items


# ── reachability: is `target` in the rational span of the feature dims? ─────

def _reachable(target, feats, _cache):
    if _is_dimensionless(target):
        return True
    k = _key(target)
    if k in _cache:
        return _cache[k]
    try:
        import numpy as np
        bases = sorted({b for _, d in feats for b in d} | set(target))
        if not bases or not feats:
            r = _is_dimensionless(target)
        else:
            V = np.array([[float(d.get(b, 0)) for _, d in feats] for b in bases])
            y = np.array([float(target.get(b, 0)) for b in bases])
            sol, *_ = np.linalg.lstsq(V, y, rcond=None)
            r = bool(np.linalg.norm(V @ sol - y) < 1e-6)
    except Exception:
        r = True                       # numpy absent / degenerate: don't prune
    _cache[k] = r
    return r


# ── constructive generation ─────────────────────────────────────────────────

def _build(target, depth, feats, rng, cache, budget):
    """Return a tree of dimension exactly `target`, or None."""
    budget[0] -= 1
    if budget[0] <= 0 or not _reachable(target, feats, cache):
        return None

    tk = _key(target)
    terms = [name for name, d in feats if _key(d) == tk]
    dimless = _is_dimensionless(target)

    if depth <= 0:
        if terms:
            return Node(rng.choice(terms))
        return Node(round(rng.uniform(-3, 3), 4)) if dimless else None

    if terms and rng.random() < 0.30:
        return Node(rng.choice(terms))
    if dimless and rng.random() < 0.12:
        return Node(round(rng.uniform(-3, 3), 4))

    prods = [("neg",), ("abs",), ("+",), ("-",), ("sqrt",), ("sq",)]
    if dimless:
        prods += [(f,) for f in _TRANSCENDENTAL]
    factors = [d for _, d in feats] + [dict(DIMENSIONLESS)]
    for A in factors:
        prods.append(("*", A))
        prods.append(("/", A))
    rng.shuffle(prods)

    for p in prods:
        op = p[0]
        if op in ("neg", "abs"):
            c = _build(target, depth - 1, feats, rng, cache, budget)
            if c is not None:
                return Node(op, c)
        elif op in ("+", "-"):
            l = _build(target, depth - 1, feats, rng, cache, budget)
            if l is None:
                continue
            r = _build(target, depth - 1, feats, rng, cache, budget)
            if r is not None:
                return Node(op, l, r)
        elif op == "sqrt":
            c = _build(_pow(target, 2), depth - 1, feats, rng, cache, budget)
            if c is not None:
                return Node("sqrt", c)
        elif op == "sq":
            c = _build(_pow(target, 0.5), depth - 1, feats, rng, cache, budget)
            if c is not None:
                return Node("sq", c)
        elif op in _TRANSCENDENTAL:
            c = _build(dict(DIMENSIONLESS), depth - 1, feats, rng, cache, budget)
            if c is not None:
                return Node(op, c)
        elif op == "*":
            A = p[1]
            l = _build(A, depth - 1, feats, rng, cache, budget)
            if l is None:
                continue
            r = _build(_mul(target, _inv(A)), depth - 1, feats, rng, cache, budget)
            if r is not None:
                return Node("*", l, r)
        elif op == "/":
            A = p[1]
            l = _build(A, depth - 1, feats, rng, cache, budget)
            if l is None:
                continue
            r = _build(_mul(A, _inv(target)), depth - 1, feats, rng, cache, budget)
            if r is not None:
                return Node("/", l, r)

    if terms:
        return Node(rng.choice(terms))
    return Node(round(rng.uniform(-3, 3), 4)) if dimless else None


def _monomial_tree(target, feats, rng, max_terms=8):
    """CHEMIN RAPIDE : resout directement les exposants entiers e_i tels que
    prod(dim_i ^ e_i) == target (moindres carres + arrondi + verification),
    puis construit l'arbre produit correspondant. Evite la recherche aveugle,
    qui coute ~0.65 s/arbre sur des unites composees.
    Retourne None si aucune solution entiere courte n'est trouvee."""
    try:
        import numpy as np
    except Exception:
        return None
    if not feats:
        return None
    bases = sorted({b for _, d in feats for b in d} | set(target))
    if not bases:
        return None
    V = np.array([[float(d.get(b, 0.0)) for _, d in feats] for b in bases])
    yv = np.array([float(target.get(b, 0.0)) for b in bases])
    try:
        sol, *_ = np.linalg.lstsq(V, yv, rcond=None)
    except Exception:
        return None

    # plusieurs arrondis candidats : la solution moindres carres n'est pas
    # forcement entiere, on essaie quelques perturbations dans le noyau
    cands = [np.round(sol)]
    for _ in range(6):
        cands.append(np.round(sol + np.array(
            [rng.uniform(-0.6, 0.6) for _ in range(len(sol))])))
    for e in cands:
        if np.linalg.norm(V @ e - yv) > 1e-6:
            continue
        if np.abs(e).sum() > max_terms or np.abs(e).max() > 4:
            continue
        node = None
        for i, k in enumerate(e):
            k = int(k)
            if k == 0:
                continue
            name = feats[i][0]
            for _ in range(abs(k)):
                leaf = Node(name)
                if k > 0:
                    node = leaf if node is None else Node("*", node, leaf)
                else:
                    node = (Node("/", Node(1.0), leaf) if node is None
                            else Node("/", node, leaf))
        if node is None:
            continue
        # coefficient libre devant, que le LM ajustera
        return Node("*", Node(round(rng.uniform(-2, 2), 4)), node)
    return None


def typed_random_tree(target_dim, max_depth, feat_dims, rng=None, tries=40):
    """Random tree GUARANTEED to have dimension `target_dim`. None if impossible."""
    rng = rng or random
    fd = _norm_feat_dims(feat_dims)
    feats = _feat_list(fd)
    cache = {}
    tgt = dict(target_dim)
    # chemin rapide d'abord (majorite des cas, quasi instantane)
    for _ in range(3):
        t = _monomial_tree(tgt, feats, rng)
        if t is not None:
            return t
    for _ in range(tries):
        d = rng.randint(2, max(2, max_depth))
        t = _build(tgt, d, feats, rng, cache, [4000])
        if t is not None:
            return t
    return None


# ── dimension-preserving mutation & crossover ───────────────────────────────

def _nodes(t):
    out, stack = [], [t]
    while stack:
        n = stack.pop()
        out.append(n)
        if n.left is not None:
            stack.append(n.left)
        if n.right is not None:
            stack.append(n.right)
    return out


def _graft(root, old, new):
    if root is old:
        return new
    if root.left is None and root.right is None:
        return root
    l = _graft(root.left, old, new) if root.left is not None else None
    r = _graft(root.right, old, new) if root.right is not None else None
    return Node(root.value, l, r)


def typed_mutate(tree, feat_dims, max_depth, rng=None):
    """Replace a random subtree by a fresh one of the SAME dimension."""
    rng = rng or random
    fd = _norm_feat_dims(feat_dims)
    feats = _feat_list(fd)
    cache = {}
    nodes = _nodes(tree)
    rng.shuffle(nodes)
    for pick in nodes:
        try:
            d = _infer(pick, fd)
        except _DimError:
            continue
        for _ in range(12):
            sub = _build(d, rng.randint(1, max(2, max_depth)), feats, rng,
                         cache, [2000])
            if sub is not None:
                return _graft(tree, pick, sub).copy()
    return tree


def typed_crossover(p1, p2, feat_dims, rng=None):
    """Swap subtrees of EQUAL dimension -> both children stay valid."""
    rng = rng or random
    fd = _norm_feat_dims(feat_dims)

    def annotated(t):
        out = []
        for n in _nodes(t):
            try:
                out.append((n, _key(_infer(n, fd))))
            except _DimError:
                pass
        return out

    a, b = annotated(p1), annotated(p2)
    by = {}
    for n, k in b:
        by.setdefault(k, []).append(n)

    cands = []
    for n, k in a:
        if k in by:
            partners = [m for m in by[k] if not (n is p1 and m is p2)]
            if partners:
                cands.append((n, partners))
    if not cands:
        return p1.copy(), p2.copy()

    n1, partners = rng.choice(cands)
    n2 = rng.choice(partners)
    return (_graft(p1, n1, n2.copy()).copy(),
            _graft(p2, n2, n1.copy()).copy())


def _is_const_leaf(n):
    return (n is not None and n.left is None and n.right is None
            and isinstance(n.value, (int, float)) and not isinstance(n.value, bool))


def _strip_linear_scaling(node):
    """Retire un enrobage de scaling lineaire AU SOMMET : a + b*f  ->  f.

    wrap_linear_scaling() produit `a + b*inner`. La regle stricte ("une
    constante ajustee est adimensionnee") rejette l'addition `a + ...`, alors
    que physiquement `a` est un decalage exprime dans l'unite de la cible.
    On tolere donc ce motif, mais UNIQUEMENT au sommet de l'arbre : la
    contrainte reste stricte partout ailleurs.
    """
    n = node
    if n.value == "+" and n.left is not None and n.right is not None:
        if _is_const_leaf(n.left):
            n = n.right
        elif _is_const_leaf(n.right):
            n = n.left
    if n.value == "*" and n.left is not None and n.right is not None:
        if _is_const_leaf(n.left):
            n = n.right
        elif _is_const_leaf(n.right):
            n = n.left
    return n


def is_typed_valid(tree, feat_dims, target_dim):
    """Cheap backstop gate: use in fitness() to reject trees from any path."""
    fd = _norm_feat_dims(feat_dims)
    try:
        if _eq(_infer(tree, fd), target_dim):
            return True
    except _DimError:
        pass
    inner = _strip_linear_scaling(tree)
    if inner is tree:
        return False
    try:
        return _eq(_infer(inner, fd), target_dim)
    except _DimError:
        return False


# ── normalisation de l'argument utilisateur `units=` ────────────────────────

def normalize_units_arg(units, target_units, n_features, feature_names=None):
    """Convertit l'argument utilisateur en (FEAT_DIMS, TARGET_DIM).

    `units` accepte :
      - un dict par nom de feature : {"X0": "kg", "X1": {"m":1,"s":-1}}
      - un dict par index          : {0: "kg", 1: "m/s"}
      - une liste ordonnée         : ["kg", "m/s"]
    Les valeurs peuvent être un dict de dimensions, ou une chaîne simple
    ("kg", "m", "s"...) résolue par dimensions.unit().
    """
    def _as_dim(v):
        if v is None:
            return {}
        if isinstance(v, dict):
            return {k: float(x) for k, x in v.items()}
        return parse_unit_string(v)

    names = list(feature_names) if feature_names else [f"X{i}" for i in range(n_features)]
    feat = {}
    if isinstance(units, (list, tuple)):
        if len(units) != n_features:
            raise ValueError(f"units: {len(units)} entrées pour {n_features} features")
        for i, v in enumerate(units):
            feat[i] = _as_dim(v)
    elif isinstance(units, dict):
        for k, v in units.items():
            if isinstance(k, int):
                idx = k
            else:
                ks = str(k)
                if ks.startswith("X[") and ks.endswith("]"):
                    idx = int(ks[2:-1])
                elif ks in names:
                    idx = names.index(ks)
                elif ks.startswith("X") and ks[1:].isdigit():
                    idx = int(ks[1:])
                else:
                    raise ValueError(f"units: feature inconnue {k!r}")
            feat[idx] = _as_dim(v)
        missing = [i for i in range(n_features) if i not in feat]
        if missing:
            raise ValueError(f"units: unités manquantes pour les features {missing}")
    else:
        raise TypeError("units doit être un dict ou une liste")

    if target_units is None:
        raise ValueError("target_units est requis quand units est fourni")
    return feat, _as_dim(target_units)


# ── parseur de chaînes d'unités composées ("m/s", "kg*m/s^2", "N", "J") ─────

_DERIVED = {
    "N":  {"kg": 1, "m": 1, "s": -2},
    "J":  {"kg": 1, "m": 2, "s": -2},
    "W":  {"kg": 1, "m": 2, "s": -3},
    "Pa": {"kg": 1, "m": -1, "s": -2},
    "Hz": {"s": -1},
    "C":  {"A": 1, "s": 1},
    "V":  {"kg": 1, "m": 2, "s": -3, "A": -1},
    "ohm": {"kg": 1, "m": 2, "s": -3, "A": -2},
    "T":  {"kg": 1, "s": -2, "A": -1},
    "rad": {}, "sr": {},
}


def parse_unit_string(s):
    """'m/s' -> {'m':1,'s':-1} ; 'kg*m/s^2' -> {'kg':1,'m':1,'s':-2} ; 'J' -> ...

    Reconnait les unites de base SI, les unites derivees usuelles, et les
    operateurs * / ^ ( ). Un jeton inconnu devient sa propre dimension de base
    (comme dimensions.unit), donc 'widget' -> {'widget': 1}.
    """
    import re
    from .dimensions import _mul, _inv, _pow, unit as _unit

    txt = str(s).strip()
    if txt in ("", "1", "-", "none", "dimensionless"):
        return {}
    toks = re.findall(r"[A-Za-z_]+|-?\d+(?:\.\d+)?|[*/^()]", txt)
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def factor():
        t = peek()
        if t == "(":
            pos[0] += 1
            d = expr()
            if peek() == ")":
                pos[0] += 1
            return d
        pos[0] += 1
        if t is None:
            return {}
        d = dict(_DERIVED[t]) if t in _DERIVED else _unit(t)
        if peek() == "^":
            pos[0] += 1
            e = peek()
            pos[0] += 1
            d = _pow(d, float(e))
        return d

    def expr():
        d = factor()
        while peek() in ("*", "/"):
            op = peek()
            pos[0] += 1
            r = factor()
            d = _mul(d, r) if op == "*" else _mul(d, _inv(r))
        return d

    return expr()
