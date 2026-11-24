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

La version 1.4 donne plus de formes aux graines tolérantes au bruit. Là où ces
graines sont les mêmes dans les deux versions et où aucune n'atteint son budget
de temps, la formule enregistrée (ses 160 premiers caractères), l'erreur sur
les lignes de test et `formula_exact` sont ceux de la 1.3.0, au bit près (782
ajustements de la mesure de sortie). Mesurée à côté de la 1.3.0 pour la sortie de la 1.4
(`benchmarks/results_1.4/release/`, les chiffres dans `m2/limits_figures.txt`),
la 1.4.0 donne :
- 152 et 95 structures sous bruit contre 116 et 87 (point 3) ;
- sur le jeu de test, 31 de ses équations jamais retrouvées contre 33, 203 et
  11 lois exactes sur ses parties principale et bonus contre 204 et 10 (214 sur
  390 avec les deux), et 10 ajustements de Strogatz exacts sur 70 contre 9. Les
  ajustements qui y changent de statut sont, à un près, des ajustements où la
  1.4.0 place d'autres graines.

Ailleurs, les deux versions donnent les mêmes chiffres, ou des chiffres qui
bougent comme d'une campagne à l'autre. Les chiffres de la 1.4.0 viennent en
premier :
- 171 lois exactes sur 205 sur le banc de décision avec les deux, et les mêmes
  cinq équations jamais retrouvées ; avec les unités, 174 avec les deux, et
  quatre équations jamais retrouvées ;
- 10 effondrements sur 65 avec les deux (le pire à −1 946), et 66 sur 250 sur
  le jeu de test avec les deux (38 standardisés, 28 dans leurs propres
  unités) ;
- 11 formules qui s'écartent sur 130 contre 12, et 65 sur 500 contre 68.

La version 1.5 ne change que l'organisation du code : à graine égale et
travail égal, elle rend les modèles de la 1.4.0, au bit près
(`benchmarks/results_1.5/split/`), et les chiffres de la 1.4.0 valent donc pour
elle. Le point 9 ajoute ce que l'étude de taille de la 1.5 a mesuré sur la
1.4.0.

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
jamais retrouvées. Deux choses que l'arc sinus ne règle pas :
- **un arc sinus dont l'argument n'est pas un monôme,** comme le n·sin θ de
  `I.26.2`. Aucune graine ne le contient, donc la recherche doit le
  construire : à 30 s, elle l'a fait dans 3 ajustements sur 5 aux graines 0 à
  4, et dans 2 sur 5 aux graines 5 à 9 ;
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
bruit et 85 avec 10 % (0.9.0 : 67 et 66), et avec la 1.4.0 dans 152 et 95 (la
1.3.0 mesurée à côté : 116 et 87). Les constantes de la formule rendue
portent le bruit : avec 1 % de bruit,
`0.00115247 + 1.00099 * v0 / (1 - 0.997137 * v1 / v2)` pour v0/(1 − v1/v2)
(Feynman I.34.1). Au-delà de 10 %, le moteur n'a
pas été mesuré.

Depuis la 1.4, les graines tolérantes au bruit portent plus de formes. Deux
choses qu'elles ne règlent pas :
- **à 10 % de bruit, deux équations perdent des ajustements qui ont la
  structure de la loi :** I.27.6 passe de 2 ajustements sur 5 à aucun sans les
  unités et de 5 à 1 avec elles, III.15.12 de 5 à 2 et de 5 à 1. Dans ces vingt
  ajustements, la 1.4.0 place d'autres graines (une là où la 1.3.0 n'en plaçait
  aucune sur I.27.6, trois contre une sur III.15.12), et la campagne N2b donnait
  les mêmes nombres : la cause probable, non examinée ;
- **sur quelques points bruités, une graine qui a la structure de la loi ne
  suffit pas à ce que la recherche la garde.** Sur le diagnostic des TP (10 ou
  20 points avec 2 % ou 5 % de bruit), la source ponctuelle a la loi sans les
  unités dans 14 ajustements sur 20 contre 18 avec la 1.3.0 (avec les unités,
  20 sur 20 avec les deux). Les graines que la 1.4 y ajoute,
  des formes en 1/d² avec une petite correction, déplacent la recherche, qui
  finit dans 4 ajustements sur une forme qui suit le bruit de plus près
  (`benchmarks/results_1.4/n2b/campaign/examine/`). Les deux changements de la
  1.4 prévus pour ces tableaux n'ont pas été adoptés (point 11).

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
(`benchmarks/results_0.9/release_1.0/m3/kepler_minmax_check.txt`). Le contrôle utilise le jeu `full` ;
avec son arc sinus, la 1.3.0 donne 2 sur 10 au lieu de 4
(`benchmarks/results_1.3/release/m3/kepler_minmax_check.txt`), et la 1.4.0 de
même (`benchmarks/results_1.4/release/m3/kepler_minmax_check.txt`). Avec la
normalisation par défaut, sur le
banc, aucune loi n'a été perdue ainsi : aucune équation n'a moins d'ajustements
exacts qu'avec la 0.9.0. `PLAN_PHASE5.md`, mécanique de N1.

Depuis la 1.4, l'étage tolérant au bruit place aussi plus de formes sur des
données exactes, là où aucune graine exacte ne les couvre. Parmi les chiffres
publics mesurés de nouveau pour la sortie de la 1.4.0 (M3), un y perd sa loi : sur les 3 000 lignes de
x0·x1/x2 + 0,3·x3 de `benchmarks/time_limit_check.py`, l'étage place 4 graines
contre 1, et en séquentiel la 1.4.0 va jusqu'à son budget de 15 s et rend une
approximation de R² 0,9979, là où la 1.3.0 rendait la loi en 6,3 s. Trois en
sortent mieux : Feynman I.16.6 sur le banc de taille, exacte dans 10
ajustements sur 17 contre 9 ; un cas du contrôle de robustesse dont l'entrée va
de 1e-3 à 1e6, qui rend sa loi là où la 1.3.0 rendait une approximation ; et
une exponentielle du contrôle des petits jeux, écrite comme la loi là où la
1.3.0 en écrivait des formes plus longues
(`benchmarks/results_1.4/release/m3_examine/`). Sur le jeu de test figé de la
mesure de sortie, sans les unités, 4 ajustements perdent leur loi exacte (2 de
TF78, 2 des systèmes de Strogatz) et 6 en gagnent une (2 et 4, dont une sur les
lignes hors du domaine), tous là où la 1.4.0 place d'autres graines.

## 6. Une formule qui s'écarte de ses prédictions

Des opérations protégées (une division par presque zéro, une puissance plafonnée
à un million) gardent les prédictions finies ; quand l'une d'elles agit sur vos
données, la formule imprimée s'écarte de `predict()`. Le moteur le dit alors
(`formula_exact` vaut False, avec un avertissement qui nomme les formules exactes
du front de Pareto). Sur les données réelles, c'est arrivé dans 7 ajustements sur
130 sur le banc et 61 sur 500 sur le jeu de test.

Depuis la 1.3, l'arc sinus est l'une de ces protections : dans le modèle, son
argument est ramené dans [−1, 1], et dans la formule imprimée il ne l'est pas.
Dans le jeu `trig`, dans la mesure de sortie de la 1.3, la formule s'écarte
dans 82 ajustements sur 530, contre 27 pour la 1.2.0. Au moins 47 des 82 ont
un arc sinus (les fiches gardent les 160 premiers caractères d'une formule).
Combien s'écartent parce que la protection agit, les fiches ne le disent pas.
La recherche peut se servir de cette protection : là où
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
quelques milliers de lignes et jusqu'à une dizaine de variables. L'étude de
taille de la 1.5 a mesuré la 1.4.0 au-delà (`benchmarks/results_1.5/size/`),
sur les 41 équations de Feynman du banc de décision sans bruit, cinq graines,
30 s par ajustement :
- **les lignes :** 165 lois exactes sur 205 à 100 lignes, 168 à 1 000, 161 à
  10 000 et 154 à 100 000. Les graines trouvent les mêmes lois à chaque taille ;
  la recherche perd les autres : les ajustements qui vont jusqu'à leur budget
  atteignent une médiane de 3 générations à 100 000 lignes, contre 116 à 100.
  Dix fois plus de temps en rend 6 sur 11.
- **les variables qui ne jouent aucun rôle dans la loi :** avec 5, 10 et 20
  ajoutées à 1 000 lignes, 144, 139 et 108 lois exactes contre 168, et dix fois
  plus de temps en rend 12 sur 60. Les chercheurs de graines limitent leurs
  combinaisons de colonnes quand les colonnes augmentent, et perdent un tiers de
  leurs lois avec 20 ajoutées ; 26 formules rendues utilisent une variable
  ajoutée.

Au-delà de ces tailles, rien n'est mesuré. Il n'est pas fait pour les suites
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

## 11. Ce que la 1.4 a mesuré et laissé de côté

Trois changements ont été mesurés pour la 1.4 et non adoptés
(`benchmarks/results_1.4/PLAN.md`). Leur code reste dans le moteur, éteint :
- **une validation croisée sur les tableaux de moins de 30 lignes (S1).** Elle
  choisissait des structures que la recherche avait trouvées sur les mêmes
  quelques points, dont elle sous-estimait l'erreur : sur le bras sans unités
  du diagnostic des TP, la loi revenait dans 113 ajustements sur 200 contre
  126, et l'ajustement médian prenait 1,67 fois plus de temps ;
- **une graine pour une constante plus une exponentielle (E2),** comme dans le
  refroidissement de Newton. La graine avait la structure de la loi dans 18
  ajustements sur 20, mais dans 11 d'entre eux la recherche rendait une autre
  forme, plus proche du bruit : la loi revenait dans 7 ajustements sur 20 contre
  3. Sa forme, proche de beaucoup de lois sur quelques points bruités, éloignait
  aussi la recherche de la source ponctuelle (18 ajustements sur 20 à 15) ;
- **l'ajustement des constantes de chaque candidat tolérant au bruit,** une
  partie de la première version du changement de la 1.4. Il faisait perdre des
  lois exactes sans bruit (I.26.2 passait de trois ajustements exacts sur cinq
  à aucun).

S1 et E2 sont reportés à la version suivante : tous deux butent sur la même
cause, le choix final parmi les formes de la recherche sur quelques points
bruités.

## 12. Les tableaux des résultats d'enseignement sont simulés

Tous les résultats sur l'enseignement viennent de tableaux simulés : le
diagnostic des TP, son jeu figé TPT10 et le jeu figé bruité TF78N tirent un
bruit gaussien sur des lois exactes, comme le banc de décision le fait avec les
équations de Feynman. Aucun tableau mesuré par des élèves n'a pu être réuni pour
la 1.4.
