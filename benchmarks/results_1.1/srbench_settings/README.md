# The settings SRBench runs GP_ELITE with: results

Measured from 2 November 2026, 18:42 UTC, to 3 November 2026, 16:44 UTC, as
`PLAN.md` and its amendment say: gp-elite 1.1.0 from PyPI (`/venv11p`), the
745 jobs of the decision bench, each run with the two settings at the same
time, B = 300 s, two jobs at a time on four cores, `PYTHONHASHSEED=0`, one BLAS
thread. The records are `run/W0.jsonl` and `run/W1.jsonl`; the runner wrote
`run/driver.log`; `compare.txt` is the output of `compare.py run`.

## The result: W0 stays

| figure | W0, the wrapper as published | W1, one call with ten restarts |
|---|---|---|
| fits, crashes | 745, 0 | 745, 0 |
| F41 exact laws | 155 | 155 |
| F41N1 structures | 95 | 91 |
| F41N10 structures | 69 | 73 |
| R6 folds, median test R² | 0.8292 | 0.8319 |
| R6 + R7raw, collapses out of domain | 23 | 23 |
| R6 + R7raw folds, median size | 34 | 32 |

Criteria of `PLAN.md`, S = W1: five of the six conditions on losses hold, one
does not (F41N1 structures, 91 against 95, fewer than W0's minus 3), and there
is no gain (F41 exact laws +0, structures 164 against 164, R6 median R²
+0.0027 where +0.01 was asked). W1 is not better than W0: the wrapper as
published stays. No setting being chosen, the final check on the datasets of
SRBench 2025, planned only for a chosen setting, is not run.

## What the two settings differ by

Reading the code while writing this record (`gp_elite/api.py` of 1.1.0, lines
738 to 795; the wrapper at 2aabbb6, lines 89 to 110): the ten calls of the
wrapper and the ten restarts of one call use the same seeds (`seed + 1000 k`,
k = 0 to 9), the same validation rows (the engine draws them with a fixed seed
of its own) and the same sharing of time (each run gets an equal share of what
is left of 90 % of the budget). What differs is the final choice: the wrapper
keeps the call whose model has the best validation R²; the engine merges the
candidates of its ten runs, polishes the finalists and applies its rule of one
standard error. The study therefore measured that choice, question 2 of
`PLAN.md`, and found no difference that its criteria count.

Paired, fit by fit:
- F41: the same 155 fits are exact with both settings, and W0 and W1 return the
  same expression (its first 160 characters, as recorded) in 139 of
  the 205 fits.
- F41N1: structure retrieved by both in 90 fits, by W0 only in 5 (three seeds
  of II.24.17, one of I.27.6 and one of I.32.5), by W1 only in 1 (I.32.5).
- F41N10: by both in 61, by W0 only in 8 (the five seeds of I.25.13 among
  them), by W1 only in 12.
- R6 folds: W1's test R² is higher in 17 folds, equal in 3, lower in 10, by a
  median of +0.0005. R7raw folds: 19, 1 and 15, median +0.0001.
- Out of domain, the collapses fall on mostly the same fits: R6, 7 with both,
  3 with W0 only, 2 with W1 only; R7raw, 10, 3 and 4.
- Time: the exact laws of F41 take a median of 6.9 s with W0 and 5.9 s with
  W1, ten calls against one; elsewhere both use the same time (medians of
  194 s and 196 s on R6, 273 s on the noisy laws).

## F41, law by law (a diagnostic, deciding nothing)

`feyn_by_law.py` (output `feyn_by_law.txt`) sets the 41 laws beside the M2
campaign of 1.1.0 in `../release/` (B = 30 s, one call of 1,000 generations,
the pool of each problem). Nine laws are never exact here, with either
setting. Eight of them hold a sine or a cosine (one an arcsine of a sine), and
the operators `physical` SRBench gives GP_ELITE hold neither: no budget can
write those laws, only approximate them. Three of the eight (II.15.4,
II.6.15b, III.15.12) are exact in all five fits of M2, in under a second,
where the pool of the bench holds sine and cosine. Six laws are exact in
neither condition: five with a sine or a cosine, and III.10.19,
`mom*sqrt(Bx^2+By^2+Bz^2)`, in 50 independent runs here (five fits of ten
runs) with no fit exact. One law with a sine counted exact here, I.18.12
(`r*F*sin(th)`), is matched by formulas of 37 to 69 nodes that imitate the
sine to the precision of the machine on the range of the data, not by the law.

By group of laws (the end of `feyn_by_law.txt`), on the 31 laws without a
sine or a cosine the settings of SRBench at 300 s and 1.1.0 in M2 at 30 s give
nearly the same counts: 148 exact fits for W0 and W1 against 143, structures
95 and 91 against 93 at 1 % noise, 69 and 73 against 71 at 10 %. The whole gap
of F41 is on the 10 laws with a sine or a cosine: 7 exact fits against 20, and
no structure under noise against 15 and 15.

About 30 of the 155 exact fits come at the end of a run of 200 s or more
(for instance I.11.19, II.2.42, I.8.14, I.16.6); the records give the time of
the fit, not the moment the law appeared in it.

## Beside the release bench (an observation, deciding nothing)

On the same real datasets, the M2 campaign of 1.1.0 (30 s, one call of 1,000
generations) gives 10 collapses out of domain on R6 + R7raw, a median size of
13 on their folds and a median test R² of 0.8095 on the R6 folds. Both
settings here give 23 collapses, sizes of 34 and 32, and R² of 0.829 and 0.832:
larger models, slightly better within the domain, worse beyond it. The two
conditions differ in several ways at once (budget, generations per run, ten
runs, `speed="fast"`), so no cause is drawn here. It is recorded for the
measurement of what more time brings, planned after 1.2 (`../ROADMAP.md`).

## The grid of the wrapper

`PLAN.md` records that the grid `hyper_params` of the wrapper is read by
`optimize_model.py` of SRBench 2025 as one configuration, so that no tuning
runs. Reading that file again for this record (branch `srbench_2025` at
dc3f6da, lines 291 to 341): when a method lists at least two configurations,
`GridSearchCV` fits each of them and the default with 3 folds, each fit given
`max_time = fit_time_limit` (3,600 s), under one alarm of
(3,600 + 600) s times the number of configurations; when the alarm rings,
SRBench keeps the default settings. With the four configurations the grid
means to give, 15 fits share 16,800 s, about 19 minutes each; with two, 9 fits
share 8,400 s, about 16 minutes. How long the wrapper takes at 3,600 s on the
datasets of SRBench is not known here (at B = 300 s it used 194 s on R6 and
273 s on the noisy laws). Written as intended, the grid would therefore tune
only if the fits end early enough; otherwise it would cost hours per run and
change nothing. Whether to propose it is put to the author with this record.

The author chose on 3 November 2026 not to propose it for now: SRBench fits
the default `est`, which this study keeps. The question on the calendar of
SRBench, drafted on 28 October, had already been sent by the author in the
week of 26 October, without the grid; nothing more is sent.

## Departures from the plan

- The container restarted at about 01:10 UTC on 3 November. The records
  were intact and paired (338 jobs per setting); the two jobs in progress were
  lost with both their settings and ran again, side by side, when the run
  resumed at 01:11 UTC (`run/driver.log`, line 26). The machine was not
  recorded at the start of the run; `run/machine.txt` records it from the
  resume: 4 cores, Intel Xeon at 2.80 GHz, AVX-512. A second restart of the
  session, at about 14:00 UTC, did not stop the run: no gap of more than
  600 s between records, and no fit longer than 288 s.
- The text of the final check in `PLAN.md` still says B = 120 s, written
  before the amendment; the check is not run.
