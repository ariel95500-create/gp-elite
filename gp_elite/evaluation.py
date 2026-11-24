"""The evaluation of a tree: the NumPy code it compiles to, the plans of
the Jacobian for Levenberg-Marquardt, the compiled functions and
their caches, the scalar and vector evaluation, Pearson's r, the cache
of predictions, and the safe writing of files.

Part of gp_elite/core.py until 1.4.0, moved without change in 1.5.
"""
from __future__ import annotations

import math
import operator
import weakref
import numpy as np
from typing import Optional, List, Tuple, Dict, Any

from . import state
from .numeric import (_COMPILE_CACHE_MAX, _NP_GLOBALS, _is_const_subtree,
                      _np_is_even, _np_max2, _np_maximum, _np_min2,
                      _np_minimum, _np_safe_arcsin, _np_safe_div, _np_safe_exp,
                      _np_safe_log, _np_safe_pow, _np_safe_pow_var,
                      _np_safe_sqrt, _np_safe_tan, _np_step, safe_arcsin,
                      safe_div, safe_exp, safe_log, safe_pow, safe_sqrt,
                      safe_tan)

def _float_literal(v) -> str:
    """[v0.8] Littéral Python d'une constante, sûr dans toute expression.

    Jusqu'en 0.7 le compilateur écrivait repr(v) tel quel : sq(-0.5) donnait
    le code « (-0.5 ** 2) », que Python lit -(0.5 ** 2) = -0.25, puisque **
    lie plus fort que le moins unaire. evaluate_vector rendait donc -0.25 là
    où l'arbre, la formule livrée, l'évaluation scalaire et l'optimisation
    des constantes valent +0.25 (0,8 % des arbres évalués pendant une
    recherche contenaient ce motif). Les constantes négatives sont désormais
    parenthésées, et les non-finies écrites float('inf') / float('nan')
    (leur nom nu levait NameError à l'appel)."""
    v = float(v)
    if v != v:
        return "float('nan')"
    if v == float("inf"):
        return "float('inf')"
    if v == float("-inf"):
        return "(-float('inf'))"
    r = repr(v)
    return "(" + r + ")" if r.startswith("-") else r


def _to_np_code(node) -> str:
    """Traduit récursivement un arbre en expression Python/NumPy (string).
    [v16-NDIM] Supporte les terminaux "X[i]" → "_x[:, i]"
    en plus de "x" → "_x" (rétrocompatibilité 1-D).
    """
    if node is None:
        return "0.0"
    v = node.value
    if v == "x":
        return "_x"
    # [v16-NDIM] Feature i de la matrice X (n_samples, n_features)
    if isinstance(v, str) and v.startswith("X[") and v.endswith("]"):
        try:
            idx = int(v[2:-1])
            return f"_x[:, {idx}]"
        except ValueError:
            return "0.0"
    if isinstance(v, float):
        return _float_literal(v)             # [v0.8] voir _float_literal
    if v == "+":
        return f"({_to_np_code(node.left)} + {_to_np_code(node.right)})"
    if v == "-":
        return f"({_to_np_code(node.left)} - {_to_np_code(node.right)})"
    if v == "*":
        return f"({_to_np_code(node.left)} * {_to_np_code(node.right)})"
    if v == "/":
        return f"_safe_div({_to_np_code(node.left)}, {_to_np_code(node.right)})"
    if v == "pow":
        fn = "_safe_pow" if _is_const_subtree(node.right) else "_safe_powv"
        return f"{fn}({_to_np_code(node.left)}, {_to_np_code(node.right)})"
    if v == "sin":
        return f"np.sin({_to_np_code(node.left)})"
    if v == "cos":
        return f"np.cos({_to_np_code(node.left)})"
    if v == "tan":
        return f"_safe_tan({_to_np_code(node.left)})"
    if v == "arcsin":                                    # [1.3-A1]
        return f"_safe_arcsin({_to_np_code(node.left)})"
    if v == "tanh":
        return f"np.tanh({_to_np_code(node.left)})"
    if v == "exp":
        return f"_safe_exp({_to_np_code(node.left)})"
    if v == "log":
        return f"_safe_log({_to_np_code(node.left)})"
    if v == "sqrt":
        return f"_safe_sqrt({_to_np_code(node.left)})"
    if v == "abs":
        return f"np.abs({_to_np_code(node.left)})"
    if v == "neg":
        return f"(-{_to_np_code(node.left)})"
    if v == "sq":
        return f"({_to_np_code(node.left)} ** 2)"
    if v == "cube":
        return f"({_to_np_code(node.left)} ** 3)"
    if v == "is_even":                                   # [SYRACUSE]
        return f"_is_even({_to_np_code(node.left)})"
    if v == "step":                                      # [V42]
        return f"_step({_to_np_code(node.left)})"
    if v == "max2":                                      # [V42]
        return f"_max2({_to_np_code(node.left)}, {_to_np_code(node.right)})"
    if v == "min2":                                      # [V42]
        return f"_min2({_to_np_code(node.left)}, {_to_np_code(node.right)})"
    return "0.0"

def _collect_constants_ordered(node) -> list:
    """Collecte les constantes en ordre BFS (stable et reproductible)."""
    result = []
    stack = [node]
    while stack:
        n = stack.pop(0)
        if n is None:
            continue
        if isinstance(n.value, float):
            result.append(n)
        if n.left:  stack.append(n.left)
        if n.right: stack.append(n.right)
    return result


def _to_np_code_parametric(node, const_list: list) -> str:
    """
    Traduit l'arbre en code NumPy avec les constantes remplacées par _c[i].
    [v16-NDIM] Supporte les terminaux "X[i]" → "_x[:, i]".
    """
    const_idx = {id(c): i for i, c in enumerate(const_list)}

    def _code(n) -> str:
        if n is None:
            return "0.0"
        v = n.value
        if v == "x":
            return "_x"
        if isinstance(v, str) and v.startswith("X[") and v.endswith("]"):
            try:
                idx = int(v[2:-1])
                return f"_x[:, {idx}]"
            except ValueError:
                return "0.0"
        if isinstance(v, float):
            idx = const_idx.get(id(n))
            return f"_c[{idx}]" if idx is not None else _float_literal(v)
        if v == "+":   return f"({_code(n.left)} + {_code(n.right)})"
        if v == "-":   return f"({_code(n.left)} - {_code(n.right)})"
        if v == "*":   return f"({_code(n.left)} * {_code(n.right)})"
        if v == "/":   return f"_safe_div({_code(n.left)}, {_code(n.right)})"
        if v == "pow":
            fn = "_safe_pow" if _is_const_subtree(n.right) else "_safe_powv"
            return f"{fn}({_code(n.left)}, {_code(n.right)})"
        if v == "sin":  return f"np.sin({_code(n.left)})"
        if v == "cos":  return f"np.cos({_code(n.left)})"
        if v == "tan":  return f"_safe_tan({_code(n.left)})"
        if v == "arcsin": return f"_safe_arcsin({_code(n.left)})"   # [1.3-A1]
        if v == "tanh": return f"np.tanh({_code(n.left)})"
        if v == "exp":  return f"_safe_exp({_code(n.left)})"
        if v == "log":  return f"_safe_log({_code(n.left)})"
        if v == "sqrt": return f"_safe_sqrt({_code(n.left)})"
        if v == "abs":  return f"np.abs({_code(n.left)})"
        if v == "neg":  return f"(-{_code(n.left)})"
        if v == "sq":   return f"({_code(n.left)} ** 2)"
        if v == "cube": return f"({_code(n.left)} ** 3)"
        if v == "is_even": return f"_is_even({_code(n.left)})"   # [SYRACUSE]
        if v == "step":    return f"_step({_code(n.left)})"      # [V42]
        if v == "max2":    return f"_max2({_code(n.left)}, {_code(n.right)})"  # [V42]
        if v == "min2":    return f"_min2({_code(n.left)}, {_code(n.right)})"  # [V42]
        return "0.0"

    return _code(node)


_PARAMETRIC_CACHE_MAX = 2048


# ============================================================
# [v0.8] ÉVALUATION INCRÉMENTALE POUR LEVENBERG-MARQUARDT
# ============================================================
# La jacobienne par différences avant réévaluait l'arbre ENTIER pour chaque
# constante perturbée, alors qu'une constante ne change que les nœuds situés
# sur le chemin de sa feuille à la racine. On compile donc, par forme d'arbre,
# une évaluation « en ligne droite » qui garde la valeur de chaque nœud, et
# pour chaque constante la liste des opérations du chemin feuille -> racine.
# Chaque colonne ne recalcule que ce chemin, les autres nœuds reprenant leur
# valeur au point courant. Les opérations et leurs opérandes sont exactement
# ceux de l'expression compilée (_to_np_code_parametric) : le résultat est le
# même bit pour bit (vérifié par tests/test_speed_equivalence.py), pour 3 à
# 5 fois moins de calcul sur la jacobienne.

_LM_UNARY_FN = {
    "sin":  np.sin, "cos": np.cos, "tan": _np_safe_tan, "tanh": np.tanh,
    "exp":  _np_safe_exp, "log": _np_safe_log, "sqrt": _np_safe_sqrt,
    "abs":  np.abs, "is_even": _np_is_even, "step": _np_step,
    "arcsin": _np_safe_arcsin,                       # [1.3-A1]
}
_LM_UNARY_SRC = {
    "sin": "np.sin", "cos": "np.cos", "tan": "_safe_tan", "tanh": "np.tanh",
    "exp": "_safe_exp", "log": "_safe_log", "sqrt": "_safe_sqrt",
    "abs": "np.abs", "is_even": "_is_even", "step": "_step",
    "arcsin": "_safe_arcsin",                        # [1.3-A1]
}
_LM_BINARY_SRC = {"/": "_safe_div", "max2": "_max2", "min2": "_min2"}
_LM_BINARY_FN = {"/": _np_safe_div, "max2": _np_max2, "min2": _np_min2}


def _lm_apply(op, a, b):
    """Une opération binaire telle que l'écrit _to_np_code_parametric."""
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    return op(a, b)          # fonction protégée (_safe_div, _safe_pow, ...)


class _LMPlan:
    """Plan d'évaluation d'une FORME d'arbre (constantes -> _c[j])."""
    __slots__ = ("full", "cols", "n_consts", "n_values")


_LM_PLAN_CACHE: Dict[Any, _LMPlan] = {}
_LM_PLAN_CACHE_MAX = 2048


def _lm_build_plan(node, consts) -> Optional[_LMPlan]:
    """Construit le plan d'une forme d'arbre, ou None si elle n'est pas
    compilable (on retombe alors sur l'évaluation complète)."""
    const_idx = {id(c): i for i, c in enumerate(consts)}
    lines = []          # code source en ligne droite
    info = []           # par indice de valeur : (op, [indices enfants], pow_fn)
    leaf_of_const = {}  # indice de constante -> indice de valeur de sa feuille
    parent = {}         # indice de valeur -> (indice parent, côté)

    # Parcours post-ordre ITÉRATIF qui reproduit _code() de
    # _to_np_code_parametric : mêmes enfants visités, mêmes expressions.
    stack = [(node, False)]
    out_idx = []        # pile des indices produits
    while stack:
        n, done = stack.pop()
        if not done:
            if n is None:
                k = len(info); info.append(("lit", [], None))
                lines.append(f"    v{k} = 0.0")
                out_idx.append(k)
                continue
            v = n.value
            if v == "x":
                k = len(info); info.append(("leaf", [], None))
                lines.append(f"    v{k} = _x")
                out_idx.append(k)
                continue
            if isinstance(v, str) and v.startswith("X[") and v.endswith("]"):
                k = len(info)
                try:
                    lines.append(f"    v{k} = _x[:, {int(v[2:-1])}]")
                    info.append(("leaf", [], None))
                except ValueError:
                    lines.append(f"    v{k} = 0.0")
                    info.append(("lit", [], None))
                out_idx.append(k)
                continue
            if isinstance(v, float):
                j = const_idx.get(id(n))
                if j is None:
                    return None
                k = len(info); info.append(("const", [], None))
                lines.append(f"    v{k} = _c[{j}]")
                leaf_of_const[j] = k
                out_idx.append(k)
                continue
            if v in ("+", "-", "*", "/", "pow", "max2", "min2"):
                stack.append((n, True))
                stack.append((n.right, False))
                stack.append((n.left, False))
                continue
            if v in _LM_UNARY_SRC or v in ("neg", "sq", "cube"):
                stack.append((n, True))
                stack.append((n.left, False))
                continue
            # opérateur inconnu : l'expression compilée écrit 0.0 sans
            # évaluer les enfants
            k = len(info); info.append(("lit", [], None))
            lines.append(f"    v{k} = 0.0")
            out_idx.append(k)
            continue
        v = n.value
        k = len(info)
        if v in ("+", "-", "*", "/", "pow", "max2", "min2"):
            b = out_idx.pop(); a = out_idx.pop()
            if v in ("+", "-", "*"):
                lines.append(f"    v{k} = (v{a} {v} v{b})")
                info.append((v, [a, b], None))
            elif v == "pow":
                fname = "_safe_pow" if _is_const_subtree(n.right) else "_safe_powv"
                lines.append(f"    v{k} = {fname}(v{a}, v{b})")
                info.append((_NP_GLOBALS[fname], [a, b], None))
            else:
                lines.append(f"    v{k} = {_LM_BINARY_SRC[v]}(v{a}, v{b})")
                info.append((_LM_BINARY_FN[v], [a, b], None))
            parent[a] = (k, 0)
            parent[b] = (k, 1)
        else:
            a = out_idx.pop()
            if v == "neg":
                lines.append(f"    v{k} = (-v{a})")
            elif v == "sq":
                lines.append(f"    v{k} = (v{a} ** 2)")
            elif v == "cube":
                lines.append(f"    v{k} = (v{a} ** 3)")
            else:
                lines.append(f"    v{k} = {_LM_UNARY_SRC[v]}(v{a})")
            info.append((v, [a], None))
            parent[a] = (k, 0)
        out_idx.append(k)

    root = out_idx.pop()
    names = ", ".join(f"v{k}" for k in range(len(info)))
    src = ("def _full(_x, _c):\n" + "\n".join(lines) +
           f"\n    return v{root}, ({names},)\n")
    globs = dict(_NP_GLOBALS)
    try:
        exec(src, globs)
    except Exception:
        return None

    cols = []
    for j in range(len(consts)):
        k = leaf_of_const.get(j)
        if k is None:
            cols.append(None)            # constante sans effet sur la sortie
            continue
        steps = []
        while k in parent:
            pk, side = parent[k]
            op, ch, _ = info[pk]
            if len(ch) == 2:
                steps.append((op, side, ch[1 - side]))
            else:
                steps.append((op, -1, -1))
            k = pk
        cols.append((leaf_of_const[j], tuple(steps)))
    plan = _LMPlan()
    plan.full = globs["_full"]
    plan.cols = cols
    plan.n_consts = len(consts)
    plan.n_values = len(info)
    return plan


def _lm_plan(node, consts) -> Optional[_LMPlan]:
    key = (node.canonical_hash(), len(consts))
    plan = _LM_PLAN_CACHE.get(key)
    if plan is None and key not in _LM_PLAN_CACHE:
        plan = _lm_build_plan(node, consts)
        _LM_PLAN_CACHE[key] = plan
        if len(_LM_PLAN_CACHE) > _LM_PLAN_CACHE_MAX:
            for old_key in list(_LM_PLAN_CACHE.keys())[:256]:
                del _LM_PLAN_CACHE[old_key]
    return plan


def _lm_column(plan, j, cv, values):
    """Valeur de la racine quand seule la constante j vaut cv[j] (les
    autres nœuds gardent `values`, calculées au point courant)."""
    col = plan.cols[j]
    t = cv[j]
    for op, side, sib in col[1]:
        if side < 0:                         # unaire
            if op == "neg":
                t = -t
            elif op == "sq":
                t = t ** 2
            elif op == "cube":
                t = t ** 3
            else:
                t = _LM_UNARY_FN[op](t)
        elif side == 0:
            t = _lm_apply(op, t, values[sib])
        else:
            t = _lm_apply(op, values[sib], t)
    return t


def compile_parametric(node) -> Tuple[Any, list]:
    """
    Compile f(_x, _c) où _c est un array numpy des constantes.
    Hash structural → une seule compilation par forme d'arbre.
    Retourne (fn, const_nodes) où const_nodes est dans l'ordre BFS.
    """
    # Collecter les constantes de CE nœud (avec leurs ids actuels)
    consts = _collect_constants_ordered(node)
    n_consts = len(consts)

    h = node.structural_hash()
    # Vérifier si le cache a une fonction avec le bon nombre de constantes
    cached = state._PARAMETRIC_CACHE.get(h)
    if cached is not None and cached[1] == n_consts:
        return cached[0], consts

    code = _to_np_code_parametric(node, consts)
    src  = f"def _f(_x, _c):\n    return {code}\n"
    globs = dict(_NP_GLOBALS)
    try:
        exec(src, globs)
        fn = globs["_f"]
    except Exception:
        fn = None

    if fn is not None:
        state._PARAMETRIC_CACHE[h] = (fn, n_consts)
        if len(state._PARAMETRIC_CACHE) > _PARAMETRIC_CACHE_MAX:
            for old_key in list(state._PARAMETRIC_CACHE.keys())[:256]:
                del state._PARAMETRIC_CACHE[old_key]

    return fn, consts


def compile_to_numpy(node):
    """
    Compile l'arbre en f(x_array) -> np.ndarray, mis en cache par hash structural.
    Utilisé par evaluate_vector et raw_mse.
    [v0.7] Indexé par exact_hash : les constantes sont écrites en dur dans le
    code compilé, deux arbres qui ne diffèrent qu'au-delà de la 4e décimale
    ne peuvent pas partager une fonction.
    """
    h = node.exact_hash()
    if h in state._COMPILE_CACHE:
        return state._COMPILE_CACHE[h]
    code = _to_np_code(node)
    src  = f"def _f(_x):\n    return {code}\n"
    globs = dict(_NP_GLOBALS)
    try:
        exec(src, globs)
        fn = globs["_f"]
    except Exception:
        fn = lambda _x, _n=node: np.array([evaluate(_n, float(xi)) for xi in _x])
    state._COMPILE_CACHE[h] = fn
    if len(state._COMPILE_CACHE) > _COMPILE_CACHE_MAX:
        # Évacuation FIFO ultra-rapide tirant parti de l'ordre d'insertion natif
        for _ in range(512):
            if state._COMPILE_CACHE:
                state._COMPILE_CACHE.pop(next(iter(state._COMPILE_CACHE)))
    return fn

# ============================================================
# ÉVALUATION SCALAIRE (conservée pour simplify / affichage)
# ============================================================

def evaluate(node, x) -> float:
    """Évaluation récursive scalaire — utilisée uniquement pour l'affichage 1-D.
    [v16-NDIM] x peut être un float (mode 1-D) ou un array 1-D de shape (n_features,)
    représentant une seule ligne de la matrice X.
    Les terminaux X[i] indexent x[i] ; le terminal "x" utilise x directement (1-D).
    """
    if node is None:
        return 0.0
    try:
        v = node.value
        if v == "x":
            return float(x) if not hasattr(x, '__len__') else float(x[0])
        # [v16-NDIM] Feature i
        if isinstance(v, str) and v.startswith("X[") and v.endswith("]"):
            try:
                idx = int(v[2:-1])
                return float(x[idx])
            except (IndexError, TypeError, ValueError):
                return 0.0
        if isinstance(v, float):
            return v
        if v == "+":
            return evaluate(node.left, x) + evaluate(node.right, x)
        if v == "-":
            return evaluate(node.left, x) - evaluate(node.right, x)
        if v == "*":
            return evaluate(node.left, x) * evaluate(node.right, x)
        if v == "/":
            return safe_div(evaluate(node.left, x), evaluate(node.right, x))
        if v == "pow":
            return safe_pow(evaluate(node.left, x), evaluate(node.right, x))
        if v == "sin":
            return math.sin(evaluate(node.left, x))
        if v == "cos":
            return math.cos(evaluate(node.left, x))
        if v == "tan":
            return safe_tan(evaluate(node.left, x))
        if v == "arcsin":                                # [1.3-A1]
            return safe_arcsin(evaluate(node.left, x))
        if v == "tanh":
            return math.tanh(evaluate(node.left, x))
        if v == "exp":
            return safe_exp(evaluate(node.left, x))
        if v == "log":
            return safe_log(evaluate(node.left, x))
        if v == "sqrt":
            return safe_sqrt(evaluate(node.left, x))
        if v == "abs":
            return abs(evaluate(node.left, x))
        if v == "neg":
            return -evaluate(node.left, x)
        if v == "sq":
            a = evaluate(node.left, x); return a * a
        if v == "cube":
            a = evaluate(node.left, x); return a * a * a
    except Exception:
        return 0.0
    return 0.0

# [v0.8] INTERPRÉTEUR — même calcul que le code compilé, sans le compiler.
# Compiler un arbre (génération du source, compile(), exec) coûte ~5 µs par
# nœud, et la grande majorité des arbres de la recherche ne sont évalués
# qu'une ou deux fois : 11 % du temps total y passait. L'interpréteur applique
# nœud par nœud EXACTEMENT les opérations qu'écrit _to_np_code (mêmes
# fonctions, mêmes opérandes, mêmes littéraux) ; le code compilé n'est plus
# produit que pour un arbre évalué au moins _COMPILE_AFTER fois. Mêmes
# valeurs bit pour bit (tests/test_speed_equivalence.py). Les arbres de plus
# de _INTERP_MAX_DEPTH niveaux passent toujours par le compilateur, pour en
# garder le comportement exact (y compris ses replis).

_INTERP_MAX_DEPTH = 100
_COMPILE_AFTER = 3
_EVAL_COUNTS: Dict[int, int] = {}
_NAN = float("nan")


class _InterpTooDeep(Exception):
    pass


def _sq(a):
    return a ** 2


def _cube(a):
    return a ** 3


_INTERP_BINARY = {"+": operator.add, "-": operator.sub, "*": operator.mul,
                  "/": _np_safe_div, "max2": _np_max2, "min2": _np_min2}
_INTERP_UNARY = {"sin": np.sin, "cos": np.cos, "tan": _np_safe_tan,
                 "arcsin": _np_safe_arcsin,                  # [1.3-A1]
                 "tanh": np.tanh, "exp": _np_safe_exp, "log": _np_safe_log,
                 "sqrt": _np_safe_sqrt, "abs": np.abs, "neg": operator.neg,
                 "sq": _sq, "cube": _cube, "is_even": _np_is_even,
                 "step": _np_step}


def _interp(n, x, d):
    """Valeur de l'arbre n sur x, selon les règles de _to_np_code."""
    if n is None:
        return 0.0
    v = n.value
    if v == "x":
        return x
    if isinstance(v, str) and v.startswith("X[") and v.endswith("]"):
        try:
            idx = int(v[2:-1])
        except ValueError:
            return 0.0
        return x[:, idx]
    if isinstance(v, float):
        v = float(v)                       # le littéral de _float_literal
        return _NAN if v != v else v
    if not isinstance(v, str):             # _to_np_code : aucun opérateur
        return 0.0
    if d >= _INTERP_MAX_DEPTH:
        raise _InterpTooDeep()
    f = _INTERP_BINARY.get(v)
    if f is not None:
        return f(_interp(n.left, x, d + 1), _interp(n.right, x, d + 1))
    f = _INTERP_UNARY.get(v)
    if f is not None:
        return f(_interp(n.left, x, d + 1))
    if v == "pow":
        f = _np_safe_pow if _is_const_subtree(n.right) else _np_safe_pow_var
        return f(_interp(n.left, x, d + 1), _interp(n.right, x, d + 1))
    return 0.0


def evaluate_vector(node, xs) -> np.ndarray:
    """Évalue sur un vecteur (1-D) ou une matrice (N-D) via le compilateur NumPy.
    [v16-NDIM]
      · xs 1-D (n_samples,)          → mode rétrocompatible, _x = xs
      · xs 2-D (n_samples, n_features) → mode N-D, _x[:, i] accès par feature
    La fonction compilée reçoit _x tel quel ; _to_np_code génère le bon indexage.
    """
    h = node.exact_hash()
    fn = state._COMPILE_CACHE.get(h)
    if fn is None:
        k = _EVAL_COUNTS.get(h, 0) + 1
        if k >= _COMPILE_AFTER:
            fn = compile_to_numpy(node)
            _EVAL_COUNTS.pop(h, None)
        else:
            _EVAL_COUNTS[h] = k
            if len(_EVAL_COUNTS) > 65536:
                _EVAL_COUNTS.clear()
    if isinstance(xs, np.ndarray):
        x_in = xs
    else:
        x_in = np.asarray(xs, dtype=float)
    if fn is None:
        try:
            with np.errstate(all="ignore"):
                r = _interp(node, x_in, 0)
        except _InterpTooDeep:
            fn = compile_to_numpy(node)
        except Exception:
            n_rows = xs.shape[0] if isinstance(xs, np.ndarray) else len(xs)
            return np.zeros(n_rows)
    try:
        # [v0.7] sq/cube/* ne sont pas proteges : un debordement donne inf,
        # remplace juste apres. Sans errstate, NumPy imprimait des
        # « RuntimeWarning: overflow » chez l'utilisateur (sans effet sur le
        # resultat, qui est identique).
        if fn is not None:
            with np.errstate(all="ignore"):
                r = fn(x_in)
        n_rows = x_in.shape[0]
        r = np.asarray(r, dtype=float)
        if r.shape == ():          # scalaire → broadcast
            r = np.full(n_rows, float(r))
        # Remplace les non-finis (inf/nan) par 0, PUIS borne les valeurs
        # extrêmes-mais-finies (ex. exp() en extrapolation hors domaine) pour
        # éviter tout overflow en aval (R², carré). Borne large (1e12) qui ne
        # change rien aux prédictions normales mais neutralise les explosions.
        r = np.where(np.isfinite(r), r, 0.0)
        return _np_minimum(_np_maximum(r, -1e12), 1e12)
    except Exception:
        n_rows = xs.shape[0] if isinstance(xs, np.ndarray) else len(xs)
        return np.zeros(n_rows)

# ============================================================
# DATASET
# ============================================================

# Hot zones par problème : zones où la cible varie le plus rapidement
# (extrema, points d'inflexion, singularités) — à sur-échantillonner
_HOT_ZONES: Dict[str, List[float]] = {
    # sin(x²) : extrema à x = sqrt(π/2 + kπ)
    "1":  [1.25, -1.25, 1.77, -1.77, 2.17, -2.17, 2.51, -2.51, 2.81, -2.81],
    # x³-x²+x-1 : inflexion à x≈0.33, racine à x=1
    "2":  [0.33, 1.0, -1.0, 0.0, 2.0, -2.0],
    # exp(-x²)·sin(2x) : extrema denses autour de 0
    "3":  [0.4, -0.4, 1.1, -1.1, 1.8, -1.8, 0.0],
    # log(1+x²)·cos(x) : oscillations modérées
    "4":  [0.0, 1.57, -1.57, 3.14, -3.14, 0.8, -0.8],
    # x·sin(x²)·cos(x/2) : combinaison des extrema de sin(x²)
    "5":  [1.25, -1.25, 1.77, -1.77, 2.17, -2.17, 0.5, -0.5, 2.51, -2.51],
    # exp(-|x|)·(x²-1) : racines à x=±1, max à x≈0
    "6":  [1.0, -1.0, 0.0, 0.5, -0.5, 2.0, -2.0, 1.5, -1.5],
    # sinc(x)·cos(x²) : singularité en 0, oscillations denses
    "7":  [0.01, 1.25, -1.25, 1.77, -1.77, 2.17, -2.17, 0.5, -0.5],
    # sin(πx)/(x²+1) : extrema à x≈±0.5, ±1.5
    "8":  [0.5, -0.5, 1.5, -1.5, 0.0, 1.0, -1.0, 2.0, -2.0],
    # tanh(x)·exp(-x²/4) : inflexion vers x≈±1
    "9":  [1.0, -1.0, 0.5, -0.5, 1.5, -1.5, 0.0, 2.0, -2.0],
    # x³·sin(1/x) : oscillations infiniment rapides près de 0
    "10": [0.3, 0.5, 0.8, 1.2, 1.6, 2.0, 2.5, 0.2, 0.4],
    # ── N-D Hot zones ────────────────────────────────────────────────────
    # ND1  X[0]·sin(X[1]) + X[2]² : gradient fort autour de 0, ±π/2
    "ND1": [0.0, 1.0, -1.0, 1.57, -1.57, 2.0, -2.0],
    # ND2  exp(-X[0]²)·cos(X[1]) : pic gaussien en X[0]=0, oscillation X[1]
    # Hot zones : X[0] proche de 0 (max de exp), X[1] sur les extrema de cos
    "ND2": [0.0, 0.3, -0.3, 0.6, -0.6, 1.0, -1.0, 1.57, -1.57],
    # ND3  X[0]³ - X[1]·X[2] : inflexion cubique, interactions linéaires
    "ND3": [0.0, 1.0, -1.0, 1.5, -1.5, 2.0, -2.0],
    # ND4  sin(X[0]+X[1])·exp(-X[2]²/2) : extrema de sin et pic gaussien
    "ND4": [0.0, 0.78, -0.78, 1.57, -1.57, 0.5, -0.5],
    # ND5  X[0]·X[1]/(1+X[2]²) : singularité adoucie, gradient fort en 0
    "ND5": [0.0, 0.5, -0.5, 1.0, -1.0, 1.5, -1.5, 2.0, -2.0],
    # BATTERY_SOH  1 - 0.02·exp(X[0])·X[1] - 0.005·X[2]²
    # · X[0] : exp(X[0]) varie de e⁻²≈0.135 à e²≈7.39 → gradient fort sur [1, 2]
    # · X[1] : facteur linéaire — discriminant aux extrema ±2
    # · X[2] : terme quadratique — extrema en ±2, nul en 0
    # Hot zones concentrées là où exp(X[0])·X[1] est maximal/minimal
    "BATTERY_SOH": [1.5, 2.0, -1.5, -2.0, 0.0, 1.0, -1.0, 0.5, -0.5],
}

# ============================================================
# FITNESS & CACHE GLOBAL
# ============================================================


# ── OBJECTIF 1 : Fitness Hybride ────────────────────────────────────────────
# Remplace le MSE pur par une métrique composite Corrélation de Pearson + MSE
# normalisé.  Plus basse = meilleure (tendant vers 0 sur solution parfaite).
#
#   std_p < 1e-6  → arbre constant → pénalité forte  mse + 2.0
#   sinon          → r  = cov(p, t) / (std_p × std_t),  borné [-1, 1]
#                    correlation_loss = 1 - r   (0 = corrélation parfaite)
#                    fitness_hybride  = 5.0 × correlation_loss
#                                     + mse / (1 + mse)
#
# Avantage : un arbre à "bonne forme géométrique mais mauvaise échelle" obtient
# un score bien inférieur au MSE pur, ce qui évite le rejet par le tri.
# Le terme mse/(1+mse) est borné dans [0,1) et pénalise l'amplitude résiduelle.
# ─────────────────────────────────────────────────────────────────────────────

def _pearson_r(preds: np.ndarray, ys_np: np.ndarray) -> float:
    """Corrélation de Pearson optimisée — calcul inline sans np.corrcoef.
    [V42-FIX] errstate all='ignore' pour supprimer les overflow des trajectoires.
    """
    with np.errstate(all='ignore'):
        a  = preds - preds.mean()
        b  = ys_np - ys_np.mean()
        na = float(np.dot(a, a))
        nb = float(np.dot(b, b))
        if na < 1e-16 or nb < 1e-16:
            return 0.0
        r = float(np.dot(a, b)) / (na * nb) ** 0.5
    if not np.isfinite(r):
        return 0.0
    return float(np.clip(r, -1.0, 1.0))



# [OPT] Cache de prédictions par hash structurel — partagé par raw_mse,
# _pure_mse et raw_pearson_r (élimine 2-3x les évaluations redondantes).
_PRED_CACHE_MAX = 8192

def _predict_cached(node, xs_np):
    # [FIX-CACHE v23.1] La clé inclut l'IDENTITÉ du jeu de données (id + shape).
    # Sans cela, une prédiction calculée sur le TRAIN (134 pts) était renvoyée
    # pour une requête sur le dataset COMPLET (168 pts) → mismatch de forme →
    # exception silencieuse → MSE rapporté à 1e6 alors que le modèle est bon.
    # [v0.8] id() n'identifie un tableau que tant qu'il existe : une fois
    # libéré, son adresse peut être réattribuée à un AUTRE tableau de même
    # taille, qui recevrait alors les prédictions du premier. Les appels du
    # moteur passent des tableaux qui vivent tout l'ajustement, mais rien ne
    # l'imposait : l'entrée garde désormais une référence faible au tableau
    # et n'est servie que pour lui.
    h = (node.exact_hash(), id(xs_np), xs_np.shape[0])   # [v0.7] exact
    e = state._PRED_CACHE.get(h)
    if e is not None and e[0]() is xs_np:
        return e[1]
    preds = evaluate_vector(node, xs_np)
    state._PRED_CACHE[h] = (weakref.ref(xs_np), preds)
    if len(state._PRED_CACHE) > _PRED_CACHE_MAX:
        for _ in range(1024):
            if state._PRED_CACHE:
                state._PRED_CACHE.pop(next(iter(state._PRED_CACHE)))
    return preds

# ════════════════════════════════════════════════════════════════
# [v18-LS] LINEAR SCALING (Keijzer, 2003)
# ════════════════════════════════════════════════════════════════
# La fitness évalue a + b·f(x) où (a, b) sont les coefficients OLS
# optimaux en FORME FERMÉE (2 produits scalaires — coût négligeable) :
#     b = cov(f(x), y) / var(f(x))        a = mean(y) − b·mean(f(x))
# Conséquence : le GP n'a plus à apprendre ni l'échelle ni l'offset,
# il ne cherche que la FORME de la fonction. C'est la technique au
# meilleur ratio gain/coût de toute la littérature GP — standard
# dans Operon, PySR, et tous les moteurs SRBench de tête.

# [CUSTOM-LOSS] Fonction de coût personnalisée optionnelle.
# Signature : loss_fn(predictions: np.ndarray, X: np.ndarray, y: np.ndarray) -> float
# Si None → comportement par default (MSE/corrélation hybride supervisé).
# Si fournie → REMPLACE entièrement le calcul d'erreur, et le linear scaling
# est ignoré (il suppose le MSE supervisé). Une valeur basse = meilleur.

# [CUSTOM-SEEDS] Liste optionnelle d'arbres Node injectés dans la population
# initiale (un par île, round-robin). Sert à amorcer la recherche avec des
# briques structurelles pertinentes (ex. X[0]², X[1]² pour une loi d'énergie).
# Rempli par l'API ; None/vide = pas d'amorçage custom.
def _safe_write(filepath, writer, what="file"):
    """[v0.2.2] An export must NEVER kill a finished run. Try the requested
    path, then the system temp directory; on total failure, warn and return
    None. Returns the path actually written, or None."""
    import tempfile, os as _os
    _err = None
    for target in (str(filepath),
                   _os.path.join(tempfile.gettempdir(),
                                 _os.path.basename(str(filepath)))):
        try:
            with open(target, "w", encoding="utf-8", newline="") as f:
                writer(f)
            if target != str(filepath):
                print(f"  ⚠ Could not write {what} to '{filepath}' — "
                      f"saved to '{target}' instead.")
            return target
        except OSError as e:
            _err = e
    print(f"  ⚠ {what} export skipped ({type(_err).__name__}: {_err}). "
          f"Hint: run from a writable folder — OneDrive / Windows "
          f"'Controlled Folder Access' can block Python writes.")
    return None
