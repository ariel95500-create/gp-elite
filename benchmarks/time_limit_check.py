"""Tests du budget de temps (time_limit).

    PYTHONHASHSEED=0 python benchmarks/time_limit_check.py

Resultat 0.7.0 (conteneur Linux, 2 coeurs, benchmarks/results_0.7/time_limit_check.txt) :
15/16 ; 15 s de budget -> 17,3 s en sequentiel (le critere T + 1 generation + 1 s
est depasse de 0,4 s : le polissage et la selection finale suivent la derniere
generation), 16,5 s en parallele. D'un run a l'autre, 16,6 a 17,3 s en sequentiel.


Criteres fixes AVANT mesure :
  - duree reelle <= T + une generation + 1 s (sequentiel ET parallele)
  - un modele valide est toujours rendu (R2 fini)
  - time_limit_reached vrai ssi le budget a coupe la recherche
  - le drapeau ne fuit pas d'un ajustement au suivant
  - un budget invalide leve ValueError
"""
import sys, time
import numpy as np
from gp_elite import GPEliteRegressor as G
from gp_elite.api import symbolic_regression

def main():
    res = []
    def check(name, ok, detail=""):
        res.append(bool(ok))
        print("  [%s] %-44s %s" % ("PASS" if ok else "FAIL", name, detail), flush=True)

    r = np.random.RandomState(0)
    X = r.uniform(1, 4, (3000, 5)); y = X[:, 0] * X[:, 1] / X[:, 2] + 0.3 * X[:, 3]

    def gen_time(parallel):
        """Duree d'une generation, mesuree (pas supposee)."""
        t = time.time()
        symbolic_regression(X, y, generations=3, parallel=parallel, seed=0)
        return (time.time() - t) / 3.0

    for par in (False, True):
        lbl = "parallele" if par else "sequentiel"
        g = gen_time(par)
        T = 15.0
        t0 = time.time()
        m = symbolic_regression(X, y, generations=500, parallel=par, seed=0, time_limit=T)
        dt = time.time() - t0
        p = m.predict(X); r2 = 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)
        check("%s : arret a l'echeance" % lbl, dt <= T + g + 1.0,
              "T=%.0fs duree=%.1fs (1 gen = %.1fs)" % (T, dt, g))
        check("%s : modele valide rendu" % lbl, np.isfinite(r2), "R2=%.4f" % r2)
        check("%s : time_limit_reached = True" % lbl, m.time_limit_reached is True)

    # budget genereux : jamais atteint, resultat identique a l'absence de budget
    a = symbolic_regression(X[:300], y[:300], generations=8, parallel=False, seed=5)
    b = symbolic_regression(X[:300], y[:300], generations=8, parallel=False, seed=5, time_limit=3600)
    check("budget genereux : non atteint", b.time_limit_reached is False)
    check("budget genereux : resultat identique", a.expression == b.expression and a.size == b.size)

    # redemarrages : partage du budget
    t0 = time.time()
    m = symbolic_regression(X, y, generations=500, parallel=False, seed=0, restarts=3, time_limit=24)
    dt = time.time() - t0
    check("3 redemarrages dans 24 s", dt <= 24 + gen_time(False) + 2.0,
          "duree=%.1fs, lances=%d" % (dt, m.restarts_completed))
    check("3 redemarrages : tous lances", m.restarts_completed == 3)

    # pas de fuite du drapeau
    symbolic_regression(X, y, generations=500, parallel=False, seed=0, time_limit=4)
    c = symbolic_regression(X[:300], y[:300], generations=5, parallel=False, seed=1)
    check("drapeau non transmis au fit suivant", c.time_limit_reached is False)

    # arguments invalides
    for bad in (0, -5, float("nan"), float("inf")):
        try:
            symbolic_regression(X[:50], y[:50], generations=2, time_limit=bad)
            check("time_limit=%r rejete" % bad, False)
        except ValueError:
            check("time_limit=%r rejete" % bad, True)

    # estimateur sklearn
    e = G(generations=500, parallel=False, time_limit=6).fit(X, y)
    check("GPEliteRegressor : diagnostic expose", e.model_.time_limit_reached is True)

    n = sum(res); print("\nBILAN : %d/%d" % (n, len(res)))
    sys.exit(0 if n == len(res) else 1)


if __name__ == "__main__":
    main()
