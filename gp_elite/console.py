"""The console: the printed result, the decoy report, the plot, run,
the benchmark of the console and the interactive menu.

Part of gp_elite/core.py until 1.4.0, moved without change in 1.5.
"""
from __future__ import annotations

import math
import random
import numpy as np
import time
import csv
import gc
import os
from typing import Optional, List, Tuple, Dict, Any

from . import state
from .config import (Config, make_cfg, make_cfg_nd)
from .tree import (Node, to_string, tree_depth, tree_size)
from .simplification import (simplify)
from .evaluation import (evaluate, evaluate_vector)
from .datasets import (DECOY_FEATURES, SYRACUSE_N_FEATURES,
                       _collatz_flight_time, _v2, generate_syracuse_dataset)
from .scoring import (_pure_mse, _scale_tree, _target_scale, fitness, raw_mse)
from .memory import (warm_transfer)
from .search import (evolve)
from .data import (ND_PROBLEMS, PROBLEMS, _IdentityScaler, _ShiftFreeScaler,
                   load_custom_csv, load_generic_csv)

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
