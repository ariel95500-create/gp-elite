## Run

| | |
|---|---|
| fits recorded | 1775 |
| crashes | 0 |
| engine_version | 1.0.0 (1775) |
| python | 3.11.15 (1775) |
| numpy | 2.4.6 (1775) |
| sklearn | 1.9.1 (1775) |
| avx512 | True (1775) |
| npy_disable |  (1775) |
| pythonhashseed | 0 (1775) |
| first and last record | 2026-10-14T00:48:15 to 2026-10-14T07:52:33 |

## Laws: decision bench, noise and frozen test set

| suite | fits | EXACT | NEAR | MISS | structure retrieved | median 1−R² | median time (s) | beyond budget, median / max (s) | median generations | formula_exact False |
|---|---|---|---|---|---|---|---|---|---|---|
| F41 | 205 | 163 | 10 | 32 |  | 1.51e-30 | 0.6 | 0.88 / 1.58 | 1 | 2 |
| F41N1 | 205 | 0 | 148 | 57 | 105 | 6.85e-06 | 30.9 | 0.89 / 1.89 | 71 | 9 |
| F41N10 | 205 | 0 | 102 | 103 | 85 | 0.00101 | 30.9 | 0.93 / 1.98 | 71 | 6 |
| TF78 | 390 | 213 | 43 | 134 |  | 1.83e-29 | 0.7 | 0.99 / 2.00 | 1 | 8 |
| TF78 main | 290 | 203 | 29 | 58 |  | 2.82e-30 | 0.6 | 0.90 / 1.89 | 1 | 2 |
| TF78 bonus | 100 | 10 | 14 | 76 |  | 0.00691 | 31.0 | 1.03 / 2.00 | 74 | 6 |
| TS14 test | 70 | 7 | 17 | 46 |  | 0.00393 | 31.3 | 1.34 / 1.97 | 69 | 12 |
| TS14 ood | 70 | 5 | 3 | 62 |  | 0.356 | 31.1 | 1.29 / 2.03 | 67 | 13 |

## F41 by family

| family | equations | fits | EXACT | NEAR |
|---|---|---|---|---|
| exponentielle | 2 | 10 | 10 | 0 |
| historique | 15 | 75 | 73 | 1 |
| logarithme | 1 | 5 | 5 | 0 |
| produit | 1 | 5 | 5 | 0 |
| produit_quotient | 2 | 10 | 9 | 0 |
| puissances | 2 | 10 | 10 | 0 |
| quotient | 2 | 10 | 10 | 0 |
| racine | 5 | 25 | 20 | 1 |
| rationnelle | 3 | 15 | 15 | 0 |
| somme_produits | 1 | 5 | 1 | 0 |
| trig | 7 | 35 | 5 | 8 |

## Out of domain, models that are not exact

| suite | models not exact | median 1−R² out of domain | collapses (R² < 0) | worst R² |
|---|---|---|---|---|
| F41 | 42 | 0.0194 | 5 | -145 |
| F41N1 | 205 | 1.51e-05 | 15 | -1.88e+03 |
| F41N10 | 205 | 0.00411 | 19 | -938 |
| TF78 | 177 | 0.0424 | 16 | -4.15e+03 |
| TF78 main | 87 | 0.0139 | 7 | -4.15e+03 |
| TF78 bonus | 90 | 0.0869 | 9 | -764 |

## Real data and Strogatz, R² on the test rows

| suite | split | fits | median R² | mean R² | collapses (R² < 0) | worst R² | formula_exact False |
|---|---|---|---|---|---|---|---|
| R6 | folds | 30 | 0.809 | 0.775 | 0 | 0.372 | 0 |
| R6 | out of domain | 30 | 0.630 | -7.03 | 5 | -224 | 0 |
| R7raw | folds | 35 | 0.879 | 0.796 | 0 | 0.0163 | 3 |
| R7raw | out of domain | 35 | 0.685 | -12.5 | 6 | -233 | 4 |
| TR25 | folds | 125 | 0.766 | -1.35e+04 | 10 | -1.68e+06 | 19 |
| TR25 | out of domain | 125 | 0.538 | -1.33e+10 | 37 | -1.66e+12 | 11 |
| TR25raw | folds | 125 | 0.758 | 0.416 | 7 | -29.3 | 15 |
| TR25raw | out of domain | 125 | 0.566 | -145 | 27 | -1.71e+04 | 16 |
| TS14 | test | 70 | 0.996 | -0.251 | 1 | -84.6 | 12 |
| TS14 | out of domain | 70 | 0.644 | -3.79e+12 | 27 | -2.65e+14 | 13 |
