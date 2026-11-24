# What size costs: the results

Part B of `../PLAN.md`. Written on 24 November 2026, after the last fit and
the profiles. It decides nothing about the engine: the author decides what
follows.

## The verdict

By the reading the plan wrote before the first fit (`compare_size.py`,
output in `reading.txt`), where E is the number of exact laws of a cell, of
205:

| axis | E at the reference, T | E at the largest size, T | L | E at the largest size, 10T | R | reading |
|---|---|---|---|---|---|---|
| rows | 165 (100 rows) | 154 (100,000 rows) | 11 | 160 | 6 | mostly brute force |
| variables | 168 (no added variable) | 108 (20 added) | 60 | 120 | 12 | mostly the algorithm |

- **Rows:** up to 100,000 rows, size costs little, and what it costs is
  mostly time. Both numbers are small: L = 11 is one fit above the
  threshold of 10, and R = 6 is half a fit above L / 2. The budget study of
  1.2 measured up to three fits between two campaigns of the same version.
- **Variables:** twenty added variables cost 60 exact laws of 205, and ten
  times the time gives back 12.

So, to the question of the plan: the number of rows is mostly a matter of
brute force, and costs little up to 100,000 rows; the number of variables
is mostly a matter of the algorithm, and costs much. The variables added
here are irrelevant to the law (distractors), drawn over the ranges of the
law's own variables.

## Where the exact laws come from

Most exact laws of F41 are found at the first generation, from the seeds
placed before it; the others are found by the search after it.

| cell | exact | at the first generation | after it |
|---|---|---|---|
| 100 rows | 165 | 150 | 15 |
| 1,000 rows (no added variable) | 168 | 150 | 18 |
| 10,000 rows | 161 | 150 | 11 |
| 100,000 rows | 154 | 150 | 4 |
| 100,000 rows, 10T | 160 | 150 | 10 |
| 5 added variables | 144 | 135 | 9 |
| 10 added variables | 139 | 130 | 9 |
| 20 added variables | 108 | 100 | 8 |
| 20 added variables, 10T | 120 | 100 | 20 |

- **Rows:** the seeds find the same 150 laws at every size, in the same
  fits (equation and seed). The loss is in the search, which found each of
  the laws lost at 100,000 rows after 2 to 136 generations at 100 rows. The
  fits that run to their budget reach a median of 116
  generations at 100 rows, 83 at 1,000, 31 at 10,000 and 3 at 100,000 (30
  at 100,000 with 10T).
- **Variables:** the seeds lose 15 of their 150 laws with 5 added
  variables, 20 with 10 and 50 with 20, and find no law they did not find
  without added variables; more time does not bring them back (100 at T
  and at 10T).
  The search runs as many generations as without added variables (a median
  of 89 against 83 for the fits that run to their budget; 708 at 10T), and
  finds 8 laws, 20 at 10T.

## How it was run

- **Engine:** 1.4.0 from PyPI in `/venv14p`. Its 11 files were checked
  identical to those of 6dc1e35 before the first fit and after the last
  (`engine_check_before.txt`, `engine_check_after.txt`).
- **Jobs:** `size_bench.py` at commit 2cb14bf: the 41 equations of F41,
  without noise, seeds 0 to 4, in nine cells, so 1,845 fits; one process per
  fit, `PYTHONHASHSEED=0`, one BLAS thread, four fits at a time on the four
  cores of one machine, the cells interleaved job by job. Python 3.11.18,
  NumPy 2.4.6.
- **Run:** from 21:11 UTC on 23 November to 01:23 UTC on 24 November, in
  three slices (`driver.sh`, `driver.log`), the records committed after each
  slice (`checkpoint.sh`). The container did not restart: one driver process
  ran from the first fit to the last.
- **Guard:** after the first slice, the median time of the first ten fits of
  each cell was 0.3 s to 5.3 s, far under twice the budgets.
- **Records:** 1,845 fits in `campaign.jsonl`, each job once, no crash, and
  every fit counted at least one generation.
- **Machine:** the processor did not change: the four `lscpu` written at the
  starts and the end (`machine_*.txt`) are identical.

## The figures

`reading.txt`:

| cell | exact | near | median generations | median time to the first generation (s) | elementary seed placed | tolerant seed placed | formula using an added variable | past the budget |
|---|---|---|---|---|---|---|---|---|
| 100 rows | 165 | 7 | 1 | 0.17 | 40 | 15 | - | 0 |
| 1,000 rows | 168 | 5 | 1 | 0.21 | 40 | 15 | - | 0 |
| 10,000 rows | 161 | 3 | 1 | 0.52 | 40 | 15 | - | 4 |
| 100,000 rows | 154 | 1 | 1 | 5.01 | 40 | 15 | - | 45 |
| 100,000 rows, 10T | 160 | 8 | 1 | 4.95 | 40 | 15 | - | 0 |
| 5 added | 144 | 23 | 1 | 0.28 | 35 | 25 | 12 | 0 |
| 10 added | 139 | 23 | 1 | 0.36 | 30 | 30 | 16 | 0 |
| 20 added | 108 | 41 | 15 | 0.54 | 30 | 55 | 26 | 0 |
| 20 added, 10T | 120 | 67 | 15 | 0.54 | 30 | 55 | 10 | 0 |

"Past the budget" counts the fits more than 10 % over their time limit.
`beside.txt`, from `beside.py`, written after the run and deciding nothing,
gives the rest: each equation cell by cell, the generations of the fits that
run to their budget, the formulas that use an added variable, how far past
the budget, and the time to the first generation.

## Beside, deciding nothing

- **Rows, the equations lost:** I.8.14 (4 of 5 seeds at 100 rows, 1 at
  100,000, 2 at 10T), II.2.42 (4, 0, 3), I.26.2 (3, 0, 0) and I.6.20a (4,
  3, 5). These are laws the search finds, not the seeds.
- **Rows, the time:** at 100,000 rows the setup and the seeds take a median
  of 5.0 s of the 30 s, and up to 32 s: five fits (four of I.11.19, one of
  III.9.52) reach their first generation after their budget. 45 fits end
  past their budget, by 8.1 s
  (median) and 16 s at most: the final choice runs after the deadline.
- **Variables, the equations lost:** ten equations exact in all five seeds
  without added variables fall to 0 or 1: I.27.6, I.44.4 and II.24.17 from
  5 added variables; III.15.12 from 10; I.10.7, I.15.10, I.34.1, II.11.3,
  II.11.27 and II.13.23 at 20. I.8.14 falls from 5 to 1 from 5 added
  variables.
- **Variables, the seeds:** the elementary seed is placed in 40 fits
  without added variables, 35 with 5, and 30 with 10 or 20. The tolerant
  seed, tried when neither the binomial nor the elementary seed finder
  returns a seed, is placed in 15, 25, 30 and 55.
- **Variables, why the seeds lose laws** (read after the run, in the
  records and the code, deciding nothing): of the 50 laws the seeds lose
  with 20 added variables, 40 were found without them by the binomial seed
  finder and 10 by the elementary one (with 5 added: 10 and 5; with 10: 10
  and 10). Both build a library of monomials of the columns (those of
  constant sign, here nearly all), and both cap it by the number of
  columns, to bound their time:
  - the binomial finder tries monomials of three columns only up to six
    columns, and gives up when its library passes 4,096 monomials, which
    happens from 23 columns;
  - the elementary finder tries monomials of three columns only up to
    eight columns.

  For example, the binomial finder returns I.34.1 with 3 and 13 columns
  and nothing with 23; it returns I.27.6, whose form needs the monomial
  `v1 / (v0 * v2)`, with 3 columns and nothing with 8.
- **Variables, the formulas:** 12, 16 and 26 returned formulas use an added
  variable at T, and 10 at 10T. Four of them count as exact (two with 5
  added variables, two with 20 at 10T): long expressions that match the
  test rows within the threshold, for example
  `0.398942 + 0.398942 * (0.0113922^(|0.33427 * v5|^...` for I.6.20a. The
  near fits grow from 5 to 23, 23 and 41, and to 67 at 10T.

## The profiles

`profile_size.py`, committed before it ran (6792460), deciding nothing:
three equations of F41, the first with two, four and six variables, at the
seven sizes, seed 0, 20 generations, no time limit, each fit run plain
(timed by phase) and under cProfile (own time by role of the map of
`core.py`). `profiles.txt` holds the tables; `profiles.jsonl` the records.
The plain and profiled runs return the same formula in all 21 pairs.

- **I.12.1** (`mu*Nn`): exact at the first generation at every size; 0.25 s
  at 100 rows, 4.7 s at 100,000, where evaluating formulas takes half of
  the profiled time.
- **I.8.14** (4 variables): 20 generations take 4.3 s at 100 rows, 7.0 s at
  1,000, 18.9 s at 10,000 and 163 s at 100,000. At 100,000 rows, the
  genetic operators take 59 % of the profiled time, and the largest own
  time of any function is that of the ε-lexicase selection (`select`, 50 s
  of 166 s), which walks the rows as cases.
- **I.11.19** (6 variables): 3.9 s at 100 rows, 300 s at 100,000, where 70 %
  of the profiled time is under the constant fitters (Levenberg-Marquardt on
  all the rows) and 35 % in the protected operators evaluating formulas.
- **With added variables** the time of a fit hardly grows (I.8.14: 4.4 s,
  3.9 s and 4.1 s with 5, 10 and 20), but the seeds take a growing share:
  under the seed makers, 59 % of the profiled time of I.8.14 with 20 added
  variables, against 7 % without (1,000 rows).

cProfile slows Python code more than NumPy code: a profiled fit takes 2.4
times its plain time at 100 rows and 1.05 times at 100,000, so the shares
lean to the Python side on small tables.

## Deviations

- **The profiles were cut once:** the worker of the session restarted
  between 01:28 and 01:32 UTC on 24 November, after the campaign, and the
  profile run stopped with it, at 21 of 42 records. It was resumed at 02:00
  UTC and skipped the recorded profiles; the fit running at the restart
  (I.8.14 at 100,000 rows, profiled) left no record and was run again. The
  container did not change: the records outside the repository were still
  there. Kernel at the profiles: 6.18.44-fc-v819.
- Nothing else: no crash, no restart of the container during the campaign,
  the same processor, the same engine before and after.

## What follows

The author decides. As the plan gives for example:
- **rows, brute force:** a cheaper evaluation on large tables, such as a
  sample of the rows during the search, planned and measured, GP_ELITE
  staying plain Python and NumPy. The profiles point to where the rows cost:
  the ε-lexicase selection, the fitting of constants and the evaluation.
- **variables, the algorithm:** the next plan starts from what the
  indicators show: the seeds no longer find a third of their laws once
  variables are added, and returned formulas take in irrelevant variables.

**The author's decision, 24 November 2026,** on three proposals put to the
study (screening the variables, a sample of the rows, lexicase by blocks
of rows):
1. 1.5 does not change: its plan promises the models of 1.4.0, bit for bit.
2. 1.6 takes the variables first, starting with the seed finders, by a
   plan whose criteria are written before any measurement, once 1.5 is
   done.
3. Then the rows, with a sample of the rows only above a number of rows,
   so that GP_ELITE stays the same, bit for bit, below it.
4. Lexicase by blocks of rows only if the sample does not suffice.

## Files

- `../PLAN.md`: the plan, Part B, validated before the first fit (gate 13).
- `size_bench.py`: the bench; `compare_size.py`: the reading, written before
  the run; `reading.txt`: its output.
- `beside.py`: written after the run, deciding nothing; `beside.txt`: its
  output.
- `profile_size.py`: the profiles, committed before they ran;
  `profiles.jsonl` and `profiles.txt`.
- `campaign.jsonl`: the 1,845 records.
- `driver.sh`, `checkpoint.sh`, `driver.log`, `machine_*.txt`: how the
  campaign was run, and the machine.
- `check_engine.sh`, `engine_check_before.txt`, `engine_check_after.txt`:
  the engine.
- `mechanics/`: the checks of the plan before the first fit.
