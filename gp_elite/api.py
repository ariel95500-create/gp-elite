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

try:                                    # [v0.7] formule en variables brutes
    from . import formula as _formula
except ImportError:
    import formula as _formula


def _build_raw_formula(node, scaler, X_raw, names):
    """[v0.7] Formula of `node` in the RAW variables, checked against predict.

    Returns (RawFormula or None, display string). None only if the scaler is
    not a per-column affine map (never the case for the engine's own
    scalers): the display then carries the variable transformation
    explicitly instead of silently showing a scaled-space formula.
    """
    try:
        rf = _formula.raw_formula(node, scaler, X_raw, names)
        return rf, rf.text()
    except Exception:
        with contextlib.redirect_stdout(io.StringIO()):
            s = core.to_string(node)
        return None, "%s   [scaled inputs: %s]" % (
            s, _formula.scaled_expression_note(scaler, X_raw, names))


def _sympy_or_raise(obj, feature_names):
    if obj.formula is None:
        raise RuntimeError("no raw-variable formula available for this model "
                           "(its input scaler is not a per-column affine map)")
    names = list(feature_names) if feature_names is not None else obj.formula.names
    bad = _names_misread_by_sympy(names or [])
    if bad:
        import warnings
        warnings.warn(
            "GP_ELITE: sympy.sympify would misread the variable name%s %s in "
            "this string (a sympy constant or function, a Python keyword, or "
            "not an identifier: sympify reads E as 2.718..., I as sqrt(-1)). "
            "Use .sympy_expr(), which builds the expression with one Symbol "
            "per column, or pass other names to .sympy()."
            % ("s" if len(bad) > 1 else "", ", ".join(repr(b) for b in bad)),
            UserWarning, stacklevel=3)
    return obj.formula.sympy(names)


_SYMPY_NAMES = None


def _names_misread_by_sympy(names):
    """[v0.8] Names that sympy.sympify would not read as a plain symbol."""
    global _SYMPY_NAMES
    import keyword
    if _SYMPY_NAMES is None:
        try:
            ns = {}
            exec("from sympy import *", ns)
            _SYMPY_NAMES = frozenset(ns)
        except ImportError:
            _SYMPY_NAMES = frozenset()
    return [str(n) for n in names
            if not str(n).isidentifier() or keyword.iskeyword(str(n))
            or str(n) in _SYMPY_NAMES]


def _sympy_expr(obj, feature_names):
    """The formula as a sympy expression with one Symbol per column, whatever
    the column names are."""
    if obj.formula is None:
        raise RuntimeError("no raw-variable formula available for this model "
                           "(its input scaler is not a per-column affine map)")
    import sympy
    names = list(feature_names) if feature_names is not None else obj.formula.names
    names = [str(n) for n in (names or [])]
    ph = ["_gpe_var%d" % i for i in range(len(names))]
    text = obj.formula.sympy(ph)
    return sympy.sympify(text, locals={p: sympy.Symbol(n)
                                       for p, n in zip(ph, names)})


# ── [v0.8] Données d'entrée : refuser clairement plutôt que calculer faux ────
# Jusqu'en 0.7, une valeur manquante (NaN) ou infinie dans X ou y passait
# sans erreur : l'ajustement rendait une formule sans rapport avec les
# données, sans le moindre avertissement. Et predict() prenait un échantillon
# 1-D pour une colonne, acceptait un nombre de colonnes faux, et rendait 0
# pour une ligne contenant NaN. Les messages sont en anglais, comme le reste
# des erreurs de l'API.

def _column_names(X, n):
    cols = getattr(X, "columns", None)
    if cols is not None and len(cols) == n:
        return [str(c) for c in cols]
    return ["X%d" % i for i in range(n)]


def _to_float_matrix(X, what="X"):
    """X as a 2-D float array; a clear error names a non-numeric column."""
    try:
        return np.asarray(X, dtype=float)
    except (TypeError, ValueError):
        pass
    obj = np.asarray(X, dtype=object)
    if obj.ndim == 1:
        obj = obj.reshape(-1, 1)
    names = _column_names(X, obj.shape[1] if obj.ndim == 2 else 1)
    if obj.ndim == 2:
        for j in range(obj.shape[1]):
            for i in range(obj.shape[0]):
                try:
                    float(obj[i, j])
                except (TypeError, ValueError):
                    raise ValueError(
                        "%s column %r is not numeric (row %d holds %r). "
                        "Convert it to numbers or leave it out."
                        % (what, names[j], i, obj[i, j])) from None
    raise ValueError("%s must contain numbers only" % what)


def _check_finite(A, what, names=None):
    bad = ~np.isfinite(A)
    if bad.any():
        rows, cols = np.nonzero(bad.reshape(A.shape[0], -1))
        where = "row %d" % rows[0]
        if names is not None and A.ndim == 2:
            where += ", column %r" % names[cols[0]]
        raise ValueError(
            "%s contains %d missing or infinite value%s in %d row%s (first: "
            "%s). gp-elite needs complete numeric data: remove or impute "
            "these rows." % (what, int(bad.sum()), "s" if bad.sum() > 1 else "",
                             len(set(rows.tolist())),
                             "s" if len(set(rows.tolist())) > 1 else "", where))


def _prepare_fit_data(X, y, feature_names):
    """Validated (X 2-D float, y 1-D float, feature names) for a fit."""
    if feature_names is None and getattr(X, "columns", None) is not None:
        feature_names = _column_names(X, len(X.columns))
    Xa = _to_float_matrix(X, "X")
    ya = _to_float_matrix(y, "y")
    if ya.ndim == 2 and ya.shape[1] == 1:
        ya = ya.ravel()
    if ya.ndim != 1:
        raise ValueError("y must be a single target: 1-D, or 2-D with one "
                         "column (got shape %s)" % (ya.shape,))
    if Xa.ndim == 1 and len(Xa) == len(ya):
        Xa = Xa.reshape(-1, 1)          # one variable
    if Xa.ndim != 2:
        raise ValueError("X must be 2-D (n_samples, n_features), got shape %s"
                         % (Xa.shape,))
    if len(Xa) != len(ya):
        raise ValueError("X has %d rows but y has %d values" % (len(Xa), len(ya)))
    if len(ya) < 3:
        raise ValueError("at least 3 samples are needed (got %d)" % len(ya))
    if Xa.shape[1] < 1:
        raise ValueError("X has no column")
    if feature_names is None:
        feature_names = ["X%d" % i for i in range(Xa.shape[1])]
    feature_names = [str(n) for n in feature_names]
    if len(feature_names) != Xa.shape[1]:
        raise ValueError("feature_names has %d names but X has %d columns"
                         % (len(feature_names), Xa.shape[1]))
    _check_finite(Xa, "X", feature_names)
    _check_finite(ya, "y")
    return Xa, ya, feature_names


def _predict_inputs(X, n_features):
    """X for predict(): 2-D, with the number of columns of the fit."""
    Xn = _to_float_matrix(X, "X")
    if Xn.ndim == 1:
        if n_features is None or n_features == 1:
            Xn = Xn.reshape(-1, 1)
        else:
            raise ValueError(
                "X is 1-D but the model uses %d variables: pass an array of "
                "shape (n_samples, %d); for a single sample, "
                "X.reshape(1, -1)" % (n_features, n_features))
    if Xn.ndim != 2:
        raise ValueError("X must be 2-D (n_samples, n_features), got shape %s"
                         % (Xn.shape,))
    if n_features is not None and Xn.shape[1] != n_features:
        raise ValueError("X has %d column%s but the model was fitted on %d"
                         % (Xn.shape[1], "s" if Xn.shape[1] != 1 else "",
                            n_features))
    return Xn


def _predict_raw(node, scaler, X, n_features):
    """Predictions on raw inputs. A row with a missing or infinite input gets
    NaN (it used to get 0, a plausible-looking wrong value)."""
    Xn = _predict_inputs(X, n_features)
    bad = ~np.isfinite(Xn).all(axis=1)
    Xs = scaler.transform(Xn) if scaler is not None else Xn
    out = core.evaluate_vector(node, Xs)
    if bad.any():
        out = np.array(out, dtype=float)
        out[bad] = np.nan
    return out


@dataclass
class ParetoEntry:
    """Un point du front de Pareto complexité/précision.

    Chaque entrée est un modèle candidat non-dominé : aucun autre candidat
    n'est à la fois plus simple ET plus précis. `predict` accepte des X bruts
    (mêmes unités qu'au fit), comme SRResult.predict. `expression` est la
    formule en variables BRUTES (voir SRResult).
    """
    expression: str
    size: int
    mse_validation: Optional[float]
    r2_validation: Optional[float]
    node: "core.Node"
    scaler: object = None
    formula: object = None          # [v0.7] formula.RawFormula (variables brutes)
    n_features: Optional[int] = None   # [v0.8] colonnes attendues par predict

    @property
    def formula_exact(self) -> Optional[bool]:
        return None if self.formula is None else self.formula.exact

    def sympy(self, feature_names=None) -> str:
        """Sympy-parsable formula in the raw variables (see SRResult.sympy)."""
        return _sympy_or_raise(self, feature_names)

    def sympy_expr(self, feature_names=None):
        """The formula as a sympy expression (see SRResult.sympy_expr)."""
        return _sympy_expr(self, feature_names)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predictions on RAW inputs (same units as the fit). A row with a
        missing or infinite input gets NaN."""
        return _predict_raw(self.node, self.scaler, X, self.n_features)

    def __str__(self):
        r2 = f"{self.r2_validation:.6f}" if self.r2_validation is not None else "n/a"
        return f"[size={self.size:>3}] R²_val={r2}  {self.expression}"


@dataclass
class SRResult:
    """Résultat d'une régression symbolique.

    Attributs
    ---------
    expression       : str   — la formule trouvée, écrite dans les variables
                               BRUTES (celles passées au fit) : évaluée sur ces
                               données, elle reproduit predict(). [v0.7]
                               Jusqu'en 0.6.x elle était écrite dans l'espace
                               normalisé interne, avec les noms bruts : fausse
                               sur les données brutes.
    formula_exact    : bool  — la formule reproduit predict() sur les données
                               d'entraînement (vérifié au fit, jamais supposé).
                               False signale qu'un garde-fou numérique du
                               moteur agit quelque part sur ces données.
    time_limit_reached : bool — l'échéance `time_limit` a interrompu la recherche
    restarts_completed : int  — redémarrages effectivement lancés
    r2_validation    : float — R² sur le hold-out interne (None si validation
                               désactivée). Ce hold-out sert à CHOISIR le
                               modèle (sélection du champion, des redémarrages,
                               du front de Pareto) : c'est une mesure de
                               sélection, optimiste, pas une estimation
                               indépendante de la généralisation. Pour celle-ci,
                               gardez votre propre jeu de test hors du fit.
    mse_validation   : float — MSE sur ce même hold-out
    mse_train        : float — MSE sur la partie entraînement (hors hold-out)
    size             : int   — nombre de nœuds de l'arbre de recherche
    depth            : int   — profondeur de l'arbre
    feature_names    : list  — noms des variables
    node             : core.Node — l'arbre dans l'espace NORMALISÉ du moteur
                               (celui qu'évalue predict après normalisation)
    formula          : formula.RawFormula — l'arbre en variables brutes
    predict          : callable — predict(X_brut) -> ndarray
    sympy            : callable — sympy(noms) -> chaîne sympy exacte
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
    # [v0.7-TIME] Diagnostic du budget de temps : vrai si l'echeance a
    # interrompu au moins une evolution ; nombre de redemarrages effectivement
    # lances (peut etre inferieur a `restarts` si le temps est epuise).
    time_limit_reached: bool = False
    restarts_completed: int = 1
    formula: object = None          # [v0.7] formula.RawFormula (variables brutes)

    @property
    def formula_exact(self) -> Optional[bool]:
        return None if self.formula is None else self.formula.exact

    def sympy(self, feature_names=None) -> str:
        """The formula as a sympy-parsable string, in the RAW variables.

        ``sympy.sympify(result.sympy())`` evaluated on the raw inputs gives
        ``result.predict`` (see ``formula_exact``). Constants keep full float
        precision. Names default to ``feature_names``. A name that sympify
        would not read as a plain symbol (E, I, N, S, beta, lambda, a name
        with a space...) triggers a warning: use ``sympy_expr()`` then.
        """
        return _sympy_or_raise(self, feature_names)

    def sympy_expr(self, feature_names=None):
        """The formula as a sympy expression, one ``sympy.Symbol`` per column
        named after it. Unlike ``sympify(result.sympy())``, it is right for
        any column name: a column called E stays a symbol instead of becoming
        Euler's number. Requires sympy.
        """
        return _sympy_expr(self, feature_names)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Prédit sur des features BRUTES (mêmes unités que le X passé au fit).

        Applique automatiquement la normalisation interne apprise au fit, donc
        l'utilisateur fournit des données dans leurs unités d'origine.
        """
        return _predict_raw(self.node, self.scaler, X,
                            len(self.feature_names) if self.feature_names else None)

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
    generations: Optional[int] = None,
    speed: str = "fast",
    parallel: Optional[bool] = None,
    validation_split: float = 0.20,
    seed: Optional[int] = None,
    units=None,
    target_units=None,
    unknown_constant: bool = False,
    loss_fn=None,
    robust: bool = False,
    extrapolate: bool = False,
    extrapolate_feature=None,
    extrapolate_direction: str = "both",
    restarts: int = 1,
    time_limit: Optional[float] = None,
    verbose: bool = False,
) -> SRResult:
    """Trouve une expression symbolique reliant X à y.

    Paramètres
    ----------
    X : ndarray (n_samples, n_features)  — variables explicatives (valeurs brutes)
    y : ndarray (n_samples,)             — cible
    feature_names : noms des colonnes (sinon X0, X1, …) — apparaissent dans la formule
    operators : 'physical' | 'trig' | 'full' | 'poly'  — pool d'opérateurs
    normalize : 'auto' | 'divmax' | 'grouped' | 'minmax' | 'standard' | 'none'
                'grouped' [v0.8] : un facteur commun aux colonnes d'échelles
                comparables, pour les lois qui additionnent ou soustraient
                des variables de même nature (voir le README).
                'auto' = 'divmax' : chaque colonne divisée par son max|x|,
                sans décalage (préserve x*y, x/y, x^n). [v0.7] Aussi pour les
                colonnes signées, qui passaient auparavant en min-max.
                Quelle que soit la normalisation, `expression` et `sympy()`
                sont rendus dans les variables brutes.
    generations : nombre de générations. None (défaut) = 200 avec
                  speed='thorough', 100 sinon.
    speed : 'ultrafast' | 'fast' | 'thorough' | 'normal'
        Taille de population et nombre d'îles. 'fast' (défaut) pour explorer
        rapidement ; 'thorough' pour CHERCHER UNE LOI : population 400, 4 îles,
        et generations=200 par défaut — plus lent, plus de calcul consacré à
        la forme exacte, sans garantie de la trouver.
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
    time_limit : budget de temps TOTAL en secondes (None = pas de limite).
                  La recherche s'arrête proprement à l'échéance et rend le
                  meilleur modèle trouvé — au lieu d'être interrompue sans
                  résultat par un minuteur externe. Le temps restant est
                  partagé équitablement entre les redémarrages non encore
                  lancés ; un redémarrage qui converge tôt libère son temps
                  pour les suivants. La première génération s'exécute
                  toujours, pour garantir un modèle. Précision : environ une
                  génération au-delà de l'échéance, plus la sélection finale
                  (typiquement < 1 % du temps total).
    restarts : nombre d'évolutions indépendantes (seeds espacés). Les archives
                  de candidats de TOUS les runs sont fusionnées — le hold-out
                  étant déterministe et identique entre runs, leurs MSE de
                  validation sont directement comparables — puis la sélection
                  parcimonieuse finale (avec polissage LM) choisit dans le pool
                  global. Convertit la variance inter-seeds en fiabilité ;
                  rendu abordable par l'accélération LM (v26).
    seed : graine de reproductibilité

    Reproductibilité [v0.8] : à seed égal, deux ajustements sur les mêmes
    données rendent le même modèle, dans un même processus comme d'un
    lancement de Python à l'autre (PYTHONHASHSEED n'intervient plus). Le
    mode parallèle suit un autre chemin que le mode séquentiel : pour
    retrouver un résultat sur une autre machine, fixez aussi `parallel`
    (None l'active dès 4 cœurs). Les calculs flottants de NumPy peuvent
    différer d'une version ou d'un processeur à l'autre.
    verbose : True affiche les logs détaillés du moteur

    Retourne
    --------
    SRResult
    """
    # [v0.8] Entrées vérifiées : NaN/infini refusés avec la ligne et la
    # colonne en cause, colonne non numérique nommée, y en colonne accepté,
    # X 1-D pris comme une seule variable, noms de colonnes d'un DataFrame
    # repris comme noms de variables.
    X, y, feature_names = _prepare_fit_data(X, y, feature_names)
    n_feat = X.shape[1]

    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    # ── Normalisation (réutilise le sélecteur du moteur) ──
    # [v0.5] La normalisation est CONSERVEE en mode constante mystere : la
    # desactiver exposait le moteur aux amplitudes physiques brutes (m1*m2
    # atteint 1e8 sur la gravitation) que _SAFE_LIMIT = 1e6 ecrete, ce qui
    # detruisait la recherche. L'estimateur replie les facteurs d'echelle
    # dans la constante rendue (voir GPEliteRegressor._deduce_constant).
    # [v0.7] Valeurs inconnues REFUSÉES. Auparavant une faute de frappe
    # passait en silence : operators='phsyical' -> 'physical', speed='fats'
    # -> preset 'normal', normalize='divmx' -> min-max.
    pool = (operators or "physical").lower()
    if pool not in core._GENCSV_POOLS:
        raise ValueError("operators=%r is not one of %s"
                         % (operators, sorted(core._GENCSV_POOLS)))
    if speed not in ("ultrafast", "fast", "normal", "thorough"):
        raise ValueError("speed=%r is not one of ['ultrafast', 'fast', "
                         "'normal', 'thorough']" % (speed,))
    _norms = ("auto", "divmax", "shiftfree", "div", "minmax", "standard",
              "zscore", "std", "none", "off", "raw", "identity", "smart",
              "grouped")
    if (normalize or "auto").lower() not in _norms:
        raise ValueError("normalize=%r is not one of ['auto', 'divmax', "
                         "'grouped', 'minmax', 'standard', 'none', 'smart']"
                         % (normalize,))
    scaler, _desc = core._choose_scaler(X, normalize, (-2.0, 2.0))
    X_scaled = scaler.fit_transform(X)

    # ── Pool d'opérateurs + noms de colonnes (mode CSV générique) ──
    b_ops, b_w, u_ops, u_w = core._GENCSV_POOLS[pool]
    core._GENERIC_BINARY_OPS, core._GENERIC_BINARY_WEIGHTS = list(b_ops), list(b_w)
    core._GENERIC_UNARY_OPS, core._GENERIC_UNARY_WEIGHTS = list(u_ops), list(u_w)
    core._GENERIC_CSV_MODE = True
    core.CSV_FEATURE_NAMES = list(feature_names)
    core.CSV_TARGET_NAME = "y"

    fast = (speed == "fast")
    ultrafast = (speed == "ultrafast")
    thorough = (speed == "thorough")

    cfg = core.make_cfg_nd(n_features=n_feat, x_min=-2.0, x_max=2.0,
                           fast=fast, ultrafast=ultrafast, thorough=thorough, use_seeding=False,
                           use_lib=True, use_cograph=True, use_seqmem=True)
    # [v0.7] 'thorough' annonçait 200 générations, mais symbolic_regression
    # imposait toujours son défaut de 100 (seul GPEliteRegressor appliquait
    # le preset) : le défaut dépend maintenant du preset.
    if generations is None:
        generations = 200 if thorough else 100
    cfg.GENERATIONS = int(generations)
    cfg.WRITE_LOG_CSV = False      # [v0.7] l'API n'ecrit aucun fichier
    # [v0.4] Recherche contrainte par les dimensions (opt-in).
    if units is not None:
        from .dim_search import normalize_units_arg
        cfg.FEAT_DIMS, cfg.TARGET_DIM = normalize_units_arg(
            units, target_units, n_feat, feature_names)
        cfg.UNKNOWN_CONST = bool(unknown_constant)   # [v0.5]
    elif unknown_constant:
        raise ValueError("unknown_constant=True exige units= et target_units=.")
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
                # [FIX-ROBUST] Résidus STANDARDISÉS par une échelle robuste de y
                # (1.4826*MAD ~ sigma). Sans cela la perte dépend de l'UNITÉ de y :
                # combinée à une parcimonie absolue, elle rendait une constante
                # moins coûteuse que la forme vraie dès que std(y) était petit
                # (I.8.14, I.12.2, I.16.6 renvoyaient une constante ou une droite,
                # même SANS bruit). delta=1.345 retrouve ici son sens statistique
                # usuel : un seuil exprimé en écarts-types de résidu.
                med = float(np.median(y))
                s = 1.4826 * float(np.median(np.abs(y - med)))
                if not (s > 0.0 and np.isfinite(s)):
                    s = float(np.std(y)) or 1.0
                r = (preds - y) / s; a = np.abs(r)
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
        # [FIX-ROBUST] La perte standardisée vit dans ~[0, 1] (~0.5 pour un
        # modèle constant). L'ancienne pénalité de 0.5/noeud la DOMINAIT : une
        # forme vraie de 10 noeuds coûtait 5.0, contre ~1.0 pour une constante
        # — la structure ne pouvait mathématiquement pas gagner. 0.005/noeud
        # conserve le rasoir d'Ockham (arbre-monstre de 60 noeuds : +0.30)
        # sans jamais interdire la forme vraie (+0.05).
        core._CUSTOM_LOSS_PARSIMONY = 0.005

    _placeholder = lambda Xm: np.zeros(Xm.shape[0])
    sink = contextlib.nullcontext() if verbose else contextlib.redirect_stdout(io.StringIO())
    n_restarts = max(1, int(restarts))
    _base_seed = seed if seed is not None else 0
    # [v0.7-TIME] Echeance globale ; partagee ensuite entre redemarrages.
    import time as _time
    if time_limit is not None:
        time_limit = float(time_limit)
        if not (time_limit > 0 and np.isfinite(time_limit)):
            raise ValueError("time_limit must be a positive number of seconds "
                             "(got %r)" % (time_limit,))
    _hard_deadline = (_time.time() + time_limit) if time_limit is not None else None
    _time_hit = False
    _restarts_done = 0
    # [v0.8] La note « lancez avec PYTHONHASHSEED=0 », imprimée une fois par
    # processus jusqu'à la 0.7, est retirée : les hachages d'arbres ne
    # dépendent plus du hachage des chaînes de CPython, et seed= suffit
    # (tests/test_guarantees.py, section 15).
    try:
        # ── [v27] MULTI-RESTART : n évolutions indépendantes, archives fusionnées ──
        # Validité de la fusion : _split_holdout est déterministe (HOLDOUT_SEED
        # fixe, indépendant du seed d'évolution) → tous les runs partagent
        # EXACTEMENT les mêmes points de validation, leurs MSE sont comparables.
        champions = []          # (champ_node, mse_val)
        merged = {}             # expr_str -> (mse, se, size, node)  (dédup)
        X_full = y_full = None
        for k in range(n_restarts):
            if _hard_deadline is not None:
                _remaining = _hard_deadline - _time.time()
                if k > 0 and _remaining <= 0:
                    _time_hit = True
                    break                      # temps epuise : on garde l'acquis
                # part egale du temps restant pour ce redemarrage
                cfg.DEADLINE = _time.time() + max(0.0, _remaining) / (n_restarts - k)
            else:
                cfg.DEADLINE = None
            sk = _base_seed + 1000 * k
            random.seed(sk); np.random.seed(sk)
            cfg.SEED = sk
            with sink:
                best, X_full, y_full = core.evolve(
                    _placeholder, cfg, problem_key="GENERIC_CSV",
                    X_override=X_scaled, y_override=y)
            _restarts_done += 1
            _time_hit = _time_hit or bool(getattr(core, "_TIME_LIMIT_HIT", False))
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
                        node=nd.copy(), scaler=scaler, n_features=n_feat))
    finally:
        core._GENERIC_CSV_MODE = False
        core._CUSTOM_LOSS_FN = None   # [CUSTOM-LOSS] ne pas fuiter vers l'appel suivant
        core._CUSTOM_SEEDS = None         # idem : seeds custom non persistants
        core._CUSTOM_LOSS_PARSIMONY = 0.0  # idem : parcimonie custom réinitialisée
        core._CUSTOM_LOSS_USE_SCALING = False  # idem : scaling custom réinitialisé
        core._CUSTOM_LOSS_ROBUST = False       # idem : scaling robuste réinitialisé

    # ── Métriques ──
    # [v0.7] mse_train sur la partie ENTRAINEMENT seulement : auparavant sur
    # toutes les données, hold-out compris (signalé par la revue externe).
    tr_xs = getattr(core, "_VAL_TRAIN_XS", None)
    tr_ys = getattr(core, "_VAL_TRAIN_YS", None)
    if val_xs is None or tr_xs is None or tr_ys is None or len(tr_ys) == 0:
        tr_xs, tr_ys = X_full, y_full
    mse_tr = core._pure_mse(best, tr_xs, tr_ys)
    r2_val = mse_val = None
    if val_xs is not None and val_ys is not None and len(val_ys) > 1:
        preds = core.evaluate_vector(best, val_xs)
        mse_val = float(np.mean((preds - val_ys) ** 2))
        var = float(np.var(val_ys))
        r2_val = (1.0 - mse_val / var) if var > 1e-15 else float("nan")

    # ── [v0.7] La formule LIVRÉE, en variables brutes, vérifiée ──
    # L'arbre vit dans l'espace normalisé du moteur ; l'afficher avec les noms
    # bruts donnait une formule fausse sur les données brutes (revue externe,
    # bloquant n°1). On la réécrit en variables brutes et on vérifie qu'elle
    # reproduit predict() sur les données d'entraînement.
    raw_formula, expression = _build_raw_formula(best, scaler, X, feature_names)
    if raw_formula is not None and not raw_formula.exact:
        # [v0.7] Jamais en silence : la formule affichee est la fonction
        # mathematique sans les garde-fous numeriques du moteur ; la ou l'un
        # d'eux agit, elle s'ecarte de predict(), qui reste le modele.
        import warnings
        warnings.warn(
            "GP_ELITE: the formula printed for the returned model departs from "
            "predict() on %d of %d training rows (largest gap %.3g), most "
            "often because a numerical safety net of the engine acts there (a "
            "power capped at 1e6 or clipped, a division by a near-zero "
            "denominator...). predict() is the model; result.formula_exact is "
            "False."
            % (raw_formula.rows_off, len(y), raw_formula.max_error),
            RuntimeWarning, stacklevel=2)
    for e in pareto_entries:
        e.formula, e.expression = _build_raw_formula(e.node, scaler, X, feature_names)

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
        time_limit_reached=bool(_time_hit),
        restarts_completed=int(_restarts_done),
        formula=raw_formula,
    )
