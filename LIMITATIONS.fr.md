# Ce que GP_ELITE ne fait pas

*[English version](LIMITATIONS.md)*

Cette page dit ce que le moteur ne fait pas, ou fait mal, chaque point avec la
mesure qui le fonde. Les chiffres viennent du travail qui a suivi la 0.9.0, sur le
banc de décision (41 équations de Feynman, cinq graines, 30 secondes par
ajustement ; 13 jeux de données réels), dans `benchmarks/results_0.9/PLAN_PHASE4.md`
et `PLAN_PHASE5.md`. Ils seront mesurés de nouveau sur le paquet de la prochaine
version.

## 1. Les lois qu'il manque encore

Sur les 41 équations, le moteur rend la loi exacte dans 160 ajustements sur 205.
Sept équations ne sont jamais retrouvées :

- **un arc sinus**, `I.26.2` arcsin(n·sin θ) et `I.30.5` arcsin(λ/(n·d)) : aucun
  jeu d'opérateurs du moteur n'a l'arc sinus ;
- **une somme de termes dont l'un est trigonométrique**, `I.37.4`
  I1 + I2 + 2·√(I1·I2)·cos δ et `III.17.37` B·(1 + α·cos θ) ;
- **des arguments imbriqués ou décalés**, `I.50.26` x1·(cos ωt + α·cos² ωt) et
  `III.9.52`, un sinus de (ω − ω0)·t/2 ;
- **la racine d'une somme de trois carrés**, `III.10.19` m·√(Bx² + By² + Bz²).

Une somme de trois produits, `I.11.19`, revient une fois sur dix.

## 2. Les gains reposent sur le banc pour lequel ils ont été conçus

Les changements qui ont fait passer le banc de 86 à 160 lois exactes (B1, E1, et
N1 pour les données bruitées) ajustent directement des familles de formes ; chaque
famille a été choisie à partir d'un prototype essayé sur les lignes d'entraînement
de ces 41 équations. Ils ont été confirmés sur des graines jamais utilisées, mais
sur les mêmes équations. Si des lois de ces formes sont aussi retrouvées ailleurs,
c'est le jeu de test figé avant ce travail qui le dira, une fois, avec la version
(78 autres équations de Feynman, 14 systèmes de Strogatz, 25 jeux de données
réels), et le résultat sera publié quel qu'il soit.

## 3. Le bruit

Avec un bruit gaussien sur la cible d'entraînement, la structure de la loi (le
modèle rendu, ses constantes réajustées sur des données propres, reproduit les
lignes de test propres) est retrouvée dans 106 ajustements sur 205 avec 1 % de
bruit et 86 avec 10 %. Les constantes de la formule rendue portent le bruit :
`v0 / (1 - 0.997 * v1 / v2)` pour v0/(1 − v1/v2). Au-delà de 10 %, le moteur n'a
pas été mesuré.

## 4. Des données réelles, hors du domaine d'entraînement

Une formule qui ajuste n'est pas une loi. Sur les 13 jeux réels du banc, pour
prédire les 20 % de lignes les plus éloignées des autres, 10 modèles sur 65
s'effondrent (R² de test négatif), le pire à −233. Sur les 25 jeux réels du jeu de
test figé, mesurés pour la 0.9.0, 36 sur 125 ; les effondrements se concentrent sur
les petits jeux ou ceux surtout faits de catégories. Gardez des lignes hors de
l'ajustement pour juger une formule, et regardez le front de Pareto : sur des
données réelles, la réponse lisible est souvent une entrée courte du front, pas le
champion rendu.

## 5. Des données exactes qu'aucune graine ne couvre

Quand des données suivent exactement une loi qu'aucune graine exacte ne couvre,
une graine qui ne fait qu'approcher les données peut détourner la recherche de la
loi. Vu sur la loi de Kepler normalisée par min-max (`normalize="minmax"`) : exacte
dans 1 ajustement sur 10 au lieu de 3, à 40 générations. Avec la normalisation par
défaut, sur le banc, aucune loi n'a été perdue ainsi. `PLAN_PHASE5.md`, mécanique
de N1.

## 6. Une formule qui s'écarte de ses prédictions

Des opérations protégées (une division par presque zéro, une puissance plafonnée
à un million) gardent les prédictions finies ; quand l'une d'elles agit sur vos
données, la formule imprimée s'écarte de `predict()`. Le moteur le dit alors
(`formula_exact` vaut False, avec un avertissement qui nomme les formules exactes
du front de Pareto). Sur les données réelles du banc, c'est arrivé dans 11
ajustements sur 260.

## 7. La même graine sur une autre machine

À partir de quatre cœurs, les îles tournent en parallèle par défaut et peuvent
rendre un autre modèle qu'en séquence ; avec `time_limit=`, le nombre de
générations atteint dépend de la vitesse de la machine. `parallel=False` et un
nombre de `generations` donnent le même modèle à chaque exécution sur une machine
donnée ; d'un processeur à l'autre, les résultats peuvent encore différer dans les
derniers chiffres, puis dans le modèle.

## 8. Les unités physiques

Sous `units=`, la population est typée : les graines de la loi de puissance, de
B1, E1 et N1 n'agissent pas, et une génération typée coûte environ 1,4 fois une
génération non typée (Feynman II.11.3).

## 9. La taille et la nature des données

GP_ELITE est écrit en Python et NumPy seulement. Il est fait pour une centaine à
quelques milliers de lignes et jusqu'à une dizaine de variables ; au-delà de quinze
à vingt variables, l'espace de recherche explose. Il n'est pas fait pour les suites
chaotiques, ni pour les grands jeux de données où la précision brute compte plus
qu'une formule lisible : des modèles d'ensemble, ou des moteurs comme PySR et
Operon, y conviennent mieux.
