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

## Nouveautés 0.4.0 « Lawful »

- **Recherche sous contrainte dimensionnelle** (`units=`) : déclarez les unités
  physiques de vos colonnes, et le moteur ne construit plus que des expressions
  dimensionnellement saines — génération typée constructive, mutation et
  croisement préservant les dimensions, plus un filtre de validité qui rejette
  les candidats non conformes sur tous les chemins de code. Sur Feynman II.11.3
  (5 variables, 5 seeds) : sans contrainte, **0/5** modèles sont
  dimensionnellement valides ; avec `units=`, **5/5 sont valides et 3/5
  retrouvent la loi exacte**. Coût : environ 16× plus lent.
- **Garde numérique dans l'optimiseur LM** : des chaînes `sq`/`cube`/`*` non
  bornées pouvaient dépasser float64 lors des produits jacobiens. Corrigé, sans
  aucun changement sur les ajustements sains.
- Sans `units=`, le comportement est **strictement inchangé** (non-régression
  vérifiée : équation, taille et MSE identiques à seed égal).

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

**Effet mesuré** — Feynman II.11.3 (5 variables, moteur complet, 5 seeds) :

| | dimensionnellement valides | loi exacte retrouvée |
|---|---:|---:|
| défaut | **0 / 5** | 0 / 5 |
| `units=` | **5 / 5** | **3 / 5** |

Coût : environ 16× plus lent. Reproductible avec `benchmarks/ab_final.py`.

**Quand s'en servir.** Pour découvrir une loi physique quand vous connaissez les
unités et que la loi est dimensionnellement homogène. **Pas** pour de la
prédiction en boîte noire : la contrainte écarte les approximations
dimensionnellement fausses mais numériquement bonnes, et fait donc *baisser* le
R² lorsque l'objectif est d'ajuster plutôt que de trouver une loi.

**Limites.** Les constantes ajustées sont traitées comme sans dimension
(convention AI Feynman) : une loi dont la constante porte des unités (G, k_B, R)
exige de fournir cette constante comme variable d'entrée typée.

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
