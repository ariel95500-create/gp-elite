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
    'final_choice',
    'seeds',
    'islands',
    'parallel',
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

