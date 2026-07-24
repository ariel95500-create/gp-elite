# GP_ELITE

**Régression symbolique par programmation génétique — pour découvrir des lois interprétables sur vos données expérimentales.**

*[🇬🇧 English version](README.md)*


GP_ELITE cherche une **formule mathématique** qui relie vos variables à une cible, au lieu d'une boîte noire. Pensé pour les petits jeux de données expérimentaux (≤10 variables, 100-5000 points) où l'on veut *comprendre* la relation : lois de dégradation, calibration de capteurs, corrélations d'ingénierie, courbes dose-réponse, lois physiques.

Depuis la **0.4 « Lawful »**, vous pouvez aussi déclarer les unités physiques de vos colonnes — la recherche elle-même ne construit alors que des expressions dimensionnellement saines, au lieu de formules qui collent aux chiffres tout en violant la physique (voir *Contraintes dimensionnelles* plus bas).

Pur **Python / NumPy** — pas de Julia, pas de compilation, pas de GPU. `pip install` et c'est parti.

![GP_ELITE redécouvre la 3ᵉ loi de Kepler à partir de 8 points (R² = 1.000000)](kepler_plot.png)

> À partir des seules distances et périodes orbitales des 8 planètes, GP_ELITE a redécouvert la 3ᵉ loi de Kepler (`T = a·√a = a^1.5`) en quelques secondes — voir [`examples/kepler_demo.py`](examples/kepler_demo.py).

```python
from gp_elite import symbolic_regression

result = symbolic_regression(X, y, feature_names=["cycle", "temperature", "courant"])
print(result.expression)        # capacity_SOH = 0.913 - 0.352·tanh(...)
print(result.r2_validation)     # 0.996  (sur des données jamais vues)
```

---

## Nouveautés 0.4.1 « Lawful »

- **Recherche sous contrainte dimensionnelle** (`units=`) : déclarez les unités
  physiques de vos colonnes, et le moteur ne construit plus que des expressions
  dimensionnellement saines — génération typée constructive, mutation et
  croisement préservant les dimensions, plus un filtre de validité qui rejette
  les candidats non conformes sur tous les chemins de code. Sur Feynman II.11.3
  (5 variables, 5 seeds, budget identique) : sans contrainte, **0/5** modèles
  sont dimensionnellement valides ; avec `units=`, **5/5 le sont**, et ils sont
  **2,6× plus compacts** pour un R² légèrement meilleur. Coût : environ 4× plus
  lent. Tableau complet plus bas.
- **La 0.4.1 corrige trois bugs** découverts en validant la 0.4.0 : sous
  `units=`, les candidats étaient notés sur une forme remise à l'échelle mais
  livrés sans elle (structure juste, constante fausse) ; l'état dimensionnel
  fuyait vers les fits suivants du même processus ; et l'optimiseur
  Levenberg–Marquardt pouvait dépasser float64 sur des chaînes `sq`/`cube`/`*`
  non bornées. Voir [CHANGELOG.md](CHANGELOG.md).
- Sans `units=`, le comportement est **inchangé** (non-régression vérifiée :
  8 fits sur deux jeux d'opérateurs et quatre seeds, plus les modes robuste et
  multi-restart, identiques octet pour octet à la 0.4.0).

Versions précédentes : **0.3.0 « Trust »** (diagnostics, stabilité, audit
dimensionnel post-hoc), **0.2.0** (constantes par Levenberg–Marquardt,
multi-restart, front de Pareto, mode extrapolation).

---

## Pourquoi GP_ELITE ?

| | GP_ELITE | Réseaux de neurones | PySR (état de l'art) |
|---|---|---|---|
| Sortie | **formule lisible** | boîte noire | formule lisible |
| Installation | `pip install` (pur Python) | lourde | nécessite **Julia** |
| Validation anti-surapprentissage | **intégrée** (hold-out) | à faire soi-même | à faire soi-même |
| Validité physique | **imposée pendant la recherche** (`units=`) | non | non |
| Sélection de variables | **rapport d'importance** | non | partielle |

La niche de GP_ELITE : **zéro barrière d'entrée**. Un ingénieur de labo, un étudiant ou un technicien pointe un fichier CSV et reçoit une loi validée, sans devenir développeur.

---

## Installation

```bash
pip install gp-elite          # depuis PyPI
# ou, depuis les sources :
git clone https://github.com/ariel95500-create/gp-elite
cd gp-elite && pip install -e .
```

Dépendances : `numpy`, `pandas`, `scikit-learn`.

---

## Utilisation

### En une ligne, sur vos données (interface graphique en console)

```bash
gp-elite
```

Choisissez le mode **6 (CSV générique)**, indiquez votre fichier, et laissez les valeurs par défaut. GP_ELITE détecte les colonnes, sépare un jeu de validation, évolue, et affiche la loi trouvée avec son rapport de généralisation.

### Par programmation (notebooks, pipelines)

```python
import numpy as np
from gp_elite import symbolic_regression

X = np.random.uniform(1, 5, (200, 2))
y = 2.0 + 3.0 * np.sqrt(X[:, 0]) - 0.5 * X[:, 1]

result = symbolic_regression(
    X, y,
    feature_names=["a", "b"],
    operators="physical",   # 'physical' | 'trig' | 'full' | 'poly'
    generations=60,
    speed="fast",           # 'ultrafast' | 'fast' | 'normal'
)

print(result.expression)        # ex : 2.0 + 3.0·sqrt(a) - 0.5·b
print(result.r2_validation)     # qualité sur le hold-out
print(result.size)              # nombre de nœuds (lisibilité)
```

---

## 🛡️ Régression robuste (loss personnalisée résistante aux outliers)

Les données réelles sont bruitées. Quelques points aberrants suffisent à faire dévier un ajustement aux moindres carrés loin de la vraie relation. GP_ELITE propose un **mode robuste** activable par un seul paramètre, qui retrouve la *vraie* loi même quand une fraction notable des données est corrompue.

```python
from gp_elite import symbolic_regression

# X, y : vos données (potentiellement bruitées)
result = symbolic_regression(X, y, feature_names=["x"], robust=True)
print(result.expression)
```

En interne, `robust=True` bascule l'objectif vers une **loss de Huber** et recale les coefficients finaux par **IRLS (moindres carrés repondérés itérativement)** : l'ajustement est piloté par la masse des données, pas par quelques points extrêmes. Le résultat reste une formule compacte et lisible.

**Comportement mesuré** (récupération de `y = 2x + 1` — RMSE contre la *vraie* loi sur les points propres, plus bas = meilleur) :

| outliers | MSE (défaut) | `robust=True` |
|---------:|-------------:|--------------:|
|      0 % |        0.063 |         0.063 |
|     10 % |        1.398 |         1.374 |
|     20 % |        1.925 |     **0.543** |

Sur données propres, le MSE ordinaire gagne d'un cheveu — **la robustesse n'est pas gratuite**. Avec 10–20 % d'outliers, le mode robuste retrouve la vraie loi là où le MSE déraille. Utilisez `robust=True` quand vous soupçonnez des valeurs aberrantes dans vos données.

Voir [`examples/robust_regression.py`](examples/robust_regression.py) pour le benchmark complet et reproductible.

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
les formes par nom (`{"X0": "kg"}`) et par indice (`{0: "kg"}`).

**Effet mesuré** — Feynman II.11.3, `x = q·Ef/(m·(w0²−w²))`, 5 variables,
5 seeds, 40 générations, budget identique par bras :

| | sans `units=` | `units=` | sans `units=`, 4× générations |
|---|---:|---:|---:|
| dimensionnellement valides | **0 / 5** | **5 / 5** | 0 / 5 |
| R² test médian | 0.99037 | **0.99786** | 0.99494 |
| taille médiane du modèle | 58 nœuds | **22 nœuds** | 67 nœuds |
| secondes / run (médiane) | 18 | 76 | 71 |

La troisième colonne donne au bras non contraint quatre fois plus de générations,
de façon à égaliser le temps machine. Il reste à **0/5** modèles physiquement
valides, et les produit plus gros : le temps de calcul ne remplace pas la
contrainte. Les échecs du bras non contraint ne sont pas marginaux — il additionne
des hertz à des nombres purs, ou élève une grandeur à la puissance d'une fréquence.

**Ce que ça ne fait *pas*.** Sur un jeu de test tiré *hors* du domaine
d'entraînement (rapport w/w0 poussé de [0.20, 0.67] vers la résonance à
[0.70, 0.90]), tous les bras s'effondrent — R² médian de 0.26, 0.34 et 0.37
respectivement. À ces budgets, **aucun bras ne retrouve II.11.3 exactement** :
`units=` achète des approximations physiquement cohérentes et compactes, pas la
loi elle-même. Les deux tableaux sont reproductibles avec `benchmarks/ab_ood.py`.

**Quand s'en servir.** Pour découvrir une loi physique quand vous connaissez les
unités et que la loi est dimensionnellement homogène, et pour garantir que ce que
le moteur rend a au moins un sens physique. **Pas** pour de la prédiction en boîte
noire : la contrainte écarte les approximations dimensionnellement fausses mais
numériquement bonnes, et peut donc faire *baisser* le R² lorsque l'objectif est
d'ajuster plutôt que de trouver une loi.

**Limites.** Les constantes ajustées sont traitées comme sans dimension
(convention AI Feynman) : une loi dont la constante porte des unités (G, k_B, R)
exige de fournir cette constante comme variable d'entrée typée. Sous `units=`, la
mise à l'échelle interne est purement multiplicative (sans décalage additif), ce
qui maintient chaque candidat dimensionnellement homogène.

---

## Exemple complet : dégradation de batterie (données NASA)

```bash
python examples/battery_soh.py
```

À partir de 168 cycles réels, GP_ELITE découvre une loi de l'état de santé (SOH) :

```
capacity_SOH ≈ 0.913 − 0.352 · tanh( cycle^((temperature/cycle)^0.485) )

R² validation = 0.996   (sur des cycles jamais vus)   12 nœuds
```

Une dégradation saturante avec les cycles, modulée par la température — physiquement plausible, et **certifiée sur des données non vues**.

---

## Sur quoi GP_ELITE est-il bon (et moins bon) ?

**Bon** : lois physiques / d'ingénierie à structure multiplicative ou exponentielle, données expérimentales bruitées de taille modeste, problèmes où l'interprétabilité prime.

Sur le **benchmark Feynman gelé** (15 équations, `PYTHONHASHSEED=0`, `restarts=4`) : **10/15 récupérations symboliques exactes (67 %)** à précision machine (1−R² < 1e-9), **14/15 sous 1e-3 (93 %)**. Face-à-face contre **gplearn** (mêmes données/splits, budget généreux pour gplearn) : **67 % vs 40 %** d'exact — GP_ELITE devant sur 9 équations, égalité sur 5, derrière sur 1. Prévision sur données réelles (SOH batterie NASA, vraie extrapolation sur cycles jamais vus) : R² médian **+0.52** contre +0.34 pour la régression linéaire, zéro modèle divergent. Reproduire : `PYTHONHASHSEED=0 python benchmarks/feynman_bench.py 0 15` et `benchmarks/duel.py`.

**Moins bon** : suites chaotiques (ex. temps de vol de Collatz — composante intrinsèquement aléatoire), >15-20 variables (l'espace de recherche explose — même si `units=` le réduit nettement quand les unités physiques sont connues), gros jeux de données où la précision pure prime sur l'interprétabilité (les modèles d'ensemble dominent alors).

---

## Caractéristiques techniques

- **Recherche sous contrainte dimensionnelle** (v0.4) : génération typée constructive, mutation et croisement préservant les dimensions, filtre de validité dans `fitness()`
- **Mise à l'échelle purement multiplicative sous `units=`** (v0.4.1) : régression par l'origine, pour que la forme *notée* soit la forme *livrée*
- **Garde numérique de l'optimiseur LM** (v0.4) : plus d'overflow float64 sur les chaînes `sq`/`cube`/`*` non bornées
- **Audit dimensionnel post-hoc** (v0.3) : `dimensions.py` — exactement la même algèbre que la recherche contrainte, l'auditeur et le moteur ne peuvent pas diverger
- **Optimisation des constantes par Levenberg–Marquardt** (v0.2) : constantes de qualité « forme fermée », déterministe, LM/Adam commutables
- **Multi-restart + fusion des archives de candidats** (v0.2) : la variance de seed transformée en fiabilité
- **API front de Pareto** (v0.2) : escalier non dominé complexité/précision
- **Mode extrapolation / prévision protégé** (v0.2) : sondes hors-domaine, plancher linéaire, sélection-frontière
- **Amorçage par motifs de composition** (v0.2) : gabarits pythagoricien, somme d'inverses, gaussienne pour les structures imbriquées
- **Modèle en îles asymétriques** (explorer / cleaner / stigmergic) avec migration périodique
- **Linear scaling** (Keijzer 2003) : le moteur cherche la *forme*, les coefficients d'échelle sont résolus en forme fermée
- **Sélection ε-lexicase** (La Cava 2016) pour préserver la diversité comportementale
- **Parallélisme des îles** (multi-cœurs) — ≈ ×3 mesuré sur 4 cœurs
- **Validation hold-out** + sélection parcimonieuse du champion (tolérance R²) : anti-surapprentissage intégré
- **Normalisation shift-free** préservant la structure multiplicative (x·y reste un produit propre)
- **Mémoire stigmergique transférable** entre exécutions (export/import de grammaires)

---

## Tests

```bash
pip install pytest
pytest -q
```

---

## Licence

MIT — voir [LICENSE](LICENSE). Utilisation libre, y compris commerciale, avec conservation de la notice de copyright.

## Citer GP_ELITE

Si GP_ELITE vous est utile dans un travail académique, voir [CITATION.cff](CITATION.cff).
