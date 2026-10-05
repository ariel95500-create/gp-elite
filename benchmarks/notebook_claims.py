"""The code of the notebooks' examples, run as written, printing what the
figures in the notebooks' text come from.

    PYTHONHASHSEED=0 python benchmarks/notebook_claims.py <snippet>

snippet: kepler30 hooke coulomb torque optionB tp nikuradse (one process
each). Output of the 0.8.0 run: benchmarks/results_0.8/notebook_snippets.txt
(0.7.0: benchmarks/results_0.7/notebook_snippets.txt).
Times depend on the machine; the rest does not.
"""
import os, sys, time, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gp_elite import symbolic_regression, GPEliteRegressor

def kepler30():
    distance = np.array([0.387, 0.723, 1.000, 1.524, 5.203, 9.537, 19.191, 30.069])
    period   = np.array([0.241, 0.615, 1.000, 1.881, 11.862, 29.457, 84.011, 164.79])
    t0 = time.time()
    result = symbolic_regression(distance.reshape(-1, 1), period, feature_names=['distance'],
                                 operators='physical', generations=30, speed='fast', seed=0)
    print(result.expression, " (%.0fs)" % (time.time() - t0))

def hooke():
    rng = np.random.RandomState(0)
    elongation = rng.uniform(0.01, 0.10, 150).reshape(-1, 1)
    force = 250.0 * elongation[:, 0]
    est = GPEliteRegressor(units=['m'], target_units='N', unknown_constant=True,
                           generations=25, speed='fast', random_state=0)
    est.fit(elongation, force)
    print('deduced units :', est.constant_units_string())
    print('deduced value :', round(est.constant_value_, 4))
    print('equation      :', est.equation_)

def coulomb():
    rng = np.random.RandomState(0)
    q1 = rng.uniform(1, 5, 200); q2 = rng.uniform(1, 5, 200)
    eps = rng.uniform(1, 3, 200); r = rng.uniform(1, 3, 200)
    X = np.column_stack([q1, q2, eps, r]); y = q1 * q2 / (4 * np.pi * eps * r**2)
    t0 = time.time()
    model = symbolic_regression(X, y, feature_names=["q1", "q2", "eps", "r"], operators="physical",
                                normalize="none", generations=25, speed="fast", restarts=3, seed=0)
    print(f"found in {time.time()-t0:.0f} s")
    print("equation :", model.expression)
    print("1/(4*pi) =", round(1/(4*np.pi), 6))

def torque():
    rng = np.random.RandomState(13)
    r_ = rng.uniform(1, 5, 200); F_ = rng.uniform(1, 5, 200); theta = rng.uniform(0, np.pi, 200)
    X2 = np.column_stack([r_, F_, theta]); y2 = r_ * F_ * np.sin(theta)
    def run(label, **extra):
        t0 = time.time()
        m = symbolic_regression(X2, y2, feature_names=["r", "F", "theta"], operators="trig",
                                normalize="none", generations=25, speed="fast", restarts=3, seed=0, **extra)
        err = np.mean((m.predict(X2) - y2)**2) / np.var(y2)
        print(f"{label:<22} {time.time()-t0:5.0f} s   error={err:.1e}   size={m.size}")
        print(f"{'':22} {m.expression}")
    run("without units")
    run("with units", units=[{"m": 1}, {"kg": 1, "m": 1, "s": -2}, {}],
        target_units={"kg": 1, "m": 2, "s": -2})

def optionB():
    pressure = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5]
    volume   = [2.0, 2.0, 2.0, 3.0, 3.0, 3.0, 4.0, 4.0, 5.0, 5.0]
    energy   = [3.0, 4.5, 6.0, 11.25, 13.5, 15.75, 24.0, 27.0, 37.5, 41.25]
    Xu = np.column_stack([pressure, volume]); yu = np.asarray(energy, dtype=float)
    model = symbolic_regression(Xu, yu, feature_names=["pressure", "volume"], operators="physical",
                                generations=30, speed="fast", restarts=4, seed=0)
    print("equation:", model.expression)

def tp():
    rng = np.random.RandomState(0); x = rng.uniform(-3, 3, 200)
    X, y = np.column_stack([x]), x * np.sin(x**2) * np.cos(x/2)
    res = symbolic_regression(X, y, feature_names=['x'], operators='full', generations=40, speed='fast', seed=0)
    print("TP loi :", res.expression)
    for g in (10, 30, 60):
        t = time.time()
        r = symbolic_regression(X, y, feature_names=['x'], operators='full', generations=g, speed='fast', seed=0)
        print(f'{g:>3} generations : MSE = {np.mean((y - r.predict(X))**2):.3e}   taille = {r.size:<3} ({time.time()-t:.0f} s)')

def nikuradse():
    import pmlb_frozen
    df = pmlb_frozen.load_frame("nikuradse_1")
    Xn = df[["r_k", "log_Re"]].to_numpy(float); yn = df["target"].to_numpy(float)
    pvk = lambda r_k: 2.0 - 2.0 * np.log10(2.0 * np.log10(r_k) + 1.74)
    print("PvK R2 = %.4f" % (1 - np.mean((pvk(Xn[:, 0]) - yn)**2) / np.var(yn)))
    t0 = time.time()
    m = symbolic_regression(Xn, yn, feature_names=["r_k", "log_Re"], operators="physical",
                            normalize="none", generations=30, speed="fast", restarts=2, seed=0)
    print(f"searched for {time.time()-t0:.0f} s")
    r2 = lambda e: 1 - np.mean((e.predict(Xn) - yn)**2) / np.var(yn)
    print("size  R2      formula_exact  expression")
    for e in sorted(list(m.pareto or []) + [m], key=lambda e: e.size):
        print(f"{e.size:>4}  {r2(e):>6.4f}  {str(e.formula_exact):<13}  {e.expression[:90]}")
    with np.errstate(over="ignore"):
        big = int(np.sum(Xn[:, 0] ** Xn[:, 1] > 1e6))
    print(f"rows where r_k ** log_Re exceeds 1e6: {big} of {len(yn)}")

if __name__ == "__main__":
    globals()[sys.argv[1]]()
