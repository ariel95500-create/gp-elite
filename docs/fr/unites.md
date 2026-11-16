# Unités physiques

Partie de la documentation de GP_ELITE : retour au [README](../../README.fr.md) ; [English version](../units.md).

## ⚖️ Contraintes dimensionnelles (pour les lois physiques)

Déclarez les unités de vos entrées et de votre cible : GP_ELITE ne cherchera plus
que des expressions dimensionnellement saines — fini les formules qui collent aux
chiffres tout en étant physiquement dénuées de sens.

```python
from gp_elite import GPEliteRegressor

est = GPEliteRegressor(
    units=["kg", "m/s"],      # unités de X0, X1
    target_units="J",         # unité de la cible
)
est.fit(X, y)
```

Les unités s'écrivent en texte simple — bases SI (`m kg s A K mol cd`), unités
dérivées courantes (`N J W Pa Hz C V ohm T`), et les opérateurs `* / ^ ( )` :
`"m/s"`, `"kg*m/s^2"`, `"s^-1"`, `"1"` pour une grandeur sans dimension. Les
dictionnaires de dimensions (`{"m": 1, "s": -1}`) fonctionnent aussi, de même que
les formes par nom (`{"X0": "kg"}`) et par indice (`{0: "kg"}`). Une chaîne mal
formée (`"m/(s"`, `"kg^"`, `"m garbage"`) lève une erreur au lieu d'être devinée.

**Effet mesuré** — Feynman II.11.3, `x = q·Ef/(m·(w0²−w²))`, 5 variables,
5 seeds, 40 générations, budget identique pour les deux premiers bras :

| | sans `units=` | `units=` | sans `units=`, 4× générations |
|---|---:|---:|---:|
| dimensionnellement valides | 5 / 5 | 5 / 5 | 5 / 5 |
| loi exacte retrouvée (tient hors domaine) | 5 / 5 | 5 / 5 | 5 / 5 |
| R² test médian | 1.00000 | 1.00000 | 1.00000 |
| R² hors domaine médian | 1.00000 | 1.00000 | 1.00000 |
| taille médiane du modèle | 20 nœuds | 20 nœuds | 20 nœuds |
| secondes / run (médiane) | 0 | 1 | 0 |

Depuis la 1.0, cette loi fait partie des formes que le moteur ajuste directement,
un monôme multiplié par une puissance d'un binôme, et la forme ajustée est placée
dans la population de départ. Depuis la 1.1, c'est vrai aussi avec `units=`, où
une forme ajustée n'est placée que si elle passe la porte des dimensions que tout
arbre typé doit passer : les deux recherches rendent la loi à chaque run, en une
seconde environ. Avec la 1.0, dont les formes ajustées n'agissaient pas avec
`units=`, la recherche contrainte la trouvait dans deux runs sur cinq et finissait
les trois autres sur des approximations (médiane de ses cinq runs : 27 nœuds,
27 s). Jusqu'à la 0.9, la recherche libre ne rendait aucun modèle
valide sur cette loi, même avec quatre fois plus de générations : ses modèles
prenaient le logarithme d'une fréquence, additionnaient des kilogrammes ou des
hertz à des nombres purs, ou élevaient une grandeur à un exposant en coulombs, et
la contrainte était le seul chemin vers une réponse valide. Elle le reste pour les
lois que le moteur n'ajuste pas directement. (Depuis la 0.9, une génération typée
coûte 1,4 fois une génération non typée, contre 8,5 fois avec la 0.8. Avec un
budget fixé, comme ici, une recherche ne s'arrête plus tôt que sur une loi
exacte, si bien que les runs qui finissent sur une approximation, et chaque run
sur des données bruitées, parcourent toutes leurs générations ; `time_limit=` les
borne, et avec les réglages par défaut, depuis la 1.2, `patience=` aussi.)

**Ce que ça ne fait *pas*.** Sur un jeu de test tiré *hors* du domaine
d'entraînement (w/w0 poussé de [0.20, 0.67] vers la résonance, [0.70, 0.90]), la
loi exacte tient (R² = 1.00000) et les approximations se dégradent : les trois runs
contraints de la 1.0 qui finissaient sur l'une d'elles avaient un R² hors domaine
de 0,32 à 0,65. Temps mesurés sur une
machine Linux à 4 cœurs, deux runs à la fois, avec les îles en séquence
(`parallel=False`). Reproductible avec `benchmarks/ab_ood.py`.

**Quand s'en servir.** Pour garantir que ce que le moteur rend a un sens physique,
et pour déduire les unités et la valeur d'une constante (ci-dessous, et
[l'étude de cas de Kepler](https://github.com/ariel95500-create/gp-elite/blob/main/examples/case_studies/kepler_units.fr.ipynb),
où les unités écartent aussi un terme que les données seules ajouteraient).
Depuis la 1.1, les formes que le moteur ajuste directement agissent aussi avec
`units=` : sur les 41 équations de Feynman du banc de décision avec leurs unités,
cinq seeds à 30 s par ajustement, 165 lois exactes sur 205 contre 108 avec la 1.0,
et 163 sans unités. Avec l'arc sinus de la 1.3, 174 et 171, contre 166 et 163
pour la 1.2 mesurée à côté ; la 1.4 les garde, 174 et 171 dans sa mesure de sortie. **Pas** pour de la
prédiction en
boîte noire : la contrainte écarte les approximations dimensionnellement fausses
mais numériquement bonnes, et peut donc faire *baisser* le R² lorsque l'objectif
est d'ajuster plutôt que de trouver une loi.

**Lois à constante dimensionnée** (`unknown_constant=`). Par défaut les
constantes ajustées sont sans dimension — convention AI Feynman — ce qui met une
loi comme celle de Hooke, `F = k·x`, hors d'atteinte : aucune constante sans
dimension ne peut relier des mètres à des newtons, et la recherche signale à
juste titre qu'aucune expression valide n'est constructible. Avec
`unknown_constant=True`, la constante de tête est autorisée à *porter* une
dimension, déduite par homogénéité :

```python
est = GPEliteRegressor(units=["m"], target_units="N", unknown_constant=True)
est.fit(X, y)
est.constant_units_string()   # '[kg / s^2]'
est.constant_value_           # 250.0
```

Le moteur ne rend alors plus seulement la forme de la loi, mais **les unités et
la valeur de la constante physique manquante**. Mesuré sur trois lois de
référence :

| loi | structure retrouvée | unités déduites | valeur | réelle |
|---|---|---|---|---|
| Hooke `F = k·x` | oui | `kg / s²` | 250 | 250 |
| Newton `F = G·m₁·m₂/r²` | oui | `m³ / kg s²` | 6,674e-11 | 6,674e-11 |
| gaz parfaits `P = nRT/V` | oui | `kg m² / K mol s²` | 8,314462618 | 8,314462618 |

La formule rendue porte elle-même la constante physique : le banc imprime
`(249.99999999999997*X0)` pour Hooke et `(8.314462617999999*((X0*X1)/X2))` pour
les gaz parfaits. Budget : 25 générations, deux redémarrages.

Reproductible avec `benchmarks/test_constante_mystere.py`. Exige `units=` et
`target_units=`. Si l'expression n'est pas un monôme des colonnes d'entrée
(`m₁ + m₂` par exemple), aucune constante brute unique n'existe :
`constant_value_` vaut alors `None`, les unités déduites restant valides.

**Limite.** Sous `units=`, la mise à l'échelle interne est purement
multiplicative (sans décalage additif), ce qui maintient chaque candidat
dimensionnellement homogène.
