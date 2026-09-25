# Changelog

## 0.7.0 — "Sound"

This release fixes what an external review of 0.6.1 found, and re-measures
every number the README quotes on the released code. One default changes
(`normalize="auto"`, measured below); no new search heuristic.

### Fixed — the delivered formula
- **The formula is written in your variables, for every normalisation, and
  checked.** The engine searches on rescaled inputs, and up to 0.6.1 the tree
  was printed with the raw column names but the scaled values: `y = 3x` on
  `x` in [1, 5] came out as `15.0 * x`. `sympy()` folded the scaling only for
  the division-by-max normalisation; with min-max (then the default for any
  column with a non-positive value) or z-score, the exported formula was off
  by 70 on a target of amplitude 28. The 0.6.1 entry below says `sympy()` is
  numerically equivalent to `predict()`: that held only without scaling.
  Now `expression`, `equation_`, `pretty()`, `sympy()`, every Pareto entry and
  the console (mode 6) give the formula in the raw variables, with the
  rescaling folded into its constants, and the fit checks that it reproduces
  `predict()` on the training data (`result.formula_exact`). Protected
  operators are written as the engine computes them where it matters on the
  data (`sqrt(|u|)` when `u` changes sign, sign-aware even powers). Property
  tests cover division-by-max, min-max, z-score and no scaling, one and several
  variables, signed and positive data; 1,500 random trees were checked against
  sympy with no discrepancy (`gp_elite/formula.py`, `tests/test_guarantees.py`).
- **A model is evaluated with its own constants.** Compiled functions,
  predictions, fitness values and simplified forms were cached under a hash
  that rounds constants to 4 decimals, so two trees differing only further
  down shared one entry: `predict()` could compute with the constants of
  another model (compiled earlier, possibly in an earlier fit of the same
  process), `simplify()` merged `1.00001*x + 1.00002*x` into `2*(1.00001*x)`,
  and two identical fits in a row could return different models (measured in
  robust mode). Every cache of values is now keyed on the exact tree.
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
  `sin`/`cos` under `operators="physical"`. 48 fits across all pools, 0
  out-of-pool operator.

### Added
- **`time_limit=`** (seconds): the search stops cleanly at the deadline and
  returns the best model found so far, instead of being killed without a
  result by an external timer. Remaining time is shared between restarts;
  `result.time_limit_reached` and `result.restarts_completed` say what
  happened. Overshoot measured at about one generation (15 s budget: 16.2 s
  sequential, 16.6 s parallel); without `time_limit` results are
  bit-identical to before.
- **`speed="thorough"`**: population 400, four islands, 200 generations by
  default, the regime for looking for an exact law. The `normal` preset
  population goes from 300 to 400 (better at equal budget, same time).
- `SRResult.sympy()`, `ParetoEntry.sympy()`, `formula_exact`.

### Changed
- **`normalize="auto"` divides every column by its max |value|**, signed
  columns included (they went through min-max, which turns each variable into
  `a*(x - x0)` and breaks multiplicative structure). Decided on a criterion
  written before measuring (`benchmarks/norm_signed.py`, raw results in
  `benchmarks/results_0.7/`). On 8 laws with signed inputs × 5 seeds: exact
  recoveries 24/40 against 10/40, near ones 33 against 31. On 6 real PMLB
  datasets standardised as SRBench does × 5 folds: median test R² 0.819
  against 0.788, mean 0.759 against 0.757, worst fold 0.016 against 0.398;
  divmax is better on 17 of 30 paired folds, no collapse on either side, and
  the delivered formulas are shorter (median 12 nodes against 17). On real
  data it is roughly a wash with one bad fold; on laws it is a clear gain.
  `normalize="minmax"` remains available.
- **A law found exactly is no longer traded for a shorter approximation.**
  The final choice keeps the smallest candidate within 0.3 % of R² of the
  best, to avoid fitting noise. On Feynman I.18.12 it returned
  `0.0776 + 0.9967*r*F*sin(1.0106*th)` while `r*F*sin(th)`, exact, was in the
  front. When the best candidate reproduces the hold-out to numerical
  precision (MSE ≤ 1e-12 × variance) there is no noise to avoid, and only
  exact candidates stay eligible. Measured: the rule never fired on the 60
  real-data fits of the normalisation study nor on the 60 of the guard study;
  on the Feynman benchmark it turns I.18.12 into an exact recovery.
- Unknown option values raise `ValueError`: `operators="phsyical"` used to
  become `"physical"`, `speed="fats"` the `normal` preset, and
  `normalize="divmx"` min-max scaling, silently.
- The console (mode 6) printed the engine's internal expression with the real
  column names (`24.97 * elongation` for the law `250 * elongation`); rescaled
  columns now carry a prime, and the law in your columns follows.
- **Scripts without an `if __name__ == "__main__":` guard** no longer run
  three times over on Windows and macOS when parallel islands start: the
  engine detects it, finishes on one core with the same result and warns
  once (measured: 9.0 s and three executions before, 5.9 s after).
- The API writes no file. It used to write `gp_elite_log.csv` into the
  installation directory or the current one.
- Near-domain guard at the final selection: among candidates the parsimony
  rule considers equivalent, one that explodes just outside the data (a pole
  between two training points) is no longer preferred. Measured cost: none —
  on 60 real-data folds (6 PMLB datasets × 2 seeds × 5 folds,
  `benchmarks/near_guard_study.py`) it never intervened, and none of the 322
  front candidates exploded on the test folds. Its benefit is shown on
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
- Feynman benchmark, 15 equations, one seed: 11/15 exact (1−R² < 1e-9 on
  held-out data), 13/15 within 1e-3; with `units=` declared, 14/15 exact, each
  in its textbook form. Against gplearn on the same data: 11/15 against 6/15
  exact.
- `units=` on Feynman II.11.3, 5 seeds: 5/5 dimensionally valid against 0/5,
  median size 19 against 61 nodes, and one run in five recovers the exact law
  (none did in 0.6).
- Robust mode: error divided by six at 10 % outliers, no gain at 20 % on the
  bundled example (the 0.6 table showed a best-of-three chosen with the true
  law).
- Data size (`normalize="none"`, 5 equations): 4 of 5 exact at every size from
  500 to 10,000 points.

### Project
- Continuous integration on Linux (Python 3.9–3.14) and Windows.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`; `CITATION.cff`
  updated; `__version__` read from the installed metadata.
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
