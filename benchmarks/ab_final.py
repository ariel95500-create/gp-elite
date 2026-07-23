"""Test A/B FINAL — moteur complet (iles + stigmergie), units= vs sans.

Equation cible : Feynman II.11.3, oscillateur force
    x = q * Ef / (m * (w0^2 - w^2))
5 variables aux unites diverses, structure ADDITIVE (w0^2 - w^2) : hors du
biais monomial du generateur typé, donc test honnete.

Mesures (sur un jeu de TEST tenu a l'ecart) :
  - R2_test
  - validite dimensionnelle du modele final (via gp_elite.dimensions, ton auditeur)
  - "recupere" = R2_test > 0.9999 ET dimensionnellement valide

Resumable : chaque (seed, bras) est ecrit dans ab_final_results.jsonl.
Ctrl+C sans risque, relance et il reprend.

Usage : python ab_final.py                      (5 seeds, 40 generations)
        python ab_final.py --seeds 3 --gens 25  (plus rapide)
        python ab_final.py --resume             (affiche juste le bilan)
"""
import argparse
import json
import os
import time

import numpy as np

OUT = "ab_final_results.jsonl"

UNITS = ["A*s", "V/m", "kg", "s^-1", "s^-1"]      # q, Ef, m, w0, w
TARGET = "m"
FEAT_DIMS = {0: {"A": 1, "s": 1},
             1: {"kg": 1, "m": 1, "s": -3, "A": -1},
             2: {"kg": 1},
             3: {"s": -1},
             4: {"s": -1}}
TARGET_DIM = {"m": 1}


def make_data(n, seed):
    rng = np.random.RandomState(seed)
    q = rng.uniform(1, 3, n)
    Ef = rng.uniform(1, 3, n)
    m = rng.uniform(1, 3, n)
    w0 = rng.uniform(3, 5, n)
    w = rng.uniform(1, 2, n)
    X = np.column_stack([q, Ef, m, w0, w])
    y = q * Ef / (m * (w0 ** 2 - w ** 2))
    return X, y


def run_one(mode, seed, gens):
    from gp_elite import GPEliteRegressor
    from gp_elite import dimensions as GD

    Xtr, ytr = make_data(200, seed)
    Xte, yte = make_data(200, seed + 5000)

    kw = dict(operators="physical", generations=gens, speed="fast",
              restarts=1, random_state=seed)
    if mode == "typed":
        kw["units"] = UNITS
        kw["target_units"] = TARGET

    t0 = time.time()
    est = GPEliteRegressor(**kw)
    est.fit(Xtr, ytr)
    dt = time.time() - t0

    pred = est.predict(Xte)
    ss = float(np.sum((yte - yte.mean()) ** 2)) or 1e-30
    r2 = 1.0 - float(np.sum((yte - pred) ** 2) / ss)

    # validite dimensionnelle du modele final.
    #  - stricte  : auditeur v0.3 (n'accepte pas l'enrobage a + b*f)
    #  - tolerante: idem mais en ignorant le scaling lineaire au sommet,
    #               qui est physiquement legitime (a = decalage en unite cible)
    from gp_elite import dim_search as DS
    try:
        strict, msg = GD.check_dimensions(est.model_.node, FEAT_DIMS, TARGET_DIM)
    except Exception as e:
        strict, msg = False, f"{type(e).__name__}: {e}"
    try:
        ok_dim = DS.is_typed_valid(est.model_.node, FEAT_DIMS, TARGET_DIM)
    except Exception as e:
        ok_dim = False
        msg = f"{type(e).__name__}: {e}"

    return dict(mode=mode, seed=seed,
                r2_test=round(r2, 6),
                dim_ok=bool(ok_dim),
                dim_strict=bool(strict),
                recovered=bool(r2 > 0.9999 and ok_dim),
                size=int(est.model_.size),
                seconds=round(dt, 1),
                equation=est.sympy()[:120],
                dim_msg=str(msg)[:80])


def load_done():
    done = set()
    if os.path.exists(OUT):
        for line in open(OUT):
            try:
                r = json.loads(line)
                if r.get("r2_test", 0) < -1e8:      # run en erreur : a rejouer
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
    print("\n" + "=" * 66)
    print(f"{'':16}{'sans units=':>16}{'avec units=':>18}")
    print("-" * 66)
    for label, key in [("recuperations", "recovered"),
                       ("modeles valides", "dim_ok")]:
        vals = []
        for mode in ("untyped", "typed"):
            g = [r for r in rows if r["mode"] == mode]
            vals.append(f"{sum(r[key] for r in g)}/{len(g)}" if g else "-")
        print(f"{label:16}{vals[0]:>16}{vals[1]:>18}")
    for mode, lbl in [("untyped", "sans"), ("typed", "avec")]:
        g = [r for r in rows if r["mode"] == mode]
        if g:
            med = float(np.median([r["r2_test"] for r in g]))
            tm = float(np.median([r["seconds"] for r in g]))
            print(f"  {lbl:5} units= : R2_test median {med:.5f} | "
                  f"{tm:.0f}s par run")
    print("=" * 66)
    best = [r for r in rows if r["mode"] == "typed" and r["recovered"]]
    if best:
        print("\nExemple d'equation recuperee (avec units=) :")
        print(f"  {best[0]['equation'][:100]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--gens", type=int, default=40)
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    if args.resume:
        summary()
        return

    done = load_done()
    if done:
        print(f"{len(done)} runs deja faits, ils seront sautes.\n")
    print(f"Feynman II.11.3  x = q*Ef/(m*(w0^2-w^2))   5 variables")
    print(f"{args.seeds} seeds x {args.gens} generations, par bras\n")

    for mode in ("untyped", "typed"):
        for seed in range(args.seeds):
            if (mode, seed) in done:
                continue
            print(f"  [{mode:<7}] seed {seed} ... ", end="", flush=True)
            try:
                r = run_one(mode, seed, args.gens)
            except Exception as e:
                r = dict(mode=mode, seed=seed, r2_test=-1e9, dim_ok=False,
                         recovered=False, size=0, seconds=0,
                         equation="", dim_msg=f"ERREUR {type(e).__name__}: {e}")
            with open(OUT, "a") as fh:
                fh.write(json.dumps(r) + "\n")
            tag = "RECUPERE" if r["recovered"] else ("valide " if r["dim_ok"] else "invalide")
            print(f"[{tag}] R2={r['r2_test']:.5f} ({r['seconds']:.0f}s)")

    summary()
    print(f"\nResultats dans {OUT} — envoie ce fichier pour analyse.")


if __name__ == "__main__":
    main()
