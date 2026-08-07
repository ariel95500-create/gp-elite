# -*- coding: utf-8 -*-
"""
PREMIER JEU DE DONNÉES RÉEL — Nikuradse (frottement en conduite rugueuse, 1933)
================================================================================
Pourquoi ce jeu :
  * MESURES RÉELLES (Nikuradse, 1933), pas de la donnée synthétique. Tous les
    bancs de GP_ELITE à ce jour sont synthétiques ; le README revendique
    « experimental datasets ». Ce script comble l'écart.
  * PROBLÈME OUVERT : la dépendance fonctionnelle du frottement au nombre de
    Reynolds et à la rugosité relative n'est toujours pas établie (Reichardt
    et al.). Ce n'est pas un exercice de manuel.
  * COMPARAISONS PUBLIÉES : Bayesian machine scientist, ESR/GP, LLM-SR ont
    tous été évalués dessus.
  * ~360 points, 2 variables : dans l'enveloppe mesurée du moteur.

Note : les variables sont déjà ADIMENSIONNELLES. La contrainte dimensionnelle
(units=) n'a donc rien à contraindre ici — ce script teste le moteur général.

ÉTAPE 1 (obligatoire) : on regarde les données AVANT de chercher quoi que ce
soit. Colonnes, plages, distribution. On ne lance pas un moteur sur des données
qu'on n'a pas regardées.

Lancement :
  python -m pip install pandas
  set PYTHONHASHSEED=0 && python benchmarks\\real_nikuradse.py
Options :
  --explore-only   s'arrête après l'inspection des données
  --gens 40          budget de générations (défaut 30)
  --normalize none   force le mode de normalisation. IMPORTANT : sous 'auto'
                     les expressions sont en variables normalisées et leurs
                     constantes ne sont pas physiquement lisibles.
"""
import os, sys, io, json, time, contextlib

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

print(f"gp_elite {getattr(gp_elite,'__version__','?')}  <-  "
      f"{os.path.abspath(gp_elite.__file__)}")

# ── 1. données ──────────────────────────────────────────────────────────────
import pandas as pd

DATASET = "nikuradse_1"
# nikuradse_1 a été ajouté au dépôt PMLB APRÈS la dernière release PyPI
# (1.0.1.post3) : fetch_data() ne le connaît pas et lève
# "Dataset not found in PMLB". On télécharge donc directement depuis la
# branche master, et fetch_data ne sert que de secours.
URL = (f"https://github.com/EpistasisLab/pmlb/raw/master/datasets/"
       f"{DATASET}/{DATASET}.tsv.gz")

print(f"\n=== téléchargement de {DATASET} ===")
df = None
try:
    df = pd.read_csv(URL, sep="\t", compression="gzip")
    print(f"  source : dépôt PMLB (master)")
except Exception as exc:
    print(f"  téléchargement direct impossible ({type(exc).__name__}: {exc})")
    try:
        from pmlb import fetch_data
        df = fetch_data(DATASET)
        print("  source : paquet pmlb")
    except Exception as exc2:
        sys.exit(f"Impossible de récupérer les données : {exc2}\n"
                 f"Solution de repli : ouvrir {URL} dans un navigateur,\n"
                 f"enregistrer le fichier à côté du script, puis relancer.")
print(f"forme : {df.shape[0]} lignes x {df.shape[1]} colonnes")
print(f"colonnes : {list(df.columns)}")

target = df.columns[-1]
feats  = list(df.columns[:-1])
X = df[feats].to_numpy(dtype=float)
y = df[target].to_numpy(dtype=float)

print(f"\ncible : '{target}'   entrées : {feats}")
print(f"\n{'colonne':<16}{'min':>14}{'max':>14}{'moyenne':>14}{'écart-type':>14}")
for i, c in enumerate(feats):
    v = X[:, i]
    print(f"{c:<16}{v.min():>14.4g}{v.max():>14.4g}{v.mean():>14.4g}{v.std():>14.4g}")
print(f"{target:<16}{y.min():>14.4g}{y.max():>14.4g}{y.mean():>14.4g}{y.std():>14.4g}")

ratio = max(X[:, i].std() for i in range(X.shape[1])) / \
        max(1e-30, min(X[:, i].std() for i in range(X.shape[1])))
print(f"\nrapport d'échelle entre colonnes : x{ratio:.1f}")
print("  -> normalize='auto' (défaut) est indiqué" if ratio > 20 else
      "  -> colonnes comparables : normalize='none' est indiqué")
norm = "auto" if ratio > 20 else "none"
if "--normalize" in sys.argv:
    norm = sys.argv[sys.argv.index("--normalize") + 1]
    print(f"  -> forcé par --normalize : '{norm}'")
if norm == "auto":
    print("  ATTENTION : sous normalize='auto', les expressions renvoyées sont")
    print("  écrites en variables NORMALISÉES. Leurs constantes ne se lisent pas")
    print("  physiquement. Pour une expression interprétable en unités réelles,")
    print("  relancer avec  --normalize none  et comparer les deux.")

n_nan = int(np.isnan(X).sum() + np.isnan(y).sum())
print(f"valeurs manquantes : {n_nan}")
if n_nan:
    keep = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X, y = X[keep], y[keep]
    print(f"  -> {int((~keep).sum())} ligne(s) écartée(s), reste {len(y)}")

if "--explore-only" in sys.argv:
    sys.exit(0)

# ── 2. référence : que fait une régression linéaire toute simple ? ──────────
# Sans point de comparaison, un R2 ne veut rien dire. On mesure d'abord le
# résultat trivial que GP_ELITE doit battre pour être utile.
rng = np.random.RandomState(0)
idx = rng.permutation(len(y))
ntr = int(0.7 * len(y))
tr, te = idx[:ntr], idx[ntr:]

def _fit_eval(basis, itr, ite):
    """Ajuste un modèle linéaire sur une base de fonctions, renvoie le R2."""
    A = np.c_[np.ones(len(itr)), basis(X[itr])]
    c, *_ = np.linalg.lstsq(A, y[itr], rcond=None)
    p = np.c_[np.ones(len(ite)), basis(X[ite])] @ c
    return 1 - np.mean((p - y[ite])**2) / np.var(y[ite]), c

BRUT = lambda Z: Z
# Référence PHYSIQUE : la famille log de Prandtl-von Karman,
#   lambda^(-1/2) = 2*log10(r/k) + 1.74
# soit, dans l'espace de la cible, une forme affine en log10(r/k) (et en
# log_Re pour couvrir le régime transitionnel). Elle généralise PAR
# CONSTRUCTION à une rugosité non vue : c'est la vraie barre à franchir.
LOGL = lambda Z: np.c_[np.log10(np.abs(Z[:, 0]) + 1e-12), Z[:, 1]]

# ── référence PHYSIQUE EXACTE, zéro paramètre ajusté ────────────────────────
# Prandtl-von Karman, régime pleinement rugueux :
#     lambda^(-1/2) = 2*log10(r/k) + 1.74
# La cible de ce jeu est log10(100*lambda), donc :
#     target = 2 - 2*log10(2*log10(r/k) + 1.74)
# Aucun coefficient n'est ajusté sur les données : c'est la théorie brute.
def pvk(Z):
    return 2.0 - 2.0 * np.log10(2.0 * np.log10(np.abs(Z[:, 0]) + 1e-12) + 1.74)

def _r2(pred, yy):
    return 1 - np.mean((pred - yy) ** 2) / np.var(yy)

r2_pvk_all = _r2(pvk(X), y)
print(f"\n=== vérification du repère : la théorie décrit-elle ces données ? ===")
print(f"  Prandtl-von Karman EXACTE (0 paramètre) sur les 362 pts : "
      f"R2 = {r2_pvk_all:.4f}")
if r2_pvk_all < 0.5:
    print("  ATTENTION : la théorie ne colle pas. L'hypothèse "
          "target = log10(100*lambda)")
    print("  est probablement fausse -> les comparaisons ci-dessous n'ont "
          "pas de sens.")

r2_lin, _ = _fit_eval(BRUT, tr, te)
r2_log, c_log = _fit_eval(LOGL, tr, te)
r2_pvk = _r2(pvk(X[te]), y[te])
print(f"\n=== références (ce que GP_ELITE doit battre) ===")
print(f"  linéaire brute                    R2 test = {r2_lin:.4f}")
print(f"  log simple ajustée (3 paramètres) R2 test = {r2_log:.4f}"
      f"   [mauvaise famille : la loi est un log DE log]")
print(f"  Prandtl-von Karman EXACTE (0 p.)  R2 test = {r2_pvk:.4f}"
      f"   <- LA barre honnête")

# ── 3. GP_ELITE ─────────────────────────────────────────────────────────────
gens = 30
if "--gens" in sys.argv:
    gens = int(sys.argv[sys.argv.index("--gens") + 1])

print(f"\n=== GP_ELITE (normalize='{norm}', gens={gens}, restarts=4) ===")
print("    patience : quelques minutes.")
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
print(f"champion  R2 test = {r2(m):.4f}   taille {m.size}")
print(f"  {m.expression}")

print(f"\nfront de Pareto (le compromis taille / précision) :")
rows = []
for e in list(m.pareto or []) + [m]:
    try:
        rows.append((int(e.size), r2(e), e.expression))
    except Exception:
        pass
seen = set(); rows.sort()
for s, r, ex in rows:
    if (s, round(r, 6)) in seen:
        continue
    seen.add((s, round(r, 6)))
    flag = "  <- bat le linéaire" if r > r2_lin else ""
    print(f"  taille {s:>3}  R2={r:>8.4f}   {ex[:70]}{flag}")

best = max(rows, key=lambda t: t[1]) if rows else None
print("\n--- lecture ---")
if best and best[1] > r2_lin:
    print(f"GP_ELITE bat la référence linéaire : {best[1]:.4f} contre {r2_lin:.4f}.")
    print("À vérifier avant d'en tirer quoi que ce soit : l'expression est-elle")
    print("interprétable, ou juste un ajustement opaque ? Une petite expression")
    print("qui bat le linéaire est un résultat ; une grosse ne prouve rien.")
else:
    print("GP_ELITE ne bat pas une simple régression linéaire ici.")
    print("C'est un résultat, pas un échec : à documenter tel quel.")

# ── 4. LE test : une rugosité JAMAIS VUE ────────────────────────────────────
# r_k ne prend que 6 valeurs discrètes (15, 30.6, 60, 126, 252, 507) : le jeu
# est en réalité SIX COURBES. Avec un découpage aléatoire, les points de test
# sont interpolés à l'intérieur des mêmes courbes que l'entraînement -> un bon
# R2 peut s'obtenir en ajustant six courbes séparément, sans aucune loi.
# Ici on retire UNE rugosité entière de l'entraînement et on prédit dessus.
# C'est la différence entre interpoler et découvrir.
HOLD = 126.0                      # valeur intérieure : test équitable
col_rk = feats[0]
mask_out = np.isclose(X[:, 0], HOLD)
if mask_out.sum() > 0:
    Xin, yin = X[~mask_out], y[~mask_out]
    Xout, yout = X[mask_out], y[mask_out]
    print(f"\n=== généralisation : rugosité {col_rk}={HOLD} retirée de "
          f"l'entraînement ===")
    print(f"    entraînement {len(yin)} pts (5 rugosités) -> test {len(yout)} pts")

    itr = np.where(~mask_out)[0]; ite = np.where(mask_out)[0]
    r2_lin_out, _ = _fit_eval(BRUT, itr, ite)
    r2_log_out, c_lo = _fit_eval(LOGL, itr, ite)
    r2_pvk_out = _r2(pvk(Xout), yout)

    # Le R2 est TROMPEUR ici : une loi qui ne dépend que de r/k prédit une
    # CONSTANTE sur la courbe retirée, alors que la cible y varie avec le
    # Reynolds. Le R2 ne peut donc structurellement pas dépasser 0, même pour
    # un modèle parfait en niveau. On mesure donc le BIAIS DE NIVEAU :
    # l'écart entre le niveau prédit et le niveau réel de la courbe, rapporté
    # à la dispersion interne de cette courbe.
    sd_in = float(np.std(yout)); mean_out = float(np.mean(yout))
    def level(pred):
        p = np.asarray(pred, dtype=float)
        p = p if p.ndim else np.full(len(yout), float(p))
        return (float(np.mean(p)) - mean_out) / sd_in
    print(f"    dispersion interne de la courbe retirée : sigma = {sd_in:.4f}"
          f"  (niveau moyen {mean_out:.4f})")
    print(f"    biais de niveau, en sigma  (plus petit = mieux) :")
    print(f"      Prandtl-von Karman EXACTE : {level(pvk(Xout)):+.3f} sigma"
          f"   (R2 brut {r2_pvk_out:+.4f})")
    A3 = np.c_[np.ones(len(itr)), LOGL(X[itr])]
    c3, *_ = np.linalg.lstsq(A3, y[itr], rcond=None)
    print(f"      log simple ajustée        : "
          f"{level(np.c_[np.ones(len(ite)), LOGL(Xout)] @ c3):+.3f} sigma"
          f"   (R2 brut {r2_log_out:+.4f})")
    print(f"      linéaire brute            : "
          f"{level(np.c_[np.ones(len(ite)), Xout] @ np.linalg.lstsq(np.c_[np.ones(len(itr)), X[itr]], y[itr], rcond=None)[0]):+.3f} sigma"
          f"   (R2 brut {r2_lin_out:+.4f})")

    t1 = time.time()
    with contextlib.redirect_stdout(io.StringIO()):
        m2 = symbolic_regression(Xin, yin, feature_names=feats,
                                 operators="physical", normalize=norm,
                                 generations=gens, speed="fast",
                                 validation_split=0.15, seed=0, restarts=4)
    def r2o(e):
        return 1 - np.mean((e.predict(Xout) - yout)**2) / np.var(yout)
    rows2, seen2 = [], set()
    for e in list(m2.pareto or []) + [m2]:
        try:
            k = (int(e.size), round(r2o(e), 6))
            if k in seen2: continue
            seen2.add(k); rows2.append((int(e.size), r2o(e), e.expression))
        except Exception:
            pass
    rows2.sort()
    print(f"\n    GP_ELITE ({time.time()-t1:.0f} s) sur la rugosité inconnue :")
    biases = {}
    for e in list(m2.pareto or []) + [m2]:
        try:
            biases[(int(e.size), round(r2o(e), 6))] = level(e.predict(Xout))
        except Exception:
            pass
    for s_, r_, ex in rows2:
        b = biases.get((s_, round(r_, 6)))
        bt = f"biais {b:+.3f}s" if b is not None else "biais    ?  "
        fl = "  <- mieux que PvK" if (b is not None and
                                      abs(b) < abs(level(pvk(Xout)))) else ""
        print(f"      taille {s_:>3}  {bt}  R2={r_:>8.4f}   {ex[:48]}{fl}")
    best2 = max(rows2, key=lambda t: t[1]) if rows2 else None
    bmin = min(biases.values(), key=abs) if biases else None
    if bmin is not None:
        bp = level(pvk(Xout))
        print(f"\n    --- lecture de la généralisation ---")
        print(f"    meilleur biais GP_ELITE : {bmin:+.3f} sigma")
        print(f"    biais de la théorie     : {bp:+.3f} sigma")
        if abs(bmin) < abs(bp):
            print("    -> GP_ELITE prédit le niveau d'une rugosité jamais vue")
            print("       AUSSI BIEN OU MIEUX que la loi classique.")
        else:
            print("    -> la loi classique prédit mieux le niveau. Écart : "
                  f"{abs(bmin) - abs(bp):+.3f} sigma.")
    if best2 and best2[1] > r2_log_out:
        print(f"\n    -> BAT la loi log de référence sur une rugosité jamais vue "
              f"({best2[1]:.4f} > {r2_log_out:.4f}).")
        print("       C'est un résultat publiable.")
    elif best2 and best2[1] > 0:
        print(f"\n    -> généralise ({best2[1]:.4f} > 0) mais ne bat pas la loi log "
              f"({r2_log_out:.4f}).")
    else:
        print(f"\n    -> NE GÉNÉRALISE PAS : R2 <= 0 sur la rugosité inconnue.")
        print("       Le bon R2 de la phase 1 est de l'interpolation à l'intérieur")
        print("       des courbes apprises. À documenter tel quel.")
else:
    rows2, r2_lin_out, best2 = [], None, None

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"real_nikuradse_{norm}.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump(dict(dataset="nikuradse_1", engine=gp_elite.__version__,
                   n=len(y), features=feats, target=str(target),
                   normalize=norm, generations=gens, seconds=round(dt, 1),
                   r2_linear_baseline=r2_lin, r2_log_baseline=r2_log,
                   r2_pvk_exact_test=r2_pvk, r2_pvk_exact_all=r2_pvk_all,
                   champion=dict(size=int(m.size), r2=r2(m), expr=m.expression),
                   pareto=[dict(size=s, r2=r, expr=ex) for s, r, ex in rows],
                   holdout=dict(roughness=HOLD, r2_linear=r2_lin_out,
                                r2_log=r2_log_out, r2_pvk=r2_pvk_out,
                                sigma_in_curve=sd_in, mean_out=mean_out,
                                bias_pvk_sigma=level(pvk(Xout)),
                                bias_gp_sigma={f"{k[0]}": v
                                               for k, v in biases.items()},
                                pareto=[dict(size=a, r2=b, expr=c)
                                        for a, b, c in rows2])),
              fh, indent=1)
print(f"\ntélémétrie -> {out}")
