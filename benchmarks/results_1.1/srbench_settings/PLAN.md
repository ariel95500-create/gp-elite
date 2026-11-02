# The settings SRBench runs GP_ELITE with: plan of the study

Written on 2 November 2026, before any fit of the study. The study was decided
by the author on 28 October 2026 (`../ROADMAP.md`, "SRBench", action 2). It
measures on the benches of the project, never on the datasets of SRBench; a
final check on public datasets of SRBench comes after the choice and decides
nothing.

## What SRBench does with GP_ELITE

Read in a clone of https://github.com/cavalab/srbench, in two places:
- master at 2aabbb6, where GP_ELITE is staged (`../srbench_2aabbb6/`): the
  wrapper `experiment/methods/gp-elite/regressor.py` (blob cbf170f9);
- the branch `srbench_2025` at dc3f6daa93bf10955df8775256a6f8644f38fd93, which
  holds the code of the 2025 edition: `experiment/optimize_model.py` (blob
  2b8fbe25), `experiment/analyze.py` (blob afedfe7f),
  `datasets/download_data.py` (blob 09c06eb2), `experiment/seeds.py` (blob
  385ad33a).

The wrapper (`est`): `operators="physical"`, `generations=60`,
`speed="fast"`, `restarts=10`, `max_time=3600`, `random_state=0`, `parallel`
left at None (islands in parallel from four cores). Its `fit` runs ten calls
of `symbolic_regression`, one after the other, each with `restarts=1`, a seed
of its own and a time limit equal to an equal share of what is left of 90 % of
`max_time`; it keeps the call with the best validation R². It runs all ten even
when the first one returns an exact law. Its grid `hyper_params` is
`[{"operators": ("physical", "full"), "generations": (30, 60)}]`.

The protocol of 2025 (`optimize_model.py`): a split of 75 % for training and
25 % for the test; a tuning by `GridSearchCV` with 3 folds on R², over the
configurations of `hyper_params` and the default one, each fit given
`max_time = fit_time_limit` (3600 s by default); then the final fit on the whole
training part with the best configuration. It reports the test R², the size of
the model and the training time; 30 runs per dataset, on 24 datasets of PMLB,
12 "black-box" and 12 "first principles" (`download_data.py`). Scaling of X and
y is off unless the command line asks for it (`--scale_x`, `--scale_y`); which
the runs of 2025 used is not recorded here.

**A finding, before any measurement.** `optimize_model.py` reads
`hyper_params` as a list of configurations, each a dict whose values are lists,
and keeps the first element of each list (`{k: v[0] for (k, v) in
hp.items()}`); it tunes only when the list has at least two configurations
(`if len(algorithm.hyper_params) > 1`). The grid of GP_ELITE is one dict of two
tuples, so its intended four configurations are never tried: no tuning runs,
and the default `est` is fitted. Written as the other wrappers write theirs (for
instance gplearn's, a list of single-value dicts), the grid would be read as
intended. This correction is put to the author with the result of the study
below; it is not measured here.

## The questions

1. Does the wrapper as published use its budget worse than another setting of
   the same engine, on the benches of the project?
2. Which of its choices matter: keeping the best of ten separate calls by
   validation R², rather than one call with ten restarts whose candidates the
   engine merges and selects with its own rule of parsimony; and 60
   generations per call, rather than the 1,000 of the project's benches.

## The settings compared

Each gets the same budget `max_time = B`, through the same code path SRBench
uses (`est.max_time = B`, then `est.fit(X, y)`):
- **W0**, the wrapper as published: the class and the `est` of
  `regressor.py` at 2aabbb6, imported from the clone (the file is part of
  SRBench, under its licence, and is not copied here; its blob hash is checked
  before each fit).
- **W1**, one call: `symbolic_regression` with `operators="physical"`,
  `generations=60`, `speed="fast"`, `validation_split=0.20`, `restarts=10`,
  `time_limit=0.9 * B`, `seed=random_state`: the engine merges the candidates
  of its ten restarts and applies its own final selection.
- **W2**, the wrapper's loop with `generations=1000` per call, everything else
  as W0.

Three choices apply to all three settings, each a departure from SRBench's
conditions, put to the author with this plan:
- **The version.** gp-elite 1.1.0 from PyPI, which SRBench installs since 2
  November 2026 (`gp-elite>=0.8.0`), rather than 1.0.0 as `../ROADMAP.md`
  says. Without units, 1.1.0 returns the models of 1.0.0 at equal work
  (`../release/README.md`, M1).
- **The islands in sequence** (`parallel=False`), as in every bench of the
  project: the models do not depend on the number of cores, and three fits can
  run side by side. The wrapper leaves `parallel` at None.
- **The budget.** B = 120 s instead of 3600 s: at 3600 s the study would take
  weeks on this machine. A call of W2 then gets about 11 s, a third of the 30 s
  of the project's benches. What holds at 120 s may not hold at 3600 s; this is
  said with the result.

## The benches

From `benchmarks/phase1_bench.py`, the decision bench and nothing of the
frozen test set: F41 (41 Feynman equations, five seeds, 205 fits), F41N1 and
F41N10 (the same with 1 % and 10 % noise on the training targets, 410 fits), R6
(6 standardised real datasets: 30 folds and 30 fits out of domain) and R7raw (7
in their own units: 35 and 35), 745 jobs per setting. Every fit gets the data as
`phase1_bench.py` builds them, column names `X0`, `X1`... as SRBench gives
them, and the operators of the setting (`physical`), not the pool of each
problem the project's benches use, and `random_state` is the seed of the job:
the counts can therefore differ from those of the benches, for every setting
alike.

Each job runs the three settings at the same time, in three processes with
`PYTHONHASHSEED=0` and one BLAS thread, one job at a time, so that every setting
meets the same load. The records are scored as `phase1_bench.py` scores its
own: exact law (1 − R² below 1e-9 on the test rows), structure retrieved under
noise, test R² of the folds, R² out of domain, the size of the model, the time.

The runner, `benchmarks/srbench_settings.py`, is committed before the first fit.
Before the 745 jobs, it is tried on two jobs of F41 and one of R6, to check that
the three settings run and are scored; those six fits are recorded apart
(`trial/`) and decide nothing.

## Criteria, written before the first fit

A setting S (W1 or W2) is better than W0 if all six hold:
1. F41 exact laws of S not fewer than W0's minus 3;
2. F41N1 and F41N10 structures retrieved, each not fewer than W0's minus 3;
3. R6 folds, median test R² not below W0's minus 0.005;
4. R6 + R7raw, collapses out of domain (R² below zero) not more than W0's plus
   2;
5. R6 + R7raw folds, median size of the models not above 1.25 times W0's;
6. and a gain on at least one: F41 exact laws at least W0's plus 10; or
   structures, F41N1 and F41N10 together, at least W0's plus 10; or R6 folds
   median test R² at least W0's plus 0.01.

If both are better, the one with the larger gain in F41 exact laws and
structures together is chosen; on a tie, the smaller median size. If neither
is, W0 stays.

The figures are read by `benchmarks/results_1.1/srbench_settings/compare.py`,
committed before the first of the 745 jobs ends.

## Then

- **Put to the author**: the result; the setting chosen, if any; the
  correction of the grid. A change of the wrapper, if he wants one, is a pull
  request to SRBench, which its maintainers decide.
- **The final check**, only if a setting is chosen, after the choice is
  committed: on the 24 datasets of SRBench 2025 (PMLB, fetched and their
  SHA-256 recorded), three runs each with the first three seeds of `seeds.py`
  (23654, 15795, 860), the split of `optimize_model.py` (75/25,
  `random_state` = the seed), no scaling and no tuning, B = 120 s, W0 and the
  chosen setting side by side; 144 fits. It reports the test R², the size and
  the time, per dataset and in median, published as measured, deciding nothing.
  The protocol of SRBench (30 runs, tuning, 3600 s) is not reproduced: about
  720 hours per setting on this machine.
- **The test of SRBench for the wrapper** (`experiment/test_evaluate_model.py`
  of master, on `192_vineyard_small`), run first with 1.0.0 and 1.1.0 from
  PyPI, as `../ROADMAP.md` asks: it shows whether the wrapper runs as it is with
  both versions.

## Amendment, before the 745 jobs (2 November 2026)

The trial (`trial/`) ran the three settings on three jobs. At B = 120 s each of
the ten calls of W0 gets about 11 s and stops before its 60 generations, which
take 19 to 25 s on the data of the bench (`trial/gens60.txt`); W2 then returns
what W0 returns (the three jobs give the same models). At 120 s the study could
not tell the settings apart; at the 3600 s of SRBench, W0 ends its ten calls in
about four minutes, some 7 % of its budget.

Put to the author with two options, he chose on 2 November 2026 (option A):
- **B = 300 s**, so that each call of W0 gets 27 s and runs its 60
  generations;
- **two settings, W0 and W1**: the question of the generations per call (W2)
  needs budgets of the order of SRBench's, out of reach at this scale here. It
  joins the measurement of what more time would bring, planned after 1.2
  (`../ROADMAP.md`), where the benches run with ten times the budget;
- each job runs W0 and W1 at the same time, two jobs at a time (four
  processes on four cores, the same load for both settings).

The criteria are those above, with S = W1. The figures are read by
`compare.py`, committed with this amendment.
