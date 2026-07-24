"""Test A/B — moteur complet, units= vs sans, avec test HORS DOMAINE.

Equation cible : Feynman II.11.3, oscillateur force
    x = q * Ef / (m * (w0^2 - w^2))

Ce que cette version corrige par rapport a ab_final.py
------------------------------------------------------
1. L'ancien critere "recupere" valait  R2_test > 0.9999 et dimensionnellement
   valide. Mais le jeu de test etait tire dans LE MEME domaine que
   l'entrainement : une approximation qui colle au domaine y marque presque
   aussi bien que la loi. Le critere ne separait donc pas "retrouver la loi"
   de "bien approximer ici".

   On ajoute un jeu HORS DOMAINE, pousse vers la resonance (w/w0 dans
   [0.70, 0.90] contre [0.20, 0.67] a l'entrainement). La vraie loi y reste
   exacte ; les approximations s'y effondrent. Mesure verifiee : les formes
   effectivement produites par le moteur passent de R2 ~0.91-0.98 a ~0.79-0.82,
   la vraie loi reste a 1.00000.

2. Un troisieme bras "untyped_fair" donne au bras SANS contrainte un budget en
   generations multiplie (defaut x4, le rapport de temps mesure), pour repondre
   d'avance a l'objection "ton bras typed a eu plus de calcul". Les bras
   untyped et typed ont, eux, un budget nominal STRICTEMENT identique
   (memes generations, meme speed donc meme population, meme restarts) :
   seul units= differe.

Mesures par run :
  - r2_test  : jeu de test tenu a l'ecart, MEME domaine  (ancien critere)
  - r2_ood   : jeu HORS DOMAINE                          (nouveau critere)
  - dim_ok / dim_strict : validite dimensionnelle du modele final
  - size, seconds

  - fits_indomain = r2_test > 0.9999 et dim_ok     <- ce que mesurait l'ancien
  - recovered     = r2_ood  > 0.999  et dim_ok     <- recuperation reelle

Resumable : chaque (seed, bras) est ecrit dans ab_ood_results.jsonl.
Ctrl+C sans risque, relance et il reprend.

Usage : python ab_ood.py                        (5 seeds, 40 generations)
        python ab_ood.py --seeds 3 --gens 25    (plus rapide)
        python ab_ood.py --no-fair              (sans le 3e bras)
        python ab_ood.py --resume               (affiche juste le bilan)

A lancer depuis la RACINE du depot, apres  set PYTHONHASHSEED=0
"""
import argparse
import json
import os
import time

import numpy as np

OUT = "ab_ood_results.jsonl"      # surchargeable par --out

UNITS = ["A*s", "V/m", "kg", "s^-1", "s^-1"]      # q, Ef, m, w0, w
TARGET = "m"
FEAT_DIMS = {0: {"A": 1, "s": 1},
             1: {"kg": 1, "m": 1, "s": -3, "A": -1},
             2: {"kg": 1},
             3: {"s": -1},
             4: {"s": -1}}
TARGET_DIM = {"m": 1}

ARMS = ("untyped", "typed", "untyped_fair")


def _loi(q, Ef, m, w0, w):
    return q * Ef / (m * (w0 ** 2 - w ** 2))


def make_data(n, seed):
    """Domaine d'entrainement : w0 dans [3,5], w dans [1,2] -> w/w0 dans [0.20, 0.67]."""
    rng = np.random.RandomState(seed)
    q = rng.uniform(1, 3, n)
    Ef = rng.uniform(1, 3, n)
    m = rng.uniform(1, 3, n)
    w0 = rng.uniform(3, 5, n)
    w = rng.uniform(1, 2, n)
    return np.column_stack([q, Ef, m, w0, w]), _loi(q, Ef, m, w0, w)


def make_data_ood(n, seed):
    """HORS DOMAINE : on approche la resonance, w/w0 dans [0.70, 0.90].

    Meme plage pour q, Ef, m, w0 : seul le rapport w/w0 sort du domaine vu a
    l'entrainement. C'est le regime ou la loi compte le plus, et celui ou une
    approximation calibree sur [0.20, 0.67] n'a aucune raison de tenir.
    """
    rng = np.random.RandomState(seed)
    q = rng.uniform(1, 3, n)
    Ef = rng.uniform(1, 3, n)
    m = rng.uniform(1, 3, n)
    w0 = rng.uniform(3, 5, n)
    w = rng.uniform(0.70, 0.90, n) * w0
    return np.column_stack([q, Ef, m, w0, w]), _loi(q, Ef, m, w0, w)


def _r2(y, pred):
    ss = float(np.sum((y - y.mean()) ** 2)) or 1e-30
    val = 1.0 - float(np.sum((y - pred) ** 2) / ss)
    return val if np.isfinite(val) else -1e6


def run_one(mode, seed, gens, fair_factor, restarts=1, speed="fast"):
    from gp_elite import GPEliteRegressor
    from gp_elite import dimensions as GD
    from gp_elite import dim_search as DS

    Xtr, ytr = make_data(200, seed)
    Xte, yte = make_data(200, seed + 5000)
    Xod, yod = make_data_ood(200, seed + 9000)

    n_gens = gens * fair_factor if mode == "untyped_fair" else gens
    kw = dict(operators="physical", generations=n_gens, speed=speed,
              restarts=restarts, random_state=seed)
    if mode == "typed":
        kw["units"] = UNITS
        kw["target_units"] = TARGET

    t0 = time.time()
    est = GPEliteRegressor(**kw)
    est.fit(Xtr, ytr)
    dt = time.time() - t0

    with np.errstate(all="ignore"):
        r2_test = _r2(yte, est.predict(Xte))
        r2_ood = _r2(yod, est.predict(Xod))

    try:
        strict, msg = GD.check_dimensions(est.model_.node, FEAT_DIMS, TARGET_DIM)
    except Exception as e:
        strict, msg = False, f"{type(e).__name__}: {e}"
    try:
        ok_dim = DS.is_typed_valid(est.model_.node, FEAT_DIMS, TARGET_DIM)
    except Exception as e:
        ok_dim = False
        msg = f"{type(e).__name__}: {e}"

    return dict(mode=mode, seed=seed, generations=n_gens,
                restarts=restarts, speed=speed,
                r2_test=round(r2_test, 6),
                r2_ood=round(r2_ood, 6),
                dim_ok=bool(ok_dim),
                dim_strict=bool(strict),
                fits_indomain=bool(r2_test > 0.9999 and ok_dim),
                recovered=bool(r2_ood > 0.999 and ok_dim),
                size=int(est.model_.size),
                seconds=round(dt, 1),
                equation=est.sympy()[:400],
                dim_msg=str(msg)[:80])


def load_done():
    done = set()
    if os.path.exists(OUT):
        for line in open(OUT):
            try:
                r = json.loads(line)
                if r.get("r2_test", 0) < -1e8:
                    continue
                done.add((r["mode"], r["seed"]))
            except Exception:
                pass
    return done


def summary():
    if not os.path.exists(OUT):
        print("Aucun resultat.")
        return
    rows = [json.loads(l) for l in open(OUT) if l.strip()]
    groups = {a: [r for r in rows if r["mode"] == a] for a in ARMS}
    groups = {a: g for a, g in groups.items() if g}
    if not groups:
        print("Aucun resultat exploitable.")
        return

    noms = {"untyped": "sans units=", "typed": "avec units=",
            "untyped_fair": "sans units= x4"}
    cols = list(groups)
    larg = 18

    print("\n" + "=" * (22 + larg * len(cols)))
    print(f"{'':22}" + "".join(f"{noms[c]:>{larg}}" for c in cols))
    print("-" * (22 + larg * len(cols)))

    def ligne(label, fn):
        print(f"{label:22}" + "".join(f"{fn(groups[c]):>{larg}}" for c in cols))

    ligne("modeles valides", lambda g: f"{sum(r['dim_ok'] for r in g)}/{len(g)}")
    ligne("colle en domaine", lambda g: f"{sum(r['fits_indomain'] for r in g)}/{len(g)}")
    ligne("RECUPERE (hors dom.)", lambda g: f"{sum(r['recovered'] for r in g)}/{len(g)}")
    ligne("R2 test median", lambda g: f"{np.median([r['r2_test'] for r in g]):.5f}")
    ligne("R2 HORS DOM. median", lambda g: f"{np.median([r['r2_ood'] for r in g]):.5f}")
    ligne("taille mediane", lambda g: f"{np.median([r['size'] for r in g]):.0f}")
    ligne("secondes / run", lambda g: f"{np.median([r['seconds'] for r in g]):.0f}")
    print("=" * (22 + larg * len(cols)))

    print("\nLecture : 'colle en domaine' est l'ancien critere (R2 sur un test tire")
    print("dans le meme domaine). 'RECUPERE' exige en plus que le modele tienne")
    print("HORS du domaine d'entrainement — c'est ce qui separe la loi de")
    print("l'approximation. Un ecart entre les deux lignes = surajustement au domaine.")

    best = [r for r in rows if r["recovered"]]
    if best:
        print("\nExemple de modele ayant reellement recupere la loi :")
        print(f"  [{best[0]['mode']}] {best[0]['equation'][:110]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--gens", type=int, default=40)
    ap.add_argument("--fair-factor", type=int, default=4,
                    help="budget du bras untyped_fair, en multiples de --gens")
    ap.add_argument("--no-fair", action="store_true",
                    help="ne pas lancer le 3e bras (comparaison a temps egal)")
    ap.add_argument("--arms", default=None,
                    help="bras a lancer, separes par des virgules "
                         "(ex: --arms typed). Defaut : tous.")
    ap.add_argument("--restarts", type=int, default=1,
                    help="restarts par run (levier le plus efficace a gros budget)")
    ap.add_argument("--speed", default="fast",
                    choices=["ultrafast", "fast", "normal"],
                    help="preset de population ; 'normal' = population plus large")
    ap.add_argument("--out", default=None,
                    help="fichier de resultats (defaut : ab_ood_results.jsonl)")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    global OUT
    if args.out:
        OUT = args.out

    if args.resume:
        summary()
        return

    if os.environ.get("PYTHONHASHSEED") != "0":
        print("ATTENTION : PYTHONHASHSEED n'est pas a 0. Les resultats ne seront")
        print("            pas reproductibles. Ferme, tape  set PYTHONHASHSEED=0")
        print("            puis relance.\n")

    if args.arms:
        demandes = [a.strip() for a in args.arms.split(",") if a.strip()]
        inconnus = [a for a in demandes if a not in ARMS]
        if inconnus:
            raise SystemExit(f"bras inconnu(s) : {inconnus}. Choix : {list(ARMS)}")
        arms = demandes
    else:
        arms = [a for a in ARMS if not (args.no_fair and a == "untyped_fair")]
    done = load_done()
    if done:
        print(f"{len(done)} runs deja faits, ils seront sautes.\n")
    print("Feynman II.11.3  x = q*Ef/(m*(w0^2-w^2))   5 variables")
    print(f"{args.seeds} seeds x {args.gens} generations x {args.restarts} "
          f"restart(s), speed={args.speed}")
    print(f"bras : {', '.join(arms)}"
          + (f"  (untyped_fair : x{args.fair_factor} generations)"
             if "untyped_fair" in arms else ""))
    print(f"sortie : {OUT}")
    print("Test hors domaine : w/w0 dans [0.70, 0.90] "
          "(entrainement : [0.20, 0.67])\n")

    for mode in arms:
        for seed in range(args.seeds):
            if (mode, seed) in done:
                continue
            print(f"  [{mode:<12}] seed {seed} ... ", end="", flush=True)
            try:
                r = run_one(mode, seed, args.gens, args.fair_factor,
                            args.restarts, args.speed)
            except Exception as e:
                r = dict(mode=mode, seed=seed, generations=0,
                         restarts=args.restarts, speed=args.speed, r2_test=-1e9,
                         r2_ood=-1e9, dim_ok=False, dim_strict=False,
                         fits_indomain=False, recovered=False, size=0,
                         seconds=0, equation="",
                         dim_msg=f"ERREUR {type(e).__name__}: {e}")
            with open(OUT, "a") as fh:
                fh.write(json.dumps(r) + "\n")
            if r["recovered"]:
                tag = "RECUPERE"
            elif r["dim_ok"]:
                tag = "valide  "
            else:
                tag = "invalide"
            print(f"[{tag}] R2={r['r2_test']:.5f} "
                  f"hors_dom={r['r2_ood']:.5f} ({r['seconds']:.0f}s)")

    summary()
    print(f"\nResultats dans {OUT} — envoie ce fichier pour analyse.")


if __name__ == "__main__":
    main()
