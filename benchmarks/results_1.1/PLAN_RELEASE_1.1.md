# Version 1.1.0 — plan written before any measurement of the release

Written on 27 October 2026, after the adoption of U1 (`PLAN.md`). The plan
of 1.1 gives its release the steps of 1.0.0 (M1 to M5), with the frozen test
set measured under units as well. Then gate 6: the author decides the
publication and the name. What is measured, and what would stop the
release, is written here before the first fit. Method as before:
- one process per fit, `PYTHONHASHSEED=0`;
- the frozen test set decides nothing;
- every deviation goes to the author.

1.1.0 is published after 1.0.0 is on PyPI, never before.

## What 1.1.0 contains

One change of the engine since 1.0.0: **U1**. Under `units=`, the seed
finders of 1.0 (power law, B1, E1, N1) run as without units. A seed is
placed only if it passes the gate of dimensions every typed tree passes
(`PLAN.md`, adopted on 26 October 2026, confirmed on 27 October). Without
units, nothing changes.

Beside the package:
- the French notebook `examples/tp_six_lois.ipynb`;
- the diagnostic of the lab sessions (`DIAGNOSTIC_TP.md`);
- the tables of units (`benchmarks/units_table.py`) and the units kinds of
  the bench;
- the workflow **Tests**, whose Python 3.9 job runs on Ubuntu 24.04 since
  ubuntu-latest no longer offers it.

## The release candidate

One commit sets the version to 1.1.0 (`pyproject.toml`,
`gp_elite/__init__.py`, `CITATION.cff`) and opens the 1.1.0 section of the
CHANGELOG, its date left to the day of publication. The wheel and the source
archive are built from that commit and installed in fresh environments:
- `/venv11`: the wheel alone, with the versions of the 1.0.0 measurements
  (Python 3.11.15, NumPy 2.4.6, scikit-learn 1.9.1);
- `/venv11x`: the same, with the packages some scripts of M3 use.

The comparison is 1.0.0 from its measured wheel (`/venv10`). If 1.0.0 is on
PyPI before M2 starts, it is installed from PyPI in a fresh environment
instead, and its `gp_elite/` files are checked identical to the measured
wheel's.

Every measurement below is of the installed wheel, with its commit recorded.
A change of the engine after them starts them again; a change of the
documentation alone does not. The files handed over for PyPI are built again
from the last commit, and their `gp_elite/` files are checked identical to
the measured wheel's, file by file.

## Measurements

The machine runs one measurement step at a time.

**M1, equivalence.** The thirteen reference configurations of
`speed_equivalence.py` return with the wheel the models of the adopted
engine (`mechanics/equiv_U1_default`). The twelve without units are
therefore those of 1.0.0. Expected: identical.

**M2, campaign R, paired with 1.0.0.** Run by `phase1_bench.py run-paired`,
two jobs at a time, in slices under two hours (the bench resumes):
- the whole suite of phase 1 (F41, F41N1, F41N10, R6, R7raw, TF78, TS14,
  TR25, TR25raw: 1,775 fits per version);
- U41, U41N1 and U41N10 (615);
- **TF78 under units** (390, kind `utf`, seeds 5 to 9, units from
  `units_table.UNITS_TF78`), added to the bench before M2 and checked to
  leave the other job lists unchanged.

That makes 2,780 fits per version at 30 s each, about twelve hours.

Expected, and what would stop the release:
- **Without units**, U1 does not act, so the two versions return the same
  model at equal work; under a time budget, timing alone moves a few fits,
  as between 0.8.0 and 0.9.0 (29 of 1,775). The release stops if, against
  1.0.0:
  - F41 has more than 3 fewer exact laws;
  - F41N1 or F41N10 has more than 3 fewer structures;
  - the median test R² of the R6 folds is more than 0.005 lower;
  - R6 and R7raw have more than 2 more collapses out of domain.

  A difference beyond these is examined before gate 6.
- **Under units**, as in the campaign. The release stops if:
  - U41 has fewer than 10 more exact laws than 1.0.0;
  - any model returned under units fails the audit `check_dimensions`.
- **The frozen test set**, TF78, TS14 and TR25 without units and TF78 under
  units, is published as measured and decides nothing.

**M3, every public figure measured again.** As for 1.0.0, on a copy of
`benchmarks/` and `examples/` without the package beside them:
- `benchmarks/release_claims/run_claims.py`;
- `case_studies.py kepler`, `hubble` and `nikuradse`;
- the TP notebook, run as a script;
- the figures of the pages of the limits, read from the records of M2.

Figures of the units mode are expected to change:
- the table of `units=` on II.11.3;
- point 8 of the limits;
- the typed fits of the Kepler and Hubble studies;
- the times of the TP notebook.

Every figure without units is expected unchanged within the noise of time
budgets. A figure that changes is published as measured, with the reason.

**M4, tests.** The test suite against the wheel in fresh environments under
Python 3.9.23, 3.11.15 and 3.14.0rc2, `twine check --strict` on both files,
and the **Tests** workflow green on the commit of the release.

**M5, two independent reviews**, one after the other, by a second agent
each time who has not seen the work. They cover:
- every figure of the two READMEs;
- the 1.1.0 entry of the CHANGELOG;
- the notebooks and case studies;
- the pages of the limits and the paper.

Every finding is corrected or answered in writing before gate 6.

## Documents

Brought up to date from M2 and M3 before M5:
- `README.md` and `README.fr.md`: what's new, the units table;
- `LIMITATIONS.md` and `LIMITATIONS.fr.md`: point 8;
- the CHANGELOG;
- the paper, wherever it describes the units mode;
- the case studies with units;
- the TP notebook, whose text quotes its own run.

## Gate 6

The author receives:
- the measured figures;
- the differences with 1.0.0;
- the reviews.

He decides the publication and the name of the version. Delivery as for
1.0.0, after 1.0.0 is on PyPI:
1. a pull request to `main`, which the author merges with "Create a merge
   commit";
2. the author publishes on PyPI and creates the release v1.1.0 on GitHub,
   with written instructions.

Claude never publishes on PyPI and never handles its credentials.

After gate 6, the plan of a version for teaching (1.2) is written from the
list of `DIAGNOSTIC_TP.md`, as the author decided on 26 October.
