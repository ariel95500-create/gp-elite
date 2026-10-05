"""
GP_ELITE — Régression symbolique par programmation génétique (1-D, N-D, CSV).

Découverte de lois empiriques interprétables sur petits jeux de données
expérimentaux : ≤10 variables, 100-5000 points, où l'on veut une FORMULE
plutôt qu'une boîte noire. Pur Python/NumPy, sans dépendance exotique.

Caractéristiques principales
----------------------------
- Modèle en îles asymétriques (explorer / cleaner / stigmergic) avec migration
- Linear scaling (Keijzer) + sélection ε-lexicase
- Parallélisme des îles (ProcessPoolExecutor, multi-cœurs)
- Validation hold-out + sélection parcimonieuse du champion (tolérance R²)
- Normalisation shift-free préservant la structure multiplicative
- Mode CSV générique : pointez un fichier, obtenez une loi validée
- Mémoire stigmergique transférable entre exécutions

Exemple minimal
---------------
>>> import numpy as np
>>> from gp_elite import symbolic_regression
>>> X = np.random.uniform(1, 5, (200, 2))
>>> y = 2.0 + 3.0 * np.sqrt(X[:, 0]) - 0.5 * X[:, 1]
>>> result = symbolic_regression(X, y, feature_names=["a", "b"], generations=40)
>>> print(result.expression)   # ex : 2.0 + 3.0*sqrt(a) - 0.5*b
>>> print(result.r2_validation)
"""

from .api import symbolic_regression, SRResult, ParetoEntry
from .stability import stability_analysis
from .dimensions import check_dimensions, audit_pareto, unit
from . import core


def __getattr__(name):
    # [v0.8] GPEliteRegressor est chargé à la première utilisation : il
    # dépend de scikit-learn, dont l'import coûtait les deux tiers du temps
    # d'`import gp_elite`, y compris dans chaque processus parallèle.
    if name == "GPEliteRegressor":
        from .sklearn_api import GPEliteRegressor
        globals()["GPEliteRegressor"] = GPEliteRegressor
        return GPEliteRegressor
    raise AttributeError("module 'gp_elite' has no attribute %r" % (name,))


def __dir__():
    return sorted(set(globals()) | {"GPEliteRegressor"})

# [CORRECTIF] La chaine etait saisie a la main et a derive de pyproject.toml
# (elle annoncait "0.6.0" dans le paquet publie en 0.6.1). On la lit desormais
# dans les metadonnees d'installation : une seule source de verite.
try:
    from importlib.metadata import version as _pkg_version, PackageNotFoundError
    try:
        __version__ = _pkg_version("gp-elite")
    except PackageNotFoundError:          # execute depuis les sources
        __version__ = "0.8.0"
except ImportError:                        # Python < 3.8
    __version__ = "0.8.0"

__all__ = ["symbolic_regression", "SRResult", "ParetoEntry", "stability_analysis", "audit_pareto", "check_dimensions", "unit", "GPEliteRegressor", "core", "__version__"]
