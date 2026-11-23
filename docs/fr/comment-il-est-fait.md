# Comment GP_ELITE est fait

Partie de la documentation de GP_ELITE : retour au [README](../../README.fr.md) ; [English version](../how-it-is-made.md).

GP_ELITE est développé avec un assistant d'IA, Claude (Anthropic), depuis mai
2026, dans plusieurs versions successives. L'auteur, Sabri Hakou, décide ;
l'assistant écrit le code et les documents, et lance les mesures. Cette page
dit qui fait quoi, et comment le vérifier vous-même.

## Avant l'assistant

Le projet est né sans IA. La représentation des expressions et la génération
des arbres, les opérateurs protégés, le modèle d'îles asymétrique, l'ajustement
des constantes par Adam, l'amorçage, la console interactive et la suite de
problèmes de test sont l'œuvre de l'auteur. Ils sont toujours dans le moteur,
modifiés depuis.

## Qui fait quoi

L'auteur décide :

- les pistes à essayer : il valide le plan de la version suivante avant toute
  mesure (pour la 1.4, le 11 novembre 2026) ;
- si une version sort, son nom et sa date (la 1.4.0 « Signal », le 23 novembre
  2026) ;
- ce qui entre dans `main` : il fusionne lui-même chaque demande de fusion
  (pull request) ;
- la publication : il envoie lui-même les fichiers sur PyPI ; pour la 1.4.0,
  après avoir vérifié leur empreinte SHA-256.

L'assistant exécute :

- il propose des pistes et écrit les plans ;
- il écrit le code, les tests, les scripts de mesure, la documentation et
  l'article ;
- il lance les mesures, rédige les comptes rendus et signale à l'auteur tout
  écart au plan.

L'assistant n'écrit jamais directement dans `main` et n'a pas accès au compte
PyPI.

## Ce que montre l'historique

Au 23 novembre 2026 :

- Depuis le 27 septembre 2026, chaque commit écrit avec l'assistant porte la
  ligne `Co-Authored-By: Claude`. C'est le cas de 481 des 547 commits de
  `main`.
- Aucun de ces commits n'a été écrit directement dans `main`. Tous y sont
  entrés par l'une des onze demandes de fusion que l'auteur a fusionnées, du
  5 octobre au 23 novembre 2026.
- Avant le 27 septembre, l'auteur déposait lui-même les fichiers, et
  l'historique ne distingue pas ce qui venait de l'assistant.

## Comment c'est contrôlé

- **Le plan avant la mesure.** Depuis la 0.8, l'hypothèse et les critères d'un
  changement de la recherche sont enregistrés avant sa première mesure ;
  l'historique git montre l'ordre.
- **Les résultats publiés, quels qu'ils soient.** Pour la 1.4, quatre
  changements ont été mesurés ; trois n'ont pas été adoptés, et leurs résultats
  sont publiés quand même
  ([`benchmarks/results_1.4/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks/results_1.4)).
- **Des jeux de test gelés.** Depuis la 0.9, chaque version est aussi mesurée
  sur des jeux fixés avant toute décision, qui ne servent jamais à en prendre
  une.
- **Deux relectures indépendantes avant chaque version, depuis la 0.9.** Ce sont
  deux autres sessions de l'assistant, qui n'ont pas vu le travail. Elles
  vérifient les affirmations des documents contre les
  enregistrements et le code. Pour la 1.4.0, elles ont relevé 26 points, tous
  corrigés ou répondus
  ([première](https://github.com/ariel95500-create/gp-elite/blob/main/benchmarks/results_1.4/release/M5_review1.md),
  [seconde](https://github.com/ariel95500-create/gp-elite/blob/main/benchmarks/results_1.4/release/M5_review2.md)).

Le détail de la méthode est dans [Comment GP_ELITE est mesuré](mesures.md).

## Pourquoi le dire

Un code écrit avec une IA inspire de la méfiance, et c'est légitime. Le dire,
et montrer comment c'est contrôlé, vaut mieux que le taire. Rien ici ne demande
à être cru : chaque chiffre renvoie à ses enregistrements et aux scripts qui
les refont, et les limites sont écrites
([ce que GP_ELITE ne fait pas](../../LIMITATIONS.fr.md)).

L'article le dit aussi, dans sa section « AI usage disclosure »
([`paper/paper.md`](https://github.com/ariel95500-create/gp-elite/blob/main/paper/paper.md)) :
les affirmations scientifiques, leurs limites et la responsabilité de
l'ensemble sont celles de l'auteur.

Si GP_ELITE échoue sur vos données,
[dites-le](https://github.com/ariel95500-create/gp-elite/issues/new/choose) :
c'est une information utile.
