
import gp_elite
print('GP_ELITE', gp_elite.__version__, 'ready.')

import os
import numpy as np
import pandas as pd

NAME = 'hubble1929.csv'
URL = ('https://raw.githubusercontent.com/ariel95500-create/gp-elite/main/'
       'examples/case_studies/data/' + NAME)
path = os.path.join('data', NAME)
df = pd.read_csv(path if os.path.exists(path) else URL, comment='#')

d = df['distance_mpc'].to_numpy(float)
v = df['velocity_kms'].to_numpy(float)
print(df.to_string(index=False))

def r2(p, t):
    return 1 - np.mean((p - t) ** 2) / np.var(t)

def rmse(p, t):
    return np.sqrt(np.mean((p - t) ** 2))

k0 = d @ v / (d @ d)              # through the origin
b1, b0 = np.polyfit(d, v, 1)      # with an intercept
print(f'through the origin: v = {k0:.2f} d             '
      f'R2 {r2(k0 * d, v):.4f}   RMSE {rmse(k0 * d, v):.1f} km/s')
print(f'with an intercept : v = {b0:.2f} + {b1:.2f} d   '
      f'R2 {r2(b0 + b1 * d, v):.4f}   RMSE {rmse(b0 + b1 * d, v):.1f} km/s')

from gp_elite import GPEliteRegressor

X = d.reshape(-1, 1)

with_units = GPEliteRegressor(units=['Mpc'], target_units='km/s',
                              unknown_constant=True, generations=30,
                              speed='fast', random_state=0, parallel=False)
with_units.fit(X, v)
p = with_units.predict(X)
print('with units   :', with_units.equation_)
print('constant     :', with_units.constant_value_, with_units.constant_units_string())
print(f'               R2 {r2(p, v):.4f}   RMSE {rmse(p, v):.1f} km/s')

no_units = GPEliteRegressor(generations=30, speed='fast', random_state=0,
                            parallel=False)
no_units.fit(X, v)
p = no_units.predict(X)
print('without units:', no_units.equation_)
print(f'               R2 {r2(p, v):.4f}   RMSE {rmse(p, v):.1f} km/s')

near, far = d <= 1.1, d > 1.1
k_near = d[near] @ v[near] / (d[near] @ d[near])
print(f'{near.sum()} nebulae to fit, {far.sum()} to predict')
print(f'least squares through the origin: v = {k_near:.2f} d   '
      f'RMSE on the 6: {rmse(k_near * d[far], v[far]):.1f} km/s')

for label, kw in (('with units', dict(units=['Mpc'], target_units='km/s',
                                      unknown_constant=True)),
                  ('without units', {})):
    m = GPEliteRegressor(generations=30, speed='fast', random_state=0,
                         parallel=False, **kw)
    m.fit(X[near], v[near])
    print(f'{label:13s}: {m.equation_}   '
          f'RMSE on the 6: {rmse(m.predict(X[far]), v[far]):.1f} km/s')

v_lmreg = v.copy()
v_lmreg[9] = -200.0     # the tenth row, 0.63 Mpc, as in the R package lmreg

for label, kw in (('with units', dict(units=['Mpc'], target_units='km/s',
                                      unknown_constant=True)),
                  ('without units', {})):
    m = GPEliteRegressor(generations=30, speed='fast', random_state=0,
                         parallel=False, **kw)
    m.fit(X, v_lmreg)
    print(f'{label:13s}: {m.equation_}   R2 {r2(m.predict(X), v_lmreg):.4f}')
