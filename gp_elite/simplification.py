"""The simplification of a tree, and its caches.

Part of gp_elite/core.py until 1.4.0, moved without change in 1.5.
"""
from __future__ import annotations

import math

from .numeric import (safe_arcsin, safe_div, safe_exp, safe_log, safe_pow,
                      safe_sqrt, safe_tan)
from .config import (BINARY_OPS)
from .tree import (Node)

_TRIVIAL_CACHE: dict = {}

# ============================================================
# SIMPLIFICATION ALGÉBRIQUE
# ============================================================

def _is_float(n) -> bool:
    return n is not None and isinstance(n.value, float)

def _is_const(n, v: float) -> bool:
    return _is_float(n) and abs(n.value - v) < 1e-9

_SIMPLIFY_CACHE: dict = {}   # hash → simplified Node (resets each generation)


def _clear_simplify_caches():
    """Vide le cache de simplification et ceux qui en dépendent."""
    _SIMPLIFY_CACHE.clear()
    _TRIVIAL_CACHE.clear()

def simplify(node: Node) -> Node:
    """Simplification algébrique avec cache structurel.

    [FIX-DAG v18] Le cache ne retourne JAMAIS d'objet partagé (copie fraîche),
    et la simplification ne mute JAMAIS l'arbre d'entrée. Cause racine d'un
    OOM corrigée : l'ancienne version créait des DAG (sous-arbres partagés)
    et pouvait engendrer des cycles -> tree_size() infini -> SIGKILL.
    [FIX-REC v18] Implémentation ITÉRATIVE (post-ordre, pile explicite) :
    l'ancienne récursion mutuelle simplify/_simplify_once consommait ~4 frames
    par niveau et levait RecursionError sur les arbres profonds produits par
    le constructeur stigmergique avant l'application du cap de profondeur.
    """
    if node is None:
        return node
    h = node.exact_hash()                    # [v0.7] exact : voir Node.exact_hash
    cached = _SIMPLIFY_CACHE.get(h)
    if cached is not None:
        return cached.copy()                 # jamais d'objet partagé
    result = _simplify_tree(_simplify_tree(node))   # 2 passes (cascade de règles)
    _SIMPLIFY_CACHE[h] = result
    return result.copy()


def _simplify_tree(root: Node) -> Node:
    """Post-ordre itératif : reconstruit une copie simplifiée de bas en haut.
    Ne mute jamais l'entrée ; chaque nœud produit est neuf ou appartient
    exclusivement au sous-arbre en construction (zéro partage).
    [v0.8] Une feuille est recopiée directement : aucune règle ne s'applique
    à un nœud sans enfant (_simplify_node rendait Node(v)), et sa forme en
    cache ne peut être qu'elle-même. Mêmes arbres, deux fois moins d'appels."""
    if root is None:
        return None
    out: dict = {}                      # id(noeud original) -> Node simplifié neuf
    stack = [(root, False)]
    pop = stack.pop
    push = stack.append
    cache_get = _SIMPLIFY_CACHE.get
    while stack:
        nd, processed = pop()
        if processed:
            l = out.pop(id(nd.left))  if nd.left  is not None else None
            r = out.pop(id(nd.right)) if nd.right is not None else None
            out[id(nd)] = _simplify_node(nd.value, l, r)
            continue
        left = nd.left
        right = nd.right
        if left is None and right is None:
            out[id(nd)] = Node(nd.value)
            continue
        # Cache structurel au niveau du sous-arbre (lecture seule, copie)
        h = nd._ehash
        c = cache_get(h if h is not None else nd.exact_hash())
        if c is not None:
            out[id(nd)] = c.copy()
            continue
        push((nd, True))
        if left  is not None: push((left,  False))
        if right is not None: push((right, False))
    return out[id(root)]


_UNARY_FOLD = frozenset(("sin", "cos", "tan", "tanh", "exp", "log", "sqrt",
                         "abs", "neg", "sq", "cube", "arcsin"))   # [1.3-A1]


def _simplify_node(v, left, right) -> Node:
    """Applique les règles algébriques à UN nœud dont les enfants sont déjà
    simplifiés. left/right appartiennent exclusivement à l'appelant : les
    réutiliser dans le résultat est sûr (aucun partage inter-arbres).
    [v0.8] Mêmes règles, dans le même ordre ; tests d'appartenance par
    ensemble et prédicats _is_float/_is_const calculés une fois."""
    lf = left is not None and isinstance(left.value, float)
    rf = right is not None and isinstance(right.value, float)
    # Repliage des constantes unaires (inclut tanh)
    if lf and v in _UNARY_FOLD:
        try:
            c = left.value
            if v == "sin":   return Node(float(math.sin(c)))
            if v == "cos":   return Node(float(math.cos(c)))
            if v == "tan":   return Node(float(safe_tan(c)))
            if v == "arcsin": return Node(float(safe_arcsin(c)))   # [1.3-A1]
            if v == "tanh":  return Node(float(math.tanh(c)))
            if v == "exp":   return Node(float(safe_exp(c)))
            if v == "log":   return Node(float(safe_log(c)))
            if v == "sqrt":  return Node(float(safe_sqrt(c)))
            if v == "abs":   return Node(float(abs(c)))
            if v == "neg":   return Node(float(-c))
            if v == "sq":    return Node(float(c * c))
            if v == "cube":  return Node(float(c * c * c))
        except Exception:
            pass

    # Règles binaires identitaires (_is_const(n, k) = n flottant et
    # |n.value - k| < 1e-9)
    if v == "+":
        if rf and abs(right.value - 0) < 1e-9:  return left
        if lf and abs(left.value - 0) < 1e-9:   return right
        # expr + expr -> 2.0 * expr
        if (left is not None and right is not None
                and not lf and not rf
                and left.exact_hash() == right.exact_hash()):
            return Node("*", Node(2.0), left)
    elif v == "-":
        if rf and abs(right.value - 0) < 1e-9:  return left
        if lf and abs(left.value - 0) < 1e-9:   return Node("neg", right)
        if left and right and left.exact_hash() == right.exact_hash():
            return Node(0.0)
    elif v == "*":
        if rf and abs(right.value - 1) < 1e-9:  return left
        if lf and abs(left.value - 1) < 1e-9:   return right
        if rf and abs(right.value - 0) < 1e-9:  return Node(0.0)
        if lf and abs(left.value - 0) < 1e-9:   return Node(0.0)
        if rf and abs(right.value - -1) < 1e-9: return Node("neg", left)
        if lf and abs(left.value - -1) < 1e-9:  return Node("neg", right)
        if rf and abs(right.value) < 1e-6: return Node(0.0)
        if lf and abs(left.value)  < 1e-6: return Node(0.0)
    elif v == "/":
        if rf and abs(right.value - 1) < 1e-9:  return left
        if lf and abs(left.value - 0) < 1e-9:   return Node(0.0)
        if left and right and left.exact_hash() == right.exact_hash():
            return Node(1.0)
        # (a * b) / a = b  et  (a * b) / b = a
        if left is not None and left.value == "*":
            lh = left.left.exact_hash()  if left.left  else None
            rh = left.right.exact_hash() if left.right else None
            dh = right.exact_hash()      if right      else None
            if lh and lh == dh: return left.right
            if rh and rh == dh: return left.left
    elif v == "pow":
        if rf and abs(right.value - 0) < 1e-9:  return Node(1.0)
        if rf and abs(right.value - 1) < 1e-9:  return left
        if lf and abs(left.value - 0) < 1e-9:   return Node(0.0)
        if lf and abs(left.value - 1) < 1e-9:   return Node(1.0)

    # Repliage des constantes binaires
    if lf and rf and v in BINARY_OPS:
        a, b = left.value, right.value
        try:
            if v == "+":   return Node(float(a + b))
            if v == "-":   return Node(float(a - b))
            if v == "*":   return Node(float(a * b))
            if v == "/":   return Node(float(safe_div(a, b)))
            if v == "pow": return Node(float(safe_pow(a, b)))
        except Exception:
            pass

    # Double négation
    if v == "neg" and left is not None and left.value == "neg":
        return left.left

    # [1.3-A2] L'arc sinus porte sa propre constante : arcsin(u) devient
    # arcsin(1 * u), que l'ajustement des constantes règle comme les autres.
    # Les variables sont divisées par leur maximum avant la recherche ; une
    # loi en arcsin a donc besoin d'un facteur dans son argument, que le
    # polissage ne sait pas ajouter (benchmarks/results_1.3/a1/examine).
    if v == "arcsin" and left is not None and not _has_own_factor(left):
        return Node("arcsin", Node("*", Node(1.0), left))

    return Node(v, left, right)


def _has_own_factor(n) -> bool:
    """[1.3-A2] Vrai si n est un produit ou un quotient dont l'opérande de
    gauche est un nombre, ou un produit dont l'opérande de droite en est un."""
    if n.value == "*":
        return _is_float(n.left) or _is_float(n.right)
    if n.value == "/":
        return _is_float(n.left)
    return False

# ============================================================
# OPTIMISATION DES CONSTANTES — Adam gradient numérique
# ============================================================

def _invalidate_all_hashes(node: Node):
    """Invalide récursivement le cache de hash sur tout l'arbre."""
    stack = [node]
    while stack:
        n = stack.pop()
        n._hash  = None
        n._chash = None
        n._ehash = None
        if n.left:  stack.append(n.left)
        if n.right: stack.append(n.right)
