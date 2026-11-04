# Version 1.2.0: plan written before any measurement of the release

Written on 4 November 2026, after the adoption of H1, the check of X1 on TP
and the withdrawal of C1 (`PLAN.md`). The plan of 1.2 gives its release the
steps of 1.1 (M1 to M5, `../results_1.1/PLAN_RELEASE_1.1.md`), then gate 8:
the author decides the publication and the name. What is measured, and what
would stop the release, is written here before the first fit. Method as
before:
- one process per fit, `PYTHONHASHSEED=0`;
- the frozen test set decides nothing;
- times are compared only within one campaign on one machine;
- every deviation goes to the author.

## What 1.2.0 contains

Three changes of the engine since 1.1.0 (commit 346cd07):
- **The typed start under units** (D0, commit 9a794a3). Its fast path
  accepts products of up to 12 factors (8 before), and it looks at the
  deadline of `time_limit=`. III.19.51 under units ends in about a second,
  where 1.1.0 takes from 430 to 735 s with `time_limit=30`.
- **H1** (commit 212d1dc). When the call sets neither `generations` nor
  `time_limit`, the search stops once the error on the hold-out rows has not
  improved by 1 % in 30 generations; `patience=` sets that number. With a
  budget set, nothing changes.
- **X1** (commit a263177). The printed formula writes a power of a number as
  an exponential, and an exponential of one variable with its scale
  (`exp(-t / τ)`), only when the rewritten formula passes the check against
  `predict()`. The model, `predict()` and `formula_exact` do not change.

C1 is not in 1.2 (`PLAN.md`, decided by the author on 4 November 2026).

Beside the package: the tests of these changes, the records and scripts of
`benchmarks/results_1.2/`, and the option `defaults` of
`benchmarks/phase1_bench.py`.

## The release candidate

One commit sets the version to 1.2.0 (`pyproject.toml`,
`gp_elite/__init__.py`, `CITATION.cff`) and opens the 1.2.0 section of the
CHANGELOG, its date and name left to gate 8. The wheel and the source archive
are built from a clean export of that commit (`python -m build`), pass
`twine check --strict`, and are installed in fresh environments:
- `/venv12b`: the wheel alone, with the packages of `/venv11p` (Python
  3.11.18, NumPy 2.4.6, SciPy 1.17.1, scikit-learn 1.9.1);
- `/venv12bx`: the same, with the packages the scripts of M3 use, as
  `/venv11bx` in the release of 1.1.

The comparison is 1.1.0 installed from PyPI (`/venv11p`). Its `gp_elite/`
files are checked identical to those of commit 346cd07, from which the
published files were built.

Every measurement below is of the installed wheel, with its commit recorded.
A change of the engine after them starts them again; a change of the
documentation alone does not. The files handed over for PyPI are built again
from the last commit, and their `gp_elite/` files are checked identical to
the measured wheel's, file by file.

## Measurements

The machine runs one measurement step at a time.

**M1, equivalence.** The thirteen reference configurations of
`speed_equivalence.py` all set their budget, so H1 does not act; the typed
start changes only products of 9 to 12 factors and a deadline reached during
it; X1 changes only the printed formula. Expected: identical to 1.1.0
(`/venv11p`), as with the engine of X1 during the mechanics of C1
(`c1/compare_1.1.0_vs_equiv_default.txt`).

**M2, campaign R, paired with 1.1.0.** Run by `phase1_bench.py run-paired`,
each job started with both versions at the same time, two jobs at a time, in
slices under two hours (the bench resumes), with the suites and the budget T
of 30 s per fit of the release of 1.1:
- the whole suite of phase 1 (F41, F41N1, F41N10, R6, R7raw, and the frozen
  test set TF78, TS14, TR25, TR25raw: 1,775 fits);
- U41, U41N1 and U41N10 (615);
- TF78 under units (390, seeds 5 to 9).

That makes 2,780 fits per version, about twelve hours.

Before M2, the bench records for every fit of 1.2.0 the formula with X1
switched off (`expr_11`, and its `formula_exact_11`). It is computed after
the timed fit, from the model returned and the arguments of the engine's own
call of its formula, so the fit and its time are not touched. Where X1 is
absent (1.1.0) the bench runs as before. Checked on three jobs with both
versions before M2: the records of 1.1.0 have the fields they had, and with
X1 switched on again the computation gives back the expression returned.

Expected, and what would stop the release:
- **Without units**, the three changes leave the model alone when a budget is
  set, so the two versions return the same model at equal work; under a time
  budget, timing alone moves a few fits, as in the release of 1.1 (47 of
  1,775). The release stops if, against 1.1.0:
  - F41 has more than 3 fewer exact laws;
  - F41N1 or F41N10 has more than 3 fewer structures;
  - the median test R² of the R6 folds is more than 0.005 lower;
  - R6 and R7raw have more than 2 more collapses out of domain.
- **Under units**, the typed start changes the fits whose product needs 9 to
  12 factors and those that reach their deadline during it. The release
  stops if:
  - U41 has more than 3 fewer exact laws than 1.1.0;
  - U41N1 or U41N10 has more than 3 fewer structures than 1.1.0;
  - any model returned under units fails the audit `check_dimensions`;
  - a fit of III.19.51 under units (U41, U41N1, U41N10, 15 fits) takes more
    than 60 s.
- **X1**, the check `PLAN.md` gives to M2. The release stops if, on a fit of
  1.2.0:
  - `formula_exact` differs from `formula_exact_11`;
  - the formula without X1 is the expression of 1.1.0 and the error on the
    test rows or `formula_exact` differs from 1.1.0 by a bit.

  The fits whose formula without X1 is not that of 1.1.0 are reported by
  suite, with whether they reached the time budget; so are the fits where X1
  rewrites the formula.

A difference beyond these is examined before gate 8. The frozen test set
(TF78, TS14 and TR25 without units, TF78 under units) is published as
measured and decides nothing.

**M3, every public figure measured again.** As for 1.1, on a copy of
`benchmarks/` and `examples/` without the package beside them:
- `benchmarks/release_claims/run_claims.py`;
- `case_studies.py kepler`, `hubble` and `nikuradse`;
- the TP notebook (`examples/tp_six_lois.ipynb`), run as a script;
- the figures of the pages of the limits, read from the records of M2.

Expected to change:
- the times and formulas of the TP notebook (H1 and X1);
- any figure measured under the API defaults (H1);
- the printed formulas that hold a power of a number (X1);
- the figures of III.19.51 under units.

Every other figure is expected unchanged within the noise of time budgets. A
figure that changes is published as measured, with the reason.

**M4, tests.** The test suite against the wheel in fresh environments under
Python 3.9, 3.11 and 3.14 (the versions installed are recorded), `twine check
--strict` on both files, and the **Tests** workflow green on the commit of
the release.

**M5, two independent reviews**, one after the other, by a second agent each
time who has not seen the work. They cover:
- every figure of the two READMEs;
- the 1.2.0 entry of the CHANGELOG;
- the notebooks and case studies;
- the pages of the limits and the paper.

Every finding is corrected or answered in writing before gate 8.

## Documents

Brought up to date from M2 and M3 before M5:
- `README.md` and `README.fr.md`: what's new (the time of a fit under the
  defaults and `patience=`, the exponential written as such, the typed start
  under units);
- `LIMITATIONS.md` and `LIMITATIONS.fr.md`: wherever they give the time of a
  fit or the units mode; on the three laws limited under units they keep
  their text of 1.1;
- the CHANGELOG;
- the paper, wherever it describes the time of a fit, the printed formula or
  the units mode;
- the TP notebook, whose text quotes its own run;
- `../results_1.1/DIAGNOSTIC_TP.md`, left as written, with a note on what
  1.2 changes.

## Gate 8

The author receives:
- the measured figures;
- the differences with 1.1.0;
- the reviews.

He decides the publication and the name of the version. Delivery as for
1.1:
1. a pull request to `main`, which the author merges with "Create a merge
   commit";
2. the author publishes on PyPI and creates the release v1.2.0 on GitHub,
   with written instructions.

Claude never publishes on PyPI and never handles its credentials.
