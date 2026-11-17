# Using GP_ELITE

Part of the documentation of GP_ELITE: back to the [README](../README.md); [version française](fr/utilisation.md).

## Is this for you?

You probably want GP_ELITE if **at least one** of these is true:

- **You have a table of measurements and want the formula, not a prediction.**
  A degradation curve, a sensor calibration, an engineering correlation. You care
  about the *shape* of the relationship, and you intend to read it, sanity-check
  it, maybe publish it.
- **You cannot install a second language runtime.** A locked-down university
  machine, a corporate laptop without admin rights, a CI container you do not
  control. `pip install gp-elite` and its three dependencies are all you need —
  no compiler, no Julia, no GPU.
- **You know the physical units of your columns.** Declare them and the search
  will only ever build dimensionally sound formulas — and can tell you the units
  *and value* of a physical constant that is not in your data at all.
- **You are teaching or learning genetic programming.** The engine is plain
  Python you can read, step through and modify, and it ships with an interactive
  console that needs no code at all.

If none of these fit, other tools may serve you better: `PySR` and `Operon` are
faster and more accurate at scale — see [How GP_ELITE is measured](measurements.md).


## Usage

### One line, on your own data (console UI)

```bash
gp-elite
```

Choose mode **6 (generic CSV)**, point to your file, and keep the defaults. GP_ELITE detects the columns, holds out a validation set, evolves, and prints the discovered law — written in your own column names and units, checked against its own predictions on your data.

Mode 6 also asks for the **physical units** of your columns. Declaring
them is optional, and skipping is one keystroke — but if you do declare them, the
search is restricted to dimensionally consistent formulas, and the engine can
deduce the units and value of a missing physical constant. On a two-column CSV of
Hooke's law it returns:

```
  Units for ['elongation'], comma-separated : m
  Unit for TARGET 'force' : N
  Deduce an unknown constant? [y/N] : y
  ...
  Formula in YOUR columns (checked on your data):
    force = 250 * elongation
  Deduced constant units : [kg / s^2]
  Deduced constant value : 250
```

### Programmatically (notebooks, pipelines)

```python
import numpy as np
from gp_elite import symbolic_regression

rng = np.random.RandomState(0)
X = rng.uniform(1, 5, (200, 2))
y = 2.0 + 3.0 * np.sqrt(X[:, 0]) - 0.5 * X[:, 1]

if __name__ == "__main__":        # needed in scripts, see the note below
    result = symbolic_regression(
        X, y,
        feature_names=["a", "b"],
        operators="physical",     # 'physical' | 'trig' | 'full' | 'poly' | 'conserve'
        generations=60,
        speed="fast",             # 'ultrafast' | 'fast' | 'normal' | 'thorough'
        seed=0,
        parallel=False,           # the same model on every machine, see below
    )
    print(result.expression)      # 2 + 3 * sqrt(a) - 0.5 * b
    print(result.r2_validation)   # 1.0
    print(result.size)            # 33 (nodes of the engine's tree)
    print(result.sympy())         # the same formula, parsable by sympy
```

Here the search returns the law it was given, written in your variables: the
engine's tree has 33 nodes, and the formula printed from it is 2 + 3·√a − 0.5·b;
the fit checks that this formula reproduces `predict()`. That is not guaranteed. On a harder law the same budget returns an
approximation that fits the hold-out almost perfectly and is still not the law
(0.7 returned one for this very example); reading the formula is how you find out.
`restarts=` and `speed="thorough"` spend more compute on the exact form, without a
guarantee.

- `speed`: `'ultrafast' | 'fast' (default) | 'normal' | 'thorough'`. `'thorough'`
  (population 400, four islands, 200 generations) is the regime for looking for an
  exact law; with twice the default number of generations, it is slower, and not
  guaranteed to do better. Without `generations=` or `time_limit=`, since 1.2,
  it too stops once it no longer improves (`patience=`, below).
- `time_limit=` (seconds): the search stops cleanly at the deadline and returns the
  best model found so far, instead of being killed without a result; the
  generation under way and the final selection add a little (in the release
  measurement of 1.4.0, the 2,291 fits stopped by a budget of 30 s took 30.5 s
  at the median and 31.9 s at most). A search that finds an exact law ends
  before its budget: with 15 s on 3,000 rows (`benchmarks/time_limit_check.py`),
  the law came back at 9.7 s with the islands in parallel. In sequence the
  search went to its budget, 15.3 s, and returned an approximation of R²
  0.9979 (with 1.3.0 the law had come back at 6.3 s).
- `patience=` (since 1.2): when the call sets neither `generations` nor
  `time_limit`, the search stops once its error on the hold-out rows (the
  training rows when there are none) has not improved by 1 % in 30 generations, then polishes and selects as usual. A fit
  of a ten-point lab table then takes seconds: the six of the French TP notebook
  (`examples/tp_six_lois.ipynb`) took 48 s in all, against 194 to 198 s with 1.1.0 on the same machine, and
  returned the same formulas; with 1.4.0, in its release measurement, they
  take 52 and 53 s in the two runs paired with 1.3.0 the same day, against
  49 and 54 s, with the same formulas (50 to 53 s over the four runs of
  1.4.0). A call that sets its budget (`generations=` or
  `time_limit=`) gets all of it, as in
  1.1. An integer k applies a patience of k generations whatever the budget, and
  0 turns it off. `GPEliteRegressor` always sets its number of generations, so
  the stop does not act there.
- `restarts=`: independent evolutions whose candidates are merged before the final
  choice.

**Your data.** `X` can be a NumPy array, a list of rows or a pandas DataFrame,
whose column names then become the variable names; `y` a 1-D array or a single
column. A missing or infinite value is refused with the row and the column
concerned (remove or impute it first), and a non-numeric column is named in the
error. With 0.7, a missing value in y or in a column the law uses went through,
and the fit returned an unrelated formula without a warning
(`benchmarks/bad_input_check.py`). Values far from 1 need no preparation: a
target of order 1e-9 or 1e20 is divided internally by a power of ten, a column of
order 1e-19 by its largest absolute value (the default normalisation), and the
formula comes back in your units (up to 0.7, such a target returned a constant or
a wrong line, with a negative R², and no warning that the fit had failed).

**Reproducibility.** With the same `seed`, the same data and the same settings, a
fit returns the same model, run after run, without setting `PYTHONHASHSEED`
(required up to 0.7). Parallel islands follow another path than the sequential
search, and `parallel=None` turns them on from four cores: set `parallel=` too.
On another machine the model can still differ: NumPy computes functions such as
`exp` and `tanh` with the instructions the processor offers, which can change
the last digit of a value, and the search can then take another path.

**Scripts and parallel islands.** On machines with four cores or more, islands run
in parallel worker processes. Those workers are started with `spawn` on every
system (Linux included) and re-import your script, so keep the top-level code
under `if __name__ == "__main__":`, as above.
Without the guard GP_ELITE detects the situation, finishes on one core with the
islands in sequence, and says so once; the islands in sequence take another path
than in parallel, so the model can differ. Hence `parallel=False` in the example
above: with the islands in parallel (the default from four cores) it returned
another model, an approximation of R² 0.99998, when measured with 1.0.0
(not measured again since). Notebooks need nothing.

### Reading the result

- **`expression` is written in your variables.** The engine searches on rescaled
  columns internally; the formula it returns has the rescaling folded back into its
  constants, and the fit checks that the formula reproduces `predict()` on your
  data (`result.formula_exact`). `result.sympy()` gives the same formula as a
  string `sympy.sympify` can parse, and `result.sympy_expr()` the sympy
  expression itself, with one symbol per column: use it when a column name is
  also a sympy constant or function (`sympify` reads `E` as 2.718..., `I` as
  √-1) or is not an identifier; `sympy()` warns in that case. (Before 0.7, the
  displayed constants were those of the internal scaled space.) Since 1.2, a
  power of a number is written as an exponential, and an exponential of one
  variable with its scale: `0.00538504 + 5.05644 * 0.00614708^(0.2 * t)` comes
  back as `0.00538504 + 5.05644 * exp(-t / 0.981975)`. The rewritten formula is kept only if it
  passes the same check, so the model and `formula_exact` do not change. The formula is the plain mathematical
  function: where one of the engine's numerical safety nets acts on your data
  (a power clipped because its base exceeds 100 or its exponent 6 in absolute
  value, or its value a million; a division by a denominator within 1e-8 of
  zero; since 1.3, the argument of an arcsine clipped to [−1, 1]), or, rarely, where rounding ruins an ill-conditioned expression, it
  departs from `predict()` on those rows, `formula_exact` is False and the fit
  warns. In the measurements of 0.8
  ([`benchmarks/results_0.8/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks/results_0.8)),
  that was the case for 6 of the 205 Feynman fits of the release at 30 s per fit,
  for none of 60 fits on standardised real data and 8 of 70 on real data in their
  own units (campaigns 5b and 6b), and for 1 of the 105 fits of the equal-work
  comparison (100 generations). The warning also says how many entries of
  `result.pareto` have an exact formula and names the most accurate of them:
  forcing an exact formula on the returned model costs accuracy (measured for
  0.9 in
  [`benchmarks/results_0.9/PLAN_PHASE2.md`](https://github.com/ariel95500-create/gp-elite/blob/main/benchmarks/results_0.9/PLAN_PHASE2.md)),
  so the choice is left to you.
- **`r2_validation` is a selection score.** The hold-out it is computed on is also
  used to choose the returned model among the candidates, so it is optimistic.
  To estimate how the formula generalises, keep a test set of your own out of the
  fit.
- **`result.pareto`** lists the other non-dominated candidates, simplest first,
  each with its own `expression`, `r2_validation` and `predict`.
- **Below 30 rows, nothing is held out:** `r2_validation` and `result.pareto`
  are then `None`, as on Kepler's eight planets or a lab table of 10 or 20
  points. Judge such a fit on rows of your own kept out of it.
- **`predict()` checks what it is given.** It expects as many columns as the fit
  had (a single sample is `X.reshape(1, -1)`), and returns NaN for a row with a
  missing or infinite input, where 0.7 returned 0.


## Tests

```bash
pip install -e ".[test]"
python -m pytest tests/ -q
```

`tests/test_guarantees.py` pins down every defect found so far — each test was
checked to fail on the code that had the defect. The suite runs on every push
that changes code (Linux, Python 3.9–3.14, and Windows).
