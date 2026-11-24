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
from .final_choice import (_EXACT_REL, _FAITHFUL_CACHE, _FINAL_LM_ITER,
                           _NEAR_CACHE, _NEAR_EXT, _NEAR_K, _PATIENCE_GAIN,
                           _Patience, _SMALL_CANDS, _SMALL_CANDS_MAX,
                           _SMALL_FAMILY, _SMALL_FAMILY_KEEP,
                           _SMALL_FAMILY_SHARE, _SMALL_FINALISTS, _SMALL_FOLDS,
                           _SMALL_FRONT, _SMALL_MIN_ROWS, _SMALL_ROWS,
                           _SMALL_SEARCH, _VAL_CANDS_MAX, _WEIGHTED_SUMS_MAX,
                           _build_near_probes, _early_stop_threshold,
                           _finalists, _formula_faithful, _has_scale,
                           _holdout_mse, _is_numerically_stable,
                           _lm_to_convergence, _near_domain_stable,
                           _polish_finalists, _refit_scaling, _select_one_se,
                           _small_choose, _small_cv, _small_fit,
                           _small_is_const, _small_materialize, _small_n_par,
                           _small_round_powers, _small_setup, _small_specs,
                           _small_strip, _small_table_select, _track_if_exact,
                           _track_small_candidate, _track_val_candidate,
                           _weight_sums)
from .seeds import (_BINOM_EXPS, _BINOM_GRID, _BINOM_GRID_ROWS, _BINOM_MAX_LIB,
                    _BINOM_TOL, _E2_CURVE, _E2_C_GRID, _E2_GATE, _ELEM_MAX_LIB,
                    _ELEM_S_GRID, _ELEM_TRIG_GATE, _ELEM_W_GRID,
                    _POWER_LAW_MIN_R2, _POWER_TOL, _SCAN_KEEP, _TOLERANT_MAX,
                    _TOLERANT_REL, _binom_library, _binomial_forms,
                    _e2_residuals, _elem_aexp_forms, _elem_flib,
                    _elem_inverse_forms, _elem_inverse_forms_w, _elem_log_scan,
                    _elem_mono, _elem_rel, _elem_transform, _elem_trig_exact,
                    _elem_trig_forms, _elem_trig_grid, _elem_wrel,
                    _elementary_forms, _elementary_forms_n2, _golden_min,
                    _half_integer_power, _log_g_exponents,
                    _make_binomial_seeds, _make_elementary_seeds,
                    _make_motif_seeds, _make_power_law_seeds,
                    _make_tolerant_seeds, _monomial, _power_law_exponents,
                    _power_law_exponents_w, _pred_rel_error, _product,
                    _refit_inner, _seed_rel_error, _seeds_blocked_by_units,
                    _small_family, _typed_seeds)
from .islands import (Island, _PW, _smart_reset_explorers, evolve_island,
                      migrate)
from .parallel import (_POOL_CHILD_ENV, _SkipLogExport, _evolve_parallel,
                       _exit_if_reimported_by_worker, _island_round_task,
                       _parallel_enabled, _parallel_worker_init, _pool_probe,
                       _warn_unguarded_main)
from .search import (_make_linear_candidate, _split_holdout, evolve)
from .data import (ND_PROBLEMS, PROBLEMS, SCALE_RATIO_THRESHOLD,
                   _IdentityScaler, _MinMaxScaler, _ND_UNARY_WEIGHTS_INIT,
                   _ShiftFreeScaler, _choose_scaler, _csv_deps, _csv_deps_ok,
                   _safe_sinc, _scale_ratio, load_custom_csv, load_generic_csv)
from .console import (_ask, _ask_int, _deduce_console_constant,
                      _interactive_menu, _one_run, _pause, _print_menu,
                      decoy_report, print_result, run, run_benchmark, try_plot)


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
    'final_choice',
    'seeds',
    'islands',
    'parallel',
    'search',
    'data',
    'console',
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

