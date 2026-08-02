"""Normalisation : la règle vaut-elle au-delà de la trigonométrie ?

CE QUI EST ACQUIS
-----------------
Sur les 10 équations trigonométriques du banc étendu, 5 seeds, comparaison
appariée : `normalize="none"` bat la normalisation actuelle sur 31 paires
sur 37, erreur médiane x0.29, modèles 16 nœuds plus compacts, p = 0.0000.
Les récupérations exactes passent de 3 à 19.

Le mécanisme est compris. La normalisation divise chaque colonne par son
maximum. Pour un produit, le facteur sort de l'expression et le linear scaling
l'absorbe — inoffensif. Pour `cos(th)`, il est piégé À L'INTÉRIEUR de la
fonction : `cos(th/max)` n'a plus rien à voir avec `cos(th)`, et le moteur
compense en empilant des nœuds au lieu de trouver la loi.

L'HYPOTHÈSE TESTÉE ICI
----------------------
Si le mécanisme est bien celui-là, il ne concerne pas que le sinus et le
cosinus : `exp`, `log`, `sqrt` et les puissances piègent l'échelle de la même
façon. La règle générale serait alors :

    ne pas normaliser une colonne qui alimente une fonction NON LINÉAIRE

Ce script teste cette hypothèse sur 15 équations des familles exponentielle,
racine, logarithme, puissances et rationnelle — celles dont le banc étendu
mesure 0 à 50 % de récupération exacte.

LE GROUPE TÉMOIN, ET POURQUOI IL EST INDISPENSABLE
--------------------------------------------------
5 équations des familles produit, quotient et produit_quotient sont incluses.
Elles atteignent 100 % de récupération exacte avec la normalisation actuelle.

Sans elles, on saurait seulement que `none` aide sur les cas difficiles — pas
s'il casse ce qui marche déjà. Or c'est exactement ce qui décide si `none` peut
devenir le défaut, ou doit rester une recommandation ciblée.

C'est la leçon d'une mesure précédente : un correctif jugé bénéfique dans une
configuration s'était révélé nuisible dans celle par défaut, faute d'avoir testé
les deux.

`demi` (normalisation partielle) est abandonné : mesuré à p = 0.88 sur la
trigonométrie, indiscernable de la référence.

    python norm_familles.py               (20 équations x 2 stratégies x 5 seeds)
    python norm_familles.py --seeds 3
    python norm_familles.py --resume
"""
import argparse
import json
import os
import time
from math import comb

if os.environ.get("PYTHONHASHSEED") != "0":
    print("ATTENTION : PYTHONHASHSEED n'est pas a 0, resultats non reproductibles.")
    print("            Ferme, tape  set PYTHONHASHSEED=0  puis relance.\n")

import numpy as np

OUT = "norm_familles.jsonl"
REF = "auto"
STRATS = ["auto", "none"]

# Familles à fonction non linéaire : l'hypothèse prédit que `none` aide.
CIBLES = ["I.40.1", "II.35.18",                                   # exponentielle
          "I.10.7", "I.15.10", "II.13.23", "II.24.17", "III.10.19",  # racine
          "I.44.4",                                               # logarithme
          "I.32.5", "III.19.51",                                  # puissances
          "I.34.1", "II.11.3", "II.11.27",                        # rationnelle
          "I.6.20a", "I.8.14"]                                    # exp/sqrt historiques

# Groupe témoin : 100 % de récupération exacte avec la normalisation actuelle.
# `none` ne doit pas les dégrader.
TEMOINS = ["I.25.13", "I.29.4", "II.34.2", "II.2.42", "II.38.3"]

EQUATIONS = CIBLES + TEMOINS


def run_one(prob, strat, seed):
    import feynman_bench as F
    from gp_elite import symbolic_regression

    idx = next(i for i, p in enumerate(F.PROBS) if p[0] == prob)
    name, formula, nv, sampler, f, pool = F.PROBS[idx][:6]
    rng = np.random.RandomState(1000 + idx + 97 * seed)
    X = sampler(rng, 200)
    y = f(X)
    perm = rng.permutation(200)
    tr, te = perm[:140], perm[140:]
    noms = [f"v{k}" for k in range(nv)]

    t0 = time.time()
    r = symbolic_regression(X[tr], y[tr], feature_names=noms, operators=pool,
                            normalize=("none" if strat == "none" else "auto"),
                            generations=30, speed="fast",
                            validation_split=0.15, seed=seed, restarts=4)
    dt = time.time() - t0
    var = float(np.var(y[te])) or 1e-30
    with np.errstate(all="ignore"):
        err = float(np.mean((r.predict(X[te]) - y[te]) ** 2) / var)
    if not np.isfinite(err):
        err = 1e30
    best, bsize = err, int(r.size)
    for e in (r.pareto or []):
        with np.errstate(all="ignore"):
            v1 = float(np.mean((e.predict(X[te]) - y[te]) ** 2) / var)
        if np.isfinite(v1) and v1 < best:
            best, bsize = v1, int(e.size)
    statut = "EXACT" if best < 1e-9 else ("NEAR" if best < 1e-3 else "MISS")
    return dict(problem=prob, formula=formula, famille=F._fam(F.PROBS[idx]),
                groupe=("temoin" if prob in TEMOINS else "cible"),
                strategy=strat, seed=seed, err=best, size=bsize,
                status=statut, seconds=round(dt, 1),
                expr=str(r.expression)[:120])


def sign_test(w, n):
    if n == 0:
        return 1.0
    k = min(w, n - w)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def _bloc(rows, titre, probs, seeds):
    """Compare `none` à `auto`, paire à paire, sur un sous-ensemble."""
    def g(p, s, sd, k="err"):
        v = [r[k] for r in rows
             if r["problem"] == p and r["strategy"] == s and r["seed"] == sd]
        return v[0] if v else None

    w = n = ties = 0
    rat, dz = [], []
    for p in probs:
        for sd in seeds:
            a, b = g(p, REF, sd), g(p, "none", sd)
            if a and b and a > 0 and b > 0:
                lr = np.log(b / a)
                if abs(lr) < 1e-12:
                    ties += 1
                else:
                    n += 1
                    w += int(b < a)
                    rat.append(lr)
            sa, sb = g(p, REF, sd, "size"), g(p, "none", sd, "size")
            if sa and sb:
                dz.append(sb - sa)
    if n == 0 and ties == 0:
        return
    pv = sign_test(w, n)
    print(f"\n  {titre}")
    print(f"    paires où 'none' gagne : {w}/{n}" +
          (f"   ({ties} égalités exclues)" if ties else ""))
    if rat:
        print(f"    erreur médiane         : x{np.exp(np.median(rat)):.2f}")
    if dz:
        print(f"    écart de taille        : {np.median(dz):+.0f} nœuds")
    print(f"    test des signes        : p = {pv:.4f}"
          f"   {'SIGNIFICATIF' if pv < 0.05 else 'non significatif'}")
    return pv, (np.exp(np.median(rat)) if rat else 1.0)


def summary():
    if not os.path.exists(OUT):
        print("Aucun resultat."); return
    rows = [json.loads(l) for l in open(OUT) if l.strip()]
    rows = [r for r in rows if r["err"] < 1e29]
    if not rows:
        print("Aucun resultat exploitable."); return
    seeds = sorted({r["seed"] for r in rows})
    presents = [p for p in EQUATIONS if any(r["problem"] == p for r in rows)]

    print("\n" + "=" * 76)
    print(f"  ERREUR MÉDIANE PAR ÉQUATION   ({len(rows)} runs)")
    print("=" * 76)
    print(f"  {'équation':<12}{'famille':<16}{'auto':>12}{'none':>12}"
          f"{'rapport':>10}   groupe")
    print("  " + "-" * 72)
    for p in presents:
        a = [r["err"] for r in rows if r["problem"] == p and r["strategy"] == "auto"]
        b = [r["err"] for r in rows if r["problem"] == p and r["strategy"] == "none"]
        if not (a and b):
            continue
        ma, mb = np.median(a), np.median(b)
        fam = next(r["famille"] for r in rows if r["problem"] == p)
        grp = next(r["groupe"] for r in rows if r["problem"] == p)
        rap = f"x{mb/ma:.2f}" if ma > 0 else "-"
        print(f"  {p:<12}{fam:<16}{ma:>12.2e}{mb:>12.2e}{rap:>10}   {grp}")

    print("\n  " + "-" * 72)
    for grp in ("cible", "temoin"):
        sub = [r for r in rows if r["groupe"] == grp]
        if not sub:
            continue
        print(f"  {grp.upper():<12}" + "".join(f"{s:>12}" for s in STRATS))
        for st in ("EXACT", "NEAR", "MISS"):
            line = f"    {st:<10}"
            for s in STRATS:
                line += f"{sum(1 for r in sub if r['strategy']==s and r['status']==st):>12}"
            print(line)
        line = f"    {'taille méd':<10}"
        for s in STRATS:
            v = [r["size"] for r in sub if r["strategy"] == s]
            line += f"{np.median(v):>12.0f}" if v else f"{'-':>12}"
        print(line)

    print("\n" + "=" * 76)
    print("  COMPARAISONS APPARIÉES")
    print("=" * 76)
    cibles = [p for p in presents if p in CIBLES]
    temoins = [p for p in presents if p in TEMOINS]
    rc = _bloc(rows, "CIBLES — familles à fonction non linéaire", cibles, seeds)
    rt = _bloc(rows, "TÉMOINS — familles multiplicatives (100 % avec 'auto')",
               temoins, seeds)

    # par famille, pour la carte
    print("\n  Par famille :")
    for fam in sorted({r["famille"] for r in rows}):
        ps = [p for p in presents
              if any(r["problem"] == p and r["famille"] == fam for r in rows)]
        w = n = 0
        for p in ps:
            for sd in seeds:
                a = [r["err"] for r in rows if r["problem"] == p
                     and r["strategy"] == "auto" and r["seed"] == sd]
                b = [r["err"] for r in rows if r["problem"] == p
                     and r["strategy"] == "none" and r["seed"] == sd]
                if a and b and a[0] > 0 and b[0] > 0 and abs(np.log(b[0]/a[0])) > 1e-12:
                    n += 1
                    w += int(b[0] < a[0])
        if n:
            print(f"    {fam:<18} 'none' gagne {w}/{n}   p = {sign_test(w, n):.3f}")

    print("\n" + "-" * 76)
    print("  LECTURE")
    print("-" * 76)
    if rc and rt:
        pc, mc = rc
        pt, mt = rt
        if pc < 0.05 and mc < 1 and pt >= 0.05:
            print("  'none' aide significativement sur les cibles SANS dégrader les")
            print("  témoins : il peut devenir le défaut, ou au minimum être")
            print("  recommandé pour toute variable alimentant une fonction non linéaire.")
        elif pc < 0.05 and mc < 1 and pt < 0.05 and mt > 1:
            print("  'none' aide sur les cibles mais DÉGRADE les témoins : le défaut")
            print("  ne doit pas changer. Recommandation ciblée uniquement, et")
            print("  l'utilisateur doit savoir laquelle s'applique à son problème.")
        elif pc >= 0.05:
            print("  Aucun effet significatif sur les cibles : le mécanisme observé en")
            print("  trigonométrie ne se généralise pas aux autres fonctions non")
            print("  linéaires. La cause des échecs y est donc ailleurs.")
    print("\n  Rappel : la trigonométrie donnait 31/37, x0.29, p = 0.0000.")


def load_done():
    d = set()
    if os.path.exists(OUT):
        for l in open(OUT):
            try:
                r = json.loads(l)
                d.add((r["problem"], r["strategy"], r["seed"]))
            except Exception:
                pass
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--out", default=None)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    global OUT
    if args.out:
        OUT = args.out
    if args.resume:
        summary(); return

    try:
        import feynman_bench  # noqa: F401
    except ImportError:
        print("ERREUR : feynman_bench.py introuvable.")
        print("Lance ce script depuis benchmarks/, ou copie-l'y.")
        raise SystemExit(1)

    import gp_elite
    print(f"gp_elite {gp_elite.__version__} depuis "
          f"{os.path.dirname(gp_elite.__file__)}")
    print(f"{len(CIBLES)} cibles + {len(TEMOINS)} témoins x {len(STRATS)} "
          f"stratégies x {args.seeds} seeds = "
          f"{len(EQUATIONS)*len(STRATS)*args.seeds} runs")
    print(f"sortie : {OUT}\n")

    done = load_done()
    if done:
        print(f"{len(done)} runs deja faits, sautes.\n")

    for prob in EQUATIONS:
        grp = "témoin" if prob in TEMOINS else "cible "
        for strat in STRATS:
            for seed in range(args.seeds):
                if (prob, strat, seed) in done:
                    continue
                print(f"  [{grp}] {prob:<11} {strat:<5} seed {seed} ... ",
                      end="", flush=True)
                try:
                    r = run_one(prob, strat, seed)
                    print(f"{r['status']:<6} err={r['err']:.2e} "
                          f"taille={r['size']:<3} ({r['seconds']:.0f}s)")
                except Exception as e:
                    r = dict(problem=prob, formula="", famille="?",
                             groupe=("temoin" if prob in TEMOINS else "cible"),
                             strategy=strat, seed=seed, err=1e30, size=0,
                             status="ERR", seconds=0, expr="",
                             error=f"{type(e).__name__}: {e}")
                    print(f"ERREUR {type(e).__name__}: {e}")
                with open(OUT, "a") as fh:
                    fh.write(json.dumps(r) + "\n")

    summary()
    print(f"\nResultats dans {OUT} — envoie ce fichier pour analyse.")


if __name__ == "__main__":
    main()
