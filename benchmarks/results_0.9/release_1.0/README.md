# Measurements of the release 1.0.0

Plan: `../PLAN_RELEASE_1.0.md`, committed before the first measurement of the
release (commit `15e95d8`). Every record here is of gp-elite 1.0.0 **installed
from its wheel** (built from commit `61b78ba`; SHA-256 of the wheel and of the
source archive in `environments.txt`) in a fresh environment, never of the
sources, except where 0.9.0 is named: it is then gp-elite 0.9.0 installed from
PyPI in another fresh environment. `environments.txt` lists the packages of
each environment: `/venv09p` (0.9.0 from PyPI), `/venv10` (the wheel alone,
for M1 and M2) and `/venv10x` (the wheel with the packages some scripts of M3
use). The 0.9.0 wheel on PyPI differs from the one measured for 0.9.0 in its
description only (`environments.txt`).

Machine: Linux, 4 cores (Intel Xeon at 2.1 GHz with AVX-512), 15 GB
(`m3_extra/machine.txt`); Python 3.11.15,
NumPy 2.4.6, scikit-learn 1.9.1, pandas 3.0.6, and for the scripts that use
them sympy 1.14.0, gplearn 0.4.3, xgboost 3.2.0, matplotlib 3.11.2, the
versions of the 0.9.0 measurements. `PYTHONHASHSEED=0`, one process per
measurement, one measurement step at a time on the machine. The scripts ran
from a copy of `benchmarks/`, `examples/` and the two README files of commit
`61b78ba`, without the package beside them, so that none could import the
sources (`m3/m3_driver.sh`).

## M1, equivalence (13 October 2026)

| File | What it shows |
|---|---|
| `M1_compare_13_configurations.txt`, `M1_equiv_1.0.0/` | the thirteen reference configurations of `benchmarks/speed_equivalence.py` return with the wheel the same models as the engine adopted in phase 5 (`../phase5/mechanics/B1_E1_N1_default`) |
| `M1_ii113_1.0.0.jsonl`, `M1_compare_ii113.txt` | the typed fits of Feynman II.11.3, seeds 0 to 9 (`benchmarks/phase3_bench.py`), return the same models as 0.9.0 (`../release/M1_ii113_0.9.0.jsonl`) |

## M3, every public figure measured again (14 October 2026)

`m3/` holds the records of the figures of `README.md`, `README.fr.md`, the
notebooks, the case studies and `paper/paper.md`. They were produced by
`m3/m3_driver.sh`, one step after the other, from 23:57 on 13 October to
00:46 on 14 October: `benchmarks/release_claims/run_claims.py` with the
commands of 0.9.0, in two queues side by side (`m3/claims_queues.txt`), the
islands in sequence under the default `parallel=None` as for 0.9.0; then
`benchmarks/case_studies.py kepler`, `hubble` and `nikuradse`
(`m3/case_*`); then the check of Kepler's law normalised by min-max
(`m3/kepler_minmax_check.txt`). After them,
`benchmarks/release_claims/deduced_constant_check.py` ran with 0.9.0 and with
1.0.0 (`m3/deduced_constant_venv09p.txt`, `m3/deduced_constant_venv10.txt`).

**What changes, and why.** Every change below comes from the seeds of 1.0
(the forms fitted directly, B1 and E1, and the noise-tolerant seeds, N1, which
`PLAN_PHASE5.md` credits with I.16.6) and from the deduced constant; the typed
search is the same as in 0.9.0 (M1). The figures of 0.9.0 in parentheses are
those of its release (`../release/m3/`), measured on another processor (Intel Xeon at 2.8 GHz): its times do not compare
directly with those of 1.0.0 here.

- Feynman 15 (`feynman15.txt`): 15/15 exact and 15/15 within 1e-3 for the
  returned model, against 12/15 and 13/15. I.16.6, I.18.12 and III.15.12
  become exact. With `normalize='none'` the three angle laws stay exact
  (`feynman_angles_normalize_none.txt`): the default now returns them too.
- The duel with gplearn (`duel_gplearn.txt`): 15/15 against 6/15 exact, 15/15
  against 7/15 within 1e-3, GP_ELITE ahead on 9 equations, tied on 6, behind
  on none (against 12/15, ahead on 8, behind on 1).
- The table of `units=` on II.11.3 (`units_ab_ood.txt`): without units, 5/5
  exact laws in about a second per run (median 1 s, 20 nodes), with four times
  the generations as well; 0/5 valid models with 0.9.0. With units, unchanged:
  5/5 valid, 2/5 exact, 27 nodes, median 27 s per run (34 s for 0.9.0, same
  models, M1). Under `units=` the forms fitted directly do not act.
- The size study (`scaling.txt`): I.16.6 exact at 1,000 points and more (at
  2,000 in a form other than the textbook one), and in 5 of the 13 runs below;
  the four other laws exact at every size in every run, as before. The five
  fits take 58 s at 1,000 points and 151 s at 10,000 (139 s and 380 s).
- The battery example (`battery_example.txt`): R² +0.993 on the random split
  (+0.991), +0.162 on the forward split (−0.314), with another equation, in
  the current and the cycle. The tree ensembles are unchanged.
- The notebook snippet of the torque (`notebook_snippet_torque.txt`): without
  units, `r * F * sin(theta)` in 6 nodes instead of `|F * r * sin(theta)|` in 7.
- `robustness_check.txt`: the case without a hold-out on a small signed
  dataset returns the exact law `0.5 + sin(2 * X0)` (R² 0.903 before).
- `small_data_release.txt`: worst train and test R² 1 instead of 0.9974 and
  0.998.
- `time_limit=` (`time_limit_check.txt`, 15 of 16 checks): with a 15 s budget
  the fit in parallel ends at 16.5 s (17.6 s); the fit in sequence stops at
  9.2 s with a model of R² 1.0000, before the budget (a search stops early only
  on an exact law), so the check that expects the budget to be reached fails;
  three restarts in a 24 s budget end at 21.6 s. In this run the check, in the
  second queue, overlapped the end of the first (Nikuradse); run again alone
  after the first review of M5 (`m3_extra/time_limit_check_alone.txt`), the
  same 15 of 16: 16.9 s in parallel, 10.2 s in sequence, 21.5 s for the three
  restarts. The README quotes the run alone.
- The deduced constant (`deduced_constant_*.txt`): on seven typed fits of
  Kepler's law in SI units, 0.9.0 reports the coefficient of the law in five
  and departs from it in two (−20 % and +344 %); 1.0.0 reports it in all
  seven. The models are the same in both versions.
- `import gp_elite` takes 0.18 s (median of seven fresh processes; 0.16 s).

**What is the same.** Every other law, formula, error, size and count: the
fifteen equations with `units=` (14/15), the mystery constant (three laws),
the robust regression, the README examples (Kepler
`0.00279171 + 0.999396 * a * sqrt(a)`, the programmatic example), the
examples, the console (the law and the constant), the 1,500 printed formulas,
the 48 fits of the operator pools, 15 of the sixteen unusual inputs (the sixteenth is under "What changes"), the
eleven
scales, the missing or infinite values, the notebook snippets other than the
torque, Nikuradse under the full protocol, and the check of min-max Kepler
(exact in 0 and 0 of 10 at 10 generations, 3 and 1 at 40, N1 off and on).
The three case studies return on the wheel what they returned on the branch
(`../case_studies/`), to the last printed digit.

## M2, campaign R paired with 0.9.0 (14 October 2026)

`m2/campaignR_0.9.0.jsonl` and `m2/campaignR_1.0.0.jsonl`: the whole suite of
phase 1 (F41, F41 with 1 % and 10 % noise, R6, R7raw, and the frozen test set
TF78, TS14, TR25, TR25raw: 1,775 fits per version, budget T of 30 s per fit),
run by `benchmarks/phase1_bench.py run-paired`, each job started with both
versions at the same time, two jobs at a time, from 00:48 to 07:52 on 14
October, in four time slices of 6,600 s (`m2/driver.log`). No crash.
`m2/tables_*.md` are the tables of `benchmarks/phase1_report.py` for each
version; `m2/compare.txt` the comparison, the criteria of the plan and the
targets of gate 2 (`benchmarks/release_claims/compare_m2_1.0.py`).

| indicator | 0.9.0 | 1.0.0 |
|---|---|---|
| F41 exact laws (205 fits) | 88 | 163 |
| the five families at zero in 0.8.0, exact (90 fits) | 0 | 55 |
| F41 equations never exact in five seeds | 20 | 7 |
| structure retrieved, F41N1 / F41N10 (205 fits each) | 67 / 66 | 105 / 85 |
| TF78 exact laws (390 fits): main 290 / bonus 100 | 145: 144 / 1 | 213: 203 / 10 |
| TF78 equations never exact in five seeds (of 78) | 46 | 34 |
| TS14 exact on the test rows (70 fits) | 8 | 7 |
| R6 folds, median test R² | 0.8095 | 0.8095 |
| R6 + R7raw, collapses out of domain (65 fits), worst R² | 11, −232.5 | 11, −232.5 |
| TR25 folds, median test R² | 0.7657 | 0.7657 |
| TR25raw folds, median test R² | 0.7544 | 0.7580 |
| TR25, collapses out of domain (125 fits) | 37 | 37 |
| formulas flagged as departing from the model, R6 + R7raw (130 fits) | 8 | 7 |

The two versions return the same expression on 1,286 of the 1,775 jobs: all the
fits of R6, 69 of 70 on R7raw, 486 of 500 on TR25 and TR25raw; 474 of the 489
that differ are in the Feynman and Strogatz suites, where 1.0.0 fits forms
directly. On F41, 16
equations gain exact fits and none loses any; on TF78, one fit exact with 0.9.0
is not with 1.0.0 (II.11.28, seed 9, within 1e-3), and on TS14 one (bacres2,
seed 9, within 1e-3).

**Criteria of the plan**: the five are met (F41, F41N1 and F41N10 not below
0.9.0; R6 median within 0.005; collapses of R6 + R7raw not above 0.9.0 plus 2).

**Targets of gate 2** (the ten rows of the table of `../PLAN.md`): eight are met
and two are missed. Met: F41 at least 110 (163); the five families at least 20
of 90 (55); TF78 at least half the relative gain on F41 (at least 206.8, read
from the starting values of gate 2 or from 0.9.0 here, which are the same: 213);
the structures at least 80 and 77 (105 and 85); every formula that departs from
the model flagged, with its exact alternatives named (the warning of 0.9.0,
unchanged); the median R² of the R6 folds at least 0.804 (0.8095) and of the
TR25 folds at least 0.761 (0.7657); the units mode on II.11.3 within 60 s (27 s,
`m3/units_ab_ood.txt`). Missed, by 1.0.0 and by 0.9.0 alike on this machine:
the collapses out of domain of R6 + R7raw, 11 for a target of at most 10 (the
worst, −232.5, is within its target of −233), and those of TR25, 37 for a
target of fewer than 37. 1.0.0 does not change these counts; the targets asked
that it lower them. For its own release, on another processor (Intel Xeon at
2.8 GHz), 0.9.0 measured 10 and 36, which met both targets; the starting
values of gate 2 (0.8.0 in phase 1) were measured on the processor type used
here, Intel Xeon at 2.1 GHz.
(`m2/compare.txt` lists eleven lines because it reads the TF78 target both
ways, and leaves out the two qualitative or M3 rows; its line "formula_exact
False, R6 + R7raw folds and test" counts the folds only, 4 and 3, where the
table above counts folds and out of domain.)

Against the measurement of 0.9.0 for its release (`../release/m2/`, on the
2.8 GHz processor): 0.9.0 gives here 88 exact laws on F41 instead of 86, 67 and
66 structures instead of 66 and 62, 145 on TF78 instead of 144, 8 exact fits on
TS14 instead of 7, 0.7657 on the TR25 folds instead of 0.7466, and 6 collapses
out of domain on R7raw instead of 5 (11 with R6 instead of 10) and 37 on TR25
instead of 36. Under a time budget the figures depend on the machine and its
load; the comparison of versions is the paired one above.

## M4, tests (14 October 2026)

`M4_wheel_tests.txt`: the test suite against the wheel installed in a fresh
environment, under Python 3.9.23, 3.11.15 and 3.14.0rc2, each importing the
installed package; `twine check --strict` passes for the wheel and the source
archive. The first run failed one test under 3.9 and 3.14,
`test_deduced_constant_matches_the_predictions`, added with the correction of
the deduced constant: it expected the constant in s/m^1.5, while the search
returns another model with other versions of NumPy, and on the processors of
GitHub, where the same test had failed in 6 of the 7 runs since its commit (run
66 passed). It now checks the
guarantee on whatever model comes back, and still fails on the code before the
correction (20 % off on seed 0, as `m3/deduced_constant_venv09p.txt` records
for 0.9.0); with it, 151 tests pass under the three versions. The
**Tests** workflow is green again from that commit on (`M4_ci_runs.txt`). The
package code is unchanged: the test is not in the wheel.

## After the first review of M5 (14 October 2026)

`m3_extra/`, measured on the wheel (`/venv10x`) one step after the other, with
nothing else on the machine (`m3_extra/driver.sh`, `driver.log`):

- `parallel_islands/`: without the switch that runs the islands in sequence, as
  for 0.9.0 (`../release/m3_rerun/parallel_islands/`). The README example as it
  stood before 0.9.0 (no `parallel=`) returns with the islands in parallel the
  same approximation as with 0.9.0, validation R² 0.9999765, 14 nodes; the README
  Kepler block returns the same law as printed; `kepler_demo.py` and
  `pools_check.py` (48 fits, no violation) give the records of `m3/`.
- `time_limit_check_alone.txt`: the check of `time_limit=`, alone (above, M3).
- `notebooks/`: the code of the six case-study notebooks, run as scripts with
  the wheel (the Nikuradse data from the local copy of the PMLB file the
  benchmarks check by SHA-256): they print the figures of seed 0 their text
  quotes. The other figures of their text (seeds 1 to 4, and in Kepler the
  fit of the inner planets without units) come from `benchmarks/case_studies.py`
  (`m3/case_*`).
- `machine.txt`: the processor, the cores and the memory.
