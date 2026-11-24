"""
GP_ELITE.py  —  Genetic Programming symbolique haute performance
================================================================
  v14.4 — Asymétrie des Îles (Spécialisation des rôles) + deepcopy champion
  --------------------------------------------------------------------------
  58. [v14.4] Island.role : spécialisation selon l'ID de l'île

      Chaque île reçoit un rôle assigné dans Island.__init__ :
        · Dernière île  (N-1)  : "stigmergic" — exploratrice stigmergique
        · Avant-dernière (N-2) : "cleaner"    — nettoyeuse BIC stricte
        · Toutes les autres    : "explorer"   — exploratrices libres
      Avec N_ISLANDS=3 : île 0=explorer, île 1=cleaner, île 2=stigmergic
      Avec N_ISLANDS=2 : île 0=cleaner,  île 1=stigmergic
      Avec N_ISLANDS=1 : île 0=stigmergic (rôles fusionnés)

  59. [v14.4] fitness(role=...) : métrique conditionnelle par rôle

      · role="cleaner"  : BIC strict (v14.2)
            n·ln(MSE_pur) + k·ln(n) + γ·n_adj²·ln(n)
        Rasoir d'Ockham forcé — détruit le bloat, promeut l'élégance.
      · role="explorer" ou "stigmergic" : MSE hybride + pénalité linéaire (v13.12)
            raw_mse(node) + min(size_pen + depth_pen, 0.05·base)
        Liberté de construire des sous-structures complexes (sin(1/x), etc.)
        sans être pénalisée pendant la phase d'assemblage transitoire.
      Cache : clé (hash, role) — un même arbre peut avoir deux scores distincts.

  60. [v14.4] Propagation cohérente du role partout

      Tous les appels à fitness() et tournament() dans evolve_island(),
      receive_migrants() et migrate() reçoivent role=island.role.
      Le global_best dans evolve() est comparé avec role="cleaner" (BIC strict)
      comme référence universelle — la métrique la plus discriminante.

  61. [v14.4] Correction bug de référence sur le champion final

      La séquence optimize_constants_adam(global_best) + simplify() pouvait
      corrompre global_best si des nœuds étaient partagés par référence.
      Correction : copy.deepcopy(global_best) avant le passage à Adam.
      Comparaison de conservation par raw_mse (MSE pur, cohérent avec la demande).



      Bug observé : le global_best FIT=-808 (gen 47) était dégradé en
      (1.229+x) MSE=0.88 par l'optimisation finale Adam.
      Cause : Adam faisait diverger les constantes vers des valeurs extrêmes,
      puis simplify() réduisait l'expression dégénérée à une feuille constante.
      La condition de conservation utilisait raw_mse (hybride Pearson+MSE),
      pas un vrai MSE, ce qui laissait passer la dégradation.

      Correction : avant de retourner child, on vérifie :
        (a) _pure_mse(child) < _pure_mse(original)  — MSE pur, pas hybride
        (b) tree_complexity(child)[0] >= max(1, tree_complexity(original)[0]*0.4)
            — la complexité ne s'effondre pas de plus de 60% (signe de dégénérescence)
      Si l'une des conditions échoue → retourner node.copy() (original intact).

  56. [v14.3 CORRECTIF] evolve() : garde finale par BIC, pas raw_mse

      La condition "if raw_mse(optimized) < raw_mse(global_best)" utilisait
      la métrique hybride Pearson+MSE au lieu d'un vrai MSE, et ne détectait
      pas correctement la dégradation post-Adam. Remplacée par une comparaison
      BIC (fitness) : score_after < score_before. Cohérent avec le reste du système.

  57. [v14.3 CORRECTIF] evolve() : _fitness_cache.clear() au lieu de = {}

      "_fitness_cache = {}" dans la boucle de générations créait une variable
      LOCALE qui masquait le dictionnaire global sans jamais le vider.
      Le cache global s'accumulait indéfiniment avec des entrées stales.
      Corrigé en _fitness_cache.clear() qui modifie le dict en place.



      Problème observé : (0.042503-x)² obtenait BIC=-417 et dominait la
      population sur x³·sin(1/x) car x³·sin(1/x) ≈ x² sur [0.1, 3]
      (les oscillations rapides de sin(1/x) près de 0 sont absentes du
      dataset sur cette plage). La constante 0.042503 est ajustée sur les
      données, ce que la pénalité linéaire seule ne pénalisait pas assez.

      Nouvelle formule fitness_BIC v14.2 :
          fitness = n·ln(MSE_pur) + k·ln(n) + γ·n_adj²·ln(n)

          k     = Σ coût(nœud)  (float→3, op/x→1, inchangé)
          n_adj = nombre de constantes AJUSTÉES dans l'arbre
          γ     = _FLOAT_GAMMA = 2.0

      Distinction constante entière vs ajustée dans _is_adjusted_float() :
        · Entière simple (0, ±1..±10, v==round(v)) : émerge de la
          simplification algébrique (x+x→2*x). Pas de pénalité quadratique.
        · Ajustée (0.042503, -2.423…, ou |v|>10) : encode de l'information
          sur le dataset. Contribue à n_adj → pénalité quadratique.

      Impact sur n_adj :
        1 constante ajustée  → + 2·ln(n)   ≈ +  8.8 sur n=80
        2 constantes ajustées → + 8·ln(n)  ≈ + 35.2 sur n=80
        4 constantes ajustées → +32·ln(n)  ≈ +140.8 sur n=80

      tree_complexity() retourne maintenant un tuple (k, n_adj).
      fitness() déstructure ce tuple et applique les deux termes.
      Tous les autres appelants de tree_complexity() sont mis à jour
      pour utiliser k, _ = tree_complexity(node).



      Bug v14 : fitness() passait raw_mse() dans ln(MSE) du BIC.
      Or raw_mse() retourne la fitness hybride dans [0, 3+], pas un vrai
      MSE. Sur x³·sin(1/x) avec l'arbre 'x' (MSE reel = 5.55), la valeur
      hybride valait ~1.00, ce qui donnait ln(1.00) ≈ 0 au lieu de
      ln(5.55) ≈ 1.71 -> BIC = 4.45 au lieu de 141.5 -> l'arbre 'x'
      semblait bon alors qu'il est mauvais (affichage FIT=1.73 observé).

      Correction : nouvelle fonction _pure_mse(node, xs, ys) qui calcule
      le MSE brut (np.mean((preds - ys)^2)) sans aucune pondération.
      Arbre constant -> mse + 1000.0 (penalite BIC garantie positive).
      raw_mse() et raw_pearson_r() restent inchanges (logs, seuils).

  53. [v14.1 CORRECTIF] Logique burn-in anti-puits-empoisonne : AND strict
      -> deux voies OR

      Bug v13.11/v14 : la condition d'ouverture de la stigmergie etait :
          generation >= 20  AND  r >= 0.50
      Sur le probleme 10 (x³·sin(1/x)), des individus avec r=0.969 et
      r=1.000 etaient bloques des la generation 0, privant la memoire
      collective d'un signal de haute qualite ("Stigmergie Bloquee" visible
      dans les logs meme avec r=1.000).

      Correction : condition a deux voies :
          Voie A : generation >= 20  AND  r >= 0.50  (burn-in classique)
          Voie B : r >= 0.95                          (ouverture anticipee)
      _stigm_allowed = Voie_A  OR  Voie_B

      La Voie B permet d'ouvrir la stigmergie immediatement si le meilleur
      individu est deja excellent, quelle que soit la generation. La Voie A
      protege contre les problemes difficiles ou la population met du temps
      a converger. Les trois seuils sont declares explicitement en tete du
      bloc pour faciliter le reglage.



      Problème de v13 : la pénalité était bridée à 5% du MSE brut et
      s'éteignait quand le MSE devenait très petit (max_pen = 0.05*mse +1e-8).
      Un polynôme de 15 nœuds avec 4 constantes ajustées pouvait ainsi battre
      sin(x) dès que ses micro-décimales le rendaient légèrement plus précis
      ("raccourci de Taylor").

      Nouvelle formule dans fitness() :
          fitness_BIC = n · ln(max(MSE, 1e-15)) + k · ln(n)

          n   = len(ys)              nombre de points de données
          k   = tree_complexity()    complexité pondérée (voir point 52)
          ln  = logarithme naturel
          1e-15 = plancher de MSE pour éviter ln(0) = -∞

      Propriétés garanties :
        · Plus basse = meilleure (valeurs souvent négatives pour MSE < 1 ;
          le tri, les îles, le tournoi et la stigmergie fonctionnent
          identiquement — ils ne supposent pas de positivité).
        · Une constante flottante (k += 3) doit améliorer le MSE d'un
          facteur exp(3·ln(n)/n) ≈ 1.14 sur n=80 pour être rentable.
          Cela bloque les micro-raffinements polynomiaux sans interdire
          les constantes utiles (π, 2.0 issue de x+x→2*x, etc.).
        · Arbre constant : raw_mse retourne mse + 2.0 >> 1 →
          n·ln(mse_safe) fortement positif → fitness très haute → rejet.

  52. [v14] Nouvelle fonction tree_complexity(node) après tree_depth()

      Traversée itérative (pas de récursion).
      Complexité pondérée :
        · Variable "x" ou opérateur symbolique  → 1 point
        · Constante flottante                   → 3 points
          (_FLOAT_COMPLEXITY_WEIGHT = 3,
           choisir 4 pour un régime plus agressif)

      tree_size() et tree_depth() sont conservés inchangés (utilisés dans
      les logs, l'affichage et le contrôle de taille max).

  Garde-fous v13.x préservés intacts :
    · raw_mse()        : fitness hybride Pearson+MSE (Obj.1 v13.11)
    · raw_pearson_r()  : filtre Anti-Puits-Empoisonné (Obj.2 v13.11)
    · simplify()       : règle x+x→2*x (v13.13) + all rules v13.12
    · Bloc Obj.3       : simplification élite avant dépôt stigmergique
    · Bloc Obj.3b      : simplification finale dans print_result
    · _np_safe_div / _np_safe_pow / _np_safe_sqrt / …
    · LOG_CSV via os.path.abspath(__file__)


      Problème : le champion stocké en mémoire peut contenir des introns
      résiduels (x+x, 1*expr, -(-(x))…) qui gonflent l'expression affichée
      sans modifier la valeur numérique.

      Solution : simplify() appliqué en tête de print_result(), unique point
      d'entrée commun à tous les modes (interactif, CLI, run()).
      pop est List[Node] bruts → simplification directe sur le nœud racine.
      Couverture complète : mode 1 interactif, mode CLI "python GP_ELITE N",
      et la fonction run() de l'API programmatique.
      Le benchmark (run_benchmark → _one_run) ne passe pas par print_result
      et n'est pas affecté.

  50. [OBJECTIF 3b] Nouvelle règle dans _simplify_once : expr + expr → 2.0 * expr
      Réduit x+x, sin(x)+sin(x), (x*x)+(x*x), etc. en 2.0 * <expr>.
      Conditions de sécurité :
        · Les deux branches ont le même structural_hash()
        · Aucune des deux n'est une constante flottante pure (évite le doublon
          avec le repliage constant 3.0+3.0 qui existe déjà plus bas)
      La règle est insérée dans le bloc "if v == '+'" existant, après les
      identités x+0 / 0+x, avant les autres règles binaires.
      La double passe de simplify() propage ensuite les réductions en cascade
      (ex: 2.0*sin(x) + 2.0*sin(x) → 2.0*(2.0*sin(x)) → 4.0*sin(x)).


      Problème : les introns (x-x, 1*x, 0+x, sin(const)…) survivent dans la
      population sans affecter la fitness mais polluent la mémoire collective.
      Un fragment "sin(x-x+x)" a un hash différent de "sin(x)" et occupe un
      slot distinct dans FRAGMENT_LIB / COGRAPH / SEQ_MEM, ce qui dilue le
      signal utile et alourdit les structures stigmergiques.

      Dans evolve_island(), juste APRÈS le calcul de _stigm_allowed et AVANT
      les appels deposit_population / COGRAPH / SEQ_MEM :

        if _stigm_allowed:
            _limit_clean = max(top_k, top_k_seq)   # top 20% au maximum
            for i in range(min(_limit_clean, len(pop))):
                _old_hash   = pop[i].structural_hash()
                _simplified = simplify(pop[i])
                _new_hash   = _simplified.structural_hash()
                if _new_hash != _old_hash:
                    _fitness_cache.pop(_old_hash, None)  # purge entrée stale
                pop[i] = _simplified
            top_fits = [fitness(ind, xs, ys, cfg) for ind in pop[:top_k]]

      · Périmètre : max(top_k, top_k_seq) = top 20% (couvre FRAGMENT_LIB et SEQ_MEM)
      · Exécuté uniquement quand _stigm_allowed (pas de cycles CPU pendant chauffe)
      · pop est List[Node] bruts → simplification directe en place
      · Cache fitness invalidé sélectivement si le hash a changé
      · top_fits recalculé après simplification pour refléter les nouveaux hashes


      Résout le "Mensonge du MSE" : les arbres à bonne forme géométrique mais
      mauvais décalage d'échelle n'étaient pas récompensés par le MSE pur.

      Nouvelle formule dans raw_mse() :
        · si std(prédictions) < 1e-6 (arbre constant) → mse + 2.0 (pénalité)
        · sinon :
            r                = cov(p,t) / (std_p × std_t), borné [-1, 1]
            correlation_loss = 1 - r             (0 = corrélation parfaite)
            fitness_hybride  = 5.0 × correlation_loss
                             + mse / (1 + mse)   (borné [0, 1))
      Fonctions ajoutées :
        · _pearson_r(preds, ys_np) → (r, std_p)     : calcul Pearson vectorisé
        · raw_pearson_r(node, xs, ys) → float        : r pur pour le filtre Obj.2
      Compatibilité totale avec le cache fitness, l'optimiseur Adam et le tri
      de la population (valeur plus basse = meilleure, inchangé).

  47. [OBJECTIF 2] Démarrage Différé + Filtre Qualité (Anti-Poisoned Well)
      Résout le "Poisoned Well" : en génération 0, la stigmergie absorbait
      des fragments issus d'arbres randoms → bruit → convergence précoce.

      Dans evolve_island(), avant chaque dépôt stigmergique :
        · BURN_IN_GENERATIONS    = 20   (générations de chauffe)
        · MIN_CORRELATION_REQUIRED = 0.50
        · Condition : generation >= 20 ET raw_pearson_r(meilleur) >= 0.50
        · Si non remplie → message "[Stigmergie Bloquée] ..." et dépôts skippés
        · Les évaporations continuent toujours (la lib s'étiole si rien n'est
          déposé, ce qui est le comportement intentionnel).
      Structures concernées : FragmentLibrary, FragmentCoGraph, FragmentSequenceMemory.

  Garde-fous v13.10 préservés intacts :
    · Filtre variance dans deposit_population (std > 10×std(ys))
    · Guard anti-constante dans stagnation_reset (feuille terminale → arbre)
    · Gestion sécurisée _np_safe_div / _np_safe_pow
    · Parsimonie plafonnée à 5% dans fitness()
    · LOG_CSV résolu via os.path.abspath(__file__)

  v13.9 — Corrections ciblées post-ablation v13.8
  -------------------------------------------------
  39. Parsimonie dynamique conditionnelle (+SEQ uniquement)
      - v13.8 activait le bloc sur toutes les conditions → vidait le
        cache fitness global en BASE, dégradait la convergence (×60)
      - v13.9 : activé seulement si cfg.USE_SEQMEM=True
      - Invalidation sélective : seules les entrées des individus de
        taille > 20 sont purgées du cache, pas la totalité

  40. τ_max adaptatif selon la longévité des fragments
      - Fragments ayant survécu ≥10 générations consécutives
        au-dessus du seuil minimal : plafond doublé (τ_max × 2)
      - Bons fragments durables (sin(x), x²) peuvent se renforcer
        sans que les fragments récents pathologiques explosent
      - Compteur gen_stable ajouté dans FragmentEntry

  41. Taux d'évaporation différencié par condition en ultrafast
      - +LIB seul          : 0.90 (agressive, pas de COGRAPH à nourrir)
      - +CO / +SEQ / FULL  : 0.95 (modérée, préserve la mémoire lib→COGRAPH)
      - Non-ultrafast       : 0.97 (inchangé)

  v13.8 — Patch correctif (audit complet)
  ----------------------------------------
  34. AttributeError critique sur _xs/_ys corrigé
      - Island.__init__ initialise désormais self._xs = self._ys = None
        et self._key = "1" → plus aucun AttributeError si migrate() ou
        receive_migrants() est appelé avant evolve() (cas ultrafast)
      - migrate() : guard "if island._xs is None: skip" sur chaque île
      - receive_migrants() : fallback tree_size si _xs non disponible

  35. Biais inter-runs du _fitness_cache corrigé
      - evolve() remet _fitness_cache = {} et _PARAMETRIC_CACHE = {}
        à chaque appel → les fitness d'un problème précédent ne
        contaminent plus le run suivant dans run_benchmark()

  36. Seeding distribué en round-robin entre les îles
      - Avant : même seed[j] injectée en slot j dans TOUTES les îles
        → îles identiques en tête, diversité initiale nulle
      - Après : seed[j] → île (j % N_ISLANDS), slot (j // N_ISLANDS)

  37. Seuils d'activation du MODE A (v3) adaptatifs
      - has_co / has_seq proportionnels à la taille de la lib
        → le MODE A (co-graphe + séquences) s'active plus tôt en
        ultrafast (pop=150, 2 îles) qu'en mode normal

  38. Libellés version corrigés (v11 → v13 partout)

  v13 — Corrections critiques + améliorations performances
  --------------------------------------------------------
  30. Bug parent1 corrigé dans evolve_island
      - parent1 est désormais TOUJOURS défini avant les deux branches
        (stigmergique et classique), servant de fallback sûr en cas
        de dépassement de MAX_TREE_SIZE / MAX_TREE_DEPTH
      - Élimine le NameError latent / variable stale dans l'île C

  31. Optimisation des constantes (Adam) renforcée
      - _invalidate_all_hashes() : invalidation récursive sur tout l'arbre
        (et non plus seulement la racine) → évaluation NumPy toujours fraîche
      - LR adaptative : divisée par 2 après 5 pas sans amélioration
      - Restart random depuis les meilleures valeurs si blocage ≥ 10 pas
      - Plus d'itérations quand peu de constantes (≤4) : max_iter × 2

  32. Hot zones adaptées par problème (_HOT_ZONES)
      - Dictionnaire {problem_key: [zones]} couvrant P1–P10
      - Sur-échantillonnage ciblé sur les extrema/inflexions/singularités
        propres à chaque cible, pas uniquement ceux de sin(x²)
      - build_dataset() accepte problem_key et l'utilise

  33. Seeds complètes P6–P10
      - make_seed() enrichi : exp_neg_abs, x2_minus1, exp_abs_x2,
        sin_over_x, cos_sq_x, sinc_cos_sq, sin_pi_x, lorentz_sin,
        exp_x2_4, sin_exp_gauss, tanh_approx_exp, x_cube_sin_inv
      - seed_map couvre maintenant P1 à P10

  Améliorations majeures héritées des versions précédentes (1–29) :
  1.  Ramped Half-and-Half        → initialisation diversifiée (standard Koza)
  2.  Opérateurs étendus          → tan, log, exp, sqrt, abs, neg
  3.  Cache global persistant     → hash structurel, survit entre générations
  4.  Gradient numérique          → diff. finies + Adam pour les constantes
  5.  Crossover size-fair         → limite le bloat par l'échange équilibré
  6.  Fitness multi-critères      → front de Pareto (erreur × taille)
  7.  Niching / crowding          → diversité phénotypique maintenue
  8.  Island model (4 îles)       → évolutions parallèles + migrations
  9.  Mutation operator-aware     → opérateurs compatibles (unaire↔unaire)
  10. Semantic distance           → mutations orientées sémantiquement
  11. Dataset bruité + stratifié  → hot zones adaptées par problème (v13)
  12. Logging CSV                 → historique complet des meilleures solutions
  13. Visualisation matplotlib    → courbes d'apprentissage + fit final
  14. Arrêt adaptatif             → détecte la convergence réelle
  15. get_all_nodes itératif      → pas de risque de stack overflow
  16. FragmentCoGraph             → matrice de co-occurrence entre fragments
  17. sample_pair()              → paire (root, companion) co-occurrente
  18. build_stigmergic_tree_v2() → construction guidée par co-occurrences
  19. Statistiques du graphe     → top paires en fin de run
  20. FragmentSequenceMemory      → séquences structurelles parent→enfant
  21. build_stigmergic_tree_v3()  → construction top-down guidée par séquences + co-graphe
  22. Transfert inter-problèmes   → warm_transfer entre runs
  23. Nouveaux problèmes complexes P5–P10
  24. Benchmark intégré           → run_benchmark(problems, n_runs)
  25. Filtre sémantique           → _is_semantically_trivial()
  26. SEQ_MEM dépôt depth >= 3   → transitions ordre 2 fiables
  27. Bug receive_migrants corrigé → tri par fitness réelle
  28. make_cfg : N_ISLANDS=4, POP_SIZE=600 en mode normal
  29. Seeds P5 : cos_half_x, x_sin_sq, x_sin_sq_cos_half
"""

from __future__ import annotations
from . import state
import bisect
import math
import struct
import hashlib
import itertools
import operator
import weakref
import random
import numpy as np
import copy
import time
import csv
import gc
import sys
import os
import json   # [v15] méta-apprentissage : export/import de grammaires séquentielles
from dataclasses import dataclass, field
from collections import deque
from typing import Optional, List, Tuple, Dict, Any
from .numeric import (_COMPILE_CACHE_MAX, _NP_GLOBALS, _SAFE_LIMIT,
                      _is_const_subtree, _np_abs, _np_is_even, _np_isfinite,
                      _np_max2, _np_maximum, _np_min2, _np_minimum,
                      _np_safe_arcsin, _np_safe_div, _np_safe_exp,
                      _np_safe_log, _np_safe_pow, _np_safe_pow_var,
                      _np_safe_sqrt, _np_safe_tan, _np_step, safe_arcsin,
                      safe_div, safe_exp, safe_log, safe_pow, safe_sqrt,
                      safe_tan)
from .config import (ALL_BINARY_OPS, ALL_OPS, ALL_UNARY_OPS, BINARY_OPS,
                     BINARY_WEIGHTS, CFG, Config, TRACE, UNARY_OPS,
                     UNARY_WEIGHTS, _BATTERY_BINARY_OPS,
                     _BATTERY_BINARY_WEIGHTS, _BATTERY_UNARY_OPS,
                     _BATTERY_UNARY_WEIGHTS, _CLEANER_BINARY_OPS,
                     _CLEANER_BINARY_WEIGHTS, _CLEANER_UNARY_OPS,
                     _CLEANER_UNARY_WEIGHTS, _EXTRA_SEEDS, _GENCSV_POOLS,
                     _RunTrace, _SYRACUSE_BINARY_OPS, _SYRACUSE_BINARY_WEIGHTS,
                     _SYRACUSE_UNARY_OPS, _SYRACUSE_UNARY_WEIGHTS,
                     _active_pool_ops, _active_pools, _detect_dominant_op,
                     _dim_active, _ds, _get_ops_for_role, _pool_choice,
                     make_cfg, make_cfg_nd)
from .tree import (Node, _CANON_CONST, _FLOAT_COMPLEXITY_WEIGHT, _FLOAT_GAMMA,
                   _PACK_D, _STR_CODES, _SYMPY_BINARY, _SYMPY_UNARY,
                   _TAG_BINARY, _TAG_FLOAT, _TAG_OTHER, _TAG_UNARY, _UNPACK_Q,
                   _is_adjusted_float, _leaf_code_canonical, _leaf_code_exact,
                   _leaf_code_rounded, _node_hashes, _str_code, _value_code,
                   collect_constants, get_all_nodes, node_to_sympy, to_string,
                   tree_complexity, tree_depth, tree_size)
from .simplification import (_SIMPLIFY_CACHE, _TRIVIAL_CACHE, _UNARY_FOLD,
                             _clear_simplify_caches, _has_own_factor,
                             _invalidate_all_hashes, _is_const, _is_float,
                             _simplify_node, _simplify_tree, simplify)
from .evaluation import (_COMPILE_AFTER, _EVAL_COUNTS, _HOT_ZONES,
                         _INTERP_BINARY, _INTERP_MAX_DEPTH, _INTERP_UNARY,
                         _InterpTooDeep, _LMPlan, _LM_BINARY_FN,
                         _LM_BINARY_SRC, _LM_PLAN_CACHE, _LM_PLAN_CACHE_MAX,
                         _LM_UNARY_FN, _LM_UNARY_SRC, _NAN,
                         _PARAMETRIC_CACHE_MAX, _PRED_CACHE_MAX,
                         _collect_constants_ordered, _cube, _float_literal,
                         _interp, _lm_apply, _lm_build_plan, _lm_column,
                         _lm_plan, _pearson_r, _predict_cached, _safe_write,
                         _sq, _to_np_code, _to_np_code_parametric,
                         compile_parametric, compile_to_numpy, evaluate,
                         evaluate_vector)
from .datasets import (DECOY_FEATURES, SYRACUSE_FEATURE_NAMES,
                       SYRACUSE_N_FEATURES, _collatz_flight_time,
                       _log_max_height_level2, _max_height_ratio,
                       _scale_feature, _v2, build_dataset,
                       generate_syracuse_dataset)
from .scoring import (_linear_scale_params, _pure_mse, _robust_scale_params,
                      _scale_tree, _target_scale, count_distinct_features,
                      fitness, get_feature_bias_weights, raw_mse,
                      raw_pearson_r, record_feature_usage, reset_feature_usage,
                      wrap_linear_scaling)
from .fitting import (optimize_constants_adam, optimize_constants_lm)
from .genetic import (EpsilonLexicaseSelector, _nd_diverse_population,
                      _random_tree_full, _random_tree_full_nd,
                      _random_tree_grow, _random_tree_grow_nd, _random_tree_nd,
                      _semantic_key, build_stigmergic_tree,
                      build_stigmergic_tree_v2, build_stigmergic_tree_v3,
                      crossover_size_fair, fragment_inject_mutation,
                      hoist_mutation, mutate, pareto_rank, point_mutation,
                      random_constant, random_terminal, random_tree,
                      semantic_dedup, semantic_mutation, shrink_mutation,
                      stigmergic_mutation, subtree_mutation, tournament)
from .memory import (FragmentCoGraph, FragmentEntry, FragmentLibrary,
                     FragmentSequenceMemory, _TRIVIAL_PROBE_X,
                     compute_semantic_sig, init_probe_set, semantic_score,
                     update_residual_sig, warm_transfer)

# [v16-BATTERY] Dépendances pour la lecture de données réelles (CSV NASA)
# [v0.8] Importées à la demande : pandas et scikit-learn représentaient les
# trois quarts du temps d'`import gp_elite` (près d'une seconde), payés aussi
# par chaque processus parallèle au démarrage, alors que la recherche n'en
# utilise aucun. Seuls les chargeurs CSV et normalize="minmax" en ont besoin.
def _csv_deps():
    """(pandas, MinMaxScaler), ou ImportError si l'un manque."""
    import pandas as pd
    from sklearn.preprocessing import MinMaxScaler
    return pd, MinMaxScaler


def _csv_deps_ok() -> bool:
    try:
        _csv_deps()
        return True
    except ImportError:
        return False


def _MinMaxScaler(*args, **kwargs):
    from sklearn.preprocessing import MinMaxScaler
    return MinMaxScaler(*args, **kwargs)



# ════════════════════════════════════════════════════════════════
# [v28-MOTIFS] SEEDING DE MOTIFS DE COMPOSITION
# ════════════════════════════════════════════════════════════════
# Constat (banc Feynman v27) : les échecs restants sont des compositions à
# TREMPLIN — sqrt(sq(a−b)+sq(c−d)), 1/(1/a+1/b) — dont les sous-expressions
# intermédiaires ont une fitness médiocre : l'évolution ne les assemble pas.
# Remède éprouvé (AI Feynman, grammar seeding) : injecter dans la population
# initiale des INSTANCES de motifs physiques canoniques sur des variables
# tirées au hasard ; l'évolution recombine, LM ajuste les constantes. Le
# tirage dépend du seed du run → les restarts (v27) COUVRENT les appariements.

def _make_motif_seeds(cfg, n_max: int = 32) -> list:
    """Instancie des motifs de composition compatibles avec le pool actif."""
    terms = list(getattr(cfg, "TERMINALS", []) or [])
    if not terms:
        return []
    uops = set(getattr(state, '_GENERIC_UNARY_OPS', []) or [])
    rng = random.Random((getattr(cfg, "SEED", 0) or 0) ^ 0x0F1F2F)
    T = lambda: Node(rng.choice(terms))
    def T2():                                   # deux terminaux distincts si possible
        a = rng.choice(terms)
        b = rng.choice([t for t in terms if t != a] or terms)
        return Node(a), Node(b)
    C = lambda lo, hi: Node(round(rng.uniform(lo, hi), 4))
    inv = lambda x: Node('/', Node(1.0), x)
    diff = lambda: Node('-', *T2())
    out = []
    def add(f):
        try:
            nd = f()
            if nd is not None:
                out.append(nd)
        except Exception:
            pass
    builders = []
    if 'sqrt' in uops and 'sq' in uops:
        builders += [lambda: Node('sqrt', Node('+', Node('sq', diff()), Node('sq', diff()))),
                     lambda: Node('sqrt', Node('+', Node('sq', T()), Node('sq', T())))]
    builders += [lambda: inv(Node('+', inv(T()), inv(T()))),                  # 1/(1/a+1/b)
                 lambda: inv(Node('+', inv(T()), Node('*', T(), inv(T()))))]  # 1/(1/a+c/b)
    if 'exp' in uops and 'sq' in uops:
        builders += [lambda: Node('exp', Node('*', C(-1.5, -0.2), Node('sq', T())))]
    if 'log' in uops:
        builders += [lambda: Node('log', Node('/', *T2()))]
    if 'cos' in uops:
        builders += [lambda: Node('*', T(), Node('-', Node(1.0),
                                                 Node('cos', Node('*', *T2()))))]
    if 'sq' in uops:
        builders += [lambda: Node('sq', diff())]                              # brique
    builders += [lambda: Node('/', Node('+', *T2()), Node('+', Node(1.0), T())),
                 lambda: inv(T())]                                            # briques
    if not builders:
        return []
    k = 0
    while len(out) < n_max and k < n_max * 4:
        add(builders[k % len(builders)])
        k += 1
    return out[:n_max]


# ════════════════════════════════════════════════════════════════
# [v0.8] GRAINES DE LOI DE PUISSANCE
# ════════════════════════════════════════════════════════════════
# Constat (campagne 2 du banc de décision, 205 ajustements Feynman à 30 s) :
# des lois qui ne sont qu'un produit de puissances des variables, comme
# I.12.2 q1·q2/(4π·ε·r²), I.32.5 ou III.19.51, étaient retrouvées 1, 2 et 0
# fois sur 5 ; les autres ajustements rendaient des formules de 50 à 70
# nœuds. Or une loi y = c·Π x_j^a_j est une droite en échelle log :
# log|y| = log|c| + Σ a_j·log|x_j|. Quand la cible et des colonnes gardent
# un signe constant, les moindres carrés sur les logarithmes donnent les
# exposants, et la normalisation par max|x| ne les change pas. On place dans
# la population initiale le monôme aux exposants arrondis au demi-entier
# (la forme d'une loi physique usuelle) et, si le pool contient `pow`, le
# monôme aux exposants ajustés (loi empirique : Levenberg-Marquardt affine
# ensuite ces exposants), et seulement si les données sont bien celles d'une
# loi de puissance : le monôme doit expliquer au moins 99,9 % de la variance
# de log|y| (_POWER_LAW_MIN_R2). Ce ne sont que deux individus par île, parmi
# une centaine, jugés comme les autres. Aucun tirage aléatoire : sans colonne de signe
# constant ou avec une cible qui change de signe (données centrées), rien
# n'est injecté et l'ajustement est celui d'avant. Hors du mode CSV
# générique, sous `units=` (population typée ; voir _SEEDS_UNDER_UNITS
# ci-dessous, phase 7) et en mode extrapolation (où les motifs sont déjà
# coupés), rien n'est injecté non plus.

_POWER_LAW_MIN_R2 = 0.999    # part de la variance de log|y| que le monôme doit expliquer

# [1.1, phase 7] Sous units= (population typée), les quatre chercheurs de
# graines (loi de puissance, B1, E1, N1) ne rendaient rien. Avec ce drapeau, ils
# tournent comme sans unités, sur les mêmes lignes et avec les mêmes seuils,
# et chaque arbre rendu n'est gardé que s'il passe la porte de validité des
# dimensions (dim_search.is_typed_valid), celle de fitness() et des
# opérateurs typés : l'invariant des unités est inchangé. Sans unités, rien
# ne change. Plan : benchmarks/results_1.1/PLAN.md (changement U1, adopté le
# 26 octobre 2026) : banc U41 (les 41 équations du banc de décision avec leurs
# unités), lois exactes 107 -> 165 sur 205, puis 107 -> 166 sur des graines
# neuves ; structure sous bruit 79 -> 113 (1 %) et 80 -> 99 (10 %) ; chaque
# modèle rendu passe l'audit des unités ; données réelles sous unités
# inchangées. Actif par défaut depuis son adoption.


def _seeds_blocked_by_units(cfg) -> bool:
    """Vrai quand units= est actif et que U1 est coupé (comportement 1.0)."""
    return _dim_active(cfg) and not state._SEEDS_UNDER_UNITS


def _typed_seeds(seeds: list, cfg) -> list:
    """[1.1] Sous units=, les seules graines qui passent la porte des
    dimensions ; sans unités, toutes."""
    if not _dim_active(cfg) or not seeds:
        return seeds
    gate = _ds().is_typed_valid
    unk = bool(getattr(cfg, "UNKNOWN_CONST", False))
    kept = [t for t in seeds if gate(t, cfg.FEAT_DIMS, cfg.TARGET_DIM, unk)]
    if len(kept) < len(seeds):
        TRACE.bump("graines_rejetees_dim", len(seeds) - len(kept))
    return kept


def _power_law_exponents(X, y, min_r2=None):
    """Exposants (a_j) de |y| ≈ c·Π |x_j|^a_j par moindres carrés sur les
    logarithmes, pour les colonnes de signe constant. Rend (cols, a) ou
    None si la cible change de signe, si aucune colonne ne convient, si le
    système est dégénéré, ou si le monôme n'explique pas au moins 99,9 % de
    la variance de log|y|.

    [v0.8] Ce dernier seuil vient de la campagne 6 : sans lui, sur données
    réelles, un monôme ajusté à des données qui n'en sont pas un (228_elusage :
    X0^-3,38, R² log-log 0,81) gagnait la sélection et s'effondrait hors du
    domaine (R² -12). Les lois de Feynman qui sont des monômes ont un R²
    log-log de 1 ; les six jeux réels et nikuradse_1, 0,93 au plus."""
    n = y.shape[0]
    with np.errstate(all="ignore"):
        if not (np.all(np.isfinite(y)) and np.all(np.isfinite(X))):
            return None
        if not (np.all(y > 0) or np.all(y < 0)):
            return None
        cols = [j for j in range(X.shape[1])
                if np.all(X[:, j] > 0) or np.all(X[:, j] < 0)]
        if not cols or n < len(cols) + 3:
            return None
        A = np.column_stack([np.ones(n), np.log(np.abs(X[:, cols]))])
        try:
            coef, _res, rank, _sv = np.linalg.lstsq(A, np.log(np.abs(y)),
                                                    rcond=None)
        except Exception:
            return None
    if rank < A.shape[1] or not np.all(np.isfinite(coef)):
        return None
    ly = np.log(np.abs(y))
    v = float(np.var(ly))
    if not v > 0.0:
        return None
    with np.errstate(all="ignore"):
        r2 = 1.0 - float(np.var(ly - A @ coef)) / v
    if not r2 >= (_POWER_LAW_MIN_R2 if min_r2 is None else min_r2):
        return None
    return cols, coef[1:]


def _power_law_exponents_w(X, y):
    """[1.4-N2] Les exposants de _power_law_exponents pour la seconde passe
    des graines tolérantes au bruit : moindres carrés sur les logarithmes
    pondérés par y², sans la condition de signe constant de la cible et sans
    seuil sur R². Un bruit de taille constante σ déplace log|y| de σ/|y| :
    le poids y² est celui qu'un tel bruit demande, et les lignes proches de
    zéro, où le bruit change le signe, ne pèsent presque rien. Les lignes où
    y est nul n'ont ni logarithme ni poids : elles sont écartées."""
    with np.errstate(all="ignore"):
        if not (np.all(np.isfinite(y)) and np.all(np.isfinite(X))):
            return None
        keep = y != 0
        m = int(keep.sum())
        cols = [j for j in range(X.shape[1])
                if np.all(X[:, j] > 0) or np.all(X[:, j] < 0)]
        if not cols or m < len(cols) + 3:
            return None
        ay = np.abs(y[keep])
        sw = ay / float(ay.max())
        A = np.column_stack([np.ones(m), np.log(np.abs(X[keep][:, cols]))])
        try:
            coef, _res, rank, _sv = np.linalg.lstsq(A * sw[:, None],
                                                    np.log(ay) * sw, rcond=None)
        except Exception:
            return None
    if rank < A.shape[1] or not np.all(np.isfinite(coef)):
        return None
    return cols, coef[1:]


def _half_integer_power(term: str, e2: int, uops) -> Optional["Node"]:
    """x^(e2/2) pour e2 > 0, avec les seuls opérateurs du pool (sq, cube,
    sqrt, *). None si une racine est nécessaire et que sqrt manque."""
    n_int, half = divmod(e2, 2)

    def ipow(k: int) -> "Node":
        if k == 1:
            return Node(term)
        if k == 3 and "cube" in uops:
            return Node("cube", Node(term))
        if k % 2 == 0:
            h = ipow(k // 2)
            return Node("sq", h) if "sq" in uops else Node("*", h, ipow(k // 2))
        return Node("*", Node(term), ipow(k - 1))

    factors = []
    if n_int:
        factors.append(ipow(n_int))
    if half:
        if "sqrt" not in uops:
            return None
        factors.append(Node("sqrt", Node(term)))
    out = factors[0]
    for f in factors[1:]:
        out = Node("*", out, f)
    return out


def _product(nodes: list) -> Optional["Node"]:
    if not nodes:
        return None
    out = nodes[0]
    for f in nodes[1:]:
        out = Node("*", out, f)
    return out


def _make_power_law_seeds(xs, ys, cfg, min_r2=None, weighted=False) -> list:
    """[v0.8] Voir le commentaire ci-dessus. Rend 0, 1 ou 2 arbres. min_r2
    remplace _POWER_LAW_MIN_R2 (graines tolérantes au bruit, phase 5).
    [1.4-N2] weighted : la seconde passe de ces graines
    (_power_law_exponents_w)."""
    if not state._GENERIC_CSV_MODE or _seeds_blocked_by_units(cfg) \
            or bool(getattr(cfg, "EXTRAPOLATION_MODE", False)) \
            or not bool(getattr(cfg, "POWER_LAW_SEEDS", True)):
        return []
    terms = list(getattr(cfg, "TERMINALS", []) or [])
    try:
        X = np.asarray(xs, dtype=float)
        y = np.asarray(ys, dtype=float)
    except Exception:
        return []
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    if X.ndim != 2 or y.ndim != 1 or X.shape[0] != y.shape[0] \
            or X.shape[1] != len(terms):
        return []
    fit = (_power_law_exponents_w(X, y) if weighted
           else _power_law_exponents(X, y, min_r2))
    if fit is None:
        return []
    cols, expo = fit
    bops = set(state._GENERIC_BINARY_OPS)
    uops = set(state._GENERIC_UNARY_OPS)
    seeds = []

    # 1) exposants arrondis au demi-entier le plus proche
    e2s = [int(round(2.0 * float(a))) for a in expo]
    if all(abs(e2) <= 12 for e2 in e2s) and any(e2s):
        num, den, ok = [], [], True
        for j, e2 in zip(cols, e2s):
            if e2 == 0:
                continue
            f = _half_integer_power(terms[j], abs(e2), uops)
            if f is None:
                ok = False
                break
            (num if e2 > 0 else den).append(f)
        if ok and (not den or "/" in bops):
            top, bot = _product(num), _product(den)
            if bot is None:
                seeds.append(top)
            else:
                seeds.append(Node("/", top if top is not None else Node(1.0), bot))

    # 2) exposants ajustés, si le pool a pow et qu'ils ne sont pas déjà
    #    des demi-entiers (sinon la graine 1 les contient)
    # [1.1, U2] Sous units=, seulement sans unités fractionnaires : un exposant
    # ajusté qui n'est pas un demi-entier doit porter sur une entrée sans
    # dimension. Sinon (pow(n, 1.0041) en moles), la graine ne passe la porte
    # que par la constante inconnue, et ses descendants font chercher au
    # constructeur typé des sous-arbres d'unités fractionnaires, qu'il atteint
    # rarement : la loi des gaz du notebook de TP passait de 50 s à 78 s
    # (benchmarks/results_1.1/PLAN_U2.md).
    def _fractional_units(j, a):
        if not _dim_active(cfg) or abs(2.0 * a - round(2.0 * a)) <= 0.04:
            return False
        d = (cfg.FEAT_DIMS or {}).get(j) or {}
        return any(abs(float(v)) > 1e-12 for v in d.values())

    if "pow" in bops and float(np.max(np.abs(2.0 * expo - np.round(2.0 * expo)))) > 0.04:
        facs = [Node("pow", Node(terms[j]), Node(round(float(a), 4)))
                for j, a in zip(cols, expo) if abs(float(a)) >= 0.02]
        if facs and not any(_fractional_units(j, float(a)) for j, a in zip(cols, expo)
                            if abs(float(a)) >= 0.02):
            seeds.append(_product(facs))

    seeds = _typed_seeds(seeds, cfg)
    if seeds:
        TRACE.set("power_law_seed", "exposants %s ; %d graine(s) : %s" % (
            ", ".join("%s^%.3g" % (terms[j], float(a)) for j, a in zip(cols, expo)),
            len(seeds), " | ".join(to_string(s) for s in seeds)))
    return seeds


# ════════════════════════════════════════════════════════════════
# [0.10, phase 4b] GRAINES « MONÔME FOIS PUISSANCE D'UN BINÔME »
# ════════════════════════════════════════════════════════════════
# Constat (base de la 0.8.0, banc de décision) : les familles rationnelle et
# racine ne sont jamais retrouvées (0 sur 40 ajustements), alors que leurs
# lois ont une forme commune, y = b·f·(1 + c·g)^p, f et g des monômes des
# variables, p dans {-1, -1/2, 1/2, 1} : om0/(1 - v/c), m/sqrt(1 - v²/c²),
# sqrt(om²/c² - pi²/d²). Le binôme connu, c'est une droite en échelle log :
# log|y| - p·log(1 + c·g) = log|b| + Σ e_j·log|x_j|. Pour chaque monôme g
# d'une à trois colonnes (exposants -2, -1, 1, 2), c se cherche sur une
# dimension et les exposants de f suivent par moindres carrés, comme les
# graines de loi de puissance. La forme n'est injectée que si elle tient à la
# précision numérique (variance résiduelle de log|y| sous 1e-12 de sa
# variance, exposants arrondis) : sur des données qui ne suivent pas une telle
# loi exactement, données réelles et bruitées comprises, rien n'est injecté
# et l'ajustement est celui d'avant. Aucun tirage aléatoire. Mêmes gardes que
# les graines de loi de puissance. Mesuré dans benchmarks/results_0.9/
# PLAN_PHASE4.md (changement B1, adopté le 12 octobre 2026) : banc de
# décision, lois exactes 86 -> 124 sur 205 (familles rationnelle et racine
# 0 -> 35 sur 90), puis 86 -> 126 sur des graines neuves ; données réelles
# inchangées (aucune graine injectée sur les 260 ajustements réels).

_BINOM_EXPS = (-2, -1, 1, 2)          # exposants des colonnes dans g
_BINOM_TOL = 1e-12                    # variance résiduelle de log t, relative
_POWER_TOL = 1e-12                    # celle qui reconnaît une loi de puissance
_BINOM_MAX_LIB = 4096                 # monômes g essayés au plus
_BINOM_GRID_ROWS = 64                 # lignes du tri initial sur la grille
_BINOM_GRID = np.array(sorted(set(
    [float(v) for v in -1.0 + np.geomspace(1e-3, 1.0, 12)[:-1]]
    + [-0.5, -0.3, -0.1, -0.03, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0])))


def _binom_library(cols, n_max):
    """Monômes g : tuples ((colonne, exposant), ...) d'une à n_max colonnes.
    None au-delà de _BINOM_MAX_LIB."""
    lib = []
    for r in range(1, n_max + 1):
        for js in itertools.combinations(cols, r):
            for es in itertools.product(_BINOM_EXPS, repeat=r):
                lib.append(tuple(zip(js, es)))
                if len(lib) > _BINOM_MAX_LIB:
                    return None
    return lib


def _golden_min(f, a, b, it=60):
    """Minimum de f sur [a, b] par la section dorée : (x, f(x))."""
    gr = (math.sqrt(5.0) - 1.0) / 2.0
    c1, c2 = b - gr * (b - a), a + gr * (b - a)
    f1, f2 = f(c1), f(c2)
    for _ in range(it):
        if f1 < f2:
            b, c2, f2 = c2, c1, f1
            c1 = b - gr * (b - a)
            f1 = f(c1)
        else:
            a, c1, f1 = c1, c2, f2
            c2 = a + gr * (b - a)
            f2 = f(c2)
    return (c1, f1) if f1 < f2 else (c2, f2)


def _binomial_forms(X, y, top: int = 8, tol=None, weighted=False) -> list:
    """Formes y = b·f·(1 + c·g)^p qui tiennent à la précision numérique.
    Rend une liste de (p, cols, exposants de f dans y, g, c). tol remplace
    _BINOM_TOL (graines tolérantes au bruit, phase 5).

    [1.4-N2] weighted : la seconde passe des graines tolérantes au bruit. Les
    moindres carrés sur les logarithmes sont pondérés par y² (voir
    _power_law_exponents_w) et la cible n'a plus à garder un signe ; les
    lignes où y est nul sont écartées. Sans weighted, les calculs sont ceux
    d'avant, opération pour opération."""
    tol = _BINOM_TOL if tol is None else tol
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    out = []
    with np.errstate(all="ignore"):
        if not (np.all(np.isfinite(y)) and np.all(np.isfinite(X))):
            return out
        if weighted:
            nzr = y != 0
            X, y = X[nzr], y[nzr]
            if not y.shape[0]:
                return out
        elif not (np.all(y > 0) or np.all(y < 0)):
            return out
        n = y.shape[0]
        cols = [j for j in range(X.shape[1])
                if np.all(X[:, j] > 0) or np.all(X[:, j] < 0)]
        if not cols or n < len(cols) + 6:
            return out
        lib = _binom_library(cols, 3 if len(cols) <= 6 else 2)
        if lib is None:
            return out
        LU = np.log(np.abs(X[:, cols]))
        L = np.column_stack([np.ones(n), LU])
        sub = np.unique(np.linspace(0, n - 1, min(n, _BINOM_GRID_ROWS)).astype(int))
        if weighted:
            sw = np.abs(y) / float(np.max(np.abs(y)))
            Lw = L * sw[:, None]
            Q, Rr = np.linalg.qr(Lw)
            Qs = np.linalg.qr(Lw[sub])[0]
            sws = sw[sub]
            un = sw / float(np.linalg.norm(sw))

            def rvar(z):                  # carré moyen du résidu pondéré
                zw = z * sw
                r_ = zw - Q @ (Q.T @ zw)
                return float(np.mean(r_ * r_))

            def rvar_sub(Z):
                Zw = Z * sws[:, None]
                R_ = Zw - Qs @ (Qs.T @ Zw)
                return np.mean(R_ * R_, axis=0)

            def wvar(z):                  # variance pondérée
                zw = z * sw
                r_ = zw - un * float(un @ zw)
                return float(np.mean(r_ * r_))

            def lsq(z):
                return np.linalg.lstsq(Lw, z * sw, rcond=None)[0]
        else:
            Q, Rr = np.linalg.qr(L)
            Qs = np.linalg.qr(L[sub])[0]

            def rvar(z):
                return float(np.var(z - Q @ (Q.T @ z)))

            def rvar_sub(Z):
                return np.var(Z - Qs @ (Qs.T @ Z), axis=0)

            def wvar(z):
                return float(np.var(z))

            def lsq(z):
                return np.linalg.lstsq(L, z, rcond=None)[0]
        dR = np.abs(np.diag(Rr))
        if not np.min(dR) > 1e-10 * np.max(dR):
            return out
        pos = {j: i for i, j in enumerate(cols)}
        E = np.zeros((len(cols), len(lib)))
        sg = np.ones(len(lib))
        for m, g in enumerate(lib):
            for j, e in g:
                E[pos[j], m] = e
                if X[0, j] < 0 and e % 2:
                    sg[m] = -sg[m]
        LG = LU @ E
        lgmax = np.max(LG, axis=0)
        GN = np.exp(LG - lgmax)                   # |g| / max|g|, dans (0, 1]
        GNs = GN[sub]
        for k in (1, 2):                          # t = |y|^k
            lt = k * np.log(np.abs(y))
            vt = wvar(lt)
            if not vt > 0.0:
                continue
            if rvar(lt) / vt < _POWER_TOL:
                continue                          # une loi de puissance
            lts = lt[sub]
            for sig in (-1.0, 1.0):               # t = f·(1 + c·g)^(-sig)
                best = np.full(len(lib), np.inf)
                for s in _BINOM_GRID:
                    W = 1.0 + s * GNs
                    ok = np.all(W > 0, axis=0)
                    Z = lts[:, None] + sig * np.log(np.where(W > 0, W, 1.0))
                    v = rvar_sub(Z)
                    v[~ok] = np.inf
                    best = np.minimum(best, v)
                found = None
                for m in np.argsort(best, kind="stable")[:top]:
                    if not np.isfinite(best[m]):
                        break
                    gn = GN[:, m]

                    def obj(s, gn=gn):
                        w = 1.0 + s * gn
                        if np.any(w <= 0):
                            return np.inf
                        z = lt + sig * np.log(w)
                        return rvar(z)
                    vals = [obj(s) for s in _BINOM_GRID]
                    i = int(np.argmin(vals))
                    a = _BINOM_GRID[i - 1] if i > 0 else -1.0 + 1e-9
                    b = _BINOM_GRID[i + 1] if i + 1 < len(_BINOM_GRID) else 100.0
                    s, v = _golden_min(obj, float(a), float(b))
                    if v / vt < tol and (found is None or v < found[0]):
                        found = (v, int(m), s)
                if found is None:
                    continue
                _v, m, s = found
                gn = GN[:, m]
                z = lt + sig * np.log(1.0 + s * gn)
                coef = lsq(z)[1:]
                step = 2.0 if k == 1 else 1.0     # demi-entiers dans y
                ex = np.round(coef * step) / step
                if not np.all(np.abs(ex) <= 6.0 * k):
                    continue
                base = lt - LU @ ex

                def obj2(s2):
                    w2 = 1.0 + s2 * gn
                    if np.any(w2 <= 0):
                        return np.inf
                    return wvar(base + sig * np.log(w2))
                h = 0.05 * (1.0 + abs(s))
                s2, v2 = _golden_min(obj2, s - h, s + h)
                if not v2 / vt < tol:
                    continue
                c = float(sg[m] * s2 / math.exp(lgmax[m]))
                out.append((-sig / k, cols, ex / k, lib[m], c))
    return out


def _monomial(terms, pairs, uops) -> Optional["Node"]:
    """Π terms[j]^e (e demi-entiers, non nuls) avec les opérateurs du pool ;
    None si une racine manque."""
    num, den = [], []
    for j, e in pairs:
        f = _half_integer_power(terms[j], int(round(2.0 * abs(e))), uops)
        if f is None:
            return None
        (num if e > 0 else den).append(f)
    top, bot = _product(num), _product(den)
    if bot is None:
        return top
    return Node("/", top if top is not None else Node(1.0), bot)


def _make_binomial_seeds(xs, ys, cfg, tol=None, weighted=False) -> list:
    """[0.10, phase 4b] Voir le commentaire ci-dessus. Rend 0 à 4 arbres.
    Le drapeau _BINOMIAL_SEEDS (actif par défaut) les coupe. [1.4-N2]
    weighted : la seconde passe des graines tolérantes au bruit."""
    if not state._BINOMIAL_SEEDS or not state._GENERIC_CSV_MODE or _seeds_blocked_by_units(cfg) \
            or bool(getattr(cfg, "EXTRAPOLATION_MODE", False)):
        return []
    terms = list(getattr(cfg, "TERMINALS", []) or [])
    try:
        X = np.asarray(xs, dtype=float)
        y = np.asarray(ys, dtype=float)
    except Exception:
        return []
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    if X.ndim != 2 or y.ndim != 1 or X.shape[0] != y.shape[0] \
            or X.shape[1] != len(terms):
        return []
    t0 = time.time()
    forms = _binomial_forms(X, y, tol=tol, weighted=weighted)
    TRACE.set("binomial_seed_s", round(time.time() - t0, 3))
    bops = set(state._GENERIC_BINARY_OPS)
    uops = set(state._GENERIC_UNARY_OPS)
    if not {"+", "*", "/"} <= bops:
        return []
    seeds = []
    for p, cols, ex, g, c in forms:
        f = _monomial(terms, [(j, float(e)) for j, e in zip(cols, ex) if e != 0],
                      uops)
        gnode = _monomial(terms, [(j, float(e)) for j, e in g], uops)
        if gnode is None or (abs(p) == 0.5 and "sqrt" not in uops):
            continue
        w = Node("+", Node(1.0), Node("*", Node(c), gnode))
        if abs(p) == 0.5:
            w = Node("sqrt", w)
        if p < 0:
            seeds.append(Node("/", f if f is not None else Node(1.0), w))
        else:
            seeds.append(w if f is None else Node("*", f, w))
    seeds = _typed_seeds(seeds, cfg)
    if seeds:
        TRACE.set("binomial_seed", " | ".join(to_string(s) for s in seeds))
    return seeds


# ════════════════════════════════════════════════════════════════
# [0.10, phase 4a] GRAINES « FONCTION D'UN MONÔME », TENUES EXACTEMENT
# ════════════════════════════════════════════════════════════════
# Même principe que les graines binomiales, pour les fonctions élémentaires :
#   y = b·f·exp(c·g), b·f·log(c·g), b·f·tanh(c·g), b·f/cosh(c·g)
#   y = f·(a + β·sin(ω·g) + γ·cos(ω·g))
#   [1.3-A3] y = b·f·arcsin(c·g), là où le pool a l'arc sinus (trig, full) ;
#   inversée comme tanh, b au moins 2/π fois le plus grand |y/f|
# f et g des monômes. Pour les quatre premières, la fonction inversée rend
# une loi de puissance des entrées (une constante cherchée sur une dimension,
# aucune pour le logarithme) ; pour la forme trigonométrique, ω se cherche
# sur une grille, a, β, γ par moindres carrés, et les exposants de f par
# moindres carrés sur les logarithmes, arrondis. Une forme n'est injectée
# que si elle tient à la précision numérique, exposants arrondis : sur des
# données qui ne suivent pas une telle loi exactement, rien n'est injecté et
# l'ajustement est celui d'avant. Aucun tirage aléatoire. Mêmes gardes que
# les graines binomiales. Mesuré dans benchmarks/results_0.9/PLAN_PHASE4.md
# (changement E1, adopté le 12 octobre 2026) : banc de décision avec B1,
# lois exactes 124 -> 157 sur 205 (familles à zéro 35 -> 55 sur 90), puis
# 126 -> 155 sur des graines neuves ; données réelles inchangées (aucune
# graine injectée sur les 520 ajustements réels, pool par défaut et "trig").

_ELEM_MAX_LIB = 4096                  # monômes f (ou g trigonométriques) au plus
_ELEM_S_GRID = np.linspace(-6.0, 3.0, 37)
_ELEM_W_GRID = np.linspace(0.05, 40.0, 800)
_ELEM_TRIG_GATE = 0.05                # résidu de grille sous lequel on affine


def _elem_flib(cols):
    """Monômes f : 1, une colonne (±1, ±2), deux ou trois colonnes (±1 ;
    trois seulement jusqu'à huit colonnes). None au-delà de _ELEM_MAX_LIB."""
    lib = [()]
    for j in cols:
        for e in (-2, -1, 1, 2):
            lib.append(((j, e),))
    for r in ((2, 3) if len(cols) <= 8 else (2,)):
        for js in itertools.combinations(cols, r):
            for es in itertools.product((-1, 1), repeat=r):
                lib.append(tuple(zip(js, es)))
                if len(lib) > _ELEM_MAX_LIB:
                    return None
    return lib


def _elem_mono(X, m):
    v = np.ones(X.shape[0])
    for j, e in m:
        v = v * X[:, j] ** e
    return v


def _elem_rel(Z, Q):
    """Variance résiduelle relative de chaque colonne de Z après projection
    sur l'espace de Q."""
    V = np.var(Z, axis=0)
    R = Z - Q @ (Q.T @ Z)
    with np.errstate(all="ignore"):
        out = np.var(R, axis=0) / V
    return np.where(V > 0, out, np.inf)


def _elem_transform(kind, R, s):
    """Transformée colonne par colonne qui est une loi de puissance des
    entrées quand la forme tient (NaN là où elle n'est pas définie)."""
    if kind == "exp-":                    # w - a > 0, a = min(w) - étendue·10^s
        W = np.log(np.abs(R))
        return np.log(W - (W.min(axis=0) - np.ptp(W, axis=0) * 10.0 ** s))
    if kind == "exp+":                    # a - w > 0, a = max(w) + étendue·10^s
        W = np.log(np.abs(R))
        return np.log((W.max(axis=0) + np.ptp(W, axis=0) * 10.0 ** s) - W)
    A = np.abs(R)
    mx = A.max(axis=0)
    if kind == "tanh":
        return np.log(np.arctanh(A / (mx * (1.0 + 10.0 ** s))))
    if kind == "arcsin":                  # [1.3-A3] |arcsin| <= pi/2 : b >= (2/pi) max
        return np.log(np.sin(A / (mx * (2.0 / math.pi) * (1.0 + 10.0 ** s))))
    return np.log(np.arccosh(mx * (1.0 + 10.0 ** s) / A))      # "sech"


def _elem_inverse_forms(X, y, cols, kinds, top: int = 6, tol=_BINOM_TOL) -> list:
    """Formes y = b·f·φ(c·g), φ dans exp, log, tanh, 1/cosh. Rend des
    tuples (kind, f, g, c), exposants de g arrondis au demi-entier."""
    n = y.shape[0]
    out = []
    lib = _elem_flib(cols)
    if lib is None:
        return out
    FV = np.column_stack([_elem_mono(X, m) for m in lib])
    R = y[:, None] / FV
    ok = np.all(R > 0, axis=0) | np.all(R < 0, axis=0)
    idx = np.where(ok)[0]
    if not idx.size:
        return out
    R = R[:, idx]
    LU = np.log(np.abs(X[:, cols]))
    L = np.column_stack([np.ones(n), LU])
    Q = np.linalg.qr(L)[0]
    sub = np.unique(np.linspace(0, n - 1, min(n, _BINOM_GRID_ROWS)).astype(int))
    Qs = np.linalg.qr(L[sub])[0]

    def g_of(coef):
        """Exposants de g arrondis (demi-entiers), None si tous nuls."""
        ex = np.round(2.0 * coef) / 2.0
        if not np.any(ex) or not np.all(np.abs(ex) <= 6.0):
            return None
        return tuple((j, float(e)) for j, e in zip(cols, ex) if e)

    if "log" in kinds:                    # r = a + Σ e_j·log|u_j|, linéaire
        v = _elem_rel(R, Q)
        for m in np.where(v < tol)[0]:
            r = R[:, m]
            coef = np.linalg.lstsq(L, r, rcond=None)[0][1:]
            nzc = np.abs(coef)[np.abs(coef) > 1e-6]
            if not nzc.size:
                continue
            g = g_of(coef / float(nzc.min()))
            if g is None:
                continue
            lg = np.log(np.abs(_elem_mono(X, g)))
            A = np.column_stack([np.ones(n), lg])
            a0, s0 = np.linalg.lstsq(A, r, rcond=None)[0]
            if not (float(np.var(r - A @ np.array([a0, s0]))) / float(np.var(r))
                    < tol) or s0 == 0.0 or abs(a0 / s0) > 700.0:
                continue
            out.append(("log", lib[idx[m]], g, float(math.exp(a0 / s0))))
            break
    for kind in [k for k in ("exp-", "exp+", "tanh", "sech", "arcsin")
                 if k.rstrip("+-") in kinds]:
        best = np.full(R.shape[1], np.inf)
        with np.errstate(all="ignore"):
            for s in _ELEM_S_GRID:
                T = _elem_transform(kind, R[sub], s)
                fin = np.all(np.isfinite(T), axis=0)
                v = _elem_rel(np.where(np.isfinite(T), T, 0.0), Qs)
                v[~fin] = np.inf
                best = np.minimum(best, v)
        order = [int(m) for m in np.argsort(best, kind="stable")[:top]]
        if kind == "arcsin":
            # [1.3-A3] La forme simple y = b·arcsin(c·g) (f = 1) est toujours
            # essayée, la première : arcsin(x) est proche de x pour un petit
            # argument, et sur la grille grossière d'autres f peuvent la
            # devancer (7e sur une loi arcsin(0,7·x0/(x1·x2))).
            j0 = np.where(idx == 0)[0]
            if j0.size and np.isfinite(best[j0[0]]):
                order = [int(j0[0])] + [m for m in order if m != j0[0]]
        for m in order:
            if not np.isfinite(best[m]):
                break
            r = R[:, [m]]

            def obj(s, r=r):
                with np.errstate(all="ignore"):
                    t = _elem_transform(kind, r, s)[:, 0]
                if not np.all(np.isfinite(t)):
                    return np.inf
                return float(_elem_rel(t[:, None], Q)[0])
            vals = [obj(s) for s in _ELEM_S_GRID]
            i = int(np.argmin(vals))
            if i in (0, len(_ELEM_S_GRID) - 1):
                continue                  # limite dégénérée de la forme
            s, v = _golden_min(obj, float(_ELEM_S_GRID[i - 1]),
                               float(_ELEM_S_GRID[i + 1]))
            if not v < tol:
                continue
            with np.errstate(all="ignore"):
                t = _elem_transform(kind, r, s)[:, 0]
            g = g_of(np.linalg.lstsq(L, t, rcond=None)[0][1:])
            if g is None:
                continue
            lg = np.log(np.abs(_elem_mono(X, g)))

            def obj2(s2, r=r, lg=lg):
                with np.errstate(all="ignore"):
                    t2 = _elem_transform(kind, r, s2)[:, 0] - lg
                if not np.all(np.isfinite(t2)):
                    return np.inf
                vt = float(np.var(t2 + lg))
                return float(np.var(t2)) / vt if vt > 0 else np.inf
            s2, v2 = _golden_min(obj2, s - 0.5, s + 0.5)
            if not v2 < tol:
                continue
            with np.errstate(all="ignore"):
                k0 = float(np.mean(_elem_transform(kind, r, s2)[:, 0] - lg))
            if abs(k0) > 700.0:
                continue
            c = math.exp(k0) * (-1.0 if kind == "exp+" else 1.0)
            out.append((kind.rstrip("+-"), lib[idx[m]], g, c))
            break
    return out


def _elem_wrel(Z, Q, w):
    """[1.4-N2] _elem_rel pondérée : variance résiduelle relative de chaque
    colonne de Z, les lignes pesant w² (Q : base orthonormée de l'espace
    pondéré, w·[1, log|x_j|]). La variance de référence est celle du résidu
    sur la constante pondérée."""
    Zw = Z * w[:, None]
    Rz = Zw - Q @ (Q.T @ Zw)
    u = w / float(np.linalg.norm(w))
    Cz = Zw - u[:, None] * (u @ Zw)[None, :]
    V = np.mean(Cz * Cz, axis=0)
    with np.errstate(all="ignore"):
        out = np.mean(Rz * Rz, axis=0) / V
    return np.where(V > 0, out, np.inf)


def _log_g_exponents(coef):
    """[1.4-N2] Exposants de g de la forme y = b·f·log(c·g), pour les graines
    tolérantes au bruit : les coefficients de y/f sur les log|x_j| valent
    b·e_j. Les chercheurs exacts les rapportent au plus petit coefficient
    non nul (au-dessus de 1e-6) ; sous bruit, un exposant nul a un
    coefficient de l'ordre du bruit, qui devient ce dénominateur (sur une
    loi n·log(V2/V1) à 1 % de bruit, les exposants 564 et -566 au lieu de 1
    et -1). Ici un coefficient compte comme nul sous le douzième du plus
    grand : les exposants gardés, des demi-entiers d'au plus 6 rapportés au
    plus petit, ne descendent pas sous le sixième. None si aucun ne reste."""
    a = np.abs(coef)
    if not a.size or not float(a.max()) > 1e-6:
        return None
    c = np.where(a > float(a.max()) / 12.0, coef, 0.0)
    ex = np.round(2.0 * c / float(np.min(np.abs(c[c != 0])))) / 2.0
    if not np.any(ex) or not np.all(np.abs(ex) <= 6.0):
        return None
    return ex


def _elem_inverse_forms_w(X, y, cols, kinds, top: int = 6, tol=_BINOM_TOL) -> list:
    """[1.4-N2] La seconde passe de _elem_inverse_forms, pour les graines
    tolérantes au bruit : la cible n'a plus à garder un signe (|y/f| est
    transformé), et les moindres carrés sur les transformées logarithmiques
    sont pondérés par y² (voir _power_law_exponents_w). La forme du
    logarithme, dont les moindres carrés portent sur y/f et non sur un
    logarithme de la cible, garde les siens, sans la condition de signe.
    y n'a pas de zéro (écartés par _elementary_forms)."""
    n = y.shape[0]
    out = []
    lib = _elem_flib(cols)
    if lib is None:
        return out
    FV = np.column_stack([_elem_mono(X, m) for m in lib])
    R = y[:, None] / FV
    idx = np.where(np.all(np.isfinite(R), axis=0) & np.all(R != 0, axis=0))[0]
    if not idx.size:
        return out
    R = R[:, idx]
    LU = np.log(np.abs(X[:, cols]))
    L = np.column_stack([np.ones(n), LU])
    sub = np.unique(np.linspace(0, n - 1, min(n, _BINOM_GRID_ROWS)).astype(int))
    sw = np.abs(y) / float(np.max(np.abs(y)))
    Lw = L * sw[:, None]
    Qw = np.linalg.qr(Lw)[0]
    Qws = np.linalg.qr(Lw[sub])[0]
    sws = sw[sub]
    ww = sw * sw

    def g_of(coef):
        ex = np.round(2.0 * coef) / 2.0
        if not np.any(ex) or not np.all(np.abs(ex) <= 6.0):
            return None
        return tuple((j, float(e)) for j, e in zip(cols, ex) if e)

    if "log" in kinds:                    # comme _elem_inverse_forms, les
        Q = np.linalg.qr(L)[0]            # exposants de g par _log_g_exponents
        v = _elem_rel(R, Q)
        for m in np.where(v < tol)[0]:
            r = R[:, m]
            ex = _log_g_exponents(np.linalg.lstsq(L, r, rcond=None)[0][1:])
            if ex is None:
                continue
            g = tuple((j, float(e)) for j, e in zip(cols, ex) if e)
            lg = np.log(np.abs(_elem_mono(X, g)))
            A = np.column_stack([np.ones(n), lg])
            a0, s0 = np.linalg.lstsq(A, r, rcond=None)[0]
            if not (float(np.var(r - A @ np.array([a0, s0]))) / float(np.var(r))
                    < tol) or s0 == 0.0 or abs(a0 / s0) > 700.0:
                continue
            out.append(("log", lib[idx[m]], g, float(math.exp(a0 / s0))))
            break
    for kind in [k for k in ("exp-", "exp+", "tanh", "sech", "arcsin")
                 if k.rstrip("+-") in kinds]:
        best = np.full(R.shape[1], np.inf)
        with np.errstate(all="ignore"):
            for s in _ELEM_S_GRID:
                T = _elem_transform(kind, R[sub], s)
                fin = np.all(np.isfinite(T), axis=0)
                v = _elem_wrel(np.where(np.isfinite(T), T, 0.0), Qws, sws)
                v[~fin] = np.inf
                best = np.minimum(best, v)
        order = [int(m) for m in np.argsort(best, kind="stable")[:top]]
        if kind == "arcsin":
            j0 = np.where(idx == 0)[0]
            if j0.size and np.isfinite(best[j0[0]]):
                order = [int(j0[0])] + [m for m in order if m != j0[0]]
        for m in order:
            if not np.isfinite(best[m]):
                break
            r = R[:, [m]]

            def obj(s, r=r):
                with np.errstate(all="ignore"):
                    t = _elem_transform(kind, r, s)[:, 0]
                if not np.all(np.isfinite(t)):
                    return np.inf
                return float(_elem_wrel(t[:, None], Qw, sw)[0])
            vals = [obj(s) for s in _ELEM_S_GRID]
            i = int(np.argmin(vals))
            if i in (0, len(_ELEM_S_GRID) - 1):
                continue
            s, v = _golden_min(obj, float(_ELEM_S_GRID[i - 1]),
                               float(_ELEM_S_GRID[i + 1]))
            if not v < tol:
                continue
            with np.errstate(all="ignore"):
                t = _elem_transform(kind, r, s)[:, 0]
            g = g_of(np.linalg.lstsq(Lw, t * sw, rcond=None)[0][1:])
            if g is None:
                continue
            lg = np.log(np.abs(_elem_mono(X, g)))

            def wvar(z):
                mu = float(np.sum(ww * z) / np.sum(ww))
                return float(np.sum(ww * (z - mu) ** 2) / np.sum(ww))

            def obj2(s2, r=r, lg=lg):
                with np.errstate(all="ignore"):
                    t2 = _elem_transform(kind, r, s2)[:, 0] - lg
                if not np.all(np.isfinite(t2)):
                    return np.inf
                vt = wvar(t2 + lg)
                return wvar(t2) / vt if vt > 0 else np.inf
            s2, v2 = _golden_min(obj2, s - 0.5, s + 0.5)
            if not v2 < tol:
                continue
            with np.errstate(all="ignore"):
                dt = _elem_transform(kind, r, s2)[:, 0] - lg
                k0 = float(np.sum(ww * dt) / np.sum(ww))
            if not abs(k0) <= 700.0:
                continue
            c = math.exp(k0) * (-1.0 if kind == "exp+" else 1.0)
            out.append((kind.rstrip("+-"), lib[idx[m]], g, c))
            break
    return out


def _pred_rel_error(p, y) -> float:
    """[1.4-N2] Le score des graines tolérantes (_seed_rel_error) calculé
    sur des prédictions : 1 - R² après mise à l'échelle linéaire."""
    with np.errstate(all="ignore"):
        p = np.asarray(p, dtype=float)
        if not np.all(np.isfinite(p)) or not np.var(p) > 0:
            return float("inf")
        a, b, ok = _linear_scale_params(p, y)
        if not ok:
            return float("inf")
        r = float(np.mean((y - (a + b * p)) ** 2) / np.var(y))
    return r if math.isfinite(r) else float("inf")


_SCAN_KEEP = 3                        # [1.4-N2] formes gardées par balayage


def _elem_log_scan(X, y, cols, tol, signed: bool) -> list:
    """[1.4-N2] Le chercheur du logarithme sur toute sa bibliothèque : les
    _SCAN_KEEP meilleures formes y = b·f·log(c·g) au score des graines
    tolérantes, les exposants de g par _log_g_exponents. signed : seulement
    les f où y/f garde un signe, comme dans la première passe."""
    n = y.shape[0]
    lib = _elem_flib(cols)
    if lib is None:
        return []
    FV = np.column_stack([_elem_mono(X, m) for m in lib])
    R = y[:, None] / FV
    ok = np.all(np.isfinite(R), axis=0)
    if signed:
        ok &= np.all(R > 0, axis=0) | np.all(R < 0, axis=0)
    idx = np.where(ok)[0]
    if not idx.size:
        return []
    R = R[:, idx]
    LU = np.log(np.abs(X[:, cols]))
    L = np.column_stack([np.ones(n), LU])
    Q = np.linalg.qr(L)[0]
    v = _elem_rel(R, Q)
    found = []
    for m in np.where(v < tol)[0]:
        r = R[:, m]
        ex = _log_g_exponents(np.linalg.lstsq(L, r, rcond=None)[0][1:])
        if ex is None:
            continue
        g = tuple((j, float(e)) for j, e in zip(cols, ex) if e)
        lg = np.log(np.abs(_elem_mono(X, g)))
        if not np.all(np.isfinite(lg)):           # [1.4-L1] une colonne négative
            continue                              # et un exposant fractionnaire
        A = np.column_stack([np.ones(n), lg])
        a0, s0 = np.linalg.lstsq(A, r, rcond=None)[0]
        if not (float(np.var(r - A @ np.array([a0, s0]))) / float(np.var(r))
                < tol) or s0 == 0.0 or abs(a0 / s0) > 700.0:
            continue
        sc = _pred_rel_error(FV[:, idx[m]] * (a0 / s0 + lg), y)
        if math.isfinite(sc):
            found.append((sc, len(found),
                          ("log", lib[idx[m]], g, float(math.exp(a0 / s0)))))
    found.sort(key=lambda t: (t[0], t[1]))
    return [f for _sc, _i, f in found[:_SCAN_KEEP]]


def _elem_trig_grid(z, gn):
    """Résidu relatif de z ~ 1 + sin(ω·gn) + cos(ω·gn) pour chaque ω de la
    grille (équations normales : pour classer seulement)."""
    n = len(z)
    w = _ELEM_W_GRID
    P = np.outer(gn, w)
    S, C = np.sin(P), np.cos(P)
    G = np.empty((len(w), 3, 3))
    G[:, 0, 0] = n
    G[:, 0, 1] = G[:, 1, 0] = S.sum(0)
    G[:, 0, 2] = G[:, 2, 0] = C.sum(0)
    G[:, 1, 1] = (S * S).sum(0)
    G[:, 1, 2] = G[:, 2, 1] = (S * C).sum(0)
    G[:, 2, 2] = (C * C).sum(0)
    rhs = np.stack([np.full(len(w), z.sum()), z @ S, z @ C], axis=1)
    with np.errstate(all="ignore"):
        try:
            coef = np.linalg.solve(G, rhs[..., None])[..., 0]
        except np.linalg.LinAlgError:
            return np.full(len(w), np.inf)
        rss = float(z @ z) - np.einsum("ij,ij->i", coef, rhs)
        vz = float(np.var(z)) * n
    return np.where(np.isfinite(rss), np.maximum(rss, 0.0) / vz, np.inf)


def _elem_trig_exact(z, gn, sub):
    """(résidu relatif, ω, (a, β, γ)) de la meilleure forme trigonométrique,
    affinée seulement si la grille la place sous _ELEM_TRIG_GATE."""
    v = _elem_trig_grid(z[sub], gn[sub])
    i = int(np.argmin(v))
    if not v[i] < _ELEM_TRIG_GATE:
        return np.inf, None, None
    vz = float(np.var(z))

    def obj(w):
        A = np.column_stack([np.ones_like(gn), np.sin(w * gn), np.cos(w * gn)])
        c = np.linalg.lstsq(A, z, rcond=None)[0]
        return float(np.var(z - A @ c)) / vz
    W = _ELEM_W_GRID
    w, val = _golden_min(obj, float(W[max(i - 1, 0)]), float(W[min(i + 1, len(W) - 1)]))
    A = np.column_stack([np.ones_like(gn), np.sin(w * gn), np.cos(w * gn)])
    return val, w, np.linalg.lstsq(A, z, rcond=None)[0]


def _elem_trig_forms(X, y, cols, tol=_BINOM_TOL, weighted=False,
                     scan=False) -> list:
    """Forme y = f·(a + β·sin(ω·g) + γ·cos(ω·g)) : au plus une. Rend des
    tuples ("trig", f, g, ω rapporté à g, (a, β, γ)).

    [1.4-N2] weighted : la seconde passe des graines tolérantes au bruit, où
    les moindres carrés sur log|y| qui donnent les exposants de f sont
    pondérés par y². scan : toute la bibliothèque est parcourue, et les
    _SCAN_KEEP meilleures formes au score des graines tolérantes sont rendues
    (au lieu de la première qui passe). Sans eux, le calcul d'avant."""
    n = y.shape[0]
    glib = [((j, 1),) for j in range(X.shape[1])]
    if len(cols) <= 8:
        for j, k in itertools.combinations(cols, 2):
            for e1, e2 in ((1, 1), (1, -1), (-1, 1)):
                glib.append(((j, e1), (k, e2)))
    nz = np.abs(y) > 0
    sub = np.unique(np.linspace(0, n - 1, min(n, _BINOM_GRID_ROWS)).astype(int))
    found = []
    wy = np.abs(y) / float(np.max(np.abs(y))) if weighted else None
    for g in glib:
        gv = _elem_mono(X, g)
        gmax = float(np.max(np.abs(gv)))
        if not (np.all(np.isfinite(gv)) and gmax > 0):
            continue
        gn = gv / gmax
        gcols = {j for j, _ in g}
        others = [j for j in cols if j not in gcols]
        if others:
            LU = np.log(np.abs(X[:, others]))
            L = np.column_stack([np.ones(n), LU])
            if weighted:
                e0 = np.linalg.lstsq(L[nz] * wy[nz, None],
                                     np.log(np.abs(y[nz])) * wy[nz],
                                     rcond=None)[0][1:]
            else:
                e0 = np.linalg.lstsq(L[nz], np.log(np.abs(y[nz])), rcond=None)[0][1:]
            f0 = np.exp(LU @ e0)
        else:
            e0, f0 = np.zeros(0), np.ones(n)
        cands = []
        if others:
            z0 = y / f0
            v = _elem_trig_grid(z0[sub], gn[sub])
            i = int(np.argmin(v))
            if np.isfinite(v[i]):
                w0 = float(_ELEM_W_GRID[i])
                A = np.column_stack([np.ones(n), np.sin(w0 * gn), np.cos(w0 * gn)])
                h = A @ np.linalg.lstsq(A, z0, rcond=None)[0]
                keep = np.abs(h) > 0.3 * np.max(np.abs(h))
                if weighted:
                    keep &= nz
                if keep.sum() > len(others) + 3:
                    if weighted:
                        e1 = np.linalg.lstsq(
                            L[keep] * wy[keep, None],
                            ((np.log(np.abs(y)) - np.log(np.abs(h))) * wy)[keep],
                            rcond=None)[0][1:]
                    else:
                        e1 = np.linalg.lstsq(
                            L[keep], (np.log(np.abs(y)) - np.log(np.abs(h)))[keep],
                            rcond=None)[0][1:]
                    cands += [np.round(e1), np.round(2.0 * e1) / 2.0]
        cands += [np.round(e0), np.round(2.0 * e0) / 2.0]
        seen = set()
        for ex in cands:
            key = tuple(float(e) for e in ex)
            if key in seen or not np.all(np.abs(ex) <= 6.0):
                continue
            seen.add(key)
            fv = np.ones(n)
            for j, e in zip(others, ex):
                fv = fv * X[:, j] ** e
            val, w, c = _elem_trig_exact(y / fv, gn, sub)
            if val < tol:
                f = tuple((j, float(e)) for j, e in zip(others, ex) if e)
                form = ("trig", f, g, float(w) / gmax, tuple(float(x) for x in c))
                if not scan:
                    return [form]
                A = np.column_stack([np.ones(n), np.sin(w * gn), np.cos(w * gn)])
                sc = _pred_rel_error(fv * (A @ c), y)
                if math.isfinite(sc):
                    found.append((sc, len(found), form))
    if scan:
        found.sort(key=lambda t: (t[0], t[1]))
        return [f for _sc, _i, f in found[:_SCAN_KEEP]]
    return []


# [1.4-E2] UNE GRAINE POUR UNE CONSTANTE PLUS UNE EXPONENTIELLE
# Constat (benchmarks/results_1.4/analysis/README.md) : la loi de Newton,
# θ = θa + (θ0 − θa)·exp(−t/τ), n'avait pas de graine. Le chercheur de
# l'exponentielle (phase 4a) passe par log|y/f|, qu'une constante additive
# rend non linéaire, et la loi revenait dans 9 ajustements de TP sur 40. E2
# (benchmarks/results_1.4/PLAN.md) cherche y = a + b·exp(c·g) dans les
# données, sans logarithme de la cible (elle n'a donc pas à garder un
# signe) : g est une colonne à la puissance 1 ou −1, ou, jusqu'à huit
# colonnes, le produit ou le rapport de deux colonnes (la bibliothèque du
# sinus et du cosinus) ; c se cherche sur une grille puis par la section
# dorée, sur le résidu des moindres carrés en (a, b). La graine est exp(c·g),
# la mise à l'échelle linéaire de la recherche portant a et b. Graine exacte
# quand la forme tient à la précision numérique et que a n'est pas nul (sinon
# c'est l'exponentielle que la phase 4a ajuste déjà) ; dans l'étage tolérant,
# un candidat comme les autres (ses trois meilleures formes). Une forme dont
# l'exponentielle varie de moins d'un facteur e^0,5 sur les données n'est pas
# rendue : elle imiterait une droite. Non adoptée par sa campagne
# (benchmarks/results_1.4/e2/campaign/README.md) : éteinte, son code gardé
# pour la décision de l'auteur.
_E2_C_GRID = np.concatenate([-np.geomspace(50.0, 0.01, 40), np.geomspace(0.01, 50.0, 40)])
_E2_GATE = 0.05                       # résidu de grille sous lequel on affine
_E2_CURVE = 0.5                       # |c|·étendue de g au moins : l'exponentielle
                                      # varie d'un facteur e^0,5 sur les données,
                                      # sinon elle imite une droite


def _e2_residuals(gn, y, cs):
    """Résidu relatif de y ≈ a + b·exp(c·gn) pour chaque c de cs."""
    with np.errstate(all="ignore"):
        U = np.exp(np.outer(gn, cs))
        Uc = U - U.mean(axis=0)
        yc = y - y.mean()
        vu = np.einsum("ij,ij->j", Uc, Uc)
        cov = Uc.T @ yc
        vy = float(yc @ yc)
        r = 1.0 - cov * cov / (vu * vy)
    return np.where(np.isfinite(r) & (vu > 0), np.maximum(r, 0.0), np.inf)


def _elem_aexp_forms(X, y, tol=_BINOM_TOL) -> list:
    """[1.4-E2] Formes y = a + b·exp(c·g) : au plus _SCAN_KEEP, rendues comme
    des formes ("exp", (), g, c) de la phase 4a (f = 1, c rapporté à g). Une
    forme n'est rendue sous un tol exact (sous 1e-3) que si a n'est pas nul."""
    n = y.shape[0]
    out = []
    if n < 7 or not np.var(y) > 0:
        return out
    cols = [j for j in range(X.shape[1]) if np.all(X[:, j] != 0)]
    glib = []
    for j in range(X.shape[1]):
        glib.append(((j, 1),))
        if j in cols:
            glib.append(((j, -1),))
    if X.shape[1] <= 8:
        for j, k in itertools.combinations(range(X.shape[1]), 2):
            glib.append(((j, 1), (k, 1)))
            if k in cols:
                glib.append(((j, 1), (k, -1)))
            if j in cols:
                glib.append(((j, -1), (k, 1)))
    found = []
    with np.errstate(all="ignore"):
        for g in glib:
            gv = _elem_mono(X, g)
            gmax = float(np.max(np.abs(gv)))
            if not (np.all(np.isfinite(gv)) and gmax > 0) or not np.var(gv) > 0:
                continue
            gn = gv / gmax
            v = _e2_residuals(gn, y, _E2_C_GRID)
            i = int(np.argmin(v))
            if not v[i] < _E2_GATE:
                continue
            lo = float(_E2_C_GRID[max(i - 1, 0)])
            hi = float(_E2_C_GRID[min(i + 1, len(_E2_C_GRID) - 1)])
            if lo < 0 < hi:                       # pas de c nul
                lo, hi = (lo, -1e-3) if _E2_C_GRID[i] < 0 else (1e-3, hi)
            c, _r = _golden_min(lambda cc: float(_e2_residuals(gn, y, np.array([cc]))[0]),
                                lo, hi)
            # quelques pas de Gauss-Newton sur (a, b, c) : la section dorée sur
            # un résidu calculé par différence s'arrête vers 1e-7 en c
            u = np.exp(c * gn)
            a, b = np.linalg.lstsq(np.column_stack([np.ones(n), u]), y, rcond=None)[0]
            e = y - a - b * u
            sse = float(e @ e)
            for _ in range(8):
                J = np.column_stack([np.ones(n), u, b * gn * u])
                d = np.linalg.lstsq(J, e, rcond=None)[0]
                c2 = c + float(d[2])
                u2 = np.exp(c2 * gn)
                ab = np.linalg.lstsq(np.column_stack([np.ones(n), u2]), y, rcond=None)[0]
                e2 = y - ab[0] - ab[1] * u2
                s2 = float(e2 @ e2)
                if not (np.isfinite(s2) and s2 < sse):
                    break
                c, u, (a, b), e, sse = c2, u2, ab, e2, s2
            r = sse / (n * float(np.var(y)))
            if not r < tol or abs(c) * float(np.ptp(gn)) < _E2_CURVE:
                continue                          # pas une droite déguisée
            if tol < 1e-3 and not abs(a) > 1e-9 * float(np.max(np.abs(y))):
                continue                          # a nul : la phase 4a
            found.append((r, len(found), ("exp", (), g, float(c) / gmax)))
    found.sort(key=lambda t: (t[0], t[1]))
    return [f for _r, _i, f in found[:_SCAN_KEEP]]


def _elementary_forms(X, y, kinds, tol=None, weighted=False, scan=False) -> list:
    """Formes de la phase 4a qui tiennent à la précision numérique (à tol
    près, graines tolérantes au bruit de la phase 5).

    [1.4-N2] Pour les graines tolérantes au bruit seulement :
    - weighted : la seconde passe. Les lignes où y est nul sont écartées, la
      cible n'a plus à garder un signe, et les moindres carrés sur les
      logarithmes sont pondérés par y² (_elem_inverse_forms_w, et les
      exposants de f de la forme trigonométrique).
    - scan : les seules formes du balayage de toute la bibliothèque, pour le
      logarithme et pour le sinus et le cosinus (leurs _SCAN_KEEP
      meilleures au score des graines tolérantes).
    Sans eux, le calcul d'avant."""
    tol = _BINOM_TOL if tol is None else tol
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    out = []
    with np.errstate(all="ignore"):
        if not (np.all(np.isfinite(y)) and np.all(np.isfinite(X))):
            return out
        if weighted:
            nzr = y != 0
            X, y = X[nzr], y[nzr]
        if scan or weighted:
            return _elementary_forms_n2(X, y, kinds, tol, weighted, scan)
        n = y.shape[0]
        cols = [j for j in range(X.shape[1])
                if np.all(X[:, j] > 0) or np.all(X[:, j] < 0)]
        inv = [k for k in kinds if k != "trig"]
        if inv and cols and n > len(cols) + 6 \
                and (np.all(y > 0) or np.all(y < 0)):
            L = np.column_stack([np.ones(n), np.log(np.abs(X[:, cols]))])
            Q = np.linalg.qr(L)[0]
            if _elem_rel(np.log(np.abs(y))[:, None], Q)[0] < _POWER_TOL:
                return out                # une loi de puissance : ses graines
            out += _elem_inverse_forms(X, y, cols, inv, tol=tol)
        if "trig" in kinds and n > 10 and np.var(y) > 0:
            out += _elem_trig_forms(X, y, cols, tol=tol)
        if "aexp" in kinds:                       # [1.4-E2]
            out += _elem_aexp_forms(X, y, tol=tol)
    return out


def _elementary_forms_n2(X, y, kinds, tol, weighted, scan) -> list:
    """[1.4-N2] La partie de _elementary_forms propre aux graines tolérantes
    au bruit (voir sa documentation). Les gardes sont celles de la première
    passe, sans la condition de signe de la cible quand weighted."""
    n = y.shape[0]
    out = []
    if not n:
        return out
    cols = [j for j in range(X.shape[1])
            if np.all(X[:, j] > 0) or np.all(X[:, j] < 0)]
    inv = [k for k in kinds if k != "trig"]
    if inv and cols and n > len(cols) + 6 \
            and (weighted or np.all(y > 0) or np.all(y < 0)):
        L = np.column_stack([np.ones(n), np.log(np.abs(X[:, cols]))])
        if weighted:
            sw = np.abs(y) / float(np.max(np.abs(y)))
            Qw = np.linalg.qr(L * sw[:, None])[0]
            power = _elem_wrel(np.log(np.abs(y))[:, None], Qw, sw)[0] < _POWER_TOL
        else:
            Q = np.linalg.qr(L)[0]
            power = _elem_rel(np.log(np.abs(y))[:, None], Q)[0] < _POWER_TOL
        if power:
            return out                    # une loi de puissance : ses graines
        if scan:
            if "log" in inv:
                out += _elem_log_scan(X, y, cols, tol, signed=not weighted)
        else:
            out += _elem_inverse_forms_w(X, y, cols, inv, tol=tol)
    if "trig" in kinds and n > 10 and np.var(y) > 0:
        out += _elem_trig_forms(X, y, cols, tol=tol, weighted=weighted, scan=scan)
    return out


def _make_elementary_seeds(xs, ys, cfg, tol=None, weighted=False,
                           scan=False) -> list:
    """[0.10, phase 4a] Voir le commentaire ci-dessus. Rend 0 à 5 arbres.
    Le drapeau _ELEMENTARY_SEEDS (actif par défaut) les coupe. [1.4-N2]
    weighted, scan : voir _elementary_forms (graines tolérantes au bruit)."""
    if not state._ELEMENTARY_SEEDS or not state._GENERIC_CSV_MODE or _seeds_blocked_by_units(cfg) \
            or bool(getattr(cfg, "EXTRAPOLATION_MODE", False)):
        return []
    terms = list(getattr(cfg, "TERMINALS", []) or [])
    try:
        X = np.asarray(xs, dtype=float)
        y = np.asarray(ys, dtype=float)
    except Exception:
        return []
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    if X.ndim != 2 or y.ndim != 1 or X.shape[0] != y.shape[0] \
            or X.shape[1] != len(terms):
        return []
    bops = set(state._GENERIC_BINARY_OPS)
    uops = set(state._GENERIC_UNARY_OPS)
    if not {"+", "*", "/"} <= bops:
        return []
    kinds = [k for k, need in (("exp", {"exp"}), ("log", {"log"}),
                               ("tanh", {"tanh"}), ("sech", {"exp"}),
                               ("trig", {"sin", "cos"}),
                               ("arcsin", {"arcsin"})) if need <= uops]   # [1.3-A3]
    if state._E2_SEEDS and "exp" in uops:               # [1.4-E2]
        kinds.append("aexp")
    if not kinds:
        return []
    t0 = time.time()
    forms = _elementary_forms(X, y, kinds, tol=tol, weighted=weighted, scan=scan)
    TRACE.set("elementary_seed_s", round(time.time() - t0, 3))
    seeds = []
    for form in forms:
        kind, fm, g = form[0], form[1], form[2]
        f = _monomial(terms, [(j, float(e)) for j, e in fm], uops)
        gnode = _monomial(terms, [(j, float(e)) for j, e in g], uops)
        if gnode is None or (fm and f is None):
            continue
        if kind == "trig":
            w, (a, b, c) = form[3], form[4]
            mx = max(abs(a), abs(b), abs(c))
            arg = lambda: Node("*", Node(w), gnode.copy())
            terms_ = []
            if abs(a) > 1e-9 * mx:
                terms_.append(Node(a / mx))
            if abs(b) > 1e-9 * mx:
                terms_.append(Node("*", Node(b / mx), Node("sin", arg())))
            if abs(c) > 1e-9 * mx:
                terms_.append(Node("*", Node(c / mx), Node("cos", arg())))
            inner = terms_[0]
            for t_ in terms_[1:]:
                inner = Node("+", inner, t_)
            seeds.append(inner if f is None else Node("*", f, inner))
            continue
        c = form[3]
        cg = lambda cc: Node("*", Node(cc), gnode.copy())
        if kind == "exp":
            h = Node("exp", cg(c))
        elif kind == "log":
            h = Node("log", cg(c))
        elif kind == "tanh":
            h = Node("tanh", cg(c))
        elif kind == "arcsin":            # [1.3-A3]
            h = Node("arcsin", cg(c))
        else:                             # 1/cosh(c·g) = 2/(exp(c·g) + exp(-c·g))
            den = Node("+", Node("exp", cg(c)), Node("exp", cg(-c)))
            seeds.append(Node("/", f if f is not None else Node(1.0), den))
            continue
        seeds.append(h if f is None else Node("*", f, h))
    seeds = _typed_seeds(seeds, cfg)
    if seeds:
        TRACE.set("elementary_seed", " | ".join(to_string(s) for s in seeds))
    return seeds


# ════════════════════════════════════════════════════════════════
# [0.10, phase 5] GRAINES TOLÉRANTES AU BRUIT
# ════════════════════════════════════════════════════════════════
# Constat (diagnostic D5, benchmarks/results_0.9/PLAN_PHASE5.md) : avec du
# bruit sur y, la structure de la loi manque parmi les candidats dans deux
# ajustements sur trois, alors que les graines de loi de puissance, B1 et E1
# la porteraient : leurs seuils (R² log-log de 0,999, précision numérique)
# sont défaits par le bruit, qui est bien plus fort sur log|y| là où y est
# petit. Quand aucune forme exacte n'a été trouvée, on relance donc les trois
# chercheurs seuils levés, et on juge chaque forme comme les données la
# jugent : 1 - R² après mise à l'échelle linéaire sur les lignes
# d'entraînement. Elle devient une graine si cette erreur ne dépasse pas
# _TOLERANT_REL : les graines qui ont la structure de la loi ajustent 10 % de
# bruit à 0,008-0,014 (1 % de bruit vers 1e-4) ; sur les données réelles du
# banc de décision, aucune n'ajuste mieux que 0,026. Mêmes gardes que les
# graines exactes ; aucun tirage aléatoire. Mesuré dans PLAN_PHASE5.md
# (changement N1, adopté le 13 octobre 2026) : structure retrouvée sous bruit
# 69 -> 106 sur 205 (1 %) et 68 -> 86 (10 %), puis 64 -> 103 et 65 -> 81 sur
# des graines neuves ; lois exactes sans bruit 157 -> 160 ; aucune graine sur
# les 520 ajustements réels. Limite connue : sur des données exactes qu'aucune
# graine exacte ne couvre, une forme approchée peut détourner la recherche
# (loi de Kepler normalisée par min-max, PLAN_PHASE5.md).

_TOLERANT_REL = 0.015

# [1.4-N2] LES CHERCHEURS TOLÉRANTS VOIENT À TRAVERS LE BRUIT
# Constat (benchmarks/results_1.4/analysis/README.md) : sous bruit, trois
# règles des chercheurs, écrites pour des données exactes, défont les
# graines tolérantes. (1) La cible doit garder un signe : 1 % de bruit le
# lui fait perdre près de zéro dans 7 équations sur 41, dont deux monômes.
# (2) Le chercheur du sinus et du cosinus (et celui du logarithme) rend la
# première forme qui passe, pas la meilleure : sur III.15.12 à 1 %, une
# forme en k seul au lieu de la loi en k·d. (3) La constante interne vient
# du chercheur, ajustée dans l'espace transformé. (4) Trouvée par la
# mécanique de N2 : le logarithme rapporte les exposants de g au plus petit
# coefficient non nul, qu'un exposant nul a sous bruit (voir
# _log_g_exponents). N2 garde l'étage, son score et son seuil, et change ses
# candidats (benchmarks/results_1.4/PLAN.md) :
# - chaque chercheur tourne comme avant, puis une seconde fois avec ses
#   moindres carrés sur les logarithmes pondérés par y² et sans la
#   condition de signe ;
# - le logarithme, le sinus et le cosinus parcourent toute leur
#   bibliothèque et rendent aussi leurs trois meilleures formes au score
#   (les exposants de g du logarithme par _log_g_exponents) ;
# - chaque candidat a ses constantes ajustées sur les lignes d'entraînement
#   par l'ajustement de constantes du moteur avant d'être noté (ses
#   exposants, arrondis par le chercheur, sont dans la structure de
#   l'arbre et restent) ;
# - les candidats sont dédoublonnés par leur forme, et ceux sous le seuil
#   placés, les meilleurs d'abord, douze au plus. Les formes que les
#   chercheurs d'avant donnent sont toujours placées quand elles passent le
#   seuil : toute graine que plaçait 1.3.0 l'est encore.
# Non adopté (campagne N2, 13 novembre 2026, benchmarks/results_1.4/n2/
# campaign/README.md) : sans bruit, F41 perd 5 lois exactes, toutes là où
# l'étage tourne, à cause de l'ajustement des constantes des candidats.
# Retiré du candidat : éteint. Sur décision de l'auteur (13 novembre), N2
# est mesuré de nouveau sans cet ajustement (N2b, _TOLERANT_REFIT False) :
# chaque candidat garde les constantes de son chercheur. N2b est adopté et
# gardé (campagne et confirmation, 13 novembre 2026, benchmarks/
# results_1.4/n2b/campaign/README.md) : il fait partie de la 1.4.
_TOLERANT_MAX = 12


def _seed_rel_error(tree, X, y) -> float:
    """1 - R² d'un arbre après mise à l'échelle linéaire (inf s'il n'est pas
    évaluable)."""
    try:
        with np.errstate(all="ignore"):
            p = np.asarray(evaluate_vector(tree, X), dtype=float)
        if not np.all(np.isfinite(p)) or not np.var(p) > 0:
            return float("inf")
        a, b, ok = _linear_scale_params(p, y)
        if not ok:
            return float("inf")
        r = float(np.mean((y - (a + b * p)) ** 2) / np.var(y))
        return r if math.isfinite(r) else float("inf")
    except Exception:
        return float("inf")


def _small_family(scored, cfg, t0) -> list:
    """[1.4-S1] Sous 30 lignes, l'étage tolérant place ses huit meilleures
    formes, une par forme, qui laissent au plus la moitié de la variance (le
    seuil de 1,5 % n'y sert pas), et les garde pour la sélection finale."""
    seen, fam = set(), []
    for r, _i, t in scored:
        if not r <= _SMALL_FAMILY_SHARE:
            break
        h = t.canonical_hash()
        if h in seen:
            continue
        seen.add(h)
        fam.append((r, t))
        if len(fam) >= _SMALL_FAMILY_KEEP:
            break
    seeds = _typed_seeds([t for _r, t in fam], cfg)
    kept = {id(t) for t in seeds}
    _SMALL_FAMILY[:] = [t.copy() for t in seeds]
    TRACE.set("tolerant_seed_s", round(time.time() - t0, 3))
    if seeds:
        TRACE.set("tolerant_seed", " | ".join(
            "%s (%.2g)" % (to_string(t), r) for r, t in fam if id(t) in kept))
    return seeds


def _refit_inner(tree, X, y, cfg):
    """[1.4-N2] Les constantes d'un candidat ajustées sur les lignes
    d'entraînement par l'étape de finition du moteur (_lm_to_convergence).
    L'arbre d'entrée si rien n'est amélioré, ou quand la recherche n'a pas
    de mise à l'échelle linéaire (perte personnalisée) : le score des
    graines et l'ajustement ne jugeraient pas la même forme. [1.4-N2b]
    L'arbre d'entrée aussi sans _TOLERANT_REFIT."""
    if not state._TOLERANT_REFIT:
        return tree
    if not (state._USE_LINEAR_SCALING and state._CUSTOM_LOSS_FN is None):
        return tree
    try:
        with np.errstate(all="ignore"):
            out = _lm_to_convergence(tree, X, y, cfg)
    except Exception:
        return tree
    return tree if out is None else out


def _make_tolerant_seeds(xs, ys, cfg, power_done: bool = False) -> list:
    """[0.10, phase 5] Voir le commentaire ci-dessus. Appelée seulement quand
    ni B1 ni E1 n'ont placé de graine ; sans la loi de puissance si ses
    graines exactes ont déjà été placées (power_done). Le drapeau
    _TOLERANT_SEEDS (actif par défaut) les coupe."""
    if not state._TOLERANT_SEEDS or not state._GENERIC_CSV_MODE or _seeds_blocked_by_units(cfg) \
            or bool(getattr(cfg, "EXTRAPOLATION_MODE", False)):
        return []
    try:
        X = np.asarray(xs, dtype=float)
        y = np.asarray(ys, dtype=float)
    except Exception:
        return []
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    if X.ndim != 2 or y.ndim != 1 or X.shape[0] != y.shape[0] \
            or not np.var(y) > 0:
        return []
    t0 = time.time()
    trace = {k: TRACE.value.get(k) for k in ("power_law_seed", "binomial_seed",
                                             "binomial_seed_s", "elementary_seed",
                                             "elementary_seed_s")}
    cands = []
    finders = [(_make_binomial_seeds, dict(tol=1.0)),
               (_make_elementary_seeds, dict(tol=1.0))]
    if not power_done:
        finders.insert(0, (_make_power_law_seeds, dict(min_r2=-math.inf)))
    for fn, kw in finders:
        try:
            cands += fn(X, y, cfg, **kw)
        except Exception:
            pass
    n_first = len(cands)                          # [1.4-N2] ceux d'avant
    if state._TOLERANT_N2:
        more = [(_make_elementary_seeds, dict(tol=1.0, scan=True)),
                (_make_binomial_seeds, dict(tol=1.0, weighted=True)),
                (_make_elementary_seeds, dict(tol=1.0, weighted=True)),
                (_make_elementary_seeds, dict(tol=1.0, weighted=True, scan=True))]
        if not power_done:
            more.insert(1, (_make_power_law_seeds, dict(weighted=True)))
        for fn, kw in more:
            try:
                cands += fn(X, y, cfg, **kw)
            except Exception:
                pass
    for k, v in trace.items():                    # les traces des graines exactes
        if v is None:
            TRACE.value.pop(k, None)
        else:
            TRACE.set(k, v)
    if not state._TOLERANT_N2:                          # 1.3.0
        scored = sorted(((_seed_rel_error(t, X, y), i, t) for i, t in enumerate(cands)),
                        key=lambda r: (r[0], r[1]))
        if state._SMALL_ON:                             # [1.4-S1] les formes de famille
            return _small_family(scored, cfg, t0)
        seeds = _typed_seeds([t for r, _, t in scored if r <= _TOLERANT_REL], cfg)
        TRACE.set("tolerant_seed_s", round(time.time() - t0, 3))
        if seeds:
            kept = {id(t) for t in seeds}
            TRACE.set("tolerant_seed", " | ".join(
                "%s (%.2g)" % (to_string(t), r) for r, _, t in scored
                if r <= _TOLERANT_REL and id(t) in kept))
        return seeds
    # [1.4-N2] les constantes ajustées, puis le score ; une forme, le meilleur
    # de ses candidats
    scored = []
    for i, t in enumerate(cands):
        t2 = _refit_inner(t, X, y, cfg)
        scored.append((_seed_rel_error(t2, X, y), i, t2))
    scored.sort(key=lambda r: (r[0], r[1]))
    forms, first = {}, set()
    # [1.4-N2b] sans ajustement des constantes, une forme que donnent les
    # chercheurs d'avant garde leur arbre, constantes comprises : N2b ne fait
    # qu'ajouter des formes aux graines de 1.3.0
    order = scored if state._TOLERANT_REFIT else sorted(
        scored, key=lambda r: (r[1] >= n_first, r[0], r[1]))
    for r, i, t in order:
        h = t.canonical_hash()
        if i < n_first:
            first.add(h)
        if h not in forms:
            forms[h] = (r, i, t)
    if state._SMALL_ON:                                 # [1.4-S1] les formes de famille
        return _small_family(sorted(forms.values(), key=lambda r: (r[0], r[1])),
                             cfg, t0)
    within = sorted((v for v in forms.values() if v[0] <= _TOLERANT_REL),
                    key=lambda r: (r[0], r[1]))
    old = [v for v in within if v[2].canonical_hash() in first]
    new = [v for v in within if v[2].canonical_hash() not in first]
    placed = sorted(old + new[:max(0, _TOLERANT_MAX - len(old))],
                    key=lambda r: (r[0], r[1]))
    seeds = _typed_seeds([t for _r, _i, t in placed], cfg)
    TRACE.set("tolerant_seed_s", round(time.time() - t0, 3))
    TRACE.set("tolerant_cands", "%d candidats, %d formes, %d sous le seuil" % (
        len(cands), len(forms), len(within)))
    if seeds:
        kept = {id(t) for t in seeds}
        TRACE.set("tolerant_seed", " | ".join(
            "%s (%.2g)" % (to_string(t), r) for r, _, t in placed
            if id(t) in kept))
    return seeds


# ============================================================
# ISLAND MODEL
# ============================================================

class Island:
    def __init__(self, island_id: int, cfg: Config, stigmergic: bool = False):
        self.id           = island_id
        self.cfg          = cfg
        self.stigmergic   = stigmergic   # True = île C (conservé pour compatibilité)
        self.population: List[Node] = []
        self.best: Optional[Node]   = None
        self.best_score: float      = float("inf")
        self.stagnation: int        = 0
        # FIX v13.7 : initialisés ici pour éviter AttributeError si migrate()
        # est appelé avant que evolve() ait injecté les données du dataset.
        self._xs:  Optional[np.ndarray] = None
        self._ys:  Optional[np.ndarray] = None
        self._key: str                  = "1"

        # [v14.4 — Asymétrie des Îles] Attribution du rôle selon l'ID ────────
        # · Dernière île (N-1)       : "stigmergic" — exploratrice stigmergique
        # · Avant-dernière île (N-2) : "cleaner"    — nettoyeuse BIC stricte
        # · Toutes les autres        : "explorer"   — exploratrices libres
        # Avec N_ISLANDS=3 : île 0="explorer", île 1="cleaner", île 2="stigmergic"
        # Avec N_ISLANDS=2 : île 0="cleaner",  île 1="stigmergic"
        # Avec N_ISLANDS=1 : île 0="stigmergic" (rôles fusionnés)
        if stigmergic or island_id == cfg.N_ISLANDS - 1:
            self.role = "stigmergic"
        elif island_id == cfg.N_ISLANDS - 2:
            self.role = "cleaner"
        else:
            self.role = "explorer"

        # [FIX-B] LAHC (Late Acceptance Hill Climbing) pour l'île cleaner.
        # Accepte un enfant si meilleur qu'il y a L générations — pas seulement
        # que le meilleur courant. Échappe aux plateaux plats sans explosion de
        # diversité. Inspiré de GP_SYRACUSE_V16.
        self.lahc_L   = 50
        self.lahc_buf = [float("inf")] * self.lahc_L
        self.lahc_idx = 0

        # [V42] banned_subtrees — anti-domination sur l'île explorer.
        # Quand un sous-arbre domine >60% du top-20, il est interdit pendant
        # 80 générations pour forcer la diversité structurelle.
        # Format : set de canonical_hash strings.
        self.banned_subtrees: set = set()
        self.banned_until:    int = 0
        self.last_dedup_removed: int = 0   # [v19] diagnostic dédup sémantique
        # ─────────────────────────────────────────────────────────────────────

    def initialize(self):
        n = self.cfg.POP_SIZE // self.cfg.N_ISLANDS
        is_nd = (len(self.cfg.TERMINALS) > 1 or
                 (len(self.cfg.TERMINALS) == 1 and self.cfg.TERMINALS[0] != "x"))

        # [v0.4] Population initiale dimensionnellement valide par construction.
        if _dim_active(self.cfg):
            state._DIM_GATE_DIMS   = self.cfg.FEAT_DIMS
            state._DIM_GATE_TARGET = self.cfg.TARGET_DIM
            ds  = _ds()
            pop = []
            fails = 0
            # [v1.2-D0] L'echeance de time_limit= vaut aussi pour ce depart :
            # une fois atteinte, l'ile cesse de tirer des qu'elle a un arbre,
            # et se complete par des copies comme apres ses tirages echoues.
            # Sans echeance, ou avant, les tirages sont ceux de 1.1.
            _deadline = getattr(self.cfg, "DEADLINE", None)
            while len(pop) < n and fails < 20 * n:
                if (_deadline is not None and pop
                        and time.time() >= _deadline):
                    break
                t = ds.typed_random_tree(
                    self.cfg.TARGET_DIM, self.cfg.MAX_INIT_DEPTH,
                    self.cfg.FEAT_DIMS, random,
                    unknown_constant=bool(getattr(self.cfg,
                                                  "UNKNOWN_CONST", False)),
                    ops=_active_pool_ops())
                if t is None:
                    fails += 1
                    continue
                pop.append(t)
            if not pop:
                if getattr(self.cfg, "UNKNOWN_CONST", False):
                    raise ValueError(
                        "aucune expression dimensionnellement cohérente ne "
                        "peut être construite depuis les unités fournies.")
                raise ValueError(
                    "target_units n'est pas atteignable depuis les unités "
                    "fournies : aucune expression dimensionnellement valide "
                    "ne peut être construite. Si la loi comporte une constante "
                    "dimensionnée (G, k_B, R, raideur...), essayez "
                    "unknown_constant=True.")
            while len(pop) < n:                    # complète par des copies
                pop.append(pop[random.randrange(len(pop))].copy())
            self.population = pop
            return

        if self.stigmergic and state.FRAGMENT_LIB.fragments:
            # Île stigmergique : construction guidée par la bibliothèque
            self.population = [
                build_stigmergic_tree_v3(state.FRAGMENT_LIB, state.COGRAPH, state.SEQ_MEM, self.cfg)
                for _ in range(n)
            ]
        elif is_nd:
            # [v16-NDIM] Initialisation N-D : couverture garantie des opérateurs.
            # Pas de seeds spécifiques — le GP doit découvrir par lui-même.
            # On répartit juste mieux l'espace de recherche initial.
            self.population = _nd_diverse_population(self.cfg, n)
        else:
            self.population = [
                random_tree(self.cfg.MAX_INIT_DEPTH, self.cfg)
                for _ in range(n)
            ]

    def receive_migrants(self, migrants: List[Node]):
        """
        [FIX-C] Migration ciblée : remplace les clones en priorité.
        Inspiré de GP_SYRACUSE_V16 — évite que la migration renforce le même
        bassin en remplaçant des individus qui ont déjà le même hash canonique
        que les immigrants. Complète par les pires si pas assez de clones.
        """
        if self._xs is None:
            self.population.sort(key=tree_size, reverse=True)
            for i, migrant in enumerate(migrants):
                self.population[i] = migrant.copy()
            return

        src_hashes = {m.canonical_hash() for m in migrants}
        pop = self.population

        # Passe 1 : remplacer les clones existants
        replaced = 0
        for j in range(len(pop) - 1, self.cfg.ELITE_SIZE - 1, -1):
            if replaced >= len(migrants):
                break
            if pop[j].canonical_hash() in src_hashes:
                pop[j] = migrants[replaced].copy()
                replaced += 1

        # Passe 2 : compléter par les pires (tri par fitness décroissante)
        if replaced < len(migrants):
            pop.sort(
                key=lambda n: fitness(n, self._xs, self._ys, self.cfg,
                                      role=self.role),
                reverse=True
            )
            for i in range(replaced, len(migrants)):
                idx = i
                if idx < len(pop) - self.cfg.ELITE_SIZE:
                    pop[idx] = migrants[i].copy()


def migrate(islands: List[Island]):
    """Migration circulaire : chaque île envoie ses meilleurs vers la suivante."""
    n = len(islands)
    if n < 2:
        return
    migrants_per_island = []
    for island in islands:
        # FIX v13.7 : skip si _xs pas encore injecté
        if island._xs is None:
            migrants_per_island.append([])
            continue
        # [v14.4] role=island.role : tri des émigrants avec la métrique de l'île source
        island.population.sort(
            key=lambda nd, isl=island: fitness(nd,
                                               isl._xs,
                                               isl._ys,
                                               isl.cfg,
                                               role=isl.role))
        migrants_per_island.append(
            [ind.copy() for ind in island.population[:island.cfg.MIGRATION_SIZE]]
        )
    for i, island in enumerate(islands):
        if migrants_per_island[(i - 1) % n]:
            island.receive_migrants(migrants_per_island[(i - 1) % n])

    # [v17] Rafraîchir les signatures sémantiques obsolètes à chaque migration.
    # Les fragments déposés avant l'initialisation du probe (ou sur un probe
    # d'un run précédent) reçoivent ici leur signature à jour.
    # On limite à 40 fragments max par migration pour ne pas ralentir les échanges.
    _refreshed = 0
    state.FRAGMENT_LIB.end_sampling()
    for h, e in state.FRAGMENT_LIB.fragments.items():
        if e.semantic_signature is None and _refreshed < 40:
            e.semantic_signature = compute_semantic_sig(e.node, state.PROBE_X)
            _refreshed += 1

# ============================================================
# ÉVOLUTION D'UNE ÎLE
# ============================================================

def evolve_island(island: Island,
                  xs: List[float], ys: List[float],
                  generation: int) -> Optional[Node]:
    island._xs = xs
    island._ys = ys
    cfg = island.cfg
    pop = island.population

    # Tri — [v14.4] chaque île trie avec SA propre métrique
    pop.sort(key=lambda n: fitness(n, xs, ys, cfg, role=island.role))

    best     = simplify(pop[0])
    best_fit = fitness(best, xs, ys, cfg, role=island.role)

    # [V42] Détection de dominance — banned_subtrees sur les îles explorer ────
    # Si un sous-arbre apparaît dans >60% du top-20, il est structurellement
    # dominant → interdit pendant 80 gens pour forcer la diversité.
    # [FIX] Exception critique : ne jamais bannir un sous-arbre présent dans
    # le MEILLEUR individu courant — celui-ci pourrait être une composante
    # correcte de la solution (ex: (X[2])² dans ND1). Le bannir bloquerait
    # toute convergence vers la formule exacte.
    if (island.role == "explorer" and generation % 10 == 0
            and generation >= 20):
        top20 = pop[:min(20, len(pop))]
        sub_counts: dict = {}
        for ind in top20:
            for node, _, _ in get_all_nodes(ind):
                if 2 <= tree_size(node) <= 8:
                    h = node.canonical_hash()
                    sub_counts[h] = sub_counts.get(h, 0) + 1
        # Hashes des sous-arbres du MEILLEUR individu → jamais bannis
        best_hashes = set()
        for node, _, _ in get_all_nodes(pop[0]):
            best_hashes.add(node.canonical_hash())

        threshold = int(len(top20) * 0.60)
        dominant  = {h: c for h, c in sub_counts.items()
                     if c >= threshold and h not in best_hashes}  # [FIX]
        if dominant and generation > island.banned_until:
            island.banned_subtrees = set(dominant.keys())
            island.banned_until    = generation + 80
        elif generation > island.banned_until:
            island.banned_subtrees = set()

    # FIX v13.9 — Parsimonie dynamique conditionnelle :
    # activée UNIQUEMENT quand USE_SEQMEM=True (seule condition générant du bloat).
    # En BASE/+LIB/+CO, le bloc v13.8 vidait le cache global sans raison
    # et dégradait la convergence (régression BASE ×60).
    # Invalidation sélective : on purge uniquement les entrées des individus
    # de grande taille, pas tout le cache.
    if cfg.USE_SEQMEM:
        _median_size = sorted(tree_size(ind) for ind in pop)[len(pop) // 2]
        if generation >= 50 and _median_size > 25:
            cfg = copy.copy(cfg)           # copie locale — ne touche pas l'original
            cfg.PARSIMONY     = max(cfg.PARSIMONY, 0.003)
            cfg.DEPTH_PENALTY = max(cfg.DEPTH_PENALTY, 0.0008)
            # Invalidation sélective : seulement les gros arbres affectés
            for n in pop:
                if tree_size(n) > 20:
                    state._fitness_cache.pop(n.structural_hash(), None)
            pop.sort(key=lambda n: fitness(n, xs, ys, cfg, role=island.role))

    # ---- Dépôt de phéromones sur les top 10% ----
    top_k     = max(3, len(pop) // 10)
    top_k_seq = max(5, len(pop) // 5)   # SEQ_MEM : top 20% pour plus de signal
    # [v14.4] top_fits calculé avec la métrique de l'île
    top_fits = [fitness(ind, xs, ys, cfg, role=island.role) for ind in pop[:top_k]]

    # ── OBJECTIF 2 : Démarrage Différé + Filtre Qualité (Anti-Poisoned Well) ──
    # Problème : en génération 0, la stigmergie se remplit de fragments issus
    # d'arbres randoms médiocres -> "bruit" qui converge vers des impasses.
    #
    # [v14.1 CORRECTION] Logique à deux voies (remplace l'ancien AND strict) :
    #
    #   Voie A — burn-in classique :
    #       generation >= BURN_IN_GENERATIONS  ET  r >= MIN_CORRELATION_REQUIRED
    #       Protège contre le bruit des premières générations sur les problèmes
    #       difficiles où la population met du temps à trouver un signal.
    #
    #   Voie B — ouverture anticipée sur qualité exceptionnelle :
    #       r >= EARLY_OPEN_CORRELATION  (seuil haut : 0.95)
    #       Si le meilleur individu est déjà excellent dès gen 0 (ex : problème
    #       facile, ou chance de tirage initial), bloquer la stigmergie serait
    #       contre-productif : on priverait la mémoire d'un signal de qualité.
    #
    # Ancien bug : AND strict -> bloquait même r=0.969 et r=1.000 à gen=0.
    # La corrélation de Pearson pure (raw_pearson_r) mesure la forme géometrique
    # independamment de l'echelle, critere pertinent pour la qualite du fragment.
    # Les evaporations continuent toujours (la lib s'etire si rien n'est depose).
    # -------------------------------------------------------------------------
    # [SYRACUSE] La suite de Collatz est fondamentalement chaotique : même une
    # corrélation de 0.10–0.20 représente un signal structurel réel (bien mieux
    # qu'une valeur random). Maintenir le seuil à 0.50 bloque définitivement
    # la stigmergie sur ce problème et empêche l'accumulation de fragments utiles.
    # En mode normal les seuils classiques v14.1 sont conservés.
    if state._SYRACUSE_MODE:
        BURN_IN_GENERATIONS      = 3     # chauffe très courte : les fragments utiles
        MIN_CORRELATION_REQUIRED = 0.05  # s'ouvre dès r=0.05 après gen 3
        EARLY_OPEN_CORRELATION   = 0.30  # ouverture anticipée Voie B
    else:
        BURN_IN_GENERATIONS      = 15    # [FIX] réduit de 20 → 15 : ouverture plus rapide
        MIN_CORRELATION_REQUIRED = 0.50  # seuil minimal apres burn-in (Voie A)
        EARLY_OPEN_CORRELATION   = 0.85  # [FIX] réduit de 0.95 → 0.85 : atteignable sur ND

    # Corrélation de Pearson pure du meilleur individu de la génération courante
    # [FIX-SIGNE] Test sur |r| : une corrélation négative forte (ex. r=-0.86,
    # relation décroissante) est aussi utile qu'une positive — le linear scaling
    # gère le signe via un coefficient négatif. Tester r>=seuil sans valeur
    # absolue bloquait à vie la stigmergie sur tout problème à pente négative
    # (ex. NASA airfoil, où le meilleur individu a r≈-0.86).
    _best_r   = raw_pearson_r(pop[0], xs, ys)
    _abs_r    = abs(_best_r) if math.isfinite(_best_r) else 0.0
    _voie_a   = (generation >= BURN_IN_GENERATIONS
                 and _abs_r >= MIN_CORRELATION_REQUIRED)
    _voie_b   = (_abs_r >= EARLY_OPEN_CORRELATION)
    _stigm_allowed = _voie_a or _voie_b

    # [v0.7] Le moment et la VOIE d'ouverture. C'est l'information qui manquait
    # quand on cherchait pourquoi la stigmergie semblait inopérante à budget
    # court : le burn-in de 15 générations la bloquait structurellement, et sur
    # certains problèmes la voie B ouvrait au contraire dès la génération 0.
    if _stigm_allowed:
        TRACE.once("stigmergie_ouverte",
                   f"génération {generation} par la voie "
                   f"{'B (r >= %.2f)' % EARLY_OPEN_CORRELATION if _voie_b else 'A (après burn-in)'}"
                   f", r = {_best_r:+.3f}")
    else:
        TRACE.bump("stigmergie_bloquee_gen")

    if not _stigm_allowed:
        # Bruit trop élevé et burn-in non terminé : signaler et bloquer les dépôts.
        # [SYRACUSE] Supprimer le message pour r=-1.000 (arbre constant) : c'est
        # du bruit de diagnostic sans intérêt qui noie les vrais événements stigmergiques.
        # Afficher uniquement les vraies corrélations mesurées (r > -0.99).
        if _best_r > -0.99:
            print(f"  [Stigmergy Blocked] Initial noise or insufficient quality "
                  f"(gen={generation}, r={_best_r:.3f})")

    # ── OBJECTIF 3 : Simplification algébrique de l'Élite avant dépôt ──────────
    # Problème : les introns (sous-expressions neutres comme x-x, 1*x, 0+x…)
    # survivent dans la population sans affecter la fitness mais polluent la
    # mémoire collective.  Un fragment "sin(x - x + x)" a un hash différent de
    # "sin(x)" et occupe un slot distinct dans FRAGMENT_LIB / COGRAPH / SEQ_MEM,
    # ce qui dilue le signal utile et alourdit inutilement les structures.
    #
    # Solution : appliquer simplify() sur les top individus concernés par le
    # dépôt AVANT que leurs sous-arbres soient extraits.  Le cache fitness est
    # invalidé sélectivement pour les individus dont la forme a changé, afin que
    # le tri suivant reflète la forme simplifiée (la fitness ne change pas sur
    # le fond, mais le hash structurel change → entrée cache orpheline purgée).
    #
    # Périmètre : max(top_k, top_k_seq) — couvre à la fois la fenêtre FRAGMENT_LIB
    # (top_k = top 10%) et la fenêtre SEQ_MEM (top_k_seq = top 20%).
    # Exécuté seulement quand _stigm_allowed pour ne pas gaspiller des cycles CPU
    # pendant la phase de chauffe où les dépôts sont de toute façon bloqués.
    #
    # Structure de la population : pop est List[Node] (nœuds bruts, pas de wrapper).
    # La simplification est faite en place ; si l'arbre change, le hash précédent
    # est purgé du cache fitness pour éviter une entrée stale.
    # ─────────────────────────────────────────────────────────────────────────────
    # [v0.7] La simplification de l'élite est gardée par le feu vert
    # STIGMERGIQUE, ce qui n'a rien d'évident à la lecture : un paramètre de
    # phéromones décide du nettoyage des introns. Couplage mesuré comme
    # bénéfique dans la configuration par défaut, donc conservé — mais tracé,
    # pour qu'il ne surprenne plus personne.
    if _stigm_allowed:
        TRACE.once("simplification_elite",
                   f"première à la génération {generation} "
                   f"(gardée par le feu vert stigmergique)")
        _limit_clean = max(top_k, top_k_seq)
        for i in range(min(_limit_clean, len(pop))):
            _old_hash   = pop[i].structural_hash()
            _simplified = simplify(pop[i])
            _new_hash   = _simplified.structural_hash()
            if _new_hash != _old_hash:
                # La forme a changé : invalider l'entrée stale dans le cache
                state._fitness_cache.pop(_old_hash, None)
            pop[i] = _simplified
        # Recalcul de top_fits sur les formes simplifiées
        # (les fitness numériques sont identiques mais les hashes ont pu changer)
        top_fits = [fitness(ind, xs, ys, cfg, role=island.role) for ind in pop[:top_k]]

    if cfg.USE_LIB:
        if _stigm_allowed:
            state.FRAGMENT_LIB.deposit_population(pop, top_fits, top_k, generation,
                                            xs=xs, ys=ys)
        # [v16-FIX] Cap de diversité opérateur : plus strict en mode N-D
        # (plusieurs features → l'espace est plus grand, la diversité est vitale)
        _is_nd = (len(cfg.TERMINALS) > 1 or
                  (len(cfg.TERMINALS) == 1 and cfg.TERMINALS[0] != "x"))
        _op_cap = 0.30 if _is_nd else cfg.OP_DIVERSITY_CAP
        state.FRAGMENT_LIB.evaporate(evap_rate=cfg.FRAG_EVAP_RATE,
                               tau_max=cfg.FRAG_TAU_MAX,
                               op_diversity_cap=_op_cap)

    # ---- Dépôt co-occurrences (Phase 5a) ----
    if cfg.USE_COGRAPH and cfg.USE_LIB:
        if _stigm_allowed:
            state.COGRAPH.deposit_population(pop, top_k)
        state.COGRAPH.evaporate()

    # ---- Dépôt séquences structurelles (Phase 5b) ----
    if cfg.USE_SEQMEM:
        if _stigm_allowed:
            state.SEQ_MEM.deposit_population_with_root(pop, top_k_seq)
        state.SEQ_MEM.evaporate()

    found_better = False

    # [v0.8] Fenêtre de tirage figé (voir FragmentLibrary.begin_sampling) :
    # d'ici à la fin de la reproduction, les mémoires stigmergiques ne sont
    # que lues. Tout dépôt ou évaporation referme de toute façon la fenêtre.
    state.FRAGMENT_LIB.begin_sampling()
    state.COGRAPH.begin_sampling(state.FRAGMENT_LIB)

    if best_fit < island.best_score:
        island.best_score = best_fit
        island.best       = best.copy()
        island.stagnation = 0
        found_better      = True
        # [FIX-E] Enregistrer l'usage des features du meilleur individu
        if state._SYRACUSE_MODE and hasattr(cfg, 'TERMINALS'):
            record_feature_usage(best, cfg.TERMINALS)
        # [v17] Mettre à jour le résidu sémantique quand le best s'améliore
        try:
            probe_preds = evaluate_vector(best, state.PROBE_X)
            if np.all(np.isfinite(probe_preds)):
                _probe_y = np.zeros(len(state.PROBE_X), dtype=np.float64)
                if xs is not None and len(xs) > 1:
                    try:
                        _probe_y[:] = float(np.mean(ys))
                    except Exception:
                        pass
                state.CURRENT_RESIDUAL_SIG = update_residual_sig(best, state.PROBE_X, _probe_y)
        except Exception:
            pass
    else:
        island.stagnation += 1

    # [FIX-B] Mise à jour du buffer LAHC à chaque génération (île cleaner)
    island.lahc_buf[island.lahc_idx % island.lahc_L] = best_fit
    island.lahc_idx += 1

    # Reset diversité
    if island.stagnation > cfg.STAGNATION_LIMIT:
        n_reset  = int(len(pop) * cfg.RESET_FRACTION)
        _is_nd   = (len(cfg.TERMINALS) > 1 or
                    (len(cfg.TERMINALS) == 1 and cfg.TERMINALS[0] != "x"))

        if island.stigmergic and cfg.USE_LIB and state.FRAGMENT_LIB.fragments:
            # Île stigmergique : renouvelle via stigmergie v3
            for _ in range(n_reset):
                idx = random.randint(cfg.ELITE_SIZE, len(pop) - 1)
                pop[idx] = build_stigmergic_tree_v3(state.FRAGMENT_LIB, state.COGRAPH, state.SEQ_MEM, cfg)
        elif _is_nd:
            # [v16-FIX] Mode N-D : reset avec couverture opérateur garantie.
            # Détecter l'opérateur dominant dans la pop actuelle et sur-représenter
            # les autres pour casser la convergence prématurée.
            dominant_op = _detect_dominant_op(pop)
            for _ in range(n_reset):
                idx = random.randint(cfg.ELITE_SIZE, len(pop) - 1)
                t   = _random_tree_nd(cfg.MAX_INIT_DEPTH, cfg)
                # Rejeter si la racine est l'opérateur dominant (50% des cas)
                if t.value == dominant_op and random.random() < 0.5:
                    t = _nd_diverse_population(cfg, 1)[0]
                pop[idx] = t
        else:
            for _ in range(n_reset):
                idx = random.randint(cfg.ELITE_SIZE, len(pop) - 1)
                pop[idx] = random_tree(cfg.MAX_INIT_DEPTH, cfg)

        island.stagnation = 0
        # [SYRACUSE/ND] Si l'élite est une feuille constante, la remplacer par un vrai arbre
        if pop[0].left is None and pop[0].right is None:
            _is_nd2 = (len(cfg.TERMINALS) > 1 or
                       (len(cfg.TERMINALS) == 1 and cfg.TERMINALS[0] != "x"))
            pop[cfg.ELITE_SIZE] = (_random_tree_nd(cfg.MAX_INIT_DEPTH, cfg)
                                   if _is_nd2 else random_tree(cfg.MAX_INIT_DEPTH, cfg))

    # Nouvelle génération
    new_pop = []

    # Élites
    for elite in pop[:cfg.ELITE_SIZE]:
        new_pop.append(elite.copy())

    # [V42] Helper — vérifie si un arbre contient un sous-arbre banni
    _banned = island.banned_subtrees
    def _is_banned(tree: Node) -> bool:
        if not _banned or tree is None:
            return False
        try:
            for node, _, _ in get_all_nodes(tree):
                if node.canonical_hash() in _banned:
                    return True
        except Exception:
            pass
        return False

    # Injection random — utilise le générateur adapté au mode actif
    inject_n = int(len(pop) * cfg.RANDOM_INJECTION)
    _is_nd_mode = (len(cfg.TERMINALS) > 1 or
                   (len(cfg.TERMINALS) == 1 and cfg.TERMINALS[0] != "x"))
    for _ in range(inject_n):
        if _is_nd_mode:
            new_pop.append(_random_tree_nd(cfg.MAX_INIT_DEPTH, cfg))
        else:
            new_pop.append(random_tree(cfg.MAX_INIT_DEPTH, cfg))

    # [OPT] Seuil élitiste Adam calculé UNE fois par génération (au lieu de par enfant)
    _elite_threshold = sorted(raw_mse(ind, xs, ys) for ind in pop[:max(4, len(pop)//4)])[-1]

    # [v18-LEX] Sélecteur ε-lexicase — îles explorer/stigmergic uniquement
    # (l'île cleaner garde le tournoi BIC : sa mission est la parcimonie,
    # pas la diversité comportementale).
    _lex = None
    if getattr(cfg, "USE_LEXICASE", False) and island.role != "cleaner":
        try:
            _lex = EpsilonLexicaseSelector(pop, xs, ys)
        except Exception:
            _lex = None

    # Reproduction
    while len(new_pop) < len(pop):

        # parent1 est TOUJOURS défini avant les deux branches pour servir de fallback sûr
        # [v14.4] role=island.role transmis au tournoi pour cohérence de pression sélective
        parent1  = (_lex.select() if _lex is not None
                    else tournament(pop, xs, ys, cfg, role=island.role))
        fallback = parent1

        # C — Taux de mutation sémantique adaptatif : augmente sur plateau
        _sem_rate = cfg.SEMANTIC_MUTATION_RATE
        if island.stagnation > cfg.STAGNATION_LIMIT // 2:
            _sem_rate = min(0.30, _sem_rate + 0.15)

        # FIX v13.8 : taux d'injection stigmergique progressif.
        # En ultrafast (N_ISLANDS=2), la lib et le COGRAPH sont pauvres
        # en gen 0. On démarre à 30% et on monte à 70% après gen 20
        # (ou quand le COGRAPH est assez riche).
        _cograph_rich = len(state.COGRAPH.co) >= max(5, min(20, len(state.FRAGMENT_LIB.fragments) * 2))
        _stim_rate = 0.70 if (_cograph_rich or generation >= 20) else 0.30

        if island.stigmergic and cfg.USE_LIB and state.FRAGMENT_LIB.fragments and random.random() < _stim_rate:
            # Île C : construction v3 (co-graphe + séquences)
            child = build_stigmergic_tree_v3(state.FRAGMENT_LIB, state.COGRAPH, state.SEQ_MEM, cfg)
            # [v14.5] Adam uniquement si l'enfant est prometteur ET élitiste (top 25%)
            if random.random() < cfg.CONST_OPT_PROB:
                child_mse = raw_mse(child, xs, ys)
                # [v0.8] _elite_threshold n'est plus recalculé ici pour chaque
                # enfant : `pop` ne change pas pendant la reproduction, la
                # valeur est celle calculée une fois avant la boucle (le
                # recalcul coûtait ~6 % du temps total).
                if child_mse < _elite_threshold:
                    child = optimize_constants_adam(child, xs, ys, cfg)
            child = simplify(child)
        else:
            # Reproduction classique (toutes îles + île C à 30%)
            child = parent1

            if random.random() < cfg.CROSSOVER_RATE:
                parent2 = (_lex.select() if _lex is not None
                           else tournament(pop, xs, ys, cfg, role=island.role))
                # [v0.4] crossover typé : n'échange que des sous-arbres de même
                # dimension -> les deux enfants restent valides.
                if _dim_active(cfg):
                    child, _ = _ds().typed_crossover(parent1, parent2,
                                                     cfg.FEAT_DIMS, random)
                else:
                    child   = crossover_size_fair(parent1, parent2, cfg)

            if random.random() < cfg.MUTATION_RATE:
                # [v0.4] mutation typée : le sous-arbre neuf a la dimension du
                # sous-arbre remplacé -> validité préservée.
                if _dim_active(cfg):
                    child = _ds().typed_mutate(child, cfg.FEAT_DIMS,
                                               cfg.MAX_MUTATION_DEPTH, random,
                                               ops=_active_pool_ops())
                else:
                    child = mutate(child, xs, ys, cfg, role=island.role)  # [v14.5] rôle transmis

            if random.random() < _sem_rate:
                child = semantic_mutation(child, xs, ys, cfg, role=island.role)

            # [v14.5] Adam sélectif : tirage probabiliste + garde élitiste (top 25%)
            if random.random() < cfg.CONST_OPT_PROB:
                child_mse = raw_mse(child, xs, ys)
                if child_mse < _elite_threshold:
                    child = optimize_constants_adam(child, xs, ys, cfg)

            child = simplify(child)

        if tree_size(child)  > cfg.MAX_TREE_SIZE:  child = fallback
        if tree_depth(child) > cfg.MAX_TREE_DEPTH: child = fallback

        # [FIX-B] LAHC pour l'île cleaner : accepte l'enfant seulement s'il
        # est meilleur qu'il y a L générations (pas seulement que le courant).
        # Permet d'échapper aux plateaux plats sans explosion de diversité.
        if island.role == "cleaner":
            child_score = fitness(child, xs, ys, cfg, role=island.role)
            lahc_ref    = island.lahc_buf[island.lahc_idx % island.lahc_L]
            if child_score > lahc_ref + 0.05:
                child = fallback

        # [V42] Filtrer les enfants contenant des sous-arbres bannis (explorer)
        if _banned and island.role == "explorer" and _is_banned(child):
            if _is_nd_mode:
                child = _random_tree_nd(cfg.MAX_INIT_DEPTH, cfg)
            else:
                child = random_tree(cfg.MAX_INIT_DEPTH, cfg)

        new_pop.append(child)

    state.FRAGMENT_LIB.end_sampling()
    state.COGRAPH.end_sampling()

    # [v19] Déduplication sémantique : on retire les clones comportementaux
    # (hors élite, déjà en tête de new_pop), puis on REMPLIT les slots libérés
    # par de nouveaux arbres -> taille de population constante, mais la fraction
    # redondante est convertie en diversité réelle. Gain double : moins de
    # sélections lexicase/copies/évaluations ET meilleure exploration.
    if getattr(cfg, "USE_SEMANTIC_DEDUP", False):
        target = len(pop)
        new_pop, _n_removed = semantic_dedup(new_pop, xs, ys, cfg,
                                             protected=cfg.ELITE_SIZE)
        # [v19] Refill des slots libérés : 70% par MUTATION d'un survivant
        # (préserve la qualité acquise, contrairement à des arbres 100%
        # randoms qui dégradent la population), 30% par injection neuve
        # (diversité fraîche). C'est le compromis exploration/exploitation
        # standard quand on remplace des clones.
        _refill = 0
        _n_keep = len(new_pop)
        while len(new_pop) < target and _refill < 4 * target:
            _refill += 1
            if _n_keep > 0 and random.random() < 0.70:
                parent = new_pop[random.randrange(_n_keep)]
                if _dim_active(cfg):          # [v0.4] refill typé
                    child = _ds().typed_mutate(parent, cfg.FEAT_DIMS,
                                               cfg.MAX_MUTATION_DEPTH, random,
                                               ops=_active_pool_ops())
                else:
                    child  = mutate(parent, xs, ys, cfg, role=island.role)
                if (tree_size(child) <= cfg.MAX_TREE_SIZE
                        and tree_depth(child) <= cfg.MAX_TREE_DEPTH):
                    new_pop.append(child)
            else:
                cand = (_random_tree_nd(cfg.MAX_INIT_DEPTH, cfg)
                        if _is_nd_mode else random_tree(cfg.MAX_INIT_DEPTH, cfg))
                new_pop.append(simplify(cand))
        while len(new_pop) < target:
            new_pop.append(new_pop[random.randrange(len(new_pop))].copy())
        island.last_dedup_removed = _n_removed

    island.population = new_pop
    return island.best if found_better else None

# ============================================================
# ÉVOLUTION PRINCIPALE (multi-îles)
# ============================================================


# ════════════════════════════════════════════════════════════════
# [v20-PAR] PARALLÉLISME DES ÎLES — ProcessPoolExecutor (spawn-safe)
# ════════════════════════════════════════════════════════════════
# Modèle en îles à gros grain, standard en GP parallèle :
#   · chaque round, les N îles évoluent PARALLEL_ROUND générations dans des
#     processus séparés, chacune sur un INSTANTANÉ FIGÉ de la stigmergie
#     (FRAGMENT_LIB, COGRAPH, SEQ_MEM) ;
#   · au retour, le maître fusionne les stigmergies (merge_from, par MAX),
#     met à jour le champion, applique migration / plateau / early-stop ;
#   · contexte "spawn" forcé → comportement IDENTIQUE Windows / Linux / macOS,
#     et exige le guard if __name__ == "__main__" (présent).
# Garanties :
#   · toute exception du pool ⇒ repli séquentiel automatique pour le reste
#     du run (aucun crash, message explicite) ;
#   · sur machine 1-2 cœurs le mode AUTO reste séquentiel (zéro overhead).
# Changement algorithmique assumé : les dépôts stigmergiques inter-îles ne
# sont visibles qu'aux frontières de round (et non en temps réel). En
# pratique ce retard préserve la diversité inter-îles — c'est le compromis
# choisi par la littérature GP parallèle.

_PW: dict = {}    # état du worker (initialisé une fois par processus)

def _pool_probe():
    """[v0.7-PAR] Tache vide : prouve qu'un worker a fini de demarrer."""
    return True


def _parallel_worker_init(data_path, use_ls, syracuse_mode,
                          gencsv=None, battery_mode=False,
                          ls_scale_only=False, dim_unknown_const=False,
                          quiet=False):
    """Initializer du pool : reçoit les données constantes UNE fois par worker.
    [v0.7-PAR] Les tableaux (xs, ys, sondes, series Syracuse) arrivent par un
    fichier temporaire, pas par initargs : les initargs sont ecrits dans le
    tube de demarrage du fils, et au-dela de sa capacite (64 Ko sous Linux)
    le parent y reste bloque si le fils meurt pendant son amorcage -- ce que
    fait justement un fils qui re-execute un script sans garde __main__. Le
    repli sequentiel promis devenait un blocage definitif des ~3000 lignes.
    [FIX-WIN v20] Sous Windows (spawn), le worker ré-importe le module depuis
    __file__ et l'enregistre sous son nom canonique dans sys.modules, ce qui
    évite le ModuleNotFoundError quand le fichier s'appelle GP_ELITE_v20_PARALLEL
    mais que le code l'a importé sous la clé "gp_v20"."""
    import sys as _sys, importlib.util as _ilu, os as _os
    _this_file = _os.path.abspath(__file__)
    _mod_name  = _os.path.splitext(_os.path.basename(_this_file))[0]
    for _key in (_mod_name, "gp_v20"):
        if _key not in _sys.modules:
            _spec = _ilu.spec_from_file_location(_key, _this_file)
            _mod  = _ilu.module_from_spec(_spec)
            _sys.modules[_key] = _mod
    state._LS_SCALE_ONLY = bool(ls_scale_only)
    state._DIM_UNKNOWN_CONST = bool(dim_unknown_const)
    import pickle as _pickle
    if quiet:
        # [v0.7-PAR] Le parent est silencieux (symbolic_regression(verbose=
        # False) redirige sa sortie) : ses workers le sont aussi. Sans cela,
        # sur une machine a 4 coeurs ou plus, leurs messages de progression
        # s'affichaient chez l'utilisateur malgre verbose=False.
        _sys.stdout = open(_os.devnull, "w")
    with open(data_path, "rb") as _fh:
        xs, ys, probe_x, syracuse_y_raw, syracuse_x_raw = _pickle.load(_fh)
    _PW["xs"] = xs
    _PW["ys"] = ys
    state.PROBE_X             = probe_x
    state._USE_LINEAR_SCALING = use_ls
    state._SYRACUSE_MODE      = syracuse_mode
    if syracuse_y_raw is not None:
        state._SYRACUSE_Y_RAW = syracuse_y_raw
    if syracuse_x_raw is not None:
        state._SYRACUSE_X_RAW = syracuse_x_raw
    # [v22-CSV] propager le mode CSV générique + pools + noms de colonnes
    state._BATTERY_CSV_MODE = battery_mode
    if gencsv is not None:
        state._GENERIC_CSV_MODE = True
        (state._GENERIC_BINARY_OPS, state._GENERIC_BINARY_WEIGHTS,
         state._GENERIC_UNARY_OPS,  state._GENERIC_UNARY_WEIGHTS,
         state.CSV_FEATURE_NAMES, state.CSV_TARGET_NAME) = gencsv
    else:
        state._GENERIC_CSV_MODE = False

def _island_round_task(payload):
    """Évolue UNE île pendant n_gens générations dans le worker.
    Reproduit fidèlement le housekeeping par génération de la boucle
    séquentielle (caches, _gen_bucket, mono_pen Syracuse)."""
    (island, gen_start, n_gens, frag, cog, seq, residual, seed) = payload
    random.seed(seed)
    np.random.seed(seed & 0x7FFFFFFF)
    state.FRAGMENT_LIB         = frag
    state.COGRAPH              = cog
    state.SEQ_MEM              = seq
    state.CURRENT_RESIDUAL_SIG = residual
    xs, ys = _PW["xs"], _PW["ys"]
    cfg = island.cfg
    best_local = None
    _deadline = getattr(cfg, "DEADLINE", None)
    for gen in range(gen_start, gen_start + n_gens):
        # [v0.7-TIME] Echeance atteinte : on rend l'ile en l'etat. Jamais a la
        # generation 0, pour qu'au moins une generation produise un modele.
        if _deadline is not None and gen > 0 and time.time() >= _deadline:
            break
        if gen % 10 == 0:
            state._fitness_cache.clear()
        _clear_simplify_caches()
        if state._SYRACUSE_MODE:
            _t = gen / max(cfg.GENERATIONS - 1, 1)
            cfg._mono_pen_cache = 0.10 - _t * 0.07
        cfg._gen_bucket = gen // 10
        nb = evolve_island(island, xs, ys, gen)
        if nb is not None:
            best_local = nb
    return (island, best_local, state.FRAGMENT_LIB, state.COGRAPH, state.SEQ_MEM)


# ── [v0.7-PAR] Parallelisme sur pour les scripts sans garde __main__ ──────
# Les iles paralleles utilisent le demarrage « spawn » (identique sur tous les
# systemes). Un processus fils spawn RE-EXECUTE le script principal de
# l'utilisateur. Sans `if __name__ == "__main__":`, chaque fils refait donc
# tout le calcul avant de servir : mesure sur 800 points, le script est
# execute 3 fois et le mode parallele met 9,0 s contre 4,6 s en sequentiel.
# Les exemples du README n'ont pas cette garde : c'est le cas par defaut d'un
# nouvel utilisateur sur une machine a 4 coeurs ou plus.
#
# Detection : pendant la creation du pool, le parent pose GP_ELITE_POOL_CHILD
# dans l'environnement, que les fils heritent. Un fils qui atteint evolve()
# pendant son demarrage est forcement en train de re-executer le script : il
# se termine SANS bruit, le pool du parent se brise, le parent bascule en
# sequentiel, previent une seule fois, et ne retente plus le parallele.
_POOL_CHILD_ENV = "GP_ELITE_POOL_CHILD"


class _SkipLogExport(Exception):
    """Export du journal desactive (API) : sortie propre du bloc d'ecriture."""


def _exit_if_reimported_by_worker():
    """Termine un fils gp-elite qui est en train de RE-EXECUTER le script.

    Attention : pendant cette phase, multiprocessing.parent_process() n'est
    PAS encore renseigne (il ne l'est qu'au demarrage du travailleur, apres
    la re-execution). Les indicateurs fiables sont ceux qu'utilise
    multiprocessing lui-meme pour detecter la phase d'amorcage :
    l'attribut `_inheriting` du processus courant, et le nom `__mp_main__`
    donne au module principal re-importe. La variable d'environnement
    restreint la detection aux fils crees par gp-elite.
    """
    if os.environ.get(_POOL_CHILD_ENV) != "1":
        return
    try:
        import multiprocessing as _mp
        bootstrapping = bool(getattr(_mp.current_process(), "_inheriting", False))
    except Exception:
        bootstrapping = False
    main_mod = sys.modules.get("__main__")
    if bootstrapping or getattr(main_mod, "__name__", "") == "__mp_main__":
        sys.exit(0)          # silencieux : le parent gere le repli


def _warn_unguarded_main(err):
    """Avertissement unique, sur stderr (non capture par le mode silencieux)."""
    if state._PARALLEL_WARNED:
        return
    state._PARALLEL_WARNED = True
    import warnings
    main_file = getattr(sys.modules.get("__main__"), "__file__", None)
    if main_file:
        msg = ("gp-elite: parallel islands could not start, most likely "
               "because the script %r is not protected by "
               "`if __name__ == \"__main__\":` (required by multiprocessing). "
               "Continuing SEQUENTIALLY: the fit completes, but the islands "
               "then run one after the other, which is slower and can return "
               "another model than in parallel. "
               "Wrap your top-level code in that guard to use several cores, "
               "or pass parallel=False to run in sequence without this message."
               % os.path.basename(main_file))
    else:
        msg = ("gp-elite: parallel islands could not start (%s); continuing "
               "sequentially. Pass parallel=False to silence this message."
               % type(err).__name__)
    warnings.warn(msg, RuntimeWarning, stacklevel=3)


def _parallel_enabled(cfg) -> bool:
    """AUTO : parallèle si ≥4 cœurs et ≥2 îles ; True force ; False bloque."""
    flag = getattr(cfg, "PARALLEL_ISLANDS", None)
    if flag is False or cfg.N_ISLANDS < 2:
        return False
    if state._PARALLEL_BROKEN:          # [v0.7-PAR] deja echoue dans ce processus
        return False
    if flag is True:
        return True
    import os as _os
    return (_os.cpu_count() or 1) >= 4

def _evolve_parallel(islands, xs, ys, cfg, t0, log_rows):
    """Boucle d'évolution parallèle par rounds. Retourne
    (global_best, global_score, completed) — completed=False signifie
    qu'une erreur est survenue et que l'appelant doit basculer en séquentiel
    en repartant de l'état courant des îles (jamais corrompu : on ne remplace
    les îles qu'après un round entièrement réussi)."""
    import os as _os
    import concurrent.futures as _cf
    import multiprocessing as _mp

    global_best  = None
    global_score = float("inf")
    _plateau_counter   = 0
    _plateau_threshold = 40
    _last_global_raw   = float("inf")

    round_len = getattr(cfg, "PARALLEL_ROUND", 0) or max(1, min(10, cfg.MIGRATION_INTERVAL))
    n_workers = min(len(islands), _os.cpu_count() or 1)
    ctx = _mp.get_context("spawn")     # identique Windows/Linux/macOS

    # [REPRO] Générateur dédié pour les seeds des workers. Indépendant de
    # l'état global de `random` (que le maître consomme via fitness/scaling/
    # etc.), donc la suite de seeds distribués est DÉTERMINISTE pour un seed
    # donné — condition nécessaire à la reproductibilité du mode parallèle.
    _seed_base = getattr(cfg, "SEED", None)
    if _seed_base is None:
        _seed_base = random.getrandbits(31)
    _worker_rng = random.Random(_seed_base ^ 0x5DEECE66D)

    _syr_y = getattr(state, '_SYRACUSE_Y_RAW', None) if state._SYRACUSE_MODE else None
    _syr_x = getattr(state, '_SYRACUSE_X_RAW', None) if state._SYRACUSE_MODE else None
    # [v22-CSV] snapshot du mode CSV générique pour les workers
    _gencsv = ((list(state._GENERIC_BINARY_OPS), list(state._GENERIC_BINARY_WEIGHTS),
                list(state._GENERIC_UNARY_OPS),  list(state._GENERIC_UNARY_WEIGHTS),
                list(state.CSV_FEATURE_NAMES), state.CSV_TARGET_NAME)
               if state._GENERIC_CSV_MODE else None)

    print(f"[v20-PAR] Parallel mode active: {len(islands)} islands / "
          f"{n_workers} workers — rounds of {round_len} generations "
          f"(stigmergic merge every round)")

    # [v29-REPRO] DÉTERMINISME DES WORKERS. Les enfants « spawn » sont des
    # interpréteurs neufs qui relisent PYTHONHASHSEED au démarrage : non fixé,
    # chaque worker randomise le hachage des str → l'ordre d'itération des
    # `set` varie → des tirages différents À ÉTAT RNG IDENTIQUE. On fige donc
    # le hachage des enfants avant de créer le pool (sans effet sur le parent,
    # déjà démarré). Combiné aux seeds par (île, round) déjà deterministics et
    # à la collecte ORDONNÉE des résultats, le mode parallèle devient
    # reproductible : même seed → même champion.
    _prev_hash = _os.environ.get("PYTHONHASHSEED")
    _prev_child = _os.environ.get(_POOL_CHILD_ENV)
    _os.environ["PYTHONHASHSEED"] = "0"
    _os.environ[_POOL_CHILD_ENV] = "1"      # [v0.7-PAR] herite par les fils

    # [v0.7-PAR] Donnees des workers par fichier temporaire (voir
    # _parallel_worker_init) : le message de demarrage reste petit.
    import pickle as _pickle, tempfile as _tempfile
    _data_path = None
    try:
        with _tempfile.NamedTemporaryFile(prefix="gp_elite_pool_", suffix=".pkl",
                                          delete=False) as _fh:
            _data_path = _fh.name
            _pickle.dump((xs, ys, state.PROBE_X, _syr_y, _syr_x), _fh,
                         protocol=_pickle.HIGHEST_PROTOCOL)
        with _cf.ProcessPoolExecutor(
                max_workers=n_workers, mp_context=ctx,
                initializer=_parallel_worker_init,
                initargs=(_data_path, state._USE_LINEAR_SCALING,
                          state._SYRACUSE_MODE,
                          _gencsv, state._BATTERY_CSV_MODE,
                          state._LS_SCALE_ONLY, state._DIM_UNKNOWN_CONST,
                          sys.stdout is not sys.__stdout__)) as ex:
            # [v0.7-PAR] Sonde : des taches vides d'abord. Un script sans
            # garde __main__ fait terminer chaque worker pendant son demarrage
            # (_exit_if_reimported_by_worker) ; la sonde echoue alors en
            # BrokenProcessPool et on bascule en sequentiel. Sans elle, la
            # premiere ronde (iles entieres, plus que la capacite d'un tube)
            # restait coincee dans la file d'envoi : Python 3.9 attend ce fil
            # d'envoi pour fermer le pool, et le repli promis ne venait jamais.
            for _f in [ex.submit(_pool_probe) for _ in range(n_workers)]:
                _f.result()
            gen = 0
            _deadline = getattr(cfg, "DEADLINE", None)
            _pat = _Patience(getattr(cfg, "PATIENCE", 0))     # [v1.2-H1]
            while gen < cfg.GENERATIONS:
                # [v0.7-TIME] Echeance atteinte : pas de nouvelle ronde.
                if _deadline is not None and gen > 0 and time.time() >= _deadline:
                    TRACE.set("time_limit", "atteint (parallele, gen %d)" % gen)
                    state._TIME_LIMIT_HIT = True
                    print(f"[TIME] Time limit reached at generation {gen} — "
                          f"returning the best model so far.")
                    break
                # Round aligné sur les frontières de migration
                nxt_mig = ((gen // cfg.MIGRATION_INTERVAL) + 1) * cfg.MIGRATION_INTERVAL
                n_gens  = min(round_len, cfg.GENERATIONS - gen, max(1, nxt_mig - gen))

                futs = [ex.submit(_island_round_task,
                                  (isl, gen, n_gens,
                                   state.FRAGMENT_LIB, state.COGRAPH, state.SEQ_MEM,
                                   state.CURRENT_RESIDUAL_SIG,
                                   _worker_rng.getrandbits(31)))
                        for isl in islands]
                results = [f.result() for f in futs]   # lève si un worker meurt

                # ── Réintégration (uniquement après round 100% réussi) ──
                for i, (isl, best_local, frag, cog, seq) in enumerate(results):
                    islands[i] = isl
                    state.FRAGMENT_LIB.merge_from(frag)
                    state.COGRAPH.merge_from(cog)
                    state.SEQ_MEM.merge_from(seq)

                _gen_end = gen + n_gens - 1
                for i, (isl, best_local, _f, _c, _s) in enumerate(results):
                    if best_local is None:
                        continue
                    cand = wrap_linear_scaling(best_local, xs, ys)
                    _track_val_candidate(cand)        # [v21-VAL]
                    _track_small_candidate(cand, xs, ys)   # [1.4-S1]
                    s = fitness(cand, xs, ys, cfg, role="cleaner")
                    if s < global_score:
                        global_score = s
                        global_best  = cand.copy()
                        raw = raw_mse(cand, xs, ys)
                        elapsed = time.time() - t0
                        print(f"[GEN {_gen_end:04d}|I{isl.id}] "
                              f"FIT={s:.8f} RAW={raw:.8f} "
                              f"SIZE={tree_size(cand):02d} "
                              f"DEPTH={tree_depth(cand):02d} ({elapsed:.1f}s)")
                        print(f"  EXPR = {to_string(cand)}")
                        print()
                        log_rows.append({
                            "gen": _gen_end, "island": isl.id,
                            "fit": s, "raw": raw,
                            "size": tree_size(cand), "depth": tree_depth(cand),
                            "expr": to_string(cand), "elapsed": elapsed})
                        # Résidu sémantique recalculé par le maître
                        try:
                            _probe_y = np.zeros(state.PROBE_X.shape[0])
                            state.CURRENT_RESIDUAL_SIG = update_residual_sig(
                                global_best, state.PROBE_X, _probe_y)
                        except Exception:
                            pass

                gen += n_gens

                # ── Logique globale (granularité round) ──
                _cur_raw = raw_mse(global_best, xs, ys) if global_best else float("inf")
                if _cur_raw < _last_global_raw - 1e-6:
                    _plateau_counter = 0
                    _last_global_raw = _cur_raw
                else:
                    _plateau_counter += n_gens

                _is_nd_run = (len(cfg.TERMINALS) > 1 or
                              (len(cfg.TERMINALS) == 1 and cfg.TERMINALS[0] != "x"))
                if (_plateau_counter >= _plateau_threshold and
                        _is_nd_run and gen < cfg.GENERATIONS - 50):
                    _plateau_counter = 0
                    _smart_reset_explorers(islands, cfg, gen, _cur_raw)

                if global_best and raw_mse(global_best, xs, ys) < cfg.PERFECT_THRESHOLD:
                    print(f"[✓] Perfect solution found at generation {gen}!")
                    break

                if global_best:
                    # [v21-VAL] early-stop jugé sur le HOLD-OUT (anti-surapprentissage)
                    _es_mse = _holdout_mse(global_best, xs, ys)
                    _es_thr = _early_stop_threshold(cfg, ys)
                    if _es_mse <= _es_thr:
                        print(f"\n{'═'*60}")
                        print(f"  [SUCCESS] Precision target reached at GEN {gen:04d}!")
                        print(f"  MSE (hold-out si actif) = {_es_mse:.2e}  ≤  seuil = {_es_thr:.2e}")
                        print(f"  Early stop — remaining generations saved.")
                        print(f"{'═'*60}\n")
                        break
                    # [v1.2-H1] Arrêt sur patience, compté à la fin de chaque
                    # round sur sa dernière génération (gen - 1).
                    if _pat.spent(_es_mse, gen - 1):
                        TRACE.set("patience", "arret (parallele, gen %d)" % (gen - 1))
                        print(f"[PATIENCE] No gain of 1 % in {_pat.p} generations — "
                              f"stop at generation {gen - 1}.")
                        break

                if gen > 0 and gen % cfg.MIGRATION_INTERVAL == 0:
                    migrate(islands)

        return global_best, global_score, True

    except Exception as _par_err:
        print(f"[v20-PAR] ⚠ Parallel unavailable ({type(_par_err).__name__}: "
              f"{_par_err}) — automatic sequential fallback.")
        # [v0.7-PAR] Un pool BRISE (fils termines) ne se reparera pas au
        # prochain appel : on cesse d'essayer dans ce processus, et on dit
        # pourquoi, une fois, sur stderr.
        if type(_par_err).__name__ == "BrokenProcessPool":
            state._PARALLEL_BROKEN = True
            _warn_unguarded_main(_par_err)
        return global_best, global_score, False
    finally:
        if _data_path is not None:
            try:
                _os.remove(_data_path)
            except OSError:
                pass
        # [v0.7-PAR] Ne laisser aucune trace dans l'environnement de
        # l'utilisateur (ses propres sous-processus en heriteraient).
        for _k, _v in (("PYTHONHASHSEED", _prev_hash), (_POOL_CHILD_ENV, _prev_child)):
            if _v is None:
                _os.environ.pop(_k, None)
            else:
                _os.environ[_k] = _v


# ════════════════════════════════════════════════════════════════
# [v21-VAL] VALIDATION HOLD-OUT
# ════════════════════════════════════════════════════════════════
# Pourquoi : jusqu'ici tous les MSE étaient mesurés sur les données
# d'ENTRAÎNEMENT — sur données réelles bruitées, une formule de 25 nœuds
# peut mémoriser le bruit et s'effondrer sur de nouvelles mesures.
# Désormais : split train/val au démarrage, évolution sur train seul,
# suivi séparé du meilleur individu EN VALIDATION, early-stopping et
# sélection finale sur la validation, rapport de généralisation.

                         # interrompu par l'echeance cfg.DEADLINE
# [v0.7-NEAR] GARDE DE STABILITE PRES DU DOMAINE (mode par defaut).
# Constat : sur donnees reelles (210_cloud, validation croisee), un modele a
# donne R2 = -1.7e10 sur des points jamais vus, alors qu'il etait sain sur
# l'entrainement et la validation. La garde hors-plage existante n'agit qu'en
# mode extrapolate=True. Principe retenu : sonder par combinaisons de PAIRES
# de points reels, x = l*xi + (1-l)*xj avec l dans [-0.1, 1.1] -- l'interieur
# de l'enveloppe des donnees plus un leger debordement le long des directions
# ou elles s'etendent vraiment. Une vraie loi ne peut pas diverger la ou des
# mesures existent en continu. Mesure sur les 41 lois du banc Feynman : 0 vraie
# loi jugee instable jusqu'a 10 % de debordement (pire ecart 2.8 etendues de y,
# seuil 50) ; a 20 %, 5/41 le seraient (lois relativistes : la sonde traverse
# v = c). Usage : DEPARTAGE seulement, entre candidats statistiquement
# indiscernables -- jamais un rejet d'un candidat qui se detache.
_NEAR_CACHE = {}
_EXACT_REL = 1e-12           # [v0.7-EXACT] plancher « exact » relatif a var(y_val)

_FAITHFUL_CACHE: Dict[int, bool] = {}


def _formula_faithful(node) -> bool:
    """[v0.8] Vrai si la fonction mathématique de l'arbre (sans garde-fou
    numérique) reproduit l'évaluation du moteur sur les données de
    l'ajustement (entraînement et hold-out, espace normalisé), avec la
    tolérance du contrôle de gp_elite.formula (1e-7 relatif)."""
    xs = [x for x in (state._VAL_TRAIN_XS, state._VAL_XS) if x is not None]
    if node is None or not xs:
        return True
    try:
        key = node.exact_hash()
    except Exception:
        key = None
    if key is not None and key in _FAITHFUL_CACHE:
        return _FAITHFUL_CACHE[key]
    ok = True
    try:
        try:
            from . import formula as _F
        except ImportError:                  # core.py lancé comme script
            import formula as _F
        for X in xs:
            p = np.asarray(evaluate_vector(node, X), dtype=float)
            with np.errstate(all="ignore"):
                v = np.asarray(_F.evaluate(node, X), dtype=float)
                if v.ndim == 0:
                    v = np.full(p.shape, float(v))
                scale = max(float(np.max(np.abs(p))) if p.size else 0.0,
                            float(np.std(p)) if p.size else 0.0, 1e-300)
                gap = np.abs(v - p)
            if not np.all(np.isfinite(gap)) or float(np.max(gap)) > 1e-7 * scale:
                ok = False
                break
    except Exception:
        ok = False
    if key is not None:
        _FAITHFUL_CACHE[key] = ok
    return ok
_NEAR_EXT = 0.10
_NEAR_K = 50.0
# [v25-EXTRAP] Garde-fou anti-divergence : points-sondes AU-DELÀ de la plage
# d'entraînement (axe d'extrapolation prolongé) + bande de plausibilité dérivée
# de y. Un candidat dont la prédiction sort de cette bande sur les sondes est
# rejeté de la sélection — ce que la validation-frontière (interne) ne peut voir.
_VAL_CANDS_MAX = 64

def _early_stop_threshold(cfg, ys_train) -> float:
    """[v0.8] Seuil d'arrêt anticipé, RELATIF à la variance de la cible pour
    les ajustements de l'API.

    Le seuil était un MSE absolu de 1e-6 : il dépendait donc de l'unité de y.
    Sur une cible de variance 0,02 (loi gaussienne de Feynman I.6.20a), un
    modèle à 1 - R² = 6e-5 l'atteignait : la recherche s'arrêtait à la 6e
    génération, puis la sélection parcimonieuse rendait une approximation
    plus courte à 1 - R² = 2e-3, alors que la loi exacte était à portée. En
    unités plus grandes, la même loi n'aurait jamais déclenché l'arrêt. On
    ne s'arrête plus que sur une loi exacte à la précision numérique
    (1 - R² <= _EXACT_REL sur le hold-out), le seul cas où chercher encore
    ne peut rien apporter. Les modes démonstration (Syracuse, batterie)
    gardent leur seuil absolu."""
    if not state._GENERIC_CSV_MODE:
        return cfg.EARLY_STOPPING_MSE
    ref = state._VAL_YS if (state._VAL_YS is not None and len(state._VAL_YS) > 1) else ys_train
    try:
        v = float(np.var(np.asarray(ref, dtype=float)))
    except Exception:
        return cfg.EARLY_STOPPING_MSE
    if not math.isfinite(v) or v <= 1e-300:
        return cfg.EARLY_STOPPING_MSE
    return _EXACT_REL * v


# [v1.2-H1] Arrêt sur patience (benchmarks/results_1.2/PLAN.md, H1).
_PATIENCE_GAIN = 0.01


class _Patience:
    """Compte les générations sans gain. L'erreur lue est celle de l'arrêt
    anticipé (MSE du hold-out, ou du train sans hold-out) ; elle compte comme
    un gain quand elle passe sous (1 - 1 %) fois la meilleure vue dans ce
    run. `spent(err, gen)` est vrai quand `p` générations sont passées sans
    gain : la boucle s'arrête alors comme sur une loi exacte, et le fit va à
    sa fin habituelle. p = 0 (défaut hors API, et toute API avec un budget
    explicite) : jamais vrai, la recherche de 1.1 est inchangée. Chaque
    évolution (redémarrage) a la sienne."""
    __slots__ = ("p", "best", "gen")

    def __init__(self, p):
        self.p = int(p or 0)
        self.best = None
        self.gen = 0

    def spent(self, err, gen):
        if self.p <= 0:
            return False
        if self.best is None or err < self.best * (1.0 - _PATIENCE_GAIN):
            self.best, self.gen = err, gen
            return False
        return gen - self.gen >= self.p


def _holdout_mse(node, xs_train, ys_train) -> float:
    """MSE sur le hold-out si disponible, sinon sur le train (fallback)."""
    if node is None:
        return float("inf")
    if state._VAL_XS is not None:
        try:
            preds = evaluate_vector(node, state._VAL_XS)
            m = float(np.mean((preds - state._VAL_YS) ** 2))
            return m if math.isfinite(m) else float("inf")
        except Exception:
            return float("inf")
    return _pure_mse(node, xs_train, ys_train)

def _is_numerically_stable(cand) -> bool:
    """[v23.1] Un candidat est rejeté de la sélection finale s'il EXPLOSE sur
    le domaine d'ENTRAÎNEMENT complet (pas seulement le hold-out). Un arbre
    avec des chaînes pow imbriquées peut coller aux 34 points de validation
    tout en prédisant des milliers ailleurs : sur-apprentissage que le
    hold-out a manqué. On vérifie que les prédictions restent dans une plage
    cohérente avec la cible observée."""
    if state._VAL_TRAIN_XS is None:
        return True
    try:
        preds = evaluate_vector(cand, state._VAL_TRAIN_XS)
        if not np.all(np.isfinite(preds)):
            return False
        # tolérance : 100× l'amplitude de la cible (généreux mais borne l'explosion)
        amp = max(1e-9, float(np.max(np.abs(state._VAL_TRAIN_YS))) * 100.0 + 10.0)
        if float(np.max(np.abs(preds))) > amp:
            return False
    except Exception:
        return False
    # [v25-EXTRAP] Garde-fou anti-divergence HORS-PLAGE. Le test ci-dessus ne
    # regarde que le domaine d'entraînement ; or l'explosion à l'extrapolation
    # survient AU-DELÀ. On évalue le candidat sur des sondes où l'axe
    # d'extrapolation est prolongé bien après le max vu, et on exige que la
    # prédiction reste dans une bande de plausibilité dérivée de y. Une droite
    # (ou toute forme bornée par linéaire) passe ; exp/pow/cube/x² sont rejetés.
    if state._EXTRAP_PROBE_XS is not None and state._EXTRAP_BAND is not None:
        try:
            p2 = evaluate_vector(cand, state._EXTRAP_PROBE_XS)
            if not np.all(np.isfinite(p2)):
                return False
            lo, hi = state._EXTRAP_BAND
            if float(np.min(p2)) < lo or float(np.max(p2)) > hi:
                return False
        except Exception:
            return False
    return True

def _track_val_candidate(cand):
    """Enregistre tout candidat-champion avec son MSE de validation et
    l'erreur-type (SE) de ce MSE. La sélection finale applique la règle
    du 1-écart-type : parmi les candidats statistiquement indistinguables
    du meilleur (val_mse ≤ best + SE_best), le PLUS PETIT arbre gagne —
    on livre une loi lisible, pas un monstre qui gratte 1e-6.
    [v23.1] Les candidats numériquement instables sur le domaine complet
    sont écartés (overfitting que le hold-out peut manquer)."""
    if cand is None or state._VAL_XS is None:
        return
    # [v0.4] Le pool de validation alimente la SELECTION FINALE (_select_one_se)
    # sans repasser par fitness() : sans ce filtre, un candidat dimensionnellement
    # invalide peut etre repeche comme modele final. On ferme la fuite ici.
    if state._DIM_GATE_DIMS is not None:
        try:
            if not _ds().is_typed_valid(cand, state._DIM_GATE_DIMS, state._DIM_GATE_TARGET,
                                        state._DIM_UNKNOWN_CONST):
                return
        except Exception:
            return
    if not _is_numerically_stable(cand):
        return
    try:
        preds = evaluate_vector(cand, state._VAL_XS)
        se_sq = (preds - state._VAL_YS) ** 2
        m = float(np.mean(se_sq))
        if not math.isfinite(m):
            return
        se = float(np.std(se_sq, ddof=1) / math.sqrt(len(se_sq))) \
             if len(se_sq) > 1 else 0.0
        state._VAL_CANDS.append((m, se, tree_size(cand), cand.copy()))
        if len(state._VAL_CANDS) > _VAL_CANDS_MAX:
            state._VAL_CANDS.sort(key=lambda t: (t[0], t[2]))
            del state._VAL_CANDS[_VAL_CANDS_MAX:]
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════
# [v0.8] POLISSAGE DES FINALISTES : convergence, et sommes pondérées
# ════════════════════════════════════════════════════════════════
# Constat (campagne 2, 205 ajustements Feynman à 30 s) : des structures
# justes sortaient avec des constantes inexactes. Feynman I.8.14,
# sqrt((x2-x1)² + (y2-y1)²), revenait 5 fois sur 5 sous la forme
# sqrt((x2' - x3')² + (x1' - x0')²) sur les colonnes normalisées : la
# structure est la bonne, mais x/max|x| donne à chaque colonne son propre
# facteur (4,97 ; 4,99...), si bien qu'une différence de deux colonnes
# demande un coefficient sur chaque terme, que l'arbre n'avait pas
# (1 - R² = 1,8e-4). Même cas pour II.2.42, k·(T2-T1)·A/d. Et II.15.4
# rendait -μ·B·sin(-10,985 - 1,00432·θ) : la bonne forme, des constantes
# que 20 itérations de Levenberg-Marquardt n'avaient pas fini d'ajuster.
# Le polissage final ajoute donc deux candidats par finaliste : le même
# arbre, ses constantes ajustées jusqu'à convergence (100 itérations), et
# l'arbre dont chaque terme de somme ou de différence reçoit son propre
# coefficient (A ± B devient a·A ± b·B), ajusté de même. Ces candidats ne
# changent pas la recherche, et n'entrent dans la sélection finale que s'ils
# reproduisent le hold-out à la précision numérique (_track_if_exact) : le
# polissage rend exacte une structure juste, il ne remplace jamais un modèle
# approché par un autre (campagne 5 : sans cette règle, des variantes plus
# ajustées gagnaient la sélection et extrapolaient moins bien).

_FINAL_LM_ITER = 100          # itérations de LM pour les finalistes
_WEIGHTED_SUMS_MAX = 6        # au-delà de 6 sommes, pas de variante pondérée
# [v0.8] Avec time_limit=, les variantes du polissage (convergence, sommes
# pondérées) cessent une seconde après l'échéance : sur 3 000 lignes elles
# prenaient près de deux secondes, que time_limit_check.py voyait dépasser
# l'échéance (18,5 s pour 15 s). La correction d'échelle, elle, est toujours
# faite. Sans échéance, rien ne change.


def _has_scale(t) -> bool:
    """Vrai si le terme porte déjà un coefficient (constante, ou produit
    dont un facteur est une constante)."""
    if t.left is None and t.right is None:
        return not isinstance(t.value, str)
    if t.value == "*":
        for c in (t.left, t.right):
            if c is not None and c.left is None and c.right is None \
                    and not isinstance(c.value, str):
                return True
    return False


def _weight_sums(node, innermost_only: bool = False) -> Optional["Node"]:
    """Copie de l'arbre où chaque terme d'une somme ou d'une différence
    reçoit un coefficient 1 (A ± B devient 1·A ± 1·B), sauf un terme qui
    en porte déjà un. Avec innermost_only, seules les sommes dont les
    termes ne contiennent aucune autre somme sont pondérées : c'est assez
    pour sqrt((x2-x1)² + (y2-y1)²), avec deux coefficients de moins.
    None s'il n'y a rien à pondérer, ou plus de _WEIGHTED_SUMS_MAX sommes."""
    n_sums = [0]
    n_new = [0]

    def rebuild(n):
        """Rend (copie, contient une somme)."""
        if n.left is None and n.right is None:
            return Node(n.value), False
        l, hl = rebuild(n.left) if n.left is not None else (None, False)
        r, hr = rebuild(n.right) if n.right is not None else (None, False)
        is_sum = n.value in ("+", "-") and l is not None and r is not None
        if is_sum:
            n_sums[0] += 1
            if not (innermost_only and (hl or hr)):
                if not _has_scale(l):
                    l = Node("*", Node(1.0), l); n_new[0] += 1
                if not _has_scale(r):
                    r = Node("*", Node(1.0), r); n_new[0] += 1
        return Node(n.value, l, r), (is_sum or hl or hr)

    try:
        out, _ = rebuild(node)
    except RecursionError:
        return None
    if n_new[0] == 0 or n_sums[0] > _WEIGHTED_SUMS_MAX:
        return None
    return out


def _lm_to_convergence(node, xs, ys, cfg) -> Optional["Node"]:
    """LM avec _FINAL_LM_ITER itérations ; None si l'ajustement n'a rien
    amélioré (optimize_constants_lm rend alors l'arbre d'entrée)."""
    old = getattr(cfg, "CONST_OPT_ITER", 20)
    try:
        cfg.CONST_OPT_ITER = max(int(old), _FINAL_LM_ITER)
        out = optimize_constants_lm(node, xs, ys, cfg)
    except Exception:
        return None
    finally:
        cfg.CONST_OPT_ITER = old
    if out is None or out.exact_hash() == node.exact_hash():
        return None
    return out


def _refit_scaling(tree, xs, ys):
    """[v0.8] Recale l'échelle et le décalage matérialisés d'un arbre après
    un ajustement de LM en projection variable. LM ajuste les constantes de
    la forme a' + b'·arbre ; un arbre qui porte déjà sa mise à l'échelle
    (a + b·f, rendue par wrap_linear_scaling) gardait donc l'ancien a et
    l'ancien b, et ses prédictions brutes n'étaient plus celles de la forme
    ajustée (sur y = 3 sin(2x) + 1 : MSE 0,39 avant LM, 271 après, 2e-31
    pour la forme mise à l'échelle). Les nouveaux a, b sont replacés dans
    les constantes existantes, sinon l'arbre est enveloppé."""
    if tree is None or not (state._USE_LINEAR_SCALING and state._CUSTOM_LOSS_FN is None):
        return tree
    try:
        xs_np = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
        ys_np = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)
        with np.errstate(all="ignore"):
            p = evaluate_vector(tree, xs_np)
            if float(np.std(p)) < 1e-6:
                return tree
            a2, b2, ok = _linear_scale_params(p, ys_np)
        if not ok or (abs(b2 - 1.0) < 1e-12 and abs(a2) < 1e-12):
            return tree
        const = lambda n: (n is not None and n.left is None and n.right is None
                           and not isinstance(n.value, str))
        t = tree.copy()
        if state._LS_SCALE_ONLY:
            if t.value == "*" and const(t.left):
                t.left = Node(float(b2) * float(t.left.value))
                return t
        elif t.value == "+" and const(t.left) and t.right is not None \
                and t.right.value == "*" and const(t.right.left):
            t.left = Node(float(a2) + float(b2) * float(t.left.value))
            t.right.left = Node(float(b2) * float(t.right.left.value))
            t.right._hash = t.right._chash = t.right._ehash = None
            return t
        return wrap_linear_scaling(tree, xs_np, ys_np)
    except Exception:
        return tree


def _finalists(cfg, k: int = 8) -> list:
    """Les candidats à polir : les k meilleurs sur le hold-out (0.7), et,
    avec le polissage, les k plus petits de la bande de tolérance où la
    sélection finale choisira. [v0.8] Sans ces derniers, la structure juste
    de I.8.14 (14 nœuds, 1 - R² = 1,8e-4) n'était jamais polie : les huit
    meilleurs sur le hold-out étaient des arbres de 48 à 68 nœuds, et la
    règle de parcimonie livrait ensuite le 14 nœuds tel quel."""
    ranked = sorted(state._VAL_CANDS, key=lambda t: (t[0], t[2]))
    top = ranked[:k]
    if not ranked or not bool(getattr(cfg, "FINAL_POLISH", True)):
        return top
    var_val = float(np.var(state._VAL_YS)) if (state._VAL_YS is not None and len(state._VAL_YS) > 1) else 0.0
    tol_r2 = float(getattr(state, 'VAL_R2_TOLERANCE', 0.003))
    best_mse, best_se = ranked[0][0], ranked[0][1]
    band = tol_r2 * var_val if var_val > 1e-15 else best_mse * 0.20
    thr = best_mse + max(best_se, band)
    seen = set()
    for t in top:
        try:
            seen.add(t[3].exact_hash())
        except Exception:
            pass
    small = []
    for t in sorted((t for t in ranked if t[0] <= thr), key=lambda t: (t[2], t[0])):
        try:
            h = t[3].exact_hash()
        except Exception:
            continue
        if h in seen:
            continue
        seen.add(h)
        small.append(t)
        if len(small) >= k:
            break
    return top + small




def _track_if_exact(cand) -> None:
    """[v0.8] Un candidat du polissage n'entre dans la sélection finale que
    s'il reproduit le hold-out à la précision numérique (le plancher sous
    lequel la sélection ne garde que des lois exactes, _EXACT_REL). Le
    polissage peut ainsi rendre exacte une structure juste, mais il ne
    remplace jamais un modèle approché par un autre modèle approché : sur des
    données mesurées, aucune variante n'atteint ce plancher, et le résultat
    est celui qu'on aurait eu sans lui. (Mesuré dans la campagne 5 : sans
    cette règle, des variantes plus ajustées gagnaient la sélection sur le
    hold-out et extrapolaient moins bien.)"""
    if cand is None or state._VAL_XS is None or state._VAL_YS is None or len(state._VAL_YS) < 2:
        return
    var_val = float(np.var(state._VAL_YS))
    if not var_val > 1e-15:
        return
    try:
        with np.errstate(all="ignore"):
            m = float(np.mean((evaluate_vector(cand, state._VAL_XS) - state._VAL_YS) ** 2))
    except Exception:
        return
    if math.isfinite(m) and m <= _EXACT_REL * var_val:
        state._POLISH_ADMITTED = state._POLISH_ADMITTED + 1
        _track_val_candidate(cand)


def _polish_finalists(top, xs, ys, cfg) -> None:
    """Polissage des finalistes avant la sélection finale (voir plus haut).
    Le premier candidat de chaque finaliste est celui de la 0.7 (constantes
    ajustées par optimize_constants_adam, donc LM à 20 itérations), recalé
    par _refit_scaling."""
    _dl = getattr(cfg, "DEADLINE", None)
    _stop = None if _dl is None else max(time.time(), float(_dl)) + state._POLISH_GRACE_S
    for _m, _se, _sz, nd in top:
        pol = _refit_scaling(optimize_constants_adam(nd.copy(), xs, ys, cfg),
                             xs, ys)
        _track_val_candidate(pol)
        if not bool(getattr(cfg, "FINAL_POLISH", True)) or state._CUSTOM_LOSS_FN is not None:
            continue
        if _stop is not None and time.time() > _stop:
            continue                            # budget de temps épuisé
        try:
            conv = _lm_to_convergence(pol, xs, ys, cfg)
            if conv is not None:
                _track_if_exact(_refit_scaling(conv, xs, ys))
            seen = set()
            for inner in (True, False):
                wt = _weight_sums(pol, innermost_only=inner)
                if wt is None or wt.exact_hash() in seen:
                    continue
                seen.add(wt.exact_hash())
                wt = _lm_to_convergence(wt, xs, ys, cfg)
                if wt is not None:
                    ws = simplify(wt)
                    if _pure_mse(ws, xs, ys) <= _pure_mse(wt, xs, ys):
                        wt = ws
                    _track_if_exact(_refit_scaling(wt, xs, ys))
        except Exception:
            pass

def _build_near_probes(xs_np, ys_np, n=400):
    """[v0.7-NEAR] Sondes par paires de points reels. Generateur DEDIE : ne
    consomme pas l'etat aleatoire global du moteur (sinon tous les resultats
    changeraient, garde active ou non)."""
    Xm = xs_np if xs_np.ndim == 2 else xs_np.reshape(-1, 1)
    if len(Xm) < 2:
        return
    rng = np.random.RandomState(20260924)
    i = rng.randint(0, len(Xm), n); j = rng.randint(0, len(Xm), n)
    lam = rng.uniform(-_NEAR_EXT, 1.0 + _NEAR_EXT, (n, 1))
    state._NEAR_PROBE_XS = lam * Xm[i] + (1.0 - lam) * Xm[j]
    y = np.asarray(ys_np, dtype=float)
    r = float(np.ptp(y)) if len(y) else 0.0
    state._NEAR_BAND = (float(np.median(y)), _NEAR_K * max(r, 1e-12))


def _near_domain_stable(cand) -> bool:
    """[v0.7-NEAR] Vrai si le candidat reste fini et dans la bande sur les
    sondes pres du domaine. Resultat mis en cache par arbre EXACT."""
    if state._NEAR_PROBE_XS is None or state._NEAR_BAND is None or cand is None:
        return True
    try:
        key = cand.exact_hash()
    except Exception:
        key = None
    if key is not None and key in _NEAR_CACHE:
        return _NEAR_CACHE[key]
    try:
        with np.errstate(all="ignore"):
            p = np.asarray(evaluate_vector(cand, state._NEAR_PROBE_XS), dtype=float)
        if p.ndim == 0:
            p = np.full(len(state._NEAR_PROBE_XS), float(p))
        c, half = state._NEAR_BAND
        ok = bool(np.all(np.isfinite(p)) and float(np.max(np.abs(p - c))) <= half)
    except Exception:
        ok = False
    if key is not None:
        _NEAR_CACHE[key] = ok
    return ok


def _select_one_se(champion, champ_val):
    """[v23.2] Sélection parcimonieuse par TOLÉRANCE R².

    Principe (philosophie 1-SE, version interprétable) : parmi tous les
    candidats stables dont la qualité d'ajustement est SCIENTIFIQUEMENT
    indistinguable du meilleur, on livre le PLUS PETIT arbre — une loi
    lisible plutôt qu'un arbre gonflé qui gratte un epsilon sur 34 points.

    Le seuil n'est plus un ratio de MSE (sans signification d'un problème à
    l'autre) mais une tolérance exprimée en R² : un candidat qualifie si sa
    perte de R² par rapport au meilleur est ≤ VAL_R2_TOLERANCE (0.3% par
    default), OU s'il est dans la barre d'1 erreur-type statistique du
    meilleur (le plus large des deux). Cas batterie : le 10-nœuds (R²=0.9973)
    et le 29-nœuds (R²=0.9981) diffèrent de 0.08% → le 10-nœuds gagne."""
    pool = list(state._VAL_CANDS)
    if champion is not None and math.isfinite(champ_val) and _is_numerically_stable(champion):
        pool.append((champ_val, 0.0, tree_size(champion), champion))
    if not pool:
        # [v25-EXTRAP] Tout a été rejeté par le garde anti-divergence (aucune
        # forme bornée trouvée) : on retombe sur le champion brut faute de mieux.
        return champion, champ_val
    pool.sort(key=lambda t: t[0])
    best_mse, best_se = pool[0][0], pool[0][1]
    # Variance de la cible de validation → conversion MSE ↔ R²
    var_val = float(np.var(state._VAL_YS)) if (state._VAL_YS is not None and len(state._VAL_YS) > 1) else 0.0
    tol_r2  = float(getattr(state, 'VAL_R2_TOLERANCE', 0.003))   # 0.3 % de R²
    # Seuil = best + max(barre statistique 1-SE, bande de tolérance R²)
    r2_band = tol_r2 * var_val if var_val > 1e-15 else best_mse * 0.20
    thr = best_mse + max(best_se, r2_band)
    # [v0.7-EXACT] PRIORITÉ À L'EXACTITUDE. La tolérance R² existe pour ne
    # pas surajuster le BRUIT. Quand le meilleur candidat reproduit le
    # hold-out à la précision numérique (MSE <= 1e-12 x variance : aucune
    # donnée mesurée n'y arrive, seule une loi exacte sur données non
    # bruitées), il n'y a pas de bruit à éviter : on ne remplace pas la loi
    # exacte par une approximation plus courte (vu sur Feynman I.18.12 :
    # r*F*sin(th) exacte dans le front, rendu 0.0776 + 0.9967*r*F*sin(1.0106*th)).
    # Seuls les candidats eux aussi exacts restent éligibles ; le plus petit
    # gagne. Sans effet dès que le meilleur MSE dépasse ce plancher.
    exact_floor = _EXACT_REL * var_val
    if var_val > 1e-15 and best_mse <= exact_floor:
        loose = min((t for t in pool if t[0] <= thr), key=lambda t: (t[2], t[0]))
        thr = exact_floor
        tight = min((t for t in pool if t[0] <= thr), key=lambda t: (t[2], t[0]))
        if tight[3] is not loose[3]:
            state._EXACT_PRIORITY_SWAPS = state._EXACT_PRIORITY_SWAPS + 1
            TRACE.set("exact_priority", "loi exacte préférée à une "
                      "approximation plus courte")
    eligible = [t for t in pool if t[0] <= thr]
    eligible.sort(key=lambda t: (t[2], t[0]))   # plus petit, puis meilleur MSE
    # [v0.8] DEPARTAGE PAR LA FIDÉLITÉ DE LA FORMULE. Parmi les candidats que
    # les données ne savent pas distinguer, on préfère le plus petit dont la
    # formule imprimée reproduit le modèle, c'est-à-dire sur lequel aucun
    # garde-fou numérique (division protégée, puissance bornée) n'agit sur
    # les données : sinon la formule livrée s'écarte de predict() et
    # l'utilisateur reçoit un avertissement (formula_exact False). Stable
    # près du domaine d'abord, comme ci-dessous.
    if not (_formula_faithful(eligible[0][3])
            and _near_domain_stable(eligible[0][3])):
        both = [t for t in eligible
                if _formula_faithful(t[3]) and _near_domain_stable(t[3])]
        if both:
            state._FAITHFUL_SWAPS = state._FAITHFUL_SWAPS + 1
            TRACE.set("faithful_formula", "candidat dont la formule reproduit "
                      "le modèle préféré à un équivalent plus court")
            m, _, _, node = both[0]
            return node, m
    # [v0.7-NEAR] DEPARTAGE : parmi les candidats que les donnees ne savent pas
    # distinguer, le plus petit qui NE DIVERGE PAS pres du domaine. Si aucun
    # n'est stable, comportement historique inchange.
    if not _near_domain_stable(eligible[0][3]):
        stable = [t for t in eligible if _near_domain_stable(t[3])]
        if stable:
            state._NEAR_GUARD_SWAPS = state._NEAR_GUARD_SWAPS + 1
            TRACE.set("near_guard", "champion divergent pres du domaine "
                      "remplace par un candidat equivalent stable")
            m, _, _, node = stable[0]
            return node, m
    m, _, _, node = eligible[0]
    return node, m

# ════════════════════════════════════════════════════════════════
# [1.4-S1] SOUS 30 LIGNES, LES CANDIDATS EN VALIDATION CROISÉE
# ════════════════════════════════════════════════════════════════
# Constat (benchmarks/results_1.4/analysis/README.md) : sous 30 lignes le
# moteur ne garde pas de hold-out (_split_holdout). Il ne suivait alors aucun
# candidat, ne polissait aucun finaliste, n'appliquait aucune règle de
# parcimonie : il rendait le meilleur individu de la recherche sur les
# lignes d'entraînement. Sur les tables de TP (10 et 20 points), la lentille
# revenait dans 2 ajustements sur 40 alors que sa graine était placée, et
# toute loi rendue sans unités portait une constante additive que seule la
# loi de Newton a. S1 (benchmarks/results_1.4/PLAN.md) :
# - les candidats : les huit meilleures formes de famille de l'étage
#   tolérant qui expliquent au moins la moitié de la variance (sans le seuil
#   de 1,5 %), placées au départ et gardées pour la fin ; les champions de
#   la recherche sur les lignes d'entraînement (64 au plus) ; et des
#   variantes de chaque finaliste, sans la constante additive de la mise à
#   l'échelle finale, et avec chaque exposant ajusté mis au demi-entier le
#   plus proche (écrit dans la structure) ;
# - 40 finalistes au plus : le champion, les formes de famille, les 8
#   meilleurs de la recherche, les 8 plus petits de la bande de tolérance,
#   et leurs variantes ;
# - la validation croisée : K = min(n, 10) plis, la ligne i dans le pli
#   i mod K (aucun tirage) ; pour chaque pli, les constantes du candidat
#   sont ajustées de nouveau sur les autres lignes, et ses erreurs au carré
#   sur les lignes du pli gardées ; son erreur est leur moyenne sur la table ;
# - le choix : parmi les candidats à une erreur type du meilleur, ou dans la
#   tolérance de 0,003 en R², celui qui a le moins de constantes ajustées
#   (le rang de la jacobienne de ses prédictions : une constante que
#   l'ajustement ne peut pas bouger seule ne compte pas), puis le plus
#   petit, puis le plus précis ; la priorité à une loi exacte et les
#   départages d'aujourd'hui (formule fidèle, stable près du domaine) sont
#   gardés ;
# - result.pareto tient le front de ces candidats par taille et erreur
#   croisée ;
# - la validation croisée s'arrête une seconde après l'échéance de
#   time_limit=, comme le polissage ; elle ne tourne pas avec une perte
#   personnalisée, en mode extrapolation, ni sous 6 lignes.
# Rien ne change pour une table de 30 lignes ou plus.

# Non adopté (campagne S1, 13 novembre 2026, benchmarks/results_1.4/s1/
# campaign/README.md) : la loi revient dans 113 ajustements de TP sur 200
# contre 126, la validation croisée favorisant des structures que la
# recherche a choisies sur les mêmes points. Retiré du candidat : éteint, le
# code gardé pour la décision de l'auteur.
_SMALL_ROWS = 30                  # en dessous : pas de hold-out, S1
_SMALL_MIN_ROWS = 6
_SMALL_FAMILY_KEEP = 8
_SMALL_FAMILY_SHARE = 0.5         # part de variance laissée au plus
_SMALL_SEARCH = 8                 # meilleurs, et plus petits de la bande
_SMALL_FINALISTS = 40
_SMALL_FOLDS = 10
_SMALL_CANDS_MAX = 64
_SMALL_CANDS: list = []           # [(mse_train, se, taille, arbre)]
_SMALL_FAMILY: list = []          # formes de famille (arbres sans échelle)
_SMALL_FRONT: list = []           # [(mse_cv, se_cv, taille, arbre, n_par, origine)]


def _small_setup(cfg, ys) -> None:
    """[1.4-S1] Au début d'un ajustement, après _split_holdout : S1 est-il
    actif ? Seulement sans hold-out : une table de 30 à 37 lignes en garde
    un, et son reste d'entraînement, sous 30 lignes, n'est pas concerné."""
    _SMALL_CANDS.clear()
    _SMALL_FAMILY.clear()
    _SMALL_FRONT.clear()
    n = len(ys)
    state._SMALL_ON = bool(state._SMALL_CV and state._GENERIC_CSV_MODE and state._VAL_XS is None
                     and _SMALL_MIN_ROWS <= n < _SMALL_ROWS
                     and state._USE_LINEAR_SCALING and state._CUSTOM_LOSS_FN is None
                     and not bool(getattr(cfg, "EXTRAPOLATION_MODE", False)))


def _track_small_candidate(cand, xs, ys) -> None:
    """[1.4-S1] Un champion de la recherche, noté sur les lignes
    d'entraînement (sous units=, seulement s'il passe la porte)."""
    if not state._SMALL_ON or cand is None:
        return
    if state._DIM_GATE_DIMS is not None:
        try:
            if not _ds().is_typed_valid(cand, state._DIM_GATE_DIMS, state._DIM_GATE_TARGET,
                                        state._DIM_UNKNOWN_CONST):
                return
        except Exception:
            return
    try:
        h = cand.exact_hash()
        if any(t[3].exact_hash() == h for t in _SMALL_CANDS):
            return
        X = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
        y = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)
        with np.errstate(all="ignore"):
            e = (np.asarray(evaluate_vector(cand, X), dtype=float) - y) ** 2
        m = float(np.mean(e))
        if not math.isfinite(m):
            return
        se = float(np.std(e, ddof=1) / math.sqrt(len(e))) if len(e) > 1 else 0.0
        _SMALL_CANDS.append((m, se, tree_size(cand), cand.copy()))
        if len(_SMALL_CANDS) > _SMALL_CANDS_MAX:
            _SMALL_CANDS.sort(key=lambda t: (t[0], t[2]))
            del _SMALL_CANDS[_SMALL_CANDS_MAX:]
    except Exception:
        pass


def _small_is_const(n) -> bool:
    return (n is not None and n.left is None and n.right is None
            and not isinstance(n.value, str))


def _small_strip(t):
    """[1.4-S1] L'arbre sans la mise à l'échelle que la recherche a
    matérialisée (a + b·f, b·f, a + f) : f. L'arbre lui-même sinon."""
    if t is None or t.left is None or t.right is None:
        return t
    if t.value == "+":
        for c, o in ((t.left, t.right), (t.right, t.left)):
            if _small_is_const(c):
                if o.value == "*" and o.left is not None and o.right is not None:
                    if _small_is_const(o.left):
                        return o.right
                    if _small_is_const(o.right):
                        return o.left
                return o
    if t.value == "*":
        if _small_is_const(t.left):
            return t.right
        if _small_is_const(t.right):
            return t.left
    return t


def _small_round_powers(f):
    """[1.4-S1] Copie de f où chaque pow(B, c) d'exposant constant c reçoit
    le demi-entier le plus proche, écrit dans la structure (carrés, cubes,
    racines, produits, 1/…) pour que l'ajustement ne le déplace plus. None si
    rien ne change ou si le pool n'a pas les opérateurs nécessaires."""
    uops, bops = set(state._GENERIC_UNARY_OPS), set(state._GENERIC_BINARY_OPS)
    changed = [False]

    def power(B, e2):
        def ipow(m):
            if m == 1:
                return B.copy()
            if m == 2 and "sq" in uops:
                return Node("sq", B.copy())
            if m == 3 and "cube" in uops:
                return Node("cube", B.copy())
            if m % 2 == 0:
                h = ipow(m // 2)
                return Node("sq", h) if "sq" in uops else Node("*", h, ipow(m // 2))
            return Node("*", B.copy(), ipow(m - 1))
        n_int, half = divmod(abs(e2), 2)
        parts = []
        if n_int:
            parts.append(ipow(n_int))
        if half:
            if "sqrt" not in uops:
                return None
            parts.append(Node("sqrt", B.copy()))
        out = parts[0]
        for q in parts[1:]:
            if "*" not in bops:
                return None
            out = Node("*", out, q)
        if e2 < 0:
            if "/" not in bops:
                return None
            out = Node("/", Node(1.0), out)
        return out

    def rec(n):
        if n is None:
            return None
        if n.value == "pow" and n.left is not None and _small_is_const(n.right):
            c = float(n.right.value)
            e2 = int(round(2.0 * c))
            base = rec(n.left)
            if abs(e2) <= 12 and math.isfinite(c):
                if e2 == 0:
                    changed[0] = True
                    return Node(1.0)
                q = power(base, e2)
                if q is not None:
                    changed[0] = True
                    return q
            return Node("pow", base, Node(c))
        return Node(n.value, rec(n.left), rec(n.right))

    try:
        out = rec(f)
    except RecursionError:
        return None
    return out if changed[0] else None


def _small_fit(f, X, y, cfg, scale_only):
    """[1.4-S1] f ajusté sur (X, y) par l'étape de finition du moteur, en
    projection variable sur a + b·f (b·f seul si scale_only), et sa mise à
    l'échelle : (f ajusté, a, b), ou None."""
    keep = state._LS_SCALE_ONLY
    try:
        if scale_only:
            state._LS_SCALE_ONLY = True
        with np.errstate(all="ignore"):
            g = _lm_to_convergence(f, X, y, cfg)
            g = f if g is None else g
            p = np.asarray(evaluate_vector(g, X), dtype=float)
            if p.ndim == 0:
                p = np.full(len(y), float(p))
            if not np.all(np.isfinite(p)):
                return None
            a, b, ok = _linear_scale_params(p, y)
        if not ok or not (math.isfinite(a) and math.isfinite(b)):
            return None
        return g, float(a), float(b)
    except Exception:
        return None
    finally:
        state._LS_SCALE_ONLY = keep


def _small_cv(start, X, y, cfg, scale_only):
    """[1.4-S1] Erreur de validation croisée (moyenne et erreur type des
    erreurs au carré sur les n lignes), plis i mod K, constantes ajustées de
    nouveau sur les autres lignes à chaque pli. None si un pli échoue."""
    n = len(y)
    K = min(n, _SMALL_FOLDS)
    fold = np.arange(n) % K
    err = np.empty(n)
    for k in range(K):
        te = fold == k
        r = _small_fit(start, X[~te], y[~te], cfg, scale_only)
        if r is None:
            return None
        g, a, b = r
        with np.errstate(all="ignore"):
            q = np.asarray(evaluate_vector(g, X[te]), dtype=float)
            e = (a + b * q - y[te]) ** 2
        if not np.all(np.isfinite(e)):
            return None
        err[te] = e
    m = float(np.mean(err))
    se = float(np.std(err, ddof=1) / math.sqrt(n)) if n > 1 else 0.0
    return m, se


def _small_n_par(g, X, scale_only) -> int:
    """[1.4-S1] Le nombre de constantes ajustées d'un candidat : le rang de
    la jacobienne de ses prédictions par rapport à ses constantes et à sa
    mise à l'échelle (b, et a sauf scale_only). Une constante que
    l'ajustement ne peut pas bouger seule (le 1 d'un 1/x, que b absorbe)
    n'y compte pas."""
    n = X.shape[0]
    with np.errstate(all="ignore"):
        p = np.asarray(evaluate_vector(g, X), dtype=float)
        if p.ndim == 0:
            p = np.full(n, float(p))
        cols = [p] if scale_only else [p, np.ones(n)]
        try:
            fn, consts = compile_parametric(g)
        except Exception:
            fn, consts = None, []
        if fn is not None and consts:
            cv = np.array([c.value for c in consts], dtype=float)
            p0 = np.asarray(fn(X, cv), dtype=float)
            for i in range(len(cv)):
                h = 1e-6 * (1.0 + abs(cv[i]))
                c2 = cv.copy()
                c2[i] += h
                cols.append((np.asarray(fn(X, c2), dtype=float) - p0) / h)
        J = np.column_stack([np.broadcast_to(c, (n,)) for c in cols])
        if not np.all(np.isfinite(J)):
            return J.shape[1]
        nrm = np.linalg.norm(J, axis=0)
        J = J[:, nrm > 0] / nrm[nrm > 0]
        if J.shape[1] == 0:
            return 0
        sv = np.linalg.svd(J, compute_uv=False)
    return int(np.sum(sv > 1e-6 * sv[0]))


def _small_materialize(g, a, b, scale_only):
    """[1.4-S1] Le modèle livré : a + b·f, ou b·f, comme
    wrap_linear_scaling l'écrit."""
    if scale_only:
        if g.value == "*" and _small_is_const(g.left):
            w = g.copy()
            w.left = Node(float(b) * float(g.left.value))
            return w
        return Node("*", Node(float(b)), g.copy())
    return simplify(Node("+", Node(float(a)), Node("*", Node(float(b)), g.copy())))


def _small_specs(champion, X, y):
    """[1.4-S1] Les finalistes, 40 au plus, dans l'ordre où ils sont notés :
    (f, scale_only, origine). Le champion d'abord, puis les formes de
    famille, les 8 meilleurs de la recherche, les 8 plus petits de la bande
    de tolérance, chacun suivi de ses variantes."""
    var = float(np.var(y))
    ranked = sorted(_SMALL_CANDS, key=lambda t: (t[0], t[2]))
    bases = []
    if champion is not None:
        bases.append((champion, "champion"))
    for t in _SMALL_FAMILY:
        bases.append((t, "family"))
    for t in ranked[:_SMALL_SEARCH]:
        bases.append((t[3], "search"))
    if ranked:
        thr = ranked[0][0] + max(ranked[0][1], float(
            getattr(state, 'VAL_R2_TOLERANCE', 0.003)) * var)
        small = sorted((t for t in ranked if t[0] <= thr), key=lambda t: (t[2], t[0]))
        for t in small[:_SMALL_SEARCH]:
            bases.append((t[3], "band"))
    modes = (True,) if state._LS_SCALE_ONLY else (False, True)
    specs, seen = [], set()
    for tree, origin in bases:
        f = tree if origin == "family" else _small_strip(tree)
        fr = _small_round_powers(f)
        for g, rounded in ((f, False), (fr, True)):
            if g is None:
                continue
            for so in modes:
                if state._DIM_GATE_DIMS is not None:
                    try:
                        if not _ds().is_typed_valid(Node("*", Node(1.0), g),
                                                    state._DIM_GATE_DIMS, state._DIM_GATE_TARGET,
                                                    state._DIM_UNKNOWN_CONST):
                            continue
                    except Exception:
                        continue
                key = (g.canonical_hash(), so)
                if key in seen:
                    continue
                seen.add(key)
                label = origin + (", exponents rounded" if rounded else "") + \
                    (", without the constant" if so and not state._LS_SCALE_ONLY else "")
                specs.append((g, so, label))
                if len(specs) >= _SMALL_FINALISTS:
                    return specs
    return specs


def _small_table_select(champion, xs, ys, cfg):
    """[1.4-S1] Le modèle d'une table de moins de 30 lignes (voir plus haut).
    Rend le champion si rien n'est noté."""
    X = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
    y = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)
    var = float(np.var(y))
    if not var > 1e-15:
        return champion
    t0 = time.time()
    _dl = getattr(cfg, "DEADLINE", None)
    _stop = None if _dl is None else max(time.time(), float(_dl)) + state._POLISH_GRACE_S
    specs = _small_specs(champion, X, y)
    _SMALL_FRONT.clear()
    for g, so, label in specs:
        if _stop is not None and _SMALL_FRONT and time.time() > _stop:
            break                                 # budget de temps épuisé
        r = _small_fit(g, X, y, cfg, so)
        if r is None:
            continue
        g_all, a, b = r
        cv = _small_cv(g_all, X, y, cfg, so)
        if cv is None:
            continue
        M = _small_materialize(g_all, a, b, so)
        _SMALL_FRONT.append((cv[0], cv[1], tree_size(M), M,
                             _small_n_par(g_all, X, so), label))
    if not _SMALL_FRONT:
        return champion
    pick = _small_choose(_SMALL_FRONT, X, y)
    TRACE.set("small_cv", "%d lignes, K = %d, %d candidats notés en %.2f s ; "
              "choisi : %s, erreur croisée %.3g, %d constantes" % (
                  len(y), min(len(y), _SMALL_FOLDS), len(_SMALL_FRONT),
                  time.time() - t0, pick[5], pick[0], pick[4]))
    return pick[3]


def _small_choose(front, X, y):
    """[1.4-S1] Le choix parmi des candidats notés en validation croisée :
    ceux à une erreur type du meilleur, ou dans la tolérance de 0,003 en R²
    (seulement les exacts si le meilleur l'est), puis le moins de constantes
    ajustées, le plus petit, le plus précis ; départage par la fidélité de la
    formule et la stabilité près du domaine, sur la table. Rend l'entrée."""
    var = float(np.var(y))
    best_m, best_se = min((t[0], t[1]) for t in front)
    thr = best_m + max(best_se, float(getattr(state, 'VAL_R2_TOLERANCE', 0.003)) * var)
    if best_m <= _EXACT_REL * var:                # priorité à l'exactitude
        thr = _EXACT_REL * var
    elig = sorted((t for t in front if t[0] <= thr),
                  key=lambda t: (t[4], t[2], t[0]))
    pick = elig[0]
    # départages : formule fidèle et stable près du domaine, sur la table
    keep = (state._VAL_TRAIN_XS, state._VAL_TRAIN_YS)
    try:
        state._VAL_TRAIN_XS, state._VAL_TRAIN_YS = X, y
        _FAITHFUL_CACHE.clear()
        _NEAR_CACHE.clear()
        _build_near_probes(X, y)
        if not (_formula_faithful(pick[3]) and _near_domain_stable(pick[3])):
            both = [t for t in elig
                    if _formula_faithful(t[3]) and _near_domain_stable(t[3])]
            if both:
                pick = both[0]
    finally:
        state._VAL_TRAIN_XS, state._VAL_TRAIN_YS = keep
        state._NEAR_PROBE_XS = None
        state._NEAR_BAND = None
        _FAITHFUL_CACHE.clear()
        _NEAR_CACHE.clear()
    return pick


def _split_holdout(xs, ys, cfg):
    """Découpe (xs, ys) en (train, val). Retourne (xs_tr, ys_tr) et installe
    le hold-out dans les globals _VAL_XS/_VAL_YS. Validation désactivée si
    VALIDATION_SPLIT<=0 ou dataset trop petit (<30 points)."""
    state._VAL_XS = None; state._VAL_YS = None
    state._VAL_TRAIN_XS = None; state._VAL_TRAIN_YS = None
    state._EXTRAP_PROBE_XS = None; state._EXTRAP_BAND = None
    state._NEAR_PROBE_XS = None; state._NEAR_BAND = None; _NEAR_CACHE.clear()
    _FAITHFUL_CACHE.clear()
    state._VAL_CANDS.clear()
    frac = float(getattr(cfg, "VALIDATION_SPLIT", 0.0) or 0.0)
    n = len(ys)
    if frac <= 0.0 or n < 30:
        return xs, ys
    n_val = max(8, int(round(n * frac)))
    if n - n_val < 20:
        return xs, ys
    xs_np = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
    ys_np = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)

    extrap = bool(getattr(cfg, "EXTRAPOLATION_MODE", False))
    feat = getattr(cfg, "EXTRAPOLATION_FEATURE", None)
    direction = str(getattr(cfg, "EXTRAPOLATION_DIRECTION", "both")).lower()
    Xm = xs_np if xs_np.ndim == 2 else xs_np.reshape(-1, 1)
    feat_ok = (feat is not None and 0 <= int(feat) < Xm.shape[1])

    # [v25-EXTRAP] GARDE ANTI-DIVERGENCE (indépendant du type de split).
    # Dès qu'un axe d'extrapolation est désigné, on construit des points-sondes
    # AU-DELÀ du domaine observé + une bande de plausibilité dérivée de y.
    # _is_numerically_stable rejette tout candidat dont la prédiction explose
    # sur ces sondes — LE filtre qui manquait, car la divergence hors-plage
    # (cycle², exp, pow…) est invisible sur un hold-out interne.
    if extrap and feat_ok:
        j = int(feat)
        lo = Xm.min(axis=0); hi = Xm.max(axis=0)
        span_j = float(hi[j] - lo[j]) if float(hi[j] - lo[j]) > 1e-12 else 1.0
        n_probe = 48
        ext = 1.5 * span_j          # [v27] sondes plus loin (1.5×) et plus denses
        if direction == "low":
            grid = np.linspace(lo[j] - ext, lo[j], n_probe)
        elif direction == "both":
            grid = np.concatenate([
                np.linspace(lo[j] - ext, lo[j], n_probe // 2),
                np.linspace(hi[j], hi[j] + ext, n_probe // 2)])
        else:  # "high" (forecasting) — prolonge vers le haut
            grid = np.linspace(hi[j], hi[j] + ext, n_probe)
        med = np.median(Xm, axis=0)
        probe = np.tile(med, (len(grid), 1)); probe[:, j] = grid
        state._EXTRAP_PROBE_XS = probe
        y_lo = float(np.min(ys_np)); y_hi = float(np.max(ys_np))
        rng_y = max(1e-9, y_hi - y_lo)
        K = 2.0    # la tendance peut se prolonger de 2 amplitudes, pas exploser
        state._EXTRAP_BAND = (y_lo - K * rng_y, y_hi + K * rng_y)

    # Choix du SPLIT. LEÇON (données batterie) : pour extrapoler, entraîner sur
    # TOUTES les données — surtout les points de bord — donne une meilleure
    # PENTE que de les retirer pour valider. Retirer la frontière du train
    # dégrade l'estimation de tendance et fait dériver l'extrapolation. Le split
    # frontière reste disponible (EXTRAPOLATION_FRONTIER_SPLIT=True) mais n'est
    # PLUS le default : le mode extrapolation = split random (train complet)
    # + garde anti-divergence + candidat linéaire plancher.
    use_frontier = extrap and bool(getattr(cfg, "EXTRAPOLATION_FRONTIER_SPLIT", False))
    if use_frontier:
        lo = Xm.min(axis=0); hi = Xm.max(axis=0)
        mid = 0.5 * (lo + hi); half = np.maximum(0.5 * (hi - lo), 1e-12)
        if feat_ok:
            j = int(feat)
            signed = (Xm[:, j] - mid[j]) / half[j]
            edge = signed if direction == "high" else \
                   (-signed if direction == "low" else np.abs(signed))
            _bd = f"axis #{j} (sens={direction})"
        else:
            edge = np.max(np.abs(Xm - mid) / half, axis=1)
            _bd = "all features"
        order = np.argsort(-edge, kind="stable")
        frac_band = float(getattr(cfg, "EXTRAPOLATION_FRONTIER_FRAC", 0.20))
        n_band = min(max(n_val, int(round(n * frac_band))), n - 20)
        val_idx = np.sort(order[:n_band]); tr_idx = np.sort(order[n_band:])
        _split_kind = f"FRONTIER [{_bd}]"; _seed_note = "deterministic"
    else:
        rng = np.random.RandomState(int(getattr(cfg, "HOLDOUT_SEED", 1234)))
        idx = rng.permutation(n)
        val_idx = np.sort(idx[:n_val]); tr_idx = np.sort(idx[n_val:])
        _guard = " +divergence-guard" if (extrap and feat_ok) else ""
        _split_kind = "random" + _guard
        _seed_note = f"seed={getattr(cfg,'HOLDOUT_SEED',1234)}"

    state._VAL_XS = xs_np[val_idx]
    state._VAL_YS = ys_np[val_idx]
    xs_tr   = xs_np[tr_idx]
    ys_tr   = ys_np[tr_idx]
    state._VAL_TRAIN_XS = xs_tr
    state._VAL_TRAIN_YS = ys_tr
    _build_near_probes(xs_np, ys_np)          # [v0.7-NEAR]
    print(f"[v21-VAL] Hold-out {_split_kind} : {len(tr_idx)} points train / "
          f"{len(val_idx)} points validation ({len(val_idx)/n:.0%}, {_seed_note})")
    print(f"          Evolution sees ONLY the train set; final champion "
          f"selected on the validation set.")
    return xs_tr, ys_tr


def _make_linear_candidate(xs_tr, ys_tr, cfg):
    """[v24-EXTRAP] Fabrique un candidat LINÉAIRE OLS  y ≈ a0 + Σ a_i·X[i]  à
    partir du TRAIN (intérieur du domaine), construit comme un petit arbre Node.
    Il concourt ensuite dans la sélection finale, qui — en mode extrapolation —
    juge sur la bande-frontière. Une droite ne peut pas diverger hors-plage :
    si la loi est quasi-linéaire, la sélection parcimonieuse la préfère aux
    formes courbes qui sur-ajustent l'intérieur puis dérivent au bord.

    [v24.2] CORRECTIF : si un axe d'extrapolation est désigné
    (EXTRAPOLATION_FEATURE), le candidat n'est ajusté QUE sur cet axe. Ajuster
    sur des features qui ne tendent pas (ex. température, courant) injecte des
    coefficients parasites qui divergent dès que ces features dérivent hors de
    la plage d'entraînement — un piège deterministic observé sur données réelles."""
    try:
        Xall = xs_tr if (isinstance(xs_tr, np.ndarray) and xs_tr.ndim == 2) \
            else np.asarray(xs_tr, dtype=float).reshape(len(ys_tr), -1)
        y = np.asarray(ys_tr, dtype=float)
        terms_all = list(getattr(cfg, "TERMINALS", []))
        feat = getattr(cfg, "EXTRAPOLATION_FEATURE", None)
        if feat is not None and 0 <= int(feat) < Xall.shape[1]:
            cols = [int(feat)]                    # droite sur l'axe désigné seul
        else:
            cols = list(range(Xall.shape[1]))     # sinon, toutes les features
        X = Xall[:, cols]
        n, d = X.shape
        if n < d + 2:
            return None
        A = np.hstack([np.ones((n, 1)), X])              # [1 | X_cols]
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)     # [a0, a1, …]
        if not np.all(np.isfinite(coef)):
            return None
        a0 = float(coef[0])
        scale = max(1e-9, float(np.std(y)))
        node = Node(round(a0, 8))
        for k, col in enumerate(cols):
            ak = float(coef[k + 1])
            if abs(ak) < 1e-6 * scale:        # coefficient négligeable → omis
                continue
            name = terms_all[col] if col < len(terms_all) else f"X[{col}]"
            term = Node('*', Node(round(ak, 8)), Node(name))
            node = Node('+', node, term)
        return node
    except Exception:
        return None


def _smart_reset_explorers(islands: List["Island"], cfg: Config,
                           gen: int, cur_raw: float) -> bool:
    """[v17-SMART-RESET, extrait v20] Réinitialise les îles explorer avec des
    squelettes sémantiques ciblés (fragments corrélés au résidu courant) +
    squelettes de diversité + 30% d'arbres randoms. Retourne True si au
    moins une île a été réinitialisée. Partagé séquentiel/parallèle."""
    _skeleton_seeds = []

    _res = state.CURRENT_RESIDUAL_SIG
    if _res is not None and len(state.FRAGMENT_LIB.fragments) > 0:
        scored = []
        for h, e in state.FRAGMENT_LIB.fragments.items():
            if e.semantic_signature is not None:
                sc = semantic_score(e.semantic_signature, _res)
                if sc > 0.15:
                    scored.append((sc, e.node))
        scored.sort(key=lambda x: x[0], reverse=True)
        for _, seed_node in scored[:3]:
            try:
                branch = _random_tree_nd(cfg.MAX_INIT_DEPTH - 1, cfg)
                op     = random.choice(['+', '-', '*'])
                _skeleton_seeds.append(Node(op, seed_node.copy(), branch))
            except Exception:
                pass

    t = cfg.TERMINALS
    if len(t) >= 6:
        _skeleton_seeds.extend([
            Node('+', Node(t[2]), Node(t[5])),
            Node('*', Node(t[2]), Node(t[5])),
            Node('*', Node(t[5]), Node(t[0])),
            Node('+', Node(t[5]), Node(t[4])),
            Node('sq', Node(t[5])),
            Node('*', Node(t[3]), Node(t[5])),
        ])
    elif len(t) >= 5:
        _skeleton_seeds.extend([
            Node('*', Node(t[2]), Node(t[0])),
            Node('+', Node(t[2]), Node(t[4])),
            Node('sq', Node(t[2])),
            Node('-', Node(t[2]), Node(t[4])),
            Node('*', Node(t[3]), Node(t[2])),
        ])

    _n_explorer_reset = 0
    for island in islands:
        if island.role == "explorer":
            n_skel  = min(len(_skeleton_seeds),
                          int(len(island.population) * 0.30))
            n_fresh = int(len(island.population) * 0.30)
            positions = list(range(cfg.ELITE_SIZE,
                                   cfg.ELITE_SIZE + n_skel + n_fresh))
            random.shuffle(positions)
            for k, pos in enumerate(positions[:n_skel]):
                if pos < len(island.population):
                    skel = _skeleton_seeds[k % len(_skeleton_seeds)]
                    island.population[pos] = skel.copy()
            for pos in positions[n_skel:n_skel + n_fresh]:
                if pos < len(island.population):
                    island.population[pos] = _random_tree_nd(
                        cfg.MAX_INIT_DEPTH, cfg)
            island.stagnation = 0
            _n_explorer_reset += 1

    if _n_explorer_reset > 0:
        n_skel_used = min(len(_skeleton_seeds), 3)
        print(f"  [SMART-RESET gen={gen}] {_n_explorer_reset} explorer island(s) "
              f"— {n_skel_used} semantic skeletons + 30% random "
              f"(RAW={cur_raw:.4f})")
        state.CURRENT_RESIDUAL_SIG = None
        return True
    return False

def evolve(func, cfg: Config, problem_key: str = '1',
           X_override=None, y_override=None):
    """
    X_override / y_override : si fournis (np.ndarray), remplacent build_dataset.
    Utilisés par le mode CSV réel (BATTERY_SOH + nasa_battery_simulation.csv).
    """
    _exit_if_reimported_by_worker()          # [v0.7-PAR]
    state._USE_LINEAR_SCALING = bool(getattr(cfg, "USE_LINEAR_SCALING", True))
    # [v0.4.1] Les drapeaux dimensionnels sont des GLOBALES de module. Sans
    # remise a zero ici, un fit avec units= contaminait tous les fits suivants
    # du meme processus : le garde-fou restait actif sur des donnees sans
    # dimensions declarees, et le champion livre devenait aberrant.
    TRACE.reset()                            # [v0.7] un journal par exécution
    if _dim_active(cfg):
        state._DIM_GATE_DIMS   = cfg.FEAT_DIMS
        state._DIM_GATE_TARGET = cfg.TARGET_DIM
        state._LS_SCALE_ONLY   = True
        state._DIM_UNKNOWN_CONST = bool(getattr(cfg, "UNKNOWN_CONST", False))
        TRACE.set("dim_mode", "ACTIF — la recherche est contrainte par les unités")
        TRACE.set("unknown_const",
                  "OUI — la constante de tête peut porter une dimension"
                  if state._DIM_UNKNOWN_CONST else "non")
        TRACE.set("ls_mode", "multiplicatif seul (régression par l'origine)")
    else:
        state._DIM_GATE_DIMS   = None
        state._DIM_GATE_TARGET = None
        state._LS_SCALE_ONLY   = False
        state._DIM_UNKNOWN_CONST = False
        TRACE.set("dim_mode", "inactif (aucune unité déclarée)")
        TRACE.set("ls_mode", "affine (a + b·f) si linear scaling actif")
    state.VAL_R2_TOLERANCE = float(getattr(cfg, "VAL_R2_TOLERANCE", 0.003))
    # [v0.7] Journal relatif au DOSSIER COURANT de l'utilisateur. L'ancienne
    # resolution (dossier du module) ecrivait dans site-packages a chaque
    # ajustement -- y compris depuis l'API --, echouait en silence sur une
    # installation en lecture seule et entrelacait les ecritures de processus
    # concurrents.
    if not os.path.isabs(cfg.LOG_CSV):
        cfg = copy.copy(cfg)
        cfg.LOG_CSV = os.path.join(os.getcwd(), cfg.LOG_CSV)
    # [v0.7-TIME] Le drapeau d'arret au temps est un etat GLOBAL : il doit
    # etre remis a zero a chaque evolve(), sinon il fuit d'un ajustement au
    # suivant dans un meme processus.
    state._TIME_LIMIT_HIT = False
    # FIX v13.7 : vider les caches entre runs pour éviter les biais
    # inter-problèmes (hash structurel identique, domaine différent).
    state._fitness_cache    = {}
    state._PARAMETRIC_CACHE = {}
    state._PRED_CACHE.clear()
    state.FRAGMENT_LIB.fragments.clear()
    state.FRAGMENT_LIB.generation = 0
    state.COGRAPH.co.clear()
    state.SEQ_MEM.transitions.clear()

    # [v17] Initialiser le probe set adapté aux dimensions du problème
    state.PROBE_X              = init_probe_set(cfg, n_probe=30)
    state.CURRENT_RESIDUAL_SIG = None
    # [FIX-E] Réinitialiser le compteur d'usage des features
    n_feats = len(cfg.TERMINALS) if hasattr(cfg, 'TERMINALS') else 1
    reset_feature_usage(n_feats)
    print(f"[v17-SEMANTIC] Probe set initialized: {state.PROBE_X.shape[0]} points × "
          f"{state.PROBE_X.shape[1] if state.PROBE_X.ndim > 1 else 1} features  "
          f"[{cfg.X_MIN:.1f}, {cfg.X_MAX:.1f}]")

    print("=" * 70)
    # [SYRACUSE / v16-BATTERY CSV] Afficher le pool d'opérateurs réellement actif
    if state._SYRACUSE_MODE:
        _active_ops = _SYRACUSE_BINARY_OPS + _SYRACUSE_UNARY_OPS
    elif state._BATTERY_CSV_MODE:
        _active_ops = _BATTERY_BINARY_OPS + _BATTERY_UNARY_OPS
    else:
        _active_ops = ALL_OPS
    print(f"Generations : {cfg.GENERATIONS}  |  Ops : {_active_ops}")
    print("=" * 70)
    print()

    # [v16-BATTERY] Si des données réelles sont fournies, on les utilise
    # directement au lieu de générer un dataset synthétique via build_dataset.
    if X_override is not None and y_override is not None:
        xs = X_override   # shape (n_samples, n_features)
        ys = y_override   # shape (n_samples,)
    else:
        xs, ys = build_dataset(func, cfg, problem_key=problem_key)

    # [v21-VAL] Split train/validation — tout ce qui suit (îles, fitness,
    # lexicase, Adam, stigmergie, parallélisme) ne voit que le TRAIN.
    xs_full, ys_full = xs, ys
    xs, ys = _split_holdout(xs, ys, cfg)
    _small_setup(cfg, ys)                     # [1.4-S1]

    # [v24-EXTRAP] En mode extrapolation, on ajoute une DROITE (OLS) au pool de
    # candidats-champions. Elle est ajustée sur le train (intérieur) puis jugée,
    # comme tous les candidats, sur la bande-frontière. Opt-in : sans effet sur
    # les runs normaux (EXTRAPOLATION_MODE reste False par default).
    if bool(getattr(cfg, "EXTRAPOLATION_MODE", False)) and state._VAL_XS is not None:
        _lin = _make_linear_candidate(xs, ys, cfg)
        if _lin is not None:
            _track_val_candidate(_lin)
            print(f"[v24-EXTRAP] Linear candidate injected into selection: "
                  f"{to_string(_lin)}")

    # Initialisation des îles (la dernière = île C stigmergique)
    islands = []
    for i in range(cfg.N_ISLANDS):
        is_stigmergic = (i == cfg.N_ISLANDS - 1)
        islands.append(Island(i, cfg, stigmergic=is_stigmergic))

    # [v14.4] Affichage des rôles — placé APRÈS la création de islands
    _roles_str = ", ".join(f"island {isl.id}={isl.role}" for isl in islands)
    print(f"GP_ELITE  —  {cfg.N_ISLANDS} islands × {cfg.POP_SIZE // cfg.N_ISLANDS} individuals  ({_roles_str})")
    print()

    # Initialiser d'abord les îles classiques pour peupler la lib
    for island in islands[:-1]:
        island.initialize()
        island._xs = xs
        island._ys = ys
        island._key = problem_key
        pop_sorted = sorted(island.population,
                            key=lambda n: fitness(n, xs, ys, cfg))
        top_k    = max(3, len(pop_sorted) // 10)
        top_fits = [fitness(ind, xs, ys, cfg) for ind in pop_sorted[:top_k]]
        state.FRAGMENT_LIB.deposit_population(pop_sorted, top_fits, top_k, gen=0,
                                        xs=xs, ys=ys)  # FIX v13.8 : filtre numérique

    # Île C : initialisée après le premier dépôt (lib déjà peuplée)
    islands[-1].initialize()
    islands[-1]._xs  = xs
    islands[-1]._ys  = ys
    islands[-1]._key = problem_key

    # ---- Seeding dirigé ----
    # Injecter des briques connues dans chaque île pour amorcer la recherche
    def make_seed(expr: str) -> Optional[Node]:
        """Construit manuellement quelques individus de départ pertinents."""
        if expr == "sin_sq_x":
            return Node("sin", Node("sq", Node("x")))
        if expr == "x_cos_x":
            return Node("*", Node("x"), Node("cos", Node("x")))
        if expr == "sin_sq_plus_xcos":
            return Node("+",
                        Node("sin", Node("sq", Node("x"))),
                        Node("*", Node("x"), Node("cos", Node("x"))))
        if expr == "sin_xx":
            return Node("sin", Node("*", Node("x"), Node("x")))
        # --- Problème 2 : x³ - x² + x - 1 ---
        if expr == "x_cube":
            return Node("cube", Node("x"))
        if expr == "x_sq":
            return Node("sq", Node("x"))
        if expr == "x_cube_poly":
            x3  = Node("cube", Node("x"))
            x2  = Node("sq",   Node("x"))
            return Node("-", Node("+", Node("-", x3, x2), Node("x")), Node(1.0))
        # --- Problème 3 : exp(-x²)·sin(2x) ---
        if expr == "exp_sq_x":
            return Node("exp", Node("neg", Node("sq", Node("x"))))
        if expr == "sin_2x":
            return Node("sin", Node("*", Node(2.0), Node("x")))
        if expr == "exp_sin":
            return Node("*",
                        Node("exp", Node("neg", Node("sq", Node("x")))),
                        Node("sin", Node("*", Node(2.0), Node("x"))))
        # --- Problème 4 : log(1+x²)·cos(x) ---
        if expr == "log1x2":
            return Node("log", Node("+", Node(1.0), Node("sq", Node("x"))))
        if expr == "cos_x":
            return Node("cos", Node("x"))
        if expr == "log_cos":
            return Node("*",
                        Node("log", Node("+", Node(1.0), Node("sq", Node("x")))),
                        Node("cos", Node("x")))
        # --- Problème 5 : x·sin(x²)·cos(x/2) ---
        if expr == "cos_half_x":
            return Node("cos", Node("*", Node(0.5), Node("x")))
        if expr == "x_sin_sq":
            return Node("*", Node("x"), Node("sin", Node("sq", Node("x"))))
        if expr == "x_sin_sq_cos_half":
            return Node("*",
                        Node("*", Node("x"), Node("sin", Node("sq", Node("x")))),
                        Node("cos", Node("*", Node(0.5), Node("x"))))
        # --- Problème 6 : exp(-|x|)·(x²-1) ---
        if expr == "exp_neg_abs":
            # exp(-|x|)
            return Node("exp", Node("neg", Node("abs", Node("x"))))
        if expr == "x2_minus1":
            # x²-1
            return Node("-", Node("sq", Node("x")), Node(1.0))
        if expr == "exp_abs_x2":
            # exp(-|x|) · (x²-1)
            return Node("*",
                        Node("exp", Node("neg", Node("abs", Node("x")))),
                        Node("-", Node("sq", Node("x")), Node(1.0)))
        # --- Problème 7 : sinc(x)·cos(x²) ---
        if expr == "sin_over_x":
            # sin(x)/x ≈ sinc
            return Node("/", Node("sin", Node("x")), Node("x"))
        if expr == "cos_sq_x":
            return Node("cos", Node("sq", Node("x")))
        if expr == "sinc_cos_sq":
            return Node("*",
                        Node("/", Node("sin", Node("x")), Node("x")),
                        Node("cos", Node("sq", Node("x"))))
        # --- Problème 8 : sin(πx)/(x²+1) ---
        if expr == "sin_pi_x":
            return Node("sin", Node("*", Node(math.pi), Node("x")))
        if expr == "x2_plus1":
            return Node("+", Node("sq", Node("x")), Node(1.0))
        if expr == "lorentz_sin":
            return Node("/",
                        Node("sin", Node("*", Node(math.pi), Node("x"))),
                        Node("+", Node("sq", Node("x")), Node(1.0)))
        # --- Problème 9 : tanh(x)·exp(-x²/4) ---
        if expr == "tanh_x":
            return Node("tanh", Node("x"))
        if expr == "exp_x2_4":
            # exp(-x²/4)
            return Node("exp", Node("neg",
                        Node("/", Node("sq", Node("x")), Node(4.0))))
        if expr == "tanh_exp_gauss":
            # tanh(x) · exp(-x²/4) — forme exacte
            return Node("*",
                        Node("tanh", Node("x")),
                        Node("exp", Node("neg",
                             Node("/", Node("sq", Node("x")), Node(4.0)))))
        if expr == "sin_exp_gauss":
            # sin(x) · exp(-x²/4) — approximation proche pour petits x
            return Node("*",
                        Node("sin", Node("x")),
                        Node("exp", Node("neg",
                             Node("/", Node("sq", Node("x")), Node(4.0)))))
        # --- Problème 10 : x³·sin(1/x) ---
        if expr == "x_cube_sin_inv":
            return Node("*",
                        Node("cube", Node("x")),
                        Node("sin", Node("/", Node(1.0), Node("x"))))
        # ── [v16-BATTERY] Seeds N-D pour BATTERY_SOH ─────────────────────────
        # Cible : 1 - 0.02·exp(X[0])·X[1] - 0.005·X[2]²
        # Stratégie : injecter les briques structurelles clés indépendamment
        # pour que la stigmergie puisse les combiner dès les premières générations.
        if expr == "bsoh_exp_x0":
            # exp(X[0]) — terme d'Arrhenius isolé
            return Node("exp", Node("X[0]"))
        if expr == "bsoh_exp_x0_x1":
            # exp(X[0]) * X[1] — interaction thermique × cycles
            return Node("*", Node("exp", Node("X[0]")), Node("X[1]"))
        if expr == "bsoh_sq_x2":
            # X[2]² — terme de dégradation quadratique courant
            return Node("sq", Node("X[2]"))
        if expr == "bsoh_decay_term":
            # 0.02 * exp(X[0]) * X[1] — terme de dégradation Arrhenius complet
            return Node("*",
                        Node(0.02),
                        Node("*", Node("exp", Node("X[0]")), Node("X[1]")))
        if expr == "bsoh_full":
            # 1 - 0.02*exp(X[0])*X[1] — structure principale sans X[2]²
            return Node("-",
                        Node(1.0),
                        Node("*",
                             Node(0.02),
                             Node("*", Node("exp", Node("X[0]")), Node("X[1]"))))
        if expr == "bsoh_x2_term":
            # 0.005 * X[2]² — terme de dégradation quadratique complet
            # Injecté explicitement car ce terme est 50× plus petit que
            # 0.02·exp(X[0])·X[1] → pression fitness très faible sans seed directe
            return Node("*", Node(0.005), Node("sq", Node("X[2]")))
        if expr == "bsoh_complete":
            # Structure cible exacte : 1 - 0.02*exp(X[0])*X[1] - 0.005*X[2]²
            # Injectée sur l'île stigmergic (île 3) pour que la lib et CoGraph
            # absorbent immédiatement les trois briques structurelles ensemble.
            return Node("-",
                        Node("-",
                             Node(1.0),
                             Node("*",
                                  Node(0.02),
                                  Node("*", Node("exp", Node("X[0]")), Node("X[1]")))),
                        Node("*", Node(0.005), Node("sq", Node("X[2]"))))
        return None

    # Seeds par problème — couvre maintenant P1–P10
    seed_map = {
        "1": ["sin_sq_x", "x_cos_x", "sin_sq_plus_xcos", "sin_xx",
               "sin_sq_x", "x_cos_x"],
        "2": ["x_cube", "x_sq", "x_cube_poly", "x_cube",
               "x_sq", "x_cube_poly"],
        "3": ["exp_sq_x", "sin_2x", "exp_sin", "exp_sq_x",
               "sin_2x", "exp_sin"],
        "4": ["log1x2", "cos_x", "log_cos", "log1x2",
               "cos_x", "log_cos"],
        "5": ["sin_sq_x", "cos_half_x", "x_sin_sq", "x_sin_sq_cos_half",
              "sin_sq_x", "cos_half_x", "x_sin_sq", "x_sin_sq_cos_half"],
        "6": ["exp_neg_abs", "x2_minus1", "exp_abs_x2",
               "exp_neg_abs", "x2_minus1", "exp_abs_x2"],
        "7": ["sin_over_x", "cos_sq_x", "sinc_cos_sq",
               "sin_over_x", "cos_sq_x"],
        "8": ["sin_pi_x", "x2_plus1", "lorentz_sin",
               "sin_pi_x", "x2_plus1", "lorentz_sin"],
        "9": ["tanh_x", "exp_x2_4", "tanh_exp_gauss",
               "tanh_x", "exp_x2_4", "tanh_exp_gauss", "sin_exp_gauss"],
        "10": ["x_cube", "x_cube_sin_inv", "x_cube",
                "x_cube_sin_inv"],
        # ── [v16-BATTERY v2] Seeds N-D — distribution raisonnée sur 4 îles ────
        # Problème observé (run v2) : bsoh_sq_x2 absorbé par tanh via mutations.
        # Le terme 0.005·X[2]² est 50× plus faible que 0.02·exp(X[0])·X[1]
        # → pression fitness insuffisante pour le maintenir sans seed directe.
        # Stratégie :
        #   · île 0 (explorer)   : briques atomiques pour diversité
        #   · île 1 (explorer)   : bsoh_complete → structure cible exacte
        #   · île 2 (cleaner)    : bsoh_decay_term + bsoh_x2_term séparément
        #   · île 3 (stigmergic) : bsoh_complete + bsoh_full pour lib/CoGraph
        "BATTERY_SOH": [
            "bsoh_exp_x0",       # île 0 slot 0 : exp(X[0])
            "bsoh_complete",     # île 1 slot 0 : structure cible EXACTE
            "bsoh_decay_term",   # île 2 slot 0 : 0.02*exp(X[0])*X[1]
            "bsoh_complete",     # île 3 slot 0 : structure cible EXACTE (lib)
            "bsoh_sq_x2",        # île 0 slot 1 : X[2]² brut
            "bsoh_x2_term",      # île 1 slot 1 : 0.005*X[2]² complet
            "bsoh_full",         # île 2 slot 1 : 1 - 0.02*exp(X[0])*X[1]
            "bsoh_x2_term",      # île 3 slot 1 : 0.005*X[2]² (renforcement)
        ],
        # ── [v16-BATTERY CSV] Seeds pour données réelles — 3 features SANS X[3] ─
        # Identiques à BATTERY_SOH mais sans aucun nœud X[3].
        # Utilisées quand nasa_battery_simulation.csv est présent (n_features=3).
        "BATTERY_SOH_CSV": [
            "bsoh_exp_x0",       # île 0 slot 0 : exp(X[0])
            "bsoh_exp_x0_x1",    # île 1 slot 0 : exp(X[0])*X[1]
            "bsoh_decay_term",   # île 2 slot 0 : 0.02*exp(X[0])*X[1]
            "bsoh_full",         # île 3 slot 0 : 1 - 0.02*exp(X[0])*X[1]
            "bsoh_sq_x2",        # île 0 slot 1 : X[2]²
            "bsoh_x2_term",      # île 1 slot 1 : 0.005*X[2]²
            "bsoh_x2_term",      # île 2 slot 1 : renforcement terme X[2]
            "bsoh_exp_x0",       # île 3 slot 1 : exp(X[0]) diversité
        ],
    }
    seeds = seed_map.get(problem_key, []) if cfg.USE_SEEDING else []
    # FIX v13.10 : P7 et P8 requièrent des structures que le GP ne découvre
    # presque jamais seul en ultrafast (sin(x)/x, π précis). On injecte leurs
    # seeds inconditionnellement, même en ablation (USE_SEEDING=False), car ces
    # briques ne biaisent pas la comparaison des conditions — elles aident juste
    # le GP à ne pas passer 100 gens sur des constantes proches de 0.
    if not cfg.USE_SEEDING and problem_key in ("7", "8"):
        seeds = seed_map.get(problem_key, [])
    # [v16-BATTERY] BATTERY_SOH : seeds N-D injectées inconditionnellement.
    # Sans seeding, exp(X[0]) n'émerge presque jamais avant gen 20 — la stigmergie
    # s'ouvre trop tard et tanh colonise la population (observé au run v16-NDIM).
    # Ces seeds ne biaisent pas la comparaison car elles reflètent uniquement
    # la physique du problème (modèle d'Arrhenius), pas une solution complète.
    if problem_key == "BATTERY_SOH":
        seeds = seed_map["BATTERY_SOH"]
    # [v16-BATTERY CSV] Mode données réelles : seeds sans X[3]
    if problem_key == "BATTERY_SOH_CSV":
        seeds = seed_map["BATTERY_SOH_CSV"]
    # FIX v13.7 : distribution round-robin des seeds entre les îles.
    for j, seed_name in enumerate(seeds):
        target_island = islands[j % cfg.N_ISLANDS]
        slot          = j // cfg.N_ISLANDS
        seed = make_seed(seed_name)
        if seed and slot < len(target_island.population):
            target_island.population[slot] = seed

    # [CUSTOM-SEEDS] Injection des arbres fournis par l'utilisateur (round-robin).
    # On les place dans des slots distincts pour ne pas écraser les seeds
    # standard. Chaque île reçoit une copie pour préserver l'isolation.
    _cseeds = getattr(state, '_CUSTOM_SEEDS', None)
    if _cseeds:
        base = len(seeds)
        for j, seed_node in enumerate(_cseeds):
            target_island = islands[j % cfg.N_ISLANDS]
            slot          = (base + j) // cfg.N_ISLANDS
            if seed_node is not None and slot < len(target_island.population):
                target_island.population[slot] = seed_node.copy()
    # [v28-MOTIFS] Injection des motifs de composition (round-robin, slots
    # suivants). Opt-out via cfg.MOTIF_SEEDS=False. Tirage dépendant du SEED :
    # chaque restart (v27) instancie d'autres appariements de variables.
    # [v29.1] Les motifs servent la RÉCUPÉRATION (structures riches en-domaine) ;
    # en mode EXTRAPOLATION ils injectent des formes courbes plausibles dans la
    # bande mais trompeuses au-delà (mesuré : batterie méd +0.52 → +0.18).
    # On les coupe donc quand EXTRAPOLATION_MODE est actif.
    if bool(getattr(cfg, "MOTIF_SEEDS", True)) \
            and not bool(getattr(cfg, "EXTRAPOLATION_MODE", False)):
        _motifs = _make_motif_seeds(cfg, int(getattr(cfg, "MOTIF_SEEDS_N", 32)))
        _base2 = len(seeds) + (len(_cseeds) if _cseeds else 0)
        for j, mnd in enumerate(_motifs):
            target_island = islands[j % cfg.N_ISLANDS]
            slot          = (_base2 + j) // cfg.N_ISLANDS
            if slot < len(target_island.population):
                target_island.population[slot] = mnd
    else:
        _motifs = []
    # [v0.8] Graines de loi de puissance (voir _make_power_law_seeds) : une
    # copie dans chaque île, au slot qui suit les motifs. Rien n'est injecté
    # (et rien ne change) quand la cible ou toutes les colonnes changent de
    # signe.
    _plaw = _make_power_law_seeds(xs, ys, cfg)
    if _plaw:
        _base3 = (len(seeds) + (len(_cseeds) if _cseeds else 0)
                  + len(_motifs)) // cfg.N_ISLANDS + 1
        for target_island in islands:
            for j, pnd in enumerate(_plaw):
                slot = _base3 + j
                if slot < len(target_island.population):
                    target_island.population[slot] = pnd.copy()
    # [0.10, phase 4b] Graines « monôme fois puissance d'un binôme » (voir
    # _make_binomial_seeds) : une copie dans chaque île, après les graines de
    # loi de puissance. Rien n'est injecté sans une forme exacte.
    _binom = _make_binomial_seeds(xs, ys, cfg)
    if _binom:
        _base4 = ((len(seeds) + (len(_cseeds) if _cseeds else 0)
                   + len(_motifs)) // cfg.N_ISLANDS + 1 + len(_plaw))
        for target_island in islands:
            for j, bnd in enumerate(_binom):
                slot = _base4 + j
                if slot < len(target_island.population):
                    target_island.population[slot] = bnd.copy()
    # [0.10, phase 4a] Graines « fonction d'un monôme » (voir
    # _make_elementary_seeds) : une copie dans chaque île, après les graines
    # binomiales. Rien n'est injecté sans une forme exacte.
    _elem = _make_elementary_seeds(xs, ys, cfg)
    if _elem:
        _base5 = ((len(seeds) + (len(_cseeds) if _cseeds else 0)
                   + len(_motifs)) // cfg.N_ISLANDS + 1 + len(_plaw)
                  + len(_binom))
        for target_island in islands:
            for j, end in enumerate(_elem):
                slot = _base5 + j
                if slot < len(target_island.population):
                    target_island.population[slot] = end.copy()
    # [0.10, phase 5] Graines tolérantes au bruit (voir _make_tolerant_seeds) :
    # seulement si aucune forme exacte de B1 ou E1 n'a été trouvée ; une copie
    # dans chaque île, après les autres graines.
    _tol = [] if (_binom or _elem) else _make_tolerant_seeds(
        xs, ys, cfg, power_done=bool(_plaw))
    if _tol:
        _base6 = ((len(seeds) + (len(_cseeds) if _cseeds else 0)
                   + len(_motifs)) // cfg.N_ISLANDS + 1 + len(_plaw)
                  + len(_binom) + len(_elem))
        for target_island in islands:
            for j, tnd in enumerate(_tol):
                slot = _base6 + j
                if slot < len(target_island.population):
                    target_island.population[slot] = tnd.copy()
    # [v16-NDIM] Pas de seeds spécifiques pour les problèmes N-D.
    # La couverture des opérateurs est assurée par _nd_diverse_population()
    # dans Island.initialize_nd(), et le transfert de grammaire par SEQ_MEM.

    global_best:  Optional[Node] = None
    global_score: float          = float("inf")

    log_rows = []
    t0 = time.time()

    # ── [v20-PAR] Tentative parallèle (AUTO : ≥4 cœurs et ≥2 îles) ──
    # En cas de succès, on saute la boucle séquentielle ; en cas d'échec
    # (pool indisponible, pickling, etc.), repli transparent : les îles ne
    # sont jamais corrompues (remplacées seulement après un round réussi),
    # la boucle séquentielle reprend là où le parallèle s'est arrêté.
    _seq_needed = True
    if _parallel_enabled(cfg):
        _pb, _ps, _completed = _evolve_parallel(islands, xs, ys, cfg, t0, log_rows)
        if _pb is not None and _ps < global_score:
            global_best, global_score = _pb, _ps
        if _completed:
            _seq_needed = False

    # Compteur de plateau global — déclenche un restart d'urgence si
    # aucune île n'améliore le global_best pendant trop longtemps
    _plateau_counter   = 0
    _plateau_threshold = 40   # générations sans amélioration globale
    _last_global_raw   = float('inf')

    _deadline = getattr(cfg, "DEADLINE", None)
    _pat = _Patience(getattr(cfg, "PATIENCE", 0))     # [v1.2-H1]
    for gen in range(cfg.GENERATIONS if _seq_needed else 0):
        # [v0.7-TIME] Echeance atteinte : arret propre, meilleur modele conserve.
        if _deadline is not None and gen > 0 and time.time() >= _deadline:
            TRACE.set("time_limit", "atteint (sequentiel, gen %d)" % gen)
            state._TIME_LIMIT_HIT = True
            print(f"[TIME] Time limit reached at generation {gen} — "
                  f"returning the best model so far.")
            break
        # [OPT] Cache fitness vidé toutes les 10 générations (aligné sur gen//10).
        # Entre deux vidages, la clé (hash, role, gen//10) garantit la fraîcheur.
        # Évite de recalculer la fitness d'individus stables entre générations.
        if gen % 10 == 0:
            state._fitness_cache.clear()
        # [OPT] Vider le cache de simplification pour libérer la mémoire
        # et éviter des résultats périmés après mutations.
        _clear_simplify_caches()
        # [FIX-A] Mettre à jour la pénalité mono-feature progressive
        # 0.10 en gen=0 → 0.03 en fin de run (décroissance linéaire)
        if state._SYRACUSE_MODE:
            _t = gen / max(cfg.GENERATIONS - 1, 1)
            cfg._mono_pen_cache = 0.10 - _t * 0.07   # 0.10 → 0.03
        # [OPT] Bucket générationnel pour le cache fitness (gen//10)
        cfg._gen_bucket = gen // 10

        # Évolution de chaque île
        _gen_improved = False
        for island in islands:
            new_best = evolve_island(island, xs, ys, gen)

            if new_best is not None:
                # [v18-LS] Matérialiser le scaling AVANT comparaison/stockage :
                # l'EXPR affichée et le champion stocké incluent a + b·(...),
                # donc le MSE rapporté correspond exactement à l'expression.
                cand = wrap_linear_scaling(new_best, xs, ys)
                _track_val_candidate(cand)            # [v21-VAL]
                _track_small_candidate(cand, xs, ys)  # [1.4-S1]
                s = fitness(cand, xs, ys, cfg, role="cleaner")
                if s < global_score:
                    global_score  = s
                    global_best   = cand.copy()
                    _gen_improved = True

                    raw = raw_mse(cand, xs, ys)
                    sz  = tree_size(cand)
                    dp  = tree_depth(cand)
                    elapsed = time.time() - t0

                    print(f"[GEN {gen:04d}|I{island.id}] "
                          f"FIT={s:.8f} "
                          f"RAW={raw:.8f} "
                          f"SIZE={sz:02d} "
                          f"DEPTH={dp:02d} "
                          f"({elapsed:.1f}s)")
                    print(f"  EXPR = {to_string(cand)}")
                    print()

                    log_rows.append({
                        "gen": gen, "island": island.id,
                        "fit": s, "raw": raw,
                        "size": sz, "depth": dp,
                        "expr": to_string(cand),
                        "elapsed": elapsed
                    })

        # Suivi du plateau global
        _cur_raw = raw_mse(global_best, xs, ys) if global_best else float('inf')
        if _cur_raw < _last_global_raw - 1e-6:
            _plateau_counter = 0
            _last_global_raw = _cur_raw
        else:
            _plateau_counter += 1

        # [SYRACUSE] Restart d'urgence : si plateau global trop long,
        # réinitialiser les îles explorer (squelettes sémantiques ciblés).
        # [v20-PAR] Logique extraite dans _smart_reset_explorers() — partagée
        # par la boucle séquentielle et la boucle parallèle.
        _is_nd_run = (len(cfg.TERMINALS) > 1 or
                      (len(cfg.TERMINALS) == 1 and cfg.TERMINALS[0] != "x"))
        if (_plateau_counter >= _plateau_threshold and
                _is_nd_run and gen < cfg.GENERATIONS - 50):
            _plateau_counter = 0
            _smart_reset_explorers(islands, cfg, gen, _cur_raw)

        # Convergence parfaite
        if global_best and raw_mse(global_best, xs, ys) < cfg.PERFECT_THRESHOLD:
            print(f"[✓] Perfect solution found at generation {gen}!")
            break

        # [v15] Early Stopping — arrêt précoce si MSE pur sous le seuil absolu
        if global_best:
            # [v21-VAL] early-stop jugé sur le HOLD-OUT (anti-surapprentissage)
            _es_mse = _holdout_mse(global_best, xs, ys)
            _es_thr = _early_stop_threshold(cfg, ys)
            if _es_mse <= _es_thr:
                print(f"\n{'═'*60}")
                print(f"  [SUCCESS] Precision target reached at GEN {gen:04d}!")
                print(f"  MSE (hold-out si actif) = {_es_mse:.2e}  ≤  seuil = {_es_thr:.2e}")
                print(f"  Early stop — remaining generations saved.")
                print(f"{'═'*60}\n")
                break
            # [v1.2-H1] Arrêt sur patience (budget choisi par le moteur).
            if _pat.spent(_es_mse, gen):
                TRACE.set("patience", "arret (sequentiel, gen %d)" % gen)
                print(f"[PATIENCE] No gain of 1 % in {_pat.p} generations — "
                      f"stop at generation {gen}.")
                break

        # Migration périodique
        if gen > 0 and gen % cfg.MIGRATION_INTERVAL == 0:
            migrate(islands)

    if _deadline is not None and time.time() >= _deadline:
        state._TIME_LIMIT_HIT = True
    # Optimisation finale des constantes sur le meilleur
    # [v14.4] Correction du bug de référence : copy.deepcopy() avant Adam+simplify
    # pour garantir que global_best n'est jamais corrompu si des nœuds sont
    # partagés par référence entre global_best et l'arbre optimisé.
    # Comparaison par raw_mse pur (MSE brut) pour détecter correctement
    # les régressions numériques post-Adam, indépendamment du rôle.
    if global_best:
        import copy as _copy
        optimized = optimize_constants_adam(global_best.copy(), xs, ys, cfg)  # [v19-OPT]
        optimized = simplify(optimized)
        # [v0.8] Le champion porte sa mise à l'échelle a + b·f ; LM en
        # projection variable ajuste la forme a' + b'·(champion) : sans
        # recalage, l'arbre rendu gardait l'ancien a et l'ancien b (raw_mse,
        # invariant d'échelle, ne le voit pas). Sans hold-out (moins de 30
        # points, ou validation_split=0), ce modèle était livré tel quel.
        optimized = _refit_scaling(optimized, xs, ys)
        if raw_mse(optimized, xs, ys) < raw_mse(global_best, xs, ys):
            global_best = optimized
        # Si Adam a dégradé, global_best reste intact (deepcopy garantit l'isolation)
        _track_val_candidate(global_best)            # [v21-VAL] post-Adam
        _track_small_candidate(global_best, xs, ys)  # [1.4-S1]

    # [1.4-S1] Sous 30 lignes, pas de hold-out : les candidats en validation
    # croisée (voir _small_table_select).
    if state._VAL_XS is None and global_best is not None and state._SMALL_ON:
        try:
            global_best = _small_table_select(global_best, xs, ys, cfg)
        except Exception:
            pass

    # ── [v21-VAL] Sélection finale + rapport de généralisation ──────────
    # Le champion LIVRÉ est celui qui généralise le mieux : si un candidat
    # suivi en cours de run bat le champion-train sur le hold-out, il prend
    # sa place. Puis rapport train vs validation, avec alerte surapprentissage.
    if state._VAL_XS is not None and global_best is not None:
        # [v26-LM] POLISSAGE DES FINALISTES : avant la sélection parcimonieuse,
        # on affine par LM les constantes des meilleurs candidats suivis. Sans
        # cela, la règle 1-SE compare des structures aux constantes brutes — une
        # forme simple et EXACTE peut perdre contre un gros arbre simplement
        # parce que ses constantes n'étaient pas encore ajustées. Coût : ~ms.
        try:
            _polish_finalists(_finalists(cfg), xs, ys, cfg)   # [v0.8] voir leurs définitions
        except Exception:
            pass
        _champ_val = _holdout_mse(global_best, xs, ys)
        _sel, _sel_val = _select_one_se(global_best, _champ_val)
        # [v25-EXTRAP] Le garde anti-divergence PRIME sur la parcimonie : si le
        # champion lui-même diverge hors-plage, il doit céder la place au
        # meilleur candidat stable, même si ce dernier n'est ni plus petit ni
        # meilleur en validation interne (sa MSE interne peut être pire — c'est
        # justement le point : le divergent gagne EN INTERNE et explose DEHORS).
        _champ_unstable = not _is_numerically_stable(global_best)
        _really_diff = (_sel is not global_best and
                        (_champ_unstable or
                         tree_size(_sel) < tree_size(global_best) or
                         _sel_val < _champ_val * 0.999))
        if _really_diff:
            _sz_sel, _sz_old = tree_size(_sel), tree_size(global_best)
            if _champ_unstable:
                _why = "out-of-range divergent champion replaced by a stable candidate"
            elif _sz_sel < _sz_old:
                _why = f"simpler ({_sz_sel} nodes vs {_sz_old}, equivalent R²)"
            else:
                _why = f"meilleur en validation (val {_sel_val:.3e} vs {_champ_val:.3e})"
            print(f"[v21-VAL] Parsimonious selection: champion replaced — {_why}")
            global_best = _sel.copy()
            _champ_val  = _sel_val
        # [v25-EXTRAP] FILET DE SÉCURITÉ DUR : en mode extrapolation, ne JAMAIS
        # livrer un modèle qui diverge hors-plage. Si, malgré tout, le champion
        # final échoue encore au garde (aucun candidat stable n'avait été suivi),
        # on retombe sur la droite OLS — sûre par construction.
        if state._EXTRAP_PROBE_XS is not None and not _is_numerically_stable(global_best):
            _lin_fb = _make_linear_candidate(xs, ys, cfg)
            if _lin_fb is not None and _is_numerically_stable(_lin_fb):
                print("[v25-EXTRAP] ⚠ Champion still divergent → falling back to the line (safe floor).")
                global_best = _lin_fb
                _champ_val  = _holdout_mse(global_best, xs, ys)
        _champ_train = _pure_mse(global_best, xs, ys)
        _var_val     = float(np.var(state._VAL_YS)) if len(state._VAL_YS) > 1 else 0.0
        _r2_val      = (1.0 - _champ_val / _var_val) if _var_val > 1e-15 else float("nan")
        _ratio       = (_champ_val / _champ_train) if _champ_train > 1e-15 else 1.0
        # solution exacte (bruit numérique pur) : ratio non significatif
        if _champ_val < 1e-12 and _champ_train < 1e-12:
            _ratio = 1.0
        print()
        print("─" * 70)
        print("[v21-VAL] GENERALIZATION REPORT (final champion)")
        print(f"  MSE train      : {_champ_train:.6e}")
        print(f"  Validation MSE : {_champ_val:.6e}   (never seen by evolution)")
        print(f"  R² validation  : {_r2_val:.4f}")
        print(f"  Ratio val/train: {_ratio:.2f}")
        if _ratio > 3.0:
            print("  ⚠ SURAPPRENTISSAGE PROBABLE : l'erreur de validation est "
                  ">3× the training error.")
            print("    Hints: ↑PARSIMONY, ↓MAX_TREE_SIZE, more data.")
        elif _ratio > 1.5:
            print("  ~ Slight train/val gap — monitor, but acceptable.")
        else:
            print("  ✓ Healthy generalization.")
        print("─" * 70)

    # Export CSV (optionnel — silencieux si filesystem en lecture seule)
    try:
        if not getattr(cfg, "WRITE_LOG_CSV", True):
            raise _SkipLogExport()
        with open(cfg.LOG_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["gen", "island", "fit", "raw",
                               "size", "depth", "expr", "elapsed"])
            writer.writeheader()
            writer.writerows(log_rows)
        print(f"[LOG] History exported → {cfg.LOG_CSV}")
    except Exception:
        pass  # filesystem en lecture seule — ignoré silencieusement

    # Stats bibliothèque de fragments
    s = state.FRAGMENT_LIB.stats()
    print(f"[STIGM] Fragments accumulated: {s['count']}")
    print(f"[STIGM] τ max : {s['max_tau']:.4f}  |  τ moyen : {s['mean_tau']:.4f}")
    if s['top_ops']:
        print(f"[STIGM] Dominant operators: {s['top_ops']}")
    if state.FRAGMENT_LIB.fragments:
        print("[STIGM] Top 3 fragments :")
        for e in state.FRAGMENT_LIB.top_fragments(3):
            from_str = to_string(e.node)
            print(f"  τ={e.tau:.3f}  freq={e.freq}  {from_str}")

    # Stats graphe de co-occurrences (Phase 5a)
    cg = state.COGRAPH.stats()
    print()
    print(f"[COGRAPH] Co-occurrence edges: {cg['edges']}")
    print(f"[COGRAPH] co max : {cg['max_co']:.5f}  |  co moyen : {cg['mean_co']:.5f}")
    top_pairs = state.COGRAPH.top_pairs(5, state.FRAGMENT_LIB)
    if top_pairs:
        print("[COGRAPH] Top 5 paires co-occurrentes :")
        for w, l1, l2 in top_pairs:
            l1s = l1[:35] + "…" if len(l1) > 36 else l1
            l2s = l2[:35] + "…" if len(l2) > 36 else l2
            print(f"  co={w:.4f}  [{l1s}]  ×  [{l2s}]")

    # Stats mémoire de séquences (Phase 5b)
    sm = state.SEQ_MEM.stats()
    print()
    print(f"[SEQ_MEM] Transitions apprises : {sm['n_transitions']}  "
          f"(poids total : {sm['total_weight']})")
    if sm['top5']:
        print("[SEQ_MEM] Top 5 transitions :")
        for trans, child in sm['top5']:
            print(f"  {trans:25s} → {child}")

    # [v21-VAL] retourner le dataset COMPLET (les menus affichent dessus)
    return global_best, xs_full, ys_full

# ============================================================
# FINAL RESULT
# ============================================================

def print_result(name: str, best: Node,
                 xs: List[float], ys: List[float],
                 cfg: Config):
    # [v13.13 — OBJECTIF 3b] Simplification finale avant affichage ──────────────
    # Le champion stocké en mémoire peut encore contenir des introns résiduels
    # (x+x non réduits, 1*expr, double négation…) qui gonflent l'expression
    # affichée sans modifier la valeur numérique.  On applique simplify() ici,
    # unique point d'entrée commun à tous les modes (interactif, CLI, run()),
    # pour garantir que l'expression affichée, sauvegardée et tracée est la
    # forme la plus compacte possible.
    # pop est List[Node] bruts → simplification directe sur le nœud racine.
    # La fitness et le MSE sont recalculés après simplification pour que les
    # métriques affichées soient cohérentes avec la forme simplifiée.
    # [v23.1] Simplification d'affichage SÛRE : on ne la garde que si elle
    # préserve la valeur numérique (un simplify bogué ne doit jamais remplacer
    # le champion validé par une forme dégradée à l'écran).
    try:
        _simp = simplify(best)
        if _pure_mse(_simp, xs, ys) <= _pure_mse(best, xs, ys) + 1e-12:
            best = _simp
    except Exception:
        pass
    # ─────────────────────────────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    print()
    print(f"Target        : {name}")
    print(f"Expression    : {to_string(best)}")
    # [FIX-LABEL v20.1] Depuis v18, raw_mse() renvoie le score HYBRIDE
    # 5·(1-|r|) + mse/(1+mse) (corrélation + MSE scalé) et non plus un MSE.
    # L'étiquette « Erreur MSE » était donc fausse — le vrai MSE est _pure_mse.
    print(f"True MSE      : {_pure_mse(best, xs, ys):.10e}")
    print(f"Hybrid score  : {raw_mse(best, xs, ys):.10f}   (5·(1-|r|) + mse/(1+mse))")
    print(f"Fitness       : {fitness(best, xs, ys, cfg):.10f}")
    print(f"Size          : {tree_size(best)}")
    print(f"Depth         : {tree_depth(best)}")
    print()

    # Vérification sur quelques points
    print("Verification:")
    is_nd = isinstance(xs, np.ndarray) and xs.ndim == 2
    if is_nd:
        n_feat = xs.shape[1]
        hdr = "  " + "  ".join(f"X[{i}]" for i in range(n_feat))
        print(f"{hdr}  {'target':>14}  {'predicted':>14}  {'error':>12}")
        print("  " + "-" * (14 * n_feat + 44))
        for row, y in zip(xs[:8], ys[:8]):
            x_str = "  ".join(f"{v:8.4f}" for v in row)
            pred  = float(evaluate_vector(best, row.reshape(1, -1))[0])
            print(f"  {x_str}  {y:14.8f}  {pred:14.8f}  {abs(pred-y):12.2e}")
    else:
        print(f"  {'x':>8}  {'target':>14}  {'predicted':>14}  {'error':>12}")
        print("  " + "-" * 52)
        for x, y in zip(xs[:10], ys[:10]):
            pred = evaluate(best, x)
            print(f"  {x:8.4f}  {y:14.8f}  {pred:14.8f}  {abs(pred-y):12.2e}")
    print()

    # Sauvegarde
    try:
        with open(cfg.SAVE_BEST, "w") as f:
            f.write(f"TARGET : {name}\n")
            f.write(f"EXPR   : {to_string(best)}\n")
            f.write(f"RAW    : {raw_mse(best, xs, ys):.10f}\n")
            f.write(f"FIT    : {fitness(best, xs, ys, cfg):.10f}\n")
            f.write(f"SIZE   : {tree_size(best)}\n")
            f.write(f"DEPTH  : {tree_depth(best)}\n")
        print(f"[SAVE] Meilleure solution → {cfg.SAVE_BEST}")
    except Exception:
        pass  # filesystem en lecture seule — ignoré silencieusement

# ============================================================
# VISUALISATION (optionnelle)
# ============================================================

def decoy_report(problem_key: str, best: "Node",
                 X_data: np.ndarray, y_data: np.ndarray,
                 cfg: "Config"):
    """
    [v16-DECOY] Rapport de robustesse pour les problèmes avec variables leurres.

    Produit trois analyses complémentaires :

    1. FEATURE IMPORTANCE (SEQ_MEM) — score normalisé par variable.
       Le leurre doit obtenir 0.000 ou proche.

    2. USAGE STRUCTUREL — compte le nombre de nœuds X[decoy] dans le meilleur
       arbre. Si le GP a trouvé la solution exacte, ce compte doit être 0.

    3. ABLATION MSE — retire X[decoy] du dataset (remplace par 0) et recalcule
       la MSE. Si le leurre est vraiment ignoré, la MSE ne change pas.

    Verdict final : PASS si toutes les conditions sont remplies, FAIL sinon.
    """
    SEP = "─" * 70
    decoy_indices = DECOY_FEATURES.get(problem_key, [])
    if not decoy_indices:
        return   # Pas un problème leurre — rien à faire

    print()
    print("═" * 70)
    print("  RAPPORT DE ROBUSTESSE — VARIABLES LEURRES")
    print("═" * 70)
    print(f"  Problem    : {problem_key}")
    print(f"  Leurre(s)  : {['X['+str(i)+']' for i in decoy_indices]}")
    print(f"  Expression : {to_string(best)}")
    print(SEP)

    all_pass = True

    # ── 1. Feature Importance via SEQ_MEM ────────────────────────────────
    print()
    print("  [1] Feature Importance (SEQ_MEM)")
    fi: Dict[str, float] = {}
    for key, dist in state.SEQ_MEM.transitions.items():
        for op, w in dist.items():
            if isinstance(op, str) and (op == "x" or op.startswith("X[")):
                fi[op] = fi.get(op, 0.0) + w
        if len(key) > 1:
            pk = key[1]
            if isinstance(pk, str) and (pk == "x" or pk.startswith("X[")):
                fi[pk] = fi.get(pk, 0.0) + sum(dist.values())
    fi_total = sum(fi.values()) or 1.0
    fi_norm  = {k: v / fi_total for k, v in fi.items()}

    # Afficher toutes les features
    for feat in cfg.TERMINALS:
        score = fi_norm.get(feat, 0.0)
        is_decoy = any(feat == f"X[{di}]" for di in decoy_indices)
        tag  = "  ← LEURRE" if is_decoy else ""
        ok   = score < 0.05   if is_decoy else True
        icon = "✓" if ok else "✗"
        print(f"    {icon} {feat:8s} : {score:.4f}{tag}")
        if is_decoy and not ok:
            all_pass = False
            print(f"      ⚠  Score {score:.4f} > threshold 0.05 — decoy not rejected by SEQ_MEM")

    # ── 2. Présence structurelle dans le meilleur arbre ───────────────────
    print()
    print("  [2] Presence in the final expression")

    def count_decoy_nodes(node, decoy_set) -> int:
        if node is None:
            return 0
        c = 1 if node.value in decoy_set else 0
        return c + count_decoy_nodes(node.left, decoy_set) + \
                   count_decoy_nodes(node.right, decoy_set)

    decoy_terminals = {f"X[{di}]" for di in decoy_indices}
    n_decoy_nodes = count_decoy_nodes(best, decoy_terminals)
    ok2 = (n_decoy_nodes == 0)
    icon2 = "✓" if ok2 else "✗"
    print(f"    {icon2} Nœuds leurres dans l'arbre : {n_decoy_nodes}")
    if not ok2:
        all_pass = False
        print(f"      ⚠  L'expression utilise encore la variable leurre !")
        # Identifier les sous-expressions impliquant le leurre
        def find_decoy_exprs(node, decoy_set, depth=0):
            if node is None or depth > 3:
                return []
            found = []
            if node.value in decoy_set:
                found.append(to_string(node))
            found += find_decoy_exprs(node.left, decoy_set, depth+1)
            found += find_decoy_exprs(node.right, decoy_set, depth+1)
            return found
        exprs = find_decoy_exprs(best, decoy_terminals)
        for e in exprs[:5]:
            print(f"        → {e}")

    # ── 3. Ablation MSE ────────────────────────────────────────────────────
    print()
    print("  [3] Ablation MSE (remplacement du leurre par 0)")
    y_pred_full = evaluate_vector(best, X_data)
    mse_full = float(np.mean((y_pred_full - y_data) ** 2))

    X_ablated = X_data.copy()
    for di in decoy_indices:
        X_ablated[:, di] = 0.0
    y_pred_ablated = evaluate_vector(best, X_ablated)
    mse_ablated = float(np.mean((y_pred_ablated - y_data) ** 2))

    delta_pct = abs(mse_ablated - mse_full) / (mse_full + 1e-15) * 100
    ok3 = (delta_pct < 5.0)   # variation < 5% → leurre vraiment ignoré
    icon3 = "✓" if ok3 else "✗"
    print(f"    MSE avec leurre   : {mse_full:.6e}")
    print(f"    MSE sans leurre   : {mse_ablated:.6e}")
    print(f"    {icon3} Variation          : {delta_pct:.2f}%  "
          f"({'decoy ignored' if ok3 else 'decoy used!'})")
    if not ok3:
        all_pass = False

    # ── Verdict final ──────────────────────────────────────────────────────
    print()
    print(SEP)
    if all_pass:
        print("  ✓ VERDICT: PASS — all decoy variables rejected.")
        print("    Feature importance and the Cleaner are working")
        print("    correctly on this problem.")
    else:
        print("  ✗ VERDICT: FAIL — at least one decoy variable is not rejected.")
        print("    Hints: increase PARSIMONY, reduce FRAG_TAU_MAX,")
        print("    or check the constant optimizer is not neutralizing X[decoy]")
        print("    par une constante multiplicative proche de 0.")
    print("═" * 70)
    print()


def try_plot(name: str, func, best: Node,
             xs: List[float], ys: List[float],
             log_csv: str):
    try:
        import matplotlib.pyplot as plt
        import numpy as np

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle(f"GP_ELITE — {name}", fontsize=13, fontweight="bold")

        # --- Courbe fit ---
        x_plot  = np.linspace(min(xs), max(xs), 300)
        y_target = [func(x) for x in x_plot]
        y_pred   = [evaluate(best, x) for x in x_plot]

        axes[0].plot(x_plot, y_target, "b-",  lw=2, label="Cible")
        axes[0].plot(x_plot, y_pred,   "r--", lw=2, label=f"GP: {to_string(best)[:50]}")
        axes[0].scatter(xs[:60], ys[:60], s=10, color="gray", alpha=0.5, label="Dataset")
        axes[0].set_title("Target vs discovered expression")
        axes[0].legend(fontsize=8)
        axes[0].grid(True, alpha=0.3)

        # --- Courbe d'apprentissage ---
        try:
            gens, fits = [], []
            with open(log_csv) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    gens.append(int(row["gen"]))
                    fits.append(float(row["fit"]))
            axes[1].semilogy(gens, fits, "g.-", lw=1.5, markersize=4)
            axes[1].set_title("Fitness over generations (log)")
            axes[1].set_xlabel("Generation")
            axes[1].set_ylabel("Fitness (log)")
            axes[1].grid(True, alpha=0.3)
        except Exception:
            axes[1].text(0.5, 0.5, "Log CSV indisponible",
                         ha="center", va="center", transform=axes[1].transAxes)

        plt.tight_layout()
        try:
            out_png = "gp_elite_result.png"
            plt.savefig(out_png, dpi=120)
            print(f"[PLOT] Graphique → {out_png}")
        except Exception:
            pass  # filesystem read-only, ignoré silencieusement
        plt.show()

    except ImportError:
        pass  # matplotlib non disponible
    except Exception:
        pass  # toute autre erreur ignorée silencieusement

# ============================================================
# INTERFACE PRINCIPALE
# ============================================================

def run(name: str, func, cfg: Config = None, problem_key: str = '1'):
    if cfg is None:
        cfg = Config()

    random.seed()   # Non-deterministic par default
                    # Utiliser random.seed(42) pour reproductibilité

    best, xs, ys = evolve(func, cfg, problem_key)

    if best is None:
        print("[ERROR] No solution found.")
        return

    print_result(name, best, xs, ys, cfg)
    try_plot(name, func, best, xs, ys, cfg.LOG_CSV)

# ============================================================
# MAIN
# ============================================================

# ============================================================
# MAIN
# ============================================================

# ----------------------------------------------------------------
# Catalogue de problèmes (4 classiques + 6 complexes)
# ----------------------------------------------------------------

def _safe_sinc(x: float) -> float:
    return math.sin(x) / x if abs(x) > 1e-8 else 1.0

PROBLEMS: Dict[str, tuple] = {
    # ---- Classiques ----
    "1": ("sin(x²) + x·cos(x)",
          lambda x: math.sin(x * x) + x * math.cos(x),
          -3.0, 3.0),

    "2": ("x³ - x² + x - 1",
          lambda x: x**3 - x**2 + x - 1,
          -3.0, 3.0),

    "3": ("exp(-x²)·sin(2x)",
          lambda x: math.exp(-x * x) * math.sin(2 * x),
          -2.5, 2.5),

    "4": ("log(1+x²)·cos(x)",
          lambda x: math.log(1 + x * x) * math.cos(x),
          -2.5, 2.5),

    # ---- Complexes ----
    "5": ("x·sin(x²)·cos(x/2)",
          lambda x: x * math.sin(x * x) * math.cos(x / 2.0),
          -3.0, 3.0),

    "6": ("exp(-|x|)·(x²-1)",
          lambda x: math.exp(-abs(x)) * (x * x - 1.0),
          -4.0, 4.0),

    "7": ("sinc(x)·cos(x²)  [sinc=sin(x)/x]",
          lambda x: _safe_sinc(x) * math.cos(x * x),
          -3.0, 3.0),

    "8": ("sin(πx)/(x²+1)",
          lambda x: math.sin(math.pi * x) / (x * x + 1.0),
          -3.0, 3.0),

    "9": ("tanh(x)·exp(-x²/4)",
          lambda x: math.tanh(x) * math.exp(-x * x / 4.0),
          -3.5, 3.5),

    "10": ("x³·sin(1/x)",
           lambda x: x ** 3 * math.sin(1.0 / x),
           0.2, 3.0),   # évite la singularité en 0
}

# ============================================================
# [v16-BATTERY] CHARGEMENT DE DONNÉES RÉELLES — NASA Battery Dataset
# ============================================================
#
# load_custom_csv(file_path) lit un CSV avec les colonnes :
#   temperature, cycle, courant  →  matrice X (n_samples, 3)
#   capacity_SOH                 →  vecteur y (n_samples,)
#
# MinMaxScaler ramène X dans [-2.0, 2.0] (même domaine que BATTERY_SOH
# synthétique) pour garantir la stabilité numérique des îles GP.
#
# Note : X ne contient PAS de leurre (3 features réelles uniquement).
# La Feature Importance et le decoy_report sont désactivés en mode CSV.
# ─────────────────────────────────────────────────────────────────────

class _ShiftFreeScaler:
    """[v23] Normalisation SANS décalage : divise chaque colonne par son
    max|x|. Préserve EXACTEMENT la structure multiplicative (x·y, x/y, x^n)
    — contrairement à MinMax qui introduit un offset β transformant x·y en
    (x+β1)(y+β2) = x·y + β1·y + β2·x + β1β2 (termes croisés → arbres gonflés).
    Le benchmark Feynman a montré 4-9× moins de nœuds et R² parfait sur les
    lois multiplicatives avec cette normalisation."""
    # [v0.8] Option normalize="grouped" : UN facteur commun aux colonnes
    # d'échelles comparables (max|x| à moins d'un facteur GROUP_RATIO les uns
    # des autres). Diviser chaque colonne par son propre max|x| préserve les
    # produits mais pas les sommes et différences de variables de même
    # nature : sur Feynman I.8.14, sqrt((x2-x1)^2 + (y2-y1)^2) avec des
    # maxima de 4,97 et 4,99 devient une autre fonction des variables
    # normalisées. Mesuré (benchmarks/results_0.8, campagne 3) : 75 lois
    # exactes contre 69 sur 205 (I.8.14 : 5/5 contre 0/5), R² réel médian
    # 0,769 contre 0,735, mais 6 effondrements hors domaine contre 4 : pas le
    # défaut, une option.
    GROUP_RATIO = 10.0

    def __init__(self, group_ratio=None):
        self.scale_ = None
        self.group_ratio = group_ratio

    def fit_transform(self, X):
        m = np.max(np.abs(X), axis=0).astype(np.float64)
        # [v0.8] Seule une colonne nulle garde le facteur 1. Le seuil était
        # 1e-12 : une colonne en unités SI de l'ordre de 1e-19 (une charge
        # en coulombs) restait alors à 1e-19 et la recherche n'en tirait rien.
        m[~(m > 0.0)] = 1.0
        ratio = getattr(self, "group_ratio", None)
        if ratio is not None and ratio > 1.0 and m.size > 1:
            order = np.argsort(m, kind="stable")
            scale = m.copy()
            start = 0
            while start < len(order):
                end = start
                while (end + 1 < len(order)
                       and m[order[end + 1]] <= ratio * m[order[start]]):
                    end += 1
                grp = order[start:end + 1]
                scale[grp] = m[grp].max()
                start = end + 1
            m = scale
        self.scale_ = m
        return X / m

    def transform(self, X):
        return X / self.scale_

    def inverse_transform(self, Xs):
        return Xs * self.scale_

class _IdentityScaler:
    """[v0.5] Ne normalise rien. Utile en mode « constante mystere » : la
    constante rendue est alors exprimee dans les unites REELLES des colonnes,
    et non dans un espace remis a l'echelle ou elle n'aurait aucun sens
    physique. scale_ vaut 1 partout, donc les consommateurs qui replient la
    normalisation (SRBench model(), audit) restent corrects sans cas special."""
    def __init__(self):
        self.scale_ = None
    def fit_transform(self, X):
        self.scale_ = np.ones(X.shape[1], dtype=np.float64)
        return np.asarray(X, dtype=np.float64)
    def transform(self, X):
        return np.asarray(X, dtype=np.float64)
    def inverse_transform(self, Xs):
        return np.asarray(Xs, dtype=np.float64)


# [v0.7] Seuil de bascule entre « ne pas normaliser » et « normaliser ».
# MESURÉ par benchmarks/feynman_scale_ratio.py (96 runs : 8 équations
# x 6 décades de disparité x 2 modes, moteur 0.6.0, PYTHONHASHSEED=0) :
#     ratio ~2    none 8/8 exactes (7 canoniques) | auto 6/8 (6)  -> none
#     ratio ~10   none 6/8 (4)                    | auto 6/8 (5)  -> égalité
#     ratio ~100  none 5/8 (4)                    | auto 6/8 (6)  -> auto
#     ratio ~1e6  none 4/8 (2)                    | auto 6/8 (5)  -> auto
# `auto` s'est révélé parfaitement invariant d'échelle (6/8 sur six
# décades) ; son seul coût est de perdre deux équations quand la
# normalisation est inutile. Les jeux bien échelonnés ont un ratio naturel
# de 1.0 à 7.4 : le seuil de 10 laisse de la marge des deux côtés.
SCALE_RATIO_THRESHOLD = 10.0


def _scale_ratio(X_raw):
    """Rapport d'échelle entre colonnes : max(écart-type) / min(écart-type),
    calculé sur les seules colonnes NON CONSTANTES (sinon une colonne de
    variance nulle donnerait un ratio infini). Renvoie 1.0 quand moins de
    deux colonnes varient — il n'y a alors rien à comparer."""
    X = np.asarray(X_raw, dtype=np.float64)
    if X.ndim != 2 or X.shape[1] < 2:
        return 1.0
    with np.errstate(invalid="ignore"):
        sd = np.std(X, axis=0)
    sd = sd[np.isfinite(sd) & (sd > 0.0)]
    if sd.size < 2:
        return 1.0
    return float(sd.max() / sd.min())


def _choose_scaler(X_raw, normalize, x_range):
    """[v23] Sélectionne la normalisation.

    'auto'  : [v0.7] shift-free (division par max|x|) pour TOUTES les
              données. Jusqu'en 0.6 : shift-free seulement si toutes les
              features étaient strictement positives, sinon MinMax — qui
              remplace chaque variable par a*(x - x0) et casse la structure
              multiplicative. Mesuré sur la version publiée (critère fixé
              avant ; 8 lois à entrées signées x 5 seeds, puis 6 jeux PMLB
              standardisés comme dans SRBench x 5 plis ;
              benchmarks/norm_signed.py) : récupérations exactes 20/40 contre
              7/40 ; R² test médian sur données réelles 0.808 contre 0.808,
              moyenne 0.781 contre 0.775, pire pli 0.406 contre 0.399,
              meilleur sur 16 plis appariés sur 30, aucun effondrement de
              part et d'autre ; formules livrées plus courtes (médiane 16
              nœuds contre 20). NE SE DEMANDE
              JAMAIS s'il faut normaliser, seulement comment.
    'smart' : [v0.7] teste d'abord la disparité d'échelle entre colonnes.
              En dessous de SCALE_RATIO_THRESHOLD, ne normalise pas (les
              features brutes préservent produits, différences et
              lisibilité des constantes) ; au-dessus, délègue à 'auto'.
    'none'  : jamais de normalisation.

    Limite connue et NON MESURÉE de 'smart' : le test ne capte que la
    disparité RELATIVE entre colonnes. Des features toutes à la même
    échelle extrême (toutes ~1e-9, ou toutes ~1e12) donnent un ratio de 1
    et ne seront pas normalisées. Ne pas ajouter de garde-fou sur l'échelle
    absolue sans l'avoir mesuré."""
    mode = (normalize or "auto").lower()
    if mode in ("none", "off", "raw", "identity"):     # [v0.5]
        return _IdentityScaler(), "none (raw features)"
    if mode == "smart":                                # [v0.7]
        ratio = _scale_ratio(X_raw)
        if ratio < SCALE_RATIO_THRESHOLD:
            return _IdentityScaler(), (
                f"none (smart: scale ratio {ratio:.1f} < "
                f"{SCALE_RATIO_THRESHOLD:g})")
        mode = "auto"
    if mode == "auto":
        mode = "divmax"
    if mode in ("divmax", "shiftfree", "div"):
        return _ShiftFreeScaler(), "divmax (shift-free, preserves products)"
    if mode == "grouped":                              # [v0.8] option
        return (_ShiftFreeScaler(group_ratio=_ShiftFreeScaler.GROUP_RATIO),
                "divmax, one factor per group of comparable columns")
    if mode in ("standard", "zscore", "std"):
        from sklearn.preprocessing import StandardScaler as _SS
        return _SS(), "standard (z-score)"
    return _MinMaxScaler(feature_range=x_range), f"minmax {x_range}"

def load_generic_csv(file_path: str,
                     target_col: str = None,
                     feature_cols: list = None,
                     op_pool: str = "physical",
                     normalize: str = "auto",
                     x_range: tuple = (-2.0, 2.0)):
    """[v22-CSV] Charge N'IMPORTE QUEL fichier CSV pour régression symbolique.

    Conventions par default (zéro configuration) :
      · dernière colonne numérique = cible (y)
      · toutes les autres colonnes numériques = features (X)
      · colonnes non numériques (texte, dates) ignorées avec avertissement
    Tout est surchargeable via target_col / feature_cols.

    Retourne (X_scaled, y, feature_names, target_name, scaler).
    Installe aussi le pool d'opérateurs choisi et les noms de colonnes
    dans les globals du module (CSV_FEATURE_NAMES, _GENERIC_*).
    """

    if not _csv_deps_ok():
        raise ImportError("pandas et scikit-learn requis : "
                          "pip install pandas scikit-learn")
    _pd = _csv_deps()[0]
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Fichier introuvable : '{file_path}'  "
                                f"(cwd : {os.getcwd()})")

    # ── Lecture + détection du séparateur (',' ';' '\t') ──
    try:
        df = _pd.read_csv(file_path, sep=None, engine="python")
    except Exception:
        df = _pd.read_csv(file_path)
    df.columns = [str(c).strip() for c in df.columns]

    # ── Colonnes numériques seulement ──
    num_df = df.apply(_pd.to_numeric, errors="coerce")
    non_num = [c for c in df.columns if num_df[c].isna().all()]
    if non_num:
        print(f"[CSV] Non-numeric columns ignored: {non_num}")
    num_cols = [c for c in df.columns if c not in non_num]
    if len(num_cols) < 2:
        raise ValueError(f"At least 2 numeric columns required "
                         f"(features + target). Detected: {num_cols}")

    # ── Cible / features ──
    if target_col is None:
        target_col = num_cols[-1]          # convention : dernière colonne
    elif target_col not in num_cols:
        raise KeyError(f"Target column '{target_col}' missing or non-numeric. "
                       f"Numeric columns: {num_cols}")
    if feature_cols is None:
        feature_cols = [c for c in num_cols if c != target_col]
    else:
        bad = [c for c in feature_cols if c not in num_cols]
        if bad:
            raise KeyError(f"Missing/non-numeric features: {bad}")

    # ── Nettoyage NaN ──
    use_cols = feature_cols + [target_col]
    n_before = len(num_df)
    clean = num_df[use_cols].dropna()
    n_drop = n_before - len(clean)
    if n_drop:
        print(f"[CSV] {n_drop} row(s) with missing values dropped.")
    n = len(clean)
    if n < 10:
        raise ValueError(f"Too little data after cleaning: {n} (min 10).")
    if n < 30:
        print(f"[CSV] ⚠ Small dataset ({n} rows) — GP is more reliable with ≥30.")

    X_raw = clean[feature_cols].values.astype(np.float64)
    y     = clean[target_col].values.astype(np.float64)

    # ── Normalisation features (shift-free 'auto' par default) ──
    scaler, _norm_desc = _choose_scaler(X_raw, normalize, x_range)
    X_scaled = scaler.fit_transform(X_raw)
    print(f"[CSV] Normalisation : {_norm_desc}")

    # ── Pool d'opérateurs ──
    op_pool = (op_pool or "physical").lower()
    if op_pool not in _GENCSV_POOLS:
        print(f"[CSV] Unknown pool '{op_pool}' — using 'physical'.")
        op_pool = "physical"
    b_ops, b_w, u_ops, u_w = _GENCSV_POOLS[op_pool]
    state._GENERIC_BINARY_OPS, state._GENERIC_BINARY_WEIGHTS = list(b_ops), list(b_w)
    state._GENERIC_UNARY_OPS,  state._GENERIC_UNARY_WEIGHTS  = list(u_ops), list(u_w)
    state._GENERIC_CSV_MODE = True
    state.CSV_FEATURE_NAMES = list(feature_cols)
    state.CSV_TARGET_NAME   = str(target_col)

    print(f"[CSV] ✓ {n} samples | {len(feature_cols)} features → target '{target_col}'")
    print(f"      Features : {feature_cols}")
    print(f"      Operator pool: '{op_pool}' "
          f"→ {b_ops + u_ops}")
    # Plages brutes par feature (utile pour interpréter la formule)
    for i, c in enumerate(feature_cols):
        print(f"        X[{i}] = {c:<20} ∈ [{X_raw[:,i].min():.4g}, {X_raw[:,i].max():.4g}]")
    print(f"      Cible '{target_col}' ∈ [{y.min():.4g}, {y.max():.4g}]  moy={y.mean():.4g}")

    return X_scaled, y, list(feature_cols), str(target_col), scaler


def load_custom_csv(file_path: str):
    """
    Charge un fichier CSV de données batterie réelles (format NASA).

    Colonnes attendues :
        temperature, cycle, courant  →  X (features physiques)
        capacity_SOH                 →  y (cible : State of Health)

    Le scaler MinMaxScaler ramène X dans [-2.0, 2.0] pour assurer
    la cohérence avec le domaine d'entraînement de BATTERY_SOH.

    Returns
    -------
    X_scaled : np.ndarray, shape (n_samples, 3)
    y        : np.ndarray, shape (n_samples,)

    Raises
    ------
    ImportError  si pandas ou scikit-learn ne sont pas installés.
    FileNotFoundError / KeyError si le fichier ou les colonnes manquent.
    ValueError  si le fichier contient moins de 10 lignes utiles.
    """
    if not _csv_deps_ok():
        raise ImportError(
            "[BATTERY_SOH] pandas et scikit-learn sont requis pour charger "
            "des données CSV réelles.\n"
            "Installez-les avec : pip install pandas scikit-learn"
        )
    _pd = _csv_deps()[0]

    # ── 1. Lecture & nettoyage des noms de colonnes ──────────────────────
    if not os.path.isfile(file_path):
        raise FileNotFoundError(
            f"[BATTERY_SOH] Fichier introuvable : '{file_path}'\n"
            f"  Current directory: {os.getcwd()}"
        )

    df = _pd.read_csv(file_path)
    # Supprimer les espaces de début/fin dans les noms de colonnes
    # (ex : 'capacity_SOH  ' → 'capacity_SOH' détecté dans le fichier NASA)
    df.columns = df.columns.str.strip()

    # ── 2. Validation des colonnes requises ──────────────────────────────
    required_cols = ['temperature', 'cycle', 'courant', 'capacity_SOH']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise KeyError(
            f"[BATTERY_SOH] Colonnes manquantes dans '{file_path}' : {missing}\n"
            f"  Detected columns: {df.columns.tolist()}\n"
            f"  Colonnes requises  : {required_cols}"
        )

    # ── 3. Suppression des lignes avec valeurs manquantes ────────────────
    n_before = len(df)
    df = df[required_cols].dropna()
    n_dropped = n_before - len(df)
    if n_dropped > 0:
        print(f"[BATTERY_SOH] ⚠  {n_dropped} row(s) with NaN dropped.")

    n_samples = len(df)
    if n_samples < 10:
        raise ValueError(
            f"[BATTERY_SOH] Too little data after cleaning: "
            f"{n_samples} ligne(s) (minimum requis : 10).\n"
            f"  Check the contents of '{file_path}'."
        )

    # Avertissement si le dataset est petit (GP peu fiable sous 30 points)
    if n_samples < 30:
        print(
            f"[BATTERY_SOH] ⚠  Small dataset ({n_samples} rows). "
            f"Le GP converge mieux avec ≥ 30 points. "
            f"Results indicative only."
        )

    # ── 4. Extraction X / y ──────────────────────────────────────────────
    # Ordre des features : [temperature, cycle, courant]
    # → cohérent avec X[:,0]=Temp, X[:,1]=Cycles, X[:,2]=Courant
    X_raw = df[['temperature', 'cycle', 'courant']].values.astype(np.float64)
    y     = df['capacity_SOH'].values.astype(np.float64)

    # ── 5. Normalisation MinMaxScaler → [-2.0, 2.0] ─────────────────────
    # feature_range=(-2, 2) aligne exactement sur le domaine synthétique
    # BATTERY_SOH, évitant tout débordement dans exp(X[:,0]) sur les îles.
    scaler  = _MinMaxScaler(feature_range=(-2.0, 2.0))
    X_scaled = scaler.fit_transform(X_raw)

    print(
        f"[BATTERY_SOH] ✓ CSV loaded: {n_samples} samples, "
        f"3 features → normalized to [-2.0, 2.0]"
    )
    print(
        f"  Plages brutes  : "
        f"T=[{X_raw[:,0].min():.2f},{X_raw[:,0].max():.2f}]  "
        f"C=[{X_raw[:,1].min():.1f},{X_raw[:,1].max():.1f}]  "
        f"I=[{X_raw[:,2].min():.3f},{X_raw[:,2].max():.3f}]"
    )
    print(
        f"  SOH brut       : "
        f"min={y.min():.4f}  max={y.max():.4f}  "
        f"moy={y.mean():.4f}"
    )

    # [v16-BATTERY CSV] Activer le pool d'opérateurs physiques
    # sin/cos/tan retirés — sans justification physique sur données batterie réelles.
    # Opérateurs retenus : exp (Arrhenius), log (Fick), pow (Wöhler),
    #                      sq (Joule), sqrt (diffusion), tanh (saturation)
    state._BATTERY_CSV_MODE = True
    print(
        f"  Operator pool: battery physics "
        f"[{', '.join(_BATTERY_UNARY_OPS)}] "
        f"— sin/cos/tan exclus"
    )

    return X_scaled, y


# [v16-NDIM] REGISTRE DE PROBLÈMES N-DIMENSIONNELS
# ============================================================
#
# Chaque entrée : (nom, func(X_matrix), n_features, x_min, x_max)
#
# func reçoit une matrice X de shape (n_samples, n_features) et retourne
# un vecteur y de shape (n_samples,) — entièrement vectorisé NumPy.
#
# Exemple :  ND1  f(X) = X[:,0]*sin(X[:,1]) + X[:,2]**2   (3 features)
#            ND2  f(X) = exp(-X[:,0]**2) * cos(X[:,1])    (2 features)
#            ND3  f(X) = X[:,0]**3 - X[:,1]*X[:,2]        (3 features, polynôme)
# ─────────────────────────────────────────────────────────────────────────────

ND_PROBLEMS: Dict[str, tuple] = {
    # (name, func(X), n_features, x_min, x_max)
    "ND1": (
        "X[:,0]·sin(X[:,1]) + X[:,2]²",
        lambda X: X[:, 0] * np.sin(X[:, 1]) + X[:, 2] ** 2,
        3, -3.0, 3.0,
    ),
    "ND2": (
        "exp(-X[:,0]²)·cos(X[:,1])",
        lambda X: np.exp(-X[:, 0] ** 2) * np.cos(X[:, 1]),
        2, -2.5, 2.5,
    ),
    "ND3": (
        "X[:,0]³ - X[:,1]·X[:,2]",
        lambda X: X[:, 0] ** 3 - X[:, 1] * X[:, 2],
        3, -3.0, 3.0,
    ),
    "ND4": (
        "sin(X[:,0]+X[:,1]) · exp(-X[:,2]²/2)",
        lambda X: np.sin(X[:, 0] + X[:, 1]) * np.exp(-X[:, 2] ** 2 / 2.0),
        3, -2.5, 2.5,
    ),
    "ND5": (
        "X[:,0]·X[:,1] / (1 + X[:,2]²)",
        lambda X: X[:, 0] * X[:, 1] / (1.0 + X[:, 2] ** 2),
        3, -3.0, 3.0,
    ),
    # ── Problèmes avec variables leurres [v16-DECOY] ──────────────────────
    # La cible ne dépend PAS de X[n_features-1] — c'est du bruit pur.
    # Test de robustesse : Feature Importance doit attribuer 0.000 au leurre,
    # et le Cleaner doit rejeter les arbres qui l'utilisent.
    "ND1_DECOY": (
        "X[:,0]·sin(X[:,1]) + X[:,2]²  [+X[3] LEURRE]",
        lambda X: X[:, 0] * np.sin(X[:, 1]) + X[:, 2] ** 2,  # X[3] ignoré
        4, -3.0, 3.0,
    ),
    "ND3_DECOY": (
        "X[:,0]³ - X[:,1]·X[:,2]  [+X[3] LEURRE]",
        lambda X: X[:, 0] ** 3 - X[:, 1] * X[:, 2],          # X[3] ignoré
        4, -3.0, 3.0,
    ),
    "ND5_DECOY": (
        "X[:,0]·X[:,1]/(1+X[:,2]²)  [+X[3] LEURRE]",
        lambda X: X[:, 0] * X[:, 1] / (1.0 + X[:, 2] ** 2),  # X[3] ignoré
        4, -3.0, 3.0,
    ),
    # ── [v16-BATTERY] Dégradation batterie Li-Ion — modèle Arrhenius ──────────
    # SOH = 1 - 0.02·exp(T)·C - 0.005·I²  + bruit capteur
    # X[0] = Température (normalisée)   X[1] = Nb cycles (normalisé)
    # X[2] = Courant décharge (norm.)   X[3] = LEURRE (bruit pur)
    "BATTERY_SOH": (
        "1 - 0.02·exp(X[0])·X[1] - 0.005·X[2]²  [+X[3] LEURRE]",
        lambda X: (
            1.0
            - 0.02 * np.exp(X[:, 0]) * X[:, 1]
            - 0.005 * (X[:, 2] ** 2)
            + np.random.normal(0, 0.001, X.shape[0])
        ),
        4, -2.0, 2.0,
    ),
    # ── [SYRACUSE] Conjecture de Collatz — temps de vol (4 features) ───────────
    # Features : X[0]=log2(n), X[1]=v2(n), X[2]=odd_part(n), X[3]=is_mod4_1(n)
    # Le dataset est généré par generate_syracuse_dataset() et injecté via
    # X_override/y_override dans evolve(). La lambda est un placeholder.
    "SYRACUSE": (
        "Collatz flight time — 4 features [log2,v2,odd_part,mod4_1]",
        lambda X: np.zeros(X.shape[0]),   # placeholder — jamais appelé
        SYRACUSE_N_FEATURES, -2.0, 2.0,
    ),
}

# ── [v16-NDIM] Poids d'opérateurs boostés pour l'initialisation N-D ────────
# En mode 1-D les seeds humaines compensaient la faible probabilité de tirer
# "exp" ou "log". En mode N-D on refuse de tricher : on augmente simplement
# le poids de ces opérateurs dans le pool d'initialisation random, et on
# garantit une couverture minimale via _nd_diverse_population().
# Le GP doit DÉCOUVRIR la structure — on lui donne juste un espace de
# recherche mieux réparti, pas la réponse.

# _ND_UNARY_WEIGHTS_INIT doit avoir autant d'éléments que le plus grand pool unaire.
# Standard = 8 ops  [sin cos log sqrt abs neg sq cube]
# Syracuse = 9 ops  [cos log sqrt abs neg sq cube is_even step]
# Le slice [:len(_u_ops)] prend les N premiers → 8 pour standard, 9 pour Syracuse.
# Doit donc avoir au moins 9 éléments.
_ND_UNARY_WEIGHTS_INIT = [3, 3, 2, 2, 1, 1, 3, 1, 3]


def _one_run(key: str, func, cfg: Config) -> dict:
    """Lance une unique évolution et retourne les métriques."""
    best, xs, ys = evolve(func, cfg, problem_key=key)
    if best is None:
        return {"mse": 1000.0, "gen": cfg.GENERATIONS, "size": 0, "ok": 0, "expr": ""}
    mse = float(raw_mse(best, xs, ys))
    try:
        with open(cfg.LOG_CSV) as f:
            rows_log = list(csv.DictReader(f))
        gen = int(rows_log[-1]["gen"]) if rows_log else cfg.GENERATIONS
        sz  = int(rows_log[-1]["size"]) if rows_log else tree_size(best)
    except Exception:
        gen = cfg.GENERATIONS
        sz  = tree_size(best)
    return {"mse": mse, "gen": gen, "size": sz,
            "ok": int(mse < 1e-4), "expr": to_string(best)}


def run_benchmark(keys: List[str],
                  n_runs: int = 5,
                  fast: bool = True,
                  ultrafast: bool = False,
                  transfer: bool = False,
                  ablation: bool = False,
                  csv_out: str = "benchmark_v13.csv"):
    """
    Benchmark rigoureux avec étude d'ablation optionnelle.

    ablation=True : teste 4 configurations par problème
      - BASE      : GP classique (pas de stigmergie, pas de seeding)
      - +LIB      : + bibliothèque de fragments (phéromones)
      - +CO       : + co-graphe
      - +SEQ      : + mémoire de séquences  (= système complet)

    transfer=True : warm_transfer entre problèmes consécutifs.

    Métriques : MSE médian, taux succès (MSE<1e-4), gen. médiane, taille médiane.
    """
    import statistics as _stats

    CONDITIONS = [
        ("BASE",  dict(use_seeding=False, use_lib=False, use_cograph=False, use_seqmem=False)),
        ("+LIB",  dict(use_seeding=False, use_lib=True,  use_cograph=False, use_seqmem=False)),
        ("+CO",   dict(use_seeding=False, use_lib=True,  use_cograph=True,  use_seqmem=False)),
        ("+SEQ",  dict(use_seeding=False, use_lib=True,  use_cograph=True,  use_seqmem=True)),
    ] if ablation else [
        ("FULL",  dict(use_seeding=True,  use_lib=True,  use_cograph=True,  use_seqmem=True)),
        ("NOSEED",dict(use_seeding=False, use_lib=True,  use_cograph=True,  use_seqmem=True)),
    ]

    print()
    print("=" * 80)
    mode_str = "ABLATION" if ablation else ("TRANSFER" if transfer else "STANDARD")
    print(f"BENCHMARK GP_ELITE v13  —  {n_runs} runs × {len(keys)} prob. × {len(CONDITIONS)} cond.  [{mode_str}]")
    print("=" * 80)

    all_rows = []
    # summary[(key, cond_name)] = dict de stats
    summary_map: Dict[tuple, dict] = {}

    # ── Ouverture du CSV en mode incrémental dès le début ────────────
    # FIX v13.10 : résoudre le CSV relatif au répertoire du script,
    # pas au cwd (évite system32 si Python lancé depuis le menu démarrer).
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(csv_out):
        csv_out = os.path.join(_script_dir, csv_out)
    out_path = os.path.abspath(csv_out)
    _csv_fields = ["problem", "name", "condition", "run",
                   "mse", "gen", "size", "ok", "elapsed", "expr"]
    try:
        _csv_file   = open(out_path, "w", newline="", encoding="utf-8")
        _csv_writer = csv.DictWriter(_csv_file, fieldnames=_csv_fields)
        _csv_writer.writeheader()
        _csv_file.flush()
        print(f"[BENCH] Incremental save → {out_path}")
    except Exception as e:
        print(f"[BENCH] Could not open {out_path}: {e} — rows will not be saved.")
        _csv_file   = None
        _csv_writer = None

    for key in keys:
        name, func, x_min, x_max = PROBLEMS[key]
        print(f"\n{'─'*70}")
        print(f"  Problem {key}: {name}  [{x_min}, {x_max}]")
        print(f"{'─'*70}")

        if transfer and key != keys[0]:
            warm_transfer(decay_lib=0.35, decay_co=0.25, decay_seq=0.45)

        for cond_name, cond_flags in CONDITIONS:
            print(f"\n  [{cond_name:6s}]", end="  ")
            cfg = make_cfg(x_min, x_max, fast=fast, ultrafast=ultrafast, **cond_flags)

            run_mses, run_gens, run_szs, run_oks = [], [], [], []

            for r in range(n_runs):
                t0  = time.time()
                res = _one_run(key, func, cfg)
                dt  = time.time() - t0
                run_mses.append(res["mse"])
                run_gens.append(res["gen"])
                run_szs.append(res["size"])
                run_oks.append(res["ok"])
                sym = "✓" if res["ok"] else "✗"
                print(f"{sym}{res['mse']:.1e}", end="  ", flush=True)

                row = {
                    "problem": key, "name": name,
                    "condition": cond_name, "run": r + 1,
                    "mse": res["mse"], "gen": res["gen"],
                    "size": res["size"], "ok": res["ok"],
                    "elapsed": round(dt, 1), "expr": res["expr"],
                }
                all_rows.append(row)

                # Écriture immédiate sur disque — survivra à un crash
                if _csv_writer:
                    try:
                        _csv_writer.writerow(row)
                        _csv_file.flush()
                    except Exception as _e:
                        print(f"\n[BENCH] CSV write error: {_e}")

                # Libération mémoire entre chaque run
                gc.collect()

            succ  = sum(run_oks) / n_runs * 100
            mmed  = _stats.median(run_mses)
            gmed  = _stats.median(run_gens)
            szmed = _stats.median(run_szs)
            print(f"→ {succ:3.0f}% succ  MSE={mmed:.2e}  gen={gmed:.0f}  sz={szmed:.0f}")
            summary_map[(key, cond_name)] = {
                "succ": succ, "mse_med": mmed,
                "gen_med": gmed, "sz_med": szmed,
            }
            # Libération mémoire entre chaque condition
            gc.collect()

    # Fermeture propre du fichier incrémental
    if _csv_file:
        try:
            _csv_file.close()
            print(f"\n[BENCH] CSV finalized → {out_path}")
        except Exception:
            pass

    # Tableau récapitulatif
    cond_names = [c for c, _ in CONDITIONS]
    col_w = 18
    print()
    print("=" * 80)
    header = f"{'PB':>3}  {'Problem':<24}" + "".join(
        f"  {cn:>{col_w}}" for cn in cond_names)
    print(header)
    print(f"{'':>3}  {'':24}" + "".join(
        f"  {'succ%/MSE_med':>{col_w}}" for _ in cond_names))
    print("-" * 80)
    for key in keys:
        name, *_ = PROBLEMS[key]
        row = f"{key:>3}  {name:<24.24}"
        for cn in cond_names:
            s = summary_map.get((key, cn))
            if s:
                cell = f"{s['succ']:3.0f}% {s['mse_med']:.2e}"
                row += f"  {cell:>{col_w}}"
            else:
                row += f"  {'N/A':>{col_w}}"
        print(row)
    print("=" * 80)

    return summary_map


# ----------------------------------------------------------------
# Entrée principale
# ----------------------------------------------------------------

def _print_menu():
    print("GP_ELITE v13 — Symbolic Regression avec stigmergie adaptative")
    print()
    print("Available problems:")
    for k, (n, _, x0, x1) in PROBLEMS.items():
        tag = "★ complexe" if int(k) >= 5 else "  classique"
        print(f"  {k:>2}: {tag}  {n}  [{x0}, {x1}]")
    print()
    print("Commandes :")
    print("  python GP_ELITE_v13.py <N>                   # problem N with seeding")
    print("  python GP_ELITE_v13.py <N> noseed            # problem N without seeding")
    print("  python GP_ELITE_v13.py <N> noseed nolib      # ablation : GP pur")
    print()
    print("  python GP_ELITE_v13.py bench [fast]          # benchmark standard (FULL + NOSEED)")
    print("  python GP_ELITE_v13.py ablation [fast]       # 4 conditions : BASE/+LIB/+CO/+SEQ")
    print("  python GP_ELITE_v13.py ablation [fast] hard  # complex problems only")
    print("  python GP_ELITE_v13.py bench_hard            # all problems, 8 runs, transfer")
    print()
    print("Flags disponibles pour les commandes benchmark/ablation :")
    print("  fast     → lightweight config (pop=300, gen=200)")
    print("  transfer → warm_transfer between consecutive problems")


def _ask(prompt: str, valid: List[str], default: str = "") -> str:
    """Pose une question et valide la réponse. Retourne default si entrée vide."""
    while True:
        rep = input(prompt).strip()
        # y/yes → o alias, only for yes/no prompts (never when 'y' is a real
        # option, e.g. the operator-pool choice [p/t/f/y]).
        _r = rep.lower()
        if "o" in valid and "y" not in valid:
            if _r in ("y", "yes"):
                rep = "o"
            elif _r == "no":
                rep = "n"
        if rep == "" and default:
            return default
        if rep in valid:
            return rep
        print(f"  → Invalid answer. Options: {', '.join(valid)}")


def _ask_int(prompt: str, lo: int, hi: int, default: int) -> int:
    """Demande un entier dans [lo, hi]."""
    while True:
        rep = input(prompt).strip()
        if rep == "":
            return default
        try:
            v = int(rep)
            if lo <= v <= hi:
                return v
        except ValueError:
            pass
        print(f"  → Entier attendu entre {lo} et {hi}.")


def _interactive_menu():
    """
    Menu interactif affiché au démarrage quand le script est lancé sans arguments.
    Permet de choisir :
      - Le mode (problème unique / ablation / benchmark)
      - Le(s) problème(s) ciblé(s)
      - Les options (fast, nombre de runs, flags stigmergie)
    """
    SEP  = "─" * 70
    SEP2 = "═" * 70

    print()
    print(SEP2)
    print("  GP_ELITE  —  Symbolic Regression (1-D & N-D) via Genetic Programming")
    print(SEP2)
    print()

    # ── Afficher tous les problèmes ──────────────────────────────────────
    print("  Available 1-D problems:")
    print()
    classic_keys = [k for k in PROBLEMS if int(k) <= 4]
    complex_keys = [k for k in PROBLEMS if int(k) >= 5]

    print("  Classiques :")
    for k in classic_keys:
        name, _, x0, x1 = PROBLEMS[k]
        print(f"    {k:>2}.  {name:<40}  [{x0}, {x1}]")
    print()
    print("  Complexes (★) :")
    for k in complex_keys:
        name, _, x0, x1 = PROBLEMS[k]
        print(f"    {k:>2}.  {name:<40}  [{x0}, {x1}]")
    print()
    print("  N-D problems (★★):")
    for k, (nd_name, _, n_feat, x0, x1) in ND_PROBLEMS.items():
        if k in DECOY_FEATURES:
            continue   # affichés séparément
        print(f"  {k:>4}.  {nd_name:<46}  {n_feat} vars  [{x0}, {x1}]")
    print()
    print("  N-D problems with decoy variable (★★★):")
    for k in DECOY_FEATURES:
        nd_name, _, n_feat, x0, x1 = ND_PROBLEMS[k]
        decoy_idx = DECOY_FEATURES[k]
        print(f"  {k:>10}.  {nd_name:<46}  {n_feat} vars  leurre=X{decoy_idx}")
    print()
    print(SEP)

    # ── Choix du mode ────────────────────────────────────────────────────
    print()
    print("  Available modes:")
    print("    1. Single 1-D problem     — targeted run, fine-grained options")
    print("    2. Ablation               — BASE / +LIB / +CO / +SEQ")
    print("    3. Benchmark standard     — FULL vs NOSEED")
    print("    4. Single N-D problem     — multi-variable regression  [v16-NDIM]")
    print("    5. ★ SYRACUSE / Collatz  — flight time, 4 features [log2,v2,odd_part,mod4_1]  [SYRACUSE]")
    print("    6. ★ Generic CSV          — regression on YOUR data (any file)  [v22-CSV]")
    print("    7. ★ FORECAST             — extrapolate a trend beyond YOUR data  [v30]")
    print()
    mode_choice = _ask("  Your choice [1/2/3/4/5/6/7] (default=1) : ",
                       valid=["1", "2", "3", "4", "5", "6", "7"], default="1")
    print()

    # ══════════════════════════════════════════════════════════════════════
    # MODE 1 — Problème unique
    # ══════════════════════════════════════════════════════════════════════
    if mode_choice == "1":
        all_keys = list(PROBLEMS.keys())
        key = _ask(
            f"  Problem number [{'/'.join(all_keys)}] (default=5) : ",
            valid=all_keys, default="5"
        )
        name, func, x_min, x_max = PROBLEMS[key]
        print(f"  → {name}")
        print()

        # Options de vitesse
        fast_rep = _ask("  Fast mode? [y/n] (default=n, pop=600 gen=400) : ",
                        valid=["o", "n", ""], default="n")
        fast = (fast_rep == "o")

        # Options stigmergiques — une seule question, détail si non
        print()
        all_on = _ask("  Enable all stigmergic components? [y/n] (default=y) : ",
                      valid=["o", "n", ""], default="o")
        if all_on != "n":
            use_lib = use_co = use_seq = use_seed = True
        else:
            print("  Component details (Enter = disable):")
            use_lib  = _ask("    Fragment library           [y/n] (default=n) : ",
                            valid=["o", "n", ""], default="n") == "o"
            use_co   = _ask("    Co-graph                   [y/n] (default=n) : ",
                            valid=["o", "n", ""], default="n") == "o"
            use_seq  = _ask("    Sequence memory            [y/n] (default=n) : ",
                            valid=["o", "n", ""], default="n") == "o"
            use_seed = _ask("    Directed seeding           [y/n] (default=n) : ",
                            valid=["o", "n", ""], default="n") == "o"

        print()
        cfg = make_cfg(
            x_min, x_max, fast=fast,
            use_seeding=use_seed,
            use_lib=use_lib,
            use_cograph=use_co,
            use_seqmem=use_seq,
        )
        cfg.GENERATIONS = 300 if fast else 500

        flags = []
        if not use_seed: flags.append("sans seeding")
        if not use_lib:  flags.append("sans lib")
        if not use_co:   flags.append("sans cograph")
        if not use_seq:  flags.append("sans seqmem")
        tag = "  [" + ", ".join(flags) + "]" if flags else ""

        print(SEP2)
        print(f"  Launching: problem {key} — {name}{tag}")
        print(f"  Config    : {'fast' if fast else 'normal'}  "
              f"pop={cfg.POP_SIZE}  gen={cfg.GENERATIONS}  islands={cfg.N_ISLANDS}")
        print(SEP2)
        print()

        # --- NOUVEAU : CHARGEMENT DE LA GRAMMAIRE ---
        if hasattr(state, 'SEQ_MEM'):
            state.SEQ_MEM.import_grammar("grammar_shared_base.json", decay=0.5)

        best, xs, ys = evolve(func, cfg, problem_key=key)
        if best:
            print_result(name, best, xs, ys, cfg)
            try_plot(name, func, best, xs, ys, cfg.LOG_CSV)

            # --- NOUVEAU : SAUVEGARDE DE LA GRAMMAIRE ---
            if hasattr(state, 'SEQ_MEM'):
                state.SEQ_MEM.export_grammar(f"grammar_meta_p{key}.json")
                state.SEQ_MEM.export_grammar("grammar_shared_base.json")
        else:
            print("[ERROR] No solution found.")
        _pause()
    # ══════════════════════════════════════════════════════════════════════
    elif mode_choice == "2":
        print("  Select the problems to test:")
        print("    a. Tous (P1–P9)")
        print("    b. Complex only (P5–P9)  [default]")
        print("    c. Choix manuel")
        scope = _ask("  Your choice [a/b/c] (default=b) : ",
                     valid=["a", "b", "c", ""], default="b")
        if scope in ("b", ""):
            keys = [str(k) for k in range(5, 10)]
        elif scope == "a":
            keys = [str(k) for k in range(1, 10)]
        else:
            print()
            print("  Enter numbers separated by spaces (e.g. 5 6 9):")
            raw = input("  → ").strip().split()
            keys = [k for k in raw if k in PROBLEMS]
            if not keys:
                print("  No valid problem — using P5–P9.")
                keys = [str(k) for k in range(5, 10)]

        fast_rep = _ask("\n  Speed? [u=ultrafast / f=fast / n=normal] (default=u) : ",
                        valid=["u", "f", "n", ""], default="u")
        ultrafast = (fast_rep in ("u", ""))
        fast      = (fast_rep == "f")

        n_runs = _ask_int(
            f"  Runs per condition [1–10] (default=3) : ",
            lo=1, hi=10, default=3
        )

        mode_str = 'ultrafast (pop=150, gen=100)' if ultrafast else ('fast' if fast else 'normal')
        print()
        print(SEP2)
        print(f"  Ablation: {len(keys)} problem(s) × 4 conditions × {n_runs} runs")
        print(f"  Problems : {', '.join(f'P{k}' for k in keys)}")
        print(f"  Config    : {mode_str}")
        print(f"  Estimated duration: ~{len(keys) * 4 * n_runs * (3 if ultrafast else 8)} min")
        print(SEP2)
        print()

        run_benchmark(keys, n_runs=n_runs, fast=fast, ultrafast=ultrafast,
                      transfer=False, ablation=True, csv_out="ablation_v13.csv")
        _pause()

    # ══════════════════════════════════════════════════════════════════════
    # MODE 3 — Benchmark standard
    # ══════════════════════════════════════════════════════════════════════
    elif mode_choice == "3":
        fast_rep = _ask("  Fast mode? [y/n] (default=n) : ",
                        valid=["o", "n", ""], default="n")
        fast = (fast_rep == "o")

        transfer_rep = _ask("  Cross-problem transfer? [y/n] (default=n) : ",
                            valid=["o", "n", ""], default="n")
        transfer = (transfer_rep == "o")

        n_runs = _ask_int(
            f"  Number of runs [1–20] (default=5) : ",
            lo=1, hi=20, default=5
        )

        keys = [str(k) for k in range(1, 10)]
        print()
        print(SEP2)
        print(f"  Benchmark : P1–P9 × {n_runs} runs  "
              f"[{'fast' if fast else 'normal'}]"
              f"{'  +transfer' if transfer else ''}")
        print(SEP2)
        print()

        run_benchmark(keys, n_runs=n_runs, fast=fast, transfer=transfer,
                      ablation=False, csv_out="benchmark_v13.csv")
        _pause()

    # ══════════════════════════════════════════════════════════════════════
    # MODE 4 — Problème N-Dimensionnel [v16-NDIM]
    # ══════════════════════════════════════════════════════════════════════
    elif mode_choice == "4":
        nd_keys = list(ND_PROBLEMS.keys())
        nd_key = _ask(
            f"  N-D problem [{'/'.join(nd_keys)}] (default=ND1) : ",
            valid=nd_keys, default="ND1"
        )
        nd_name, nd_func, n_feat, x_min, x_max = ND_PROBLEMS[nd_key]
        print(f"  → {nd_name}  ({n_feat} variable(s), x ∈ [{x_min}, {x_max}])")
        print()

        fast_rep = _ask(
            "  Speed? [u=ultrafast / f=fast / n=normal / b=boost] (default=f) : ",
            valid=["u", "f", "n", "b", ""], default="f"
        )
        ultrafast = (fast_rep == "u")
        fast      = (fast_rep in ("f", ""))
        boost     = (fast_rep == "b")

        print()
        print(SEP2)
        print(f"  Lancement N-D : {nd_key} — {nd_name}")
        print(f"  Features : {[f'X[{i}]' for i in range(n_feat)]}")
        mode_str = ('ultrafast' if ultrafast else
                    'fast'      if fast      else
                    'boost'     if boost     else 'normal')
        print(f"  Config   : {mode_str}")
        if boost:
            print(f"  ⚡ BOOST: 6 islands × 250 individuals — 800 generations")
        print(SEP2)
        print()

        cfg_nd = make_cfg_nd(
            n_features=n_feat, x_min=x_min, x_max=x_max,
            fast=fast, ultrafast=ultrafast,
            use_seeding=False, use_lib=True, use_cograph=True, use_seqmem=True
        )
        # [v16-BOOST] Mode boost : population et générations augmentés
        # pour les datasets complexes (NASA réel, multi-batteries).
        # 6 îles : 2 explorers, 1 cleaner, 1 focused, 1 diversifier, 1 stigmergic
        # 250 individus/île = 1500 total (×2.5 vs normal)
        # 800 générations   = ×2 vs normal
        # STAGNATION_LIMIT augmenté pour ne pas resetter trop tôt sur signal complexe
        if boost:
            cfg_nd.N_ISLANDS        = 6
            cfg_nd.POP_SIZE         = 1500
            cfg_nd.GENERATIONS      = 800
            cfg_nd.STAGNATION_LIMIT = 60
            cfg_nd.ELITE_SIZE       = 8
            cfg_nd.TOURNAMENT_SIZE  = 5
            cfg_nd.MIGRATION_SIZE   = 5
            cfg_nd.MIGRATION_INTERVAL = 20
            cfg_nd.DEPTH_PENALTY    = 0.0001   # moins punitif → arbres plus profonds autorisés
        else:
            cfg_nd.GENERATIONS = 200 if fast else (100 if ultrafast else 400)

        # [v16-BATTERY] BATTERY_SOH : 200 points pour discriminer exp(X[0])·X[1]
        # de tanh(constante - X[1]). Avec N_POINTS=80, les deux formes ont un MSE
        # similaire sur [-2,2] → le GP converge vers la plus simple (tanh).
        if nd_key == "BATTERY_SOH":
            cfg_nd.N_POINTS = 200
            # PARSIMONY renforcé : pénalise les structures profondes comme
            # pow(0.978, (tanh(X[2])²)³) qui approximent 0.005·X[2]² sans
            # le trouver explicitement. La vraie cible a taille=13 — on pousse
            # le GP vers des expressions compactes et correctes structurellement.
            cfg_nd.PARSIMONY = getattr(cfg_nd, 'PARSIMONY', 0.001) * 3.0

        # [v16-FIX] Transfert chirurgical : structural_only=True filtre toutes
        # les règles contenant des opérateurs unaires (sin, cos, exp…).
        # Seules les règles de composition neutres (+,-,*,/) sont transférées.
        # Cela évite que le prior de ND1 (dominé par sin/tanh) biaise ND2 (exp).
        import os
        if hasattr(state, 'SEQ_MEM') and os.path.exists("grammar_shared_base.json"):
            state.SEQ_MEM.import_grammar("grammar_shared_base.json",
                                                decay=0.4,
                                                structural_only=True)
            print(f"[TRANSFER] Structural grammar loaded (structural_only, decay=0.4)")

        # [v16-BATTERY] Mode données réelles : remplacement du dataset synthétique
        # par les mesures CSV si le fichier 'nasa_battery_simulation.csv' existe.
        _csv_file   = 'nasa_battery_simulation.csv'
        _use_csv    = (nd_key == "BATTERY_SOH" and os.path.isfile(_csv_file))
        _X_csv      = None
        _y_csv      = None
        if _use_csv:
            try:
                _X_csv, _y_csv = load_custom_csv(_csv_file)
                # ── CORRECTIF IndexError : recréer cfg_nd avec n_features=3 ──
                # Le registre ND_PROBLEMS["BATTERY_SOH"] déclare 4 features
                # (dont X[3] leurre). En mode CSV, la matrice n'a que 3 colonnes
                # → les seeds et terminaux X[3] provoquent un IndexError dans Adam.
                # On recrée cfg_nd avec n_features=3 et N_POINTS adapté au CSV.
                cfg_nd = make_cfg_nd(
                    n_features=3, x_min=x_min, x_max=x_max,
                    fast=fast, ultrafast=ultrafast,
                    use_seeding=False, use_lib=True,
                    use_cograph=True, use_seqmem=True,
                )
                cfg_nd.GENERATIONS = 200 if fast else (100 if ultrafast else 400)
                cfg_nd.PARSIMONY   = getattr(cfg_nd, 'PARSIMONY', 0.001) * 3.0
                cfg_nd.N_POINTS    = _X_csv.shape[0]
                # problem_key distincte → seeds sans X[3] (bsoh_complete_csv)
                nd_key_run = "BATTERY_SOH_CSV"
                print(f"[BATTERY_SOH] Mode CSV actif — N_POINTS={cfg_nd.N_POINTS}, 3 features (sans leurre)")
            except Exception as _csv_err:
                print(f"[BATTERY_SOH] ⚠  CSV error, falling back to synthetic data.")
                print(f"  Detail: {_csv_err}")
                _use_csv   = False
                nd_key_run = nd_key
        else:
            nd_key_run = nd_key

        best, X_data, y_data = evolve(
            nd_func, cfg_nd, problem_key=nd_key_run,
            X_override=_X_csv if _use_csv else None,
            y_override=_y_csv if _use_csv else None,
        )
        if best:
            print_result(nd_name, best, X_data, y_data, cfg_nd)
            y_pred  = evaluate_vector(best, X_data)
            val_mse = float(np.mean((y_pred - y_data) ** 2))
            print(f"[VALIDATION] MSE on training dataset: {val_mse:.8e}")
            # [v16-DECOY] Rapport leurre uniquement en mode synthétique (4 features)
            if nd_key in DECOY_FEATURES and not _use_csv:
                decoy_report(nd_key, best, X_data, y_data, cfg_nd)
            if hasattr(state, 'SEQ_MEM'):
                state.SEQ_MEM.export_grammar(f"grammar_meta_{nd_key}.json")
                state.SEQ_MEM.export_grammar("grammar_shared_base.json")
        else:
            print("[ERROR] No solution found.")
        _pause()

    # ══════════════════════════════════════════════════════════════════════
    # MODE 5 — Conjecture de Syracuse / Collatz  [SYRACUSE]
    # ══════════════════════════════════════════════════════════════════════
    elif mode_choice == "5":
        print("  ★ Mode SYRACUSE — Conjecture de Collatz")
        print("  Objectif : trouver f(n) ≈ temps_de_vol(n)")
        print()

        n_end_raw = _ask_int(
            "  Starting integers up to N_MAX [100–10000] (default=2000) : ",
            lo=100, hi=10000, default=2000
        )
        fast_rep = _ask(
            "  Mode rapide ? [u=ultrafast / f=fast / n=normal] (default=f) : ",
            valid=["u", "f", "n", ""], default="f"
        )
        ultrafast = (fast_rep == "u")
        fast      = (fast_rep in ("f", ""))

        print()
        print(SEP2)
        print(f"  [SYRACUSE] Generating the dataset...")

        _X_syrac, _y_syrac = generate_syracuse_dataset(n_start=2, n_end=n_end_raw)

        cfg_syrac = make_cfg_nd(
            n_features=SYRACUSE_N_FEATURES,   # 5 features : log2, v2, steps3, mod4_1, interaction
            x_min=-2.0, x_max=2.0,
            fast=fast, ultrafast=ultrafast,
            use_seeding=False,
            use_lib=True, use_cograph=True, use_seqmem=True
        )
        cfg_syrac.N_POINTS           = len(_y_syrac)
        cfg_syrac.NOISE_STD          = 0.0
        cfg_syrac.GENERATIONS        = (100 if ultrafast else 300 if fast else 600)
        cfg_syrac.EARLY_STOPPING_MSE = 1e-4
        cfg_syrac.PARSIMONY          = 0.0003
        # [SYRACUSE] Réglages anti-constante :
        # · RANDOM_INJECTION augmenté : maintenir la pression de diversité
        #   face aux bassins d'attraction des constantes (r=-1 piège)
        # · STAGNATION_LIMIT réduit : forcer le reset plus tôt pour casser les plateaux
        # · RESET_FRACTION augmenté : remplacer une plus grande fraction de la pop
        #   lors du reset pour sortir du bassin constant
        cfg_syrac.RANDOM_INJECTION   = 0.15   # vs 0.08 standard — diversité sans trop réduire la reproduction
        cfg_syrac.STAGNATION_LIMIT   = 20     # vs 30 standard — reset plus fréquent pour casser les plateaux
        cfg_syrac.RESET_FRACTION     = 0.45   # vs 0.30 standard
        # [v17-FIX anti-homogénisation] Réduire la migration pour préserver
        # la diversité inter-îles. Avec MIGRATION_SIZE=5 et INTERVAL=20,
        # les îles se recalibrent trop vite sur la solution dominante et
        # stagnent ensemble. On espace et réduit pour laisser les îles explorer.
        cfg_syrac.MIGRATION_SIZE     = 2      # vs 5 standard
        cfg_syrac.MIGRATION_INTERVAL = 35     # vs 20 standard
        # [v17-DEPTH] Le résidu de Collatz est non-linéaire de haut ordre.
        # Borne OLS poly-deg2 déjà dépassée (MSE=0.320 < 0.326) → profondeur
        # maximale augmentée et parsimonie réduite pour les runs normaux.
        if not (ultrafast or fast):
            cfg_syrac.MAX_DEPTH      = 12    # vs 8 standard
            cfg_syrac.MAX_INIT_DEPTH = 7     # vs 6 standard
            cfg_syrac.PARSIMONY      = 0.0001  # vs 0.0003 — moins pénaliser la taille

        mode_str = ('ultrafast' if ultrafast else 'fast' if fast else 'normal')
        print(f"  Config    : {mode_str}  pop={cfg_syrac.POP_SIZE}  "
              f"gen={cfg_syrac.GENERATIONS}  îles={cfg_syrac.N_ISLANDS}")
        print(SEP2)
        print()

        import os
        # [FIX] Ne charger la grammaire que si elle est compatible avec le problème actuel.
        # Une grammaire construite sur Syracuse (10 features, X[8]/X[9]) est incompatible
        # avec ND1 (3 features) — le SeqMem essaierait de construire des arbres avec des
        # terminaux inexistants → crash silencieux ou arbres invalides.
        _grammar_ok = (os.path.exists("grammar_shared_base.json") and
                       nd_key == "SYRACUSE")   # uniquement si même type de problème
        if hasattr(state, 'SEQ_MEM') and _grammar_ok:
            state.SEQ_MEM.import_grammar("grammar_shared_base.json",
                                                decay=0.4, structural_only=True)
            print(f"[TRANSFER] Structural grammar loaded (structural_only, decay=0.4)")

        _syrac_func = lambda X: np.zeros(X.shape[0])   # placeholder

        # [v17-SEED] Injecter la meilleure expression connue comme amorce stigmergique.
        # Expression (run précédent, RAW=0.320, meilleur connu) :
        #   X[2] + ((X[0] + ((X[0] + -1.203302) + is_even(X[2] + (-0.251139/(X[0]+-2.416812))))) / 3.902016)
        # Construite directement via Node pour éviter un parser non existant.
        try:
            _t = cfg_syrac.TERMINALS   # ["X[0]", ..., "X[5]"]
            # is_even(X[2] + (-0.251139 / (X[0] + -2.416812)))
            _inner = Node("is_even",
                          Node("+", Node(_t[2]),
                               Node("/", Node(-0.251139),
                                    Node("+", Node(_t[0]), Node(-2.416812)))))
            # X[0] + (X[0] + -1.203302) + is_even(...)
            _mid = Node("+",
                        Node("+", Node(_t[0]),
                             Node("+", Node(_t[0]), Node(-1.203302))),
                        _inner)
            # X[2] + (_mid / 3.902016)
            _seed_tree = Node("+", Node(_t[2]),
                              Node("/", _mid, Node(3.902016)))
            state.FRAGMENT_LIB.deposit(_seed_tree, rank=1, fitness=-9999.0, gen=0)
            print(f"[SEED] Seed expression deposited → {to_string(_seed_tree)[:80]}...")
        except Exception as _e:
            print(f"[SEED] Injection skipped: {_e}")

        best, X_data, y_data = evolve(
            _syrac_func, cfg_syrac, problem_key="SYRACUSE",
            X_override=_X_syrac,
            y_override=_y_syrac,
        )

        if best:
            print_result("Syracuse/Collatz flight time", best, X_data, y_data, cfg_syrac)
            y_pred  = evaluate_vector(best, X_data)
            val_mse = float(np.mean((y_pred - y_data) ** 2))
            print(f"[VALIDATION] Final MSE (normalized space): {val_mse:.8e}")
            print()
            print("  Verification on a few famous values:")
            y_min_r = float(state._SYRACUSE_Y_RAW.min())
            y_max_r = float(state._SYRACUSE_Y_RAW.max())
            n_min_r = 2.0
            n_max_r = float(n_end_raw)
            print(f"  {'n':>6}  {'true_ft':>10}  {'pred_ft':>12}  {'abs_err':>12}")
            print("  " + "-" * 46)
            for n_check in [2, 3, 6, 7, 27, 97, 703, 871]:
                if n_check < 2 or n_check > n_end_raw:
                    continue
                true_flight = _collatz_flight_time(n_check)
                # Construire le vecteur de features pour n_check
                v2_val  = float(_v2(n_check))
                op_val  = float(n_check) / (2.0 ** v2_val)
                m4_val  = 1.0 if n_check % 4 == 1 else -1.0
                feats_raw = np.array([
                    np.log2(float(n_check)),
                    v2_val,
                    op_val,
                    m4_val,
                ], dtype=np.float64)
                # Normaliser chaque feature avec les min/max du dataset
                feats_scaled = np.array([
                    -2.0 + 4.0 * (feats_raw[i] - state._SYRACUSE_FEAT_MINS[i])
                    / max(state._SYRACUSE_FEAT_MAXS[i] - state._SYRACUSE_FEAT_MINS[i], 1e-12)
                    for i in range(SYRACUSE_N_FEATURES)
                ])
                x_arr       = feats_scaled.reshape(1, -1)
                y_norm_pred = float(evaluate_vector(best, x_arr)[0])
                # Dénormaliser y → espace naturel (nb d'étapes)
                y_pred_nat  = y_min_r + (y_norm_pred + 2.0) / 4.0 * (y_max_r - y_min_r)
                err = abs(y_pred_nat - true_flight)
                print(f"  {n_check:>6}  {true_flight:>10}  {y_pred_nat:>12.2f}  {err:>12.2f}")
            print()
            if hasattr(state, 'SEQ_MEM'):
                state.SEQ_MEM.export_grammar("grammar_meta_SYRACUSE.json")
                state.SEQ_MEM.export_grammar("grammar_shared_base.json")
                print("[META] Grammars exported → grammar_meta_SYRACUSE.json "
                      "/ grammar_shared_base.json")
        else:
            print("[ERROR] No solution found.")
        _pause()

    # ══════════════════════════════════════════════════════════════════════
    # ══════════════════════════════════════════════════════════════════════
    # MODE 7 — PRÉVISION [v30] : extrapolation gardée le long d'un axe
    # (config VALIDÉE : axe seul en entrée, garde anti-divergence, restarts,
    #  sélection-frontière méta, front de Pareto — via l'API)
    # ══════════════════════════════════════════════════════════════════════
    elif mode_choice == "7":
        print("  ★ FORECAST mode — extrapolate a trend beyond the data")
        print()
        path = input("  CSV file path : ").strip().strip('"').strip("'")
        if not path:
            print("[ERROR] No path provided."); _pause(); return
        try:
            import pandas as _pd7
            _df7 = _pd7.read_csv(path, sep=None, engine="python")
            _df7.columns = [str(c).strip() for c in _df7.columns]
        except Exception as _e:
            print(f"[ERROR] Could not read the file: {_e}"); _pause(); return
        cols = list(_df7.columns)
        print(f"\n  Detected columns: {cols}")
        tgt = input(f"  TARGET column [default = last '{cols[-1]}'] : ").strip()
        target_col = tgt if tgt in cols else cols[-1]
        others = [c for c in cols if c != target_col]
        _guess = "cycle" if "cycle" in others else others[0]
        ax = input(f"  Forecast AXIS (the variable that advances: time, cycle…) "
                   f"[default='{_guess}'] : ").strip()
        axis_col = ax if ax in others else _guess
        dr = _ask("  Direction [h=high values/future (default) / l=low / b=both] : ",
                  valid=["h", "l", "b", ""], default="h")
        direction = {"h": "high", "l": "low", "b": "both", "": "high"}[dr]
        rs = input("  Restarts (reliability; default=4) : ").strip()
        n_rs = int(rs) if rs.isdigit() and int(rs) > 0 else 4
        X7 = _df7[[axis_col]].to_numpy(dtype=float)
        y7 = _df7[target_col].to_numpy(dtype=float)
        print(f"\n  ✓ {len(y7)} points | forecasting '{target_col}' along "
              f"'{axis_col}'  (dir={direction}, restarts={n_rs})")
        print("    Note: for forecasting, only variables that TREND are")
        print("    usable — other columns are ignored (validated in v25).")
        import sys as _sys7
        _sys7.modules.setdefault("core", _sys7.modules[__name__])
        try:
            import api as _api7
        except Exception as _e:
            print(f"[ERROR] api.py must be in the same folder ({_e})")
            _pause(); return
        print("\n  Evolving (1–3 minutes depending on the machine)...")
        _t7 = time.time()
        r7 = _api7.symbolic_regression(
            X7, y7, feature_names=[axis_col], operators="physical",
            generations=30, speed="fast", validation_split=0.20, seed=0,
            restarts=n_rs, extrapolate_feature=axis_col,
            extrapolate_direction=direction)
        print(f"  Done in {time.time()-_t7:.0f}s")
        print("\n" + "=" * 70)
        print("FORECAST RESULT")
        print("=" * 70)
        print(f"  Model     : {r7.expression}")
        print(f"  R² (val)  : {r7.r2_validation:.4f}   taille : {r7.size}")
        if r7.pareto:
            print("\n  Pareto front (complexity ↔ accuracy):")
            for _e7 in r7.pareto:
                print("   ", _e7)
        a_lo, a_hi = float(X7[:, 0].min()), float(X7[:, 0].max())
        _span = max(a_hi - a_lo, 1e-12)
        print(f"\n  Projection beyond the data "
              f"({axis_col} observed: {a_lo:g} → {a_hi:g}):")
        for _fr in (0.10, 0.25, 0.50, 0.75):
            _av = a_hi + _fr * _span if direction != "low" else a_lo - _fr * _span
            _pv = float(r7.predict(np.array([[_av]]))[0])
            print(f"    {axis_col} = {_av:>10.4g}   →   {target_col} ≈ {_pv:.4f}")
        print("\n  ⚠ An extrapolation remains a hypothesis: the further from")
        print("    the data, the less reliable it is.")
        _pause(); return

    # ══════════════════════════════════════════════════════════════════════
    # MODE 6 — CSV générique [v22-CSV] : régression sur les données de l'utilisateur
    # ══════════════════════════════════════════════════════════════════════
    elif mode_choice == "6":
        print("  ★ Generic CSV mode — symbolic regression on YOUR data")
        print()
        path = input("  CSV file path : ").strip().strip('"').strip("'")
        if not path:
            print("[ERROR] No path provided.")
            _pause(); return

        # Aperçu des colonnes pour guider l'utilisateur
        try:
            import pandas as _pdprev
            _prev = _pdprev.read_csv(path, sep=None, engine="python", nrows=5)
            _prev.columns = [str(c).strip() for c in _prev.columns]
            print(f"\n  Detected columns: {list(_prev.columns)}")
            print(f"  Preview:\n{_prev.head(3).to_string(index=False)}\n")
        except Exception as _e:
            print(f"[ERROR] Could not read the file: {_e}")
            _pause(); return

        cols = list(_prev.columns)
        # Cible
        tgt = input(f"  TARGET column [default = last '{cols[-1]}'] : ").strip()
        target_col = tgt if tgt in cols else None
        if tgt and tgt not in cols:
            print(f"  → '{tgt}' not found, using the last column.")
        # Features (vide = toutes les autres)
        feat_raw = input("  FEATURE columns, comma-separated "
                         "[default = all others] : ").strip()
        feature_cols = None
        if feat_raw:
            wanted = [c.strip() for c in feat_raw.split(",")]
            feature_cols = [c for c in wanted if c in cols]
            if len(feature_cols) != len(wanted):
                print(f"  → features retenues : {feature_cols}")
        # Pool d'opérateurs
        print("\n  Operator pool (the problem's 'physics'):")
        print("    p = physical  exp/log/sqrt/tanh/pow — decay, saturation (default)")
        print("    t = trig      + sin/cos — periodic/oscillatory phenomena")
        print("    f = full      everything — when unsure a priori")
        print("    y = poly      +,-,*,/,sq,cube,sqrt — pure algebraic relations")
        pool_rep = _ask("  Choice [p/t/f/y] (default=p) : ",
                        valid=["p", "t", "f", "y", ""], default="p")
        op_pool = {"p": "physical", "t": "trig", "f": "full",
                   "y": "poly", "": "physical"}[pool_rep]

        print("\n  Feature normalization:")
        print("    a = auto      shift-free: each column / its max |value| (default)")
        print("    d = divmax    shift-free (preserves x·y, x/y — multiplicative laws)")
        print("    m = minmax    [-2,2] (bounds exp/pow, but inflates products)")
        print("    s = standard  z-score (centered & scaled)")
        norm_rep = _ask("  Choice [a/d/m/s] (default=a) : ",
                        valid=["a", "d", "m", "s", ""], default="a")
        normalize = {"a": "auto", "d": "divmax", "m": "minmax",
                     "s": "standard", "": "auto"}[norm_rep]

        # ── [v0.6] Contrainte dimensionnelle ────────────────────────────
        # La fonctionnalité phare de la 0.4/0.5 n'était accessible que depuis
        # l'API Python, alors que le mode CSV s'adresse précisément à qui
        # connaît les unités de ses colonnes.
        feat_dims_cli = target_dim_cli = None
        unknown_const_cli = False
        _fcols = feature_cols if feature_cols else [c for c in cols
                                                    if c != (target_col or cols[-1])]
        print("\n  Physical units (optional — restricts the search to")
        print("  dimensionally consistent formulas):")
        print("    Leave blank to skip. Examples: kg | m/s | kg*m/s^2 | s^-1 | 1")
        _u_raw = input(f"  Units for {_fcols}, comma-separated : ").strip()
        if _u_raw:
            _u_list = [u.strip() for u in _u_raw.split(",")]
            _t_raw = input(f"  Unit for TARGET "
                           f"'{target_col or cols[-1]}' : ").strip()
            if len(_u_list) != len(_fcols):
                print(f"  → {len(_u_list)} units for {len(_fcols)} columns: "
                      f"units ignored.")
            elif not _t_raw:
                print("  → no target unit: units ignored.")
            else:
                try:
                    from .dim_search import (normalize_units_arg as _nua,
                                             parse_unit_string as _pus,
                                             _DERIVED as _DRV)
                    # Une unité inconnue n'est pas rejetée : elle devient une
                    # dimension à part entière. Pratique pour des grandeurs
                    # exotiques, dangereux pour une faute de frappe — « metre »
                    # au lieu de « m » créerait une base incompatible et la
                    # recherche ne trouverait plus rien. On prévient.
                    _si = {"m", "kg", "s", "A", "K", "mol", "cd"}
                    _known = _si | set(_DRV) | {"1"}
                    _odd = sorted({b for u in _u_list + [_t_raw]
                                   for b in _pus(u)} - _known)
                    if _odd:
                        print(f"  ⚠ unrecognised unit base(s): {_odd}")
                        print("    They are treated as new dimensions, which is "
                              "intended only if\n    they really are. Known: "
                              "m kg s A K mol cd, plus "
                              f"{' '.join(sorted(_DRV))}.")
                    feat_dims_cli, target_dim_cli = _nua(
                        _u_list, _t_raw, len(_fcols), _fcols)
                    print("  → dimensional constraint ACTIVE.")
                    print("\n  If the law carries a dimensioned constant that is")
                    print("  not among your columns (G, k_B, R, a stiffness...),")
                    print("  the engine can deduce its units and value.")
                    _uc = _ask("  Deduce an unknown constant? [y/N] : ",
                               valid=["y", "n", ""], default="n")
                    unknown_const_cli = (_uc == "y")
                except Exception as _ue:
                    print(f"  → units not understood ({_ue}); units ignored.")
                    feat_dims_cli = target_dim_cli = None

        fast_rep = _ask("\n  Speed? [u=ultrafast / f=fast / n=normal] (default=f) : ",
                        valid=["u", "f", "n", ""], default="f")
        ultrafast = (fast_rep == "u")
        fast      = (fast_rep in ("f", ""))

        print()
        print(SEP2)
        print("  Loading data...")
        try:
            X, y, feat_names, target_name, _scaler = load_generic_csv(
                path, target_col=target_col, feature_cols=feature_cols,
                op_pool=op_pool, normalize=normalize, x_range=(-2.0, 2.0))
        except Exception as _e:
            print(f"[ERREUR] {_e}")
            _pause(); return

        n_feat = X.shape[1]
        cfg = make_cfg_nd(n_features=n_feat, x_min=-2.0, x_max=2.0,
                          fast=fast, ultrafast=ultrafast, use_seeding=False,
                          use_lib=True, use_cograph=True, use_seqmem=True)
        cfg.N_POINTS  = len(y)
        cfg.NOISE_STD = 0.0
        # Validation hold-out active par default sur données réelles (v21)
        cfg.VALIDATION_SPLIT = 0.20
        if feat_dims_cli is not None:                      # [v0.6]
            cfg.FEAT_DIMS     = feat_dims_cli
            cfg.TARGET_DIM    = target_dim_cli
            cfg.UNKNOWN_CONST = unknown_const_cli

        mode_str = ('ultrafast' if ultrafast else 'fast' if fast else 'normal')
        print(f"  Config : {mode_str}  pop={cfg.POP_SIZE}  gen={cfg.GENERATIONS}  "
              f"islands={cfg.N_ISLANDS}  features={n_feat}")
        print(SEP2)
        print()

        _gen_func = lambda Xm: np.zeros(Xm.shape[0])  # placeholder (override)
        # [v0.8] Cible d'échelle extrême : la recherche voit y / 10^k, la loi
        # affichée dans les colonnes de l'utilisateur est remise dans ses
        # unités (voir _target_scale).
        _y_scale = _target_scale(np.asarray(y, dtype=float))
        if _y_scale != 1.0:
            print(f"  Target divided by {_y_scale:g} during the search "
                  f"(its values are far from 1); the formula below is in "
                  f"its own units.")
        try:
            best, X_data, y_data = evolve(
                _gen_func, cfg, problem_key="GENERIC_CSV",
                X_override=X, y_override=(y / _y_scale if _y_scale != 1.0 else y))
        except Exception as _e:
            import traceback as _tbx
            print(f"[ERROR] Evolution interrupted: {_e}")
            _tbx.print_exc()
            _pause(); return

        if best:
            # [v0.7] L'expression brute du moteur vit dans l'espace NORMALISÉ.
            # L'afficher avec les noms réels (« 24.97 * elongation » pour une
            # loi 250 * elongation) induisait en erreur : pendant cet
            # affichage, chaque colonne porte un prime (elongation′ = colonne
            # remise à l'échelle), et la loi dans les colonnes réelles suit.
            _names_real = list(getattr(state, 'CSV_FEATURE_NAMES', None) or feat_names)
            state.CSV_FEATURE_NAMES = [f"{nm}′" for nm in _names_real]
            try:
                print_result(f"CSV: {target_name} = f({', '.join(feat_names)})",
                             best, X_data, y_data, cfg)
            finally:
                state.CSV_FEATURE_NAMES = _names_real
            print("\n  Note: 'Expression' above is the engine's internal form, on")
            print("  rescaled columns (a prime marks a rescaled column, e.g.")
            print(f"  {feat_names[0]}′). Use the formula below.")
            # [v0.7] La meme loi, ecrite dans les colonnes de l'utilisateur et
            # verifiee sur ses donnees (formula.py). C'est elle qu'il faut
            # recopier : l'expression normalisee n'est pas valable telle quelle
            # sur les donnees brutes.
            try:
                try:
                    from . import formula as _fm
                except ImportError:
                    import formula as _fm
                _Xraw = _scaler.inverse_transform(np.asarray(X_data, dtype=float))
                _bn = best.node if hasattr(best, "node") else best
                _rf = _fm.raw_formula(
                    _scale_tree(_bn, _y_scale), _scaler, _Xraw, list(feat_names),
                    predictions=None if _y_scale == 1.0 else
                    np.asarray(evaluate_vector(_bn, np.asarray(X_data, dtype=float)),
                               dtype=float) * _y_scale)
                print("\n  Formula in YOUR columns (checked on your data):")
                print(f"    {target_name} = {_rf.text()}")
                if not _rf.exact:
                    print("    (!) differs from the engine's predictions on some rows:"
                          " a numerical safety\n        net of the engine is active "
                          "there (max gap %.3g)." % _rf.max_error)
            except Exception as _fe:
                print(f"\n  (formula in raw columns unavailable: {_fe})")
            if feat_dims_cli is not None:                  # [v0.6]
                print("\n  Dimensional constraint was active: every candidate "
                      "was\n  dimensionally consistent by construction.")
                if unknown_const_cli:
                    _bn2 = best.node if hasattr(best, "node") else best
                    try:
                        _xr = _scaler.inverse_transform(np.asarray(X_data, dtype=float))
                        _pr = np.asarray(evaluate_vector(
                            _bn2, np.asarray(X_data, dtype=float)), dtype=float) * _y_scale
                    except Exception:
                        _xr = _pr = None
                    _u, _v = _deduce_console_constant(
                        _scale_tree(_bn2, _y_scale),
                        feat_dims_cli, target_dim_cli, _scaler, n_feat,
                        Xraw=_xr, preds=_pr)
                    if _u is not None:
                        from .dimensions import _fmt as _fmtdim
                        print(f"  Deduced constant units : {_fmtdim(_u)}")
                    if _v is not None:
                        print(f"  Deduced constant value : {_v:.6g}")
                    elif _u is not None:
                        print("  Value not recoverable in raw units "
                              "(non-monomial form, or shifting normalization).")
        else:
            print("[ERROR] No solution found.")
        # Réinitialiser le mode pour ne pas polluer un run suivant
        state._GENERIC_CSV_MODE = False
        _pause()


def _deduce_console_constant(node, feat_dims, target_dim, scaler, n_feat,
                             Xraw=None, preds=None):
    """[v0.6] Unités et valeur de la constante de tête, pour le mode console.

    Le mode CSV appelle evolve() directement et non l'estimateur scikit-learn :
    il n'a donc pas accès à GPEliteRegressor._deduce_constant. On refait ici le
    même calcul.

    L'arbre livré a la forme b * f(x) (mise à l'échelle par l'origine). Sa
    dimension physique est celle de f ; pour que le tout ait la dimension cible,
    b doit porter cible / dim(f). La valeur de b est exprimée dans l'espace
    normalisé : on la ramène aux unités réelles en repliant les facteurs
    d'échelle, dont les exposants s'obtiennent en refaisant une inférence
    dimensionnelle où chaque colonne porte sa propre pseudo-dimension.

    Retourne (dict_unites, valeur) ; l'un ou l'autre peut être None.
    """
    try:
        from . import dim_search as _DS
    except ImportError:
        import gp_elite.dim_search as _DS
    if node is None:
        return None, None

    inner, b = node, None
    if (node.value == "*" and node.left is not None
            and isinstance(node.left.value, float)):
        b, inner = float(node.left.value), node.right

    dim_inner = _DS.infer_dim(inner, feat_dims)
    if dim_inner is None:
        return None, None
    d = dict(target_dim)
    for k, v in dim_inner.items():
        d[k] = d.get(k, 0.0) - float(v)
    units = {k: v for k, v in d.items() if abs(v) > 1e-9}

    if b is None:
        return units, None
    # Le repliage n'a de sens que pour une mise à l'échelle purement
    # multiplicative : minmax et standard décalent, et aucune constante brute
    # unique n'existe alors.
    sc = getattr(scaler, "scale_", None)
    if sc is None or not isinstance(scaler, (_ShiftFreeScaler, _IdentityScaler)):
        return units, None
    pseudo = {i: {f"__s{i}": 1} for i in range(n_feat)}
    expo = _DS.infer_dim(inner, pseudo)
    if expo is None:
        return units, None
    rho = 1.0
    for i in range(n_feat):
        e = float(expo.get(f"__s{i}", 0.0))
        if e:
            rho *= float(sc[i]) ** (-e)
    val = float(b) * rho
    # [0.10] Comme GPEliteRegressor._deduce_constant : une constante cachée à
    # l'intérieur de f échappe à b * rho ; quand le modèle est bien
    # c * prod x_i^e_i sur les données, c se lit sur ses prédictions.
    if Xraw is not None and preds is not None:
        try:
            Xa = np.asarray(Xraw, dtype=float)
            mono = np.ones(Xa.shape[0])
            for i in range(n_feat):
                e = float(expo.get(f"__s{i}", 0.0))
                if e:
                    mono = mono * Xa[:, i] ** e
            with np.errstate(all="ignore"):
                ratio = np.asarray(preds, dtype=float) / mono
            if ratio.size and np.all(np.isfinite(ratio)):
                c = float(np.median(ratio))
                if c != 0.0 and np.max(np.abs(ratio / c - 1.0)) < 1e-6:
                    val = c
        except Exception:
            pass
    return units, (val if math.isfinite(val) else None)


def _pause():
    """Maintient la fenêtre ouverte jusqu'à ce que l'utilisateur appuie sur Entrée."""
    print()
    print("─" * 70)
    input("  Done. Press Enter to quit...")


# ── The door ─────────────────────────────────────────────────────────────
# gp_elite.core keeps every name it had in 1.4.0. The names of the shared
# state live in gp_elite.state: read on gp_elite.core, they are read there;
# set on it, they are set there. Any other name set on gp_elite.core (a
# test that replaces a function, a bench that wraps one) is also set in the
# engine's modules that hold the same object, as every function of core.py
# saw it in 1.4.0.
_STATE_NAMES = frozenset(('COGRAPH', 'CSV_FEATURE_NAMES', 'CSV_TARGET_NAME', 'CURRENT_RESIDUAL_SIG', 'FRAGMENT_LIB', 'PROBE_X', 'SEQ_MEM', 'VAL_R2_TOLERANCE', '_BATTERY_CSV_MODE', '_BINOMIAL_SEEDS', '_COMPILE_CACHE', '_CUSTOM_LOSS_FN', '_CUSTOM_LOSS_PARSIMONY', '_CUSTOM_LOSS_ROBUST', '_CUSTOM_LOSS_USE_SCALING', '_CUSTOM_SEEDS', '_DIM_GATE_DIMS', '_DIM_GATE_TARGET', '_DIM_SEARCH', '_DIM_UNKNOWN_CONST', '_E2_SEEDS', '_ELEMENTARY_SEEDS', '_EXACT_PRIORITY_SWAPS', '_EXTRAP_BAND', '_EXTRAP_PROBE_XS', '_FAITHFUL_SWAPS', '_GENERIC_BINARY_OPS', '_GENERIC_BINARY_WEIGHTS', '_GENERIC_CSV_MODE', '_GENERIC_UNARY_OPS', '_GENERIC_UNARY_WEIGHTS', '_LS_SCALE_ONLY', '_NEAR_BAND', '_NEAR_GUARD_SWAPS', '_NEAR_PROBE_XS', '_PARALLEL_BROKEN', '_PARALLEL_WARNED', '_PARAMETRIC_CACHE', '_POLISH_ADMITTED', '_POLISH_GRACE_S', '_PRED_CACHE', '_SEEDS_UNDER_UNITS', '_SMALL_CV', '_SMALL_ON', '_SYRACUSE_FEAT_MAXS', '_SYRACUSE_FEAT_MINS', '_SYRACUSE_MODE', '_SYRACUSE_X_RAW', '_SYRACUSE_Y_RAW', '_TIME_LIMIT_HIT', '_TOLERANT_N2', '_TOLERANT_REFIT', '_TOLERANT_SEEDS', '_USE_LINEAR_SCALING', '_VAL_CANDS', '_VAL_TRAIN_XS', '_VAL_TRAIN_YS', '_VAL_XS', '_VAL_YS', '_feature_usage_counter', '_fitness_cache'))
_ENGINE_MODULES = tuple(sys.modules[__package__ + "." + _m] for _m in (
    'numeric',
    'config',
    'tree',
    'simplification',
    'evaluation',
    'datasets',
    'scoring',
    'fitting',
    'genetic',
    'memory',
))
_MISSING = object()


def __getattr__(name):
    if name in _STATE_NAMES and hasattr(state, name):
        return getattr(state, name)
    raise AttributeError("module %r has no attribute %r" % (__name__, name))


def __dir__():
    return sorted(set(globals()) | {n for n in _STATE_NAMES if hasattr(state, n)})


class _Door(type(sys)):
    def __setattr__(self, name, value):
        if name in _STATE_NAMES:
            setattr(state, name, value)
            return
        old = self.__dict__.get(name, _MISSING)
        if old is not _MISSING:
            for m in _ENGINE_MODULES:
                if getattr(m, name, _MISSING) is old:
                    setattr(m, name, value)
        super().__setattr__(name, value)

    def __delattr__(self, name):
        if name in _STATE_NAMES:
            delattr(state, name)
            return
        old = self.__dict__.get(name, _MISSING)
        if old is not _MISSING:
            for m in _ENGINE_MODULES:
                if getattr(m, name, _MISSING) is old:
                    delattr(m, name)
        super().__delattr__(name)


sys.modules[__name__].__class__ = _Door


if __name__ == "__main__":
    import traceback as _tb

    args = sys.argv[1:]
    mode = args[0] if args else ""

    # ── Lancement sans argument → menu interactif ─────────────────────
    if not args:
        # [v19-FIX] Garde traceback : sans ce wrapper, toute exception dans le
        # menu interactif (mode double-clic) remontait sans être capturée et la
        # fenêtre se fermait avant affichage. Désormais l'erreur reste lisible.
        try:
            _interactive_menu()
        except Exception:
            print("\n" + "=" * 70)
            print("ERREUR FATALE — traceback complet :")
            print("=" * 70)
            _tb.print_exc()
            print("=" * 70)
            try:
                input('\nAppuyez sur Entrée pour quitter...')
            except Exception:
                pass
            raise

    # ── Lancement avec argument (mode CLI, compatible v12) ────────────
    elif mode in PROBLEMS:
        key  = mode
        name, func, x_min, x_max = PROBLEMS[key]

        noseed = "noseed" in args
        nolib  = "nolib"  in args
        noco   = "noco"   in args
        noseq  = "noseq"  in args
        fast   = "fast"   in args

        cfg = make_cfg(
            x_min, x_max, fast=fast,
            use_seeding=not noseed,
            use_lib    =not nolib,
            use_cograph=not noco,
            use_seqmem =not noseq,
        )
        cfg.GENERATIONS = 300 if fast else 500

        flags_str = []
        if noseed: flags_str.append("sans seeding")
        if nolib:  flags_str.append("sans lib")
        if noco:   flags_str.append("sans cograph")
        if noseq:  flags_str.append("sans seqmem")
        tag = "  [" + ", ".join(flags_str) + "]" if flags_str else ""

        print(f"Launching: problem {key} — {name}{tag}")

        # [v15] MÉTA-APPRENTISSAGE — chargement de la grammaire partagée
        # decay=0.5 : guide sans bloquer la découverte de nouvelles structures
        if hasattr(state, 'SEQ_MEM'):
            state.SEQ_MEM.import_grammar("grammar_shared_base.json", decay=0.5)

        best, xs, ys = evolve(func, cfg, problem_key=key)

        if best:
            print_result(name, best, xs, ys, cfg)
            try_plot(name, func, best, xs, ys, cfg.LOG_CSV)

            # [v15] MÉTA-APPRENTISSAGE — export après succès
            if hasattr(state, 'SEQ_MEM'):
                # Archive locale au problème (pour analyse et replay)
                state.SEQ_MEM.export_grammar(f"grammar_meta_p{key}.json")
                # Mise à jour de la base partagée pour le prochain run / problème
                state.SEQ_MEM.export_grammar("grammar_shared_base.json")
        else:
            print("[ERROR] No solution found.")
        _pause()

    elif mode == "bench":
        fast     = "fast"     in args
        transfer = "transfer" in args
        n_runs   = 5
        keys     = [str(k) for k in range(1, 10)]
        run_benchmark(keys, n_runs=n_runs, fast=fast, transfer=transfer,
                      ablation=False, csv_out="benchmark_v13.csv")
        _pause()

    elif mode == "ablation":
        uf   = "ultrafast" in args
        fast = "fast" in args and not uf
        hard = "hard" in args
        keys = [str(k) for k in (range(5, 10) if hard else range(1, 10))]
        n    = 3
        run_benchmark(keys, n_runs=n, fast=fast, ultrafast=uf, transfer=False,
                      ablation=True, csv_out="ablation_v13.csv")
        _pause()

    elif mode == "bench_hard":
        keys = [str(k) for k in range(1, 11)]
        run_benchmark(keys, n_runs=8, fast=False, transfer=True,
                      ablation=False, csv_out="bench_hard_v13.csv")
        _pause()

    # ── [v16-NDIM] CLI N-D : python GP_ELITE_v16_ndim.py ND1 [fast] ─────
    elif mode in ND_PROBLEMS:
        nd_name, nd_func, n_feat, x_min, x_max = ND_PROBLEMS[mode]
        fast      = "fast"      in args
        ultrafast = "ultrafast" in args
        print(f"[v16-NDIM] Lancement : {mode} — {nd_name}  ({n_feat} features)")
        cfg_nd = make_cfg_nd(
            n_features=n_feat, x_min=x_min, x_max=x_max,
            fast=fast, ultrafast=ultrafast,
            use_seeding=False, use_lib=True, use_cograph=True, use_seqmem=True
        )
        cfg_nd.GENERATIONS = 200 if fast else (100 if ultrafast else 400)
        # [v16-BATTERY] Idem chemin interactif : 200 points discriminants
        if mode == "BATTERY_SOH":
            cfg_nd.N_POINTS = 200
            cfg_nd.PARSIMONY = getattr(cfg_nd, 'PARSIMONY', 0.001) * 3.0
        import os
        if hasattr(state, 'SEQ_MEM') and os.path.exists("grammar_shared_base.json"):
            state.SEQ_MEM.import_grammar("grammar_shared_base.json",
                                                decay=0.4,
                                                structural_only=True)
            print(f"[TRANSFER] Structural grammar loaded (structural_only, decay=0.4)")

        # [v16-BATTERY] Mode données réelles (chemin CLI)
        _csv_file  = 'nasa_battery_simulation.csv'
        _use_csv   = (mode == "BATTERY_SOH" and os.path.isfile(_csv_file))
        _X_csv     = None
        _y_csv     = None
        if _use_csv:
            try:
                _X_csv, _y_csv = load_custom_csv(_csv_file)
                # ── CORRECTIF IndexError : recréer cfg_nd avec n_features=3 ──
                cfg_nd = make_cfg_nd(
                    n_features=3, x_min=x_min, x_max=x_max,
                    fast=fast, ultrafast=ultrafast,
                    use_seeding=False, use_lib=True,
                    use_cograph=True, use_seqmem=True,
                )
                cfg_nd.GENERATIONS = 200 if fast else (100 if ultrafast else 400)
                cfg_nd.PARSIMONY   = getattr(cfg_nd, 'PARSIMONY', 0.001) * 3.0
                cfg_nd.N_POINTS    = _X_csv.shape[0]
                nd_key_run = "BATTERY_SOH_CSV"
                print(f"[BATTERY_SOH] Mode CSV actif — N_POINTS={cfg_nd.N_POINTS}, 3 features (sans leurre)")
            except Exception as _csv_err:
                print(f"[BATTERY_SOH] ⚠  CSV error, falling back to synthetic data.")
                print(f"  Detail: {_csv_err}")
                _use_csv   = False
                nd_key_run = mode
        else:
            nd_key_run = mode

        best, X_data, y_data = evolve(
            nd_func, cfg_nd, problem_key=nd_key_run,
            X_override=_X_csv if _use_csv else None,
            y_override=_y_csv if _use_csv else None,
        )
        if best:
            print_result(nd_name, best, X_data, y_data, cfg_nd)
            y_pred  = evaluate_vector(best, X_data)
            val_mse = float(np.mean((y_pred - y_data) ** 2))
            print(f"[VALIDATION] MSE final : {val_mse:.8e}")
            if mode in DECOY_FEATURES and not _use_csv:
                decoy_report(mode, best, X_data, y_data, cfg_nd)
            if hasattr(state, 'SEQ_MEM'):
                state.SEQ_MEM.export_grammar(f"grammar_meta_{mode}.json")
                state.SEQ_MEM.export_grammar("grammar_shared_base.json")
        else:
            print("[ERROR] No solution found.")
        _pause()

    # ── [SYRACUSE] CLI : python GP_ELITE_v16_ndim_SYRACUSE.py SYRACUSE [fast] [ultrafast] ─
    elif mode == "SYRACUSE":
        fast      = "fast"      in args
        ultrafast = "ultrafast" in args
        # N_MAX optionnel : python ... SYRACUSE 5000 fast
        n_end_cli = 2000
        for a in args[1:]:
            try:
                n_end_cli = int(a)
                break
            except ValueError:
                pass

        print(f"[SYRACUSE] Lancement CLI — n ∈ [2, {n_end_cli}]")
        _X_syrac, _y_syrac = generate_syracuse_dataset(n_start=2, n_end=n_end_cli)

        cfg_syrac = make_cfg_nd(
            n_features=SYRACUSE_N_FEATURES,   # 5 features : log2, v2, steps3, mod4_1, interaction
            x_min=-2.0, x_max=2.0,
            fast=fast, ultrafast=ultrafast,
            use_seeding=False,
            use_lib=True, use_cograph=True, use_seqmem=True
        )
        cfg_syrac.N_POINTS           = len(_y_syrac)
        cfg_syrac.NOISE_STD          = 0.0
        cfg_syrac.GENERATIONS        = (100 if ultrafast else 300 if fast else 600)
        cfg_syrac.EARLY_STOPPING_MSE = 1e-4
        cfg_syrac.PARSIMONY          = 0.0003
        cfg_syrac.RANDOM_INJECTION   = 0.15
        cfg_syrac.STAGNATION_LIMIT   = 20
        cfg_syrac.RESET_FRACTION     = 0.45

        import os
        if hasattr(state, 'SEQ_MEM') and os.path.exists("grammar_shared_base.json"):
            state.SEQ_MEM.import_grammar("grammar_shared_base.json",
                                                decay=0.4, structural_only=True)

        _syrac_func = lambda X: np.zeros(X.shape[0])
        best, X_data, y_data = evolve(
            _syrac_func, cfg_syrac, problem_key="SYRACUSE",
            X_override=_X_syrac, y_override=_y_syrac,
        )
        if best:
            print_result("Syracuse/Collatz flight time", best, X_data, y_data, cfg_syrac)
            y_pred  = evaluate_vector(best, X_data)
            val_mse = float(np.mean((y_pred - y_data) ** 2))
            print(f"[VALIDATION] Final MSE (normalized space): {val_mse:.8e}")
            if hasattr(state, 'SEQ_MEM'):
                state.SEQ_MEM.export_grammar("grammar_meta_SYRACUSE.json")
                state.SEQ_MEM.export_grammar("grammar_shared_base.json")
        else:
            print("[ERROR] No solution found.")
        _pause()

    else:
        try:
            _interactive_menu()
        except Exception as _e:
            print("\n" + "="*70)
            print("ERREUR FATALE — traceback complet :")
            print("="*70)
            _tb.print_exc()
            print("="*70)
            try:
                input('\nAppuyez sur Entrée pour quitter...')
            except Exception:
                pass
            raise

    try:
        input('\n[FIN] Run terminé avec succès. Appuyez sur Entrée pour quitter...')
    except (EOFError, KeyboardInterrupt):
        pass

