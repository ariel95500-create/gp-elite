"""
API haut niveau de GP_ELITE.

Expose une fonction unique `symbolic_regression(X, y, ...)` qui encapsule le
moteur d'évolution et retourne un objet résultat propre. Pensé pour l'usage
programmatique (notebooks, pipelines) ; le menu interactif reste accessible
via la CLI `gp-elite` ou `python -m gp_elite`.
"""
from __future__ import annotations

_HASHSEED_WARNED = False
import io
import random
import contextlib
from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

try:                                    # usage en package : gp_elite/
    from . import core
except ImportError:
    try:                                # usage direct : api.py à côté de core.py
        import core
    except ImportError:                 # dernier recours : core-2.py à côté
        import importlib.util as _ilu, os as _osp, sys as _sysp
        _p = _osp.path.join(_osp.path.dirname(_osp.path.abspath(__file__)), "core-2.py")
        if _osp.path.exists(_p):
            _spec = _ilu.spec_from_file_location("core", _p)
            core = _ilu.module_from_spec(_spec)
            _sysp.modules["core"] = core
            _spec.loader.exec_module(core)
        else:
            raise ImportError(
                "GP_ELITE : placez core.py (ou core-2.py) dans le même dossier "
                "que ce fichier, puis importez-le depuis votre script : "
                "from api import symbolic_regression")


@dataclass
class ParetoEntry:
    """Un point du front de Pareto complexité/précision.

    Chaque entrée est un modèle candidat non-dominé : aucun autre candidat
    n'est à la fois plus simple ET plus précis. `predict` accepte des X bruts
    (mêmes unités qu'au fit), comme SRResult.predict.
    """
    expression: str
    size: int
    mse_validation: Optional[float]
    r2_validation: Optional[float]
    node: "core.Node"
    scaler: object = None

    def predict(self, X: np.ndarray) -> np.ndarray:
        Xn = np.asarray(X, dtype=float)
        if Xn.ndim == 1:
            Xn = Xn.reshape(-1, 1)
        if self.scaler is not None:
            Xn = self.scaler.transform(Xn)
        return core.evaluate_vector(self.node, Xn)

    def __str__(self):
        r2 = f"{self.r2_validation:.6f}" if self.r2_validation is not None else "n/a"
        return f"[size={self.size:>3}] R²_val={r2}  {self.expression}"


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
    scaler: object = None   # [FIX] scaler interne pour dénormaliser dans predict
    pareto: Optional[list] = None   # [v27] front de Pareto (liste de ParetoEntry)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Prédit sur des features BRUTES (mêmes unités que le X passé au fit).

        Applique automatiquement la normalisation interne apprise au fit, donc
        l'utilisateur fournit des données dans leurs unités d'origine.
        """
        Xn = np.asarray(X, dtype=float)
        if Xn.ndim == 1:
            Xn = Xn.reshape(-1, 1)
        if self.scaler is not None:
            Xn = self.scaler.transform(Xn)
        return core.evaluate_vector(self.node, Xn)

    def diagnostics(self, X: np.ndarray, y: np.ndarray, verbose: bool = True,
                    ordered: bool = False):
        """[v0.3] Residual diagnostics — is this formula trustworthy on (X, y)?

        A high R² says the curve passes near the points; it does NOT say the
        model is right. These checks catch the ways a good-looking fit can
        still be wrong:

          - structure : residuals vs the model's own prediction should be
                        flat. Curvature (a parabola in the residual-vs-fitted
                        cloud) means a term is missing and the model is
                        systematically off in some region.
          - normality : residuals should look Gaussian. Heavy tails / skew
                        flag outliers or the wrong error model.
          - independence : only meaningful when rows have a real order (a
                        time series). Set ordered=True to enable the
                        Durbin-Watson test; a value far from 2 then means a
                        trend was missed. Off by default, because on
                        arbitrarily-ordered rows DW is meaningless.

        Returns a dict of raw numbers; prints a readable verdict if verbose.
        Pass the SAME data you care about (train to inspect the fit, or a
        held-out set to check generalization).
        """
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        y = np.asarray(y, dtype=float).ravel()
        yhat = self.predict(X)
        r = y - yhat
        n = r.size
        sd = float(np.std(r)) or 1e-30
        rs = r / sd

        # (1) structure: how much of the residual variance a smooth quadratic
        #     can still explain — from the fitted values AND from each feature.
        #     Order-independent. A missing term shows up as leftover curvature
        #     against ŷ (usually) or against a raw feature (when ŷ is ~constant,
        #     i.e. a badly underfit model).
        denom = float(np.sum((r - r.mean())**2)) or 1e-30
        def _curv_r2(v):
            if np.std(v) < 1e-30:
                return 0.0
            z = (v - v.mean()) / np.std(v)
            A = np.c_[np.ones_like(z), z, z**2]
            coef, *_ = np.linalg.lstsq(A, r, rcond=None)
            return max(0.0, 1.0 - float(np.sum((r - A @ coef)**2) / denom))
        struct = _curv_r2(yhat.astype(float))
        for k in range(X.shape[1]):
            struct = max(struct, _curv_r2(X[:, k]))

        # (2) normality: excess kurtosis & skew (0,0 for a Gaussian)
        skew = float(np.mean(rs**3))
        kurt = float(np.mean(rs**4) - 3.0)

        out = dict(n=n, resid_std=sd, structure_r2=struct,
                   skew=skew, excess_kurtosis=kurt)

        # (3) independence (opt-in): Durbin-Watson, only if rows are ordered
        dw = None
        if ordered:
            dw = float(np.sum(np.diff(r)**2) / np.sum(r**2)) if np.sum(r**2) > 0 else 2.0
            out["durbin_watson"] = dw

        if verbose:
            def flag(ok): return "OK  " if ok else "WARN"
            s_ok = struct < 0.10
            n_ok = abs(skew) < 1.0 and abs(kurt) < 2.0
            print("Residual diagnostics  (n=%d)" % n)
            print("  [%s] structure   : residual curvature R² = %.3f  "
                  "(want < 0.10 — else a term is missing)" % (flag(s_ok), struct))
            print("  [%s] normality   : skew = %+.2f, excess kurtosis = %+.2f  "
                  "(want ~0 — else outliers / wrong error model)" % (flag(n_ok), skew, kurt))
            all_ok = s_ok and n_ok
            if ordered:
                i_ok = 1.5 < dw < 2.5
                all_ok = all_ok and i_ok
                print("  [%s] independence: Durbin-Watson = %.2f  "
                      "(want ~2 — else autocorrelation)" % (flag(i_ok), dw))
            else:
                print("  [ -- ] independence: skipped (pass ordered=True for "
                      "time-series data)")
            if all_ok:
                print("  => residuals look like clean noise: no red flags.")
            else:
                print("  => at least one flag: the fit may be good but the "
                      "model is suspect. Treat the formula with caution.")
        return out

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
    robust: bool = False,
    extrapolate: bool = False,
    extrapolate_feature=None,
    extrapolate_direction: str = "both",
    restarts: int = 1,
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
    extrapolate : True active le mode extrapolation — hold-out sur la
                  bande-frontière du domaine (au lieu d'un tirage aléatoire)
                  + injection d'un candidat linéaire dans la sélection. À
                  utiliser quand on prédit HORS de la plage d'entraînement.
    extrapolate_feature : axe le long duquel on extrapole — nom de colonne
                  (str) ou index (int). None = score de bord sur toutes les
                  features. Désigner un axe implique extrapolate=True.
    extrapolate_direction : 'both' (deux bords) | 'high' (valeurs hautes, cas
                  prévision/forecasting) | 'low' (valeurs basses).
    restarts : nombre d'évolutions indépendantes (seeds espacés). Les archives
                  de candidats de TOUS les runs sont fusionnées — le hold-out
                  étant déterministe et identique entre runs, leurs MSE de
                  validation sont directement comparables — puis la sélection
                  parcimonieuse finale (avec polissage LM) choisit dans le pool
                  global. Convertit la variance inter-seeds en fiabilité ;
                  rendu abordable par l'accélération LM (v26).
    seed : graine de reproductibilité

    Reproductibilité [v29] : à seed égal, les répétitions AU SEIN d'un même
    processus sont identiques (workers parallèles inclus). Pour une
    reproductibilité ENTRE invocations de Python, lancez l'interpréteur avec
    PYTHONHASHSEED=0 (le hachage aléatoire des str, propre à CPython, modifie
    sinon l'ordre d'itération des `set` et donc certains tirages).
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

    # [v24-EXTRAP] Mode extrapolation : hold-out frontière + candidat linéaire.
    cfg.EXTRAPOLATION_MODE = bool(extrapolate)
    # [v24.1] Axe d'extrapolation (par nom ou index) + sens de la bande.
    if extrapolate_feature is not None:
        cfg.EXTRAPOLATION_MODE = True          # désigner un axe implique le mode
        if isinstance(extrapolate_feature, str):
            if extrapolate_feature not in feature_names:
                raise ValueError(
                    f"extrapolate_feature '{extrapolate_feature}' absent de "
                    f"feature_names {feature_names}")
            cfg.EXTRAPOLATION_FEATURE = feature_names.index(extrapolate_feature)
        else:
            cfg.EXTRAPOLATION_FEATURE = int(extrapolate_feature)
    if extrapolate_direction not in ("both", "high", "low"):
        raise ValueError("extrapolate_direction doit être 'both', 'high' ou 'low'")
    cfg.EXTRAPOLATION_DIRECTION = str(extrapolate_direction)

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

    # [ROBUST] Régression robuste aux outliers. Active une loss de Huber par
    # défaut (sauf loss_fn explicite), un scaling de coefficients robuste
    # (IRLS, insensible aux points aberrants), en gardant la structure cherchée
    # par GP. Le linear scaling MSE classique se ferait biaiser par les outliers.
    if robust:
        cfg.PARALLEL_ISLANDS = False
        if loss_fn is None:
            _delta_h = 1.345
            def _huber(preds, X, y, _d=_delta_h):
                r = preds - y; a = np.abs(r)
                return float(np.mean(np.where(a <= _d, 0.5 * r**2, _d * (a - 0.5 * _d))))
            core._CUSTOM_LOSS_FN = _huber
        core._CUSTOM_LOSS_USE_SCALING = True
        core._CUSTOM_LOSS_ROBUST = True
        cfg.USE_LINEAR_SCALING = False
        core._USE_LINEAR_SCALING = False
        # [ROBUST] Sans le linear scaling MSE (qui d'ordinaire favorise les
        # formes simples), le mode robuste tend à produire des arbres bouffis
        # qui sacrifient l'interprétabilité — le cœur de la régression
        # symbolique. Une légère parcimonie restaure des formules simples ET
        # robustes (size ~7 au lieu de ~50), au prix d'un R² très légèrement
        # inférieur.
        core._CUSTOM_LOSS_PARSIMONY = 0.5

    _placeholder = lambda Xm: np.zeros(Xm.shape[0])
    sink = contextlib.nullcontext() if verbose else contextlib.redirect_stdout(io.StringIO())
    n_restarts = max(1, int(restarts))
    _base_seed = seed if seed is not None else 0
    # [v29-REPRO] Avertissement unique : sans PYTHONHASHSEED figé, deux
    # invocations distinctes de Python peuvent produire des champions
    # différents à seed égal (hachage str aléatoire de CPython).
    global _HASHSEED_WARNED
    import os as _os
    if _os.environ.get("PYTHONHASHSEED") is None and not _HASHSEED_WARNED:
        _HASHSEED_WARNED = True
        print("[GP_ELITE] Note reproductibilité : lancez avec PYTHONHASHSEED=0 "
              "pour des résultats identiques entre invocations (les répétitions "
              "dans ce processus sont déjà déterministes).")
    try:
        # ── [v27] MULTI-RESTART : n évolutions indépendantes, archives fusionnées ──
        # Validité de la fusion : _split_holdout est déterministe (HOLDOUT_SEED
        # fixe, indépendant du seed d'évolution) → tous les runs partagent
        # EXACTEMENT les mêmes points de validation, leurs MSE sont comparables.
        champions = []          # (champ_node, mse_val)
        merged = {}             # expr_str -> (mse, se, size, node)  (dédup)
        X_full = y_full = None
        for k in range(n_restarts):
            sk = _base_seed + 1000 * k
            random.seed(sk); np.random.seed(sk)
            cfg.SEED = sk
            with sink:
                best, X_full, y_full = core.evolve(
                    _placeholder, cfg, problem_key="GENERIC_CSV",
                    X_override=X_scaled, y_override=y)
            _vm = core._holdout_mse(best, X_full, y_full)
            champions.append((best.copy(), _vm))
            for (m, se, sz, nd) in list(getattr(core, "_VAL_CANDS", [])):
                key = core.to_string(nd)
                if key not in merged or m < merged[key][0]:
                    merged[key] = (m, se, sz, nd.copy())

        best, champ_val = min(champions, key=lambda t: t[1])
        val_xs = getattr(core, "_VAL_XS", None)
        val_ys = getattr(core, "_VAL_YS", None)

        if n_restarts > 1 and val_xs is not None and merged:
            # Réinstalle le pool GLOBAL puis rejoue la sélection finale dessus :
            # polissage LM des meilleurs finalistes inter-runs, règle 1-SE,
            # garde de stabilité (mode extrapolation) — comme en fin de run,
            # mais sur l'union des connaissances des n restarts.
            pool = sorted(merged.values(), key=lambda t: (t[0], t[2]))[:core._VAL_CANDS_MAX]
            core._VAL_CANDS[:] = [t for t in pool]
            with sink:
                for (_m, _se, _sz, _nd) in pool[:8]:
                    _pol = core.optimize_constants_adam(_nd.copy(), X_full, y_full, cfg)
                    core._track_val_candidate(_pol)
                _sel, _sel_val = core._select_one_se(best, champ_val)
                if _sel is not None:
                    if (core._EXTRAP_PROBE_XS is not None
                            and not core._is_numerically_stable(_sel)):
                        _lin = core._make_linear_candidate(X_full, y_full, cfg)
                        if _lin is not None and core._is_numerically_stable(_lin):
                            _sel, _sel_val = _lin, core._holdout_mse(_lin, X_full, y_full)
                    best, champ_val = _sel.copy(), _sel_val

            # [v27-EXTRAP] SÉLECTION-FRONTIÈRE MÉTA. Synthèse des études v24/v25 :
            # la performance sur la bande-frontière PRÉDIT l'extrapolation
            # (validé deux fois), mais retirer cette bande du train ruine la
            # pente (leçon v25). Ici, la bande reste DANS le train ; elle sert
            # uniquement de CRITÈRE pour départager les candidats inter-runs —
            # là où la validation intérieure aléatoire ne classe pas le
            # comportement au bord. Garde-sonde (divergence hors-plage) requis,
            # départage parcimonieux à 1 erreur-type sur l'erreur de bande.
            _featj = getattr(cfg, "EXTRAPOLATION_FEATURE", None)
            if bool(getattr(cfg, "EXTRAPOLATION_MODE", False)) and _featj is not None:
                j = int(_featj)
                col = X_full[:, j]
                k_band = max(8, int(round(0.20 * len(col))))
                _dirn = str(getattr(cfg, "EXTRAPOLATION_DIRECTION", "both"))
                if _dirn == "high":
                    bidx = np.argsort(col)[-k_band:]
                elif _dirn == "low":
                    bidx = np.argsort(col)[:k_band]
                else:
                    half = max(4, k_band // 2)
                    o = np.argsort(col); bidx = np.r_[o[:half], o[-half:]]
                Xb, yb = X_full[bidx], y_full[bidx]
                cands = [(core.tree_size(nd), nd) for (_m, _se2, _sz2, nd) in core._VAL_CANDS]
                cands.append((core.tree_size(best), best))
                _lin2 = core._make_linear_candidate(X_full, y_full, cfg)
                if _lin2 is not None:
                    cands.append((core.tree_size(_lin2), _lin2))
                scored = []
                for _sz3, nd in cands:
                    if not core._is_numerically_stable(nd):
                        continue
                    try:
                        pr = core.evaluate_vector(nd, Xb)
                        e2 = (pr - yb) ** 2
                        mB = float(np.mean(e2))
                        if not np.isfinite(mB):
                            continue
                        seB = float(np.std(e2, ddof=1) / np.sqrt(len(e2))) if len(e2) > 1 else 0.0
                        scored.append((mB, seB, _sz3, nd))
                    except Exception:
                        continue
                if scored:
                    scored.sort(key=lambda t: t[0])
                    thrB = scored[0][0] + scored[0][1]
                    elig = [t for t in scored if t[0] <= thrB]
                    elig.sort(key=lambda t: (t[2], t[0]))
                    # [v27] CEINTURE FINALE : revérifie la stabilité du choix au
                    # moment de le retenir (les sondes ont pu être resserrées) ;
                    # descend la liste des éligibles puis TOUS les scorés ; en
                    # dernier ressort, la droite — jamais un modèle divergent.
                    _pick = None
                    for _cand in (elig + scored):
                        if core._is_numerically_stable(_cand[3]):
                            _pick = _cand[3]; break
                    if _pick is None and _lin2 is not None \
                            and core._is_numerically_stable(_lin2):
                        _pick = _lin2
                    if _pick is not None:
                        best = _pick.copy()
                        champ_val = core._holdout_mse(best, X_full, y_full)

        expression = core.to_string(best)

        # ── [v27] FRONT DE PARETO complexité/précision ──
        # Escalier des non-dominés : trié par taille croissante, un candidat
        # entre au front s'il bat strictement la meilleure MSE vue jusque-là.
        pareto_entries = []
        if val_xs is not None and val_ys is not None and len(val_ys) > 1:
            var_v = float(np.var(val_ys))
            _all = list(merged.values()) if merged else []
            _all.append((champ_val, 0.0, core.tree_size(best), best))
            _all = [t for t in _all if core._is_numerically_stable(t[3])]
            _all.sort(key=lambda t: (t[2], t[0]))          # taille puis MSE
            _best_mse = float("inf")
            for (m, _se, sz, nd) in _all:
                if m < _best_mse * (1.0 - 1e-12):
                    _best_mse = m
                    _r2 = (1.0 - m / var_v) if var_v > 1e-15 else None
                    pareto_entries.append(ParetoEntry(
                        expression=core.to_string(nd), size=int(sz),
                        mse_validation=float(m), r2_validation=_r2,
                        node=nd.copy(), scaler=scaler))
    finally:
        core._GENERIC_CSV_MODE = False
        core._CUSTOM_LOSS_FN = None   # [CUSTOM-LOSS] ne pas fuiter vers l'appel suivant
        core._CUSTOM_SEEDS = None         # idem : seeds custom non persistants
        core._CUSTOM_LOSS_PARSIMONY = 0.0  # idem : parcimonie custom réinitialisée
        core._CUSTOM_LOSS_USE_SCALING = False  # idem : scaling custom réinitialisé
        core._CUSTOM_LOSS_ROBUST = False       # idem : scaling robuste réinitialisé

    # ── Métriques ──
    mse_tr = core._pure_mse(best, X_full, y_full)
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
        scaler=scaler,   # [FIX] permet à predict de dénormaliser automatiquement
        pareto=pareto_entries or None,   # [v27] front complexité/précision
    )
