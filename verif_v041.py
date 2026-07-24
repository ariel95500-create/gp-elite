"""Verificateur gp-elite v0.4.1 — un seul lancement, aucune reference a creer.

    python verif_v041.py

A lancer depuis la RACINE du depot (a cote de pyproject.toml), pour que le
dossier gp_elite/ local soit celui qui est teste.

Quatre controles :
  1. correctif LM       — plus d'overflow float64 dans l'optimiseur
  2. comportement defaut— une loi connue est retrouvee (mesure de REFERENCE)
  3. units=             — modele numeriquement juste ET dimensionnellement sain
  4. etancheite         — le fit du test 2, rejoue, doit redonner la MEME chose

L'ordre compte : le test 2 doit etre mesure AVANT tout fit avec units=,
sinon la fuite du test 4 se masque elle-meme.
"""
import os
import sys

# PYTHONHASHSEED doit etre pose AVANT le demarrage de l'interpreteur : on se
# relance une fois si besoin, sinon les fits ne sont pas reproductibles.
if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)

import numpy as np

RESULTS = []
REFERENCE = {}


def bandeau(n, titre):
    print("\n" + "=" * 64)
    print(f"TEST {n} — {titre}")
    print("=" * 64)


def verdict(n, ok, msg):
    RESULTS.append((n, ok))
    print(f"\n  >>> {'OK — ' if ok else 'ECHEC — '}{msg}")


def donnees():
    np.random.seed(0)
    X = np.random.uniform(1, 4, (80, 2))
    return X, 0.5 * X[:, 0] * X[:, 1] ** 2      # y = 1/2 * m * v^2


def r2_de(est, X, y):
    p = est.predict(X)
    return 1.0 - float(np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2))


# ---------------------------------------------------------------- test 1
def test_lm():
    bandeau(1, "CORRECTIF LM (garde anti-overflow)")
    import gp_elite.core as C
    present = "_LM_NUM_CLIP" in open(C.__file__, encoding="utf-8").read()
    print(f"  borne _LM_NUM_CLIP dans le fichier : {'oui' if present else 'NON'}")

    N = C.Node
    np.random.seed(0)
    X = np.column_stack([np.random.uniform(60, 95, 60)])
    y = np.random.uniform(0, 1, 60)
    t = N("*", N(3.0), N("X[0]"))
    for _ in range(6):
        t = N("cube", t)                      # chaine volontairement explosive
    try:
        with np.errstate(over="raise", invalid="raise",
                         divide="ignore", under="ignore"):
            C.optimize_constants_lm(t, X, y, C.Config())
        pas_overflow = True
        print("  chaine cube^6 dans le LM          : aucun overflow")
    except FloatingPointError as e:
        pas_overflow = False
        print(f"  chaine cube^6 dans le LM          : OVERFLOW ({e})")
    verdict(1, present and pas_overflow,
            "le LM encaisse les arbres explosifs." if present and pas_overflow
            else "le correctif LM est absent ou inoperant.")


# ---------------------------------------------------------------- test 2
def test_units():
    bandeau(3, "units= (justesse numerique + validite dimensionnelle)")
    from gp_elite import GPEliteRegressor
    from gp_elite import dimensions as GD
    X, y = donnees()
    est = GPEliteRegressor(operators="physical", generations=10, speed="fast",
                           restarts=1, random_state=1,
                           units=["kg", "m/s"], target_units="J")
    est.fit(X, y)
    r2 = r2_de(est, X, y)
    rows = GD.audit_pareto(est.model_,
                           {0: {"kg": 1}, 1: {"m": 1, "s": -1}},
                           {"kg": 1, "m": 2, "s": -2}, verbose=False)
    sains = sum(1 for r in rows if r["ok"])
    print(f"  R2                 : {r2:.6f}   (bug v0.4 : environ -1.89)")
    print(f"  equation trouvee   : {est.sympy()[:58]}")
    print(f"  audit front Pareto : {sains}/{len(rows)} formes saines")
    ok = (r2 > 0.99) and (sains == len(rows))
    verdict(3, ok,
            "units= rend un modele juste ET dimensionnellement sain."
            if ok else "units= rend encore un modele numeriquement faux.")


# ---------------------------------------------------------------- test 3
def test_etancheite():
    bandeau(4, "ETANCHEITE (le fit du test 2, rejoue apres un fit units=)")
    if "equation" not in REFERENCE:
        print("  reference du test 2 indisponible.")
        verdict(4, False, "impossible de conclure.")
        return
    est, X, y = _fit_reference()
    r2 = r2_de(est, X, y)
    meme_eq = (est.sympy() == REFERENCE["equation"])
    print(f"  R2 au test 2               : {REFERENCE['r2']:.6f}")
    print(f"  R2 apres un fit units=     : {r2:.6f}   "
          f"(bug v0.4 : s'effondrait)")
    print(f"  equation identique         : {meme_eq}")
    verdict(4, meme_eq and abs(r2 - REFERENCE["r2"]) < 1e-9,
            "aucune fuite : le mode dimensionnel est etanche."
            if meme_eq else
            "le mode dimensionnel deborde encore sur les fits suivants.")


# ---------------------------------------------------------------- test 4
def _fit_reference():
    """Le fit temoin, sans units=. Rejoue a l'identique au test 4."""
    from gp_elite import GPEliteRegressor
    np.random.seed(1)
    X = np.random.uniform(1, 5, (150, 2))
    y = 2.0 + 3.0 * np.sqrt(X[:, 0]) - 0.5 * X[:, 1]
    est = GPEliteRegressor(operators="physical", generations=25, speed="fast",
                           restarts=1, random_state=0)
    est.fit(X, y)
    return est, X, y


def test_defaut():
    bandeau(2, "COMPORTEMENT PAR DEFAUT (loi connue, sans units=)")
    est, X, y = _fit_reference()
    r2 = r2_de(est, X, y)
    REFERENCE["equation"] = est.sympy()
    REFERENCE["r2"] = r2
    print(f"  cible    : 2 + 3*sqrt(a) - 0.5*b")
    print(f"  trouvee  : {est.sympy()[:58]}")
    print(f"  R2       : {r2:.6f}")
    verdict(2, r2 > 0.99,
            "le moteur par defaut est intact."
            if r2 > 0.99 else "le moteur par defaut ne retrouve plus la loi.")


def main():
    import gp_elite
    print(f"gp_elite charge depuis : {os.path.dirname(gp_elite.__file__)}")
    print(f"__version__ declare    : {gp_elite.__version__}")

    for fn in (test_lm, test_defaut, test_units, test_etancheite):
        try:
            fn()
        except Exception as e:
            n = len(RESULTS) + 1
            print(f"\n  ERREUR : {type(e).__name__}: {e}")
            verdict(n, False, "le test n'a pas pu aller au bout.")

    rates = [n for n, ok in RESULTS if not ok]
    print("\n" + "=" * 64)
    if rates:
        print(f"BILAN : {len(rates)} test(s) en echec -> {rates}. Ne pas publier.")
    else:
        print("BILAN : les 4 tests passent. La v0.4.1 est bonne a publier.")
    print("=" * 64)


if __name__ == "__main__":
    main()
