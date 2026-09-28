# GP_ELITE

**Régression symbolique par programmation génétique — pour découvrir des lois interprétables sur vos données expérimentales.**

Déclarez vos unités, et la recherche ne construit jamais que des équations
dimensionnellement valides — une contrainte dure, pas une pénalité douce.
L'enveloppe de fonctionnement est mesurée, pas revendiquée : combien de points
il faut, comment le temps de calcul augmente, et où elle échoue.

*[🇬🇧 English version](README.md)*

[![Ouvrir dans Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ariel95500-create/gp-elite/blob/main/examples/quickstart.fr.ipynb) **Essayez dans votre navigateur** — rien à installer, quatre étapes, dix minutes.

GP_ELITE cherche une **formule mathématique** qui relie vos variables à une cible, au lieu d'une boîte noire. Pensé pour les petits jeux de données expérimentaux (≤10 variables) où l'on veut *comprendre* la relation : lois de dégradation, calibration de capteurs, corrélations d'ingénierie, courbes dose-réponse, lois physiques.

Sur cinq équations de Feynman (sans normalisation), le modèle rendu retrouve la loi exacte de quatre d'entre elles à chaque taille de 25 à 10 000 points, à chaque run ; la cinquième, la forme rationnelle imbriquée I.16.6, est manquée à toutes les tailles. Le temps de calcul médian double à peu près de 1 000 à 10 000 points (`benchmarks/feynman_scaling.py`, version 0.7.0).

Depuis la **0.4 « Lawful »**, vous pouvez aussi déclarer les unités physiques de vos colonnes — la recherche elle-même ne construit alors que des expressions dimensionnellement saines, au lieu de formules qui collent aux chiffres tout en violant la physique (voir *Contraintes dimensionnelles* plus bas).

Pur **Python / NumPy** — pas de Julia, pas de compilation, pas de GPU. `pip install` et c'est parti.

![GP_ELITE redécouvre la 3ᵉ loi de Kepler à partir de 8 points (R² = 1.000000)](kepler_plot.png)

> À partir des seules distances et périodes orbitales des 8 planètes, GP_ELITE a redécouvert la 3ᵉ loi de Kepler, `T = a·√a = a^1.5` — voir [`examples/kepler_demo.py`](examples/kepler_demo.py).

```python
import numpy as np
from gp_elite import symbolic_regression

a = np.array([0.387, 0.723, 1.000, 1.524, 5.203, 9.537, 19.191, 30.069])   # UA
T = np.array([0.241, 0.615, 1.000, 1.881, 11.862, 29.457, 84.011, 164.79])  # années

resultat = symbolic_regression(a.reshape(-1, 1), T, feature_names=["a"], generations=40, seed=0)
print(resultat.expression)   # 0.00279171 + 0.999396 * a * sqrt(a)
```

La formule est écrite dans *vos* variables et *vos* unités : en unités astronomiques et
en années, la constante de Kepler vaut 1, et c'est ce qui revient.

---

## Est-ce pour vous ?

GP_ELITE est probablement fait pour vous si **au moins une** de ces phrases vous
correspond :

- **Vous avez un tableau de mesures et vous voulez la formule, pas une
  prédiction.** Une courbe de dégradation, une calibration de capteur, une
  corrélation d'ingénierie. C'est la *forme* de la relation qui vous intéresse,
  et vous comptez la lire, la vérifier, peut-être la publier.
- **Vous ne pouvez pas installer un second environnement d'exécution.** Machine
  universitaire verrouillée, poste d'entreprise sans droits administrateur,
  conteneur d'intégration continue que vous ne maîtrisez pas. `pip install
  gp-elite` et ses trois dépendances suffisent — pas de compilateur, pas de
  Julia, pas de GPU.
- **Vous connaissez les unités physiques de vos colonnes.** Déclarez-les et la
  recherche ne construira que des formules dimensionnellement saines — et pourra
  vous donner les unités *et la valeur* d'une constante physique qui ne figure
  même pas dans vos données.
- **Vous enseignez ou apprenez la programmation génétique.** Le moteur est du
  Python que vous pouvez lire, exécuter pas à pas et modifier, avec une interface
  console qui ne demande aucun code.

Si rien de tout cela ne vous correspond, d'autres outils vous serviront mieux :
`PySR` et `Operon` sont plus rapides et plus précis à grande échelle — voir
*Est-ce solide ?* plus bas.

---

## Installation

```bash
pip install gp-elite          # depuis PyPI
# ou, depuis les sources :
git clone https://github.com/ariel95500-create/gp-elite
cd gp-elite && pip install -e ".[test]"
```

Dépendances : `numpy`, `pandas`, `scikit-learn`. Python 3.9 à 3.14, testé sous Linux et Windows.

---

## Utilisation

### En une ligne, sur vos données (interface console)

```bash
gp-elite
```

Choisissez le mode **6 (CSV générique)**, indiquez votre fichier, et laissez les valeurs par défaut. GP_ELITE détecte les colonnes, sépare un jeu de validation, évolue, et affiche la loi trouvée — écrite avec les noms de vos colonnes et dans vos unités, vérifiée contre ses propres prédictions sur vos données.

Le mode 6 demande aussi les **unités physiques** de vos colonnes.
Les déclarer est facultatif — passer prend une touche — mais si vous le faites,
la recherche se restreint aux formules dimensionnellement cohérentes, et le
moteur peut déduire les unités et la valeur d'une constante physique manquante.
Sur un CSV à deux colonnes de la loi de Hooke :

```
  Units for ['elongation'], comma-separated : m
  Unit for TARGET 'force' : N
  Deduce an unknown constant? [y/N] : y
  ...
  Formula in YOUR columns (checked on your data):
    force = 250 * elongation
  Deduced constant units : [kg / s^2]
  Deduced constant value : 250
```

### Par programmation (notebooks, pipelines)

```python
import numpy as np
from gp_elite import symbolic_regression

rng = np.random.RandomState(0)
X = rng.uniform(1, 5, (200, 2))
y = 2.0 + 3.0 * np.sqrt(X[:, 0]) - 0.5 * X[:, 1]

if __name__ == "__main__":        # nécessaire dans un script, voir la note plus bas
    resultat = symbolic_regression(
        X, y,
        feature_names=["a", "b"],
        operators="physical",     # 'physical' | 'trig' | 'full' | 'poly' | 'conserve'
        generations=60,
        speed="fast",             # 'ultrafast' | 'fast' | 'normal' | 'thorough'
        seed=0,
    )
    print(resultat.expression)      # 8.27088 + 2.49792 * (0.201558 * a - 0.200185 * b - exp(-0.591087 * a) - exp(-0.034099 * a)) + 0.0319226 * a
    print(resultat.r2_validation)   # 0.999998
    print(resultat.size)            # 25
    print(resultat.sympy())         # la même formule, lisible par sympy
```

À ce budget, la recherche rend une approximation, pas la loi qu'on lui a donnée : le
terme en `b` est juste (2.49792 × −0.200185 ≈ −0.500·b), tandis que `3·√a` est approché
par une combinaison de `a` et de deux exponentielles — une formule qui colle au hold-out
à R² 0.999998 et qui n'est pourtant pas la loi. C'est en lisant la formule qu'on s'en
aperçoit ; `restarts=` et `speed="thorough"` consacrent plus de calcul à la forme
exacte, sans garantie.

- `speed` : `'ultrafast' | 'fast' (défaut) | 'normal' | 'thorough'`. `'thorough'`
  (population 400, quatre îles, 200 générations) est le régime pour chercher une
  loi exacte ; avec deux fois plus de générations que par défaut, il est plus
  lent, et ne garantit pas de faire mieux.
- `time_limit=` (secondes) : la recherche s'arrête proprement à l'échéance et rend
  le meilleur modèle trouvé, au lieu d'être interrompue sans résultat ; la
  sélection finale qui suit ajoute un peu (environ deux secondes pour un budget
  de 15 s dans notre mesure).
- `restarts=` : évolutions indépendantes dont les candidats sont fusionnés avant le
  choix final.

**Scripts et îles parallèles.** Sur une machine à quatre cœurs ou plus, les îles
tournent dans des processus parallèles. Ces processus sont démarrés en mode
`spawn` sur tous les systèmes (Linux compris) et ré-importent votre script :
gardez le code de premier niveau sous
`if __name__ == "__main__":`, comme ci-dessus. Sans cette garde, GP_ELITE détecte
la situation, termine sur un cœur avec le même résultat, et le signale une fois.
Rien à faire dans un notebook.

### Lire le résultat

- **`expression` est écrite dans vos variables.** Le moteur cherche sur des
  colonnes remises à l'échelle en interne ; la formule rendue replie cette mise à
  l'échelle dans ses constantes, et l'ajustement vérifie qu'elle reproduit
  `predict()` sur vos données (`resultat.formula_exact`). `resultat.sympy()` donne
  la même formule sous forme de chaîne lisible par `sympy.sympify`. (Avant la 0.7,
  les constantes affichées étaient celles de l'espace normalisé interne.) La
  formule est la fonction mathématique pure : là où l'un des garde-fous
  numériques du moteur agit sur vos données (une puissance bornée parce que sa
  base dépasse 100 ou son exposant 6 en valeur absolue, ou sa valeur un million ;
  une division par un dénominateur à moins de 1e-8 de zéro), ou, rarement, là où
  l'arrondi ruine une expression mal conditionnée, elle s'écarte de `predict()` sur
  ces lignes, `formula_exact` vaut False et l'ajustement le signale. C'était le cas
  pour 6 des 70 ajustements faits avec la normalisation par défaut dans
  `benchmarks/norm_signed.py`.
- **`r2_validation` est un score de sélection.** Le hold-out sur lequel il est
  calculé sert aussi à choisir le modèle rendu parmi les candidats : il est donc
  optimiste. Pour estimer comment la formule généralise, gardez vos propres
  données de test hors de l'ajustement.
- **`resultat.pareto`** liste les autres candidats non dominés, du plus simple au
  plus complexe, chacun avec son `expression`, son `r2_validation` et son `predict`.

---

## 🛡️ Régression robuste (loss résistante aux valeurs aberrantes)

Les données réelles sont sales. Quelques points aberrants suffisent à faire dévier un ajustement aux moindres carrés loin de la vraie relation. GP_ELITE propose un **mode robuste** activable par un seul paramètre, conçu pour suivre la masse des données plutôt que quelques points extrêmes.

```python
resultat = symbolic_regression(X, y, feature_names=["x"], robust=True)
```

En interne, `robust=True` bascule l'objectif vers une **loss de Huber** et recale les coefficients finaux par **IRLS (moindres carrés repondérés itérativement)**. Le résultat reste une formule compacte et lisible.

**Comportement mesuré** (récupération de `y = 2x + 1` ; RMSE contre la *vraie* loi sur les points propres, plus bas = meilleur ; cinq seeds, médiane et pire seed) :

| valeurs aberrantes | défaut (MSE) | `robust=True` |
|-------------------:|-------------:|--------------:|
|                0 % | 0.063 [0.063] | 0.063 [0.063] |
|               10 % | 1.398 [1.398] | **0.237** [0.237] |
|               20 % | 1.925 [1.925] | 1.925 [1.925] |

Sur données propres, les deux modes rendent des droites légèrement différentes, aussi
proches l'une que l'autre de la vraie loi. Avec 10 % de valeurs aberrantes, le mode
robuste divise l'erreur par six. Avec 20 %, sur cet exemple, il ne fait pas mieux que le
défaut : dans les deux modes, les cinq seeds rendent la même droite, tirée par les
valeurs aberrantes (`y = 4.23319 + 1.32825 * x`). La robustesse est un outil à essayer
quand on soupçonne des valeurs aberrantes, pas une garantie — comparez les deux modes
sur vos propres données.
(Jusqu'en 0.6, ce tableau montrait le meilleur de trois runs, choisi en comparant avec
la vraie loi, ce qu'aucun utilisateur ne peut faire.)

Reproduire : `python examples/robust_regression.py`.

---

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
| dimensionnellement valides | **0 / 5** | **5 / 5** | 0 / 5 |
| loi exacte retrouvée (tient hors domaine) | 0 / 5 | **2 / 5** | 0 / 5 |
| R² test médian | 0.98661 | **0.99957** | 0.99333 |
| R² hors domaine médian | 0.10 | **0.65** | 0.45 |
| taille médiane du modèle | 41 nœuds | **17 nœuds** | 53 nœuds |
| secondes / run (médiane) | 22 | 57 | 104 |

La troisième colonne donne au bras non contraint quatre fois plus de générations —
ici plus de temps machine que le bras contraint (104 s contre 57 s). Il reste à
**0/5** modèles physiquement valides : le calcul ne remplace pas la contrainte. Les
échecs sans contrainte ne sont pas marginaux : sur les dix runs non contraints, les
modèles additionnent des hertz à des kilogrammes, à des nombres purs ou à des
coulombs, un champ électrique à des coulombs, ou prennent la tangente hyperbolique
d'une charge ou d'une fréquence.

**Ce que ça ne fait *pas*.** Sur un jeu de test tiré *hors* du domaine
d'entraînement (w/w0 poussé de [0.20, 0.67] vers la résonance, [0.70, 0.90]), les
approximations s'effondrent dans tous les bras. Deux runs contraints sur cinq ont
trouvé la loi exacte, qui y tient (R² = 1.00000) ; les trois autres sont des
approximations physiquement cohérentes et compactes, pas la loi. Temps mesurés sur un conteneur
Linux à 2 cœurs, un run par cœur. Reproductible avec `benchmarks/ab_ood.py`.

**Quand s'en servir.** Pour découvrir une loi physique quand vous connaissez les
unités et que la loi est dimensionnellement homogène, et pour garantir que ce que
le moteur rend a au moins un sens physique. **Pas** pour de la prédiction en boîte
noire : la contrainte écarte les approximations dimensionnellement fausses mais
numériquement bonnes, et peut donc faire *baisser* le R² lorsque l'objectif est
d'ajuster plutôt que de trouver une loi.

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
| gaz parfaits `P = nRT/V` | oui | `kg m² / K mol s²` | 8,31446 | 8,314463 |

La formule rendue porte elle-même la constante physique : `250 * x`,
`8.31446 * n * T / V`. Budget : 25 générations, deux redémarrages.

Reproductible avec `benchmarks/test_constante_mystere.py`. Exige `units=` et
`target_units=`. Si l'expression n'est pas un monôme des colonnes d'entrée
(`m₁ + m₂` par exemple), aucune constante brute unique n'existe :
`constant_value_` vaut alors `None`, les unités déduites restant valides.

**Limite.** Sous `units=`, la mise à l'échelle interne est purement
multiplicative (sans décalage additif), ce qui maintient chaque candidat
dimensionnellement homogène.

---

## Exemple sur des données de vieillissement de batterie simulées

```bash
python examples/battery_soh.py
```

Le fichier [`examples/nasa_battery_simulation.csv`](examples/nasa_battery_simulation.csv)
contient 168 cycles de charge **simulés** (numéro de cycle, température, courant,
état de santé de la capacité). Son origine n'est pas documentée au-delà de son nom :
considérez-le comme une démonstration de la démarche, pas comme un résultat sur de
vraies batteries. Le script y affiche (extrait) :

```
PROTOCOL 1 — random split (INTERPOLATION, leaks info)
  GP_ELITE      R² = +0.991
  RandomForest  R² = +0.997
  XGBoost       R² = +0.997

PROTOCOL 2 — forward split (EXTRAPOLATION): train on cycles 1..142, predict 143..168
  RandomForest (300)      R² = -2.515
  XGBoost (300 trees)     R² = -2.324
  GP_ELITE (one equation) R² = +0.594

  Equation: SOH = 0.563502 - 0.0192492 * sqrt(cycle) + 0.118299 * courant + 0.0162273 * (courant²)²
```

Un découpage aléatoire de données séquentielles est de l'interpolation, qui flatte
toutes les méthodes. Sur le découpage chronologique, les forêts d'arbres ne peuvent
que répéter des valeurs vues à l'entraînement et passent sous la moyenne ; l'équation
continue de suivre la tendance. C'est l'argument pour une formule sur des données
physiques — sur ce jeu simulé, à confirmer sur les vôtres.

---

## Est-ce solide ?

Question légitime pour un projet dont vous n'avez jamais entendu parler. Voici
ce que ça vaut face aux alternatives, et ce que ça ne vaut pas.

| | GP_ELITE | Réseaux de neurones | PySR (état de l'art) |
|---|---|---|---|
| Sortie | **formule lisible** | boîte noire | formule lisible |
| Installation | `pip install` (pur Python) | lourde | nécessite **Julia** |
| Validation hors échantillon | **intégrée** (sert à choisir le modèle) | à faire soi-même | à faire soi-même |
| Unités physiques | **contrainte dure pendant la recherche** (`units=`) | non | pénalité douce (`X_units=`) |
| Stabilité de la réponse | **rapport bootstrap** (`stability_analysis`) | non | non |
| Vitesse et précision à grande échelle | moindres | — | **supérieures** |

La niche de GP_ELITE : **zéro barrière d'entrée**. Un ingénieur de labo, un étudiant ou un technicien pointe un fichier CSV et reçoit une loi validée, sans devenir développeur. `PySR` et `Operon` sont plus rapides et plus précis sur les problèmes grands ou difficiles ; GP_ELITE ne prétend pas le contraire.

---

## Sur quoi GP_ELITE est-il bon (et moins bon) ?

**Bon** : lois physiques / d'ingénierie à structure multiplicative ou exponentielle, données expérimentales de taille modeste, problèmes où l'interprétabilité prime.

Sur le **banc Feynman gelé** (15 équations de physique, `PYTHONHASHSEED=0`,
`restarts=4`, une seed), jugé sur le modèle qu'il rend : **12/15 récupérations
symboliques exactes** (1−R² < 1e-9 sur des données tenues à l'écart) et **13/15 sous
1e-3** ; les échecs sont I.16.6 (addition relativiste des vitesses, une forme
rationnelle imbriquée) et III.15.12 (2U·(1 − cos kd), le cosinus d'un produit).
Face-à-face contre **gplearn** sur les mêmes données et découpages (population
2000 × 30 générations), chaque méthode jugée sur le modèle qu'elle rend : **12/15 contre
6/15** exactes, 13/15 contre 7/15 sous 1e-3 — GP_ELITE devant sur 7 équations, à
égalité sur 8, derrière sur aucune. Avec les
unités physiques déclarées (`units=`, même budget, sans normalisation), 14/15 reviennent
exactes, chacune sous sa forme de manuel (`benchmarks/feynman_units.py`). Une seed sur
quinze équations est une vitrine, pas une comparaison statistique. Reproduire :
`PYTHONHASHSEED=0 python benchmarks/feynman_bench.py 0 15` et
`PYTHONHASHSEED=0 python benchmarks/duel.py`.

**Moins bon** : suites chaotiques (ex. temps de vol de Collatz — composante intrinsèquement aléatoire), >15-20 variables (l'espace de recherche explose — même si `units=` le réduit nettement quand les unités physiques sont connues), gros jeux de données où la précision pure prime sur l'interprétabilité (les modèles d'ensemble dominent alors).

---

## Caractéristiques techniques

- **Formule dans vos variables, vérifiée** (v0.7) : la mise à l'échelle interne est repliée dans les constantes ; `formula_exact` indique si la formule reproduit `predict()` sur les données d'entraînement
- **Budget de temps** (v0.7) : `time_limit=` arrête proprement et rend le meilleur modèle trouvé
- **Déduction de la constante mystère** (v0.5) : la constante de tête peut porter une dimension, inférée par homogénéité ; unités et valeur brute exposées sur l'estimateur
- **Recherche sous contrainte dimensionnelle** (v0.4) : génération typée constructive, mutation et croisement préservant les dimensions, filtre de validité dans `fitness()` — une seule sémantique partagée avec l'auditeur (v0.7)
- **Mise à l'échelle purement multiplicative sous `units=`** (v0.4.1) : régression par l'origine, pour que la forme *notée* soit la forme *livrée*
- **Garde numérique de l'optimiseur LM** (v0.4) : plus d'overflow float64 sur les chaînes `sq`/`cube`/`*` non bornées
- **Audit dimensionnel post-hoc** (v0.3) : `dimensions.py`
- **Optimisation des constantes par Levenberg–Marquardt** (v0.2) : déterministe, LM/Adam commutables
- **Multi-restart + fusion des archives de candidats** (v0.2) : la variance de seed transformée en fiabilité
- **API front de Pareto** (v0.2) : escalier non dominé complexité/précision
- **Mode extrapolation / prévision protégé** (v0.2) : sondes hors-domaine, plancher linéaire, sélection-frontière
- **Amorçage par motifs de composition** (v0.2) : gabarits pythagoricien, somme d'inverses, gaussienne pour les structures imbriquées
- **Modèle en îles asymétriques** (explorer / cleaner / stigmergic) avec migration périodique, dans des processus parallèles sur les machines à quatre cœurs ou plus
- **Linear scaling** (Keijzer 2003) : le moteur cherche la *forme*, échelle et décalage sont résolus en forme fermée
- **Sélection ε-lexicase** (La Cava 2016) pour préserver la diversité comportementale
- **Validation hold-out** + sélection parcimonieuse du champion (tolérance R²)
- **Normalisation sans décalage** préservant la structure multiplicative (x·y reste un produit propre), pour toutes les données depuis la 0.7
- **Mémoire stigmergique** exportable entre exécutions (export/import de grammaires) — une fonctionnalité documentée, pas un avantage de performance mesuré

---

## Nouveautés

**0.7 « Sound »** — la formule que vous obtenez est le modèle obtenu : écrite dans
vos variables pour toute normalisation et vérifiée à l'ajustement ; un budget
`time_limit=` ; des garanties dimensionnelles rendues strictes ; chaque chiffre de
ce README re-mesuré sur la version publiée. **0.6 « Bench »** — les unités
physiques dans la console. **0.5 « Unknown »** — unités *et* valeur de la
constante manquante d'une loi. **0.4 « Lawful »** — recherche sous contrainte
dimensionnelle. **0.3 « Trust »** — diagnostics et stabilité.

Historique complet, avec les mesures qui étayent chaque affirmation, dans
[CHANGELOG.md](CHANGELOG.md). Chaque banc derrière un chiffre de ce README se
trouve dans [`benchmarks/`](benchmarks/), avec ses résultats bruts.

## Ça n'a pas marché sur vos données ? Dites-le

GP_ELITE est réglé sur des benchmarks publiés — Feynman, Strogatz — qui sont
propres, sans bruit et bien échelonnés. Les mesures réelles ne sont rien de tout
cela, et c'est précisément là que le moteur a le plus besoin de progresser.

Donc s'il vous rend n'importe quoi sur vos données, c'est une **information
utile, pas une erreur de votre part**.
[Ouvrez une issue](https://github.com/ariel95500-create/gp-elite/issues/new/choose)
avec la forme de vos données et ce que vous avez obtenu. Pas besoin de partager
les données elles-mêmes, pas besoin de savoir pourquoi ça a échoué, et vous
pouvez écrire en français comme en anglais.

Les rapports d'échec sur mesures réelles sont la contribution la plus précieuse
que ce projet puisse recevoir. Voir [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Tests

```bash
pip install -e ".[test]"
PYTHONHASHSEED=0 python -m pytest tests/ -q          # Linux / macOS
set "PYTHONHASHSEED=0" && python -m pytest tests/ -q   # Windows
```

`tests/test_guarantees.py` fige chaque défaut trouvé jusqu'ici — chaque test a été
vérifié en échec sur le code qui portait le défaut. La suite tourne à chaque envoi
sur GitHub (Linux, Python 3.9 à 3.14, et Windows).

---

## Licence

MIT — voir [LICENSE](LICENSE). Utilisation libre, y compris commerciale, avec conservation de la notice de copyright.

## Citer GP_ELITE

Si GP_ELITE vous est utile dans un travail académique, voir [CITATION.cff](CITATION.cff).
