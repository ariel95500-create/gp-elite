# Utiliser GP_ELITE

Partie de la documentation de GP_ELITE : retour au [README](../../README.fr.md) ; [English version](../usage.md).

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
[Comment GP_ELITE est mesuré](mesures.md).


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
        parallel=False,           # le même modèle sur toute machine, voir plus bas
    )
    print(resultat.expression)      # 2 + 3 * sqrt(a) - 0.5 * b
    print(resultat.r2_validation)   # 1.0
    print(resultat.size)            # 33 (nœuds de l'arbre du moteur)
    print(resultat.sympy())         # la même formule, lisible par sympy
```

Ici, la recherche rend la loi qu'on lui a donnée, écrite dans vos variables : l'arbre
du moteur a 33 nœuds, et la formule qui en est imprimée est 2 + 3·√a − 0.5·b ;
l'ajustement vérifie que cette formule reproduit `predict()`. Ce n'est pas garanti. Sur une loi plus difficile, le même budget
rend une approximation qui colle presque parfaitement au hold-out et n'est pourtant pas
la loi (la 0.7 en rendait une pour cet exemple même) ; c'est en lisant la formule qu'on
s'en aperçoit. `restarts=` et `speed="thorough"` consacrent plus de calcul à la forme
exacte, sans garantie.

- `speed` : `'ultrafast' | 'fast' (défaut) | 'normal' | 'thorough'`. `'thorough'`
  (population 400, quatre îles, 200 générations) est le régime pour chercher une
  loi exacte ; avec deux fois plus de générations que par défaut, il est plus
  lent, et ne garantit pas de faire mieux. Sans `generations=` ni `time_limit=`,
  depuis la 1.2, il s'arrête lui aussi dès qu'il ne progresse plus (`patience=`,
  plus bas).
- `time_limit=` (secondes) : la recherche s'arrête proprement à l'échéance et rend
  le meilleur modèle trouvé, au lieu d'être interrompue sans résultat ; la
  génération en cours et la sélection finale ajoutent un peu (dans la mesure de
  sortie de la 1.4.0, les 2 291 ajustements arrêtés par un budget de 30 s ont
  pris 30,5 s en médiane et 31,9 s au plus). Une recherche qui trouve une loi
  exacte finit avant son budget : avec 15 s sur 3 000 lignes
  (`benchmarks/time_limit_check.py`), la loi est revenue à 9,7 s avec les îles
  en parallèle. En séquence, la recherche est allée jusqu'à son budget, 15,3 s,
  et a rendu une approximation de R² 0,9979 (avec la 1.3.0, la loi était
  revenue à 6,3 s).
- `patience=` (depuis la 1.2) : quand l'appel ne fixe ni `generations` ni
  `time_limit`, la recherche s'arrête dès que son erreur sur les lignes mises de
  côté (sur les lignes d'entraînement s'il n'y en a pas) n'a pas baissé de 1 % en
  30 générations, puis polit et choisit comme
  d'habitude. Un ajustement sur un tableau de TP de dix points prend alors
  quelques secondes : les six du notebook de TP (`examples/tp_six_lois.ipynb`)
  prenaient 48 s en tout, contre
  194 à 198 s avec la 1.1.0 sur la même machine, et rendaient les mêmes formules ;
  avec la 1.4.0, dans sa mesure de sortie, ils prennent 52 et 53 s dans les deux
  passages appariés avec la 1.3.0 le même jour, contre 49 et 54 s, avec les
  mêmes formules (50 à 53 s sur les quatre passages de la 1.4.0).
  Un appel qui fixe son budget (`generations=` ou `time_limit=`) le reçoit en
  entier, comme en 1.1. Un entier k
  applique une patience de k générations quel que soit le budget, et 0 la coupe.
  `GPEliteRegressor` fixe toujours son nombre de générations, si bien que l'arrêt
  n'y agit pas.
- `restarts=` : évolutions indépendantes dont les candidats sont fusionnés avant le
  choix final.

**Vos données.** `X` peut être un tableau NumPy, une liste de lignes ou un
DataFrame pandas, dont les noms de colonnes deviennent alors les noms de
variables ; `y` un tableau 1-D ou une seule colonne. Une valeur manquante ou
infinie est refusée avec la ligne et la colonne en cause (retirez-la ou
complétez-la d'abord), et une colonne non numérique est nommée dans l'erreur.
Avec la 0.7, une valeur manquante dans y ou dans une colonne dont la loi se sert
passait, et l'ajustement rendait une formule sans rapport, sans avertissement
(`benchmarks/bad_input_check.py`). Des valeurs éloignées de 1 ne demandent aucune
préparation : une cible de l'ordre de 1e-9 ou de 1e20 est divisée en interne par
une puissance de dix, une colonne de l'ordre de 1e-19 par sa plus grande valeur
absolue (la normalisation par défaut), et la formule revient dans vos unités
(jusqu'à la 0.7, une telle cible rendait une constante ou une droite fausse, avec
un R² négatif, et aucun avertissement que l'ajustement avait échoué).

**Reproductibilité.** Avec le même `seed`, les mêmes données et les mêmes
réglages, un ajustement rend le même modèle d'un lancement à l'autre, sans fixer
`PYTHONHASHSEED` (nécessaire jusqu'à la 0.7). Les îles parallèles suivent un
autre chemin que la recherche séquentielle, et `parallel=None` les active dès
quatre cœurs : fixez aussi `parallel=`. Sur une autre machine, le modèle peut
encore différer : NumPy calcule des fonctions comme `exp` et `tanh` avec les
instructions qu'offre le processeur, ce qui peut changer le dernier chiffre
d'une valeur, et la recherche peut alors prendre un autre chemin.

**Scripts et îles parallèles.** Sur une machine à quatre cœurs ou plus, les îles
tournent dans des processus parallèles. Ces processus sont démarrés en mode
`spawn` sur tous les systèmes (Linux compris) et ré-importent votre script :
gardez le code de premier niveau sous
`if __name__ == "__main__":`, comme ci-dessus. Sans cette garde, GP_ELITE détecte
la situation, termine sur un cœur avec les îles en séquence, et le signale une
fois ; les îles en séquence suivent un autre chemin qu'en parallèle, et le modèle
peut différer. D'où `parallel=False` dans l'exemple ci-dessus : avec les îles en
parallèle (le défaut dès quatre cœurs), il rendait un autre modèle, une
approximation de R² 0,99998, mesurée avec la 1.0.0 (pas mesurée de nouveau
depuis).
Rien à faire dans un notebook.

### Lire le résultat

- **`expression` est écrite dans vos variables.** Le moteur cherche sur des
  colonnes remises à l'échelle en interne ; la formule rendue replie cette mise à
  l'échelle dans ses constantes, et l'ajustement vérifie qu'elle reproduit
  `predict()` sur vos données (`resultat.formula_exact`). `resultat.sympy()` donne
  la même formule sous forme de chaîne lisible par `sympy.sympify`, et
  `resultat.sympy_expr()` l'expression sympy elle-même, avec un symbole par
  colonne : à utiliser quand un nom de colonne est aussi une constante ou une
  fonction de sympy (`sympify` lit `E` comme 2,718..., `I` comme √-1) ou n'est
  pas un identifiant ; `sympy()` le signale dans ce cas. (Avant la 0.7, les
  constantes affichées étaient celles de l'espace normalisé interne.) Depuis la
  1.2, une puissance d'un nombre s'écrit comme une exponentielle, et une
  exponentielle d'une seule variable avec son échelle :
  `0.00538504 + 5.05644 * 0.00614708^(0.2 * t)` revient sous la forme
  `0.00538504 + 5.05644 * exp(-t / 0.981975)`. La formule réécrite n'est gardée que si elle
  passe la même vérification, si bien que le modèle et `formula_exact` ne
  changent pas. La
  formule est la fonction mathématique pure : là où l'un des garde-fous
  numériques du moteur agit sur vos données (une puissance bornée parce que sa
  base dépasse 100 ou son exposant 6 en valeur absolue, ou sa valeur un million ;
  une division par un dénominateur à moins de 1e-8 de zéro ; depuis la 1.3,
  l'argument d'un arc sinus ramené dans [−1, 1]), ou, rarement, là où
  l'arrondi ruine une expression mal conditionnée, elle s'écarte de `predict()` sur
  ces lignes, `formula_exact` vaut False et l'ajustement le signale. Dans les
  mesures de la 0.8
  ([`benchmarks/results_0.8/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks/results_0.8)),
  c'était le cas pour 6 des 205 ajustements Feynman de la version publiée à 30 s
  par ajustement, pour aucun des 60 ajustements sur données réelles
  standardisées et 8 des 70 sur données réelles dans leurs unités (campagnes 5b
  et 6b), et pour 1 des 105 ajustements de la comparaison à travail égal
  (100 générations). L'avertissement dit aussi combien d'entrées de
  `resultat.pareto` ont une formule exacte et nomme la plus précise d'entre
  elles : imposer une formule exacte au modèle rendu coûte de la précision
  (mesuré pour la 0.9 dans
  [`benchmarks/results_0.9/PLAN_PHASE2.md`](https://github.com/ariel95500-create/gp-elite/blob/main/benchmarks/results_0.9/PLAN_PHASE2.md)),
  le choix vous revient donc.
- **`r2_validation` est un score de sélection.** Le hold-out sur lequel il est
  calculé sert aussi à choisir le modèle rendu parmi les candidats : il est donc
  optimiste. Pour estimer comment la formule généralise, gardez vos propres
  données de test hors de l'ajustement.
- **`resultat.pareto`** liste les autres candidats non dominés, du plus simple au
  plus complexe, chacun avec son `expression`, son `r2_validation` et son `predict`.
- **Sous 30 lignes, rien n'est tenu à l'écart :** `r2_validation` et
  `resultat.pareto` valent alors `None`, comme sur les huit planètes de Kepler ou
  un tableau de TP de 10 ou 20 points. Jugez un tel ajustement sur des lignes à
  vous, gardées hors de lui.
- **`predict()` vérifie ce qu'on lui donne.** Il attend autant de colonnes qu'à
  l'ajustement (un seul échantillon s'écrit `X.reshape(1, -1)`), et rend NaN pour
  une ligne dont une entrée manque ou est infinie, là où la 0.7 rendait 0.


## Tests

```bash
pip install -e ".[test]"
python -m pytest tests/ -q
```

`tests/test_guarantees.py` fige chaque défaut trouvé jusqu'ici — chaque test a été
vérifié en échec sur le code qui portait le défaut. La suite tourne à chaque envoi
sur GitHub qui modifie du code (Linux, Python 3.9 à 3.14, et Windows).
