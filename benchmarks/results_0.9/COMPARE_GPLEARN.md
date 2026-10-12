# gp-elite against gplearn on the decision bench

Measured with the plan written before any fit (`PLAN_GPLEARN.md`, commits
6d72283 and 95c522a). gplearn 0.4.3 from PyPI, 335 fits from 23:10 on
9 October to 00:06 UTC on 10 October 2026 (the machine of the session
restarted once, after 25 fits; the fits running at that moment left no
record and were run again in full), no crash. gp-elite 0.8.0 from PyPI: the
phase 1 baseline, same data, splits, seeds, budget (30 s) and machine, three
fits at a time. Raw records: `gplearn_0.4.3.jsonl`; tables:
`python benchmarks/compare_gplearn.py report benchmarks/results_0.9/gplearn_0.4.3.jsonl`.

## What the numbers say

- **Exact laws (F41): gp-elite 88 of 205, gplearn 31.** Fit by fit, 63 laws
  are found by gp-elite only, 6 by gplearn only, 25 by both.
- **Real data, within the folds: gp-elite ahead, clearly on data in their own
  units.** Median test R² 0.809 against 0.790 on R6 (worst fold 0.372
  against 0.108) and 0.879 against 0.601 on R7raw, where gplearn collapses
  in 6 folds of 35 (worst R² −5,140) and gp-elite in none.
- **Out of domain: gp-elite is better in the median, gplearn collapses more
  often, gp-elite deeper.** R6: median 0.698 against 0.477, collapses 4
  against 8, but the worst is −224 for gp-elite and −0.74 for gplearn. R7raw:
  median 0.685 against 0.252, collapses 6 against 10, worst −233 against
  −2,940.
- Paired fit by fit on real data, gp-elite gives the higher test R² in 46 of
  60 R6 fits and 58 of 70 R7raw fits (median difference +0.15 on both).
- In 30 s gplearn runs a median of 59 generations of 1,000 programs; it
  stopped early on a perfect training fit in 23 of the 335 fits.

| suite | tool | fits | EXACT | NEAR | MISS | median 1 − R² | median size |
|---|---|---|---|---|---|---|---|
| F41 | gp-elite 0.8.0 | 205 | 88 | 30 | 87 | 0.000498 | 17 |
| F41 | gplearn 0.4.3 | 205 | 31 | 13 | 161 | 0.038 | 12 |

| suite | split | tool | fits | median R² | mean R² | worst R² | collapses (R² < 0) |
|---|---|---|---|---|---|---|---|
| R6 | folds | gp-elite 0.8.0 | 30 | 0.809 | 0.775 | 0.372 | 0 |
| R6 | folds | gplearn 0.4.3 | 30 | 0.790 | 0.674 | 0.108 | 0 |
| R6 | out of domain | gp-elite 0.8.0 | 30 | 0.698 | −6.91 | −224 | 4 |
| R6 | out of domain | gplearn 0.4.3 | 30 | 0.477 | 0.33 | −0.74 | 8 |
| R7raw | folds | gp-elite 0.8.0 | 35 | 0.879 | 0.796 | 0.0163 | 0 |
| R7raw | folds | gplearn 0.4.3 | 35 | 0.601 | −150 | −5,140 | 6 |
| R7raw | out of domain | gp-elite 0.8.0 | 35 | 0.685 | −12.5 | −233 | 6 |
| R7raw | out of domain | gplearn 0.4.3 | 35 | 0.252 | −93.2 | −2,940 | 10 |

## The laws only gplearn found

All six are trigonometric laws, from a family gp-elite never finds (0 of 90 in
the baseline):

| law | seeds | gplearn's formula | gp-elite |
|---|---|---|---|
| I.18.12, r·F·sin θ | 0, 1, 4 | `mul(div(sin(X2), inv(X1)), X0)` | NEAR or MISS, with forms such as `(0.319·v2)^(0.200·sin(…))` |
| II.15.4, −μ·B·cos θ | 0, 1, 2 | `mul(mul(X1, X0), neg(cos(X2)))` | MISS, with `cos((−2.55 − 0.161·v2)²)` |

gplearn works on the variables as given, so `sin(θ)` is one node. gp-elite
divides each column by its largest absolute value before the search, so the
same law needs `sin(k·u)` with `u = θ / max|θ|` and an unknown constant `k`
inside the function, which its search does not reach; its formulas show it
looking for that constant. This points at phase 4 (4a, an adjustable
argument inside sin, cos, exp, log and sqrt), and at a simpler idea to try
there: offering the trigonometric functions the variable in its own units.

## Expectations written before, against the outcome

| expectation | outcome |
|---|---|
| gplearn finds far fewer exact laws | yes: 31 against 88 |
| its median test R² on real data is lower | yes, slightly on R6 folds (0.790 against 0.809), widely elsewhere |
| it runs a few dozen generations in 30 s | yes, 59 in the median |
| (not expected) | gplearn finds 6 trigonometric laws that gp-elite misses |
| (not expected) | gplearn's out-of-domain failures on standardised data are more frequent but far shallower |

## Caveats

gp-elite was developed partly on F41, and neither tool was tuned (SRBench
tuned gplearn's hyperparameters by grid search). One machine, one budget
(30 s per fit). These numbers compare the two tools as a user installs them.
