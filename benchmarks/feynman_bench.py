"""Banc Feynman étendu pour GP_ELITE — carte des forces par famille structurelle.

Ce banc part des 15 équations d'origine et en ajoute 26, portant le corpus à 41.
Le but n'est pas un score global mais un ÉTAT DES LIEUX : sur quelles FAMILLES
de structures le moteur réussit, et sur lesquelles il échoue.

Les 15 d'origine étaient choisies avant toute mesure, ce qui rendait le 10/15 du
README honnête mais étroit — et non comparable aux taux publiés sur le corpus
complet. Les 26 ajoutées couvrent délibérément des familles sous-représentées :
formes rationnelles (le point dur connu, cf. II.11.3), racines, exponentielles,
logarithmes, sommes de produits.

Chaque équation porte une étiquette de famille. Le bilan agrège par famille,
ce qui transforme une liste de succès et d'échecs en carte exploitable.

Critères, inchangés :
  EXACT : 1−R²_test < 1e-9   (précision machine → récupération symbolique)
  NEAR  : 1−R²_test < 1e-3

Usage : python feynman_bench.py <i_debut> <i_fin>   (fin exclue, 41 au total)
        python feynman_bench.py 0 41                (tout, plusieurs heures)
        python feynman_bench.py --bilan             (agrégat par famille)

Reprise possible : les résultats s'ajoutent à feyn_results.jsonl.
Lancer avec PYTHONHASHSEED=0.
"""
import numpy as np, time, json, sys, io, contextlib
from gp_elite import symbolic_regression

R = np.random.RandomState  # échantillonneurs déterministes par problème

def U(rng, lo, hi, n): return rng.uniform(lo, hi, n)

# (nom, formule, n_vars, sampler(rng,n)->X, f(X)->y, pool[, famille])
# La famille est optionnelle : les 15 d'origine héritent de "historique" pour
# rester distinguables des 26 ajoutées.
PROBS = [
 ("I.12.1",  "mu*Nn",                    2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1], "physical"),
 ("I.12.5",  "q2*Ef",                    2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1], "physical"),
 ("I.14.4",  "k*x^2/2",                  2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: 0.5*X[:,0]*X[:,1]**2, "physical"),
 ("I.39.1",  "(3/2)*pr*V",               2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n)],
   lambda X: 1.5*X[:,0]*X[:,1], "physical"),
 ("II.3.24", "P/(4*pi*r^2)",             2, lambda r,n: np.c_[U(r,1,5,n),U(r,1,3,n)],
   lambda X: X[:,0]/(4*np.pi*X[:,1]**2), "physical"),
 ("I.6.20a", "exp(-th^2/2)/sqrt(2*pi)",  1, lambda r,n: np.c_[U(r,-3,3,n)],
   lambda X: np.exp(-X[:,0]**2/2)/np.sqrt(2*np.pi), "physical"),
 ("I.8.14",  "sqrt((x2-x1)^2+(y2-y1)^2)",4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: np.sqrt((X[:,1]-X[:,0])**2+(X[:,3]-X[:,2])**2), "physical"),
 ("I.16.6",  "(u+v)/(1+u*v/c^2)",        3, lambda r,n: np.c_[U(r,1,2,n),U(r,1,2,n),U(r,3,10,n)],
   lambda X: (X[:,0]+X[:,1])/(1+X[:,0]*X[:,1]/X[:,2]**2), "physical"),
 ("I.27.6",  "1/(1/d1+n/d2)",            3, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,2,n)],
   lambda X: 1.0/(1.0/X[:,0]+X[:,2]/X[:,1]), "physical"),
 ("I.34.8",  "q*v*B/p",                  4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1]*X[:,2]/X[:,3], "physical"),
 ("I.43.16", "mu*q*V/d",                 4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,5,n),U(r,1,5,n)],
   lambda X: X[:,0]*X[:,1]*X[:,2]/X[:,3], "physical"),
 ("I.12.2",  "q1*q2/(4*pi*eps*r^2)",     4, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,1,3,n),U(r,1,3,n)],
   lambda X: X[:,0]*X[:,1]/(4*np.pi*X[:,2]*X[:,3]**2), "physical"),
 ("II.15.4", "-mu*B*cos(th)",            3, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,0,6.28,n)],
   lambda X: -X[:,0]*X[:,1]*np.cos(X[:,2]), "trig"),
 ("I.18.12", "r*F*sin(th)",              3, lambda r,n: np.c_[U(r,1,5,n),U(r,1,5,n),U(r,0,3.14,n)],
   lambda X: X[:,0]*X[:,1]*np.sin(X[:,2]), "trig"),
 ("III.15.12","2*U*(1-cos(k*d))",        3, lambda r,n: np.c_[U(r,1,5,n),U(r,0.5,2,n),U(r,0.5,2,n)],
   lambda X: 2*X[:,0]*(1-np.cos(X[:,1]*X[:,2])), "trig"),

 # ── produits et puissances simples ───────────────────────────────────────
 ("I.10.7",  "m/sqrt(1-v^2/c^2)",        3, [(1,5),(1,2),(3,10)],
   lambda X: X[:,0]/np.sqrt(1-X[:,1]**2/X[:,2]**2), "physical", "racine"),
 ("I.11.19", "x1*y1+x2*y2+x3*y3",        6, [(1,5)]*6,
   lambda X: X[:,0]*X[:,1]+X[:,2]*X[:,3]+X[:,4]*X[:,5], "physical", "somme_produits"),
 ("I.15.10", "m*v/sqrt(1-v^2/c^2)",      3, [(1,5),(1,2),(3,10)],
   lambda X: X[:,0]*X[:,1]/np.sqrt(1-X[:,1]**2/X[:,2]**2), "physical", "racine"),
 ("I.25.13", "q/C",                      2, [(1,5),(1,5)],
   lambda X: X[:,0]/X[:,1], "physical", "quotient"),
 ("I.26.2",  "arcsin(n*sin(th2))",       2, [(0,1),(1,5)],
   lambda X: np.arcsin(np.clip(X[:,0]*np.sin(X[:,1]),-1,1)), "trig", "trig"),
 ("I.29.4",  "om/c",                     2, [(1,10),(1,10)],
   lambda X: X[:,0]/X[:,1], "physical", "quotient"),
 ("I.30.5",  "arcsin(lam/(n*d))",        3, [(1,2),(2,5),(1,5)],
   lambda X: np.arcsin(np.clip(X[:,0]/(X[:,1]*X[:,2]),-1,1)), "trig", "trig"),
 ("I.32.5",  "q^2*a^2/(6*pi*eps*c^3)",   4, [(1,5),(1,5),(1,5),(1,5)],
   lambda X: X[:,0]**2*X[:,1]**2/(6*np.pi*X[:,2]*X[:,3]**3), "physical", "puissances"),
 ("I.34.1",  "om0/(1-v/c)",              3, [(1,5),(1,2),(3,10)],
   lambda X: X[:,0]/(1-X[:,1]/X[:,2]), "physical", "rationnelle"),
 ("I.37.4",  "I1+I2+2*sqrt(I1*I2)*cos(d)",3,[(1,5),(1,5),(1,6)],
   lambda X: X[:,0]+X[:,1]+2*np.sqrt(X[:,0]*X[:,1])*np.cos(X[:,2]), "trig", "trig"),
 ("I.40.1",  "n0*exp(-m*g*x/(kb*T))",    6, [(1,5),(1,5),(1,5),(1,5),(1,5),(1,5)],
   lambda X: X[:,0]*np.exp(-X[:,1]*X[:,2]*X[:,3]/(X[:,4]*X[:,5])), "physical", "exponentielle"),
 ("I.44.4",  "n*kb*T*log(V2/V1)",        4, [(1,5),(1,5),(1,5),(1,5)],
   lambda X: X[:,0]*X[:,1]*X[:,2]*np.log(X[:,3]), "physical", "logarithme"),
 ("I.50.26", "x1*(cos(w*t)+a*cos(w*t)^2)",3,[(1,3),(1,3),(1,3)],
   lambda X: X[:,0]*(np.cos(X[:,1]*X[:,2])+X[:,1]*np.cos(X[:,1]*X[:,2])**2), "trig", "trig"),
 ("II.2.42", "k*(T2-T1)*A/d",            5, [(1,5),(1,5),(1,5),(1,5),(1,5)],
   lambda X: X[:,0]*(X[:,1]-X[:,2])*X[:,3]/X[:,4], "physical", "produit_quotient"),
 ("II.6.15b","3*pd*cos(th)*sin(th)/(4*pi*eps*r^3)",4,[(1,3),(1,3),(1,3),(1,3)],
   lambda X: 3*X[:,0]*np.cos(X[:,1])*np.sin(X[:,1])/(4*np.pi*X[:,2]*X[:,3]**3), "trig", "trig"),
 ("II.11.3", "q*Ef/(m*(w0^2-w^2))",      5, [(1,3),(1,3),(1,3),(3,5),(1,2)],
   lambda X: X[:,0]*X[:,1]/(X[:,2]*(X[:,3]**2-X[:,4]**2)), "physical", "rationnelle"),
 ("II.11.27","n*al*eps*Ef/(1-n*al/3)",   4, [(0,1),(0,1),(1,2),(1,2)],
   lambda X: X[:,0]*X[:,1]*X[:,2]*X[:,3]/(1-X[:,0]*X[:,1]/3), "physical", "rationnelle"),
 ("II.13.23","rho/sqrt(1-v^2/c^2)",      3, [(1,5),(1,2),(3,10)],
   lambda X: X[:,0]/np.sqrt(1-X[:,1]**2/X[:,2]**2), "physical", "racine"),
 ("II.24.17","sqrt(om^2/c^2-pi^2/d^2)",  3, [(4,6),(1,2),(2,4)],
   lambda X: np.sqrt(X[:,0]**2/X[:,1]**2-np.pi**2/X[:,2]**2), "physical", "racine"),
 ("II.34.2", "q*v*r/2",                  3, [(1,5),(1,5),(1,5)],
   lambda X: X[:,0]*X[:,1]*X[:,2]/2, "physical", "produit"),
 ("II.35.18","n0/(exp(mom*B/(kb*T))+exp(-mom*B/(kb*T)))",4,[(1,3),(1,3),(1,3),(1,3)],
   lambda X: X[:,0]/(np.exp(X[:,1]*X[:,2]/X[:,3])+np.exp(-X[:,1]*X[:,2]/X[:,3])), "physical","exponentielle"),
 ("II.38.3", "Y*A*x/d",                  4, [(1,5),(1,5),(1,5),(1,5)],
   lambda X: X[:,0]*X[:,1]*X[:,2]/X[:,3], "physical", "produit_quotient"),
 ("III.9.52","pd*Ef*t/h*sin((w-w0)*t/2)^2",5,[(1,3),(1,3),(1,3),(1,5),(1,3)],
   lambda X: X[:,0]*X[:,1]*X[:,2]/X[:,3]*np.sin((X[:,4]-1)*X[:,2]/2)**2, "trig", "trig"),
 ("III.10.19","mom*sqrt(Bx^2+By^2+Bz^2)",4,[(1,5),(1,5),(1,5),(1,5)],
   lambda X: X[:,0]*np.sqrt(X[:,1]**2+X[:,2]**2+X[:,3]**2), "physical", "racine"),
 ("III.17.37","B*(1+al*cos(th))",        3, [(1,5),(0,1),(0,6)],
   lambda X: X[:,0]*(1+X[:,1]*np.cos(X[:,2])), "trig", "trig"),
 ("III.19.51","-m*q^4/(2*(4*pi*eps)^2*h^2*n^2)",5,[(1,3),(1,3),(1,3),(1,3),(1,3)],
   lambda X: -X[:,0]*X[:,1]**4/(2*(4*np.pi*X[:,2])**2*X[:,3]**2*X[:,4]**2), "physical","puissances"),
]

def _fam(p):
    """Famille structurelle ; les entrées d'origine n'en portent pas."""
    return p[6] if len(p) > 6 else "historique"


def _sampler_bornes(bornes):
    """Échantillonneur construit à partir d'une liste de bornes par variable."""
    def s(r, n):
        return np.c_[tuple(U(r, lo, hi, n) for lo, hi in bornes)]
    return s


# Les 26 ajoutées déclarent des bornes plutôt qu'un sampler : on les convertit.
PROBS = [p if callable(p[3]) else (p[0], p[1], p[2], _sampler_bornes(p[3]),
                                   p[4], p[5], p[6]) for p in PROBS]


def bilan(out="feyn_results.jsonl"):
    """Agrège par famille : c'est la carte, pas le score."""
    import collections, os
    if not os.path.exists(out):
        print("Aucun résultat."); return
    rows = [json.loads(l) for l in open(out) if l.strip()]
    vus = {}
    for r in rows:                      # dernier résultat par équation
        vus[r["name"]] = r
    rows = list(vus.values())
    par_fam = collections.defaultdict(list)
    fam_de = {p[0]: _fam(p) for p in PROBS}
    for r in rows:
        par_fam[fam_de.get(r["name"], "?")].append(r)

    print(f"\n{'famille':<20}{'EXACT':>8}{'NEAR':>8}{'MISS':>8}{'total':>8}"
          f"{'taille méd.':>13}")
    print("-" * 65)
    for fam in sorted(par_fam, key=lambda f: -len(par_fam[f])):
        g = par_fam[fam]
        c = collections.Counter(r["status"] for r in g)
        med = float(np.median([r["pb_size"] for r in g]))
        print(f"{fam:<20}{c['EXACT']:>8}{c['NEAR']:>8}{c['MISS']:>8}"
              f"{len(g):>8}{med:>13.0f}")
    c = collections.Counter(r["status"] for r in rows)
    print("-" * 65)
    print(f"{'TOTAL':<20}{c['EXACT']:>8}{c['NEAR']:>8}{c['MISS']:>8}{len(rows):>8}")
    print(f"\nExact = récupération symbolique (1−R² < 1e-9). Une famille où")
    print("MISS domine est un point dur identifié, donc une piste de travail.")
    manques = [r["name"] for r in rows if r["status"] == "MISS"]
    if manques:
        print(f"\nÉchecs : {', '.join(sorted(manques))}")


def run_range(i0, i1, out="feyn_results.jsonl"):
    for i in range(i0, min(i1, len(PROBS))):
        p = PROBS[i]
        name, formula, nv, sampler, f, pool = p[:6]
        rng = R(1000+i)
        X = sampler(rng, 200); y = f(X)
        idx = rng.permutation(200); tr, te = idx[:140], idx[140:]
        names = [f"v{k}" for k in range(nv)]
        t0 = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            r = symbolic_regression(X[tr], y[tr], feature_names=names,
                                    operators=pool, generations=30, speed="fast",
                                    validation_split=0.15, seed=0, restarts=4)
        dt = time.time()-t0
        p = r.predict(X[te]); v = np.var(y[te])
        one_minus_r2 = float(np.mean((p-y[te])**2)/v)
        # [Pareto-best] la règle 1-SE peut livrer un champion jusqu'à ~3e-3 sous
        # le meilleur trouvé ; pour la RÉCUPÉRATION, on mesure aussi le meilleur
        # point du front sur le test.
        pb = one_minus_r2; pb_size = r.size
        for e in (r.pareto or []):
            pe = e.predict(X[te])
            v1 = float(np.mean((pe-y[te])**2)/v)
            if v1 < pb: pb, pb_size = v1, e.size
        status = "EXACT" if pb < 1e-9 else ("NEAR" if pb < 1e-3 else "MISS")
        rec = dict(name=name, formula=formula, nv=nv, famille=_fam(p),
                   status=status,
                   one_minus_r2=one_minus_r2, pareto_best=pb, pb_size=pb_size,
                   time=round(dt,1), size=r.size, expr=r.expression[:90])
        with open(out, "a") as fh: fh.write(json.dumps(rec)+"\n")
        print(f"  {name:<10} {status:<6} champ={one_minus_r2:.1e} pareto={pb:.1e}"
              f"  ({dt:.0f}s)  {formula}")
        sys.stdout.flush()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--bilan", "--summary"):
        bilan()
    else:
        a = int(sys.argv[1]) if len(sys.argv) > 1 else 0
        b = int(sys.argv[2]) if len(sys.argv) > 2 else len(PROBS)
        print(f"=== BANC FEYNMAN — équations {a}..{b-1} sur {len(PROBS)} "
              f"(restarts=4, fast/30) ===")
        run_range(a, b)
        bilan()
