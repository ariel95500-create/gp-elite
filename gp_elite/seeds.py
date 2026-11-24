"""The seeds placed before the first generation: motifs, power laws,
binomial forms, elementary forms and noise-tolerant forms.

Part of gp_elite/core.py until 1.4.0, moved in 1.5, where it reads and
sets the names of the shared state in gp_elite.state (state.NAME).
"""
from __future__ import annotations

import math
import itertools
import random
import numpy as np
import time
from typing import Optional, List, Tuple, Dict, Any

from . import state
from .config import (TRACE, _dim_active, _ds)
from .tree import (Node, to_string)
from .evaluation import (evaluate_vector)
from .scoring import (_linear_scale_params)
from .final_choice import (_SMALL_FAMILY, _SMALL_FAMILY_KEEP,
                           _SMALL_FAMILY_SHARE, _lm_to_convergence)

# ════════════════════════════════════════════════════════════════
# [v28-MOTIFS] SEEDING DE MOTIFS DE COMPOSITION
# ════════════════════════════════════════════════════════════════
# Constat (banc Feynman v27) : les échecs restants sont des compositions à
# TREMPLIN — sqrt(sq(a−b)+sq(c−d)), 1/(1/a+1/b) — dont les sous-expressions
# intermédiaires ont une fitness médiocre : l'évolution ne les assemble pas.
# Remède éprouvé (AI Feynman, grammar seeding) : injecter dans la population
# initiale des INSTANCES de motifs physiques canoniques sur des variables
# tirées au hasard ; l'évolution recombine, LM ajuste les constantes. Le
# tirage dépend du seed du run → les restarts (v27) COUVRENT les appariements.

def _make_motif_seeds(cfg, n_max: int = 32) -> list:
    """Instancie des motifs de composition compatibles avec le pool actif."""
    terms = list(getattr(cfg, "TERMINALS", []) or [])
    if not terms:
        return []
    uops = set(getattr(state, '_GENERIC_UNARY_OPS', []) or [])
    rng = random.Random((getattr(cfg, "SEED", 0) or 0) ^ 0x0F1F2F)
    T = lambda: Node(rng.choice(terms))
    def T2():                                   # deux terminaux distincts si possible
        a = rng.choice(terms)
        b = rng.choice([t for t in terms if t != a] or terms)
        return Node(a), Node(b)
    C = lambda lo, hi: Node(round(rng.uniform(lo, hi), 4))
    inv = lambda x: Node('/', Node(1.0), x)
    diff = lambda: Node('-', *T2())
    out = []
    def add(f):
        try:
            nd = f()
            if nd is not None:
                out.append(nd)
        except Exception:
            pass
    builders = []
    if 'sqrt' in uops and 'sq' in uops:
        builders += [lambda: Node('sqrt', Node('+', Node('sq', diff()), Node('sq', diff()))),
                     lambda: Node('sqrt', Node('+', Node('sq', T()), Node('sq', T())))]
    builders += [lambda: inv(Node('+', inv(T()), inv(T()))),                  # 1/(1/a+1/b)
                 lambda: inv(Node('+', inv(T()), Node('*', T(), inv(T()))))]  # 1/(1/a+c/b)
    if 'exp' in uops and 'sq' in uops:
        builders += [lambda: Node('exp', Node('*', C(-1.5, -0.2), Node('sq', T())))]
    if 'log' in uops:
        builders += [lambda: Node('log', Node('/', *T2()))]
    if 'cos' in uops:
        builders += [lambda: Node('*', T(), Node('-', Node(1.0),
                                                 Node('cos', Node('*', *T2()))))]
    if 'sq' in uops:
        builders += [lambda: Node('sq', diff())]                              # brique
    builders += [lambda: Node('/', Node('+', *T2()), Node('+', Node(1.0), T())),
                 lambda: inv(T())]                                            # briques
    if not builders:
        return []
    k = 0
    while len(out) < n_max and k < n_max * 4:
        add(builders[k % len(builders)])
        k += 1
    return out[:n_max]


# ════════════════════════════════════════════════════════════════
# [v0.8] GRAINES DE LOI DE PUISSANCE
# ════════════════════════════════════════════════════════════════
# Constat (campagne 2 du banc de décision, 205 ajustements Feynman à 30 s) :
# des lois qui ne sont qu'un produit de puissances des variables, comme
# I.12.2 q1·q2/(4π·ε·r²), I.32.5 ou III.19.51, étaient retrouvées 1, 2 et 0
# fois sur 5 ; les autres ajustements rendaient des formules de 50 à 70
# nœuds. Or une loi y = c·Π x_j^a_j est une droite en échelle log :
# log|y| = log|c| + Σ a_j·log|x_j|. Quand la cible et des colonnes gardent
# un signe constant, les moindres carrés sur les logarithmes donnent les
# exposants, et la normalisation par max|x| ne les change pas. On place dans
# la population initiale le monôme aux exposants arrondis au demi-entier
# (la forme d'une loi physique usuelle) et, si le pool contient `pow`, le
# monôme aux exposants ajustés (loi empirique : Levenberg-Marquardt affine
# ensuite ces exposants), et seulement si les données sont bien celles d'une
# loi de puissance : le monôme doit expliquer au moins 99,9 % de la variance
# de log|y| (_POWER_LAW_MIN_R2). Ce ne sont que deux individus par île, parmi
# une centaine, jugés comme les autres. Aucun tirage aléatoire : sans colonne de signe
# constant ou avec une cible qui change de signe (données centrées), rien
# n'est injecté et l'ajustement est celui d'avant. Hors du mode CSV
# générique, sous `units=` (population typée ; voir _SEEDS_UNDER_UNITS
# ci-dessous, phase 7) et en mode extrapolation (où les motifs sont déjà
# coupés), rien n'est injecté non plus.

_POWER_LAW_MIN_R2 = 0.999    # part de la variance de log|y| que le monôme doit expliquer

# [1.1, phase 7] Sous units= (population typée), les quatre chercheurs de
# graines (loi de puissance, B1, E1, N1) ne rendaient rien. Avec ce drapeau, ils
# tournent comme sans unités, sur les mêmes lignes et avec les mêmes seuils,
# et chaque arbre rendu n'est gardé que s'il passe la porte de validité des
# dimensions (dim_search.is_typed_valid), celle de fitness() et des
# opérateurs typés : l'invariant des unités est inchangé. Sans unités, rien
# ne change. Plan : benchmarks/results_1.1/PLAN.md (changement U1, adopté le
# 26 octobre 2026) : banc U41 (les 41 équations du banc de décision avec leurs
# unités), lois exactes 107 -> 165 sur 205, puis 107 -> 166 sur des graines
# neuves ; structure sous bruit 79 -> 113 (1 %) et 80 -> 99 (10 %) ; chaque
# modèle rendu passe l'audit des unités ; données réelles sous unités
# inchangées. Actif par défaut depuis son adoption.


def _seeds_blocked_by_units(cfg) -> bool:
    """Vrai quand units= est actif et que U1 est coupé (comportement 1.0)."""
    return _dim_active(cfg) and not state._SEEDS_UNDER_UNITS


def _typed_seeds(seeds: list, cfg) -> list:
    """[1.1] Sous units=, les seules graines qui passent la porte des
    dimensions ; sans unités, toutes."""
    if not _dim_active(cfg) or not seeds:
        return seeds
    gate = _ds().is_typed_valid
    unk = bool(getattr(cfg, "UNKNOWN_CONST", False))
    kept = [t for t in seeds if gate(t, cfg.FEAT_DIMS, cfg.TARGET_DIM, unk)]
    if len(kept) < len(seeds):
        TRACE.bump("graines_rejetees_dim", len(seeds) - len(kept))
    return kept


def _power_law_exponents(X, y, min_r2=None):
    """Exposants (a_j) de |y| ≈ c·Π |x_j|^a_j par moindres carrés sur les
    logarithmes, pour les colonnes de signe constant. Rend (cols, a) ou
    None si la cible change de signe, si aucune colonne ne convient, si le
    système est dégénéré, ou si le monôme n'explique pas au moins 99,9 % de
    la variance de log|y|.

    [v0.8] Ce dernier seuil vient de la campagne 6 : sans lui, sur données
    réelles, un monôme ajusté à des données qui n'en sont pas un (228_elusage :
    X0^-3,38, R² log-log 0,81) gagnait la sélection et s'effondrait hors du
    domaine (R² -12). Les lois de Feynman qui sont des monômes ont un R²
    log-log de 1 ; les six jeux réels et nikuradse_1, 0,93 au plus."""
    n = y.shape[0]
    with np.errstate(all="ignore"):
        if not (np.all(np.isfinite(y)) and np.all(np.isfinite(X))):
            return None
        if not (np.all(y > 0) or np.all(y < 0)):
            return None
        cols = [j for j in range(X.shape[1])
                if np.all(X[:, j] > 0) or np.all(X[:, j] < 0)]
        if not cols or n < len(cols) + 3:
            return None
        A = np.column_stack([np.ones(n), np.log(np.abs(X[:, cols]))])
        try:
            coef, _res, rank, _sv = np.linalg.lstsq(A, np.log(np.abs(y)),
                                                    rcond=None)
        except Exception:
            return None
    if rank < A.shape[1] or not np.all(np.isfinite(coef)):
        return None
    ly = np.log(np.abs(y))
    v = float(np.var(ly))
    if not v > 0.0:
        return None
    with np.errstate(all="ignore"):
        r2 = 1.0 - float(np.var(ly - A @ coef)) / v
    if not r2 >= (_POWER_LAW_MIN_R2 if min_r2 is None else min_r2):
        return None
    return cols, coef[1:]


def _power_law_exponents_w(X, y):
    """[1.4-N2] Les exposants de _power_law_exponents pour la seconde passe
    des graines tolérantes au bruit : moindres carrés sur les logarithmes
    pondérés par y², sans la condition de signe constant de la cible et sans
    seuil sur R². Un bruit de taille constante σ déplace log|y| de σ/|y| :
    le poids y² est celui qu'un tel bruit demande, et les lignes proches de
    zéro, où le bruit change le signe, ne pèsent presque rien. Les lignes où
    y est nul n'ont ni logarithme ni poids : elles sont écartées."""
    with np.errstate(all="ignore"):
        if not (np.all(np.isfinite(y)) and np.all(np.isfinite(X))):
            return None
        keep = y != 0
        m = int(keep.sum())
        cols = [j for j in range(X.shape[1])
                if np.all(X[:, j] > 0) or np.all(X[:, j] < 0)]
        if not cols or m < len(cols) + 3:
            return None
        ay = np.abs(y[keep])
        sw = ay / float(ay.max())
        A = np.column_stack([np.ones(m), np.log(np.abs(X[keep][:, cols]))])
        try:
            coef, _res, rank, _sv = np.linalg.lstsq(A * sw[:, None],
                                                    np.log(ay) * sw, rcond=None)
        except Exception:
            return None
    if rank < A.shape[1] or not np.all(np.isfinite(coef)):
        return None
    return cols, coef[1:]


def _half_integer_power(term: str, e2: int, uops) -> Optional["Node"]:
    """x^(e2/2) pour e2 > 0, avec les seuls opérateurs du pool (sq, cube,
    sqrt, *). None si une racine est nécessaire et que sqrt manque."""
    n_int, half = divmod(e2, 2)

    def ipow(k: int) -> "Node":
        if k == 1:
            return Node(term)
        if k == 3 and "cube" in uops:
            return Node("cube", Node(term))
        if k % 2 == 0:
            h = ipow(k // 2)
            return Node("sq", h) if "sq" in uops else Node("*", h, ipow(k // 2))
        return Node("*", Node(term), ipow(k - 1))

    factors = []
    if n_int:
        factors.append(ipow(n_int))
    if half:
        if "sqrt" not in uops:
            return None
        factors.append(Node("sqrt", Node(term)))
    out = factors[0]
    for f in factors[1:]:
        out = Node("*", out, f)
    return out


def _product(nodes: list) -> Optional["Node"]:
    if not nodes:
        return None
    out = nodes[0]
    for f in nodes[1:]:
        out = Node("*", out, f)
    return out


def _make_power_law_seeds(xs, ys, cfg, min_r2=None, weighted=False) -> list:
    """[v0.8] Voir le commentaire ci-dessus. Rend 0, 1 ou 2 arbres. min_r2
    remplace _POWER_LAW_MIN_R2 (graines tolérantes au bruit, phase 5).
    [1.4-N2] weighted : la seconde passe de ces graines
    (_power_law_exponents_w)."""
    if not state._GENERIC_CSV_MODE or _seeds_blocked_by_units(cfg) \
            or bool(getattr(cfg, "EXTRAPOLATION_MODE", False)) \
            or not bool(getattr(cfg, "POWER_LAW_SEEDS", True)):
        return []
    terms = list(getattr(cfg, "TERMINALS", []) or [])
    try:
        X = np.asarray(xs, dtype=float)
        y = np.asarray(ys, dtype=float)
    except Exception:
        return []
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    if X.ndim != 2 or y.ndim != 1 or X.shape[0] != y.shape[0] \
            or X.shape[1] != len(terms):
        return []
    fit = (_power_law_exponents_w(X, y) if weighted
           else _power_law_exponents(X, y, min_r2))
    if fit is None:
        return []
    cols, expo = fit
    bops = set(state._GENERIC_BINARY_OPS)
    uops = set(state._GENERIC_UNARY_OPS)
    seeds = []

    # 1) exposants arrondis au demi-entier le plus proche
    e2s = [int(round(2.0 * float(a))) for a in expo]
    if all(abs(e2) <= 12 for e2 in e2s) and any(e2s):
        num, den, ok = [], [], True
        for j, e2 in zip(cols, e2s):
            if e2 == 0:
                continue
            f = _half_integer_power(terms[j], abs(e2), uops)
            if f is None:
                ok = False
                break
            (num if e2 > 0 else den).append(f)
        if ok and (not den or "/" in bops):
            top, bot = _product(num), _product(den)
            if bot is None:
                seeds.append(top)
            else:
                seeds.append(Node("/", top if top is not None else Node(1.0), bot))

    # 2) exposants ajustés, si le pool a pow et qu'ils ne sont pas déjà
    #    des demi-entiers (sinon la graine 1 les contient)
    # [1.1, U2] Sous units=, seulement sans unités fractionnaires : un exposant
    # ajusté qui n'est pas un demi-entier doit porter sur une entrée sans
    # dimension. Sinon (pow(n, 1.0041) en moles), la graine ne passe la porte
    # que par la constante inconnue, et ses descendants font chercher au
    # constructeur typé des sous-arbres d'unités fractionnaires, qu'il atteint
    # rarement : la loi des gaz du notebook de TP passait de 50 s à 78 s
    # (benchmarks/results_1.1/PLAN_U2.md).
    def _fractional_units(j, a):
        if not _dim_active(cfg) or abs(2.0 * a - round(2.0 * a)) <= 0.04:
            return False
        d = (cfg.FEAT_DIMS or {}).get(j) or {}
        return any(abs(float(v)) > 1e-12 for v in d.values())

    if "pow" in bops and float(np.max(np.abs(2.0 * expo - np.round(2.0 * expo)))) > 0.04:
        facs = [Node("pow", Node(terms[j]), Node(round(float(a), 4)))
                for j, a in zip(cols, expo) if abs(float(a)) >= 0.02]
        if facs and not any(_fractional_units(j, float(a)) for j, a in zip(cols, expo)
                            if abs(float(a)) >= 0.02):
            seeds.append(_product(facs))

    seeds = _typed_seeds(seeds, cfg)
    if seeds:
        TRACE.set("power_law_seed", "exposants %s ; %d graine(s) : %s" % (
            ", ".join("%s^%.3g" % (terms[j], float(a)) for j, a in zip(cols, expo)),
            len(seeds), " | ".join(to_string(s) for s in seeds)))
    return seeds


# ════════════════════════════════════════════════════════════════
# [0.10, phase 4b] GRAINES « MONÔME FOIS PUISSANCE D'UN BINÔME »
# ════════════════════════════════════════════════════════════════
# Constat (base de la 0.8.0, banc de décision) : les familles rationnelle et
# racine ne sont jamais retrouvées (0 sur 40 ajustements), alors que leurs
# lois ont une forme commune, y = b·f·(1 + c·g)^p, f et g des monômes des
# variables, p dans {-1, -1/2, 1/2, 1} : om0/(1 - v/c), m/sqrt(1 - v²/c²),
# sqrt(om²/c² - pi²/d²). Le binôme connu, c'est une droite en échelle log :
# log|y| - p·log(1 + c·g) = log|b| + Σ e_j·log|x_j|. Pour chaque monôme g
# d'une à trois colonnes (exposants -2, -1, 1, 2), c se cherche sur une
# dimension et les exposants de f suivent par moindres carrés, comme les
# graines de loi de puissance. La forme n'est injectée que si elle tient à la
# précision numérique (variance résiduelle de log|y| sous 1e-12 de sa
# variance, exposants arrondis) : sur des données qui ne suivent pas une telle
# loi exactement, données réelles et bruitées comprises, rien n'est injecté
# et l'ajustement est celui d'avant. Aucun tirage aléatoire. Mêmes gardes que
# les graines de loi de puissance. Mesuré dans benchmarks/results_0.9/
# PLAN_PHASE4.md (changement B1, adopté le 12 octobre 2026) : banc de
# décision, lois exactes 86 -> 124 sur 205 (familles rationnelle et racine
# 0 -> 35 sur 90), puis 86 -> 126 sur des graines neuves ; données réelles
# inchangées (aucune graine injectée sur les 260 ajustements réels).

_BINOM_EXPS = (-2, -1, 1, 2)          # exposants des colonnes dans g
_BINOM_TOL = 1e-12                    # variance résiduelle de log t, relative
_POWER_TOL = 1e-12                    # celle qui reconnaît une loi de puissance
_BINOM_MAX_LIB = 4096                 # monômes g essayés au plus
_BINOM_GRID_ROWS = 64                 # lignes du tri initial sur la grille
_BINOM_GRID = np.array(sorted(set(
    [float(v) for v in -1.0 + np.geomspace(1e-3, 1.0, 12)[:-1]]
    + [-0.5, -0.3, -0.1, -0.03, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0])))


def _binom_library(cols, n_max):
    """Monômes g : tuples ((colonne, exposant), ...) d'une à n_max colonnes.
    None au-delà de _BINOM_MAX_LIB."""
    lib = []
    for r in range(1, n_max + 1):
        for js in itertools.combinations(cols, r):
            for es in itertools.product(_BINOM_EXPS, repeat=r):
                lib.append(tuple(zip(js, es)))
                if len(lib) > _BINOM_MAX_LIB:
                    return None
    return lib


def _golden_min(f, a, b, it=60):
    """Minimum de f sur [a, b] par la section dorée : (x, f(x))."""
    gr = (math.sqrt(5.0) - 1.0) / 2.0
    c1, c2 = b - gr * (b - a), a + gr * (b - a)
    f1, f2 = f(c1), f(c2)
    for _ in range(it):
        if f1 < f2:
            b, c2, f2 = c2, c1, f1
            c1 = b - gr * (b - a)
            f1 = f(c1)
        else:
            a, c1, f1 = c1, c2, f2
            c2 = a + gr * (b - a)
            f2 = f(c2)
    return (c1, f1) if f1 < f2 else (c2, f2)


def _binomial_forms(X, y, top: int = 8, tol=None, weighted=False) -> list:
    """Formes y = b·f·(1 + c·g)^p qui tiennent à la précision numérique.
    Rend une liste de (p, cols, exposants de f dans y, g, c). tol remplace
    _BINOM_TOL (graines tolérantes au bruit, phase 5).

    [1.4-N2] weighted : la seconde passe des graines tolérantes au bruit. Les
    moindres carrés sur les logarithmes sont pondérés par y² (voir
    _power_law_exponents_w) et la cible n'a plus à garder un signe ; les
    lignes où y est nul sont écartées. Sans weighted, les calculs sont ceux
    d'avant, opération pour opération."""
    tol = _BINOM_TOL if tol is None else tol
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    out = []
    with np.errstate(all="ignore"):
        if not (np.all(np.isfinite(y)) and np.all(np.isfinite(X))):
            return out
        if weighted:
            nzr = y != 0
            X, y = X[nzr], y[nzr]
            if not y.shape[0]:
                return out
        elif not (np.all(y > 0) or np.all(y < 0)):
            return out
        n = y.shape[0]
        cols = [j for j in range(X.shape[1])
                if np.all(X[:, j] > 0) or np.all(X[:, j] < 0)]
        if not cols or n < len(cols) + 6:
            return out
        lib = _binom_library(cols, 3 if len(cols) <= 6 else 2)
        if lib is None:
            return out
        LU = np.log(np.abs(X[:, cols]))
        L = np.column_stack([np.ones(n), LU])
        sub = np.unique(np.linspace(0, n - 1, min(n, _BINOM_GRID_ROWS)).astype(int))
        if weighted:
            sw = np.abs(y) / float(np.max(np.abs(y)))
            Lw = L * sw[:, None]
            Q, Rr = np.linalg.qr(Lw)
            Qs = np.linalg.qr(Lw[sub])[0]
            sws = sw[sub]
            un = sw / float(np.linalg.norm(sw))

            def rvar(z):                  # carré moyen du résidu pondéré
                zw = z * sw
                r_ = zw - Q @ (Q.T @ zw)
                return float(np.mean(r_ * r_))

            def rvar_sub(Z):
                Zw = Z * sws[:, None]
                R_ = Zw - Qs @ (Qs.T @ Zw)
                return np.mean(R_ * R_, axis=0)

            def wvar(z):                  # variance pondérée
                zw = z * sw
                r_ = zw - un * float(un @ zw)
                return float(np.mean(r_ * r_))

            def lsq(z):
                return np.linalg.lstsq(Lw, z * sw, rcond=None)[0]
        else:
            Q, Rr = np.linalg.qr(L)
            Qs = np.linalg.qr(L[sub])[0]

            def rvar(z):
                return float(np.var(z - Q @ (Q.T @ z)))

            def rvar_sub(Z):
                return np.var(Z - Qs @ (Qs.T @ Z), axis=0)

            def wvar(z):
                return float(np.var(z))

            def lsq(z):
                return np.linalg.lstsq(L, z, rcond=None)[0]
        dR = np.abs(np.diag(Rr))
        if not np.min(dR) > 1e-10 * np.max(dR):
            return out
        pos = {j: i for i, j in enumerate(cols)}
        E = np.zeros((len(cols), len(lib)))
        sg = np.ones(len(lib))
        for m, g in enumerate(lib):
            for j, e in g:
                E[pos[j], m] = e
                if X[0, j] < 0 and e % 2:
                    sg[m] = -sg[m]
        LG = LU @ E
        lgmax = np.max(LG, axis=0)
        GN = np.exp(LG - lgmax)                   # |g| / max|g|, dans (0, 1]
        GNs = GN[sub]
        for k in (1, 2):                          # t = |y|^k
            lt = k * np.log(np.abs(y))
            vt = wvar(lt)
            if not vt > 0.0:
                continue
            if rvar(lt) / vt < _POWER_TOL:
                continue                          # une loi de puissance
            lts = lt[sub]
            for sig in (-1.0, 1.0):               # t = f·(1 + c·g)^(-sig)
                best = np.full(len(lib), np.inf)
                for s in _BINOM_GRID:
                    W = 1.0 + s * GNs
                    ok = np.all(W > 0, axis=0)
                    Z = lts[:, None] + sig * np.log(np.where(W > 0, W, 1.0))
                    v = rvar_sub(Z)
                    v[~ok] = np.inf
                    best = np.minimum(best, v)
                found = None
                for m in np.argsort(best, kind="stable")[:top]:
                    if not np.isfinite(best[m]):
                        break
                    gn = GN[:, m]

                    def obj(s, gn=gn):
                        w = 1.0 + s * gn
                        if np.any(w <= 0):
                            return np.inf
                        z = lt + sig * np.log(w)
                        return rvar(z)
                    vals = [obj(s) for s in _BINOM_GRID]
                    i = int(np.argmin(vals))
                    a = _BINOM_GRID[i - 1] if i > 0 else -1.0 + 1e-9
                    b = _BINOM_GRID[i + 1] if i + 1 < len(_BINOM_GRID) else 100.0
                    s, v = _golden_min(obj, float(a), float(b))
                    if v / vt < tol and (found is None or v < found[0]):
                        found = (v, int(m), s)
                if found is None:
                    continue
                _v, m, s = found
                gn = GN[:, m]
                z = lt + sig * np.log(1.0 + s * gn)
                coef = lsq(z)[1:]
                step = 2.0 if k == 1 else 1.0     # demi-entiers dans y
                ex = np.round(coef * step) / step
                if not np.all(np.abs(ex) <= 6.0 * k):
                    continue
                base = lt - LU @ ex

                def obj2(s2):
                    w2 = 1.0 + s2 * gn
                    if np.any(w2 <= 0):
                        return np.inf
                    return wvar(base + sig * np.log(w2))
                h = 0.05 * (1.0 + abs(s))
                s2, v2 = _golden_min(obj2, s - h, s + h)
                if not v2 / vt < tol:
                    continue
                c = float(sg[m] * s2 / math.exp(lgmax[m]))
                out.append((-sig / k, cols, ex / k, lib[m], c))
    return out


def _monomial(terms, pairs, uops) -> Optional["Node"]:
    """Π terms[j]^e (e demi-entiers, non nuls) avec les opérateurs du pool ;
    None si une racine manque."""
    num, den = [], []
    for j, e in pairs:
        f = _half_integer_power(terms[j], int(round(2.0 * abs(e))), uops)
        if f is None:
            return None
        (num if e > 0 else den).append(f)
    top, bot = _product(num), _product(den)
    if bot is None:
        return top
    return Node("/", top if top is not None else Node(1.0), bot)


def _make_binomial_seeds(xs, ys, cfg, tol=None, weighted=False) -> list:
    """[0.10, phase 4b] Voir le commentaire ci-dessus. Rend 0 à 4 arbres.
    Le drapeau _BINOMIAL_SEEDS (actif par défaut) les coupe. [1.4-N2]
    weighted : la seconde passe des graines tolérantes au bruit."""
    if not state._BINOMIAL_SEEDS or not state._GENERIC_CSV_MODE or _seeds_blocked_by_units(cfg) \
            or bool(getattr(cfg, "EXTRAPOLATION_MODE", False)):
        return []
    terms = list(getattr(cfg, "TERMINALS", []) or [])
    try:
        X = np.asarray(xs, dtype=float)
        y = np.asarray(ys, dtype=float)
    except Exception:
        return []
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    if X.ndim != 2 or y.ndim != 1 or X.shape[0] != y.shape[0] \
            or X.shape[1] != len(terms):
        return []
    t0 = time.time()
    forms = _binomial_forms(X, y, tol=tol, weighted=weighted)
    TRACE.set("binomial_seed_s", round(time.time() - t0, 3))
    bops = set(state._GENERIC_BINARY_OPS)
    uops = set(state._GENERIC_UNARY_OPS)
    if not {"+", "*", "/"} <= bops:
        return []
    seeds = []
    for p, cols, ex, g, c in forms:
        f = _monomial(terms, [(j, float(e)) for j, e in zip(cols, ex) if e != 0],
                      uops)
        gnode = _monomial(terms, [(j, float(e)) for j, e in g], uops)
        if gnode is None or (abs(p) == 0.5 and "sqrt" not in uops):
            continue
        w = Node("+", Node(1.0), Node("*", Node(c), gnode))
        if abs(p) == 0.5:
            w = Node("sqrt", w)
        if p < 0:
            seeds.append(Node("/", f if f is not None else Node(1.0), w))
        else:
            seeds.append(w if f is None else Node("*", f, w))
    seeds = _typed_seeds(seeds, cfg)
    if seeds:
        TRACE.set("binomial_seed", " | ".join(to_string(s) for s in seeds))
    return seeds


# ════════════════════════════════════════════════════════════════
# [0.10, phase 4a] GRAINES « FONCTION D'UN MONÔME », TENUES EXACTEMENT
# ════════════════════════════════════════════════════════════════
# Même principe que les graines binomiales, pour les fonctions élémentaires :
#   y = b·f·exp(c·g), b·f·log(c·g), b·f·tanh(c·g), b·f/cosh(c·g)
#   y = f·(a + β·sin(ω·g) + γ·cos(ω·g))
#   [1.3-A3] y = b·f·arcsin(c·g), là où le pool a l'arc sinus (trig, full) ;
#   inversée comme tanh, b au moins 2/π fois le plus grand |y/f|
# f et g des monômes. Pour les quatre premières, la fonction inversée rend
# une loi de puissance des entrées (une constante cherchée sur une dimension,
# aucune pour le logarithme) ; pour la forme trigonométrique, ω se cherche
# sur une grille, a, β, γ par moindres carrés, et les exposants de f par
# moindres carrés sur les logarithmes, arrondis. Une forme n'est injectée
# que si elle tient à la précision numérique, exposants arrondis : sur des
# données qui ne suivent pas une telle loi exactement, rien n'est injecté et
# l'ajustement est celui d'avant. Aucun tirage aléatoire. Mêmes gardes que
# les graines binomiales. Mesuré dans benchmarks/results_0.9/PLAN_PHASE4.md
# (changement E1, adopté le 12 octobre 2026) : banc de décision avec B1,
# lois exactes 124 -> 157 sur 205 (familles à zéro 35 -> 55 sur 90), puis
# 126 -> 155 sur des graines neuves ; données réelles inchangées (aucune
# graine injectée sur les 520 ajustements réels, pool par défaut et "trig").

_ELEM_MAX_LIB = 4096                  # monômes f (ou g trigonométriques) au plus
_ELEM_S_GRID = np.linspace(-6.0, 3.0, 37)
_ELEM_W_GRID = np.linspace(0.05, 40.0, 800)
_ELEM_TRIG_GATE = 0.05                # résidu de grille sous lequel on affine


def _elem_flib(cols):
    """Monômes f : 1, une colonne (±1, ±2), deux ou trois colonnes (±1 ;
    trois seulement jusqu'à huit colonnes). None au-delà de _ELEM_MAX_LIB."""
    lib = [()]
    for j in cols:
        for e in (-2, -1, 1, 2):
            lib.append(((j, e),))
    for r in ((2, 3) if len(cols) <= 8 else (2,)):
        for js in itertools.combinations(cols, r):
            for es in itertools.product((-1, 1), repeat=r):
                lib.append(tuple(zip(js, es)))
                if len(lib) > _ELEM_MAX_LIB:
                    return None
    return lib


def _elem_mono(X, m):
    v = np.ones(X.shape[0])
    for j, e in m:
        v = v * X[:, j] ** e
    return v


def _elem_rel(Z, Q):
    """Variance résiduelle relative de chaque colonne de Z après projection
    sur l'espace de Q."""
    V = np.var(Z, axis=0)
    R = Z - Q @ (Q.T @ Z)
    with np.errstate(all="ignore"):
        out = np.var(R, axis=0) / V
    return np.where(V > 0, out, np.inf)


def _elem_transform(kind, R, s):
    """Transformée colonne par colonne qui est une loi de puissance des
    entrées quand la forme tient (NaN là où elle n'est pas définie)."""
    if kind == "exp-":                    # w - a > 0, a = min(w) - étendue·10^s
        W = np.log(np.abs(R))
        return np.log(W - (W.min(axis=0) - np.ptp(W, axis=0) * 10.0 ** s))
    if kind == "exp+":                    # a - w > 0, a = max(w) + étendue·10^s
        W = np.log(np.abs(R))
        return np.log((W.max(axis=0) + np.ptp(W, axis=0) * 10.0 ** s) - W)
    A = np.abs(R)
    mx = A.max(axis=0)
    if kind == "tanh":
        return np.log(np.arctanh(A / (mx * (1.0 + 10.0 ** s))))
    if kind == "arcsin":                  # [1.3-A3] |arcsin| <= pi/2 : b >= (2/pi) max
        return np.log(np.sin(A / (mx * (2.0 / math.pi) * (1.0 + 10.0 ** s))))
    return np.log(np.arccosh(mx * (1.0 + 10.0 ** s) / A))      # "sech"


def _elem_inverse_forms(X, y, cols, kinds, top: int = 6, tol=_BINOM_TOL) -> list:
    """Formes y = b·f·φ(c·g), φ dans exp, log, tanh, 1/cosh. Rend des
    tuples (kind, f, g, c), exposants de g arrondis au demi-entier."""
    n = y.shape[0]
    out = []
    lib = _elem_flib(cols)
    if lib is None:
        return out
    FV = np.column_stack([_elem_mono(X, m) for m in lib])
    R = y[:, None] / FV
    ok = np.all(R > 0, axis=0) | np.all(R < 0, axis=0)
    idx = np.where(ok)[0]
    if not idx.size:
        return out
    R = R[:, idx]
    LU = np.log(np.abs(X[:, cols]))
    L = np.column_stack([np.ones(n), LU])
    Q = np.linalg.qr(L)[0]
    sub = np.unique(np.linspace(0, n - 1, min(n, _BINOM_GRID_ROWS)).astype(int))
    Qs = np.linalg.qr(L[sub])[0]

    def g_of(coef):
        """Exposants de g arrondis (demi-entiers), None si tous nuls."""
        ex = np.round(2.0 * coef) / 2.0
        if not np.any(ex) or not np.all(np.abs(ex) <= 6.0):
            return None
        return tuple((j, float(e)) for j, e in zip(cols, ex) if e)

    if "log" in kinds:                    # r = a + Σ e_j·log|u_j|, linéaire
        v = _elem_rel(R, Q)
        for m in np.where(v < tol)[0]:
            r = R[:, m]
            coef = np.linalg.lstsq(L, r, rcond=None)[0][1:]
            nzc = np.abs(coef)[np.abs(coef) > 1e-6]
            if not nzc.size:
                continue
            g = g_of(coef / float(nzc.min()))
            if g is None:
                continue
            lg = np.log(np.abs(_elem_mono(X, g)))
            A = np.column_stack([np.ones(n), lg])
            a0, s0 = np.linalg.lstsq(A, r, rcond=None)[0]
            if not (float(np.var(r - A @ np.array([a0, s0]))) / float(np.var(r))
                    < tol) or s0 == 0.0 or abs(a0 / s0) > 700.0:
                continue
            out.append(("log", lib[idx[m]], g, float(math.exp(a0 / s0))))
            break
    for kind in [k for k in ("exp-", "exp+", "tanh", "sech", "arcsin")
                 if k.rstrip("+-") in kinds]:
        best = np.full(R.shape[1], np.inf)
        with np.errstate(all="ignore"):
            for s in _ELEM_S_GRID:
                T = _elem_transform(kind, R[sub], s)
                fin = np.all(np.isfinite(T), axis=0)
                v = _elem_rel(np.where(np.isfinite(T), T, 0.0), Qs)
                v[~fin] = np.inf
                best = np.minimum(best, v)
        order = [int(m) for m in np.argsort(best, kind="stable")[:top]]
        if kind == "arcsin":
            # [1.3-A3] La forme simple y = b·arcsin(c·g) (f = 1) est toujours
            # essayée, la première : arcsin(x) est proche de x pour un petit
            # argument, et sur la grille grossière d'autres f peuvent la
            # devancer (7e sur une loi arcsin(0,7·x0/(x1·x2))).
            j0 = np.where(idx == 0)[0]
            if j0.size and np.isfinite(best[j0[0]]):
                order = [int(j0[0])] + [m for m in order if m != j0[0]]
        for m in order:
            if not np.isfinite(best[m]):
                break
            r = R[:, [m]]

            def obj(s, r=r):
                with np.errstate(all="ignore"):
                    t = _elem_transform(kind, r, s)[:, 0]
                if not np.all(np.isfinite(t)):
                    return np.inf
                return float(_elem_rel(t[:, None], Q)[0])
            vals = [obj(s) for s in _ELEM_S_GRID]
            i = int(np.argmin(vals))
            if i in (0, len(_ELEM_S_GRID) - 1):
                continue                  # limite dégénérée de la forme
            s, v = _golden_min(obj, float(_ELEM_S_GRID[i - 1]),
                               float(_ELEM_S_GRID[i + 1]))
            if not v < tol:
                continue
            with np.errstate(all="ignore"):
                t = _elem_transform(kind, r, s)[:, 0]
            g = g_of(np.linalg.lstsq(L, t, rcond=None)[0][1:])
            if g is None:
                continue
            lg = np.log(np.abs(_elem_mono(X, g)))

            def obj2(s2, r=r, lg=lg):
                with np.errstate(all="ignore"):
                    t2 = _elem_transform(kind, r, s2)[:, 0] - lg
                if not np.all(np.isfinite(t2)):
                    return np.inf
                vt = float(np.var(t2 + lg))
                return float(np.var(t2)) / vt if vt > 0 else np.inf
            s2, v2 = _golden_min(obj2, s - 0.5, s + 0.5)
            if not v2 < tol:
                continue
            with np.errstate(all="ignore"):
                k0 = float(np.mean(_elem_transform(kind, r, s2)[:, 0] - lg))
            if abs(k0) > 700.0:
                continue
            c = math.exp(k0) * (-1.0 if kind == "exp+" else 1.0)
            out.append((kind.rstrip("+-"), lib[idx[m]], g, c))
            break
    return out


def _elem_wrel(Z, Q, w):
    """[1.4-N2] _elem_rel pondérée : variance résiduelle relative de chaque
    colonne de Z, les lignes pesant w² (Q : base orthonormée de l'espace
    pondéré, w·[1, log|x_j|]). La variance de référence est celle du résidu
    sur la constante pondérée."""
    Zw = Z * w[:, None]
    Rz = Zw - Q @ (Q.T @ Zw)
    u = w / float(np.linalg.norm(w))
    Cz = Zw - u[:, None] * (u @ Zw)[None, :]
    V = np.mean(Cz * Cz, axis=0)
    with np.errstate(all="ignore"):
        out = np.mean(Rz * Rz, axis=0) / V
    return np.where(V > 0, out, np.inf)


def _log_g_exponents(coef):
    """[1.4-N2] Exposants de g de la forme y = b·f·log(c·g), pour les graines
    tolérantes au bruit : les coefficients de y/f sur les log|x_j| valent
    b·e_j. Les chercheurs exacts les rapportent au plus petit coefficient
    non nul (au-dessus de 1e-6) ; sous bruit, un exposant nul a un
    coefficient de l'ordre du bruit, qui devient ce dénominateur (sur une
    loi n·log(V2/V1) à 1 % de bruit, les exposants 564 et -566 au lieu de 1
    et -1). Ici un coefficient compte comme nul sous le douzième du plus
    grand : les exposants gardés, des demi-entiers d'au plus 6 rapportés au
    plus petit, ne descendent pas sous le sixième. None si aucun ne reste."""
    a = np.abs(coef)
    if not a.size or not float(a.max()) > 1e-6:
        return None
    c = np.where(a > float(a.max()) / 12.0, coef, 0.0)
    ex = np.round(2.0 * c / float(np.min(np.abs(c[c != 0])))) / 2.0
    if not np.any(ex) or not np.all(np.abs(ex) <= 6.0):
        return None
    return ex


def _elem_inverse_forms_w(X, y, cols, kinds, top: int = 6, tol=_BINOM_TOL) -> list:
    """[1.4-N2] La seconde passe de _elem_inverse_forms, pour les graines
    tolérantes au bruit : la cible n'a plus à garder un signe (|y/f| est
    transformé), et les moindres carrés sur les transformées logarithmiques
    sont pondérés par y² (voir _power_law_exponents_w). La forme du
    logarithme, dont les moindres carrés portent sur y/f et non sur un
    logarithme de la cible, garde les siens, sans la condition de signe.
    y n'a pas de zéro (écartés par _elementary_forms)."""
    n = y.shape[0]
    out = []
    lib = _elem_flib(cols)
    if lib is None:
        return out
    FV = np.column_stack([_elem_mono(X, m) for m in lib])
    R = y[:, None] / FV
    idx = np.where(np.all(np.isfinite(R), axis=0) & np.all(R != 0, axis=0))[0]
    if not idx.size:
        return out
    R = R[:, idx]
    LU = np.log(np.abs(X[:, cols]))
    L = np.column_stack([np.ones(n), LU])
    sub = np.unique(np.linspace(0, n - 1, min(n, _BINOM_GRID_ROWS)).astype(int))
    sw = np.abs(y) / float(np.max(np.abs(y)))
    Lw = L * sw[:, None]
    Qw = np.linalg.qr(Lw)[0]
    Qws = np.linalg.qr(Lw[sub])[0]
    sws = sw[sub]
    ww = sw * sw

    def g_of(coef):
        ex = np.round(2.0 * coef) / 2.0
        if not np.any(ex) or not np.all(np.abs(ex) <= 6.0):
            return None
        return tuple((j, float(e)) for j, e in zip(cols, ex) if e)

    if "log" in kinds:                    # comme _elem_inverse_forms, les
        Q = np.linalg.qr(L)[0]            # exposants de g par _log_g_exponents
        v = _elem_rel(R, Q)
        for m in np.where(v < tol)[0]:
            r = R[:, m]
            ex = _log_g_exponents(np.linalg.lstsq(L, r, rcond=None)[0][1:])
            if ex is None:
                continue
            g = tuple((j, float(e)) for j, e in zip(cols, ex) if e)
            lg = np.log(np.abs(_elem_mono(X, g)))
            A = np.column_stack([np.ones(n), lg])
            a0, s0 = np.linalg.lstsq(A, r, rcond=None)[0]
            if not (float(np.var(r - A @ np.array([a0, s0]))) / float(np.var(r))
                    < tol) or s0 == 0.0 or abs(a0 / s0) > 700.0:
                continue
            out.append(("log", lib[idx[m]], g, float(math.exp(a0 / s0))))
            break
    for kind in [k for k in ("exp-", "exp+", "tanh", "sech", "arcsin")
                 if k.rstrip("+-") in kinds]:
        best = np.full(R.shape[1], np.inf)
        with np.errstate(all="ignore"):
            for s in _ELEM_S_GRID:
                T = _elem_transform(kind, R[sub], s)
                fin = np.all(np.isfinite(T), axis=0)
                v = _elem_wrel(np.where(np.isfinite(T), T, 0.0), Qws, sws)
                v[~fin] = np.inf
                best = np.minimum(best, v)
        order = [int(m) for m in np.argsort(best, kind="stable")[:top]]
        if kind == "arcsin":
            j0 = np.where(idx == 0)[0]
            if j0.size and np.isfinite(best[j0[0]]):
                order = [int(j0[0])] + [m for m in order if m != j0[0]]
        for m in order:
            if not np.isfinite(best[m]):
                break
            r = R[:, [m]]

            def obj(s, r=r):
                with np.errstate(all="ignore"):
                    t = _elem_transform(kind, r, s)[:, 0]
                if not np.all(np.isfinite(t)):
                    return np.inf
                return float(_elem_wrel(t[:, None], Qw, sw)[0])
            vals = [obj(s) for s in _ELEM_S_GRID]
            i = int(np.argmin(vals))
            if i in (0, len(_ELEM_S_GRID) - 1):
                continue
            s, v = _golden_min(obj, float(_ELEM_S_GRID[i - 1]),
                               float(_ELEM_S_GRID[i + 1]))
            if not v < tol:
                continue
            with np.errstate(all="ignore"):
                t = _elem_transform(kind, r, s)[:, 0]
            g = g_of(np.linalg.lstsq(Lw, t * sw, rcond=None)[0][1:])
            if g is None:
                continue
            lg = np.log(np.abs(_elem_mono(X, g)))

            def wvar(z):
                mu = float(np.sum(ww * z) / np.sum(ww))
                return float(np.sum(ww * (z - mu) ** 2) / np.sum(ww))

            def obj2(s2, r=r, lg=lg):
                with np.errstate(all="ignore"):
                    t2 = _elem_transform(kind, r, s2)[:, 0] - lg
                if not np.all(np.isfinite(t2)):
                    return np.inf
                vt = wvar(t2 + lg)
                return wvar(t2) / vt if vt > 0 else np.inf
            s2, v2 = _golden_min(obj2, s - 0.5, s + 0.5)
            if not v2 < tol:
                continue
            with np.errstate(all="ignore"):
                dt = _elem_transform(kind, r, s2)[:, 0] - lg
                k0 = float(np.sum(ww * dt) / np.sum(ww))
            if not abs(k0) <= 700.0:
                continue
            c = math.exp(k0) * (-1.0 if kind == "exp+" else 1.0)
            out.append((kind.rstrip("+-"), lib[idx[m]], g, c))
            break
    return out


def _pred_rel_error(p, y) -> float:
    """[1.4-N2] Le score des graines tolérantes (_seed_rel_error) calculé
    sur des prédictions : 1 - R² après mise à l'échelle linéaire."""
    with np.errstate(all="ignore"):
        p = np.asarray(p, dtype=float)
        if not np.all(np.isfinite(p)) or not np.var(p) > 0:
            return float("inf")
        a, b, ok = _linear_scale_params(p, y)
        if not ok:
            return float("inf")
        r = float(np.mean((y - (a + b * p)) ** 2) / np.var(y))
    return r if math.isfinite(r) else float("inf")


_SCAN_KEEP = 3                        # [1.4-N2] formes gardées par balayage


def _elem_log_scan(X, y, cols, tol, signed: bool) -> list:
    """[1.4-N2] Le chercheur du logarithme sur toute sa bibliothèque : les
    _SCAN_KEEP meilleures formes y = b·f·log(c·g) au score des graines
    tolérantes, les exposants de g par _log_g_exponents. signed : seulement
    les f où y/f garde un signe, comme dans la première passe."""
    n = y.shape[0]
    lib = _elem_flib(cols)
    if lib is None:
        return []
    FV = np.column_stack([_elem_mono(X, m) for m in lib])
    R = y[:, None] / FV
    ok = np.all(np.isfinite(R), axis=0)
    if signed:
        ok &= np.all(R > 0, axis=0) | np.all(R < 0, axis=0)
    idx = np.where(ok)[0]
    if not idx.size:
        return []
    R = R[:, idx]
    LU = np.log(np.abs(X[:, cols]))
    L = np.column_stack([np.ones(n), LU])
    Q = np.linalg.qr(L)[0]
    v = _elem_rel(R, Q)
    found = []
    for m in np.where(v < tol)[0]:
        r = R[:, m]
        ex = _log_g_exponents(np.linalg.lstsq(L, r, rcond=None)[0][1:])
        if ex is None:
            continue
        g = tuple((j, float(e)) for j, e in zip(cols, ex) if e)
        lg = np.log(np.abs(_elem_mono(X, g)))
        if not np.all(np.isfinite(lg)):           # [1.4-L1] une colonne négative
            continue                              # et un exposant fractionnaire
        A = np.column_stack([np.ones(n), lg])
        a0, s0 = np.linalg.lstsq(A, r, rcond=None)[0]
        if not (float(np.var(r - A @ np.array([a0, s0]))) / float(np.var(r))
                < tol) or s0 == 0.0 or abs(a0 / s0) > 700.0:
            continue
        sc = _pred_rel_error(FV[:, idx[m]] * (a0 / s0 + lg), y)
        if math.isfinite(sc):
            found.append((sc, len(found),
                          ("log", lib[idx[m]], g, float(math.exp(a0 / s0)))))
    found.sort(key=lambda t: (t[0], t[1]))
    return [f for _sc, _i, f in found[:_SCAN_KEEP]]


def _elem_trig_grid(z, gn):
    """Résidu relatif de z ~ 1 + sin(ω·gn) + cos(ω·gn) pour chaque ω de la
    grille (équations normales : pour classer seulement)."""
    n = len(z)
    w = _ELEM_W_GRID
    P = np.outer(gn, w)
    S, C = np.sin(P), np.cos(P)
    G = np.empty((len(w), 3, 3))
    G[:, 0, 0] = n
    G[:, 0, 1] = G[:, 1, 0] = S.sum(0)
    G[:, 0, 2] = G[:, 2, 0] = C.sum(0)
    G[:, 1, 1] = (S * S).sum(0)
    G[:, 1, 2] = G[:, 2, 1] = (S * C).sum(0)
    G[:, 2, 2] = (C * C).sum(0)
    rhs = np.stack([np.full(len(w), z.sum()), z @ S, z @ C], axis=1)
    with np.errstate(all="ignore"):
        try:
            coef = np.linalg.solve(G, rhs[..., None])[..., 0]
        except np.linalg.LinAlgError:
            return np.full(len(w), np.inf)
        rss = float(z @ z) - np.einsum("ij,ij->i", coef, rhs)
        vz = float(np.var(z)) * n
    return np.where(np.isfinite(rss), np.maximum(rss, 0.0) / vz, np.inf)


def _elem_trig_exact(z, gn, sub):
    """(résidu relatif, ω, (a, β, γ)) de la meilleure forme trigonométrique,
    affinée seulement si la grille la place sous _ELEM_TRIG_GATE."""
    v = _elem_trig_grid(z[sub], gn[sub])
    i = int(np.argmin(v))
    if not v[i] < _ELEM_TRIG_GATE:
        return np.inf, None, None
    vz = float(np.var(z))

    def obj(w):
        A = np.column_stack([np.ones_like(gn), np.sin(w * gn), np.cos(w * gn)])
        c = np.linalg.lstsq(A, z, rcond=None)[0]
        return float(np.var(z - A @ c)) / vz
    W = _ELEM_W_GRID
    w, val = _golden_min(obj, float(W[max(i - 1, 0)]), float(W[min(i + 1, len(W) - 1)]))
    A = np.column_stack([np.ones_like(gn), np.sin(w * gn), np.cos(w * gn)])
    return val, w, np.linalg.lstsq(A, z, rcond=None)[0]


def _elem_trig_forms(X, y, cols, tol=_BINOM_TOL, weighted=False,
                     scan=False) -> list:
    """Forme y = f·(a + β·sin(ω·g) + γ·cos(ω·g)) : au plus une. Rend des
    tuples ("trig", f, g, ω rapporté à g, (a, β, γ)).

    [1.4-N2] weighted : la seconde passe des graines tolérantes au bruit, où
    les moindres carrés sur log|y| qui donnent les exposants de f sont
    pondérés par y². scan : toute la bibliothèque est parcourue, et les
    _SCAN_KEEP meilleures formes au score des graines tolérantes sont rendues
    (au lieu de la première qui passe). Sans eux, le calcul d'avant."""
    n = y.shape[0]
    glib = [((j, 1),) for j in range(X.shape[1])]
    if len(cols) <= 8:
        for j, k in itertools.combinations(cols, 2):
            for e1, e2 in ((1, 1), (1, -1), (-1, 1)):
                glib.append(((j, e1), (k, e2)))
    nz = np.abs(y) > 0
    sub = np.unique(np.linspace(0, n - 1, min(n, _BINOM_GRID_ROWS)).astype(int))
    found = []
    wy = np.abs(y) / float(np.max(np.abs(y))) if weighted else None
    for g in glib:
        gv = _elem_mono(X, g)
        gmax = float(np.max(np.abs(gv)))
        if not (np.all(np.isfinite(gv)) and gmax > 0):
            continue
        gn = gv / gmax
        gcols = {j for j, _ in g}
        others = [j for j in cols if j not in gcols]
        if others:
            LU = np.log(np.abs(X[:, others]))
            L = np.column_stack([np.ones(n), LU])
            if weighted:
                e0 = np.linalg.lstsq(L[nz] * wy[nz, None],
                                     np.log(np.abs(y[nz])) * wy[nz],
                                     rcond=None)[0][1:]
            else:
                e0 = np.linalg.lstsq(L[nz], np.log(np.abs(y[nz])), rcond=None)[0][1:]
            f0 = np.exp(LU @ e0)
        else:
            e0, f0 = np.zeros(0), np.ones(n)
        cands = []
        if others:
            z0 = y / f0
            v = _elem_trig_grid(z0[sub], gn[sub])
            i = int(np.argmin(v))
            if np.isfinite(v[i]):
                w0 = float(_ELEM_W_GRID[i])
                A = np.column_stack([np.ones(n), np.sin(w0 * gn), np.cos(w0 * gn)])
                h = A @ np.linalg.lstsq(A, z0, rcond=None)[0]
                keep = np.abs(h) > 0.3 * np.max(np.abs(h))
                if weighted:
                    keep &= nz
                if keep.sum() > len(others) + 3:
                    if weighted:
                        e1 = np.linalg.lstsq(
                            L[keep] * wy[keep, None],
                            ((np.log(np.abs(y)) - np.log(np.abs(h))) * wy)[keep],
                            rcond=None)[0][1:]
                    else:
                        e1 = np.linalg.lstsq(
                            L[keep], (np.log(np.abs(y)) - np.log(np.abs(h)))[keep],
                            rcond=None)[0][1:]
                    cands += [np.round(e1), np.round(2.0 * e1) / 2.0]
        cands += [np.round(e0), np.round(2.0 * e0) / 2.0]
        seen = set()
        for ex in cands:
            key = tuple(float(e) for e in ex)
            if key in seen or not np.all(np.abs(ex) <= 6.0):
                continue
            seen.add(key)
            fv = np.ones(n)
            for j, e in zip(others, ex):
                fv = fv * X[:, j] ** e
            val, w, c = _elem_trig_exact(y / fv, gn, sub)
            if val < tol:
                f = tuple((j, float(e)) for j, e in zip(others, ex) if e)
                form = ("trig", f, g, float(w) / gmax, tuple(float(x) for x in c))
                if not scan:
                    return [form]
                A = np.column_stack([np.ones(n), np.sin(w * gn), np.cos(w * gn)])
                sc = _pred_rel_error(fv * (A @ c), y)
                if math.isfinite(sc):
                    found.append((sc, len(found), form))
    if scan:
        found.sort(key=lambda t: (t[0], t[1]))
        return [f for _sc, _i, f in found[:_SCAN_KEEP]]
    return []


# [1.4-E2] UNE GRAINE POUR UNE CONSTANTE PLUS UNE EXPONENTIELLE
# Constat (benchmarks/results_1.4/analysis/README.md) : la loi de Newton,
# θ = θa + (θ0 − θa)·exp(−t/τ), n'avait pas de graine. Le chercheur de
# l'exponentielle (phase 4a) passe par log|y/f|, qu'une constante additive
# rend non linéaire, et la loi revenait dans 9 ajustements de TP sur 40. E2
# (benchmarks/results_1.4/PLAN.md) cherche y = a + b·exp(c·g) dans les
# données, sans logarithme de la cible (elle n'a donc pas à garder un
# signe) : g est une colonne à la puissance 1 ou −1, ou, jusqu'à huit
# colonnes, le produit ou le rapport de deux colonnes (la bibliothèque du
# sinus et du cosinus) ; c se cherche sur une grille puis par la section
# dorée, sur le résidu des moindres carrés en (a, b). La graine est exp(c·g),
# la mise à l'échelle linéaire de la recherche portant a et b. Graine exacte
# quand la forme tient à la précision numérique et que a n'est pas nul (sinon
# c'est l'exponentielle que la phase 4a ajuste déjà) ; dans l'étage tolérant,
# un candidat comme les autres (ses trois meilleures formes). Une forme dont
# l'exponentielle varie de moins d'un facteur e^0,5 sur les données n'est pas
# rendue : elle imiterait une droite. Non adoptée par sa campagne
# (benchmarks/results_1.4/e2/campaign/README.md) : éteinte, son code gardé
# pour la décision de l'auteur.
_E2_C_GRID = np.concatenate([-np.geomspace(50.0, 0.01, 40), np.geomspace(0.01, 50.0, 40)])
_E2_GATE = 0.05                       # résidu de grille sous lequel on affine
_E2_CURVE = 0.5                       # |c|·étendue de g au moins : l'exponentielle
                                      # varie d'un facteur e^0,5 sur les données,
                                      # sinon elle imite une droite


def _e2_residuals(gn, y, cs):
    """Résidu relatif de y ≈ a + b·exp(c·gn) pour chaque c de cs."""
    with np.errstate(all="ignore"):
        U = np.exp(np.outer(gn, cs))
        Uc = U - U.mean(axis=0)
        yc = y - y.mean()
        vu = np.einsum("ij,ij->j", Uc, Uc)
        cov = Uc.T @ yc
        vy = float(yc @ yc)
        r = 1.0 - cov * cov / (vu * vy)
    return np.where(np.isfinite(r) & (vu > 0), np.maximum(r, 0.0), np.inf)


def _elem_aexp_forms(X, y, tol=_BINOM_TOL) -> list:
    """[1.4-E2] Formes y = a + b·exp(c·g) : au plus _SCAN_KEEP, rendues comme
    des formes ("exp", (), g, c) de la phase 4a (f = 1, c rapporté à g). Une
    forme n'est rendue sous un tol exact (sous 1e-3) que si a n'est pas nul."""
    n = y.shape[0]
    out = []
    if n < 7 or not np.var(y) > 0:
        return out
    cols = [j for j in range(X.shape[1]) if np.all(X[:, j] != 0)]
    glib = []
    for j in range(X.shape[1]):
        glib.append(((j, 1),))
        if j in cols:
            glib.append(((j, -1),))
    if X.shape[1] <= 8:
        for j, k in itertools.combinations(range(X.shape[1]), 2):
            glib.append(((j, 1), (k, 1)))
            if k in cols:
                glib.append(((j, 1), (k, -1)))
            if j in cols:
                glib.append(((j, -1), (k, 1)))
    found = []
    with np.errstate(all="ignore"):
        for g in glib:
            gv = _elem_mono(X, g)
            gmax = float(np.max(np.abs(gv)))
            if not (np.all(np.isfinite(gv)) and gmax > 0) or not np.var(gv) > 0:
                continue
            gn = gv / gmax
            v = _e2_residuals(gn, y, _E2_C_GRID)
            i = int(np.argmin(v))
            if not v[i] < _E2_GATE:
                continue
            lo = float(_E2_C_GRID[max(i - 1, 0)])
            hi = float(_E2_C_GRID[min(i + 1, len(_E2_C_GRID) - 1)])
            if lo < 0 < hi:                       # pas de c nul
                lo, hi = (lo, -1e-3) if _E2_C_GRID[i] < 0 else (1e-3, hi)
            c, _r = _golden_min(lambda cc: float(_e2_residuals(gn, y, np.array([cc]))[0]),
                                lo, hi)
            # quelques pas de Gauss-Newton sur (a, b, c) : la section dorée sur
            # un résidu calculé par différence s'arrête vers 1e-7 en c
            u = np.exp(c * gn)
            a, b = np.linalg.lstsq(np.column_stack([np.ones(n), u]), y, rcond=None)[0]
            e = y - a - b * u
            sse = float(e @ e)
            for _ in range(8):
                J = np.column_stack([np.ones(n), u, b * gn * u])
                d = np.linalg.lstsq(J, e, rcond=None)[0]
                c2 = c + float(d[2])
                u2 = np.exp(c2 * gn)
                ab = np.linalg.lstsq(np.column_stack([np.ones(n), u2]), y, rcond=None)[0]
                e2 = y - ab[0] - ab[1] * u2
                s2 = float(e2 @ e2)
                if not (np.isfinite(s2) and s2 < sse):
                    break
                c, u, (a, b), e, sse = c2, u2, ab, e2, s2
            r = sse / (n * float(np.var(y)))
            if not r < tol or abs(c) * float(np.ptp(gn)) < _E2_CURVE:
                continue                          # pas une droite déguisée
            if tol < 1e-3 and not abs(a) > 1e-9 * float(np.max(np.abs(y))):
                continue                          # a nul : la phase 4a
            found.append((r, len(found), ("exp", (), g, float(c) / gmax)))
    found.sort(key=lambda t: (t[0], t[1]))
    return [f for _r, _i, f in found[:_SCAN_KEEP]]


def _elementary_forms(X, y, kinds, tol=None, weighted=False, scan=False) -> list:
    """Formes de la phase 4a qui tiennent à la précision numérique (à tol
    près, graines tolérantes au bruit de la phase 5).

    [1.4-N2] Pour les graines tolérantes au bruit seulement :
    - weighted : la seconde passe. Les lignes où y est nul sont écartées, la
      cible n'a plus à garder un signe, et les moindres carrés sur les
      logarithmes sont pondérés par y² (_elem_inverse_forms_w, et les
      exposants de f de la forme trigonométrique).
    - scan : les seules formes du balayage de toute la bibliothèque, pour le
      logarithme et pour le sinus et le cosinus (leurs _SCAN_KEEP
      meilleures au score des graines tolérantes).
    Sans eux, le calcul d'avant."""
    tol = _BINOM_TOL if tol is None else tol
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    out = []
    with np.errstate(all="ignore"):
        if not (np.all(np.isfinite(y)) and np.all(np.isfinite(X))):
            return out
        if weighted:
            nzr = y != 0
            X, y = X[nzr], y[nzr]
        if scan or weighted:
            return _elementary_forms_n2(X, y, kinds, tol, weighted, scan)
        n = y.shape[0]
        cols = [j for j in range(X.shape[1])
                if np.all(X[:, j] > 0) or np.all(X[:, j] < 0)]
        inv = [k for k in kinds if k != "trig"]
        if inv and cols and n > len(cols) + 6 \
                and (np.all(y > 0) or np.all(y < 0)):
            L = np.column_stack([np.ones(n), np.log(np.abs(X[:, cols]))])
            Q = np.linalg.qr(L)[0]
            if _elem_rel(np.log(np.abs(y))[:, None], Q)[0] < _POWER_TOL:
                return out                # une loi de puissance : ses graines
            out += _elem_inverse_forms(X, y, cols, inv, tol=tol)
        if "trig" in kinds and n > 10 and np.var(y) > 0:
            out += _elem_trig_forms(X, y, cols, tol=tol)
        if "aexp" in kinds:                       # [1.4-E2]
            out += _elem_aexp_forms(X, y, tol=tol)
    return out


def _elementary_forms_n2(X, y, kinds, tol, weighted, scan) -> list:
    """[1.4-N2] La partie de _elementary_forms propre aux graines tolérantes
    au bruit (voir sa documentation). Les gardes sont celles de la première
    passe, sans la condition de signe de la cible quand weighted."""
    n = y.shape[0]
    out = []
    if not n:
        return out
    cols = [j for j in range(X.shape[1])
            if np.all(X[:, j] > 0) or np.all(X[:, j] < 0)]
    inv = [k for k in kinds if k != "trig"]
    if inv and cols and n > len(cols) + 6 \
            and (weighted or np.all(y > 0) or np.all(y < 0)):
        L = np.column_stack([np.ones(n), np.log(np.abs(X[:, cols]))])
        if weighted:
            sw = np.abs(y) / float(np.max(np.abs(y)))
            Qw = np.linalg.qr(L * sw[:, None])[0]
            power = _elem_wrel(np.log(np.abs(y))[:, None], Qw, sw)[0] < _POWER_TOL
        else:
            Q = np.linalg.qr(L)[0]
            power = _elem_rel(np.log(np.abs(y))[:, None], Q)[0] < _POWER_TOL
        if power:
            return out                    # une loi de puissance : ses graines
        if scan:
            if "log" in inv:
                out += _elem_log_scan(X, y, cols, tol, signed=not weighted)
        else:
            out += _elem_inverse_forms_w(X, y, cols, inv, tol=tol)
    if "trig" in kinds and n > 10 and np.var(y) > 0:
        out += _elem_trig_forms(X, y, cols, tol=tol, weighted=weighted, scan=scan)
    return out


def _make_elementary_seeds(xs, ys, cfg, tol=None, weighted=False,
                           scan=False) -> list:
    """[0.10, phase 4a] Voir le commentaire ci-dessus. Rend 0 à 5 arbres.
    Le drapeau _ELEMENTARY_SEEDS (actif par défaut) les coupe. [1.4-N2]
    weighted, scan : voir _elementary_forms (graines tolérantes au bruit)."""
    if not state._ELEMENTARY_SEEDS or not state._GENERIC_CSV_MODE or _seeds_blocked_by_units(cfg) \
            or bool(getattr(cfg, "EXTRAPOLATION_MODE", False)):
        return []
    terms = list(getattr(cfg, "TERMINALS", []) or [])
    try:
        X = np.asarray(xs, dtype=float)
        y = np.asarray(ys, dtype=float)
    except Exception:
        return []
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    if X.ndim != 2 or y.ndim != 1 or X.shape[0] != y.shape[0] \
            or X.shape[1] != len(terms):
        return []
    bops = set(state._GENERIC_BINARY_OPS)
    uops = set(state._GENERIC_UNARY_OPS)
    if not {"+", "*", "/"} <= bops:
        return []
    kinds = [k for k, need in (("exp", {"exp"}), ("log", {"log"}),
                               ("tanh", {"tanh"}), ("sech", {"exp"}),
                               ("trig", {"sin", "cos"}),
                               ("arcsin", {"arcsin"})) if need <= uops]   # [1.3-A3]
    if state._E2_SEEDS and "exp" in uops:               # [1.4-E2]
        kinds.append("aexp")
    if not kinds:
        return []
    t0 = time.time()
    forms = _elementary_forms(X, y, kinds, tol=tol, weighted=weighted, scan=scan)
    TRACE.set("elementary_seed_s", round(time.time() - t0, 3))
    seeds = []
    for form in forms:
        kind, fm, g = form[0], form[1], form[2]
        f = _monomial(terms, [(j, float(e)) for j, e in fm], uops)
        gnode = _monomial(terms, [(j, float(e)) for j, e in g], uops)
        if gnode is None or (fm and f is None):
            continue
        if kind == "trig":
            w, (a, b, c) = form[3], form[4]
            mx = max(abs(a), abs(b), abs(c))
            arg = lambda: Node("*", Node(w), gnode.copy())
            terms_ = []
            if abs(a) > 1e-9 * mx:
                terms_.append(Node(a / mx))
            if abs(b) > 1e-9 * mx:
                terms_.append(Node("*", Node(b / mx), Node("sin", arg())))
            if abs(c) > 1e-9 * mx:
                terms_.append(Node("*", Node(c / mx), Node("cos", arg())))
            inner = terms_[0]
            for t_ in terms_[1:]:
                inner = Node("+", inner, t_)
            seeds.append(inner if f is None else Node("*", f, inner))
            continue
        c = form[3]
        cg = lambda cc: Node("*", Node(cc), gnode.copy())
        if kind == "exp":
            h = Node("exp", cg(c))
        elif kind == "log":
            h = Node("log", cg(c))
        elif kind == "tanh":
            h = Node("tanh", cg(c))
        elif kind == "arcsin":            # [1.3-A3]
            h = Node("arcsin", cg(c))
        else:                             # 1/cosh(c·g) = 2/(exp(c·g) + exp(-c·g))
            den = Node("+", Node("exp", cg(c)), Node("exp", cg(-c)))
            seeds.append(Node("/", f if f is not None else Node(1.0), den))
            continue
        seeds.append(h if f is None else Node("*", f, h))
    seeds = _typed_seeds(seeds, cfg)
    if seeds:
        TRACE.set("elementary_seed", " | ".join(to_string(s) for s in seeds))
    return seeds


# ════════════════════════════════════════════════════════════════
# [0.10, phase 5] GRAINES TOLÉRANTES AU BRUIT
# ════════════════════════════════════════════════════════════════
# Constat (diagnostic D5, benchmarks/results_0.9/PLAN_PHASE5.md) : avec du
# bruit sur y, la structure de la loi manque parmi les candidats dans deux
# ajustements sur trois, alors que les graines de loi de puissance, B1 et E1
# la porteraient : leurs seuils (R² log-log de 0,999, précision numérique)
# sont défaits par le bruit, qui est bien plus fort sur log|y| là où y est
# petit. Quand aucune forme exacte n'a été trouvée, on relance donc les trois
# chercheurs seuils levés, et on juge chaque forme comme les données la
# jugent : 1 - R² après mise à l'échelle linéaire sur les lignes
# d'entraînement. Elle devient une graine si cette erreur ne dépasse pas
# _TOLERANT_REL : les graines qui ont la structure de la loi ajustent 10 % de
# bruit à 0,008-0,014 (1 % de bruit vers 1e-4) ; sur les données réelles du
# banc de décision, aucune n'ajuste mieux que 0,026. Mêmes gardes que les
# graines exactes ; aucun tirage aléatoire. Mesuré dans PLAN_PHASE5.md
# (changement N1, adopté le 13 octobre 2026) : structure retrouvée sous bruit
# 69 -> 106 sur 205 (1 %) et 68 -> 86 (10 %), puis 64 -> 103 et 65 -> 81 sur
# des graines neuves ; lois exactes sans bruit 157 -> 160 ; aucune graine sur
# les 520 ajustements réels. Limite connue : sur des données exactes qu'aucune
# graine exacte ne couvre, une forme approchée peut détourner la recherche
# (loi de Kepler normalisée par min-max, PLAN_PHASE5.md).

_TOLERANT_REL = 0.015

# [1.4-N2] LES CHERCHEURS TOLÉRANTS VOIENT À TRAVERS LE BRUIT
# Constat (benchmarks/results_1.4/analysis/README.md) : sous bruit, trois
# règles des chercheurs, écrites pour des données exactes, défont les
# graines tolérantes. (1) La cible doit garder un signe : 1 % de bruit le
# lui fait perdre près de zéro dans 7 équations sur 41, dont deux monômes.
# (2) Le chercheur du sinus et du cosinus (et celui du logarithme) rend la
# première forme qui passe, pas la meilleure : sur III.15.12 à 1 %, une
# forme en k seul au lieu de la loi en k·d. (3) La constante interne vient
# du chercheur, ajustée dans l'espace transformé. (4) Trouvée par la
# mécanique de N2 : le logarithme rapporte les exposants de g au plus petit
# coefficient non nul, qu'un exposant nul a sous bruit (voir
# _log_g_exponents). N2 garde l'étage, son score et son seuil, et change ses
# candidats (benchmarks/results_1.4/PLAN.md) :
# - chaque chercheur tourne comme avant, puis une seconde fois avec ses
#   moindres carrés sur les logarithmes pondérés par y² et sans la
#   condition de signe ;
# - le logarithme, le sinus et le cosinus parcourent toute leur
#   bibliothèque et rendent aussi leurs trois meilleures formes au score
#   (les exposants de g du logarithme par _log_g_exponents) ;
# - chaque candidat a ses constantes ajustées sur les lignes d'entraînement
#   par l'ajustement de constantes du moteur avant d'être noté (ses
#   exposants, arrondis par le chercheur, sont dans la structure de
#   l'arbre et restent) ;
# - les candidats sont dédoublonnés par leur forme, et ceux sous le seuil
#   placés, les meilleurs d'abord, douze au plus. Les formes que les
#   chercheurs d'avant donnent sont toujours placées quand elles passent le
#   seuil : toute graine que plaçait 1.3.0 l'est encore.
# Non adopté (campagne N2, 13 novembre 2026, benchmarks/results_1.4/n2/
# campaign/README.md) : sans bruit, F41 perd 5 lois exactes, toutes là où
# l'étage tourne, à cause de l'ajustement des constantes des candidats.
# Retiré du candidat : éteint. Sur décision de l'auteur (13 novembre), N2
# est mesuré de nouveau sans cet ajustement (N2b, _TOLERANT_REFIT False) :
# chaque candidat garde les constantes de son chercheur. N2b est adopté et
# gardé (campagne et confirmation, 13 novembre 2026, benchmarks/
# results_1.4/n2b/campaign/README.md) : il fait partie de la 1.4.
_TOLERANT_MAX = 12


def _seed_rel_error(tree, X, y) -> float:
    """1 - R² d'un arbre après mise à l'échelle linéaire (inf s'il n'est pas
    évaluable)."""
    try:
        with np.errstate(all="ignore"):
            p = np.asarray(evaluate_vector(tree, X), dtype=float)
        if not np.all(np.isfinite(p)) or not np.var(p) > 0:
            return float("inf")
        a, b, ok = _linear_scale_params(p, y)
        if not ok:
            return float("inf")
        r = float(np.mean((y - (a + b * p)) ** 2) / np.var(y))
        return r if math.isfinite(r) else float("inf")
    except Exception:
        return float("inf")


def _small_family(scored, cfg, t0) -> list:
    """[1.4-S1] Sous 30 lignes, l'étage tolérant place ses huit meilleures
    formes, une par forme, qui laissent au plus la moitié de la variance (le
    seuil de 1,5 % n'y sert pas), et les garde pour la sélection finale."""
    seen, fam = set(), []
    for r, _i, t in scored:
        if not r <= _SMALL_FAMILY_SHARE:
            break
        h = t.canonical_hash()
        if h in seen:
            continue
        seen.add(h)
        fam.append((r, t))
        if len(fam) >= _SMALL_FAMILY_KEEP:
            break
    seeds = _typed_seeds([t for _r, t in fam], cfg)
    kept = {id(t) for t in seeds}
    _SMALL_FAMILY[:] = [t.copy() for t in seeds]
    TRACE.set("tolerant_seed_s", round(time.time() - t0, 3))
    if seeds:
        TRACE.set("tolerant_seed", " | ".join(
            "%s (%.2g)" % (to_string(t), r) for r, t in fam if id(t) in kept))
    return seeds


def _refit_inner(tree, X, y, cfg):
    """[1.4-N2] Les constantes d'un candidat ajustées sur les lignes
    d'entraînement par l'étape de finition du moteur (_lm_to_convergence).
    L'arbre d'entrée si rien n'est amélioré, ou quand la recherche n'a pas
    de mise à l'échelle linéaire (perte personnalisée) : le score des
    graines et l'ajustement ne jugeraient pas la même forme. [1.4-N2b]
    L'arbre d'entrée aussi sans _TOLERANT_REFIT."""
    if not state._TOLERANT_REFIT:
        return tree
    if not (state._USE_LINEAR_SCALING and state._CUSTOM_LOSS_FN is None):
        return tree
    try:
        with np.errstate(all="ignore"):
            out = _lm_to_convergence(tree, X, y, cfg)
    except Exception:
        return tree
    return tree if out is None else out


def _make_tolerant_seeds(xs, ys, cfg, power_done: bool = False) -> list:
    """[0.10, phase 5] Voir le commentaire ci-dessus. Appelée seulement quand
    ni B1 ni E1 n'ont placé de graine ; sans la loi de puissance si ses
    graines exactes ont déjà été placées (power_done). Le drapeau
    _TOLERANT_SEEDS (actif par défaut) les coupe."""
    if not state._TOLERANT_SEEDS or not state._GENERIC_CSV_MODE or _seeds_blocked_by_units(cfg) \
            or bool(getattr(cfg, "EXTRAPOLATION_MODE", False)):
        return []
    try:
        X = np.asarray(xs, dtype=float)
        y = np.asarray(ys, dtype=float)
    except Exception:
        return []
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    if X.ndim != 2 or y.ndim != 1 or X.shape[0] != y.shape[0] \
            or not np.var(y) > 0:
        return []
    t0 = time.time()
    trace = {k: TRACE.value.get(k) for k in ("power_law_seed", "binomial_seed",
                                             "binomial_seed_s", "elementary_seed",
                                             "elementary_seed_s")}
    cands = []
    finders = [(_make_binomial_seeds, dict(tol=1.0)),
               (_make_elementary_seeds, dict(tol=1.0))]
    if not power_done:
        finders.insert(0, (_make_power_law_seeds, dict(min_r2=-math.inf)))
    for fn, kw in finders:
        try:
            cands += fn(X, y, cfg, **kw)
        except Exception:
            pass
    n_first = len(cands)                          # [1.4-N2] ceux d'avant
    if state._TOLERANT_N2:
        more = [(_make_elementary_seeds, dict(tol=1.0, scan=True)),
                (_make_binomial_seeds, dict(tol=1.0, weighted=True)),
                (_make_elementary_seeds, dict(tol=1.0, weighted=True)),
                (_make_elementary_seeds, dict(tol=1.0, weighted=True, scan=True))]
        if not power_done:
            more.insert(1, (_make_power_law_seeds, dict(weighted=True)))
        for fn, kw in more:
            try:
                cands += fn(X, y, cfg, **kw)
            except Exception:
                pass
    for k, v in trace.items():                    # les traces des graines exactes
        if v is None:
            TRACE.value.pop(k, None)
        else:
            TRACE.set(k, v)
    if not state._TOLERANT_N2:                          # 1.3.0
        scored = sorted(((_seed_rel_error(t, X, y), i, t) for i, t in enumerate(cands)),
                        key=lambda r: (r[0], r[1]))
        if state._SMALL_ON:                             # [1.4-S1] les formes de famille
            return _small_family(scored, cfg, t0)
        seeds = _typed_seeds([t for r, _, t in scored if r <= _TOLERANT_REL], cfg)
        TRACE.set("tolerant_seed_s", round(time.time() - t0, 3))
        if seeds:
            kept = {id(t) for t in seeds}
            TRACE.set("tolerant_seed", " | ".join(
                "%s (%.2g)" % (to_string(t), r) for r, _, t in scored
                if r <= _TOLERANT_REL and id(t) in kept))
        return seeds
    # [1.4-N2] les constantes ajustées, puis le score ; une forme, le meilleur
    # de ses candidats
    scored = []
    for i, t in enumerate(cands):
        t2 = _refit_inner(t, X, y, cfg)
        scored.append((_seed_rel_error(t2, X, y), i, t2))
    scored.sort(key=lambda r: (r[0], r[1]))
    forms, first = {}, set()
    # [1.4-N2b] sans ajustement des constantes, une forme que donnent les
    # chercheurs d'avant garde leur arbre, constantes comprises : N2b ne fait
    # qu'ajouter des formes aux graines de 1.3.0
    order = scored if state._TOLERANT_REFIT else sorted(
        scored, key=lambda r: (r[1] >= n_first, r[0], r[1]))
    for r, i, t in order:
        h = t.canonical_hash()
        if i < n_first:
            first.add(h)
        if h not in forms:
            forms[h] = (r, i, t)
    if state._SMALL_ON:                                 # [1.4-S1] les formes de famille
        return _small_family(sorted(forms.values(), key=lambda r: (r[0], r[1])),
                             cfg, t0)
    within = sorted((v for v in forms.values() if v[0] <= _TOLERANT_REL),
                    key=lambda r: (r[0], r[1]))
    old = [v for v in within if v[2].canonical_hash() in first]
    new = [v for v in within if v[2].canonical_hash() not in first]
    placed = sorted(old + new[:max(0, _TOLERANT_MAX - len(old))],
                    key=lambda r: (r[0], r[1]))
    seeds = _typed_seeds([t for _r, _i, t in placed], cfg)
    TRACE.set("tolerant_seed_s", round(time.time() - t0, 3))
    TRACE.set("tolerant_cands", "%d candidats, %d formes, %d sous le seuil" % (
        len(cands), len(forms), len(within)))
    if seeds:
        kept = {id(t) for t in seeds}
        TRACE.set("tolerant_seed", " | ".join(
            "%s (%.2g)" % (to_string(t), r) for r, _, t in placed
            if id(t) in kept))
    return seeds
