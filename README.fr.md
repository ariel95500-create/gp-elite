GP_ELITE
Régression symbolique par programmation génétique — pour découvrir des lois interprétables sur vos données expérimentales.
🇬🇧 English version

GP_ELITE cherche une formule mathématique qui relie vos variables à une cible, au lieu d'une boîte noire. Pensé pour les petits jeux de données expérimentaux (≤10 variables, 100-5000 points) où l'on veut comprendre la relation : lois de dégradation, calibration de capteurs, corrélations d'ingénierie, courbes dose-réponse, lois physiques.
Pur Python / NumPy — pas de Julia, pas de compilation, pas de GPU. `pip install` et c'est parti.
![GP_ELITE redécouvre la 3ᵉ loi de Kepler à partir de 8 points (R² = 1.000000)](kepler_plot.png)
> À partir des seules distances et périodes orbitales des 8 planètes, GP\_ELITE a redécouvert la 3ᵉ loi de Kepler (`T = a·√a = a^1.5`) en quelques secondes — voir \[`examples/kepler\_demo.py`](examples/kepler\_demo.py).
```python
from gp\_elite import symbolic\_regression

result = symbolic\_regression(X, y, feature\_names=\["cycle", "temperature", "courant"])
print(result.expression)        # capacity\_SOH = 0.913 - 0.352·tanh(...)
print(result.r2\_validation)     # 0.996  (sur des données jamais vues)
```
---
Pourquoi GP_ELITE ?
	GP_ELITE	Réseaux de neurones	PySR (état de l'art)
Sortie	formule lisible	boîte noire	formule lisible
Installation	`pip install` (pur Python)	lourde	nécessite Julia
Validation anti-surapprentissage	intégrée (hold-out)	à faire soi-même	à faire soi-même
Sélection de variables	rapport d'importance	non	partielle
La niche de GP_ELITE : zéro barrière d'entrée. Un ingénieur de labo, un étudiant ou un technicien pointe un fichier CSV et reçoit une loi validée, sans devenir développeur.
---
Installation
```bash
pip install gp-elite          # depuis PyPI
# ou, depuis les sources :
git clone https://github.com/ariel95500-create/gp-elite
cd gp-elite \&\& pip install -e .
```
Dépendances : `numpy`, `pandas`, `scikit-learn`.
---
Utilisation
En une ligne, sur vos données (interface graphique en console)
```bash
gp-elite
```
Choisissez le mode 6 (CSV générique), indiquez votre fichier, et laissez les valeurs par défaut. GP_ELITE détecte les colonnes, sépare un jeu de validation, évolue, et affiche la loi trouvée avec son rapport de généralisation.
Par programmation (notebooks, pipelines)
```python
import numpy as np
from gp\_elite import symbolic\_regression

X = np.random.uniform(1, 5, (200, 2))
y = 2.0 + 3.0 \* np.sqrt(X\[:, 0]) - 0.5 \* X\[:, 1]

result = symbolic\_regression(
    X, y,
    feature\_names=\["a", "b"],
    operators="physical",   # 'physical' | 'trig' | 'full' | 'poly'
    generations=60,
    speed="fast",           # 'ultrafast' | 'fast' | 'normal'
)

print(result.expression)        # ex : 2.0 + 3.0·sqrt(a) - 0.5·b
print(result.r2\_validation)     # qualité sur le hold-out
print(result.size)              # nombre de nœuds (lisibilité)
```
---
Exemple complet : dégradation de batterie (données NASA)
```bash
python examples/battery\_soh.py
```
À partir de 168 cycles réels, GP_ELITE découvre une loi de l'état de santé (SOH) :
```
capacity\_SOH ≈ 0.913 − 0.352 · tanh( cycle^((temperature/cycle)^0.485) )

R² validation = 0.996   (sur des cycles jamais vus)   12 nœuds
```
Une dégradation saturante avec les cycles, modulée par la température — physiquement plausible, et certifiée sur des données non vues.
---
Sur quoi GP_ELITE est-il bon (et moins bon) ?
Bon : lois physiques / d'ingénierie à structure multiplicative ou exponentielle, données expérimentales bruitées de taille modeste, problèmes où l'interprétabilité prime.
Sur un sous-ensemble représentatif du Feynman Symbolic Regression Benchmark (16 équations physiques), en mode `fast` (~15 s/équation) : 81 % des équations résolues à R² > 0.999, R² moyen 0.993.
Moins bon : suites chaotiques (ex. temps de vol de Collatz — composante intrinsèquement aléatoire), >15-20 variables (l'espace de recherche explose), gros jeux de données où la précision pure prime sur l'interprétabilité (les modèles d'ensemble dominent alors).
---
Caractéristiques techniques
Modèle en îles asymétriques (explorer / cleaner / stigmergic) avec migration périodique
Linear scaling (Keijzer 2003) : le moteur cherche la forme, les coefficients d'échelle sont résolus en forme fermée
Sélection ε-lexicase (La Cava 2016) pour préserver la diversité comportementale
Parallélisme des îles (multi-cœurs) — ≈ ×3 mesuré sur 4 cœurs
Validation hold-out + sélection parcimonieuse du champion (tolérance R²) : anti-surapprentissage intégré
Normalisation shift-free préservant la structure multiplicative (x·y reste un produit propre)
Mémoire stigmergique transférable entre exécutions (export/import de grammaires)
---
Tests
```bash
pip install pytest
pytest -q
```
---
Licence
MIT — voir LICENSE. Utilisation libre, y compris commerciale, avec conservation de la notice de copyright.
Citer GP_ELITE
Si GP_ELITE vous est utile dans un travail académique, voir CITATION.cff.
