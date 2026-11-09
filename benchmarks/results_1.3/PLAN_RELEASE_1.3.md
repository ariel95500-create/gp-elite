# Version 1.3.0: plan written before any measurement of the release

Written on 9 November 2026, after the adoption and the confirmation of A3
(`PLAN.md`). The plan of 1.3 gives its release the steps of 1.2 (M1 to M5,
`../results_1.2/PLAN_RELEASE_1.2.md`), then gate 10: the author decides the
publication and the name. What is measured, and what would stop the release,
is written here before the first fit. Method as before:
- one process per fit, `PYTHONHASHSEED=0`;
- the frozen test set decides nothing;
- times are compared only within one campaign on one machine;
- every deviation goes to the author.

## What 1.3.0 contains

One change of the engine since 1.2.0, in three parts, commit 492863e:
- **A1:** an operator `arcsin`, the arcsine of its argument clipped to
  [−1, 1], in the pools `trig` and `full`, with weight 2. The pools
  `physical` (the default), `poly` and `conserve` are left as they are.
- **A2:** the simplifier writes the argument of each arcsine with a constant
  factor of its own, arcsin(u) → arcsin(1 · u), which the fit of constants
  adjusts.
- **A3:** the seeds of phase 4a gain the form y = b·f·arcsin(c·g), f and g
  monomials, only where the pool has the arcsine.

Beside the package:
- the tests of these changes (`tests/test_arcsin.py`);
- the records and scripts of `benchmarks/results_1.3/`;
- the bench options `--problems` of `phase1_bench.py` and `--experiments`
  of `tp_diagnostic.py`;
- the new fields of their records: the seeds placed, and the check of
  dimensions on the units arm of TP.

## The release candidate

One commit sets the version to 1.3.0 (`pyproject.toml`,
`gp_elite/__init__.py`, `CITATION.cff`) and opens the 1.3.0 section of the
CHANGELOG, its date and name left to gate 10. The wheel and the source
archive are built from a clean export of that commit (`python -m build`),
pass `twine check --strict`, and are installed in fresh environments:
- `/venv13r`: the wheel alone, with the packages of `/venv12p` (Python
  3.11.18, NumPy 2.4.6, SciPy 1.17.1, scikit-learn 1.9.1);
- `/venv13rx`: the same, with the packages the scripts of M3 use, as
  `/venv12bx` in the release of 1.2.

The names `/venv13a`, `/venv13b` and `/venv13c` are those of the
candidates of A1, A2 and A3, and are not reused.

The comparison is 1.2.0 installed from PyPI (`/venv12p`). Its `gp_elite/`
files are checked identical to those of the wheel published, whose SHA-256 is
in `../results_1.2/release/environments.txt`.

Every measurement below is of the installed wheel, with its commit recorded.
A change of the engine after them starts them again; a change of the
documentation alone does not. The files handed over for PyPI are built again
from the last commit, and their `gp_elite/` files are checked identical to
the measured wheel's, file by file.

## Measurements

The machine runs one measurement step at a time.

**M1, equivalence.** The thirteen reference configurations of
`speed_equivalence.py`. Expected, as in the mechanics of A1, A2 and A3:
- the eleven of the pool `physical` identical to 1.2.0;
- E_minmax (`full`) and L_standard (`trig`) different from 1.2.0, and
  identical to the candidate of A3 (`a3/equiv_a3/`), whose engine is that of
  the release.

**M2, campaign R, paired with 1.2.0.** Run by `phase1_bench.py run-paired`,
each job started with both versions at the same time, two jobs at a time, in
slices under two hours (the bench resumes). The suites and the budget T of
30 s per fit are those of the release of 1.2:
- the whole suite of phase 1 (F41, F41N1, F41N10, R6, R7raw, and the frozen
  test set TF78, TS14, TR25, TR25raw: 1,775 fits);
- U41, U41N1 and U41N10 (615);
- TF78 under units (390, seeds 5 to 9).

That makes 2,780 fits per version, about twelve hours.

Expected, and what would stop the release:
- **The pool `physical`:** the change does not reach it, so the two versions
  return the same model at equal work. Under a time budget, timing alone
  moves a few fits, as in the releases of 1.1 and 1.2. The release stops if,
  on a fit of the pool `physical` where neither version reached its time
  budget, the formula, the error on the test rows or `formula_exact`
  differs by a bit.
- **Without units,** the release stops if, against 1.2.0:
  - F41 has more than 3 fewer exact laws;
  - F41N1 or F41N10 has more than 3 fewer structures;
  - the median test R² of the R6 folds is more than 0.005 lower;
  - R6 and R7raw have more than 2 more collapses out of domain;
  - the two arcsine laws of F41 are exact with the arcsine in fewer than 5
    of their 10 fits, the criterion of A3.
- **Under units,** the release stops if:
  - U41 has more than 3 fewer exact laws than 1.2.0;
  - U41N1 or U41N10 has more than 3 fewer structures than 1.2.0;
  - any model returned under units fails the audit `check_dimensions`.

Reported:
- the fits of the pool `trig` that change status, by suite;
- the formulas with the arcsine;
- how often `formula_exact` is False, by version and suite.

A difference beyond these is examined before gate 10. The frozen test set is
published as measured and decides nothing:
- TF78, TS14 and TR25 without units, and TF78 under units;
- among them, the 17 equations of TF78 of the pool `trig`, and its one
  arccosine law, feynman_test_10.

**M3, every public figure measured again.** As for 1.2, on a copy of
`benchmarks/` and `examples/` without the package beside them:
- `benchmarks/release_claims/run_claims.py`;
- `case_studies.py kepler`, `hubble` and `nikuradse`;
- the TP notebook (`examples/tp_six_lois.ipynb`), run as a script;
- the figures of the pages of the limits, read from the records of M2.

Expected to change: every figure that counts the exact laws or structures
of F41, U41 or the frozen test set, and every figure of the ten equations of
the pool `trig`. Expected unchanged, within the noise of time budgets:
- the TP notebook and the case studies, which use the pool `physical`;
- every figure of the pool `physical`.

A figure that changes is published as measured, with the reason.

**M4, tests.** As for 1.2:
- the test suite against the wheel in fresh environments under Python 3.9,
  3.11 and 3.14, the versions installed recorded;
- `twine check --strict` on both files;
- the **Tests** workflow green on the commit of the release.

**M5, two independent reviews**, one after the other, by a second agent each
time who has not seen the work. They cover:
- every figure of the two READMEs;
- the 1.3.0 entry of the CHANGELOG;
- the notebooks and case studies;
- the pages of the limits and the paper.

Every finding is corrected or answered in writing before gate 10.

## Documents

Brought up to date from M2 and M3 before M5:
- **`README.md` and `README.fr.md`:**
  - what's new, the arcsine;
  - the operators of `trig` and `full`;
  - the counts of exact laws and structures.
- **`LIMITATIONS.md` and `LIMITATIONS.fr.md`:**
  - point 1, where the arcsine laws leave the list of the equations never
    recovered, if M2 says so;
  - what the arcsine does not reach: Snell's law on a few noisy points, and
    an arcsine whose argument is neither a monomial nor found by the search;
  - the printed formula, which departs from the model more often where the
    clip of the arcsine acts.
- **The CHANGELOG.**
- **The paper,** wherever its figures move.
- **`../results_1.1/DIAGNOSTIC_TP.md`,** left as written, with a note: the
  arcsine does not bring Snell's law back on the TP, where the noise hides it
  (`a1/examine/README.md`).

## Gate 10

The author receives:
- the measured figures;
- the differences with 1.2.0;
- the reviews;
- one consequence outside the benches: the SRBench wrapper tries
  `operators="full"`, so once 1.3.0 is on PyPI, those runs have the arcsine.

He decides the publication and the name of the version. Delivery as for
1.2:
1. a pull request to `main`, which the author merges with "Create a merge
   commit";
2. the author publishes on PyPI and creates the release v1.3.0 on GitHub,
   with written instructions.

Claude never publishes on PyPI and never handles its credentials.
