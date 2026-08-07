# -*- coding: utf-8 -*-
"""
VALIDATION DU PATCH robust (bug n°1) — à lancer APRÈS application du patch
==========================================================================
Rejoue les 5 cas de validation du dossier + le duel outlier, avec verdicts
automatiques. Tout doit être VERT sauf le duel (jaune attendu tant que le
bug n°2 — polissage LM en MSE — n'est pas traité).

  set PYTHONHASHSEED=0 && python benchmarks\\validate_robust_fix.py
"""
import os, sys, io, contextlib
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.isdir(os.path.join(_ROOT, "gp_elite")):
    sys.path.insert(0, _ROOT)
import gp_elite
from gp_elite import symbolic_regression
import numpy as np

print(f"gp_elite {getattr(gp_elite,'__version__','?')}  <-  {os.path.abspath(gp_elite.__file__)}")
R = np.random.RandomState
def U(r, lo, hi, n): return r.uniform(lo, hi, n)

def fit(X, y, names, rob=True):
    with contextlib.redirect_stdout(io.StringIO()):
        r = symbolic_regression(X[:350], y[:350], feature_names=names,
                                operators="physical", normalize="none",
                                generations=30, speed="fast",
                                validation_split=0.15, seed=0, restarts=4,
                                robust=rob)
    return r

def best_vs(r, X, y):
    v = np.var(y[350:]); b = float(np.mean((r.predict(X[350:]) - y[350:])**2)/v)
    bs, be = r.size, r.expression
    for e in (r.pareto or []):
        ec = float(np.mean((e.predict(X[350:]) - y[350:])**2)/v)
        if ec < b: b, bs, be = ec, e.size, e.expression
    return b, bs, be

ok_all = True
def check(tag, cond, detail):
    global ok_all
    mark = "OK " if cond else "ÉCHEC"
    if not cond: ok_all = False
    print(f"[{mark}] {tag:<38} {detail}")

# 1. I.8.14 propre — avant patch : constante
rng = R(1006)
X = np.c_[U(rng,1,5,500),U(rng,1,5,500),U(rng,1,5,500),U(rng,1,5,500)]
y = np.sqrt((X[:,1]-X[:,0])**2 + (X[:,3]-X[:,2])**2)
b,s,e = best_vs(fit(X,y,["v0","v1","v2","v3"]), X, y)
check("1. I.8.14 propre récupérée", b < 1e-9, f"err={b:.1e} size={s}")

# 2. non-régression I.12.1
rng = R(1000)
X2 = np.c_[U(rng,1,5,500),U(rng,1,5,500)]; y2 = X2[:,0]*X2[:,1]
b,s,e = best_vs(fit(X2,y2,["v0","v1"]), X2, y2)
check("2. I.12.1 propre inchangée", b < 1e-9, f"err={b:.1e} size={s}")

# 3. invariance d'échelle (le test qui échouait de façon prédictive)
b,s,e = best_vs(fit(X2, y2/10, ["v0","v1"]), X2, y2/10)
check("3. I.12.1 ÷10 : invariance d'échelle", b < 1e-9, f"err={b:.1e} size={s}")

# 4. I.12.2 propre — avant patch : droite sur v3
rng = R(1011)
X4 = np.c_[U(rng,1,5,500),U(rng,1,5,500),U(rng,1,3,500),U(rng,1,3,500)]
y4 = X4[:,0]*X4[:,1]/(4*np.pi*X4[:,2]*X4[:,3]**2)
b,s,e = best_vs(fit(X4,y4,["v0","v1","v2","v3"]), X4, y4)
check("4. I.12.2 propre récupérée", b < 1e-9, f"err={b:.1e} size={s}")

# 5. I.16.6 propre — avant patch : droite triviale err~0.5 ; après : vraie
#    recherche (MISS attendu, l'équation est insoluble même en mode défaut)
rng = R(1007)
X5 = np.c_[U(rng,1,2,500),U(rng,1,2,500),U(rng,3,10,500)]
y5 = (X5[:,0]+X5[:,1])/(1+X5[:,0]*X5[:,1]/X5[:,2]**2)
b,s,e = best_vs(fit(X5,y5,["v0","v1","v2"]), X5, y5)
check("5. I.16.6 propre : plus de droite triviale", b < 0.2, f"err={b:.1e} size={s}")

# 6. duel outlier 10% sur I.8.14 : structure retrouvée par le bras robust.
#    (Les CONSTANTES restent biaisées tant que le bug n°2 n'est pas traité :
#    on ne teste ici que la structure, err < 0.2 contre ~1.0 pour l'ancien
#    mode qui renvoyait une constante.)
nrng = R(777+6)
yn = y.copy(); k = 50
pos = nrng.choice(500, size=k, replace=False)
yn[pos] += nrng.choice([-1.,1.], size=k) * 10.0 * float(np.std(y))
b,s,e = best_vs(fit(X, yn, ["v0","v1","v2","v3"]), X, y)
check("6. outlier 10% : structure retrouvée", b < 0.2, f"err_vs_vérité={b:.1e} size={s}")

print()
print("TOUT EST VERT — patch validé." if ok_all else
      "AU MOINS UN ÉCHEC — ne pas committer ; comparer avec le dossier.")
