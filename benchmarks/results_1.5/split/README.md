# The engine in modules: how it was made and checked

Part A of `../PLAN.md`. Written on 24 November 2026, after the last check.
The page for contributors is `../../../docs/architecture.md`. The reviews of
the release found a fault of the door and a few lines to set back as they
were in 1.4.0; their corrections are in `../release/M5_review2.md`. The
figures below are those of the split, before them.

## The result

`gp_elite/core.py` of 1.4.0, 12,999 lines, is now 17 modules by role and
`gp_elite/state.py`, the module of the shared state. `core.py` keeps 849
lines: its docstring, its imports, the names it imports back from the
modules, the door, and its `if __name__ == "__main__":` block. Every module
has fewer than 2,000 lines (the longest, `seeds.py`, 1,623). The four
criteria of the plan hold:

| criterion | what was measured | record |
|---|---|---|
| A1, the same models | all identical in full, against 1.4.0 from PyPI: the 13 configurations, 615 fits of F41, U41 and F41N1 with the defaults, 400 of the TP diagnostic, the console | `a1/20_final_full.txt` |
| A2, the tests | 269 passed under Python 3.9.25, 3.11.18 and 3.14.6; the CI green on its whole matrix from eb2eac5 | `a2_local.txt`, `../release/ci_runs.txt` |
| A3, the speed | 680.1 s against 678.2 s for 205 fits of F41, the engines in turn, a ratio of 1.0028 | `a3.txt`, `a3_timing.jsonl` |
| A4, the door | the 421 names of `gp_elite.core` in 1.4.0, and each rule of the door, in 69 tests | `../../../tests/test_door.py` |

A1 compares the 13 configurations whole (the tree with its constants in
`float.hex`, the printed formula, the errors, the size, `formula_exact`, the
Pareto front), the records of the 615 fits and of the 400 fits of the TP
diagnostic field by field (their formulas to the first 160 characters, which
is what the records keep), and the console on the lines of its result and the
formula it writes, since it fixes no seed (`compare_a1.py`). The raw runs
are in `a1/runs/`. The same checks on the wheels of the release are in
`../release/`.

## How

1. **The map, before any move** (`map_core.py`, `map.txt`): the run-time
   names of `core.py`, each function and the names it uses, each part's role.
   The first map (0a0090e) counted 45 run-time names; it missed those set
   through `globals()` and by `monkeypatch.setattr`. The corrected map
   (81ed9c3, c7e00fa) counts 66: 61 that hold data and 5 functions that the
   tests replace. The author was told, and approved the count in the
   amendment of `../PLAN.md`.
2. **What the parts use, and the order of the modules** (`deps_core.py`,
   `deps.txt`; `layout_core.py`, `layout.txt`, `layout_check.txt`): cut at
   the sections of the file, the roles used each other in one cycle; 25
   parts placed in another module than their section's, and the order of
   `layout.txt`, leave no module using a module after it.
3. **The one change of code, first** (Split 1, 71902c3, made by
   `state_rewrite.py` and checked on the syntax trees): the 61 names that
   hold data go to `gp_elite/state.py`, every function reads and sets them
   as `state.NAME`, and the door comes at the end of `core.py`. The author
   approved this order, the state before the moves, in the amendment of
   `../PLAN.md`.
4. **The plain moves, one module at a time** (Split 2 to Split 18, made by
   `move_group.py` and driven by `run_moves.py`): each move copies its parts
   without change, checked on the syntax trees, `core.py` imports the names
   back, and every name of 1.4.0 must still be on `gp_elite.core`; each is
   committed, then checked by the short version of A1 (the 13
   configurations and F41 with the defaults) in a second commit, before the
   next move (`a1/02_numeric.txt` to `a1/18_console.txt`, all identical).
5. **The door made a data descriptor per name** (eb2eac5, below), checked by
   the short A1 (`a1/19_door.txt`), then A1 in full, A2 and A3.

`a1/00_baseline_twice.txt`: A1 in full run twice on 1.4.0 finds the two runs
identical, which is what the comparison rests on.

## What went wrong, and what was done

- **The CI failed from Split 1 to eb2eac5.** Under pytest 9.2, which the CI
  installs where the Python allows it, `monkeypatch` saves the value it
  finds in the module's own dictionary; the names of the state were not in
  the dictionary of `gp_elite.core`, so it saved nothing and, on undo,
  deleted the name, which the door passed on to `gp_elite.state`. Every run
  from the push of Split 1 to 6ba1356 failed: in the run of 3190a7c, 7 of
  the 8 jobs failed (under Python 3.11 on Ubuntu, 55 tests of 200 failed and
  6 more raised errors at teardown), and the job under Python 3.9, whose
  pytest is 8.4, passed (`../release/ci_runs.txt`). On the machine, under
  pytest 8.4 and 9.1, the suite passed, and the check after each step was
  A1, not the tests, so it was seen only once the moves were done. In
  eb2eac5 each name of the state is a data descriptor of the class of
  `gp_elite.core`, which `monkeypatch` saves and puts back by value.
  `tests/test_door.py` of eb2eac5, run on the door before it, fails under
  pytest 9.2.0 (63 failed and 61 errors) and passes under 8.4.2
  (`former_door_check.txt`, made after the release's reviews). The models
  do not change (`a1/19_door.txt`).
- **The tools stopped twice on their own faults:** the check of the names
  read the comment line of `core_names_1.4.0.txt` as a name (4fe34dc), and
  `move_group.py` read the parameters (`a`, `b`) of the 22 lambdas of the
  tables `_SYMPY_UNARY` and `_SYMPY_BINARY`, at the top of the tree section,
  as uses of names of the console (398e94d). Each time the move was undone
  or not made, the tool corrected, and the chain restarted.
- **How a move is committed:** `run_moves.py` was first written to commit a
  move together with its check (2df5225). It was stopped during its first
  check (numeric), and changed in bcbac70, before any move was committed,
  so that the move is committed first and its check follows in a second
  commit, the working tree staying clean while the check runs. Split 1,
  made before by `state_rewrite.py`, was committed while its check ran
  (71902c3), and its check came in 0068717.

## Files

- `map_core.py`, `map.txt`; `deps_core.py`, `deps.txt`; `layout_core.py`,
  `layout.txt`, `layout_check.txt`: the map and the order.
- `state_rewrite.py`: the change of code of Split 1. Its door is the one of
  Split 1; the door of eb2eac5 was written by hand.
- `move_group.py`, `run_moves.py`: the moves.
- `run_a1.sh`, `compare_a1.py`, `a1/`: A1, and `a1/runs/` its raw runs
  (README there). `a2_local.txt`: A2 on the machine.
  `former_door_check.sh` and `.txt`: the test of the door on the former door. `time_a3.py`, `a3.txt`, `a3_timing.jsonl`: A3.
  `core_names_1.4.0.txt`: the names of A4 (also in `../../../tests/`).
