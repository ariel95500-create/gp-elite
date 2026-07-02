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
from . import core

__version__ = "0.2.0"

__all__ = ["symbolic_regression", "SRResult", "ParetoEntry", "core", "__version__"]
