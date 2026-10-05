# -*- coding: utf-8 -*-
"""
BANC D'ALLOCATION DU BUDGET — comment dépenser le calcul, et quel défaut choisir
================================================================================
LE CONSTAT QUI MOTIVE CE BANC
-----------------------------
Valeurs par défaut réelles de `symbolic_regression()` (api.py, l.205+) :
    generations=100, restarts=1, validation_split=0.20, speed="fast"
Valeurs utilisées par TOUS les bancs GP_ELITE à ce jour :
    generations=30,  restarts=4, validation_split=0.15, speed="fast"

=> L'enveloppe mesurée du moteur (14/15 Feynman, gain de débruitage x140,
   formes canoniques a partir de ~500 points, Nikuradse) décrit une
   configuration QU'AUCUN UTILISATEUR NE RECOIT PAR DEFAUT.

Ce banc compare les deux, et le fait dans le cadre général de la question :
à budget de calcul CONSTANT, comment le répartir entre les trois cadrans ?

    budget ~= (individus par génération) x générations x relances

    speed  : ultrafast=300, fast=900, normal=2400 individus/génération
    générations : chercher plus PROFOND (une population qui évolue longtemps)
    relances    : chercher plus SOUVENT (repartir de zéro, éviter un optimum
                  local, mais perdre l'acquis à chaque fois)

Budget de référence : 90 000 individus = celui du DÉFAUT ACTUEL.

ALLOCATIONS COMPARÉES (toutes à ~90 000, sauf `bench` signalé) :
    default    fast      x100 gén. x1  relance   =  90 000   <- le défaut réel
    bench      fast      x 30 gén. x4  relances  = 108 000   <- nos bancs (+20 %)
    equilibre  fast      x 50 gén. x2  relances  =  90 000
    largeur    fast      x 10 gén. x10 relances  =  90 000
    population normal    x 38 gén. x1  relance   =  91 200
    petite_pop ultrafast x100 gén. x3  relances  =  90 000

HYPOTHÈSE À TESTER (folklore de la programmation génétique, et intuition
du mainteneur) : à budget égal, les générations paient mieux que la
population. Si elle se confirme, `default` doit battre `population`.
Question ouverte symétrique : `default` (tout en profondeur) bat-il `bench`
(réparti) ? C'est cela qui décidera du futur défaut.

PROTOCOLE — tout le reste est gelé et identique aux autres bancs :
  operators = pool d'origine, normalize="none", validation_split=0.15,
  seed=0, split 140/60, mêmes graines RandomState(1000+i).
  SEUL le triplet (speed, generations, restarts) varie.

Sortie : feyn_budget.jsonl   |   Reprise automatique.

Lancement :
  set "PYTHONHASHSEED=0" && python benchmarks\\feynman_budget.py
Options :
  --alloc default,bench     sous-ensemble d'allocations
  --eq I.16.6,I.12.2        sous-ensemble d'équations
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
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feyn_budget.jsonl")

R = np.random.RandomState
def U(rng, lo, hi, n): return rng.uniform(lo, hi, n)

PER_GEN = {"ultrafast": 300, "fast": 900, "normal": 2400}

# nom -> (speed, generations, restarts, commentaire)
ALLOCS = {
    "default":    ("fast",      100,  1, "le défaut actuel du paquet"),
    "bench":      ("fast",       30,  4, "la config de tous nos bancs (+20 % budget)"),
    "equilibre":  ("fast",       50,  2, "réparti"),
    "largeur":    ("fast",       10, 10, "tout en relances"),
    "population": ("normal",     38,  1, "grosse population, une passe"),
    "petite_pop": ("ultrafast", 100,  3, "petite population, plus de passes"),
}
ORDER = ["default", "bench", "equilibre", "largeur", "population", "petite_pop"]

PROBS = [
 (0,  "I.12.1",   "mu*Nn",                     2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1], "physical"),
 (1,  "I.12.5",   "q2*Ef",                     2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1], "physical"),
 (2,  "I.14.4",   "k*x^2/2",                   2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: 0.5*X[:,0]*X[:,1]**2, "physical"),
 (3,  "I.39.1",   "(3/2)*pr*V",                2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: 1.5*X[:,0]*X[:,1], "physical"),
 (4,  "II.3.24",  "P/(4*pi*r^2)",              2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,3,n)],
   lambda X: X[:,0]/(4*np.pi*X[:,1]**2), "physical"),
 (5,  "I.6.20a",  "exp(-th^2/2)/sqrt(2*pi)",   1, lambda r,n: np.c_[U(r,-3,3,n)],
   lambda X: np.exp(-X[:,0]**2/2)/np.sqrt(2*np.pi), "physical"),
 (6,  "I.8.14",   "sqrt((x2-x1)^2+(y2-y1)^2)", 4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: np.sqrt((X[:,1]-X[:,0])**2+(X[:,3]-X[:,2])**2), "physical"),
 (7,  "I.16.6",   "(u+v)/(1+u*v/c^2)",         3, lambda r,n: np.c_[U(r,1,2,n),U(r,1,2,n),U(r,3,10,n)],
   lambda X: (X[:,0]+X[:,1])/(1+X[:,0]*X[:,1]/X[:,2]**2), "physical"),
 (8,  "I.27.6",   "1/(1/d1+n/d2)",             3, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,2,n)],
   lambda X: 1.0/(1.0/X[:,0]+X[:,2]/X[:,1]), "physical"),
 (9,  "I.34.8",   "q*v*B/p",                   4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1]*X[:,2]/X[:,3], "physical"),
 (10, "I.43.16",  "mu*q*V/d",                  4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1]*X[:,2]/X[:,3], "physical"),
 (11, "I.12.2",   "q1*q2/(4*pi*eps*r^2)",      4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,3,n),U(r,1,3,n)],
   lambda X: X[:,0]*X[:,1]/(4*np.pi*X[:,2]*X[:,3]**2), "physical"),
 (12, "II.15.4",  "-mu*B*cos(th)",             3, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,0,6.28,n)],
   lambda X: -X[:,0]*X[:,1]*np.cos(X[:,2]), "trig"),
 (13, "I.18.12",  "r*F*sin(th)",               3, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,0,3.14,n)],
   lambda X: X[:,0]*X[:,1]*np.sin(X[:,2]), "trig"),
 (14, "III.15.12","2*U*(1-cos(k*d))",          3, lambda r,n: np.c_[U(r,1,5,n),U(r,0.5,2,n),U(r,0.5,2,n)],
   lambda X: 2*X[:,0]*(1-np.cos(X[:,1]*X[:,2])), "trig"),
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
            r = json.loads(line); ks.add((r["alloc"], r["name"]))
        except Exception: pass
    return ks

def _check_engine():
    print(f"gp_elite {ENGINE}  <-  {os.path.abspath(gp_elite.__file__)}")
    if ENGINE != EXPECTED_ENGINE:
        print(f"\n!! ARRÊT : moteur {ENGINE}, attendu {EXPECTED_ENGINE}.")
        print("   Passer outre volontairement : --force")
        if "--force" not in sys.argv: sys.exit(1)

def run(allocs, eq_filter):
    done = _done()
    for alloc in allocs:
        speed, gens, rst, note = ALLOCS[alloc]
        budget = PER_GEN[speed] * gens * rst
        print(f"\n=== allocation '{alloc}' — {speed} x{gens} gén. x{rst} relance(s) "
              f"= {budget:,} individus — {note} ===".replace(",", " "))
        for idx, name, formula, nv, sampler, f, pool in PROBS:
            if eq_filter and name not in eq_filter: continue
            if (alloc, name) in done:
                print(f"  {name:<11} déjà fait — repris"); continue
            rng = R(1000 + idx)
            X = sampler(rng, 200); y = f(X)
            perm = rng.permutation(200); tr, te = perm[:140], perm[140:]
            names = [f"v{k}" for k in range(nv)]
            t0 = time.time()
            with contextlib.redirect_stdout(io.StringIO()):
                r = symbolic_regression(X[tr], y[tr], feature_names=names,
                                        operators=pool, normalize="none",
                                        generations=gens, speed=speed,
                                        validation_split=0.15, seed=0,
                                        restarts=rst)
            dt = time.time() - t0
            v_te = float(np.var(y[te])); v_tr = float(np.var(y[tr]))
            front, seen = [], set()
            for e in list(r.pareto or []) + [r]:
                try: et = _err(e, X[te], y[te], v_te)
                except Exception: continue
                k = (int(e.size), round(et, 15))
                if k in seen: continue
                seen.add(k)
                front.append({"size": int(e.size), "err_test": et,
                              "err_train": _err(e, X[tr], y[tr], v_tr),
                              "expr": e.expression})
            front.sort(key=lambda d: d["size"])
            best = min(front, key=lambda d: d["err_test"])
            pb, sz = best["err_test"], best["size"]
            status = "EXACT" if pb < 1e-9 else ("NEAR" if pb < 1e-3 else "MISS")
            census = _census(best["expr"])
            susp = sorted((set(census) & _SUSPECT) - _expected(formula))
            clean = bool(status == "EXACT" and not susp
                         and sz <= CANON.get(name, 99) + 4)
            with open(OUT, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(dict(
                    alloc=alloc, name=name, formula=formula,
                    speed=speed, generations=gens, restarts=rst,
                    budget=budget, per_gen=PER_GEN[speed],
                    status=status, clean_recovery=clean,
                    pareto_best=pb, pb_size=sz, time=round(dt, 1),
                    one_minus_r2=_err(r, X[te], y[te], v_te),
                    n_vars=nv, pool=pool, normalize="none",
                    validation_split=0.15, seed=0, engine_version=ENGINE,
                    pythonhashseed=os.environ.get("PYTHONHASHSEED"),
                    date=datetime.datetime.now().isoformat(timespec="seconds"),
                    data_hash=hashlib.sha1(X.tobytes()).hexdigest()[:12],
                    expr_full=r.expression, front=front,
                    ops_census=census, suspect_ops=susp)) + "\n")
            mark = "propre" if clean else ("" if status != "EXACT" else "non-canonique")
            print(f"  {name:<11} {status:<6} pb={pb:.1e} size={sz:<4} "
                  f"{dt:6.0f}s  {mark}")
            sys.stdout.flush()

def bilan():
    if not os.path.exists(OUT):
        print("(pas encore de résultats)"); return
    rows = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    allocs = [a for a in ORDER if any(r["alloc"] == a for r in rows)]

    print(f"\n=== MATRICE équation x allocation (moteur {ENGINE}) ===")
    print("    E=exact propre · e=exact non-canonique · N=near · M=miss")
    print(f"{'équation':<11}" + "".join(f"{a:>12}" for a in allocs))
    for _, name, *_ in PROBS:
        line = f"{name:<11}"
        for a in allocs:
            s = [r for r in rows if r["name"] == name and r["alloc"] == a]
            c = "-" if not s else ("E" if s[0]["clean_recovery"] else
                 "e" if s[0]["status"] == "EXACT" else
                 "N" if s[0]["status"] == "NEAR" else "M")
            line += f"{c:>12}"
        print(line)

    print(f"\n=== classement à budget ~constant ===")
    print(f"{'allocation':<12}{'config':<22}{'budget':>10}{'exactes':>10}"
          f"{'propres':>10}{'temps':>10}")
    res = []
    for a in allocs:
        s = [r for r in rows if r["alloc"] == a]
        ex = sum(1 for r in s if r["status"] == "EXACT")
        cl = sum(1 for r in s if r["clean_recovery"])
        t = sum(r["time"] for r in s)
        sp, g, rr, _ = ALLOCS[a]
        cfg = f"{sp} x{g}g x{rr}r"
        print(f"{a:<12}{cfg:<22}{s[0]['budget']:>10}{ex:>6}/{len(s):<4}"
              f"{cl:>6}/{len(s):<4}{t:>9.0f}s")
        res.append((a, ex, cl, t, len(s)))

    if len(res) >= 2:
        best_ex = max(res, key=lambda x: (x[1], x[2], -x[3]))
        print(f"\n  meilleure allocation : '{best_ex[0]}' "
              f"({best_ex[1]}/{best_ex[4]} exactes, {best_ex[2]} propres, "
              f"{best_ex[3]:.0f}s)")

    d = {a: r for a, *r in [(x[0], x[1], x[2], x[3], x[4]) for x in res]}
    if "default" in d and "bench" in d:
        print(f"\n  --- LA question du défaut ---")
        print(f"  default (fast x100g x1r)  : {d['default'][0]} exactes, "
              f"{d['default'][1]} propres, {d['default'][2]:.0f}s")
        print(f"  bench   (fast x30g x4r)   : {d['bench'][0]} exactes, "
              f"{d['bench'][1]} propres, {d['bench'][2]:.0f}s")
        if d["bench"][0] > d["default"][0] or (
           d["bench"][0] == d["default"][0] and d["bench"][1] > d["default"][1]):
            print("  -> la config des bancs bat le défaut : le défaut du paquet")
            print("     devrait changer, et l'enveloppe publiée deviendrait")
            print("     enfin celle que reçoivent les utilisateurs.")
        else:
            print("  -> le défaut tient. Il faudra alors mesurer l'enveloppe")
            print("     publiée DANS la configuration par défaut, ou dire")
            print("     clairement quels réglages les chiffres supposent.")
    if "default" in d and "population" in d:
        print(f"\n  --- générations vs population, à budget égal ---")
        print(f"  default    (fast x100g)  : {d['default'][0]} exactes")
        print(f"  population (normal x38g) : {d['population'][0]} exactes")
        if d["default"][0] > d["population"][0]:
            print("  -> les générations paient mieux que la population. "
                  "Hypothèse confirmée.")
        elif d["default"][0] < d["population"][0]:
            print("  -> la population paie mieux. Hypothèse INFIRMÉE.")
        else:
            print("  -> égalité : seul le temps réel départage.")
    print("\nCe banc se rapporte À CÔTÉ des bras auto / none / units.")

if __name__ == "__main__":
    argv = sys.argv[1:]
    allocs = ORDER; eqs = None
    if "--alloc" in argv: allocs = argv[argv.index("--alloc") + 1].split(",")
    if "--eq" in argv:    eqs = set(argv[argv.index("--eq") + 1].split(","))
    if os.environ.get("PYTHONHASHSEED") != "0":
        print("!! ATTENTION : PYTHONHASHSEED != 0 — relancer avec PYTHONHASHSEED=0.")
    _check_engine()
    if "--bilan" in argv or "--summary" in argv:
        bilan()
    else:
        print("=== BANC D'ALLOCATION DU BUDGET ===")
        print(f"    {'allocation':<12}{'config':<24}{'budget'}")
        for a in allocs:
            sp, g, rr, note = ALLOCS[a]
            print(f"    {a:<12}{sp+' x'+str(g)+'g x'+str(rr)+'r':<24}"
                  f"{PER_GEN[sp]*g*rr:>8}  {note}")
        run(allocs, eqs)
        bilan()
