"""The fitting of the constants of a formula: Levenberg-Marquardt and
Adam.

Part of gp_elite/core.py until 1.4.0, moved without change in 1.5.
"""
from __future__ import annotations

import math
import numpy as np

from . import state
from .numeric import (_np_maximum, _np_minimum)
from .tree import (tree_complexity, tree_depth)
from .simplification import (_invalidate_all_hashes)
from .evaluation import (_collect_constants_ordered, _lm_column, _lm_plan,
                         compile_parametric)
from .scoring import (_linear_scale_params, _pure_mse)

def optimize_constants_lm(node: Node,
                          xs: np.ndarray,
                          ys: np.ndarray,
                          cfg: Config) -> Node:
    """
    [v26-LM] Optimisation des constantes par LEVENBERG-MARQUARDT.
    Pourquoi : l'ajustement des constantes d'une expression est un problème de
    MOINDRES CARRÉS — la classe exacte pour laquelle LM est conçu. Adam (1er
    ordre, différences finies) y converge lentement et s'arrête loin de
    l'optimum ; LM exploite la structure JᵀJ du problème et atteint la
    précision machine en 10-30 itérations. C'est le levier n°1 documenté des
    moteurs SR de référence (Operon : LM natif ; PySR : BFGS/NelderMead).
    Coût/itération : (n_consts+1) évaluations vectorisées (Jacobienne par
    différences avant) + résolution d'un système n_consts×n_consts.
    Déterministe (aucun redémarrage bruité) → runs reproductibles.
    [v0.8] Jacobienne incrémentale (_lm_plan) : chaque colonne ne recalcule
    que le chemin de la constante à la racine. Mêmes valeurs bit pour bit.
    """
    child = node.copy()
    y  = np.asarray(ys, dtype=float)
    _varpro = state._USE_LINEAR_SCALING and state._CUSTOM_LOSS_FN is None
    _ls_scale_only = state._LS_SCALE_ONLY
    _ym = float(y.mean())
    _yc = y - _ym
    _LM_NUM_CLIP = 1e150   # [v0.4] borne anti-overflow : au-dela, r@r ou J.T@J
                           # depassent float64. sq/cube/* ne sont pas bornes par
                           # _SAFE_LIMIT et peuvent sortir ~1e217.

    def _resid_p(p):
        p = np.asarray(p, dtype=float)
        if p.ndim == 0:
            p = np.full_like(y, float(p))
        bad = ~np.isfinite(p)
        if bad.any():
            p = np.where(bad, 0.0, p)
            r = p - y
            r[bad] = 1e6          # zone invalide : fortement pénalisée
            return _np_minimum(_np_maximum(r, -_LM_NUM_CLIP), _LM_NUM_CLIP)
        if _varpro:
            # [v0.8] Projection variable : le résidu est celui de la forme
            # MISE À L'ÉCHELLE a + b·f (a, b par moindres carrés à chaque
            # évaluation), celle que juge la fitness. Sans cela, LM ajustait
            # les constantes pour que f seule colle à y, et déformait la
            # forme dès que l'arbre n'avait pas de constante d'échelle libre.
            # Mêmes opérations que _linear_scale_params (moyenne et écart de
            # y calculés une fois ; p est fini ici, ce qui rend son test de
            # finitude redondant avec celui de l'amplitude).
            if _ls_scale_only:
                a_ls, b_ls, ok = _linear_scale_params(p, y)
                if ok:
                    p = a_ls + b_ls * p
            else:
                pm = float(p.mean())
                pc = p - pm
                if not float(np.max(np.abs(pc))) > 1e15:
                    var_p = float(np.dot(pc, pc))
                    if not var_p < 1e-12:
                        b_ls = float(np.dot(pc, _yc)) / var_p
                        a_ls = _ym - b_ls * pm
                        if math.isfinite(a_ls) and math.isfinite(b_ls):
                            p = a_ls + b_ls * p
        return _np_minimum(_np_maximum(p - y, -_LM_NUM_CLIP), _LM_NUM_CLIP)

    # [v0.8] plan incrémental quand il est disponible ; sinon, évaluation
    # complète comme en 0.7 (arbres très profonds, très gros volumes).
    consts = _collect_constants_ordered(child)
    plan = None
    if consts and tree_depth(child) <= 90:
        plan = _lm_plan(child, consts)
        if plan is not None and plan.n_values * max(len(y), 1) > 20_000_000:
            plan = None
    if plan is not None:
        def _eval(cv):
            with np.errstate(all='ignore'):
                p, vals = plan.full(xs, cv)
            return _resid_p(p), vals

        def _column(i, cv, r0, vals):
            if plan.cols[i] is None:          # constante sans effet
                return r0
            with np.errstate(all='ignore'):
                p = _lm_column(plan, i, cv, vals)
            return _resid_p(p)
    else:
        fn, consts = compile_parametric(child)
        if not consts or fn is None:
            return child

        def _eval(cv):
            with np.errstate(all='ignore'):
                p = fn(xs, cv)
            return _resid_p(p), None

        def _column(i, cv, r0, vals):
            return _eval(cv)[0]

    nC = len(consts)
    c  = np.array([cn.value for cn in consts], dtype=float)
    lo_b = float(cfg.ERC_MIN) * 3.0
    hi_b = float(cfg.ERC_MAX) * 3.0

    r, vals = _eval(c)
    sse_best = float(r @ r)
    c_best = c.copy()
    lam = 1e-3
    max_iter = max(20, int(getattr(cfg, "CONST_OPT_ITER", 30)))
    for _ in range(max_iter):
        # Jacobienne par différences avant : J[:, i] = ∂r/∂c_i
        J = np.empty((len(y), nC), dtype=float)
        for i in range(nC):
            h = 1e-6 * (1.0 + abs(c[i]))
            cp = c.copy(); cp[i] += h
            J[:, i] = (_column(i, cp, r, vals) - r) / h
        # [v0.4] jacobienne assainie : sans cela J.T @ J deborde float64
        J = np.nan_to_num(J, nan=0.0,
                          posinf=_LM_NUM_CLIP, neginf=-_LM_NUM_CLIP)
        np.clip(J, -_LM_NUM_CLIP, _LM_NUM_CLIP, out=J)
        g  = J.T @ r                      # gradient (½∇SSE)
        if float(np.max(np.abs(g))) < 1e-14:
            break
        JtJ = J.T @ J
        D = np.diag(np.maximum(np.diag(JtJ), 1e-12))
        stepped = False
        for _try in range(8):             # adaptation du damping λ
            try:
                delta = np.linalg.solve(JtJ + lam * D, -g)
            except np.linalg.LinAlgError:
                lam *= 10.0; continue
            c_new = np.clip(c + delta, lo_b, hi_b)
            r_new, vals_new = _eval(c_new)
            sse_new = float(r_new @ r_new)
            if np.isfinite(sse_new) and sse_new < sse_best:
                rel = (sse_best - sse_new) / max(sse_best, 1e-300)
                c, r, sse_best = c_new, r_new, sse_new
                vals = vals_new
                c_best = c.copy()
                lam = max(lam / 3.0, 1e-12)
                stepped = True
                if rel < 1e-13:           # précision machine atteinte
                    _try = None
                break
            lam *= 4.0
        if not stepped:
            break                          # λ saturé : optimum local atteint
        if _try is None:
            break

    for i, cn in enumerate(consts):
        cn.value = float(c_best[i])
    _invalidate_all_hashes(child)

    # Garde anti-dégénérescence : identique à la voie Adam — on n'accepte que
    # strictement meilleur, sans effondrement de complexité.
    mse_before  = _pure_mse(node,  xs, ys)
    mse_after   = _pure_mse(child, xs, ys)
    k_before, _ = tree_complexity(node)
    k_after,  _ = tree_complexity(child)
    if mse_after >= mse_before or k_after < max(1, k_before * 0.4):
        return node.copy()
    return child


def optimize_constants_adam(node: Node,
                             xs: np.ndarray,
                             ys: np.ndarray,
                             cfg: Config) -> Node:
    """
    Optimisation Adam avec compilateur paramétrique f(_x, _c).
    v14 — gain ×10–50 : une seule compilation par structure,
    les constantes varient dans un array NumPy sans recompilation.
    [v26-LM] Par default, cette fonction DÉLÈGUE à Levenberg-Marquardt
    (optimize_constants_lm), nettement supérieur sur les moindres carrés.
    Mettre cfg.CONST_OPT_LM=False pour revenir à la voie Adam historique.
    """
    if bool(getattr(cfg, "CONST_OPT_LM", True)):
        return optimize_constants_lm(node, xs, ys, cfg)
    child  = node.copy()
    fn, consts = compile_parametric(child)
    if not consts:
        return child

    n_consts = len(consts)
    max_iter = cfg.CONST_OPT_ITER * (2 if n_consts <= 4 else 1)

    lr  = cfg.ADAM_LR
    b1  = cfg.ADAM_BETA1
    b2  = cfg.ADAM_BETA2
    eps = cfg.ADAM_EPS
    h   = 1e-4

    m  = np.zeros(n_consts)
    v2 = np.zeros(n_consts)

    c_arr = np.array([c.value for c in consts], dtype=float)

    if fn is None:
        # Fallback si compilation paramétrique échoue
        return child

    def _mse(c):
        with np.errstate(all='ignore'):
            pred = fn(xs, c)
        pred = np.where(np.isfinite(pred), pred, 0.0)
        return float(np.mean((pred - ys) ** 2))

    best_mse  = _mse(c_arr)
    best_c    = c_arr.copy()
    stagnation = 0

    for t in range(1, max_iter + 1):
        grad = np.zeros(n_consts)
        for i in range(n_consts):
            orig_val = c_arr[i]
            
            # Évaluation de la borne positive (+h) in-place
            c_arr[i] = orig_val + h
            mse_plus = _mse(c_arr)
            
            # Évaluation de la borne négative (-h) in-place
            c_arr[i] = orig_val - h
            mse_minus = _mse(c_arr)
            
            # Restauration immédiate de la valeur d'origine dans le tableau maître
            c_arr[i] = orig_val
            
            # Calcul du gradient stabilisé
            g = (mse_plus - mse_minus) / (2 * h)
            grad[i] = max(-1e6, min(1e6, g))

        m  = b1 * m  + (1 - b1) * grad
        v2 = b2 * v2 + (1 - b2) * grad ** 2
        m_hat  = m  / (1 - b1 ** t)
        v2_hat = v2 / (1 - b2 ** t)
        c_arr -= lr * m_hat / (np.sqrt(np.maximum(v2_hat, 0.0)) + eps)
        c_arr  = np.clip(c_arr, cfg.ERC_MIN * 3, cfg.ERC_MAX * 3)

        new_mse = _mse(c_arr)
        if new_mse < best_mse:
            best_mse  = new_mse
            best_c    = c_arr.copy()
            stagnation = 0
        else:
            stagnation += 1
            if stagnation == 5:
                lr *= 0.5
            if stagnation >= 10:
                noise  = np.abs(best_c) * 0.05 + 0.01
                c_arr  = best_c + np.random.normal(0, noise)
                c_arr  = np.clip(c_arr, cfg.ERC_MIN * 3, cfg.ERC_MAX * 3)
                m[:]   = 0.0
                v2[:]  = 0.0
                stagnation = 0
                lr = cfg.ADAM_LR * 0.3

    # Appliquer les meilleures constantes à l'arbre
    for i, c in enumerate(consts):
        c.value = float(best_c[i])
    _invalidate_all_hashes(child)

    # [v14.3] Garde anti-dégénérescence ─────────────────────────────────────────
    # Adam peut faire diverger les constantes vers des valeurs extrêmes, ce qui
    # conduit simplify() à réduire l'expression à une feuille constante avec un
    # MSE catastrophique (cas observé : global_best dégradé de FIT=-808 à MSE=0.88).
    # On n'accepte la version optimisée que si :
    #   (a) son MSE pur est strictement meilleur que l'original, ET
    #   (b) la complexité ne s'effondre pas de plus de 60% (pas de dégénérescence).
    mse_before   = _pure_mse(node,  xs, ys)
    mse_after    = _pure_mse(child, xs, ys)
    k_before, _  = tree_complexity(node)
    k_after,  _  = tree_complexity(child)
    if mse_after >= mse_before or k_after < max(1, k_before * 0.4):
        return node.copy()   # original intact : Adam a divergé
    # ─────────────────────────────────────────────────────────────────────────────
    return child
