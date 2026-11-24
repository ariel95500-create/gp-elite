"""The protected operators of the engine, scalar and vectorised: the
safe forms of the operations formulas use (division, power,
logarithm, square root, exponential, tangent, arcsine...).

Part of gp_elite/core.py until 1.4.0, moved without change in 1.5.
"""
from __future__ import annotations

import math
import numpy as np

# ============================================================
# OPÉRATIONS SÉCURISÉES — scalaires (utilisées par simplify/display)
# ============================================================

_SAFE_LIMIT = 1e6

def safe_div(a: float, b: float) -> float:
    return a if abs(b) < 1e-8 else a / b

def safe_pow(a: float, b: float) -> float:
    try:
        if abs(b) > 8:
            return 1.0
        r = pow(abs(a) + 1e-12, b)
        if not math.isfinite(r) or abs(r) > _SAFE_LIMIT:
            return 1.0
        return r
    except Exception:
        return 1.0

def safe_tan(x: float) -> float:
    try:
        r = math.tan(x)
        return 0.0 if not math.isfinite(r) or abs(r) > _SAFE_LIMIT else r
    except Exception:
        return 0.0

def safe_arcsin(x: float) -> float:
    """[1.3-A1] Arcsine of the argument clipped to [-1, 1] (its guard)."""
    try:
        return math.asin(min(max(x, -1.0), 1.0))
    except Exception:
        return 0.0

def safe_log(x: float) -> float:
    return math.log(abs(x) + 1e-12)

def safe_exp(x: float) -> float:
    try:
        r = math.exp(min(x, 20.0))
        return r if math.isfinite(r) else _SAFE_LIMIT
    except Exception:
        return 0.0

def safe_sqrt(x: float) -> float:
    return math.sqrt(abs(x))

# ============================================================
# OPÉRATIONS SÉCURISÉES — vectorisées NumPy
# ============================================================

# [v0.8] ufuncs appelés directement : np.clip passe par plusieurs couches
# Python (~3 µs par appel), ce qui dominait le coût des opérations protégées
# sur les petits jeux de données. min(max(a, lo), hi) donne exactement
# np.clip(a, lo, hi), NaN compris (propagé par np.maximum comme par np.clip).
_np_minimum = np.minimum
_np_maximum = np.maximum
_np_abs = np.abs
_np_isfinite = np.isfinite

def _np_safe_div(a, b):
    """
    Division protégée NumPy.
    [v16-FIX] np.where évalue les DEUX branches avant de choisir : si a/b déborde
    en float64 même quand |b|>1e-8, le RuntimeWarning est levé.
    Solution : clipper a en amont et remplacer b~0 par 1.0 avant la division.
    [v0.8] Mêmes valeurs, bit pour bit, que la version 0.7 (vérifié par
    tests/test_speed_equivalence.py) : bornes par np.minimum/np.maximum au
    lieu de np.clip (dont l'enveloppe Python coûtait plus que le calcul sur
    les petits jeux de données), masque calculé une fois, et division directe
    quand aucun dénominateur n'est proche de zéro (le cas courant). Sans
    dénominateur minuscule, |a| <= 1e6 et |b| >= 1e-8 : la division ne peut
    ni déborder ni lever d'avertissement.
    """
    a = _np_minimum(_np_maximum(a, -_SAFE_LIMIT), _SAFE_LIMIT)
    small = _np_abs(b) < 1e-8
    if small.any():
        with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
            r = np.where(small, a, a / np.where(small, 1.0, b))
    else:
        r = a / b
    return np.where(_np_isfinite(r), r, 0.0)

def _np_safe_pow(a, b):
    """
    Puissance sécurisée NumPy.
    [v16-FIX] errstate étendu à 'over' pour supprimer les overflow warnings.
    [V42-FIX] Clipping de la BASE en plus de l'exposant :
    Les features de trajectoire X[6]-X[9] peuvent atteindre ~7 (log1p de grandes
    valeurs), et sq(X[7]) ≈ 49 — pow(49, 8) = 1.9e13 qui déborde float32 dans
    certains contextes. On clippe la base à [-100, 100] avant la puissance.
    [v0.8] Exposant scalaire (le cas de la compilation : _safe_pow ne reçoit
    que des exposants constants) : une seule des deux branches est calculée,
    au lieu des deux puis d'un choix. Mêmes valeurs bit pour bit.
    """
    b = _np_minimum(_np_maximum(b, -6.0), 6.0)   # exposant limité : base^6 suffisant pour GP
    a = _np_minimum(_np_maximum(a, -100.0), 100.0)  # base clippée : évite pow(large, large)
    with np.errstate(all='ignore'):
        if np.ndim(b) == 0:
            b_int = np.round(b)
            if abs(b - b_int) < 1e-6:
                r = np.sign(a) * np.power(_np_abs(a) + 1e-12, _np_abs(b_int))
                if not b_int >= 0:
                    r = 1.0 / (_np_abs(r) + 1e-12) * np.sign(r)
            else:
                r = np.power(_np_abs(a) + 1e-12, b)
        else:
            b_int = np.round(b)
            is_int = np.abs(b - b_int) < 1e-6
            r_int  = np.sign(a) * np.power(np.abs(a) + 1e-12, np.abs(b_int))
            r_int  = np.where(b_int >= 0, r_int, 1.0 / (np.abs(r_int) + 1e-12) * np.sign(r_int))
            r_real = np.power(np.abs(a) + 1e-12, b)
            r = np.where(is_int, r_int, r_real)
    return np.where(_np_isfinite(r) & (_np_abs(r) < _SAFE_LIMIT), r, 1.0)

def _np_safe_pow_var(a, b):
    """[v0.7] Puissance a exposant VARIABLE : |a|^b sur toutes les lignes.

    La branche entiere de _np_safe_pow (sign(a)*|a|^n) sert aux exposants
    CONSTANTS (pow(u, 3) garde le signe de u). Appliquee ligne par ligne a un
    exposant variable, elle rendait la fonction discontinue : la ou
    l'exposant tombait exactement sur un entier, le resultat changeait de
    signe. Avec la division par max|x|, une colonne vaut exactement ±1 sur
    sa ligne extreme, donc le cas se produisait a coup sur ; la recherche
    pouvait s'en servir comme d'un indicateur de ligne, et aucune formule
    lisible ne reproduisait le modele (561_cpu standardise : formule et
    predict() en desaccord de 0.97 sur 2 lignes). Memes garde-fous que
    _np_safe_pow (exposant et base bornes, resultat non fini ou enorme -> 1).
    """
    b = _np_minimum(_np_maximum(b, -6.0), 6.0)
    a = _np_minimum(_np_maximum(a, -100.0), 100.0)
    with np.errstate(all='ignore'):
        r = np.power(_np_abs(a) + 1e-12, b)
    return np.where(_np_isfinite(r) & (_np_abs(r) < _SAFE_LIMIT), r, 1.0)

def _is_const_subtree(node) -> bool:
    """[v0.7] Vrai si le sous-arbre ne contient aucune variable (x, X[i]) :
    c'est lui qui decide de la semantique de pow (exposant constant :
    branche entiere signee ; exposant variable : |a|^b), a la compilation
    comme dans la formule livree (gp_elite/formula.py)."""
    if node is None:
        return True
    v = node.value
    if node.left is None and node.right is None:
        return not (v == "x" or (isinstance(v, str) and v.startswith("X[")))
    return _is_const_subtree(node.left) and _is_const_subtree(node.right)

def _np_safe_tan(a):
    with np.errstate(all='ignore'):
        r = np.tan(a)
    return np.where(np.isfinite(r) & (np.abs(r) < _SAFE_LIMIT), r, 0.0)

def _np_safe_arcsin(a):
    """[1.3-A1] Arcsine of the argument clipped to [-1, 1] (its guard); NaN
    stays NaN, as through the other clipped operators."""
    return np.arcsin(_np_minimum(_np_maximum(a, -1.0), 1.0))

def _np_safe_exp(a):
    """
    [v16-FIX] clip symétrique [-88, 88] : exp(88) ≈ 1.6e38 < float64 max.
    Remplace le clip asymétrique [-500, 20] qui sous-estimait des expressions
    comme exp(-X[:,0]²) sur des valeurs négatives légitimement grandes.
    """
    with np.errstate(over='ignore', invalid='ignore'):
        r = np.exp(_np_minimum(_np_maximum(a, -88.0), 88.0))
    return np.where(_np_isfinite(r), r, 0.0)

def _np_safe_log(a):
    return np.log(np.abs(a) + 1e-12)

def _np_safe_sqrt(a):
    return np.sqrt(np.abs(a))

def _np_is_even(a):
    """
    [SYRACUSE] Opérateur 'is_even' protégé — détecte la parité d'un nombre.
    Retourne +1.0 si round(a) est pair, -1.0 sinon.
    Ce signal binaire aide les îles à capter immédiatement la bifurcation
    structurelle n_pair → n/2  vs  n_impair → 3n+1 du problème de Collatz.
    Opère sur des valeurs réelles continues via arrondi à l'entier le plus proche.
    Robuste aux NaN/inf : remplacés par 0 avant le cast pour éviter le RuntimeWarning.
    """
    with np.errstate(invalid='ignore'):
        a_safe = np.where(np.isfinite(a), a, 0.0)
        a_clipped = np.clip(np.abs(a_safe), 0.0, 2.0e15)   # évite overflow int64
        a_int = np.round(a_clipped).astype(np.int64)
    return np.where(a_int % 2 == 0, 1.0, -1.0)


def _np_step(a):
    """
    [V42] Opérateur step — condition IF encodée de façon différentiable.
    Retourne 1.0 si a > 0, 0.0 sinon.

    Permet au GP d'écrire des conditions comme :
      step(X[8] - X[21]) = 1 si la trajectoire monte encore à l'étape 21
    Essentiel pour capter les bifurcations Collatz tardives (n=97, n=703).
    """
    return np.where(np.asarray(a) > 0.0, 1.0, 0.0)


def _np_max2(a, b):
    """[V42] max(a, b) — sélection de branche, condition IF binaire."""
    return np.maximum(np.asarray(a), np.asarray(b))


def _np_min2(a, b):
    """[V42] min(a, b) — sélection de branche, condition IF binaire."""
    return np.minimum(np.asarray(a), np.asarray(b))

# ============================================================
# COMPILATEUR ARBRE → FONCTION NUMPY
# ============================================================

_COMPILE_CACHE_MAX = 4096   # entrées max — élagage FIFO au-delà

_NP_GLOBALS = {
    "np":          np,
    "_safe_div":   _np_safe_div,
    "_safe_pow":   _np_safe_pow,
    "_safe_powv":  _np_safe_pow_var,   # [v0.7] exposant variable
    "_safe_tan":   _np_safe_tan,
    "_safe_arcsin": _np_safe_arcsin,  # [1.3-A1]
    "_safe_exp":   _np_safe_exp,
    "_safe_log":   _np_safe_log,
    "_safe_sqrt":  _np_safe_sqrt,
    "_is_even":    _np_is_even,   # [SYRACUSE] parité binaire protégée
    "_step":       _np_step,      # [V42] condition IF : 1 si a>0 else 0
    "_max2":       _np_max2,      # [V42] max(a, b) — sélection de branche
    "_min2":       _np_min2,      # [V42] min(a, b) — sélection de branche
}
