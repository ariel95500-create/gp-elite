# -*- coding: utf-8 -*-
"""
VALIDATION DU MODE normalize="smart"  — à lancer APRÈS application du patch
============================================================================
  A. sélection      — `smart` choisit-il le bon scaler ? (instantané)
  B. non-régression — `auto`/`none`/`divmax`/`minmax`/`standard` strictement
                      inchangés ? PARTIE CRITIQUE : le bras `auto` est gelé.
  C. banc Feynman   — `smart` reproduit-il le bras `none` (14/15) ? (~8 min)

  set PYTHONHASHSEED=0 && python benchmarks\\validate_smart_normalize.py
  options :  --skip-c   ne lance que A et B (instantané)

NOTE TECHNIQUE — pourquoi tout est dans main() sous une garde :
sous Windows, le multiprocessing de Python utilise `spawn` : chaque
processus enfant RÉ-IMPORTE le module principal. Sans la garde
`if __name__ == "__main__"`, l'enfant ré-exécute tout le script depuis le
haut — l'affichage se duplique et les processus se multiplient. Tous les
scripts de benchmarks/ qui appellent symbolic_regression DOIVENT avoir
cette garde. (Le mode robust=True installe une perte personnalisée, qui
désactive le parallélisme : ces scripts-là ne montrent pas le symptôme,
mais la garde reste obligatoire.)
"""
import os, sys, io, contextlib, multiprocessing

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.isdir(os.path.join(_ROOT, "gp_elite")):
    sys.path.insert(0, _ROOT)

import gp_elite
from gp_elite import core, symbolic_regression
import numpy as np

ok_all = True


def check(tag, cond, detail=""):
    global ok_all
    if not cond:
        ok_all = False
    print(f"[{'OK ' if cond else 'ÉCHEC'}] {tag:<46} {detail}")


def U(rng, lo, hi, n):
    return rng.uniform(lo, hi, n)


Rs = np.random.RandomState

PROBS = [
 (0, "I.12.1", 2, lambda r, n: np.c_[U(r,1,5,n), U(r,1,5,n)],
  lambda X: X[:,0]*X[:,1], "physical"),
 (1, "I.12.5", 2, lambda r, n: np.c_[U(r,1,5,n), U(r,1,5,n)],
  lambda X: X[:,0]*X[:,1], "physical"),
 (2, "I.14.4", 2, lambda r, n: np.c_[U(r,1,5,n), U(r,1,5,n)],
  lambda X: 0.5*X[:,0]*X[:,1]**2, "physical"),
 (3, "I.39.1", 2, lambda r, n: np.c_[U(r,1,5,n), U(r,1,5,n)],
  lambda X: 1.5*X[:,0]*X[:,1], "physical"),
 (4, "II.3.24", 2, lambda r, n: np.c_[U(r,1,5,n), U(r,1,3,n)],
  lambda X: X[:,0]/(4*np.pi*X[:,1]**2), "physical"),
 (5, "I.6.20a", 1, lambda r, n: np.c_[U(r,-3,3,n)],
  lambda X: np.exp(-X[:,0]**2/2)/np.sqrt(2*np.pi), "physical"),
 (6, "I.8.14", 4, lambda r, n: np.c_[U(r,1,5,n), U(r,1,5,n), U(r,1,5,n), U(r,1,5,n)],
  lambda X: np.sqrt((X[:,1]-X[:,0])**2 + (X[:,3]-X[:,2])**2), "physical"),
 (7, "I.16.6", 3, lambda r, n: np.c_[U(r,1,2,n), U(r,1,2,n), U(r,3,10,n)],
  lambda X: (X[:,0]+X[:,1])/(1+X[:,0]*X[:,1]/X[:,2]**2), "physical"),
 (8, "I.27.6", 3, lambda r, n: np.c_[U(r,1,5,n), U(r,1,5,n), U(r,1,2,n)],
  lambda X: 1.0/(1.0/X[:,0] + X[:,2]/X[:,1]), "physical"),
 (9, "I.34.8", 4, lambda r, n: np.c_[U(r,1,5,n), U(r,1,5,n), U(r,1,5,n), U(r,1,5,n)],
  lambda X: X[:,0]*X[:,1]*X[:,2]/X[:,3], "physical"),
 (10, "I.43.16", 4, lambda r, n: np.c_[U(r,1,5,n), U(r,1,5,n), U(r,1,5,n), U(r,1,5,n)],
  lambda X: X[:,0]*X[:,1]*X[:,2]/X[:,3], "physical"),
 (11, "I.12.2", 4, lambda r, n: np.c_[U(r,1,5,n), U(r,1,5,n), U(r,1,3,n), U(r,1,3,n)],
  lambda X: X[:,0]*X[:,1]/(4*np.pi*X[:,2]*X[:,3]**2), "physical"),
 (12, "II.15.4", 3, lambda r, n: np.c_[U(r,1,5,n), U(r,1,5,n), U(r,0,6.28,n)],
  lambda X: -X[:,0]*X[:,1]*np.cos(X[:,2]), "trig"),
 (13, "I.18.12", 3, lambda r, n: np.c_[U(r,1,5,n), U(r,1,5,n), U(r,0,3.14,n)],
  lambda X: X[:,0]*X[:,1]*np.sin(X[:,2]), "trig"),
 (14, "III.15.12", 3, lambda r, n: np.c_[U(r,1,5,n), U(r,0.5,2,n), U(r,0.5,2,n)],
  lambda X: 2*X[:,0]*(1-np.cos(X[:,1]*X[:,2])), "trig"),
]
REF_NONE = {p[1]: "EXACT" for p in PROBS}
REF_NONE["I.16.6"] = "MISS"


def main():
    print(f"gp_elite {getattr(gp_elite, '__version__', '?')}  <-  "
          f"{os.path.abspath(gp_elite.__file__)}")
    if not hasattr(core, "SCALE_RATIO_THRESHOLD"):
        sys.exit("!! ARRÊT : patch non appliqué (SCALE_RATIO_THRESHOLD "
                 "absent de core.py).")
    print(f"seuil de bascule : {core.SCALE_RATIO_THRESHOLD}")

    R = Rs(0)
    CASES = [
     ("Feynman I.12.1 (2 col., 1-5)", np.c_[R.uniform(1,5,200), R.uniform(1,5,200)], "none"),
     ("Feynman I.16.6 (u, v, c)", np.c_[R.uniform(1,2,200), R.uniform(1,2,200),
                                        R.uniform(3,10,200)], "none"),
     ("une seule colonne", R.uniform(1,5,200).reshape(-1,1), "none"),
     ("colonne constante + normale", np.c_[np.ones(200), R.uniform(1,5,200)], "none"),
     ("toutes colonnes constantes", np.c_[np.ones(200), np.full(200,3.0)], "none"),
     ("négatifs, échelles comparables", np.c_[R.uniform(-3,3,200), R.uniform(-2,2,200)], "none"),
     ("disparité x100", np.c_[R.uniform(1,5,200), R.uniform(1,5,200)*100], "scale"),
     ("disparité x1e6", np.c_[R.uniform(1,5,200), R.uniform(1,5,200)*1e6], "scale"),
     ("Nikuradse-1 (r_k, log_Re)", np.c_[R.uniform(15,507,200), R.uniform(3.6,6,200)], "scale"),
    ]

    print("\n=== A. `smart` choisit-il le bon scaler ? ===")
    for nm, X, attendu in CASES:
        ratio = core._scale_ratio(X)
        sc, desc = core._choose_scaler(X, "smart", (-2.0, 2.0))
        ident = isinstance(sc, core._IdentityScaler)
        bon = ident if attendu == "none" else (not ident)
        check(nm, bon, f"ratio={ratio:>10.1f}  ->  "
                       f"{'identité' if ident else desc[:24]}")

    print("\n=== B. non-régression des modes existants (bras `auto` GELÉ) ===")
    ATTENDU = {"none": "_IdentityScaler", "divmax": "_ShiftFreeScaler",
               "minmax": "MinMaxScaler", "standard": "StandardScaler"}
    for nm, X, _ in CASES[:2] + CASES[6:8]:
        for mode, exp_type in ATTENDU.items():
            sc, _d = core._choose_scaler(X, mode, (-2.0, 2.0))
            check(f"{mode:<9} sur {nm[:26]}", type(sc).__name__ == exp_type,
                  type(sc).__name__)
        sc, _d = core._choose_scaler(X, "auto", (-2.0, 2.0))
        att = "_ShiftFreeScaler" if bool(np.all(X > 0)) else "MinMaxScaler"
        check(f"{'auto':<9} sur {nm[:26]}", type(sc).__name__ == att,
              f"{type(sc).__name__} (tout positif : {bool(np.all(X>0))})")
    sc, _d = core._choose_scaler(CASES[0][1], "auto", (-2.0, 2.0))
    check("auto ne renvoie jamais l'identité",
          not isinstance(sc, core._IdentityScaler), type(sc).__name__)

    if "--skip-c" in sys.argv:
        print("\n" + ("TOUT EST VERT (A+B)." if ok_all else "AU MOINS UN ÉCHEC."))
        return 0 if ok_all else 1

    print("\n=== C. banc Feynman sous `smart` (~8 min) ===")
    print("    attendu : identique au bras `none` — 14/15, I.16.6 seul MISS")
    n_ex = 0
    ecarts = []
    for idx, name, nv, samp, f, pool in PROBS:
        rng = Rs(1000 + idx)
        X = samp(rng, 200)
        y = f(X)
        perm = rng.permutation(200)
        tr, te = perm[:140], perm[140:]
        ratio = core._scale_ratio(X)
        with contextlib.redirect_stdout(io.StringIO()):
            r = symbolic_regression(X[tr], y[tr],
                                    feature_names=[f"v{k}" for k in range(nv)],
                                    operators=pool, normalize="smart",
                                    generations=30, speed="fast",
                                    validation_split=0.15, seed=0, restarts=4)
        v = float(np.var(y[te]))
        pb = min(float(np.mean((e.predict(X[te]) - y[te])**2)/v)
                 for e in list(r.pareto or []) + [r])
        st = "EXACT" if pb < 1e-9 else ("NEAR" if pb < 1e-3 else "MISS")
        if st == "EXACT":
            n_ex += 1
        same = (st == REF_NONE[name])
        if not same:
            ecarts.append(f"{name} ({REF_NONE[name]} -> {st})")
        print(f"  {name:<11} ratio={ratio:>5.1f}  {st:<6} pb={pb:.1e}"
              f"   {'' if same else '  <- diffère du bras none'}")
        sys.stdout.flush()

    print(f"\n  résultat : {n_ex}/15 exactes")
    check("smart reproduit le bras none (>=13/15)", n_ex >= 13, f"{n_ex}/15")
    check("aucun écart de statut vs bras none", not ecarts,
          ", ".join(ecarts) if ecarts else "aucun")
    print("\n" + ("TOUT EST VERT — mode `smart` validé, bras `auto` intact."
                  if ok_all else
                  "AU MOINS UN ÉCHEC — ne pas committer."))
    return 0 if ok_all else 1


if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
