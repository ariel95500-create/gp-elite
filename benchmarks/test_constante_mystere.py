"""Suite de validation « constante mystere » — Hooke, Newton, gaz parfaits.

CE QUE CETTE FONCTIONNALITE DOIT FAIRE
--------------------------------------
En v0.4.1, les constantes ajustees sont traitees comme SANS DIMENSION
(convention AI Feynman). Consequence : une loi dont la constante porte des
unites est hors d'atteinte du mode contraint. Sur la loi de Hooke,

    F = k * x        [x] = m,  [F] = N = kg.m.s^-2,  donc [k] = kg.s^-2

aucune expression dimensionnellement valide n'existe si k doit etre sans
dimension — et la v0.4.1 leve d'ailleurs une ValueError explicite.

La fonctionnalite « constante mystere » leve cette limite : on autorise la
constante multiplicative de tete a PORTER une dimension, et le moteur DEDUIT
laquelle par homogeneite. C'est une extension directe de la mise a l'echelle
par l'origine introduite en 0.4.1 (b * f(x), sans decalage) : il suffit que b
cesse d'etre force sans dimension.

Interet scientifique : le moteur ne se contente plus de retrouver une forme,
il annonce les unites de la constante physique manquante. Sur les trois cas
ci-dessous la reponse est connue d'avance, donc verifiable sans ambiguite.

API SUPPOSEE (a ajuster si l'implementation retient d'autres noms)
------------------------------------------------------------------
    est = GPEliteRegressor(units=[...], target_units="...",
                           unknown_constant=True)
    est.fit(X, y)
    est.constant_units_    -> dict de dimensions, ex. {"kg": 1, "s": -2}
    est.constant_value_    -> float, la valeur ajustee

Le script fonctionne AVANT implementation : chaque cas non supporte est
rapporte comme "non implemente" au lieu de faire echouer le script.

    python test_constante_mystere.py
    python test_constante_mystere.py --gens 40      (budget plus large)
"""
import argparse
import os
import sys

if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)

import numpy as np

RESULTS = []


# ─────────────────────────────────────────────────────── les trois cas
def cas_hooke(n=150, seed=0):
    """F = k*x. 1 variable, lineaire. Le cas le plus depouille possible."""
    rng = np.random.RandomState(seed)
    x = rng.uniform(0.01, 0.10, n)
    k = 250.0                                    # N/m
    return (np.column_stack([x]), k * x,
            dict(nom="Hooke  F = k*x",
                 units=["m"], target_units="N",
                 attendu={"kg": 1, "s": -2},     # N/m
                 valeur=k, tol_valeur=0.02))


def cas_newton(n=250, seed=0):
    """F = G*m1*m2/r^2. 3 variables, produit et division."""
    rng = np.random.RandomState(seed)
    m1 = rng.uniform(1e3, 1e4, n)
    m2 = rng.uniform(1e3, 1e4, n)
    r = rng.uniform(1.0, 5.0, n)
    G = 6.674e-11
    return (np.column_stack([m1, m2, r]), G * m1 * m2 / r ** 2,
            dict(nom="Newton F = G*m1*m2/r^2",
                 units=["kg", "kg", "m"], target_units="N",
                 attendu={"m": 3, "kg": -1, "s": -2},
                 valeur=G, tol_valeur=0.02))


def cas_gaz(n=250, seed=0):
    """P = n*R*T/V. 4 variables. Le plus riche des trois."""
    rng = np.random.RandomState(seed)
    mol = rng.uniform(0.5, 5.0, n)
    T = rng.uniform(250.0, 400.0, n)
    V = rng.uniform(0.01, 0.10, n)
    R = 8.314462618
    return (np.column_stack([mol, T, V]), mol * R * T / V,
            dict(nom="Gaz    P = n*R*T/V",
                 units=["mol", "K", "m^3"], target_units="Pa",
                 attendu={"kg": 1, "m": 2, "s": -2, "mol": -1, "K": -1},
                 valeur=R, tol_valeur=0.02))


# ─────────────────────────────────────────────────────── utilitaires
def fmt_dim(d):
    if not d:
        return "[sans dimension]"
    num = " ".join(f"{k}^{v:g}" if v != 1 else k
                   for k, v in sorted(d.items()) if v > 0)
    den = " ".join(f"{k}^{-v:g}" if v != -1 else k
                   for k, v in sorted(d.items()) if v < 0)
    return f"[{num or '1'}" + (f" / {den}]" if den else "]")


def dims_egales(a, b, tol=1e-9):
    if a is None or b is None:
        return False
    cles = set(a) | set(b)
    return all(abs(float(a.get(k, 0)) - float(b.get(k, 0))) < tol for k in cles)


def r2(y, p):
    ss = float(np.sum((y - y.mean()) ** 2)) or 1e-30
    v = 1.0 - float(np.sum((y - p) ** 2) / ss)
    return v if np.isfinite(v) else -1e6


# ─────────────────────────────────────────────────────── un cas
def lancer(fabrique, gens, restarts):
    from gp_elite import GPEliteRegressor
    X, y, spec = fabrique()
    print("\n" + "=" * 66)
    print(f"  {spec['nom']}")
    print("=" * 66)
    print(f"  unites entrees   : {spec['units']}   cible : {spec['target_units']}")
    print(f"  constante attendue : {fmt_dim(spec['attendu'])}"
          f"   valeur {spec['valeur']:.6g}")

    try:
        est = GPEliteRegressor(operators="physical", generations=gens,
                               speed="fast", restarts=restarts, random_state=0,
                               units=spec["units"],
                               target_units=spec["target_units"],
                               unknown_constant=True)
    except TypeError as e:
        print(f"\n  >>> NON IMPLEMENTE : {e}")
        RESULTS.append((spec["nom"], None))
        return

    try:
        est.fit(X, y)
    except Exception as e:
        print(f"\n  >>> ECHEC au fit : {type(e).__name__}: {e}")
        RESULTS.append((spec["nom"], False))
        return

    score = r2(y, est.predict(X))
    dim = getattr(est, "constant_units_", None)
    val = getattr(est, "constant_value_", None)

    print(f"\n  equation   : {est.sympy()[:60]}")
    print(f"  R2         : {score:.6f}")
    print(f"  constante deduite : {fmt_dim(dim) if dim is not None else '(non expose)'}")
    if val is not None:
        print(f"  valeur ajustee    : {val:.6g}")

    ok_r2 = score > 0.999
    ok_dim = dims_egales(dim, spec["attendu"])
    ok_val = (val is not None
              and abs(val - spec["valeur"]) <= spec["tol_valeur"] * abs(spec["valeur"]))

    print(f"\n  [{'OK ' if ok_r2  else 'NON'}] R2 > 0.999")
    print(f"  [{'OK ' if ok_dim else 'NON'}] dimension de la constante correcte")
    print(f"  [{'OK ' if ok_val else 'NON'}] valeur a {spec['tol_valeur']:.0%} pres")
    RESULTS.append((spec["nom"], ok_r2 and ok_dim and ok_val))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gens", type=int, default=25)
    ap.add_argument("--restarts", type=int, default=2)
    args = ap.parse_args()

    import gp_elite
    print(f"gp_elite : {os.path.dirname(gp_elite.__file__)}  ({gp_elite.__version__})")
    print(f"budget   : {args.gens} generations x {args.restarts} restart(s)")

    for f in (cas_hooke, cas_newton, cas_gaz):
        try:
            lancer(f, args.gens, args.restarts)
        except Exception as e:
            print(f"\n  >>> ERREUR INATTENDUE : {type(e).__name__}: {e}")
            RESULTS.append((f.__name__, False))

    print("\n" + "=" * 66)
    print("  BILAN")
    print("=" * 66)
    for nom, ok in RESULTS:
        etat = "non implemente" if ok is None else ("REUSSI" if ok else "echoue")
        print(f"  {nom:28s} {etat}")
    reussis = sum(1 for _, ok in RESULTS if ok)
    print(f"\n  {reussis}/{len(RESULTS)} cas valides")
    if reussis == len(RESULTS):
        print("  La constante mystere fonctionne sur les trois lois.")


if __name__ == "__main__":
    main()
