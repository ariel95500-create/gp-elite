# Version 1.4.0: plan written before any measurement of the release

Written on 13 November 2026, after the adoption and the confirmation of N2b
(`PLAN.md`). The plan of 1.4 gives its release the steps of 1.3 (M1 to M5,
`../results_1.3/PLAN_RELEASE_1.3.md`), then gate 12: the author decides the
publication and the name. What is measured, and what would stop the release,
is written here before the first fit. Method as before:
- one process per fit, `PYTHONHASHSEED=0`, one BLAS thread;
- the frozen test sets decide nothing;
- times are compared only within one campaign on one machine;
- every deviation goes to the author.

## What 1.4.0 contains

Two changes since 1.3.0:
- **N2b,** in the noise-tolerant stage of the seeds (`gp_elite/core.py`,
  `_TOLERANT_N2`):
  - a second pass weighted by y², without the condition on the sign of the
    target;
  - scans of the finders of the sine, the cosine and the logarithm, of which
    the three best forms are kept, with the rule of the exponents of the
    logarithm found by the mechanics of N2;
  - the candidates deduplicated by their form, twelve seeds at most, and
    every seed that 1.3.0 places still placed;
  - each candidate keeps the constants of its finder.
- **W1:** the warning of a formula that departs from `predict()` names the
  clip of the arcsine. It changes no model.

The code of S1, of E2 and of the fit of the constants of N2 stays in the
engine, switched off (`_SMALL_CV`, `_E2_SEEDS` and `_TOLERANT_REFIT` False).
None of them is part of 1.4: their campaigns did not adopt them, S1 is
postponed to the next version, and E2 waits for the decision of the author.

Beside the package:
- the tests of these changes (`tests/test_guarantees.py`);
- the records and scripts of `benchmarks/results_1.4/`;
- the bench options `--noise-draws` and the kinds of TF78N of
  `phase1_bench.py`, and the set TPT10 of `tp_diagnostic.py` (`--set`);
- the new fields of the records of TP: `units_gate`, `additive_constant`
  and `small_cv`.

## The release candidate

One commit sets the version to 1.4.0 (`pyproject.toml`,
`gp_elite/__init__.py`, `CITATION.cff`) and opens the 1.4.0 section of the
CHANGELOG, its date and name left to gate 12. The wheel and the source
archive are built from a clean export of that commit, pass
`twine check --strict`, and are installed in fresh environments:
- `/venv14r`: the wheel alone, with the packages of `/venv13p` (Python
  3.11.18, NumPy 2.4.6, SciPy 1.17.1, scikit-learn 1.9.1);
- `/venv14rx`: the same, with the packages the scripts of M3 use, as
  `/venv13rx` in the release of 1.3.

The names `/venv14n2`, `/venv14e2` and `/venv14n2b` are those of the
candidates of the campaigns, and are not reused.

The comparison is 1.3.0 installed from PyPI (`/venv13p`). Its `gp_elite/`
files are checked identical to those of the wheel published, whose SHA-256 is
in `../results_1.3/release/environments.txt`.

Every measurement below is of the installed wheel, with its commit recorded.
A change of the engine after them starts them again; a change of the
documentation alone does not. The files handed over for PyPI are built again
from the last commit, and their `gp_elite/` files are checked identical to
the measured wheel's, file by file.

## Measurements

The machine runs one measurement step at a time.

**M1, equivalence.** The thirteen reference configurations of
`speed_equivalence.py`, with 1.3.0, with the candidate of N2b
(`/venv14n2b`) and with the release. Expected:
- the thirteen of the release identical to those of the candidate of N2b,
  whose engine is that of the release;
- against 1.3.0, the configurations where the noise-tolerant stage places
  other seeds may differ; they are reported, the others are identical.

**M2, campaign R, paired with 1.3.0.** Every job is started with both
versions at the same time, two jobs at a time, in slices under two hours
(the benches resume), from a copy of `benchmarks/` without the package
beside it. First, in one go, the two sets of TP (`tp_diagnostic.py
run-paired`):
- TP, the design set of 1.4: draws 0 to 4, two arms (400 fits);
- TPT10, the frozen set for teaching (400 fits).

Then the benches (`phase1_bench.py run-paired`), with the budget T of 30 s
per fit of the release of 1.3:
- the whole suite of phase 1 (F41, F41N1, F41N10, R6, R7raw, and the frozen
  test set TF78, TS14, TR25, TR25raw: 1,775 fits);
- U41, U41N1 and U41N10 (615);
- TF78 under units (390, seeds 5 to 9);
- TF78N, the frozen noisy test set (312).

That makes 3,892 fits per version, about fourteen hours. There are no real
tables of students: none could be gathered (gate 11).

Expected, and what would stop the release:
- **Where 1.4 does not act:** N2b changes only the noise-tolerant seeds, and
  W1 no model. The release stops if, on a fit of the benches where neither
  version reached its time budget and both placed the same noise-tolerant
  seeds (the recorded `tolerant_seed`, none included), the recorded formula,
  the error on the test rows or `formula_exact` differs by a bit.
- **TP:** its fits do not depend on time, so its 400 models are expected to
  be those of B in campaign N2b; a difference is examined. The release stops
  if, against 1.3.0:
  - the law comes back in more than 5 fewer fits in either arm;
  - a model of the units arm fails its gate of dimensions (`units_gate`);
  - the median time of a fit is more than 1.5 times 1.3.0's in either arm.
- **Without units,** the release stops if, against 1.3.0:
  - F41 has more than 3 fewer exact laws, or an equation exact at three
    seeds or more falls to one or none;
  - F41N1 or F41N10 has more than 3 fewer structures;
  - F41N1 and F41N10 together have fewer than 15 structures more, the gain
    for which N2b was adopted;
  - the median test R² of the R6 folds is more than 0.005 lower;
  - R6 and R7raw have more than 2 more collapses out of domain.
- **Under units,** the release stops if:
  - U41 has more than 3 fewer exact laws than 1.3.0, or an equation exact at
    three seeds or more falls to one or none;
  - U41N1 or U41N10 has more than 3 fewer structures than 1.3.0;
  - a model returned under units fails the audit `check_dimensions`.

The comparison and these criteria are a script committed before the records
are read. Reported beside:
- the fits that change status, by suite;
- the noise-tolerant seeds placed, by suite and version;
- how often `formula_exact` is False, by version and suite;
- on TP, the law by experiment, the point source among them (18 → 14 in
  campaign N2b).

A difference beyond these is examined before gate 12. The frozen test sets
are published as measured and decide nothing:
- TF78, TS14 and TR25 without units, and TF78 under units;
- TF78N, without units and under units;
- TPT10, by experiment and arm.

**M3, every public figure measured again.** The steps of the M3 of 1.3
(`../results_1.3/release/m3/m3_driver.sh`), one after the other, on a copy
of `benchmarks/`, `examples/` and the READMEs without the package beside
them, with `/venv14rx`:
- `benchmarks/release_claims/run_claims.py`, with the examples of the
  READMEs and the snippets of the notebooks;
- `case_studies.py kepler`, `hubble` and `nikuradse`;
- the deduced constant, with 1.3.0 beside it;
- the TP notebook (`examples/tp_six_lois.ipynb`), run as the script of its
  code cells, and four times more, 1.3.0 and 1.4.0 in turn, to compare its
  times on one day;
- the figures of the pages of the limits, read from the records of M2.

Each record is compared with the M3 of 1.3 (`../results_1.3/release/
m3_compare.py`). Expected to change: the figures on noisy data where the
noise-tolerant stage places other seeds (the TP notebook among them), and
every figure that counts the structures under noise. Expected unchanged,
within the noise of time budgets: the figures on exact data, among them
Feynman 15, the duel with gplearn and the mystery constant. A figure that
changes is published as measured, with the reason.

**M4, tests.** As for 1.3:
- the test suite against the wheel in fresh environments under Python 3.9,
  3.11 and 3.14, the versions installed recorded;
- `twine check --strict` on both files;
- the **Tests** workflow green on the commit of the release.

**M5, two independent reviews**, one after the other, by a second agent each
time who has not seen the work. They cover:
- every figure of the two READMEs;
- the 1.4.0 entry of the CHANGELOG;
- the notebooks and case studies;
- the pages of the limits and the paper.

Every finding is corrected or answered in writing before gate 12.

## Documents

Brought up to date from M2 and M3 before M5:
- **`README.md` and `README.fr.md`:** what's new, N2b; the counts of
  structures under noise.
- **`LIMITATIONS.md` and `LIMITATIONS.fr.md`:**
  - point 3, noise: the counts of M2, and what the campaigns of 1.4 found on
    small noisy tables: on 10 or 20 noisy points, a seed with the structure
    of the law does not make the search keep it (the point source of TP
    falls from 18 fits of 20 to 14);
  - point 10, the stop under the defaults, if M2 or M3 moves its figures;
  - what stays out of 1.4: S1, E2 and the fit of the constants of N2, each
    with the cause its campaign found;
  - every result on teaching comes from simulated tables (the amendment of
    TF78N).
- **The CHANGELOG:** N2b and W1, and the code switched off.
- **The TP notebooks,** where their figures move.
- **`../results_1.1/DIAGNOSTIC_TP.md`,** left as written, with a note on
  what 1.4 changes on TP.
- **The paper,** wherever its figures move.

## Gate 12

The author receives:
- the measured figures;
- the differences with 1.3.0;
- the reviews;
- one consequence outside the benches: the SRBench wrapper runs noisy
  targets, so once 1.4.0 is on PyPI, those runs have N2b.

He decides the publication and the name of the version. Delivery as for
1.3:
1. a pull request to `main`, which the author merges with "Create a merge
   commit";
2. the author publishes on PyPI and creates the release v1.4.0 on GitHub,
   with written instructions.

Claude never publishes on PyPI and never handles its credentials.
