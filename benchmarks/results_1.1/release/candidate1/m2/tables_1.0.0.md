## Run

| | |
|---|---|
| fits recorded | 2780 |
| crashes | 0 |
| engine_version | 1.0.0 (2780) |
| python | 3.11.15 (2780) |
| numpy | 2.4.6 (2780) |
| sklearn | 1.9.1 (2780) |
| avx512 | True (2780) |
| npy_disable |  (2780) |
| pythonhashseed | 0 (2780) |
| first and last record | 2026-10-27T02:45:40 to 2026-10-27T13:32:03 |

## Laws: decision bench, noise and frozen test set

| suite | fits | EXACT | NEAR | MISS | structure retrieved | median 1−R² | median time (s) | beyond budget, median / max (s) | median generations | formula_exact False |
|---|---|---|---|---|---|---|---|---|---|---|
| F41 | 205 | 163 | 11 | 31 |  | 1.51e-30 | 0.5 | 0.86 / 1.46 | 1 | 2 |
| F41N1 | 205 | 0 | 151 | 54 | 108 | 5.32e-06 | 30.8 | 0.82 / 2.15 | 81 | 7 |
| F41N10 | 205 | 0 | 101 | 104 | 86 | 0.0011 | 30.8 | 0.82 / 1.83 | 80 | 5 |
| TF78 | 390 | 213 | 47 | 130 |  | 1.83e-29 | 0.6 | 0.80 / 1.97 | 1 | 9 |
| TF78 main | 290 | 203 | 29 | 58 |  | 2.82e-30 | 0.4 | 0.71 / 1.52 | 1 | 2 |
| TF78 bonus | 100 | 10 | 18 | 72 |  | 0.00569 | 30.8 | 0.84 / 1.97 | 88 | 7 |
| TS14 test | 70 | 8 | 20 | 42 |  | 0.0029 | 31.0 | 1.10 / 2.07 | 82 | 11 |
| TS14 ood | 70 | 5 | 3 | 62 |  | 0.343 | 30.9 | 1.04 / 1.72 | 82 | 13 |

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
| trig | 7 | 35 | 5 | 8 |

## Out of domain, models that are not exact

| suite | models not exact | median 1−R² out of domain | collapses (R² < 0) | worst R² |
|---|---|---|---|---|
| F41 | 42 | 0.0179 | 4 | -2.03e+03 |
| F41N1 | 205 | 1.47e-05 | 14 | -1.39e+03 |
| F41N10 | 205 | 0.00418 | 18 | -938 |
| TF78 | 177 | 0.0387 | 12 | -8.03e+04 |
| TF78 main | 87 | 0.0139 | 6 | -8.03e+04 |
| TF78 bonus | 90 | 0.0486 | 6 | -764 |

## Real data and Strogatz, R² on the test rows

| suite | split | fits | median R² | mean R² | collapses (R² < 0) | worst R² | formula_exact False |
|---|---|---|---|---|---|---|---|
| R6 | folds | 30 | 0.809 | 0.775 | 0 | 0.372 | 1 |
| R6 | out of domain | 30 | 0.698 | -71.8 | 5 | -1.95e+03 | 1 |
| R7raw | folds | 35 | 0.879 | 0.796 | 0 | 0.0163 | 3 |
| R7raw | out of domain | 35 | 0.735 | -12.5 | 5 | -233 | 4 |
| TR25 | folds | 125 | 0.769 | -1.35e+04 | 10 | -1.68e+06 | 18 |
| TR25 | out of domain | 125 | 0.538 | -1.02e+20 | 38 | -1.28e+22 | 12 |
| TR25raw | folds | 125 | 0.771 | 0.418 | 7 | -29.3 | 18 |
| TR25raw | out of domain | 125 | 0.578 | -142 | 26 | -1.71e+04 | 17 |
| TS14 | test | 70 | 0.997 | -0.249 | 1 | -84.6 | 11 |
| TS14 | out of domain | 70 | 0.657 | -2.95e+20 | 28 | -2.06e+22 | 13 |
