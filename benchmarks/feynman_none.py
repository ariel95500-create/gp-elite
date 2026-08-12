"""Bras `normalize="none"` du banc Feynman gelé — les 15 équations historiques.

Réplique EXACTEMENT le protocole de feynman_bench.py (mêmes graines
RandomState(1000+i), même split 140/60, seed=0, restarts=4, fast/30) en ne
changeant qu'un seul paramètre : normalize="none" au lieu du défaut "auto".

Contexte. La campagne de normalisation (740 runs cumulés) a établi que sur des
colonnes de dynamiques COMPARABLES, la normalisation par colonne nuit aux
fonctions à argument absolu (sinus, cosinus, logarithme) et casse les
différences entre variables (a·x2 − b·x1 n'est plus proportionnel à x2 − x1
dès que a ≠ b). Les 15 équations gelées ont toutes des colonnes en U(1,5) ou
proches — le cas exact où `none` doit dominer. Ce script le mesure.

Résultat attendu (mesuré le 2026-08-03 sur une machine indépendante) :
10/15 EXACT sous auto → 14/15 EXACT sous none, zéro régression, plus rapide.
Seule I.16.6 (rationnelle imbriquée) résiste — le point dur connu (cf. II.11.3).

Usage (Windows, depuis la racine du dépôt) :
    set PYTHONHASHSEED=0
    set PYTHONPATH=%CD%
    python benchmarks\feynman_none.py

Reprise possible : les résultats s'ajoutent à feyn_none.jsonl, les équations
déjà mesurées sont sautées. Le face-à-face avec le bras gelé auto
(benchmarks/results_frozen_v0.2.0.jsonl) s'affiche à la fin.
"""
import numpy as np, time, json, io, contextlib, sys, os

_ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ICI)                      # feynman_bench voisin
sys.path.insert(0, os.path.dirname(_ICI))     # racine du dépôt → gp_elite,
                                              # même sans PYTHONPATH
import feynman_bench as FB
from gp_elite import symbolic_regression

OUT = "feyn_none.jsonl"
FROZEN = os.path.join(_ICI, "results_frozen_v0.2.0.jsonl")
N_HISTORIQUES = 15  # les 15 premières entrées de FB.PROBS sont la suite gelée

SEUIL_EXACT = 1e-9
SEUIL_NEAR = 1e-3


def deja_faites():
    if not os.path.exists(OUT):
        return set()
    noms = set()
    with open(OUT, encoding="utf-8") as fh:
        for ligne in fh:
            if ligne.strip():
                noms.add(json.loads(ligne)["name"])
    return noms


def bras_gele_auto():
    """Erreur pareto du bras gelé, dédupliquée en gardant la dernière mesure."""
    ref = {}
    if os.path.exists(FROZEN):
        with open(FROZEN, encoding="utf-8") as fh:
            for ligne in fh:
                if ligne.strip():
                    r = json.loads(ligne)
                    ref[r["name"]] = r.get("gpe_err")
    return ref


def statut(err):
    if err is None:
        return "?    "
    return "EXACT" if err < SEUIL_EXACT else ("NEAR " if err < SEUIL_NEAR else "MISS ")


def main():
    if os.environ.get("PYTHONHASHSEED") != "0":
        print("ATTENTION : PYTHONHASHSEED n'est pas à 0 — résultats non reproductibles.")
    import gp_elite
    print(f"gp_elite {getattr(gp_elite, '__version__', '?')} — "
          f"{os.path.dirname(gp_elite.__file__)}")

    faites = deja_faites()
    for i in range(N_HISTORIQUES):
        p = FB.PROBS[i]
        name, formula, nv, sampler, f, pool = p[:6]
        if name in faites:
            print(f"  {name:<10} déjà mesurée — sautée")
            continue
        rng = np.random.RandomState(1000 + i)
        X = sampler(rng, 200)
        y = f(X)
        idx = rng.permutation(200)
        tr, te = idx[:140], idx[140:]
        t0 = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            r = symbolic_regression(
                X[tr], y[tr],
                feature_names=[f"v{k}" for k in range(nv)],
                operators=pool, generations=30, speed="fast",
                validation_split=0.15, seed=0, restarts=4,
                normalize="none",
            )
        dt = time.time() - t0
        pred = r.predict(X[te])
        v = float(np.var(y[te]))
        champ = float(np.mean((pred - y[te]) ** 2) / v)
        pb, pb_size = champ, r.size
        for e in (r.pareto or []):
            v1 = float(np.mean((e.predict(X[te]) - y[te]) ** 2) / v)
            if v1 < pb:
                pb, pb_size = v1, e.size
        st = statut(pb).strip()
        rec = dict(name=name, formula=formula, normalize="none", status=st,
                   one_minus_r2=champ, pareto_best=pb, pb_size=pb_size,
                   time=round(dt, 1), expr=r.expression[:90])
        with open(OUT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(f"  {name:<10} {st:<6} champ={champ:.1e} pareto={pb:.1e}  ({dt:.0f}s)  {formula}")
        sys.stdout.flush()

    # ─── face-à-face final ───
    ref = bras_gele_auto()
    mes = {}
    with open(OUT, encoding="utf-8") as fh:
        for ligne in fh:
            if ligne.strip():
                r = json.loads(ligne)
                mes[r["name"]] = r
    print("\n=== FACE-À-FACE — bras gelé auto (v0.2.0) vs bras none ===")
    print(f"{'équation':<11} {'auto':<7} {'none':<7} {'err none':>10}   formule")
    ex_auto = ex_none = 0
    for i in range(N_HISTORIQUES):
        name = FB.PROBS[i][0]
        ea = ref.get(name)
        m = mes.get(name)
        en = m["pareto_best"] if m else None
        sa, sn = statut(ea), statut(en)
        if ea is not None and ea < SEUIL_EXACT:
            ex_auto += 1
        if en is not None and en < SEUIL_EXACT:
            ex_none += 1
        fleche = "  ◀◀" if (sn.strip() == "EXACT" and sa.strip() != "EXACT") else ""
        print(f"{name:<11} {sa:<7} {sn:<7} {en if en is None else format(en, '.1e'):>10}"
              f"   {FB.PROBS[i][1]}{fleche}")
    print(f"\nEXACT : {ex_auto}/15 (auto, gelé) → {ex_none}/15 (none)")
    print("Rappel : `auto` reste le défaut du moteur — la campagne à 270 runs a\n"
          "montré qu'il protège les échelles disparates. Ce bras mesure le cas\n"
          "documenté « colonnes comparables », celui de ce banc.")


if __name__ == "__main__":
    main()
