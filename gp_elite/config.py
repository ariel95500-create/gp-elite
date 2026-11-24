"""The configuration of a run: the run trace (TRACE), Config, the pools
of operators and how a run draws from them, and the configurations
the console makes (make_cfg, make_cfg_nd).

Part of gp_elite/core.py until 1.4.0, moved without change in 1.5.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any

from . import state

# ============================================================
# CONFIGURATION GLOBALE
# ============================================================

# [v0.4.1] Linear scaling PUREMENT multiplicatif (regression par l'origine).
# Actif en mode dimensionnel : voir _linear_scale_params.
# ═══════════════════════════════════════════════════════════════════════════
# [v0.7] JOURNAL D'EXÉCUTION — observabilité du moteur
#
# Pourquoi. Cinq défauts trouvés en juillet 2026 avaient la même nature : non
# pas une erreur de logique, mais une INTERACTION INVISIBLE entre mécanismes.
# L'état dimensionnel qui fuyait d'un fit au suivant ; la notation faite sur une
# forme mise à l'échelle et la livraison sur une autre ; le feu vert stigmergique
# qui gouvernait aussi le nettoyage des introns ; un burn-in qui bloquait
# structurellement un mécanisme sans que rien ne le signale. Chacun a coûté des
# heures de mesure alors qu'une ligne de sortie l'aurait révélé.
#
# RÈGLE ABSOLUE : ce journal est en ÉCRITURE SEULE. Rien de ce qui y est
# enregistré n'est jamais relu par le moteur. Ajouter une entrée ne peut donc
# pas modifier un résultat — sans quoi on ajouterait au problème qu'on prétend
# résoudre.
# ═══════════════════════════════════════════════════════════════════════════
class _RunTrace:
    """Collecteur d'événements. Aucune de ses valeurs ne pilote quoi que ce soit."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.first = {}      # premier événement d'un type : {clé: description}
        self.count = {}      # compteurs
        self.value = {}      # dernière valeur observée

    def once(self, key, description):
        """Enregistre le PREMIER événement de ce type et ignore les suivants."""
        if key not in self.first:
            self.first[key] = description

    def bump(self, key, by=1):
        self.count[key] = self.count.get(key, 0) + by

    def set(self, key, val):
        self.value[key] = val

    def lines(self):
        """Le journal, prêt à afficher. Liste vide si rien n'a été observé."""
        out = []
        for k in ("dim_mode", "unknown_const", "ls_mode"):
            if k in self.value:
                out.append(f"  {k:<22} {self.value[k]}")
        for k, d in self.first.items():
            out.append(f"  {k:<22} {d}")
        for k, c in sorted(self.count.items()):
            out.append(f"  {k:<22} {c}")
        return out

    def report(self, title="JOURNAL D'EXÉCUTION"):
        ls = self.lines()
        if not ls:
            return
        print(f"\n  {title}")
        print("  " + "-" * 58)
        for l in ls:
            print(l)


TRACE = _RunTrace()

# [v0.5] Mode « constante mystere » : la constante multiplicative de tete peut
# PORTER une dimension, deduite par homogeneite (cible / dimension de l'arbre).
# Leve la limite « constantes sans dimension » de la v0.4.


def _ds():
    """[v0.4] Import paresseux de dim_search (évite l'import circulaire :
    dim_search importe core.Node)."""
    if state._DIM_SEARCH is None:
        from . import dim_search as _m
        state._DIM_SEARCH = _m
    return state._DIM_SEARCH


def _dim_active(cfg):
    return getattr(cfg, "FEAT_DIMS", None) is not None


@dataclass
class Config:
    # [v0.4] Recherche contrainte par les dimensions physiques.
    #   FEAT_DIMS  : {0: {"kg":1}, 1: {"m":1,"s":-1}}  (dict par index de feature)
    #   TARGET_DIM : {"kg":1, "m":2, "s":-2}
    # None (défaut) = comportement v0.3 strictement inchangé.
    FEAT_DIMS = None
    TARGET_DIM = None
    # [v0.5] Autorise la constante de tete a porter une dimension.
    UNKNOWN_CONST = False

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
    # [v0.8] Polissage des finalistes (voir _polish_finalists).
    FINAL_POLISH: bool     = True
    # [v0.8] Monômes ajustés en échelle log (voir _make_power_law_seeds).
    POWER_LAW_SEEDS: bool  = True
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
    # [v0.7-TIME] Echeance ABSOLUE (time.time()) au-dela de laquelle l'evolution
    # s'arrete proprement et rend le meilleur modele trouve. None = pas de
    # limite. Posee par symbolic_regression(time_limit=...) ; verifiee avant
    # chaque generation (sequentiel), avant chaque ronde (maitre parallele) et
    # avant chaque generation DANS les processus fils. La premiere generation
    # s'execute toujours, pour garantir un modele.
    DEADLINE: Optional[float] = None

    # [v19] Déduplication sémantique de population (cf. Operon / PySR)
    USE_SEMANTIC_DEDUP: bool = False # écarte les clones comportementaux ; OFF par default :
    #   sur cette base le taux de clones est ~14%%, insuffisant pour amortir le
    #   coût du hash sémantique. Activable pour gros POP_SIZE ou problèmes très
    #   convergents (Operon/PySR l'utilisent sur des populations moins diverses).
    SEMANTIC_DEDUP_DECIMALS: int = 3 # arrondi des prédictions probe pour le hash sémantique

    # Sorties
    LOG_CSV: str           = "gp_elite_log.csv"
    # [v0.7] Une bibliotheque n'ecrit pas de fichier en silence. L'API met ce
    # drapeau a False ; le mode console le garde (journal dans le DOSSIER
    # COURANT, plus dans le dossier d'installation du paquet).
    WRITE_LOG_CSV: bool    = True
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
ALL_UNARY_OPS  = UNARY_OPS  + ["tanh", "exp", "tan", "is_even", "step",
                               "arcsin"]   # [1.3-A1]
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
#   trig     : + sin/cos — phénomènes périodiques/oscillants ; [1.3-A1] et
#              arcsin (réfraction, diffraction)
#   full     : tout — quand on ne sait pas a priori (avec arcsin depuis 1.3)
#   poly     : uniquement +,-,*,/,sq,cube,sqrt — relations algébriques pures
_GENCSV_POOLS = {
    "physical": (["+", "-", "*", "/", "pow"],          [4, 4, 5, 2, 3],
                 ["exp", "log", "sqrt", "tanh", "sq", "neg", "abs"],
                                                        [4, 3, 3, 2, 3, 1, 2]),
    # [1.3-A1] arcsin (argument clipped to [-1, 1]) in trig and full, weight 2
    "trig":     (["+", "-", "*", "/", "pow"],          [3, 3, 4, 2, 1],
                 ["sin", "cos", "exp", "log", "sqrt", "tanh", "sq", "neg", "abs",
                  "arcsin"],
                                                        [3, 3, 2, 2, 2, 2, 2, 1, 1, 2]),
    "full":     (["+", "-", "*", "/", "pow"],          [3, 3, 4, 2, 1],
                 ["sin", "cos", "log", "exp", "sqrt", "tanh", "abs", "neg", "sq", "cube",
                  "arcsin"],
                                                        [2, 2, 2, 2, 2, 2, 1, 1, 3, 1, 2]),
    "poly":     (["+", "-", "*", "/"],                 [4, 4, 5, 2],
                 ["sqrt", "neg", "sq", "cube", "abs"],  [2, 1, 3, 2, 1]),
    # [CONSERVATION] Pool minimal pour la découverte de lois physiques : pas
    # d'exp/log/pow (qui génèrent des arbres exploitant le bruit numérique des
    # dérivées). Juste les briques des invariants courants : +, -, *, carré,
    # et trigonométrie pour les potentiels (pendule, etc.).
    "conserve": (["+", "-", "*"],                      [4, 3, 4],
                 ["sq", "cos", "sin", "neg"],           [4, 3, 3, 1]),
}


# Noms réels des colonnes (pour affichage des formules : X[0] → "temperature")

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

# Flag global activé par load_custom_csv() → tous les pools basculent

def _get_ops_for_role(role: str):
    """Retourne (binary_ops, binary_weights, unary_ops, unary_weights) selon le rôle.

    En mode Syracuse (_SYRACUSE_MODE=True), tous les rôles utilisent
    le pool algébrique Collatz — tanh/sin/cos/exp exclus.
    En mode CSV batterie (_BATTERY_CSV_MODE=True), pool physique batterie.
    """
    # [SYRACUSE] pool Collatz prioritaire sur tous les rôles
    if state._SYRACUSE_MODE:
        if role == "cleaner":
            return (_CLEANER_BINARY_OPS, _CLEANER_BINARY_WEIGHTS,
                    _CLEANER_UNARY_OPS,  _CLEANER_UNARY_WEIGHTS)
        return (_SYRACUSE_BINARY_OPS, _SYRACUSE_BINARY_WEIGHTS,
                _SYRACUSE_UNARY_OPS,  _SYRACUSE_UNARY_WEIGHTS)
    # [v22-CSV] pool générique prioritaire (choisi par l'utilisateur)
    if state._GENERIC_CSV_MODE:
        return (state._GENERIC_BINARY_OPS, state._GENERIC_BINARY_WEIGHTS,
                state._GENERIC_UNARY_OPS,  state._GENERIC_UNARY_WEIGHTS)
    # [v16-BATTERY CSV] pool physique prioritaire sur tous les rôles
    if state._BATTERY_CSV_MODE:
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
    if state._GENERIC_CSV_MODE:
        b_ops, b_w = state._GENERIC_BINARY_OPS, state._GENERIC_BINARY_WEIGHTS
        u_ops, u_w = state._GENERIC_UNARY_OPS,  state._GENERIC_UNARY_WEIGHTS
    elif state._SYRACUSE_MODE:
        b_ops, b_w = _SYRACUSE_BINARY_OPS, _SYRACUSE_BINARY_WEIGHTS
        u_ops, u_w = _SYRACUSE_UNARY_OPS,  _SYRACUSE_UNARY_WEIGHTS
    elif state._BATTERY_CSV_MODE:
        b_ops, b_w = _BATTERY_BINARY_OPS, _BATTERY_BINARY_WEIGHTS
        u_ops, u_w = _BATTERY_UNARY_OPS,  _BATTERY_UNARY_WEIGHTS
    else:
        b_ops, b_w = BINARY_OPS, BINARY_WEIGHTS
        u_ops, u_w = UNARY_OPS,  UNARY_WEIGHTS
    all_ops = b_ops + u_ops
    all_w   = b_w   + u_w
    return b_ops, b_w, u_ops, u_w, all_ops, all_w

def _active_pool_ops():
    """[v0.7] Operateurs autorises pour le generateur TYPE (units=). Le pool
    `operators=` vit dans _GENERIC_BINARY_OPS / _GENERIC_UNARY_OPS, restaures
    aussi dans les processus paralleles. None = pas de filtrage (hors mode
    CSV generique, comportement historique)."""
    if not state._GENERIC_CSV_MODE:
        return None
    return frozenset(state._GENERIC_BINARY_OPS) | frozenset(state._GENERIC_UNARY_OPS)


def _pool_choice(ops, weights, fallback="neg"):
    """[v0.7] Tire un operateur de `ops`, RESTREINT au pool `operators=`.

    Les constructeurs stigmergiques enveloppaient leurs arbres avec un unaire
    tire de ["sin", "cos", "neg", "sq"] code en dur : du cos apparaissait
    dans le front de Pareto avec le pool 'physical', qui n'en contient pas.
    Un seul tirage aleatoire comme avant : pour un pool qui contient deja ces
    operateurs, le comportement est strictement inchange."""
    pool = _active_pool_ops()
    if pool is not None:
        pairs = [(o, w) for o, w in zip(ops, weights) if o in pool]
        if not pairs:
            return fallback if fallback in pool else None
        ops, weights = [p[0] for p in pairs], [p[1] for p in pairs]
    return random.choices(ops, weights=weights)[0]


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
                thorough: bool = False,
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
                   fast=fast, ultrafast=ultrafast, thorough=thorough,
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
                thorough: bool = False,
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
    elif thorough:
        # [MESURE] pop=400 bat 300 et 800 a budget egal (15 comparaisons
        # appariees gagnees sur 18, 3 equations). Mode destine a la DECOUVERTE
        # de lois : budget eleve, plus lent, recuperation exacte accessible.
        pop, gen, islands = 400, 400, 4
    elif fast:
        # [MESURE] 300 -> 400 : meilleur a budget egal, sans surcout de temps
        # (le temps suit le produit pop x generations, pas la population seule).
        pop, gen, islands = 400, 200, 3
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
