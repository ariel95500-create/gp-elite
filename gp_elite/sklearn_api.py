"""[v0.3] scikit-learn compatible estimator.

Wraps symbolic_regression in the standard fit/predict API so GP_ELITE drops
into sklearn Pipelines, cross_val_score, GridSearchCV — and, importantly, into
SRBench, whose harness expects a scikit-learn regressor exposing the discovered
equation.

    from gp_elite import GPEliteRegressor
    est = GPEliteRegressor(operators="physical", generations=40).fit(X, y)
    est.predict(X_new)
    est.sympy()          # the equation as a string

Design notes for sklearn conformance:
- __init__ only stores params, no logic and no validation (a hard sklearn rule).
- get_params/set_params come free from BaseEstimator because every __init__
  argument is stored on self under the same name.
- fitted attributes end with a trailing underscore (model_, n_features_in_).
"""
import numpy as np

try:
    from sklearn.base import BaseEstimator, RegressorMixin
    from sklearn.utils.validation import check_is_fitted
    try:
        from sklearn.utils.validation import validate_data
    except Exception:                   # older sklearn: no validate_data
        validate_data = None
    _HAS_SKLEARN = True
except Exception:                       # sklearn optional at import time
    BaseEstimator = object
    RegressorMixin = object
    validate_data = None
    _HAS_SKLEARN = False

from .api import symbolic_regression


class GPEliteRegressor(RegressorMixin, BaseEstimator):
    """Symbolic regression as a scikit-learn estimator.

    Parameters mirror symbolic_regression. After fit, the discovered model is
    in `model_` (an SRResult) and the equation string in `equation_`.
    """

    def __init__(self, operators="physical", normalize="auto",
                 generations=40, speed="fast", validation_split=0.20,
                 restarts=1, robust=False, parallel=None, random_state=0,
                 units=None, target_units=None, unknown_constant=False):
        # store-only: no logic here (sklearn requirement)
        self.operators = operators
        self.normalize = normalize
        self.generations = generations
        self.speed = speed
        self.validation_split = validation_split
        self.restarts = restarts
        self.robust = robust
        self.parallel = parallel
        self.random_state = random_state
        # [v0.4] Unités physiques (opt-in). None = comportement v0.3.
        self.units = units
        self.target_units = target_units
        # [v0.5] La constante multiplicative de tete peut porter une dimension,
        # deduite par homogeneite. Requiert units= et target_units=.
        self.unknown_constant = unknown_constant

    # sklearn tags. The API changed in 1.6: new versions call __sklearn_tags__,
    # older ones call _more_tags. Support both so SRBench works on any version.
    def _more_tags(self):
        return {"requires_y": True, "poor_score": True,
                "non_deterministic": False}

    def __sklearn_tags__(self):
        tags = super().__sklearn_tags__()
        # regressor that may score poorly on adversarial sklearn test sets
        try:
            tags.regressor_tags.poor_score = True
        except Exception:
            pass
        return tags

    def fit(self, X, y):
        if validate_data is not None:
            X, y = validate_data(self, X, y, y_numeric=True,
                                 ensure_min_samples=2, dtype="numeric")
        else:
            X = np.asarray(X, dtype=float); y = np.asarray(y, dtype=float)
            if X.ndim == 1:
                X = X.reshape(-1, 1)
            if X.shape[0] != y.shape[0]:
                raise ValueError("X and y have inconsistent lengths")
            if not np.all(np.isfinite(X)) or not np.all(np.isfinite(y)):
                raise ValueError("X and y must be finite")
            self.n_features_in_ = X.shape[1]
        if y.ndim != 1:
            y = y.ravel()

        names = [f"X{i}" for i in range(self.n_features_in_)]
        self.model_ = symbolic_regression(
            X, y, feature_names=names,
            operators=self.operators, normalize=self.normalize,
            generations=self.generations, speed=self.speed,
            validation_split=self.validation_split, restarts=self.restarts,
            robust=self.robust, parallel=self.parallel,
            units=self.units, target_units=self.target_units,
            unknown_constant=self.unknown_constant,
            seed=self.random_state)
        self.equation_ = self.model_.expression
        self.is_fitted_ = True
        if self.unknown_constant:
            self._deduce_constant()
        return self

    # ── [v0.5] constante mystere ────────────────────────────────────────────
    def _deduce_constant(self):
        """Deduit dimension et valeur de la constante multiplicative de tete.

        L'arbre livre a la forme  b * f(x)  (mise a l'echelle par l'origine,
        v0.4.1). Sa dimension physique est celle de f ; pour que le tout ait
        la dimension cible, b doit porter  cible / dim(f).  On expose :
            constant_units_  dict de dimensions, ex. {"kg": 1, "s": -2}
            constant_value_  float, la valeur ajustee de b
        Les deux valent None si la deduction echoue.
        """
        from . import dim_search as DS
        from . import core as C
        self.constant_units_ = None
        self.constant_value_ = None
        node = getattr(self.model_, "node", None)
        if node is None:
            return
        fd, tgt = DS.normalize_units_arg(
            self.units, self.target_units, self.n_features_in_,
            [f"X{i}" for i in range(self.n_features_in_)])

        # b = constante en tete si l'arbre est bien  (const * reste)
        inner, b = node, None
        if (node.value == "*" and node.left is not None
                and isinstance(node.left.value, float)):
            b, inner = float(node.left.value), node.right
        dim_inner = DS.infer_dim(inner, fd)
        if dim_inner is None:
            return
        # cible / dim(f)
        d = dict(tgt)
        for k, v in dim_inner.items():
            d[k] = d.get(k, 0.0) - float(v)
        self.constant_units_ = {k: v for k, v in d.items() if abs(v) > 1e-9}

        if b is None:
            return
        # ── Repliage de la normalisation ────────────────────────────────────
        # L'arbre voit des colonnes normalisees X/s, donc b est exprime dans
        # cet espace. Pour rendre la constante PHYSIQUE il faut le facteur
        # rho = prod(s_i ^ -e_i), ou e_i est l'exposant de la colonne i dans
        # l'expression. On obtient ces exposants en refaisant une inference
        # dimensionnelle ou chaque colonne porte sa PROPRE pseudo-dimension :
        # le resultat est directement le vecteur des exposants.
        scaler = getattr(self.model_, "scaler", None)
        sc = getattr(scaler, "scale_", None)
        if sc is None:
            self.constant_value_ = float(b)
            return
        pseudo = {i: {f"__s{i}": 1} for i in range(self.n_features_in_)}
        expo = DS.infer_dim(inner, pseudo)
        if expo is None:
            # Expression non monomiale en les colonnes (ex. m1 + m2) : aucune
            # constante brute unique n'existe. On laisse None plutot que de
            # rendre un nombre faux.
            return
        rho = 1.0
        for i in range(self.n_features_in_):
            e = float(expo.get(f"__s{i}", 0.0))
            if e:
                rho *= float(sc[i]) ** (-e)
        val = float(b) * rho
        self.constant_value_ = val if C.math.isfinite(val) else None

    def constant_units_string(self):
        """Les unites deduites, en texte lisible (ex. '[kg / s^2]')."""
        from .dimensions import _fmt
        d = getattr(self, "constant_units_", None)
        return None if d is None else _fmt(d)

    def predict(self, X):
        if _HAS_SKLEARN:
            check_is_fitted(self, "model_")
        elif not getattr(self, "is_fitted_", False):
            raise RuntimeError("call fit before predict")
        if validate_data is not None:
            X = validate_data(self, X, reset=False, dtype="numeric")
        else:
            X = np.asarray(X, dtype=float)
            if X.ndim == 1:
                X = X.reshape(-1, 1)
            if X.shape[1] != self.n_features_in_:
                raise ValueError(
                    f"X has {X.shape[1]} features, expected "
                    f"{self.n_features_in_}")
        return self.model_.predict(X)

    # SRBench convention: expose the symbolic model
    def sympy(self):
        """Return the discovered equation as a string (SRBench reads this)."""
        check_is_fitted(self, "model_") if _HAS_SKLEARN else None
        return self.equation_

    @property
    def pareto_(self):
        """The Pareto front of the fitted model (list of ParetoEntry)."""
        return getattr(self.model_, "pareto", None) if hasattr(self, "model_") else None
