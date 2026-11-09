## Run

| | |
|---|---|
| fits recorded | 2780 |
| crashes | 0 |
| engine_version | 1.3.0 (2780) |
| python | 3.11.18 (2780) |
| numpy | 2.4.6 (2780) |
| sklearn | 1.9.1 (2780) |
| avx512 | True (2780) |
| npy_disable |  (2780) |
| pythonhashseed | 0 (2780) |
| first and last record | 2026-11-09T04:35:30 to 2026-11-09T13:43:37 |

## Laws: decision bench, noise and frozen test set

| suite | fits | EXACT | NEAR | MISS | structure retrieved | median 1−R² | median time (s) | beyond budget, median / max (s) | median generations | formula_exact False |
|---|---|---|---|---|---|---|---|---|---|---|
| F41 | 205 | 171 | 7 | 27 |  | 1.29e-30 | 0.4 | 0.62 / 1.29 | 1 | 6 |
| F41N1 | 205 | 0 | 157 | 48 | 116 | 5.32e-06 | 30.6 | 0.60 / 1.52 | 105 | 9 |
| F41N10 | 205 | 0 | 104 | 101 | 87 | 0.000986 | 30.6 | 0.64 / 1.63 | 103 | 12 |
| TF78 | 390 | 214 | 53 | 123 |  | 1.83e-29 | 0.5 | 0.71 / 1.71 | 1 | 17 |
| TF78 main | 290 | 204 | 32 | 54 |  | 2.82e-30 | 0.4 | 0.67 / 1.44 | 1 | 7 |
| TF78 bonus | 100 | 10 | 21 | 69 |  | 0.00478 | 30.6 | 0.73 / 1.71 | 100 | 10 |
| TS14 test | 70 | 8 | 19 | 43 |  | 0.00267 | 30.7 | 0.82 / 1.71 | 94 | 11 |
| TS14 ood | 70 | 5 | 5 | 60 |  | 0.413 | 30.8 | 0.92 / 1.71 | 91 | 17 |

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
| trig | 7 | 35 | 13 | 4 |

## Out of domain, models that are not exact

| suite | models not exact | median 1−R² out of domain | collapses (R² < 0) | worst R² |
|---|---|---|---|---|
| F41 | 34 | 0.0698 | 6 | -2.08e+03 |
| F41N1 | 205 | 9.24e-06 | 11 | -821 |
| F41N10 | 205 | 0.00351 | 18 | -5.69e+05 |
| TF78 | 176 | 0.0337 | 13 | -385 |
| TF78 main | 86 | 0.0139 | 5 | -3.14 |
| TF78 bonus | 90 | 0.0425 | 8 | -385 |

## Real data and Strogatz, R² on the test rows

| suite | split | fits | median R² | mean R² | collapses (R² < 0) | worst R² | formula_exact False |
|---|---|---|---|---|---|---|---|
| R6 | folds | 30 | 0.809 | 0.774 | 0 | 0.372 | 1 |
| R6 | out of domain | 30 | 0.666 | -71.8 | 5 | -1.95e+03 | 1 |
| R7raw | folds | 35 | 0.879 | 0.802 | 0 | 0.0163 | 4 |
| R7raw | out of domain | 35 | 0.735 | -12.8 | 5 | -233 | 5 |
| TR25 | folds | 125 | 0.769 | -1.34e+04 | 9 | -1.68e+06 | 18 |
| TR25 | out of domain | 125 | 0.548 | -1.02e+20 | 37 | -1.28e+22 | 15 |
| TR25raw | folds | 125 | 0.781 | 0.477 | 7 | -22.2 | 16 |
| TR25raw | out of domain | 125 | 0.566 | -5.07e+15 | 28 | -6.33e+17 | 16 |
| TS14 | test | 70 | 0.997 | -0.255 | 1 | -84.6 | 11 |
| TS14 | out of domain | 70 | 0.587 | -2.58e+18 | 27 | -1.81e+20 | 17 |
