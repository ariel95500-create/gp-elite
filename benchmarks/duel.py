"""Duel GP_ELITE vs gplearn — mêmes données, mêmes splits, budgets comparables.
À lancer avec PYTHONHASHSEED=0 pour des chiffres gelés.
Usage: PYTHONHASHSEED=0 python3 duel.py <i0> <i1>
"""
import numpy as np, time, json, sys, io, contextlib, warnings
warnings.filterwarnings("ignore")
from feynman_bench import PROBS
from gp_elite import symbolic_regression
from gplearn.genetic import SymbolicRegressor
from gplearn.functions import make_function

_exp = make_function(function=lambda x: np.exp(np.clip(x, -50.0, 50.0)), name='exp', arity=1)
BASE = ('add','sub','mul','div','sqrt','log','neg','inv','abs', _exp)

def status(e): return "EXACT" if e < 1e-9 else ("NEAR" if e < 1e-3 else "MISS")

def run_range(i0, i1, out="duel_results.jsonl"):
    for i in range(i0, min(i1, len(PROBS))):
        name, formula, nv, sampler, f, pool = PROBS[i]
        rng = np.random.RandomState(1000 + i)
        X = sampler(rng, 200); y = f(X)
        idx = rng.permutation(200); tr, te = idx[:140], idx[140:]
        vte = np.var(y[te])
        # ── GP_ELITE (restarts=4, fast/30) ──
        t0 = time.time()
        with contextlib.redirect_stdout(io.StringIO()):
            r = symbolic_regression(X[tr], y[tr],
                    feature_names=[f"v{k}" for k in range(nv)],
                    operators=pool, generations=30, speed="fast",
                    validation_split=0.15, seed=0, restarts=4)
        tg = time.time() - t0
        eg = float(np.mean((r.predict(X[te]) - y[te])**2) / vte)
        for pe in (r.pareto or []):
            eg = min(eg, float(np.mean((pe.predict(X[te]) - y[te])**2) / vte))
        # ── gplearn (pop 2000 × 30 gens, pool équivalent) ──
        fs = BASE + (('sin','cos') if pool == "trig" else ())
        t0 = time.time()
        gp = SymbolicRegressor(population_size=2000, generations=30,
                               function_set=fs, parsimony_coefficient=0.001,
                               random_state=0, n_jobs=1, verbose=0)
        gp.fit(X[tr], y[tr])
        tl = time.time() - t0
        pl = gp.predict(X[te])
        el = float(np.mean((pl - y[te])**2) / vte) if np.all(np.isfinite(pl)) else float("inf")
        rec = dict(name=name, gpe=status(eg), gpe_err=eg, gpe_t=round(tg,1),
                   gpl=status(el), gpl_err=el, gpl_t=round(tl,1))
        with open(out, "a") as fh: fh.write(json.dumps(rec) + "\n")
        print(f"  {name:<10} GPE:{status(eg):<6}{eg:.1e} ({tg:>3.0f}s) | "
              f"gplearn:{status(el):<6}{el:.1e} ({tl:>3.0f}s)")
        sys.stdout.flush()

if __name__ == "__main__":
    run_range(int(sys.argv[1]), int(sys.argv[2]))
