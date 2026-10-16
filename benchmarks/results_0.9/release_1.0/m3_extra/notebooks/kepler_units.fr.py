
import gp_elite
print('GP_ELITE', gp_elite.__version__, 'prêt.')

import os
import numpy as np
import pandas as pd

NAME = 'planets_simon1994.csv'
URL = ('https://raw.githubusercontent.com/ariel95500-create/gp-elite/main/'
       'examples/case_studies/data/' + NAME)
path = os.path.join('data', NAME)
df = pd.read_csv(path if os.path.exists(path) else URL, comment='#')

# 1 296 000 secondes d'arc dans un tour, 1000 ans dans un millénaire
df['period_yr'] = 1296000000.0 / df['mean_motion']
df['a3_over_T2'] = df['a_au']**3 / df['period_yr']**2
print(df[['planet', 'a_au', 'period_yr', 'a3_over_T2']].to_string(index=False))

from gp_elite import GPEliteRegressor

AU = 149597870700.0          # mètres dans une unité astronomique (UAI 2012)
YEAR = 365.25 * 86400.0      # secondes dans une année julienne
GM_IAU = 1.3271244e20        # m^3/s^2, valeur nominale (UAI 2015)

a = df['a_au'].to_numpy() * AU
T = df['period_yr'].to_numpy() * YEAR

est = GPEliteRegressor(units=['m'], target_units='s', unknown_constant=True,
                       generations=30, speed='fast', random_state=0,
                       parallel=False)
est.fit(a.reshape(-1, 1), T)

c = est.constant_value_
GM = (2 * np.pi / c) ** 2
print('loi       :', est.equation_)
print('constante :', c, est.constant_units_string())
print(f'G * M_sol : {GM:.6e} m^3/s^2   ({100 * (GM / GM_IAU - 1):+.3f} % de la valeur UAI)')

inner, outer = slice(0, 4), slice(4, 8)

est_in = GPEliteRegressor(units=['m'], target_units='s', unknown_constant=True,
                          generations=30, speed='fast', random_state=0,
                          parallel=False)
est_in.fit(a[inner].reshape(-1, 1), T[inner])

c_in = est_in.constant_value_
GM_in = (2 * np.pi / c_in) ** 2
print('loi, de Mercure à Mars :', est_in.equation_)
print('constante :', c_in, est_in.constant_units_string())
print(f'G * M_sol : {GM_in:.6e} m^3/s^2   ({100 * (GM_in / GM_IAU - 1):+.4f} % de la valeur UAI)')
print()
pred = est_in.predict(a[outer].reshape(-1, 1))
for name, p, t in zip(df['planet'][outer], pred, T[outer]):
    print(f'{name:8s} prédite {p / YEAR:9.4f} ans   table {t / YEAR:9.4f} ans   '
          f'écart {100 * (p / t - 1):+.3f} %')

x_au = df[['a_au']].to_numpy()
P = df['period_yr'].to_numpy()

plain = GPEliteRegressor(generations=30, speed='fast', random_state=0,
                         parallel=False)
plain.fit(x_au, P)
print('loi sans unités :', plain.equation_)
print()
for name, p, t in zip(df['planet'], plain.predict(x_au), P):
    print(f'{name:8s} écart {100 * (p / t - 1):+.3f} %')
