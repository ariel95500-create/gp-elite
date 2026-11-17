# Comment GP_ELITE est mesuré

Partie de la documentation de GP_ELITE : retour au [README](../../README.fr.md) ; [English version](../measurements.md).

## La taille des données

Sur cinq équations de Feynman (sans normalisation), le modèle rendu retrouve la loi exacte de quatre d'entre elles à chaque taille de 25 à 10 000 points, à chaque run ; la cinquième, la forme rationnelle imbriquée I.16.6, revient exacte à partir de 1 000 points (à 5 000 sous une autre forme que celle du manuel), et dans 6 des 13 runs en dessous (à 200 points une fois sous une telle forme). Les cinq ajustements prennent 40 s au total à 1 000 points et 100 s à 10 000 sur un cœur de notre machine à 4 cœurs (`benchmarks/feynman_scaling.py`, version 1.4.0 ; les temps dépendent de la machine).


## Est-ce solide ?

Question légitime pour un projet dont vous n'avez jamais entendu parler. Voici
ce que ça vaut face aux alternatives, et ce que ça ne vaut pas.

| | GP_ELITE | Réseaux de neurones | PySR (état de l'art) |
|---|---|---|---|
| Sortie | **formule lisible** | boîte noire | formule lisible |
| Installation | `pip install` (pur Python) | lourde | nécessite **Julia** |
| Validation hors échantillon | **intégrée** dès 30 lignes (sert à choisir le modèle) | à faire soi-même | à faire soi-même |
| Unités physiques | **contrainte dure pendant la recherche** (`units=`) | non | pénalité douce (`X_units=`) |
| Stabilité de la réponse | **rapport bootstrap** (`stability_analysis`) | non | non |
| Vitesse et précision à grande échelle | moindres | — | **supérieures** |

La dernière ligne n'est pas une mesure de ce projet : c'est une concession, tirée
des résultats publiés des moteurs compilés.

**Comment les changements sont décidés.** Depuis la 0.8, un changement destiné à
améliorer la recherche ou la sélection finale n'entre dans le comportement par
défaut que s'il passe une comparaison écrite d'avance : l'hypothèse et les
critères de décision sont enregistrés avant la première mesure
([`benchmarks/results_0.8/PLAN.md`](https://github.com/ariel95500-create/gp-elite/blob/main/benchmarks/results_0.8/PLAN.md) ;
le plan de la première campagne a été enregistré six minutes après le début de
son premier ajustement), le moteur avec le changement est comparé au moteur sans
lui sur 41 équations de Feynman et sur des jeux de données réels (six
standardisés, sept dans leurs propres unités), 30 secondes par ajustement, un
processus par ajustement, et les résultats sont publiés quels qu'ils soient
([`RESULTS.md`](https://github.com/ariel95500-create/gp-elite/blob/main/benchmarks/results_0.8/RESULTS.md)),
y compris ceux des changements qui n'ont pas passé. Quand un changement a échoué
et qu'une version restreinte en a ensuite été testée, la restriction a été conçue
après avoir vu l'échec et mesurée sur les mêmes problèmes ; `RESULTS.md` dit où.
Les corrections de défauts ne sont pas décidées ainsi ; les fichiers de
`benchmarks/results_0.8/` montrent ce qu'elles changent. Les changements de la
1.0 ont été décidés de la même façon
([`benchmarks/results_0.9/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks/results_0.9),
`PLAN_PHASE4.md` et `PLAN_PHASE5.md`), et depuis la 0.9 chaque version est aussi
mesurée une fois sur un jeu de test figé avant toute décision et jamais utilisé
pour en prendre une : 78 autres équations de Feynman, 14 systèmes de Strogatz et
25 jeux de données réels. Sur ses équations de Feynman, la 1.0 retrouve 213 lois
exactes sur 390, contre 145 pour la 0.9 mesurée à côté ; sur ses systèmes de
Strogatz, 7 ajustements exacts sur 70 contre 8 ; sur ses jeux réels, le même R²
médian à 0,004 près et le même nombre d'effondrements hors de la plage
d'apprentissage
([`release_1.0/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks/results_0.9/release_1.0)).
Le changement de la 1.1 a été décidé de la même façon
([`benchmarks/results_1.1/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks/results_1.1)).
Mesurées côte à côte pour la sortie de la 1.1, les deux versions donnent sans
unités les mêmes comptes de lois exactes sur le jeu figé (213 lois exactes sur 390 sur ses
équations de Feynman, 8 sur 70 sur ses systèmes de Strogatz : sous un budget de
temps, les comptes bougent un peu d'une campagne à l'autre), et avec leurs unités
la 1.1 retrouve 226 lois exactes sur 390 contre 169. Les changements de la 1.2 ont
été décidés de la même façon
([`benchmarks/results_1.2/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks/results_1.2)) ;
mesurées côte à côte pour la sortie de la 1.2, les deux versions donnent les mêmes
comptes sur le jeu figé, avec et sans unités (214 lois exactes sur 390 sur ses
équations de Feynman, 10 sur 70 sur ses systèmes de Strogatz, et 229 sur 390 avec
les unités). Le changement de la 1.3 a été décidé de la même façon
([`benchmarks/results_1.3/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks/results_1.3)).
Mesurée à côté de la 1.2 pour la sortie de la 1.3, sur le jeu figé, la 1.3
retrouve 214 lois exactes sur 390 sur ses équations de Feynman contre 213, 8 sur
70 sur ses systèmes de Strogatz avec les deux versions, et 228 sur 390 avec les
unités contre 229. Les 213 et 8 de la 1.2 dans cette campagne, contre 214 et 10
lors de sa propre sortie, viennent du budget de temps, qui fait bouger les comptes
d'une campagne à l'autre. Le changement de la 1.4 a été décidé de la même façon
([`benchmarks/results_1.4/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks/results_1.4)),
où trois des quatre changements mesurés n'ont pas été adoptés. Mesurées côte à
côte pour la sortie de la 1.4, sur le jeu figé, les deux versions retrouvent 214
lois exactes sur 390 sur ses équations de Feynman et 228 avec les unités, et la
1.4 a 10 ajustements exacts sur 70 sur ses systèmes de Strogatz contre 9. Avant
tout changement de la 1.4, ses équations de Feynman ont aussi été figées avec
1 % et 10 % de bruit sur leur cible : la 1.4 y retrouve la structure de la loi
dans 37 et 28 ajustements sur 78 contre 34 et 27, et avec les unités dans 37 et
33 contre 35 et 32.

La niche de GP_ELITE : **zéro barrière d'entrée**. Un ingénieur de labo, un étudiant ou un technicien pointe un fichier CSV et reçoit une loi validée, sans devenir développeur. `PySR` et `Operon` sont plus rapides et plus précis sur les problèmes grands ou difficiles ; GP_ELITE ne prétend pas le contraire.


## Sur quoi GP_ELITE est-il bon (et moins bon) ?

**Bon** : lois physiques / d'ingénierie à structure multiplicative ou exponentielle, données expérimentales de taille modeste, problèmes où l'interprétabilité prime.

Sur le **banc Feynman gelé** (15 équations de physique, `restarts=4`, une seed), jugé
sur le modèle qu'il rend : **15/15 récupérations symboliques exactes** (1−R² < 1e-9
sur des données tenues à l'écart), contre 12/15 pour la 0.9 ; les trois qu'il ajoute
sont I.16.6 (addition relativiste des vitesses, une forme rationnelle imbriquée qui
ne fait pas partie des formes que la 1.0 ajuste directement, atteinte par la
recherche) et deux lois avec un sinus ou un cosinus, I.18.12 (r·F·sin θ) et
III.15.12, que la 1.0 ajuste directement. Face-à-face contre **gplearn** sur les mêmes données et
découpages (population 2000 × 30 générations), chaque méthode jugée sur le modèle
qu'elle rend : **15/15 contre 6/15** exactes, 15/15 contre 7/15 sous 1e-3 — GP_ELITE
devant sur 9 équations et à égalité sur 6. Jusqu'à la 0.9, une loi avec un angle dans
un sinus ou un cosinus demandait `normalize='none'`, car diviser un angle par sa plus
grande valeur change la période que le sinus doit retrouver (mesuré pour la 0.9 sur
les dix lois trigonométriques du banc de 41 équations, cinq seeds chacune : 13
ajustements exacts sur 50, contre 2 sur 50 avec le réglage par défaut ; sur données
réelles, laisser telles quelles les colonnes d'échelles proches,
`normalize='smart'`, a moins bien prédit hors de la plage d'apprentissage,
[`benchmarks/results_0.9/PLAN_TRIG.md`](https://github.com/ariel95500-create/gp-elite/blob/main/benchmarks/results_0.9/PLAN_TRIG.md)) ;
avec la 1.0, le réglage par défaut rend les trois lois de cette vitrine qui en ont
un, et `normalize='none'` reste à essayer quand une telle loi ne revient pas. Avec
les unités physiques déclarées (`units=`, même budget, sans normalisation), 15/15
reviennent exactes (`benchmarks/feynman_units.py`), 14 sous leur forme de manuel ;
I.16.6, manquée jusqu'à la 1.0, revient avec un facteur 1,00755 en haut et en bas (1,00758 avec la 1.3)
qui se simplifie. Une seed sur quinze équations est une
vitrine, pas une comparaison statistique :
[`benchmarks/results_0.8/RESULTS.md`](https://github.com/ariel95500-create/gp-elite/blob/main/benchmarks/results_0.8/RESULTS.md)
mesure la 0.7.0 et chaque changement de la recherche et de la sélection finale
de la 0.8 sur 41 équations et cinq seeds à 30 s par ajustement, et la 0.7.0
contre la 0.8.0 côte à côte, à travail égal, sur ces quinze équations avec cinq
seeds et sur six jeux de données réels.
Reproduire : `python benchmarks/feynman_bench.py 0 15` et `python benchmarks/duel.py`.

**Moins bon** : suites chaotiques (ex. temps de vol de Collatz — composante intrinsèquement aléatoire), >15-20 variables (l'espace de recherche explose — même si `units=` le réduit nettement quand les unités physiques sont connues), gros jeux de données où la précision pure prime sur l'interprétabilité (les modèles d'ensemble dominent alors).
