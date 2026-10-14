## Run

| | |
|---|---|
| fits recorded | 1775 |
| crashes | 0 |
| engine_version | 0.9.0 (1775) |
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
| F41 | 205 | 88 | 28 | 89 |  | 0.0005 | 30.6 | 1.16 / 1.96 | 70 | 6 |
| F41N1 | 205 | 0 | 101 | 104 | 67 | 0.0011 | 31.1 | 1.12 / 1.97 | 71 | 11 |
| F41N10 | 205 | 0 | 85 | 120 | 66 | 0.00191 | 31.0 | 1.02 / 1.91 | 71 | 11 |
| TF78 | 390 | 145 | 41 | 204 |  | 0.00127 | 30.6 | 1.08 / 1.92 | 68 | 15 |
| TF78 main | 290 | 144 | 29 | 117 |  | 2.57e-06 | 29.3 | 1.12 / 1.87 | 56 | 9 |
| TF78 bonus | 100 | 1 | 12 | 87 |  | 0.0123 | 31.0 | 1.03 / 1.92 | 75 | 6 |
| TS14 test | 70 | 8 | 16 | 46 |  | 0.00515 | 31.2 | 1.25 / 2.19 | 70 | 12 |
| TS14 ood | 70 | 5 | 3 | 62 |  | 0.356 | 31.2 | 1.23 / 1.91 | 68 | 14 |

## F41 by family

| family | equations | fits | EXACT | NEAR |
|---|---|---|---|---|
| exponentielle | 2 | 10 | 0 | 0 |
| historique | 15 | 75 | 53 | 5 |
| logarithme | 1 | 5 | 0 | 1 |
| produit | 1 | 5 | 5 | 0 |
| produit_quotient | 2 | 10 | 9 | 0 |
| puissances | 2 | 10 | 10 | 0 |
| quotient | 2 | 10 | 10 | 0 |
| racine | 5 | 25 | 0 | 11 |
| rationnelle | 3 | 15 | 0 | 9 |
| somme_produits | 1 | 5 | 1 | 0 |
| trig | 7 | 35 | 0 | 2 |

## Out of domain, models that are not exact

| suite | models not exact | median 1−R² out of domain | collapses (R² < 0) | worst R² |
|---|---|---|---|---|
| F41 | 117 | 0.0326 | 11 | -3.39e+03 |
| F41N1 | 205 | 0.00676 | 14 | -1.88e+03 |
| F41N10 | 205 | 0.0101 | 24 | -938 |
| TF78 | 245 | 0.0415 | 15 | -4.15e+03 |
| TF78 main | 146 | 0.0321 | 6 | -4.15e+03 |
| TF78 bonus | 99 | 0.0825 | 9 | -764 |

## Real data and Strogatz, R² on the test rows

| suite | split | fits | median R² | mean R² | collapses (R² < 0) | worst R² | formula_exact False |
|---|---|---|---|---|---|---|---|
| R6 | folds | 30 | 0.809 | 0.775 | 0 | 0.372 | 0 |
| R6 | out of domain | 30 | 0.630 | -7.03 | 5 | -224 | 0 |
| R7raw | folds | 35 | 0.879 | 0.796 | 0 | 0.0163 | 4 |
| R7raw | out of domain | 35 | 0.685 | -12.5 | 6 | -233 | 4 |
| TR25 | folds | 125 | 0.766 | -1.35e+04 | 10 | -1.68e+06 | 19 |
| TR25 | out of domain | 125 | 0.538 | -1.33e+10 | 37 | -1.66e+12 | 12 |
| TR25raw | folds | 125 | 0.754 | 0.401 | 8 | -29.3 | 16 |
| TR25raw | out of domain | 125 | 0.566 | -145 | 27 | -1.71e+04 | 16 |
| TS14 | test | 70 | 0.995 | -0.251 | 1 | -84.6 | 12 |
| TS14 | out of domain | 70 | 0.644 | -2.95e+20 | 28 | -2.06e+22 | 14 |
