"""Normalisation et arguments périodiques — quelle stratégie retenir ?

CE QUI A CONDUIT ICI
--------------------
Le banc étendu à 41 équations donne une carte nette : le moteur récupère 100 %
des produits, quotients et produits de quotients, et 0 % des familles trigo,
racine, rationnelle et exponentielle. La taille médiane des modèles raconte la
même histoire — 8 nœuds sur un quotient, 55 en trigonométrie : quand il ne
trouve pas la loi, il empile de la complexité.

Une cause a été identifiée pour la trigonométrie. La normalisation divise chaque
colonne par son maximum, ce qui est inoffensif pour un produit — le facteur sort
de l'expression et le linear scaling l'absorbe — mais destructeur pour un
argument d'angle : `cos(th/max)` n'a plus rien à voir avec `cos(th)`, et le
facteur de compensation est piégé À L'INTÉRIEUR de la fonction périodique.

Mesuré sur III.17.37, `B*(1+al*cos(th))` :

    normalize="auto"   1-R2 = 2.0e-01, 26 nœuds, formule illisible
    normalize="none"   1-R2 = 4.1e-32,  8 nœuds, B + cos(th)*(al*B)

La loi exacte, à précision machine. Mais sur quatre autres équations trigo,
l'effet va de « légèrement mieux » à « un peu moins bien » — avec, à chaque
fois, un modèle nettement plus compact.

CE QUE CE SCRIPT DÉCIDE
-----------------------
Une heuristique automatique a été envisagée : ne pas normaliser une colonne dont
l'étendue est proche d'un multiple de 2*pi. Elle a été écartée par la mesure — les
angles du corpus s'étalent de 1.50 à 6.28 radians, et une variable quelconque
tirée dans [1,5] a une étendue de 4. Indiscernable.

Restent deux stratégies, testées ici sur les 7 équations trigonométriques :

    auto  — la normalisation actuelle (référence)
    none  — pas de normalisation du tout
    demi  — normalisation, mais bornes élargies pour préserver l'échelle
            des colonnes dont l'étendue dépasse 2 (voir _demi ci-dessous)

La troisième teste si un compromis existe : garder le bénéfice de la
normalisation sur les colonnes à grande dynamique, sans écraser les angles.

RÈGLE FIXÉE D'AVANCE
--------------------
Si `none` domine nettement (plus d'exacts, ou modèles plus compacts sans perte
de précision), la recommandation devient : documenter `normalize="none"` pour
les problèmes à variable angulaire, et le proposer dans le mode console.

Si aucune stratégie ne domine, la conclusion est que la normalisation n'est pas
la cause principale des échecs trigonométriques, et il faudra chercher ailleurs
— probablement du côté de la génération d'arguments d'angle.

MÉTHODE
-------
5 seeds par équation et par stratégie. Comparaison appariée contre `auto`,
test des signes en excluant les égalités. Aucune moyenne géométrique : une
résolution quasi exacte suffit à l'écraser.

    python norm_trig.py                (7 équations x 3 stratégies x 5 seeds)
    python norm_trig.py --seeds 3
    python norm_trig.py --resume
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

OUT = "norm_trig.jsonl"
REF = "auto"
STRATS = ["auto", "none", "demi"]

# Les 7 équations trigonométriques du banc étendu, avec leur indice d'origine
# (l'indice fixe la graine d'échantillonnage, pour rester comparable au banc).
TRIG = ["II.15.4", "I.18.12", "III.15.12", "I.26.2", "I.30.5",
        "I.37.4", "I.50.26", "II.6.15b", "III.9.52", "III.17.37"]


def _demi_normalise(X):
    """Normalise seulement les colonnes à grande dynamique.

    Une colonne dont l'étendue dépasse 2 est probablement une grandeur physique
    à échelle libre : la normaliser aide. En dessous, elle peut être un angle en
    radians ou une grandeur déjà réduite : on la laisse brute.

    Le seuil de 2 n'est pas une loi, c'est une hypothèse que ce script teste.
    """
    Xs = np.array(X, dtype=float, copy=True)
    for k in range(Xs.shape[1]):
        etendue = float(Xs[:, k].max() - Xs[:, k].min())
        if etendue > 2.0:
            m = float(np.max(np.abs(Xs[:, k]))) or 1.0
            Xs[:, k] = Xs[:, k] / m
    return Xs


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

    Xin, norm = X, "auto"
    if strat == "none":
        norm = "none"
    elif strat == "demi":
        Xin, norm = _demi_normalise(X), "none"   # pré-normalisé à la main

    t0 = time.time()
    r = symbolic_regression(Xin[tr], y[tr], feature_names=noms, operators=pool,
                            normalize=norm, generations=30, speed="fast",
                            validation_split=0.15, seed=seed, restarts=4)
    dt = time.time() - t0
    var = float(np.var(y[te])) or 1e-30
    with np.errstate(all="ignore"):
        err = float(np.mean((r.predict(Xin[te]) - y[te]) ** 2) / var)
    if not np.isfinite(err):
        err = 1e30
    # meilleur point du front, comme dans le banc
    best, bsize = err, int(r.size)
    for e in (r.pareto or []):
        with np.errstate(all="ignore"):
            v1 = float(np.mean((e.predict(Xin[te]) - y[te]) ** 2) / var)
        if np.isfinite(v1) and v1 < best:
            best, bsize = v1, int(e.size)
    statut = "EXACT" if best < 1e-9 else ("NEAR" if best < 1e-3 else "MISS")
    return dict(problem=prob, formula=formula, strategy=strat, seed=seed,
                err=best, size=bsize, status=statut, seconds=round(dt, 1),
                expr=str(r.expression)[:120])


def sign_test(w, n):
    if n == 0:
        return 1.0
    k = min(w, n - w)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def summary():
    if not os.path.exists(OUT):
        print("Aucun resultat."); return
    rows = [json.loads(l) for l in open(OUT) if l.strip()]
    rows = [r for r in rows if r["err"] < 1e29]
    if not rows:
        print("Aucun resultat exploitable."); return
    probs = [p for p in TRIG if any(r["problem"] == p for r in rows)]
    seeds = sorted({r["seed"] for r in rows})
    strats = [s for s in STRATS if any(r["strategy"] == s for r in rows)]

    def g(p, s, sd, k="err"):
        v = [r[k] for r in rows
             if r["problem"] == p and r["strategy"] == s and r["seed"] == sd]
        return v[0] if v else None

    print("\n" + "=" * 74)
    print(f"  ERREUR MEDIANE PAR EQUATION   ({len(rows)} runs)")
    print("=" * 74)
    print(f"  {'equation':<12}" + "".join(f"{s:>13}" for s in strats) + "   formule")
    print("  " + "-" * 70)
    for p in probs:
        line = f"  {p:<12}"
        for s in strats:
            v = [r["err"] for r in rows if r["problem"] == p and r["strategy"] == s]
            line += f"{np.median(v):>13.2e}" if v else f"{'-':>13}"
        f = next(r["formula"] for r in rows if r["problem"] == p)
        print(line + f"   {f[:28]}")

    print("\n  " + "-" * 70)
    print(f"  {'statuts':<12}" + "".join(f"{s:>13}" for s in strats))
    for st in ("EXACT", "NEAR", "MISS"):
        line = f"  {st:<12}"
        for s in strats:
            line += f"{sum(1 for r in rows if r['strategy']==s and r['status']==st):>13}"
        print(line)
    line = f"  {'taille med.':<12}"
    for s in strats:
        line += f"{np.median([r['size'] for r in rows if r['strategy']==s]):>13.0f}"
    print(line)

    print("\n" + "=" * 74)
    print(f"  COMPARE A '{REF}', PAIRE A PAIRE (meme equation, meme seed)")
    print("=" * 74)
    print(f"  {'strategie':<10}{'mieux':>10}{'err mediane':>15}{'taille':>12}{'p':>10}")
    for s in strats:
        if s == REF:
            continue
        w = n = ties = 0
        rat, dsz = [], []
        for p in probs:
            for sd in seeds:
                a, b = g(p, REF, sd), g(p, s, sd)
                if a is None or b is None or a <= 0 or b <= 0:
                    continue
                lr = np.log(b / a)
                if abs(lr) < 1e-12:
                    ties += 1
                else:
                    n += 1; w += int(b < a); rat.append(lr)
                sa, sb = g(p, REF, sd, "size"), g(p, s, sd, "size")
                if sa and sb:
                    dsz.append(sb - sa)
        pv = sign_test(w, n)
        med = f"x{np.exp(np.median(rat)):.2f}" if rat else "-"
        tz = f"{np.median(dsz):+.0f} noeuds" if dsz else "-"
        flag = "  <-- significatif" if pv < 0.05 else ""
        print(f"  {s:<10}{f'{w}/{n}':>10}{med:>15}{tz:>12}{pv:>10.4f}{flag}")
        if ties:
            print(f"  {'':10}({ties} egalites exclues)")

    print("\nLecture : sous 1.00, la strategie fait MIEUX que la normalisation")
    print("actuelle. Un ecart de taille negatif signifie des modeles plus compacts,")
    print("ce qui compte autant que l'erreur : un modele de 8 noeuds qui atteint la")
    print("precision machine est une LOI, un modele de 55 noeuds est un ajustement.")


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
        print("Lance ce script depuis le dossier benchmarks/, ou copie-l'y.")
        raise SystemExit(1)

    import gp_elite
    print(f"gp_elite {gp_elite.__version__} depuis "
          f"{os.path.dirname(gp_elite.__file__)}")
    total = len(TRIG) * len(STRATS) * args.seeds
    print(f"{len(TRIG)} equations x {len(STRATS)} strategies x {args.seeds} "
          f"seeds = {total} runs")
    print(f"sortie : {OUT}\n")

    done = load_done()
    if done:
        print(f"{len(done)} runs deja faits, sautes.\n")

    for prob in TRIG:
        for strat in STRATS:
            for seed in range(args.seeds):
                if (prob, strat, seed) in done:
                    continue
                print(f"  {prob:<11} {strat:<5} seed {seed} ... ", end="", flush=True)
                try:
                    r = run_one(prob, strat, seed)
                    print(f"{r['status']:<6} err={r['err']:.2e} "
                          f"taille={r['size']:<3} ({r['seconds']:.0f}s)")
                except Exception as e:
                    r = dict(problem=prob, formula="", strategy=strat, seed=seed,
                             err=1e30, size=0, status="ERR", seconds=0, expr="",
                             error=f"{type(e).__name__}: {e}")
                    print(f"ERREUR {type(e).__name__}: {e}")
                with open(OUT, "a") as fh:
                    fh.write(json.dumps(r) + "\n")

    summary()
    print(f"\nResultats dans {OUT} — envoie ce fichier pour analyse.")


if __name__ == "__main__":
    main()
