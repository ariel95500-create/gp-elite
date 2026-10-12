## Run

| | |
|---|---|
| fits recorded | 1775 |
| crashes | 0 |
| engine_version | 0.8.0 (1775) |
| python | 3.11.15 (1775) |
| numpy | 2.4.6 (1775) |
| sklearn | 1.9.1 (1775) |
| avx512 | True (1775) |
| npy_disable |  (1775) |
| pythonhashseed | 0 (1775) |
| first and last record | 2026-10-11T20:44:45 to 2026-10-12T03:55:34 |

## Laws: decision bench, noise and frozen test set

| suite | fits | EXACT | NEAR | MISS | structure retrieved | median 1−R² | median time (s) | beyond budget, median / max (s) | median generations | formula_exact False |
|---|---|---|---|---|---|---|---|---|---|---|
| F41 | 205 | 86 | 25 | 94 |  | 0.000622 | 30.8 | 1.34 / 2.62 | 56 | 8 |
| F41N1 | 205 | 0 | 98 | 107 | 66 | 0.00125 | 31.3 | 1.28 / 2.27 | 62 | 9 |
| F41N10 | 205 | 0 | 81 | 124 | 62 | 0.00211 | 31.2 | 1.24 / 2.03 | 61 | 10 |
| TF78 | 390 | 144 | 37 | 209 |  | 0.00144 | 30.8 | 1.33 / 2.40 | 54 | 15 |
| TF78 main | 290 | 143 | 25 | 122 |  | 2.61e-06 | 30.1 | 1.36 / 2.40 | 47 | 8 |
| TF78 bonus | 100 | 1 | 12 | 87 |  | 0.0129 | 31.3 | 1.28 / 2.18 | 61 | 7 |
| TS14 test | 70 | 7 | 15 | 48 |  | 0.00479 | 31.4 | 1.43 / 2.20 | 57 | 15 |
| TS14 ood | 70 | 5 | 3 | 62 |  | 0.437 | 31.4 | 1.46 / 2.21 | 56 | 12 |

## F41 by family

| family | equations | fits | EXACT | NEAR |
|---|---|---|---|---|
| exponentielle | 2 | 10 | 0 | 0 |
| historique | 15 | 75 | 52 | 6 |
| logarithme | 1 | 5 | 0 | 1 |
| produit | 1 | 5 | 5 | 0 |
| produit_quotient | 2 | 10 | 8 | 1 |
| puissances | 2 | 10 | 10 | 0 |
| quotient | 2 | 10 | 10 | 0 |
| racine | 5 | 25 | 0 | 8 |
| rationnelle | 3 | 15 | 0 | 8 |
| somme_produits | 1 | 5 | 1 | 0 |
| trig | 7 | 35 | 0 | 1 |

## Out of domain, models that are not exact

| suite | models not exact | median 1−R² out of domain | collapses (R² < 0) | worst R² |
|---|---|---|---|---|
| F41 | 119 | 0.0398 | 13 | -3.39e+03 |
| F41N1 | 205 | 0.00773 | 17 | -1.88e+03 |
| F41N10 | 205 | 0.00971 | 24 | -938 |
| TF78 | 246 | 0.0426 | 16 | -4.15e+03 |
| TF78 main | 147 | 0.0336 | 6 | -4.15e+03 |
| TF78 bonus | 99 | 0.0934 | 10 | -764 |

## Real data and Strogatz, R² on the test rows

| suite | split | fits | median R² | mean R² | collapses (R² < 0) | worst R² | formula_exact False |
|---|---|---|---|---|---|---|---|
| R6 | folds | 30 | 0.809 | 0.773 | 0 | 0.292 | 0 |
| R6 | out of domain | 30 | 0.630 | -7.03 | 5 | -224 | 0 |
| R7raw | folds | 35 | 0.879 | 0.796 | 0 | 0.0163 | 4 |
| R7raw | out of domain | 35 | 0.685 | -12.5 | 5 | -233 | 4 |
| TR25 | folds | 125 | 0.747 | -1.35e+04 | 10 | -1.68e+06 | 19 |
| TR25 | out of domain | 125 | 0.538 | -2.05e+03 | 37 | -2.54e+05 | 14 |
| TR25raw | folds | 125 | 0.754 | 0.00174 | 8 | -79.2 | 15 |
| TR25raw | out of domain | 125 | 0.566 | -147 | 27 | -1.71e+04 | 19 |
| TS14 | test | 70 | 0.995 | -7.36e+07 | 2 | -5.15e+09 | 15 |
| TS14 | out of domain | 70 | 0.563 | -7.96e+05 | 28 | -5.03e+07 | 12 |
