# Version 1.0.0 — plan written before any measurement of the release

Written on 13 October 2026, when the author approved preparing 1.0 after the
case studies of phase 6. The plan of 0.9 / 1.0 gives 1.0 the steps of 0.9.0
(campaign R on the version, the frozen test set measured once, every public
figure measured again, two independent reviews, the tests of the package
under Python 3.9 to 3.14), then the JOSS submission and the announcement to
SRBench; phase 6 adds the paper brought up to date and the launch. Then gate
4: the author decides the publication. As in every phase, what is measured,
and what would stop the release, is written here before the first fit.

## What 1.0.0 contains

Changes of the engine and of its interface since 0.9.0, each measured in its
phase:

1. B1: laws that are a monomial times a power of a binomial are fitted
   directly and seed the search (phase 4b, `PLAN_PHASE4.md`).
2. E1: the same method for a function (exp, log, tanh, sech, sine and cosine)
   of a monomial (phase 4a, `PLAN_PHASE4.md`).
3. N1: when no form holds exactly, the forms of the power law, B1 and E1 are
   sought again with their thresholds lifted, and placed if they leave at
   most 1.5 % of the variance unexplained (phase 5, `PLAN_PHASE5.md`).
4. With `unknown_constant=True`, the deduced constant is read on the
   predictions when the model is a monomial, so that it is always the
   coefficient of the returned law (found with the Kepler case study, commit
   `a354dea`, test 24).
5. The warning printed when parallel islands cannot start no longer says the
   results are identical (decided by the author at gate 3).

Documentation: the pages of the limits (`LIMITATIONS.md`,
`LIMITATIONS.fr.md`), step 4 of the French notebook, the three case studies
in English and French (`examples/case_studies/`), the CHANGELOG. The records
of phases 4 to 6 are in the repository, not in the package.

Not in 1.0.0: the change 4c, set aside by the author, and nothing that was
measured and not adopted.

## The release candidate

One commit sets the version to 1.0.0 (`pyproject.toml`,
`gp_elite/__init__.py`, `CITATION.cff`) and turns the "Unreleased" section of
the CHANGELOG into 1.0.0, its date left to the day of publication. The wheel
and the source archive are built from that commit; the wheel is installed in
a fresh environment `/venv10` with the versions of the 0.9.0 measurements
(Python 3.11.15, NumPy 2.4.6, scikit-learn 1.9.1), and in `/venv10x` with the
packages some scripts of M3 use (as `/venv09x`). gp-elite 0.9.0 is installed
from PyPI in a fresh environment `/venv09p`; its wheel's SHA-256 is compared
with the one measured for 0.9.0 (`release/environments.txt`). Every
measurement below is of the installed wheel, its commit recorded. A change of
the engine after them starts them again; a change of the documentation alone
does not. The files handed over for PyPI are built again from the last
commit, after the documentation; their `gp_elite/` files are checked
identical, file by file, to those of the measured wheel.

## Measurements

The machine runs one measurement step at a time: M2 and M3 hold figures
under time budgets or timed, and nothing else runs beside them.

**M1, equivalence.** The thirteen reference configurations of
`benchmarks/speed_equivalence.py` return with the wheel the same models as
the engine adopted in phase 5 (`phase5/mechanics/B1_E1_N1_default`); the
typed fits of Feynman II.11.3, seeds 0 to 9 (`benchmarks/phase3_bench.py`),
return the same models as 0.9.0 (`release/M1_ii113_0.9.0.jsonl`), since none
of B1, E1 and N1 acts under `units=`. Expected: identical.

**M2, campaign R, paired with 0.9.0.** The whole suite of phase 1 (F41, F41
with 1 % and 10 % noise, R6, R7raw, and the frozen test set TF78, TS14, TR25,
TR25raw: 1,775 fits per version, budget T of 30 s per fit), run by
`phase1_bench.py run-paired` for the wheel and for 0.9.0 from PyPI, each job
started with both versions at the same time, two jobs at a time, in slices
of 6,600 s (the bench resumes). About seven hours. The frozen test set is
measured here, once for this version.

Expectations, written before: on F41 the counts of the campaigns of phases 4
and 5 (160 exact laws of 205 on the branch; 0.9.0 86 on this kind of
machine), on F41N1 and F41N10 those of phase 5 (106 and 86 structures), the
real data unchanged within the noise of time budgets (the changes placed no
seed on the 520 real fits of phase 5).

**M3, every public figure measured again.** Every figure of `README.md`,
`README.fr.md`, the notebooks (quickstart in English and French, the TP
notebook), the case studies, `LIMITATIONS.md` and `LIMITATIONS.fr.md`, and
`paper/paper.md`:

- with `benchmarks/release_claims/run_claims.py`, the commands of 0.9.0, on
  a copy of `benchmarks/` and `examples/` without the package beside them;
- `benchmarks/case_studies.py kepler`, `hubble` and `nikuradse`, on that
  copy;
- the check of Kepler's law normalised by min-max
  (`phase5/mechanics/kepler_minmax_check.py`), seeds 0 to 9, 10 and 40
  generations, N1 on and off through `benchmarks/phase2_flags/`;
- the figures of `LIMITATIONS` on the bench (exact laws, the seven equations
  never found, structures under noise, collapses out of domain, formulas
  flagged as departing from their predictions) read from the records of
  M2, and those of the test set from M2 as well.

The figure of the typed generation (1.4 times an untyped one, phase 3)
describes the typed mode, which M1 proves unchanged; it stays as measured.
A figure that changes is published as measured, with the reason.

**M4, tests.** The test suite against the wheel installed in fresh
environments under Python 3.9.23, 3.11.15 and 3.14.0rc2, `twine check` on
both files, and the **Tests** workflow of the repository (Linux, Python 3.9
to 3.14; Windows, 3.12 and 3.14) green on the commit of the release.

**M5, two independent reviews.** Two reviewers (a second agent each time,
who has not seen the work) check every figure of the README in both
languages, of the 1.0.0 entry of the CHANGELOG, of the notebooks and case
studies, of the pages of the limits and of the paper against the result
files, one after the other. Every finding is corrected or answered in
writing before gate 4. These reviews are also the exit criterion of phase 6.

## The targets of gate 2

Reported as measured on the wheel in M2, against the table of gate 2 and
against 0.9.0 side by side. The starting values of gate 2 were measured on
another processor, and a figure under a time budget depends on the machine:
both readings are given.

*Note of 14 October 2026, after the second review of M5:* the sentence above is
wrong. The starting values of gate 2 (0.8.0 in phase 1, `PLAN.md`) were
measured on the processor type of the measurements of 1.0.0, an Intel Xeon at
2.1 GHz (`release_1.0/m3_extra/machine.txt`); it is the release of 0.9.0 that
ran on another one, an Intel Xeon at 2.8 GHz (`release/README.md`). Both
readings are given all the same (`release_1.0/README.md`, M2).

| Indicator | Target for 1.0 |
|---|---|
| F41 exact laws (205 fits, 30 s) | at least 110 |
| the five families at zero (18 equations, 90 fits) | at least 20 |
| TF78 exact laws (390 fits) | at least half of the relative gain on F41 |
| structure retrieved, F41N1 / F41N10 | at least 80 / 77 |
| formulas departing from the model | each flagged, its exact alternatives named |
| collapses out of domain, R6 + R7raw (65 fits) | no more than 10, worst no deeper than −233 |
| median test R², R6 folds | at least 0.804 |
| median test R², TR25 folds | at least 0.761 |
| collapses, TR25 out of domain (125 fits) | fewer than 37 |
| units mode, Feynman II.11.3 | at most 60 s (met in 0.9.0) |

## What would stop the release

- M1: any model that differs. The cause is found before anything else.
- M2, against 0.9.0 on this machine: fewer exact laws on F41; fewer
  structures retrieved on F41N1 or F41N10; a median test R² of the R6 folds
  more than 0.005 below; more collapses out of domain on R6 and R7raw than
  0.9.0 plus 2. A difference beyond these is examined before gate 4 and
  reported whatever its cause.
- A target of gate 2 on the decision bench that is missed is reported to the
  author, who decides at gate 4. The frozen test set (TF78, TS14, TR25) is
  published as measured, whatever it says, and decides nothing; point 2 of
  the pages of the limits is written from it.
- M3: a public figure that no record of the wheel supports.
- M4: a failing test.
- M5: a finding left without an answer.

## Around the release

- **The paper** (`paper/paper.md`) is brought up to date with the figures of
  M2 and M3 before the reviews of M5, which check it.
- **JOSS and SRBench.** Claude prepares the submission to JOSS (the author
  submits it through its web form) and the announcement to SRBench, as for
  0.8.0, in English prose for the maintainers.
- **The launch** (`PLAN_PHASE6.md`, item 5): its texts are drafted after M2
  and M3, from their figures only, and handed to the author with the
  delivery.

## Gate 4

The author receives the measured figures, the differences with 0.9.0, the
targets of gate 2 and the reviews, and decides the publication and the name
of the version. Delivery as for 0.9.0: the work goes to the working branch, a
pull request to `main` that the author merges with "Create a merge commit",
then the author publishes on PyPI and creates the release v1.0.0 on GitHub,
with written instructions. Claude never publishes on PyPI and never handles
its credentials.

## Gate 4, decided by the author on 16 October 2026

After reading the measurements (`release_1.0/README.md`), the differences with
0.9.0, the targets of gate 2 (eight met, two missed as by 0.9.0 measured
beside it) and the two reviews (`release_1.0/M5_review1.md`,
`release_1.0/M5_review2.md`), the author decided:

1. 1.0.0 is published.
2. The name of the version is "Families".

On 14 October he also answered the question of the paper: pull request 227 of
cavalab/srbench is merged (`release_1.0/M5_review2.md`, finding 4).

The package code of the measured wheel, built from commit `61b78ba`, is
unchanged in the branch submitted for merging (`gp_elite/` and
`pyproject.toml`); the commits after it change documentation, tests, benchmark
scripts and records only. `CITATION.cff` gives 17 October 2026, the first day the
author can publish, as the date of the release; it is set to the day of
publication if that is another. `CITATION.cff` is not in the published files.
