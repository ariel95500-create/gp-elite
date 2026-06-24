"""
API haut niveau de GP_ELITE.

Expose une fonction unique `symbolic_regression(X, y, ...)` qui encapsule le
moteur d'évolution et retourne un objet résultat propre. Pensé pour l'usage
programmatique (notebooks, pipelines) ; le menu interactif reste accessible
via la CLI `gp-elite` ou `python -m gp_elite`.
"""
from __future__ import annotations

import io
import random
import contextlib
from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

from . import core


@dataclass
class SRResult:
    """Résultat d'une régression symbolique.

    Attributs
    ---------
    expression       : str   — la formule trouvée (noms de colonnes si fournis)
    r2_validation    : float — R² sur le hold-out (None si validation désactivée)
    mse_validation   : float — MSE sur le hold-out
    mse_train        : float — MSE sur l'entraînement
    size             : int   — nombre de nœuds de l'arbre
    depth            : int   — profondeur de l'arbre
    feature_names    : list  — noms des variables
    node             : core.Node — l'arbre brut (pour évaluation / inspection)
    predict          : callable — predict(X_norm) -> ndarray
    """
    expression: str
    r2_validation: Optional[float]
    mse_validation: Optional[float]
    mse_train: float
    size: int
    depth: int
    feature_names: list
    node: "core.Node"

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Prédit sur des features DÉJÀ normalisées (mêmes échelles que le fit)."""
        return core.evaluate_vector(self.node, np.asarray(X, dtype=float))

    def __str__(self) -> str:
        r2 = f"{self.r2_validation:.4f}" if self.r2_validation is not None else "n/a"
        return (f"SRResult(expr='{self.expression}', "
                f"R²_val={r2}, size={self.size})")


def symbolic_regression(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: Optional[Sequence[str]] = None,
    *,
    operators: str = "physical",
    normalize: str = "auto",
    generations: int = 100,
    speed: str = "fast",
    parallel: Optional[bool] = None,
    validation_split: float = 0.20,
    seed: Optional[int] = None,
    loss_fn=None,
    verbose: bool = False,
) -> SRResult:
    """Trouve une expression symbolique reliant X à y.

    Paramètres
    ----------
    X : ndarray (n_samples, n_features)  — variables explicatives (valeurs brutes)
    y : ndarray (n_samples,)             — cible
    feature_names : noms des colonnes (sinon X0, X1, …) — apparaissent dans la formule
    operators : 'physical' | 'trig' | 'full' | 'poly'  — pool d'opérateurs
    normalize : 'auto' | 'divmax' | 'minmax' | 'standard'
                'auto' = shift-free si toutes les features sont positives
    generations : nombre de générations
    speed : 'ultrafast' | 'fast' | 'normal'  — taille population / îles
    parallel : True force le multi-processus, False le désactive,
               None = auto (≥4 cœurs)
    validation_split : fraction hold-out (0.0 = pas de validation)
    seed : graine de reproductibilité
    verbose : True affiche les logs détaillés du moteur

    Retourne
    --------
    SRResult
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    if X.ndim != 2:
        raise ValueError(f"X doit être 2-D (n_samples, n_features), reçu {X.shape}")
    if y.ndim != 1 or len(y) != len(X):
        raise ValueError("y doit être 1-D de même longueur que X")
    n_feat = X.shape[1]

    if feature_names is None:
        feature_names = [f"X{i}" for i in range(n_feat)]
    feature_names = list(feature_names)
    if len(feature_names) != n_feat:
        raise ValueError("feature_names doit avoir une entrée par colonne de X")

    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    # ── Normalisation (réutilise le sélecteur du moteur) ──
    scaler, _desc = core._choose_scaler(X, normalize, (-2.0, 2.0))
    X_scaled = scaler.fit_transform(X)

    # ── Pool d'opérateurs + noms de colonnes (mode CSV générique) ──
    pool = (operators or "physical").lower()
    if pool not in core._GENCSV_POOLS:
        pool = "physical"
    b_ops, b_w, u_ops, u_w = core._GENCSV_POOLS[pool]
    core._GENERIC_BINARY_OPS, core._GENERIC_BINARY_WEIGHTS = list(b_ops), list(b_w)
    core._GENERIC_UNARY_OPS, core._GENERIC_UNARY_WEIGHTS = list(u_ops), list(u_w)
    core._GENERIC_CSV_MODE = True
    core.CSV_FEATURE_NAMES = list(feature_names)
    core.CSV_TARGET_NAME = "y"

    fast = (speed == "fast")
    ultrafast = (speed == "ultrafast")

    cfg = core.make_cfg_nd(n_features=n_feat, x_min=-2.0, x_max=2.0,
                           fast=fast, ultrafast=ultrafast, use_seeding=False,
                           use_lib=True, use_cograph=True, use_seqmem=True)
    cfg.GENERATIONS = int(generations)
    cfg.N_POINTS = len(y)
    cfg.VALIDATION_SPLIT = float(validation_split)
    cfg.SEED = seed   # [REPRO] propage le seed pour le parallélisme déterministe
    if parallel is not None:
        cfg.PARALLEL_ISLANDS = bool(parallel)

    # [CUSTOM-LOSS] Installe la fonction de coût personnalisée dans le moteur.
    # Quand elle est active, on force le mode séquentiel : les workers spawn
    # ne partagent pas la globale (et une fonction Python arbitraire ne se
    # sérialise pas toujours proprement). Limitation assumée de cette version.
    core._CUSTOM_LOSS_FN = loss_fn
    if loss_fn is not None:
        cfg.PARALLEL_ISLANDS = False
        # Le linear scaling (a + b·f contre y) suppose un y supervisé : avec
        # une loss custom (souvent sans y), il dénaturerait le champion (ex.
        # le réduirait à ~0 face à un y factice). On le désactive globalement.
        cfg.USE_LINEAR_SCALING = False
        core._USE_LINEAR_SCALING = False

    _placeholder = lambda Xm: np.zeros(Xm.shape[0])
    sink = contextlib.nullcontext() if verbose else contextlib.redirect_stdout(io.StringIO())
    try:
        with sink:
            best, X_full, y_full = core.evolve(
                _placeholder, cfg, problem_key="GENERIC_CSV",
                X_override=X_scaled, y_override=y)
        # Capturer l'expression PENDANT que le mode CSV est actif, pour que
        # to_string substitue bien les noms de colonnes (a, b, …) à X[i].
        expression = core.to_string(best)
    finally:
        core._GENERIC_CSV_MODE = False
        core._CUSTOM_LOSS_FN = None   # [CUSTOM-LOSS] ne pas fuiter vers l'appel suivant
        core._CUSTOM_SEEDS = None         # idem : seeds custom non persistants
        core._CUSTOM_LOSS_PARSIMONY = 0.0  # idem : parcimonie custom réinitialisée

    # ── Métriques ──
    mse_tr = core._pure_mse(best, X_full, y_full)
    val_xs = getattr(core, "_VAL_XS", None)
    val_ys = getattr(core, "_VAL_YS", None)
    r2_val = mse_val = None
    if val_xs is not None and val_ys is not None and len(val_ys) > 1:
        preds = core.evaluate_vector(best, val_xs)
        mse_val = float(np.mean((preds - val_ys) ** 2))
        var = float(np.var(val_ys))
        r2_val = (1.0 - mse_val / var) if var > 1e-15 else float("nan")

    return SRResult(
        expression=expression,
        r2_validation=r2_val,
        mse_validation=mse_val,
        mse_train=float(mse_tr),
        size=core.tree_size(best),
        depth=core.tree_depth(best),
        feature_names=feature_names,
        node=best,
    )
