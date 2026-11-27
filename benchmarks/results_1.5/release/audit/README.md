# An audit of the code before gate 14 (27 November 2026)

The author asked, before deciding the publication, for an audit of the code
read as if for the first time, now that it is in modules. Two passes of
review were run with a fresh context: the engine (`gp_elite/`, every
module), then the modules around it, which 1.5 does not change (`api`,
`sklearn_api`, `formula`, `dimensions`, `dim_search`, `stability`, `cli`).
Each finding was then checked here: by reading the code, or by reproducing
it on 1.5 (the working tree, `/venv15s`) and on 1.4.0 from PyPI
(`/venv14p`) with `check_api.py` and `check_units.py`, whose outputs are
`check_api.txt` and `check_units.txt`. Nothing in `gp_elite/` was changed.

Every finding that holds is in 1.4.0 already, word for word: none comes from
the split. The models of 1.5 are those of 1.4.0, as M1 measured.

## What holds, in the modules users call

| # | where | what | checked |
|---|---|---|---|
| 1 | `api.py`, `mse_train` of the result | When the model returned is a constant, `mse_train` is 1,000 too large: it is read from a fitness helper that adds a penalty of 1,000 to constant predictions. The model and `mse_validation` are right. | `check_api.txt` B: target constant at 3, model `3`, `mse_train` 1000.0, `mse_validation` 0.0, in both versions |
| 2 | `api.py`, `seed` | With `seed=None`, the default, a fit is seeded with 0: two calls give the same model, which the documentation does not say. And every fit seeds the global generators of `random` and `numpy.random`, so the caller's own random draws after a fit are not what they would have been. | `check_api.txt` C and C2, in both versions |
| 3 | `api.py`, `extrapolate_feature` | An integer out of range is not checked: with `restarts=2` the fit raises `IndexError` after all its evolutions; with `restarts=1` it runs without the guard asked for; `-1` is ignored by the search but read as the last column by the choice among restarts. | `check_api.txt` D, in both versions |
| 4 | `dim_search.py`, units given as text | `"(m/s)^2"` and `"kg*(m/s)^2"` are refused, although parentheses and `^` are documented; `"m*2"`, `"10*m"` and `"()"` are accepted and make a dimension of their own (`"2"`, `"10"`, `")"`). | `check_units.txt`, in both versions |
| 5 | `dimensions.py`, `check_dimensions` | A feature given by its name (`"mass"`, `"X0"`) rather than its index is taken as dimensionless, so a correct law is flagged. | `check_units.txt`, in both versions |
| 6 | `dimensions.py`, `max2` and `min2` | Their dimension is computed as a product: `max2` of two lengths comes out in m², and a correct formula is flagged. `max2` is in the pool of binary operators, so under units the check can turn away a valid model. | `check_units.txt`, in both versions |
| 7 | `stability.py`, `stability_analysis` | Every exception of a run is swallowed: a misspelled argument ends as "all runs failed" with no reason, and the result then has no `median_r2`. | `check_units.txt`, in both versions |

## What holds, in the console only

| # | where | what | checked |
|---|---|---|---|
| 8 | `search.py` 235-238 and `console.py` 406, 676, 840, 973 | The transfer between problems of the console's benchmark, and the import of a grammar by the menu, do nothing: `evolve` empties the fragment library, the co-graph and the sequence memory at its start (since v13.7), just after the console filled them. `docs/features.md` lists grammar export and import as a documented feature; the export works, the import is lost. | read; the same lines in 1.4.0's `core.py` (9890-9893) |
| 9 | `console.py` 1100 | Option 7 of the menu (forecasting) never runs once GP_ELITE is installed: its `import api` looks for a file `api.py` in the current folder, finds none, prints "api.py must be in the same folder" and returns. Forecasting through `symbolic_regression` works. | `import api` from a data folder: `ModuleNotFoundError` |
| 10 | `parallel.py` | In the Syracuse mode with parallel islands, the bias towards the little-used features is off in the workers: they never reset their counter of usage, which stays empty. | read: only `search.py` 245 calls `reset_feature_usage` |

## What does not hold, or is already known

- A call that fails a check of its arguments (`time_limit=-1` with
  `robust=True`) leaves the CSV mode and the robust loss set in the engine,
  but the next call of `symbolic_regression` sets them back, and it returns
  the model a fresh process returns (`check_api.txt` A and A0). The finding
  said the next call would inherit them; it does not.
- The pool's initializer registers empty modules `core` and `gp_v20` in each
  worker: as in 1.4.0, on purpose (`M5_review2.md`, finding 10), and the
  fallbacks that could reach them are never reached in a worker.
- Four functions whose annotations name a class of a later module: known and
  documented in the CHANGELOG (`M5_review2.md`, finding 11).
- Unreachable lines after a `return` in `datasets.py`: there since 1.4.0,
  harmless.
