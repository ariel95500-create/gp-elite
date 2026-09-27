# -*- coding: utf-8 -*-
"""
BANC DU POINT DE BASCULE — à partir de quelle disparité d'échelle
faut-il normaliser ?
==================================================================
POURQUOI
--------
Le banc des défauts a montré que `normalize="auto"` coûte ~4 équations sur
Feynman (10.3/15 pour le meilleur candidat, contre 14/15 pour le bras
`none`) — davantage que tous les réglages de budget réunis. Mais on ne peut
pas basculer le défaut sur `none` : 270 runs sur échelles disparates
justifiaient `auto`.

L'heuristique actuelle (`core._choose_scaler`, l.7296) ne se demande jamais
S'IL FAUT normaliser — seulement COMMENT :

    all_pos = bool(np.all(X_raw > 0))
    mode = "divmax" if all_pos else "minmax"

Il manque un test préalable : si les colonnes sont déjà d'échelles
comparables, ne rien faire.

Sondage préalable (rapport des écarts-types entre colonnes) :
    jeux Feynman            : 1.0 à 7.4
    Nikuradse (réel)        : 208
    unités SI mélangées     : 10^8 à 10^9
Un seuil entre 10 et 100 sépare les deux mondes. CE BANC LE MESURE au lieu
de le deviner.

MÉTHODE
-------
Pour chaque équation, on multiplie la DERNIÈRE colonne de X par 10^e, e
croissant. La cible y reste calculée sur les données NON redimensionnées :
la loi à retrouver garde la même structure, seules ses constantes changent.
On compare alors `none` et `auto` à chaque niveau de disparité.

Le croisement des deux courbes EST le seuil à écrire dans l'heuristique.

PROTOCOLE — identique aux autres bancs : generations=30, speed="fast",
restarts=4, validation_split=0.15, seed=0, split 140/60, graines
RandomState(1000+i). Seuls varient l'échelle et le mode de normalisation.

Sortie : feyn_scale_ratio.jsonl   |   Reprise automatique.

Lancement :
  set "PYTHONHASHSEED=0" && python benchmarks\\feynman_scale_ratio.py
Options :
  --exps 0,1,2,3,4,6     décades testées (défaut)
  --modes none,auto
  --bilan
"""
import os, sys, json, time, io, re, contextlib, hashlib, datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

EXPECTED_ENGINE = "0.6.0"
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.isdir(os.path.join(_ROOT, "gp_elite")):
    sys.path.insert(0, _ROOT)

import gp_elite
from gp_elite import symbolic_regression
import numpy as np

ENGINE = getattr(gp_elite, "__version__", "?")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "feyn_scale_ratio.jsonl")

R = np.random.RandomState
def U(rng, lo, hi, n): return rng.uniform(lo, hi, n)

EXPS = [0, 1, 2, 3, 4, 6]          # facteur 10^e sur la dernière colonne
MODES = ["none", "auto"]

# sous-ensemble représentatif : 2 à 4 variables, toutes les familles
PROBS = [
 (0,  "I.12.1",   "mu*Nn",                     2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1], "physical", 3),
 (2,  "I.14.4",   "k*x^2/2",                   2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: 0.5*X[:,0]*X[:,1]**2, "physical", 7),
 (4,  "II.3.24",  "P/(4*pi*r^2)",              2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,3,n)],
   lambda X: X[:,0]/(4*np.pi*X[:,1]**2), "physical", 6),
 (6,  "I.8.14",   "sqrt((x2-x1)^2+(y2-y1)^2)", 4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: np.sqrt((X[:,1]-X[:,0])**2+(X[:,3]-X[:,2])**2), "physical", 10),
 (8,  "I.27.6",   "1/(1/d1+n/d2)",             3, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,2,n)],
   lambda X: 1.0/(1.0/X[:,0]+X[:,2]/X[:,1]), "physical", 9),
 (9,  "I.34.8",   "q*v*B/p",                   4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1]*X[:,2]/X[:,3], "physical", 7),
 (11, "I.12.2",   "q1*q2/(4*pi*eps*r^2)",      4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,3,n),U(r,1,3,n)],
   lambda X: X[:,0]*X[:,1]/(4*np.pi*X[:,2]*X[:,3]**2), "physical", 11),
 (14, "III.15.12","2*U*(1-cos(k*d))",          3, lambda r,n: np.c_[U(r,1,5,n),U(r,0.5,2,n),U(r,0.5,2,n)],
   lambda X: 2*X[:,0]*(1-np.cos(X[:,1]*X[:,2])), "trig", 10),
]

_OPS = ("sin","cos","tanh","tan","exp","log","sqrt","abs","pow","cube")
_SUSPECT = {"sin","cos","tanh","tan","exp","log","sqrt"}

def _census(expr):
    c = {}
    for op in _OPS:
        k = len(re.findall(r"\b%s\s*\(" % op, expr))
        if op == "tan": k -= len(re.findall(r"\btanh\s*\(", expr))
        if k > 0: c[op] = k
    sq = expr.count("\u00b2")
    if sq: c["square"] = sq
    return c

def _expected(f): return set(re.findall(r"\b(sin|cos|tanh|tan|exp|log|sqrt|abs)\b", f))
def _err(e, X, y, v): return float(np.mean((e.predict(X) - y) ** 2) / v)

def scale_ratio(X):
    sd = np.std(X, axis=0)
    return float(sd.max() / max(sd.min(), 1e-30))

def _done():
    if not os.path.exists(OUT): return set()
    ks = set()
    for line in open(OUT, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        try:
            r = json.loads(line); ks.add((r["name"], r["exp"], r["normalize"]))
        except Exception: pass
    return ks

def _check_engine():
    print(f"gp_elite {ENGINE}  <-  {os.path.abspath(gp_elite.__file__)}")
    if ENGINE != EXPECTED_ENGINE:
        print(f"\n!! ARRÊT : moteur {ENGINE}, attendu {EXPECTED_ENGINE}.")
        if "--force" not in sys.argv: sys.exit(1)

def run(exps, modes):
    done = _done()
    for e in exps:
        print(f"\n=== dernière colonne x10^{e} ===")
        for idx, name, formula, nv, sampler, f, pool, canon in PROBS:
            rng = R(1000 + idx)
            X0 = sampler(rng, 200)
            y = f(X0)                       # cible calculée AVANT redimensionnement
            X = X0.copy(); X[:, -1] *= 10.0 ** e
            ratio = scale_ratio(X)
            perm = rng.permutation(200); tr, te = perm[:140], perm[140:]
            names = [f"v{k}" for k in range(nv)]
            for mode in modes:
                if (name, e, mode) in done:
                    print(f"  {name:<11} {mode:<5} déjà fait — repris"); continue
                t0 = time.time()
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        r = symbolic_regression(X[tr], y[tr], feature_names=names,
                                                operators=pool, normalize=mode,
                                                generations=30, speed="fast",
                                                validation_split=0.15, seed=0,
                                                restarts=4)
                    exc = None
                except Exception as ex:
                    exc, r = f"{type(ex).__name__}: {ex}", None
                dt = time.time() - t0
                if r is None:
                    with open(OUT, "a", encoding="utf-8") as fh:
                        fh.write(json.dumps(dict(name=name, exp=e, normalize=mode,
                            status="ERROR", error=exc, time=round(dt,1),
                            scale_ratio=ratio, engine_version=ENGINE)) + "\n")
                    print(f"  {name:<11} {mode:<5} ERREUR {exc[:50]}")
                    continue
                v_te = float(np.var(y[te]))
                front, seen = [], set()
                for ent in list(r.pareto or []) + [r]:
                    try: et = _err(ent, X[te], y[te], v_te)
                    except Exception: continue
                    k = (int(ent.size), round(et, 15))
                    if k in seen: continue
                    seen.add(k)
                    front.append({"size": int(ent.size), "err_test": et,
                                  "expr": ent.expression})
                front.sort(key=lambda d: d["size"])
                best = min(front, key=lambda d: d["err_test"])
                pb, sz = best["err_test"], best["size"]
                status = "EXACT" if pb < 1e-9 else ("NEAR" if pb < 1e-3 else "MISS")
                census = _census(best["expr"])
                susp = sorted((set(census) & _SUSPECT) - _expected(formula))
                clean = bool(status == "EXACT" and not susp and sz <= canon + 6)
                with open(OUT, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(dict(
                        name=name, formula=formula, exp=e, scale_ratio=ratio,
                        normalize=mode, status=status, clean_recovery=clean,
                        pareto_best=pb, pb_size=sz, time=round(dt, 1),
                        n_vars=nv, pool=pool, generations=30, restarts=4,
                        speed="fast", seed=0, engine_version=ENGINE,
                        pythonhashseed=os.environ.get("PYTHONHASHSEED"),
                        date=datetime.datetime.now().isoformat(timespec="seconds"),
                        data_hash=hashlib.sha1(X.tobytes()).hexdigest()[:12],
                        expr_full=r.expression, front=front,
                        ops_census=census, suspect_ops=susp)) + "\n")
                print(f"  {name:<11} {mode:<5} {status:<6} pb={pb:.1e} "
                      f"size={sz:<4} ratio={ratio:>10.1f} {dt:5.0f}s")
                sys.stdout.flush()

def bilan():
    if not os.path.exists(OUT):
        print("(pas encore de résultats)"); return
    rows = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r.get("status") != "ERROR"]
    if not rows: print("(rien d'exploitable)"); return
    exps = sorted({r["exp"] for r in rows})
    modes = [m for m in MODES if any(r["normalize"] == m for r in rows)]

    print(f"\n=== LE POINT DE BASCULE (moteur {ENGINE}) ===")
    print(f"{'x10^e':>7}{'ratio médian':>15}" +
          "".join(f"{m+' exactes':>16}" for m in modes) +
          f"{'  verdict'}")
    cross = None
    for e in exps:
        sub = [r for r in rows if r["exp"] == e]
        rat = sorted(r["scale_ratio"] for r in sub)
        med = rat[len(rat)//2]
        cells, sc = [], {}
        for m in modes:
            z = [r for r in sub if r["normalize"] == m]
            k = sum(1 for r in z if r["status"] == "EXACT")
            sc[m] = (k, len(z))
            cells.append(f"{k:>7}/{len(z):<8}")
        verdict = ""
        if "none" in sc and "auto" in sc:
            if sc["none"][0] > sc["auto"][0]: verdict = "none gagne"
            elif sc["auto"][0] > sc["none"][0]:
                verdict = "AUTO gagne"
                if cross is None: cross = med
            else: verdict = "égalité"
        print(f"{e:>7}{med:>15.1f}" + "".join(cells) + f"  {verdict}")

    print(f"\n{'x10^e':>7}{'ratio médian':>15}" +
          "".join(f"{m+' propres':>16}" for m in modes))
    for e in exps:
        sub = [r for r in rows if r["exp"] == e]
        rat = sorted(r["scale_ratio"] for r in sub); med = rat[len(rat)//2]
        cells = []
        for m in modes:
            z = [r for r in sub if r["normalize"] == m]
            k = sum(1 for r in z if r["clean_recovery"])
            cells.append(f"{k:>7}/{len(z):<8}")
        print(f"{e:>7}{med:>15.1f}" + "".join(cells))

    print("\n--- lecture ---")
    if cross is None:
        print("  `auto` ne prend jamais l'avantage sur la plage testée.")
        print("  -> soit le seuil est au-delà de 10^%d, soit `none` est" % max(exps))
        print("     préférable partout ici. Étendre les décades avant de conclure.")
    else:
        print(f"  `auto` prend l'avantage à partir d'un rapport d'échelle")
        print(f"  d'environ {cross:.0f}. C'est le SEUIL à écrire dans")
        print(f"  l'heuristique de `_choose_scaler` :")
        print(f"      si rapport(ecarts-types) < seuil  ->  ne pas normaliser")
        print(f"      sinon                              ->  heuristique actuelle")
        print(f"  Prendre une marge : un seuil un peu SOUS le croisement coûte")
        print(f"  peu (on normalise un peu trop tôt), au-dessus on rate le cas")
        print(f"  que la normalisation devait sauver.")
    print("\nCe banc prépare une modification du MOTEUR : il ne se rapporte pas")
    print("à côté des autres bras, il sert à écrire du code.")

if __name__ == "__main__":
    argv = sys.argv[1:]
    exps = EXPS; modes = MODES
    if "--exps" in argv:  exps = [int(x) for x in argv[argv.index("--exps") + 1].split(",")]
    if "--modes" in argv: modes = argv[argv.index("--modes") + 1].split(",")
    if os.environ.get("PYTHONHASHSEED") != "0":
        print("!! ATTENTION : PYTHONHASHSEED != 0 — relancer avec PYTHONHASHSEED=0.")
    _check_engine()
    if "--bilan" in argv or "--summary" in argv:
        bilan()
    else:
        print(f"=== BANC DU POINT DE BASCULE — décades {exps}, modes {modes} ===")
        print(f"    {len(PROBS)} équations x {len(exps)} décades x {len(modes)} modes "
              f"= {len(PROBS)*len(exps)*len(modes)} runs")
        run(exps, modes)
        bilan()
