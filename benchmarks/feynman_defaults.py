# -*- coding: utf-8 -*-
"""
BANC DES DÉFAUTS — quelle configuration livrer aux utilisateurs ?
==================================================================
POURQUOI CE BANC
----------------
Les défauts sont la configuration la plus utilisée du paquet : la quasi-
totalité des utilisateurs ne changera jamais un paramètre. Or les défauts
actuels n'ont jamais été mesurés, et tous les bancs GP_ELITE décrivent une
configuration différente de celle qui sort de la boîte.

Ce que les bancs précédents ont établi (pools / speed / budget, 210 runs) :
  * les RELANCES dominent : 1 relance = 11/15, >=3 relances = 14/15,
    indépendamment de la population. Le défaut actuel a restarts=1.
  * une longue passe unique produit des expressions ENFLÉES (63 noeuds là
    où 4 relances en donnent 11).
  * `full` ne coûte rien face à `physical` (0 gain, 0 perte, temps x0.99)
    mais couvre 15/15 équations au lieu de 12/15.
  * `normal` est le seul mode où toutes les récupérations sont canoniques.
  * le modèle « individus évalués » ne prédit pas le temps : la population
    est vectorisée (bon marché), la relance a des coûts fixes (chère).

MAIS ces bancs faisaient varier UN cadran en gelant les autres sur les
valeurs des bancs, pas sur les défauts. On ne peut pas en déduire un jeu de
défauts. D'où ce banc : des CONFIGURATIONS COMPLÈTES, en face-à-face.

DEUX DIFFÉRENCES ESSENTIELLES AVEC LES BANCS PRÉCÉDENTS
-------------------------------------------------------
1. `normalize="auto"` et `validation_split=0.20` — les VRAIS défauts, pas
   les réglages de banc. On mesure ce que reçoit un utilisateur.
   (Conséquence attendue : les scores absolus seront plus bas que dans le
   bras `none`. Ce n'est pas le sujet — seul le CLASSEMENT des candidats
   compte ici.)
2. PLUSIEURS GRAINES de moteur (seed=0,1,2), données inchangées. Un écart
   d'une ou deux équations sur 15 est du bruit ; il faut moyenner pour
   décider quoi que ce soit.

PHASE 2 — LE BRUIT
------------------
Un défaut sert d'abord des données réelles. Régler les défauts sur des
données synthétiques propres serait l'erreur classique. La phase 2 rejoue
les mêmes candidats avec 3 % de bruit gaussien, entraînement sur le bruité
et ÉVALUATION CONTRE LA CIBLE PROPRE (protocole de `feynman_noise.py`).
Un candidat qui gagne sur le propre et perd sur le bruité n'est pas un bon
défaut.

Sortie : feyn_defaults.jsonl   |   Reprise automatique.

Lancement :
  set PYTHONHASHSEED=0 && python benchmarks\\feynman_defaults.py
Options :
  --cand current,min_fix   sous-ensemble de candidats
  --seeds 0,1              graines moteur (défaut 0,1,2)
  --phase 1|2|both         (défaut both)
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
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feyn_defaults.jsonl")

R = np.random.RandomState
def U(rng, lo, hi, n): return rng.uniform(lo, hi, n)

# ── candidats : configurations COMPLÈTES ────────────────────────────────────
# chaque entrée = (operators, normalize, generations, speed, restarts,
#                  validation_split, commentaire)
CANDIDATES = {
 "current":  ("physical", "auto", 100, "fast",   1, 0.20,
              "le défaut actuel du paquet — l'existant à battre"),
 "min_fix":  ("physical", "auto",  30, "fast",   4, 0.20,
              "un seul changement : les relances (le cadran dominant)"),
 "pool_fix": ("full",     "auto",  30, "fast",   4, 0.20,
              "+ pool complet : couvre 15/15 équations au lieu de 12/15"),
 "full_fix": ("full",     "auto",  30, "normal", 4, 0.20,
              "+ grosse population : le seul mode 100 % canonique"),
}
ORDER = ["current", "min_fix", "pool_fix", "full_fix"]
NOISE_LEVEL = 0.03          # phase 2 : 3 % de l'écart-type de y

PROBS = [
 (0,  "I.12.1",   "mu*Nn",                     2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1]),
 (1,  "I.12.5",   "q2*Ef",                     2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1]),
 (2,  "I.14.4",   "k*x^2/2",                   2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: 0.5*X[:,0]*X[:,1]**2),
 (3,  "I.39.1",   "(3/2)*pr*V",                2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: 1.5*X[:,0]*X[:,1]),
 (4,  "II.3.24",  "P/(4*pi*r^2)",              2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,3,n)],
   lambda X: X[:,0]/(4*np.pi*X[:,1]**2)),
 (5,  "I.6.20a",  "exp(-th^2/2)/sqrt(2*pi)",   1, lambda r,n: np.c_[U(r,-3,3,n)],
   lambda X: np.exp(-X[:,0]**2/2)/np.sqrt(2*np.pi)),
 (6,  "I.8.14",   "sqrt((x2-x1)^2+(y2-y1)^2)", 4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: np.sqrt((X[:,1]-X[:,0])**2+(X[:,3]-X[:,2])**2)),
 (7,  "I.16.6",   "(u+v)/(1+u*v/c^2)",         3, lambda r,n: np.c_[U(r,1,2,n),U(r,1,2,n),U(r,3,10,n)],
   lambda X: (X[:,0]+X[:,1])/(1+X[:,0]*X[:,1]/X[:,2]**2)),
 (8,  "I.27.6",   "1/(1/d1+n/d2)",             3, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,2,n)],
   lambda X: 1.0/(1.0/X[:,0]+X[:,2]/X[:,1])),
 (9,  "I.34.8",   "q*v*B/p",                   4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1]*X[:,2]/X[:,3]),
 (10, "I.43.16",  "mu*q*V/d",                  4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1]*X[:,2]/X[:,3]),
 (11, "I.12.2",   "q1*q2/(4*pi*eps*r^2)",      4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,3,n),U(r,1,3,n)],
   lambda X: X[:,0]*X[:,1]/(4*np.pi*X[:,2]*X[:,3]**2)),
 (12, "II.15.4",  "-mu*B*cos(th)",             3, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,0,6.28,n)],
   lambda X: -X[:,0]*X[:,1]*np.cos(X[:,2])),
 (13, "I.18.12",  "r*F*sin(th)",               3, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,0,3.14,n)],
   lambda X: X[:,0]*X[:,1]*np.sin(X[:,2])),
 (14, "III.15.12","2*U*(1-cos(k*d))",          3, lambda r,n: np.c_[U(r,1,5,n),U(r,0.5,2,n),U(r,0.5,2,n)],
   lambda X: 2*X[:,0]*(1-np.cos(X[:,1]*X[:,2]))),
]
CANON = {"I.12.1":3,"I.12.5":3,"I.14.4":7,"I.39.1":5,"II.3.24":6,"I.6.20a":8,
         "I.8.14":10,"I.16.6":13,"I.27.6":9,"I.34.8":7,"I.43.16":7,"I.12.2":11,
         "II.15.4":7,"I.18.12":7,"III.15.12":10}

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

def _done():
    if not os.path.exists(OUT): return set()
    ks = set()
    for line in open(OUT, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        try:
            r = json.loads(line)
            ks.add((r["phase"], r["cand"], r["name"], r["engine_seed"]))
        except Exception: pass
    return ks

def _check_engine():
    print(f"gp_elite {ENGINE}  <-  {os.path.abspath(gp_elite.__file__)}")
    if ENGINE != EXPECTED_ENGINE:
        print(f"\n!! ARRÊT : moteur {ENGINE}, attendu {EXPECTED_ENGINE}.")
        print("   Passer outre volontairement : --force")
        if "--force" not in sys.argv: sys.exit(1)

def one(phase, cand, idx, name, formula, nv, sampler, f, eseed, done):
    if (phase, cand, name, eseed) in done: return None
    pool, norm, gens, speed, rst, vsplit, _ = CANDIDATES[cand]
    rng = R(1000 + idx)
    X = sampler(rng, 200); y_clean = f(X)
    if phase == "2":
        nrng = R(777 + idx)
        y_train_src = y_clean + nrng.normal(0.0, NOISE_LEVEL * float(np.std(y_clean)),
                                            size=y_clean.shape)
    else:
        y_train_src = y_clean
    perm = rng.permutation(200); tr, te = perm[:140], perm[140:]
    names = [f"v{k}" for k in range(nv)]
    t0 = time.time()
    with contextlib.redirect_stdout(io.StringIO()):
        r = symbolic_regression(X[tr], y_train_src[tr], feature_names=names,
                                operators=pool, normalize=norm,
                                generations=gens, speed=speed,
                                validation_split=vsplit, seed=eseed,
                                restarts=rst)
    dt = time.time() - t0
    # ÉVALUATION TOUJOURS CONTRE LA CIBLE PROPRE
    v_te = float(np.var(y_clean[te]))
    front, seen = [], set()
    for e in list(r.pareto or []) + [r]:
        try: et = _err(e, X[te], y_clean[te], v_te)
        except Exception: continue
        k = (int(e.size), round(et, 15))
        if k in seen: continue
        seen.add(k)
        front.append({"size": int(e.size), "err_clean": et, "expr": e.expression})
    front.sort(key=lambda d: d["size"])
    best = min(front, key=lambda d: d["err_clean"])
    pb, sz = best["err_clean"], best["size"]
    # seuil adapté : à bruit non nul, 1e-9 est inatteignable
    thr = 1e-9 if phase == "1" else (NOISE_LEVEL ** 2) / 10.0
    status = "EXACT" if pb < thr else ("NEAR" if pb < 1e-3 else "MISS")
    census = _census(best["expr"])
    susp = sorted((set(census) & _SUSPECT) - _expected(formula))
    clean = bool(status == "EXACT" and not susp and sz <= CANON.get(name, 99) + 4)
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(
            phase=phase, cand=cand, name=name, formula=formula,
            engine_seed=eseed, noise=(NOISE_LEVEL if phase == "2" else 0.0),
            operators=pool, normalize=norm, generations=gens, speed=speed,
            restarts=rst, validation_split=vsplit, threshold=thr,
            status=status, clean_recovery=clean, pareto_best=pb, pb_size=sz,
            time=round(dt, 1), n_vars=nv, engine_version=ENGINE,
            pythonhashseed=os.environ.get("PYTHONHASHSEED"),
            date=datetime.datetime.now().isoformat(timespec="seconds"),
            data_hash=hashlib.sha1(X.tobytes()).hexdigest()[:12],
            expr_full=r.expression, front=front,
            ops_census=census, suspect_ops=susp)) + "\n")
    return status, clean, dt, sz

def run(cands, seeds, phases):
    done = _done()
    for phase in phases:
        lbl = "propre" if phase == "1" else f"bruité {NOISE_LEVEL:.0%}"
        print(f"\n########## PHASE {phase} — données {lbl} ##########")
        for cand in cands:
            pool, norm, gens, speed, rst, vs, note = CANDIDATES[cand]
            print(f"\n=== '{cand}' : {pool}/{norm}/{gens}g/{speed}/r={rst}"
                  f"/val={vs} — {note}")
            for eseed in seeds:
                ok = cl = 0; tt = 0.0; n = 0
                for idx, name, formula, nv, sampler, f in PROBS:
                    res = one(phase, cand, idx, name, formula, nv, sampler, f,
                              eseed, done)
                    if res is None:
                        continue
                    st, c, dt, sz = res
                    n += 1; tt += dt
                    if st == "EXACT": ok += 1
                    if c: cl += 1
                if n:
                    print(f"   graine {eseed} : {ok}/{n} exactes, {cl} propres, "
                          f"{tt:.0f}s")
                else:
                    print(f"   graine {eseed} : déjà fait — repris")
                sys.stdout.flush()

def bilan():
    if not os.path.exists(OUT):
        print("(pas encore de résultats)"); return
    rows = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    for phase in sorted({r["phase"] for r in rows}):
        sub = [r for r in rows if r["phase"] == phase]
        lbl = "PROPRE" if phase == "1" else f"BRUITÉ {NOISE_LEVEL:.0%}"
        cands = [c for c in ORDER if any(r["cand"] == c for r in sub)]
        seeds = sorted({r["engine_seed"] for r in sub})
        print(f"\n=== PHASE {phase} — données {lbl} "
              f"({len(seeds)} graine(s) : {seeds}) ===")
        print(f"{'candidat':<10}{'config':<34}"
              + "".join(f"{'s'+str(s):>7}" for s in seeds)
              + f"{'moyenne':>10}{'propres':>10}{'temps':>9}")
        stats = {}
        for c in cands:
            pool, norm, gens, speed, rst, vs, _ = CANDIDATES[c]
            cfg = f"{pool}/{gens}g/{speed}/r{rst}"
            per = []
            for s in seeds:
                z = [r for r in sub if r["cand"] == c and r["engine_seed"] == s]
                per.append(sum(1 for r in z if r["status"] == "EXACT"))
            z = [r for r in sub if r["cand"] == c]
            cl = sum(1 for r in z if r["clean_recovery"]) / max(len(seeds), 1)
            t = sum(r["time"] for r in z) / max(len(seeds), 1)
            m = sum(per) / max(len(per), 1)
            stats[c] = (m, cl, t, per)
            print(f"{c:<10}{cfg:<34}" + "".join(f"{p:>7}" for p in per)
                  + f"{m:>10.1f}{cl:>10.1f}{t:>8.0f}s")
        if "current" in stats:
            base = stats["current"]
            print(f"\n  écart au défaut actuel (sur 15 équations, moyenne des graines) :")
            for c in cands:
                if c == "current": continue
                m, cl, t, _ = stats[c]
                d = m - base[0]; dc = cl - base[1]; rt = t / max(base[2], 1e-9)
                verdict = ("gain net" if d >= 1.5 else
                           "gain marginal" if d >= 0.5 else
                           "équivalent" if d > -0.5 else "recul")
                print(f"    {c:<10} {d:+5.1f} exactes  {dc:+5.1f} propres  "
                      f"temps x{rt:.2f}   -> {verdict}")
            print("\n  Rappel : un écart inférieur à ~1.5 équation n'est pas")
            print("  significatif avec ce nombre de graines. Ne change pas un")
            print("  défaut pour un gain marginal.")
    ph = {r["phase"] for r in rows}
    if {"1", "2"} <= ph:
        print("\n=== COHÉRENCE propre / bruité ===")
        for c in ORDER:
            a = [r for r in rows if r["phase"] == "1" and r["cand"] == c]
            b = [r for r in rows if r["phase"] == "2" and r["cand"] == c]
            if not a or not b: continue
            sa = sum(1 for r in a if r["status"] == "EXACT") / len({r["engine_seed"] for r in a})
            sb = sum(1 for r in b if r["status"] == "EXACT") / len({r["engine_seed"] for r in b})
            print(f"  {c:<10} propre {sa:>4.1f}/15   bruité {sb:>4.1f}/15   "
                  f"chute {sa-sb:+.1f}")
        print("\n  Un candidat qui gagne sur le propre et chute sur le bruité")
        print("  n'est PAS un bon défaut : les données réelles ont du bruit.")

if __name__ == "__main__":
    argv = sys.argv[1:]
    cands = ORDER; seeds = [0, 1, 2]; phases = ["1", "2"]
    if "--cand" in argv:  cands = argv[argv.index("--cand") + 1].split(",")
    if "--seeds" in argv: seeds = [int(x) for x in argv[argv.index("--seeds") + 1].split(",")]
    if "--phase" in argv:
        p = argv[argv.index("--phase") + 1]
        phases = ["1", "2"] if p == "both" else [p]
    if os.environ.get("PYTHONHASHSEED") != "0":
        print("!! ATTENTION : PYTHONHASHSEED != 0 — relancer avec PYTHONHASHSEED=0.")
    _check_engine()
    if "--bilan" in argv or "--summary" in argv:
        bilan()
    else:
        print("=== BANC DES DÉFAUTS ===")
        print("    on mesure ce que reçoit un UTILISATEUR : normalize='auto',")
        print("    validation_split=0.20 — pas les réglages de banc.")
        for c in cands:
            pool, norm, gens, speed, rst, vs, note = CANDIDATES[c]
            print(f"    {c:<10} {pool}/{norm}/{gens}g/{speed}/r={rst}  — {note}")
        run(cands, seeds, phases)
        bilan()
