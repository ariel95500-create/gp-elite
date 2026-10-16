
import gp_elite
print('GP_ELITE', gp_elite.__version__, 'ready.')

import numpy as np
import pandas as pd

URL = '/tmp/claude-0/-home-user/bc0c332b-bd15-5108-8e98-a0d2a0e03650/scratchpad/work10/benchmarks/_pmlb_cache/nikuradse_1.tsv.gz'   # the PMLB file, local copy checked by SHA-256
df = pd.read_csv(URL, sep='\t', compression='gzip')

X = df[['r_k', 'log_Re']].to_numpy(float)
y = df['target'].to_numpy(float)
print(len(y), 'measurements, roughness ratios', sorted(df['r_k'].unique().tolist()))

rng = np.random.RandomState(0)
idx = rng.permutation(len(y))
ntr = int(0.7 * len(y))
tr, te = idx[:ntr], idx[ntr:]

def r2(p, t):
    return 1 - np.mean((p - t) ** 2) / np.var(t)

def pvk(Z):     # Prandtl-von Karman, fully rough regime
    return 2.0 - 2.0 * np.log10(2.0 * np.log10(np.abs(Z[:, 0]) + 1e-12) + 1.74)

def line(basis, itr, ite):     # least squares on a basis, R2 on ite
    A = np.c_[np.ones(len(itr)), basis(X[itr])]
    coef = np.linalg.lstsq(A, y[itr], rcond=None)[0]
    return r2(np.c_[np.ones(len(ite)), basis(X[ite])] @ coef, y[ite])

logs = lambda Z: np.c_[np.log10(np.abs(Z[:, 0]) + 1e-12), Z[:, 1]]
print(f'{len(tr)} rows to fit, {len(te)} to test')
print(f'straight line, fitted          R2 test {line(lambda Z: Z, tr, te):.4f}')
print(f'line in log10(r_k), fitted     R2 test {line(logs, tr, te):.4f}')
print(f'Prandtl-von Karman, no fitting R2 test {r2(pvk(X[te]), y[te]):.4f}'
      f'   (all rows {r2(pvk(X), y):.4f})')

import time
from gp_elite import symbolic_regression

def search(Xf, yf):
    return symbolic_regression(Xf, yf, feature_names=['r_k', 'log_Re'],
                               operators='physical', normalize='auto',
                               generations=30, speed='fast',
                               validation_split=0.15, seed=0, restarts=4,
                               parallel=False)

def front(model, Zt, yt):
    rows = {}
    for e in list(model.pareto or []) + [model]:
        rows.setdefault((int(e.size), round(r2(e.predict(Zt), yt), 6)), e)
    return sorted(rows.items(), key=lambda kv: kv[0])

t0 = time.time()
m = search(X[tr], y[tr])
print(f'searched for {time.time() - t0:.0f} s\n')
print('size  R2 test  expression')
for (s, r), e in front(m, X[te], y[te]):
    print(f'{s:>4}  {r:7.4f}  {e.expression[:90]}')

out = np.isclose(X[:, 0], 126.0)
Xin, yin, Xout, yout = X[~out], y[~out], X[out], y[out]

def bias(pred):
    return (np.mean(pred) - np.mean(yout)) / np.std(yout)

t0 = time.time()
m2 = search(Xin, yin)
print(f'searched for {time.time() - t0:.0f} s')
print(f'{len(yin)} rows to fit (five roughness ratios), {len(yout)} to predict\n')
print(f'Prandtl-von Karman: level gap {bias(pvk(Xout)):+.3f} sd')
print('size  level gap  expression')
for (s, r), e in front(m2, Xout, yout):
    print(f'{s:>4}  {bias(e.predict(Xout)):+.3f} sd   {e.expression[:70]}')
