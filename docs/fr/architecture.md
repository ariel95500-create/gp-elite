# Comment le moteur est organisé

Partie de la documentation de GP_ELITE : retour au [README](../../README.fr.md) ; [English version](../architecture.md).

Jusqu'à la 1.4.0, le moteur de GP_ELITE tenait dans un seul fichier,
`gp_elite/core.py`, de 12 999 lignes. Depuis la 1.5, c'est un ensemble de
modules, chacun avec un rôle. Le découpage a changé l'organisation du code,
pas ce que fait le moteur : à graine égale et travail égal, la 1.5 rend les
modèles que rend la 1.4.0, au bit près, avec la même interface, à la même
vitesse (à 0,3 % près sur 205 ajustements des 41 équations de Feynman du
banc). Le code qui va chercher à l'intérieur de `gp_elite.core` peut voir
quelques changements, listés plus bas. Cette page est pour qui veut lire le
moteur ou le modifier.

## Les modules

Du plus bas au plus haut. Un module n'importe que les modules placés au-dessus
de lui dans ce tableau, jamais un module placé en dessous, et aucun n'importe
`core.py`. Quelques fonctions importent, au moment où elles s'exécutent, des
modules du paquet extérieurs au moteur (`dim_search`, `dimensions` et
`formula`, et `api` pour l'option 7 de la console), qui importent eux-mêmes
`gp_elite.core`. `tests/test_layering.py` vérifie ces règles.

| module | ce qu'il contient | lignes |
|---|---|---|
| `state` | l'état partagé : les noms qui changent pendant un ajustement | 72 |
| `numeric` | les opérateurs protégés, scalaires et vectoriels : les formes sûres des opérations qu'utilisent les formules | 242 |
| `config` | la trace d'un ajustement (`TRACE`), `Config`, les réserves d'opérateurs, les configurations de la console | 621 |
| `tree` | l'arbre d'une formule : `Node`, ses empreintes, son texte et sa forme sympy, sa taille, sa profondeur, sa complexité et ses constantes | 475 |
| `simplification` | la simplification d'un arbre, et ses mémoires cache | 217 |
| `evaluation` | le code NumPy produit à partir d'un arbre, les plans du jacobien, les fonctions compilées et leurs caches, le r de Pearson, le cache des prédictions | 791 |
| `datasets` | les jeux de données de la console : Collatz (Syracuse), les variables leurres, `build_dataset` | 449 |
| `scoring` | la mise à l'échelle linéaire et robuste, les erreurs, l'échelle de la cible, l'usage des variables, `fitness` | 477 |
| `fitting` | l'ajustement des constantes : Levenberg-Marquardt et Adam | 295 |
| `genetic` | les arbres aléatoires, la déduplication, la sélection ε-lexicase et par tournoi, le croisement, les mutations, les rangs de Pareto, les arbres stigmergiques | 899 |
| `memory` | la bibliothèque de fragments, les points sondes et les signatures sémantiques, le co-graphe, la mémoire de séquences, `warm_transfer` | 1 383 |
| `final_choice` | l'arrêt anticipé, la patience, la validation, les finalistes et leur polissage, le domaine proche, la règle d'un écart-type, les petites tables | 1 004 |
| `seeds` | les graines placées avant la première génération : motifs, lois de puissance, formes binomiales, élémentaires et tolérantes au bruit | 1 624 |
| `islands` | `Island`, la migration, une génération d'une île (`evolve_island`), la remise à zéro des îles exploratrices | 778 |
| `parallel` | les îles en parallèle : les processus, leurs réserves, la garde du module principal | 409 |
| `search` | la séparation de la validation, le candidat linéaire, et `evolve`, qui mène un ajustement des graines au choix final | 922 |
| `data` | les mises à l'échelle, le chargement des fichiers CSV et leurs dépendances facultatives, les problèmes de la console | 581 |
| `console` | le résultat affiché, le rapport des leurres, le graphique, `run`, le banc d'essai et le menu interactif | 1 450 |
| `core` | la porte : tous les noms qu'avait `gp_elite.core` dans la 1.4.0 (plus bas) | 856 |

Autour du moteur, les modules que la 1.4.0 avait déjà ne changent pas : `api`
(`symbolic_regression`, le point d'entrée), `sklearn_api` (`GPEliteRegressor`),
`formula` (la formule dans les variables de l'utilisateur), `dimensions` et
`dim_search` (les unités physiques), `stability` et `cli`.

Un ajustement suit ce chemin : `symbolic_regression` prépare les données et
appelle `evolve`, qui place les graines, fait tourner les générations des îles
(en parallèle ou non), puis fait le choix final.

## L'état partagé

61 noms tiennent des données qui peuvent changer une fois le moteur importé :
52 changent pendant un ajustement (les lignes de validation, les mémoires cache,
la perte personnalisée, les réserves d'opérateurs du mode CSV, les mémoires de
la recherche...), et 9 sont des interrupteurs des graines et du choix final que
seuls les tests modifient. Ils vivent dans `gp_elite/state.py`, et chaque
fonction les lit et les modifie là, au moment où elle s'exécute :

```python
from . import state

def f():
    if state._USE_LINEAR_SCALING:     # lu quand f s'exécute
        ...
    state._TIME_LIMIT_HIT = True      # modifié pour tous les modules
```

Jamais `from .state import _USE_LINEAR_SCALING` : cela copierait la valeur au
moment de l'import, et le module continuerait à lire l'ancienne après qu'un
ajustement l'a changée, sans aucune erreur.

## gp_elite.core, la porte

Les scripts, les bancs d'essai et les tests écrits pour la 1.4.0 lisent et
modifient des noms sur `gp_elite.core`. Les tests de la 1.4.0 passent sans
changement, et la porte garde ce dont ils dépendent :
- chaque nom qu'avait `gp_elite.core` dans la 1.4.0 peut encore y être lu ;
- un nom de l'état partagé, lu, modifié ou supprimé sur `gp_elite.core`, est
  lu, modifié ou supprimé dans `gp_elite.state` (chacun est un descripteur de
  données de la classe du module, pour que le `monkeypatch` de pytest remette
  la bonne valeur) ;
- tout autre nom modifié ou supprimé sur `gp_elite.core`, une fonction qu'un
  test remplace ou une enveloppe qu'un banc d'essai pose sur `evolve_island`,
  est aussi modifié ou supprimé dans chaque module du moteur qui tenait le
  même objet quand `gp_elite.core` a été importé, comme dans la 1.4.0, où
  toutes les fonctions partageaient un seul espace de noms ; ainsi un nom
  supprimé puis remis les atteint de nouveau.

`tests/test_door.py` vérifie les 421 noms de la 1.4.0 et chacune de ces règles.

Ce que la porte ne garde pas, pour le code qui va chercher à l'intérieur du
moteur : `vars(gp_elite.core)` ne contient plus les noms de l'état, et une
valeur écrite dans ce dictionnaire n'atteint pas le moteur ; `unittest.mock.patch`
avec `create=True` supprime un nom de l'état quand il se termine ; recharger
`gp_elite.core` ne refait plus le moteur ; `from gp_elite.core import *` ne
donne plus les sept noms publics de l'état ; et les fonctions et les classes
appartiennent désormais à leurs modules (un fichier pickle fait par la 1.5 ne
se charge pas dans la 1.4.0, et `help(gp_elite.core)` n'en liste aucune). Le
CHANGELOG (1.5.0) liste ces changements en entier.

## Pour les contributeurs

- Un nom qui change pendant un ajustement va dans `state.py`, et se lit et se
  modifie sous la forme `state.NOM`.
- Un module n'importe que des modules placés au-dessus de lui dans le tableau ;
  une fonction peut importer, au moment où elle s'exécute, un module du paquet
  extérieur au moteur. `tests/test_layering.py` le vérifie : un nouveau module
  va dans le tableau et dans le test.
- Pour observer une fonction pendant un ajustement, par exemple pour compter
  les générations, posez-la sur `gp_elite.core`, qui la transmet à chaque
  module du moteur qui la tient. La remplacer seulement dans le module où elle
  vit ne suffit pas : `evolve_island` vit dans `islands`, mais `search` et
  `parallel` l'importent par son nom et appellent leur propre référence.
- Le code nouveau importe les noms depuis les modules où ils vivent, pas depuis
  `gp_elite.core`.

Comment le découpage a été fait et vérifié, déplacement par déplacement : voir
`benchmarks/results_1.5/PLAN.md` et `benchmarks/results_1.5/split/`.
