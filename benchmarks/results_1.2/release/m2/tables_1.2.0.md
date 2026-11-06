## Run

| | |
|---|---|
| fits recorded | 2780 |
| crashes | 0 |
| engine_version | 1.2.0 (2780) |
| python | 3.11.18 (2780) |
| numpy | 2.4.6 (2780) |
| sklearn | 1.9.1 (2780) |
| avx512 | True (2780) |
| npy_disable |  (2780) |
| pythonhashseed | 0 (2780) |
| first and last record | 2026-11-04T18:24:04 to 2026-11-05T04:19:00 |

## Laws: decision bench, noise and frozen test set

| suite | fits | EXACT | NEAR | MISS | structure retrieved | median 1−R² | median time (s) | beyond budget, median / max (s) | median generations | formula_exact False |
|---|---|---|---|---|---|---|---|---|---|---|
| F41 | 205 | 163 | 12 | 30 |  | 1.51e-30 | 0.4 | 0.59 / 1.17 | 1 | 1 |
| F41N1 | 205 | 0 | 154 | 51 | 108 | 5.32e-06 | 30.6 | 0.56 / 1.36 | 117 | 7 |
| F41N10 | 205 | 0 | 101 | 104 | 85 | 0.0011 | 30.6 | 0.61 / 1.61 | 114 | 7 |
| TF78 | 390 | 214 | 54 | 122 |  | 1.83e-29 | 0.5 | 0.64 / 1.78 | 1 | 8 |
| TF78 main | 290 | 204 | 32 | 54 |  | 2.82e-30 | 0.4 | 0.59 / 1.67 | 1 | 1 |
| TF78 bonus | 100 | 10 | 22 | 68 |  | 0.00483 | 30.6 | 0.67 / 1.78 | 106 | 7 |
| TS14 test | 70 | 10 | 19 | 41 |  | 0.00202 | 30.7 | 0.83 / 1.61 | 102 | 10 |
| TS14 ood | 70 | 5 | 3 | 62 |  | 0.343 | 30.7 | 0.88 / 1.49 | 101 | 12 |

## F41 by family

| family | equations | fits | EXACT | NEAR |
|---|---|---|---|---|
| exponentielle | 2 | 10 | 10 | 0 |
| historique | 15 | 75 | 73 | 1 |
| logarithme | 1 | 5 | 5 | 0 |
| produit | 1 | 5 | 5 | 0 |
| produit_quotient | 2 | 10 | 9 | 1 |
| puissances | 2 | 10 | 10 | 0 |
| quotient | 2 | 10 | 10 | 0 |
| racine | 5 | 25 | 20 | 1 |
| rationnelle | 3 | 15 | 15 | 0 |
| somme_produits | 1 | 5 | 1 | 0 |
| trig | 7 | 35 | 5 | 9 |

## Out of domain, models that are not exact

| suite | models not exact | median 1−R² out of domain | collapses (R² < 0) | worst R² |
|---|---|---|---|---|
| F41 | 42 | 0.0194 | 7 | -97.6 |
| F41N1 | 205 | 1.47e-05 | 13 | -1.39e+03 |
| F41N10 | 205 | 0.00351 | 20 | -938 |
| TF78 | 176 | 0.0308 | 14 | -764 |
| TF78 main | 86 | 0.0139 | 6 | -5.3 |
| TF78 bonus | 90 | 0.0429 | 8 | -764 |

## Real data and Strogatz, R² on the test rows

| suite | split | fits | median R² | mean R² | collapses (R² < 0) | worst R² | formula_exact False |
|---|---|---|---|---|---|---|---|
| R6 | folds | 30 | 0.809 | 0.774 | 0 | 0.372 | 1 |
| R6 | out of domain | 30 | 0.630 | -71.8 | 5 | -1.95e+03 | 1 |
| R7raw | folds | 35 | 0.879 | 0.783 | 1 | -0.668 | 5 |
| R7raw | out of domain | 35 | 0.735 | -12.8 | 5 | -233 | 5 |
| TR25 | folds | 125 | 0.769 | -1.34e+04 | 9 | -1.68e+06 | 18 |
| TR25 | out of domain | 125 | 0.548 | -1.02e+20 | 38 | -1.28e+22 | 15 |
| TR25raw | folds | 125 | 0.771 | 0.424 | 8 | -22.2 | 16 |
| TR25raw | out of domain | 125 | 0.566 | -5.07e+15 | 28 | -6.33e+17 | 16 |
| TS14 | test | 70 | 0.998 | -0.243 | 1 | -84.6 | 10 |
| TS14 | out of domain | 70 | 0.657 | -2.58e+18 | 28 | -1.81e+20 | 12 |
