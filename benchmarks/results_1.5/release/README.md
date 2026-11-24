# Measurements of the release 1.5.0

What `../PLAN.md` asks before gate 14 ("The release of 1.5.0"), as it was
measured, for two candidates: the first, measured on the morning of 24
November, and the second, which carries the corrections the reviews of M5
asked for, measured again in the same way. The machine has 4 cores of an
Intel Xeon (`machine.txt`, `candidate2/M1.log`). Every fit runs in its own
process with `PYTHONHASHSEED=0` and one BLAS thread, but configuration
M_twice of A1, which runs two fits in one process by design.

What A1 compares (`../split/compare_a1.py`): the 13 configurations of
`../../speed_equivalence.py` whole (the tree with its constants in
`float.hex`, the printed formula, the errors, the size, `formula_exact`, the
Pareto front); the records of F41, U41 and F41N1 with the defaults of the
API (615 fits) and of the TP diagnostic (400 fits) field by field, every
field but the time, the date and the path and version of the engine, the
formulas to their first 160 characters, which is what the records keep; and
the console on the lines of its result and the formula it writes, since it
fixes no seed. The raw runs are in `../split/a1/runs/`.

## The first candidate (22f5734)

Commit 22f5734 carries the engine measured in `../split/` (the door of
eb2eac5) and changes only the version number: `pyproject.toml`, the version
`gp_elite` gives when it runs from the sources, and `CITATION.cff`. Its wheel
and source archive were built with `uv build` from a clean export.
`environments.txt` gives their SHA-256, the SHA-256 of each of the 29 files
of `gp_elite/` in the wheel, and the packages of the two environments:
- `/venv15r`: the wheel alone, with the packages of `/venv14p` (Python
  3.11.18, NumPy 2.4.6);
- `/venv14p`: gp-elite 1.4.0 installed from PyPI, whose 11 files of
  `gp_elite/` are those of 6dc1e35 (`../size/engine_check_*.txt`).

The machine had restarted at 06:51:57 UTC on 24 November, after the
measurements of `../split/` and before this candidate: its boot time, read
with `uptime -s` at 09:06 UTC, before a later restart, and not saved to a
file then.

### M1, A1, A3 and A4 on the wheel (24 November 2026, 07:04 to 08:05 UTC)

`run_m1.sh`, one after the other (`M1.log`):
- **A1, in full:** the 13 configurations, the 615 fits and the 400 fits of
  the TP diagnostic and the console, compared with the run of 1.4.0 of the
  split (`../split/a1/runs/a1_140` against `a1_rel`): all identical
  (`M1_A1.txt`). The total time of the 13 configurations, 21.2 s for 1.4.0
  and 27.0 s for the wheel, comes from runs some hours apart, the second
  just after the restart of the machine; it says nothing of the speed,
  which A3 measures.
- **A3, alone on the machine:** F41 with the defaults, 205 fits per engine,
  one at a time, the two engines interleaved fit by fit
  (`../split/time_a3.py`): 695.9 s for 1.4.0, 694.7 s for the wheel, a
  ratio of 0.9983, within the 3 % of the criterion; the same first 160
  characters of the formula in all 205 jobs, which is what the records keep
  (`M1_A3.txt`, `M1_A3_timing.jsonl`). The import of `gp_elite`, beside:
  0.093 s and 0.102 s (median of 20).
- **A4:** `tests/test_door.py` against the installed wheel, from a copy of
  `tests/`: 69 passed (`M1_A4.txt`).

### M4, tests

`m4/summary.txt` gives the test suite run by `m4/run.sh` against the wheel
of the candidate, installed in a fresh environment for each of Python
3.9.25, 3.11.18 and 3.14.6 with the pins of the M4 of 1.4
(`m4/requirements_*.txt`), each importing the installed package, from
08:05 UTC on 24 November, after M1, to 08:15 (its last file was written at
08:15:48): 269 tests pass under each of the three (`m4/pytest_*.txt`).
`twine check --strict` passes for the wheel and the source archive
(`m4/twine_check.txt`).

## M5, two independent reviews

Both ran on HEAD 6950444, each by an agent that had seen neither the work
nor the other review, as since 0.9:
- the claims of the documents against the records (`M5_review1.md`): no
  figure stated is wrong when recomputed from its record, and the two
  languages agree; 27 findings, on sentences that claimed more than the
  records show, on statements about the code, and on claims without a
  committed record;
- the split itself (`M5_review2.md`): the engine's code is 1.4.0's after
  the rule of the shared state, the rule holds everywhere, and nothing at
  import changes; 13 findings, among them a fault of the door (a name
  deleted on `gp_elite.core` and set again no longer reached the engine),
  two lines whose meaning the move had changed, and annotations naming
  classes their module does not import.

The documents were corrected, and the code in f5fc346: the door, option 7
of the console, the initializer of the pool, the imports named in
annotations, and docstrings. 96ce1b6 adds `tests/test_layering.py`, which
checks the order of the modules. The files of `gp_elite/` changed, so the
wheel measured above is not the one to publish: the second candidate was
built and measured again, as the plan asks of the wheel built for the
release. The other changes the second review found are listed in the
CHANGELOG (1.5.0) and on the architecture pages.

## The second candidate (96ce1b6)

Commit 96ce1b6: the engine of the first candidate with the corrections of
f5fc346, and the test of the order of the modules. Its wheel and source
archive were built with `uv build` from a clean export (`candidate2/build.sh`,
24 November at 16:56 UTC). `candidate2/environments.txt` gives their
SHA-256, the SHA-256 of each of the 29 files of `gp_elite/` in the wheel,
each equal to the file of the commit, and the packages of `/venv15r2` (the
wheel alone, with the packages of `/venv14p`, Python 3.11.18). Of the 29
files, 17 differ from the first candidate: `core.py`, `state.py` and the 15
modules that read the shared state, whose docstrings changed.

### M1 and M4

Running at the time of this commit, as for the first candidate
(`candidate2/run_m1.sh`, `candidate2/M1.log`, then `candidate2/m4/run.sh`).

### The CI

The **Tests** workflow of the repository (Python 3.9 to 3.14 on Linux, 3.12
and 3.14 on Windows) runs on every push that changes more than documents:
it ignores the pushes that change only `*.md` files or `paper/`.
`ci_runs.txt` lists its runs on the branch, read after they ended. From
eb2eac5, the door that holds the names of the state as data descriptors, it
is green on every commit that has a run; from the push of Split 1 to the commit
before eb2eac5 it failed, as `../split/README.md` tells.

## Gate 14

To come: the author decides the publication, its name and its date.

## Files

- `run_m1.sh`, `M1.log`, `M1_A1.txt`, `M1_A3.txt`, `M1_A3_timing.jsonl`,
  `M1_A4.txt`, `environments.txt`, `m4/`: the first candidate.
- `candidate2/`: the same for the second candidate, and `build.sh`.
- `M5_review1.md`, `M5_review2.md`: what was done for each finding;
  `m5/review1_report.md`, `m5/review2_report.md` and their folders: the
  reports and the scripts of the reviews; `m5/after/`: the scripts of the
  second review run again on the corrected code.
- `machine.txt`: the machine and the Python of each environment.
- `ci_runs.txt`: the runs of the Tests workflow on the branch.
