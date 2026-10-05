# -*- coding: utf-8 -*-
"""
BANC DES MODES `speed` — coût, efficacité, et allocation du budget
===================================================================
Objet : `speed=` accepte trois modes, un seul est mesuré (`fast`, utilisé par
tous les bancs). L'intuition affichée — « ultrafast pour les tests rapides,
normal pour les cas difficiles » — n'a jamais été vérifiée.

CE QUE `speed` CHANGE RÉELLEMENT (core.make_cfg, l.7788) :
    ultrafast : pop=150, 2 îles, élite=4, tournoi=3, const_opt=15 itér.
    fast      : pop=300, 3 îles, élite=6, tournoi=4, const_opt=20 itér.
    normal    : pop=600, 4 îles, élite=6, tournoi=4, const_opt=20 itér.
Individus évalués par génération : 300 / 900 / 2400.
=> normal coûte ~2.7x fast, qui coûte ~3x ultrafast.
(Le nombre de générations n'est PAS piloté par speed ici : `generations=`
le fixe explicitement.)

DEUX AXES
---------
AXE 1 — comparaison naïve, à générations et relances égales.
  Répond à : « que gagne ou perd un utilisateur en changeant de mode ? »
  Résultat en partie attendu : plus de population, plus de récupérations.
  L'information utile est le RAPPORT gain/coût, pas le gain seul.

AXE 2 — face-à-face À COÛT ÉGAL. C'est le résultat intéressant.
  Un budget de calcul se dépense de deux façons : chercher plus LARGE
  (`normal`) ou chercher plus SOUVENT (`restarts`). À nombre d'individus
  égal, laquelle paie ?
      normal x 4 relances   ~=   fast x 11 relances   ~=   ultrafast x 32
  On compare normal(4) et fast(11) sur les équations difficiles — les seules
  où la différence peut se voir. Le script rapporte les temps RÉELS obtenus,
  pour qu'on vérifie que l'égalité de budget a bien été tenue.

PROTOCOLE — identique aux autres bancs SAUF le paramètre étudié :
  normalize="none", generations=30, validation_split=0.15, seed=0,
  split 140/60, mêmes graines RandomState(1000+i).

Sortie : feyn_speed.jsonl   |   Reprise automatique.

Lancement :
  set "PYTHONHASHSEED=0" && python benchmarks\\feynman_speed.py
Options :
  --axe 1|2|both     (défaut : both)
  --modes fast,normal
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
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feyn_speed.jsonl")

R = np.random.RandomState
def U(rng, lo, hi, n): return rng.uniform(lo, hi, n)

# individus évalués par génération, pour raisonner à coût égal
COST = {"ultrafast": 150 * 2, "fast": 300 * 3, "normal": 600 * 4}
MODES = ["ultrafast", "fast", "normal"]

# axe 2 : configurations de coût théorique équivalent (~9600 individus/gén.)
ISO = [("normal", 4), ("fast", 11), ("ultrafast", 32)]
ISO_DEFAULT = [("normal", 4), ("fast", 11)]
ISO_EQ = ["I.16.6", "I.12.2", "I.8.14"]      # les cas où l'écart peut se voir

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
BY_NAME = {p[1]: p for p in PROBS}
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
            r = json.loads(line); ks.add((r["axe"], r["name"], r["speed"], r["restarts"]))
        except Exception: pass
    return ks

def _check_engine():
    print(f"gp_elite {ENGINE}  <-  {os.path.abspath(gp_elite.__file__)}")
    if ENGINE != EXPECTED_ENGINE:
        print(f"\n!! ARRÊT : moteur {ENGINE}, attendu {EXPECTED_ENGINE}.")
        print("   Passer outre volontairement : --force")
        if "--force" not in sys.argv: sys.exit(1)

def one(axe, name, speed, restarts, done):
    if (axe, name, speed, restarts) in done:
        print(f"  {name:<11} {speed:<10} r={restarts:<3} déjà fait — repris"); return
    idx, _, formula, nv, sampler, f, pool = BY_NAME[name]
    rng = R(1000 + idx)
    X = sampler(rng, 200); y = f(X)
    perm = rng.permutation(200); tr, te = perm[:140], perm[140:]
    names = [f"v{k}" for k in range(nv)]
    t0 = time.time()
    with contextlib.redirect_stdout(io.StringIO()):
        r = symbolic_regression(X[tr], y[tr], feature_names=names, operators=pool,
                                normalize="none", generations=30, speed=speed,
                                validation_split=0.15, seed=0, restarts=restarts)
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
                      "err_train": _err(e, X[tr], y[tr], v_tr), "expr": e.expression})
    front.sort(key=lambda d: d["size"])
    best = min(front, key=lambda d: d["err_test"])
    pb, sz = best["err_test"], best["size"]
    status = "EXACT" if pb < 1e-9 else ("NEAR" if pb < 1e-3 else "MISS")
    census = _census(best["expr"])
    susp = sorted((set(census) & _SUSPECT) - _expected(formula))
    clean = bool(status == "EXACT" and not susp and sz <= CANON.get(name, 99) + 4)
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(
            axe=axe, name=name, formula=formula, speed=speed, restarts=restarts,
            cost_per_gen=COST[speed], budget=COST[speed] * restarts,
            status=status, clean_recovery=clean, pareto_best=pb, pb_size=sz,
            time=round(dt, 1), one_minus_r2=_err(r, X[te], y[te], v_te),
            n_vars=nv, pool=pool, generations=30, normalize="none", seed=0,
            engine_version=ENGINE,
            pythonhashseed=os.environ.get("PYTHONHASHSEED"),
            date=datetime.datetime.now().isoformat(timespec="seconds"),
            data_hash=hashlib.sha1(X.tobytes()).hexdigest()[:12],
            expr_full=r.expression, front=front,
            ops_census=census, suspect_ops=susp)) + "\n")
    mark = "propre" if clean else ("" if status != "EXACT" else "non-canonique")
    print(f"  {name:<11} {speed:<10} r={restarts:<3} {status:<6} "
          f"pb={pb:.1e} size={sz:<4} {dt:6.0f}s  {mark}")
    sys.stdout.flush()

def run(axe_sel, modes):
    done = _done()
    if axe_sel in ("1", "both"):
        print(f"\n########## AXE 1 — trois modes, budget de relances identique "
              f"(restarts=4) ##########")
        for mode in modes:
            print(f"\n=== speed='{mode}'  ({COST[mode]} individus/génération) ===")
            for _, name, *_ in PROBS:
                one("1", name, mode, 4, done)
    if axe_sel in ("2", "both"):
        print(f"\n########## AXE 2 — À COÛT ÉGAL : chercher large ou chercher "
              f"souvent ? ##########")
        for name in ISO_EQ:
            print(f"\n=== {name} ===")
            for mode, rst in ISO_DEFAULT:
                one("2", name, mode, rst, done)

def bilan():
    if not os.path.exists(OUT):
        print("(pas encore de résultats)"); return
    rows = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    a1 = [r for r in rows if r["axe"] == "1"]
    a2 = [r for r in rows if r["axe"] == "2"]

    if a1:
        modes = [m for m in MODES if any(r["speed"] == m for r in a1)]
        print(f"\n=== AXE 1 — matrice équation x mode "
              f"(E propre · e non-canonique · N near · M miss) ===")
        print(f"{'équation':<11}" + "".join(f"{m:>12}" for m in modes))
        for _, name, *_ in PROBS:
            line = f"{name:<11}"
            for m in modes:
                s = [r for r in a1 if r["name"] == name and r["speed"] == m]
                c = "-" if not s else ("E" if s[0]["clean_recovery"] else
                     "e" if s[0]["status"] == "EXACT" else
                     "N" if s[0]["status"] == "NEAR" else "M")
                line += f"{c:>12}"
            print(line)
        print(f"\n{'mode':<11}{'exactes':>10}{'propres':>10}{'temps tot.':>13}"
              f"{'coût théo.':>12}{'gain/coût':>12}")
        ref = None
        for m in modes:
            s = [r for r in a1 if r["speed"] == m]
            ex = sum(1 for r in s if r["status"] == "EXACT")
            cl = sum(1 for r in s if r["clean_recovery"])
            t = sum(r["time"] for r in s)
            if m == "fast": ref = (ex, t)
            rap = ""
            if ref and m != "fast" and ref[1] > 0:
                d_ex = ex - ref[0]; d_t = t / ref[1]
                rap = f"{d_ex:+d} eq / x{d_t:.1f}"
            print(f"{m:<11}{ex:>6}/{len(s):<4}{cl:>6}/{len(s):<4}{t:>11.0f}s"
                  f"{COST[m]:>12}{rap:>12}")
        print("\n  Lecture : la colonne 'gain/coût' compare à `fast`. Un mode qui")
        print("  coûte x2.7 pour +1 équation n'est pas un bon achat par défaut ;")
        print("  il peut le rester comme dernier recours sur un cas dur.")

    if a2:
        print(f"\n=== AXE 2 — à coût égal : chercher LARGE vs chercher SOUVENT ===")
        print(f"{'équation':<11}{'config':<18}{'statut':<8}{'pareto':>10}"
              f"{'taille':>8}{'temps':>9}")
        for name in sorted({r["name"] for r in a2}):
            s = sorted([r for r in a2 if r["name"] == name],
                       key=lambda r: -r["cost_per_gen"])
            for r in s:
                print(f"{name:<11}{r['speed']+' x'+str(r['restarts']):<18}"
                      f"{r['status']:<8}{r['pareto_best']:>10.1e}"
                      f"{r['pb_size']:>8}{r['time']:>8.0f}s")
            if len(s) >= 2:
                t = [x["time"] for x in s]
                print(f"{'':11}rapport de temps réel : x{max(t)/max(min(t),1e-9):.2f}"
                      f"   (budget théorique visé : x1.00)")
            print()
        wins = {}
        for name in {r["name"] for r in a2}:
            s = [r for r in a2 if r["name"] == name]
            b = min(s, key=lambda r: r["pareto_best"])
            wins[b["speed"]] = wins.get(b["speed"], 0) + 1
        print("  meilleur résultat par équation :",
              ", ".join(f"{k} x{v}" for k, v in sorted(wins.items())))
        print("  -> si `fast` avec beaucoup de relances tient tête à `normal`,")
        print("     le conseil mesuré devient : augmenter restarts avant speed.")
    print("\nCe banc se rapporte À CÔTÉ des bras auto / none / units.")

if __name__ == "__main__":
    argv = sys.argv[1:]
    axe = "both"; modes = MODES
    if "--axe" in argv:   axe = argv[argv.index("--axe") + 1]
    if "--modes" in argv: modes = argv[argv.index("--modes") + 1].split(",")
    if os.environ.get("PYTHONHASHSEED") != "0":
        print("!! ATTENTION : PYTHONHASHSEED != 0 — relancer avec PYTHONHASHSEED=0.")
    _check_engine()
    if "--bilan" in argv or "--summary" in argv:
        bilan()
    else:
        print(f"=== BANC DES MODES speed — axe {axe} ===")
        print(f"    coûts par génération : " +
              ", ".join(f"{m}={COST[m]}" for m in MODES))
        run(axe, modes)
        bilan()
