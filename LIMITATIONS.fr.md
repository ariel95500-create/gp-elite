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
unités. Sans unités, elle rend les modèles de la 1.0.0 à travail égal ; sous le
budget de 30 s, les comptes bougent un peu d'une campagne à l'autre, pour les deux
versions (mesurées côte à côte pour la sortie de la 1.1, les deux
donnent 108 et 86 structures sous bruit, 8 ajustements de Strogatz exacts sur 70
et 10 effondrements sur 65, là où les points ci-dessous disent 105, 85, 7 et 11 ;
pour les formules imprimées qui s'écartent de leur modèle, point 6, 7 sur 130 et
66 sur 500 pour la 1.0.0, 8 et 67 pour la 1.1.0, là où il dit 7 et 61).
Le point 8 est mesuré sur le paquet de la 1.1.0, côte à côte avec la 1.0.0
(`benchmarks/results_1.1/release/`), sauf les temps de son premier tiret,
mesurés sur la 1.2.0 à côté de la 1.1.0 ; le point 10 sur la campagne qui a
décidé l'arrêt de la 1.2.

Avec un budget fixé et sans toucher à `patience=`, la version 1.2 ne change pas
les modèles sans unités ; avec les unités, elle ne change que les ajustements
dont le départ typé demande un produit de 9 à 12 facteurs ou atteint son
échéance (sur le banc, Feynman III.19.51). Mesurées
côte à côte pour la sortie de la 1.2 (`benchmarks/results_1.2/release/`, les
chiffres dans `m2/limits_figures.txt`), la 1.1.0 et la 1.2.0 donnent le même
chiffre sur chaque point, et d'une campagne à l'autre les chiffres bougent comme
ci-dessus : 214 lois exactes sur 390 sur le jeu de test (204 sur 290 et 10 sur
100), 33 de ses équations jamais retrouvées, 10 ajustements de Strogatz exacts
sur 70, 108 et 85 structures sous bruit, 10 effondrements sur 65 (le pire à
−1 946) et 66 sur 250 sur le jeu de test (38 standardisés, 28 dans leurs propres
unités), 12 formules qui s'écartent sur 130 et 65 sur 500, et avec les unités 166
lois exactes sur 205. Ce que la 1.2 change, c'est le temps d'un ajustement avec
les réglages par défaut, et avec lui une partie des modèles (points 8 et 10).

La version 1.3 ajoute l'arc sinus aux jeux d'opérateurs `trig` et `full`, et
laisse le jeu `physical`, celui par défaut, tel qu'il était : avec lui, les
modèles de la 1.2 à travail égal. Mesurée à côté de la 1.2.0 pour la sortie de
la 1.3 (`benchmarks/results_1.3/release/`, les chiffres dans
`m2/limits_figures.txt`), la 1.3.0 donne :
- 171 lois exactes sur 205 sur le banc de décision contre 163, et cinq
  équations jamais retrouvées contre sept (point 1) ;
- 116 et 87 structures sous bruit contre 108 et 85 ;
- avec les unités, 174 lois exactes sur 205 contre 166, et quatre équations
  jamais retrouvées contre six.

Ailleurs, les deux versions donnent les mêmes chiffres, ou des chiffres qui
bougent comme d'une campagne à l'autre. Les chiffres de la 1.3.0 viennent en
premier :
- sur le jeu de test, 214 lois exactes sur 390 contre 213 (204 et 203 sur 290,
  10 et 10 sur 100), et 33 de ses équations jamais retrouvées contre 34 ;
- 8 ajustements de Strogatz exacts sur 70 avec les deux ;
- 10 effondrements sur 65 avec les deux (le pire à −1 946), et 65 sur 250 sur
  le jeu de test avec les deux (37 standardisés, 28 dans leurs propres
  unités) ;
- 11 formules qui s'écartent sur 130 avec les deux, et 65 sur 500 contre 64.

## 1. Les lois qu'il manque encore

Sur les 41 équations, le moteur rend la loi exacte dans 163 ajustements sur 205
(0.9.0 : 88). Sept équations ne sont jamais retrouvées :

- **un arc sinus**, `I.26.2` arcsin(n·sin θ) et `I.30.5` arcsin(λ/(n·d)) : aucun
  jeu d'opérateurs de la 1.0 n'avait l'arc sinus. Depuis la 1.3, les deux
  reviennent (plus bas) ;
- **une somme de termes dont l'un est trigonométrique**, `I.37.4`
  I1 + I2 + 2·√(I1·I2)·cos δ et `III.17.37` B·(1 + α·cos θ) ;
- **des arguments imbriqués ou décalés**, `I.50.26` x1·(cos ωt + α·cos² ωt) et
  `III.9.52`, un sinus de (ω − ω0)·t/2 ;
- **la racine d'une somme de trois carrés**, `III.10.19` m·√(Bx² + By² + Bz²).

Une somme de trois produits, `I.11.19`, revient une fois sur cinq. Sur les 78
équations du jeu de test, 34 ne sont jamais retrouvées.

**Depuis la 1.3, l'arc sinus.** Les jeux `trig` et `full` ont l'opérateur, et
les graines contiennent l'arc sinus d'un monôme. Dans la mesure de sortie de la
1.3, `I.30.5` revient exacte dans 5 ajustements sur 5, et `I.26.2` dans 3 sur
5. Le moteur rend alors 171 lois exactes sur 205, et cinq équations ne sont
jamais retrouvées. Deux choses que l'arc sinus n'atteint pas :
- **un arc sinus dont l'argument n'est pas un monôme,** comme le n·sin θ de
  `I.26.2`. La recherche doit le construire, et à 30 s elle l'a fait dans 3
  ajustements sur 5 ;
- **la loi de Snell sur quelques points bruités,** i2 = arcsin(sin(i1)/n).
  Avec 10 ou 20 points et 2 % ou 5 % de bruit, les courbes rendues sont plus
  proches de la loi que le bruit ajouté (mesuré sur une première version de
  l'arc sinus, `benchmarks/results_1.3/a1/examine/`). La loi ne revient dans
  aucun des 40 ajustements du diagnostic des TP, avec la 1.2.0 comme avec la
  1.3.0, sur deux séries de tirages.

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
(`release_1.0/m3/kepler_minmax_check.txt`). Le contrôle utilise le jeu `full` ;
avec son arc sinus, la 1.3.0 donne 2 sur 10 au lieu de 4
(`benchmarks/results_1.3/release/m3/kepler_minmax_check.txt`). Avec la
normalisation par défaut, sur le
banc, aucune loi n'a été perdue ainsi : aucune équation n'a moins d'ajustements
exacts qu'avec la 0.9.0. `PLAN_PHASE5.md`, mécanique de N1.

## 6. Une formule qui s'écarte de ses prédictions

Des opérations protégées (une division par presque zéro, une puissance plafonnée
à un million) gardent les prédictions finies ; quand l'une d'elles agit sur vos
données, la formule imprimée s'écarte de `predict()`. Le moteur le dit alors
(`formula_exact` vaut False, avec un avertissement qui nomme les formules exactes
du front de Pareto). Sur les données réelles, c'est arrivé dans 7 ajustements sur
130 sur le banc et 61 sur 500 sur le jeu de test.

Depuis la 1.3, l'arc sinus est l'une de ces protections : dans le modèle, son
argument est ramené dans [−1, 1], et dans la formule imprimée il ne l'est pas.
Dans les jeux qui ont l'arc sinus, dans la mesure de sortie de la 1.3, la
formule s'écarte dans 82 ajustements sur 530, contre 27 pour la 1.2.0. 47 des
82 ont un arc sinus. La recherche peut se servir de cette protection : là où
l'argument sort de [−1, 1], l'arc sinus du modèle est plat, à ±π/2. Sur le
problème du notebook de TP du jeu `full` (`examples/tp_regression_symbolique.ipynb`,
dix graines), la 1.3.0 a eu l'erreur la plus grande dans 6 à 8 graines sur 10 à
chaque budget. Dix graines ne montrent pas cet écart, au test des signes du
notebook (`benchmarks/results_1.3/release/m3/examine/`).

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
205 (1.0.0 : 108), et six équations ne sont jamais retrouvées en cinq graines
(1.0.0 : 13). Ce qui reste :

- **les données bruitées parcourent tout le budget que l'appel fixe.** Avec
  `generations=` ou `time_limit=`, une recherche ne s'arrête plus tôt que sur une
  loi exacte, et avec du bruit il n'y en a pas, même quand la graine placée au
  départ est la loi. Avec les réglages par défaut, depuis la 1.2, l'arrêt du
  point 10 la termine : les six ajustements du notebook de TP
  (`examples/tp_six_lois.ipynb`, dix points et 2 % de bruit chacun) prennent de 7
  à 10 s chacun, contre 28 à 37 s avec la 1.1.0 sur la même machine, avec les
  mêmes formules ;
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

## 10. L'arrêt avec les réglages par défaut

Depuis la 1.2, un appel qui ne fixe ni `generations` ni `time_limit` arrête sa
recherche dès que l'erreur sur les lignes mises de côté (sur les lignes
d'entraînement s'il n'y en a pas) n'a pas baissé de 1 % en
30 générations (`patience=`). L'arrêt peut finir une recherche qui aurait encore
progressé. Sur le banc de décision lancé avec les réglages par défaut, en cinq
graines, contre la 1.1.0 mesurée à côté (campagne H1 de
`benchmarks/results_1.2/PLAN.md`, sur le candidat avec l'arrêt) : 161 lois
exactes sur 205 contre 163, et 166 contre 167 avec les unités ; avec 10 % de
bruit, la structure dans 83 ajustements contre 85, et 100 contre 99 avec les
unités ; avec 1 % de bruit, un peu moins de lois approchées (146 contre 153) ;
sur les six jeux réels standardisés, un R² de test médian de 0,802 contre 0,809,
et sur les 65 ajustements hors de la plage d'apprentissage des sept jeux réels, 9
effondrements contre 11. L'ajustement
médian sur données bruitées et réelles a pris de 7 à 9 s contre 25 à 35 s. Quand
le résultat compte plus que le temps, fixez `generations=` ou `time_limit=`, ou
`patience=0`.
