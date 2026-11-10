# The TP notebook of the pool `full`: plan written before the fits

Written on 9 November 2026, after M3 (`../../m3_compare_1.2.0_vs_1.3.0.txt`)
and before any fit below. It decides nothing about the release. What it finds
goes to the author at gate 10 with M3.

## What M3 saw

`examples/tp_regression_symbolique.ipynb`, parts 1 and 2, fits
x·sin(x²)·cos(x/2) on 200 points with `operators='full'`, seed 0
(`../notebook_snippet_tp.txt`). The pool `full` has the arcsine since 1.3.0.
No bench of M2 uses the pool `full`, and the plan of the release did not
expect this notebook to change. With seed 0:

| generations | 1.2.0, MSE (size) | 1.3.0, MSE (size) |
|---|---|---|
| 10 | 9.706e-03 (34) | 5.654e-02 (38) |
| 30 | 1.784e-04 (41) | 1.628e-02 (46) |
| 60 | 1.784e-04 (41) | 1.281e-03 (43) |

The fit of part 1 (40 generations) returns a formula with the arcsine in
1.3.0. Two of the three fits of part 2 warn that the printed formula departs
from `predict()`. The text of question 2 says "from 30 to 60, nothing
changes", which held with 1.2.0 and no longer holds.

The question: is 1.3.0 worse on this problem, or is it the draw of seed 0?

## E2, ten seeds

- **Data and fit:** those of the notebook (`jeu(seed)`, then
  `symbolic_regression(X, y, feature_names=['x'], operators='full',
  generations=g, speed='fast', seed=s, parallel=False)`), with
  g = 10, 30 and 60 and s = 0 to 9, the data drawn with the seed of the fit,
  as in part 3 of the notebook. That makes 30 fits per version.
- **Engines:** 1.2.0 in `/venv12bx` and 1.3.0 in `/venv13rx`, the
  environments of M3. Each fit runs in its own process, with
  `PYTHONHASHSEED=0` and one BLAS thread. The two versions run the same fit
  at the same time.
- **Records:** for each fit, the MSE on the 200 rows, the size,
  `formula_exact`, whether the formula has an arcsine, the time and the
  formula. They go in `e2_1.2.0.jsonl` and `e2_1.3.0.jsonl`, written by
  `e2.py` and read by `e2_read.py`. Both scripts are committed before the
  first fit.

## How it is read, written before

At each budget, the seeds are compared in pairs. The test is the sign test
of part 3 of the notebook, on the seeds where the two MSE differ:
- **1.3.0 is called worse at that budget** if its MSE is the higher in the
  majority of those seeds, with p < 0.05;
- **1.3.0 is called better** if its MSE is the lower in the majority, with
  p < 0.05;
- **otherwise no difference is shown.**

Reported beside: the median MSE and size, and how many formulas depart from
`predict()` or have the arcsine, by version and budget.

The text of question 2 is brought to what 1.3.0 gives at seed 0, whatever E2
finds. If 1.3.0 is called worse, the notebook and the pages of the limits
say so, with these figures. The author decides at gate 10 whether to publish
as is.
