# -*- coding: utf-8 -*-
"""
BANC DE SCALING — enveloppe de fonctionnement en TAILLE DE DONNÉES
===================================================================
Objet : vérifier l'affirmation du README — « built for small experimental
datasets (<=10 variables, 100-5000 points) ». Aujourd'hui le banc Feynman
tourne à N=200, soit UN seul point à l'intérieur de la plage annoncée ;
les deux bornes (100 et 5000) ne sont pas mesurées.

Ce banc balaie N de 25 à 10000 — délibérément EN DEÇÀ et AU-DELÀ de la
plage annoncée — sur un sous-ensemble représentatif d'équations Feynman,
et mesure : récupération, propreté de la forme, et temps.

Question ouverte que ce banc tranche :
  hypothèse A « plus de données => résultats dégradés » (intuition initiale)
  hypothèse B « plus de données => récupération meilleure, coût en hausse »
Sondages préliminaires (conteneur, 0.6.0) : I.14.4 exacte et PLUS RAPIDE à
N=3200 qu'à N=200 ; I.16.6 passe de 4.1e-3 (MISS) à 3.8e-4 (NEAR) entre
N=200 et N=1000, en 93 s contre 116 s. => hypothèse B favorisée, à
confirmer sur machine de référence.

PROTOCOLE — identique au banc Feynman SAUF la taille :
  normalize="none", operators=pool d'origine, generations=30, speed="fast",
  validation_split=0.15, seed=0, restarts=4, split 70/30.
  Un seul paramètre varie : N. (Le bras « none » sert de contrôle car il
  isole l'effet TAILLE ; le bras « auto », défaut du moteur, pourra faire
  l'objet d'un second passage avec --arm auto.)

  Répétitions : 3 tirages indépendants pour N <= 200 (la variance est
  maximale à petit N et le coût y est négligeable), 1 au-delà.

Sortie : feyn_scaling.jsonl — télémétrie v2 (même esprit que le bras units)
Reprise : relancer reprend là où le script s'est arrêté.

Lancement :
  Windows :  set PYTHONHASHSEED=0 && python benchmarks\\feynman_scaling.py
  Linux   :  PYTHONHASHSEED=0 python3 benchmarks/feynman_scaling.py
Options :
  --arm none|auto      bras de normalisation (défaut : none)
  --sizes 25,100,1000  grille de tailles personnalisée
  --eq I.16.6,I.12.1   sous-ensemble d'équations
  --bilan              bilan seul depuis le jsonl
"""
import os, sys, json, time, io, re, contextlib, hashlib, datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

EXPECTED_ENGINE = "0.6.0"

# La racine du dépôt passe AVANT tout : sinon un gp_elite installé par pip
# (potentiellement plus ancien) masque la copie du dépôt.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.isdir(os.path.join(_ROOT, "gp_elite")):
    sys.path.insert(0, _ROOT)

import gp_elite
from gp_elite import symbolic_regression
import numpy as np

ENGINE = getattr(gp_elite, "__version__", "?")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feyn_scaling.jsonl")

R = np.random.RandomState
def U(rng, lo, hi, n): return rng.uniform(lo, hi, n)

# ── grille de tailles ───────────────────────────────────────────────────────
# 25 et 50  : SOUS la borne basse annoncée (100)
# 100..5000 : la plage annoncée par le README
# 10000     : AU-DELÀ de la borne haute annoncée
SIZES = [25, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
CLAIM_LO, CLAIM_HI = 100, 5000
REPEATS_SMALL, SMALL_N = 3, 200      # 3 tirages si N <= 200, sinon 1

# ── sous-ensemble représentatif (indices = ceux du banc Feynman) ────────────
# choisi pour couvrir les paliers de difficulté observés :
#   I.12.1    produit trivial, 2 vars           — plancher de référence
#   I.8.14    4 vars, différences internes      — le motif pythagoricien
#   III.15.12 trig, cosinus d'un produit        — famille trig
#   I.12.2    4 vars, 1/(4 pi eps r^2)          — sujette au « tangle »
#   I.16.6    rationnelle imbriquée             — le point dur du banc
PROBS = [
 (0,  "I.12.1",   "mu*Nn",                     2,
   lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1], "physical"),
 (6,  "I.8.14",   "sqrt((x2-x1)^2+(y2-y1)^2)", 4,
   lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: np.sqrt((X[:,1]-X[:,0])**2+(X[:,3]-X[:,2])**2), "physical"),
 (14, "III.15.12","2*U*(1-cos(k*d))",          3,
   lambda r,n: np.c_[U(r,1,5,n),U(r,0.5,2,n),U(r,0.5,2,n)],
   lambda X: 2*X[:,0]*(1-np.cos(X[:,1]*X[:,2])), "trig"),
 (11, "I.12.2",   "q1*q2/(4*pi*eps*r^2)",      4,
   lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,3,n),U(r,1,3,n)],
   lambda X: X[:,0]*X[:,1]/(4*np.pi*X[:,2]*X[:,3]**2), "physical"),
 (7,  "I.16.6",   "(u+v)/(1+u*v/c^2)",         3,
   lambda r,n: np.c_[U(r,1,2,n),U(r,1,2,n),U(r,3,10,n)],
   lambda X: (X[:,0]+X[:,1])/(1+X[:,0]*X[:,1]/X[:,2]**2), "physical"),
]

# taille de la forme littérale (pour juger la « propreté » d'une récupération)
CANON_SIZE = {"I.12.1": 3, "I.8.14": 10, "III.15.12": 10,
              "I.12.2": 11, "I.16.6": 13}

_OPS = ("sin","cos","tanh","tan","exp","log","sqrt","abs","pow")
_SUSPECT = {"sin","cos","tanh","tan","exp","log","sqrt"}

def _census(expr):
    c = {}
    for op in _OPS:
        k = len(re.findall(r"\b%s\s*\(" % op, expr))
        if op == "tan":
            k -= len(re.findall(r"\btanh\s*\(", expr))
        if k: c[op] = k
    sq = expr.count("\u00b2")
    if sq: c["square"] = sq
    return c

def _expected(formula):
    return set(re.findall(r"\b(sin|cos|tanh|tan|exp|log|sqrt|abs)\b", formula))

def _err(e, X, y, var):
    return float(np.mean((e.predict(X) - y) ** 2) / var)

def _done():
    if not os.path.exists(OUT): return set()
    keys = set()
    with open(OUT, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try:
                r = json.loads(line)
                keys.add((r["name"], r["n_total"], r["rep"], r["arm"]))
            except Exception: pass
    return keys

def _check_engine():
    print(f"gp_elite {ENGINE}  <-  {os.path.abspath(gp_elite.__file__)}")
    if ENGINE != EXPECTED_ENGINE:
        print(f"\n!! ARRÊT : moteur {ENGINE}, attendu {EXPECTED_ENGINE}.")
        print("   Le scaling doit tourner sur la MÊME version que les autres")
        print("   bancs, sinon les comparaisons n'ont aucune valeur.")
        print("   Le chemin ci-dessus pointe-t-il vers ton dépôt ou vers")
        print("   site-packages ? Passer outre volontairement : --force")
        if "--force" not in sys.argv:
            sys.exit(1)
        print("   (--force : on continue malgré tout)\n")

# ── boucle ──────────────────────────────────────────────────────────────────
def run(sizes, eq_filter, arm):
    done = _done()
    for idx, name, formula, nv, sampler, f, pool in PROBS:
        if eq_filter and name not in eq_filter:
            continue
        print(f"\n--- {name}   {formula}")
        for N in sizes:
            reps = REPEATS_SMALL if N <= SMALL_N else 1
            for rep in range(reps):
                if (name, N, rep, arm) in done:
                    print(f"  N={N:<6} rep={rep}  déjà fait — repris")
                    continue
                # graine : celle du banc pour rep=0, décalée ensuite
                rng = R(1000 + idx + 10000 * rep)
                X = sampler(rng, N); y = f(X)
                ntr = int(round(0.7 * N))
                perm = rng.permutation(N); tr, te = perm[:ntr], perm[ntr:]
                dhash = hashlib.sha1(X.tobytes()).hexdigest()[:12]
                yhash = hashlib.sha1(y.tobytes()).hexdigest()[:12]
                names = [f"v{k}" for k in range(nv)]
                t0 = time.time()
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        r = symbolic_regression(
                            X[tr], y[tr], feature_names=names, operators=pool,
                            normalize=arm, generations=30, speed="fast",
                            validation_split=0.15, seed=0, restarts=4)
                    err_run = None
                except Exception as exc:                    # on n'arrête pas le banc
                    err_run = f"{type(exc).__name__}: {exc}"
                    r = None
                dt = time.time() - t0

                if r is None:
                    rec = dict(name=name, n_total=N, rep=rep, arm=arm,
                               status="ERROR", error=err_run, time=round(dt,1),
                               engine_version=ENGINE)
                    with open(OUT, "a", encoding="utf-8") as fh:
                        fh.write(json.dumps(rec) + "\n")
                    print(f"  N={N:<6} rep={rep}  ERREUR  {err_run[:60]}")
                    continue

                v_te = float(np.var(y[te])); v_tr = float(np.var(y[tr]))
                champ_te = _err(r, X[te], y[te], v_te)
                front, seen = [], set()
                for e in list(r.pareto or []) + [r]:
                    try: e_te = _err(e, X[te], y[te], v_te)
                    except Exception: continue
                    k = (int(e.size), round(e_te, 15))
                    if k in seen: continue
                    seen.add(k)
                    front.append({"size": int(e.size), "err_test": e_te,
                                  "err_train": _err(e, X[tr], y[tr], v_tr),
                                  "expr": e.expression})
                front.sort(key=lambda d: d["size"])
                pbe = min(front, key=lambda d: d["err_test"])
                pb, pb_size = pbe["err_test"], pbe["size"]
                status = ("EXACT" if pb < 1e-9 else
                          "NEAR" if pb < 1e-3 else "MISS")
                census = _census(pbe["expr"])
                suspects = sorted((set(census) & _SUSPECT) - _expected(formula))
                clean = bool(status == "EXACT" and not suspects
                             and pb_size <= CANON_SIZE.get(name, 99) + 4)

                rec = dict(
                    name=name, formula=formula, n_total=N, rep=rep, arm=arm,
                    status=status, clean_recovery=clean,
                    one_minus_r2=champ_te, pareto_best=pb, pb_size=pb_size,
                    time=round(dt, 1),
                    in_readme_claim=bool(CLAIM_LO <= N <= CLAIM_HI),
                    n_train=ntr, n_test=N - ntr, n_vars=nv, pool=pool,
                    engine_version=ENGINE,
                    pythonhashseed=os.environ.get("PYTHONHASHSEED"),
                    date=datetime.datetime.now().isoformat(timespec="seconds"),
                    seed=0, restarts=4, generations=30, speed="fast",
                    validation_split=0.15, normalize=arm,
                    X_hash=dhash, y_hash=yhash,
                    expr_full=r.expression, front=front,
                    ops_census=census, suspect_ops=suspects,
                    ops_suspects=bool(suspects),
                )
                with open(OUT, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec) + "\n")
                mark = "propre" if clean else ("" if status != "EXACT" else "non-canonique")
                print(f"  N={N:<6} rep={rep}  {status:<6} pb={pb:.1e} "
                      f"size={pb_size:<4} {dt:6.1f}s  {mark}")
                sys.stdout.flush()

# ── bilan ───────────────────────────────────────────────────────────────────
def bilan():
    if not os.path.exists(OUT):
        print("(pas encore de résultats)"); return
    rows = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r.get("status") != "ERROR"]
    if not rows:
        print("(aucun résultat exploitable)"); return
    sizes = sorted({r["n_total"] for r in rows})
    names = [p[1] for p in PROBS if any(r["name"] == p[1] for r in rows)]

    print(f"\n=== SCALING — statut par équation et par taille "
          f"(moteur {ENGINE}) ===")
    print("    (E=EXACT propre, e=EXACT non-canonique, N=NEAR, M=MISS ; "
          "| = bornes annoncées du README)")
    hdr = "équation   "
    for N in sizes:
        hdr += ("|" if N == CLAIM_LO else " ") + f"{N:>6}"
        if N == CLAIM_HI: hdr += "|"
    print(hdr)
    for nm in names:
        line = f"{nm:<11}"
        for N in sizes:
            sub = [r for r in rows if r["name"] == nm and r["n_total"] == N]
            if not sub:
                cell = "  -"
            else:
                cs = []
                for r in sub:
                    cs.append("E" if r.get("clean_recovery") else
                              "e" if r["status"] == "EXACT" else
                              "N" if r["status"] == "NEAR" else "M")
                cell = "".join(cs)
            line += ("|" if N == CLAIM_LO else " ") + f"{cell:>6}"
            if N == CLAIM_HI: line += "|"
        print(line)

    print(f"\n=== taux de récupération et coût par taille ===")
    print(f"{'N':>7}  {'exactes':>9}  {'propres':>9}  {'temps méd.':>11}  README")
    for N in sizes:
        sub = [r for r in rows if r["n_total"] == N]
        if not sub: continue
        ex = sum(1 for r in sub if r["status"] == "EXACT")
        cl = sum(1 for r in sub if r.get("clean_recovery"))
        ts = sorted(r["time"] for r in sub)
        med = ts[len(ts)//2]
        inside = "dans la plage" if CLAIM_LO <= N <= CLAIM_HI else "HORS plage"
        print(f"{N:>7}  {ex:>4}/{len(sub):<4}  {cl:>4}/{len(sub):<4}  "
              f"{med:>9.1f}s  {inside}")

    lo = [r for r in rows if r["n_total"] < CLAIM_LO]
    hi = [r for r in rows if r["n_total"] > CLAIM_HI]
    print("\n--- lecture pour le README ---")
    if lo:
        e = sum(1 for r in lo if r["status"] == "EXACT")
        print(f"  sous la borne basse ({CLAIM_LO}) : {e}/{len(lo)} exactes "
              f"-> la borne basse est-elle justifiée ?")
    if hi:
        e = sum(1 for r in hi if r["status"] == "EXACT")
        t = sorted(r["time"] for r in hi)[len(hi)//2]
        print(f"  au-dessus de la borne haute ({CLAIM_HI}) : {e}/{len(hi)} "
              f"exactes, temps médian {t:.0f}s -> la borne haute est-elle "
              f"une limite de qualité, de temps, ou aucune des deux ?")
    print("\nCe banc mesure l'effet de la TAILLE seule (bras "
          f"'{rows[0]['normalize']}'). Il ne remplace ni le banc gelé ni les "
          "bras none/units.")

if __name__ == "__main__":
    argv = sys.argv[1:]
    arm = "none"; sizes = SIZES; eqs = None
    if "--arm" in argv:   arm = argv[argv.index("--arm") + 1]
    if "--sizes" in argv: sizes = [int(x) for x in argv[argv.index("--sizes") + 1].split(",")]
    if "--eq" in argv:    eqs = set(argv[argv.index("--eq") + 1].split(","))
    if os.environ.get("PYTHONHASHSEED") != "0":
        print("!! ATTENTION : PYTHONHASHSEED != 0 — relancer avec "
              "PYTHONHASHSEED=0 pour la reproductibilité.")
    _check_engine()
    if "--bilan" in argv or "--summary" in argv:
        bilan()
    else:
        print(f"=== BANC DE SCALING — bras '{arm}', tailles {sizes} ===")
        print(f"    plage annoncée par le README : {CLAIM_LO}-{CLAIM_HI} points")
        run(sizes, eqs, arm)
        bilan()
