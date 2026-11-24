"""The memories of the search: the fragment library, the probe set and
the semantic signatures, the co-graph of fragments, the sequence
memory, and what they pass on to the next run (warm_transfer).

Part of gp_elite/core.py until 1.4.0, moved in 1.5, where it reads and
sets the names of the shared state in gp_elite.state (state.NAME).
"""
from __future__ import annotations

import bisect
import random
import numpy as np
import os
import json
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any

from . import state
from .config import (_active_pools)
from .config import Config   # [1.5] named in annotations only
from .tree import (Node, get_all_nodes, to_string, tree_depth, tree_size)
from .simplification import (_TRIVIAL_CACHE, simplify)
from .evaluation import (_safe_write, evaluate_vector)
from .genetic import (random_terminal, random_tree)

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


# [v0.8] Sonde de _is_semantically_trivial (construite une fois) et verdicts
# mémorisés, vidés en même temps que le cache de simplification.
_TRIVIAL_PROBE_X = np.array([
    [-2.0, -1.5,  0.3,  1.0],
    [-1.0, -0.5,  0.7,  2.0],
    [ 0.5,  0.1,  1.1, -0.5],
    [ 1.5,  1.0, -0.3, -1.5],
    [ 2.5,  2.0, -1.0, -2.5],
])


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
        self._sampling = None   # [v0.8] tables de tirage (voir begin_sampling)

    # [v0.8] Tables de tirage figées. sample() reconstruisait à CHAQUE appel la
    # liste des candidats et leurs poids sémantiques en parcourant toute la
    # bibliothèque, alors qu'elle ne change qu'aux dépôts et évaporations.
    # Entre begin_sampling() et end_sampling(), fenêtre pendant laquelle
    # l'appelant garantit que la bibliothèque n'est pas modifiée (la
    # reproduction d'une île), chaque table est calculée une fois, à
    # l'identique, puis réutilisée : mêmes tirages, bit pour bit.
    def begin_sampling(self):
        self._sampling = {}

    def end_sampling(self):
        self._sampling = None

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
        [v0.8] Verdict mémorisé par arbre exact jusqu'au prochain vidage du
        cache de simplification (_clear_simplify_caches) : dans cet
        intervalle, simplify(node) rendrait de toute façon la forme déjà
        calculée, donc le verdict est le même. Les dépôts testaient les mêmes
        sous-arbres à chaque génération (5 % du temps total).
        """
        h = node.exact_hash()
        v = _TRIVIAL_CACHE.get(h)
        if v is not None:
            return v
        v = self._is_semantically_trivial_uncached(node)
        _TRIVIAL_CACHE[h] = v
        return v

    def _is_semantically_trivial_uncached(self, node: "Node") -> bool:
        simplified = simplify(node)  # [v19-OPT] simplify ne mute plus l'entrée
        if simplified.left is None and simplified.right is None:
            return True
        # Sonde N-D générique : matrice 5×4 couvrant les features 0–3
        try:
            vals = evaluate_vector(simplified, _TRIVIAL_PROBE_X)
            if np.std(vals) < 1e-6:
                return True
        except Exception:
            pass
        return False

    def __getstate__(self):
        # [v0.8] une table de tirage ne traverse jamais un processus
        st = dict(self.__dict__)
        st["_sampling"] = None
        return st

    def merge_from(self, other: "FragmentLibrary"):
        """[v20-PAR] Fusionne la bibliothèque d'un worker dans celle du maître.
        Chaque worker part du MÊME instantané puis dépose/évapore localement :
        on fusionne par MAX de phéromone (signal le plus fort conservé, pas
        de double comptage de l'instantané commun), freq/last_gen par max,
        best_fitness par min."""
        self._sampling = None
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
        self._sampling = None
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
                sig = compute_semantic_sig(node, state.PROBE_X)
                # Bonus δ si le fragment corrige le résidu courant
                if sig is not None and state.CURRENT_RESIDUAL_SIG is not None:
                    sem = semantic_score(sig, state.CURRENT_RESIDUAL_SIG)
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
                    e.semantic_signature = compute_semantic_sig(e.node, state.PROBE_X)

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
        self._sampling = None
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
        [v0.8] Table de tirage réutilisée dans une fenêtre begin_sampling().
        """
        res_sig = state.CURRENT_RESIDUAL_SIG
        cache = getattr(self, "_sampling", None)
        if cache is not None:
            key = (min_size, max_size, root_op)
            ent = cache.get(key)
            if ent is None or ent[0] is not res_sig:
                ent = (res_sig,) + self._sample_table(min_size, max_size,
                                                      root_op, res_sig)
                cache[key] = ent
            _, candidates, cumsum, total = ent
        else:
            candidates, cumsum, total = self._sample_table(min_size, max_size,
                                                           root_op, res_sig)
        if candidates is None or total <= 0:
            return None
        # Tirage pondéré via cumsum (plus rapide que boucle cumul)
        r = random.random() * total
        idx = int(np.searchsorted(cumsum, r))
        idx = min(idx, len(candidates) - 1)
        return candidates[idx][1].node.copy()  # [v19-OPT] copy itératif (≈50× vs deepcopy)

    def _sample_table(self, min_size, max_size, root_op, res_sig):
        """(candidats, poids cumulés, total) du tirage de sample()."""
        candidates = [
            (h, e) for h, e in self.fragments.items()
            if min_size <= e.size <= max_size
            and (root_op is None or e.root_op == root_op)
        ]
        if not candidates:
            return None, None, None

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
        return candidates, np.cumsum(weights), total

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
state.FRAGMENT_LIB = FragmentLibrary()


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

# Résidu du meilleur individu courant projeté sur PROBE_X
# Mis à jour dans evolve_island() après chaque amélioration du best


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
        self._sampling = None   # [v0.8] tables de tirage (voir begin_sampling)

    # [v0.8] Même principe que FragmentLibrary.begin_sampling : sample_pair et
    # sample_companion parcouraient toutes les arêtes (jusqu'à 2 000) à chaque
    # appel. Dans la fenêtre, où ni le graphe ni la bibliothèque ne changent,
    # les tables sont construites une fois dans l'ordre exact du parcours
    # d'origine, et le tirage « premier cumul >= r » se fait par bisection :
    # même résultat que la boucle, les poids étant positifs.
    def begin_sampling(self, lib: "FragmentLibrary"):
        self._sampling = {"lib": lib, "pair": None, "adj": None, "comp": {}}

    def end_sampling(self):
        self._sampling = None

    @staticmethod
    def _cumulate(ws):
        """Cumuls dans l'ordre (mêmes additions que la boucle d'origine),
        ou None si un poids négatif ou non fini interdit la bisection."""
        cum, acc = [], 0.0
        for w in ws:
            if not (w >= 0.0) or w == float("inf"):
                return None
            acc += w
            cum.append(acc)
        return cum

    @staticmethod
    def _key(h1: int, h2: int) -> Tuple[int, int]:
        return (h1, h2) if h1 < h2 else (h2, h1)

    def __getstate__(self):
        st = dict(self.__dict__)
        st["_sampling"] = None
        return st

    def merge_from(self, other: "FragmentCoGraph"):
        """[v20-PAR] Fusion par MAX d'arête (même logique que FragmentLibrary)."""
        self._sampling = None
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
        self._sampling = None
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
        self._sampling = None
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
        cache = getattr(self, "_sampling", None)
        if cache is not None and cache["lib"] is lib:
            ent = cache["comp"].get(h_root)
            if ent is None:
                adj = cache["adj"]
                if adj is None:
                    adj = cache["adj"] = self._adjacency(lib)
                cands = adj.get(h_root, [])
                ent = (cands, sum(w for _, w in cands),
                       self._cumulate(w for _, w in cands))
                cache["comp"][h_root] = ent
            candidates, total, cum = ent
            if not candidates or total <= 0:
                return None
            r = random.random() * total
            if cum is not None:
                i = bisect.bisect_left(cum, r)
                h_other = candidates[i][0] if i < len(candidates) else candidates[-1][0]
                return lib.fragments[h_other].node.copy()
            cumul = 0.0
            for h_other, w in candidates:
                cumul += w
                if r <= cumul:
                    return lib.fragments[h_other].node.copy()
            return lib.fragments[candidates[-1][0]].node.copy()

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

        r = random.random() * total
        cumul = 0.0
        for h_other, w in candidates:
            cumul += w
            if r <= cumul:
                return lib.fragments[h_other].node.copy()  # [v19-OPT]
        return lib.fragments[candidates[-1][0]].node.copy()  # [v19-OPT]

    def _adjacency(self, lib: "FragmentLibrary") -> dict:
        """h -> [(voisin, poids)] dans l'ordre de parcours de self.co, voisins
        limités aux fragments présents dans lib (filtre de sample_companion)."""
        adj: dict = {}
        frags = lib.fragments
        for (h1, h2), w in self.co.items():
            if h1 == h2:
                if h2 in frags:
                    adj.setdefault(h1, []).append((h2, w))
                continue
            if h2 in frags:
                adj.setdefault(h1, []).append((h2, w))
            if h1 in frags:
                adj.setdefault(h2, []).append((h1, w))
        return adj

    def sample_pair(self, lib: "FragmentLibrary"
                    ) -> Tuple[Optional[Any], Optional[Any]]:
        """
        Tire une paire (root_frag, companion) corrélée.
        Pondère par le poids d'arête × τ_root × τ_companion.
        Retourne (None, None) si la lib ou le graphe est trop vide.
        """
        if not self.co or not lib.fragments:
            return None, None

        cache = getattr(self, "_sampling", None)
        if cache is not None and cache["lib"] is lib:
            ent = cache["pair"]
            if ent is None:
                valid = self._pair_table(lib)
                ent = cache["pair"] = (valid, sum(w for _, w in valid),
                                       self._cumulate(w for _, w in valid))
            valid, total, cum = ent
        else:
            valid, total, cum = self._pair_table(lib), None, None
            if valid:
                total = sum(w for _, w in valid)

        if not valid:
            return None, None
        if total <= 0:
            return None, None

        r = random.random() * total
        if cum is not None:
            i = bisect.bisect_left(cum, r)
            if i < len(valid):
                (h1, h2), _ = valid[i]
                if random.random() < 0.5:
                    h1, h2 = h2, h1
                return lib.fragments[h1].node.copy(), lib.fragments[h2].node.copy()
            (h1, h2), _ = valid[-1]
            return (lib.fragments[h1].node.copy(), lib.fragments[h2].node.copy())
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

    def _pair_table(self, lib: "FragmentLibrary") -> list:
        """Distribution de sample_pair sur les arêtes valides (ordre de self.co)."""
        valid: List[Tuple[Tuple[int, int], float]] = []
        frags = lib.fragments
        for (h1, h2), w in self.co.items():
            if h1 in frags and h2 in frags:
                tau_prod = frags[h1].tau * frags[h2].tau
                valid.append(((h1, h2), w * tau_prod))
        return valid

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
state.COGRAPH = FragmentCoGraph()


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
state.SEQ_MEM = FragmentSequenceMemory()


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
    state.FRAGMENT_LIB.end_sampling()
    state.COGRAPH.end_sampling()
    # Fragment library : décote τ
    for e in state.FRAGMENT_LIB.fragments.values():
        e.tau *= decay_lib
    # Élagage post-décote
    to_del = [h for h, e in state.FRAGMENT_LIB.fragments.items()
              if e.tau < FragmentLibrary.MIN_TAU]
    for h in to_del:
        del state.FRAGMENT_LIB.fragments[h]

    # Co-graph : décote les arêtes
    for k in list(state.COGRAPH.co.keys()):
        state.COGRAPH.co[k] *= decay_co
        if state.COGRAPH.co[k] < FragmentCoGraph.MIN_CO:
            del state.COGRAPH.co[k]

    # Sequence memory : décote les transitions
    state.SEQ_MEM.warm_transfer(decay=decay_seq)

    kept_frags = len(state.FRAGMENT_LIB.fragments)
    kept_edges = len(state.COGRAPH.co)
    kept_trans = len(state.SEQ_MEM.transitions)
    print(f"[TRANSFER] Decay applied — "
          f"fragments={kept_frags}  edges={kept_edges}  transitions={kept_trans}")
