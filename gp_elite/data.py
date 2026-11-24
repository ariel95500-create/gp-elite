"""The data of the console: the scalers, the loading of CSV files and
their optional dependencies, and the problems of the console.

Part of gp_elite/core.py until 1.4.0, moved without change in 1.5.
"""
from __future__ import annotations

import math
import numpy as np
import os
from typing import Optional, List, Tuple, Dict, Any

from . import state
from .config import (_BATTERY_UNARY_OPS, _GENCSV_POOLS)
from .datasets import (SYRACUSE_N_FEATURES)

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
