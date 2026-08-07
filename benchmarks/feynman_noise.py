# -*- coding: utf-8 -*-
"""
BANC DE BRUIT — robustesse aux données expérimentales imparfaites
==================================================================
Objet : le README revendique « experimental datasets ». Or les trois bancs
existants (auto / none / units) et le banc de scaling tournent tous sur des
données SYNTHÉTIQUES SANS BRUIT. Aucune mesure ne soutient aujourd'hui la
partie « expérimentale » de l'affirmation. Ce banc la teste.

MÉTHODE — le point critique
---------------------------
Avec du bruit, le critère habituel « 1-R2 < 1e-9 » devient INATTEIGNABLE :
le plancher de bruit borne l'erreur (à 1 % de bruit, même la loi exacte
plafonne vers 1e-4). Évaluer sur des données bruitées ferait donc conclure
à tort que le moteur s'effondre.

Protocole retenu :
  * ENTRAÎNEMENT sur y bruité  (ce que vit l'expérimentateur)
  * ÉVALUATION contre y PROPRE (la vraie question : a-t-on retrouvé la loi ?)

Deux métriques, dans cet ordre d'importance :
  1. RÉCUPÉRATION STRUCTURELLE — la forme trouvée est-elle canonique ?
     (taille proche de la forme littérale, pas d'opérateur parasite)
     C'est elle qui survit ou non au bruit, et c'est ce qui intéresse un
     utilisateur qui cherche une loi interprétable.
  2. GAIN DE DÉBRUITAGE — noise_floor / err_clean : le modèle est-il plus
     proche de la vérité que ne l'étaient les données ? Un gain > 1 signifie
     que le moteur a débruité ; c'est le vrai service rendu.
     (noise_floor ~= level^2 : variance du bruit rapportée à celle de y)

Statuts :
  EXACT     err_clean < 1e-9            (possible seulement à bruit nul)
  RECOVERED forme canonique retrouvée   (la loi est là, constantes imprécises)
  DENOISED  err_clean < noise_floor     (mieux que les données, forme non canonique)
  MISS      le reste

DEUX RÉGIMES DE BRUIT
---------------------
  --noise gauss    (défaut) bruit gaussien relatif sur y, sur TOUS les points
                   -> imprécision de mesure. levels = fraction de std(y).
  --noise outlier  une FRACTION des points est corrompue violemment
                   -> capteur qui déraille. levels = fraction de points touchés.

DEUX BRAS
---------
  défaut       réglages standard du moteur
  --robust     active robust=True (perte de Huber + calage robuste), conçu
               pour les valeurs aberrantes. Son intérêt est attendu surtout
               en régime 'outlier' — c'est précisément ce qu'on veut mesurer.

Le bruit porte sur y uniquement ; X reste propre (évite les domaines
invalides pour sqrt/log et isole l'effet mesuré).

Taille fixée à N=500 : le banc de scaling a montré que c'est le seuil à
partir duquel les formes canoniques sortent de façon fiable (en dessous, on
mélangerait l'effet 'petites données' avec l'effet bruit).

PROTOCOLE par ailleurs identique aux autres bancs : normalize="none",
generations=30, speed="fast", validation_split=0.15, seed=0, restarts=4,
split 70/30, 3 tirages indépendants par point de mesure.

Sortie : feyn_noise.jsonl  |  Reprise automatique.

Lancement :
  set PYTHONHASHSEED=0 && python benchmarks\\feynman_noise.py
Options :
  --noise gauss|outlier   régime de bruit (défaut : gauss)
  --robust                bras robuste
  --levels 0,0.01,0.1     niveaux personnalisés
  --eq I.16.6,I.12.1      sous-ensemble
  --n 500                 taille des données
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
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feyn_noise.jsonl")

R = np.random.RandomState
def U(rng, lo, hi, n): return rng.uniform(lo, hi, n)

LEVELS_GAUSS   = [0.0, 0.001, 0.01, 0.03, 0.10]   # fraction de std(y)
LEVELS_OUTLIER = [0.0, 0.01, 0.05, 0.10]          # fraction de points corrompus
REPEATS = 3
DEFAULT_N = 500

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
CANON_SIZE = {"I.12.1": 3, "I.8.14": 10, "III.15.12": 10,
              "I.12.2": 11, "I.16.6": 13}

_OPS = ("sin","cos","tanh","tan","exp","log","sqrt","abs","pow")
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

def _rel(pred, y, var):
    return float(np.mean((pred - y) ** 2) / var)

def _apply_noise(y, level, kind, rng):
    """Renvoie (y_bruite, sigma_effectif, plancher_de_bruit_relatif)."""
    if level <= 0:
        return y.copy(), 0.0, 0.0
    sd = float(np.std(y))
    if kind == "gauss":
        sigma = level * sd
        yn = y + rng.normal(0.0, sigma, size=y.shape)
    else:  # outlier : une fraction des points reçoit une perturbation massive
        yn = y.copy()
        k = max(1, int(round(level * len(y))))
        pos = rng.choice(len(y), size=k, replace=False)
        signs = rng.choice([-1.0, 1.0], size=k)
        yn[pos] = yn[pos] + signs * 10.0 * sd      # +/- 10 ecarts-types
        sigma = float(np.std(yn - y))
    floor = float(np.var(yn - y) / np.var(y))       # 1-R2 des donnees vs verite
    return yn, sigma, floor

def _done():
    if not os.path.exists(OUT): return set()
    ks = set()
    with open(OUT, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try:
                r = json.loads(line)
                ks.add((r["name"], r["level"], r["rep"], r["noise_kind"], r["arm"]))
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

def run(levels, eq_filter, kind, robust, N):
    done = _done()
    arm = "robust" if robust else "default"
    for idx, name, formula, nv, sampler, f, pool in PROBS:
        if eq_filter and name not in eq_filter: continue
        print(f"\n--- {name}   {formula}")
        for level in levels:
            for rep in range(REPEATS):
                key = (name, level, rep, kind, arm)
                if key in done:
                    print(f"  bruit={level:<6} rep={rep}  déjà fait — repris"); continue
                rng = R(1000 + idx + 10000 * rep)
                X = sampler(rng, N)
                y_clean = f(X)
                nrng = R(777 + idx + 100 * rep)
                y_noisy, sigma, floor = _apply_noise(y_clean, level, kind, nrng)
                ntr = int(round(0.7 * N))
                perm = rng.permutation(N); tr, te = perm[:ntr], perm[ntr:]
                names = [f"v{k}" for k in range(nv)]
                t0 = time.time()
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        r = symbolic_regression(
                            X[tr], y_noisy[tr], feature_names=names, operators=pool,
                            normalize="none", generations=30, speed="fast",
                            validation_split=0.15, seed=0, restarts=4,
                            robust=robust)
                    exc_txt = None
                except Exception as exc:
                    exc_txt, r = f"{type(exc).__name__}: {exc}", None
                dt = time.time() - t0
                if r is None:
                    with open(OUT, "a", encoding="utf-8") as fh:
                        fh.write(json.dumps(dict(name=name, level=level, rep=rep,
                            noise_kind=kind, arm=arm, status="ERROR",
                            error=exc_txt, time=round(dt,1),
                            engine_version=ENGINE)) + "\n")
                    print(f"  bruit={level:<6} rep={rep}  ERREUR {exc_txt[:50]}")
                    continue

                v_clean = float(np.var(y_clean[te]))
                v_noisy = float(np.var(y_noisy[te]))
                # front : on choisit le meilleur CONTRE LA CIBLE PROPRE
                front, seen = [], set()
                for e in list(r.pareto or []) + [r]:
                    try:
                        ec = _rel(e.predict(X[te]), y_clean[te], v_clean)
                    except Exception:
                        continue
                    k = (int(e.size), round(ec, 15))
                    if k in seen: continue
                    seen.add(k)
                    front.append({"size": int(e.size), "err_clean": ec,
                                  "err_noisy": _rel(e.predict(X[te]), y_noisy[te], v_noisy),
                                  "expr": e.expression})
                front.sort(key=lambda d: d["size"])
                best = min(front, key=lambda d: d["err_clean"])
                err_clean, sz = best["err_clean"], best["size"]
                census = _census(best["expr"])
                suspects = sorted((set(census) & _SUSPECT) - _expected(formula))
                # [correctif] Une forme compacte peut être structurellement
                # FAUSSE (ex. I.16.6 : l'approximation du 1er ordre a la bonne
                # taille et aucun opérateur parasite). On exige donc aussi que
                # le modèle batte le plancher de bruit — sinon il n'a rien
                # appris que les données ne disaient déjà.
                beats_floor = (err_clean < floor) if floor > 0 else (err_clean < 1e-9)
                compact = bool(not suspects and sz <= CANON_SIZE.get(name, 99) + 4)
                struct_ok = bool(compact and beats_floor)
                gain = (floor / err_clean) if (floor > 0 and err_clean > 0) else None
                if err_clean < 1e-9:            status = "EXACT"
                elif struct_ok:                 status = "RECOVERED"
                elif floor > 0 and err_clean < floor: status = "DENOISED"
                else:                           status = "MISS"

                rec = dict(
                    name=name, formula=formula, level=level, rep=rep,
                    noise_kind=kind, arm=arm, robust=robust,
                    status=status, struct_ok=struct_ok,
                    compact_form=compact, beats_floor=beats_floor,
                    err_clean=err_clean, err_noisy=best["err_noisy"],
                    noise_floor=floor, denoise_gain=gain,
                    noise_sigma=sigma, pb_size=sz, time=round(dt, 1),
                    n_total=N, n_train=ntr, n_test=N - ntr, n_vars=nv, pool=pool,
                    champion_err_clean=_rel(r.predict(X[te]), y_clean[te], v_clean),
                    engine_version=ENGINE,
                    pythonhashseed=os.environ.get("PYTHONHASHSEED"),
                    date=datetime.datetime.now().isoformat(timespec="seconds"),
                    seed=0, restarts=4, generations=30, speed="fast",
                    validation_split=0.15, normalize="none",
                    X_hash=hashlib.sha1(X.tobytes()).hexdigest()[:12],
                    y_noisy_hash=hashlib.sha1(y_noisy.tobytes()).hexdigest()[:12],
                    expr_full=r.expression, front=front,
                    ops_census=census, suspect_ops=suspects,
                )
                with open(OUT, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec) + "\n")
                g = f"gain x{gain:.0f}" if gain else ""
                print(f"  bruit={level:<6} rep={rep}  {status:<9} err_clean={err_clean:.1e} "
                      f"size={sz:<4} {g:<10} {dt:5.0f}s")
                sys.stdout.flush()

def bilan():
    if not os.path.exists(OUT):
        print("(pas encore de résultats)"); return
    rows = [json.loads(l) for l in open(OUT, encoding="utf-8") if l.strip()]
    rows = [r for r in rows if r.get("status") != "ERROR"]
    if not rows: print("(aucun résultat exploitable)"); return
    for kind in sorted({r["noise_kind"] for r in rows}):
        for arm in sorted({r["arm"] for r in rows if r["noise_kind"] == kind}):
            sub0 = [r for r in rows if r["noise_kind"] == kind and r["arm"] == arm]
            levels = sorted({r["level"] for r in sub0})
            names = []
            for r in sub0:
                if r["name"] not in names: names.append(r["name"])
            print(f"\n=== BRUIT '{kind}' — bras '{arm}' — moteur {ENGINE} ===")
            print("    (X=EXACT, R=RECOVERED forme canonique, D=DENOISED, M=MISS)")
            print(f"{'équation':<11}" + "".join(f"{l:>9}" for l in levels))
            for nm in names:
                line = f"{nm:<11}"
                for l in levels:
                    s = [r for r in sub0 if r["name"] == nm and r["level"] == l]
                    c = "".join({"EXACT":"X","RECOVERED":"R","DENOISED":"D",
                                 "MISS":"M"}[r["status"]] for r in s)
                    line += f"{c:>9}"
                print(line)
            print(f"\n{'bruit':>8} {'struct.':>9} {'gain méd.':>11} {'err_clean méd':>15}")
            for l in levels:
                s = [r for r in sub0 if r["level"] == l]
                ok = sum(1 for r in s if r["struct_ok"])
                gs = sorted(r["denoise_gain"] for r in s if r["denoise_gain"])
                ec = sorted(r["err_clean"] for r in s)
                g = f"x{gs[len(gs)//2]:.0f}" if gs else "-"
                print(f"{l:>8} {ok:>4}/{len(s):<4} {g:>11} {ec[len(ec)//2]:>15.2e}")
    print("\nLecture : 'struct.' = formes canoniques retrouvées (métrique "
          "principale).\n'gain' = combien de fois le modèle est plus proche de la "
          "vérité que\nles données bruitées elles-mêmes (>1 = le moteur débruite).")

if __name__ == "__main__":
    argv = sys.argv[1:]
    kind = "gauss"; robust = "--robust" in argv; eqs = None; N = DEFAULT_N
    if "--noise" in argv:  kind = argv[argv.index("--noise") + 1]
    if "--eq" in argv:     eqs = set(argv[argv.index("--eq") + 1].split(","))
    if "--n" in argv:      N = int(argv[argv.index("--n") + 1])
    levels = LEVELS_GAUSS if kind == "gauss" else LEVELS_OUTLIER
    if "--levels" in argv: levels = [float(x) for x in argv[argv.index("--levels") + 1].split(",")]
    if os.environ.get("PYTHONHASHSEED") != "0":
        print("!! ATTENTION : PYTHONHASHSEED != 0 — relancer avec PYTHONHASHSEED=0.")
    _check_engine()
    if "--bilan" in argv or "--summary" in argv:
        bilan()
    else:
        print(f"=== BANC DE BRUIT — régime '{kind}', bras "
              f"'{'robust' if robust else 'default'}', N={N}, {REPEATS} tirages ===")
        print(f"    niveaux : {levels}")
        print("    entraînement sur y bruité, ÉVALUATION contre y propre")
        run(levels, eqs, kind, robust, N)
        bilan()
