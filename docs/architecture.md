# How the engine is organised

Part of the documentation of GP_ELITE: back to the [README](../README.md); [version française](fr/architecture.md).

Until 1.4.0, the engine of GP_ELITE was one file, `gp_elite/core.py`, of
12,999 lines. Since 1.5 it is a package of modules, each with one role. The
split changed how the code is organised, not what the engine does: at equal
seed and equal work, 1.5 returns the models 1.4.0 returns, bit for bit, with
the same interface, at the same speed (within 0.3 % on 205 fits of the 41
Feynman equations of the bench). Code that reaches inside `gp_elite.core`
can see a few changes, listed below. This page is for anyone who wants to
read the engine or change it.

## The modules

From the lowest to the highest. A module imports only the modules above it
in this table, never one below it, and none imports `core.py`. A few
functions import, when they run, modules of the package outside the engine
(`dim_search`, `dimensions` and `formula`, and `api` for option 7 of the
console), which themselves import `gp_elite.core`. `tests/test_layering.py`
checks these rules.

| module | what it holds | lines |
|---|---|---|
| `state` | the shared state: the names that change while a fit runs | 72 |
| `numeric` | the protected operators, scalar and vectorised: the safe forms of the operations formulas use | 242 |
| `config` | the run trace (`TRACE`), `Config`, the pools of operators, the configurations the console makes | 621 |
| `tree` | the tree of a formula: `Node`, its hashes, its text and sympy form, its size, depth, complexity and constants | 475 |
| `simplification` | the simplification of a tree, and its caches | 217 |
| `evaluation` | the NumPy code a tree compiles to, the plans of the Jacobian, the compiled functions and their caches, Pearson's r, the cache of predictions | 791 |
| `datasets` | the datasets the console builds: Collatz (Syracuse), the decoy features, `build_dataset` | 449 |
| `scoring` | linear and robust scaling, the errors, the scale of the target, the usage of the variables, `fitness` | 477 |
| `fitting` | the fitting of constants: Levenberg-Marquardt and Adam | 295 |
| `genetic` | random trees, deduplication, ε-lexicase and tournament selection, crossover, mutations, Pareto ranks, stigmergic trees | 899 |
| `memory` | the fragment library, the probe set and semantic signatures, the co-graph, the sequence memory, `warm_transfer` | 1,383 |
| `final_choice` | early stop, patience, the hold-out, the finalists and their polish, the near domain, the rule of one standard error, the small tables | 1,004 |
| `seeds` | the seeds placed before the first generation: motifs, power laws, binomial, elementary and noise-tolerant forms | 1,624 |
| `islands` | `Island`, migration, one generation of an island (`evolve_island`), the reset of the explorer islands | 778 |
| `parallel` | the islands in parallel: the workers, the pools of processes, the guard of the main module | 409 |
| `search` | the hold-out split, the linear candidate, and `evolve`, which runs a fit from the seeds to the final choice | 922 |
| `data` | the scalers, the loading of CSV files and their optional dependencies, the problems of the console | 581 |
| `console` | the printed result, the decoy report, the plot, `run`, the benchmark and the interactive menu | 1,450 |
| `core` | the door: every name `gp_elite.core` had in 1.4.0 (below) | 856 |

Around the engine, the modules that 1.4.0 already had do not change: `api`
(`symbolic_regression`, the entry point), `sklearn_api` (`GPEliteRegressor`),
`formula` (the formula in the user's own variables), `dimensions` and
`dim_search` (physical units), `stability` and `cli`.

A fit goes this way: `symbolic_regression` prepares the data and calls
`evolve`, which places the seeds, runs the generations of the islands (in
parallel or not), and makes the final choice.

## The shared state

61 names hold data that can change once the engine is imported: 52 change
while a fit runs (the hold-out rows, the caches, the custom loss, the pools
of operators of the CSV mode, the memories of the search...), and 9 are
switches of the seeds and of the final choice that only the tests set. They
live in `gp_elite/state.py`, and every function reads and sets them
there, at the moment it runs:

```python
from . import state

def f():
    if state._USE_LINEAR_SCALING:     # read when f runs
        ...
    state._TIME_LIMIT_HIT = True      # set for every module
```

Never `from .state import _USE_LINEAR_SCALING`: that would copy the value at
import, and the module would go on reading the old one after a fit changed
it, without any error.

## gp_elite.core, the door

Scripts, benches and tests written for 1.4.0 read and set names on
`gp_elite.core`. The tests of 1.4.0 pass unchanged, and the door keeps what
they rely on:
- every name `gp_elite.core` had in 1.4.0 can still be read on it;
- a name of the shared state, read, set or deleted on `gp_elite.core`, is
  read, set or deleted in `gp_elite.state` (each is a data descriptor of the
  class of the module, so that pytest's `monkeypatch` puts back the right
  value);
- any other name set or deleted on `gp_elite.core`, a function a test
  replaces or a wrap a bench puts on `evolve_island`, is also set or deleted
  in every module of the engine that held the same object when
  `gp_elite.core` was imported, as in 1.4.0, where all the functions shared
  one namespace; so a name deleted, then set again, reaches them again.

`tests/test_door.py` checks the 421 names of 1.4.0 and each of these rules.

What the door does not keep, for code that reaches inside the engine:
`vars(gp_elite.core)` no longer holds the names of the state, and a value
written into that dictionary does not reach the engine; `unittest.mock.patch`
with `create=True` deletes a name of the state when it ends; reloading
`gp_elite.core` no longer makes the engine afresh;
`from gp_elite.core import *` no longer gives the seven public names of the
state; and the functions and classes now belong to their modules (a pickle made by 1.5 does not load in
1.4.0, and `help(gp_elite.core)` lists none of them). The CHANGELOG (1.5.0)
lists these changes in full.

## For contributors

- A name that changes while a fit runs goes to `state.py`, and is read and
  set as `state.NAME`.
- A module imports only from the modules above it in the table; a function
  may import, when it runs, a module of the package outside the engine.
  `tests/test_layering.py` checks it: a new module goes in the table and in
  the test.
- To observe a function during a fit, for example to count the generations,
  set it on `gp_elite.core`, which passes it on to every module of the engine
  that holds it. Replacing it only in the module where it lives is not
  enough: `evolve_island` lives in `islands`, but `search` and `parallel`
  import it by name and call their own reference.
- New code imports names from the modules where they live, not from
  `gp_elite.core`.

How the split was made and checked, move by move, is in
`benchmarks/results_1.5/PLAN.md` and `benchmarks/results_1.5/split/`.
