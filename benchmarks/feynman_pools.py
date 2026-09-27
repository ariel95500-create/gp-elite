# -*- coding: utf-8 -*-
"""
BANC DES POOLS D'OPÉRATEURS
============================
Objet : `operators=` accepte CINQ pools (`physical`, `trig`, `full`, `poly`,
`conserve`). Deux seulement sont mesurés (`physical`, `trig`), `poly` est
effleuré, et `full` et `conserve` ne l'ont jamais été. Or ce paramètre est
le premier que règle un utilisateur, et la documentation n'en décrit que
quatre — `conserve` n'y figure pas du tout.

LA SUBTILITÉ À TRAITER
----------------------
Un pool ne peut pas retrouver une loi dont il n'a pas les opérateurs :
`conserve` n'a AUCUNE division (Coulomb est hors de portée quel que soit le
budget), `poly` n'a ni sinus ni exponentielle. Comparer les taux bruts
mesurerait la couverture des opérateurs, pas la qualité du pool.

Ce banc rapporte donc DEUX chiffres distincts :
  * couverture   : combien d'équations le pool peut exprimer EN PRINCIPE
  * récupération : parmi celles-là seulement, combien il retrouve vraiment
La seconde est la mesure honnête de la qualité d'un pool.

LA QUESTION OUVERTE
-------------------
`full` contient tout : il ne rate rien par construction. Mais un espace de
recherche plus large dilue-t-il l'effort ? Le face-à-face `physical` / `full`
sur les 12 équations que les DEUX peuvent exprimer est le résultat principal
attendu de ce banc.

PROTOCOLE — identique aux autres bras, SAUF le pool :
  normalize="none", generations=30, speed="fast", validation_split=0.15,
  seed=0, restarts=4, split 140/60, mêmes graines RandomState(1000+i).

Ce banc NE REMPLACE RIEN : il se rapporte à côté des bras auto / none / units.

Sortie : feyn_pools.jsonl (télémétrie v2)   |   Reprise automatique.

Lancement :
  set "PYTHONHASHSEED=0" && python benchmarks\\feynman_pools.py
Options :
  --pools physical,full   sous-ensemble de pools
  --eq I.12.1,I.16.6      sous-ensemble d'équations
  --all                   inclut les paires (pool, équation) NON exprimables
                          (par défaut on les saute : le résultat est connu
                          d'avance et le calcul serait perdu)
  --bilan                 bilan seul
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
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feyn_pools.jsonl")

R = np.random.RandomState
def U(rng, lo, hi, n): return rng.uniform(lo, hi, n)

# ── contenu réel des pools (core._GENCSV_POOLS, l.1894) ─────────────────────
POOL_OPS = {
    "physical": {"+","-","*","/","pow","exp","log","sqrt","tanh","sq","neg","abs"},
    "trig":     {"+","-","*","/","pow","sin","cos","exp","log","sqrt","tanh","sq","neg","abs"},
    "full":     {"+","-","*","/","pow","sin","cos","log","exp","sqrt","tanh","abs","neg","sq","cube"},
    "poly":     {"+","-","*","/","sqrt","neg","sq","cube","abs"},
    "conserve": {"+","-","*","sq","cos","sin","neg"},
}
POOLS = ["physical", "trig", "full", "poly", "conserve"]

# ── les 15 équations + les opérateurs MINIMAUX qu'il faut pour les exprimer ──
# (nom, formule, n_vars, sampler, f, opérateurs requis)
PROBS = [
 ("I.12.1",   "mu*Nn",                     2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1], {"*"}),
 ("I.12.5",   "q2*Ef",                     2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1], {"*"}),
 ("I.14.4",   "k*x^2/2",                   2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: 0.5*X[:,0]*X[:,1]**2, {"*","sq"}),
 ("I.39.1",   "(3/2)*pr*V",                2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: 1.5*X[:,0]*X[:,1], {"*"}),
 ("II.3.24",  "P/(4*pi*r^2)",              2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,3,n)],
   lambda X: X[:,0]/(4*np.pi*X[:,1]**2), {"/","sq"}),
 ("I.6.20a",  "exp(-th^2/2)/sqrt(2*pi)",   1, lambda r,n: np.c_[U(r,-3,3,n)],
   lambda X: np.exp(-X[:,0]**2/2)/np.sqrt(2*np.pi), {"exp","sq"}),
 ("I.8.14",   "sqrt((x2-x1)^2+(y2-y1)^2)", 4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: np.sqrt((X[:,1]-X[:,0])**2+(X[:,3]-X[:,2])**2), {"sqrt","sq","-","+"}),
 ("I.16.6",   "(u+v)/(1+u*v/c^2)",         3, lambda r,n: np.c_[U(r,1,2,n),U(r,1,2,n),U(r,3,10,n)],
   lambda X: (X[:,0]+X[:,1])/(1+X[:,0]*X[:,1]/X[:,2]**2), {"/","+","*","sq"}),
 ("I.27.6",   "1/(1/d1+n/d2)",             3, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,2,n)],
   lambda X: 1.0/(1.0/X[:,0]+X[:,2]/X[:,1]), {"/","+"}),
 ("I.34.8",   "q*v*B/p",                   4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1]*X[:,2]/X[:,3], {"*","/"}),
 ("I.43.16",  "mu*q*V/d",                  4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1]*X[:,2]/X[:,3], {"*","/"}),
 ("I.12.2",   "q1*q2/(4*pi*eps*r^2)",      4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,3,n),U(r,1,3,n)],
   lambda X: X[:,0]*X[:,1]/(4*np.pi*X[:,2]*X[:,3]**2), {"*","/","sq"}),
 ("II.15.4",  "-mu*B*cos(th)",             3, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,0,6.28,n)],
   lambda X: -X[:,0]*X[:,1]*np.cos(X[:,2]), {"*","cos","neg"}),
 ("I.18.12",  "r*F*sin(th)",               3, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,0,3.14,n)],
   lambda X: X[:,0]*X[:,1]*np.sin(X[:,2]), {"*","sin"}),
 ("III.15.12","2*U*(1-cos(k*d))",          3, lambda r,n: np.c_[U(r,1,5,n),U(r,0.5,2,n),U(r,0.5,2,n)],
   lambda X: 2*X[:,0]*(1-np.cos(X[:,1]*X[:,2])), {"*","-","cos"}),
]

CANON_SIZE = {"I.12.1":3,"I.12.5":3,"I.14.4":7,"I.39.1":5,"II.3.24":6,
              "I.6.20a":8,"I.8.14":10,"I.16.6":13,"I.27.6":9,"I.34.8":7,
              "I.43.16":7,"I.12.2":11,"II.15.4":7,"I.18.12":7,"III.15.12":10}

def expressible(pool, required):
    return required <= POOL_OPS[pool]

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

def _expected(formula):
    return set(re.findall(r"\b(sin|cos|tanh|tan|exp|log|sqrt|abs)\b", formula))

def _err(e, X, y, var):
    return float(np.mean((e.predict(X) - y) ** 2) / var)

def _done():
    if not os.path.exists(OUT): return set()
    ks = set()
    with open(OUT, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try:
                r = json.loads(line); ks.add((r["name"], r["pool"]))
            except Exception: pass
    return ks

def _check_engine():
    print(f"gp_elite {ENGINE}  <-  {os.path.abspath(gp_elite.__file__)}")
    if ENGINE != EXPECTED_ENGINE:
        print(f"\n!! ARRÊT : moteur {ENGINE}, attendu {EXPECTED_ENGINE}.")
        print("   Tous les bancs doivent tourner sur la MÊME version.")
        print("   Passer outre volontairement : --force")
        if "--force" not in sys.argv: sys.exit(1)
        print("   (--force)\n")

def run(pools, eq_filter, run_all):
    done = _done()
    for pool in pools:
        print(f"\n=== pool '{pool}' ===")
        for i, (name, formula, nv, sampler, f, req) in enumerate(PROBS):
            if eq_filter and name not in eq_filter: continue
            expr_ok = expressible(pool, req)
            if (name, pool) in done:
                print(f"  {name:<11} déjà fait — repris"); continue
            if not expr_ok and not run_all:
                manque = sorted(req - POOL_OPS[pool])
                with open(OUT, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(dict(name=name, formula=formula, pool=pool,
                        expressible=False, missing_ops=manque, status="SKIP",
                        engine_version=ENGINE)) + "\n")
                print(f"  {name:<11} non exprimable (manque {','.join(manque)}) — sauté")
                continue
            rng = R(1000 + i)
            X = sampler(rng, 200); y = f(X)
            idx = rng.permutation(200); tr, te = idx[:140], idx[140:]
            names = [f"v{k}" for k in range(nv)]
            t0 = time.time()
            with contextlib.redirect_stdout(io.StringIO()):
                r = symbolic_regression(X[tr], y[tr], feature_names=names,
                                        operators=pool, normalize="none",
                                        generations=30, speed="fast",
                                        validation_split=0.15, seed=0, restarts=4)
            dt = time.time() - t0
            v_te = float(np.var(y[te])); v_tr = float(np.var(y[tr]))
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
            best = min(front, key=lambda d: d["err_test"])
            pb, sz = best["err_test"], best["size"]
            status = "EXACT" if pb < 1e-9 else ("NEAR" if pb < 1e-3 else "MISS")
            census = _census(best["expr"])
            suspects = sorted((set(census) & _SUSPECT) - _expected(formula))
            clean = bool(status == "EXACT" and not suspects
                         and sz <= CANON_SIZE.get(name, 99) + 4)
            with open(OUT, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(dict(
                    name=name, formula=formula, pool=pool, expressible=True,
                    required_ops=sorted(req), status=status, clean_recovery=clean,
                    pareto_best=pb, pb_size=sz, time=round(dt, 1),
                    one_minus_r2=_err(r, X[te], y[te], v_te),
                    n_train=140, n_test=60, n_vars=nv,
                    engine_version=ENGINE,
                    pythonhashseed=os.environ.get("PYTHONHASHSEED"),
                    date=datetime.datetime.now().isoformat(timespec="seconds"),
                    seed=0, restarts=4, generations=30, speed="fast",
                    validation_split=0.15, normalize="none",
                    data_hash=hashlib.sha1(X.tobytes()).hexdigest()[:12],
                    expr_full=r.expression, front=front,
                    ops_census=census, suspect_ops=suspects)) + "\n")
            mark = "propre" if clean else ("" if status != "EXACT" else "non-canonique")
            print(f"  {name:<11} {status:<6} pb={pb:.1e} size={sz:<4} "
                  f"{dt:5.0f}s  {mark}")
            sys.stdout.flush()

def bilan():
    if not os.path.exists(OUT):
        print("(pas encore de résultats)"); return
    rows = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    pools = [p for p in POOLS if any(r["pool"] == p for r in rows)]
    names = [p[0] for p in PROBS]

    print(f"\n=== MATRICE équation x pool (moteur {ENGINE}) ===")
    print("    E=exact propre · e=exact non-canonique · N=near · M=miss · "
          "·=non exprimable")
    print(f"{'équation':<11}" + "".join(f"{p:>11}" for p in pools))
    for nm in names:
        line = f"{nm:<11}"
        for p in pools:
            s = [r for r in rows if r["name"] == nm and r["pool"] == p]
            if not s: c = "-"
            elif not s[0].get("expressible", True): c = "·"
            else:
                r0 = s[0]
                c = ("E" if r0.get("clean_recovery") else
                     "e" if r0["status"] == "EXACT" else
                     "N" if r0["status"] == "NEAR" else "M")
            line += f"{c:>11}"
        print(line)

    print(f"\n=== couverture et récupération par pool ===")
    print(f"{'pool':<11}{'couverture':>12}{'exactes/expr.':>15}"
          f"{'propres/expr.':>15}{'temps tot.':>12}")
    for p in pools:
        sub = [r for r in rows if r["pool"] == p]
        expr = [r for r in sub if r.get("expressible", True)]
        ex = sum(1 for r in expr if r["status"] == "EXACT")
        cl = sum(1 for r in expr if r.get("clean_recovery"))
        t = sum(r.get("time", 0) for r in expr)
        print(f"{p:<11}{len(expr):>7}/{len(PROBS):<4}{ex:>10}/{len(expr):<4}"
              f"{cl:>10}/{len(expr):<4}{t:>10.0f}s")

    # face-à-face physical / full sur leur intersection
    a = {r["name"]: r for r in rows if r["pool"] == "physical" and r.get("expressible", True)}
    b = {r["name"]: r for r in rows if r["pool"] == "full" and r.get("expressible", True)}
    common = sorted(set(a) & set(b))
    if common:
        print(f"\n=== LE face-à-face : physical vs full "
              f"({len(common)} équations exprimables par les deux) ===")
        print(f"{'équation':<11}{'physical':>22}{'full':>22}")
        gain = loss = 0
        for nm in common:
            ra, rb = a[nm], b[nm]
            sa = f"{ra['status']} {ra['pareto_best']:.0e} t{ra['pb_size']}"
            sb = f"{rb['status']} {rb['pareto_best']:.0e} t{rb['pb_size']}"
            flag = ""
            if ra["status"] == "EXACT" and rb["status"] != "EXACT":
                flag = "  <- full perd"; loss += 1
            elif rb["status"] == "EXACT" and ra["status"] != "EXACT":
                flag = "  <- full gagne"; gain += 1
            print(f"{nm:<11}{sa:>22}{sb:>22}{flag}")
        ta = sum(a[n].get("time", 0) for n in common)
        tb = sum(b[n].get("time", 0) for n in common)
        print(f"\n  full gagne {gain}, perd {loss}  |  temps : "
              f"physical {ta:.0f}s vs full {tb:.0f}s (x{tb/max(ta,1e-9):.2f})")
        if loss > gain:
            print("  -> élargir le pool DILUE la recherche : garder un pool")
            print("     minimal est un conseil mesuré, pas une intuition.")
        elif gain > loss:
            print("  -> le pool large ne coûte rien en qualité ici.")
        else:
            print("  -> match nul en qualité ; seul le temps départage.")
    print("\nCe banc se rapporte À CÔTÉ des bras auto / none / units.")

if __name__ == "__main__":
    argv = sys.argv[1:]
    pools = POOLS; eqs = None
    if "--pools" in argv: pools = argv[argv.index("--pools") + 1].split(",")
    if "--eq" in argv:    eqs = set(argv[argv.index("--eq") + 1].split(","))
    if os.environ.get("PYTHONHASHSEED") != "0":
        print("!! ATTENTION : PYTHONHASHSEED != 0 — relancer avec PYTHONHASHSEED=0.")
    _check_engine()
    if "--bilan" in argv or "--summary" in argv:
        bilan()
    else:
        print(f"=== BANC DES POOLS — {pools} ===")
        print("    couverture théorique (opérateurs requis vs disponibles) :")
        for p in pools:
            k = sum(1 for pr in PROBS if expressible(p, pr[5]))
            print(f"      {p:<10} {k:>2}/{len(PROBS)} équations exprimables")
        run(pools, eqs, "--all" in argv)
        bilan()
