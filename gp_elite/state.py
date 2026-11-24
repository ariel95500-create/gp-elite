"""The shared state of the engine: the names of gp_elite.core of 1.4.0
that change while it runs (benchmarks/results_1.5/split/map.txt).

Every function of the engine reads and sets them here, at the moment it
runs (`state.NAME`), never through a copy; gp_elite.core passes on to this
module the names set on it. The values below are those core.py gave them
when it was imported. Three are not defined until a fit sets them, as in
1.4.0: VAL_R2_TOLERANCE, _CUSTOM_LOSS_ROBUST, _CUSTOM_LOSS_USE_SCALING. The
three memories (FRAGMENT_LIB, COGRAPH, SEQ_MEM) are made by gp_elite.memory
when it is imported, each after its class, as core.py made them in 1.4.0.
"""
from __future__ import annotations

import numpy as np
from typing import Any, Dict, List, Optional   # named in the annotations below

PROBE_X: np.ndarray = np.zeros((20, 4))
CURRENT_RESIDUAL_SIG: Optional[np.ndarray] = None
_DIM_SEARCH = None
_DIM_GATE_DIMS = None       # [v0.4] miroir de cfg.FEAT_DIMS pour _track_val_candidate
_DIM_GATE_TARGET = None
_LS_SCALE_ONLY = False
_DIM_UNKNOWN_CONST = False
_GENERIC_CSV_MODE: bool       = False
_GENERIC_BINARY_OPS: list     = ["+", "-", "*", "/", "pow"]
_GENERIC_BINARY_WEIGHTS: list = [4, 4, 5, 2, 3]
_GENERIC_UNARY_OPS: list      = ["exp", "log", "sqrt", "tanh", "sq", "neg", "abs"]
_GENERIC_UNARY_WEIGHTS: list  = [4, 3, 3, 2, 3, 1, 2]
CSV_FEATURE_NAMES: list = []
CSV_TARGET_NAME: str    = "y"
_SYRACUSE_MODE: bool = False
_BATTERY_CSV_MODE: bool = False
_COMPILE_CACHE: Dict[int, Any] = {}
_PARAMETRIC_CACHE: Dict[int, Any] = {}
_SYRACUSE_Y_RAW:     np.ndarray = np.array([])  # cible brute avant normalisation
_SYRACUSE_X_RAW:     np.ndarray = np.array([])  # entiers bruts avant feature-engineering
_SYRACUSE_FEAT_MINS: np.ndarray = np.array([])  # min de chaque feature (pour dénorm)
_SYRACUSE_FEAT_MAXS: np.ndarray = np.array([])  # max de chaque feature (pour dénorm)
_fitness_cache: Dict[int, float] = {}
_PRED_CACHE: dict = {}
_USE_LINEAR_SCALING: bool = True   # synchronisé sur cfg dans evolve()
_CUSTOM_LOSS_FN = None
_CUSTOM_SEEDS = None
_SEEDS_UNDER_UNITS = True
_BINOMIAL_SEEDS = True
_ELEMENTARY_SEEDS = True
_E2_SEEDS = False
_TOLERANT_SEEDS = True
_TOLERANT_N2 = True
_TOLERANT_REFIT = False
_CUSTOM_LOSS_PARSIMONY = 0.0
_feature_usage_counter: List[int] = []   # initialisé par reset_feature_usage()
_PARALLEL_BROKEN = False     # vrai apres un pool brise : plus de tentative
_PARALLEL_WARNED = False
_TIME_LIMIT_HIT = False  # [v0.7-TIME] vrai si le dernier evolve() a ete
                         # interrompu par l'echeance cfg.DEADLINE
_VAL_XS = None          # hold-out features  (None = validation désactivée)
_VAL_YS = None          # hold-out cible
_VAL_TRAIN_XS = None    # [v23.1] train features (test de stabilité numérique)
_NEAR_PROBE_XS = None
_NEAR_BAND = None          # (centre, demi-largeur) en unites de y
_NEAR_GUARD_SWAPS = 0      # nombre de departages effectifs (diagnostic, tests)
_EXACT_PRIORITY_SWAPS = 0   # [v0.7-EXACT] nombre de fois ou la regle a change le choix
_FAITHFUL_SWAPS = 0          # [v0.8] departages par la fidelite de la formule
_VAL_TRAIN_YS = None    # [v23.1] train cible
_EXTRAP_PROBE_XS = None
_EXTRAP_BAND = None     # (y_lo, y_hi) plausibles
_VAL_CANDS: list = []   # [(val_mse, val_se, size, node)] candidats-champions
_POLISH_GRACE_S = 1.0
_POLISH_ADMITTED = 0          # variantes polies admises (diagnostic, bancs)
_SMALL_CV = False
_SMALL_ON = False                 # actif pour l'ajustement en cours
