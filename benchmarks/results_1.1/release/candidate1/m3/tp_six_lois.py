
import time
import numpy as np
import gp_elite
from gp_elite import symbolic_regression
print('GP_ELITE', gp_elite.__version__, 'prêt.')

def mesures(loi, plages, n=10, erreur=0.02, graine=0):
    rng = np.random.default_rng(graine)
    if len(plages) == 1:
        lo, hi = plages[0]
        X = np.linspace(lo, hi, n).reshape(-1, 1)
    else:
        X = np.column_stack([rng.uniform(lo, hi, n) for lo, hi in plages])
    y = loi(X) * (1 + erreur * rng.standard_normal(n))
    return X, y


def chercher(X, y, noms, unites, unite_cible, constante_inconnue):
    t0 = time.time()
    r = symbolic_regression(X, y, feature_names=noms,
                            units=dict(zip(noms, unites)),
                            target_units=unite_cible,
                            unknown_constant=constante_inconnue,
                            parallel=False, seed=0)
    print(f'formule trouvée : {r.expression}   ({time.time() - t0:.0f} s)')
    return r


def coefficient(r):
    # le facteur numérique devant la formule
    return float(r.sympy_expr().as_coeff_Mul()[0])

X, T = mesures(lambda X: 2 * np.pi * np.sqrt(X[:, 0] / 9.81), [(0.10, 1.00)])
r = chercher(X, T, ['L'], ['m'], 's', constante_inconnue=True)
c = coefficient(r)
print(f'T = {c:.4f} * sqrt(L), donc g = (2*pi/{c:.4f})^2 = {(2 * np.pi / c) ** 2:.2f} m/s^2')

X, T = mesures(lambda X: 2 * np.pi * np.sqrt(X[:, 0] / X[:, 1]),
               [(0.05, 0.50), (10.0, 50.0)])
r = chercher(X, T, ['m', 'k'], ['kg', 'kg/s^2'], 's', constante_inconnue=False)
print(f'facteur devant la racine : {coefficient(r):.4f}  (2*pi = {2 * np.pi:.4f})')

X, d = mesures(lambda X: 0.5 * 9.81 * X[:, 0] ** 2, [(0.10, 0.60)])
r = chercher(X, d, ['t'], ['s'], 'm', constante_inconnue=True)
c = coefficient(r)
print(f'd = {c:.4f} * t^2, donc g = 2 * {c:.4f} = {2 * c:.2f} m/s^2')

X, P = mesures(lambda X: X[:, 0] ** 2 / X[:, 1], [(1.0, 12.0), (10.0, 100.0)])
r = chercher(X, P, ['U', 'R'], ['kg*m^2/(s^3*A)', 'kg*m^2/(s^3*A^2)'],
             'kg*m^2/s^3', constante_inconnue=False)

X, P = mesures(lambda X: X[:, 0] * 8.314 * X[:, 1] / X[:, 2],
               [(0.01, 0.10), (273.0, 373.0), (1e-3, 5e-3)])
r = chercher(X, P, ['n', 'T', 'V'], ['mol', 'K', 'm^3'], 'kg/(m*s^2)',
             constante_inconnue=True)
print(f'R = {coefficient(r):.3f} J/(mol K)  (valeur exacte 8.314)')

X, E = mesures(lambda X: 10.0 / (4 * np.pi * X[:, 0] ** 2), [(0.2, 2.0)])
r = chercher(X, E, ['d'], ['m'], 'kg/s^3', constante_inconnue=True)
c = coefficient(r)
print(f'E = {c:.4f} / d^2, donc P = 4*pi*{c:.4f} = {4 * np.pi * c:.2f} W  (valeur exacte 10 W)')
