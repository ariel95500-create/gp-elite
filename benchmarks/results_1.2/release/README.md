# Measurements of the release 1.2.0

What `../PLAN_RELEASE_1.2.md` asks before gate 8, as it was measured. The
machine has 4 cores with AVX-512 (`m2/machine.txt`: an Intel Xeon of model 173
under KVM); every fit runs in its own process with `PYTHONHASHSEED=0`. The
container does not always run on the same host, so the versions are compared
within one campaign or one day, never across days.

## The release candidate

Commit c3ea7fc carries the engine of a263177 (the typed start, H1 and X1); it
changes the version number and opens the CHANGELOG. Its wheel and source
archive, built from a clean export, are in `environments.txt` with their SHA-256
and the `uv pip freeze` of three environments:
- `/venv12b`: the wheel alone (Python 3.11.18, NumPy 2.4.6, SciPy 1.17.1,
  scikit-learn 1.9.1);
- `/venv12bx`: the same, with the packages the scripts of M3 use;
- `/venv11p`: gp-elite 1.1.0 installed from PyPI, with the same packages. Its
  `gp_elite/` files are identical to those of commit 346cd07, from which 1.1.0
  was published.

## M1, equivalence (4 November 2026)

`M1_equiv_1.1.0/` and `M1_equiv_1.2.0/`: the thirteen reference configurations
of `benchmarks/speed_equivalence.py`, run with `/venv11p` and `/venv12b` by
`run_m1.sh` (`M1.log`). `M1_compare_1.1.0_vs_1.2.0.txt`: all identical, as the
plan expected; the thirteen take 21.7 s with 1.1.0 and 21.1 s with 1.2.0. The
core count the log prints is that of `nproc` under `OMP_NUM_THREADS=1`, which
`nproc` honours; the note at the end of `M1.log` says so.

## M2, campaign R paired with 1.1.0 (4 and 5 November 2026)

`m2/campaignR_1.1.0.jsonl` and `m2/campaignR_1.2.0.jsonl`: 1.1.0 from PyPI
(`/venv11p`) against the candidate (`/venv12b`), 2,780 fits per version with a
budget T of 30 s per fit:
- the whole suite of phase 1 (F41, F41N1, F41N10, R6, R7raw, and the frozen test
  set TF78, TS14, TR25, TR25raw: 1,775 fits);
- U41, U41N1 and U41N10 (615);
- TF78 under units (390, seeds 5 to 9).

Before M2, `benchmarks/phase1_bench.py` was given the record of the formula of
1.2.0 with X1 switched off (`expr_11`, `formula_exact_11`), computed after the
timed fit, as the plan says. The check on three jobs with both versions is in
`m2/bench_check_1.1.0.jsonl` and `m2/bench_check_1.2.0.jsonl`.

The campaign was run by `phase1_bench.py run-paired` (`m2/driver.sh`), from a
copy of `benchmarks/` of commit e92f86d, each job started with both versions at
the same time, two jobs at a time, in time slices of 6,300 s
(`m2/driver.log`), from 18:24 on 4 November to 04:19 on 5 November (times of
the machine, UTC). Three things happened on the way, each written in the log:
- **The container restarted at about 20:22** and stopped the driver. The 806
  jobs recorded by then were whole and paired in both files; the jobs in flight
  were lost.
- **The data of the frozen test set.** The copy of `benchmarks/` lacked
  `benchmarks/_pmlb_cache`, which git ignores, so the files of the frozen test
  set were downloaded during the fits, by both versions at once. 17 jobs
  crashed on the download (13 fits of 1.1.0, 16 of 1.2.0). Every file of the
  cache (117 of the test set, 7 of `pmlb_frozen`) was then fetched once and
  checked against its SHA-256. The 17 jobs were removed from both files, kept
  in `m2/removed_for_the_data_cache.jsonl`, and run again with the rest. The
  results kept are not touched: every load of these files checks their SHA-256,
  and a file that does not match stops the fit rather than feeding it. The
  driver started again at 20:24.
- **The container restarted again between 02:30 and 02:33.** The 2,229 jobs
  recorded were whole and paired, on the same processor; the driver started
  again at 02:33 from the jobs not recorded.

At the end: 2,780 jobs in each file, the same jobs in both, none twice, no
crash.

`m2/tables_*.md` are the tables of `benchmarks/phase1_report.py` for each
version. `m2/compare.txt` holds the comparison and the criteria of the plan
(`benchmarks/release_claims/compare_m2_1.2.py`). `m2/details.txt` is the script
of the release of 1.1 (`../../results_1.1/release/m2/details.py`) on these
records; `m2/details_x1.txt` splits the jobs that differ by what X1 does
(`m2/details_x1.py`).

| indicator | 1.1.0 | 1.2.0 |
|---|---|---|
| F41 exact laws (205 fits) | 163 | 163 |
| structure retrieved, F41N1 / F41N10 (205 fits each) | 108 / 85 | 108 / 85 |
| R6 folds, median test R² | 0.8095 | 0.8095 |
| R6 + R7raw, collapses out of domain (65 fits) | 10 | 10 |
| U41 exact laws (205 fits) | 166 | 166 |
| structure retrieved, U41N1 / U41N10 (205 fits each) | 113 / 98 | 113 / 98 |
| fits under units passing `check_dimensions` | 1,005 of 1,005 | 1,005 of 1,005 |
| fits under units, median time (s) | 30.2 | 30.2 |
| fits under units, longest (s) | 420.7 | 31.6 |
| frozen test set, deciding nothing: | | |
| TF78 exact laws (390 fits) | 214 | 214 |
| TS14 exact on the test rows (70 fits) | 10 | 10 |
| TR25 folds, median test R² | 0.7692 | 0.7692 |
| TF78 under units, exact laws (390 fits) | 229 | 229 |

**No status changes.** In none of the 2,780 jobs does a fit go from exact, near
or missed to another of the three, and the structures retrieved are the same.
Out of domain, R6, R7raw, TR25, TR25raw and TS14 have the same collapses in
both versions (5, 5, 38, 28 and 28).

**The printed formula.** 316 jobs return another expression. Two causes:
- **X1 alone, 276 jobs** (257 without units, 19 under units): with X1 switched
  off, the formula of 1.2.0 is that of 1.1.0. For example, Feynman I.6.20a,
  seed 1: `0.398942 * |0.0114856^(0.11194 * v0²)|` becomes
  `0.398942 * |exp(-0.5 * v0²)|`.
- **Another model, 40 jobs** (22 without units, 18 under units). 28 of them
  reached the time budget in both versions: a fit stopped at its budget returns
  the best model found by then, and that depends on the load of the machine.
  The other 12 are III.19.51 under units, whose typed start D0 changes. At
  seeds 0 and 3 of U41, exact with both versions, in 370.6 and 374.5 s with
  1.1.0 and in 1.0 and 1.1 s with 1.2.0, which writes the same law in another
  form. The ten fits with noise (U41N1 and U41N10) reached the budget in both
  versions, but 1.1.0 spent it in its typed start and ran one generation,
  where 1.2.0 runs 35 to 40. (`m2/details_x1.txt` counts those ten among the
  16 fits under units at the budget in both versions; this split was corrected
  after the first review of M5.)

X1 rewrites the printed formula on 287 fits of 1.2.0, 267 without units and 20
under units, the frozen test set included. On every fit,
`formula_exact` is that of the formula without X1, and on the 316 fits outside
the frozen test set where neither version reached its budget (III.19.51 under
units aside), the formula without X1, the error on the test rows and
`formula_exact` are those of 1.1.0, to the bit. The same holds on the 471 such
fits of the frozen test set.

**III.19.51 under units.** The 15 fits (U41, U41N1, U41N10, five seeds each):

| suite | 1.1.0, time (s) | 1.2.0, time (s) | status, both versions |
|---|---|---|---|
| U41 | 342 to 387 | 0.99 to 1.16 | exact |
| U41N1 | 334 to 421 | 30.12 to 30.46 | near |
| U41N10 | 341 to 384 | 30.05 to 30.40 | near |

With noise, 1.2.0 runs its budget of 30 s, as on the other laws with noise;
1.1.0 overran it by eleven to fourteen times. The plan quoted 430 to 735 s for
1.1.0, measured on another day: the figures that compare are those of this
campaign. Without III.19.51, the longest fit under units takes 31.6 s with
1.2.0 and 31.5 s with 1.1.0.

Fits that reached their time budget: 1,993 with 1.1.0 and 1,987 with 1.2.0, of
2,780.

**Criteria of the plan**: the thirteen are met (`m2/compare.txt`).
- F41 not more than 3 exact laws below 1.1.0: 163 and 163.
- F41N1 and F41N10 not more than 3 structures below: identical.
- R6 median within 0.005: identical.
- Collapses of R6 + R7raw not above 1.1.0 plus 2: 10 and 10.
- U41 not more than 3 exact laws below 1.1.0: 166 and 166.
- U41N1 and U41N10 not more than 3 structures below: identical.
- Every model returned under units passes `check_dimensions`: 1,005 of 1,005.
- III.19.51 under units, each of the 15 fits within 60 s: the longest takes
  30.5 s.
- X1: the formula without X1 is recorded on every fit (1,360 outside the frozen
  test set, none missing); `formula_exact` is never changed by X1; where neither
  version reached its budget (316 fits), the model is that of 1.1.0.

The frozen test set decides nothing and is published as measured: TF78 214 and
214 exact laws, TS14 10 and 10, TR25 median 0.7692 and 0.7692, TF78 under units
229 and 229.

## M3, every public figure measured again (5 November 2026)

`m3/` holds the records of the figures of the READMEs, the notebooks, the case
studies and the paper, produced by `m3/m3_driver.sh` with `/venv12bx`, one step
after the other, from 04:23 to 05:04, nothing else on the machine. The driver
runs the steps of the M3 of 1.1 on a copy of `benchmarks/`, `examples/` and the
READMEs of commit 784152d without the package beside them, and one step more:
the TP notebook four times, 1.1.0 (`/venv11p`) and 1.2.0 in turn, to compare
its times on one day (`m3/tp_timing/notebook_pair/`). The notebook is run as
the script of its code cells without the `pip` line (`m3/tp_six_lois.py`),
which is the script of the M3 of 1.1 to the byte: only its text changed since.
The container restarted after M3 ended, between 05:04 and 05:20.

**Against the M3 of 1.1.** `m3_compare.py` compares each record with the one of
30 October once times, dates, the paths of the environments and folders, and
the version numbers are masked (`m3_compare_1.1.0_vs_1.2.0.txt`). 40 records are
the same: every law, formula, error, size and count, among them the Kepler and
Hubble case studies, Feynman 15 (15 of 15 exact) and Feynman 15 with `units=`
(15 of 15), the records of the table of `units=` on II.11.3 (its text differs
by the seconds, below), the duel with gplearn, the
mystery constant and the snippets of the notebooks. What differs has two
causes.

The printed formula, where X1 writes a power of a number as an exponential. The
models, their sizes and their errors are those of 1.1:
- the battery example: `exp(0.51573 * courant)` becomes `exp(courant / 1.939)`;
- the Nikuradse case study, seeds 0, 1, 3 and 4 (`case_nikuradse/`,
  `nikuradse_full.txt`), formulas of size 13 to 72, and the warning of seed 1,
  which quotes one of them;
- `robustness_check`, the case of integer and boolean columns:
  `15 + 15 * (0.2 * X0 - 0.866667^X1)` becomes
  `15 + 15 * (0.2 * X0 - exp(-X1 / 6.98808))`, an exact formula in both;
- `small_data_check`, four fits of the law `2.5 exp(-0.7x) + 0.3`, for example
  `0.3 + 2.5 * 0.0436988^(0.223611 * X0)` becomes `0.3 + 2.5 * exp(-X0 / 1.42857)`;
- `feynman_scaling`, one fit of I.16.6 at 500 points, whose census of operators
  counts the exponential.

Timing:
- the order in which the parallel queues of `run_claims.py` ended
  (`claims_queues.txt`);
- in the console example, run on three parallel islands, the order of the
  islands' prints and the statistics of the stigmergic memory. The final
  result is the same: `force = 250 * elongation`, constant 250 kg/s²;
- the times: the machine of this day is faster than that of 30 October. One
  generation of `time_limit_check.py` takes 0.6 s in sequence against 1.0 s
  then; `import gp_elite` takes a median of 0.073 s against 0.12 s; the five
  fits of `feynman_scaling.py` take 38 s at 1,000 points and 103 s at 10,000,
  against 58 s and 153 s; the seconds of each run in `units_ab_ood.txt` round
  to 0 or 1 as they did;
- `time_limit_check.py`: 13 of 16 checks, against 15 of 16 on 30 October.

**`time_limit_check.py`.** The three checks that fail ask that the budget cut
the search (`time_limit_reached` True): the fit in sequence and the fit in
parallel with a budget of 15 s, and `GPEliteRegressor` with a budget of 6 s.
Here the search finds the exact law first (R² 1.0000) and ends by itself, at
6.3 s in sequence and 12.5 s in parallel, so the flag is rightly False. The
fit in sequence did so on 30 October as well; on this faster machine the two
others do too. Run again after M3, 1.1.0 and 1.2.0 in turn, twice each, on
this day (`m3_extra/time_limit_pair/`): 1.1.0 passes 13 and 14 of 16, 1.2.0
13 and 13. The fit of `GPEliteRegressor` is the one that varies: 1.1.0 reached
its budget in its second run and not in its first. The same checks, then,
with both versions: nothing in 1.2.0 changes the time budget, and H1 does not
act when `time_limit=` is set.

**The TP notebook.** The six fits return the formulas and the deduced
constants of 1.1.0 (g 9.81 and 9.74, R 8.250, P 10.02 W), in 8, 10, 8, 8, 8
and 7 s, 49 s in all. That is H1: the notebook sets neither `generations` nor
`time_limit`, so each search stops once its error on the hold-out rows has not
improved by 1 % in 30 generations. On the same day, one version after the
other, alone on the machine:

| fit | 1.1.0, run 1 / run 2 (s) | 1.2.0, run 1 / run 2 (s) |
|---|---|---|
| pendulum | 28 / 28 | 8 / 8 |
| spring | 34 / 33 | 10 / 10 |
| free fall | 37 / 37 | 8 / 8 |
| power | 32 / 30 | 7 / 7 |
| gas | 36 / 35 | 8 / 8 |
| illuminance | 31 / 31 | 7 / 7 |
| in all | 198 / 194 | 48 / 48 |

Every fit returns the same formula in the four runs. The notebook takes about
a quarter of its time with 1.1.0. Its text quoted the run of 1.1.0 on another
day (42 to 55 s a fit), which compares with neither column; it now quotes the
run of this M3.

The figures of the pages of the limits read from the records of M2 are given
with the documents.

## M4, tests (5 November 2026)

`M4_wheel_tests.txt`: the test suite of 971bcec, the same as that of a263177,
against the wheel of c3ea7fc, installed in a fresh environment for each of
Python 3.9.25, 3.11.18 and 3.14.6, with the pins of the environments of the M4
of 1.1 (`m4/requirements_*.txt`), each importing the installed package
(`m4/run.sh`): 169 tests pass under the three versions. `twine check --strict`
passes for the wheel and the source archive. The **Tests** workflow of the
repository is green on every commit of the branch since the candidate; it is
checked again on the commit of the release, and the files handed over for PyPI,
built again from that commit, are checked again too.
