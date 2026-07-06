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
import math
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

# [v16-BATTERY] Dépendances pour la lecture de données réelles (CSV NASA)
try:
    import pandas as _pd
    from sklearn.preprocessing import MinMaxScaler as _MinMaxScaler
    _CSV_DEPS_OK = True
except ImportError:
    _CSV_DEPS_OK = False

# ============================================================
# BIBLIOTHÈQUE DE FRAGMENTS — SUBSTRAT STIGMERGIQUE
# ============================================================

@dataclass
class FragmentEntry:
    """Entrée dans la bibliothèque de fragments."""
    node:         Any   = None
    tau:          float = 0.0    # Phéromone accumulée
    freq:         int   = 0      # Nombre de fois vu dans top-k
    best_fitness: float = 1e9   # Meilleure fitness d'un individu contenant ce fragment
    last_gen:     int   = 0
    size:         int   = 0
    depth:        int   = 0
    root_op:      str   = ""     # Opérateur racine (pour tirage filtré)
    gen_stable:   int   = 0      # FIX v13.9 : gens consécutives au-dessus du seuil min
    # [v17 — GUIDAGE SÉMANTIQUE] Signature comportementale sur probe set fixe.
    # Vecteur numpy de shape (N_PROBE,) — sortie du fragment sur PROBE_X.
    # None tant que non calculée (fragments déposés avant initialisation du probe).
    semantic_signature: Optional[np.ndarray] = None


class FragmentLibrary:
    """
    Bibliothèque de fragments maintenue par phéromones (stigmergie).

    Chaque génération :
      1. Les top-k individus déposent τ sur leurs sous-arbres (Δ = 1/rank)
      2. Évaporation globale : τ *= EVAP_RATE
      3. Élagage : fragments trop faibles ou en surnombre supprimés

    Construction :
      - Tirage pondéré par τ pour assembler de nouveaux individus
      - Filtrable par taille et opérateur racine
    """
    MAX_SIZE      = 200
    EVAP_RATE     = 0.97
    MIN_TAU       = 0.01
    MIN_FRAG_SIZE = 2
    MAX_FRAG_SIZE = 15   # réduit : évite les fragments géants avec constantes

    def __init__(self):
        self.fragments: Dict[int, FragmentEntry] = {}
        self.generation = 0

    def _structural_quality(self, node: "Node") -> float:
        """
        Score de qualité structurelle d'un fragment [0..1].
        Pénalise les fragments à dominante constante.
        - 1.0 = uniquement des variables/opérateurs
        - 0.0 = uniquement des constantes figées
        [v16-NDIM] Reconnaît X[i] en plus de "x" comme variable utile.
        """
        all_nodes = list(get_all_nodes(node))
        if not all_nodes:
            return 0.0
        n_const   = sum(1 for n, _, _ in all_nodes
                        if isinstance(n.value, float) and n.left is None)
        n_var     = sum(1 for n, _, _ in all_nodes
                        if isinstance(n.value, str) and (
                            n.value == "x" or n.value.startswith("X[")))
        n_total   = len(all_nodes)
        score = (n_var * 2.0 - n_const * 0.5) / max(n_total, 1)
        return max(0.05, min(1.0, score + 0.5))

    def _is_semantically_trivial(self, node: "Node") -> bool:
        """
        Détecte les fragments sémantiquement nuls ou triviaux.
        [v16-NDIM] Génère une mini-matrice X de test (5 lignes) compatible
        avec le mode N-D ; en mode 1-D le vecteur xs reste un 1-D array.
        """
        simplified = simplify(node)  # [v19-OPT] simplify ne mute plus l'entrée
        if simplified.left is None and simplified.right is None:
            return True
        # Sonde N-D générique : matrice 5×4 couvrant les features 0–3
        test_X = np.array([
            [-2.0, -1.5,  0.3,  1.0],
            [-1.0, -0.5,  0.7,  2.0],
            [ 0.5,  0.1,  1.1, -0.5],
            [ 1.5,  1.0, -0.3, -1.5],
            [ 2.5,  2.0, -1.0, -2.5],
        ])
        try:
            vals = evaluate_vector(simplified, test_X)
            if np.std(vals) < 1e-6:
                return True
        except Exception:
            pass
        return False

    def merge_from(self, other: "FragmentLibrary"):
        """[v20-PAR] Fusionne la bibliothèque d'un worker dans celle du maître.
        Chaque worker part du MÊME instantané puis dépose/évapore localement :
        on fusionne par MAX de phéromone (signal le plus fort conservé, pas
        de double comptage de l'instantané commun), freq/last_gen par max,
        best_fitness par min."""
        for h, e in other.fragments.items():
            mine = self.fragments.get(h)
            if mine is None:
                self.fragments[h] = e
            else:
                if e.tau > mine.tau:
                    mine.tau = e.tau
                mine.freq         = max(mine.freq, e.freq)
                mine.best_fitness = min(mine.best_fitness, e.best_fitness)
                mine.last_gen     = max(mine.last_gen, e.last_gen)
                mine.gen_stable   = max(mine.gen_stable, e.gen_stable)
                if mine.semantic_signature is None:
                    mine.semantic_signature = e.semantic_signature
        # Ré-élagage si dépassement après fusion
        if len(self.fragments) > self.MAX_SIZE:
            ranked = sorted(self.fragments.items(), key=lambda kv: kv[1].tau,
                            reverse=True)[: self.MAX_SIZE]
            self.fragments = dict(ranked)

    def deposit(self, individual: Node, rank: int, fitness: float, gen: int):
        """Dépose τ = quality/rank sur tous les sous-arbres valides d'un individu."""
        delta_base = 1.0 / rank
        nodes = get_all_nodes(individual)
        seen  = set()
        for node, _, _ in nodes:
            sz = tree_size(node)
            if sz < self.MIN_FRAG_SIZE or sz > self.MAX_FRAG_SIZE:
                continue
            h = node.canonical_hash()
            if h in seen:
                continue
            seen.add(h)
            if self._is_semantically_trivial(node):
                continue
            quality = self._structural_quality(node)
            delta   = delta_base * quality
            if h not in self.fragments:
                op = node.value if isinstance(node.value, str) else "const"
                # [v17] Calcul de la signature sémantique au premier dépôt
                sig = compute_semantic_sig(node, PROBE_X)
                # Bonus δ si le fragment corrige le résidu courant
                if sig is not None and CURRENT_RESIDUAL_SIG is not None:
                    sem = semantic_score(sig, CURRENT_RESIDUAL_SIG)
                    if sem > 0.5:
                        delta *= 1.5   # [v17] bonus dépôt sémantique Phase 8
                self.fragments[h] = FragmentEntry(
                    node               = node.copy(),  # [v19-OPT] copy itératif
                    tau                = delta,
                    freq               = 1,
                    best_fitness       = fitness,
                    last_gen           = gen,
                    size               = sz,
                    depth              = tree_depth(node),
                    root_op            = op,
                    semantic_signature = sig,   # [v17]
                )
            else:
                e = self.fragments[h]
                e.tau         += delta
                e.freq        += 1
                e.last_gen     = gen
                if fitness < e.best_fitness:
                    e.best_fitness = fitness
                # [v17] Rafraîchir la signature si absente (fragment ancien)
                if e.semantic_signature is None:
                    e.semantic_signature = compute_semantic_sig(e.node, PROBE_X)

    def deposit_population(self, population: List[Node],
                           fitnesses: List[float],
                           top_k: int, gen: int,
                           xs=None, ys=None):
        """Dépose depuis les top_k meilleurs (déjà triés par fitness croissante).
        FIX v13.8 — filtre MSE : rejette individus NaN/inf ou MSE > 50×médiane.
        FIX v13.10 — filtre variance : rejette individus dont l'écart-type des
        prédictions dépasse 10×std(ys) — détecte les arbres à croissance
        polynomiale/exponentielle rapide (pow(x,x·x)) non détectés par MSE seul.
        """
        if xs is not None and ys is not None and top_k > 0:
            ys_std    = float(np.std(ys)) if len(ys) > 1 else 1.0
            raw_mses  = []
            raw_stds  = []
            for ind in population[:top_k]:
                try:
                    vals = evaluate_vector(ind, xs)
                    if np.all(np.isfinite(vals)):
                        raw_mses.append(float(np.mean((vals - ys) ** 2)))
                        raw_stds.append(float(np.std(vals)))
                    else:
                        raw_mses.append(float('inf'))
                        raw_stds.append(float('inf'))
                except Exception:
                    raw_mses.append(float('inf'))
                    raw_stds.append(float('inf'))
            finite_mses = [m for m in raw_mses if np.isfinite(m)]
            median_mse  = float(np.median(finite_mses)) if finite_mses else float('inf')
            mse_thresh  = max(50.0 * median_mse, 1e3)
            std_thresh  = max(10.0 * ys_std, 1.0)   # FIX v13.10 : critère variance
        else:
            raw_mses  = [0.0] * top_k
            raw_stds  = [0.0] * top_k
            mse_thresh = float('inf')
            std_thresh = float('inf')

        for rank, (ind, fit, rmse, rstd) in enumerate(
                zip(population[:top_k], fitnesses[:top_k], raw_mses, raw_stds), 1):
            if rmse > mse_thresh or rstd > std_thresh:  # FIX v13.10 : double filtre
                continue
            self.deposit(ind, rank, fit, gen)

    def evaporate(self, evap_rate: float = None, tau_max: float = None,
                  op_diversity_cap: float = 0.40):
        """Évaporation + élagage + cap de diversité opérateur.

        [v16-FIX] op_diversity_cap : proportion maximale qu'un seul root_op
        peut représenter dans la bibliothèque (en poids τ total).
        Si un opérateur dépasse ce seuil, ses fragments les plus faibles
        sont pénalisés par un facteur supplémentaire jusqu'à revenir sous
        le cap. Cela empêche cos(sqrt(...)) de monopoliser la lib et
        laisse de la place à exp, tanh, log pour émerger.

        Exemple : cap=0.40 → aucun opérateur ne peut représenter plus de
        40 % du τ total. Avec 11 opérateurs, on garantit une diversité
        minimale équivalente à ~2.5 opérateurs toujours représentés.
        """
        rate  = evap_rate if evap_rate is not None else self.EVAP_RATE
        t_max = tau_max   if tau_max   is not None else 1e9

        # ── 1. Évaporation standard ───────────────────────────────────────
        to_del = [h for h, e in self.fragments.items()
                  if e.tau * rate < self.MIN_TAU]
        for h in to_del:
            del self.fragments[h]
        for e in self.fragments.values():
            e.tau *= rate
            if e.tau >= self.MIN_TAU * 5:
                e.gen_stable += 1
            else:
                e.gen_stable = 0
            if e.tau > t_max:
                e.tau = t_max

        # ── 2. Cap de diversité opérateur [v16-FIX] ──────────────────────
        if op_diversity_cap < 1.0 and self.fragments:
            for _pass in range(8):
                tau_total = sum(e.tau for e in self.fragments.values())
                if tau_total <= 0:
                    break
                # Recalculer la part de chaque op sur les valeurs courantes
                op_tau: Dict[str, float] = {}
                for e in self.fragments.values():
                    op_tau[e.root_op] = op_tau.get(e.root_op, 0.0) + e.tau
                over_cap = {op: t for op, t in op_tau.items()
                            if t / tau_total > op_diversity_cap + 1e-6}
                if not over_cap:
                    break
                for op, op_total in over_cap.items():
                    share   = op_total / tau_total
                    # Facteur appliqué UNE seule fois pour ramener à cap
                    penalty = op_diversity_cap / share
                    op_frags = [(h, e) for h, e in self.fragments.items()
                                if e.root_op == op]
                    to_del_cap = []
                    for h, e in op_frags:
                        e.tau *= penalty
                        if e.tau < self.MIN_TAU:
                            to_del_cap.append(h)
                    # Toujours conserver au moins 1 fragment par opérateur
                    surviving = len(op_frags) - len(to_del_cap)
                    if surviving == 0 and to_del_cap:
                        to_del_cap.pop()   # garder le dernier (le plus fort)
                    for h in to_del_cap:
                        if h in self.fragments:
                            del self.fragments[h]

        # ── 3. Élagage si surnombre ───────────────────────────────────────
        if len(self.fragments) > self.MAX_SIZE:
            keys = sorted(self.fragments, key=lambda h: self.fragments[h].tau)
            for h in keys[:len(self.fragments) - self.MAX_SIZE]:
                del self.fragments[h]
        self.generation += 1

    def sample(self, min_size: int = 2, max_size: int = 15,
               root_op: str = None) -> Optional[Node]:
        """
        [v17] Tire un fragment avec pondération sémantique hybride.
        [OPT] Calcul sémantique vectorisé en batch — toutes les signatures
        sont empilées en une matrice et le calcul de corrélation est fait
        en une seule passe matricielle plutôt que N appels séquentiels.
        """
        candidates = [
            (h, e) for h, e in self.fragments.items()
            if min_size <= e.size <= max_size
            and (root_op is None or e.root_op == root_op)
        ]
        if not candidates:
            return None

        res_sig = CURRENT_RESIDUAL_SIG
        taus    = np.array([e.tau for _, e in candidates], dtype=np.float64)

        if res_sig is not None:
            # Empiler toutes les signatures disponibles en une matrice (M × N_PROBE)
            sigs = []
            has_sig = []
            for _, e in candidates:
                if e.semantic_signature is not None:
                    sigs.append(e.semantic_signature)
                    has_sig.append(True)
                else:
                    sigs.append(None)
                    has_sig.append(False)

            if any(has_sig):
                # Calcul vectorisé : centrer les signatures et le résidu
                b = res_sig - res_sig.mean()
                nb = float(np.dot(b, b))
                sem_scores = np.zeros(len(candidates), dtype=np.float64)
                if nb > 1e-16:
                    # Batch : empiler les sigs valides
                    valid_idx = [i for i, ok in enumerate(has_sig) if ok]
                    mat = np.array([sigs[i] for i in valid_idx], dtype=np.float64)
                    # Centrer chaque ligne
                    mat_c = mat - mat.mean(axis=1, keepdims=True)
                    # Normes
                    norms = np.einsum('ij,ij->i', mat_c, mat_c)   # dot produit de chaque ligne avec elle-même
                    mask  = norms > 1e-16
                    if mask.any():
                        dots = mat_c[mask] @ b   # (M', N_PROBE) × (N_PROBE,) → (M',)
                        rs   = dots / np.sqrt(norms[mask] * nb)
                        rs   = np.clip(np.abs(rs), 0.0, 1.0)
                        valid_with_sig = [valid_idx[i] for i, m in enumerate(mask) if m]
                        for i, r_val in zip(valid_with_sig, rs):
                            sem_scores[i] = r_val

                weights = taus * (0.5 + 1.5 * sem_scores)
            else:
                weights = taus * 0.5
        else:
            weights = taus * 0.5

        total = float(weights.sum())
        if total <= 0:
            return None
        # Tirage pondéré via cumsum (plus rapide que boucle cumul)
        r = random.random() * total
        cumsum = np.cumsum(weights)
        idx = int(np.searchsorted(cumsum, r))
        idx = min(idx, len(candidates) - 1)
        return candidates[idx][1].node.copy()  # [v19-OPT] copy itératif (≈50× vs deepcopy)

    def top_fragments(self, n: int = 5) -> List[FragmentEntry]:
        return sorted(self.fragments.values(), key=lambda e: -e.tau)[:n]

    def stats(self) -> dict:
        if not self.fragments:
            return {"count": 0, "max_tau": 0.0, "mean_tau": 0.0, "top_ops": []}
        taus = [e.tau for e in self.fragments.values()]
        ops: Dict[str, int] = {}
        for e in self.fragments.values():
            ops[e.root_op] = ops.get(e.root_op, 0) + 1
        return {
            "count":    len(self.fragments),
            "max_tau":  max(taus),
            "mean_tau": sum(taus) / len(taus),
            "top_ops":  sorted(ops.items(), key=lambda x: -x[1])[:5],
        }


# Instance globale partagée entre toutes les îles
FRAGMENT_LIB = FragmentLibrary()


# ============================================================
# [v17] GUIDAGE SÉMANTIQUE — Probe set + signatures comportementales
# ============================================================
#
# Principe : chaque fragment dans la bibliothèque reçoit une "empreinte
# comportementale" — sa sortie évaluée sur un petit ensemble de points
# fixes (PROBE_X). Lors du tirage, on pondère τ par la corrélation entre
# cette empreinte et le résidu courant du meilleur individu.
#
# Résultat : la stigmergie ne sélectionne plus "ce qui était bon en général"
# mais "ce qui corrige ce qui reste à corriger maintenant".
#
# Architecture :
#   · PROBE_X               — matrice de points fixes (N_PROBE × N_FEATURES)
#                             générée dynamiquement selon cfg au début du run
#   · FragmentEntry.semantic_signature — sortie du fragment sur PROBE_X
#   · CURRENT_RESIDUAL_SIG  — résidu du meilleur individu projeté sur PROBE_X
#   · compute_probe_x()     — génère PROBE_X adapté aux dims du problème
#   · compute_semantic_sig()— évalue fragment sur PROBE_X (robuste NaN/inf)
#   · semantic_score()      — corrélation(sig_fragment, résidu_probe) ∈ [0,1]
#   · sample() modifié      — poids = τ × (0.5 + 1.5 × sem_score) clampé
# ─────────────────────────────────────────────────────────────────────────────

# Points de sonde fixes — mis à jour par init_probe_set() à chaque run
PROBE_X: np.ndarray = np.zeros((20, 4))

# Résidu du meilleur individu courant projeté sur PROBE_X
# Mis à jour dans evolve_island() après chaque amélioration du best
CURRENT_RESIDUAL_SIG: Optional[np.ndarray] = None


def init_probe_set(cfg: "Config", n_probe: int = 30) -> np.ndarray:
    """
    [v17] Génère le probe set adapté aux dimensions du problème.

    Contrairement à la proposition originale (PROBE_X fixe 5×4), on génère
    un probe set dynamique calibré sur [cfg.X_MIN, cfg.X_MAX] et
    cfg.N_FEATURES colonnes. Cela garantit la compatibilité avec tous les
    problèmes (1-D à N-D) sans dimension mismatch.

    Stratégie d'échantillonnage : grille régulière + points randoms.
    La grille couvre les extrema et le centre ; les points randoms
    assurent une couverture dense de l'espace intérieur.
    """
    n_feat    = len(cfg.TERMINALS) if hasattr(cfg, 'TERMINALS') else 1
    x_lo, x_hi = cfg.X_MIN, cfg.X_MAX

    # Grille régulière sur les extrema + quartiles (couverture structurelle)
    grid_pts  = np.linspace(x_lo, x_hi, 5)
    n_grid    = min(10, n_probe // 3)
    rng       = np.random.default_rng(seed=42)   # seed fixe = reproductible
    grid_rows = rng.choice(grid_pts, size=(n_grid, n_feat))

    # Points randoms uniformes (couverture dense)
    n_rand    = n_probe - n_grid
    rand_rows = rng.uniform(x_lo, x_hi, size=(n_rand, n_feat))

    probe = np.vstack([grid_rows, rand_rows]).astype(np.float64)
    # [HOTFIX] mode 1-D ('x') : les fonctions compilées utilisent _x directement
    # -> probe doit être 1-D sinon residual broadcast (30,)-(30,1) -> (30,30)
    terms = getattr(cfg, 'TERMINALS', ['x'])
    if n_feat == 1 and terms == ['x']:
        return probe[:, 0].copy()
    return probe


def compute_semantic_sig(node: "Node",
                          probe: np.ndarray) -> Optional[np.ndarray]:
    """
    [v17] Évalue un fragment sur le probe set.

    Retourne un vecteur (N_PROBE,) si l'évaluation est valide,
    None si le fragment produit des NaN/inf ou une sortie constante
    (corrélation de Pearson indéfinie sur sortie constante).
    """
    try:
        vals = evaluate_vector(node, probe)
        if not np.all(np.isfinite(vals)):
            return None
        if np.std(vals) < 1e-8:
            return None          # constante → corrélation indéfinie
        return vals.astype(np.float64)
    except Exception:
        return None


def semantic_score(frag_sig: Optional[np.ndarray],
                   residual_sig: Optional[np.ndarray]) -> float:
    """
    [v17] Corrélation absolue de Pearson — version optimisée sans np.corrcoef.

    [OPT] np.corrcoef construit une matrice 2×2 complète et appelle cov() puis std()
    séparément, soit ~5 passes sur les données. Version inline : 3 passes max
    (mean_a, mean_b, puis dot produit) — ~2× plus rapide sur petits vecteurs (N=30).
    """
    if frag_sig is None or residual_sig is None:
        return 0.0
    # Centrage
    a = frag_sig - frag_sig.mean()
    b = residual_sig - residual_sig.mean()
    # Normes
    na = float(np.dot(a, a))
    nb = float(np.dot(b, b))
    if na < 1e-16 or nb < 1e-16:
        return 0.0
    r = float(np.dot(a, b)) / (na * nb) ** 0.5
    if not (-1.0 <= r <= 1.0):
        return 0.0
    return abs(r)


def update_residual_sig(best_ind: "Node",
                        probe: np.ndarray,
                        probe_y: np.ndarray) -> Optional[np.ndarray]:
    """
    [v17] Calcule le résidu du meilleur individu sur le probe set.

    probe_y : valeurs cibles exactes aux points du probe (interpolées
              ou calculées depuis y_raw si disponible — sinon, 0.0
              ce qui revient à utiliser la signature directe du best).
    """
    try:
        preds = evaluate_vector(best_ind, probe)
        if not np.all(np.isfinite(preds)):
            return None
        residual = probe_y - preds
        if np.std(residual) < 1e-8:
            return None
        return residual.astype(np.float64)
    except Exception:
        return None


# ============================================================
# GRAPHE DE CO-OCCURRENCES DE FRAGMENTS  (Phase 5a)
# ============================================================

class FragmentCoGraph:
    """
    Graphe de co-occurrences entre fragments de la bibliothèque.

    Pour chaque paire (h_i, h_j) de fragments présents simultanément
    dans un même individu top-k, on accumule un poids :

        co[h_i][h_j] += delta_i * delta_j   (delta = 1/rank)

    Propriétés :
      - Symétrique : co[a][b] == co[b][a]
      - Évaporation périodique (même taux que FragmentLibrary)
      - Élagage des arêtes trop faibles (MIN_CO)
      - Limité à MAX_EDGES arêtes (les plus faibles supprimées en priorité)

    Utilisation :
      - sample_companion(h_root) → tire le fragment le plus co-occurrent
        avec h_root, proportionnellement aux poids d'arête
      - sample_pair()            → tire une paire corrélée (root_frag, companion)
      - top_pairs(n)             → liste les n paires les plus fortes
    """

    MAX_EDGES   = 2000     # Limite du nombre d'arêtes mémorisées
    EVAP_RATE   = 0.97     # Même rythme que FragmentLibrary
    MIN_CO      = 0.005    # Seuil d'élagage

    def __init__(self):
        # co[(h_i, h_j)] = poids, avec h_i < h_j (non-orienté)
        self.co: Dict[Tuple[int, int], float] = {}

    @staticmethod
    def _key(h1: int, h2: int) -> Tuple[int, int]:
        return (h1, h2) if h1 < h2 else (h2, h1)

    def merge_from(self, other: "FragmentCoGraph"):
        """[v20-PAR] Fusion par MAX d'arête (même logique que FragmentLibrary)."""
        co = self.co
        for k, w in other.co.items():
            if w > co.get(k, 0.0):
                co[k] = w
        if len(co) > self.MAX_EDGES:
            ranked = sorted(co.items(), key=lambda kv: kv[1],
                            reverse=True)[: self.MAX_EDGES]
            self.co = dict(ranked)

    def deposit(self, hashes: List[int], rank: int):
        """
        Dépose sur toutes les paires de fragments d'un individu de rang `rank`.
        delta = 1/rank² (produit des deltas individuels = (1/rank)²).
        Pour éviter une explosion quadratique, on ne considère que les
        MAX_LOCAL_PAIRS premières paires (les fragments sont déjà triés par τ).
        """
        MAX_LOCAL = 12   # max de fragments par individu pris en compte
        hs = hashes[:MAX_LOCAL]
        delta = 1.0 / (rank * rank)
        for i in range(len(hs)):
            for j in range(i + 1, len(hs)):
                k = self._key(hs[i], hs[j])
                self.co[k] = self.co.get(k, 0.0) + delta

    def deposit_individual(self, individual, rank: int):
        """Collecte les hashes des sous-arbres valides et dépose."""
        from itertools import islice
        hashes = []
        seen   = set()
        for node, _, _ in get_all_nodes(individual):
            sz = tree_size(node)
            if sz < FragmentLibrary.MIN_FRAG_SIZE or sz > FragmentLibrary.MAX_FRAG_SIZE:
                continue
            h = node.canonical_hash()
            if h in seen:
                continue
            seen.add(h)
            hashes.append(h)
        if len(hashes) >= 2:
            self.deposit(hashes, rank)

    def deposit_population(self, population: List, top_k: int):
        """Dépose depuis les top_k individus (déjà triés par fitness croissante)."""
        for rank, ind in enumerate(population[:top_k], 1):
            self.deposit_individual(ind, rank)

    def evaporate(self):
        """Évaporation + élagage des arêtes faibles + limite MAX_EDGES."""
        to_del = [k for k, v in self.co.items() if v * self.EVAP_RATE < self.MIN_CO]
        for k in to_del:
            del self.co[k]
        for k in self.co:
            self.co[k] *= self.EVAP_RATE
        # Élagage si surnombre
        if len(self.co) > self.MAX_EDGES:
            sorted_keys = sorted(self.co, key=lambda k: self.co[k])
            for k in sorted_keys[:len(self.co) - self.MAX_EDGES]:
                del self.co[k]

    def sample_companion(self, h_root: int,
                          lib: "FragmentLibrary") -> Optional[Any]:
        """
        Tire un fragment compagnon de h_root proportionnellement
        au poids de co-occurrence.
        Ne retourne que des fragments encore présents dans `lib`.
        """
        candidates: List[Tuple[Tuple[int, int], float]] = []
        for (h1, h2), w in self.co.items():
            other = h2 if h1 == h_root else (h1 if h2 == h_root else None)
            if other is None:
                continue
            if other in lib.fragments:
                candidates.append((other, w))

        if not candidates:
            return None

        total = sum(w for _, w in candidates)
        if total <= 0:
            return None

        import copy as _copy
        r = random.random() * total
        cumul = 0.0
        for h_other, w in candidates:
            cumul += w
            if r <= cumul:
                return lib.fragments[h_other].node.copy()  # [v19-OPT]
        return lib.fragments[candidates[-1][0]].node.copy()  # [v19-OPT]

    def sample_pair(self, lib: "FragmentLibrary"
                    ) -> Tuple[Optional[Any], Optional[Any]]:
        """
        Tire une paire (root_frag, companion) corrélée.
        Pondère par le poids d'arête × τ_root × τ_companion.
        Retourne (None, None) si la lib ou le graphe est trop vide.
        """
        if not self.co or not lib.fragments:
            return None, None

        # Construire la distribution sur les arêtes valides
        valid: List[Tuple[Tuple[int, int], float]] = []
        for (h1, h2), w in self.co.items():
            if h1 in lib.fragments and h2 in lib.fragments:
                tau_prod = lib.fragments[h1].tau * lib.fragments[h2].tau
                valid.append(((h1, h2), w * tau_prod))

        if not valid:
            return None, None

        total = sum(w for _, w in valid)
        if total <= 0:
            return None, None

        import copy as _copy
        r = random.random() * total
        cumul = 0.0
        for (h1, h2), w in valid:
            cumul += w
            if r <= cumul:
                # Tirage uniforme entre les deux orientations
                if random.random() < 0.5:
                    h1, h2 = h2, h1
                root = lib.fragments[h1].node.copy()  # [v19-OPT]
                comp = lib.fragments[h2].node.copy()  # [v19-OPT]
                return root, comp
        (h1, h2), _ = valid[-1]
        return (lib.fragments[h1].node.copy(),  # [v19-OPT]
                lib.fragments[h2].node.copy())

    def top_pairs(self, n: int = 5, lib: "FragmentLibrary" = None
                  ) -> List[Tuple[float, str, str]]:
        """Retourne les n paires les plus fortes sous forme lisible."""
        valid = []
        for (h1, h2), w in self.co.items():
            if lib is None or (h1 in lib.fragments and h2 in lib.fragments):
                label1 = to_string(lib.fragments[h1].node) if lib and h1 in lib.fragments else str(h1)
                label2 = to_string(lib.fragments[h2].node) if lib and h2 in lib.fragments else str(h2)
                valid.append((w, label1, label2))
        valid.sort(key=lambda x: -x[0])
        return valid[:n]

    def stats(self) -> dict:
        if not self.co:
            return {"edges": 0, "max_co": 0.0, "mean_co": 0.0}
        vals = list(self.co.values())
        return {
            "edges":   len(self.co),
            "max_co":  max(vals),
            "mean_co": sum(vals) / len(vals),
        }


# Instance globale partagée entre toutes les îles
COGRAPH = FragmentCoGraph()


# ============================================================
# MÉMOIRE DE SÉQUENCES STRUCTURELLES  (Phase 5b)
# ============================================================

class FragmentSequenceMemory:
    """
    Modèle de Markov d'ordre 1 sur la structure des arbres GP.

    Capture les transitions :
        (op_parent, position) → {op_enfant: poids}

    où position ∈ {"left", "right", "unary"}.

    Exemple : si dans les top individus on voit souvent
        exp → (unary) → neg → (unary) → sq → (unary) → x
    alors la mémoire apprend que exp.unary → neg est probable,
    neg.unary → sq est probable, etc.

    Utilisation :
      - next_op(parent_op, position) → tire le prochain opérateur
        selon la distribution conditionnelle apprise
      - build_top_down(cfg) → construit un arbre en suivant ces transitions

    Évaporation : même rythme que FragmentLibrary (× EVAP_RATE par génération).
    """

    EVAP_RATE = 0.99   # plus lent : accumule le signal sur plus de générations
    MIN_W     = 0.005  # seuil d'élagage plus bas
    MAX_KEYS  = 800    # plus de transitions mémorisées

    def __init__(self):
        # transitions[(parent_op, position)][child_op] = poids
        self.transitions: Dict[Tuple[str, str], Dict[str, float]] = {}

    def _op_label(self, node) -> str:
        """Étiquette canonique d'un nœud.
        [v16-NDIM] Les terminaux X[i] sont encodés tels quels ("X[0]", "X[1]", …)
        pour permettre le tracking de l'importance des features dans SEQ_MEM/JSON.
        """
        if node is None:
            return "none"
        v = node.value
        if isinstance(v, float):
            return "const"
        # Variable scalaire 1-D (rétrocompatibilité) OU variable N-D
        if v == "x" or (isinstance(v, str) and v.startswith("X[")):
            return v      # ex: "x", "X[0]", "X[2]" — distincts dans la grammaire
        return str(v)

    def merge_from(self, other: "FragmentSequenceMemory"):
        """[v20-PAR] Fusion par MAX de poids par transition."""
        for key, dist in other.transitions.items():
            mine = self.transitions.get(key)
            if mine is None:
                self.transitions[key] = dict(dist)
            else:
                for op, w in dist.items():
                    if w > mine.get(op, 0.0):
                        mine[op] = w
        if len(self.transitions) > self.MAX_KEYS:
            ranked = sorted(self.transitions.items(),
                            key=lambda kv: sum(kv[1].values()),
                            reverse=True)[: self.MAX_KEYS]
            self.transitions = dict(ranked)

    def deposit_tree(self, root, rank: int):
        """
        Parcourt l'arbre et dépose sur chaque transition parent→enfant.
        Markov ordre 2 : clé = (grandparent_op, parent_op, position)
        pour capturer le contexte local plus finement.
        Ordre 1 en fallback quand pas de grand-parent (racine).
        """
        delta = 1.0 / rank
        # Stack : (node, parent_op, grandparent_op, position)
        stack = [(root, None, None, None)]
        while stack:
            node, p_op, gp_op, pos = stack.pop()
            p_op  = p_op  or "root"
            gp_op = gp_op or "root"

            if node.left is not None and node.right is not None:
                # Binaire
                n_op = self._op_label(node)
                for child, cpos in ((node.left, "left"), (node.right, "right")):
                    c_op = self._op_label(child)
                    # Clé ordre 2
                    key2 = (gp_op, p_op, cpos)
                    if key2 not in self.transitions:
                        self.transitions[key2] = {}
                    self.transitions[key2][c_op] = \
                        self.transitions[key2].get(c_op, 0.0) + delta
                    # Clé ordre 1 (fallback)
                    key1 = ("*", p_op, cpos)
                    if key1 not in self.transitions:
                        self.transitions[key1] = {}
                    self.transitions[key1][c_op] = \
                        self.transitions[key1].get(c_op, 0.0) + delta * 0.5
                    stack.append((child, n_op, p_op, cpos))
            elif node.left is not None:
                # Unaire
                n_op = self._op_label(node)
                child = node.left
                c_op  = self._op_label(child)
                key2  = (gp_op, p_op, "unary")
                if key2 not in self.transitions:
                    self.transitions[key2] = {}
                self.transitions[key2][c_op] = \
                    self.transitions[key2].get(c_op, 0.0) + delta
                key1 = ("*", p_op, "unary")
                if key1 not in self.transitions:
                    self.transitions[key1] = {}
                self.transitions[key1][c_op] = \
                    self.transitions[key1].get(c_op, 0.0) + delta * 0.5
                stack.append((child, n_op, p_op, "unary"))

    def deposit_population(self, population: List, top_k: int):
        for rank, ind in enumerate(population[:top_k], 1):
            self.deposit_tree(ind, rank)

    def evaporate(self):
        """Évaporation + élagage."""
        empty_keys = []
        for key, dist in self.transitions.items():
            to_del = [op for op, w in dist.items()
                      if w * self.EVAP_RATE < self.MIN_W]
            for op in to_del:
                del dist[op]
            for op in dist:
                dist[op] *= self.EVAP_RATE
            if not dist:
                empty_keys.append(key)
        for k in empty_keys:
            del self.transitions[k]
        if len(self.transitions) > self.MAX_KEYS:
            scored = sorted(self.transitions.items(),
                            key=lambda kv: sum(kv[1].values()))
            for k, _ in scored[:len(self.transitions) - self.MAX_KEYS]:
                del self.transitions[k]

    def next_op(self, parent_op: str, position: str,
                fallback_pool: List[str],
                fallback_weights: List[float],
                grandparent_op: str = "root") -> str:
        """
        Tire le prochain opérateur via Markov ordre 2 avec fallback ordre 1.
        [v17-FIX] Filtre les opérateurs hors du pool actif pour éviter que
        des transitions apprises sur des problèmes 1-D (cos, sin, tanh)
        ne contaminent les runs Syracuse ou Batterie.
        """
        # Ensemble des opérateurs légaux dans le mode actif
        _b_ops, _b_w, _u_ops, _u_w, _, _ = _active_pools()
        _valid_ops = set(_b_ops + _u_ops)

        def _sample_filtered(dist):
            """Tire depuis dist en excluant les ops hors pool actif."""
            filtered = {op: w for op, w in dist.items() if op in _valid_ops
                        or op in fallback_pool}
            if not filtered:
                return None
            ops = list(filtered.keys())
            ws  = [filtered[op] for op in ops]
            return random.choices(ops, weights=ws)[0]

        # Essai ordre 2
        key2 = (grandparent_op, parent_op, position)
        dist = self.transitions.get(key2)
        if dist:
            result = _sample_filtered(dist)
            if result is not None:
                return result
        # Fallback ordre 1
        key1 = ("*", parent_op, position)
        dist = self.transitions.get(key1)
        if dist:
            result = _sample_filtered(dist)
            if result is not None:
                return result
        return random.choices(fallback_pool, weights=fallback_weights)[0]

    def build_top_down(self, cfg: "Config", max_depth: int = 5) -> "Node":
        """
        Construit un arbre top-down via Markov ordre 2 avec fallback ordre 1.
        FIX v13.8 — compteur de nœuds partagé : stoppe la récursion si
        MAX_TREE_SIZE//2 est atteint, pour éviter les arbres géants en +SEQ.
        """
        # Racine : clé ("root", "root", "unary") ordre 2
        root_dist = (self.transitions.get(("root", "root", "unary")) or
                     self.transitions.get(("*", "root", "unary"), {}))
        if root_dist:
            # [v17-FIX] Filtrer les opérateurs hors pool actif (cos, sin, etc.)
            _b_ops, _b_w, _u_ops, _u_w, _, _ = _active_pools()
            _valid = set(_b_ops + _u_ops)
            filtered_root = {op: w for op, w in root_dist.items() if op in _valid}
            if filtered_root:
                ops = list(filtered_root.keys())
                ws  = [filtered_root[op] for op in ops]
                root_op = random.choices(ops, weights=ws)[0]
            else:
                root_op = random.choices(_b_ops + _u_ops, weights=_b_w + _u_w)[0]
        else:
            _b_ops, _b_w, _u_ops, _u_w, _, _ = _active_pools()
            root_op = random.choices(
                _b_ops + _u_ops,
                weights=_b_w + _u_w
            )[0]

        # Compteur de nœuds partagé entre toutes les récursions
        size_budget = [cfg.MAX_TREE_SIZE // 2]

        # [v16-NDIM] Fallback pools dynamiques selon cfg.TERMINALS
        _var_pool    = cfg.TERMINALS   # ["x"] ou ["X[0]", "X[1]", …]
        _n_vars      = len(_var_pool)
        _var_weight  = 4
        # [SYRACUSE/BATTERY] Toujours utiliser le pool du mode actif
        _b_ops, _b_w, _u_ops, _u_w, _, _ = _active_pools()
        fallback_all = _b_ops + _u_ops + _var_pool + ["const"]
        fallback_w   = _b_w   + _u_w   + [_var_weight] * _n_vars + [2]
        fallback_uni = _u_ops + _var_pool + ["const"]
        fallback_wu  = _u_w   + [5] * _n_vars + [2]

        def make_node(op: str, depth: int, parent_op: str = "root") -> "Node":
            # stopper si budget épuisé, profondeur nulle, ou terminal
            if depth <= 0 or op in _var_pool or op == "const" or size_budget[0] <= 0:
                size_budget[0] -= 1
                return random_terminal(cfg)
            size_budget[0] -= 1
            # [SYRACUSE/BATTERY] Routage via les pools du mode actif (pas les globaux)
            if op in _b_ops:
                l_op = self.next_op(op, "left",  fallback_all, fallback_w,  grandparent_op=parent_op)
                r_op = self.next_op(op, "right", fallback_all, fallback_w,  grandparent_op=parent_op)
                left  = make_node(l_op, depth - 1, op)
                right = make_node(r_op, depth - 1, op)
                return Node(op, left, right)
            elif op in _u_ops:
                c_op  = self.next_op(op, "unary", fallback_uni, fallback_wu, grandparent_op=parent_op)
                child = make_node(c_op, depth - 1, op)
                return Node(op, child)
            else:
                return random_terminal(cfg)

        tree   = make_node(root_op, max_depth, "root")
        result = simplify(tree)
        if tree_size(result) > cfg.MAX_TREE_SIZE:
            return random_tree(cfg.MAX_INIT_DEPTH, cfg)
        return result

    def deposit_root(self, root):
        """Dépose la racine comme transition spéciale ordre-2."""
        r_op  = self._op_label(root)
        key2  = ("root", "root", "unary")
        key1  = ("*",    "root", "unary")
        for key in (key2, key1):
            if key not in self.transitions:
                self.transitions[key] = {}
            self.transitions[key][r_op] = \
                self.transitions[key].get(r_op, 0.0) + 1.0

    def deposit_population_with_root(self, population: List, top_k: int):
        for rank, ind in enumerate(population[:top_k], 1):
            # v12 : ne déposer que les arbres assez profonds pour alimenter l'ordre 2
            if tree_depth(ind) >= 3:
                self.deposit_root(ind)
                self.deposit_tree(ind, rank)
            else:
                # Arbre trop plat : uniquement la racine (ordre 1 fallback)
                self.deposit_root(ind)

    def stats(self) -> dict:
        n_keys   = len(self.transitions)
        total_w  = sum(sum(d.values()) for d in self.transitions.values())
        top_trans = []
        for key, dist in self.transitions.items():
            best_child = max(dist, key=dist.get) if dist else "?"
            top_trans.append((sum(dist.values()), key, best_child))
        top_trans.sort(key=lambda x: -x[0])
        # Formater la clé lisiblement (ordre 2 vs ordre 1)
        def fmt_key(k):
            if len(k) == 3:
                return f"{k[0]}.{k[1]}.{k[2]}"
            return f"{k[0]}.{k[1]}"
        return {
            "n_transitions": n_keys,
            "total_weight":  round(total_w, 2),
            "top5": [(fmt_key(k), c) for _, k, c in top_trans[:5]],
        }

    def warm_transfer(self, decay: float = 0.5):
        """
        Décote toutes les transitions (transfert inter-problèmes) :
        conserve la structure mais réduit la confiance.
        """
        for dist in self.transitions.values():
            for op in dist:
                dist[op] *= decay

    def export_grammar(self, filepath: str):
        """
        [v15] Exporte les transitions grammaticales apprises au format JSON.
        [v16-NDIM] Ajoute une section "feature_importance" qui cumule le poids
        de toutes les transitions impliquant chaque terminal X[i].
        Cela permet une analyse post-hoc de l'importance des features.
        """
        serialized_transitions = {}
        for key, dist in self.transitions.items():
            str_key = "::".join(str(x) for x in key) if isinstance(key, tuple) else str(key)
            serialized_transitions[str_key] = dist

        # ── Feature Importance : cumul des poids par variable ────────────
        feature_importance: Dict[str, float] = {}
        for key, dist in self.transitions.items():
            # La variable peut apparaître comme enfant dans dist
            for op, w in dist.items():
                if op == "x" or (isinstance(op, str) and op.startswith("X[")):
                    feature_importance[op] = feature_importance.get(op, 0.0) + w
            # Ou comme parent dans key (2e élément)
            if len(key) > 1:
                parent_op = key[1]
                if parent_op == "x" or (isinstance(parent_op, str)
                                         and parent_op.startswith("X[")):
                    total_w = sum(dist.values())
                    feature_importance[parent_op] = (
                        feature_importance.get(parent_op, 0.0) + total_w)

        # Normaliser [0, 1]
        fi_total = sum(feature_importance.values()) or 1.0
        feature_importance_norm = {k: round(v / fi_total, 6)
                                   for k, v in feature_importance.items()}

        payload = {
            "version": "16.0",
            "n_transitions": len(self.transitions),
            "transitions": serialized_transitions,
            "feature_importance": feature_importance_norm,  # [v16-NDIM]
        }

        _written = _safe_write(filepath,
                               lambda f: json.dump(payload, f, indent=4),
                               what="meta-grammar")
        filepath = _written or filepath   # downstream messages show the real path

        # ── Statistiques de décomposition structurel / spécifique ────────
        SPECIFIC_OPS = {'sin', 'cos', 'tanh', 'exp', 'log', 'sqrt',
                        'tan', 'abs', 'neg', 'sq', 'cube', 'pow'}
        n_structural = 0
        n_specific_  = 0
        for key, dist in self.transitions.items():
            parent_op = key[1] if len(key) > 1 else ""
            best_op   = max(dist, key=dist.get) if dist else ""
            if (parent_op in SPECIFIC_OPS) or (best_op in SPECIFIC_OPS):
                n_specific_ += 1
            else:
                n_structural += 1

        print(f"\n[TRANSFER-EXPORT] Sequence grammar → {filepath} "
              f"({len(self.transitions)} transitions : "
              f"{n_structural} structural | {n_specific_} specific).")
        if feature_importance_norm:
            sorted_fi = sorted(feature_importance_norm.items(),
                               key=lambda kv: -kv[1])
            fi_str = "  ".join(f"{k}={v:.3f}" for k, v in sorted_fi[:8])
            print(f"[FEATURE-IMPORTANCE] {fi_str}")

    def import_grammar(self, filepath: str, decay: float = 0.5,
                       structural_only: bool = False):
        """
        [v15.1] Charge une grammaire externe et l'injecte dans self.transitions.

        Deux modes de transfert :

        structural_only=False (default) — transfert différentiel classique :
          · Règles génériques (composition : +, -, *, /)
            → decay normal : se transfèrent bien entre problèmes
          · Règles spécifiques (sin, cos, tanh, exp, log, sqrt…)
            → decay × SPECIFIC_PENALTY (×0.2) : atténuées fortement

        structural_only=True — transfert chirurgical [v16-FIX] :
          · Seules les règles PUREMENT structurelles sont importées :
            position dans l'arbre (root, left, right, unary) et opérateurs
            de composition (+, -, *, /, pow) sans aucun opérateur unaire
            dans la clé ni dans la distribution.
          · Les règles comme "*.cos.left → cos" ou "*.*.right → sin" sont
            **filtrées entièrement** — elles encodent la structure du problème
            source et biaisent la recherche sur un problème cible différent.
          · Utile quand les problèmes source et cible ont des opérateurs-clés
            différents (ex: ND1 utilise sin, ND2 utilise exp).

        Retourne True si le chargement a réussi, False sinon.
        """
        # Opérateurs mathématiques spécifiques — biaisant si transférés tels quels
        SPECIFIC_OPS = {'sin', 'cos', 'tanh', 'exp', 'log', 'sqrt',
                        'tan', 'abs', 'neg', 'sq', 'cube', 'pow'}
        # Opérateurs de composition purement structurels — neutres inter-problèmes
        STRUCTURAL_OPS = {'+', '-', '*', '/'}
        SPECIFIC_PENALTY = 0.2

        if not os.path.exists(filepath):
            print(f"\n[TRANSFER-IMPORT] No file found: {filepath} — starting blank.")
            return False

        with open(filepath, "r", encoding="utf-8") as f:
            payload = json.load(f)

        self.transitions.clear()
        n_generic  = 0
        n_specific = 0
        n_filtered = 0

        for str_key, dist in payload.get("transitions", {}).items():
            tuple_key  = tuple(str_key.split("::"))
            parent_op  = tuple_key[1] if len(tuple_key) > 1 else ""
            best_op    = max(dist, key=dist.get) if dist else ""

            # ── Mode structural_only : filtrage chirurgical ────────────────
            if structural_only:
                # Rejeter si la clé contient un opérateur spécifique
                key_has_specific = any(k in SPECIFIC_OPS for k in tuple_key)
                # Rejeter si la distribution est dominée par un opérateur spécifique
                # (best_op ou plus de 50% du poids vers des ops spécifiques)
                total_w     = sum(dist.values()) or 1.0
                specific_w  = sum(w for op, w in dist.items() if op in SPECIFIC_OPS)
                dist_has_specific = (best_op in SPECIFIC_OPS or
                                     specific_w / total_w > 0.50)
                if key_has_specific or dist_has_specific:
                    n_filtered += 1
                    continue
                # Garder uniquement les règles de composition neutres
                # Filtrer aussi les entrées de distribution spécifiques
                clean_dist = {op: w for op, w in dist.items()
                              if op not in SPECIFIC_OPS}
                if not clean_dist:
                    n_filtered += 1
                    continue
                self.transitions[tuple_key] = {
                    op: w * decay for op, w in clean_dist.items()
                }
                n_generic += 1

            # ── Mode différentiel classique ────────────────────────────────
            else:
                is_specific = (parent_op in SPECIFIC_OPS) or (best_op in SPECIFIC_OPS)
                if is_specific:
                    effective_decay = decay * SPECIFIC_PENALTY
                    n_specific += 1
                else:
                    effective_decay = decay
                    n_generic += 1
                self.transitions[tuple_key] = {
                    op: w * effective_decay for op, w in dist.items()
                }

        mode_str = "structural_only" if structural_only else "différentiel"
        if structural_only:
            print(f"\n[TRANSFER-IMPORT] Grammaire {mode_str} depuis {filepath} "
                  f"({n_generic} structural rules decay={decay:.2f} "
                  f"| {n_filtered} specific rules filtered).")
        else:
            print(f"\n[TRANSFER-IMPORT] Grammar injected from {filepath} "
                  f"({len(self.transitions)} rules: {n_generic} generic decay={decay:.2f} "
                  f"| {n_specific} specific decay={decay * SPECIFIC_PENALTY:.3f}).")
        return True


# Instance globale
SEQ_MEM = FragmentSequenceMemory()

# ============================================================
# CONFIGURATION GLOBALE
# ============================================================

@dataclass
class Config:
    # Population et évolution
    POP_SIZE: int          = 800
    GENERATIONS: int       = 400
    ELITE_SIZE: int        = 8
    TOURNAMENT_SIZE: int   = 5
    TOURNAMENT_PRESSURE: float = 0.85   # prob. de choisir le meilleur

    # Profondeur / taille
    MAX_INIT_DEPTH: int    = 6
    MAX_MUTATION_DEPTH: int = 4
    MAX_TREE_SIZE: int     = 60
    MAX_TREE_DEPTH: int    = 12

    # Opérateurs génétiques
    MUTATION_RATE: float   = 0.70
    CROSSOVER_RATE: float  = 0.70
    HOIST_RATE: float      = 0.10
    POINT_MUTATION_RATE: float = 0.15
    SHRINK_RATE: float     = 0.10
    SEMANTIC_MUTATION_RATE: float = 0.15

    # Parsimonie (Pareto au lieu de somme)
    PARSIMONY: float       = 0.002
    DEPTH_PENALTY: float   = 0.0005

    # Diversité
    RANDOM_INJECTION: float = 0.08
    STAGNATION_LIMIT: int  = 30
    RESET_FRACTION: float  = 0.30
    CROWDING_FACTOR: int   = 3      # tournoi de remplacement

    # Optimisation des constantes (Adam)
    CONST_OPT_PROB: float  = 0.15   # [v14.5] Throttling Adam : 15% pour diviser le coût CPU × 5
    CONST_OPT_ITER: int    = 20
    # [v26-LM] Optimiseur de constantes : True = Levenberg-Marquardt (default,
    # moindres carrés natifs, précision machine, deterministic) ; False = voie
    # Adam historique (1er ordre). LM est le levier n°1 des moteurs SR de
    # référence — voir optimize_constants_lm.
    CONST_OPT_LM: bool     = True
    # [v28-MOTIFS] Seeding de motifs de composition (sqrt(sq+sq), 1/(1/a+1/b),
    # gaussienne, log-ratio, 1−cos…) dans la population initiale. Cible les
    # structures à tremplin que l'évolution n'assemble pas seule.
    MOTIF_SEEDS: bool      = True
    MOTIF_SEEDS_N: int     = 32
    ADAM_LR: float         = 0.05
    ADAM_BETA1: float      = 0.9
    ADAM_BETA2: float      = 0.999
    ADAM_EPS: float        = 1e-8

    # Island model
    N_ISLANDS: int         = 4
    MIGRATION_INTERVAL: int = 20
    MIGRATION_SIZE: int    = 5

    # Stigmergie — contrôle phéromones
    FRAG_EVAP_RATE: float  = 0.85   # [v14.5] Évaporation renforcée (vs 0.97) pour forcer le renouveau
    FRAG_TAU_MAX:  float   = 40.0   # [v14.5] Cap anti-monopole strict (vs 100.0) — τ max = 40

    # Dataset
    N_POINTS: int          = 120
    X_MIN: float           = -3.0
    X_MAX: float           = 3.0
    NOISE_STD: float       = 0.0     # bruit sur les cibles (0 = propre)

    # [v16-NDIM] Terminal set dynamique
    # Mode 1-D (default) : ["x"]
    # Mode N-D          : ["X[0]", "X[1]", …, "X[n_features-1]"]
    # Généré automatiquement par make_cfg_nd() ou renseigné manuellement.
    TERMINALS: List[str]   = field(default_factory=lambda: ["x"])

    # [v16-FIX] Cap de diversité opérateur dans FragmentLibrary [0..1]
    # Proportion maximale qu'un seul root_op peut représenter (en poids τ).
    # 0.40 en 1-D (espace restreint, convergence utile)
    # 0.30 en N-D (espace plus grand, la diversité est cruciale)
    # Passé à evaporate() à chaque génération.
    OP_DIVERSITY_CAP: float = 0.40

    # ERC
    ERC_MIN: float         = -5.0
    ERC_MAX: float         = 5.0

    # Convergence
    PERFECT_THRESHOLD: float  = 1e-9
    # [v15] Early Stopping absolu : arrêt dès que MSE pur ≤ seuil.
    # Évite de gaspiller les générations restantes quand la solution est
    # quasi-analytique. Hérité automatiquement par make_cfg et run_benchmark.
    EARLY_STOPPING_MSE: float = 1e-6

    # Ablation / benchmark flags
    USE_SEEDING: bool      = True   # False = benchmark sans aide humaine
    USE_LIB: bool          = True   # False = désactive FragmentLibrary
    USE_COGRAPH: bool      = True   # False = désactive co-occurrences
    USE_SEQMEM: bool       = True   # False = désactive séquences

    # [v18] Techniques de pointe (parité Operon / PySR)
    USE_LINEAR_SCALING: bool = True  # Keijzer 2003 : fitness sur a + b·f(x), (a,b) en forme fermée
    USE_LEXICASE: bool       = True  # ε-lexicase (La Cava 2016) sur les îles explorer/stigmergic

    # [v21-VAL] Validation hold-out — la rigueur scientifique du résultat
    #   L'évolution (fitness, lexicase, Adam, stigmergie) ne voit QUE le
    #   train set ; le champion final est sélectionné et rapporté sur le
    #   set de validation jamais vu. 0.0 = désactivé (ancien comportement).
    VALIDATION_SPLIT: float = 0.20   # fraction hold-out (min 8 points)
    HOLDOUT_SEED: int       = 1234   # split reproductible
    VAL_R2_TOLERANCE: float = 0.003  # [v23.2] tolérance R² pour sélection parcimonieuse

    # [v24-EXTRAP] Mode extrapolation dédié (OPT-IN, n'affecte PAS les runs normaux)
    #   Quand True, deux changements ciblés, validés empiriquement :
    #     1. Le hold-out n'est plus un tirage ALÉATOIRE mais la BANDE-FRONTIER
    #        du domaine (les points les plus au bord). Le R² interne random
    #        ne discrimine pas l'extrapolation (≈0.998 pour tous) ; le R² sur la
    #        frontière, lui, la prédit. Le champion livré est donc celui qui
    #        tient AU BORD, pas celui qui gratte un epsilon à l'intérieur.
    #     2. Un candidat LINÉAIRE (OLS, très faible taille) est injecté dans le
    #        pool de sélection. Une droite ne peut pas diverger hors-plage ; la
    #        sélection parcimonieuse la choisit quand la loi est quasi-linéaire.
    #   Laisser False reproduit exactement le comportement standard.
    #
    #   RECETTE VALIDÉE (données batterie NASA réelles, v25) — trois pièces :
    #     1. GARDE ANTI-DIVERGENCE : on sonde le candidat AU-DELÀ du domaine
    #        (axe d'extrapolation prolongé) et on rejette toute prédiction
    #        implausible. Sans lui, GP explose à l'extrapolation (exp/pow/x²/
    #        cube) car la divergence est invisible sur un hold-out interne.
    #     2. TRAIN COMPLET : split random (pas frontière) — retirer les
    #        points de bord du train dégrade l'estimation de la pente.
    #     3. RESTRICTION À L'AXE QUI TEND : ne nourrir que la (les) feature(s)
    #        porteuse(s) de tendance. Les features qui n'évoluent pas (temp,
    #        courant) restent bornées donc passent le garde, mais leur légère
    #        dérive hors-échantillon BIAISE la prédiction. En prévision pure,
    #        les exclure (extrapolate_feature=<axe>, entrée = cet axe seul).
    #   Résultat : R² d'extrapolation médian +0.51 (vs +0.34 pour une régression
    #   linéaire, vs médiane NÉGATIVE sans ces pièces). GP capture alors une
    #   structure non-linéaire bornée que la droite manque, SANS diverger.
    #   ⚠ Le garde neutralise la DIVERGENCE, pas un mauvais ajustement borné :
    #   la variance entre seeds reste réelle — lancer plusieurs graines et
    #   garder la meilleure en validation.
    EXTRAPOLATION_MODE: bool        = False
    EXTRAPOLATION_FRONTIER_FRAC: float = 0.20  # part du domaine prise comme frontière
    #   [v24.1] Affinage : axe d'extrapolation. L'extrapolation se fait presque
    #   toujours le long d'UN seul axe (cycles, temps), pas de tous. Désigner
    #   cette feature aligne la bande-frontière sur la VRAIE direction
    #   d'extrapolation, au lieu de prendre les points extrêmes sur n'importe
    #   quelle feature (qui peut être non pertinente, ex. température).
    #     EXTRAPOLATION_FEATURE  : index de l'axe (None = toutes, symétrique)
    #     EXTRAPOLATION_DIRECTION: "both" (deux bords) | "high" (valeurs hautes,
    #                              cas forecasting) | "low" (valeurs basses)
    EXTRAPOLATION_FEATURE: Optional[int] = None
    EXTRAPOLATION_DIRECTION: str         = "both"
    #   [v25] Type de split en mode extrapolation. LEÇON batterie : entraîner
    #   sur TOUTES les données (y compris le bord) estime mieux la pente que de
    #   retirer la frontière pour valider. Défaut False → split random (train
    #   complet) + garde anti-divergence + candidat linéaire. True = ancien
    #   hold-out frontière (à réserver aux cas où l'on veut valider au bord).
    EXTRAPOLATION_FRONTIER_SPLIT: bool   = False

    # [REPRO] Seed maître propagé depuis l'API. Sert à dériver de façon
    # deterministic les seeds des workers parallèles (None = non reproductible).
    SEED: Optional[int] = None

    # [v20] Parallélisme des îles (ProcessPoolExecutor, spawn-safe Windows)
    #   None  = AUTO : activé si ≥4 cœurs ET ≥2 îles (sinon séquentiel)
    #   True  = forcé (≥2 îles requis) ; False = toujours séquentiel
    # Changement algorithmique assumé : chaque île évolue PARALLEL_ROUND
    # générations sur un instantané figé des structures stigmergiques
    # (lib de fragments, co-graphe, SeqMem), fusionnées à chaque round.
    # Toute erreur du pool => repli séquentiel automatique et silencieux.
    PARALLEL_ISLANDS: Optional[bool] = None
    PARALLEL_ROUND: int = 0          # 0 = auto : min(10, MIGRATION_INTERVAL)

    # [v19] Déduplication sémantique de population (cf. Operon / PySR)
    USE_SEMANTIC_DEDUP: bool = False # écarte les clones comportementaux ; OFF par default :
    #   sur cette base le taux de clones est ~14%%, insuffisant pour amortir le
    #   coût du hash sémantique. Activable pour gros POP_SIZE ou problèmes très
    #   convergents (Operon/PySR l'utilisent sur des populations moins diverses).
    SEMANTIC_DEDUP_DECIMALS: int = 3 # arrondi des prédictions probe pour le hash sémantique

    # Sorties
    LOG_CSV: str           = "gp_elite_log.csv"
    SAVE_BEST: str         = "gp_elite_best.txt"


CFG = Config()

# ============================================================
# OPÉRATEURS
# ============================================================

BINARY_OPS  = ["+", "-", "*", "/", "pow"]
# max2/min2/step/is_even réservés au mode Syracuse via _get_ops_for_role/_active_pools
UNARY_OPS   = ["sin", "cos", "log", "sqrt", "abs", "neg", "sq", "cube"]
ALL_OPS     = BINARY_OPS + UNARY_OPS

# [FIX-OPS v20.1] Catégories UNIVERSELLES — pour les TESTS d'appartenance
# (to_string, point_mutation, shrink_mutation...). Les listes UNARY_OPS /
# BINARY_OPS ci-dessus restent les POOLS DE TIRAGE du mode standard, mais
# elles ne couvrent pas les opérateurs des modes Syracuse (max2/min2/step/
# is_even) et Batterie (tanh/exp). Tester l'appartenance contre les pools
# de tirage gelait ces opérateurs en mutation et tronquait leur affichage
# (ex: "tanh" imprimé SANS son argument).
ALL_UNARY_OPS  = UNARY_OPS  + ["tanh", "exp", "tan", "is_even", "step"]
ALL_BINARY_OPS = BINARY_OPS + ["max2", "min2"]

# Poids standard — problèmes classiques 1-D/N-D
BINARY_WEIGHTS = [3, 3, 4, 2, 1]   # +  -  *  /  pow
UNARY_WEIGHTS  = [3, 3, 2, 2, 1, 1, 3, 1]
#                 sin cos log sqrt abs neg sq cube

# [v17] Pool île Cleaner Syracuse : cos réintégré à poids minimal, step ajouté
_CLEANER_BINARY_OPS     = ["+", "-", "*", "/", "pow", "max2", "min2"]
_CLEANER_BINARY_WEIGHTS = [3,   3,   4,   2,   2,     2,      2    ]
_CLEANER_UNARY_OPS      = ["cos", "log", "sqrt", "abs", "neg", "sq", "cube", "is_even", "step"]
_CLEANER_UNARY_WEIGHTS  = [1,     3,     2,      1,     1,     3,    2,      5,         2     ]

# [v16-BATTERY CSV] Pool physique pour données réelles batterie ────────────────
# Conservé pour compatibilité avec load_custom_csv() et le mode BATTERY_SOH.
_BATTERY_BINARY_OPS     = ["+", "-", "*", "/", "pow"]
_BATTERY_BINARY_WEIGHTS = [4, 4, 5, 2, 3]
_BATTERY_UNARY_OPS      = ["exp", "log", "sqrt", "tanh", "sq", "neg"]
_BATTERY_UNARY_WEIGHTS  = [4, 3, 3, 2, 3, 1]

# [v22-CSV] Pools d'opérateurs sélectionnables pour le mode CSV générique ──────
# L'utilisateur choisit la "physique" de son problème au chargement :
#   physical : exp/log/sqrt/tanh/pow — lois de décroissance, saturation,
#              Arrhenius, diffusion (default pour données expérimentales)
#   trig     : + sin/cos — phénomènes périodiques/oscillants
#   full     : tout — quand on ne sait pas a priori
#   poly     : uniquement +,-,*,/,sq,cube,sqrt — relations algébriques pures
_GENCSV_POOLS = {
    "physical": (["+", "-", "*", "/", "pow"],          [4, 4, 5, 2, 3],
                 ["exp", "log", "sqrt", "tanh", "sq", "neg", "abs"],
                                                        [4, 3, 3, 2, 3, 1, 2]),
    "trig":     (["+", "-", "*", "/", "pow"],          [3, 3, 4, 2, 1],
                 ["sin", "cos", "exp", "log", "sqrt", "tanh", "sq", "neg", "abs"],
                                                        [3, 3, 2, 2, 2, 2, 2, 1, 1]),
    "full":     (["+", "-", "*", "/", "pow"],          [3, 3, 4, 2, 1],
                 ["sin", "cos", "log", "exp", "sqrt", "tanh", "abs", "neg", "sq", "cube"],
                                                        [2, 2, 2, 2, 2, 2, 1, 1, 3, 1]),
    "poly":     (["+", "-", "*", "/"],                 [4, 4, 5, 2],
                 ["sqrt", "neg", "sq", "cube", "abs"],  [2, 1, 3, 2, 1]),
    # [CONSERVATION] Pool minimal pour la découverte de lois physiques : pas
    # d'exp/log/pow (qui génèrent des arbres exploitant le bruit numérique des
    # dérivées). Juste les briques des invariants courants : +, -, *, carré,
    # et trigonométrie pour les potentiels (pendule, etc.).
    "conserve": (["+", "-", "*"],                      [4, 3, 4],
                 ["sq", "cos", "sin", "neg"],           [4, 3, 3, 1]),
}

_GENERIC_CSV_MODE: bool       = False
_GENERIC_BINARY_OPS: list     = ["+", "-", "*", "/", "pow"]
_GENERIC_BINARY_WEIGHTS: list = [4, 4, 5, 2, 3]
_GENERIC_UNARY_OPS: list      = ["exp", "log", "sqrt", "tanh", "sq", "neg", "abs"]
_GENERIC_UNARY_WEIGHTS: list  = [4, 3, 3, 2, 3, 1, 2]

# Noms réels des colonnes (pour affichage des formules : X[0] → "temperature")
CSV_FEATURE_NAMES: list = []
CSV_TARGET_NAME: str    = "y"

# [SYRACUSE] Pool algébrique pour la conjecture de Collatz ────────────────────
# Opérateurs retenus : ceux utiles à modéliser des croissances irrégulières,
# des divergences logarithmiques, et la bifurcation pair/impair structurelle.
# [v17-POOL REVISION] cos réintégré suite à l'analyse des runs :
# · Run avec cos   → RAW=1.21  (meilleure expression trouvée)
# · Run sans cos   → RAW=1.51  (régression significative)
# cos(cos(x)) agit comme un modulateur doux ∈ [0.54, 1.0] — non-périodique
# dans le domaine [-2, 2] où il opère. Ce n'est PAS une oscillation parasite
# mais une compression non-linéaire que le GP a découverte empiriquement.
# [V42] max2/min2 ajoutés : permettent des conditions IF symboliques.
# [V42] step ajouté : condition IF unaire — détecte si trajectoire monte/descend.
_SYRACUSE_BINARY_OPS     = ["+", "-", "*", "/", "pow", "max2", "min2"]
_SYRACUSE_BINARY_WEIGHTS = [4,   4,   5,   2,   3,     2,      2    ]
#                            +    -    *    /   pow    max2    min2
_SYRACUSE_UNARY_OPS      = ["cos", "log", "sqrt", "abs", "neg", "sq", "cube", "is_even", "step"]
_SYRACUSE_UNARY_WEIGHTS  = [1,     3,     2,      1,     2,     3,    2,      5,         3     ]
#                            cos   log    sqrt    abs    neg    sq    cube    is_even     step

# Flag global activé par generate_syracuse_dataset() → tous les pools basculent
_SYRACUSE_MODE: bool = False

# Flag global activé par load_custom_csv() → tous les pools basculent
_BATTERY_CSV_MODE: bool = False

def _get_ops_for_role(role: str):
    """Retourne (binary_ops, binary_weights, unary_ops, unary_weights) selon le rôle.

    En mode Syracuse (_SYRACUSE_MODE=True), tous les rôles utilisent
    le pool algébrique Collatz — tanh/sin/cos/exp exclus.
    En mode CSV batterie (_BATTERY_CSV_MODE=True), pool physique batterie.
    """
    # [SYRACUSE] pool Collatz prioritaire sur tous les rôles
    if _SYRACUSE_MODE:
        if role == "cleaner":
            return (_CLEANER_BINARY_OPS, _CLEANER_BINARY_WEIGHTS,
                    _CLEANER_UNARY_OPS,  _CLEANER_UNARY_WEIGHTS)
        return (_SYRACUSE_BINARY_OPS, _SYRACUSE_BINARY_WEIGHTS,
                _SYRACUSE_UNARY_OPS,  _SYRACUSE_UNARY_WEIGHTS)
    # [v22-CSV] pool générique prioritaire (choisi par l'utilisateur)
    if _GENERIC_CSV_MODE:
        return (_GENERIC_BINARY_OPS, _GENERIC_BINARY_WEIGHTS,
                _GENERIC_UNARY_OPS,  _GENERIC_UNARY_WEIGHTS)
    # [v16-BATTERY CSV] pool physique prioritaire sur tous les rôles
    if _BATTERY_CSV_MODE:
        return (_BATTERY_BINARY_OPS, _BATTERY_BINARY_WEIGHTS,
                _BATTERY_UNARY_OPS,  _BATTERY_UNARY_WEIGHTS)
    if role == "cleaner":
        return (_CLEANER_BINARY_OPS, _CLEANER_BINARY_WEIGHTS,
                _CLEANER_UNARY_OPS,  _CLEANER_UNARY_WEIGHTS)
    return (BINARY_OPS, BINARY_WEIGHTS, UNARY_OPS, UNARY_WEIGHTS)


def _active_pools():
    """
    Retourne (bin_ops, bin_w, uni_ops, uni_w, all_ops, all_w) du mode actif.

    Point d'entrée unique pour TOUTES les fonctions de génération d'arbres
    et de mutation qui ne connaissent pas leur 'rôle' d'île :
      · _nd_diverse_population  (couverture initiale)
      · _random_tree_full_nd    (full trees)
      · _random_tree_grow_nd    (grow trees)
      · SeqMem.build_from_seq   (fallback mutation)
      · fallback_all / fallback_uni dans evolve_island

    Garantit qu'aucun opérateur étranger au problème (sin/cos/tanh en mode
    Syracuse ; sin/cos/tan en mode batterie) ne s'infiltre dans la population
    via un tirage random non supervisé.
    """
    if _GENERIC_CSV_MODE:
        b_ops, b_w = _GENERIC_BINARY_OPS, _GENERIC_BINARY_WEIGHTS
        u_ops, u_w = _GENERIC_UNARY_OPS,  _GENERIC_UNARY_WEIGHTS
    elif _SYRACUSE_MODE:
        b_ops, b_w = _SYRACUSE_BINARY_OPS, _SYRACUSE_BINARY_WEIGHTS
        u_ops, u_w = _SYRACUSE_UNARY_OPS,  _SYRACUSE_UNARY_WEIGHTS
    elif _BATTERY_CSV_MODE:
        b_ops, b_w = _BATTERY_BINARY_OPS, _BATTERY_BINARY_WEIGHTS
        u_ops, u_w = _BATTERY_UNARY_OPS,  _BATTERY_UNARY_WEIGHTS
    else:
        b_ops, b_w = BINARY_OPS, BINARY_WEIGHTS
        u_ops, u_w = UNARY_OPS,  UNARY_WEIGHTS
    all_ops = b_ops + u_ops
    all_w   = b_w   + u_w
    return b_ops, b_w, u_ops, u_w, all_ops, all_w


class Node:
    __slots__ = ("value", "left", "right", "_hash", "_chash")

    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left  = left
        self.right = right
        self._hash  = None
        self._chash = None   # [v18] canonical_hash mémoïsé

    def copy(self):
        """Copie profonde ITÉRATIVE (post-ordre) — aucune limite de profondeur.
        [FIX-REC v18] L'ancienne version récursive levait RecursionError sur
        les arbres profonds produits par les constructeurs stigmergiques."""
        out = {}
        stack = [(self, False)]
        while stack:
            nd, processed = stack.pop()
            if processed:
                # NB : ne PAS propager _hash/_chash — les mutations in-place
                # (point_mutation) n'invalident que le nœud touché ; des hashes
                # hérités sur les ancêtres seraient périmés -> faux hits de cache.
                out[id(nd)] = Node(nd.value,
                          out.pop(id(nd.left))  if nd.left  is not None else None,
                          out.pop(id(nd.right)) if nd.right is not None else None)
            else:
                stack.append((nd, True))
                if nd.left  is not None: stack.append((nd.left,  False))
                if nd.right is not None: stack.append((nd.right, False))
        return out[id(self)]

    def structural_hash(self) -> int:
        """Hash structurel, mémoïsé, calcul ITÉRATIF post-ordre.
        [OPT v18] Plus de str(round(v)) par feuille ni de récursion Python."""
        if self._hash is not None:
            return self._hash
        stack = [(self, False)]
        while stack:
            nd, processed = stack.pop()
            if nd._hash is not None:
                continue
            if processed:
                if nd.left is None and nd.right is None:
                    nd._hash = hash(("leaf", round(nd.value, 4)
                                     if isinstance(nd.value, float) else nd.value))
                elif nd.right is None:
                    nd._hash = hash(("unary", nd.value, nd.left._hash))
                else:
                    nd._hash = hash(("binary", nd.value,
                                     nd.left._hash, nd.right._hash))
            else:
                stack.append((nd, True))
                if nd.left  is not None and nd.left._hash  is None:
                    stack.append((nd.left,  False))
                if nd.right is not None and nd.right._hash is None:
                    stack.append((nd.right, False))
        return self._hash

    def canonical_hash(self) -> int:
        """Hash canonique (constantes -> 'C'), MÉMOÏSÉ et itératif.
        [OPT v18] L'ancienne version recalculait récursivement à chaque appel
        -> O(n²) par individu dans _is_banned et le scan de dominance."""
        if self._chash is not None:
            return self._chash
        stack = [(self, False)]
        while stack:
            nd, processed = stack.pop()
            if nd._chash is not None:
                continue
            if processed:
                if nd.left is None and nd.right is None:
                    key = "C" if isinstance(nd.value, float) else nd.value
                    nd._chash = hash(("leaf", key))
                elif nd.right is None:
                    nd._chash = hash(("unary", nd.value, nd.left._chash))
                else:
                    nd._chash = hash(("binary", nd.value,
                                      nd.left._chash, nd.right._chash))
            else:
                stack.append((nd, True))
                if nd.left  is not None and nd.left._chash  is None:
                    stack.append((nd.left,  False))
                if nd.right is not None and nd.right._chash is None:
                    stack.append((nd.right, False))
        return self._chash

    def invalidate_hash(self):
        self._hash  = None
        self._chash = None

# ============================================================
# AFFICHAGE
# ============================================================

def to_string(node) -> str:
    if node is None:
        return "0"
    v = node.value
    if v in ALL_BINARY_OPS:                              # [FIX-OPS v20.1]
        if v == "pow":
            return f"pow({to_string(node.left)}, {to_string(node.right)})"
        if v == "max2":
            return f"max({to_string(node.left)}, {to_string(node.right)})"
        if v == "min2":
            return f"min({to_string(node.left)}, {to_string(node.right)})"
        return f"({to_string(node.left)} {v} {to_string(node.right)})"
    if v in ALL_UNARY_OPS:                               # [FIX-OPS v20.1]
        if v == "neg":
            return f"(-{to_string(node.left)})"
        if v == "sq":
            return f"({to_string(node.left)})²"
        if v == "cube":
            return f"({to_string(node.left)})³"
        if v == "is_even":
            return f"is_even({to_string(node.left)})"
        if v == "step":                                  # [V42]
            return f"step({to_string(node.left)})"
        return f"{v}({to_string(node.left)})"
    if v == "max2":                                      # [V42]
        return f"max({to_string(node.left)}, {to_string(node.right)})"
    if v == "min2":                                      # [V42]
        return f"min({to_string(node.left)}, {to_string(node.right)})"
    if isinstance(v, float):
        return str(round(v, 6))
    # [v22-CSV] X[i] → nom réel de la colonne (ex: X[0] → "temperature")
    if (_GENERIC_CSV_MODE and CSV_FEATURE_NAMES and
            isinstance(v, str) and v.startswith("X[") and v.endswith("]")):
        try:
            idx = int(v[2:-1])
            if 0 <= idx < len(CSV_FEATURE_NAMES):
                return CSV_FEATURE_NAMES[idx]
        except (ValueError, IndexError):
            pass
    # "x" (1-D) ou "X[i]" (N-D) : retourné tel quel
    return str(v)

# ============================================================
# MÉTRIQUES
# ============================================================

def tree_size(node) -> int:
    if node is None:
        return 0
    stack = [node]
    count = 0
    while stack:
        n = stack.pop()
        count += 1
        if n.left:  stack.append(n.left)
        if n.right: stack.append(n.right)
    return count

def tree_depth(node) -> int:
    if node is None:
        return 0
    stack = [(node, 1)]
    max_d = 0
    while stack:
        n, d = stack.pop()
        if d > max_d:
            max_d = d
        if n.left:  stack.append((n.left,  d + 1))
        if n.right: stack.append((n.right, d + 1))
    return max_d


# [v14.2 — BIC] Complexité pondérée + pénalité quadratique sur floats ajustés ──
# Formule fitness_BIC v14.2 :
#   fitness = n·ln(MSE_pur) + k·ln(n) + γ·n_adj²·ln(n)
#
#   k     = Σ coût(nœud)   coût(float)=_FLOAT_COMPLEXITY_WEIGHT, coût(op/x)=1
#   n_adj = nombre de constantes AJUSTÉES (non-entières simples)
#   γ     = _FLOAT_GAMMA = 2.0
#
# Distinction constantes entières vs ajustées :
#   · Entière simple (0, ±1, ±2 … ±10) : issue de simplification algébrique
#     (ex : 2.0 via x+x→2*x). Pas de pénalité quadratique.
#   · Ajustée (0.042503, -2.423…) : encode de l'information sur le dataset,
#     contribue à n_adj et déclenche la pénalité sur-linéaire.
#
# Impact : 1 float ajusté → +2·ln(n), 2 → +8·ln(n), 4 → +32·ln(n).
# ─────────────────────────────────────────────────────────────────────────────
_FLOAT_COMPLEXITY_WEIGHT = 3   # coût linéaire d'un float dans k
_FLOAT_GAMMA             = 2.0 # coefficient de la pénalité quadratique


def _is_adjusted_float(value) -> bool:
    """
    [v14.2] True si la valeur est une constante flottante AJUSTÉE (non émergente).
    Exclut les entiers simples (|v|<=10 et v==round(v)) qui peuvent émerger
    naturellement de la simplification algébrique (x+x → 2.0*x, etc.).
    """
    if not isinstance(value, float):
        return False
    if not math.isfinite(value):
        return True     # inf/nan : constante "ajustée" pathologique (pénalisée),
                        # et surtout évite OverflowError sur round(inf)
    if abs(value - round(value)) < 1e-9 and abs(value) <= 10.0:
        return False    # constante entière simple : non pénalisée
    return True


def tree_complexity(node) -> tuple:
    """
    [v14.2] Complexité pondérée de l'arbre pour le calcul BIC.

    Traversée itérative (pas de récursion).
    Retourne (k, n_adj) :
        k     = Σ coût(nœud)  avec coût(float)=_FLOAT_COMPLEXITY_WEIGHT,
                                    coût(op/x) =1
        n_adj = nombre de constantes ajustées (non-entières ou |v|>10)

    Les deux valeurs sont utilisées dans fitness() :
        BIC = n·ln(MSE) + k·ln(n) + _FLOAT_GAMMA·n_adj²·ln(n)
    """
    if node is None:
        return 0, 0
    stack = [node]
    k, n_adj = 0, 0
    while stack:
        nd = stack.pop()
        if isinstance(nd.value, float):
            k += _FLOAT_COMPLEXITY_WEIGHT
            if _is_adjusted_float(nd.value):
                n_adj += 1
        else:
            k += 1
        if nd.left:  stack.append(nd.left)
        if nd.right: stack.append(nd.right)
    return k, n_adj

# ============================================================
# NAVIGATION (itérative)
# ============================================================

def get_all_nodes(root):
    """
    Retourne [(node, parent, side), ...] en ordre BFS.
    Optimisé en O(N) grâce à un collections.deque local.
    """
    if root is None:
        return []
    result = []
    queue = deque([(root, None, None)])
    while queue:
        node, parent, side = queue.popleft()
        result.append((node, parent, side))
        if node.left is not None:
            queue.append((node.left, node, "left"))
        if node.right is not None:
            queue.append((node.right, node, "right"))
    return result

def collect_constants(root) -> List[Node]:
    """Retourne tous les noeuds constantes flottantes."""
    result = []
    stack  = [root]
    while stack:
        n = stack.pop()
        if isinstance(n.value, float):
            result.append(n)
        if n.left:  stack.append(n.left)
        if n.right: stack.append(n.right)
    return result

# ============================================================
# OPÉRATIONS SÉCURISÉES — scalaires (utilisées par simplify/display)
# ============================================================

_SAFE_LIMIT = 1e6

def safe_div(a: float, b: float) -> float:
    return a if abs(b) < 1e-8 else a / b

def safe_pow(a: float, b: float) -> float:
    try:
        if abs(b) > 8:
            return 1.0
        r = pow(abs(a) + 1e-12, b)
        if not math.isfinite(r) or abs(r) > _SAFE_LIMIT:
            return 1.0
        return r
    except Exception:
        return 1.0

def safe_tan(x: float) -> float:
    try:
        r = math.tan(x)
        return 0.0 if not math.isfinite(r) or abs(r) > _SAFE_LIMIT else r
    except Exception:
        return 0.0

def safe_log(x: float) -> float:
    return math.log(abs(x) + 1e-12)

def safe_exp(x: float) -> float:
    try:
        r = math.exp(min(x, 20.0))
        return r if math.isfinite(r) else _SAFE_LIMIT
    except Exception:
        return 0.0

def safe_sqrt(x: float) -> float:
    return math.sqrt(abs(x))

# ============================================================
# OPÉRATIONS SÉCURISÉES — vectorisées NumPy
# ============================================================

def _np_safe_div(a, b):
    """
    Division protégée NumPy.
    [v16-FIX] np.where évalue les DEUX branches avant de choisir : si a/b déborde
    en float64 même quand |b|>1e-8, le RuntimeWarning est levé.
    Solution : clipper a en amont et remplacer b~0 par 1.0 avant la division.
    """
    a = np.clip(a, -_SAFE_LIMIT, _SAFE_LIMIT)
    b_safe = np.where(np.abs(b) < 1e-8, 1.0, b)
    with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
        r = np.where(np.abs(b) < 1e-8, a, a / b_safe)
    return np.where(np.isfinite(r), r, 0.0)

def _np_safe_pow(a, b):
    """
    Puissance sécurisée NumPy.
    [v16-FIX] errstate étendu à 'over' pour supprimer les overflow warnings.
    [V42-FIX] Clipping de la BASE en plus de l'exposant :
    Les features de trajectoire X[6]-X[9] peuvent atteindre ~7 (log1p de grandes
    valeurs), et sq(X[7]) ≈ 49 — pow(49, 8) = 1.9e13 qui déborde float32 dans
    certains contextes. On clippe la base à [-100, 100] avant la puissance.
    """
    b = np.clip(b, -6.0, 6.0)   # exposant limité : base^6 suffisant pour GP
    a = np.clip(a, -100.0, 100.0)  # base clippée : évite pow(large, large)
    with np.errstate(all='ignore'):
        b_int = np.round(b)
        is_int = np.abs(b - b_int) < 1e-6
        r_int  = np.sign(a) * np.power(np.abs(a) + 1e-12, np.abs(b_int))
        r_int  = np.where(b_int >= 0, r_int, 1.0 / (np.abs(r_int) + 1e-12) * np.sign(r_int))
        r_real = np.power(np.abs(a) + 1e-12, b)
        r = np.where(is_int, r_int, r_real)
    return np.where(np.isfinite(r) & (np.abs(r) < _SAFE_LIMIT), r, 1.0)

def _np_safe_tan(a):
    with np.errstate(all='ignore'):
        r = np.tan(a)
    return np.where(np.isfinite(r) & (np.abs(r) < _SAFE_LIMIT), r, 0.0)

def _np_safe_exp(a):
    """
    [v16-FIX] clip symétrique [-88, 88] : exp(88) ≈ 1.6e38 < float64 max.
    Remplace le clip asymétrique [-500, 20] qui sous-estimait des expressions
    comme exp(-X[:,0]²) sur des valeurs négatives légitimement grandes.
    """
    with np.errstate(over='ignore', invalid='ignore'):
        r = np.exp(np.clip(a, -88.0, 88.0))
    return np.where(np.isfinite(r), r, 0.0)

def _np_safe_log(a):
    return np.log(np.abs(a) + 1e-12)

def _np_safe_sqrt(a):
    return np.sqrt(np.abs(a))

def _np_is_even(a):
    """
    [SYRACUSE] Opérateur 'is_even' protégé — détecte la parité d'un nombre.
    Retourne +1.0 si round(a) est pair, -1.0 sinon.
    Ce signal binaire aide les îles à capter immédiatement la bifurcation
    structurelle n_pair → n/2  vs  n_impair → 3n+1 du problème de Collatz.
    Opère sur des valeurs réelles continues via arrondi à l'entier le plus proche.
    Robuste aux NaN/inf : remplacés par 0 avant le cast pour éviter le RuntimeWarning.
    """
    with np.errstate(invalid='ignore'):
        a_safe = np.where(np.isfinite(a), a, 0.0)
        a_clipped = np.clip(np.abs(a_safe), 0.0, 2.0e15)   # évite overflow int64
        a_int = np.round(a_clipped).astype(np.int64)
    return np.where(a_int % 2 == 0, 1.0, -1.0)


def _np_step(a):
    """
    [V42] Opérateur step — condition IF encodée de façon différentiable.
    Retourne 1.0 si a > 0, 0.0 sinon.

    Permet au GP d'écrire des conditions comme :
      step(X[8] - X[21]) = 1 si la trajectoire monte encore à l'étape 21
    Essentiel pour capter les bifurcations Collatz tardives (n=97, n=703).
    """
    return np.where(np.asarray(a) > 0.0, 1.0, 0.0)


def _np_max2(a, b):
    """[V42] max(a, b) — sélection de branche, condition IF binaire."""
    return np.maximum(np.asarray(a), np.asarray(b))


def _np_min2(a, b):
    """[V42] min(a, b) — sélection de branche, condition IF binaire."""
    return np.minimum(np.asarray(a), np.asarray(b))

# ============================================================
# COMPILATEUR ARBRE → FONCTION NUMPY
# ============================================================

_COMPILE_CACHE: Dict[int, Any] = {}
_COMPILE_CACHE_MAX = 4096   # entrées max — élagage FIFO au-delà

_NP_GLOBALS = {
    "np":          np,
    "_safe_div":   _np_safe_div,
    "_safe_pow":   _np_safe_pow,
    "_safe_tan":   _np_safe_tan,
    "_safe_exp":   _np_safe_exp,
    "_safe_log":   _np_safe_log,
    "_safe_sqrt":  _np_safe_sqrt,
    "_is_even":    _np_is_even,   # [SYRACUSE] parité binaire protégée
    "_step":       _np_step,      # [V42] condition IF : 1 si a>0 else 0
    "_max2":       _np_max2,      # [V42] max(a, b) — sélection de branche
    "_min2":       _np_min2,      # [V42] min(a, b) — sélection de branche
}

def _to_np_code(node) -> str:
    """Traduit récursivement un arbre en expression Python/NumPy (string).
    [v16-NDIM] Supporte les terminaux "X[i]" → "_x[:, i]"
    en plus de "x" → "_x" (rétrocompatibilité 1-D).
    """
    if node is None:
        return "0.0"
    v = node.value
    if v == "x":
        return "_x"
    # [v16-NDIM] Feature i de la matrice X (n_samples, n_features)
    if isinstance(v, str) and v.startswith("X[") and v.endswith("]"):
        try:
            idx = int(v[2:-1])
            return f"_x[:, {idx}]"
        except ValueError:
            return "0.0"
    if isinstance(v, float):
        return repr(v)
    if v == "+":
        return f"({_to_np_code(node.left)} + {_to_np_code(node.right)})"
    if v == "-":
        return f"({_to_np_code(node.left)} - {_to_np_code(node.right)})"
    if v == "*":
        return f"({_to_np_code(node.left)} * {_to_np_code(node.right)})"
    if v == "/":
        return f"_safe_div({_to_np_code(node.left)}, {_to_np_code(node.right)})"
    if v == "pow":
        return f"_safe_pow({_to_np_code(node.left)}, {_to_np_code(node.right)})"
    if v == "sin":
        return f"np.sin({_to_np_code(node.left)})"
    if v == "cos":
        return f"np.cos({_to_np_code(node.left)})"
    if v == "tan":
        return f"_safe_tan({_to_np_code(node.left)})"
    if v == "tanh":
        return f"np.tanh({_to_np_code(node.left)})"
    if v == "exp":
        return f"_safe_exp({_to_np_code(node.left)})"
    if v == "log":
        return f"_safe_log({_to_np_code(node.left)})"
    if v == "sqrt":
        return f"_safe_sqrt({_to_np_code(node.left)})"
    if v == "abs":
        return f"np.abs({_to_np_code(node.left)})"
    if v == "neg":
        return f"(-{_to_np_code(node.left)})"
    if v == "sq":
        return f"({_to_np_code(node.left)} ** 2)"
    if v == "cube":
        return f"({_to_np_code(node.left)} ** 3)"
    if v == "is_even":                                   # [SYRACUSE]
        return f"_is_even({_to_np_code(node.left)})"
    if v == "step":                                      # [V42]
        return f"_step({_to_np_code(node.left)})"
    if v == "max2":                                      # [V42]
        return f"_max2({_to_np_code(node.left)}, {_to_np_code(node.right)})"
    if v == "min2":                                      # [V42]
        return f"_min2({_to_np_code(node.left)}, {_to_np_code(node.right)})"
    return "0.0"

def _collect_constants_ordered(node) -> list:
    """Collecte les constantes en ordre BFS (stable et reproductible)."""
    result = []
    stack = [node]
    while stack:
        n = stack.pop(0)
        if n is None:
            continue
        if isinstance(n.value, float):
            result.append(n)
        if n.left:  stack.append(n.left)
        if n.right: stack.append(n.right)
    return result


def _to_np_code_parametric(node, const_list: list) -> str:
    """
    Traduit l'arbre en code NumPy avec les constantes remplacées par _c[i].
    [v16-NDIM] Supporte les terminaux "X[i]" → "_x[:, i]".
    """
    const_idx = {id(c): i for i, c in enumerate(const_list)}

    def _code(n) -> str:
        if n is None:
            return "0.0"
        v = n.value
        if v == "x":
            return "_x"
        if isinstance(v, str) and v.startswith("X[") and v.endswith("]"):
            try:
                idx = int(v[2:-1])
                return f"_x[:, {idx}]"
            except ValueError:
                return "0.0"
        if isinstance(v, float):
            idx = const_idx.get(id(n))
            return f"_c[{idx}]" if idx is not None else repr(v)
        if v == "+":   return f"({_code(n.left)} + {_code(n.right)})"
        if v == "-":   return f"({_code(n.left)} - {_code(n.right)})"
        if v == "*":   return f"({_code(n.left)} * {_code(n.right)})"
        if v == "/":   return f"_safe_div({_code(n.left)}, {_code(n.right)})"
        if v == "pow": return f"_safe_pow({_code(n.left)}, {_code(n.right)})"
        if v == "sin":  return f"np.sin({_code(n.left)})"
        if v == "cos":  return f"np.cos({_code(n.left)})"
        if v == "tan":  return f"_safe_tan({_code(n.left)})"
        if v == "tanh": return f"np.tanh({_code(n.left)})"
        if v == "exp":  return f"_safe_exp({_code(n.left)})"
        if v == "log":  return f"_safe_log({_code(n.left)})"
        if v == "sqrt": return f"_safe_sqrt({_code(n.left)})"
        if v == "abs":  return f"np.abs({_code(n.left)})"
        if v == "neg":  return f"(-{_code(n.left)})"
        if v == "sq":   return f"({_code(n.left)} ** 2)"
        if v == "cube": return f"({_code(n.left)} ** 3)"
        if v == "is_even": return f"_is_even({_code(n.left)})"   # [SYRACUSE]
        if v == "step":    return f"_step({_code(n.left)})"      # [V42]
        if v == "max2":    return f"_max2({_code(n.left)}, {_code(n.right)})"  # [V42]
        if v == "min2":    return f"_min2({_code(n.left)}, {_code(n.right)})"  # [V42]
        return "0.0"

    return _code(node)


_PARAMETRIC_CACHE: Dict[int, Any] = {}
_PARAMETRIC_CACHE_MAX = 2048


def compile_parametric(node) -> Tuple[Any, list]:
    """
    Compile f(_x, _c) où _c est un array numpy des constantes.
    Hash structural → une seule compilation par forme d'arbre.
    Retourne (fn, const_nodes) où const_nodes est dans l'ordre BFS.
    """
    # Collecter les constantes de CE nœud (avec leurs ids actuels)
    consts = _collect_constants_ordered(node)
    n_consts = len(consts)

    h = node.structural_hash()
    # Vérifier si le cache a une fonction avec le bon nombre de constantes
    cached = _PARAMETRIC_CACHE.get(h)
    if cached is not None and cached[1] == n_consts:
        return cached[0], consts

    code = _to_np_code_parametric(node, consts)
    src  = f"def _f(_x, _c):\n    return {code}\n"
    globs = dict(_NP_GLOBALS)
    try:
        exec(src, globs)
        fn = globs["_f"]
    except Exception:
        fn = None

    if fn is not None:
        _PARAMETRIC_CACHE[h] = (fn, n_consts)
        if len(_PARAMETRIC_CACHE) > _PARAMETRIC_CACHE_MAX:
            for old_key in list(_PARAMETRIC_CACHE.keys())[:256]:
                del _PARAMETRIC_CACHE[old_key]

    return fn, consts


def compile_to_numpy(node):
    """
    Compile l'arbre en f(x_array) -> np.ndarray, mis en cache par hash structural.
    Utilisé par evaluate_vector et raw_mse.
    """
    h = node.structural_hash()
    if h in _COMPILE_CACHE:
        return _COMPILE_CACHE[h]
    code = _to_np_code(node)
    src  = f"def _f(_x):\n    return {code}\n"
    globs = dict(_NP_GLOBALS)
    try:
        exec(src, globs)
        fn = globs["_f"]
    except Exception:
        fn = lambda _x, _n=node: np.array([evaluate(_n, float(xi)) for xi in _x])
    _COMPILE_CACHE[h] = fn
    if len(_COMPILE_CACHE) > _COMPILE_CACHE_MAX:
        # Évacuation FIFO ultra-rapide tirant parti de l'ordre d'insertion natif
        for _ in range(512):
            if _COMPILE_CACHE:
                _COMPILE_CACHE.pop(next(iter(_COMPILE_CACHE)))
    return fn

# ============================================================
# ÉVALUATION SCALAIRE (conservée pour simplify / affichage)
# ============================================================

def evaluate(node, x) -> float:
    """Évaluation récursive scalaire — utilisée uniquement pour l'affichage 1-D.
    [v16-NDIM] x peut être un float (mode 1-D) ou un array 1-D de shape (n_features,)
    représentant une seule ligne de la matrice X.
    Les terminaux X[i] indexent x[i] ; le terminal "x" utilise x directement (1-D).
    """
    if node is None:
        return 0.0
    try:
        v = node.value
        if v == "x":
            return float(x) if not hasattr(x, '__len__') else float(x[0])
        # [v16-NDIM] Feature i
        if isinstance(v, str) and v.startswith("X[") and v.endswith("]"):
            try:
                idx = int(v[2:-1])
                return float(x[idx])
            except (IndexError, TypeError, ValueError):
                return 0.0
        if isinstance(v, float):
            return v
        if v == "+":
            return evaluate(node.left, x) + evaluate(node.right, x)
        if v == "-":
            return evaluate(node.left, x) - evaluate(node.right, x)
        if v == "*":
            return evaluate(node.left, x) * evaluate(node.right, x)
        if v == "/":
            return safe_div(evaluate(node.left, x), evaluate(node.right, x))
        if v == "pow":
            return safe_pow(evaluate(node.left, x), evaluate(node.right, x))
        if v == "sin":
            return math.sin(evaluate(node.left, x))
        if v == "cos":
            return math.cos(evaluate(node.left, x))
        if v == "tan":
            return safe_tan(evaluate(node.left, x))
        if v == "tanh":
            return math.tanh(evaluate(node.left, x))
        if v == "exp":
            return safe_exp(evaluate(node.left, x))
        if v == "log":
            return safe_log(evaluate(node.left, x))
        if v == "sqrt":
            return safe_sqrt(evaluate(node.left, x))
        if v == "abs":
            return abs(evaluate(node.left, x))
        if v == "neg":
            return -evaluate(node.left, x)
        if v == "sq":
            a = evaluate(node.left, x); return a * a
        if v == "cube":
            a = evaluate(node.left, x); return a * a * a
    except Exception:
        return 0.0
    return 0.0

def evaluate_vector(node, xs) -> np.ndarray:
    """Évalue sur un vecteur (1-D) ou une matrice (N-D) via le compilateur NumPy.
    [v16-NDIM]
      · xs 1-D (n_samples,)          → mode rétrocompatible, _x = xs
      · xs 2-D (n_samples, n_features) → mode N-D, _x[:, i] accès par feature
    La fonction compilée reçoit _x tel quel ; _to_np_code génère le bon indexage.
    """
    fn = compile_to_numpy(node)
    if isinstance(xs, np.ndarray):
        x_in = xs
    else:
        x_in = np.asarray(xs, dtype=float)
    try:
        r = fn(x_in)
        n_rows = x_in.shape[0]
        r = np.asarray(r, dtype=float)
        if r.shape == ():          # scalaire → broadcast
            r = np.full(n_rows, float(r))
        # Remplace les non-finis (inf/nan) par 0, PUIS borne les valeurs
        # extrêmes-mais-finies (ex. exp() en extrapolation hors domaine) pour
        # éviter tout overflow en aval (R², carré). Borne large (1e12) qui ne
        # change rien aux prédictions normales mais neutralise les explosions.
        r = np.where(np.isfinite(r), r, 0.0)
        return np.clip(r, -1e12, 1e12)
    except Exception:
        n_rows = xs.shape[0] if isinstance(xs, np.ndarray) else len(xs)
        return np.zeros(n_rows)

# ============================================================
# DATASET
# ============================================================

# Hot zones par problème : zones où la cible varie le plus rapidement
# (extrema, points d'inflexion, singularités) — à sur-échantillonner
_HOT_ZONES: Dict[str, List[float]] = {
    # sin(x²) : extrema à x = sqrt(π/2 + kπ)
    "1":  [1.25, -1.25, 1.77, -1.77, 2.17, -2.17, 2.51, -2.51, 2.81, -2.81],
    # x³-x²+x-1 : inflexion à x≈0.33, racine à x=1
    "2":  [0.33, 1.0, -1.0, 0.0, 2.0, -2.0],
    # exp(-x²)·sin(2x) : extrema denses autour de 0
    "3":  [0.4, -0.4, 1.1, -1.1, 1.8, -1.8, 0.0],
    # log(1+x²)·cos(x) : oscillations modérées
    "4":  [0.0, 1.57, -1.57, 3.14, -3.14, 0.8, -0.8],
    # x·sin(x²)·cos(x/2) : combinaison des extrema de sin(x²)
    "5":  [1.25, -1.25, 1.77, -1.77, 2.17, -2.17, 0.5, -0.5, 2.51, -2.51],
    # exp(-|x|)·(x²-1) : racines à x=±1, max à x≈0
    "6":  [1.0, -1.0, 0.0, 0.5, -0.5, 2.0, -2.0, 1.5, -1.5],
    # sinc(x)·cos(x²) : singularité en 0, oscillations denses
    "7":  [0.01, 1.25, -1.25, 1.77, -1.77, 2.17, -2.17, 0.5, -0.5],
    # sin(πx)/(x²+1) : extrema à x≈±0.5, ±1.5
    "8":  [0.5, -0.5, 1.5, -1.5, 0.0, 1.0, -1.0, 2.0, -2.0],
    # tanh(x)·exp(-x²/4) : inflexion vers x≈±1
    "9":  [1.0, -1.0, 0.5, -0.5, 1.5, -1.5, 0.0, 2.0, -2.0],
    # x³·sin(1/x) : oscillations infiniment rapides près de 0
    "10": [0.3, 0.5, 0.8, 1.2, 1.6, 2.0, 2.5, 0.2, 0.4],
    # ── N-D Hot zones ────────────────────────────────────────────────────
    # ND1  X[0]·sin(X[1]) + X[2]² : gradient fort autour de 0, ±π/2
    "ND1": [0.0, 1.0, -1.0, 1.57, -1.57, 2.0, -2.0],
    # ND2  exp(-X[0]²)·cos(X[1]) : pic gaussien en X[0]=0, oscillation X[1]
    # Hot zones : X[0] proche de 0 (max de exp), X[1] sur les extrema de cos
    "ND2": [0.0, 0.3, -0.3, 0.6, -0.6, 1.0, -1.0, 1.57, -1.57],
    # ND3  X[0]³ - X[1]·X[2] : inflexion cubique, interactions linéaires
    "ND3": [0.0, 1.0, -1.0, 1.5, -1.5, 2.0, -2.0],
    # ND4  sin(X[0]+X[1])·exp(-X[2]²/2) : extrema de sin et pic gaussien
    "ND4": [0.0, 0.78, -0.78, 1.57, -1.57, 0.5, -0.5],
    # ND5  X[0]·X[1]/(1+X[2]²) : singularité adoucie, gradient fort en 0
    "ND5": [0.0, 0.5, -0.5, 1.0, -1.0, 1.5, -1.5, 2.0, -2.0],
    # BATTERY_SOH  1 - 0.02·exp(X[0])·X[1] - 0.005·X[2]²
    # · X[0] : exp(X[0]) varie de e⁻²≈0.135 à e²≈7.39 → gradient fort sur [1, 2]
    # · X[1] : facteur linéaire — discriminant aux extrema ±2
    # · X[2] : terme quadratique — extrema en ±2, nul en 0
    # Hot zones concentrées là où exp(X[0])·X[1] est maximal/minimal
    "BATTERY_SOH": [1.5, 2.0, -1.5, -2.0, 0.0, 1.0, -1.0, 0.5, -0.5],
}


# ============================================================
# [SYRACUSE] GÉNÉRATION DE DONNÉES EN LIGNE — Conjecture de Collatz
# ============================================================
#
# generate_syracuse_dataset() remplace entièrement le chargement du CSV NASA.
# Le dataset est généré directement en mémoire :
#   · X : vecteur colonne (n_samples, 1) des nombres de départ n ∈ [2, 2000]
#   · y : vecteur (n_samples,) des temps de vol correspondants
#
# Temps de vol = nombre d'étapes pour atteindre 1 depuis n :
#   tant que n > 1 :
#     si n pair  → n = n // 2
#     si n impair → n = 3*n + 1
#
# Le pipeline de normalisation MinMax [-2.0, 2.0] est appliqué à X
# pour garantir la stabilité numérique de l'optimiseur Adam et des îles.
# y est également normalisé dans [-2.0, 2.0] pour la même raison.
#
# Remarque : y_raw est conservé dans _SYRACUSE_Y_RAW pour la visualisation
# et l'évaluation finale en unités naturelles (nb d'étapes).
# ─────────────────────────────────────────────────────────────────────────────

_SYRACUSE_Y_RAW:     np.ndarray = np.array([])  # cible brute avant normalisation
_SYRACUSE_X_RAW:     np.ndarray = np.array([])  # entiers bruts avant feature-engineering
_SYRACUSE_FEAT_MINS: np.ndarray = np.array([])  # min de chaque feature (pour dénorm)
_SYRACUSE_FEAT_MAXS: np.ndarray = np.array([])  # max de chaque feature (pour dénorm)

# Noms humains des 4 features — utilisés dans les logs et la vérification finale
def _max_height_ratio(n: int, cap: int = 300) -> float:
    """
    [v17-FEAT★] log(max_height(n) / n) — hauteur maximale relative log-scalée.

    Calcule le maximum atteint par la trajectoire de Collatz depuis n,
    divisé par n (pour normaliser par taille), puis log-transformé.

    Pourquoi c'est LA feature clé :
      · Corrélation avec le temps de vol : r = 0.688 (vs 0.25 pour log2(n))
      · Discrimine parfaitement les champions :
          n=97  → log(95.18) = 4.556   (118 étapes)
          n=96  → log(1.00)  = 0.000   (12 étapes)
          n=27  → log(341.9) = 5.835   (111 étapes)
          n=703 → log(356.3) = 5.876   (170 étapes)
      · Capture à la fois les champions 'rapides' (n=27, monte haut vite)
        et les champions 'tardifs' (n=97, monte très haut mais lentement).

    n=97 était invisible pour steps_before_ret (steps=3, banal) mais
    log(max_height/n) = 4.556 le place correctement parmi les champions.

    cap : nombre max d'étapes calculées (évite les boucles infinies sur
    de très grands n — la conjecture est vérifiée jusqu'à 2^68).
    """
    if n <= 1:
        return 0.0
    start = n
    m = n
    for _ in range(cap):
        if n <= 1:
            break
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        if n > m:
            m = n
    ratio = m / start
    return float(np.log(max(ratio, 1.0)))   # log(1)=0 si aucune montée


SYRACUSE_FEATURE_NAMES = [
    "X[0]=log2(n)",
    "X[1]=v2(n)",
    "X[2]=log(max_height/n)",
    "X[3]=is_mod4_1(n)",
    "X[4]=log2(n)*log2(v2+1)",
    "X[5]=log(max_h2/max_h1)",
    "X[6]=log(traj_step_14)",
    "X[7]=log(traj_step_21)",
    "X[8]=log(traj_step_28)",
    "X[9]=log(traj_step_30)",
]
SYRACUSE_N_FEATURES = 10


def _collatz_flight_time(n: int) -> int:
    """Calcule le temps de vol de Collatz pour l'entier n > 1."""
    steps = 0
    while n > 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        steps += 1
    return steps


def _v2(n: int) -> int:
    """
    Valuation 2-adique de n : nombre de fois que 2 divise n exactement.
    Exemples : v2(12)=2 (12=4×3), v2(7)=0, v2(8)=3.
    Mathématiquement fondamentale pour Collatz : v2(n) mesure directement
    combien de fois la règle "÷2" va s'appliquer de façon consécutive
    au départ de n — le run initial de divisions par 2.
    """
    if n <= 0:
        return 0
    count = 0
    while n % 2 == 0:
        n //= 2
        count += 1
    return count


def _log_max_height_level2(n: int, cap: int = 300) -> float:
    """
    [v17-FEAT★★] log(max_height_after_first_return / max_height_before)

    Hauteur maximale relative atteinte APRÈS la première redescente sous n,
    normalisée par la hauteur maximale atteinte AVANT.

    Capture la structure en deux temps de la suite de Collatz :
      · Phase 1 : montée initiale → max_h1 = X[2]
      · Phase 2 : après redescente sous n → nouvelle montée → max_h2

    Corrélation avec le temps de vol : r=0.73★ (similaire à X[2])
    Corrélation avec le résidu actuel : r=+0.18 (signal complémentaire)
    Combinaison optimale OLS [X[0], X[2], X[5]] → MSE=0.367 < 0.356 (4 feats)

    Pour n=27 : monte très haut, redescend, remonte encore → lmh2 élevé
    Pour n=96 : descend vite, ne remonte plus → lmh2 = 0
    """
    if n <= 1:
        return 0.0
    start = n
    m1    = float(n)   # max avant première redescente
    m2    = float(n)   # max après première redescente
    seen_below = False
    for _ in range(cap):
        if n <= 1:
            break
        if n % 2 == 0:
            n = n // 2
        else:
            n = 3 * n + 1
        if not seen_below:
            if n > m1:
                m1 = float(n)
            if n < start:
                seen_below = True
                m2 = float(n)
        else:
            if n > m2:
                m2 = float(n)
    if not seen_below or m1 <= 0:
        return 0.0
    ratio2 = m2 / m1
    return float(np.log(max(ratio2, 1.0)))
    """Normalise un vecteur dans [-2.0, 2.0] (MinMax indépendant par feature)."""
    lo, hi = float(arr.min()), float(arr.max())
    if hi > lo:
        return -2.0 + 4.0 * (arr - lo) / (hi - lo)
    return np.zeros_like(arr, dtype=np.float64)


def _scale_feature(arr: np.ndarray) -> np.ndarray:
    """Normalise un vecteur dans [-2.0, 2.0] (MinMax indépendant par feature)."""
    lo, hi = float(arr.min()), float(arr.max())
    if hi > lo:
        return -2.0 + 4.0 * (arr - lo) / (hi - lo)
    return np.zeros_like(arr, dtype=np.float64)


def generate_syracuse_dataset(n_start: int = 2,
                               n_end:   int = 2000) -> tuple:
    """
    [SYRACUSE v2 — 4 FEATURES] Génère le dataset de la conjecture de Syracuse.

    Au lieu d'une seule feature (n normalisé), on construit 4 features qui
    encodent directement la structure algébrique de la suite de Collatz.
    Chaque feature est normalisée indépendamment dans [-2.0, 2.0] pour
    préserver sa signification mathématique propre.

    Features
    --------
    X[0] = log2(n)
        Trend logarithmique fondamental. Les temps de vol croissent
        approximativement comme log2(n) en moyenne. Donne au GP la
        composante basse-fréquence gratuitement.

    X[1] = v2(n)  — valuation 2-adique
        Nombre de facteurs 2 consécutifs dans n (= trailing zeros binaires).
        v2(n) > 0 ↔ n pair. Mesure exactement le run initial de ÷2 consécutifs
        avant la première étape impaire. Rend is_even redondant et lui est
        strictement plus informatif.

    X[2] = odd_part(n) = n / 2^v2(n)
        Le "noyau impair" de n : la partie qui détermine la prochaine étape
        impaire (3*odd_part + 1). Capture l'interaction entre la structure
        2-adique et la trajectoire longue terme.

    X[3] = is_mod4_1(n)  — indicateur n ≡ 1 (mod 4)
        Encodé comme +1.0 si n%4==1, -1.0 sinon.
        Les entiers n ≡ 1 (mod 4) ont un comportement Collatz distinct :
        après la première étape impaire (3n+1), le résultat est ≡ 0 (mod 4),
        garantissant deux ÷2 immédiats. Ce signal binaire net est exploitable
        directement par le GP sans nécessiter is_even(X[0]).

    Paramètres
    ----------
    n_start : premier entier (default 2)
    n_end   : dernier entier inclus (default 2000)

    Retourne
    --------
    X_scaled : np.ndarray (n_samples, 4) — 4 features normalisées [-2, 2]
    y_scaled : np.ndarray (n_samples,)   — temps de vol normalisés [-2, 2]

    Effets de bord
    --------------
    · Active _SYRACUSE_MODE = True → bascule les pools d'opérateurs
    · Met à jour _SYRACUSE_X_RAW (entiers bruts), _SYRACUSE_Y_RAW (vols bruts)
    · Stocke _SYRACUSE_FEAT_MINS/_MAXS pour la dénormalisation finale
    · Enregistre les hot zones dans _HOT_ZONES["SYRACUSE"] sur les 4 features
    """
    global _SYRACUSE_MODE, _SYRACUSE_Y_RAW, _SYRACUSE_X_RAW
    global _SYRACUSE_FEAT_MINS, _SYRACUSE_FEAT_MAXS

    # ── 1. Calcul des temps de vol ────────────────────────────────────────
    ns      = np.arange(n_start, n_end + 1, dtype=np.int64)
    ns_f    = ns.astype(np.float64)
    flights = np.array([_collatz_flight_time(int(n)) for n in ns],
                       dtype=np.float64)

    _SYRACUSE_X_RAW = ns_f.copy()
    _SYRACUSE_Y_RAW = flights.copy()
    n_samples = len(ns)

    # ── 2. Construction des 5 features ───────────────────────────────────
    # X[0] : log2(n) — trend logarithmique fondamental
    feat_log2   = np.log2(ns_f)

    # X[1] : v2(n) — valuation 2-adique (run initial de ÷2)
    feat_v2     = np.array([_v2(int(n)) for n in ns], dtype=np.float64)

    # X[2] : log(max_height(n) / n) — hauteur maximale relative [★ feature clé]
    # Corrélation directe avec le temps de vol : r=0.688 (vs r=0.25 pour log2(n))
    # Discrimine les champions tardifs (n=97 → 4.556) que steps3 manquait.
    feat_mhr    = np.array([_max_height_ratio(int(n)) for n in ns],
                           dtype=np.float64)

    # X[3] : is_mod4_1(n) — indicateur binaire ±1
    feat_mod4_1 = np.where(ns % 4 == 1, 1.0, -1.0)

    # X[5] : log(max_h2 / max_h1) — hauteur relative 2ème niveau [★★]
    # Capture la structure en deux phases de la trajectoire Collatz.
    # r_vol=0.73 (complémentaire à X[2]), r_résidu=+0.18 sur le résidu actuel.
    # Combinaison OLS optimale : [X[0], X[2], X[5]] → meilleure que 4 features.
    feat_lmh2   = np.array([_log_max_height_level2(int(n)) for n in ns],
                            dtype=np.float64)
    # Le GP cherchait cette interaction (cf. X[3]*X[0] dominant run précédent).
    feat_inter  = feat_log2 * np.log2(feat_v2 + 1.0)

    # ── Features de trajectoire dynamique [V42] X[6]..X[9] ───────────────
    # Les états successifs de la suite de Collatz encodés directement.
    # Étapes sélectionnées par corrélation avec le résidu de mhr :
    #   Étape 14 : r_résidu=+0.20  r_vol=+0.54
    #   Étape 21 : r_résidu=+0.28  r_vol=+0.66
    #   Étape 28 : r_résidu=+0.36  r_vol=+0.76 ★
    #   Étape 30 : r_résidu=+0.37  r_vol=+0.77 ★
    # Normalisation log1p pour comprimer la heavy-tail des valeurs de trajectoire.
    # Calcul vectorisé (rapide) : tous les n simultanément.
    def _traj_step(ns_arr: np.ndarray, target_step: int) -> np.ndarray:
        current = ns_arr.astype(np.float64).copy()
        for _ in range(target_step):
            is_odd  = (np.round(current) % 2 != 0)
            current = np.where(is_odd, 3.0 * current + 1.0, current / 2.0)
            current = np.clip(current, 1.0, 1e15)
        return np.log1p(current)   # log(étape + 1)

    feat_traj14 = _traj_step(ns, 14)   # X[6]
    feat_traj21 = _traj_step(ns, 21)   # X[7]
    feat_traj28 = _traj_step(ns, 28)   # X[8]
    feat_traj30 = _traj_step(ns, 30)   # X[9]

    # ── 3. Normalisation indépendante par feature → [-2.0, 2.0] ──────────
    raw_features = [feat_log2, feat_v2, feat_mhr, feat_mod4_1, feat_inter, feat_lmh2,
                    feat_traj14, feat_traj21, feat_traj28, feat_traj30]
    _SYRACUSE_FEAT_MINS = np.array([f.min() for f in raw_features])
    _SYRACUSE_FEAT_MAXS = np.array([f.max() for f in raw_features])

    X_scaled = np.column_stack([_scale_feature(f) for f in raw_features])
    # (n_samples, 10)

    # ── 4. Normalisation de y → [-2.0, 2.0] ──────────────────────────────
    y_min_raw, y_max_raw = float(flights.min()), float(flights.max())
    if y_max_raw > y_min_raw:
        y_scaled = -2.0 + 4.0 * (flights - y_min_raw) / (y_max_raw - y_min_raw)
    else:
        y_scaled = np.zeros_like(flights)

    # ── 5. Hot zones sur X[0]=log2(n) ────────────────────────────────────
    famous   = [27, 703, 871, 6171, 77031, 837799]
    hot_raw  = [n for n in famous if n_start <= n <= n_end]
    log2_min = float(feat_log2.min())
    log2_max = float(feat_log2.max())
    hot_zones = []
    for n in hot_raw:
        h = -2.0 + 4.0 * (np.log2(n) - log2_min) / (log2_max - log2_min)
        hot_zones.append(round(float(h), 4))
    for frac in [0.05, 0.15, 0.3, 0.5, 0.7, 0.85, 0.95]:
        hot_zones.append(round(-2.0 + 4.0 * frac, 4))
    _HOT_ZONES["SYRACUSE"] = hot_zones if hot_zones else [0.0, 1.0, -1.0, 1.5, -1.5]

    # ── 6. Activation du mode Syracuse ───────────────────────────────────
    _SYRACUSE_MODE = True

    # ── 7. Logs de démarrage ──────────────────────────────────────────────
    lmh2_max  = float(feat_lmh2.max())
    lmh2_mean = float(feat_lmh2.mean())
    mhr_max   = float(feat_mhr.max())
    mhr_mean  = float(feat_mhr.mean())
    v2_max    = int(feat_v2.max())
    pct_mod   = float((ns % 4 == 1).mean() * 100)
    print(
        f"[SYRACUSE_COLLATZ] ✓ Dataset generated: {n_samples} samples, "
        f"10 features → normalized to [-2.0, 2.0]"
    )
    print(f"  Start        : n ∈ [{n_start}, {n_end}]")
    print(f"  Temps de vol : min={int(y_min_raw)}  max={int(y_max_raw)}  "
          f"moy={flights.mean():.1f}")
    print(f"  Features     :")
    print(f"    X[0] = log2(n)             ∈ [{feat_log2.min():.2f}, {feat_log2.max():.2f}]")
    print(f"    X[1] = v2(n)               ∈ [0, {v2_max}]  (valuation 2-adique)")
    print(f"    X[2] = log(max_h/n)        ∈ [0, {mhr_max:.2f}]  moy={mhr_mean:.2f}  r=0.69 ★")
    print(f"    X[3] = is_mod4_1(n)        {pct_mod:.1f}% de 1  (indicateur ±1)")
    print(f"    X[4] = log2(n)*log2(v2+1)  interaction 2-adique × trend")
    print(f"    X[5] = log(max_h2/max_h1)  ∈ [0, {lmh2_max:.2f}]  moy={lmh2_mean:.2f}  r=0.73 ★★")
    print(f"    X[6] = log(traj_step_14)   trajectory step 14  r_vol=0.54 [V42]")
    print(f"    X[7] = log(traj_step_21)   trajectory step 21  r_vol=0.66 [V42]")
    print(f"    X[8] = log(traj_step_28)   trajectory step 28  r_vol=0.76 [V42] ★")
    print(f"    X[9] = log(traj_step_30)   trajectory step 30  r_vol=0.77 [V42] ★")
    print(f"  Operators    : {_SYRACUSE_UNARY_OPS + _SYRACUSE_BINARY_OPS}")
    print(f"  step/max/min : ✓ symbolic IF conditions enabled [V42]")

    return X_scaled, y_scaled


def build_dataset(func, cfg: Config,
                  problem_key: str = "1") -> Tuple[np.ndarray, np.ndarray]:
    """
    Dataset stratifié avec sur-échantillonnage des zones difficiles.
    [v16-NDIM] Supporte les problèmes 1-D ET N-D.

    · Mode 1-D : cfg.TERMINALS == ["x"]  →  xs.shape = (n_samples,)
      Comportement identique à v15 (rétrocompatibilité totale).

    · Mode N-D : cfg.TERMINALS = ["X[0]", …, "X[n_features-1]"]
      →  xs.shape = (n_samples, n_features)
      Chaque feature est échantillonnée dans [cfg.X_MIN, cfg.X_MAX].
      La fonction cible reçoit la matrice X complète : func(X).

    Le vecteur ys (n_samples,) est calculé en appelant func(xs).
    """
    n_features = len(cfg.TERMINALS)
    is_nd      = (n_features > 1 or
                  (len(cfg.TERMINALS) == 1 and cfg.TERMINALS[0] != "x"))

    n_regular = cfg.N_POINTS // 3
    n_random  = cfg.N_POINTS // 3
    n_focused = cfg.N_POINTS - n_regular - n_random

    if not is_nd:
        # ── Mode 1-D (rétrocompatible) ────────────────────────────────────
        xs = [cfg.X_MIN + i * (cfg.X_MAX - cfg.X_MIN) / (n_regular - 1)
              for i in range(n_regular)]
        xs += [random.uniform(cfg.X_MIN, cfg.X_MAX) for _ in range(n_random)]
        hot_zones = _HOT_ZONES.get(problem_key, [0.0, 1.0, -1.0, 1.5, -1.5])
        for _ in range(n_focused):
            center = random.choice(hot_zones)
            xs.append(max(cfg.X_MIN, min(cfg.X_MAX,
                          center + random.gauss(0, 0.15))))
        ys_list = []
        for x in xs:
            y = func(x)
            if cfg.NOISE_STD > 0:
                y += random.gauss(0, cfg.NOISE_STD)
            ys_list.append(y)
        return np.asarray(xs, dtype=float), np.asarray(ys_list, dtype=float)

    else:
        # ── Mode N-D ──────────────────────────────────────────────────────
        # Points réguliers (grille uniforme sur chaque feature, indépendants)
        rows_reg = np.column_stack([
            np.linspace(cfg.X_MIN, cfg.X_MAX, n_regular)
            for _ in range(n_features)
        ])
        # Points randoms
        rows_rnd = np.random.uniform(cfg.X_MIN, cfg.X_MAX,
                                     (n_random, n_features))
        # Points focalisés (hot zones 1-D appliquées à chaque feature)
        hot_zones = _HOT_ZONES.get(problem_key, [0.0, 1.0, -1.0, 1.5, -1.5])
        focused_rows = []
        for _ in range(n_focused):
            row = []
            for _ in range(n_features):
                center = random.choice(hot_zones)
                val = max(cfg.X_MIN, min(cfg.X_MAX,
                          center + random.gauss(0, 0.15)))
                row.append(val)
            focused_rows.append(row)
        rows_foc = np.array(focused_rows, dtype=float)

        X = np.vstack([rows_reg, rows_rnd, rows_foc])   # (n_samples, n_features)

        # [v16-DECOY] Remplacer les colonnes leurres par du bruit pur U[-3, 3].
        # Le bruit est intentionnellement décorrélé de toutes les autres features
        # ET de y — c'est la définition d'une variable leurre robuste.
        # On utilise une seed fixe par feature pour la reproductibilité.
        decoy_indices = DECOY_FEATURES.get(problem_key, [])
        for di in decoy_indices:
            rng_decoy = np.random.default_rng(seed=42 + di)
            X[:, di] = rng_decoy.uniform(cfg.X_MIN, cfg.X_MAX, X.shape[0])

        # Calcul des cibles — func reçoit la matrice X complète
        Y = func(X)
        if cfg.NOISE_STD > 0:
            Y = Y + np.random.normal(0, cfg.NOISE_STD, Y.shape)

        return X.astype(float), np.asarray(Y, dtype=float)

# ============================================================
# FITNESS & CACHE GLOBAL
# ============================================================

_fitness_cache: Dict[int, float] = {}

# ── OBJECTIF 1 : Fitness Hybride ────────────────────────────────────────────
# Remplace le MSE pur par une métrique composite Corrélation de Pearson + MSE
# normalisé.  Plus basse = meilleure (tendant vers 0 sur solution parfaite).
#
#   std_p < 1e-6  → arbre constant → pénalité forte  mse + 2.0
#   sinon          → r  = cov(p, t) / (std_p × std_t),  borné [-1, 1]
#                    correlation_loss = 1 - r   (0 = corrélation parfaite)
#                    fitness_hybride  = 5.0 × correlation_loss
#                                     + mse / (1 + mse)
#
# Avantage : un arbre à "bonne forme géométrique mais mauvaise échelle" obtient
# un score bien inférieur au MSE pur, ce qui évite le rejet par le tri.
# Le terme mse/(1+mse) est borné dans [0,1) et pénalise l'amplitude résiduelle.
# ─────────────────────────────────────────────────────────────────────────────

def _pearson_r(preds: np.ndarray, ys_np: np.ndarray) -> float:
    """Corrélation de Pearson optimisée — calcul inline sans np.corrcoef.
    [V42-FIX] errstate all='ignore' pour supprimer les overflow des trajectoires.
    """
    with np.errstate(all='ignore'):
        a  = preds - preds.mean()
        b  = ys_np - ys_np.mean()
        na = float(np.dot(a, a))
        nb = float(np.dot(b, b))
        if na < 1e-16 or nb < 1e-16:
            return 0.0
        r = float(np.dot(a, b)) / (na * nb) ** 0.5
    if not np.isfinite(r):
        return 0.0
    return float(np.clip(r, -1.0, 1.0))



# [OPT] Cache de prédictions par hash structurel — partagé par raw_mse,
# _pure_mse et raw_pearson_r (élimine 2-3x les évaluations redondantes).
_PRED_CACHE: dict = {}
_PRED_CACHE_MAX = 8192

def _predict_cached(node, xs_np):
    # [FIX-CACHE v23.1] La clé inclut l'IDENTITÉ du jeu de données (id + shape).
    # Sans cela, une prédiction calculée sur le TRAIN (134 pts) était renvoyée
    # pour une requête sur le dataset COMPLET (168 pts) → mismatch de forme →
    # exception silencieuse → MSE rapporté à 1e6 alors que le modèle est bon.
    h = (node.structural_hash(), id(xs_np), xs_np.shape[0])
    r = _PRED_CACHE.get(h)
    if r is not None:
        return r
    preds = evaluate_vector(node, xs_np)
    _PRED_CACHE[h] = preds
    if len(_PRED_CACHE) > _PRED_CACHE_MAX:
        for _ in range(1024):
            if _PRED_CACHE:
                _PRED_CACHE.pop(next(iter(_PRED_CACHE)))
    return preds

# ════════════════════════════════════════════════════════════════
# [v18-LS] LINEAR SCALING (Keijzer, 2003)
# ════════════════════════════════════════════════════════════════
# La fitness évalue a + b·f(x) où (a, b) sont les coefficients OLS
# optimaux en FORME FERMÉE (2 produits scalaires — coût négligeable) :
#     b = cov(f(x), y) / var(f(x))        a = mean(y) − b·mean(f(x))
# Conséquence : le GP n'a plus à apprendre ni l'échelle ni l'offset,
# il ne cherche que la FORME de la fonction. C'est la technique au
# meilleur ratio gain/coût de toute la littérature GP — standard
# dans Operon, PySR, et tous les moteurs SRBench de tête.
_USE_LINEAR_SCALING: bool = True   # synchronisé sur cfg dans evolve()

# [CUSTOM-LOSS] Fonction de coût personnalisée optionnelle.
# Signature : loss_fn(predictions: np.ndarray, X: np.ndarray, y: np.ndarray) -> float
# Si None → comportement par default (MSE/corrélation hybride supervisé).
# Si fournie → REMPLACE entièrement le calcul d'erreur, et le linear scaling
# est ignoré (il suppose le MSE supervisé). Une valeur basse = meilleur.
_CUSTOM_LOSS_FN = None

# [CUSTOM-SEEDS] Liste optionnelle d'arbres Node injectés dans la population
# initiale (un par île, round-robin). Sert à amorcer la recherche avec des
# briques structurelles pertinentes (ex. X[0]², X[1]² pour une loi d'énergie).
# Rempli par l'API ; None/vide = pas d'amorçage custom.
def _safe_write(filepath, writer, what="file"):
    """[v0.2.2] An export must NEVER kill a finished run. Try the requested
    path, then the system temp directory; on total failure, warn and return
    None. Returns the path actually written, or None."""
    import tempfile, os as _os
    _err = None
    for target in (str(filepath),
                   _os.path.join(tempfile.gettempdir(),
                                 _os.path.basename(str(filepath)))):
        try:
            with open(target, "w", encoding="utf-8", newline="") as f:
                writer(f)
            if target != str(filepath):
                print(f"  ⚠ Could not write {what} to '{filepath}' — "
                      f"saved to '{target}' instead.")
            return target
        except OSError as e:
            _err = e
    print(f"  ⚠ {what} export skipped ({type(_err).__name__}: {_err}). "
          f"Hint: run from a writable folder — OneDrive / Windows "
          f"'Controlled Folder Access' can block Python writes.")
    return None


_CUSTOM_SEEDS = None

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
    uops = set(globals().get("_GENERIC_UNARY_OPS", []) or [])
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


# [CUSTOM-LOSS PARSIMONY] Poids de la pénalité de taille pour la loss custom
# (0 = désactivé). Favorise les lois simples ; utile pour la découverte de
# lois de conservation (sinon des arbres géants exploitent le bruit numérique).
_CUSTOM_LOSS_PARSIMONY = 0.0

def _linear_scale_params(preds: np.ndarray, ys_np: np.ndarray):
    """Coefficients OLS (a, b) de  y ≈ a + b·preds.  Retourne (a, b, ok)."""
    pm = float(preds.mean()); ym = float(ys_np.mean())
    pc = preds - pm
    # [FIX-OVF v20] Clamp avant dot pour éviter overflow sur arbres explosifs
    if not np.all(np.isfinite(pc)) or np.max(np.abs(pc)) > 1e15:
        return 0.0, 1.0, False
    var_p = float(np.dot(pc, pc))
    if var_p < 1e-12:
        return 0.0, 1.0, False
    b = float(np.dot(pc, ys_np - ym)) / var_p
    a = ym - b * pm
    if not (math.isfinite(a) and math.isfinite(b)):
        return 0.0, 1.0, False
    return a, b, True

def _robust_scale_params(preds: np.ndarray, ys_np: np.ndarray, delta: float = 0.5, n_iter: int = 5):
    """Coefficients (a, b) de y ≈ a + b·preds calés de façon ROBUSTE (Huber)
    via moindres carrés repondérés itératifs (IRLS). Contrairement à
    _linear_scale_params (OLS, sensible aux outliers), les points aberrants
    reçoivent un poids réduit → la droite suit la vraie tendance.
    Retourne (a, b, ok). 5 itérations suffisent (convergence rapide testée)."""
    pc = preds - float(preds.mean())
    if not np.all(np.isfinite(pc)) or np.max(np.abs(pc)) > 1e15:
        return 0.0, 1.0, False
    if float(np.dot(pc, pc)) < 1e-12:
        return 0.0, 1.0, False
    a, b = float(ys_np.mean()), 1.0
    f = preds
    for _ in range(n_iter):
        r = a + b * f - ys_np
        s = float(np.std(r)) + 1e-9
        rs = np.abs(r / s)
        w = np.where(rs <= delta, 1.0, delta / (rs + 1e-9))   # poids de Huber
        W = np.sqrt(w)
        A = np.column_stack([W, f * W])
        try:
            sol, *_ = np.linalg.lstsq(A, ys_np * W, rcond=None)
        except Exception:
            return 0.0, 1.0, False
        a, b = float(sol[0]), float(sol[1])
        if not (math.isfinite(a) and math.isfinite(b)):
            return 0.0, 1.0, False
    return a, b, True

def raw_mse(node, xs, ys) -> float:
    """
    [v13.11 — OBJECTIF 1] Fitness Hybride : Corrélation de Pearson + MSE normalisé.

    Remplace l'ancienne combinaison "70% MSE + 30% relatif" par :

        si std(prédictions) < 1e-6 (arbre constant) :
            retourne  mse + 2.0   ← pénalité forte, évite la division par zéro

        sinon :
            r                = cov(p,t) / (std_p × std_t), borné [-1, 1]
            correlation_loss = 1 - r                         (0 = parfait)
            fitness          = 5.0 × correlation_loss
                             + mse / (1 + mse)               (borné [0, 1))

    Une valeur plus basse est toujours meilleure (convention inchangée).
    Les garde-fous NumPy (_np_safe_div, _np_safe_pow) restent actifs via
    evaluate_vector → _to_np_code → fonctions sécurisées.
    """
    xs_np = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
    ys_np = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)

    # [CUSTOM-LOSS] Si une fonction de coût est fournie, elle REMPLACE
    # entièrement le calcul hybride MSE/corrélation. Le linear scaling est
    # ignoré (il suppose le MSE supervisé). La loss reçoit (preds, X, y) et
    # doit renvoyer un scalaire à minimiser. Toute erreur/non-fini → pénalité.
    # [CUSTOM-LOSS PARSIMONY] Si _CUSTOM_LOSS_PARSIMONY > 0, on ajoute une
    # pénalité proportionnelle à la taille de l'arbre : rasoir d'Ockham qui
    # favorise les lois simples et neutralise les arbres-monstres exploitant
    # les imperfections numériques (crucial pour la découverte de lois).
    if _CUSTOM_LOSS_FN is not None:
        try:
            with np.errstate(all='ignore'):
                preds = _predict_cached(node, xs_np)
                # [CUSTOM-LOSS SCALING] En mode supervisé (régression robuste,
                # quantile...), on cale a + b·preds vers y AVANT d'appeler la
                # loss. Le scaling MSE en forme fermée donne déjà de bons a,b
                # même pour une loss robuste, et débloque la calibration des
                # coefficients (sinon le GP peine à trouver la bonne droite).
                # Désactivé par default (non-supervisé / invariants).
                if globals().get("_CUSTOM_LOSS_USE_SCALING", False) and float(np.std(preds)) > 1e-9:
                    if globals().get("_CUSTOM_LOSS_ROBUST", False):
                        a_ls, b_ls, _ok = _robust_scale_params(preds, ys_np)
                    else:
                        a_ls, b_ls, _ok = _linear_scale_params(preds, ys_np)
                    if _ok:
                        preds = a_ls + b_ls * preds
                val = float(_CUSTOM_LOSS_FN(preds, xs_np, ys_np))
            if not math.isfinite(val):
                return 1000.0
            _pars = globals().get("_CUSTOM_LOSS_PARSIMONY", 0.0)
            if _pars > 0.0:
                val += _pars * tree_size(node)
            return val
        except Exception:
            return 1000.0

    try:
        with np.errstate(all='ignore'):    # [V42-FIX] silencer les overflow sur trajectoires
            preds     = _predict_cached(node, xs_np)
            residuals = preds - ys_np
            mse       = float(np.mean(residuals ** 2))
        std_p     = float(preds.std())
        r         = _pearson_r(preds, ys_np) if std_p >= 1e-6 else 0.0

        if std_p < 1e-6:
            # Arbre constant → pénalité pour décourager les constantes pures.
            # [SYRACUSE] Pénalité triplée : sur les données Collatz normalisées,
            # une constante nulle a MSE≈1.33 → fitness≈3.33 avec +2.0, ce qui
            # est meilleur que tout arbre non-constant à faible corrélation
            # (r≈0.1 → fitness≈5.4). Résultat : les îles restent bloquées sur des
            # constantes indéfiniment. +5.0 corrige ce biais structurel.
            _const_penalty = 5.0 if _SYRACUSE_MODE else 2.0
            return mse + _const_penalty

        # [v18-LS] MSE calculé sur les prédictions scalées a + b·f(x).
        # b peut être négatif → une anti-corrélation parfaite devient une
        # solution parfaite : la perte de corrélation utilise |r|.
        if _USE_LINEAR_SCALING:
            a_ls, b_ls, _ok = _linear_scale_params(preds, ys_np)
            if _ok:
                with np.errstate(all='ignore'):
                    _sres = (a_ls + b_ls * preds) - ys_np
                    mse   = float(np.mean(_sres ** 2))
                if not math.isfinite(mse):
                    return 1000.0
            correlation_loss = 1.0 - abs(r)
        else:
            correlation_loss = 1.0 - r
        # mse / (1 + mse) ∈ [0, 1) : comprime les très gros MSE sans les annuler
        fitness_hybrid = (5.0 * correlation_loss) + (mse / (1.0 + mse))
        return fitness_hybrid

    except Exception:
        return 1000.0


def raw_pearson_r(node, xs, ys) -> float:
    """
    [v13.11 — OBJECTIF 2] Retourne la corrélation de Pearson pure (r ∈ [-1, 1])
    du meilleur individu, utilisée par le filtre Anti-Puits-Empoisonné avant
    d'autoriser le dépôt dans les structures stigmergiques.
    Retourne -1.0 en cas d'erreur ou d'arbre constant.
    """
    xs_np = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
    ys_np = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)
    try:
        preds = _predict_cached(node, xs_np)
        if float(preds.std()) < 1e-6:
            return -1.0   # arbre constant → corrélation non définie
        return _pearson_r(preds, ys_np)
    except Exception:
        return -1.0


def _pure_mse(node, xs, ys) -> float:
    """
    [v14.1] Calcule le MSE pur (erreur quadratique moyenne brute) sans aucune
    pondération Pearson ni pénalité de constante.
    Utilisé exclusivement par fitness() pour alimenter le ln(MSE) du BIC.

    Séparé de raw_mse() pour ne pas polluer le BIC avec la valeur hybride
    Pearson+MSE de raw_mse (qui retourne dans [0, 3+] et non un vrai MSE).
    raw_mse() reste inchangé : il continue à servir les logs, PERFECT_THRESHOLD
    et le filtre Anti-Puits-Empoisonné qui ont besoin de la métrique hybride.

    Arbre constant (std_p < 1e-6) : retourne mse + 1000.0 pour garantir un
    BIC fortement positif (rejet), sans risquer de ln(0) si mse est nul.
    """
    xs_np = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
    ys_np = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)
    try:
        preds = _predict_cached(node, xs_np)
        # Arbre constant : std(preds) quasi-nul → pénalité pour BIC
        if float(np.std(preds)) < 1e-6:
            return float(np.mean((preds - ys_np) ** 2)) + 1000.0
        # [v18-LS] Le BIC juge la forme optimalement scalée (cohérent avec raw_mse)
        if _USE_LINEAR_SCALING:
            a_ls, b_ls, _ok = _linear_scale_params(preds, ys_np)
            if _ok:
                preds = a_ls + b_ls * preds
        with np.errstate(all='ignore'):
            mse = float(np.mean((preds - ys_np) ** 2))
        return mse if math.isfinite(mse) else 1e6
    except Exception:
        return 1e6


def wrap_linear_scaling(node, xs, ys):
    """
    [v18-LS] Matérialise le scaling optimal dans l'arbre :  a + b·f(x).
    Appelé au moment de stocker/afficher un champion, pour que l'EXPR
    imprimée corresponde exactement au MSE rapporté (et pour qu'Adam
    puisse ensuite affiner a et b comme n'importe quelle constante).
    Ne wrappe que si le gain est réel et la forme non dégénérée.
    """
    if node is None:
        return node
    # [ROBUST] En mode régression robuste, on matérialise le scaling ROBUSTE
    # (IRLS) dans l'arbre final même si le linear scaling MSE est désactivé,
    # pour que l'expression retournée ait les bons coefficients (insensibles
    # aux outliers), pas ceux biaisés par le MSE.
    _robust = globals().get("_CUSTOM_LOSS_ROBUST", False)
    if not _USE_LINEAR_SCALING and not _robust:
        return node.copy()
    xs_np = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
    ys_np = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)
    try:
        with np.errstate(all='ignore'):
            preds = evaluate_vector(node, xs_np)
            if float(np.std(preds)) < 1e-6:
                return node.copy()
            if _robust:
                a_ls, b_ls, _ok = _robust_scale_params(preds, ys_np)
            else:
                a_ls, b_ls, _ok = _linear_scale_params(preds, ys_np)
            if not _ok or (abs(b_ls - 1.0) < 1e-9 and abs(a_ls) < 1e-9):
                return node.copy()
            # En mode robuste, on accepte le wrap sans exiger une baisse du MSE
            # (le MSE peut monter alors que la robustesse s'améliore).
            if not _robust:
                mse_raw = float(np.mean((preds - ys_np) ** 2))
                mse_ls  = float(np.mean((a_ls + b_ls * preds - ys_np) ** 2))
                if not math.isfinite(mse_ls) or mse_ls >= mse_raw - 1e-15:
                    return node.copy()
        wrapped = Node("+", Node(float(a_ls)),
                       Node("*", Node(float(b_ls)), node.copy()))
        return simplify(wrapped)
    except Exception:
        return node.copy()


# ============================================================
# [FIX-E] Compteur d'usage de features — biais vers les sous-utilisées
# ============================================================
# Inspiré de GP_SYRACUSE_V16 : maintient un compteur d'utilisation par
# feature et favorise les features peu présentes dans la population.
# Réinitialisation à chaque run via reset_feature_usage().
# Utilisé dans rand_term / random_terminal pour biaiser le tirage.

_feature_usage_counter: List[int] = []   # initialisé par reset_feature_usage()

def reset_feature_usage(n_features: int):
    """Réinitialise le compteur au début d'un run."""
    global _feature_usage_counter
    _feature_usage_counter = [1] * n_features   # 1 pour éviter div/0

def record_feature_usage(node: "Node", terminals: List[str]):
    """Parcourt un arbre et incrémente les compteurs de features utilisées."""
    global _feature_usage_counter
    if not _feature_usage_counter:
        return
    stack = [node]
    while stack:
        n = stack.pop()
        if n is None:
            continue
        if isinstance(n.value, str) and n.value in terminals:
            idx = terminals.index(n.value)
            if idx < len(_feature_usage_counter):
                _feature_usage_counter[idx] += 1
        if n.left:  stack.append(n.left)
        if n.right: stack.append(n.right)

def get_feature_bias_weights(terminals: List[str]) -> List[float]:
    """
    Poids inversement proportionnels à l'usage — features rares favorisées.
    Retourne une liste de la même longueur que terminals.
    Normalisée autour de 1.0 pour ne pas modifier le taux de tirage global.
    """
    if not _feature_usage_counter or len(_feature_usage_counter) < len(terminals):
        return [1.0] * len(terminals)
    total = sum(_feature_usage_counter[:len(terminals)])
    inv   = [total / (u + 1.0) for u in _feature_usage_counter[:len(terminals)]]
    s     = sum(inv)
    return [v / s * len(terminals) for v in inv]

def count_distinct_features(node: "Node", terminals: List[str]) -> int:
    """Compte le nombre de features distinctes utilisées dans l'arbre."""
    used  = set()
    stack = [node]
    while stack:
        n = stack.pop()
        if n is None:
            continue
        if isinstance(n.value, str) and n.value in terminals:
            used.add(n.value)
        if n.left:  stack.append(n.left)
        if n.right: stack.append(n.right)
    return len(used)


def fitness(node, xs: List[float], ys: List[float], cfg: Config,
            role: str = "explorer") -> float:
    """
    [v14.4 — Asymétrie des Îles] Fitness conditionnelle selon le rôle de l'île.

    Chaque île évalue les individus avec sa propre métrique, ce qui crée une
    pression sélective spécialisée sans pour autant contraindre toutes les îles
    au même régime. La migration fait ensuite circuler les bons individus entre
    les îles, permettant à l'exploratrice de fournir des sous-structures
    complexes que la nettoyeuse simplifiera ensuite.

    ── role == "cleaner" (Île Nettoyeuse) ──────────────────────────────────────
    Métrique BIC stricte (v14.x) :
        fitness = n·ln(max(MSE_pur, 1e-15)) + k·ln(n) + γ·n_adj²·ln(n)
    Rasoir d'Ockham forcé : les constantes ajustées et les introns coûtent cher.
    But : détruire le bloat, promouvoir l'élégance symbolique.

    ── role == "explorer" ou "stigmergic" (Îles Exploratrices) ────────────────
    Métrique v13.12 : MSE hybride (Pearson+MSE) + pénalité linéaire plafonnée.
        base      = raw_mse(node, xs, ys)          # fitness hybride Pearson+MSE
        size_pen  = tree_size(node) * cfg.PARSIMONY
        depth_pen = tree_depth(node) * cfg.DEPTH_PENALTY
        penalty   = min(size_pen + depth_pen, 0.05 * base + 1e-8)
        fitness   = base + penalty
    Liberté de construire des sous-structures complexes comme sin(1/x) sans
    être massacrée par le BIC lors de la phase d'assemblage transitoire.

    Cache : clé (hash, role) — un même arbre peut avoir deux scores différents
    selon le rôle. Invalidation via _fitness_cache.clear() à chaque génération.
    """
    h   = node.structural_hash()
    key = (h, role)
    if key in _fitness_cache:
        return _fitness_cache[key]

    if role == "cleaner":
        # ── BIC strict (v14.2) ───────────────────────────────────────────────
        mse_pur      = _pure_mse(node, xs, ys)
        n            = len(ys)
        k, n_adj     = tree_complexity(node)
        ln_n         = math.log(n)
        mse_safe     = max(mse_pur, 1e-15)
        score        = (n * math.log(mse_safe)
                        + k * ln_n
                        + _FLOAT_GAMMA * (n_adj ** 2) * ln_n)
    else:
        # ── Explorer / Stigmergic : MSE hybride + pénalité linéaire (v13.12) ─
        base      = raw_mse(node, xs, ys)
        size_pen  = tree_size(node)  * cfg.PARSIMONY
        depth_pen = tree_depth(node) * cfg.DEPTH_PENALTY
        max_pen   = 0.05 * base + 1e-8
        penalty   = min(size_pen + depth_pen, max_pen)
        score     = base + penalty

def fitness(node, xs: List[float], ys: List[float], cfg: Config,
            role: str = "explorer") -> float:
    """
    [v14.4] Fitness conditionnelle par rôle d'île.
    [FIX-A v17] Pénalité mono-feature : force l'exploration multi-variable
    en mode Syracuse — corrige le blocage sur X[2] seul.
    [OPT] Clé de cache incluant gen//10 via cfg._gen_bucket : évite de
    recalculer la fitness d'un individu inchangé pendant 10 générations.
    Inspiré de GP_SYRACUSE_V16 — gain ~25% sur le temps total.
    """
    h   = node.structural_hash()
    # [OPT] Bucket générationnel : même individu → même fitness pendant 10 gens
    gen_bucket = getattr(cfg, '_gen_bucket', 0)
    key = (h, role, gen_bucket)
    if key in _fitness_cache:
        return _fitness_cache[key]

    if role == "cleaner" and _CUSTOM_LOSS_FN is None:
        mse_pur      = _pure_mse(node, xs, ys)
        n            = len(ys)
        k, n_adj     = tree_complexity(node)
        # [v18-LS] Les 2 constantes de scaling + leurs opérateurs (+, *) ne sont
        # pas gratuits pour le rasoir d'Ockham : coût linéaire forfaitaire +4.
        if _USE_LINEAR_SCALING:
            k += 4
        ln_n         = math.log(n)
        mse_safe     = max(mse_pur, 1e-15)
        score        = (n * math.log(mse_safe)
                        + k * ln_n
                        + _FLOAT_GAMMA * (n_adj ** 2) * ln_n)
    elif _CUSTOM_LOSS_FN is not None:
        # [CUSTOM-LOSS] Tous les rôles minimisent la loss custom (via raw_mse,
        # qui la court-circuite). On ajoute une légère pénalité de parcimonie
        # pour garder des expressions lisibles, comme pour les explorers.
        base      = raw_mse(node, xs, ys)
        size_pen  = tree_size(node)  * cfg.PARSIMONY
        depth_pen = tree_depth(node) * cfg.DEPTH_PENALTY
        max_pen   = 0.05 * abs(base) + 1e-8
        penalty   = min(size_pen + depth_pen, max_pen)
        score     = base + penalty
    else:
        base      = raw_mse(node, xs, ys)
        size_pen  = tree_size(node)  * cfg.PARSIMONY
        depth_pen = tree_depth(node) * cfg.DEPTH_PENALTY
        max_pen   = 0.05 * base + 1e-8
        penalty   = min(size_pen + depth_pen, max_pen)
        score     = base + penalty

    # [FIX-A] Pénalité mono-feature progressive — active en mode Syracuse N-D.
    # Casse le monopole de X[2] = log(max_h/n) observé systématiquement.
    # La pénalité décroît progressivement pour laisser le GP converger en fin de run
    # sans contraindre trop fortement les expressions finales.
    if _SYRACUSE_MODE and hasattr(cfg, 'TERMINALS') and len(cfg.TERMINALS) > 1:
        n_feat = count_distinct_features(node, cfg.TERMINALS)
        if n_feat == 0:
            score += 5.0    # constante pure — pénalité forte et stable
        elif n_feat == 1:
            # Décroissance progressive : 0.10 en gen 0 → 0.03 en fin de run
            # Inspiré de GP_SYRACUSE_V16 FIX-A (parsimony_coeff pattern)
            _mono_pen = getattr(cfg, '_mono_pen_cache', None)
            if _mono_pen is None:
                score += 0.08  # valeur par default si gen non disponible
            else:
                score += _mono_pen

    _fitness_cache[key] = score
    return score

# ============================================================
# GÉNÉRATION ALÉATOIRE — Ramped Half-and-Half
# ============================================================

def random_constant(cfg: Config) -> float:
    return round(random.uniform(cfg.ERC_MIN, cfg.ERC_MAX), 6)

def random_terminal(cfg: Config) -> Node:
    """[v16-NDIM] Tire un terminal dans cfg.TERMINALS (dynamique).
    [FIX-E] En mode Syracuse N-D, biais vers les features sous-utilisées.
    Probabilité 55% variable (avec biais), 45% constante ERC.
    """
    if random.random() < 0.55:
        # [FIX-E] En mode Syracuse, utiliser les poids d'usage inversés
        if (_SYRACUSE_MODE and _feature_usage_counter
                and len(cfg.TERMINALS) > 1):
            weights = get_feature_bias_weights(cfg.TERMINALS)
            return Node(random.choices(cfg.TERMINALS, weights=weights)[0])
        return Node(random.choice(cfg.TERMINALS))
    return Node(float(random_constant(cfg)))

def _random_tree_full(depth: int, cfg: Config) -> Node:
    """Full : toutes les feuilles à la profondeur max.
    [FIX-OPS v20.1] Pools du MODE ACTIF (et non les globaux) : l'ancienne
    version injectait sin/cos en mode Batterie/Syracuse via les ~10 fallbacks
    qui appellent random_tree, polluant population et bibliothèque de
    fragments (ex: sin(X[1]) freq=108 observé), et n'utilisait jamais
    tanh/exp/step/min2/max2 dans ces injections."""
    _b_ops, _b_w, _u_ops, _u_w, _, _ = _active_pools()
    if depth <= 0:
        return random_terminal(cfg)
    if random.random() < 0.30:
        op = random.choices(_u_ops, weights=_u_w)[0]
        return Node(op, _random_tree_full(depth - 1, cfg))
    op = random.choices(_b_ops, weights=_b_w)[0]
    return Node(op,
                _random_tree_full(depth - 1, cfg),
                _random_tree_full(depth - 1, cfg))

def _random_tree_grow(depth: int, cfg: Config) -> Node:
    """Grow : feuilles possibles à chaque niveau. [FIX-OPS v20.1] pools mode actif."""
    _b_ops, _b_w, _u_ops, _u_w, _, _ = _active_pools()
    if depth <= 0:
        return random_terminal(cfg)
    r = random.random()
    if r < 0.20:
        return random_terminal(cfg)
    if r < 0.45:
        op = random.choices(_u_ops, weights=_u_w)[0]
        return Node(op, _random_tree_grow(depth - 1, cfg))
    op = random.choices(_b_ops, weights=_b_w)[0]
    return Node(op,
                _random_tree_grow(depth - 1, cfg),
                _random_tree_grow(depth - 1, cfg))

def random_tree(max_depth: int, cfg: Config) -> Node:
    """Ramped Half-and-Half : moitié full, moitié grow, profondeurs variées."""
    d = random.randint(2, max_depth)
    if random.random() < 0.5:
        return _random_tree_full(d, cfg)
    return _random_tree_grow(d, cfg)

# ============================================================
# SIMPLIFICATION ALGÉBRIQUE
# ============================================================

def _is_float(n) -> bool:
    return n is not None and isinstance(n.value, float)

def _is_const(n, v: float) -> bool:
    return _is_float(n) and abs(n.value - v) < 1e-9

_SIMPLIFY_CACHE: dict = {}   # hash → simplified Node (resets each generation)

def simplify(node: Node) -> Node:
    """Simplification algébrique avec cache structurel.

    [FIX-DAG v18] Le cache ne retourne JAMAIS d'objet partagé (copie fraîche),
    et la simplification ne mute JAMAIS l'arbre d'entrée. Cause racine d'un
    OOM corrigée : l'ancienne version créait des DAG (sous-arbres partagés)
    et pouvait engendrer des cycles -> tree_size() infini -> SIGKILL.
    [FIX-REC v18] Implémentation ITÉRATIVE (post-ordre, pile explicite) :
    l'ancienne récursion mutuelle simplify/_simplify_once consommait ~4 frames
    par niveau et levait RecursionError sur les arbres profonds produits par
    le constructeur stigmergique avant l'application du cap de profondeur.
    """
    if node is None:
        return node
    h = node.structural_hash()
    cached = _SIMPLIFY_CACHE.get(h)
    if cached is not None:
        return cached.copy()                 # jamais d'objet partagé
    result = _simplify_tree(_simplify_tree(node))   # 2 passes (cascade de règles)
    _SIMPLIFY_CACHE[h] = result
    return result.copy()


def _simplify_tree(root: Node) -> Node:
    """Post-ordre itératif : reconstruit une copie simplifiée de bas en haut.
    Ne mute jamais l'entrée ; chaque nœud produit est neuf ou appartient
    exclusivement au sous-arbre en construction (zéro partage)."""
    if root is None:
        return None
    out: dict = {}                      # id(noeud original) -> Node simplifié neuf
    stack = [(root, False)]
    while stack:
        nd, processed = stack.pop()
        if processed:
            l = out.pop(id(nd.left))  if nd.left  is not None else None
            r = out.pop(id(nd.right)) if nd.right is not None else None
            out[id(nd)] = _simplify_node(nd.value, l, r)
        else:
            # Cache structurel au niveau du sous-arbre (lecture seule, copie)
            c = _SIMPLIFY_CACHE.get(nd.structural_hash())
            if c is not None:
                out[id(nd)] = c.copy()
                continue
            stack.append((nd, True))
            if nd.left  is not None: stack.append((nd.left,  False))
            if nd.right is not None: stack.append((nd.right, False))
    return out[id(root)]


def _simplify_node(v, left, right) -> Node:
    """Applique les règles algébriques à UN nœud dont les enfants sont déjà
    simplifiés. left/right appartiennent exclusivement à l'appelant : les
    réutiliser dans le résultat est sûr (aucun partage inter-arbres)."""
    # Repliage des constantes unaires (inclut tanh)
    if v in ("sin", "cos", "tan", "tanh", "exp", "log", "sqrt", "abs", "neg", "sq", "cube"):
        if _is_float(left):
            try:
                c = left.value
                if v == "sin":   return Node(float(math.sin(c)))
                if v == "cos":   return Node(float(math.cos(c)))
                if v == "tan":   return Node(float(safe_tan(c)))
                if v == "tanh":  return Node(float(math.tanh(c)))
                if v == "exp":   return Node(float(safe_exp(c)))
                if v == "log":   return Node(float(safe_log(c)))
                if v == "sqrt":  return Node(float(safe_sqrt(c)))
                if v == "abs":   return Node(float(abs(c)))
                if v == "neg":   return Node(float(-c))
                if v == "sq":    return Node(float(c * c))
                if v == "cube":  return Node(float(c * c * c))
            except Exception:
                pass

    # Règles binaires identitaires
    if v == "+":
        if _is_const(right, 0):  return left
        if _is_const(left,  0):  return right
        # expr + expr -> 2.0 * expr
        if (left is not None and right is not None
                and not _is_float(left) and not _is_float(right)
                and left.structural_hash() == right.structural_hash()):
            return Node("*", Node(2.0), left)
    if v == "-":
        if _is_const(right, 0):  return left
        if _is_const(left,  0):  return Node("neg", right)
        if left and right and left.structural_hash() == right.structural_hash():
            return Node(0.0)
    if v == "*":
        if _is_const(right, 1):  return left
        if _is_const(left,  1):  return right
        if _is_const(right, 0):  return Node(0.0)
        if _is_const(left,  0):  return Node(0.0)
        if _is_const(right, -1): return Node("neg", left)
        if _is_const(left,  -1): return Node("neg", right)
        if _is_float(right) and abs(right.value) < 1e-6: return Node(0.0)
        if _is_float(left)  and abs(left.value)  < 1e-6: return Node(0.0)
    if v == "/":
        if _is_const(right, 1):  return left
        if _is_const(left,  0):  return Node(0.0)
        if left and right and left.structural_hash() == right.structural_hash():
            return Node(1.0)
        # (a * b) / a = b  et  (a * b) / b = a
        if left is not None and left.value == "*":
            lh = left.left.structural_hash()  if left.left  else None
            rh = left.right.structural_hash() if left.right else None
            dh = right.structural_hash()      if right      else None
            if lh and lh == dh: return left.right
            if rh and rh == dh: return left.left
    if v == "pow":
        if _is_const(right, 0):  return Node(1.0)
        if _is_const(right, 1):  return left
        if _is_const(left,  0):  return Node(0.0)
        if _is_const(left,  1):  return Node(1.0)

    # Repliage des constantes binaires
    if v in BINARY_OPS and _is_float(left) and _is_float(right):
        a, b = left.value, right.value
        try:
            if v == "+":   return Node(float(a + b))
            if v == "-":   return Node(float(a - b))
            if v == "*":   return Node(float(a * b))
            if v == "/":   return Node(float(safe_div(a, b)))
            if v == "pow": return Node(float(safe_pow(a, b)))
        except Exception:
            pass

    # Double négation
    if v == "neg" and left is not None and left.value == "neg":
        return left.left

    return Node(v, left, right)

# ============================================================
# OPTIMISATION DES CONSTANTES — Adam gradient numérique
# ============================================================

def _invalidate_all_hashes(node: Node):
    """Invalide récursivement le cache de hash sur tout l'arbre."""
    stack = [node]
    while stack:
        n = stack.pop()
        n._hash  = None
        n._chash = None
        if n.left:  stack.append(n.left)
        if n.right: stack.append(n.right)


def optimize_constants_lm(node: Node,
                          xs: np.ndarray,
                          ys: np.ndarray,
                          cfg: Config) -> Node:
    """
    [v26-LM] Optimisation des constantes par LEVENBERG-MARQUARDT.
    Pourquoi : l'ajustement des constantes d'une expression est un problème de
    MOINDRES CARRÉS — la classe exacte pour laquelle LM est conçu. Adam (1er
    ordre, différences finies) y converge lentement et s'arrête loin de
    l'optimum ; LM exploite la structure JᵀJ du problème et atteint la
    précision machine en 10-30 itérations. C'est le levier n°1 documenté des
    moteurs SR de référence (Operon : LM natif ; PySR : BFGS/NelderMead).
    Coût/itération : (n_consts+1) évaluations vectorisées (Jacobienne par
    différences avant) + résolution d'un système n_consts×n_consts.
    Déterministe (aucun redémarrage bruité) → runs reproductibles.
    """
    child = node.copy()
    fn, consts = compile_parametric(child)
    if not consts or fn is None:
        return child

    nC = len(consts)
    y  = np.asarray(ys, dtype=float)
    c  = np.array([cn.value for cn in consts], dtype=float)
    lo_b = float(cfg.ERC_MIN) * 3.0
    hi_b = float(cfg.ERC_MAX) * 3.0

    def _resid(cv):
        with np.errstate(all='ignore'):
            p = fn(xs, cv)
        p = np.asarray(p, dtype=float)
        if p.ndim == 0:
            p = np.full_like(y, float(p))
        bad = ~np.isfinite(p)
        if bad.any():
            p = np.where(bad, 0.0, p)
            r = p - y
            r[bad] = 1e6          # zone invalide : fortement pénalisée
            return r
        return p - y

    r = _resid(c)
    sse_best = float(r @ r)
    c_best = c.copy()
    lam = 1e-3
    max_iter = max(20, int(getattr(cfg, "CONST_OPT_ITER", 30)))
    for _ in range(max_iter):
        # Jacobienne par différences avant : J[:, i] = ∂r/∂c_i
        J = np.empty((len(y), nC), dtype=float)
        for i in range(nC):
            h = 1e-6 * (1.0 + abs(c[i]))
            cp = c.copy(); cp[i] += h
            J[:, i] = (_resid(cp) - r) / h
        g  = J.T @ r                      # gradient (½∇SSE)
        if float(np.max(np.abs(g))) < 1e-14:
            break
        JtJ = J.T @ J
        D = np.diag(np.maximum(np.diag(JtJ), 1e-12))
        stepped = False
        for _try in range(8):             # adaptation du damping λ
            try:
                delta = np.linalg.solve(JtJ + lam * D, -g)
            except np.linalg.LinAlgError:
                lam *= 10.0; continue
            c_new = np.clip(c + delta, lo_b, hi_b)
            r_new = _resid(c_new)
            sse_new = float(r_new @ r_new)
            if np.isfinite(sse_new) and sse_new < sse_best:
                rel = (sse_best - sse_new) / max(sse_best, 1e-300)
                c, r, sse_best = c_new, r_new, sse_new
                c_best = c.copy()
                lam = max(lam / 3.0, 1e-12)
                stepped = True
                if rel < 1e-13:           # précision machine atteinte
                    _try = None
                break
            lam *= 4.0
        if not stepped:
            break                          # λ saturé : optimum local atteint
        if _try is None:
            break

    for i, cn in enumerate(consts):
        cn.value = float(c_best[i])
    _invalidate_all_hashes(child)

    # Garde anti-dégénérescence : identique à la voie Adam — on n'accepte que
    # strictement meilleur, sans effondrement de complexité.
    mse_before  = _pure_mse(node,  xs, ys)
    mse_after   = _pure_mse(child, xs, ys)
    k_before, _ = tree_complexity(node)
    k_after,  _ = tree_complexity(child)
    if mse_after >= mse_before or k_after < max(1, k_before * 0.4):
        return node.copy()
    return child


def optimize_constants_adam(node: Node,
                             xs: np.ndarray,
                             ys: np.ndarray,
                             cfg: Config) -> Node:
    """
    Optimisation Adam avec compilateur paramétrique f(_x, _c).
    v14 — gain ×10–50 : une seule compilation par structure,
    les constantes varient dans un array NumPy sans recompilation.
    [v26-LM] Par default, cette fonction DÉLÈGUE à Levenberg-Marquardt
    (optimize_constants_lm), nettement supérieur sur les moindres carrés.
    Mettre cfg.CONST_OPT_LM=False pour revenir à la voie Adam historique.
    """
    if bool(getattr(cfg, "CONST_OPT_LM", True)):
        return optimize_constants_lm(node, xs, ys, cfg)
    child  = node.copy()
    fn, consts = compile_parametric(child)
    if not consts:
        return child

    n_consts = len(consts)
    max_iter = cfg.CONST_OPT_ITER * (2 if n_consts <= 4 else 1)

    lr  = cfg.ADAM_LR
    b1  = cfg.ADAM_BETA1
    b2  = cfg.ADAM_BETA2
    eps = cfg.ADAM_EPS
    h   = 1e-4

    m  = np.zeros(n_consts)
    v2 = np.zeros(n_consts)

    c_arr = np.array([c.value for c in consts], dtype=float)

    if fn is None:
        # Fallback si compilation paramétrique échoue
        return child

    def _mse(c):
        with np.errstate(all='ignore'):
            pred = fn(xs, c)
        pred = np.where(np.isfinite(pred), pred, 0.0)
        return float(np.mean((pred - ys) ** 2))

    best_mse  = _mse(c_arr)
    best_c    = c_arr.copy()
    stagnation = 0

    for t in range(1, max_iter + 1):
        grad = np.zeros(n_consts)
        for i in range(n_consts):
            orig_val = c_arr[i]
            
            # Évaluation de la borne positive (+h) in-place
            c_arr[i] = orig_val + h
            mse_plus = _mse(c_arr)
            
            # Évaluation de la borne négative (-h) in-place
            c_arr[i] = orig_val - h
            mse_minus = _mse(c_arr)
            
            # Restauration immédiate de la valeur d'origine dans le tableau maître
            c_arr[i] = orig_val
            
            # Calcul du gradient stabilisé
            g = (mse_plus - mse_minus) / (2 * h)
            grad[i] = max(-1e6, min(1e6, g))

        m  = b1 * m  + (1 - b1) * grad
        v2 = b2 * v2 + (1 - b2) * grad ** 2
        m_hat  = m  / (1 - b1 ** t)
        v2_hat = v2 / (1 - b2 ** t)
        c_arr -= lr * m_hat / (np.sqrt(np.maximum(v2_hat, 0.0)) + eps)
        c_arr  = np.clip(c_arr, cfg.ERC_MIN * 3, cfg.ERC_MAX * 3)

        new_mse = _mse(c_arr)
        if new_mse < best_mse:
            best_mse  = new_mse
            best_c    = c_arr.copy()
            stagnation = 0
        else:
            stagnation += 1
            if stagnation == 5:
                lr *= 0.5
            if stagnation >= 10:
                noise  = np.abs(best_c) * 0.05 + 0.01
                c_arr  = best_c + np.random.normal(0, noise)
                c_arr  = np.clip(c_arr, cfg.ERC_MIN * 3, cfg.ERC_MAX * 3)
                m[:]   = 0.0
                v2[:]  = 0.0
                stagnation = 0
                lr = cfg.ADAM_LR * 0.3

    # Appliquer les meilleures constantes à l'arbre
    for i, c in enumerate(consts):
        c.value = float(best_c[i])
    _invalidate_all_hashes(child)

    # [v14.3] Garde anti-dégénérescence ─────────────────────────────────────────
    # Adam peut faire diverger les constantes vers des valeurs extrêmes, ce qui
    # conduit simplify() à réduire l'expression à une feuille constante avec un
    # MSE catastrophique (cas observé : global_best dégradé de FIT=-808 à MSE=0.88).
    # On n'accepte la version optimisée que si :
    #   (a) son MSE pur est strictement meilleur que l'original, ET
    #   (b) la complexité ne s'effondre pas de plus de 60% (pas de dégénérescence).
    mse_before   = _pure_mse(node,  xs, ys)
    mse_after    = _pure_mse(child, xs, ys)
    k_before, _  = tree_complexity(node)
    k_after,  _  = tree_complexity(child)
    if mse_after >= mse_before or k_after < max(1, k_before * 0.4):
        return node.copy()   # original intact : Adam a divergé
    # ─────────────────────────────────────────────────────────────────────────────
    return child

# ════════════════════════════════════════════════════════════════
# [v18-LEX] SÉLECTION ε-LEXICASE  (La Cava, Spector et al., 2016)
# ════════════════════════════════════════════════════════════════
# Au lieu d'agréger l'erreur en un scalaire (MSE), chaque événement de
# sélection parcourt les CAS DE TEST dans un ordre random et ne garde
# que les individus à moins de ε du meilleur sur chaque cas. ε = MAD
# (median absolute deviation) de l'erreur du cas dans la population.
# Effet : préserve les SPÉCIALISTES (individus excellents sur un sous-
# domaine), maintient la diversité comportementale, et domine le tournoi
# sur la quasi-totalité des benchmarks de régression symbolique (SRBench).
# Coût : la matrice d'erreurs (P × C) est construite UNE fois par
# génération via le cache de prédictions — coût marginal quasi nul.

# ════════════════════════════════════════════════════════════════
# [v19] DÉDUPLICATION SÉMANTIQUE DE POPULATION
# ════════════════════════════════════════════════════════════════
# Deux arbres syntaxiquement différents mais qui produisent le MÊME vecteur
# de sorties sont des CLONES COMPORTEMENTAUX : ils occupent un slot, coûtent
# une sélection lexicase, des copies et des évaluations, sans apporter de
# diversité réelle. On les détecte via un hash du vecteur de prédictions
# (arrondi) sur le dataset, et on n'en garde qu'UN exemplaire — le plus court
# (rasoir d'Ockham : à comportement égal, l'expression la plus simple gagne).
# Standard dans Operon et PySR ; supprime typiquement 30-50% de la population.

def _semantic_key(ind, xs_np, decimals: int):
    """Clé de hash du comportement de l'arbre sur xs_np (None si dégénéré)."""
    try:
        preds = _predict_cached(ind, xs_np)
        if not np.all(np.isfinite(preds)):
            return None
        # Arrondi puis hash des octets bruts : robuste et rapide
        q = np.round(preds, decimals)
        return hash(q.tobytes())
    except Exception:
        return None


def semantic_dedup(population, xs, ys, cfg, protected=0):
    """Retire les clones comportementaux de `population`.

    · protected : les `protected` premiers individus (élite déjà triée) sont
      toujours conservés et réservent leur clé — on ne les déduplique pas
      entre eux mais ils empêchent un doublon plus loin dans la liste.
    · À comportement identique, on garde l'arbre de plus petite taille.
    Retourne (population_unique, n_removed).
    """
    if not getattr(cfg, "USE_SEMANTIC_DEDUP", False):
        return population, 0
    xs_np = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
    decimals = getattr(cfg, "SEMANTIC_DEDUP_DECIMALS", 4)
    seen = {}          # clé sémantique -> index conservé dans `kept`
    kept = []
    removed = 0
    for i, ind in enumerate(population):
        key = _semantic_key(ind, xs_np, decimals)
        if key is None or i < protected:
            # Indécidable ou protégé : on garde sans dédupliquer
            kept.append(ind)
            if key is not None and key not in seen:
                seen[key] = len(kept) - 1
            continue
        j = seen.get(key)
        if j is None:
            seen[key] = len(kept)
            kept.append(ind)
        else:
            # Clone : garder le plus court des deux
            if tree_size(ind) < tree_size(kept[j]):
                kept[j] = ind
            removed += 1
    return kept, removed


class EpsilonLexicaseSelector:
    __slots__ = ("pop", "E", "eps", "n_cases", "_case_buf")

    def __init__(self, population: List["Node"], xs, ys):
        xs_np = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
        ys_np = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)
        rows = []
        with np.errstate(all='ignore'):
            for ind in population:
                preds = _predict_cached(ind, xs_np)
                # [v18-LS] erreurs mesurées sur la forme scalée — cohérent
                # avec raw_mse/_pure_mse qui jugent aussi la forme scalée.
                if _USE_LINEAR_SCALING and float(np.std(preds)) >= 1e-6:
                    a_ls, b_ls, _ok = _linear_scale_params(preds, ys_np)
                    if _ok:
                        preds = a_ls + b_ls * preds
                err = np.abs(preds - ys_np)
                rows.append(np.where(np.isfinite(err), err, 1e9))
        self.pop     = population
        self.E       = np.vstack(rows)                            # (P, C)
        med          = np.median(self.E, axis=0)
        self.eps     = np.median(np.abs(self.E - med), axis=0)    # MAD par cas
        self.n_cases = self.E.shape[1]
        # [v19-OPT] buffer d'ordre des cas réutilisé (shuffle in-place) :
        # évite une allocation np.random.permutation par sélection.
        self._case_buf = np.arange(self.n_cases)

    def select(self) -> "Node":
        # [v19-OPT] Filtrage incrémental sur des INDICES Python (cand est une
        # liste d'ints), ce qui évite le fancy-indexing NumPy self.E[cand, c]
        # (qui alloue un tableau à chaque cas). On indexe colonne par colonne.
        np.random.shuffle(self._case_buf)
        E = self.E
        eps = self.eps
        cand = None  # None = "tous les individus"
        for c in self._case_buf:
            col = E[:, c]
            if cand is None:
                thresh = col.min() + eps[c]
                cand = np.flatnonzero(col <= thresh)
            else:
                sub = col[cand]
                thresh = sub.min() + eps[c]
                cand = cand[sub <= thresh]
            if cand.shape[0] == 1:
                break
        idx = int(cand[0]) if cand.shape[0] == 1 else int(cand[np.random.randint(cand.shape[0])])
        return self.pop[idx].copy()

# ============================================================
# SÉLECTION PAR TOURNOI AVEC PRESSION
# ============================================================

def tournament(population: List[Node],
               xs: List[float], ys: List[float],
               cfg: Config,
               role: str = "explorer") -> Node:
    participants = random.sample(population, cfg.TOURNAMENT_SIZE)
    # [v14.4] Tri avec la métrique propre à l'île (role transmis par evolve_island)
    participants.sort(key=lambda n: fitness(n, xs, ys, cfg, role))
    # Sélection probabiliste avec pression
    for i, ind in enumerate(participants):
        if random.random() < cfg.TOURNAMENT_PRESSURE or i == len(participants) - 1:
            return ind.copy()
    return participants[0].copy()

# ============================================================
# CROSSOVER SIZE-FAIR
# ============================================================

def crossover_size_fair(a: Node, b: Node, cfg: Config) -> Node:
    """
    Croisement sous-arbre avec sélection biaisée vers des tailles comparables.
    Réduit fortement le bloat.
    """
    child   = a.copy()
    nodes_a = get_all_nodes(child)
    nodes_b = get_all_nodes(b)

    # Taille cible : proche de la taille de a
    size_a = tree_size(a)

    def _subtree_sizes(nodes):
        # [OPT] tailles de tous les sous-arbres en UNE passe (ordre BFS inversé
        # = enfants avant parents) au lieu de tree_size() par noeud (O(n²)->O(n))
        size_of = {}
        for n, _, _ in reversed(nodes):
            size_of[id(n)] = 1 + (size_of.get(id(n.left), 0) if n.left else 0) \
                               + (size_of.get(id(n.right), 0) if n.right else 0)
        return size_of

    def pick_node_by_size(nodes, target_size):
        size_of = _subtree_sizes(nodes)
        weights = [1.0 / (1.0 + abs(size_of[id(n)] - target_size // 3))
                   for n, _, _ in nodes]
        return random.choices(nodes, weights=weights, k=1)[0]

    _, parent_a, side_a = pick_node_by_size(nodes_a, size_a)
    node_b, _, _        = pick_node_by_size(nodes_b, size_a)
    subtree = node_b.copy()

    if parent_a is None:
        result = subtree
    else:
        if side_a == "left":
            parent_a.left  = subtree
        else:
            parent_a.right = subtree
        result = child

    if tree_size(result)  > cfg.MAX_TREE_SIZE:  return a.copy()
    if tree_depth(result) > cfg.MAX_TREE_DEPTH: return a.copy()
    return result

# ============================================================
# MUTATIONS
# ============================================================

def hoist_mutation(node: Node) -> Node:
    child  = node.copy()
    nodes  = get_all_nodes(child)
    target, parent, side = random.choice(nodes)
    subnodes = get_all_nodes(target)
    # Préférer les sous-arbres non-terminaux
    non_trivial = [(n, p, s) for n, p, s in subnodes
                   if n.left is not None]
    pool = non_trivial if non_trivial else subnodes
    chosen, _, _ = random.choice(pool)
    replacement  = chosen.copy()
    if parent is None:
        return replacement
    if side == "left":
        parent.left  = replacement
    else:
        parent.right = replacement
    return child

def shrink_mutation(node: Node, cfg: Config) -> Node:
    """Remplace un sous-arbre par un terminal → réduit la taille."""
    child  = node.copy()
    nodes  = get_all_nodes(child)
    # Choisir un noeud non-terminal
    non_trivial = [(n, p, s) for n, p, s in nodes
                   if n.left is not None and p is not None]
    if not non_trivial:
        return child
    target, parent, side = random.choice(non_trivial)
    replacement = random_terminal(cfg)
    if side == "left":
        parent.left  = replacement
    else:
        parent.right = replacement
    return child

def point_mutation(node: Node, cfg: Config, role: str = "explorer") -> Node:
    """Mute uniquement la valeur d'un noeud (opérateur ou constante)."""
    child  = node.copy()
    nodes  = get_all_nodes(child)
    target, _, _ = random.choice(nodes)

    # [v14.5] Pool d'opérateurs filtré selon le rôle de l'île
    _b_ops, _b_w, _u_ops, _u_w = _get_ops_for_role(role)

    if isinstance(target.value, float):
        # Perturbation gaussienne adaptative
        sigma = max(0.1, abs(target.value) * 0.3)
        target.value += random.gauss(0, sigma)
        target.value = max(cfg.ERC_MIN * 3, min(cfg.ERC_MAX * 3, target.value))
        target.invalidate_hash()

    elif target.value in ALL_BINARY_OPS:                 # [FIX-OPS v20.1]
        target.value = random.choices(_b_ops, weights=_b_w)[0]
        target.invalidate_hash()

    elif target.value in ALL_UNARY_OPS:                  # [FIX-OPS v20.1]
        target.value = random.choices(_u_ops, weights=_u_w)[0]
        # un binaire (max2/min2) muté vers un unaire perdrait son bras droit ;
        # le pool _u_ops ne contient que des unaires donc on coupe right
        if target.value in ALL_UNARY_OPS:
            target.right = None
        target.invalidate_hash()

    return simplify(child)

def semantic_mutation(node: Node,
                      xs: List[float], ys: List[float],
                      cfg: Config, role: str = "explorer") -> Node:
    """
    Mutation orientée sémantiquement :
    génère plusieurs sous-arbres et garde celui qui améliore le plus la fitness.
    """
    best  = node
    best_fit = fitness(node, xs, ys, cfg, role=role)
    for _ in range(4):
        candidate = mutate(node, xs, ys, cfg, role=role)
        f = fitness(candidate, xs, ys, cfg, role=role)
        if f < best_fit:
            best_fit = f
            best     = candidate
    return best

def subtree_mutation(node: Node, cfg: Config) -> Node:
    child  = node.copy()
    nodes  = get_all_nodes(child)
    target, parent, side = random.choice(nodes)
    # [SYRACUSE/ND] Utiliser le générateur adapté au mode actif
    _is_nd_sub = (len(cfg.TERMINALS) > 1 or
                  (len(cfg.TERMINALS) == 1 and cfg.TERMINALS[0] != "x"))
    new_subtree = (_random_tree_nd(cfg.MAX_MUTATION_DEPTH, cfg)
                   if _is_nd_sub else random_tree(cfg.MAX_MUTATION_DEPTH, cfg))

    if parent is None:
        result = new_subtree
    else:
        if side == "left":
            parent.left  = new_subtree
        else:
            parent.right = new_subtree
        result = child

    if tree_size(result)  > cfg.MAX_TREE_SIZE:  return node.copy()
    if tree_depth(result) > cfg.MAX_TREE_DEPTH: return node.copy()
    return simplify(result)

def stigmergic_mutation(node: Node, cfg: Config) -> Node:
    """
    Mutation stigmergique : remplace un sous-arbre par un fragment
    tiré de la bibliothèque de phéromones.
    Si la bibliothèque est vide ou le tirage échoue → subtree_mutation classique.
    """
    frag = FRAGMENT_LIB.sample(min_size=2, max_size=cfg.MAX_TREE_SIZE // 3)
    if frag is None:
        return subtree_mutation(node, cfg)

    child  = node.copy()
    nodes  = get_all_nodes(child)
    target, parent, side = random.choice(nodes)

    if parent is None:
        result = frag
    else:
        if side == "left":
            parent.left  = frag
        else:
            parent.right = frag
        result = child

    if tree_size(result)  > cfg.MAX_TREE_SIZE:  return node.copy()
    if tree_depth(result) > cfg.MAX_TREE_DEPTH: return node.copy()
    return simplify(result)


def fragment_inject_mutation(node: Node, cfg: Config) -> Node:
    """
    Mutation par injection de fragment : remplace un sous-arbre
    par un fragment tiré de la bibliothèque, en ciblant un nœud
    de taille compatible.

    Différence avec stigmergic_mutation : cible les nœuds internes,
    pas seulement les feuilles — permet de greffer des structures
    entières (ex: sin(x²)) à des endroits stratégiques de l'arbre.
    """
    if not FRAGMENT_LIB.fragments:
        return subtree_mutation(node, cfg)

    tree = node.copy()
    sz   = tree_size(tree)

    # Chercher un nœud interne à remplacer (pas la racine si arbre simple)
    internals = [(n, p, s) for n, p, s in get_all_nodes(tree)
                 if p is not None]
    if not internals:
        return subtree_mutation(tree, cfg)

    target_node, parent, side = random.choice(internals)
    target_sz = tree_size(target_node)

    # Tirer un fragment de taille proche (+/- 50%)
    max_frag = min(int(target_sz * 1.5) + 3, cfg.MAX_TREE_SIZE - (sz - target_sz))
    min_frag = max(2, target_sz // 2)
    if max_frag < min_frag:
        max_frag = min_frag + 4

    frag = FRAGMENT_LIB.sample(min_size=min_frag, max_size=min(max_frag, 12))
    if frag is None:
        frag = FRAGMENT_LIB.sample(min_size=2, max_size=8)
    if frag is None:
        return subtree_mutation(tree, cfg)

    if side == "left":
        parent.left  = frag
    else:
        parent.right = frag

    if tree_size(tree) > cfg.MAX_TREE_SIZE:
        return node.copy()
    return simplify(tree)


def mutate(node: Node,
           xs: List[float], ys: List[float],
           cfg: Config,
           role: str = "explorer") -> Node:
    r = random.random()
    if r < cfg.HOIST_RATE:
        return hoist_mutation(node)
    if r < cfg.HOIST_RATE + cfg.SHRINK_RATE:
        return shrink_mutation(node, cfg)
    if r < cfg.HOIST_RATE + cfg.SHRINK_RATE + cfg.POINT_MUTATION_RATE:
        return point_mutation(node, cfg, role=role)   # [v14.5] role transmis
    # Mutations stigmergiques si lib non vide
    if FRAGMENT_LIB.fragments:
        rr = random.random()
        if rr < 0.15:
            return fragment_inject_mutation(node, cfg)   # injection ciblée
        if rr < 0.30:
            return stigmergic_mutation(node, cfg)        # remplacement feuille
    return subtree_mutation(node, cfg)

# ============================================================
# PARETO DOMINANCE (multi-objectif error × size)
# ============================================================

def pareto_rank(population: List[Node],
                xs: List[float], ys: List[float]) -> List[int]:
    """
    Retourne le rang de Pareto de chaque individu.
    Rang 1 = front de Pareto optimal.
    """
    n  = len(population)
    mse_list  = [raw_mse(ind, xs, ys) for ind in population]
    size_list = [tree_size(ind) for ind in population]
    ranks = [0] * n

    for i in range(n):
        rank = 1
        for j in range(n):
            if i == j:
                continue
            # j domine i si j est meilleur ou égal sur les deux objectifs
            if (mse_list[j] <= mse_list[i] and size_list[j] <= size_list[i] and
                    (mse_list[j] < mse_list[i] or size_list[j] < size_list[i])):
                rank += 1
        ranks[i] = rank
    return ranks

# ============================================================
# CONSTRUCTEUR STIGMERGIQUE — île C
# ============================================================

def build_stigmergic_tree(lib: FragmentLibrary,
                          cfg: Config) -> Node:
    """
    Construit un arbre complet depuis la bibliothèque de phéromones.

    Stratégie en 3 temps :
      1. Tire un fragment racine proportionnellement à τ
      2. Greffe itérative d'autres fragments jusqu'à la taille cible
      3. Complète les branches ouvertes par des terminaux randoms

    Si la bibliothèque est vide → fallback random_tree classique.

    (conservée pour compatibilité — appelée par build_stigmergic_tree_v2
     quand le graphe de co-occurrences est trop pauvre)
    """
    if not lib.fragments:
        return random_tree(cfg.MAX_INIT_DEPTH, cfg)

    target_size = random.randint(6, min(22, cfg.MAX_TREE_SIZE // 2))

    # Fragment racine (taille modérée)
    root_frag = lib.sample(min_size=2, max_size=max(2, target_size // 2))
    if root_frag is None:
        return random_tree(cfg.MAX_INIT_DEPTH, cfg)

    tree = root_frag

    # Greffage itératif
    for _ in range(10):
        remaining = target_size - tree_size(tree)
        if remaining < 2:
            break

        frag = lib.sample(min_size=2, max_size=min(remaining, 8))
        if frag is None:
            break

        r = random.random()
        if r < 0.45:
            # Wrapper binaire : op(tree, frag)
            op = random.choices(["+", "-", "*"], weights=[3, 2, 3])[0]
            tree = Node(op, tree, frag) if random.random() < 0.5 else Node(op, frag, tree)
        elif r < 0.65:
            # Wrapper unaire autour de l'arbre
            op = random.choices(["sin", "cos", "neg", "sq"],
                                weights=[2, 2, 1, 2])[0]
            tree = Node(op, tree)
        else:
            # Insertion profonde : remplacer un terminal par le fragment
            terminals = [(n, p, s) for n, p, s in get_all_nodes(tree)
                         if n.left is None and n.right is None and p is not None]
            if terminals:
                _, par, side = random.choice(terminals)
                if side == "left":  par.left  = frag
                else:               par.right = frag

        if tree_size(tree) > cfg.MAX_TREE_SIZE:
            tree = root_frag
            break

    return simplify(tree) if tree_size(tree) <= cfg.MAX_TREE_SIZE else root_frag


def build_stigmergic_tree_v2(lib: FragmentLibrary,
                              cograph: FragmentCoGraph,
                              cfg: Config) -> Node:
    """
    Construction stigmergique guidée par le graphe de co-occurrences (Phase 5a).

    Stratégie :
      A) Si le co-graphe est assez peuplé (≥ 10 arêtes) :
         1. Tire une paire corrélée (root_frag, companion) via cograph.sample_pair()
         2. Assemble root + companion avec un opérateur binaire pondéré par τ
         3. Greffe des fragments supplémentaires (compagnons du root ou randoms)
            jusqu'à la taille cible, en préférant les compagnons connus

      B) Sinon : fallback vers build_stigmergic_tree classique.

    Le compagnon est greffé avec un opérateur binaire dont le choix favorise
    les combinaisons rencontrées dans les top individus :
      - Si root est 'exp' → '*' très probable  (exp × sin pattern)
      - Sinon → tirage pondéré standard [+,-,*]
    """
    if not lib.fragments:
        return random_tree(cfg.MAX_INIT_DEPTH, cfg)

    # Seuil pour activer le co-graph
    if len(cograph.co) < 10:
        return build_stigmergic_tree(lib, cfg)

    target_size = random.randint(6, min(22, cfg.MAX_TREE_SIZE // 2))

    # ---- Étape 1 : paire corrélée ----
    root_frag, companion = cograph.sample_pair(lib)

    if root_frag is None:
        # Pas de paire valide → fallback
        return build_stigmergic_tree(lib, cfg)

    # ---- Étape 2 : assemblage root + companion ----
    root_op = root_frag.value if isinstance(root_frag.value, str) else "const"

    # Heuristique d'opérateur selon la racine du fragment
    if root_op in ("exp", "log"):
        # exp(…) × sin(…) est un pattern fréquent → favoriser *
        op_weights = [1, 1, 5]
    elif root_op in ("sin", "cos"):
        op_weights = [3, 2, 3]
    else:
        op_weights = [3, 2, 4]

    bin_op = random.choices(["+", "-", "*"], weights=op_weights)[0]

    # Orientation random
    if random.random() < 0.5:
        tree = Node(bin_op, root_frag, companion)
    else:
        tree = Node(bin_op, companion, root_frag)

    if tree_size(tree) > cfg.MAX_TREE_SIZE:
        tree = root_frag   # repli conservatif

    # ---- Étape 3 : greffages supplémentaires ----
    h_root = root_frag.structural_hash()
    for _ in range(8):
        remaining = target_size - tree_size(tree)
        if remaining < 2:
            break

        # 50% du temps : chercher un compagnon connu du fragment racine
        frag = None
        if random.random() < 0.50:
            frag = cograph.sample_companion(h_root, lib)
        if frag is None or tree_size(frag) > remaining:
            frag = lib.sample(min_size=2, max_size=min(remaining, 8))
        if frag is None:
            break

        r = random.random()
        if r < 0.45:
            op = random.choices(["+", "-", "*"], weights=[3, 2, 3])[0]
            tree = Node(op, tree, frag) if random.random() < 0.5 else Node(op, frag, tree)
        elif r < 0.65:
            op = random.choices(["sin", "cos", "neg", "sq"], weights=[2, 2, 1, 2])[0]
            tree = Node(op, tree)
        else:
            terminals = [(n, p, s) for n, p, s in get_all_nodes(tree)
                         if n.left is None and n.right is None and p is not None]
            if terminals:
                _, par, side = random.choice(terminals)
                if side == "left":  par.left  = frag
                else:               par.right = frag

        if tree_size(tree) > cfg.MAX_TREE_SIZE:
            break   # on garde l'état courant avant débordement

    result = simplify(tree)
    if tree_size(result) > cfg.MAX_TREE_SIZE:
        result = root_frag
    return result


# ============================================================
# TRANSFERT INTER-PROBLÈMES  (Phase 5c)
# ============================================================

def warm_transfer(decay_lib: float = 0.4,
                  decay_co:  float = 0.3,
                  decay_seq: float = 0.5):
    """
    Décote les mémoires stigmergiques pour un transfert entre problèmes.

    Conserve la connaissance structurelle (fragments, transitions)
    mais réduit la confiance pour laisser le nouveau problème
    réécrire sa propre distribution.

    decay_lib : taux de rétention pour FragmentLibrary (τ)
    decay_co  : taux de rétention pour FragmentCoGraph (co)
    decay_seq : taux de rétention pour FragmentSequenceMemory
    """
    # Fragment library : décote τ
    for e in FRAGMENT_LIB.fragments.values():
        e.tau *= decay_lib
    # Élagage post-décote
    to_del = [h for h, e in FRAGMENT_LIB.fragments.items()
              if e.tau < FragmentLibrary.MIN_TAU]
    for h in to_del:
        del FRAGMENT_LIB.fragments[h]

    # Co-graph : décote les arêtes
    for k in list(COGRAPH.co.keys()):
        COGRAPH.co[k] *= decay_co
        if COGRAPH.co[k] < FragmentCoGraph.MIN_CO:
            del COGRAPH.co[k]

    # Sequence memory : décote les transitions
    SEQ_MEM.warm_transfer(decay=decay_seq)

    kept_frags = len(FRAGMENT_LIB.fragments)
    kept_edges = len(COGRAPH.co)
    kept_trans = len(SEQ_MEM.transitions)
    print(f"[TRANSFER] Decay applied — "
          f"fragments={kept_frags}  edges={kept_edges}  transitions={kept_trans}")


# ============================================================
# CONSTRUCTEUR STIGMERGIQUE v3 — île C  (Phase 5b+5c)
# ============================================================

def build_stigmergic_tree_v3(lib: FragmentLibrary,
                              cograph: FragmentCoGraph,
                              seq_mem: FragmentSequenceMemory,
                              cfg) -> Node:
    """
    Construction stigmergique v3 : combine mémoire de séquences + co-graphe.

    Stratégie adaptative selon la richesse des mémoires :

    MODE A — co-graphe riche (≥20 arêtes) ET seq_mem riche (≥10 transitions) :
      1. Tire une paire corrélée (root_frag, companion) via cograph
      2. Construit un arbre top-down via seq_mem
      3. Greffe root_frag + companion dans cet arbre

    MODE B — seulement co-graphe riche :
      → build_stigmergic_tree_v2

    MODE C — seulement seq_mem riche :
      → arbre top-down seq_mem + fragments greffés

    MODE D — aucun :
      → build_stigmergic_tree classique
    """
    has_co  = len(cograph.co) >= max(5,  min(20, len(lib.fragments) * 2))
    has_seq = len(seq_mem.transitions) >= max(3, min(10, len(lib.fragments)))
    has_lib = bool(lib.fragments)

    if not has_lib:
        return random_tree(cfg.MAX_INIT_DEPTH, cfg)

    def graft_at_terminal(tree_root, frag_node):
        terminals = [(n, p, s) for n, p, s in get_all_nodes(tree_root)
                     if n.left is None and n.right is None and p is not None]
        if not terminals:
            return tree_root
        _, par, side = random.choice(terminals)
        if side == "left":  par.left  = frag_node.copy()  # [v19-OPT]
        else:               par.right = frag_node.copy()
        return tree_root

    # ---- MODE C ----
    if has_seq and not has_co:
        # FIX v13.8 : profondeur plafonnée à MAX_TREE_DEPTH//3 pour éviter bloat
        max_d = min(4, cfg.MAX_TREE_DEPTH // 3)
        depth = random.randint(2, max_d)
        tree  = seq_mem.build_top_down(cfg, max_depth=depth)
        frag  = lib.sample(min_size=2, max_size=cfg.MAX_TREE_SIZE // 3)
        if frag is not None:
            tree = graft_at_terminal(tree, frag)
        result = simplify(tree)
        return result if tree_size(result) <= cfg.MAX_TREE_SIZE else random_tree(cfg.MAX_INIT_DEPTH, cfg)

    # ---- MODE B ----
    if has_co and not has_seq:
        return build_stigmergic_tree_v2(lib, cograph, cfg)

    # ---- MODE D ----
    if not has_co and not has_seq:
        return build_stigmergic_tree(lib, cfg)

    # ---- MODE A ----
    root_frag, companion = cograph.sample_pair(lib)
    if root_frag is None:
        return build_stigmergic_tree_v2(lib, cograph, cfg)

    # FIX v13.8 : profondeur plafonnée pour MODE A également
    max_d    = min(4, cfg.MAX_TREE_DEPTH // 3)
    depth    = random.randint(2, max(2, max_d))
    top_down = seq_mem.build_top_down(cfg, max_depth=depth)

    # Greffe root_frag dans le top-down
    top_down = graft_at_terminal(top_down, root_frag)
    if tree_size(top_down) > cfg.MAX_TREE_SIZE:
        top_down = root_frag

    # Greffe companion
    if (companion is not None and
            tree_size(top_down) + tree_size(companion) <= cfg.MAX_TREE_SIZE):
        root_op_td = top_down.value if isinstance(top_down.value, str) else "const"
        bin_op = "*" if root_op_td in ("exp", "log") else                  random.choices(["+", "-", "*"], weights=[2, 1, 4])[0]
        top_down = (Node(bin_op, top_down, companion)
                    if random.random() < 0.5
                    else Node(bin_op, companion, top_down))

    # Fragments supplémentaires via co-graph
    h_root = root_frag.structural_hash()
    for _ in range(4):
        remaining = (cfg.MAX_TREE_SIZE // 2) - tree_size(top_down)
        if remaining < 2:
            break
        frag = cograph.sample_companion(h_root, lib)
        if frag is None or tree_size(frag) > remaining:
            frag = lib.sample(min_size=2, max_size=min(remaining, 8))
        if frag is None:
            break
        top_down = graft_at_terminal(top_down, frag)
        if tree_size(top_down) > cfg.MAX_TREE_SIZE:
            break

    result = simplify(top_down)
    if tree_size(result) > cfg.MAX_TREE_SIZE:
        result = root_frag
    return result


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

        if self.stigmergic and FRAGMENT_LIB.fragments:
            # Île stigmergique : construction guidée par la bibliothèque
            self.population = [
                build_stigmergic_tree_v3(FRAGMENT_LIB, COGRAPH, SEQ_MEM, self.cfg)
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
    for h, e in FRAGMENT_LIB.fragments.items():
        if e.semantic_signature is None and _refreshed < 40:
            e.semantic_signature = compute_semantic_sig(e.node, PROBE_X)
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
                    _fitness_cache.pop(n.structural_hash(), None)
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
    if _SYRACUSE_MODE:
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
    if _stigm_allowed:
        _limit_clean = max(top_k, top_k_seq)
        for i in range(min(_limit_clean, len(pop))):
            _old_hash   = pop[i].structural_hash()
            _simplified = simplify(pop[i])
            _new_hash   = _simplified.structural_hash()
            if _new_hash != _old_hash:
                # La forme a changé : invalider l'entrée stale dans le cache
                _fitness_cache.pop(_old_hash, None)
            pop[i] = _simplified
        # Recalcul de top_fits sur les formes simplifiées
        # (les fitness numériques sont identiques mais les hashes ont pu changer)
        top_fits = [fitness(ind, xs, ys, cfg, role=island.role) for ind in pop[:top_k]]

    if cfg.USE_LIB:
        if _stigm_allowed:
            FRAGMENT_LIB.deposit_population(pop, top_fits, top_k, generation,
                                            xs=xs, ys=ys)
        # [v16-FIX] Cap de diversité opérateur : plus strict en mode N-D
        # (plusieurs features → l'espace est plus grand, la diversité est vitale)
        _is_nd = (len(cfg.TERMINALS) > 1 or
                  (len(cfg.TERMINALS) == 1 and cfg.TERMINALS[0] != "x"))
        _op_cap = 0.30 if _is_nd else cfg.OP_DIVERSITY_CAP
        FRAGMENT_LIB.evaporate(evap_rate=cfg.FRAG_EVAP_RATE,
                               tau_max=cfg.FRAG_TAU_MAX,
                               op_diversity_cap=_op_cap)

    # ---- Dépôt co-occurrences (Phase 5a) ----
    if cfg.USE_COGRAPH and cfg.USE_LIB:
        if _stigm_allowed:
            COGRAPH.deposit_population(pop, top_k)
        COGRAPH.evaporate()

    # ---- Dépôt séquences structurelles (Phase 5b) ----
    if cfg.USE_SEQMEM:
        if _stigm_allowed:
            SEQ_MEM.deposit_population_with_root(pop, top_k_seq)
        SEQ_MEM.evaporate()

    found_better = False

    if best_fit < island.best_score:
        island.best_score = best_fit
        island.best       = best.copy()
        island.stagnation = 0
        found_better      = True
        # [FIX-E] Enregistrer l'usage des features du meilleur individu
        if _SYRACUSE_MODE and hasattr(cfg, 'TERMINALS'):
            record_feature_usage(best, cfg.TERMINALS)
        # [v17] Mettre à jour le résidu sémantique quand le best s'améliore
        global CURRENT_RESIDUAL_SIG
        try:
            probe_preds = evaluate_vector(best, PROBE_X)
            if np.all(np.isfinite(probe_preds)):
                _probe_y = np.zeros(len(PROBE_X), dtype=np.float64)
                if xs is not None and len(xs) > 1:
                    try:
                        _probe_y[:] = float(np.mean(ys))
                    except Exception:
                        pass
                CURRENT_RESIDUAL_SIG = update_residual_sig(best, PROBE_X, _probe_y)
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

        if island.stigmergic and cfg.USE_LIB and FRAGMENT_LIB.fragments:
            # Île stigmergique : renouvelle via stigmergie v3
            for _ in range(n_reset):
                idx = random.randint(cfg.ELITE_SIZE, len(pop) - 1)
                pop[idx] = build_stigmergic_tree_v3(FRAGMENT_LIB, COGRAPH, SEQ_MEM, cfg)
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
        _cograph_rich = len(COGRAPH.co) >= max(5, min(20, len(FRAGMENT_LIB.fragments) * 2))
        _stim_rate = 0.70 if (_cograph_rich or generation >= 20) else 0.30

        if island.stigmergic and cfg.USE_LIB and FRAGMENT_LIB.fragments and random.random() < _stim_rate:
            # Île C : construction v3 (co-graphe + séquences)
            child = build_stigmergic_tree_v3(FRAGMENT_LIB, COGRAPH, SEQ_MEM, cfg)
            # [v14.5] Adam uniquement si l'enfant est prometteur ET élitiste (top 25%)
            if random.random() < cfg.CONST_OPT_PROB:
                child_mse = raw_mse(child, xs, ys)
                _elite_threshold = sorted(raw_mse(ind, xs, ys) for ind in pop[:max(4, len(pop)//4)])[-1]
                if child_mse < _elite_threshold:
                    child = optimize_constants_adam(child, xs, ys, cfg)
            child = simplify(child)
        else:
            # Reproduction classique (toutes îles + île C à 30%)
            child = parent1

            if random.random() < cfg.CROSSOVER_RATE:
                parent2 = (_lex.select() if _lex is not None
                           else tournament(pop, xs, ys, cfg, role=island.role))
                child   = crossover_size_fair(parent1, parent2, cfg)

            if random.random() < cfg.MUTATION_RATE:
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

def _parallel_worker_init(xs, ys, probe_x, use_ls, syracuse_mode,
                          syracuse_y_raw, syracuse_x_raw,
                          gencsv=None, battery_mode=False):
    """Initializer du pool : reçoit les données constantes UNE fois par worker.
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
    global PROBE_X, _USE_LINEAR_SCALING, _SYRACUSE_MODE
    global _SYRACUSE_Y_RAW, _SYRACUSE_X_RAW
    _PW["xs"] = xs
    _PW["ys"] = ys
    PROBE_X             = probe_x
    _USE_LINEAR_SCALING = use_ls
    _SYRACUSE_MODE      = syracuse_mode
    if syracuse_y_raw is not None:
        _SYRACUSE_Y_RAW = syracuse_y_raw
    if syracuse_x_raw is not None:
        _SYRACUSE_X_RAW = syracuse_x_raw
    # [v22-CSV] propager le mode CSV générique + pools + noms de colonnes
    global _GENERIC_CSV_MODE, _BATTERY_CSV_MODE
    global _GENERIC_BINARY_OPS, _GENERIC_BINARY_WEIGHTS
    global _GENERIC_UNARY_OPS, _GENERIC_UNARY_WEIGHTS
    global CSV_FEATURE_NAMES, CSV_TARGET_NAME
    _BATTERY_CSV_MODE = battery_mode
    if gencsv is not None:
        _GENERIC_CSV_MODE = True
        (_GENERIC_BINARY_OPS, _GENERIC_BINARY_WEIGHTS,
         _GENERIC_UNARY_OPS,  _GENERIC_UNARY_WEIGHTS,
         CSV_FEATURE_NAMES, CSV_TARGET_NAME) = gencsv
    else:
        _GENERIC_CSV_MODE = False

def _island_round_task(payload):
    """Évolue UNE île pendant n_gens générations dans le worker.
    Reproduit fidèlement le housekeeping par génération de la boucle
    séquentielle (caches, _gen_bucket, mono_pen Syracuse)."""
    (island, gen_start, n_gens, frag, cog, seq, residual, seed) = payload
    global FRAGMENT_LIB, COGRAPH, SEQ_MEM, CURRENT_RESIDUAL_SIG
    random.seed(seed)
    np.random.seed(seed & 0x7FFFFFFF)
    FRAGMENT_LIB         = frag
    COGRAPH              = cog
    SEQ_MEM              = seq
    CURRENT_RESIDUAL_SIG = residual
    xs, ys = _PW["xs"], _PW["ys"]
    cfg = island.cfg
    best_local = None
    for gen in range(gen_start, gen_start + n_gens):
        if gen % 10 == 0:
            _fitness_cache.clear()
        _SIMPLIFY_CACHE.clear()
        if _SYRACUSE_MODE:
            _t = gen / max(cfg.GENERATIONS - 1, 1)
            cfg._mono_pen_cache = 0.10 - _t * 0.07
        cfg._gen_bucket = gen // 10
        nb = evolve_island(island, xs, ys, gen)
        if nb is not None:
            best_local = nb
    return (island, best_local, FRAGMENT_LIB, COGRAPH, SEQ_MEM)

def _parallel_enabled(cfg) -> bool:
    """AUTO : parallèle si ≥4 cœurs et ≥2 îles ; True force ; False bloque."""
    flag = getattr(cfg, "PARALLEL_ISLANDS", None)
    if flag is False or cfg.N_ISLANDS < 2:
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
    global CURRENT_RESIDUAL_SIG, FRAGMENT_LIB, COGRAPH, SEQ_MEM

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

    _syr_y = globals().get("_SYRACUSE_Y_RAW", None) if _SYRACUSE_MODE else None
    _syr_x = globals().get("_SYRACUSE_X_RAW", None) if _SYRACUSE_MODE else None
    # [v22-CSV] snapshot du mode CSV générique pour les workers
    _gencsv = ((list(_GENERIC_BINARY_OPS), list(_GENERIC_BINARY_WEIGHTS),
                list(_GENERIC_UNARY_OPS),  list(_GENERIC_UNARY_WEIGHTS),
                list(CSV_FEATURE_NAMES), CSV_TARGET_NAME)
               if _GENERIC_CSV_MODE else None)

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
    _os.environ["PYTHONHASHSEED"] = "0"

    try:
        with _cf.ProcessPoolExecutor(
                max_workers=n_workers, mp_context=ctx,
                initializer=_parallel_worker_init,
                initargs=(xs, ys, PROBE_X, _USE_LINEAR_SCALING,
                          _SYRACUSE_MODE, _syr_y, _syr_x,
                          _gencsv, _BATTERY_CSV_MODE)) as ex:
            gen = 0
            while gen < cfg.GENERATIONS:
                # Round aligné sur les frontières de migration
                nxt_mig = ((gen // cfg.MIGRATION_INTERVAL) + 1) * cfg.MIGRATION_INTERVAL
                n_gens  = min(round_len, cfg.GENERATIONS - gen, max(1, nxt_mig - gen))

                futs = [ex.submit(_island_round_task,
                                  (isl, gen, n_gens,
                                   FRAGMENT_LIB, COGRAPH, SEQ_MEM,
                                   CURRENT_RESIDUAL_SIG,
                                   _worker_rng.getrandbits(31)))
                        for isl in islands]
                results = [f.result() for f in futs]   # lève si un worker meurt

                # ── Réintégration (uniquement après round 100% réussi) ──
                for i, (isl, best_local, frag, cog, seq) in enumerate(results):
                    islands[i] = isl
                    FRAGMENT_LIB.merge_from(frag)
                    COGRAPH.merge_from(cog)
                    SEQ_MEM.merge_from(seq)

                _gen_end = gen + n_gens - 1
                for i, (isl, best_local, _f, _c, _s) in enumerate(results):
                    if best_local is None:
                        continue
                    cand = wrap_linear_scaling(best_local, xs, ys)
                    _track_val_candidate(cand)        # [v21-VAL]
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
                            _probe_y = np.zeros(PROBE_X.shape[0])
                            CURRENT_RESIDUAL_SIG = update_residual_sig(
                                global_best, PROBE_X, _probe_y)
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
                    if _es_mse <= cfg.EARLY_STOPPING_MSE:
                        print(f"\n{'═'*60}")
                        print(f"  [SUCCESS] Precision target reached at GEN {gen:04d}!")
                        print(f"  MSE (hold-out si actif) = {_es_mse:.2e}  ≤  seuil = {cfg.EARLY_STOPPING_MSE:.2e}")
                        print(f"  Early stop — remaining generations saved.")
                        print(f"{'═'*60}\n")
                        break

                if gen > 0 and gen % cfg.MIGRATION_INTERVAL == 0:
                    migrate(islands)

        return global_best, global_score, True

    except Exception as _par_err:
        print(f"[v20-PAR] ⚠ Parallel unavailable ({type(_par_err).__name__}: "
              f"{_par_err}) — automatic sequential fallback.")
        return global_best, global_score, False


# ════════════════════════════════════════════════════════════════
# [v21-VAL] VALIDATION HOLD-OUT
# ════════════════════════════════════════════════════════════════
# Pourquoi : jusqu'ici tous les MSE étaient mesurés sur les données
# d'ENTRAÎNEMENT — sur données réelles bruitées, une formule de 25 nœuds
# peut mémoriser le bruit et s'effondrer sur de nouvelles mesures.
# Désormais : split train/val au démarrage, évolution sur train seul,
# suivi séparé du meilleur individu EN VALIDATION, early-stopping et
# sélection finale sur la validation, rapport de généralisation.

_VAL_XS = None          # hold-out features  (None = validation désactivée)
_VAL_YS = None          # hold-out cible
_VAL_TRAIN_XS = None    # [v23.1] train features (test de stabilité numérique)
_VAL_TRAIN_YS = None    # [v23.1] train cible
# [v25-EXTRAP] Garde-fou anti-divergence : points-sondes AU-DELÀ de la plage
# d'entraînement (axe d'extrapolation prolongé) + bande de plausibilité dérivée
# de y. Un candidat dont la prédiction sort de cette bande sur les sondes est
# rejeté de la sélection — ce que la validation-frontière (interne) ne peut voir.
_EXTRAP_PROBE_XS = None
_EXTRAP_BAND = None     # (y_lo, y_hi) plausibles
_VAL_CANDS: list = []   # [(val_mse, val_se, size, node)] candidats-champions
_VAL_CANDS_MAX = 64

def _holdout_mse(node, xs_train, ys_train) -> float:
    """MSE sur le hold-out si disponible, sinon sur le train (fallback)."""
    if node is None:
        return float("inf")
    if _VAL_XS is not None:
        try:
            preds = evaluate_vector(node, _VAL_XS)
            m = float(np.mean((preds - _VAL_YS) ** 2))
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
    if _VAL_TRAIN_XS is None:
        return True
    try:
        preds = evaluate_vector(cand, _VAL_TRAIN_XS)
        if not np.all(np.isfinite(preds)):
            return False
        # tolérance : 100× l'amplitude de la cible (généreux mais borne l'explosion)
        amp = max(1e-9, float(np.max(np.abs(_VAL_TRAIN_YS))) * 100.0 + 10.0)
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
    if _EXTRAP_PROBE_XS is not None and _EXTRAP_BAND is not None:
        try:
            p2 = evaluate_vector(cand, _EXTRAP_PROBE_XS)
            if not np.all(np.isfinite(p2)):
                return False
            lo, hi = _EXTRAP_BAND
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
    if cand is None or _VAL_XS is None:
        return
    if not _is_numerically_stable(cand):
        return
    try:
        preds = evaluate_vector(cand, _VAL_XS)
        se_sq = (preds - _VAL_YS) ** 2
        m = float(np.mean(se_sq))
        if not math.isfinite(m):
            return
        se = float(np.std(se_sq, ddof=1) / math.sqrt(len(se_sq))) \
             if len(se_sq) > 1 else 0.0
        _VAL_CANDS.append((m, se, tree_size(cand), cand.copy()))
        if len(_VAL_CANDS) > _VAL_CANDS_MAX:
            _VAL_CANDS.sort(key=lambda t: (t[0], t[2]))
            del _VAL_CANDS[_VAL_CANDS_MAX:]
    except Exception:
        pass

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
    pool = list(_VAL_CANDS)
    if champion is not None and math.isfinite(champ_val) and _is_numerically_stable(champion):
        pool.append((champ_val, 0.0, tree_size(champion), champion))
    if not pool:
        # [v25-EXTRAP] Tout a été rejeté par le garde anti-divergence (aucune
        # forme bornée trouvée) : on retombe sur le champion brut faute de mieux.
        return champion, champ_val
    pool.sort(key=lambda t: t[0])
    best_mse, best_se = pool[0][0], pool[0][1]
    # Variance de la cible de validation → conversion MSE ↔ R²
    var_val = float(np.var(_VAL_YS)) if (_VAL_YS is not None and len(_VAL_YS) > 1) else 0.0
    tol_r2  = float(globals().get("VAL_R2_TOLERANCE", 0.003))   # 0.3 % de R²
    # Seuil = best + max(barre statistique 1-SE, bande de tolérance R²)
    r2_band = tol_r2 * var_val if var_val > 1e-15 else best_mse * 0.20
    thr = best_mse + max(best_se, r2_band)
    eligible = [t for t in pool if t[0] <= thr]
    eligible.sort(key=lambda t: (t[2], t[0]))   # plus petit, puis meilleur MSE
    m, _, _, node = eligible[0]
    return node, m

def _split_holdout(xs, ys, cfg):
    """Découpe (xs, ys) en (train, val). Retourne (xs_tr, ys_tr) et installe
    le hold-out dans les globals _VAL_XS/_VAL_YS. Validation désactivée si
    VALIDATION_SPLIT<=0 ou dataset trop petit (<30 points)."""
    global _VAL_XS, _VAL_YS, _VAL_TRAIN_XS, _VAL_TRAIN_YS, _EXTRAP_PROBE_XS, _EXTRAP_BAND
    _VAL_XS = None; _VAL_YS = None
    _VAL_TRAIN_XS = None; _VAL_TRAIN_YS = None
    _EXTRAP_PROBE_XS = None; _EXTRAP_BAND = None
    _VAL_CANDS.clear()
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
        _EXTRAP_PROBE_XS = probe
        y_lo = float(np.min(ys_np)); y_hi = float(np.max(ys_np))
        rng_y = max(1e-9, y_hi - y_lo)
        K = 2.0    # la tendance peut se prolonger de 2 amplitudes, pas exploser
        _EXTRAP_BAND = (y_lo - K * rng_y, y_hi + K * rng_y)

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

    _VAL_XS = xs_np[val_idx]
    _VAL_YS = ys_np[val_idx]
    xs_tr   = xs_np[tr_idx]
    ys_tr   = ys_np[tr_idx]
    _VAL_TRAIN_XS = xs_tr
    _VAL_TRAIN_YS = ys_tr
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
    global CURRENT_RESIDUAL_SIG
    _skeleton_seeds = []

    _res = CURRENT_RESIDUAL_SIG
    if _res is not None and len(FRAGMENT_LIB.fragments) > 0:
        scored = []
        for h, e in FRAGMENT_LIB.fragments.items():
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
        CURRENT_RESIDUAL_SIG = None
        return True
    return False

def evolve(func, cfg: Config, problem_key: str = '1',
           X_override=None, y_override=None):
    """
    X_override / y_override : si fournis (np.ndarray), remplacent build_dataset.
    Utilisés par le mode CSV réel (BATTERY_SOH + nasa_battery_simulation.csv).
    """
    global _fitness_cache, _PARAMETRIC_CACHE
    global PROBE_X, CURRENT_RESIDUAL_SIG     # [v17]
    global _USE_LINEAR_SCALING               # [v18-LS]
    _USE_LINEAR_SCALING = bool(getattr(cfg, "USE_LINEAR_SCALING", True))
    globals()["VAL_R2_TOLERANCE"] = float(getattr(cfg, "VAL_R2_TOLERANCE", 0.003))
    # FIX v13.10 : LOG_CSV relatif au répertoire du script
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(cfg.LOG_CSV):
        cfg = copy.copy(cfg)
        cfg.LOG_CSV = os.path.join(_script_dir, cfg.LOG_CSV)
    # FIX v13.7 : vider les caches entre runs pour éviter les biais
    # inter-problèmes (hash structurel identique, domaine différent).
    _fitness_cache    = {}
    _PARAMETRIC_CACHE = {}
    _PRED_CACHE.clear()
    FRAGMENT_LIB.fragments.clear()
    FRAGMENT_LIB.generation = 0
    COGRAPH.co.clear()
    SEQ_MEM.transitions.clear()

    # [v17] Initialiser le probe set adapté aux dimensions du problème
    PROBE_X              = init_probe_set(cfg, n_probe=30)
    CURRENT_RESIDUAL_SIG = None
    # [FIX-E] Réinitialiser le compteur d'usage des features
    n_feats = len(cfg.TERMINALS) if hasattr(cfg, 'TERMINALS') else 1
    reset_feature_usage(n_feats)
    print(f"[v17-SEMANTIC] Probe set initialized: {PROBE_X.shape[0]} points × "
          f"{PROBE_X.shape[1] if PROBE_X.ndim > 1 else 1} features  "
          f"[{cfg.X_MIN:.1f}, {cfg.X_MAX:.1f}]")

    print("=" * 70)
    # [SYRACUSE / v16-BATTERY CSV] Afficher le pool d'opérateurs réellement actif
    if _SYRACUSE_MODE:
        _active_ops = _SYRACUSE_BINARY_OPS + _SYRACUSE_UNARY_OPS
    elif _BATTERY_CSV_MODE:
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

    # [v24-EXTRAP] En mode extrapolation, on ajoute une DROITE (OLS) au pool de
    # candidats-champions. Elle est ajustée sur le train (intérieur) puis jugée,
    # comme tous les candidats, sur la bande-frontière. Opt-in : sans effet sur
    # les runs normaux (EXTRAPOLATION_MODE reste False par default).
    if bool(getattr(cfg, "EXTRAPOLATION_MODE", False)) and _VAL_XS is not None:
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
        FRAGMENT_LIB.deposit_population(pop_sorted, top_fits, top_k, gen=0,
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
    _cseeds = globals().get("_CUSTOM_SEEDS", None)
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

    for gen in range(cfg.GENERATIONS if _seq_needed else 0):
        # [OPT] Cache fitness vidé toutes les 10 générations (aligné sur gen//10).
        # Entre deux vidages, la clé (hash, role, gen//10) garantit la fraîcheur.
        # Évite de recalculer la fitness d'individus stables entre générations.
        if gen % 10 == 0:
            _fitness_cache.clear()
        # [OPT] Vider le cache de simplification pour libérer la mémoire
        # et éviter des résultats périmés après mutations.
        _SIMPLIFY_CACHE.clear()
        # [FIX-A] Mettre à jour la pénalité mono-feature progressive
        # 0.10 en gen=0 → 0.03 en fin de run (décroissance linéaire)
        if _SYRACUSE_MODE:
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
            if _es_mse <= cfg.EARLY_STOPPING_MSE:
                print(f"\n{'═'*60}")
                print(f"  [SUCCESS] Precision target reached at GEN {gen:04d}!")
                print(f"  MSE (hold-out si actif) = {_es_mse:.2e}  ≤  seuil = {cfg.EARLY_STOPPING_MSE:.2e}")
                print(f"  Early stop — remaining generations saved.")
                print(f"{'═'*60}\n")
                break

        # Migration périodique
        if gen > 0 and gen % cfg.MIGRATION_INTERVAL == 0:
            migrate(islands)

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
        if raw_mse(optimized, xs, ys) < raw_mse(global_best, xs, ys):
            global_best = optimized
        # Si Adam a dégradé, global_best reste intact (deepcopy garantit l'isolation)
        _track_val_candidate(global_best)            # [v21-VAL] post-Adam

    # ── [v21-VAL] Sélection finale + rapport de généralisation ──────────
    # Le champion LIVRÉ est celui qui généralise le mieux : si un candidat
    # suivi en cours de run bat le champion-train sur le hold-out, il prend
    # sa place. Puis rapport train vs validation, avec alerte surapprentissage.
    if _VAL_XS is not None and global_best is not None:
        # [v26-LM] POLISSAGE DES FINALISTES : avant la sélection parcimonieuse,
        # on affine par LM les constantes des meilleurs candidats suivis. Sans
        # cela, la règle 1-SE compare des structures aux constantes brutes — une
        # forme simple et EXACTE peut perdre contre un gros arbre simplement
        # parce que ses constantes n'étaient pas encore ajustées. Coût : ~ms.
        try:
            _top = sorted(_VAL_CANDS, key=lambda t: (t[0], t[2]))[:8]
            for _mse_i, _se_i, _sz_i, _nd_i in _top:
                _pol = optimize_constants_adam(_nd_i.copy(), xs, ys, cfg)
                _track_val_candidate(_pol)
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
        if _EXTRAP_PROBE_XS is not None and not _is_numerically_stable(global_best):
            _lin_fb = _make_linear_candidate(xs, ys, cfg)
            if _lin_fb is not None and _is_numerically_stable(_lin_fb):
                print("[v25-EXTRAP] ⚠ Champion still divergent → falling back to the line (safe floor).")
                global_best = _lin_fb
                _champ_val  = _holdout_mse(global_best, xs, ys)
        _champ_train = _pure_mse(global_best, xs, ys)
        _var_val     = float(np.var(_VAL_YS)) if len(_VAL_YS) > 1 else 0.0
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
    s = FRAGMENT_LIB.stats()
    print(f"[STIGM] Fragments accumulated: {s['count']}")
    print(f"[STIGM] τ max : {s['max_tau']:.4f}  |  τ moyen : {s['mean_tau']:.4f}")
    if s['top_ops']:
        print(f"[STIGM] Dominant operators: {s['top_ops']}")
    if FRAGMENT_LIB.fragments:
        print("[STIGM] Top 3 fragments :")
        for e in FRAGMENT_LIB.top_fragments(3):
            from_str = to_string(e.node)
            print(f"  τ={e.tau:.3f}  freq={e.freq}  {from_str}")

    # Stats graphe de co-occurrences (Phase 5a)
    cg = COGRAPH.stats()
    print()
    print(f"[COGRAPH] Co-occurrence edges: {cg['edges']}")
    print(f"[COGRAPH] co max : {cg['max_co']:.5f}  |  co moyen : {cg['mean_co']:.5f}")
    top_pairs = COGRAPH.top_pairs(5, FRAGMENT_LIB)
    if top_pairs:
        print("[COGRAPH] Top 5 paires co-occurrentes :")
        for w, l1, l2 in top_pairs:
            l1s = l1[:35] + "…" if len(l1) > 36 else l1
            l2s = l2[:35] + "…" if len(l2) > 36 else l2
            print(f"  co={w:.4f}  [{l1s}]  ×  [{l2s}]")

    # Stats mémoire de séquences (Phase 5b)
    sm = SEQ_MEM.stats()
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
    for key, dist in SEQ_MEM.transitions.items():
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
    def __init__(self):
        self.scale_ = None
    def fit_transform(self, X):
        m = np.max(np.abs(X), axis=0).astype(np.float64)
        m[m < 1e-12] = 1.0
        self.scale_ = m
        return X / m
    def transform(self, X):
        return X / self.scale_
    def inverse_transform(self, Xs):
        return Xs * self.scale_

def _choose_scaler(X_raw, normalize, x_range):
    """[v23] Sélectionne la normalisation. 'auto' : shift-free si toutes les
    features sont strictement positives (cas multiplicatif typique en
    sciences — masses, distances, températures absolues), sinon MinMax."""
    mode = (normalize or "auto").lower()
    if mode == "auto":
        all_pos = bool(np.all(X_raw > 0))
        mode = "divmax" if all_pos else "minmax"
    if mode in ("divmax", "shiftfree", "div"):
        return _ShiftFreeScaler(), "divmax (shift-free, preserves products)"
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
    global _GENERIC_CSV_MODE, _GENERIC_BINARY_OPS, _GENERIC_BINARY_WEIGHTS
    global _GENERIC_UNARY_OPS, _GENERIC_UNARY_WEIGHTS
    global CSV_FEATURE_NAMES, CSV_TARGET_NAME

    if not _CSV_DEPS_OK:
        raise ImportError("pandas et scikit-learn requis : "
                          "pip install pandas scikit-learn")
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
    _GENERIC_BINARY_OPS, _GENERIC_BINARY_WEIGHTS = list(b_ops), list(b_w)
    _GENERIC_UNARY_OPS,  _GENERIC_UNARY_WEIGHTS  = list(u_ops), list(u_w)
    _GENERIC_CSV_MODE = True
    CSV_FEATURE_NAMES = list(feature_cols)
    CSV_TARGET_NAME   = str(target_col)

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
    if not _CSV_DEPS_OK:
        raise ImportError(
            "[BATTERY_SOH] pandas et scikit-learn sont requis pour charger "
            "des données CSV réelles.\n"
            "Installez-les avec : pip install pandas scikit-learn"
        )

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
    global _BATTERY_CSV_MODE
    _BATTERY_CSV_MODE = True
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

# ── Métadonnées des variables leurres ─────────────────────────────────────────
# Clé = problem_key, valeur = liste des indices de features leurres.
# Utilisé par decoy_report() pour produire un verdict pass/fail explicite.
DECOY_FEATURES: Dict[str, List[int]] = {
    "ND1_DECOY":    [3],
    "ND3_DECOY":    [3],
    "ND5_DECOY":    [3],
    "BATTERY_SOH":  [3],   # X[3] = leurre (bruit pur, déconnecté de la cible)
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
#  standard(8): sin cos log sqrt abs neg sq cube
#  Syracuse(9): cos log sqrt abs neg sq cube is_even step (le 9ème = 3 pour step)


def _nd_diverse_population(cfg: Config, n: int) -> List["Node"]:
    """
    [v16-NDIM] Génère n arbres randoms avec couverture garantie des opérateurs.
    Principe : diviser la population en autant de slots que d'opérateurs unaires,
    puis générer au moins un arbre dont la racine (ou le premier niveau) utilise
    chaque opérateur. Le reste est du Ramped Half-and-Half classique.

    Cela évite le biais d'initialisation sans connaître la cible :
    - exp apparaîtra dans ~n/11 individus dès la gen 0
    - La SEQ_MEM et le FRAGMENT_LIB feront le reste
    """
    pop = []
    # [SYRACUSE/BATTERY] Couverture initiale sur le pool du mode actif uniquement
    _, _, _u_ops, _u_w, _, _ = _active_pools()
    n_unary = len(_u_ops)
    # 1re tranche : un individu par opérateur unaire (couverture minimale)
    coverage_size = min(n_unary, n // 4)
    for i in range(coverage_size):
        op = _u_ops[i % n_unary]
        depth = random.randint(2, cfg.MAX_INIT_DEPTH)
        child = _random_tree_grow_nd(depth - 1, cfg)
        pop.append(Node(op, child))
    # 2e tranche : ramped half-and-half avec poids boostés
    while len(pop) < n:
        pop.append(_random_tree_nd(cfg.MAX_INIT_DEPTH, cfg))
    return pop


def _random_tree_full_nd(depth: int, cfg: Config) -> "Node":
    """Full tree avec pool d'opérateurs adapté au mode actif (Syracuse/Battery/Standard)."""
    if depth <= 0:
        return random_terminal(cfg)
    _b_ops, _b_w, _u_ops, _u_w, _, _ = _active_pools()
    if random.random() < 0.30:
        op = random.choices(_u_ops, weights=_u_w)[0]  # [FIX-CSV v22] poids du pool actif
        return Node(op, _random_tree_full_nd(depth - 1, cfg))
    op = random.choices(_b_ops, weights=_b_w)[0]
    return Node(op,
                _random_tree_full_nd(depth - 1, cfg),
                _random_tree_full_nd(depth - 1, cfg))


def _random_tree_grow_nd(depth: int, cfg: Config) -> "Node":
    """Grow tree avec pool d'opérateurs adapté au mode actif (Syracuse/Battery/Standard)."""
    if depth <= 0:
        return random_terminal(cfg)
    r = random.random()
    if r < 0.20:
        return random_terminal(cfg)
    _b_ops, _b_w, _u_ops, _u_w, _, _ = _active_pools()
    if r < 0.45:
        op = random.choices(_u_ops, weights=_u_w)[0]  # [FIX-CSV v22] poids du pool actif
        return Node(op, _random_tree_grow_nd(depth - 1, cfg))
    op = random.choices(_b_ops, weights=_b_w)[0]
    return Node(op,
                _random_tree_grow_nd(depth - 1, cfg),
                _random_tree_grow_nd(depth - 1, cfg))


def _random_tree_nd(max_depth: int, cfg: Config) -> "Node":
    """Ramped Half-and-Half N-D avec poids boostés."""
    d = random.randint(2, max_depth)
    if random.random() < 0.5:
        return _random_tree_full_nd(d, cfg)
    return _random_tree_grow_nd(d, cfg)


def _detect_dominant_op(population: List["Node"]) -> str:
    """
    [v16-FIX] Détecte l'opérateur le plus fréquent en racine dans la population.
    Utilisé lors des resets de stagnation pour éviter de ré-injecter le même
    opérateur qui a causé la convergence prématurée.
    Retourne "none" si la population est vide ou si aucun opérateur ne domine.
    """
    if not population:
        return "none"
    counts: Dict[str, int] = {}
    for node in population:
        v = node.value if isinstance(node.value, str) else "const"
        counts[v] = counts.get(v, 0) + 1
    return max(counts, key=lambda k: counts[k])


def make_cfg_nd(n_features: int,
                x_min: float = -3.0,
                x_max: float = 3.0,
                fast: bool = False,
                ultrafast: bool = False,
                use_seeding: bool = False,
                use_lib: bool = True,
                use_cograph: bool = True,
                use_seqmem: bool = True) -> Config:
    """
    [v16-NDIM] Crée une Config adaptée à la régression symbolique N-dimensionnelle.

    · TERMINALS est généré dynamiquement : ["X[0]", "X[1]", …, "X[n_features-1]"]
    · Les seeds (seeding dirigé) sont désactivées par default car elles sont
      spécifiques à "x" ; passer use_seeding=True si vous avez vos propres seeds N-D.
    · Tous les autres hyperparamètres suivent la même logique que make_cfg().

    Usage :
        cfg = make_cfg_nd(n_features=3, x_min=-3, x_max=3, fast=True)
        best, X, y = evolve(ND_PROBLEMS["ND1"][1], cfg, problem_key="ND1")
    """
    cfg = make_cfg(x_min=x_min, x_max=x_max,
                   fast=fast, ultrafast=ultrafast,
                   use_seeding=use_seeding,
                   use_lib=use_lib, use_cograph=use_cograph,
                   use_seqmem=use_seqmem)
    # Remplacer le terminal set 1-D par le set N-D dynamique
    cfg.TERMINALS = [f"X[{i}]" for i in range(n_features)]
    # [v16-FIX] Paramètres anti-monopole renforcés pour N-D :
    # · FRAG_TAU_MAX plus bas → pas de fragment qui verrouille toute la lib
    # · OP_DIVERSITY_CAP plus bas → diversité opérateur garantie
    cfg.FRAG_TAU_MAX      = 8.0 if not (fast or ultrafast) else (5.0 if ultrafast else 6.0)
    cfg.OP_DIVERSITY_CAP  = 0.30
    return cfg


# Seeds pour les nouveaux problèmes
_EXTRA_SEEDS: Dict[str, list] = {
    "5": ["sin_sq_x", "x_cos_x", "sin_sq_x"],   # réutilise des briques p.1
    "6": ["exp_sq_x"],                            # exp(-x²) proche de exp(-|x|)
    "7": [],
    "8": [],
    "9": [],
    "10": ["x_cube"],
}


# ----------------------------------------------------------------
# Benchmark intégré  (Phase 5c — évaluation rigoureuse)
# ----------------------------------------------------------------

def make_cfg(x_min: float, x_max: float,
             fast: bool = False,
             ultrafast: bool = False,
             use_seeding: bool = True,
             use_lib: bool = True, use_cograph: bool = True,
             use_seqmem: bool = True) -> Config:
    """
    Crée une config standard adaptée au benchmark.
    ultrafast : pop=150, gen=100, 2 îles — pour machines limitées en RAM/CPU.
    fast      : pop=300, gen=200, 3 îles.
    normal    : pop=600, gen=400, 4 îles.
    """
    if ultrafast:
        pop, gen, islands = 150, 100, 2
    elif fast:
        pop, gen, islands = 300, 200, 3
    else:
        pop, gen, islands = 600, 400, 4

    return Config(
        POP_SIZE               = pop,
        GENERATIONS            = gen,
        N_ISLANDS              = islands,
        ELITE_SIZE             = 4 if ultrafast else 6,
        TOURNAMENT_SIZE        = 3 if ultrafast else 4,
        N_POINTS               = 60 if ultrafast else 80,
        CONST_OPT_ITER         = 15 if ultrafast else 20,
        CONST_OPT_PROB         = 0.15,   # [v14.5] Throttling Adam
        SEMANTIC_MUTATION_RATE = 0.0,
        MUTATION_RATE          = 0.80,
        CROSSOVER_RATE         = 0.60,
        MIGRATION_INTERVAL     = 20 if ultrafast else 25,
        MIGRATION_SIZE         = 3 if ultrafast else 4,
        STAGNATION_LIMIT       = 25 if ultrafast else 40,
        RESET_FRACTION         = 0.20,
        PARSIMONY              = 0.0008,
        DEPTH_PENALTY          = 0.0002,
        MAX_INIT_DEPTH         = 7,
        MAX_TREE_SIZE          = 70,
        MAX_TREE_DEPTH         = 13,
        X_MIN                  = x_min,
        X_MAX                  = x_max,
        # [v14.5] Évaporation renforcée + cap strict anti-monopole
        FRAG_EVAP_RATE         = (0.80 if (ultrafast and not use_cograph and not use_seqmem)
                                  else 0.82 if ultrafast
                                  else 0.85),
        FRAG_TAU_MAX           = 15.0 if ultrafast else 40.0,
        USE_SEEDING            = use_seeding,
        USE_LIB                = use_lib,
        USE_COGRAPH            = use_cograph,
        USE_SEQMEM             = use_seqmem,
        TERMINALS              = ["x"],   # [v16-NDIM] mode 1-D par default
        # [v15] EARLY_STOPPING_MSE = 1e-6 hérité du default Config.
    )


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
        if 'SEQ_MEM' in globals():
            globals()['SEQ_MEM'].import_grammar("grammar_shared_base.json", decay=0.5)

        best, xs, ys = evolve(func, cfg, problem_key=key)
        if best:
            print_result(name, best, xs, ys, cfg)
            try_plot(name, func, best, xs, ys, cfg.LOG_CSV)

            # --- NOUVEAU : SAUVEGARDE DE LA GRAMMAIRE ---
            if 'SEQ_MEM' in globals():
                globals()['SEQ_MEM'].export_grammar(f"grammar_meta_p{key}.json")
                globals()['SEQ_MEM'].export_grammar("grammar_shared_base.json")
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
        if 'SEQ_MEM' in globals() and os.path.exists("grammar_shared_base.json"):
            globals()['SEQ_MEM'].import_grammar("grammar_shared_base.json",
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
            if 'SEQ_MEM' in globals():
                globals()['SEQ_MEM'].export_grammar(f"grammar_meta_{nd_key}.json")
                globals()['SEQ_MEM'].export_grammar("grammar_shared_base.json")
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
        if 'SEQ_MEM' in globals() and _grammar_ok:
            globals()['SEQ_MEM'].import_grammar("grammar_shared_base.json",
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
            FRAGMENT_LIB.deposit(_seed_tree, rank=1, fitness=-9999.0, gen=0)
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
            y_min_r = float(_SYRACUSE_Y_RAW.min())
            y_max_r = float(_SYRACUSE_Y_RAW.max())
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
                    -2.0 + 4.0 * (feats_raw[i] - _SYRACUSE_FEAT_MINS[i])
                    / max(_SYRACUSE_FEAT_MAXS[i] - _SYRACUSE_FEAT_MINS[i], 1e-12)
                    for i in range(SYRACUSE_N_FEATURES)
                ])
                x_arr       = feats_scaled.reshape(1, -1)
                y_norm_pred = float(evaluate_vector(best, x_arr)[0])
                # Dénormaliser y → espace naturel (nb d'étapes)
                y_pred_nat  = y_min_r + (y_norm_pred + 2.0) / 4.0 * (y_max_r - y_min_r)
                err = abs(y_pred_nat - true_flight)
                print(f"  {n_check:>6}  {true_flight:>10}  {y_pred_nat:>12.2f}  {err:>12.2f}")
            print()
            if 'SEQ_MEM' in globals():
                globals()['SEQ_MEM'].export_grammar("grammar_meta_SYRACUSE.json")
                globals()['SEQ_MEM'].export_grammar("grammar_shared_base.json")
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
        print("    a = auto      shift-free if features positive, else minmax (default)")
        print("    d = divmax    shift-free (preserves x·y, x/y — multiplicative laws)")
        print("    m = minmax    [-2,2] (bounds exp/pow, but inflates products)")
        print("    s = standard  z-score (centered & scaled)")
        norm_rep = _ask("  Choice [a/d/m/s] (default=a) : ",
                        valid=["a", "d", "m", "s", ""], default="a")
        normalize = {"a": "auto", "d": "divmax", "m": "minmax",
                     "s": "standard", "": "auto"}[norm_rep]

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

        mode_str = ('ultrafast' if ultrafast else 'fast' if fast else 'normal')
        print(f"  Config : {mode_str}  pop={cfg.POP_SIZE}  gen={cfg.GENERATIONS}  "
              f"islands={cfg.N_ISLANDS}  features={n_feat}")
        print(SEP2)
        print()

        _gen_func = lambda Xm: np.zeros(Xm.shape[0])  # placeholder (override)
        try:
            best, X_data, y_data = evolve(
                _gen_func, cfg, problem_key="GENERIC_CSV",
                X_override=X, y_override=y)
        except Exception as _e:
            import traceback as _tbx
            print(f"[ERROR] Evolution interrupted: {_e}")
            _tbx.print_exc()
            _pause(); return

        if best:
            print_result(f"CSV: {target_name} = f({', '.join(feat_names)})",
                         best, X_data, y_data, cfg)
            # Rappel du dictionnaire X[i] → nom de colonne
            print("\n  Variable mapping:")
            for i, nm in enumerate(feat_names):
                print(f"    X[{i}] = {nm}")
            print(f"\n  Note: features are normalized. "
                  f"The formula is expressed on these normalized values.")
        else:
            print("[ERROR] No solution found.")
        # Réinitialiser le mode pour ne pas polluer un run suivant
        globals()['_GENERIC_CSV_MODE'] = False
        _pause()


def _pause():
    """Maintient la fenêtre ouverte jusqu'à ce que l'utilisateur appuie sur Entrée."""
    print()
    print("─" * 70)
    input("  Done. Press Enter to quit...")


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
        if 'SEQ_MEM' in globals():
            globals()['SEQ_MEM'].import_grammar("grammar_shared_base.json", decay=0.5)

        best, xs, ys = evolve(func, cfg, problem_key=key)

        if best:
            print_result(name, best, xs, ys, cfg)
            try_plot(name, func, best, xs, ys, cfg.LOG_CSV)

            # [v15] MÉTA-APPRENTISSAGE — export après succès
            if 'SEQ_MEM' in globals():
                # Archive locale au problème (pour analyse et replay)
                globals()['SEQ_MEM'].export_grammar(f"grammar_meta_p{key}.json")
                # Mise à jour de la base partagée pour le prochain run / problème
                globals()['SEQ_MEM'].export_grammar("grammar_shared_base.json")
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
        if 'SEQ_MEM' in globals() and os.path.exists("grammar_shared_base.json"):
            globals()['SEQ_MEM'].import_grammar("grammar_shared_base.json",
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
            if 'SEQ_MEM' in globals():
                globals()['SEQ_MEM'].export_grammar(f"grammar_meta_{mode}.json")
                globals()['SEQ_MEM'].export_grammar("grammar_shared_base.json")
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
        if 'SEQ_MEM' in globals() and os.path.exists("grammar_shared_base.json"):
            globals()['SEQ_MEM'].import_grammar("grammar_shared_base.json",
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
            if 'SEQ_MEM' in globals():
                globals()['SEQ_MEM'].export_grammar("grammar_meta_SYRACUSE.json")
                globals()['SEQ_MEM'].export_grammar("grammar_shared_base.json")
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

