"""The tree of a formula: Node, its hashes, its text (to_string) and its
sympy form, its size, depth and complexity, and its constants.

Part of gp_elite/core.py until 1.4.0, moved without change in 1.5.
"""
from __future__ import annotations

import math
import struct
import hashlib
from collections import deque
from typing import Optional, List, Tuple, Dict, Any

from . import state
from .config import (ALL_BINARY_OPS, ALL_UNARY_OPS)

# [v0.8] HACHAGE DES ARBRES INDÉPENDANT DE PYTHONHASHSEED.
# Jusqu'en 0.7, les hash d'arbres portaient des chaînes (noms d'opérateurs et
# de variables, constantes écrites en hexadécimal) dont le hash change d'un
# lancement de Python à l'autre. Leur VALEUR orientait certains tirages (le
# graphe de co-occurrences range chaque paire de fragments par hash
# croissant) : deux lancements du même script avec seed=0 rendaient des
# modèles différents, sauf à fixer PYTHONHASHSEED=0 avant de lancer Python.
# Les chaînes sont maintenant codées par un entier stable (blake2b, 64 bits)
# et les constantes par leurs bits IEEE ; hash() d'un tuple d'entiers ne
# dépend pas de PYTHONHASHSEED. seed= suffit à reproduire un ajustement.

_STR_CODES: Dict[str, int] = {}
_PACK_D = struct.Struct("<d").pack
_UNPACK_Q = struct.Struct("<q").unpack
_TAG_FLOAT, _TAG_OTHER, _TAG_UNARY, _TAG_BINARY = 1, 2, 3, 4
_CANON_CONST = hash((_TAG_FLOAT, 0x7FF0DEADC0DE))


def _str_code(s) -> int:
    c = _STR_CODES.get(s)
    if c is None:
        c = int.from_bytes(hashlib.blake2b(str(s).encode("utf-8", "surrogatepass"),
                                           digest_size=8).digest(), "little")
        _STR_CODES[s] = c
    return c


def _value_code(v) -> int:
    """Code stable d'une valeur de nœud non flottante (opérateur, variable)."""
    if isinstance(v, str):
        return _str_code(v)
    if isinstance(v, int):
        return v
    return _str_code(repr(v))


def _leaf_code_exact(v) -> int:
    if isinstance(v, float):
        return hash((_TAG_FLOAT, _UNPACK_Q(_PACK_D(v))[0]))
    return hash((_TAG_OTHER, _value_code(v)))


def _leaf_code_rounded(v) -> int:
    if isinstance(v, float):
        # + 0.0 : -0.0 et 0.0 restent le même individu, comme avant
        return hash((_TAG_FLOAT, _UNPACK_Q(_PACK_D(round(v, 4) + 0.0))[0]))
    return hash((_TAG_OTHER, _value_code(v)))


def _leaf_code_canonical(v) -> int:
    if isinstance(v, float):
        return _CANON_CONST
    return hash((_TAG_OTHER, _value_code(v)))


def _node_hashes(root, attr, leaf_code):
    """Calcule et mémorise `attr` sur tous les nœuds de root qui ne l'ont
    pas encore (pré-ordre, puis enfants avant parents)."""
    stack = [root]
    order = []
    pop = stack.pop
    push = stack.append
    add = order.append
    while stack:
        nd = pop()
        add(nd)
        l = nd.left
        if l is not None and getattr(l, attr) is None:
            push(l)
        r = nd.right
        if r is not None and getattr(r, attr) is None:
            push(r)
    for nd in reversed(order):
        l = nd.left
        r = nd.right
        if l is None and r is None:
            setattr(nd, attr, leaf_code(nd.value))
        elif r is None:
            setattr(nd, attr, hash((_TAG_UNARY, _value_code(nd.value),
                                    getattr(l, attr))))
        else:
            setattr(nd, attr, hash((_TAG_BINARY, _value_code(nd.value),
                                    getattr(l, attr), getattr(r, attr))))


class Node:
    __slots__ = ("value", "left", "right", "_hash", "_chash", "_ehash")

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left  = left
        self.right = right
        self._hash  = None
        self._chash = None   # [v18] canonical_hash mémoïsé
        self._ehash = None   # [v0.7] exact_hash mémoïsé

    def copy(self):
        """Copie profonde ITÉRATIVE — aucune limite de profondeur.
        [FIX-REC v18] L'ancienne version récursive levait RecursionError sur
        les arbres profonds produits par les constructeurs stigmergiques.
        [v0.8] Chaque nœud neuf est créé une fois puis relié à son parent
        (plus de dictionnaire id -> copie ni de double passage par la pile) :
        2,3 fois plus rapide, même arbre.
        NB : ne PAS propager _hash/_chash/_ehash — les mutations in-place
        (point_mutation) n'invalident que le nœud touché ; des hashes hérités
        sur les ancêtres seraient périmés -> faux hits de cache."""
        root = Node(self.value)
        stack = [(self, root)]
        pop = stack.pop
        push = stack.append
        while stack:
            src, dst = pop()
            l = src.left
            if l is not None:
                nl = dst.left = Node(l.value)
                if l.left is not None or l.right is not None:
                    push((l, nl))
            r = src.right
            if r is not None:
                nr = dst.right = Node(r.value)
                if r.left is not None or r.right is not None:
                    push((r, nr))
        return root

    def structural_hash(self) -> int:
        """Hash structurel (constantes arrondies à 4 décimales), mémoïsé.
        [v0.8] Indépendant de PYTHONHASHSEED : voir _node_hashes."""
        h = self._hash
        if h is not None:
            return h
        _node_hashes(self, "_hash", _leaf_code_rounded)
        return self._hash

    def exact_hash(self) -> int:
        """[v0.7] Hash avec les valeurs EXACTES des constantes.

        structural_hash() arrondit les constantes a 4 decimales : c'est voulu
        pour la deduplication de population (1.00001 et 1.00002 y sont le
        meme individu). Mais tout cache qui stocke une VALEUR calculee a
        partir d'un arbre (fonction compilee dont les constantes sont en dur,
        predictions, fitness, forme simplifiee) doit etre indexe sur l'arbre
        EXACT. Jusqu'en 0.6, evaluate_vector(1.00002*x) rendait 1.00001*x si
        ce dernier avait ete compile avant -- y compris lors d'un ajustement
        precedent du meme processus : predict() pouvait calculer avec les
        constantes d'un autre modele, et deux ajustements identiques
        successifs pouvaient diverger."""
        h = self._ehash
        if h is not None:
            return h
        # Même calcul que _node_hashes(self, "_ehash", _leaf_code_exact),
        # écrit avec des accès directs : c'est le hash le plus sollicité.
        stack = [self]
        order = []
        pop = stack.pop
        push = stack.append
        add = order.append
        while stack:
            nd = pop()
            add(nd)
            l = nd.left
            if l is not None and l._ehash is None:
                push(l)
            r = nd.right
            if r is not None and r._ehash is None:
                push(r)
        codes = _STR_CODES
        for nd in reversed(order):
            l = nd.left
            r = nd.right
            v = nd.value
            if l is None and r is None:
                if isinstance(v, float):
                    nd._ehash = hash((1, _UNPACK_Q(_PACK_D(v))[0]))
                else:
                    c = codes.get(v) if isinstance(v, str) else None
                    nd._ehash = hash((2, c if c is not None else _value_code(v)))
                continue
            c = codes.get(v) if isinstance(v, str) else None
            if c is None:
                c = _value_code(v)
            if r is None:
                nd._ehash = hash((3, c, l._ehash))
            else:
                nd._ehash = hash((4, c, l._ehash, r._ehash))
        return self._ehash

    def canonical_hash(self) -> int:
        """Hash canonique (toute constante vaut 'C'), mémoïsé.
        [OPT v18] L'ancienne version recalculait récursivement à chaque appel
        -> O(n²) par individu dans _is_banned et le scan de dominance."""
        h = self._chash
        if h is not None:
            return h
        _node_hashes(self, "_chash", _leaf_code_canonical)
        return self._chash

    def invalidate_hash(self):
        self._hash  = None
        self._chash = None
        self._ehash = None

# ============================================================
# AFFICHAGE
# ============================================================

def to_string(node) -> str:
    if node is None:
        return "0"
    v = node.value
    if v in ALL_BINARY_OPS:                              # [FIX-OPS v20.1]
        if v == "pow":
            return f"pow({to_string(node.left)}, {to_string(node.right)})"
        if v == "max2":
            return f"max({to_string(node.left)}, {to_string(node.right)})"
        if v == "min2":
            return f"min({to_string(node.left)}, {to_string(node.right)})"
        return f"({to_string(node.left)} {v} {to_string(node.right)})"
    if v in ALL_UNARY_OPS:                               # [FIX-OPS v20.1]
        if v == "neg":
            return f"(-{to_string(node.left)})"
        if v == "sq":
            return f"({to_string(node.left)})²"
        if v == "cube":
            return f"({to_string(node.left)})³"
        if v == "is_even":
            return f"is_even({to_string(node.left)})"
        if v == "step":                                  # [V42]
            return f"step({to_string(node.left)})"
        return f"{v}({to_string(node.left)})"
    if v == "max2":                                      # [V42]
        return f"max({to_string(node.left)}, {to_string(node.right)})"
    if v == "min2":                                      # [V42]
        return f"min({to_string(node.left)}, {to_string(node.right)})"
    if isinstance(v, float):
        return str(round(v, 6))
    # [v22-CSV] X[i] → nom réel de la colonne (ex: X[0] → "temperature")
    if (state._GENERIC_CSV_MODE and state.CSV_FEATURE_NAMES and
            isinstance(v, str) and v.startswith("X[") and v.endswith("]")):
        try:
            idx = int(v[2:-1])
            if 0 <= idx < len(state.CSV_FEATURE_NAMES):
                return state.CSV_FEATURE_NAMES[idx]
        except (ValueError, IndexError):
            pass
    # "x" (1-D) ou "X[i]" (N-D) : retourné tel quel
    return str(v)


# ─────────────────────────────────────────────────────────────────────────────
# Conversion en chaîne SYMPY-parsable (distincte de to_string, qui est un
# affichage lisible où sq->² et cube->³ ne sont pas du sympy valide).
# Source unique : réutilisée par GPEliteRegressor.sympy() et par le wrapper
# SRBench, pour qu'ils ne divergent jamais.
# ─────────────────────────────────────────────────────────────────────────────

_SYMPY_UNARY = {
    "neg":     lambda a: "(-(%s))" % a,
    "abs":     lambda a: "Abs(%s)" % a,
    "inv":     lambda a: "(1/(%s))" % a,
    "sq":      lambda a: "((%s)**2)" % a,
    "cube":    lambda a: "((%s)**3)" % a,
    "sqrt":    lambda a: "sqrt(Abs(%s))" % a,   # sqrt du moteur est garde-fou domaine
    "log":     lambda a: "log(Abs(%s))" % a,    # log du moteur est garde-fou domaine
    "exp":     lambda a: "exp(%s)" % a,
    "sin":     lambda a: "sin(%s)" % a,
    "cos":     lambda a: "cos(%s)" % a,
    "tan":     lambda a: "tan(%s)" % a,
    "tanh":    lambda a: "tanh(%s)" % a,
    "arcsin":  lambda a: "asin(%s)" % a,        # [1.3-A1]
    "step":    lambda a: "Heaviside(%s)" % a,
    "is_even": lambda a: "(1 - Mod(floor(%s), 2))" % a,
}
_SYMPY_BINARY = {
    "+":    lambda a, b: "((%s) + (%s))" % (a, b),
    "-":    lambda a, b: "((%s) - (%s))" % (a, b),
    "*":    lambda a, b: "((%s) * (%s))" % (a, b),
    "/":    lambda a, b: "((%s) / (%s))" % (a, b),
    "pow":  lambda a, b: "((%s)**(%s))" % (a, b),
    "max2": lambda a, b: "Max((%s), (%s))" % (a, b),
    "min2": lambda a, b: "Min((%s), (%s))" % (a, b),
}


def node_to_sympy(node, feature_names=None):
    """Retourne une chaine SYMPY-parsable pour l'arbre `node`.

    Contrairement a to_string (affichage lisible, non parsable a cause de ²/³),
    cette forme se relit avec sympy.sympify() et s'evalue numeriquement a
    l'identique de predict(). `feature_names` mappe X[i] -> nom de colonne.
    Leve ValueError sur un operateur non reconnu (jamais un fallback silencieux
    qui produirait une fonction indefinie comme cube(x) au lieu de x**3).
    """
    if node is None:
        return "0"
    if node.left is None and node.right is None:
        v = node.value
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return "%.12g" % float(v)
        # numpy scalars : np.float64 herite de float, mais pas np.int64 de int
        try:
            import numpy as _np
            if isinstance(v, (_np.integer, _np.floating)):
                return "%.12g" % float(v)
        except Exception:
            pass
        s = str(v)
        if s.startswith("X[") and s.endswith("]"):
            try:
                i = int(s[2:-1])
            except ValueError:
                return s
            if feature_names and i < len(feature_names):
                return feature_names[i]
            return "X%d" % i
        return s
    op = node.value
    if node.right is None:
        a = node_to_sympy(node.left, feature_names)
        f = _SYMPY_UNARY.get(op)
        if f is None:
            raise ValueError("node_to_sympy: unmapped unary operator %r" % op)
        return f(a)
    a = node_to_sympy(node.left, feature_names)
    b = node_to_sympy(node.right, feature_names)
    f = _SYMPY_BINARY.get(op)
    if f is None:
        raise ValueError("node_to_sympy: unmapped binary operator %r" % op)
    return f(a, b)


# ============================================================
# MÉTRIQUES
# ============================================================

def tree_size(node) -> int:
    if node is None:
        return 0
    stack = [node]
    count = 0
    while stack:
        n = stack.pop()
        count += 1
        if n.left:  stack.append(n.left)
        if n.right: stack.append(n.right)
    return count

def tree_depth(node) -> int:
    if node is None:
        return 0
    stack = [(node, 1)]
    max_d = 0
    while stack:
        n, d = stack.pop()
        if d > max_d:
            max_d = d
        if n.left:  stack.append((n.left,  d + 1))
        if n.right: stack.append((n.right, d + 1))
    return max_d


# [v14.2 — BIC] Complexité pondérée + pénalité quadratique sur floats ajustés ──
# Formule fitness_BIC v14.2 :
#   fitness = n·ln(MSE_pur) + k·ln(n) + γ·n_adj²·ln(n)
#
#   k     = Σ coût(nœud)   coût(float)=_FLOAT_COMPLEXITY_WEIGHT, coût(op/x)=1
#   n_adj = nombre de constantes AJUSTÉES (non-entières simples)
#   γ     = _FLOAT_GAMMA = 2.0
#
# Distinction constantes entières vs ajustées :
#   · Entière simple (0, ±1, ±2 … ±10) : issue de simplification algébrique
#     (ex : 2.0 via x+x→2*x). Pas de pénalité quadratique.
#   · Ajustée (0.042503, -2.423…) : encode de l'information sur le dataset,
#     contribue à n_adj et déclenche la pénalité sur-linéaire.
#
# Impact : 1 float ajusté → +2·ln(n), 2 → +8·ln(n), 4 → +32·ln(n).
# ─────────────────────────────────────────────────────────────────────────────
_FLOAT_COMPLEXITY_WEIGHT = 3   # coût linéaire d'un float dans k
_FLOAT_GAMMA             = 2.0 # coefficient de la pénalité quadratique


def _is_adjusted_float(value) -> bool:
    """
    [v14.2] True si la valeur est une constante flottante AJUSTÉE (non émergente).
    Exclut les entiers simples (|v|<=10 et v==round(v)) qui peuvent émerger
    naturellement de la simplification algébrique (x+x → 2.0*x, etc.).
    """
    if not isinstance(value, float):
        return False
    if not math.isfinite(value):
        return True     # inf/nan : constante "ajustée" pathologique (pénalisée),
                        # et surtout évite OverflowError sur round(inf)
    if abs(value - round(value)) < 1e-9 and abs(value) <= 10.0:
        return False    # constante entière simple : non pénalisée
    return True


def tree_complexity(node) -> tuple:
    """
    [v14.2] Complexité pondérée de l'arbre pour le calcul BIC.

    Traversée itérative (pas de récursion).
    Retourne (k, n_adj) :
        k     = Σ coût(nœud)  avec coût(float)=_FLOAT_COMPLEXITY_WEIGHT,
                                    coût(op/x) =1
        n_adj = nombre de constantes ajustées (non-entières ou |v|>10)

    Les deux valeurs sont utilisées dans fitness() :
        BIC = n·ln(MSE) + k·ln(n) + _FLOAT_GAMMA·n_adj²·ln(n)
    """
    if node is None:
        return 0, 0
    stack = [node]
    k, n_adj = 0, 0
    while stack:
        nd = stack.pop()
        if isinstance(nd.value, float):
            k += _FLOAT_COMPLEXITY_WEIGHT
            if _is_adjusted_float(nd.value):
                n_adj += 1
        else:
            k += 1
        if nd.left:  stack.append(nd.left)
        if nd.right: stack.append(nd.right)
    return k, n_adj

# ============================================================
# NAVIGATION (itérative)
# ============================================================

def get_all_nodes(root):
    """
    Retourne [(node, parent, side), ...] en ordre BFS.
    Optimisé en O(N) grâce à un collections.deque local.
    """
    if root is None:
        return []
    result = []
    queue = deque([(root, None, None)])
    while queue:
        node, parent, side = queue.popleft()
        result.append((node, parent, side))
        if node.left is not None:
            queue.append((node.left, node, "left"))
        if node.right is not None:
            queue.append((node.right, node, "right"))
    return result

def collect_constants(root) -> List[Node]:
    """Retourne tous les noeuds constantes flottantes."""
    result = []
    stack  = [root]
    while stack:
        n = stack.pop()
        if isinstance(n.value, float):
            result.append(n)
        if n.left:  stack.append(n.left)
        if n.right: stack.append(n.right)
    return result
