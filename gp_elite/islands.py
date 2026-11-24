"""The islands: Island, migration, one generation of an island
(evolve_island), and the reset of the explorer islands.

Part of gp_elite/core.py until 1.4.0, moved without change in 1.5.
"""
from __future__ import annotations

import math
import random
import numpy as np
import copy
import time
from typing import Optional, List, Tuple, Dict, Any

from . import state
from .config import (TRACE, _active_pool_ops, _detect_dominant_op, _dim_active,
                     _ds)
from .tree import (Node, get_all_nodes, tree_depth, tree_size)
from .simplification import (simplify)
from .evaluation import (evaluate_vector)
from .scoring import (fitness, raw_mse, raw_pearson_r, record_feature_usage)
from .fitting import (optimize_constants_adam)
from .genetic import (EpsilonLexicaseSelector, _nd_diverse_population,
                      _random_tree_nd, build_stigmergic_tree_v3,
                      crossover_size_fair, mutate, random_tree, semantic_dedup,
                      semantic_mutation, tournament)
from .memory import (compute_semantic_sig, semantic_score, update_residual_sig)

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
