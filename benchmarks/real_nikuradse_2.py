# -*- coding: utf-8 -*-
"""
NIKURADSE-2 — la formulation « collapse de Prandtl »
=====================================================
Confirmé par G. Kronberger (échange du 07/08/2026) :
  * nikuradse_1 : les mesures ORIGINALES de Nikuradse (2 variables)
  * nikuradse_2 : la COLLAPSE DE PRANDTL (1 variable) — c'est cette
    version qu'utilise la littérature (Kronberger et al., « The
    Inefficiency of Genetic Programming for Symbolic Regression » ;
    Guimerà et al., Bayesian machine scientist)

POURQUOI CE RUN
---------------
GP_ELITE a déjà traité nikuradse_1 (la version la PLUS difficile : le
moteur doit trouver seul la dépendance à la rugosité). Ce script traite
nikuradse_2 pour une raison précise : rendre nos chiffres DIRECTEMENT
COMPARABLES aux résultats publiés, puisque tout le monde travaille sur
cette formulation.

CE QUE LA COLLAPSE CONTIENT DÉJÀ
--------------------------------
La collapse encode l'intuition physique : quelqu'un a d'abord compris
comment combiner rugosité et Reynolds pour réduire le problème à une
courbe unique. Retrouver une loi sur nikuradse_2 est donc un exercice
PLUS FACILE que sur nikuradse_1 — c'est à dire et à écrire, sinon le
résultat serait survendu.

ATTENTION — ON NE CONNAÎT PAS ENCORE LES COLONNES
--------------------------------------------------
Contrairement à nikuradse_1, on n'a pas inspecté ce jeu. Le script
COMMENCE donc par une inspection et s'arrête là avec `--explore-only`.
Ne lancer la recherche qu'après avoir regardé ce que contiennent les
données. (Attendu d'après la littérature : x = log(v*·k/nu) et
y = lambda^(-1/2) - 2·log10(r/k), mais À VÉRIFIER.)

Lancement :
  python benchmarks\\real_nikuradse_2.py --explore-only      <- D'ABORD
  set PYTHONHASHSEED=0 && python benchmarks\\real_nikuradse_2.py
Options :
  --normalize none|auto   (défaut : choisi d'après le rapport d'échelle)
  --gens 30
"""
import os, sys, io, json, time, contextlib

import multiprocessing

# [FIX-SPAWN] Sous Windows, le multiprocessing de Python utilise `spawn` :
# chaque processus enfant RÉ-IMPORTE ce module. Sans cette garde, l'enfant
# ré-exécute tout le script (affichage dupliqué, processus qui se
# multiplient, temps de calcul faussés). On sort immédiatement si nous ne
# sommes pas le processus principal.
if multiprocessing.current_process().name != "MainProcess":
    import sys as _s; _s.exit(0)
multiprocessing.freeze_support()


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

EXPECTED_ENGINE = "0.6.0"
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.isdir(os.path.join(_ROOT, "gp_elite")):
    sys.path.insert(0, _ROOT)

import gp_elite
from gp_elite import symbolic_regression
import numpy as np
import pandas as pd

print(f"gp_elite {getattr(gp_elite,'__version__','?')}  <-  "
      f"{os.path.abspath(gp_elite.__file__)}")

DATASET = "nikuradse_2"
URL = (f"https://github.com/EpistasisLab/pmlb/raw/master/datasets/"
       f"{DATASET}/{DATASET}.tsv.gz")

print(f"\n=== téléchargement de {DATASET} ===")
try:
    df = pd.read_csv(URL, sep="\t", compression="gzip")
except Exception as exc:
    sys.exit(f"Téléchargement impossible : {exc}\n"
             f"Repli : ouvrir {URL} dans un navigateur, enregistrer le\n"
             f"fichier à côté du script, puis adapter la lecture.")

print(f"forme : {df.shape[0]} lignes x {df.shape[1]} colonnes")
print(f"colonnes : {list(df.columns)}")

target = df.columns[-1]
feats = list(df.columns[:-1])
X = df[feats].to_numpy(dtype=float)
y = df[target].to_numpy(dtype=float)

print(f"\ncible : '{target}'   entrées : {feats}")
print(f"\n{'colonne':<16}{'min':>14}{'max':>14}{'moyenne':>14}{'écart-type':>14}")
for i, c in enumerate(feats):
    v = X[:, i]
    print(f"{c:<16}{v.min():>14.4g}{v.max():>14.4g}{v.mean():>14.4g}{v.std():>14.4g}")
print(f"{target:<16}{y.min():>14.4g}{y.max():>14.4g}{y.mean():>14.4g}{y.std():>14.4g}")

# combien de valeurs distinctes par colonne ? (nikuradse_1 avait 6 rugosités
# discrètes : le même piège peut exister ici)
print(f"\nvaleurs distinctes :")
for c in list(df.columns):
    u = df[c].nunique()
    print(f"  {c:<14} {u:>5}" + ("   <- variable discrète ?" if u <= 12 else ""))

if X.shape[1] >= 2:
    sd = np.std(X, axis=0)
    ratio = float(sd.max() / max(sd.min(), 1e-30))
    print(f"\nrapport d'échelle entre colonnes : x{ratio:.1f}")
    norm = "auto" if ratio > 20 else "none"
else:
    print("\nune seule variable d'entrée : pas de rapport d'échelle")
    norm = "none"
print(f"normalisation retenue : '{norm}'"
      + ("  (sous 'auto' les expressions sont écrites en variables "
         "NORMALISÉES et leurs constantes ne se lisent pas physiquement)"
         if norm == "auto" else ""))

n_nan = int(np.isnan(X).sum() + np.isnan(y).sum())
print(f"valeurs manquantes : {n_nan}")
if n_nan:
    keep = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X, y = X[keep], y[keep]
    print(f"  -> {int((~keep).sum())} ligne(s) écartée(s), reste {len(y)}")

if "--explore-only" in sys.argv:
    print("\n(inspection seule — relancer sans --explore-only pour chercher)")
    sys.exit(0)

if "--normalize" in sys.argv:
    norm = sys.argv[sys.argv.index("--normalize") + 1]
    print(f"  -> forcé par --normalize : '{norm}'")
gens = 30
if "--gens" in sys.argv:
    gens = int(sys.argv[sys.argv.index("--gens") + 1])

# ── références ──────────────────────────────────────────────────────────────
rng = np.random.RandomState(0)
idx = rng.permutation(len(y)); ntr = int(0.7 * len(y))
tr, te = idx[:ntr], idx[ntr:]

def _fit_eval(basis, itr, ite):
    A = np.c_[np.ones(len(itr)), basis(X[itr])]
    c, *_ = np.linalg.lstsq(A, y[itr], rcond=None)
    p = np.c_[np.ones(len(ite)), basis(X[ite])] @ c
    return 1 - np.mean((p - y[ite])**2) / np.var(y[ite]), c

BRUT = lambda Z: Z
LOGX = lambda Z: np.c_[np.log10(np.abs(Z[:, 0]) + 1e-12)]

r2_lin, c_lin = _fit_eval(BRUT, tr, te)
r2_log, c_log = _fit_eval(LOGX, tr, te)
print(f"\n=== références (le minimum à battre) ===")
print(f"  linéaire        R2 test = {r2_lin:.4f}   "
      f"[{c_lin[0]:+.4f} {c_lin[1]:+.4f}*x]")
print(f"  affine en log10 R2 test = {r2_log:.4f}   "
      f"[{c_log[0]:+.4f} {c_log[1]:+.4f}*log10(x)]")
print("  (sur la collapse, la loi de Prandtl-von Karman devient une DROITE :")
print("   une référence linéaire déjà forte est le comportement ATTENDU.)")

# ── GP_ELITE ────────────────────────────────────────────────────────────────
print(f"\n=== GP_ELITE (normalize='{norm}', gens={gens}, restarts=4) ===")
t0 = time.time()
with contextlib.redirect_stdout(io.StringIO()):
    m = symbolic_regression(X[tr], y[tr], feature_names=feats,
                            operators="physical", normalize=norm,
                            generations=gens, speed="fast",
                            validation_split=0.15, seed=0, restarts=4)
dt = time.time() - t0

def r2(e):
    return 1 - np.mean((e.predict(X[te]) - y[te])**2) / np.var(y[te])

print(f"\ndurée : {dt:.0f} s")
rows, seen = [], set()
for e in list(m.pareto or []) + [m]:
    try:
        k = (int(e.size), round(r2(e), 6))
        if k in seen: continue
        seen.add(k); rows.append((int(e.size), r2(e), e.expression))
    except Exception:
        pass
rows.sort()
print(f"champion  R2 test = {r2(m):.4f}   taille {m.size}")
print(f"\nfront de Pareto :")
for s, r, ex in rows:
    fl = "  <- bat les deux références" if r > max(r2_lin, r2_log) else ""
    print(f"  taille {s:>3}  R2={r:>8.4f}   {ex[:70]}{fl}")

best = max(rows, key=lambda t: t[1]) if rows else None
print("\n--- lecture ---")
if best:
    ref = max(r2_lin, r2_log)
    if best[1] > ref:
        print(f"GP_ELITE dépasse la meilleure référence simple "
              f"({best[1]:.4f} > {ref:.4f}).")
        print("À vérifier : l'expression gagnante est-elle COMPACTE ? Sur une")
        print("collapse, un gros modèle qui bat une droite ne prouve rien —")
        print("il peut simplement suivre la dispersion résiduelle.")
    else:
        print(f"GP_ELITE ne dépasse pas la meilleure référence simple "
              f"({best[1]:.4f} vs {ref:.4f}).")
        print("Sur une collapse, c'est un résultat ATTENDU et honnête : la")
        print("transformation a déjà fait le travail de découverte.")
print("\nRappel de cadrage : la collapse encode l'intuition physique en amont.")
print("Le résultat vraiment difficile reste celui de nikuradse_1, sur les")
print("mesures originales à deux variables.")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   f"real_nikuradse_2_{norm}.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(dict(dataset=DATASET, engine=gp_elite.__version__,
                   n=len(y), features=feats, target=str(target),
                   normalize=norm, generations=gens, seconds=round(dt, 1),
                   r2_linear=r2_lin, r2_log=r2_log,
                   champion=dict(size=int(m.size), r2=r2(m), expr=m.expression),
                   pareto=[dict(size=s, r2=r, expr=ex) for s, r, ex in rows]),
              fh, indent=1)
print(f"\ntélémétrie -> {out}")
