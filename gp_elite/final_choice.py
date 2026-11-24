"""The final choice of the model: early stop, patience, the hold-out,
the finalists and their polish, the near domain, the rule of one
standard error, and the small tables.

Part of gp_elite/core.py until 1.4.0, moved in 1.5, where it reads and
sets the names of the shared state in gp_elite.state (state.NAME).
"""
from __future__ import annotations

import math
import numpy as np
import time
from typing import Optional, List, Tuple, Dict, Any

from . import state
from .config import (TRACE, _ds)
from .tree import (Node, tree_size)
from .simplification import (simplify)
from .evaluation import (compile_parametric, evaluate_vector)
from .scoring import (_linear_scale_params, _pure_mse, wrap_linear_scaling)
from .fitting import (optimize_constants_adam, optimize_constants_lm)

# ════════════════════════════════════════════════════════════════
# [v21-VAL] VALIDATION HOLD-OUT
# ════════════════════════════════════════════════════════════════
# Pourquoi : jusqu'ici tous les MSE étaient mesurés sur les données
# d'ENTRAÎNEMENT — sur données réelles bruitées, une formule de 25 nœuds
# peut mémoriser le bruit et s'effondrer sur de nouvelles mesures.
# Désormais : split train/val au démarrage, évolution sur train seul,
# suivi séparé du meilleur individu EN VALIDATION, early-stopping et
# sélection finale sur la validation, rapport de généralisation.

                         # interrompu par l'echeance cfg.DEADLINE
# [v0.7-NEAR] GARDE DE STABILITE PRES DU DOMAINE (mode par defaut).
# Constat : sur donnees reelles (210_cloud, validation croisee), un modele a
# donne R2 = -1.7e10 sur des points jamais vus, alors qu'il etait sain sur
# l'entrainement et la validation. La garde hors-plage existante n'agit qu'en
# mode extrapolate=True. Principe retenu : sonder par combinaisons de PAIRES
# de points reels, x = l*xi + (1-l)*xj avec l dans [-0.1, 1.1] -- l'interieur
# de l'enveloppe des donnees plus un leger debordement le long des directions
# ou elles s'etendent vraiment. Une vraie loi ne peut pas diverger la ou des
# mesures existent en continu. Mesure sur les 41 lois du banc Feynman : 0 vraie
# loi jugee instable jusqu'a 10 % de debordement (pire ecart 2.8 etendues de y,
# seuil 50) ; a 20 %, 5/41 le seraient (lois relativistes : la sonde traverse
# v = c). Usage : DEPARTAGE seulement, entre candidats statistiquement
# indiscernables -- jamais un rejet d'un candidat qui se detache.
_NEAR_CACHE = {}
_EXACT_REL = 1e-12           # [v0.7-EXACT] plancher « exact » relatif a var(y_val)

_FAITHFUL_CACHE: Dict[int, bool] = {}


def _formula_faithful(node) -> bool:
    """[v0.8] Vrai si la fonction mathématique de l'arbre (sans garde-fou
    numérique) reproduit l'évaluation du moteur sur les données de
    l'ajustement (entraînement et hold-out, espace normalisé), avec la
    tolérance du contrôle de gp_elite.formula (1e-7 relatif)."""
    xs = [x for x in (state._VAL_TRAIN_XS, state._VAL_XS) if x is not None]
    if node is None or not xs:
        return True
    try:
        key = node.exact_hash()
    except Exception:
        key = None
    if key is not None and key in _FAITHFUL_CACHE:
        return _FAITHFUL_CACHE[key]
    ok = True
    try:
        try:
            from . import formula as _F
        except ImportError:                  # core.py lancé comme script
            import formula as _F
        for X in xs:
            p = np.asarray(evaluate_vector(node, X), dtype=float)
            with np.errstate(all="ignore"):
                v = np.asarray(_F.evaluate(node, X), dtype=float)
                if v.ndim == 0:
                    v = np.full(p.shape, float(v))
                scale = max(float(np.max(np.abs(p))) if p.size else 0.0,
                            float(np.std(p)) if p.size else 0.0, 1e-300)
                gap = np.abs(v - p)
            if not np.all(np.isfinite(gap)) or float(np.max(gap)) > 1e-7 * scale:
                ok = False
                break
    except Exception:
        ok = False
    if key is not None:
        _FAITHFUL_CACHE[key] = ok
    return ok
_NEAR_EXT = 0.10
_NEAR_K = 50.0
# [v25-EXTRAP] Garde-fou anti-divergence : points-sondes AU-DELÀ de la plage
# d'entraînement (axe d'extrapolation prolongé) + bande de plausibilité dérivée
# de y. Un candidat dont la prédiction sort de cette bande sur les sondes est
# rejeté de la sélection — ce que la validation-frontière (interne) ne peut voir.
_VAL_CANDS_MAX = 64

def _early_stop_threshold(cfg, ys_train) -> float:
    """[v0.8] Seuil d'arrêt anticipé, RELATIF à la variance de la cible pour
    les ajustements de l'API.

    Le seuil était un MSE absolu de 1e-6 : il dépendait donc de l'unité de y.
    Sur une cible de variance 0,02 (loi gaussienne de Feynman I.6.20a), un
    modèle à 1 - R² = 6e-5 l'atteignait : la recherche s'arrêtait à la 6e
    génération, puis la sélection parcimonieuse rendait une approximation
    plus courte à 1 - R² = 2e-3, alors que la loi exacte était à portée. En
    unités plus grandes, la même loi n'aurait jamais déclenché l'arrêt. On
    ne s'arrête plus que sur une loi exacte à la précision numérique
    (1 - R² <= _EXACT_REL sur le hold-out), le seul cas où chercher encore
    ne peut rien apporter. Les modes démonstration (Syracuse, batterie)
    gardent leur seuil absolu."""
    if not state._GENERIC_CSV_MODE:
        return cfg.EARLY_STOPPING_MSE
    ref = state._VAL_YS if (state._VAL_YS is not None and len(state._VAL_YS) > 1) else ys_train
    try:
        v = float(np.var(np.asarray(ref, dtype=float)))
    except Exception:
        return cfg.EARLY_STOPPING_MSE
    if not math.isfinite(v) or v <= 1e-300:
        return cfg.EARLY_STOPPING_MSE
    return _EXACT_REL * v


# [v1.2-H1] Arrêt sur patience (benchmarks/results_1.2/PLAN.md, H1).
_PATIENCE_GAIN = 0.01


class _Patience:
    """Compte les générations sans gain. L'erreur lue est celle de l'arrêt
    anticipé (MSE du hold-out, ou du train sans hold-out) ; elle compte comme
    un gain quand elle passe sous (1 - 1 %) fois la meilleure vue dans ce
    run. `spent(err, gen)` est vrai quand `p` générations sont passées sans
    gain : la boucle s'arrête alors comme sur une loi exacte, et le fit va à
    sa fin habituelle. p = 0 (défaut hors API, et toute API avec un budget
    explicite) : jamais vrai, la recherche de 1.1 est inchangée. Chaque
    évolution (redémarrage) a la sienne."""
    __slots__ = ("p", "best", "gen")

    def __init__(self, p):
        self.p = int(p or 0)
        self.best = None
        self.gen = 0

    def spent(self, err, gen):
        if self.p <= 0:
            return False
        if self.best is None or err < self.best * (1.0 - _PATIENCE_GAIN):
            self.best, self.gen = err, gen
            return False
        return gen - self.gen >= self.p


def _holdout_mse(node, xs_train, ys_train) -> float:
    """MSE sur le hold-out si disponible, sinon sur le train (fallback)."""
    if node is None:
        return float("inf")
    if state._VAL_XS is not None:
        try:
            preds = evaluate_vector(node, state._VAL_XS)
            m = float(np.mean((preds - state._VAL_YS) ** 2))
            return m if math.isfinite(m) else float("inf")
        except Exception:
            return float("inf")
    return _pure_mse(node, xs_train, ys_train)

def _is_numerically_stable(cand) -> bool:
    """[v23.1] Un candidat est rejeté de la sélection finale s'il EXPLOSE sur
    le domaine d'ENTRAÎNEMENT complet (pas seulement le hold-out). Un arbre
    avec des chaînes pow imbriquées peut coller aux 34 points de validation
    tout en prédisant des milliers ailleurs : sur-apprentissage que le
    hold-out a manqué. On vérifie que les prédictions restent dans une plage
    cohérente avec la cible observée."""
    if state._VAL_TRAIN_XS is None:
        return True
    try:
        preds = evaluate_vector(cand, state._VAL_TRAIN_XS)
        if not np.all(np.isfinite(preds)):
            return False
        # tolérance : 100× l'amplitude de la cible (généreux mais borne l'explosion)
        amp = max(1e-9, float(np.max(np.abs(state._VAL_TRAIN_YS))) * 100.0 + 10.0)
        if float(np.max(np.abs(preds))) > amp:
            return False
    except Exception:
        return False
    # [v25-EXTRAP] Garde-fou anti-divergence HORS-PLAGE. Le test ci-dessus ne
    # regarde que le domaine d'entraînement ; or l'explosion à l'extrapolation
    # survient AU-DELÀ. On évalue le candidat sur des sondes où l'axe
    # d'extrapolation est prolongé bien après le max vu, et on exige que la
    # prédiction reste dans une bande de plausibilité dérivée de y. Une droite
    # (ou toute forme bornée par linéaire) passe ; exp/pow/cube/x² sont rejetés.
    if state._EXTRAP_PROBE_XS is not None and state._EXTRAP_BAND is not None:
        try:
            p2 = evaluate_vector(cand, state._EXTRAP_PROBE_XS)
            if not np.all(np.isfinite(p2)):
                return False
            lo, hi = state._EXTRAP_BAND
            if float(np.min(p2)) < lo or float(np.max(p2)) > hi:
                return False
        except Exception:
            return False
    return True

def _track_val_candidate(cand):
    """Enregistre tout candidat-champion avec son MSE de validation et
    l'erreur-type (SE) de ce MSE. La sélection finale applique la règle
    du 1-écart-type : parmi les candidats statistiquement indistinguables
    du meilleur (val_mse ≤ best + SE_best), le PLUS PETIT arbre gagne —
    on livre une loi lisible, pas un monstre qui gratte 1e-6.
    [v23.1] Les candidats numériquement instables sur le domaine complet
    sont écartés (overfitting que le hold-out peut manquer)."""
    if cand is None or state._VAL_XS is None:
        return
    # [v0.4] Le pool de validation alimente la SELECTION FINALE (_select_one_se)
    # sans repasser par fitness() : sans ce filtre, un candidat dimensionnellement
    # invalide peut etre repeche comme modele final. On ferme la fuite ici.
    if state._DIM_GATE_DIMS is not None:
        try:
            if not _ds().is_typed_valid(cand, state._DIM_GATE_DIMS, state._DIM_GATE_TARGET,
                                        state._DIM_UNKNOWN_CONST):
                return
        except Exception:
            return
    if not _is_numerically_stable(cand):
        return
    try:
        preds = evaluate_vector(cand, state._VAL_XS)
        se_sq = (preds - state._VAL_YS) ** 2
        m = float(np.mean(se_sq))
        if not math.isfinite(m):
            return
        se = float(np.std(se_sq, ddof=1) / math.sqrt(len(se_sq))) \
             if len(se_sq) > 1 else 0.0
        state._VAL_CANDS.append((m, se, tree_size(cand), cand.copy()))
        if len(state._VAL_CANDS) > _VAL_CANDS_MAX:
            state._VAL_CANDS.sort(key=lambda t: (t[0], t[2]))
            del state._VAL_CANDS[_VAL_CANDS_MAX:]
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════
# [v0.8] POLISSAGE DES FINALISTES : convergence, et sommes pondérées
# ════════════════════════════════════════════════════════════════
# Constat (campagne 2, 205 ajustements Feynman à 30 s) : des structures
# justes sortaient avec des constantes inexactes. Feynman I.8.14,
# sqrt((x2-x1)² + (y2-y1)²), revenait 5 fois sur 5 sous la forme
# sqrt((x2' - x3')² + (x1' - x0')²) sur les colonnes normalisées : la
# structure est la bonne, mais x/max|x| donne à chaque colonne son propre
# facteur (4,97 ; 4,99...), si bien qu'une différence de deux colonnes
# demande un coefficient sur chaque terme, que l'arbre n'avait pas
# (1 - R² = 1,8e-4). Même cas pour II.2.42, k·(T2-T1)·A/d. Et II.15.4
# rendait -μ·B·sin(-10,985 - 1,00432·θ) : la bonne forme, des constantes
# que 20 itérations de Levenberg-Marquardt n'avaient pas fini d'ajuster.
# Le polissage final ajoute donc deux candidats par finaliste : le même
# arbre, ses constantes ajustées jusqu'à convergence (100 itérations), et
# l'arbre dont chaque terme de somme ou de différence reçoit son propre
# coefficient (A ± B devient a·A ± b·B), ajusté de même. Ces candidats ne
# changent pas la recherche, et n'entrent dans la sélection finale que s'ils
# reproduisent le hold-out à la précision numérique (_track_if_exact) : le
# polissage rend exacte une structure juste, il ne remplace jamais un modèle
# approché par un autre (campagne 5 : sans cette règle, des variantes plus
# ajustées gagnaient la sélection et extrapolaient moins bien).

_FINAL_LM_ITER = 100          # itérations de LM pour les finalistes
_WEIGHTED_SUMS_MAX = 6        # au-delà de 6 sommes, pas de variante pondérée
# [v0.8] Avec time_limit=, les variantes du polissage (convergence, sommes
# pondérées) cessent une seconde après l'échéance : sur 3 000 lignes elles
# prenaient près de deux secondes, que time_limit_check.py voyait dépasser
# l'échéance (18,5 s pour 15 s). La correction d'échelle, elle, est toujours
# faite. Sans échéance, rien ne change.


def _has_scale(t) -> bool:
    """Vrai si le terme porte déjà un coefficient (constante, ou produit
    dont un facteur est une constante)."""
    if t.left is None and t.right is None:
        return not isinstance(t.value, str)
    if t.value == "*":
        for c in (t.left, t.right):
            if c is not None and c.left is None and c.right is None \
                    and not isinstance(c.value, str):
                return True
    return False


def _weight_sums(node, innermost_only: bool = False) -> Optional["Node"]:
    """Copie de l'arbre où chaque terme d'une somme ou d'une différence
    reçoit un coefficient 1 (A ± B devient 1·A ± 1·B), sauf un terme qui
    en porte déjà un. Avec innermost_only, seules les sommes dont les
    termes ne contiennent aucune autre somme sont pondérées : c'est assez
    pour sqrt((x2-x1)² + (y2-y1)²), avec deux coefficients de moins.
    None s'il n'y a rien à pondérer, ou plus de _WEIGHTED_SUMS_MAX sommes."""
    n_sums = [0]
    n_new = [0]

    def rebuild(n):
        """Rend (copie, contient une somme)."""
        if n.left is None and n.right is None:
            return Node(n.value), False
        l, hl = rebuild(n.left) if n.left is not None else (None, False)
        r, hr = rebuild(n.right) if n.right is not None else (None, False)
        is_sum = n.value in ("+", "-") and l is not None and r is not None
        if is_sum:
            n_sums[0] += 1
            if not (innermost_only and (hl or hr)):
                if not _has_scale(l):
                    l = Node("*", Node(1.0), l); n_new[0] += 1
                if not _has_scale(r):
                    r = Node("*", Node(1.0), r); n_new[0] += 1
        return Node(n.value, l, r), (is_sum or hl or hr)

    try:
        out, _ = rebuild(node)
    except RecursionError:
        return None
    if n_new[0] == 0 or n_sums[0] > _WEIGHTED_SUMS_MAX:
        return None
    return out


def _lm_to_convergence(node, xs, ys, cfg) -> Optional["Node"]:
    """LM avec _FINAL_LM_ITER itérations ; None si l'ajustement n'a rien
    amélioré (optimize_constants_lm rend alors l'arbre d'entrée)."""
    old = getattr(cfg, "CONST_OPT_ITER", 20)
    try:
        cfg.CONST_OPT_ITER = max(int(old), _FINAL_LM_ITER)
        out = optimize_constants_lm(node, xs, ys, cfg)
    except Exception:
        return None
    finally:
        cfg.CONST_OPT_ITER = old
    if out is None or out.exact_hash() == node.exact_hash():
        return None
    return out


def _refit_scaling(tree, xs, ys):
    """[v0.8] Recale l'échelle et le décalage matérialisés d'un arbre après
    un ajustement de LM en projection variable. LM ajuste les constantes de
    la forme a' + b'·arbre ; un arbre qui porte déjà sa mise à l'échelle
    (a + b·f, rendue par wrap_linear_scaling) gardait donc l'ancien a et
    l'ancien b, et ses prédictions brutes n'étaient plus celles de la forme
    ajustée (sur y = 3 sin(2x) + 1 : MSE 0,39 avant LM, 271 après, 2e-31
    pour la forme mise à l'échelle). Les nouveaux a, b sont replacés dans
    les constantes existantes, sinon l'arbre est enveloppé."""
    if tree is None or not (state._USE_LINEAR_SCALING and state._CUSTOM_LOSS_FN is None):
        return tree
    try:
        xs_np = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
        ys_np = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)
        with np.errstate(all="ignore"):
            p = evaluate_vector(tree, xs_np)
            if float(np.std(p)) < 1e-6:
                return tree
            a2, b2, ok = _linear_scale_params(p, ys_np)
        if not ok or (abs(b2 - 1.0) < 1e-12 and abs(a2) < 1e-12):
            return tree
        const = lambda n: (n is not None and n.left is None and n.right is None
                           and not isinstance(n.value, str))
        t = tree.copy()
        if state._LS_SCALE_ONLY:
            if t.value == "*" and const(t.left):
                t.left = Node(float(b2) * float(t.left.value))
                return t
        elif t.value == "+" and const(t.left) and t.right is not None \
                and t.right.value == "*" and const(t.right.left):
            t.left = Node(float(a2) + float(b2) * float(t.left.value))
            t.right.left = Node(float(b2) * float(t.right.left.value))
            t.right._hash = t.right._chash = t.right._ehash = None
            return t
        return wrap_linear_scaling(tree, xs_np, ys_np)
    except Exception:
        return tree


def _finalists(cfg, k: int = 8) -> list:
    """Les candidats à polir : les k meilleurs sur le hold-out (0.7), et,
    avec le polissage, les k plus petits de la bande de tolérance où la
    sélection finale choisira. [v0.8] Sans ces derniers, la structure juste
    de I.8.14 (14 nœuds, 1 - R² = 1,8e-4) n'était jamais polie : les huit
    meilleurs sur le hold-out étaient des arbres de 48 à 68 nœuds, et la
    règle de parcimonie livrait ensuite le 14 nœuds tel quel."""
    ranked = sorted(state._VAL_CANDS, key=lambda t: (t[0], t[2]))
    top = ranked[:k]
    if not ranked or not bool(getattr(cfg, "FINAL_POLISH", True)):
        return top
    var_val = float(np.var(state._VAL_YS)) if (state._VAL_YS is not None and len(state._VAL_YS) > 1) else 0.0
    tol_r2 = float(getattr(state, 'VAL_R2_TOLERANCE', 0.003))
    best_mse, best_se = ranked[0][0], ranked[0][1]
    band = tol_r2 * var_val if var_val > 1e-15 else best_mse * 0.20
    thr = best_mse + max(best_se, band)
    seen = set()
    for t in top:
        try:
            seen.add(t[3].exact_hash())
        except Exception:
            pass
    small = []
    for t in sorted((t for t in ranked if t[0] <= thr), key=lambda t: (t[2], t[0])):
        try:
            h = t[3].exact_hash()
        except Exception:
            continue
        if h in seen:
            continue
        seen.add(h)
        small.append(t)
        if len(small) >= k:
            break
    return top + small




def _track_if_exact(cand) -> None:
    """[v0.8] Un candidat du polissage n'entre dans la sélection finale que
    s'il reproduit le hold-out à la précision numérique (le plancher sous
    lequel la sélection ne garde que des lois exactes, _EXACT_REL). Le
    polissage peut ainsi rendre exacte une structure juste, mais il ne
    remplace jamais un modèle approché par un autre modèle approché : sur des
    données mesurées, aucune variante n'atteint ce plancher, et le résultat
    est celui qu'on aurait eu sans lui. (Mesuré dans la campagne 5 : sans
    cette règle, des variantes plus ajustées gagnaient la sélection sur le
    hold-out et extrapolaient moins bien.)"""
    if cand is None or state._VAL_XS is None or state._VAL_YS is None or len(state._VAL_YS) < 2:
        return
    var_val = float(np.var(state._VAL_YS))
    if not var_val > 1e-15:
        return
    try:
        with np.errstate(all="ignore"):
            m = float(np.mean((evaluate_vector(cand, state._VAL_XS) - state._VAL_YS) ** 2))
    except Exception:
        return
    if math.isfinite(m) and m <= _EXACT_REL * var_val:
        state._POLISH_ADMITTED = state._POLISH_ADMITTED + 1
        _track_val_candidate(cand)


def _polish_finalists(top, xs, ys, cfg) -> None:
    """Polissage des finalistes avant la sélection finale (voir plus haut).
    Le premier candidat de chaque finaliste est celui de la 0.7 (constantes
    ajustées par optimize_constants_adam, donc LM à 20 itérations), recalé
    par _refit_scaling."""
    _dl = getattr(cfg, "DEADLINE", None)
    _stop = None if _dl is None else max(time.time(), float(_dl)) + state._POLISH_GRACE_S
    for _m, _se, _sz, nd in top:
        pol = _refit_scaling(optimize_constants_adam(nd.copy(), xs, ys, cfg),
                             xs, ys)
        _track_val_candidate(pol)
        if not bool(getattr(cfg, "FINAL_POLISH", True)) or state._CUSTOM_LOSS_FN is not None:
            continue
        if _stop is not None and time.time() > _stop:
            continue                            # budget de temps épuisé
        try:
            conv = _lm_to_convergence(pol, xs, ys, cfg)
            if conv is not None:
                _track_if_exact(_refit_scaling(conv, xs, ys))
            seen = set()
            for inner in (True, False):
                wt = _weight_sums(pol, innermost_only=inner)
                if wt is None or wt.exact_hash() in seen:
                    continue
                seen.add(wt.exact_hash())
                wt = _lm_to_convergence(wt, xs, ys, cfg)
                if wt is not None:
                    ws = simplify(wt)
                    if _pure_mse(ws, xs, ys) <= _pure_mse(wt, xs, ys):
                        wt = ws
                    _track_if_exact(_refit_scaling(wt, xs, ys))
        except Exception:
            pass

def _build_near_probes(xs_np, ys_np, n=400):
    """[v0.7-NEAR] Sondes par paires de points reels. Generateur DEDIE : ne
    consomme pas l'etat aleatoire global du moteur (sinon tous les resultats
    changeraient, garde active ou non)."""
    Xm = xs_np if xs_np.ndim == 2 else xs_np.reshape(-1, 1)
    if len(Xm) < 2:
        return
    rng = np.random.RandomState(20260924)
    i = rng.randint(0, len(Xm), n); j = rng.randint(0, len(Xm), n)
    lam = rng.uniform(-_NEAR_EXT, 1.0 + _NEAR_EXT, (n, 1))
    state._NEAR_PROBE_XS = lam * Xm[i] + (1.0 - lam) * Xm[j]
    y = np.asarray(ys_np, dtype=float)
    r = float(np.ptp(y)) if len(y) else 0.0
    state._NEAR_BAND = (float(np.median(y)), _NEAR_K * max(r, 1e-12))


def _near_domain_stable(cand) -> bool:
    """[v0.7-NEAR] Vrai si le candidat reste fini et dans la bande sur les
    sondes pres du domaine. Resultat mis en cache par arbre EXACT."""
    if state._NEAR_PROBE_XS is None or state._NEAR_BAND is None or cand is None:
        return True
    try:
        key = cand.exact_hash()
    except Exception:
        key = None
    if key is not None and key in _NEAR_CACHE:
        return _NEAR_CACHE[key]
    try:
        with np.errstate(all="ignore"):
            p = np.asarray(evaluate_vector(cand, state._NEAR_PROBE_XS), dtype=float)
        if p.ndim == 0:
            p = np.full(len(state._NEAR_PROBE_XS), float(p))
        c, half = state._NEAR_BAND
        ok = bool(np.all(np.isfinite(p)) and float(np.max(np.abs(p - c))) <= half)
    except Exception:
        ok = False
    if key is not None:
        _NEAR_CACHE[key] = ok
    return ok


def _select_one_se(champion, champ_val):
    """[v23.2] Sélection parcimonieuse par TOLÉRANCE R².

    Principe (philosophie 1-SE, version interprétable) : parmi tous les
    candidats stables dont la qualité d'ajustement est SCIENTIFIQUEMENT
    indistinguable du meilleur, on livre le PLUS PETIT arbre — une loi
    lisible plutôt qu'un arbre gonflé qui gratte un epsilon sur 34 points.

    Le seuil n'est plus un ratio de MSE (sans signification d'un problème à
    l'autre) mais une tolérance exprimée en R² : un candidat qualifie si sa
    perte de R² par rapport au meilleur est ≤ VAL_R2_TOLERANCE (0.3% par
    default), OU s'il est dans la barre d'1 erreur-type statistique du
    meilleur (le plus large des deux). Cas batterie : le 10-nœuds (R²=0.9973)
    et le 29-nœuds (R²=0.9981) diffèrent de 0.08% → le 10-nœuds gagne."""
    pool = list(state._VAL_CANDS)
    if champion is not None and math.isfinite(champ_val) and _is_numerically_stable(champion):
        pool.append((champ_val, 0.0, tree_size(champion), champion))
    if not pool:
        # [v25-EXTRAP] Tout a été rejeté par le garde anti-divergence (aucune
        # forme bornée trouvée) : on retombe sur le champion brut faute de mieux.
        return champion, champ_val
    pool.sort(key=lambda t: t[0])
    best_mse, best_se = pool[0][0], pool[0][1]
    # Variance de la cible de validation → conversion MSE ↔ R²
    var_val = float(np.var(state._VAL_YS)) if (state._VAL_YS is not None and len(state._VAL_YS) > 1) else 0.0
    tol_r2  = float(getattr(state, 'VAL_R2_TOLERANCE', 0.003))   # 0.3 % de R²
    # Seuil = best + max(barre statistique 1-SE, bande de tolérance R²)
    r2_band = tol_r2 * var_val if var_val > 1e-15 else best_mse * 0.20
    thr = best_mse + max(best_se, r2_band)
    # [v0.7-EXACT] PRIORITÉ À L'EXACTITUDE. La tolérance R² existe pour ne
    # pas surajuster le BRUIT. Quand le meilleur candidat reproduit le
    # hold-out à la précision numérique (MSE <= 1e-12 x variance : aucune
    # donnée mesurée n'y arrive, seule une loi exacte sur données non
    # bruitées), il n'y a pas de bruit à éviter : on ne remplace pas la loi
    # exacte par une approximation plus courte (vu sur Feynman I.18.12 :
    # r*F*sin(th) exacte dans le front, rendu 0.0776 + 0.9967*r*F*sin(1.0106*th)).
    # Seuls les candidats eux aussi exacts restent éligibles ; le plus petit
    # gagne. Sans effet dès que le meilleur MSE dépasse ce plancher.
    exact_floor = _EXACT_REL * var_val
    if var_val > 1e-15 and best_mse <= exact_floor:
        loose = min((t for t in pool if t[0] <= thr), key=lambda t: (t[2], t[0]))
        thr = exact_floor
        tight = min((t for t in pool if t[0] <= thr), key=lambda t: (t[2], t[0]))
        if tight[3] is not loose[3]:
            state._EXACT_PRIORITY_SWAPS = state._EXACT_PRIORITY_SWAPS + 1
            TRACE.set("exact_priority", "loi exacte préférée à une "
                      "approximation plus courte")
    eligible = [t for t in pool if t[0] <= thr]
    eligible.sort(key=lambda t: (t[2], t[0]))   # plus petit, puis meilleur MSE
    # [v0.8] DEPARTAGE PAR LA FIDÉLITÉ DE LA FORMULE. Parmi les candidats que
    # les données ne savent pas distinguer, on préfère le plus petit dont la
    # formule imprimée reproduit le modèle, c'est-à-dire sur lequel aucun
    # garde-fou numérique (division protégée, puissance bornée) n'agit sur
    # les données : sinon la formule livrée s'écarte de predict() et
    # l'utilisateur reçoit un avertissement (formula_exact False). Stable
    # près du domaine d'abord, comme ci-dessous.
    if not (_formula_faithful(eligible[0][3])
            and _near_domain_stable(eligible[0][3])):
        both = [t for t in eligible
                if _formula_faithful(t[3]) and _near_domain_stable(t[3])]
        if both:
            state._FAITHFUL_SWAPS = state._FAITHFUL_SWAPS + 1
            TRACE.set("faithful_formula", "candidat dont la formule reproduit "
                      "le modèle préféré à un équivalent plus court")
            m, _, _, node = both[0]
            return node, m
    # [v0.7-NEAR] DEPARTAGE : parmi les candidats que les donnees ne savent pas
    # distinguer, le plus petit qui NE DIVERGE PAS pres du domaine. Si aucun
    # n'est stable, comportement historique inchange.
    if not _near_domain_stable(eligible[0][3]):
        stable = [t for t in eligible if _near_domain_stable(t[3])]
        if stable:
            state._NEAR_GUARD_SWAPS = state._NEAR_GUARD_SWAPS + 1
            TRACE.set("near_guard", "champion divergent pres du domaine "
                      "remplace par un candidat equivalent stable")
            m, _, _, node = stable[0]
            return node, m
    m, _, _, node = eligible[0]
    return node, m

# ════════════════════════════════════════════════════════════════
# [1.4-S1] SOUS 30 LIGNES, LES CANDIDATS EN VALIDATION CROISÉE
# ════════════════════════════════════════════════════════════════
# Constat (benchmarks/results_1.4/analysis/README.md) : sous 30 lignes le
# moteur ne garde pas de hold-out (_split_holdout). Il ne suivait alors aucun
# candidat, ne polissait aucun finaliste, n'appliquait aucune règle de
# parcimonie : il rendait le meilleur individu de la recherche sur les
# lignes d'entraînement. Sur les tables de TP (10 et 20 points), la lentille
# revenait dans 2 ajustements sur 40 alors que sa graine était placée, et
# toute loi rendue sans unités portait une constante additive que seule la
# loi de Newton a. S1 (benchmarks/results_1.4/PLAN.md) :
# - les candidats : les huit meilleures formes de famille de l'étage
#   tolérant qui expliquent au moins la moitié de la variance (sans le seuil
#   de 1,5 %), placées au départ et gardées pour la fin ; les champions de
#   la recherche sur les lignes d'entraînement (64 au plus) ; et des
#   variantes de chaque finaliste, sans la constante additive de la mise à
#   l'échelle finale, et avec chaque exposant ajusté mis au demi-entier le
#   plus proche (écrit dans la structure) ;
# - 40 finalistes au plus : le champion, les formes de famille, les 8
#   meilleurs de la recherche, les 8 plus petits de la bande de tolérance,
#   et leurs variantes ;
# - la validation croisée : K = min(n, 10) plis, la ligne i dans le pli
#   i mod K (aucun tirage) ; pour chaque pli, les constantes du candidat
#   sont ajustées de nouveau sur les autres lignes, et ses erreurs au carré
#   sur les lignes du pli gardées ; son erreur est leur moyenne sur la table ;
# - le choix : parmi les candidats à une erreur type du meilleur, ou dans la
#   tolérance de 0,003 en R², celui qui a le moins de constantes ajustées
#   (le rang de la jacobienne de ses prédictions : une constante que
#   l'ajustement ne peut pas bouger seule ne compte pas), puis le plus
#   petit, puis le plus précis ; la priorité à une loi exacte et les
#   départages d'aujourd'hui (formule fidèle, stable près du domaine) sont
#   gardés ;
# - result.pareto tient le front de ces candidats par taille et erreur
#   croisée ;
# - la validation croisée s'arrête une seconde après l'échéance de
#   time_limit=, comme le polissage ; elle ne tourne pas avec une perte
#   personnalisée, en mode extrapolation, ni sous 6 lignes.
# Rien ne change pour une table de 30 lignes ou plus.

# Non adopté (campagne S1, 13 novembre 2026, benchmarks/results_1.4/s1/
# campaign/README.md) : la loi revient dans 113 ajustements de TP sur 200
# contre 126, la validation croisée favorisant des structures que la
# recherche a choisies sur les mêmes points. Retiré du candidat : éteint, le
# code gardé pour la décision de l'auteur.
_SMALL_ROWS = 30                  # en dessous : pas de hold-out, S1
_SMALL_MIN_ROWS = 6
_SMALL_FAMILY_KEEP = 8
_SMALL_FAMILY_SHARE = 0.5         # part de variance laissée au plus
_SMALL_SEARCH = 8                 # meilleurs, et plus petits de la bande
_SMALL_FINALISTS = 40
_SMALL_FOLDS = 10
_SMALL_CANDS_MAX = 64
_SMALL_CANDS: list = []           # [(mse_train, se, taille, arbre)]
_SMALL_FAMILY: list = []          # formes de famille (arbres sans échelle)
_SMALL_FRONT: list = []           # [(mse_cv, se_cv, taille, arbre, n_par, origine)]


def _small_setup(cfg, ys) -> None:
    """[1.4-S1] Au début d'un ajustement, après _split_holdout : S1 est-il
    actif ? Seulement sans hold-out : une table de 30 à 37 lignes en garde
    un, et son reste d'entraînement, sous 30 lignes, n'est pas concerné."""
    _SMALL_CANDS.clear()
    _SMALL_FAMILY.clear()
    _SMALL_FRONT.clear()
    n = len(ys)
    state._SMALL_ON = bool(state._SMALL_CV and state._GENERIC_CSV_MODE and state._VAL_XS is None
                     and _SMALL_MIN_ROWS <= n < _SMALL_ROWS
                     and state._USE_LINEAR_SCALING and state._CUSTOM_LOSS_FN is None
                     and not bool(getattr(cfg, "EXTRAPOLATION_MODE", False)))


def _track_small_candidate(cand, xs, ys) -> None:
    """[1.4-S1] Un champion de la recherche, noté sur les lignes
    d'entraînement (sous units=, seulement s'il passe la porte)."""
    if not state._SMALL_ON or cand is None:
        return
    if state._DIM_GATE_DIMS is not None:
        try:
            if not _ds().is_typed_valid(cand, state._DIM_GATE_DIMS, state._DIM_GATE_TARGET,
                                        state._DIM_UNKNOWN_CONST):
                return
        except Exception:
            return
    try:
        h = cand.exact_hash()
        if any(t[3].exact_hash() == h for t in _SMALL_CANDS):
            return
        X = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
        y = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)
        with np.errstate(all="ignore"):
            e = (np.asarray(evaluate_vector(cand, X), dtype=float) - y) ** 2
        m = float(np.mean(e))
        if not math.isfinite(m):
            return
        se = float(np.std(e, ddof=1) / math.sqrt(len(e))) if len(e) > 1 else 0.0
        _SMALL_CANDS.append((m, se, tree_size(cand), cand.copy()))
        if len(_SMALL_CANDS) > _SMALL_CANDS_MAX:
            _SMALL_CANDS.sort(key=lambda t: (t[0], t[2]))
            del _SMALL_CANDS[_SMALL_CANDS_MAX:]
    except Exception:
        pass


def _small_is_const(n) -> bool:
    return (n is not None and n.left is None and n.right is None
            and not isinstance(n.value, str))


def _small_strip(t):
    """[1.4-S1] L'arbre sans la mise à l'échelle que la recherche a
    matérialisée (a + b·f, b·f, a + f) : f. L'arbre lui-même sinon."""
    if t is None or t.left is None or t.right is None:
        return t
    if t.value == "+":
        for c, o in ((t.left, t.right), (t.right, t.left)):
            if _small_is_const(c):
                if o.value == "*" and o.left is not None and o.right is not None:
                    if _small_is_const(o.left):
                        return o.right
                    if _small_is_const(o.right):
                        return o.left
                return o
    if t.value == "*":
        if _small_is_const(t.left):
            return t.right
        if _small_is_const(t.right):
            return t.left
    return t


def _small_round_powers(f):
    """[1.4-S1] Copie de f où chaque pow(B, c) d'exposant constant c reçoit
    le demi-entier le plus proche, écrit dans la structure (carrés, cubes,
    racines, produits, 1/…) pour que l'ajustement ne le déplace plus. None si
    rien ne change ou si le pool n'a pas les opérateurs nécessaires."""
    uops, bops = set(state._GENERIC_UNARY_OPS), set(state._GENERIC_BINARY_OPS)
    changed = [False]

    def power(B, e2):
        def ipow(m):
            if m == 1:
                return B.copy()
            if m == 2 and "sq" in uops:
                return Node("sq", B.copy())
            if m == 3 and "cube" in uops:
                return Node("cube", B.copy())
            if m % 2 == 0:
                h = ipow(m // 2)
                return Node("sq", h) if "sq" in uops else Node("*", h, ipow(m // 2))
            return Node("*", B.copy(), ipow(m - 1))
        n_int, half = divmod(abs(e2), 2)
        parts = []
        if n_int:
            parts.append(ipow(n_int))
        if half:
            if "sqrt" not in uops:
                return None
            parts.append(Node("sqrt", B.copy()))
        out = parts[0]
        for q in parts[1:]:
            if "*" not in bops:
                return None
            out = Node("*", out, q)
        if e2 < 0:
            if "/" not in bops:
                return None
            out = Node("/", Node(1.0), out)
        return out

    def rec(n):
        if n is None:
            return None
        if n.value == "pow" and n.left is not None and _small_is_const(n.right):
            c = float(n.right.value)
            e2 = int(round(2.0 * c))
            base = rec(n.left)
            if abs(e2) <= 12 and math.isfinite(c):
                if e2 == 0:
                    changed[0] = True
                    return Node(1.0)
                q = power(base, e2)
                if q is not None:
                    changed[0] = True
                    return q
            return Node("pow", base, Node(c))
        return Node(n.value, rec(n.left), rec(n.right))

    try:
        out = rec(f)
    except RecursionError:
        return None
    return out if changed[0] else None


def _small_fit(f, X, y, cfg, scale_only):
    """[1.4-S1] f ajusté sur (X, y) par l'étape de finition du moteur, en
    projection variable sur a + b·f (b·f seul si scale_only), et sa mise à
    l'échelle : (f ajusté, a, b), ou None."""
    keep = state._LS_SCALE_ONLY
    try:
        if scale_only:
            state._LS_SCALE_ONLY = True
        with np.errstate(all="ignore"):
            g = _lm_to_convergence(f, X, y, cfg)
            g = f if g is None else g
            p = np.asarray(evaluate_vector(g, X), dtype=float)
            if p.ndim == 0:
                p = np.full(len(y), float(p))
            if not np.all(np.isfinite(p)):
                return None
            a, b, ok = _linear_scale_params(p, y)
        if not ok or not (math.isfinite(a) and math.isfinite(b)):
            return None
        return g, float(a), float(b)
    except Exception:
        return None
    finally:
        state._LS_SCALE_ONLY = keep


def _small_cv(start, X, y, cfg, scale_only):
    """[1.4-S1] Erreur de validation croisée (moyenne et erreur type des
    erreurs au carré sur les n lignes), plis i mod K, constantes ajustées de
    nouveau sur les autres lignes à chaque pli. None si un pli échoue."""
    n = len(y)
    K = min(n, _SMALL_FOLDS)
    fold = np.arange(n) % K
    err = np.empty(n)
    for k in range(K):
        te = fold == k
        r = _small_fit(start, X[~te], y[~te], cfg, scale_only)
        if r is None:
            return None
        g, a, b = r
        with np.errstate(all="ignore"):
            q = np.asarray(evaluate_vector(g, X[te]), dtype=float)
            e = (a + b * q - y[te]) ** 2
        if not np.all(np.isfinite(e)):
            return None
        err[te] = e
    m = float(np.mean(err))
    se = float(np.std(err, ddof=1) / math.sqrt(n)) if n > 1 else 0.0
    return m, se


def _small_n_par(g, X, scale_only) -> int:
    """[1.4-S1] Le nombre de constantes ajustées d'un candidat : le rang de
    la jacobienne de ses prédictions par rapport à ses constantes et à sa
    mise à l'échelle (b, et a sauf scale_only). Une constante que
    l'ajustement ne peut pas bouger seule (le 1 d'un 1/x, que b absorbe)
    n'y compte pas."""
    n = X.shape[0]
    with np.errstate(all="ignore"):
        p = np.asarray(evaluate_vector(g, X), dtype=float)
        if p.ndim == 0:
            p = np.full(n, float(p))
        cols = [p] if scale_only else [p, np.ones(n)]
        try:
            fn, consts = compile_parametric(g)
        except Exception:
            fn, consts = None, []
        if fn is not None and consts:
            cv = np.array([c.value for c in consts], dtype=float)
            p0 = np.asarray(fn(X, cv), dtype=float)
            for i in range(len(cv)):
                h = 1e-6 * (1.0 + abs(cv[i]))
                c2 = cv.copy()
                c2[i] += h
                cols.append((np.asarray(fn(X, c2), dtype=float) - p0) / h)
        J = np.column_stack([np.broadcast_to(c, (n,)) for c in cols])
        if not np.all(np.isfinite(J)):
            return J.shape[1]
        nrm = np.linalg.norm(J, axis=0)
        J = J[:, nrm > 0] / nrm[nrm > 0]
        if J.shape[1] == 0:
            return 0
        sv = np.linalg.svd(J, compute_uv=False)
    return int(np.sum(sv > 1e-6 * sv[0]))


def _small_materialize(g, a, b, scale_only):
    """[1.4-S1] Le modèle livré : a + b·f, ou b·f, comme
    wrap_linear_scaling l'écrit."""
    if scale_only:
        if g.value == "*" and _small_is_const(g.left):
            w = g.copy()
            w.left = Node(float(b) * float(g.left.value))
            return w
        return Node("*", Node(float(b)), g.copy())
    return simplify(Node("+", Node(float(a)), Node("*", Node(float(b)), g.copy())))


def _small_specs(champion, X, y):
    """[1.4-S1] Les finalistes, 40 au plus, dans l'ordre où ils sont notés :
    (f, scale_only, origine). Le champion d'abord, puis les formes de
    famille, les 8 meilleurs de la recherche, les 8 plus petits de la bande
    de tolérance, chacun suivi de ses variantes."""
    var = float(np.var(y))
    ranked = sorted(_SMALL_CANDS, key=lambda t: (t[0], t[2]))
    bases = []
    if champion is not None:
        bases.append((champion, "champion"))
    for t in _SMALL_FAMILY:
        bases.append((t, "family"))
    for t in ranked[:_SMALL_SEARCH]:
        bases.append((t[3], "search"))
    if ranked:
        thr = ranked[0][0] + max(ranked[0][1], float(
            getattr(state, 'VAL_R2_TOLERANCE', 0.003)) * var)
        small = sorted((t for t in ranked if t[0] <= thr), key=lambda t: (t[2], t[0]))
        for t in small[:_SMALL_SEARCH]:
            bases.append((t[3], "band"))
    modes = (True,) if state._LS_SCALE_ONLY else (False, True)
    specs, seen = [], set()
    for tree, origin in bases:
        f = tree if origin == "family" else _small_strip(tree)
        fr = _small_round_powers(f)
        for g, rounded in ((f, False), (fr, True)):
            if g is None:
                continue
            for so in modes:
                if state._DIM_GATE_DIMS is not None:
                    try:
                        if not _ds().is_typed_valid(Node("*", Node(1.0), g),
                                                    state._DIM_GATE_DIMS, state._DIM_GATE_TARGET,
                                                    state._DIM_UNKNOWN_CONST):
                            continue
                    except Exception:
                        continue
                key = (g.canonical_hash(), so)
                if key in seen:
                    continue
                seen.add(key)
                label = origin + (", exponents rounded" if rounded else "") + \
                    (", without the constant" if so and not state._LS_SCALE_ONLY else "")
                specs.append((g, so, label))
                if len(specs) >= _SMALL_FINALISTS:
                    return specs
    return specs


def _small_table_select(champion, xs, ys, cfg):
    """[1.4-S1] Le modèle d'une table de moins de 30 lignes (voir plus haut).
    Rend le champion si rien n'est noté."""
    X = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
    y = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)
    var = float(np.var(y))
    if not var > 1e-15:
        return champion
    t0 = time.time()
    _dl = getattr(cfg, "DEADLINE", None)
    _stop = None if _dl is None else max(time.time(), float(_dl)) + state._POLISH_GRACE_S
    specs = _small_specs(champion, X, y)
    _SMALL_FRONT.clear()
    for g, so, label in specs:
        if _stop is not None and _SMALL_FRONT and time.time() > _stop:
            break                                 # budget de temps épuisé
        r = _small_fit(g, X, y, cfg, so)
        if r is None:
            continue
        g_all, a, b = r
        cv = _small_cv(g_all, X, y, cfg, so)
        if cv is None:
            continue
        M = _small_materialize(g_all, a, b, so)
        _SMALL_FRONT.append((cv[0], cv[1], tree_size(M), M,
                             _small_n_par(g_all, X, so), label))
    if not _SMALL_FRONT:
        return champion
    pick = _small_choose(_SMALL_FRONT, X, y)
    TRACE.set("small_cv", "%d lignes, K = %d, %d candidats notés en %.2f s ; "
              "choisi : %s, erreur croisée %.3g, %d constantes" % (
                  len(y), min(len(y), _SMALL_FOLDS), len(_SMALL_FRONT),
                  time.time() - t0, pick[5], pick[0], pick[4]))
    return pick[3]


def _small_choose(front, X, y):
    """[1.4-S1] Le choix parmi des candidats notés en validation croisée :
    ceux à une erreur type du meilleur, ou dans la tolérance de 0,003 en R²
    (seulement les exacts si le meilleur l'est), puis le moins de constantes
    ajustées, le plus petit, le plus précis ; départage par la fidélité de la
    formule et la stabilité près du domaine, sur la table. Rend l'entrée."""
    var = float(np.var(y))
    best_m, best_se = min((t[0], t[1]) for t in front)
    thr = best_m + max(best_se, float(getattr(state, 'VAL_R2_TOLERANCE', 0.003)) * var)
    if best_m <= _EXACT_REL * var:                # priorité à l'exactitude
        thr = _EXACT_REL * var
    elig = sorted((t for t in front if t[0] <= thr),
                  key=lambda t: (t[4], t[2], t[0]))
    pick = elig[0]
    # départages : formule fidèle et stable près du domaine, sur la table
    keep = (state._VAL_TRAIN_XS, state._VAL_TRAIN_YS)
    try:
        state._VAL_TRAIN_XS, state._VAL_TRAIN_YS = X, y
        _FAITHFUL_CACHE.clear()
        _NEAR_CACHE.clear()
        _build_near_probes(X, y)
        if not (_formula_faithful(pick[3]) and _near_domain_stable(pick[3])):
            both = [t for t in elig
                    if _formula_faithful(t[3]) and _near_domain_stable(t[3])]
            if both:
                pick = both[0]
    finally:
        state._VAL_TRAIN_XS, state._VAL_TRAIN_YS = keep
        state._NEAR_PROBE_XS = None
        state._NEAR_BAND = None
        _FAITHFUL_CACHE.clear()
        _NEAR_CACHE.clear()
    return pick
