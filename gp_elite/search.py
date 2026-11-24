"""The search: the hold-out split, the linear candidate, and evolve,
which runs a fit from the seeds to the final choice.

Part of gp_elite/core.py until 1.4.0, moved in 1.5, where it reads and
sets the names of the shared state in gp_elite.state (state.NAME).
"""
from __future__ import annotations

import math
import numpy as np
import copy
import time
import csv
import os
from typing import Optional, List, Tuple, Dict, Any

from . import state
from .config import (ALL_OPS, TRACE, _BATTERY_BINARY_OPS, _BATTERY_UNARY_OPS,
                     _SYRACUSE_BINARY_OPS, _SYRACUSE_UNARY_OPS, _dim_active)
from .config import Config   # [1.5] named in annotations only
from .tree import (Node, to_string, tree_depth, tree_size)
from .simplification import (_clear_simplify_caches, simplify)
from .datasets import (build_dataset)
from .scoring import (_pure_mse, fitness, raw_mse, reset_feature_usage,
                      wrap_linear_scaling)
from .fitting import (optimize_constants_adam)
from .memory import (init_probe_set)
from .final_choice import (_FAITHFUL_CACHE, _NEAR_CACHE, _Patience,
                           _build_near_probes, _early_stop_threshold,
                           _finalists, _holdout_mse, _is_numerically_stable,
                           _polish_finalists, _refit_scaling, _select_one_se,
                           _small_setup, _small_table_select,
                           _track_small_candidate, _track_val_candidate)
from .seeds import (_make_binomial_seeds, _make_elementary_seeds,
                    _make_motif_seeds, _make_power_law_seeds,
                    _make_tolerant_seeds)
from .islands import (Island, _smart_reset_explorers, evolve_island, migrate)
from .parallel import (_SkipLogExport, _evolve_parallel,
                       _exit_if_reimported_by_worker, _parallel_enabled)

def _split_holdout(xs, ys, cfg):
    """Découpe (xs, ys) en (train, val). Retourne (xs_tr, ys_tr) et installe
    le hold-out dans les globals _VAL_XS/_VAL_YS. Validation désactivée si
    VALIDATION_SPLIT<=0 ou dataset trop petit (<30 points)."""
    state._VAL_XS = None; state._VAL_YS = None
    state._VAL_TRAIN_XS = None; state._VAL_TRAIN_YS = None
    state._EXTRAP_PROBE_XS = None; state._EXTRAP_BAND = None
    state._NEAR_PROBE_XS = None; state._NEAR_BAND = None; _NEAR_CACHE.clear()
    _FAITHFUL_CACHE.clear()
    state._VAL_CANDS.clear()
    frac = float(getattr(cfg, "VALIDATION_SPLIT", 0.0) or 0.0)
    n = len(ys)
    if frac <= 0.0 or n < 30:
        return xs, ys
    n_val = max(8, int(round(n * frac)))
    if n - n_val < 20:
        return xs, ys
    xs_np = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
    ys_np = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)

    extrap = bool(getattr(cfg, "EXTRAPOLATION_MODE", False))
    feat = getattr(cfg, "EXTRAPOLATION_FEATURE", None)
    direction = str(getattr(cfg, "EXTRAPOLATION_DIRECTION", "both")).lower()
    Xm = xs_np if xs_np.ndim == 2 else xs_np.reshape(-1, 1)
    feat_ok = (feat is not None and 0 <= int(feat) < Xm.shape[1])

    # [v25-EXTRAP] GARDE ANTI-DIVERGENCE (indépendant du type de split).
    # Dès qu'un axe d'extrapolation est désigné, on construit des points-sondes
    # AU-DELÀ du domaine observé + une bande de plausibilité dérivée de y.
    # _is_numerically_stable rejette tout candidat dont la prédiction explose
    # sur ces sondes — LE filtre qui manquait, car la divergence hors-plage
    # (cycle², exp, pow…) est invisible sur un hold-out interne.
    if extrap and feat_ok:
        j = int(feat)
        lo = Xm.min(axis=0); hi = Xm.max(axis=0)
        span_j = float(hi[j] - lo[j]) if float(hi[j] - lo[j]) > 1e-12 else 1.0
        n_probe = 48
        ext = 1.5 * span_j          # [v27] sondes plus loin (1.5×) et plus denses
        if direction == "low":
            grid = np.linspace(lo[j] - ext, lo[j], n_probe)
        elif direction == "both":
            grid = np.concatenate([
                np.linspace(lo[j] - ext, lo[j], n_probe // 2),
                np.linspace(hi[j], hi[j] + ext, n_probe // 2)])
        else:  # "high" (forecasting) — prolonge vers le haut
            grid = np.linspace(hi[j], hi[j] + ext, n_probe)
        med = np.median(Xm, axis=0)
        probe = np.tile(med, (len(grid), 1)); probe[:, j] = grid
        state._EXTRAP_PROBE_XS = probe
        y_lo = float(np.min(ys_np)); y_hi = float(np.max(ys_np))
        rng_y = max(1e-9, y_hi - y_lo)
        K = 2.0    # la tendance peut se prolonger de 2 amplitudes, pas exploser
        state._EXTRAP_BAND = (y_lo - K * rng_y, y_hi + K * rng_y)

    # Choix du SPLIT. LEÇON (données batterie) : pour extrapoler, entraîner sur
    # TOUTES les données — surtout les points de bord — donne une meilleure
    # PENTE que de les retirer pour valider. Retirer la frontière du train
    # dégrade l'estimation de tendance et fait dériver l'extrapolation. Le split
    # frontière reste disponible (EXTRAPOLATION_FRONTIER_SPLIT=True) mais n'est
    # PLUS le default : le mode extrapolation = split random (train complet)
    # + garde anti-divergence + candidat linéaire plancher.
    use_frontier = extrap and bool(getattr(cfg, "EXTRAPOLATION_FRONTIER_SPLIT", False))
    if use_frontier:
        lo = Xm.min(axis=0); hi = Xm.max(axis=0)
        mid = 0.5 * (lo + hi); half = np.maximum(0.5 * (hi - lo), 1e-12)
        if feat_ok:
            j = int(feat)
            signed = (Xm[:, j] - mid[j]) / half[j]
            edge = signed if direction == "high" else \
                   (-signed if direction == "low" else np.abs(signed))
            _bd = f"axis #{j} (sens={direction})"
        else:
            edge = np.max(np.abs(Xm - mid) / half, axis=1)
            _bd = "all features"
        order = np.argsort(-edge, kind="stable")
        frac_band = float(getattr(cfg, "EXTRAPOLATION_FRONTIER_FRAC", 0.20))
        n_band = min(max(n_val, int(round(n * frac_band))), n - 20)
        val_idx = np.sort(order[:n_band]); tr_idx = np.sort(order[n_band:])
        _split_kind = f"FRONTIER [{_bd}]"; _seed_note = "deterministic"
    else:
        rng = np.random.RandomState(int(getattr(cfg, "HOLDOUT_SEED", 1234)))
        idx = rng.permutation(n)
        val_idx = np.sort(idx[:n_val]); tr_idx = np.sort(idx[n_val:])
        _guard = " +divergence-guard" if (extrap and feat_ok) else ""
        _split_kind = "random" + _guard
        _seed_note = f"seed={getattr(cfg,'HOLDOUT_SEED',1234)}"

    state._VAL_XS = xs_np[val_idx]
    state._VAL_YS = ys_np[val_idx]
    xs_tr   = xs_np[tr_idx]
    ys_tr   = ys_np[tr_idx]
    state._VAL_TRAIN_XS = xs_tr
    state._VAL_TRAIN_YS = ys_tr
    _build_near_probes(xs_np, ys_np)          # [v0.7-NEAR]
    print(f"[v21-VAL] Hold-out {_split_kind} : {len(tr_idx)} points train / "
          f"{len(val_idx)} points validation ({len(val_idx)/n:.0%}, {_seed_note})")
    print(f"          Evolution sees ONLY the train set; final champion "
          f"selected on the validation set.")
    return xs_tr, ys_tr


def _make_linear_candidate(xs_tr, ys_tr, cfg):
    """[v24-EXTRAP] Fabrique un candidat LINÉAIRE OLS  y ≈ a0 + Σ a_i·X[i]  à
    partir du TRAIN (intérieur du domaine), construit comme un petit arbre Node.
    Il concourt ensuite dans la sélection finale, qui — en mode extrapolation —
    juge sur la bande-frontière. Une droite ne peut pas diverger hors-plage :
    si la loi est quasi-linéaire, la sélection parcimonieuse la préfère aux
    formes courbes qui sur-ajustent l'intérieur puis dérivent au bord.

    [v24.2] CORRECTIF : si un axe d'extrapolation est désigné
    (EXTRAPOLATION_FEATURE), le candidat n'est ajusté QUE sur cet axe. Ajuster
    sur des features qui ne tendent pas (ex. température, courant) injecte des
    coefficients parasites qui divergent dès que ces features dérivent hors de
    la plage d'entraînement — un piège deterministic observé sur données réelles."""
    try:
        Xall = xs_tr if (isinstance(xs_tr, np.ndarray) and xs_tr.ndim == 2) \
            else np.asarray(xs_tr, dtype=float).reshape(len(ys_tr), -1)
        y = np.asarray(ys_tr, dtype=float)
        terms_all = list(getattr(cfg, "TERMINALS", []))
        feat = getattr(cfg, "EXTRAPOLATION_FEATURE", None)
        if feat is not None and 0 <= int(feat) < Xall.shape[1]:
            cols = [int(feat)]                    # droite sur l'axe désigné seul
        else:
            cols = list(range(Xall.shape[1]))     # sinon, toutes les features
        X = Xall[:, cols]
        n, d = X.shape
        if n < d + 2:
            return None
        A = np.hstack([np.ones((n, 1)), X])              # [1 | X_cols]
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)     # [a0, a1, …]
        if not np.all(np.isfinite(coef)):
            return None
        a0 = float(coef[0])
        scale = max(1e-9, float(np.std(y)))
        node = Node(round(a0, 8))
        for k, col in enumerate(cols):
            ak = float(coef[k + 1])
            if abs(ak) < 1e-6 * scale:        # coefficient négligeable → omis
                continue
            name = terms_all[col] if col < len(terms_all) else f"X[{col}]"
            term = Node('*', Node(round(ak, 8)), Node(name))
            node = Node('+', node, term)
        return node
    except Exception:
        return None

def evolve(func, cfg: Config, problem_key: str = '1',
           X_override=None, y_override=None):
    """
    X_override / y_override : si fournis (np.ndarray), remplacent build_dataset.
    Utilisés par le mode CSV réel (BATTERY_SOH + nasa_battery_simulation.csv).
    """
    _exit_if_reimported_by_worker()          # [v0.7-PAR]
    state._USE_LINEAR_SCALING = bool(getattr(cfg, "USE_LINEAR_SCALING", True))
    # [v0.4.1] Les drapeaux dimensionnels sont des GLOBALES de module. Sans
    # remise a zero ici, un fit avec units= contaminait tous les fits suivants
    # du meme processus : le garde-fou restait actif sur des donnees sans
    # dimensions declarees, et le champion livre devenait aberrant.
    TRACE.reset()                            # [v0.7] un journal par exécution
    if _dim_active(cfg):
        state._DIM_GATE_DIMS   = cfg.FEAT_DIMS
        state._DIM_GATE_TARGET = cfg.TARGET_DIM
        state._LS_SCALE_ONLY   = True
        state._DIM_UNKNOWN_CONST = bool(getattr(cfg, "UNKNOWN_CONST", False))
        TRACE.set("dim_mode", "ACTIF — la recherche est contrainte par les unités")
        TRACE.set("unknown_const",
                  "OUI — la constante de tête peut porter une dimension"
                  if state._DIM_UNKNOWN_CONST else "non")
        TRACE.set("ls_mode", "multiplicatif seul (régression par l'origine)")
    else:
        state._DIM_GATE_DIMS   = None
        state._DIM_GATE_TARGET = None
        state._LS_SCALE_ONLY   = False
        state._DIM_UNKNOWN_CONST = False
        TRACE.set("dim_mode", "inactif (aucune unité déclarée)")
        TRACE.set("ls_mode", "affine (a + b·f) si linear scaling actif")
    state.VAL_R2_TOLERANCE = float(getattr(cfg, "VAL_R2_TOLERANCE", 0.003))
    # [v0.7] Journal relatif au DOSSIER COURANT de l'utilisateur. L'ancienne
    # resolution (dossier du module) ecrivait dans site-packages a chaque
    # ajustement -- y compris depuis l'API --, echouait en silence sur une
    # installation en lecture seule et entrelacait les ecritures de processus
    # concurrents.
    if not os.path.isabs(cfg.LOG_CSV):
        cfg = copy.copy(cfg)
        cfg.LOG_CSV = os.path.join(os.getcwd(), cfg.LOG_CSV)
    # [v0.7-TIME] Le drapeau d'arret au temps est un etat GLOBAL : il doit
    # etre remis a zero a chaque evolve(), sinon il fuit d'un ajustement au
    # suivant dans un meme processus.
    state._TIME_LIMIT_HIT = False
    # FIX v13.7 : vider les caches entre runs pour éviter les biais
    # inter-problèmes (hash structurel identique, domaine différent).
    state._fitness_cache    = {}
    state._PARAMETRIC_CACHE = {}
    state._PRED_CACHE.clear()
    state.FRAGMENT_LIB.fragments.clear()
    state.FRAGMENT_LIB.generation = 0
    state.COGRAPH.co.clear()
    state.SEQ_MEM.transitions.clear()

    # [v17] Initialiser le probe set adapté aux dimensions du problème
    state.PROBE_X              = init_probe_set(cfg, n_probe=30)
    state.CURRENT_RESIDUAL_SIG = None
    # [FIX-E] Réinitialiser le compteur d'usage des features
    n_feats = len(cfg.TERMINALS) if hasattr(cfg, 'TERMINALS') else 1
    reset_feature_usage(n_feats)
    print(f"[v17-SEMANTIC] Probe set initialized: {state.PROBE_X.shape[0]} points × "
          f"{state.PROBE_X.shape[1] if state.PROBE_X.ndim > 1 else 1} features  "
          f"[{cfg.X_MIN:.1f}, {cfg.X_MAX:.1f}]")

    print("=" * 70)
    # [SYRACUSE / v16-BATTERY CSV] Afficher le pool d'opérateurs réellement actif
    if state._SYRACUSE_MODE:
        _active_ops = _SYRACUSE_BINARY_OPS + _SYRACUSE_UNARY_OPS
    elif state._BATTERY_CSV_MODE:
        _active_ops = _BATTERY_BINARY_OPS + _BATTERY_UNARY_OPS
    else:
        _active_ops = ALL_OPS
    print(f"Generations : {cfg.GENERATIONS}  |  Ops : {_active_ops}")
    print("=" * 70)
    print()

    # [v16-BATTERY] Si des données réelles sont fournies, on les utilise
    # directement au lieu de générer un dataset synthétique via build_dataset.
    if X_override is not None and y_override is not None:
        xs = X_override   # shape (n_samples, n_features)
        ys = y_override   # shape (n_samples,)
    else:
        xs, ys = build_dataset(func, cfg, problem_key=problem_key)

    # [v21-VAL] Split train/validation — tout ce qui suit (îles, fitness,
    # lexicase, Adam, stigmergie, parallélisme) ne voit que le TRAIN.
    xs_full, ys_full = xs, ys
    xs, ys = _split_holdout(xs, ys, cfg)
    _small_setup(cfg, ys)                     # [1.4-S1]

    # [v24-EXTRAP] En mode extrapolation, on ajoute une DROITE (OLS) au pool de
    # candidats-champions. Elle est ajustée sur le train (intérieur) puis jugée,
    # comme tous les candidats, sur la bande-frontière. Opt-in : sans effet sur
    # les runs normaux (EXTRAPOLATION_MODE reste False par default).
    if bool(getattr(cfg, "EXTRAPOLATION_MODE", False)) and state._VAL_XS is not None:
        _lin = _make_linear_candidate(xs, ys, cfg)
        if _lin is not None:
            _track_val_candidate(_lin)
            print(f"[v24-EXTRAP] Linear candidate injected into selection: "
                  f"{to_string(_lin)}")

    # Initialisation des îles (la dernière = île C stigmergique)
    islands = []
    for i in range(cfg.N_ISLANDS):
        is_stigmergic = (i == cfg.N_ISLANDS - 1)
        islands.append(Island(i, cfg, stigmergic=is_stigmergic))

    # [v14.4] Affichage des rôles — placé APRÈS la création de islands
    _roles_str = ", ".join(f"island {isl.id}={isl.role}" for isl in islands)
    print(f"GP_ELITE  —  {cfg.N_ISLANDS} islands × {cfg.POP_SIZE // cfg.N_ISLANDS} individuals  ({_roles_str})")
    print()

    # Initialiser d'abord les îles classiques pour peupler la lib
    for island in islands[:-1]:
        island.initialize()
        island._xs = xs
        island._ys = ys
        island._key = problem_key
        pop_sorted = sorted(island.population,
                            key=lambda n: fitness(n, xs, ys, cfg))
        top_k    = max(3, len(pop_sorted) // 10)
        top_fits = [fitness(ind, xs, ys, cfg) for ind in pop_sorted[:top_k]]
        state.FRAGMENT_LIB.deposit_population(pop_sorted, top_fits, top_k, gen=0,
                                        xs=xs, ys=ys)  # FIX v13.8 : filtre numérique

    # Île C : initialisée après le premier dépôt (lib déjà peuplée)
    islands[-1].initialize()
    islands[-1]._xs  = xs
    islands[-1]._ys  = ys
    islands[-1]._key = problem_key

    # ---- Seeding dirigé ----
    # Injecter des briques connues dans chaque île pour amorcer la recherche
    def make_seed(expr: str) -> Optional[Node]:
        """Construit manuellement quelques individus de départ pertinents."""
        if expr == "sin_sq_x":
            return Node("sin", Node("sq", Node("x")))
        if expr == "x_cos_x":
            return Node("*", Node("x"), Node("cos", Node("x")))
        if expr == "sin_sq_plus_xcos":
            return Node("+",
                        Node("sin", Node("sq", Node("x"))),
                        Node("*", Node("x"), Node("cos", Node("x"))))
        if expr == "sin_xx":
            return Node("sin", Node("*", Node("x"), Node("x")))
        # --- Problème 2 : x³ - x² + x - 1 ---
        if expr == "x_cube":
            return Node("cube", Node("x"))
        if expr == "x_sq":
            return Node("sq", Node("x"))
        if expr == "x_cube_poly":
            x3  = Node("cube", Node("x"))
            x2  = Node("sq",   Node("x"))
            return Node("-", Node("+", Node("-", x3, x2), Node("x")), Node(1.0))
        # --- Problème 3 : exp(-x²)·sin(2x) ---
        if expr == "exp_sq_x":
            return Node("exp", Node("neg", Node("sq", Node("x"))))
        if expr == "sin_2x":
            return Node("sin", Node("*", Node(2.0), Node("x")))
        if expr == "exp_sin":
            return Node("*",
                        Node("exp", Node("neg", Node("sq", Node("x")))),
                        Node("sin", Node("*", Node(2.0), Node("x"))))
        # --- Problème 4 : log(1+x²)·cos(x) ---
        if expr == "log1x2":
            return Node("log", Node("+", Node(1.0), Node("sq", Node("x"))))
        if expr == "cos_x":
            return Node("cos", Node("x"))
        if expr == "log_cos":
            return Node("*",
                        Node("log", Node("+", Node(1.0), Node("sq", Node("x")))),
                        Node("cos", Node("x")))
        # --- Problème 5 : x·sin(x²)·cos(x/2) ---
        if expr == "cos_half_x":
            return Node("cos", Node("*", Node(0.5), Node("x")))
        if expr == "x_sin_sq":
            return Node("*", Node("x"), Node("sin", Node("sq", Node("x"))))
        if expr == "x_sin_sq_cos_half":
            return Node("*",
                        Node("*", Node("x"), Node("sin", Node("sq", Node("x")))),
                        Node("cos", Node("*", Node(0.5), Node("x"))))
        # --- Problème 6 : exp(-|x|)·(x²-1) ---
        if expr == "exp_neg_abs":
            # exp(-|x|)
            return Node("exp", Node("neg", Node("abs", Node("x"))))
        if expr == "x2_minus1":
            # x²-1
            return Node("-", Node("sq", Node("x")), Node(1.0))
        if expr == "exp_abs_x2":
            # exp(-|x|) · (x²-1)
            return Node("*",
                        Node("exp", Node("neg", Node("abs", Node("x")))),
                        Node("-", Node("sq", Node("x")), Node(1.0)))
        # --- Problème 7 : sinc(x)·cos(x²) ---
        if expr == "sin_over_x":
            # sin(x)/x ≈ sinc
            return Node("/", Node("sin", Node("x")), Node("x"))
        if expr == "cos_sq_x":
            return Node("cos", Node("sq", Node("x")))
        if expr == "sinc_cos_sq":
            return Node("*",
                        Node("/", Node("sin", Node("x")), Node("x")),
                        Node("cos", Node("sq", Node("x"))))
        # --- Problème 8 : sin(πx)/(x²+1) ---
        if expr == "sin_pi_x":
            return Node("sin", Node("*", Node(math.pi), Node("x")))
        if expr == "x2_plus1":
            return Node("+", Node("sq", Node("x")), Node(1.0))
        if expr == "lorentz_sin":
            return Node("/",
                        Node("sin", Node("*", Node(math.pi), Node("x"))),
                        Node("+", Node("sq", Node("x")), Node(1.0)))
        # --- Problème 9 : tanh(x)·exp(-x²/4) ---
        if expr == "tanh_x":
            return Node("tanh", Node("x"))
        if expr == "exp_x2_4":
            # exp(-x²/4)
            return Node("exp", Node("neg",
                        Node("/", Node("sq", Node("x")), Node(4.0))))
        if expr == "tanh_exp_gauss":
            # tanh(x) · exp(-x²/4) — forme exacte
            return Node("*",
                        Node("tanh", Node("x")),
                        Node("exp", Node("neg",
                             Node("/", Node("sq", Node("x")), Node(4.0)))))
        if expr == "sin_exp_gauss":
            # sin(x) · exp(-x²/4) — approximation proche pour petits x
            return Node("*",
                        Node("sin", Node("x")),
                        Node("exp", Node("neg",
                             Node("/", Node("sq", Node("x")), Node(4.0)))))
        # --- Problème 10 : x³·sin(1/x) ---
        if expr == "x_cube_sin_inv":
            return Node("*",
                        Node("cube", Node("x")),
                        Node("sin", Node("/", Node(1.0), Node("x"))))
        # ── [v16-BATTERY] Seeds N-D pour BATTERY_SOH ─────────────────────────
        # Cible : 1 - 0.02·exp(X[0])·X[1] - 0.005·X[2]²
        # Stratégie : injecter les briques structurelles clés indépendamment
        # pour que la stigmergie puisse les combiner dès les premières générations.
        if expr == "bsoh_exp_x0":
            # exp(X[0]) — terme d'Arrhenius isolé
            return Node("exp", Node("X[0]"))
        if expr == "bsoh_exp_x0_x1":
            # exp(X[0]) * X[1] — interaction thermique × cycles
            return Node("*", Node("exp", Node("X[0]")), Node("X[1]"))
        if expr == "bsoh_sq_x2":
            # X[2]² — terme de dégradation quadratique courant
            return Node("sq", Node("X[2]"))
        if expr == "bsoh_decay_term":
            # 0.02 * exp(X[0]) * X[1] — terme de dégradation Arrhenius complet
            return Node("*",
                        Node(0.02),
                        Node("*", Node("exp", Node("X[0]")), Node("X[1]")))
        if expr == "bsoh_full":
            # 1 - 0.02*exp(X[0])*X[1] — structure principale sans X[2]²
            return Node("-",
                        Node(1.0),
                        Node("*",
                             Node(0.02),
                             Node("*", Node("exp", Node("X[0]")), Node("X[1]"))))
        if expr == "bsoh_x2_term":
            # 0.005 * X[2]² — terme de dégradation quadratique complet
            # Injecté explicitement car ce terme est 50× plus petit que
            # 0.02·exp(X[0])·X[1] → pression fitness très faible sans seed directe
            return Node("*", Node(0.005), Node("sq", Node("X[2]")))
        if expr == "bsoh_complete":
            # Structure cible exacte : 1 - 0.02*exp(X[0])*X[1] - 0.005*X[2]²
            # Injectée sur l'île stigmergic (île 3) pour que la lib et CoGraph
            # absorbent immédiatement les trois briques structurelles ensemble.
            return Node("-",
                        Node("-",
                             Node(1.0),
                             Node("*",
                                  Node(0.02),
                                  Node("*", Node("exp", Node("X[0]")), Node("X[1]")))),
                        Node("*", Node(0.005), Node("sq", Node("X[2]"))))
        return None

    # Seeds par problème — couvre maintenant P1–P10
    seed_map = {
        "1": ["sin_sq_x", "x_cos_x", "sin_sq_plus_xcos", "sin_xx",
               "sin_sq_x", "x_cos_x"],
        "2": ["x_cube", "x_sq", "x_cube_poly", "x_cube",
               "x_sq", "x_cube_poly"],
        "3": ["exp_sq_x", "sin_2x", "exp_sin", "exp_sq_x",
               "sin_2x", "exp_sin"],
        "4": ["log1x2", "cos_x", "log_cos", "log1x2",
               "cos_x", "log_cos"],
        "5": ["sin_sq_x", "cos_half_x", "x_sin_sq", "x_sin_sq_cos_half",
              "sin_sq_x", "cos_half_x", "x_sin_sq", "x_sin_sq_cos_half"],
        "6": ["exp_neg_abs", "x2_minus1", "exp_abs_x2",
               "exp_neg_abs", "x2_minus1", "exp_abs_x2"],
        "7": ["sin_over_x", "cos_sq_x", "sinc_cos_sq",
               "sin_over_x", "cos_sq_x"],
        "8": ["sin_pi_x", "x2_plus1", "lorentz_sin",
               "sin_pi_x", "x2_plus1", "lorentz_sin"],
        "9": ["tanh_x", "exp_x2_4", "tanh_exp_gauss",
               "tanh_x", "exp_x2_4", "tanh_exp_gauss", "sin_exp_gauss"],
        "10": ["x_cube", "x_cube_sin_inv", "x_cube",
                "x_cube_sin_inv"],
        # ── [v16-BATTERY v2] Seeds N-D — distribution raisonnée sur 4 îles ────
        # Problème observé (run v2) : bsoh_sq_x2 absorbé par tanh via mutations.
        # Le terme 0.005·X[2]² est 50× plus faible que 0.02·exp(X[0])·X[1]
        # → pression fitness insuffisante pour le maintenir sans seed directe.
        # Stratégie :
        #   · île 0 (explorer)   : briques atomiques pour diversité
        #   · île 1 (explorer)   : bsoh_complete → structure cible exacte
        #   · île 2 (cleaner)    : bsoh_decay_term + bsoh_x2_term séparément
        #   · île 3 (stigmergic) : bsoh_complete + bsoh_full pour lib/CoGraph
        "BATTERY_SOH": [
            "bsoh_exp_x0",       # île 0 slot 0 : exp(X[0])
            "bsoh_complete",     # île 1 slot 0 : structure cible EXACTE
            "bsoh_decay_term",   # île 2 slot 0 : 0.02*exp(X[0])*X[1]
            "bsoh_complete",     # île 3 slot 0 : structure cible EXACTE (lib)
            "bsoh_sq_x2",        # île 0 slot 1 : X[2]² brut
            "bsoh_x2_term",      # île 1 slot 1 : 0.005*X[2]² complet
            "bsoh_full",         # île 2 slot 1 : 1 - 0.02*exp(X[0])*X[1]
            "bsoh_x2_term",      # île 3 slot 1 : 0.005*X[2]² (renforcement)
        ],
        # ── [v16-BATTERY CSV] Seeds pour données réelles — 3 features SANS X[3] ─
        # Identiques à BATTERY_SOH mais sans aucun nœud X[3].
        # Utilisées quand nasa_battery_simulation.csv est présent (n_features=3).
        "BATTERY_SOH_CSV": [
            "bsoh_exp_x0",       # île 0 slot 0 : exp(X[0])
            "bsoh_exp_x0_x1",    # île 1 slot 0 : exp(X[0])*X[1]
            "bsoh_decay_term",   # île 2 slot 0 : 0.02*exp(X[0])*X[1]
            "bsoh_full",         # île 3 slot 0 : 1 - 0.02*exp(X[0])*X[1]
            "bsoh_sq_x2",        # île 0 slot 1 : X[2]²
            "bsoh_x2_term",      # île 1 slot 1 : 0.005*X[2]²
            "bsoh_x2_term",      # île 2 slot 1 : renforcement terme X[2]
            "bsoh_exp_x0",       # île 3 slot 1 : exp(X[0]) diversité
        ],
    }
    seeds = seed_map.get(problem_key, []) if cfg.USE_SEEDING else []
    # FIX v13.10 : P7 et P8 requièrent des structures que le GP ne découvre
    # presque jamais seul en ultrafast (sin(x)/x, π précis). On injecte leurs
    # seeds inconditionnellement, même en ablation (USE_SEEDING=False), car ces
    # briques ne biaisent pas la comparaison des conditions — elles aident juste
    # le GP à ne pas passer 100 gens sur des constantes proches de 0.
    if not cfg.USE_SEEDING and problem_key in ("7", "8"):
        seeds = seed_map.get(problem_key, [])
    # [v16-BATTERY] BATTERY_SOH : seeds N-D injectées inconditionnellement.
    # Sans seeding, exp(X[0]) n'émerge presque jamais avant gen 20 — la stigmergie
    # s'ouvre trop tard et tanh colonise la population (observé au run v16-NDIM).
    # Ces seeds ne biaisent pas la comparaison car elles reflètent uniquement
    # la physique du problème (modèle d'Arrhenius), pas une solution complète.
    if problem_key == "BATTERY_SOH":
        seeds = seed_map["BATTERY_SOH"]
    # [v16-BATTERY CSV] Mode données réelles : seeds sans X[3]
    if problem_key == "BATTERY_SOH_CSV":
        seeds = seed_map["BATTERY_SOH_CSV"]
    # FIX v13.7 : distribution round-robin des seeds entre les îles.
    for j, seed_name in enumerate(seeds):
        target_island = islands[j % cfg.N_ISLANDS]
        slot          = j // cfg.N_ISLANDS
        seed = make_seed(seed_name)
        if seed and slot < len(target_island.population):
            target_island.population[slot] = seed

    # [CUSTOM-SEEDS] Injection des arbres fournis par l'utilisateur (round-robin).
    # On les place dans des slots distincts pour ne pas écraser les seeds
    # standard. Chaque île reçoit une copie pour préserver l'isolation.
    _cseeds = getattr(state, '_CUSTOM_SEEDS', None)
    if _cseeds:
        base = len(seeds)
        for j, seed_node in enumerate(_cseeds):
            target_island = islands[j % cfg.N_ISLANDS]
            slot          = (base + j) // cfg.N_ISLANDS
            if seed_node is not None and slot < len(target_island.population):
                target_island.population[slot] = seed_node.copy()
    # [v28-MOTIFS] Injection des motifs de composition (round-robin, slots
    # suivants). Opt-out via cfg.MOTIF_SEEDS=False. Tirage dépendant du SEED :
    # chaque restart (v27) instancie d'autres appariements de variables.
    # [v29.1] Les motifs servent la RÉCUPÉRATION (structures riches en-domaine) ;
    # en mode EXTRAPOLATION ils injectent des formes courbes plausibles dans la
    # bande mais trompeuses au-delà (mesuré : batterie méd +0.52 → +0.18).
    # On les coupe donc quand EXTRAPOLATION_MODE est actif.
    if bool(getattr(cfg, "MOTIF_SEEDS", True)) \
            and not bool(getattr(cfg, "EXTRAPOLATION_MODE", False)):
        _motifs = _make_motif_seeds(cfg, int(getattr(cfg, "MOTIF_SEEDS_N", 32)))
        _base2 = len(seeds) + (len(_cseeds) if _cseeds else 0)
        for j, mnd in enumerate(_motifs):
            target_island = islands[j % cfg.N_ISLANDS]
            slot          = (_base2 + j) // cfg.N_ISLANDS
            if slot < len(target_island.population):
                target_island.population[slot] = mnd
    else:
        _motifs = []
    # [v0.8] Graines de loi de puissance (voir _make_power_law_seeds) : une
    # copie dans chaque île, au slot qui suit les motifs. Rien n'est injecté
    # (et rien ne change) quand la cible ou toutes les colonnes changent de
    # signe.
    _plaw = _make_power_law_seeds(xs, ys, cfg)
    if _plaw:
        _base3 = (len(seeds) + (len(_cseeds) if _cseeds else 0)
                  + len(_motifs)) // cfg.N_ISLANDS + 1
        for target_island in islands:
            for j, pnd in enumerate(_plaw):
                slot = _base3 + j
                if slot < len(target_island.population):
                    target_island.population[slot] = pnd.copy()
    # [0.10, phase 4b] Graines « monôme fois puissance d'un binôme » (voir
    # _make_binomial_seeds) : une copie dans chaque île, après les graines de
    # loi de puissance. Rien n'est injecté sans une forme exacte.
    _binom = _make_binomial_seeds(xs, ys, cfg)
    if _binom:
        _base4 = ((len(seeds) + (len(_cseeds) if _cseeds else 0)
                   + len(_motifs)) // cfg.N_ISLANDS + 1 + len(_plaw))
        for target_island in islands:
            for j, bnd in enumerate(_binom):
                slot = _base4 + j
                if slot < len(target_island.population):
                    target_island.population[slot] = bnd.copy()
    # [0.10, phase 4a] Graines « fonction d'un monôme » (voir
    # _make_elementary_seeds) : une copie dans chaque île, après les graines
    # binomiales. Rien n'est injecté sans une forme exacte.
    _elem = _make_elementary_seeds(xs, ys, cfg)
    if _elem:
        _base5 = ((len(seeds) + (len(_cseeds) if _cseeds else 0)
                   + len(_motifs)) // cfg.N_ISLANDS + 1 + len(_plaw)
                  + len(_binom))
        for target_island in islands:
            for j, end in enumerate(_elem):
                slot = _base5 + j
                if slot < len(target_island.population):
                    target_island.population[slot] = end.copy()
    # [0.10, phase 5] Graines tolérantes au bruit (voir _make_tolerant_seeds) :
    # seulement si aucune forme exacte de B1 ou E1 n'a été trouvée ; une copie
    # dans chaque île, après les autres graines.
    _tol = [] if (_binom or _elem) else _make_tolerant_seeds(
        xs, ys, cfg, power_done=bool(_plaw))
    if _tol:
        _base6 = ((len(seeds) + (len(_cseeds) if _cseeds else 0)
                   + len(_motifs)) // cfg.N_ISLANDS + 1 + len(_plaw)
                  + len(_binom) + len(_elem))
        for target_island in islands:
            for j, tnd in enumerate(_tol):
                slot = _base6 + j
                if slot < len(target_island.population):
                    target_island.population[slot] = tnd.copy()
    # [v16-NDIM] Pas de seeds spécifiques pour les problèmes N-D.
    # La couverture des opérateurs est assurée par _nd_diverse_population()
    # dans Island.initialize_nd(), et le transfert de grammaire par SEQ_MEM.

    global_best:  Optional[Node] = None
    global_score: float          = float("inf")

    log_rows = []
    t0 = time.time()

    # ── [v20-PAR] Tentative parallèle (AUTO : ≥4 cœurs et ≥2 îles) ──
    # En cas de succès, on saute la boucle séquentielle ; en cas d'échec
    # (pool indisponible, pickling, etc.), repli transparent : les îles ne
    # sont jamais corrompues (remplacées seulement après un round réussi),
    # la boucle séquentielle reprend là où le parallèle s'est arrêté.
    _seq_needed = True
    if _parallel_enabled(cfg):
        _pb, _ps, _completed = _evolve_parallel(islands, xs, ys, cfg, t0, log_rows)
        if _pb is not None and _ps < global_score:
            global_best, global_score = _pb, _ps
        if _completed:
            _seq_needed = False

    # Compteur de plateau global — déclenche un restart d'urgence si
    # aucune île n'améliore le global_best pendant trop longtemps
    _plateau_counter   = 0
    _plateau_threshold = 40   # générations sans amélioration globale
    _last_global_raw   = float('inf')

    _deadline = getattr(cfg, "DEADLINE", None)
    _pat = _Patience(getattr(cfg, "PATIENCE", 0))     # [v1.2-H1]
    for gen in range(cfg.GENERATIONS if _seq_needed else 0):
        # [v0.7-TIME] Echeance atteinte : arret propre, meilleur modele conserve.
        if _deadline is not None and gen > 0 and time.time() >= _deadline:
            TRACE.set("time_limit", "atteint (sequentiel, gen %d)" % gen)
            state._TIME_LIMIT_HIT = True
            print(f"[TIME] Time limit reached at generation {gen} — "
                  f"returning the best model so far.")
            break
        # [OPT] Cache fitness vidé toutes les 10 générations (aligné sur gen//10).
        # Entre deux vidages, la clé (hash, role, gen//10) garantit la fraîcheur.
        # Évite de recalculer la fitness d'individus stables entre générations.
        if gen % 10 == 0:
            state._fitness_cache.clear()
        # [OPT] Vider le cache de simplification pour libérer la mémoire
        # et éviter des résultats périmés après mutations.
        _clear_simplify_caches()
        # [FIX-A] Mettre à jour la pénalité mono-feature progressive
        # 0.10 en gen=0 → 0.03 en fin de run (décroissance linéaire)
        if state._SYRACUSE_MODE:
            _t = gen / max(cfg.GENERATIONS - 1, 1)
            cfg._mono_pen_cache = 0.10 - _t * 0.07   # 0.10 → 0.03
        # [OPT] Bucket générationnel pour le cache fitness (gen//10)
        cfg._gen_bucket = gen // 10

        # Évolution de chaque île
        _gen_improved = False
        for island in islands:
            new_best = evolve_island(island, xs, ys, gen)

            if new_best is not None:
                # [v18-LS] Matérialiser le scaling AVANT comparaison/stockage :
                # l'EXPR affichée et le champion stocké incluent a + b·(...),
                # donc le MSE rapporté correspond exactement à l'expression.
                cand = wrap_linear_scaling(new_best, xs, ys)
                _track_val_candidate(cand)            # [v21-VAL]
                _track_small_candidate(cand, xs, ys)  # [1.4-S1]
                s = fitness(cand, xs, ys, cfg, role="cleaner")
                if s < global_score:
                    global_score  = s
                    global_best   = cand.copy()
                    _gen_improved = True

                    raw = raw_mse(cand, xs, ys)
                    sz  = tree_size(cand)
                    dp  = tree_depth(cand)
                    elapsed = time.time() - t0

                    print(f"[GEN {gen:04d}|I{island.id}] "
                          f"FIT={s:.8f} "
                          f"RAW={raw:.8f} "
                          f"SIZE={sz:02d} "
                          f"DEPTH={dp:02d} "
                          f"({elapsed:.1f}s)")
                    print(f"  EXPR = {to_string(cand)}")
                    print()

                    log_rows.append({
                        "gen": gen, "island": island.id,
                        "fit": s, "raw": raw,
                        "size": sz, "depth": dp,
                        "expr": to_string(cand),
                        "elapsed": elapsed
                    })

        # Suivi du plateau global
        _cur_raw = raw_mse(global_best, xs, ys) if global_best else float('inf')
        if _cur_raw < _last_global_raw - 1e-6:
            _plateau_counter = 0
            _last_global_raw = _cur_raw
        else:
            _plateau_counter += 1

        # [SYRACUSE] Restart d'urgence : si plateau global trop long,
        # réinitialiser les îles explorer (squelettes sémantiques ciblés).
        # [v20-PAR] Logique extraite dans _smart_reset_explorers() — partagée
        # par la boucle séquentielle et la boucle parallèle.
        _is_nd_run = (len(cfg.TERMINALS) > 1 or
                      (len(cfg.TERMINALS) == 1 and cfg.TERMINALS[0] != "x"))
        if (_plateau_counter >= _plateau_threshold and
                _is_nd_run and gen < cfg.GENERATIONS - 50):
            _plateau_counter = 0
            _smart_reset_explorers(islands, cfg, gen, _cur_raw)

        # Convergence parfaite
        if global_best and raw_mse(global_best, xs, ys) < cfg.PERFECT_THRESHOLD:
            print(f"[✓] Perfect solution found at generation {gen}!")
            break

        # [v15] Early Stopping — arrêt précoce si MSE pur sous le seuil absolu
        if global_best:
            # [v21-VAL] early-stop jugé sur le HOLD-OUT (anti-surapprentissage)
            _es_mse = _holdout_mse(global_best, xs, ys)
            _es_thr = _early_stop_threshold(cfg, ys)
            if _es_mse <= _es_thr:
                print(f"\n{'═'*60}")
                print(f"  [SUCCESS] Precision target reached at GEN {gen:04d}!")
                print(f"  MSE (hold-out si actif) = {_es_mse:.2e}  ≤  seuil = {_es_thr:.2e}")
                print(f"  Early stop — remaining generations saved.")
                print(f"{'═'*60}\n")
                break
            # [v1.2-H1] Arrêt sur patience (budget choisi par le moteur).
            if _pat.spent(_es_mse, gen):
                TRACE.set("patience", "arret (sequentiel, gen %d)" % gen)
                print(f"[PATIENCE] No gain of 1 % in {_pat.p} generations — "
                      f"stop at generation {gen}.")
                break

        # Migration périodique
        if gen > 0 and gen % cfg.MIGRATION_INTERVAL == 0:
            migrate(islands)

    if _deadline is not None and time.time() >= _deadline:
        state._TIME_LIMIT_HIT = True
    # Optimisation finale des constantes sur le meilleur
    # [v14.4] Correction du bug de référence : copy.deepcopy() avant Adam+simplify
    # pour garantir que global_best n'est jamais corrompu si des nœuds sont
    # partagés par référence entre global_best et l'arbre optimisé.
    # Comparaison par raw_mse pur (MSE brut) pour détecter correctement
    # les régressions numériques post-Adam, indépendamment du rôle.
    if global_best:
        import copy as _copy
        optimized = optimize_constants_adam(global_best.copy(), xs, ys, cfg)  # [v19-OPT]
        optimized = simplify(optimized)
        # [v0.8] Le champion porte sa mise à l'échelle a + b·f ; LM en
        # projection variable ajuste la forme a' + b'·(champion) : sans
        # recalage, l'arbre rendu gardait l'ancien a et l'ancien b (raw_mse,
        # invariant d'échelle, ne le voit pas). Sans hold-out (moins de 30
        # points, ou validation_split=0), ce modèle était livré tel quel.
        optimized = _refit_scaling(optimized, xs, ys)
        if raw_mse(optimized, xs, ys) < raw_mse(global_best, xs, ys):
            global_best = optimized
        # Si Adam a dégradé, global_best reste intact (deepcopy garantit l'isolation)
        _track_val_candidate(global_best)            # [v21-VAL] post-Adam
        _track_small_candidate(global_best, xs, ys)  # [1.4-S1]

    # [1.4-S1] Sous 30 lignes, pas de hold-out : les candidats en validation
    # croisée (voir _small_table_select).
    if state._VAL_XS is None and global_best is not None and state._SMALL_ON:
        try:
            global_best = _small_table_select(global_best, xs, ys, cfg)
        except Exception:
            pass

    # ── [v21-VAL] Sélection finale + rapport de généralisation ──────────
    # Le champion LIVRÉ est celui qui généralise le mieux : si un candidat
    # suivi en cours de run bat le champion-train sur le hold-out, il prend
    # sa place. Puis rapport train vs validation, avec alerte surapprentissage.
    if state._VAL_XS is not None and global_best is not None:
        # [v26-LM] POLISSAGE DES FINALISTES : avant la sélection parcimonieuse,
        # on affine par LM les constantes des meilleurs candidats suivis. Sans
        # cela, la règle 1-SE compare des structures aux constantes brutes — une
        # forme simple et EXACTE peut perdre contre un gros arbre simplement
        # parce que ses constantes n'étaient pas encore ajustées. Coût : ~ms.
        try:
            _polish_finalists(_finalists(cfg), xs, ys, cfg)   # [v0.8] voir leurs définitions
        except Exception:
            pass
        _champ_val = _holdout_mse(global_best, xs, ys)
        _sel, _sel_val = _select_one_se(global_best, _champ_val)
        # [v25-EXTRAP] Le garde anti-divergence PRIME sur la parcimonie : si le
        # champion lui-même diverge hors-plage, il doit céder la place au
        # meilleur candidat stable, même si ce dernier n'est ni plus petit ni
        # meilleur en validation interne (sa MSE interne peut être pire — c'est
        # justement le point : le divergent gagne EN INTERNE et explose DEHORS).
        _champ_unstable = not _is_numerically_stable(global_best)
        _really_diff = (_sel is not global_best and
                        (_champ_unstable or
                         tree_size(_sel) < tree_size(global_best) or
                         _sel_val < _champ_val * 0.999))
        if _really_diff:
            _sz_sel, _sz_old = tree_size(_sel), tree_size(global_best)
            if _champ_unstable:
                _why = "out-of-range divergent champion replaced by a stable candidate"
            elif _sz_sel < _sz_old:
                _why = f"simpler ({_sz_sel} nodes vs {_sz_old}, equivalent R²)"
            else:
                _why = f"meilleur en validation (val {_sel_val:.3e} vs {_champ_val:.3e})"
            print(f"[v21-VAL] Parsimonious selection: champion replaced — {_why}")
            global_best = _sel.copy()
            _champ_val  = _sel_val
        # [v25-EXTRAP] FILET DE SÉCURITÉ DUR : en mode extrapolation, ne JAMAIS
        # livrer un modèle qui diverge hors-plage. Si, malgré tout, le champion
        # final échoue encore au garde (aucun candidat stable n'avait été suivi),
        # on retombe sur la droite OLS — sûre par construction.
        if state._EXTRAP_PROBE_XS is not None and not _is_numerically_stable(global_best):
            _lin_fb = _make_linear_candidate(xs, ys, cfg)
            if _lin_fb is not None and _is_numerically_stable(_lin_fb):
                print("[v25-EXTRAP] ⚠ Champion still divergent → falling back to the line (safe floor).")
                global_best = _lin_fb
                _champ_val  = _holdout_mse(global_best, xs, ys)
        _champ_train = _pure_mse(global_best, xs, ys)
        _var_val     = float(np.var(state._VAL_YS)) if len(state._VAL_YS) > 1 else 0.0
        _r2_val      = (1.0 - _champ_val / _var_val) if _var_val > 1e-15 else float("nan")
        _ratio       = (_champ_val / _champ_train) if _champ_train > 1e-15 else 1.0
        # solution exacte (bruit numérique pur) : ratio non significatif
        if _champ_val < 1e-12 and _champ_train < 1e-12:
            _ratio = 1.0
        print()
        print("─" * 70)
        print("[v21-VAL] GENERALIZATION REPORT (final champion)")
        print(f"  MSE train      : {_champ_train:.6e}")
        print(f"  Validation MSE : {_champ_val:.6e}   (never seen by evolution)")
        print(f"  R² validation  : {_r2_val:.4f}")
        print(f"  Ratio val/train: {_ratio:.2f}")
        if _ratio > 3.0:
            print("  ⚠ SURAPPRENTISSAGE PROBABLE : l'erreur de validation est "
                  ">3× the training error.")
            print("    Hints: ↑PARSIMONY, ↓MAX_TREE_SIZE, more data.")
        elif _ratio > 1.5:
            print("  ~ Slight train/val gap — monitor, but acceptable.")
        else:
            print("  ✓ Healthy generalization.")
        print("─" * 70)

    # Export CSV (optionnel — silencieux si filesystem en lecture seule)
    try:
        if not getattr(cfg, "WRITE_LOG_CSV", True):
            raise _SkipLogExport()
        with open(cfg.LOG_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["gen", "island", "fit", "raw",
                               "size", "depth", "expr", "elapsed"])
            writer.writeheader()
            writer.writerows(log_rows)
        print(f"[LOG] History exported → {cfg.LOG_CSV}")
    except Exception:
        pass  # filesystem en lecture seule — ignoré silencieusement

    # Stats bibliothèque de fragments
    s = state.FRAGMENT_LIB.stats()
    print(f"[STIGM] Fragments accumulated: {s['count']}")
    print(f"[STIGM] τ max : {s['max_tau']:.4f}  |  τ moyen : {s['mean_tau']:.4f}")
    if s['top_ops']:
        print(f"[STIGM] Dominant operators: {s['top_ops']}")
    if state.FRAGMENT_LIB.fragments:
        print("[STIGM] Top 3 fragments :")
        for e in state.FRAGMENT_LIB.top_fragments(3):
            from_str = to_string(e.node)
            print(f"  τ={e.tau:.3f}  freq={e.freq}  {from_str}")

    # Stats graphe de co-occurrences (Phase 5a)
    cg = state.COGRAPH.stats()
    print()
    print(f"[COGRAPH] Co-occurrence edges: {cg['edges']}")
    print(f"[COGRAPH] co max : {cg['max_co']:.5f}  |  co moyen : {cg['mean_co']:.5f}")
    top_pairs = state.COGRAPH.top_pairs(5, state.FRAGMENT_LIB)
    if top_pairs:
        print("[COGRAPH] Top 5 paires co-occurrentes :")
        for w, l1, l2 in top_pairs:
            l1s = l1[:35] + "…" if len(l1) > 36 else l1
            l2s = l2[:35] + "…" if len(l2) > 36 else l2
            print(f"  co={w:.4f}  [{l1s}]  ×  [{l2s}]")

    # Stats mémoire de séquences (Phase 5b)
    sm = state.SEQ_MEM.stats()
    print()
    print(f"[SEQ_MEM] Transitions apprises : {sm['n_transitions']}  "
          f"(poids total : {sm['total_weight']})")
    if sm['top5']:
        print("[SEQ_MEM] Top 5 transitions :")
        for trans, child in sm['top5']:
            print(f"  {trans:25s} → {child}")

    # [v21-VAL] retourner le dataset COMPLET (les menus affichent dessus)
    return global_best, xs_full, ys_full
