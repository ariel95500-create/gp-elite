# Version 0.9.0 — plan written before any measurement of the release

Written on 11 October 2026, when the author chose to prepare 0.9 after
phase 3. The plan of 0.9 / 1.0 gives the version four steps: campaign R on
the version, the frozen test set measured once, every public figure measured
again, two independent reviews, and the tests of the package under Python
3.9 to 3.14. Then gate 3: the author decides the publication. Method as in
the phases: what is measured, and what would stop the release, is written
here before the first fit.

## What 0.9.0 contains

Changes of the engine and of its interface since 0.8.0, each measured in its
phase:

1. When the formula of the returned model departs from `predict()`, the
   warning names the exact formulas of the Pareto front (phase 2,
   `PLAN_PHASE2.md`). No model changes.
2. The search with `units=` is more than five times faster, with the same
   models bit for bit (phase 3, `PLAN_PHASE3.md`).

Documentation: the reproducibility from one machine to another (pull request
#2), the test of delivered formulas made robust (#2), the date of
`CITATION.cff` (#3), the advice `normalize='none'` for an angle inside a sine
or a cosine (`PLAN_TRIG.md`), and the warning above. The benches and records
of phases 1 to 4 (`benchmarks/`, `benchmarks/results_0.9/`) are in the
repository, not in the package.

Not in 0.9.0: no change of the search. The changes tried in phases 2 and 4
(F1, F3R, G1, G1b, S1, S2, T1, A1) were not adopted and are not in the code.

## The release candidate

One commit sets the version to 0.9.0 (`pyproject.toml`,
`gp_elite/__init__.py`, `CITATION.cff`) and opens the 0.9.0 section of the
CHANGELOG, its date left to the day of publication. The wheel and the source
archive are built from that commit and the wheel is installed in a fresh
environment with the versions of phase 1 (Python 3.11.15, NumPy 2.4.6,
scikit-learn 1.9.1). Every measurement below is of that installed wheel, its
commit recorded. A change of the engine after them starts them again; a
change of the documentation alone does not.

## Measurements

**M1, equivalence.** The thirteen reference configurations of
`benchmarks/speed_equivalence.py` return with the wheel the same models as
0.8.0, and the typed fits of II.11.3 (seeds 0 to 9, `phase3_bench.py`) the
same models as U0. Expected: identical, both changes being proven so.

**M2, campaign R, paired with 0.8.0.** The whole suite of phase 1 (F41, F41
with 1 % and 10 % noise, R6, R7raw, TF78, TS14, TR25, TR25raw: 1,775 fits
per engine, budget T of 30 s per fit), run by `phase1_bench.py` for the
wheel and for gp-elite 0.8.0 installed from PyPI, the two engines on the
same job at the same time, four fits at a time (two jobs). Why 0.8.0 again:
the container was replaced on 11 October, the phase 1 figures come from
another processor, and a figure under a time budget depends on the machine;
side by side, the two versions are compared under the same load. About nine
hours of machine; the bench resumes after an interruption.

Expectation: the same counts within the noise of time budgets. Without
`units=` the two versions return the same model at equal work (M1), so a
difference can come only from where the deadline falls. Phase 1 found again
on another machine exactly the 88 exact laws of campaign R of 0.8.

**M3, every public figure measured again.** Every figure of the README, of
`README.fr.md` and of the notebooks, with the commands listed in
`benchmarks/results_0.8/README.md`, on the wheel, into
`benchmarks/results_0.9/release/`. The table of `units=` (Feynman II.11.3,
`ab_ood.py`, five seeds, 40 generations) is measured with `parallel=False`,
the setting of the 0.8 figures (a 2-core container ran the islands in
sequence) and of phase 3, and the README says so. A figure that changes is
published as measured, with the reason.

**M4, tests.** The test suite on the wheel under Python 3.11 here, and the
**Tests** workflow of the repository (Linux, Python 3.9 to 3.14; Windows,
3.12 and 3.14) green on the commit of the release.

**M5, two independent reviews.** Two reviewers (a second agent each time,
who has not seen the work) check every figure of the README, of the
CHANGELOG and of the notebooks against the result files, one after the
other. Every finding is corrected or answered in writing before gate 3.

## What would stop the release

- M1: any model that differs. The release is then refused and the cause
  found, as for any speed-up.
- M2, against 0.8.0 on this machine: F41 more than 6 exact laws below (the
  spread seen between equivalent engines in 0.8); a median test R² of R6 or
  of the TR25 folds more than 0.005 below; more collapses out of domain on R6
  and R7raw than 0.8.0 plus 2. A difference beyond these is examined before
  gate 3, and reported whatever its cause. The frozen test set is published
  as measured; it decides nothing.
- M3: a public figure that no record of the wheel supports.
- M4: a failing test.
- M5: a finding left without an answer.

## Gate 3

The author receives the measured figures, the differences with 0.8.0 and the
reviews, and decides the publication. Delivery as for 0.8.0, after pull
request #4 is merged: the work of phases 2 to 4 and the release commit go to
the working branch, a pull request to `main` that the author merges with
"Create a merge commit", then the author publishes on PyPI and creates the
release v0.9.0 on GitHub, with written instructions. Claude never publishes
on PyPI and never handles its credentials.
