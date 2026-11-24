"""The datasets the console builds: the Collatz (Syracuse) features and
data, the decoy features, and build_dataset.

Part of gp_elite/core.py until 1.4.0, moved in 1.5, where it reads and
sets the names of the shared state in gp_elite.state (state.NAME).
"""
from __future__ import annotations

import random
import numpy as np
from typing import Optional, List, Tuple, Dict, Any

from . import state
from .config import (_SYRACUSE_BINARY_OPS, _SYRACUSE_UNARY_OPS)
from .config import Config   # [1.5] named in annotations only
from .evaluation import (_HOT_ZONES)

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

    # ── 1. Calcul des temps de vol ────────────────────────────────────────
    ns      = np.arange(n_start, n_end + 1, dtype=np.int64)
    ns_f    = ns.astype(np.float64)
    flights = np.array([_collatz_flight_time(int(n)) for n in ns],
                       dtype=np.float64)

    state._SYRACUSE_X_RAW = ns_f.copy()
    state._SYRACUSE_Y_RAW = flights.copy()
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
    state._SYRACUSE_FEAT_MINS = np.array([f.min() for f in raw_features])
    state._SYRACUSE_FEAT_MAXS = np.array([f.max() for f in raw_features])

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
    state._SYRACUSE_MODE = True

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

# ── Métadonnées des variables leurres ─────────────────────────────────────────
# Clé = problem_key, valeur = liste des indices de features leurres.
# Utilisé par decoy_report() pour produire un verdict pass/fail explicite.
DECOY_FEATURES: Dict[str, List[int]] = {
    "ND1_DECOY":    [3],
    "ND3_DECOY":    [3],
    "ND5_DECOY":    [3],
    "BATTERY_SOH":  [3],   # X[3] = leurre (bruit pur, déconnecté de la cible)
}
