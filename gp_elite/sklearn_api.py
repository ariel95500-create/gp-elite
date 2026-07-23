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
                 units=None, target_units=None):
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
            seed=self.random_state)
        self.equation_ = self.model_.expression
        self.is_fitted_ = True
        return self

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
