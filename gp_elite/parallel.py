"""The islands in parallel: the workers, the pools of processes, and the
guard of the main module.

Part of gp_elite/core.py until 1.4.0, moved without change in 1.5.
"""
from __future__ import annotations

import random
import numpy as np
import time
import sys
import os

from . import state
from .config import (TRACE)
from .tree import (to_string, tree_depth, tree_size)
from .simplification import (_clear_simplify_caches)
from .scoring import (fitness, raw_mse, wrap_linear_scaling)
from .memory import (update_residual_sig)
from .final_choice import (_Patience, _early_stop_threshold, _holdout_mse,
                           _track_small_candidate, _track_val_candidate)
from .islands import (_PW, _smart_reset_explorers, evolve_island, migrate)

def _pool_probe():
    """[v0.7-PAR] Tache vide : prouve qu'un worker a fini de demarrer."""
    return True


def _parallel_worker_init(data_path, use_ls, syracuse_mode,
                          gencsv=None, battery_mode=False,
                          ls_scale_only=False, dim_unknown_const=False,
                          quiet=False):
    """Initializer du pool : reçoit les données constantes UNE fois par worker.
    [v0.7-PAR] Les tableaux (xs, ys, sondes, series Syracuse) arrivent par un
    fichier temporaire, pas par initargs : les initargs sont ecrits dans le
    tube de demarrage du fils, et au-dela de sa capacite (64 Ko sous Linux)
    le parent y reste bloque si le fils meurt pendant son amorcage -- ce que
    fait justement un fils qui re-execute un script sans garde __main__. Le
    repli sequentiel promis devenait un blocage definitif des ~3000 lignes.
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
    state._LS_SCALE_ONLY = bool(ls_scale_only)
    state._DIM_UNKNOWN_CONST = bool(dim_unknown_const)
    import pickle as _pickle
    if quiet:
        # [v0.7-PAR] Le parent est silencieux (symbolic_regression(verbose=
        # False) redirige sa sortie) : ses workers le sont aussi. Sans cela,
        # sur une machine a 4 coeurs ou plus, leurs messages de progression
        # s'affichaient chez l'utilisateur malgre verbose=False.
        _sys.stdout = open(_os.devnull, "w")
    with open(data_path, "rb") as _fh:
        xs, ys, probe_x, syracuse_y_raw, syracuse_x_raw = _pickle.load(_fh)
    _PW["xs"] = xs
    _PW["ys"] = ys
    state.PROBE_X             = probe_x
    state._USE_LINEAR_SCALING = use_ls
    state._SYRACUSE_MODE      = syracuse_mode
    if syracuse_y_raw is not None:
        state._SYRACUSE_Y_RAW = syracuse_y_raw
    if syracuse_x_raw is not None:
        state._SYRACUSE_X_RAW = syracuse_x_raw
    # [v22-CSV] propager le mode CSV générique + pools + noms de colonnes
    state._BATTERY_CSV_MODE = battery_mode
    if gencsv is not None:
        state._GENERIC_CSV_MODE = True
        (state._GENERIC_BINARY_OPS, state._GENERIC_BINARY_WEIGHTS,
         state._GENERIC_UNARY_OPS,  state._GENERIC_UNARY_WEIGHTS,
         state.CSV_FEATURE_NAMES, state.CSV_TARGET_NAME) = gencsv
    else:
        state._GENERIC_CSV_MODE = False

def _island_round_task(payload):
    """Évolue UNE île pendant n_gens générations dans le worker.
    Reproduit fidèlement le housekeeping par génération de la boucle
    séquentielle (caches, _gen_bucket, mono_pen Syracuse)."""
    (island, gen_start, n_gens, frag, cog, seq, residual, seed) = payload
    random.seed(seed)
    np.random.seed(seed & 0x7FFFFFFF)
    state.FRAGMENT_LIB         = frag
    state.COGRAPH              = cog
    state.SEQ_MEM              = seq
    state.CURRENT_RESIDUAL_SIG = residual
    xs, ys = _PW["xs"], _PW["ys"]
    cfg = island.cfg
    best_local = None
    _deadline = getattr(cfg, "DEADLINE", None)
    for gen in range(gen_start, gen_start + n_gens):
        # [v0.7-TIME] Echeance atteinte : on rend l'ile en l'etat. Jamais a la
        # generation 0, pour qu'au moins une generation produise un modele.
        if _deadline is not None and gen > 0 and time.time() >= _deadline:
            break
        if gen % 10 == 0:
            state._fitness_cache.clear()
        _clear_simplify_caches()
        if state._SYRACUSE_MODE:
            _t = gen / max(cfg.GENERATIONS - 1, 1)
            cfg._mono_pen_cache = 0.10 - _t * 0.07
        cfg._gen_bucket = gen // 10
        nb = evolve_island(island, xs, ys, gen)
        if nb is not None:
            best_local = nb
    return (island, best_local, state.FRAGMENT_LIB, state.COGRAPH, state.SEQ_MEM)


# ── [v0.7-PAR] Parallelisme sur pour les scripts sans garde __main__ ──────
# Les iles paralleles utilisent le demarrage « spawn » (identique sur tous les
# systemes). Un processus fils spawn RE-EXECUTE le script principal de
# l'utilisateur. Sans `if __name__ == "__main__":`, chaque fils refait donc
# tout le calcul avant de servir : mesure sur 800 points, le script est
# execute 3 fois et le mode parallele met 9,0 s contre 4,6 s en sequentiel.
# Les exemples du README n'ont pas cette garde : c'est le cas par defaut d'un
# nouvel utilisateur sur une machine a 4 coeurs ou plus.
#
# Detection : pendant la creation du pool, le parent pose GP_ELITE_POOL_CHILD
# dans l'environnement, que les fils heritent. Un fils qui atteint evolve()
# pendant son demarrage est forcement en train de re-executer le script : il
# se termine SANS bruit, le pool du parent se brise, le parent bascule en
# sequentiel, previent une seule fois, et ne retente plus le parallele.
_POOL_CHILD_ENV = "GP_ELITE_POOL_CHILD"


class _SkipLogExport(Exception):
    """Export du journal desactive (API) : sortie propre du bloc d'ecriture."""


def _exit_if_reimported_by_worker():
    """Termine un fils gp-elite qui est en train de RE-EXECUTER le script.

    Attention : pendant cette phase, multiprocessing.parent_process() n'est
    PAS encore renseigne (il ne l'est qu'au demarrage du travailleur, apres
    la re-execution). Les indicateurs fiables sont ceux qu'utilise
    multiprocessing lui-meme pour detecter la phase d'amorcage :
    l'attribut `_inheriting` du processus courant, et le nom `__mp_main__`
    donne au module principal re-importe. La variable d'environnement
    restreint la detection aux fils crees par gp-elite.
    """
    if os.environ.get(_POOL_CHILD_ENV) != "1":
        return
    try:
        import multiprocessing as _mp
        bootstrapping = bool(getattr(_mp.current_process(), "_inheriting", False))
    except Exception:
        bootstrapping = False
    main_mod = sys.modules.get("__main__")
    if bootstrapping or getattr(main_mod, "__name__", "") == "__mp_main__":
        sys.exit(0)          # silencieux : le parent gere le repli


def _warn_unguarded_main(err):
    """Avertissement unique, sur stderr (non capture par le mode silencieux)."""
    if state._PARALLEL_WARNED:
        return
    state._PARALLEL_WARNED = True
    import warnings
    main_file = getattr(sys.modules.get("__main__"), "__file__", None)
    if main_file:
        msg = ("gp-elite: parallel islands could not start, most likely "
               "because the script %r is not protected by "
               "`if __name__ == \"__main__\":` (required by multiprocessing). "
               "Continuing SEQUENTIALLY: the fit completes, but the islands "
               "then run one after the other, which is slower and can return "
               "another model than in parallel. "
               "Wrap your top-level code in that guard to use several cores, "
               "or pass parallel=False to run in sequence without this message."
               % os.path.basename(main_file))
    else:
        msg = ("gp-elite: parallel islands could not start (%s); continuing "
               "sequentially. Pass parallel=False to silence this message."
               % type(err).__name__)
    warnings.warn(msg, RuntimeWarning, stacklevel=3)


def _parallel_enabled(cfg) -> bool:
    """AUTO : parallèle si ≥4 cœurs et ≥2 îles ; True force ; False bloque."""
    flag = getattr(cfg, "PARALLEL_ISLANDS", None)
    if flag is False or cfg.N_ISLANDS < 2:
        return False
    if state._PARALLEL_BROKEN:          # [v0.7-PAR] deja echoue dans ce processus
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

    _syr_y = getattr(state, '_SYRACUSE_Y_RAW', None) if state._SYRACUSE_MODE else None
    _syr_x = getattr(state, '_SYRACUSE_X_RAW', None) if state._SYRACUSE_MODE else None
    # [v22-CSV] snapshot du mode CSV générique pour les workers
    _gencsv = ((list(state._GENERIC_BINARY_OPS), list(state._GENERIC_BINARY_WEIGHTS),
                list(state._GENERIC_UNARY_OPS),  list(state._GENERIC_UNARY_WEIGHTS),
                list(state.CSV_FEATURE_NAMES), state.CSV_TARGET_NAME)
               if state._GENERIC_CSV_MODE else None)

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
    _prev_hash = _os.environ.get("PYTHONHASHSEED")
    _prev_child = _os.environ.get(_POOL_CHILD_ENV)
    _os.environ["PYTHONHASHSEED"] = "0"
    _os.environ[_POOL_CHILD_ENV] = "1"      # [v0.7-PAR] herite par les fils

    # [v0.7-PAR] Donnees des workers par fichier temporaire (voir
    # _parallel_worker_init) : le message de demarrage reste petit.
    import pickle as _pickle, tempfile as _tempfile
    _data_path = None
    try:
        with _tempfile.NamedTemporaryFile(prefix="gp_elite_pool_", suffix=".pkl",
                                          delete=False) as _fh:
            _data_path = _fh.name
            _pickle.dump((xs, ys, state.PROBE_X, _syr_y, _syr_x), _fh,
                         protocol=_pickle.HIGHEST_PROTOCOL)
        with _cf.ProcessPoolExecutor(
                max_workers=n_workers, mp_context=ctx,
                initializer=_parallel_worker_init,
                initargs=(_data_path, state._USE_LINEAR_SCALING,
                          state._SYRACUSE_MODE,
                          _gencsv, state._BATTERY_CSV_MODE,
                          state._LS_SCALE_ONLY, state._DIM_UNKNOWN_CONST,
                          sys.stdout is not sys.__stdout__)) as ex:
            # [v0.7-PAR] Sonde : des taches vides d'abord. Un script sans
            # garde __main__ fait terminer chaque worker pendant son demarrage
            # (_exit_if_reimported_by_worker) ; la sonde echoue alors en
            # BrokenProcessPool et on bascule en sequentiel. Sans elle, la
            # premiere ronde (iles entieres, plus que la capacite d'un tube)
            # restait coincee dans la file d'envoi : Python 3.9 attend ce fil
            # d'envoi pour fermer le pool, et le repli promis ne venait jamais.
            for _f in [ex.submit(_pool_probe) for _ in range(n_workers)]:
                _f.result()
            gen = 0
            _deadline = getattr(cfg, "DEADLINE", None)
            _pat = _Patience(getattr(cfg, "PATIENCE", 0))     # [v1.2-H1]
            while gen < cfg.GENERATIONS:
                # [v0.7-TIME] Echeance atteinte : pas de nouvelle ronde.
                if _deadline is not None and gen > 0 and time.time() >= _deadline:
                    TRACE.set("time_limit", "atteint (parallele, gen %d)" % gen)
                    state._TIME_LIMIT_HIT = True
                    print(f"[TIME] Time limit reached at generation {gen} — "
                          f"returning the best model so far.")
                    break
                # Round aligné sur les frontières de migration
                nxt_mig = ((gen // cfg.MIGRATION_INTERVAL) + 1) * cfg.MIGRATION_INTERVAL
                n_gens  = min(round_len, cfg.GENERATIONS - gen, max(1, nxt_mig - gen))

                futs = [ex.submit(_island_round_task,
                                  (isl, gen, n_gens,
                                   state.FRAGMENT_LIB, state.COGRAPH, state.SEQ_MEM,
                                   state.CURRENT_RESIDUAL_SIG,
                                   _worker_rng.getrandbits(31)))
                        for isl in islands]
                results = [f.result() for f in futs]   # lève si un worker meurt

                # ── Réintégration (uniquement après round 100% réussi) ──
                for i, (isl, best_local, frag, cog, seq) in enumerate(results):
                    islands[i] = isl
                    state.FRAGMENT_LIB.merge_from(frag)
                    state.COGRAPH.merge_from(cog)
                    state.SEQ_MEM.merge_from(seq)

                _gen_end = gen + n_gens - 1
                for i, (isl, best_local, _f, _c, _s) in enumerate(results):
                    if best_local is None:
                        continue
                    cand = wrap_linear_scaling(best_local, xs, ys)
                    _track_val_candidate(cand)        # [v21-VAL]
                    _track_small_candidate(cand, xs, ys)   # [1.4-S1]
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
                            _probe_y = np.zeros(state.PROBE_X.shape[0])
                            state.CURRENT_RESIDUAL_SIG = update_residual_sig(
                                global_best, state.PROBE_X, _probe_y)
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
                    _es_thr = _early_stop_threshold(cfg, ys)
                    if _es_mse <= _es_thr:
                        print(f"\n{'═'*60}")
                        print(f"  [SUCCESS] Precision target reached at GEN {gen:04d}!")
                        print(f"  MSE (hold-out si actif) = {_es_mse:.2e}  ≤  seuil = {_es_thr:.2e}")
                        print(f"  Early stop — remaining generations saved.")
                        print(f"{'═'*60}\n")
                        break
                    # [v1.2-H1] Arrêt sur patience, compté à la fin de chaque
                    # round sur sa dernière génération (gen - 1).
                    if _pat.spent(_es_mse, gen - 1):
                        TRACE.set("patience", "arret (parallele, gen %d)" % (gen - 1))
                        print(f"[PATIENCE] No gain of 1 % in {_pat.p} generations — "
                              f"stop at generation {gen - 1}.")
                        break

                if gen > 0 and gen % cfg.MIGRATION_INTERVAL == 0:
                    migrate(islands)

        return global_best, global_score, True

    except Exception as _par_err:
        print(f"[v20-PAR] ⚠ Parallel unavailable ({type(_par_err).__name__}: "
              f"{_par_err}) — automatic sequential fallback.")
        # [v0.7-PAR] Un pool BRISE (fils termines) ne se reparera pas au
        # prochain appel : on cesse d'essayer dans ce processus, et on dit
        # pourquoi, une fois, sur stderr.
        if type(_par_err).__name__ == "BrokenProcessPool":
            state._PARALLEL_BROKEN = True
            _warn_unguarded_main(_par_err)
        return global_best, global_score, False
    finally:
        if _data_path is not None:
            try:
                _os.remove(_data_path)
            except OSError:
                pass
        # [v0.7-PAR] Ne laisser aucune trace dans l'environnement de
        # l'utilisateur (ses propres sous-processus en heriteraient).
        for _k, _v in (("PYTHONHASHSEED", _prev_hash), (_POOL_CHILD_ENV, _prev_child)):
            if _v is None:
                _os.environ.pop(_k, None)
            else:
                _os.environ[_k] = _v
