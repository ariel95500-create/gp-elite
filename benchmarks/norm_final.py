"""Normalisation : le défaut peut-il changer ? — vérification finale.

CE QUI EST ACQUIS
-----------------
Deux campagnes appariées, 350 runs au total :

  trigonométrie (10 équations, 5 seeds)
      `none` gagne 31/37, erreur médiane x0.29, p = 0.0000
      récupérations exactes : 3 -> 19

  familles non linéaires + témoins (20 équations, 5 seeds)
      cibles  : `none` gagne 44/70, x0.55, p = 0.041, exacts 6 -> 20
      témoins : `none` gagne  8/10, x0.34, p = 0.109, exacts 21 -> 24

Sur les témoins — produits et quotients qui atteignaient déjà 100 % — `none`
ne dégrade rien et produit des modèles plus compacts. L'effet se concentre sur
les fonctions à argument absolu (cosinus, logarithme) et il est nul sur les
exponentielles et les puissances, ce qui est cohérent : `x^2` supporte la
normalisation puisque le facteur en sort, comme pour un produit.

CE QUI MANQUE AVANT DE CHANGER LE DÉFAUT
----------------------------------------
Toutes ces mesures portent sur des données SYNTHÉTIQUES, sans bruit, aux
colonnes de dynamiques comparables. Or la normalisation existe précisément pour
protéger le cas inverse : des colonnes dont les ordres de grandeur diffèrent de
plusieurs décades — une masse en kilogrammes à côté d'une longueur d'onde en
nanomètres.

Une sonde préliminaire a donné un résultat troublant : sur `2.5*a*b/c^2` avec
des échelles (1e6, 1, 1e-6), `auto` et `none` échouent IDENTIQUEMENT
(1.8e+00, 6 nœuds). La normalisation ne protégerait donc pas là où elle devrait
le plus servir. Ce script le vérifie sérieusement.

CE QUE CE SCRIPT MESURE
-----------------------
Trois axes croisés, sur des lois dont la forme est connue :

  ÉCHELLE  comparable (x1)  |  modérée (1e3 .. 1e-2)  |  extrême (1e6 .. 1e-6)
  BRUIT    aucun            |  1 %                    |  5 %
  LOI      produit-quotient |  avec cosinus           |  avec logarithme

L'axe échelle est le cœur : si `none` tient jusqu'aux échelles extrêmes, le
défaut peut changer sans réserve. S'il s'effondre là où `auto` résiste, alors
le bon défaut dépend des données, et la documentation doit le dire.

Le bruit est ajouté parce qu'un moteur qui trouve la loi exacte sur données
propres peut se comporter tout autrement dès que le signal est dégradé — et
les données réelles le sont toujours.

RÈGLE FIXÉE D'AVANCE
--------------------
  `none` >= `auto` partout, y compris échelles extrêmes
        -> le défaut devient `none`

  `none` meilleur sauf aux échelles extrêmes
        -> le défaut reste `auto`, et `none` est recommandé quand les colonnes
           ont des dynamiques comparables, ce qui est le cas courant

  les deux échouent aux échelles extrêmes
        -> la normalisation ne remplit pas son rôle ; c'est un défaut à part
           entière, à traiter avant de toucher au défaut

    python norm_final.py                (27 configurations x 5 seeds x 2)
    python norm_final.py --seeds 3
    python norm_final.py --resume
"""
import argparse
import json
import os
import time
from math import comb

if os.environ.get("PYTHONHASHSEED") != "0":
    print("ATTENTION : PYTHONHASHSEED n'est pas a 0, resultats non reproductibles.\n")

import numpy as np

OUT = "norm_final.jsonl"
STRATS = ["auto", "none"]

# (nom, facteurs d'échelle par colonne)
ECHELLES = [
    ("comparable", (1.0, 1.0, 1.0)),
    ("moderee",    (1e3, 1.0, 1e-2)),
    ("extreme",    (1e6, 1.0, 1e-6)),
]
BRUITS = [("propre", 0.0), ("bruit1pc", 0.01), ("bruit5pc", 0.05)]


def loi_produit(a, b, c):
    """2.5*a*b/c^2 — famille où `auto` atteignait déjà 100 %."""
    return 2.5 * a * b / c ** 2


def loi_cosinus(a, b, c):
    """a*(1+0.4*cos(b)) — le cas où `none` gagne le plus.

    `c` est présente mais inutile : elle teste aussi la robustesse au leurre.
    """
    return a * (1.0 + 0.4 * np.cos(b))


def loi_log(a, b, c):
    """a*log(b/c) — l'autre famille qui bascule complètement avec `none`."""
    return a * np.log(np.abs(b / c) + 1e-12)


LOIS = [("produit", loi_produit), ("cosinus", loi_cosinus), ("log", loi_log)]


def fabrique(loi_fn, echelles, bruit, seed, n=200):
    """Données brutes : les échelles s'appliquent APRÈS le calcul de la loi.

    On multiplie chaque colonne par son facteur puis on divise dans la loi, de
    sorte que la cible garde le même ordre de grandeur quelle que soit
    l'échelle. Seul le CONDITIONNEMENT des entrées change — c'est exactement la
    variable qu'on veut isoler.
    """
    rng = np.random.RandomState(seed)
    a = rng.uniform(1.0, 5.0, n)
    b = rng.uniform(1.0, 5.0, n)
    c = rng.uniform(1.0, 5.0, n)
    y = loi_fn(a, b, c)
    if bruit > 0:
        y = y + rng.normal(0.0, bruit * float(np.std(y)), n)
    s0, s1, s2 = echelles
    X = np.column_stack([a * s0, b * s1, c * s2])
    return X, y, (s0, s1, s2)


def _corrige(loi_nom, loi_fn, X, ech):
    """Reconstitue les colonnes brutes à partir des colonnes mises à l'échelle."""
    s0, s1, s2 = ech
    return X[:, 0] / s0, X[:, 1] / s1, X[:, 2] / s2


def run_one(loi_nom, ech_nom, bruit_nom, strat, seed):
    from gp_elite import symbolic_regression
    loi_fn = dict(LOIS)[loi_nom]
    ech = dict(ECHELLES)[ech_nom]
    bruit = dict(BRUITS)[bruit_nom]

    X, y, _ = fabrique(loi_fn, ech, bruit, seed)
    idx = np.random.RandomState(seed + 555).permutation(len(y))
    tr, te = idx[:140], idx[140:]

    t0 = time.time()
    r = symbolic_regression(X[tr], y[tr], feature_names=["a", "b", "c"],
                            operators=("trig" if loi_nom == "cosinus" else "physical"),
                            normalize=("none" if strat == "none" else "auto"),
                            generations=30, speed="fast",
                            validation_split=0.15, seed=seed, restarts=2)
    dt = time.time() - t0
    var = float(np.var(y[te])) or 1e-30
    with np.errstate(all="ignore"):
        err = float(np.mean((r.predict(X[te]) - y[te]) ** 2) / var)
    if not np.isfinite(err):
        err = 1e30
    # Avec bruit, l'exactitude à 1e-9 est inatteignable : le seuil devient le
    # plancher de bruit lui-même.
    seuil = max(1e-9, (bruit ** 2) * 1.5)
    statut = "BON" if err < seuil else ("PROCHE" if err < 1e-2 else "RATE")
    return dict(loi=loi_nom, echelle=ech_nom, bruit=bruit_nom, strategy=strat,
                seed=seed, err=err, size=int(r.size), status=statut,
                seconds=round(dt, 1), expr=str(r.expression)[:110])


def sign_test(w, n):
    if n == 0:
        return 1.0
    k = min(w, n - w)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def _paires(rows, filtre):
    """Compare `none` à `auto` sur le sous-ensemble retenu par `filtre`."""
    cles = sorted({(r["loi"], r["echelle"], r["bruit"], r["seed"])
                   for r in rows if filtre(r)})
    w = n = t = 0
    rat, dz = [], []
    for k in cles:
        a = [r for r in rows if (r["loi"], r["echelle"], r["bruit"], r["seed"]) == k
             and r["strategy"] == "auto"]
        b = [r for r in rows if (r["loi"], r["echelle"], r["bruit"], r["seed"]) == k
             and r["strategy"] == "none"]
        if not (a and b):
            continue
        ea, eb = a[0]["err"], b[0]["err"]
        if ea > 0 and eb > 0:
            lr = np.log(eb / ea)
            if abs(lr) < 1e-12:
                t += 1
            else:
                n += 1; w += int(eb < ea); rat.append(lr)
        dz.append(b[0]["size"] - a[0]["size"])
    return w, n, t, rat, dz


def summary():
    if not os.path.exists(OUT):
        print("Aucun resultat."); return
    rows = [json.loads(l) for l in open(OUT) if l.strip()]
    rows = [r for r in rows if r["err"] < 1e29]
    if not rows:
        print("Aucun resultat exploitable."); return

    print("\n" + "=" * 78)
    print(f"  ERREUR MÉDIANE   ({len(rows)} runs)")
    print("=" * 78)
    print(f"  {'loi':<10}{'échelle':<12}{'bruit':<10}{'auto':>12}{'none':>12}"
          f"{'rapport':>10}")
    print("  " + "-" * 74)
    for loi, _ in LOIS:
        for ech, _ in ECHELLES:
            for br, _ in BRUITS:
                a = [r["err"] for r in rows if r["loi"] == loi and r["echelle"] == ech
                     and r["bruit"] == br and r["strategy"] == "auto"]
                b = [r["err"] for r in rows if r["loi"] == loi and r["echelle"] == ech
                     and r["bruit"] == br and r["strategy"] == "none"]
                if not (a and b):
                    continue
                ma, mb = np.median(a), np.median(b)
                rap = f"x{mb/ma:.2f}" if ma > 0 else "-"
                print(f"  {loi:<10}{ech:<12}{br:<10}{ma:>12.2e}{mb:>12.2e}{rap:>10}")

    print("\n" + "=" * 78)
    print("  PAR ÉCHELLE — l'axe qui décide")
    print("=" * 78)
    verdicts = {}
    for ech, _ in ECHELLES:
        w, n, t, rat, dz = _paires(rows, lambda r, e=ech: r["echelle"] == e)
        if n == 0 and t == 0:
            continue
        pv = sign_test(w, n)
        med = np.exp(np.median(rat)) if rat else 1.0
        verdicts[ech] = (w, n, med, pv)
        print(f"  {ech:<12} 'none' gagne {w}/{n}"
              + (f" ({t} ég.)" if t else "")
              + f"   err méd. x{med:.2f}"
              + (f"   taille {np.median(dz):+.0f}" if dz else "")
              + f"   p = {pv:.4f}"
              + ("   <-- significatif" if pv < 0.05 else ""))

    print("\n  Par niveau de bruit :")
    for br, _ in BRUITS:
        w, n, t, rat, _ = _paires(rows, lambda r, b=br: r["bruit"] == b)
        if n:
            print(f"    {br:<10} {w}/{n}   x{np.exp(np.median(rat)):.2f}"
                  f"   p = {sign_test(w, n):.3f}")

    print("\n  Par loi :")
    for loi, _ in LOIS:
        w, n, t, rat, _ = _paires(rows, lambda r, l=loi: r["loi"] == l)
        if n:
            print(f"    {loi:<10} {w}/{n}   x{np.exp(np.median(rat)):.2f}"
                  f"   p = {sign_test(w, n):.3f}")

    print("\n  Taux de réussite (BON) :")
    for ech, _ in ECHELLES:
        line = f"    {ech:<12}"
        for s in STRATS:
            sub = [r for r in rows if r["echelle"] == ech and r["strategy"] == s]
            if sub:
                line += f"{s}={sum(1 for r in sub if r['status']=='BON')}/{len(sub):<7}"
        print(line)

    print("\n" + "-" * 78)
    print("  VERDICT")
    print("-" * 78)
    ex = verdicts.get("extreme")
    co = verdicts.get("comparable")
    if ex and co:
        _, _, med_ex, p_ex = ex
        _, _, med_co, _ = co
        rate_auto = sum(1 for r in rows if r["echelle"] == "extreme"
                        and r["strategy"] == "auto" and r["status"] == "RATE")
        rate_none = sum(1 for r in rows if r["echelle"] == "extreme"
                        and r["strategy"] == "none" and r["status"] == "RATE")
        tot = sum(1 for r in rows if r["echelle"] == "extreme"
                  and r["strategy"] == "auto")
        if tot and rate_auto >= 0.8 * tot and rate_none >= 0.8 * tot:
            print("  Les DEUX stratégies échouent aux échelles extrêmes")
            print(f"  (auto {rate_auto}/{tot} ratés, none {rate_none}/{tot}).")
            print("  La normalisation ne remplit pas le rôle qu'on lui prête :")
            print("  c'est un défaut à traiter AVANT de toucher au défaut de `normalize`.")
        elif med_ex <= 1.0 and med_co <= 1.0:
            print("  'none' tient à toutes les échelles : le défaut peut devenir `none`.")
        elif med_co < 1.0 < med_ex:
            print("  'none' est meilleur aux échelles comparables et moins bon aux")
            print("  extrêmes : garder `auto` par défaut, recommander `none` quand les")
            print("  colonnes ont des dynamiques voisines — le cas courant.")
        else:
            print("  Aucune tendance claire ; ne pas changer le défaut.")


def load_done():
    d = set()
    if os.path.exists(OUT):
        for l in open(OUT):
            try:
                r = json.loads(l)
                d.add((r["loi"], r["echelle"], r["bruit"], r["strategy"], r["seed"]))
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

    import gp_elite
    print(f"gp_elite {gp_elite.__version__} depuis "
          f"{os.path.dirname(gp_elite.__file__)}")
    total = len(LOIS) * len(ECHELLES) * len(BRUITS) * len(STRATS) * args.seeds
    print(f"{len(LOIS)} lois x {len(ECHELLES)} échelles x {len(BRUITS)} bruits "
          f"x 2 stratégies x {args.seeds} seeds = {total} runs")
    print(f"sortie : {OUT}\n")

    done = load_done()
    if done:
        print(f"{len(done)} runs deja faits, sautes.\n")

    for loi, _ in LOIS:
        for ech, _ in ECHELLES:
            for br, _ in BRUITS:
                for strat in STRATS:
                    for seed in range(args.seeds):
                        if (loi, ech, br, strat, seed) in done:
                            continue
                        print(f"  {loi:<9}{ech:<11}{br:<10}{strat:<5}"
                              f"seed {seed} ... ", end="", flush=True)
                        try:
                            r = run_one(loi, ech, br, strat, seed)
                            print(f"{r['status']:<7}err={r['err']:.2e} "
                                  f"taille={r['size']:<3} ({r['seconds']:.0f}s)")
                        except Exception as e:
                            r = dict(loi=loi, echelle=ech, bruit=br,
                                     strategy=strat, seed=seed, err=1e30,
                                     size=0, status="ERR", seconds=0, expr="",
                                     error=f"{type(e).__name__}: {e}")
                            print(f"ERREUR {type(e).__name__}: {e}")
                        with open(OUT, "a") as fh:
                            fh.write(json.dumps(r) + "\n")

    summary()
    print(f"\nResultats dans {OUT} — envoie ce fichier pour analyse.")


if __name__ == "__main__":
    main()
