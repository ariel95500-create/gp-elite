# Measurements of the release 1.4.0

What `../PLAN_RELEASE_1.4.md` asks before gate 12, as it was measured. The
machine has 4 cores (an Intel Xeon under KVM). Every fit runs in its own
process with `PYTHONHASHSEED=0`. The container does not always run on the same
host, so the versions are compared within one campaign or one day, never
across days.

## The release candidate

Commit f6a36cd carries the engine of 227d837, the candidate of the campaign
of N2b. It changes the version number, opens the CHANGELOG and rewrites one
comment of `gp_elite/core.py`. Its wheel and source archive were built from a
clean export. `environments.txt` gives their SHA-256 and the `uv pip freeze`
of the environments:
- `/venv14r`: the wheel alone, with the packages of `/venv13r` (Python
  3.11.18, NumPy 2.4.6, SciPy 1.17.1, scikit-learn 1.9.1);
- `/venv14rx`: the same, with the packages of `/venv13rx`, for M3;
- `/venv13p`: gp-elite 1.3.0 installed from PyPI. Its `gp_elite/` files are
  those of the published wheel, downloaded again and checked against its
  SHA-256.

`twine check --strict` passes for both files.

## M1, equivalence (13 November 2026)

`M1_equiv_1.3.0/`, `M1_equiv_n2b/` and `M1_equiv_1.4.0/` hold the thirteen
reference configurations of `benchmarks/speed_equivalence.py`. They were run
with `/venv13p`, `/venv14n2b` and `/venv14r` by `run_m1.sh`, from a copy of
`benchmarks/` of f6a36cd (`M1.log`). As the plan expected:
- **the thirteen of 1.4.0** are identical to those of the candidate of N2b
  (`M1_compare_n2b_vs_1.4.0.txt`);
- **against 1.3.0** (`M1_compare_1.3.0_vs_1.4.0.txt`), twelve are identical,
  and C_big differs in its Pareto front only: its model is the same. C_big is
  a noisy table, 5,000 rows of x0·x1/x2 with Gaussian noise. 1.4.0 places
  twelve noise-tolerant seeds there, the six of 1.3.0 among them, where 1.3.0
  places six. That was first read on a trace that was not kept; after the
  first review of M5, `m1_examine/cbig_seeds.py`, committed before its run,
  recorded it on one generation of each version (`m1_examine/`).

The thirteen took 21.8 s with 1.3.0, 21.5 s with the candidate of N2b and
26.2 s with 1.4.0, run in that order. The last two have the same engine, so
these times say nothing about it.

## M2, campaign R paired with 1.3.0 (13 and 14 November 2026)

`m2/campaignR_1.3.0.jsonl` and `m2/campaignR_1.4.0.jsonl`: 1.3.0 from PyPI
(`/venv13p`) against the candidate (`/venv14r`), 3,092 fits per version with
a budget T of 30 s per fit:
- the whole suite of phase 1 (F41, F41N1, F41N10, R6, R7raw, and the frozen
  test set TF78, TS14, TR25, TR25raw: 1,775 fits);
- U41, U41N1 and U41N10 (615);
- TF78 under units (390, seeds 5 to 9);
- TF78N, the frozen noisy test set (312).

`m2/tp_*.jsonl` and `m2/tpt10_*.jsonl` hold the two sets of TP, 400 fits per
version each.

The campaign was run by `m2/slice.sh`, from a copy of `benchmarks/` of
commit 796b31c with the data cache of the M2 of 1.3. Each job started with
both versions at the same time, two jobs at a time (`m2/driver.log`, times
of the machine, UTC):
- TP and TPT10 in one go, from 20:46 to 21:52 on 13 November;
- the benches in six slices of at most 6,300 s, from 21:53 to 08:19 on
  14 November.

The container did not restart, and the machine recorded at each slice is of
the same model (`m2/machine_*.txt`). At the end, each set has the same jobs
in both files, and no fit crashed.

`m2/compare.txt` holds the comparison and the criteria of the plan
(`benchmarks/release_claims/compare_m2_1.4.py`, committed before any record
of M2 existed). To check that it runs, it was tried before on records of
earlier campaigns: those of the M2 of 1.3 for the benches, those of campaign
N2b for TP, and the baseline of TPT10 against itself. That printed the
counts of the baseline of TPT10 by experiment, which its plan had left
unread; no change of the engine followed, and TPT10 decides nothing.

| indicator | 1.3.0 | 1.4.0 |
|---|---|---|
| F41 exact laws (205 fits) | 171 | 171 |
| structure retrieved, F41N1 / F41N10 (205 fits each) | 116 / 87 | 152 / 95 |
| R6 folds, median test R² | 0.8095 | 0.8095 |
| R6 + R7raw, collapses out of domain (65 fits) | 10 | 10 |
| U41 exact laws (205 fits) | 174 | 174 |
| structure retrieved, U41N1 / U41N10 (205 fits each) | 121 / 95 | 150 / 93 |
| fits under units passing `check_dimensions`, TF78N included | 1,161 of 1,161 | 1,161 of 1,161 |
| TP, the law, plain arm / units arm (200 fits each) | 126 / 120 | 123 / 120 |
| TP, median time of a fit, plain arm / units arm (s) | 7.0 / 8.3 | 7.0 / 8.4 |
| frozen test sets, deciding nothing: | | |
| TF78 exact laws (390 fits) | 214 | 214 |
| TS14 exact on the test rows (70 fits) | 9 | 10 |
| TR25 folds, median test R² | 0.7692 | 0.7692 |
| TF78 under units, exact laws (390 fits) | 228 | 228 |
| TF78N, structure retrieved, 1 % / 10 % noise (78 fits each) | 34 / 27 | 37 / 28 |
| TF78N under units, the same | 35 / 32 | 37 / 33 |
| TPT10, the law, plain arm / units arm (200 fits each) | 107 / 103 | 107 / 103 |

**Criteria of the plan:** the eighteen are met (`m2/compare.txt`).
- **Where 1.4 does not act:** 2,428 fits of 3,092 place the same
  noise-tolerant seeds in both versions, none in most of them. On the 782 of
  these where neither version reached its budget, the recorded formula, the
  error on the test rows and `formula_exact` are those of 1.3.0, to the bit.
- **TP:** the 400 models of 1.4.0 are those of the candidate of N2b in its
  campaign, as expected: the fits of TP are reproducible. The law comes back
  in 123 fits against 126 in the plain arm and 120 against 120 under units,
  within the 5 allowed; the median time is 7.0 s against 7.0 s and 8.4 s
  against 8.3 s; the 200 models of the units arm pass their gate.
- **Without units:** F41 keeps its 171 exact laws, and no equation falls.
  F41N1 and F41N10 have 247 structures against 203, the gain of N2b (+44,
  the plan asks +15). The R6 median and the collapses out of domain are
  unchanged.
- **Under units:** U41 keeps its 174 exact laws, and no equation falls.
  U41N1 has 150 structures against 121, U41N10 93 against 95, within the 3
  allowed. The 1,161 models returned under units pass `check_dimensions`.

The counts under noise are those of campaign N2b to the unit, for both
versions. U41 has one exact law more in each version than in that campaign
(174 against 173), which timing alone moves.

**Beside, deciding nothing** (`m2/compare.txt`):
- The structures move on nine equations, as in campaign N2b: gains at 1 %
  noise on I.32.5, I.40.1, I.44.4, II.11.27, II.11.3, II.35.18, III.15.12 and
  III.19.51, and at 10 % on I.32.5, I.44.4 and III.19.51, and under units on
  II.11.27 (0 → 1); losses at 10 %
  noise on I.27.6 (2 → 0 without units, 5 → 1 with them) and III.15.12 (5 → 2
  and 5 → 1).
- The noise-tolerant seeds are placed in more fits with 1.4.0: 165 against
  140 in F41N1, 130 against 95 in F41N10, 125 against 95 in U41N1, 115
  against 85 in U41N10. Neither version places one on R6, R7raw or TR25. On
  TR25raw, seeds are placed in 7 fits; in 5 of them (four folds of
  first_principles_planck, one of 1096_FacultySalaries), 1.4.0 places other
  seeds and returns another formula, the test R² moving by 0.006 at most.
- `formula_exact` is False about as often with both versions, suite by
  suite.
- On TP, the point source has the law in 14 fits of 20 against 18 in the
  plain arm (`../n2b/campaign/examine/`); the count of every other experiment
  moves by one at most. Fit by fit, 9 change, all in the plain arm: 6 lose the
  law (the point source 4, the gas and the thin lens 1 each) and 3 gain it
  (the spring, the free fall and the thin lens).

**The frozen test sets,** published as measured, decide nothing:
- TF78, TS14, TR25 and TF78 under units hardly move. TF78 keeps its 214
  exact laws, though 14 of its fits change status, and TF78 under units its
  228. TS14 has one exact fit more, and TR25 the same median.
- TF78N, the noisy set N2b was not designed on: the structure comes back in
  37 and 28 fits of 78 against 34 and 27, and under units in 37 and 33
  against 35 and 32.
- TPT10: the law comes back in the same number of fits, 107 and 103; it is
  useful in 173 fits against 169 in the plain arm. By experiment, the count
  moves by 2 at most (the capacitor charge 7 → 9, Kepler's third law 10 → 9,
  the thermistor 4 → 3). Fit by fit, 10 change, all in the plain arm: 5 lose
  the law and 5 gain it, Kepler's third law in 3 of them (2 lost, 1 gained).

`m2/limits_figures.txt` gives the figures of the pages of the limits read
from the records of M2, for both versions; the pages were brought to them
with the documents.

## M3, every public figure measured again (14 November 2026)

`m3/` holds the records of the figures of the READMEs, the notebooks, the
case studies and the paper. They were produced by `m3/m3_driver.sh` with
`/venv14rx`, one step after the other, from 08:21 to 09:00 on 14 November,
after M2, with nothing else on the machine (`m3/m3_driver.log`). The driver
runs the steps of the M3 of 1.3 on a copy of `benchmarks/`, `examples/` and
the READMEs of commit fbe9b00, without the package beside them. Beside them,
it runs the deduced constant with 1.3.0 (`/venv13rx`), and the TP notebook
four times more, 1.3.0 and 1.4.0 in turn (`m3/tp_timing/notebook_pair/`).
The notebook is run as the script of its code cells without the `pip` line
(`m3/tp_six_lois.py`), the script of the M3 of 1.2 and 1.3 to the byte.

**Against the M3 of 1.3.** `m3_compare.py` compares each record with the one
of 9 November once times, dates, the paths of the environments and folders,
and the version numbers are masked (`m3_compare_1.3.0_vs_1.4.0.txt`). 44
records are the same: every law, formula, error, size and count. Among them
are the three figures on exact data that the plan names: Feynman 15 (15 of
15 exact), the duel with gplearn (15 of 15 against 6 of 15) and the mystery
constant. The examples of the README are the same too, and so are the
snippets of the notebooks but two, the Nikuradse case study at seeds 0 and 3
with its five reports, and Kepler's law normalised by min-max with the pool
`full`.

The comparison lists four records as new. The deduced constant with 1.4.0
(`m3/deduced_constant_venv14rx.txt`) differs from the one with 1.3.0 only by
the line of the version. The other three are the runs of the TP notebook
with 1.4.0, below. The records of 1.3 that have no counterpart here are the
runs of 1.2.0 (the deduced constant and two runs of the TP notebook),
`notebook_tp_six_lois_1.3.0.txt`, whose run of 1.4.0 is compared with it
below, and `../../results_1.3/release/m3/examine/`, the examination that
followed the M3 of 1.3.

22 records differ, for six causes:
- **The noise-tolerant stage on noisy data,** as the plan expected:
  `battery_example.txt`, on the simulated battery data. On the forward
  split, the equation of 1.4.0 has an R² of −3.812 on the cycles held out,
  against +0.162 with 1.3.0, and the script's closing sentence changes with
  it; on the random split, +0.992 against +0.993. The pages of the examples
  were brought to it with the documents.
- **The trace of the seeds placed:** `case_kepler.txt` and
  `case_hubble.txt`. Their models, constants and errors are those of 1.3.0.
  Their list of the seeds placed has the new passes of the noise-tolerant
  stage, and on the fit without units of the eight planets (C8), the stage
  places 10 seeds against 5.
- **W1, the text of the warning:** `m3/case_nikuradse/nikuradse_seed1.txt`,
  `seed2` and `seed4`, `notebook_snippet_nikuradse.txt` and
  `notebook_snippet_tp.txt`. The warning of a formula that departs from
  `predict()` names the clip of the arcsine; the counts it gives are those
  of 1.3.0.
- **Data without noise where the noise-tolerant stage runs,** below: nine
  records of five scripts, `scaling.jsonl` and `scaling.txt`,
  `feynman15_units.jsonl` and `feynman15_units.txt`,
  `robustness_check.jsonl`, `robustness_check.txt` and
  `robustness_check_run.txt`, `small_data_release.jsonl`, and
  `time_limit_check.txt`.
- **Timing:** `claims_queues.txt`, the order in which the two queues of
  `run_claims.py` ended; `console_hooke.txt` and `gp_elite_log.csv`, the
  console example on three parallel islands, where the order of the islands'
  prints and the statistics of the stigmergic memory change while the final
  result stays `force = 250 * elongation`, constant 250 kg/s²; and
  `import_time.txt`.
- **The driver itself:** `m3_driver.log`, its dates, commit and kernel.

As in the M3 of 1.3, `gp_elite_best.txt` and `gp_elite_log.csv`, which the
console example writes, were compared here and are not published
(`.gitignore`).

**Data without noise.** The plan expected the figures on exact data to stay
as they were, within the noise of time budgets. Nine records moved, because
the noise-tolerant stage does not wait for noise: it runs wherever the exact
finders of binomials and of functions of a monomial place no seed, and N2b
adds its forms there. `m3_examine/seeds.py`, committed before its run and
deciding nothing, builds the data of every fit of those five scripts and of
the battery example as M3 does, runs each for one generation with 1.3.0 and
1.4.0 (`/venv13rx` and `/venv14rx`), and records the seeds of each call of
the stage (`m3_examine/seeds_compare.txt`; the data of the 86 fits whose
records carry a hash are checked against it). Every fit whose record moved
is one where 1.4.0 places other noise-tolerant seeds:
- **The scaling bench** (`scaling.txt`): the 85 fits of five Feynman
  equations from 25 to 10,000 points. The stage places other seeds in 6 of
  them, all six of I.16.6, the relativistic addition of velocities: exactly
  the 6 fits that return another model. The 79 fits with the same seeds
  return the same models. I.16.6 is exact in 10 fits of 17 against 9: at 200
  points in 3 of 3 against 2, once in a form other than the textbook one; at
  2,000 points now in the textbook form, at 5,000 in another one.
- **Feynman 15 under units** (`feynman15_units.txt`): 15 of 15 exact with
  both versions. On I.16.6, where the stage places 5 seeds against 4, the law
  comes back with a factor 1.00755 above and below that cancels, against
  1.00758.
- **The robustness check** (`robustness_check.txt`): on the case of a wide
  dynamic range, y = x1·log(x0) with x0 from 1e-3 to 1e6, the stage of
  1.4.0 places one seed, x1·log(c·x0), and 1.4.0 returns the law,
  `X1 * log(X0)`, exact. 1.3.0, which placed no seed there, returned an
  approximation of R² 0.999367 whose printed formula departed from the
  model. The fifteen other cases are the same.
- **The small-data check** (`small_data_release.jsonl`): on the 25 points of
  2.5 exp(−0.7x) + 0.3, the stage places 5 seeds against 1, among them an
  exponential of x. At search seeds 1 to 3, 1.4.0 returns the law as
  written, `0.3 + 2.5 * exp(-X0 / 1.42857)`, size 8. 1.3.0 printed the same
  formula at seed 1 from a model of size 9, and two longer forms of the same
  function at seeds 2 and 3, sizes 10 and 13. Every R² is that of 1.3.0, and
  so is the summary (`small_data_release.txt`).
- **The check of `time_limit=`** (`time_limit_check.txt`): 15 of 16 checks
  against 14 of 16. On its 3,000 rows of x0·x1/x2 + 0.3·x3, the stage places
  4 seeds against 1. In sequence, 1.4.0 runs to its budget, 15.3 s, and
  returns an approximation of R² 0.9979, where 1.3.0 returned the law at
  6.3 s; the check that the budget stopped the search passes for that
  reason. In parallel, the law comes back at 9.7 s, before the budget, as at
  13.2 s with 1.3.0, so that check fails with both versions. On the first
  300 rows, where the script runs three more fits, the stage places 4 seeds
  against none, and their formulas no longer depart from `predict()`: with
  1.3.0, the warning was printed for each of the three.

The pages that quote these figures were brought to them with the documents:
the scaling bench and I.16.6 under units in `docs/measurements.md`, the check
of `time_limit=` in `docs/usage.md`, and their French versions.

**Timing:**
- The five fits of `feynman_scaling.py` at 1,000 and 10,000 points, with the
  same models with both versions, take 40 s and 100 s, against 41 s and
  113 s on 9 November.
- The check of `time_limit=` in parallel, 9.7 s against 13.2 s, and the
  import of the package, 0.069 to 0.083 s against 0.077 to 0.086 s.

These are two days, on hosts that may differ, so these times do not compare
the versions.

**The TP notebook of the six laws.** The six fits return the formulas and
the deduced constants of 1.3.0. The same day, one version after the other,
alone on the machine:

| fit | 1.3.0, run 1 / run 2 (s) | 1.4.0, run 1 / run 2 (s) |
|---|---|---|
| pendulum | 8 / 9 | 8 / 9 |
| spring | 11 / 11 | 11 / 11 |
| free fall | 8 / 9 | 8 / 8 |
| power | 7 / 8 | 8 / 9 |
| gas | 8 / 9 | 9 / 9 |
| illuminance | 7 / 8 | 8 / 7 |
| in all | 49 / 54 | 52 / 53 |

Every fit returns the same formula in the four runs and in the run of the
driver (`m3/notebook_tp_six_lois_1.4.0.txt`, 51 s in all), as with 1.3.0 in
the M3 of 1.3.

## M4, tests (14 November 2026)

`m4/summary.txt` gives the test suite of f005aab, run against the wheel of
f6a36cd by `m4/run.sh`, from 09:00 to 09:10, after M3. The wheel was
installed in a fresh environment for each of Python 3.9.25, 3.11.18 and
3.14.6, with the pins of the M4 of 1.2 and 1.3 (`m4/requirements_*.txt`),
each importing the installed package. 199 tests pass under the three versions
(`m4/pytest_*.txt`). `twine check --strict` passes for the wheel and the
source archive (`m4/twine_check.txt`), whose SHA-256 are those of
`environments.txt`.

Under 3.9 and 3.11, LAPACK printed "On entry to DLASCL ..." six times during
the tests, so the last line of their output, which `summary.txt` keeps, is
that message; the line before it reads "199 passed". The messages come from
a check of scikit-learn that the tests run,
`check_positive_only_tag_during_fit`: there the new scan of the logarithm met
a form it could not evaluate. That was a fault of N2b, below.

## The fault of the scan of the logarithm, and correction L1 (16 November 2026)

Where an input column is negative throughout, a monomial of that column with
a fractional exponent is not a number. The scan of the logarithm of N2b
(`_elem_log_scan`) passed such a form to `np.linalg.lstsq`, which raised. The
try/except of the noise-tolerant stage then dropped every form of that pass,
the scans of the sine and the cosine included, and LAPACK printed its message
on the console. Two scripts, which decide nothing, measured it
(`m4/log_scan/`):
- `negative.py`: on noisy data whose first input column is negative
  throughout, six laws at 1 % and 10 % noise, a pass of N2b raised in 11
  cases of 12, and LAPACK printed its message 114 times. With the column
  positive, no pass raised.
- `count.py`: the 3,892 fits of M2, TP and TPT10, run again with 1.4.0 for
  one generation, which runs the noise-tolerant stage on the data of each
  fit. The stage runs in 3,562 of them (2,762 of the 3,092 of the benches,
  and the 800 of TP and TPT10), and no pass of N2b raises. The fault touched
  no fit of the measurements.

**A correction of the plan.** The amendment of the plan says of these fits
that all their inputs are positive. That is not so: the standardised real
datasets (R6, TR25) have negative values. The scans of N2b use only the input
columns that keep one sign, positive or negative throughout
(`_elementary_forms_n2` in `gp_elite/core.py`), so a column of mixed sign
never reaches them; the fault needs a column negative throughout. What the
count shows is that no pass raised on any of the 3,892 fits (first review of
M5).

The author decided to correct it and to check the corrected engine by a
targeted verification rather than run the measurements again
(`../PLAN_RELEASE_1.4.md`, "Correction L1 after M4", written before the
verification ran). L1 (ec44e8e) adds two lines to `_elem_log_scan`: a form
whose logarithm is not finite on the data is skipped. A test checks it on a
negative column (`test_l1_log_scan_skips_a_form_it_cannot_evaluate` in
`tests/test_guarantees.py`). The wheel and the source archive were built
again from ec44e8e, with the same version number, 1.4.0. `l1/environments.txt`
gives their SHA-256, `twine check --strict` passing for both, and the eleven
files of `gp_elite/`, identical in the wheel and in the environments to those
of the commit. `core.py` is the only one that differs from f6a36cd. The wheel
was installed in two fresh environments with the packages of `/venv14r` and
`/venv14rx`: `/venv14r2` and `/venv14r2x`.

`l1/verify.sh` runs the verification in three parts, from a copy of
`benchmarks/`, `examples/`, `tests/` and the READMEs of ec44e8e, without the
package beside them (`l1/verify.log`).

**Part a** (16 November, 20:56 to 22:09):
- **M1:** the thirteen reference configurations are those of the measured
  release, to the bit (`l1/M1_compare_release_vs_l1.txt`).
- **TP and TPT10:** the 800 models are those of 1.4.0 in M2, on every field of
  their records but the time, the date and the path of the engine
  (`l1/compare_tp_l1.py`, `l1/compare_tp_l1.txt`).
- **The 24 cases of `negative.py`:** no pass of N2b raises, and LAPACK prints
  nothing (`l1/negative_l1.txt`).
- **M4 again,** with fresh environments and the tests of ec44e8e: 200 tests
  pass under Python 3.9.25, 3.11.18 and 3.14.6, the test of L1 among them,
  and LAPACK prints nothing (`l1/m4_summary.txt`, `l1/m4_pytest_*.txt`,
  `l1/m4_requirements_*.txt`).

**Part b** (16 November, 22:09 to 22:55): the count run again with
`/venv14r2`. On the 3,892 fits, no pass of N2b raises and no fit crashes,
and job by job the records are those of the count of M4 with the measured
wheel: the same fits run the noise-tolerant stage (`l1/count_l1.jsonl`;
`l1/count_l1.txt` is `m4/log_scan/count.txt` to the byte).

**Part c** (17 November, 02:28 to 03:01, alone on the machine): M3 again
with `/venv14r2x`, the steps of `m3/m3_driver.sh` without the runs of 1.3.0
and the timing pair (`l1/m3/`). Against the M3 of the measured release
(`l1/m3_compare_release_vs_l1.txt`), 57 records are the same, the check of
`time_limit=` among them, and the four that differ differ by timing only:
- `claims_queues.txt`, the order in which the two queues ended;
- `console_hooke.txt`, the order of the islands' prints and the statistics
  of the stigmergic memory in the console example, whose result stays
  `force = 250 * elongation`, constant 250 kg/s²;
- `import_time.txt`, the times of the import;
- `scaling.txt`, the width of one time on its line, 9.5 s against 10.0 s,
  which the mask of the times leaves.

The console example's `gp_elite_best.txt` is that of the measured M3, and
its `gp_elite_log.csv` differs by the same timing; both were compared with
the copies the measured M3 left outside the repository, as in M3.

**The verification holds:** on every check of the amendment, the corrected
engine gives what the measured release gave, times aside. The measurements
of M2 and M3, and the figures of the documents, stand for it.
