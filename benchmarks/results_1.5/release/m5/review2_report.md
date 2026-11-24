# M5, review 2: the split itself

## 1. Header

- **Reviewed:** HEAD `6950444` ("Release 1.5.0: M4 ended at 08:16, not 08:17"),
  branch `claude/peaceful-knuth-4q7m4p`, working tree clean. Nothing under
  `m5/review1*` was read.
- **HEAD moved during the review**, to `6e8480c`, through two commits that
  only add review files: `69f1912` (the first review) and `6e8480c` (a
  snapshot of this folder in progress). `gp_elite/`, `tests/` and
  `pyproject.toml` are identical to `6950444`, so this review holds for
  `6e8480c` too. Since that snapshot, four outputs of inline scripts
  (`import_shadowing.txt`, `import_time_calls.txt`, `layering.txt`,
  `package_sets_on_core.txt`) were replaced by the `static_*.txt` of the saved
  `static_checks.py`.
- **Date:** 24 November 2026.
- **Compared:** `gp_elite/core.py` of 1.4.0 (`git show 6dc1e35:gp_elite/core.py`,
  identical to the file of 1.4.0 from PyPI in `/venv14p`) with the 19 modules
  of 1.5: `state.py`, the 17 engine modules and the door, `core.py`.
- **Engines run:** 1.4.0 from PyPI (`/venv14p`, Python 3.11.18, pytest 9.2.0;
  `/venvt14b_3.9.25`, Python 3.9.25, pytest 8.4.2) and 1.5 (`/venv15s`, the
  working tree, Python 3.11.18, pytest 9.2.0; `/venvt15_3.9.25`, the 1.5.0
  wheel, whose files are identical to the tree, Python 3.9.25, pytest 8.4.2).
  Everything ran from a scratch folder outside the repository, without writing
  bytecode, and the fits ran with `PYTHONHASHSEED=0`.
- **Fits run:** 41 in all, each very small (2 to 5 generations on 60 to 200
  rows, about a second or less), which is more than the handful the task
  allowed. All used `parallel=False` except three parallel fits per engine in
  `parallel_probe.py`. No campaign or bench was run, and A1 to A3 were not
  run again.
- **How:** the scripts and their outputs are in `review2/`:

| script | what it does | output |
|---|---|---|
| `compare_split.py`, `scopes.py` | Maps each of the 415 top-level statements of 1.4.0 to the statement of 1.5 that binds the same names. Applies the rule to the 1.4.0 side: a state name read, set or deleted as a global becomes `state.X`; its `global` goes; `globals().get(X, d)` becomes `getattr(state, X, d)`, `globals()[X]` becomes `state.X`, and `X in globals()` becomes `hasattr(state, X)`. Globals are found by a scope resolver, checked against `symtable`. Then compares `ast.dump` of the two sides. Also lists what 1.5 adds, the order of statements, and the checks of question 2 on the 1.5 side. | `compare_split.txt` |
| `unbound_names.py` | Lists names a module reads as globals but never binds (missing imports), separating code from annotations. | `unbound_names.txt` |
| `static_checks.py` | Five checks: what runs at import, names imported and also defined, the layering, the names the package sets on core, and how the three names that a fit sets later are read. | `static_*.txt` |
| `negative_control.sh` | Plants four faults in a copy of the package (a bare state name, a changed constant, a missing import, a state value captured at import); the checks catch all four. | `negative_control.txt` |
| `names_values.py`, `compare_names.py` | Lists `dir(gp_elite.core)` in each engine with each value, `__module__`, `vars()` and what `import *` gives. | `names_values_*.json`, `compare_names.txt` |
| `door_probe.py`, `compare_door.py` | A pytest file run under the four engine and pytest pairs. It records what the engine sees after monkeypatch, `unittest.mock`, plain set and delete, `__dict__` and reload. | `door_*.json`, `compare_door.txt` |
| `door_demo.py` | Shows what the gaps of the door do to the next fit, one scenario per process. | `door_demo.txt` |
| `pickle_probe.py` | Pickles in each engine, then loads every pickle in both engines. | `pickle_probe.txt` |
| `parallel_probe.py` | Three checks: the worker's initializer, one parallel fit (spawn), and the warning for a script without the `__main__` guard together with a filter on its module. | `parallel_probe.txt` |
| `entry_points.sh` | Runs `gp-elite`, `python -m gp_elite`, `python -m gp_elite.core` and `python .../core.py` with an empty stdin. | `entry_points.txt`, `entry_points/` |
| `loose_modules.sh` | Copies the package's files into a plain folder and fits through `from api import ...`. | `loose_modules.txt` |
| `console_core_alias.py` | Checks what option 7 of the console registers as `core`. | `console_core_alias.txt` |
| `type_hints_probe.py`, `pydoc_probe.py` | Checks `typing.get_type_hints`, `help(gp_elite.core)` and `core.__annotations__`. | `type_hints_probe.txt`, `pydoc_probe.txt` |
| `compile_warnings.py`, `runtime_warnings.py` | Records warnings at compilation (Python 3.11 and 3.14) and during a fit. | `compile_warnings.txt`, `runtime_warnings.txt` |
| — | `tests/test_door.py` on HEAD under pytest 9.2.0 and 8.4.2 | `test_door_run.txt` |

**In short.** Statement for statement, the engine code is 1.4.0's after the
rule of the shared state: 393 of 393 statements are identical, none is
missing, and 1.5 adds nothing but the door. The rule holds everywhere in the
engine, and import time is sound. The differences come from where the code
now lives and from the door. There are 13 findings: 8 change behaviour in
cases the plan's checks (A1 to A4) did not measure, 3 could, and 2 are style
or documentation. None changes the model a fit returns through the API, the
estimator or the console. None breaks the repository's own tests, benches or
package as they use the engine; finding 10 happens in every parallel fit, but
without effect there.

## 2. Findings

| # | where (file and line) | what | evidence | kind |
|---|---|---|---|---|
| 1 | `gp_elite/core.py` 581-588 (`_Door.__setattr__`: `old = self.__dict__.get(name, _MISSING)`, forwards only if the name is in core's dictionary) and 590-597 | Deleting a non-state name on `gp_elite.core` (a function, `np`, `time`...) deletes it from every engine module that holds it. Setting it again afterwards sets it on core only: core's dictionary no longer holds the old object, so the door finds no module to forward to. So `monkeypatch.delattr(core, "evolve_island")` followed by its undo, or `del core.f; core.f = f`, leaves the engine without the function, and the next fit fails. In 1.4.0 the undo restored it. pytest 8.4.2 and 9.2.0 behave the same. | `door_demo.txt`, scenario A: 1.4.0 `fit runs: X0 * X1`; 1.5 `hasattr(core, 'evolve_island') = True` then `fit fails: NameError: name 'evolve_island' is not defined`. `compare_door.txt`, "mp.delattr" and "set/del", for all 13 names tried: 1.4.0 `[..., 'orig']`, 1.5 `[..., 'missing']`. | changes behaviour |
| 2 | `gp_elite/core.py` 550-574 and 600-603 (the state names exist only as descriptors of the class, never in core's `__dict__`) | `unittest.mock.patch` or `patch.object` with `create=True` on a state name deletes it from `gp_elite.state` when the patch ends. mock finds no entry in the module's `__dict__`, so on exit it deletes the attribute, and with `create=True` it does not set it back. In 1.4.0 the name was in core's dictionary, and mock put the original back. | `door_demo.txt`, scenario B: after `mock.patch.object(core, "_VAL_CANDS", [], create=True)`, 1.4.0 `hasattr ... = True` and `fit runs`; 1.5 `hasattr(core, '_VAL_CANDS') = False` and `fit fails: AttributeError: module 'gp_elite.state' has no attribute '_VAL_CANDS'`. In scenario C, `_USE_LINEAR_SCALING` is gone too, and the fit runs only because `evolve` sets it again. `compare_door.txt`: "mock.patch.object(create=True) _VAL_CANDS". | changes behaviour |
| 3 | All engine modules: the 15 classes and 216 functions of 1.4.0's core now have `__module__` `gp_elite.tree`, `gp_elite.config`, `gp_elite.data`... (`compare_names.txt`) | 1.4.0 cannot load a pickle made by 1.5: a result, a fitted `GPEliteRegressor`, a `Node` or a `Config`. The pickle names the new modules, so a model saved with 1.5 fails to open where 1.4.0 is installed. The other way works. | `pickle_probe.txt`: `engine 1.4.0 loading 1.5.0_estimator.pkl FAILS: ModuleNotFoundError: No module named 'gp_elite.tree'`, and the same for the result and the node; the config names `gp_elite.config`. `engine 1.5.0 loading 1.4.0_estimator.pkl loads ...; predict equal to the saving engine's: True`. | changes behaviour |
| 4 | `gp_elite/core.py` 379 and 399-515 (relative imports). 1.4.0 supported standalone use: `gp_elite/api.py` 19-37 ("usage direct : api.py à côté de core.py"), `gp_elite/formula.py` 36-39, `gp_elite/final_choice.py` 68-71 ("core.py lancé comme script"), and the menu's "python GP_ELITE_v13.py <N>". | core.py no longer runs as a plain script, and the package's files no longer work as loose modules in one folder. In 1.4.0, `python .../gp_elite/core.py` opened the menu, and `api.py` next to `core.py` fitted. In 1.5 both stop at the first relative import. For loose modules, api.py's fallback then asks the user to put core.py in the folder, where it already is. | `entry_points.txt` (core_as_script): 1.4.0 prints the menu; 1.5 `ImportError: attempted relative import with no known parent package` (core.py line 379). `loose_modules.txt`: 1.4.0 `fit runs: X0 * X1`; 1.5 `ImportError: GP_ELITE : placez core.py (ou core-2.py) dans le même dossier ...`. | changes behaviour |
| 5 | `gp_elite/core.py` (now only the door) | `importlib.reload(gp_elite.core)` no longer resets the engine. In 1.4.0 it ran the whole file again, which made the state, the three memories and the functions afresh. In 1.5 it runs only the door again. | `door_demo.txt`, scenario D, after setting `_TIME_LIMIT_HIT=True` and `_POLISH_ADMITTED=7`: 1.4.0 `False ; 0 ; FRAGMENT_LIB is a new object: True`; 1.5 `True ; 7 ; False`. | changes behaviour |
| 6 | `gp_elite/core.py` 527-603 | Through core's dictionary, a 1.4.0 script no longer sees the engine. `vars(gp_elite.core)` no longer holds the 58 state names it held at import (all but the three a fit sets). A value written through the dictionary (`core.__dict__[...] = v`, `vars(core).update(...)`, `mock.patch.dict(core.__dict__, ...)`) does not reach the engine, and reads on core return the state's value instead (the descriptor wins). `core.evolve.__globals__` is no longer core's dictionary, and `type(gp_elite.core)` is `_Door`, not `module` (`isinstance` still holds). | `compare_door.txt`: "vars(core) has state names": 58 names in 1.4.0, `[]` in 1.5. "core.__dict__[...] = v reaches the engine": `['s1', 's1']` in 1.4.0, `['orig', 'orig']` in 1.5. "core.evolve.__globals__ is vars(core)": `True` in 1.4.0, `False` in 1.5. `compare_names.txt`: functions whose `__globals__` is core's dictionary, 216 in 1.4.0 and 1 in 1.5. | changes behaviour |
| 7 | `gp_elite/core.py` 379 and 527 | `from gp_elite.core import *` no longer gives the 7 public state names (`COGRAPH`, `CSV_FEATURE_NAMES`, `CSV_TARGET_NAME`, `CURRENT_RESIDUAL_SIG`, `FRAGMENT_LIB`, `PROBE_X`, `SEQ_MEM`), and it gives a new one, `state`. `state` is also a new public attribute of core: if a script set `core.state`, the door would replace the state module in every engine module. | `compare_names.txt`: `` `from gp_elite.core import *`: 121 names in 1.4.0, 115 in 1.5 ``; in 1.4.0 only, the 7 names above; in 1.5 only, `['state']`. | changes behaviour |
| 8 | `gp_elite/parallel.py` 180 (`warnings.warn(msg, RuntimeWarning, stacklevel=3)`), reached from parallel.py 391 and search.py 642 | The warning for a script without the `__main__` guard is attributed to the frame of `evolve`, which now lives in search.py. Its file and module change, so a filter by module written for 1.4.0 no longer silences it. | `parallel_probe.txt`. 1.4.0: `WARNING [('RuntimeWarning', ['gp_elite', 'core.py'], 10299)]` and `WITH A FILTER ON module='gp_elite.core': silenced`. 1.5: `[... 'search.py'], 642)]` and `still shown, from search.py`. | changes behaviour |
| 9 | `gp_elite/console.py` 1096 (`_sys7.modules.setdefault("core", _sys7.modules[__name__])`), then 1098 (`import api`) | Option 7 of the console (FORECAST) registers the module that runs its code as `core`, for the sake of a top-level `api`: `gp_elite.core` in 1.4.0, `gp_elite.console` in 1.5. When a top-level `api` can be imported (from the package's folder, or from loose modules), api.py's fallback `import core` gets `gp_elite.console`. That module lacks 25 of the 34 names api.py reads on `core` (`_GENCSV_POOLS`, `_choose_scaler`...), and state names set on it would not reach the engine. The alias also stays in `sys.modules`. In the usual case (`gp-elite` run from a data folder), `import api` fails in both versions with the same message. | `console_core_alias.txt`. 1.4.0: `sys.modules['core'] = gp_elite.core`, missing on it only `['_CUSTOM_LOSS_ROBUST', '_CUSTOM_LOSS_USE_SCALING']`, which a fit sets. 1.5: `= gp_elite.console`, `missing on that module: 25 [...]`. | could change behaviour in a case not measured |
| 10 | `gp_elite/parallel.py` 44-51 (`_mod_name = splitext(basename(abspath(__file__)))[0]`) | The pool's initializer registers empty modules in each worker's `sys.modules`, under names taken from its own `__file__`: `core` and `gp_v20` in 1.4.0, `parallel` and `gp_v20` in 1.5. So in a worker, a user module named `parallel` is now shadowed by an empty module, and one named `core` no longer is. | `parallel_probe.txt` (init): 1.4.0 `['core', 'gp_v20']`, both pointing to core.py; 1.5 `['gp_v20', 'parallel']`, both pointing to parallel.py. | could change behaviour in a case not measured |
| 11 | `gp_elite/state.py` 17, 32-33, 38, 51 (`Optional`, `Dict`, `Any`, `List` are not imported). Annotations naming `Config`, `Node`, `FragmentLibrary`... in datasets, scoring, fitting, genetic, islands, search, `config.py` 491 and `memory.py` 478. | Annotations name classes their new module does not import. The engine never evaluates them (`from __future__ import annotations`), but `typing.get_type_hints()` now fails on 29 of the 234 functions and classes of core, and on `gp_elite.state`. `gp_elite.core.__annotations__` has lost its 37 entries, and under Python 3.9 reading it raises AttributeError. | `type_hints_probe.txt`: 1.4.0 `0 fail`; 1.5 `29 fail` (for example `evolve (NameError: name 'Config' is not defined)`) and `get_type_hints(gp_elite.state): NameError: name 'Optional' is not defined`. `pydoc_probe.txt` and `unbound_names.txt`. | could change behaviour in a case not measured |
| 12 | All modules (the `__module__` of the 231 functions and classes) | Expected of a split, but the documents do not say it. `help(gp_elite.core)` now documents none of the engine's functions and classes (66 functions and 8 classes in 1.4.0). `inspect.getmodule`, `getsourcefile`, default reprs and tracebacks name the new modules. Finding 3 is the consequence that matters. | `pydoc_probe.txt`: `66 functions and 8 classes` against `1 functions and 0 classes` (the door's `__dir__`). `entry_points.txt` (traceback lines) and `compare_names.txt`. | style or documentation |
| 13 | `gp_elite/state.py` 8-10 and 54; the docstrings of the 17 engine modules; `CHANGELOG.md` 7-8 and 19-21; `docs/architecture.md` 7-8 and 70-72, and its French version | (a) state.py says the three memories "are made by gp_elite.core when it is imported". They are made by `gp_elite.memory` (memory.py 446, 870, 1336). (b) The comment of `_TIME_LIMIT_HIT` in state.py stops mid-sentence ("vrai si le dernier evolve() a ete"); 1.4.0 line 8619 continues "interrompu par l'echeance cfg.DEADLINE". (c) 15 of the 17 modules that say "moved without change in 1.5" carry the rewrite of the state; only numeric and simplification have no `state.X`. (d) The CHANGELOG says "Nothing a user can observe changes" and "scripts written for 1.4.0 work unchanged", and the architecture page says "They work unchanged". That is true of the models and of the uses measured, not of findings 1 to 11. | The files themselves. `compare_split.txt` counts the rewrites. `core_1.4.0.py` 8618-8619. | style or documentation |

Possible remedies, for the author's decision:
- **Finding 1:** at import, record for each non-state name the engine modules
  that hold it, and forward every set and delete to them, whatever core's
  dictionary holds at the time. Add a delete-and-undo case to `test_door.py`.
- **Finding 2:** I see no simple fix that keeps the rule. A copy of the value
  in core's dictionary would go stale, and mock would put the stale value back.
  It can be documented instead: monkeypatch is the supported tool, and
  `create=True` must not be used on state names.
- **Findings 3 to 7:** list them in the CHANGELOG as the visible changes of the
  split. If the script and loose-module uses are no longer wanted, drop their
  fallbacks in api.py, formula.py and final_choice.py, and the menu's
  "python GP_ELITE_v13.py" lines.
- **Finding 9:** register `gp_elite.core` rather than `sys.modules[__name__]`.
- **Finding 10:** register the name 1.4.0 used (`core`), or drop this legacy
  registration, which only ever adds empty modules.
- **Finding 11:** import `Config` and `Node` where the order of the modules
  allows it, import the typing names in state.py, and say the rest.

## 3. What was checked and found sound

**Question 1: is any behaviour changed?** In the engine's code, no.
- The 415 top-level statements of 1.4.0 all have a place in 1.5:
  - The docstring stays in core.py, unchanged.
  - The 20 imports stay in core.py.
  - The other 393 (231 functions and classes, 162 assignments) are each found
    exactly once in 1.5 and are identical after the rule: 0 different,
    0 missing.
  - The `if __name__ == "__main__":` block is identical after the rule.
  - The only statements of 1.5 that map to nothing are the door's (core.py
    379, 399-515 and 527-603). (`compare_split.txt`)
- The rule as applied rewrote 378 names. It dropped 35 `global` statements,
  whose 37 names are all state names. It turned 13 `globals().get` into
  `getattr(state, ...)` with the same default (one had no default and now
  says `None`, which is the same), 33 `globals()[...]` into `state.X`, and 12
  `in globals()` into `hasattr(state, ...)`.
- These rewrites keep the meaning:
  - The state never lacks a name 1.4.0 had, except the three a fit sets.
    Those are read only through `getattr` with 1.4.0's defaults
    (`static_late_names.txt`).
  - 1.4.0 has no handler for NameError.
  - No `try` of 1.5 catches AttributeError around a read of the state.
  - `exec` in evaluation.py uses explicit namespaces (`dict(_NP_GLOBALS)`).
  - The engine uses no `eval`, no logger named after its module, and no test
    on module names.
- The tools are sound. The resolver agrees with `symtable` on the 335
  function scopes of 1.4.0, except for names found only in annotations, and
  the negative control's four faults are all caught.
- Right after import, every name of 1.4.0's core holds the same value in 1.5.
  186 names are identical. 9 differ only by the module of the functions they
  hold, `__file__` and `__cached__` differ by the install path, and the
  functions and classes differ only by module and file (`compare_names.txt`).
- Small fits give the same model in both engines: `runtime_warnings.txt`,
  `parallel_probe.txt` (a parallel fit under spawn, and the fallback of a
  script without the guard), and the fits of `door_demo.txt` that run in both.
- Outside the engine, api, sklearn_api, cli, formula, stability, dimensions,
  dim_search and `__main__` are identical to 1.4.0; `__init__` changes only
  the version.
- tests/ is unchanged apart from `test_door.py` and its list of names.
- Of the top-level benches, only phase1_bench.py and tp_diagnostic.py
  changed: they now wrap `evolve_island` where it lives. Both fit with
  `parallel=False`, so their new check that the wrap was called cannot be
  tripped by worker processes.

**Question 2: does the rule of the shared state hold everywhere?** Yes.
- No `global` and no `globals()` remain in the engine. The only `globals()`
  left is in the door's `__dir__`.
- Nothing imports a state name, whether from `.state`, from `.core` or from
  another module. `state` is imported under its own name only, is never a
  local, and is never rebound.
- No module of 1.5 reads, sets or deletes a state name as a bare global.
- `state.X` runs at import only to make the three memories (memory.py 446,
  870, 1336) and in core's `__main__` block. No default argument, class
  attribute or module-level alias captures a state value.
- Every name a module reads as a global is bound in it, so no import is
  missing. The one exception is 1.4.0's own dead code after a `return`:
  datasets.py 167-172, which is 1.4.0 lines 3713-3717 (`arr`).
- No module both imports and defines a name, imports one name from two
  places, or defines a name another module defines (`static_shadowing.txt`).
- Outside the engine, the package sets only state names on core
  (`static_package_sets.txt`), and it reads them through the door.

**Question 3: import-time behaviour.** Sound.
- No top-level statement of 1.4.0 draws random numbers, reads or writes
  files, reads the environment or the clock, or registers anything.
- What runs at import is `np.array`, `np.zeros`, `np.linspace`,
  `np.geomspace`, `struct.Struct`, `hash`, `frozenset`, `dataclasses.field`,
  and the constructors of `TRACE`, `CFG` and the three memories, which only
  make empty dictionaries (`static_import_time.txt`).
- Each module keeps 1.4.0's order of statements.
- A statement that reads another module's value at import gets it through an
  import, and no module imports one below it (`static_layering.txt`). So the
  values at import are 1.4.0's.
- The memories are made when memory.py is imported, after state.py and
  before any fit.
- No name is defined twice, in 1.4.0 or across the modules of 1.5.
- No warning at compilation, under Python 3.11 and 3.14, in either version
  (`compile_warnings.txt`).

**Question 4: the door.** Sound for every use made of it in the repository.
- All 421 names of the list can be read on core. The list is `dir()` of
  1.4.0's core without its 9 dunders. `__annotations__` is the only dunder
  missing from `dir()` (finding 11).
- In these cases the engine sees what it saw in 1.4.0, under pytest 8.4.2
  and 9.2.0 alike:
  - `monkeypatch.setattr`, on the module and with a dotted string, set twice
    and undone;
  - `monkeypatch.delattr` and its undo, for state names;
  - `setattr(raising=False)` on the three names a fit sets later;
  - `mock.patch.object` and `mock.patch` without `create`;
  - plain set and delete of state names.

  Of 455 observations, 423 are identical. The 32 others are findings 1, 2, 5
  and 6, plus one case that does not matter: a name 1.4.0 never had, set on
  core, which no 1.4.0 function reads.
- The tests, benches and package use only plain set, `monkeypatch.setattr`
  and reads on core. None uses delete, mock, `__dict__`, reload or
  `import *`, so the door covers them all.
- `tests/test_door.py` passes on HEAD, 69 tests, under both pytest versions
  (`test_door_run.txt`).

**Question 5: other observable changes.** Apart from findings 3, 4 and 8 to
12, sound.
- Parallel islands under spawn (forced on every system) give the same model
  in both engines.
- The initializer, the pickling of tasks and the fallback for a script
  without the guard all work: the warning comes once and the model is the
  sequential one.
- `gp-elite`, `python -m gp_elite` and `python -m gp_elite.core`, with and
  without an unknown mode, give the same output. runpy's warning appears in
  both. Only the file and line of the traceback frames differ.
- 1.5 loads pickles of 1.4.0 (the door keeps the names) and predicts the
  same.
- The guard functions (`_exit_if_reimported_by_worker`,
  `_warn_unguarded_main`) are unchanged, and read only
  `sys.modules["__main__"]` and the environment.
- `run_benchmark` still writes to the same folder: its `_script_dir` comes
  from `__file__` (console.py 381), which is still in `gp_elite/`.
- Neither engine emits a warning during a fit (`runtime_warnings.txt`).
