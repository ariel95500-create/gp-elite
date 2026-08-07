# -*- coding: utf-8 -*-
"""
BANC FEYNMAN — BRAS « UNITS » (recherche dimensionnellement contrainte)
=======================================================================
Troisième bras du banc. Protocole STRICTEMENT identique au bras « none »
(mêmes graines RandomState(1000+i), mêmes splits 140/60, seed=0,
restarts=4, fast/30, normalize="none"), avec UN ajout : la déclaration
des dimensions physiques de chaque variable et de la cible
(units= / target_units=), qui bascule le moteur en recherche typée
(dim_search, v0.4) — seuls des arbres dimensionnellement homogènes
sont construits.

Ce bras NE REMPLACE RIEN. Il se rapporte À CÔTÉ des bras « auto »
(gelé) et « none ». Le défaut du moteur reste auto.

Sortie : feyn_units.jsonl — format enrichi (télémétrie v2)
  hérités du banc   name, formula, normalize, status, one_minus_r2,
                    pareto_best, pb_size, time, expr
  traçabilité       arm, engine_version, pythonhashseed, date, seed,
                    restarts, generations, speed, validation_split,
                    pool, n_train, n_test, units, target_units, data_hash
  diagnostic        train_one_minus_r2, pb_train, champion_is_pb,
                    expr_full, front[] (le front de Pareto complet :
                    taille, erreur test, expression entière),
                    ops_census, suspect_ops, ops_suspects

Reprise : relancer le script reprend là où il s'est arrêté.

Lancement (PYTHONHASHSEED=0 obligatoire pour la reproductibilité) :
  Windows :  set PYTHONHASHSEED=0 && python benchmarks\\feynman_units.py
  Linux   :  PYTHONHASHSEED=0 python3 benchmarks/feynman_units.py
Options :  feynman_units.py [i0] [i1]   → tranche d'équations
           feynman_units.py --bilan     → bilan seul depuis le jsonl
"""
import os, sys, json, time, io, re, contextlib, hashlib, datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

EXPECTED_ENGINE = "0.6.0"          # version de référence des trois bras

# [correctif] La racine du dépôt passe AVANT tout : sinon un gp_elite installé
# par pip (potentiellement plus ancien) masque la copie du dépôt. C'est ce qui
# a produit un faux « 0.5.0 » au premier lancement.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.isdir(os.path.join(_ROOT, "gp_elite")):
    sys.path.insert(0, _ROOT)

import gp_elite
from gp_elite import symbolic_regression
import numpy as np

ENGINE = getattr(gp_elite, "__version__", "?")

def _check_engine():
    print(f"gp_elite {ENGINE}  <-  {os.path.abspath(gp_elite.__file__)}")
    if ENGINE != EXPECTED_ENGINE:
        print(f"\n!! ARRÊT : moteur {ENGINE}, attendu {EXPECTED_ENGINE}.")
        print("   Les trois bras (auto/none/units) doivent tourner sur la MÊME")
        print("   version, sinon la comparaison n'a aucune valeur.")
        print("   Diagnostic : le chemin ci-dessus pointe-t-il vers ton dépôt")
        print("   ou vers site-packages ? Si site-packages, désinstalle la copie")
        print("   pip (pip uninstall gp-elite) ou lance depuis la racine du")
        print("   dépôt. Pour passer outre volontairement : --force")
        if "--force" not in sys.argv:
            sys.exit(1)
        print("   (--force : on continue malgré tout)\n")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feyn_units.jsonl") \
      if "__file__" in globals() else "feyn_units.jsonl"

R = np.random.RandomState
def U(rng, lo, hi, n): return rng.uniform(lo, hi, n)

# ── dimensions SI de base ───────────────────────────────────────────────────
NODIM  = {}
M      = {"m": 1}
VEL    = {"m": 1, "s": -1}
FORCE  = {"kg": 1, "m": 1, "s": -2}
ENERGY = {"kg": 1, "m": 2, "s": -2}          # (le couple a les mêmes dimensions)
CHARGE = {"A": 1, "s": 1}
EFIELD = {"kg": 1, "m": 1, "s": -3, "A": -1}  # V/m
BFIELD = {"kg": 1, "s": -2, "A": -1}          # tesla
EPS0   = {"A": 2, "s": 4, "kg": -1, "m": -3}  # permittivité
VOLT   = {"kg": 1, "m": 2, "s": -3, "A": -1}
PRESS  = {"kg": 1, "m": -1, "s": -2}
POWER  = {"kg": 1, "m": 2, "s": -3}
STIFF  = {"kg": 1, "s": -2}                   # raideur k
MOBIL  = {"s": 1, "kg": -1}                   # rend v = mu·q·V/d homogène
MAGMOM = {"A": 1, "m": 2}                     # moment magnétique
MOMENT = {"kg": 1, "m": 1, "s": -1}           # quantité de mouvement

# ── les 15 équations : protocole identique au banc gelé ─────────────────────
# (nom, formule, n_vars, sampler, f, pool, units, target_units)
PROBS = [
 ("I.12.1",   "mu*Nn",                     2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1], "physical",
   [NODIM, FORCE], FORCE),
 ("I.12.5",   "q2*Ef",                     2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1], "physical",
   [CHARGE, EFIELD], FORCE),
 ("I.14.4",   "k*x^2/2",                   2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: 0.5*X[:,0]*X[:,1]**2, "physical",
   [STIFF, M], ENERGY),
 ("I.39.1",   "(3/2)*pr*V",                2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: 1.5*X[:,0]*X[:,1], "physical",
   [PRESS, {"m": 3}], ENERGY),
 ("II.3.24",  "P/(4*pi*r^2)",              2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,3,n)],
   lambda X: X[:,0]/(4*np.pi*X[:,1]**2), "physical",
   [POWER, M], {"kg": 1, "s": -3}),
 ("I.6.20a",  "exp(-th^2/2)/sqrt(2*pi)",   1, lambda r,n: np.c_[U(r,-3,3,n)],
   lambda X: np.exp(-X[:,0]**2/2)/np.sqrt(2*np.pi), "physical",
   [NODIM], NODIM),
 ("I.8.14",   "sqrt((x2-x1)^2+(y2-y1)^2)", 4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: np.sqrt((X[:,1]-X[:,0])**2+(X[:,3]-X[:,2])**2), "physical",
   [M, M, M, M], M),
 ("I.16.6",   "(u+v)/(1+u*v/c^2)",         3, lambda r,n: np.c_[U(r,1,2,n),U(r,1,2,n),U(r,3,10,n)],
   lambda X: (X[:,0]+X[:,1])/(1+X[:,0]*X[:,1]/X[:,2]**2), "physical",
   [VEL, VEL, VEL], VEL),
 ("I.27.6",   "1/(1/d1+n/d2)",             3, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,2,n)],
   lambda X: 1.0/(1.0/X[:,0]+X[:,2]/X[:,1]), "physical",
   [M, M, NODIM], M),
 ("I.34.8",   "q*v*B/p",                   4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1]*X[:,2]/X[:,3], "physical",
   [CHARGE, VEL, BFIELD, MOMENT], {"s": -1}),
 ("I.43.16",  "mu*q*V/d",                  4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1]*X[:,2]/X[:,3], "physical",
   [MOBIL, CHARGE, VOLT, M], VEL),
 ("I.12.2",   "q1*q2/(4*pi*eps*r^2)",      4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,3,n),U(r,1,3,n)],
   lambda X: X[:,0]*X[:,1]/(4*np.pi*X[:,2]*X[:,3]**2), "physical",
   [CHARGE, CHARGE, EPS0, M], FORCE),
 ("II.15.4",  "-mu*B*cos(th)",             3, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,0,6.28,n)],
   lambda X: -X[:,0]*X[:,1]*np.cos(X[:,2]), "trig",
   [MAGMOM, BFIELD, NODIM], ENERGY),
 ("I.18.12",  "r*F*sin(th)",               3, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,0,3.14,n)],
   lambda X: X[:,0]*X[:,1]*np.sin(X[:,2]), "trig",
   [M, FORCE, NODIM], ENERGY),
 ("III.15.12","2*U*(1-cos(k*d))",          3, lambda r,n: np.c_[U(r,1,5,n),U(r,0.5,2,n),U(r,0.5,2,n)],
   lambda X: 2*X[:,0]*(1-np.cos(X[:,1]*X[:,2])), "trig",
   [ENERGY, {"m": -1}, M], ENERGY),
]

# statuts du bras « none » confirmés sur la machine de référence (face-à-face)
NONE_REF = {p[0]: "EXACT" for p in PROBS}
NONE_REF["I.16.6"] = "MISS"

# ── télémétrie ──────────────────────────────────────────────────────────────
_OPS = ("sin", "cos", "tanh", "tan", "exp", "log", "sqrt", "abs", "pow")
_SUSPECT = {"sin", "cos", "tanh", "tan", "exp", "log", "sqrt"}

def _census(expr):
    c = {}
    for op in _OPS:
        k = len(re.findall(r"\b%s\s*\(" % op, expr))
        if op == "tan":
            k -= len(re.findall(r"\btanh\s*\(", expr))
        if k:
            c[op] = k
    sq = expr.count("\u00b2")
    if sq:
        c["square"] = sq
    return c

def _expected(formula):
    return set(re.findall(r"\b(sin|cos|tanh|tan|exp|log|sqrt|abs)\b", formula))

def _err(e, X, y, var):
    p = e.predict(X)
    return float(np.mean((p - y) ** 2) / var)

def _done():
    if not os.path.exists(OUT):
        return set()
    names = set()
    with open(OUT, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    names.add(json.loads(line)["name"])
                except Exception:
                    pass
    return names

# ── boucle ──────────────────────────────────────────────────────────────────
def run_range(i0, i1):
    done = _done()
    for i in range(i0, min(i1, len(PROBS))):
        name, formula, nv, sampler, f, pool, units, tunits = PROBS[i]
        if name in done:
            print(f"  {name:<10} déjà fait — repris du jsonl")
            continue
        rng = R(1000 + i)
        X = sampler(rng, 200); y = f(X)
        idx = rng.permutation(200); tr, te = idx[:140], idx[140:]
        names = [f"v{k}" for k in range(nv)]
        dhash = hashlib.sha1(X.tobytes() + y.tobytes()).hexdigest()[:12]
        t0 = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            r = symbolic_regression(X[tr], y[tr], feature_names=names,
                                    operators=pool, normalize="none",
                                    generations=30, speed="fast",
                                    validation_split=0.15, seed=0, restarts=4,
                                    units=units, target_units=tunits)
        dt = time.time() - t0
        v_te = float(np.var(y[te])); v_tr = float(np.var(y[tr]))

        champ_te = _err(r, X[te], y[te], v_te)
        champ_tr = _err(r, X[tr], y[tr], v_tr)

        front, seen = [], set()
        for e in list(r.pareto or []) + [r]:
            try:
                e_te = _err(e, X[te], y[te], v_te)
            except Exception:
                continue
            key = (int(e.size), round(e_te, 15))
            if key in seen:
                continue
            seen.add(key)
            front.append({"size": int(e.size), "err_test": e_te,
                          "err_train": _err(e, X[tr], y[tr], v_tr),
                          "expr": e.expression})
        front.sort(key=lambda d: d["size"])
        pb_entry = min(front, key=lambda d: d["err_test"])
        pb, pb_size = pb_entry["err_test"], pb_entry["size"]
        pb_train = pb_entry["err_train"]

        status = "EXACT" if pb < 1e-9 else ("NEAR" if pb < 1e-3 else "MISS")
        census = _census(pb_entry["expr"])
        suspects = sorted((set(census) & _SUSPECT) - _expected(formula))

        rec = dict(
            # hérités
            name=name, formula=formula, normalize="none", status=status,
            one_minus_r2=champ_te, pareto_best=pb, pb_size=pb_size,
            time=round(dt, 1), expr=r.expression[:90],
            # traçabilité
            arm="units", engine_version=ENGINE,
            pythonhashseed=os.environ.get("PYTHONHASHSEED"),
            date=datetime.datetime.now().isoformat(timespec="seconds"),
            seed=0, restarts=4, generations=30, speed="fast",
            validation_split=0.15, pool=pool,
            n_train=140, n_test=60,
            units={names[k]: units[k] for k in range(nv)},
            target_units=tunits, data_hash=dhash,
            # diagnostic
            train_one_minus_r2=champ_tr, pb_train=pb_train,
            champion_is_pb=bool(pb_entry["size"] == int(r.size)
                                and abs(pb - champ_te) < 1e-300 or pb == champ_te),
            expr_full=r.expression, front=front,
            ops_census=census, suspect_ops=suspects,
            ops_suspects=bool(suspects),
        )
        with open(OUT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
        flag = ("  !ops:" + ",".join(suspects)) if suspects else ""
        print(f"  {name:<10} {status:<6} champ={champ_te:.1e} pareto={pb:.1e}"
              f"  ({dt:.0f}s){flag}")
        sys.stdout.flush()

# ── bilan ───────────────────────────────────────────────────────────────────
def bilan():
    if not os.path.exists(OUT):
        print("(pas encore de résultats)"); return
    rows = []
    with open(OUT, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    by = {r["name"]: r for r in rows}
    ordered = [by[p[0]] for p in PROBS if p[0] in by]
    n_ex = sum(1 for r in ordered if r["status"] == "EXACT")
    print(f"\n=== BILAN BRAS UNITS — {n_ex}/{len(ordered)} EXACT "
          f"(moteur {ENGINE}) ===")
    print(f"{'équation':<11}{'none':<7}{'units':<7}{'pareto_best':<13}"
          f"{'taille':<8}{'drapeaux'}")
    basc_up, basc_down = [], []
    for r in ordered:
        ref = NONE_REF.get(r["name"], "?")
        fl = ",".join(r.get("suspect_ops") or [])
        print(f"{r['name']:<11}{ref:<7}{r['status']:<7}"
              f"{r['pareto_best']:<13.1e}{r['pb_size']:<8}{fl}")
        if ref != "EXACT" and r["status"] == "EXACT":
            basc_up.append(r["name"])
        if ref == "EXACT" and r["status"] != "EXACT":
            basc_down.append(r["name"])
    if basc_up:
        print(f"\nGagnées vs none : {', '.join(basc_up)}")
    if basc_down:
        print(f"RÉGRESSIONS vs none : {', '.join(basc_down)}  <-- à examiner")
    if not basc_down and len(ordered) == len(PROBS):
        print("\nAucune régression vs le bras none.")
    print("\nRappel : I.16.6 sous units n'est pas seed-robuste (1 seed/4 en "
          "session d'étude) — un MISS ici resterait un résultat, pas un bug.")
    print("Ce bras se rapporte À CÔTÉ des bras auto (gelé) et none — "
          "il ne remplace rien.")

if __name__ == "__main__":
    if os.environ.get("PYTHONHASHSEED") != "0":
        print("!! ATTENTION : PYTHONHASHSEED != 0 — reproductibilité "
              "inter-machines non garantie. Relancer avec "
              "PYTHONHASHSEED=0.")
    _check_engine()
    print(f"bras UNITS (recherche typée), normalize=none, seed=0, "
          f"restarts=4, fast/30")
    if len(sys.argv) > 1 and sys.argv[1] in ("--bilan", "--summary"):
        bilan()
    else:
        a = int(sys.argv[1]) if len(sys.argv) > 1 else 0
        b = int(sys.argv[2]) if len(sys.argv) > 2 else len(PROBS)
        print(f"=== BANC FEYNMAN, BRAS UNITS — équations {a}..{b-1} ===")
        run_range(a, b)
        bilan()
