# gp-elite against gplearn — plan written before any fit

Written on 9 October 2026, before the first fit of gplearn. Asked by the
author the same evening: how does gp-elite compare with the other symbolic
regression tools written in pure Python? This compares; it decides nothing
about gp-elite.

## Which tools

Of the pure-Python tools, gplearn is the most used (a scikit-learn
estimator). DEAP is a toolbox in which a regressor has to be assembled, and
FFX restricts the formulas to a fixed family of forms; PySR (Julia), Operon
(C++) and AI Feynman (Fortran) are not pure Python. gplearn alone is
measured.

## Engines

- **gp-elite 0.8.0** from PyPI: the records of the phase 1 baseline
  (`baseline_0.8.0.jsonl`, F41, R6 and R7raw), measured on this machine with
  the same protocol; not run again.
- **gplearn 0.4.3** from PyPI, in a fresh environment (NumPy 2.4.6,
  scikit-learn 1.9.1).

## Every gplearn fit

- The decision bench exactly as phase 1 builds it: F41 (205 fits), R6 and
  R7raw (folds and out of domain, 130 fits), same data, splits and seeds 0
  to 4; one process per fit, three at a time, `PYTHONHASHSEED=0`, one BLAS
  thread.
- gplearn has no time limit: the fit runs one generation at a time
  (`warm_start=True`) until 30 s are spent, and the generation running at
  that moment finishes, as in gp-elite; at most 1000 generations. gplearn's
  own stopping rule (a training fitness at its `stopping_criteria`, 0 by
  default) still ends the run early (added before the first recorded fit:
  a run one generation at a time would otherwise skip it).
- Settings: gplearn's defaults (population 1000, tournament 20, parsimony
  coefficient 0.001, constants drawn in [−1, 1], mean squared error), with
  `random_state` = the seed, `n_jobs=1`, and the function set of all its
  built-in functions (add, sub, mul, div, sqrt, log, abs, neg, inv, max, min,
  sin, cos, tan), the closest to gp-elite's operator pools. Neither tool is
  tuned: each runs as a user installs it.

## Scores and report (`COMPARE_GPLEARN.md`)

As in phase 1: EXACT when 1 − R² on the test rows is below 1e-9, NEAR below
1e-3, MISS otherwise; on real data, test R² over the folds and out of
domain, collapses (R² < 0) and worst case; formula size, time and
generations. Both tools side by side, per suite, and paired fit by fit;
nothing excluded after the fact (a crash is a miss).

## Expectations, written before (not criteria)

- gplearn finds far fewer exact laws: it does not optimise its constants, so
  a law whose constants are not among its random draws can only be
  approached.
- On real data its median test R² is lower than gp-elite's.
- It runs a few dozen generations in 30 s.

## Caveats, written before and published with the numbers

- gp-elite was developed partly on F41; its defaults may suit these
  equations.
- SRBench tuned gplearn's hyperparameters by grid search; this comparison
  does not, for either tool.
- One machine, one budget (30 s per fit).
