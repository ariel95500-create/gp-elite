"""The genetic operators: random trees (in one and in n dimensions),
deduplication, epsilon-lexicase and tournament selection, crossover,
the mutations, Pareto ranks and the stigmergic trees.

Part of gp_elite/core.py until 1.4.0, moved without change in 1.5.
"""
from __future__ import annotations

import random
import numpy as np
from typing import Optional, List, Tuple, Dict, Any

from . import state
from .config import (ALL_BINARY_OPS, ALL_UNARY_OPS, _active_pools,
                     _get_ops_for_role, _pool_choice)
from .tree import (Node, get_all_nodes, tree_depth, tree_size)
from .simplification import (simplify)
from .evaluation import (_predict_cached)
from .scoring import (_linear_scale_params, fitness, get_feature_bias_weights,
                      raw_mse)

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
        if (state._SYRACUSE_MODE and state._feature_usage_counter
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
    __slots__ = ("pop", "E", "eps", "n_cases", "_case_buf", "_ET")

    def __init__(self, population: List["Node"], xs, ys):
        xs_np = xs if isinstance(xs, np.ndarray) else np.asarray(xs, dtype=float)
        ys_np = ys if isinstance(ys, np.ndarray) else np.asarray(ys, dtype=float)
        rows = []
        with np.errstate(all='ignore'):
            for ind in population:
                preds = _predict_cached(ind, xs_np)
                # [v18-LS] erreurs mesurées sur la forme scalée — cohérent
                # avec raw_mse/_pure_mse qui jugent aussi la forme scalée.
                if state._USE_LINEAR_SCALING and float(np.std(preds)) >= 1e-6:
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
        # [v0.8] erreurs rangées par cas (C, P) : une ligne = un cas.
        self._ET = np.ascontiguousarray(self.E.T)

    def select(self) -> "Node":
        """Sélection ε-lexicase, par BLOCS de cas.

        [v0.8] Même résultat, tirage pour tirage, que le filtrage cas par cas
        (_select_reference, gardée pour les tests) : les cas sont parcourus
        dans le même ordre aléatoire, et le hasard n'est consommé qu'aux mêmes
        endroits. Ce qui change : quand les candidats restants passent tous
        les cas d'un bloc (fréquent, car la mise à l'échelle linéaire rend
        beaucoup d'individus équivalents), le bloc entier est franchi en une
        opération NumPy au lieu d'une boucle Python par cas. Sur 5 000
        lignes, la sélection parcourait ainsi les 5 000 cas à chaque parent
        et prenait près de la moitié du temps de calcul.

        Pourquoi c'est exact : tant que personne n'est éliminé, l'ensemble des
        candidats ne change pas, donc les seuils (min + ε) calculés d'un coup
        sur le bloc sont ceux que le parcours cas par cas aurait calculés. Au
        premier cas du bloc qui élimine quelqu'un, on applique ce cas seul et
        on repart du cas suivant."""
        np.random.shuffle(self._case_buf)
        order = self._case_buf
        ET = self._ET
        eps = self.eps
        n = order.shape[0]
        c = order[0]
        col = ET[c]
        cand = np.flatnonzero(col <= col.min() + eps[c])
        pos, B = 1, 8
        while cand.shape[0] > 1 and pos < n:
            blk = order[pos:pos + B]
            sub = ET[blk[:, None], cand]                 # (b, k)
            ok = sub <= (sub.min(axis=1) + eps[blk])[:, None]
            rows_ok = ok.all(axis=1)
            if rows_ok.all():                            # bloc sans élimination
                pos += blk.shape[0]
                B = min(2 * B, 1024)
                continue
            j = int(rows_ok.argmin())                    # premier cas qui élimine
            cand = cand[ok[j]]
            pos += j + 1
            B = 8
        idx = int(cand[0]) if cand.shape[0] == 1 else int(cand[np.random.randint(cand.shape[0])])
        return self.pop[idx].copy()

    def _select_reference(self) -> "Node":
        """Filtrage cas par cas (version 0.7), gardé comme référence : les
        tests vérifient que select() rend le même individu à chaque tirage."""
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
    frag = state.FRAGMENT_LIB.sample(min_size=2, max_size=cfg.MAX_TREE_SIZE // 3)
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
    if not state.FRAGMENT_LIB.fragments:
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

    frag = state.FRAGMENT_LIB.sample(min_size=min_frag, max_size=min(max_frag, 12))
    if frag is None:
        frag = state.FRAGMENT_LIB.sample(min_size=2, max_size=8)
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
    if state.FRAGMENT_LIB.fragments:
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
            op = _pool_choice(["+", "-", "*"], [3, 2, 3], fallback="+") or "+"
            tree = Node(op, tree, frag) if random.random() < 0.5 else Node(op, frag, tree)
        elif r < 0.65:
            # Wrapper unaire autour de l'arbre
            op = _pool_choice(["sin", "cos", "neg", "sq"], [2, 2, 1, 2])
            if op is not None:
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
    # [v0.8] Le graphe de co-occurrences est indexé par canonical_hash
    # (FragmentCoGraph.deposit_individual) : le chercher par structural_hash
    # ne trouvait le fragment que s'il ne contenait aucune constante, et le
    # tirage d'un compagnon retombait sinon sur la bibliothèque seule.
    h_root = root_frag.canonical_hash()
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
            op = _pool_choice(["+", "-", "*"], [3, 2, 3], fallback="+") or "+"
            tree = Node(op, tree, frag) if random.random() < 0.5 else Node(op, frag, tree)
        elif r < 0.65:
            op = _pool_choice(["sin", "cos", "neg", "sq"], [2, 2, 1, 2])
            if op is not None:
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
    # [v0.8] Le graphe de co-occurrences est indexé par canonical_hash
    # (FragmentCoGraph.deposit_individual) : le chercher par structural_hash
    # ne trouvait le fragment que s'il ne contenait aucune constante, et le
    # tirage d'un compagnon retombait sinon sur la bibliothèque seule.
    h_root = root_frag.canonical_hash()
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
