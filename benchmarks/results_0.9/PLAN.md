# Measuring wider (phase 1 of the 0.9 / 1.0 plan) — plan written before any measurement

Written on 5 October 2026, after the plan of the 0.9 and 1.0 versions was
validated, before the frozen test set is built and before any fit of this
phase. Only the PMLB summary table (`pmlb/all_summary_stats.tsv`, SHA-256
`d658820a…3c1b6766eba983bb078e3bcc539141b1ac2cc33960`) and the PMLB dataset
names were looked at to write the selection rules below; no data file of the
test set was opened.

Phase 1 decides nothing about the engine. It builds a test set that is never
used to decide (measured once per version, published as is), and measures
gp-elite 0.8.0 as published, on this machine, on everything later phases are
judged on. Those numbers replace the starting values of the plan's objectives
at gate 2.

## Engine and machine

- **Engine.** gp-elite 0.8.0 installed with `pip install gp-elite==0.8.0` in a
  fresh virtual environment (wheel SHA-256 `b0ca029c…aaf891`, as published on
  PyPI on 5 October 2026), never the repository checkout.
- **Machine.** 4 cores (Intel Xeon at 2.1 GHz with AVX-512), 15 GB, Linux,
  Python 3.11. The measurements of 0.8 ran on a 2-core container, two fits at
  a time: times and time-budgeted results are not comparable with them, which
  is why F41 is measured again here.
- **Every fit.** `symbolic_regression` defaults otherwise (`speed="fast"`, one
  restart, 20 % internal hold-out), `parallel=False`, one process per fit,
  `PYTHONHASHSEED=0`, three fits at a time (one per core; the fourth core is
  left to the first targeted trial of phase 2, which runs alongside as the
  plan says). Budget T: `time_limit=30` s, `generations=1000`.
- **Records.** One JSON line per fit, as `benchmarks/decision_bench.py`
  writes them, with the engine file, the package versions and the date.

## The frozen test set (`benchmarks/test_set/`)

Built by `benchmarks/test_set.py` before any fit of this phase, each file
frozen by the SHA-256 of its decompressed content: the loader refuses a file
that changed. No targeted trial and no decision of any phase may use it.

**TF78, the Feynman equations of PMLB absent from the bench.** Every
`feynman_*` dataset of PMLB (119: 99 from the main AI Feynman table and 20
bonus equations, `feynman_test_*`) except the 41 of `feynman_bench.py` (its
`I.6.20a` is PMLB's `feynman_I_6_2a`): 78 datasets, 58 main and 20 bonus.
Each PMLB file holds 100,000 rows drawn uniformly in the variables' ranges.
For each dataset k (in sorted name order):

- training box: for each variable, from its minimum to its minimum plus 1/1.3
  of its observed width, so that the full range extends the box by 30 % of
  its width above, as the out-of-domain set of F41 does;
- 200 rows drawn with `RandomState(2000 + k)` among the rows inside the box,
  140 for training and 60 for the test;
- out of domain: up to 200 rows drawn with `RandomState(6000 + k)` among the
  rows with at least one variable above the box;
- operator pool: `"trig"` when the formula given in the PMLB metadata
  contains a trigonometric function or its inverse, `"physical"` otherwise
  (the rule the bench follows);
- EXACT when 1 − R² on the test rows is below 1e-9, NEAR below 1e-3, as the
  bench.

**TS14, the Strogatz systems.** The 14 `strogatz_*` datasets (400 rows, two
variables). Split `test`: 280 rows for training and 120 for the test, drawn
with `RandomState(3000 + k)`. Split `ood`: training on the 80 % of rows
closest to the centre, testing on the 20 % farthest (as R6). Operator pool
by the same rule. EXACT and NEAR as above, **if** the formula of the PMLB
metadata reproduces the PMLB target to 1e-9 of its scale on all 400 rows;
this check is made when the set is built, before any fit, and a dataset that
fails it is scored by NEAR only (its target was integrated numerically).

**TR25, real datasets.** Every PMLB regression dataset that is not synthetic
(not `*fri_c*`, `feynman_*` or `strogatz_*`), is not one of the seven datasets
of the decision bench nor `nikuradse_2` (the measurements of `nikuradse_1`),
has at most 10 features and 50 to 5,000 rows: 25 datasets, all kept.

`1027_ESL`, `1028_SWD`, `1029_LEV`, `1030_ERA`, `1096_FacultySalaries`,
`192_vineyard`, `229_pwLinear`, `230_machine_cpu`, `519_vinnie`, `522_pm10`,
`523_analcatdata_neavote`, `529_pollen`, `556_analcatdata_apnea2`,
`557_analcatdata_apnea1`, `663_rabe_266`, `665_sleuth_case2002`,
`666_rmftsa_ladata`, `678_visualizing_environmental`, `687_sleuth_ex1605`,
`706_sleuth_case1202`, `first_principles_planck`, `first_principles_rydberg`,
`first_principles_supernovae_zg`, `first_principles_supernovae_zr`,
`solar_flare`

The plan named 20; the rule gives 25 and all are kept rather than choosing
which to drop. As R6 and R7raw: five folds (`KFold(5, shuffle=True,
random_state=0)`) and one out-of-domain split, standardised on the training
part (TR25) and in their own units (TR25raw).

Engine seeds 5 to 9 everywhere (the folds take seed 5, the five folds
providing the replication). Seeds 0 to 4 stay those of the decision bench.

## The decision bench, measured again and extended with noise

- **F41, R6, R7raw** exactly as in `benchmarks/results_0.8/PLAN.md`, seeds 0
  to 4, measured again on this machine.
- **F41N1 and F41N10.** F41 with Gaussian noise added to the training targets
  only: standard deviation 1 % and 10 % of the standard deviation of the
  training targets, drawn with `RandomState(7000 + i)`. The test and
  out-of-domain targets stay exact.
- **Structure retrieved** (noisy suites only): the returned model's constants
  are refitted on the noise-free training targets by the engine's own
  finishing step (Levenberg-Marquardt to convergence, `core._lm_to_convergence`,
  then `core._refit_scaling`), in the engine's internal variables; the
  structure is retrieved when the refitted model has 1 − R² below 1e-9 on the
  noise-free test rows. This separates "found the law, constants blurred by
  the noise" from "found another formula". The refit is computed after the
  fit and its timing, and never fed back to it.

## Reproducibility from one processor to another

The thirteen reference configurations of `benchmarks/speed_equivalence.py`,
each run three times with the 0.8.0 wheel: with NumPy's default dispatch,
with `NPY_DISABLE_CPU_FEATURES="X86_V4"` (no AVX-512) and with
`NPY_DISABLE_CPU_FEATURES="X86_V4 X86_V3"` (no AVX2 either). Reported as is:
how many configurations return a different model, field by field as that
script compares them. This is a characterisation, not a decision: it says
what "same model on another machine" can and cannot mean.

## What is reported (`BASELINE.md`), for every suite

Exact, near and missed laws (by family for F41, main and bonus for TF78);
median and worst 1 − R² on the test; out of domain, median 1 − R² of the
models that are not exact and the number of collapses (R² < 0) with the worst
case; for real data, median test R² over folds, collapses (R² < 0) and worst
case, folds and out of domain apart; `formula_exact` False counts; median
time and time beyond the budget; median generations. For the noisy suites,
the structure-retrieved counts beside the exact ones.

Nothing is excluded after the fact: a fit that crashes is counted as a miss
with its error, and a fit cut by a machine interruption is run again in full,
as in 0.8.

## Expectations, written before

These are not criteria; they are what is expected, so that a surprise is
seen as one.

- F41 on this machine: different from the 88 of campaign R in either
  direction, the machine and the load being different; the 18 equations of
  the five zero families of 0.8 expected to stay at zero.
- TF78 below F41 in exact rate (F41 was built partly from equations the
  engine was developed on), and the 20 bonus equations below the 58 main ones.
- TR25: some collapses out of domain, as on R6 and R7raw.
- Reproducibility: at least one of the thirteen configurations returns a
  different model without AVX-512 (shown on one case on 5 October 2026).

## Notes added after the measurement (5 October 2026)

- The first targeted trial of phase 2 did not run alongside the baseline:
  the change it tests (a candidate on which a numerical safety net acts is
  invalid during the search) touches every evaluation path of the engine
  (interpreter, compiled code, Levenberg-Marquardt, caches) and gets its own
  written plan after gate 2. The fourth core stayed idle.
- The reproducibility study ran after the baseline, not alongside it: one of
  the thirteen configurations runs parallel islands, which would have taken
  cores from the timed fits. Each setting was also run twice, to tell a
  processor effect from a run-to-run difference.

## Gate 2, validated on 9 October 2026

The frozen test set (TF78, TS14, TR25) and the targets below were validated
by the author after reading `BASELINE.md`. Starting values are those of
gp-elite 0.8.0 measured in this phase.

| Indicator | 0.8.0 | Target for 1.0 |
|---|---|---|
| F41 exact laws (205 fits, 30 s) | 88 | at least 110 |
| the five families at zero (18 equations, 90 fits) | 0 | at least 20 |
| TF78 exact laws (390 fits) | 145 | at least half of the relative gain on F41 |
| structure retrieved, F41N1 / F41N10 (205 fits each) | 70 / 67 | at least 80 / 77 |
| formula equal to the model, R6 + R7raw (130 fits) | 122 | 130 |
| collapses out of domain, R6 + R7raw (65 fits) | 10, worst R² −233 | no more, worst no deeper |
| median test R², R6 folds | 0.809 | at least 0.804 |
| median test R², TR25 folds | 0.766 | at least 0.761 |
| collapses, TR25 out of domain (125 fits) | 37 | fewer |
| units mode, Feynman II.11.3 | 149 s in 0.8 (measured again in phase 3) | at most 60 s |

The test-set indicators (TF78, TR25) are measured once per version and never
used to decide a change.
