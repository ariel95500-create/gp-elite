# Ce que GP_ELITE ne fait pas

*[English version](LIMITATIONS.md)*

Cette page dit ce que le moteur ne fait pas, ou fait mal, chaque point avec la
mesure qui le fonde. Sauf quand un point dit autre chose, les chiffres ont été
mesurés sur le paquet de la version
1.0.0, côte à côte avec la 0.9.0, sur le banc de décision (41 équations de Feynman,
cinq graines, 30 secondes par ajustement ; 7 jeux de données réels) et sur un jeu
de test figé avant tout le travail de la 1.0 (78 autres équations de Feynman, 14
systèmes de Strogatz, 25 jeux de données réels) :
`benchmarks/results_0.9/release_1.0/`. La version 1.1 ne change que le mode des
unités : sans unités, elle rend les mêmes chiffres, et le point 8 est mesuré sur le
paquet de la 1.1.0, côte à côte avec la 1.0.0 (`benchmarks/results_1.1/release/`).

## 1. Les lois qu'il manque encore

Sur les 41 équations, le moteur rend la loi exacte dans 163 ajustements sur 205
(0.9.0 : 88). Sept équations ne sont jamais retrouvées :

- **un arc sinus**, `I.26.2` arcsin(n·sin θ) et `I.30.5` arcsin(λ/(n·d)) : aucun
  jeu d'opérateurs du moteur n'a l'arc sinus ;
- **une somme de termes dont l'un est trigonométrique**, `I.37.4`
  I1 + I2 + 2·√(I1·I2)·cos δ et `III.17.37` B·(1 + α·cos θ) ;
- **des arguments imbriqués ou décalés**, `I.50.26` x1·(cos ωt + α·cos² ωt) et
  `III.9.52`, un sinus de (ω − ω0)·t/2 ;
- **la racine d'une somme de trois carrés**, `III.10.19` m·√(Bx² + By² + Bz²).

Une somme de trois produits, `I.11.19`, revient une fois sur cinq. Sur les 78
équations du jeu de test, 34 ne sont jamais retrouvées.

## 2. Les gains sont moindres loin du banc pour lequel ils ont été conçus

Les changements de la 1.0 (B1, E1, et N1 pour les données bruitées) ajustent
directement des familles de formes ; chaque famille a été choisie à partir d'un
prototype essayé sur les lignes d'entraînement des 41 équations du banc, où elles
font passer les lois exactes de 88 à 163 (+85 %). Sur les 78 équations du jeu de
test, figé avant ce travail et mesuré une seule fois, les lois exactes passent de
145 à 213 sur 390 (+47 %) : 203 sur 290 sur les 58 équations de la table principale
de Feynman (0.9.0 : 144), mais 10 sur 100 sur ses 20 équations bonus (0.9.0 : 1).
Sur les 14 systèmes de Strogatz, le moteur ne fait pas mieux : 7 ajustements exacts
sur 70 sur les lignes de test, contre 8.

## 3. Le bruit

Avec un bruit gaussien sur la cible d'entraînement, la structure de la loi (le
modèle rendu, ses constantes réajustées sur des données propres, reproduit les
lignes de test propres) est retrouvée dans 105 ajustements sur 205 avec 1 % de
bruit et 85 avec 10 % (0.9.0 : 67 et 66). Les constantes de la formule rendue
portent le bruit : avec 1 % de bruit,
`0.00115247 + 1.00099 * v0 / (1 - 0.997137 * v1 / v2)` pour v0/(1 − v1/v2)
(Feynman I.34.1). Au-delà de 10 %, le moteur n'a
pas été mesuré.

## 4. Des données réelles, hors du domaine d'entraînement

Une formule qui ajuste n'est pas une loi. Sur les 7 jeux réels du banc (chacun dans
ses propres unités, six d'entre eux standardisés aussi), pour prédire les 20 % de
lignes les plus éloignées du centre des données, 11 modèles sur 65 s'effondrent (R²
de test négatif), le pire à −233 ; sur les 25 jeux réels du jeu de test, 64 sur 250
(37 sur 125 standardisés, 27 dans leurs propres unités). La 1.0 n'y change rien : la
0.9.0, mesurée à côté, donne les mêmes nombres. Sur le jeu de test, les
effondrements se concentrent sur quelques jeux : six des 25 en font 28 sur 37. Gardez des lignes hors de
l'ajustement pour juger une formule, et regardez le front de Pareto : sur des
données réelles, la réponse lisible est souvent une entrée courte du front, pas le
champion rendu.

## 5. Des données exactes qu'aucune graine ne couvre

Quand des données suivent exactement une loi qu'aucune graine exacte ne couvre,
une graine qui ne fait qu'approcher les données peut détourner la recherche de la
loi. Vu sur la loi de Kepler normalisée par min-max (`normalize="minmax"`) : exacte
dans 1 ajustement sur 10 au lieu de 3, à 40 générations
(`release_1.0/m3/kepler_minmax_check.txt`). Avec la normalisation par défaut, sur le
banc, aucune loi n'a été perdue ainsi : aucune équation n'a moins d'ajustements
exacts qu'avec la 0.9.0. `PLAN_PHASE5.md`, mécanique de N1.

## 6. Une formule qui s'écarte de ses prédictions

Des opérations protégées (une division par presque zéro, une puissance plafonnée
à un million) gardent les prédictions finies ; quand l'une d'elles agit sur vos
données, la formule imprimée s'écarte de `predict()`. Le moteur le dit alors
(`formula_exact` vaut False, avec un avertissement qui nomme les formules exactes
du front de Pareto). Sur les données réelles, c'est arrivé dans 7 ajustements sur
130 sur le banc et 61 sur 500 sur le jeu de test.

## 7. La même graine sur une autre machine

À partir de quatre cœurs, les îles tournent en parallèle par défaut et peuvent
rendre un autre modèle qu'en séquence ; avec `time_limit=`, le nombre de
générations atteint dépend de la vitesse de la machine. `parallel=False` et un
nombre de `generations` donnent le même modèle à chaque exécution sur une machine
donnée ; d'un processeur à l'autre, les résultats peuvent encore différer dans les
derniers chiffres, puis dans le modèle.

## 8. Les unités physiques

Sous `units=`, la population est typée, et une génération typée coûte environ 1,4
fois une génération non typée (mesuré en phase 3, `PLAN_PHASE3.md`). Depuis la 1.1,
les graines de la loi de puissance, de B1, E1 et N1 agissent aussi avec les unités,
chacune placée seulement si elle passe la porte des dimensions. Sur les 41
équations avec leurs unités, le moteur rend la loi exacte dans 165 ajustements sur
205 (1.0.0 : 108), et six équations ne sont jamais retrouvées avec cinq graines
aléatoires
(1.0.0 : 13). Ce qui reste :

- **les données bruitées parcourent tout le budget.** Une recherche ne s'arrête
  plus tôt que sur une loi exacte, et avec du bruit il n'y en a pas, même quand la
  graine placée au départ est la loi. Les six ajustements du notebook de TP
  (`examples/tp_six_lois.ipynb`, dix points et 2 % de bruit chacun) prennent
  environ 40 à 60 secondes chacun ; la chute libre prend 51 s contre 44 s avec la
  1.0.0, les cinq autres à peu près le temps de la 1.0.0 ;
- **les exposants ajustés.** Avec les unités, une graine aux exposants ajustés sur
  les données n'est placée que si chaque exposant qui n'est pas un demi-entier
  porte sur une entrée sans dimension. Des exposants comme 1,0041 sur une quantité
  en moles ne peuvent pas être homogènes, et avec `unknown_constant=True` une telle
  graine faisait chercher à la recherche typée des unités fractionnaires : la loi
  des gaz du notebook de TP prenait 78 s au lieu de 50 s avant la correction de la
  1.1.0 (`benchmarks/results_1.1/PLAN_U2.md`). La graine aux exposants arrondis aux
  demi-entiers est placée comme avant.

## 9. La taille et la nature des données

GP_ELITE est écrit en Python et NumPy seulement. Il est fait pour une centaine à
quelques milliers de lignes et jusqu'à une dizaine de variables, la plage de ses
mesures (10 000 lignes au plus, dans l'étude de taille) ; au-delà, rien n'est
mesuré, et l'espace de recherche grandit vite avec le nombre de variables. Il n'est pas fait pour les suites
chaotiques, ni pour les grands jeux de données où la précision brute compte plus
qu'une formule lisible : des modèles d'ensemble, ou des moteurs comme PySR et
Operon, y conviennent mieux.
