"""The score of a formula: linear and robust scaling, the errors, the
scale of the target, the usage of the variables, and fitness.

Part of gp_elite/core.py until 1.4.0, moved without change in 1.5.
"""
from __future__ import annotations

import math
import numpy as np
from typing import Optional, List, Tuple, Dict, Any

from . import state
from .config import (TRACE, _dim_active, _ds)
from .tree import (Node, _FLOAT_GAMMA, tree_complexity, tree_depth, tree_size)
from .simplification import (simplify)
from .evaluation import (_pearson_r, _predict_cached, evaluate_vector)

# [CUSTOM-LOSS PARSIMONY] Poids de la pénalité de taille pour la loss custom
# (0 = désactivé). Favorise les lois simples ; utile pour la découverte de
# lois de conservation (sinon des arbres géants exploitent le bruit numérique).

def _linear_scale_params(preds: np.ndarray, ys_np: np.ndarray):
    """Coefficients OLS (a, b) de  y ≈ a + b·preds.  Retourne (a, b, ok).

    [v0.4.1] En mode dimensionnel, l'offset `a` ajouterait une constante
    adimensionnee a une grandeur dimensionnee : on regresse donc PAR L'ORIGINE
    (a = 0). Un coefficient multiplicatif sans dimension est exactement ce que
    portent les lois physiques (le 1/2 de 1/2mv², le 4π de Coulomb), donc la
    forme scalee reste dimensionnellement saine — et surtout MATERIALISABLE
    dans l'arbre livre, ce que l'offset interdisait.
    """
    if state._LS_SCALE_ONLY:
        if not np.all(np.isfinite(preds)) or float(np.max(np.abs(preds))) > 1e15:
            return 0.0, 1.0, False
        den = float(np.dot(preds, preds))
        if den < 1e-12:
            return 0.0, 1.0, False
        b = float(np.dot(preds, ys_np)) / den
        if not math.isfinite(b):
            return 0.0, 1.0, False
        return 0.0, b, True

    pm = float(preds.mean()); ym = float(ys_np.mean())
    pc = preds - pm
    # [FIX-OVF v20] Clamp avant dot pour éviter overflow sur arbres explosifs
    if not np.all(np.isfinite(pc)) or np.max(np.abs(pc)) > 1e15:
        return 0.0, 1.0, False
    var_p = float(np.dot(pc, pc))
    if var_p < 1e-12:
        return 0.0, 1.0, False
    b = float(np.dot(pc, ys_np - ym)) / var_p
    a = ym - b * pm
    if not (math.isfinite(a) and math.isfinite(b)):
        return 0.0, 1.0, False
    return a, b, True

def _robust_scale_params(preds: np.ndarray, ys_np: np.ndarray, delta: float = 0.5, n_iter: int = 5):
    """Coefficients (a, b) de y ≈ a + b·preds calés de façon ROBUSTE (Huber)
    via moindres carrés repondérés itératifs (IRLS). Contrairement à
    _linear_scale_params (OLS, sensible aux outliers), les points aberrants
    reçoivent un poids réduit → la droite suit la vraie tendance.
    Retourne (a, b, ok). 5 itérations suffisent (convergence rapide testée)."""
    pc = preds - float(preds.mean())
    if not np.all(np.isfinite(pc)) or np.max(np.abs(pc)) > 1e15:
        return 0.0, 1.0, False
    if float(np.dot(pc, pc)) < 1e-12:
        return 0.0, 1.0, False
    a, b = float(ys_np.mean()), 1.0
    f = preds
    for _ in range(n_iter):
        r = a + b * f - ys_np
        s = float(np.std(r)) + 1e-9
        rs = np.abs(r / s)
        w = np.where(rs <= delta, 1.0, delta / (rs + 1e-9))   # poids de Huber
        W = np.sqrt(w)
        A = np.column_stack([W, f * W])
        try:
            sol, *_ = np.linalg.lstsq(A, ys_np * W, rcond=None)
        except Exception:
            return 0.0, 1.0, False
        a, b = float(sol[0]), float(sol[1])
        if not (math.isfinite(a) and math.isfinite(b)):
            return 0.0, 1.0, False
    return a, b, True

def raw_mse(node, xs, ys) -> float:
    """
    [v13.11 — OBJECTIF 1] Fitness Hybride : Corrélation de Pearson + MSE normalisé.

    Remplace l'ancienne combinaison "70% MSE + 30% relatif" par :

        si std(prédictions) < 1e-6 (arbre constant) :
            retourne  mse + 2.0   ← pénalité forte, évite la division par zéro

        sinon :
            r                = cov(p,t) / (std_p × std_t), borné [-1, 1]
            correlation_loss = 1 - r                         (0 = parfait)
            fitness          = 5.0 × correlation_loss
                             + mse / (1 + mse)               (borné [0, 1))

    Une valeur plus basse est toujours meilleure (convention inchangée).
    Les garde-fous NumPy (_np_safe_div, _np_safe_pow) restent actifs via
    evaluate_vector → _to_np_code → fonctions sécurisées.
    """
    xs_np = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
    ys_np = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)

    # [CUSTOM-LOSS] Si une fonction de coût est fournie, elle REMPLACE
    # entièrement le calcul hybride MSE/corrélation. Le linear scaling est
    # ignoré (il suppose le MSE supervisé). La loss reçoit (preds, X, y) et
    # doit renvoyer un scalaire à minimiser. Toute erreur/non-fini → pénalité.
    # [CUSTOM-LOSS PARSIMONY] Si _CUSTOM_LOSS_PARSIMONY > 0, on ajoute une
    # pénalité proportionnelle à la taille de l'arbre : rasoir d'Ockham qui
    # favorise les lois simples et neutralise les arbres-monstres exploitant
    # les imperfections numériques (crucial pour la découverte de lois).
    if state._CUSTOM_LOSS_FN is not None:
        try:
            with np.errstate(all='ignore'):
                preds = _predict_cached(node, xs_np)
                # [CUSTOM-LOSS SCALING] En mode supervisé (régression robuste,
                # quantile...), on cale a + b·preds vers y AVANT d'appeler la
                # loss. Le scaling MSE en forme fermée donne déjà de bons a,b
                # même pour une loss robuste, et débloque la calibration des
                # coefficients (sinon le GP peine à trouver la bonne droite).
                # Désactivé par default (non-supervisé / invariants).
                if getattr(state, '_CUSTOM_LOSS_USE_SCALING', False) and float(np.std(preds)) > 1e-9:
                    if getattr(state, '_CUSTOM_LOSS_ROBUST', False):
                        a_ls, b_ls, _ok = _robust_scale_params(preds, ys_np)
                    else:
                        a_ls, b_ls, _ok = _linear_scale_params(preds, ys_np)
                    if _ok:
                        preds = a_ls + b_ls * preds
                val = float(state._CUSTOM_LOSS_FN(preds, xs_np, ys_np))
            if not math.isfinite(val):
                return 1000.0
            _pars = getattr(state, '_CUSTOM_LOSS_PARSIMONY', 0.0)
            if _pars > 0.0:
                val += _pars * tree_size(node)
            return val
        except Exception:
            return 1000.0

    try:
        with np.errstate(all='ignore'):    # [V42-FIX] silencer les overflow sur trajectoires
            preds     = _predict_cached(node, xs_np)
            residuals = preds - ys_np
            mse       = float(np.mean(residuals ** 2))
        std_p     = float(preds.std())
        r         = _pearson_r(preds, ys_np) if std_p >= 1e-6 else 0.0

        if std_p < 1e-6:
            # Arbre constant → pénalité pour décourager les constantes pures.
            # [SYRACUSE] Pénalité triplée : sur les données Collatz normalisées,
            # une constante nulle a MSE≈1.33 → fitness≈3.33 avec +2.0, ce qui
            # est meilleur que tout arbre non-constant à faible corrélation
            # (r≈0.1 → fitness≈5.4). Résultat : les îles restent bloquées sur des
            # constantes indéfiniment. +5.0 corrige ce biais structurel.
            _const_penalty = 5.0 if state._SYRACUSE_MODE else 2.0
            return mse + _const_penalty

        # [v18-LS] MSE calculé sur les prédictions scalées a + b·f(x).
        # b peut être négatif → une anti-corrélation parfaite devient une
        # solution parfaite : la perte de corrélation utilise |r|.
        if state._USE_LINEAR_SCALING:
            a_ls, b_ls, _ok = _linear_scale_params(preds, ys_np)
            if _ok:
                with np.errstate(all='ignore'):
                    _sres = (a_ls + b_ls * preds) - ys_np
                    mse   = float(np.mean(_sres ** 2))
                if not math.isfinite(mse):
                    return 1000.0
            correlation_loss = 1.0 - abs(r)
        else:
            correlation_loss = 1.0 - r
        # mse / (1 + mse) ∈ [0, 1) : comprime les très gros MSE sans les annuler
        fitness_hybrid = (5.0 * correlation_loss) + (mse / (1.0 + mse))
        return fitness_hybrid

    except Exception:
        return 1000.0


def raw_pearson_r(node, xs, ys) -> float:
    """
    [v13.11 — OBJECTIF 2] Retourne la corrélation de Pearson pure (r ∈ [-1, 1])
    du meilleur individu, utilisée par le filtre Anti-Puits-Empoisonné avant
    d'autoriser le dépôt dans les structures stigmergiques.
    Retourne -1.0 en cas d'erreur ou d'arbre constant.
    """
    xs_np = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
    ys_np = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)
    try:
        preds = _predict_cached(node, xs_np)
        if float(preds.std()) < 1e-6:
            return -1.0   # arbre constant → corrélation non définie
        return _pearson_r(preds, ys_np)
    except Exception:
        return -1.0


def _pure_mse(node, xs, ys) -> float:
    """
    [v14.1] Calcule le MSE pur (erreur quadratique moyenne brute) sans aucune
    pondération Pearson ni pénalité de constante.
    Utilisé exclusivement par fitness() pour alimenter le ln(MSE) du BIC.

    Séparé de raw_mse() pour ne pas polluer le BIC avec la valeur hybride
    Pearson+MSE de raw_mse (qui retourne dans [0, 3+] et non un vrai MSE).
    raw_mse() reste inchangé : il continue à servir les logs, PERFECT_THRESHOLD
    et le filtre Anti-Puits-Empoisonné qui ont besoin de la métrique hybride.

    Arbre constant (std_p < 1e-6) : retourne mse + 1000.0 pour garantir un
    BIC fortement positif (rejet), sans risquer de ln(0) si mse est nul.
    """
    xs_np = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
    ys_np = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)
    try:
        preds = _predict_cached(node, xs_np)
        # Arbre constant : std(preds) quasi-nul → pénalité pour BIC
        if float(np.std(preds)) < 1e-6:
            return float(np.mean((preds - ys_np) ** 2)) + 1000.0
        # [v18-LS] Le BIC juge la forme optimalement scalée (cohérent avec raw_mse)
        if state._USE_LINEAR_SCALING:
            a_ls, b_ls, _ok = _linear_scale_params(preds, ys_np)
            if _ok:
                preds = a_ls + b_ls * preds
        with np.errstate(all='ignore'):
            mse = float(np.mean((preds - ys_np) ** 2))
        return mse if math.isfinite(mse) else 1e6
    except Exception:
        return 1e6


def _target_scale(y):
    """[v0.8] Power of ten by which the target is divided during the search
    when its spread is far from 1 (standard deviation outside [1e-3, 1e3],
    or the largest |y| when y is constant). The engine has absolute
    thresholds tuned for targets of ordinary size: up to 0.7, a law whose
    values were of order 1e-9 (a capacitance in farads, an energy in joules
    of one molecule) or 1e20 came back as a constant or a wrong line, with a
    negative R², and no warning. The delivered model, its formula and its
    MSEs are in the units of y; within [1e-3, 1e3] nothing changes."""
    y = np.asarray(y, dtype=float)
    m = float(np.max(np.abs(y))) if y.size else 0.0
    if not (m > 0.0 and np.isfinite(m)):
        return 1.0
    sd = m * float(np.std(y / m))       # sans débordement pour |y| ~ 1e200
    ref = sd if sd > 0 else m
    if not (ref > 0.0 and np.isfinite(ref)) or 1e-3 <= ref <= 1e3:
        return 1.0
    return 10.0 ** round(math.log10(ref))


def _scale_tree(tree, s: float):
    """[v0.8] L'arbre multiplié par s, en repliant s dans les constantes de
    tête quand l'arbre porte déjà sa mise à l'échelle (a + b·f, ou b·f sous
    units=), pour que la constante de tête reste lisible (et que la
    constante déduite par unknown_constant reste la bonne)."""
    if tree is None or s == 1.0:
        return tree
    const = lambda n: (n is not None and n.left is None and n.right is None
                       and not isinstance(n.value, str))
    t = tree.copy()
    if t.value == "*" and const(t.left):
        t.left = Node(float(s) * float(t.left.value))
        return t
    if t.value == "+" and const(t.left) and t.right is not None \
            and t.right.value == "*" and const(t.right.left):
        t.left = Node(float(s) * float(t.left.value))
        t.right.left = Node(float(s) * float(t.right.left.value))
        t.right._hash = t.right._chash = t.right._ehash = None
        return t
    if const(t):
        return Node(float(s) * float(t.value))
    return Node("*", Node(float(s)), t)


def wrap_linear_scaling(node, xs, ys):
    """
    [v18-LS] Matérialise le scaling optimal dans l'arbre :  a + b·f(x).
    Appelé au moment de stocker/afficher un champion, pour que l'EXPR
    imprimée corresponde exactement au MSE rapporté (et pour qu'Adam
    puisse ensuite affiner a et b comme n'importe quelle constante).
    Ne wrappe que si le gain est réel et la forme non dégénérée.

    [v0.4.1] En mode dimensionnel, on materialise `b·f(x)` (SANS offset) au
    lieu de ne rien wrapper. La v0.4 desactivait ce wrap parce que `a + b·f(x)`
    viole l'homogeneite — mais fitness()/raw_mse continuaient, eux, a NOTER les
    candidats sur leur forme scalee. Le champion etait donc choisi sur un score
    scale puis livre non scale : structure correcte, constante fausse, R2
    negatif. Le scaling par l'origine reconcilie les deux.
    """
    if node is None:
        return node
    # [ROBUST] En mode régression robuste, on matérialise le scaling ROBUSTE
    # (IRLS) dans l'arbre final même si le linear scaling MSE est désactivé,
    # pour que l'expression retournée ait les bons coefficients (insensibles
    # aux outliers), pas ceux biaisés par le MSE.
    _robust = getattr(state, '_CUSTOM_LOSS_ROBUST', False)
    if not state._USE_LINEAR_SCALING and not _robust:
        return node.copy()
    xs_np = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
    ys_np = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)
    try:
        with np.errstate(all='ignore'):
            preds = evaluate_vector(node, xs_np)
            if float(np.std(preds)) < 1e-6:
                return node.copy()
            if _robust:
                a_ls, b_ls, _ok = _robust_scale_params(preds, ys_np)
            else:
                a_ls, b_ls, _ok = _linear_scale_params(preds, ys_np)
            if not _ok or (abs(b_ls - 1.0) < 1e-9 and abs(a_ls) < 1e-9):
                return node.copy()
            # En mode robuste, on accepte le wrap sans exiger une baisse du MSE
            # (le MSE peut monter alors que la robustesse s'améliore).
            if not _robust:
                mse_raw = float(np.mean((preds - ys_np) ** 2))
                mse_ls  = float(np.mean((a_ls + b_ls * preds - ys_np) ** 2))
                if not math.isfinite(mse_ls) or mse_ls >= mse_raw - 1e-15:
                    return node.copy()
        if state._LS_SCALE_ONLY:
            # [v0.4.1] Si l'arbre porte deja une constante multiplicative en
            # tete, on FUSIONNE au lieu d'empiler : sans cela le modele livre
            # gagne deux noeuds et une constante redondante (`b · (c · f(x))`),
            # ce qui degrade la lisibilite et fausse la mesure de parcimonie.
            if (node.value == "*" and node.left is not None
                    and isinstance(node.left.value, float)):
                wrapped = node.copy()
                wrapped.left = Node(float(b_ls) * float(node.left.value))
            else:
                wrapped = Node("*", Node(float(b_ls)), node.copy())
        else:
            wrapped = Node("+", Node(float(a_ls)),
                           Node("*", Node(float(b_ls)), node.copy()))
        return simplify(wrapped)
    except Exception:
        return node.copy()


# ============================================================
# [FIX-E] Compteur d'usage de features — biais vers les sous-utilisées
# ============================================================
# Inspiré de GP_SYRACUSE_V16 : maintient un compteur d'utilisation par
# feature et favorise les features peu présentes dans la population.
# Réinitialisation à chaque run via reset_feature_usage().
# Utilisé dans rand_term / random_terminal pour biaiser le tirage.


def reset_feature_usage(n_features: int):
    """Réinitialise le compteur au début d'un run."""
    state._feature_usage_counter = [1] * n_features   # 1 pour éviter div/0

def record_feature_usage(node: "Node", terminals: List[str]):
    """Parcourt un arbre et incrémente les compteurs de features utilisées."""
    if not state._feature_usage_counter:
        return
    stack = [node]
    while stack:
        n = stack.pop()
        if n is None:
            continue
        if isinstance(n.value, str) and n.value in terminals:
            idx = terminals.index(n.value)
            if idx < len(state._feature_usage_counter):
                state._feature_usage_counter[idx] += 1
        if n.left:  stack.append(n.left)
        if n.right: stack.append(n.right)

def get_feature_bias_weights(terminals: List[str]) -> List[float]:
    """
    Poids inversement proportionnels à l'usage — features rares favorisées.
    Retourne une liste de la même longueur que terminals.
    Normalisée autour de 1.0 pour ne pas modifier le taux de tirage global.
    """
    if not state._feature_usage_counter or len(state._feature_usage_counter) < len(terminals):
        return [1.0] * len(terminals)
    total = sum(state._feature_usage_counter[:len(terminals)])
    inv   = [total / (u + 1.0) for u in state._feature_usage_counter[:len(terminals)]]
    s     = sum(inv)
    return [v / s * len(terminals) for v in inv]

def count_distinct_features(node: "Node", terminals: List[str]) -> int:
    """Compte le nombre de features distinctes utilisées dans l'arbre."""
    used  = set()
    stack = [node]
    while stack:
        n = stack.pop()
        if n is None:
            continue
        if isinstance(n.value, str) and n.value in terminals:
            used.add(n.value)
        if n.left:  stack.append(n.left)
        if n.right: stack.append(n.right)
    return len(used)


def fitness(node, xs: List[float], ys: List[float], cfg: Config,
            role: str = "explorer") -> float:
    """
    [v14.4] Fitness conditionnelle par rôle d'île.
    [FIX-A v17] Pénalité mono-feature : force l'exploration multi-variable
    en mode Syracuse — corrige le blocage sur X[2] seul.
    [OPT] Clé de cache incluant gen//10 via cfg._gen_bucket : évite de
    recalculer la fitness d'un individu inchangé pendant 10 générations.
    Inspiré de GP_SYRACUSE_V16 — gain ~25% sur le temps total.
    """
    # [v0.4] GARDE-FOU DIMENSIONNEL — rejette tout arbre physiquement incohérent
    # AVANT toute évaluation, quel que soit le chemin qui l'a produit (mutation
    # sémantique, refill de déduplication, sous-arbres bannis, bibliothèque...).
    # C'est ce point qui garantit l'invariant, pas les opérateurs typés seuls.
    # No-op si FEAT_DIMS is None (chemin v0.3 inchangé).
    if _dim_active(cfg) and not _ds().is_typed_valid(
            node, cfg.FEAT_DIMS, cfg.TARGET_DIM,
            bool(getattr(cfg, "UNKNOWN_CONST", False))):
        TRACE.bump("candidats_rejetes_dim")     # [v0.7]
        return float("inf")

    h   = node.exact_hash()          # [v0.7] exact : voir Node.exact_hash
    # [OPT] Bucket générationnel : même individu → même fitness pendant 10 gens
    gen_bucket = getattr(cfg, '_gen_bucket', 0)
    key = (h, role, gen_bucket)
    if key in state._fitness_cache:
        return state._fitness_cache[key]

    if role == "cleaner" and state._CUSTOM_LOSS_FN is None:
        mse_pur      = _pure_mse(node, xs, ys)
        n            = len(ys)
        k, n_adj     = tree_complexity(node)
        # [v18-LS] Les 2 constantes de scaling + leurs opérateurs (+, *) ne sont
        # pas gratuits pour le rasoir d'Ockham : coût linéaire forfaitaire +4.
        if state._USE_LINEAR_SCALING:
            k += 4
        ln_n         = math.log(n)
        mse_safe     = max(mse_pur, 1e-15)
        score        = (n * math.log(mse_safe)
                        + k * ln_n
                        + _FLOAT_GAMMA * (n_adj ** 2) * ln_n)
    elif state._CUSTOM_LOSS_FN is not None:
        # [CUSTOM-LOSS] Tous les rôles minimisent la loss custom (via raw_mse,
        # qui la court-circuite). On ajoute une légère pénalité de parcimonie
        # pour garder des expressions lisibles, comme pour les explorers.
        base      = raw_mse(node, xs, ys)
        size_pen  = tree_size(node)  * cfg.PARSIMONY
        depth_pen = tree_depth(node) * cfg.DEPTH_PENALTY
        max_pen   = 0.05 * abs(base) + 1e-8
        penalty   = min(size_pen + depth_pen, max_pen)
        score     = base + penalty
    else:
        base      = raw_mse(node, xs, ys)
        size_pen  = tree_size(node)  * cfg.PARSIMONY
        depth_pen = tree_depth(node) * cfg.DEPTH_PENALTY
        max_pen   = 0.05 * base + 1e-8
        penalty   = min(size_pen + depth_pen, max_pen)
        score     = base + penalty

    # [FIX-A] Pénalité mono-feature progressive — active en mode Syracuse N-D.
    # Casse le monopole de X[2] = log(max_h/n) observé systématiquement.
    # La pénalité décroît progressivement pour laisser le GP converger en fin de run
    # sans contraindre trop fortement les expressions finales.
    if state._SYRACUSE_MODE and hasattr(cfg, 'TERMINALS') and len(cfg.TERMINALS) > 1:
        n_feat = count_distinct_features(node, cfg.TERMINALS)
        if n_feat == 0:
            score += 5.0    # constante pure — pénalité forte et stable
        elif n_feat == 1:
            # Décroissance progressive : 0.10 en gen 0 → 0.03 en fin de run
            # Inspiré de GP_SYRACUSE_V16 FIX-A (parsimony_coeff pattern)
            _mono_pen = getattr(cfg, '_mono_pen_cache', None)
            if _mono_pen is None:
                score += 0.08  # valeur par default si gen non disponible
            else:
                score += _mono_pen

    state._fitness_cache[key] = score
    return score
