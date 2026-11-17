# Caractéristiques techniques et historique

Partie de la documentation de GP_ELITE : retour au [README](../../README.fr.md) ; [English version](../features.md).

## Caractéristiques techniques

- **Plus de graines tolérantes au bruit** (v1.4) : une seconde passe qui pondère
  les lignes par y² et n'exige plus que la cible garde un signe, des balayages du
  logarithme, du sinus et du cosinus sur toute leur bibliothèque, et de
  nouvelles formes jusqu'à douze graines en tout, chaque graine que plaçait la
  1.3 toujours placée avec les constantes de son chercheur ; l'étage tourne
  quand aucune forme binomiale ni aucune fonction d'un monôme ne tient les
  données exactement, avec ou sans bruit
- **L'arc sinus** (v1.3) : `arcsin` dans les jeux `'trig'` et `'full'`, son
  argument ramené dans [−1, 1] et doté d'un facteur constant que l'ajustement
  des constantes règle, et parmi les formes ajustées directement l'arc sinus
  d'un monôme, b·f·arcsin(c·g)
- **Arrêt sur patience** (v1.2) : quand l'appel ne fixe ni `generations` ni
  `time_limit`, la recherche s'arrête dès que son erreur sur les lignes mises de
  côté (sur les lignes d'entraînement s'il n'y en a pas) n'a pas baissé de 1 % en
  30 générations (`patience=`)
- **Exponentielles écrites comme telles** (v1.2) : une puissance d'un nombre
  s'imprime comme une exponentielle, et une exponentielle d'une seule variable
  avec son échelle, `exp(-t / τ)`, chacune gardée seulement si elle passe la
  vérification contre `predict()`
- **Formes ajustées directement** (v1.0) : un monôme multiplié par une puissance
  d'un binôme, b·f·(1 + c·g)^p avec p parmi −1, −½, ½, 1 (lois rationnelles,
  1/√(1 − v²/c²), la racine d'une somme de deux termes), et un monôme multiplié par
  une fonction d'un monôme, b·f·exp(c·g), b·f·log(c·g), b·f·tanh(c·g), b·f/cosh(c·g)
  ou f·(a + β·sin(ω·g) + γ·cos(ω·g)) : chacune est ajustée par une recherche à une
  dimension et des moindres carrés, et placée dans la population de départ
  lorsqu'elle tient à la précision numérique
- **Graines tolérantes au bruit** (v1.0) : quand aucune forme ne tient exactement, la
  loi de puissance et les formes ci-dessus sont recherchées de nouveau avec leurs
  seuils levés, et placées si elles laissent au plus 1,5 % de la variance inexpliquée
- **Lois de puissance amorcées** (v0.8) : quand les données suivent une loi de puissance, le monôme ajusté sur les logarithmes entre dans la population initiale
- **Polissage vers la loi exacte** (v0.8) : les finalistes reçoivent des constantes ajustées jusqu'à convergence et un coefficient par terme de chaque somme ; une variante n'est admise que si elle est exacte
- **Constantes ajustées pour la forme jugée** (v0.8) : Levenberg–Marquardt en projection variable (l'échelle et le décalage de la mise à l'échelle linéaire résolus dans le résidu)
- **Données de toute échelle** (v0.8) : une cible de n'importe quel ordre de grandeur est divisée en interne par une puissance de dix, et la normalisation par défaut divise chaque colonne par sa plus grande valeur absolue
- **Formule dans vos variables, vérifiée** (v0.7) : la mise à l'échelle interne est repliée dans les constantes ; `formula_exact` indique si la formule reproduit `predict()` sur les données d'entraînement
- **Budget de temps** (v0.7) : `time_limit=` arrête proprement et rend le meilleur modèle trouvé ; avec `units=`, le départ typé le respecte aussi depuis la v1.2
- **Déduction de la constante mystère** (v0.5) : la constante de tête peut porter une dimension, inférée par homogénéité ; unités et valeur brute exposées sur l'estimateur, la valeur lue sur les prédictions quand le modèle est un monôme (v1.0)
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


## Nouveautés

**1.4** — plus de graines tolérantes au bruit : sur les 41 équations de Feynman du
banc de décision avec un bruit gaussien sur la cible, la structure de la loi
revient dans 152 et 95 ajustements sur 205 (1 % et 10 % de bruit) contre 116 et 87
pour la 1.3 mesurée à côté, et dans 150 et 93 avec les unités contre 121 et 95 ;
sans bruit, les lois exactes de la 1.3, 171 et 174 avec les unités. Trois autres
changements ont été mesurés et non adoptés. **1.3 « Arc »** — l'arc sinus, dans les jeux `trig` et `full` : sur les 41 équations
de Feynman du banc de décision, ses deux lois à arc sinus reviennent exactes
dans 8 ajustements sur 10, avec et sans unités, là où la 1.2 n'en avait aucune.
Cela fait 171 lois exactes sur 205 contre 163, et 174 contre 166 avec les
unités. Le jeu `physical`, celui par défaut, reste tel qu'il était : avec lui,
les modèles de la 1.2 à travail égal. **1.2 « Classroom »** — avec les réglages par défaut, un ajustement s'arrête dès qu'il ne
progresse plus (`patience=`) : les six lois du notebook de TP en 48 s, contre 194
à 198 s pour la 1.1.0 sur la même machine, avec les mêmes formules ; une
exponentielle revient écrite comme telle, `exp(-t / τ)`, sans changer le modèle ;
avec `units=`, Feynman III.19.51 sans bruit se termine en une seconde environ, là où la
1.1.0 prenait environ six minutes avec un budget de 30 s. Avec un budget fixé,
les modèles de la 1.1 à travail égal, sauf ceux dont la correction change le départ
typé avec `units=` (III.19.51 sur le banc) : sur les 2 780 ajustements de la mesure
de sortie, aucun ne change de statut. **1.1 « Coherent »** — les formes que la 1.0 ajuste directement agissent aussi avec `units=`,
chacune placée seulement si elle passe la porte des dimensions : sur les 41
équations de Feynman du banc de décision avec leurs unités, 165 lois exactes sur
205 contre 108 pour la 1.0 mesurée à côté ; chacun des 1 005 modèles rendus avec
unités dans la mesure de la version (ces équations avec et sans bruit, et le jeu
de test figé) a passé l'audit des unités ; sans unités, les modèles de la 1.0 à
travail égal.
**1.0 « Families »** — des familles entières de lois ajustées directement (formes
rationnelles, racines, exponentielles, logarithmes, sinus et cosinus d'un monôme),
sur des données bruitées aussi : sur les 41 équations de Feynman du banc de
décision, 163 lois exactes sur 205 contre 88 pour la 0.9 mesurée à côté, et sur
78 autres équations de Feynman figées avant le travail, 213 sur 390 contre 145
(sur les 14 systèmes de Strogatz figés avec elles, 7 sur 70 contre 8) ; sur
données réelles, le même R² médian à 0,004 près et le même nombre d'effondrements
hors de la plage d'apprentissage ; trois études de cas sur données publiques et une page de ce
que le moteur ne fait pas. **0.9 « Steady »** — la recherche avec `units=` plus rapide, pour les mêmes
modèles (plus de cinq fois sur Feynman II.11.3) ; une formule qui s'écarte du
modèle nomme les formules exactes du front de Pareto ; un jeu de test figé avant
toute décision et jamais utilisé pour en prendre une, sur lequel chaque version
publiée est mesurée. **0.8 « Swift »** — plus rapide (les accélérations seules rendent les mêmes
modèles), davantage de lois retrouvées (lois de puissance amorcées, structures
justes menées jusqu'à la loi exacte), des données de toute échelle, des entrées
vérifiées ; chaque changement destiné à améliorer la recherche décidé par une
comparaison écrite avant de la lancer. **0.7 « Sound »** — la formule que vous obtenez est le modèle obtenu : écrite dans
vos variables pour toute normalisation et vérifiée à l'ajustement ; un budget
`time_limit=` ; des garanties dimensionnelles rendues strictes ; chaque chiffre de
son README re-mesuré sur son code final. **0.6 « Bench »** — les unités
physiques dans la console. **0.5 « Unknown »** — unités *et* valeur de la
constante manquante d'une loi. **0.4 « Lawful »** — recherche sous contrainte
dimensionnelle. **0.3 « Trust »** — diagnostics et stabilité.

Historique complet, avec les mesures qui étayent chaque affirmation, dans
[CHANGELOG.md](../../CHANGELOG.md). Chaque banc derrière un chiffre de cette page se
trouve dans [`benchmarks/`](../../benchmarks/), avec ses résultats bruts.
