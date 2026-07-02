"""Banc Feynman pour GP_ELITE — 15 équations représentatives (AI Feynman / SRBench).

Critères :
  EXACT : 1−R²_test < 1e-9   (précision machine → récupération symbolique)
  NEAR  : 1−R²_test < 1e-3
Usage : python3 feynman_bench.py <i_debut> <i_fin>   (bornes d'équations, fin exclue)
Résultats ajoutés dans feyn_results.jsonl
"""
import numpy as np, time, json, sys, io, contextlib
from gp_elite import symbolic_regression

R = np.random.RandomState  # échantillonneurs déterministes par problème

def U(rng, lo, hi, n): return rng.uniform(lo, hi, n)

# (nom, formule_affichée, n_vars, sampler(rng,n)->X, f(X)->y, pool)
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
]

def run_range(i0, i1, out="feyn_results.jsonl"):
    for i in range(i0, min(i1, len(PROBS))):
        name, formula, nv, sampler, f, pool = PROBS[i]
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
        rec = dict(name=name, formula=formula, nv=nv, status=status,
                   one_minus_r2=one_minus_r2, pareto_best=pb, pb_size=pb_size,
                   time=round(dt,1), size=r.size, expr=r.expression[:90])
        with open(out, "a") as fh: fh.write(json.dumps(rec)+"\n")
        print(f"  {name:<10} {status:<6} champ={one_minus_r2:.1e} pareto={pb:.1e}"
              f"  ({dt:.0f}s)  {formula}")
        sys.stdout.flush()

if __name__ == "__main__":
    a, b = int(sys.argv[1]), int(sys.argv[2])
    print(f"=== BANC FEYNMAN — équations {a}..{b-1} (restarts=4, fast/30) ===")
    run_range(a, b)
