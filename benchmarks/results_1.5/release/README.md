# Measurements of the release 1.5.0

What `../PLAN.md` asks before gate 14 ("The release of 1.5.0"), as it was
measured. The machine has 4 cores (an Intel Xeon). Every fit runs in its own
process with `PYTHONHASHSEED=0` and one BLAS thread.

## The release candidate

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

The machine restarted at about 06:52 UTC on 24 November, after the
measurements of `../split/` and before this candidate; nothing was running.

## M1, A1, A3 and A4 on the wheel (24 November 2026, 07:04 to 08:05 UTC)

`run_m1.sh`, one after the other (`M1.log`):
- **A1, in full:** the 13 reference configurations of
  `../../speed_equivalence.py`, F41, U41 and F41N1 with the defaults of the
  API (615 fits), the TP diagnostic (400 fits) and the console, compared
  with the run of 1.4.0 of the split (`/home/user/a1_140`) by
  `../split/compare_a1.py`: all identical, field by field (`M1_A1.txt`).
  The total time of the 13 configurations, 21.2 s for 1.4.0 and 27.0 s for
  the wheel, comes from runs some hours apart, the second just after the
  restart of the machine; it says nothing of the speed, which A3 measures.
- **A3, alone on the machine:** F41 with the defaults, 205 fits per engine,
  one at a time, the two engines interleaved fit by fit
  (`../split/time_a3.py`): 695.9 s for 1.4.0, 694.7 s for the wheel, a
  ratio of 0.9983, within the 3 % of the criterion; the same formula in all
  205 jobs (`M1_A3.txt`, `M1_A3_timing.jsonl`). The import of `gp_elite`,
  beside: 0.093 s and 0.102 s (median of 20).
- **A4:** `tests/test_door.py` against the installed wheel, from a copy of
  `tests/`: 69 passed (`M1_A4.txt`).

## M4, tests

`m4/summary.txt` gives the test suite run by `m4/run.sh` against the wheel
of the candidate, installed in a fresh environment for each of Python
3.9.25, 3.11.18 and 3.14.6 with the pins of the M4 of 1.4
(`m4/requirements_*.txt`), each importing the installed package
(`m4/pytest_*.txt`), and `twine check --strict` on the wheel and the source
archive (`m4/twine_check.txt`).

The **Tests** workflow of the repository (Python 3.9 to 3.14 on Linux, 3.12
and 3.14 on Windows) is green on every commit of the branch since eb2eac5,
the door that holds the names of the state as data descriptors; from the
first commit of the split to that one, it failed under pytest 9.2
(`../split/a2_local.txt`, and the README of `../split/`).

## M5, two independent reviews

To come: the claims of the documents against the records, and the split
itself (is any behaviour changed, does the rule of the shared state hold
everywhere).

## Gate 14

To come: the author decides the publication, its name and its date.
