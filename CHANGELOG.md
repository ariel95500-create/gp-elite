# Changelog

## Unreleased

- The README said that setting `seed=` and `parallel=` returns the same model
  on another machine. It does on the same machine; on another one, NumPy's
  floating-point functions (`exp`, `tanh`...) can differ in the last digit
  with the instructions the processor offers, and the search can then take
  another path. The README now says so.
- `test_delivered_formula_is_the_model` assumed that no numerical safety net
  acts on the Pareto candidates of its data. On one of GitHub's Windows
  runners one did, with the same code, seed and package versions as runs that
  passed, and the engine flagged that formula inexact as documented. The test
  now checks the flag: a formula flagged exact reproduces `predict()`, and an
  inexact returned model warns.
- `CITATION.cff`: `date-released` is 5 October 2026, the day 0.8.0 was
  published on PyPI (it said 30 September 2026, the date the release was
  prepared).
- When the formula of the returned model departs from `predict()`, the
  warning now says how many entries of `result.pareto` have an exact formula
  and names the most accurate of them on the hold-out. No model changes. Two
  ways of making the returned formula always exact were measured and not
  adopted: rejecting such candidates during the search lost exact laws, and
  removing them at the final selection lowered the test R² on real data
  (`benchmarks/results_0.9/PLAN_PHASE2.md`).

## 0.8.0 — "Swift"

This release makes the engine faster (the speed-ups alone return the same
models), recovers more laws, and fixes failures a user could meet without
being told: data whose values are far from 1, and unusable inputs. Every
change meant to improve the search or the final selection was decided by a
comparison whose hypothesis and criteria were written before it ran
(`benchmarks/decision_bench.py`: the 41 equations of
`benchmarks/feynman_bench.py` with five seeds, six real PMLB datasets
standardised as SRBench does, and seven, those six and nikuradse_1, in their
own units, at 30 seconds per fit; plans in `benchmarks/results_0.8/PLAN.md`,
results and raw records in `benchmarks/results_0.8/RESULTS.md`). Changes that
did not meet their criteria are listed there too, with their numbers. The
corrections listed under Fixed were not subject to such a decision;
`RESULTS.md` and the other files of `benchmarks/results_0.8/` show what they
change.

At 30 seconds per fit, on the 41 equations with five seeds (205 runs), the
release returns the exact law (1 - R² < 1e-9 on held-out points) 88 times,
measured last (campaign R); 0.7.0 did 64 times, in the first campaign, on the
same machine (each change's own effect is given below, measured against the
engine without it). On the six real datasets, standardised, the engine of
campaign 5b (the later changes do not act there) keeps the median test R² of
the folds (0.809 against 0.808 for 0.7.0); out of their domain it has fewer
collapses (R² < 0: 5 against 7 in 30 fits), but the worst is deeper (-224 on
228_elusage, against -43 on 210_cloud). Side by side at equal work (100
generations, 0.8.0 as of commit `b0e12cf`, whose later changes act neither
without a time limit nor on these data), 0.8.0 takes 0.44 of the time of
0.7.0 on the 15 equations of the README (0.58 per generation, less per fit
because it finds the exact law at the first generation more often: 40 fits of
75 against 9) and finds 54 exact laws against 46; on the real datasets it
takes 0.58 of the time (medians of per-fit ratios), with a slightly lower
test R² (median 0.809 against 0.815; worse on 14 folds, better on 9).

### Faster, same models
At equal seed and equal work, the changes below return the same model as
before, bit for bit (checked on 13 reference configurations by
`benchmarks/speed_equivalence.py`, and by `tests/test_speed_equivalence.py`).
`import gp_elite` takes 0.08 s instead of 0.92 s (median of seven fresh
processes; pandas and scikit-learn are imported only where needed).
- ε-lexicase selection processes cases by blocks: when a block of cases
  eliminates no candidate, it is passed in one NumPy operation. Same draws,
  same parents.
- Levenberg-Marquardt computes each column of its Jacobian by re-evaluating
  only the path from the constant to the root.
- A tree is interpreted until it has been evaluated three times, and only
  then compiled.
- Stigmergic sampling tables are frozen while a generation is produced;
  protected operators, tree copies and the simplifier are cheaper; the
  prediction cache can no longer be fooled by a reused array identifier.

### Fixed
- **Data far from 1.** A target of order 1e-9 or 1e20 (SI units make this
  common: farads, joules per molecule, pascals of a star) came back as a
  constant or a wrong straight line, with a negative R² and no warning that
  the fit had failed; a column of order 1e-19 was not normalised, and
  predictions above 1e12 were clipped. The search now works on y divided by a
  power of ten when its standard deviation lies outside [1e-3, 1e3], and the
  model, its formula and its MSEs come back in the units of y; the division by
  max|x| leaves only null columns at 1. `benchmarks/scale_check.py`, eleven
  scales from 1e-34 to 1e30: the law is recovered at all eleven on the
  release, against 2 with 0.7.0.
- **The square of a negative constant** was evaluated negative during the
  search.
- **`seed=` alone reproduces a fit**, whatever `PYTHONHASHSEED` is: tree
  hashes no longer depend on Python's string hashing. The note asking for
  `PYTHONHASHSEED=0`, printed once per process even with `verbose=False`, is
  gone.
- **Unusable inputs are refused** instead of fitted: a missing or infinite
  value is named with its row and column, a non-numeric column is named. With
  0.7.0, a missing value in y or in a column the law uses went through, and
  the fit returned an unrelated formula without a warning; a non-numeric
  column stopped the fit on a conversion error that did not name it
  (`benchmarks/bad_input_check.py`). `predict()` checks the number of columns
  and returns NaN for a row with a missing or infinite input (0.7.0 returned
  0).
- **`time_limit=` is kept more closely.** The variants of the final polish
  stop one second after the deadline, or one second after they start if that
  is later. At 30 s per fit on the 41 Feynman equations, the time spent
  beyond the budget falls from 1.26 s (median; 6.3 s at most) to 1.03 s
  (1.85 s at most), with the same 88 exact laws (campaign R); a 15 s budget
  on 3,000 rows ends at 16.7 s (`benchmarks/time_limit_check.py`).
- An exact law was printed with the rounding noise of its offset
  (`8.88178e-16 + v1 * v2 / v3`), or with a power 0 of a positive
  sub-expression; such a term is no longer printed (the model does not
  change, and the printed formula is still checked against it).

### Changed — the search and the final selection
Each item below met the criteria written before its campaign (numbers at 30 s
per fit, 205 Feynman runs, against the engine without the change, whose fits
come from the campaign that measured it).
- **Early stop relative to the scale of y, and constants fitted for the form
  that is judged.** The search stopped at a hold-out MSE of 1e-6 whatever the
  unit of y; it now stops only on a law exact to numerical precision, so a
  search that finds only an approximation uses its whole budget. And
  Levenberg-Marquardt fitted the tree alone, while the search judges it after
  the linear scaling a + b·f: it now fits the constants of the scaled form
  (variable projection). Together: 69 exact laws against 58 (sign test on the
  runs exact for one engine only, p = 0.019); on real data, a median paired
  difference of +0.000 and as many collapses.
- **A formula that reproduces the model is preferred** among candidates the
  data cannot tell apart: fits whose printed formula departs from `predict()`
  (`formula_exact` False) fall from 28 to 11 out of 265, and from 6 to 0 out of
  60 on real data, at the cost of 6 exact laws (63 against 69, the tolerance
  written in the plan). The stigmergic co-occurrence graph, queried with the
  wrong key, now finds fragments that contain constants.
- **Right structures are finished into exact laws.** For each finalist of the
  final selection, the constants are fitted to convergence, and variants
  give each term of a sum its own coefficient (sqrt((x2-x1)² + (y2-y1)²) on
  columns divided by different maxima needs one); a variant enters the
  selection only if it reproduces the hold-out to numerical precision, so it
  never replaces an approximate model by another. 75 exact laws against 64
  (I.8.14 from 0 to 5 of 5); on real data no variant was ever admitted. About
  0.7 s more per fit at the sizes measured (140 to 500 rows).
- **Power laws are seeded.** When the data follow a power law (a monomial
  fitted on the logarithms explains 99.9 % of the variance of log|y|), that
  monomial, with its exponents rounded to halves, and with its fitted
  exponents if the pool has `pow`, starts in the initial population. 88 exact
  laws against 75: q1·q2/(4π·ε·r²) from 2 to 5 of 5, III.19.51 from 0 to 5;
  none lost; never triggered on the real datasets, where that fit explains at
  most 96 % of the variance of log|y| on the training rows.
- A champion or finalist polished by Levenberg-Marquardt keeps a scale and
  an offset that match it (a defect of the development version of variable
  projection, found in campaign 4 and never released; as a correction, it was
  kept whatever campaign 5 showed: 64 exact laws against 63).

The polish and the seeds were first measured without their restriction, and
failed on collapses on real data; the restricted versions were designed after
seeing those failures and measured on the same equations, seeds and splits,
and the 99.9 % threshold of the seeds was set knowing that the real datasets
stay well below it. On these real datasets the restricted mechanisms never
act, by construction: their real-data criteria show that they do no harm
there, not that they would help on data closer to a power law.

### Added
- `normalize="grouped"`: one scale factor for the columns whose magnitudes
  are within a factor 10 of each other, so that sums and differences of
  same-kind variables keep their form. Measured and left as an option: +6
  exact laws out of 205 (within the scatter between equivalent engines) and 2
  more collapses on real data out of domain.
- `SRResult.sympy_expr()` and `ParetoEntry.sympy_expr()`: the sympy expression
  with one symbol per column, right for column names sympy would misread
  (`E`, `I`, names with spaces).
- `benchmarks/decision_bench.py` (A/B comparison of two engines at equal time
  or equal work, one process per fit), `benchmarks/small_data_check.py`,
  `benchmarks/scale_check.py`, `benchmarks/robustness_check.py`,
  `benchmarks/bad_input_check.py`, `benchmarks/typed_generations_check.py`,
  `benchmarks/speed_equivalence.py`; `benchmarks/feynman_bench.py --normalize
  none`.

### Measured and not kept
- The speed-up (with the fix of the negative square) does not find more laws
  in the same time: twice the generations in 30 s, 64 exact laws against 64.
- A warning based on how much the predictions grow just outside the training
  box does not predict out-of-domain failure (3 of 8 collapses caught, 5 false
  alarms): not shipped.
- The polish of finalists without the exact-only rule, and power-law seeds
  without the power-law test: as many or more exact laws (+11 and +15, against
  +11 and +13 for the versions kept), and one and two more collapses on real
  data.

### Measured on this release
Every figure of the README and the notebooks was re-measured on the release
(commit `cdddaf0`) or comes from `RESULTS.md`; raw results and logs are in
`benchmarks/results_0.8/`, with the commands in its README. Each method is
judged on the model it returns:
- Feynman benchmark, 15 equations, one seed: 12/15 exact and 13/15 within
  1e-3, as with 0.7.0, but not the same laws: I.8.14 now comes back exact and
  III.15.12 within 1e-3, while I.18.12 (r·F·sin θ) is missed. Without the
  column normalisation (`normalize="none"`), the three laws with a sine or a
  cosine all come back exact. With `units=` declared, 14/15 exact, each in its
  textbook form. Against gplearn on the same data: 12/15 against 6/15 exact,
  ahead on 8 equations, behind on one (I.18.12).
- `units=` on Feynman II.11.3, 5 seeds: 5/5 dimensionally valid against 0/5,
  median size 27 against 59 nodes, and two runs in five recover the exact law.
  The typed search takes longer than with 0.7.0: 149 s per run (median)
  against 57 s. 0.7.0 stopped a search once its hold-out MSE fell below 1e-6,
  0.8.0 only on an exact law, so the typed runs that end on an approximation
  now use all their generations; per generation, the typed search takes
  about a fifth less time than with 0.7.0 (two seeds, run side by side;
  diagnostic D2 in `RESULTS.md`). `time_limit=` bounds it.
- Robust mode: the error is divided by six at 10 % outliers, with no gain at
  20 %, on the bundled example.
- Data size (`normalize="none"`, 5 equations): the four equations other than
  I.16.6 recovered exactly at every size from 25 to 10,000 points, in every
  run; I.16.6 is not recovered exactly at any size. The five fits take 108 s
  in total at 1,000 points and 284 s at 10,000.
- Unusual inputs (`benchmarks/robustness_check.py`, 16 cases: constant,
  null or duplicated columns, three rows, inputs and targets of order 1e±150
  and 1e±200...): each returns a model with finite predictions, and 15 of the
  16 formulas reproduce `predict()`.
- Printed formulas (`benchmarks/formula_fuzz.py`, 1,500 random trees): 1,461
  exact, each matching `predict()` through sympy (0.7.0: 1,448); 38 inexact
  because a safety net acts, 1 because of the rewriting.
- `operators=` respected in 48 fits out of 48; `time_limit=15` ends at 16.7 s,
  sequential or parallel (single runs; 0.7.0: 17.3 s and 16.5 s).
- The simulated battery example (`examples/battery_soh.py`) extrapolates
  worse than with 0.7.0: R² -0.314 on the forward split, against +0.594,
  still ahead of the two tree ensembles (-2.5 and -2.3).

## 0.7.0 — "Sound"

Not published on its own: these changes reach users with 0.8.0.

This release fixes what an external review of 0.6.1 found, and re-measures
every number the README quotes on its final code. Defaults that change:
`normalize="auto"` (measured below), the population of the default `fast`
preset (300 → 400), and the number of generations of `speed="thorough"` and,
in `GPEliteRegressor`, of each preset (below). The final selection gains two
rules, both measured below; the evolutionary search itself has no new
heuristic.

### Fixed — the delivered formula
- **The formula is written in your variables, for every normalisation, and
  checked.** The engine searches on rescaled inputs, and up to 0.6.1 the tree
  was printed with the raw column names but the scaled values: `y = 3x` on
  `x` in [1, 5] came out as `15.0 * x`, in `expression` as in `sympy()`. (The
  development branch after 0.6.1 folded the scaling into `sympy()` for the
  division-by-max normalisation only; with min-max, then the default for any
  column with a non-positive value, or z-score, its exported formula was
  still wrong.) The 0.6.1 entry below says
  `sympy()` is numerically equivalent to `predict()`: that held only without
  scaling.
  Now `expression`, `equation_`, `pretty()`, `sympy()`, every Pareto entry and
  the console (mode 6) give the formula in the raw variables, with the
  rescaling folded into its constants, and the fit checks that it reproduces
  `predict()` on the training data (`result.formula_exact`). Protected
  operators are written as the engine computes them where it matters on the
  data (`sqrt(|u|)` when `u` changes sign, sign-aware even powers). Property
  tests cover division-by-max, min-max, z-score and no scaling, one and several
  variables, signed and positive data (`tests/test_guarantees.py`); of 1,500
  random trees, the 1,448 whose formula is reported exact all reproduce
  `predict()` once parsed by sympy; of the 52 others, 51 involve a safety net
  of the engine and one an ill-conditioned expression (`benchmarks/formula_fuzz.py`).
- **A model is evaluated with its own constants.** Compiled functions,
  predictions, fitness values and simplified forms were cached under a hash
  that rounds constants to 4 decimals, so two trees differing only further
  down shared one entry: `predict()` could compute with the constants of
  another model (compiled earlier, possibly in an earlier fit of the same
  process), `simplify()` merged `1.00001*x + 1.00002*x` into `2*(1.00001*x)`,
  and two identical fits in a row could return different models (measured in
  robust mode). Every cache of values is now keyed on the exact tree.
- **A power with a variable exponent no longer jumps where the exponent is an
  integer.** The engine's power keeps the sign of its base for a constant
  integer exponent (`pow(u, 3)` is `u³`), but it applied that branch row by
  row to exponents that depend on the variables as well: the model jumped
  wherever such an exponent landed exactly on an integer, which division by
  max|x| guarantees on a column's extreme row. The search could exploit the
  jump as a row indicator, and no readable formula reproduced the model (seen
  on the standardised PMLB dataset 561_cpu, where `formula_exact` was False).
  A variable exponent now always gives `|u|^v`, the function the formula
  prints. This changes
  the search, which is why every figure below was measured after it.
- **A formula that departs from the model is never delivered silently.** The
  formula is the plain mathematical function; where one of the engine's
  numerical safety nets acts on the training data (a clipped or capped power,
  a division by a near-zero denominator), or, rarely, where rounding ruins an
  ill-conditioned expression, it departs from `predict()` on those rows. `formula_exact` is then False and the fit warns with the number of
  rows concerned. Measured: 6 of the 70 fits made with the default
  normalisation in `benchmarks/norm_signed.py`.
- `mse_train` was computed on all rows, hold-out included; it now uses the
  training rows only. `r2_validation` is documented for what it is: the
  hold-out also chooses the returned model, so it is an optimistic selection
  score, not an independent estimate of generalisation.
- `unknown_constant=True` with a shifting normalisation (`minmax`,
  `standard`) returned a wrong constant value through the estimator (the
  console already declined); it now returns `None`, as documented in 0.6.0.

### Fixed — dimensional guarantees
- The engine's validity gate and the post-hoc auditor share one semantics:
  `1 + 2·x` with `x` in metres is rejected by both (the gate accepted it).
- A power with a non-constant exponent requires a dimensionless base (`x^z`
  with `x` in metres used to pass as metres).
- Unit strings are fully validated: `m garbage`, `m/(s` and `m/s2` raise
  instead of being silently read as something else.
- `operators=` is respected everywhere: the typed generator used `sin`, `exp`,
  `sqrt`... under `operators="poly"`, and the stigmergic builders could insert
  `sin`/`cos` under `operators="physical"`. 48 fits with the `poly` and
  `physical` pools, with and without `units=`: 0 out-of-pool operator
  (`benchmarks/pools_check.py`).

### Added
- **`time_limit=`** (seconds): the search stops cleanly at the deadline and
  returns the best model found so far, instead of being killed without a
  result by an external timer. Remaining time is shared between restarts;
  `result.time_limit_reached` and `result.restarts_completed` say what
  happened. Overshoot measured at about two seconds on a 15 s budget
  (17.3 s sequential, 16.5 s parallel, 3,000 rows,
  `benchmarks/time_limit_check.py`): the final polishing and selection run
  after the last generation. That is more than the one generation plus one
  second the check had set in advance for the sequential case. A budget that is not reached changes nothing:
  same model with and without `time_limit=3600` (checked on one problem, and
  by a test).
- **`speed="thorough"`**: population 400, four islands, 200 generations by
  default in both `symbolic_regression` and `GPEliteRegressor`, the regime
  for looking for an exact law. `GPEliteRegressor(generations=None)` now takes
  its default from `speed` (30, 40, 60 and 200 generations for `ultrafast`,
  `fast`, `normal` and `thorough`; it was 40 for every preset).
- `SRResult.sympy()`, `ParetoEntry.sympy()`, `formula_exact`.

### Changed
- **`normalize="auto"` divides every column by its max |value|**, signed
  columns included (they went through min-max, which turns each variable into
  `a*(x - x0)` and breaks multiplicative structure). Decided on a criterion
  written before measuring (`benchmarks/norm_signed.py`, raw results in
  `benchmarks/results_0.7/`). On 8 laws with signed inputs × 5 seeds: exact
  recoveries 20/40 against 7/40, near ones 30 against 27. On 6 real PMLB
  datasets standardised as SRBench does × 5 folds: median test R² 0.808
  against 0.808, mean 0.781 against 0.775, worst fold 0.406 against 0.399;
  divmax is better on 16 of 30 paired folds, no collapse on either side, and
  the delivered formulas are shorter (median 16 nodes against 20). On real
  data it is a wash; on laws it is a clear gain.
  `normalize="minmax"` remains available.
- **A law found exactly is no longer traded for a shorter approximation.**
  The final choice keeps the smallest candidate within 0.3 % of R² of the
  best, to avoid fitting noise. The rule was found on Feynman I.18.12, where
  an earlier state of the engine returned `0.0776 + 0.9967*r*F*sin(1.0106*th)`
  while `r*F*sin(th)`, exact, was in the front. When the best candidate reproduces the hold-out to numerical
  precision (MSE ≤ 1e-12 × variance) there is no noise to avoid, and only
  exact candidates stay eligible. Measured: the rule never fired on the 60
  real-data fits of the normalisation study nor on the 60 of the guard study;
  on the Feynman benchmark it acted on two equations, I.14.4 and I.6.20a,
  both returned exact.
- The default `fast` preset uses a population of 400 instead of 300, so each
  generation evaluates a third more candidates.
- Unknown option values raise `ValueError`: `operators="phsyical"` used to
  become `"physical"`, `speed="fats"` the `normal` preset, and
  `normalize="divmx"` min-max scaling, silently.
- The console (mode 6) printed the engine's internal expression with the real
  column names (`24.97 * elongation` for the law `250 * elongation`); rescaled
  columns now carry a prime, and the law in your columns follows.
- **Scripts without an `if __name__ == "__main__":` guard** no longer have
  their whole computation run again by every worker process when parallel
  islands start (the workers use the `spawn` start method on every system,
  Linux included, and re-import the script): the engine detects it, finishes
  on one core with the same result and warns once. Checked on
  Python 3.9, 3.11 and 3.14, with 120 and 3,000 rows: the workers receive the
  data through a temporary file and are probed with empty tasks first, as
  otherwise the parent could wait forever on a worker that had already exited
  (from about 3,000 rows, and on Python 3.9 at any size).
- With `verbose=False`, the worker processes of parallel islands no longer
  print their progress.
- The API writes no file. It used to write `gp_elite_log.csv` into the
  installation directory or the current one.
- Near-domain guard at the final selection: among candidates the parsimony
  rule considers equivalent, one that explodes just outside the data (a pole
  between two training points) is no longer preferred. Measured cost: none —
  on 60 real-data folds (6 PMLB datasets × 2 seeds × 5 folds,
  `benchmarks/near_guard_study.py`) it never intervened, and none of the 299
  front candidates exploded on the test folds. One fold (210_cloud, 108
  rows) returned a poor model, test R² −0.58, without any candidate
  exploding: the guard targets poles, not a weak fit. Its benefit is shown on
  constructed cases (a spurious pole between training points, in
  `tests/test_guarantees.py`). The one real collapse seen with 0.6 (210_cloud,
  thorough preset, one fold at R² = −8e10) could not be reproduced on another
  platform, so whether the guard would have caught it is not verified.
- Benchmarks judge every method on the model it returns. `duel.py` used to
  score GP_ELITE on the best point of its Pareto front chosen by looking at
  the test set, and gplearn on its single returned program;
  `feynman_bench.py` reported the front. `examples/robust_regression.py` kept
  the best of three runs by comparing with the true law.

### Measured on this release
Every figure in the README was re-measured on 0.7.0 (raw results and logs in
`benchmarks/results_0.7/`, commands in its README), each method judged on the
model it returns:
- Feynman benchmark, 15 equations, one seed: 12/15 exact (1−R² < 1e-9 on
  held-out data), 13/15 within 1e-3; with `units=` declared, 14/15 exact, each
  in its textbook form. Against gplearn on the same data: 12/15 against 6/15
  exact, ahead on 7 equations, behind on none.
- `units=` on Feynman II.11.3, 5 seeds: 5/5 dimensionally valid against 0/5,
  median size 17 against 41 nodes, and two runs in five recover the exact law
  (none did in 0.6).
- Robust mode: error divided by six at 10 % outliers, no gain at 20 % on the
  bundled example (the 0.6 table showed a best-of-three chosen with the true
  law).
- Data size (`normalize="none"`, 5 equations): the four equations other than
  I.16.6 recovered exactly at every size from 25 to 10,000 points, in every
  run; I.16.6 missed at every size; median time ×2 from 1,000 to 10,000
  points.

### Project
- Continuous integration on Linux (Python 3.9–3.14) and Windows.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`; `CITATION.cff`
  updated; `__version__` read from the installed metadata (the 0.6.1 wheel
  reported `0.6.0`).
- Real datasets used by the studies are frozen by content hash
  (`benchmarks/pmlb_frozen.py`).
- `examples/battery_soh.py` normalised its test data twice; its data file is a
  simulation and is now labelled as such everywhere.
- Removed a dead first definition of `fitness()`, silently overwritten by the
  second.

## 0.6.1

### Fixed
- **`sympy()` now returns a sympy-parsable string.** It previously returned the
  human-readable display form, where `sq` renders as `²` and `cube` as `³`,
  which `sympy.sympify()` cannot parse — so on a majority of fitted models the
  method that promises sympy handed back a string sympy rejected. Operators are
  now mapped explicitly (`sq`→`**2`, `cube`→`**3`, `max2`→`Max`, `min2`→`Min`,
  `step`→`Heaviside`, `is_even`→`Mod`, with domain-guarded `sqrt`/`log`), and an
  unmapped operator raises instead of silently producing an undefined function.
  The returned string is numerically equivalent to `predict()` (checked to
  ~1e-10). Conversion is centralized in `core.node_to_sympy`.

### Added
- **`pretty()`** returns the previous human-readable form (with `²` and `³`),
  for display. Use `sympy()` for a parsable string.

## 0.6.0 — "Bench"

### Added
- **Physical units in the console** (mode 6, generic CSV). The dimensional
  constraint and the mystery-constant deduction were reachable only from the
  Python API, while mode 6 targets exactly the user who knows what their columns
  mean. Mode 6 now asks for the units of the feature columns and of the target,
  then offers to deduce an unknown dimensioned constant. Declining is one
  keystroke and the previous behaviour is unchanged. Verified end to end on a
  Hooke's-law CSV: returns `[kg / s^2]` and 250.0 against a true 250, on two
  independent platforms.
- Unrecognised unit bases are now flagged. `normalize_units_arg` accepts any
  token as a new dimension — useful for exotic quantities, dangerous for a typo,
  since `metre` instead of `m` silently creates an incompatible base and the
  search then finds nothing. The console lists unknown bases and names the
  recognised ones, without blocking.

### Notes
Constant values are folded back into the raw units of the input columns. This is
only possible under multiplicative normalisation (`auto` on positive features,
or `divmax`); with `minmax` or `standard`, which shift, the units are reported
without a value and the reason is stated.

## 0.5.0 — "Unknown"

### Added
- **Mystery-constant mode** (`unknown_constant=True`). Until now, fitted
  constants were dimensionless (the AI Feynman convention), which put any law
  whose constant carries units out of reach of the constrained search: on
  Hooke's `F = k·x`, no dimensionless constant can relate metres to newtons and
  the engine correctly refused to build anything. The leading multiplicative
  constant may now *carry* a dimension, deduced by homogeneity as
  `target / dim(f)`. The estimator exposes `constant_units_`,
  `constant_value_` and `constant_units_string()`.

  Validated on three reference laws where the answer is known in advance
  (`benchmarks/test_constante_mystere.py`, 20 generations, 1 restart): Hooke
  recovers `kg/s²` and 250.0; Newton recovers `m³/kg·s²` and 6.674e-11; the
  ideal gas law recovers `kg·m²/K·mol·s²` and 8.31446 against a true
  8.314463. All three at R² = 1.000000, structure exact.

- `normalize="none"` — an identity scaler, for callers who want the engine to
  see raw columns.

### Implementation notes
Under `unknown_constant`, the validity gate no longer requires an expression to
*reach* the target dimension, only to *have* a well-defined one; typed
generation draws a random reachable surrogate target so the initial population
spans several dimension classes. Normalisation is deliberately kept on — an
early version disabled it so the constant would be physical, which broke the
gravitation case, since raw `m₁·m₂` reaches 1e8 while the engine clamps at
`_SAFE_LIMIT = 1e6`. Instead the estimator folds the scale factors back into
the reported constant, recovering the per-column exponents by re-running the
dimensional inference with one pseudo-dimension per column. A non-monomial
expression yields `constant_value_ = None` rather than a wrong number.

### Notes
Opt-in and inert by default: `units=` without `unknown_constant` behaves exactly
as in 0.4.1, and without `units=` the engine is byte-identical (8 fits across two
operator sets and four seeds, plus the robust and multi-restart modes). The 19
repository tests pass, as does `verif_v041.py`.

## 0.4.1 — "Lawful" (fixes)

### Fixed
- **`units=` returned numerically wrong models.** `fitness()` and `raw_mse()`
  scored candidates on their linearly-scaled form (`a + b·f(x)`), while
  `wrap_linear_scaling` was disabled under `units=` because the additive offset
  breaks dimensional homogeneity. The champion was therefore *selected* on a
  scaled score and *delivered* unscaled: exact structure, wrong constant,
  negative R². Under `units=` the engine now regresses through the origin
  (`b·f(x)`, no offset) — dimensionally sound, and materialised in the delivered
  tree. On `y = ½·m·v²`: R² goes from **-1.89 to 1.000000**, same size (7 nodes),
  still 1/1 dimensionally valid.
- **Dimensional state leaked between fits.** `_DIM_GATE_DIMS` / `_DIM_GATE_TARGET`
  are module globals, set on a `units=` fit and never reset. Any ordinary fit
  that followed *in the same process* silently ran with the dimensional gate
  active: the same fit scored R² = 1.000000 in a fresh process and **R² = -1.71**
  after a `units=` fit. They are now synchronised on every `evolve()` call, and
  the scale-only flag is propagated to the parallel workers.
- **Float64 overflow in the Levenberg–Marquardt optimizer.** Unbounded
  `sq`/`cube`/`*` chains could reach ~1e198 and overflow during the Jacobian
  products (`overflow encountered in matmul`). Residuals and the Jacobian are
  now bounded. No change to sane fits.

### Notes
Non-regression verified without `units=`: 8 fits (2 operator sets x 4 seeds)
plus the robust and multi-restart modes are byte-identical to 0.4.0.

## 0.4.0 — "Lawful"

### Added
- **Dimensionally-constrained search** (`units=`, `target_units=`): constructive
  typed generation, dimension-preserving mutation and crossover, and a validity
  gate in `fitness()` that rejects unsound candidates from every code path.
  Units accept plain strings (`"m/s"`, `"kg*m/s^2"`, `"J"`, `"s^-1"`) or
  dimension dicts, plus per-name and per-index forms.
- `dim_search.py`, built on the existing `dimensions.py` algebra so that the
  post-hoc auditor and the constrained search cannot diverge.

Without `units=`, 0.3.0 behaviour is unchanged.

## 0.3.0 — "Trust"

### Added
- **Residual diagnostics** (`result.diagnostics(X, y)`): a high R² only says
  the curve passes near the points, not that the model is right. Runs the
  classic residual checks and prints a plain verdict — *structure* (leftover
  curvature = a missing term), *normality* (skew/kurtosis = outliers or wrong
  error model), and *independence* (Durbin-Watson autocorrelation, opt-in via
  `ordered=True` for time series). See `examples/residual_diagnostics.py`.

- **Structural stability analysis** (`stability_analysis(X, y)`): the direct
  answer to the launch's most-repeated critique ("resample the data and you
  get a different formula"). Refits on bootstrap resamples and reports how
  often each structural form recurs, together with the median fit R². The two
  numbers separate three regimes honestly: a dominant form at high R² (trust
  it), several forms at high R² (a real law, not uniquely identified — pick by
  parsimony), or a recurring form at low R² (signal too weak, trust nothing).
  See `examples/stability_bootstrap.py`.


- **Dimensional consistency audit** (`check_dimensions`, `audit_pareto`): the
  direct answer to the launch critique that exponents like `temperature/cycle`
  are physically meaningless. Declare the units of your columns and target; a
  small unit-algebra walks each formula and flags the physical violations
  (non-dimensionless arguments to exp/log/sin, adding a length to a time, a
  dimensioned exponent). It's a post-hoc auditor, not a search constraint
  (that's heavier, still on the roadmap): it tells you which Pareto forms are
  candidate laws and which are empirical-only. See `examples/dimensional_audit.py`.


- **scikit-learn estimator** (`GPEliteRegressor`): standard fit/predict/score,
  works in Pipelines / GridSearchCV / cross_val_score, exposes the discovered
  equation via `.sympy()` and `.equation_`. Passes sklearn's full
  `check_estimator` conformance suite (sklearn 1.6+ tag API supported). This is
  the entry ticket for SRBench. A rehearsal harness
  (`benchmarks/srbench_dryrun.py`) runs the SRBench-style protocol (train/test
  split, fit through the wrapper, report test R²): internal dry run solved 9/11
  sampled Feynman equations at R²_test > 0.999.

## 0.2.2 — 2026-07-06

### Fixed
- **Exports can no longer crash a finished run.** `export_grammar` (meta-
  learning JSON) previously raised on `PermissionError` and destroyed the
  results of a completed evolution. All exports now fall back to the system
  temp directory, and on total failure print a clear warning with a hint
  (OneDrive / Windows "Controlled Folder Access" can block Python writes)
  — the run always completes. Reported on Windows, mode 1 + SEQ transfer.
- One missed French string in benchmark mode translated.

## 0.2.1 — 2026-07-02

### Changed
- **English user interface**: all runtime messages, the interactive menu
  (including mode 7 FORECAST), prompts, reports, warnings, public docstrings
  and error messages are now in English (~150 strings). Yes/no prompts accept
  `y`/`yes` (mapped safely — `y` still selects *poly* in the operator-pool
  choice). French code comments are retained for now; internal i18n is on the
  roadmap. `README.fr.md` continues to serve French readers.

### Fixed
- `examples/kepler_demo.py`: pass raw units to `predict()` (the scaler is
  applied internally). Restores the showcase R² = 1.000000.

## 0.2.0 — 2026-07-02

### Added
- **Levenberg–Marquardt constant fitting** (default; `CONST_OPT_LM=False`
  reverts to legacy Adam). Machine-precision constants — e.g. Coulomb's
  `q1·q2/(4πεr²)` recovered exactly (1−R² ≈ 8e-32). 6–14× faster on
  constant-heavy problems.
- **Native multi-restart** (`restarts=N`): candidate archives merged across
  runs (shared deterministic hold-out), one global selection. Turns seed
  variance into reliability.
- **Pareto front output** (`result.pareto`, `ParetoEntry` objects with their
  own `.predict`): the full complexity ↔ accuracy staircase.
- **Forecast / extrapolation mode**: `extrapolate_feature=`,
  `extrapolate_direction=` — beyond-domain divergence probes, linear safety
  floor, frontier meta-selection. New **mode 7** in the interactive menu.
- **Composition motif seeding** (Pythagorean, reciprocal sums, Gaussian…) for
  nested structures; automatically disabled in extrapolation mode.
- Reproducible benchmarks: `benchmarks/feynman_bench.py` (15 equations,
  frozen protocol) and `benchmarks/duel.py` (gplearn head-to-head).

### Fixed
- **Reproducibility**: parallel workers now use a fixed hash seed; identical
  results per seed within a process. Across invocations: run with
  `PYTHONHASHSEED=0` (documented).
- Robust `api.py` import outside a package (file-next-to-file usage, Windows).
- Motif × extrapolation interaction (forecast regression).

### Numbers (frozen protocol, PYTHONHASHSEED=0)
- Feynman, 15 equations: **10/15 exact recoveries (67%)**, 14/15 < 1e-3.
- gplearn head-to-head (same data/splits, generous budget for gplearn):
  **67% vs 40%** exact; GP_ELITE ahead on 9 equations, tied 5, behind 1.
- Battery SOH forecasting (true extrapolation, unseen cycles): median R²
  **+0.52** vs +0.34 (linear regression), zero divergent models.
