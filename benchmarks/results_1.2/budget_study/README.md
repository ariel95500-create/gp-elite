# What more time brings: the results

The study of `PLAN.md`, item 4 of `../../results_1.1/ROADMAP.md`. Written on
7 November 2026, after the last fit. It decides nothing about the engine:
the author decides what follows.

## The verdict

By the criteria the plan wrote before the first fit, between the arms T and
10T: **more time adds little.** None of the criteria holds.

| criterion (more time adds much if any holds) | T | 10T | holds |
|---|---|---|---|
| F41: at least 10 more exact laws (of 205) | 163 | 164 | no |
| U41: at least 10 more exact laws (of 205) | 165 | 169 | no |
| F41N1: at least 10 more structures (of 205) | 108 | 111 | no |
| F41N10: at least 10 more structures (of 205) | 85 | 90 | no |
| R6 folds: median test R² at least 0.01 higher | 0.8126 | 0.8126 | no |

Given ten times the time, 1.2.0 returns at most five more models of 205 on
any deciding suite. So, as the plan reads it, a faster engine would add
little, and the work stays on the search itself.

## How it was run

- **Engine:** 1.2.0 from PyPI in `/venv12p`. Its 11 files in `gp_elite/` were
  checked identical to those of the wheel measured for the release
  (`052ee69a…`, `../release/environments.txt`), before the first fit and
  again after the last.
- **Jobs:** the bench of `../../phase1_bench.py` at commit b09d293, with
  `--budget-factors 1,3,10`, one process per fit, `PYTHONHASHSEED=0`, four
  fits at a time on the four cores of one machine.
- **Run:** from 11:53 UTC on 6 November 2026 to 13:44 UTC on 7 November, in
  slices of 6,300 s (`driver.sh`, `driver.log`).
- **Records:** 4,020 fits, the same 1,340 jobs in each arm (`campaign.jsonl`).
  No broken line, no job twice, no crash. All 1,340 triples (a job at T, 3T
  and 10T) are complete.
- **Budgets:** the median time of a fit is 30.3 s, 90.3 s and 300.3 s.
  The median generations of the noisy fits are 115, 320 and 1,020 on
  F41N1, and 103, 287 and 907 on F41N10.
- **Generations and the clock:** in the engine of 1.2.0 with
  `parallel=False`, as far as the code read shows, the number of generations
  does only two things. It bounds the loop, and it keeps the restart of the
  explorer islands out of the last 50 generations. The clock enters only
  through the deadline. So raising the generations with the budget, as the
  plan does, changes nothing in a fit but the moment it stops.

## The figures

`compare_budget.txt`, from `compare_budget.py`, written before the run:

| indicator | T | 3T | 10T |
|---|---|---|---|
| F41 exact | 163 | 160 | 164 |
| U41 exact | 165 | 167 | 169 |
| F41N1 structure retrieved | 108 | 110 | 111 |
| F41N10 structure retrieved | 85 | 87 | 90 |
| R6 folds median R² | 0.8126 | 0.8126 | 0.8126 |
| R6 + R7raw out-of-domain collapses | 10 | 16 | 22 |
| TF78 exact (reported, deciding nothing) | 214 | 227 | 233 |
| fits at the time budget | 803 | 780 | 758 |
| noisy and real fits, median size | 15 | 16 | 16 |

The arm T returns what the M2 of the release measured at the same budget,
on a processor of the same name. F41 has 163 exact laws in both. U41 has 165
against 166, and the median R² of R6 is 0.8126 against 0.8095. That is
within what a time budget moves from one campaign to the next.

## What changes from T to 10T

- **F41:** 158 fits are exact at both budgets. Six become exact at 10T:
  - I.11.19, 1 seed to 3;
  - II.2.42, 4 to 5;
  - III.17.37, 0 to 3.

  Five are lost, all five seeds of I.8.14. The arm 3T has three fewer exact
  laws than T, so the count does not grow steadily with the time.
- **I.8.14, exact at T and lost with more time:** at T the five seeds return
  `4.98212 * sqrt(0.0402876 * (v2 - v3)² + 0.0402876 * (v1 - v0)²)`, the
  law. At 3T and 10T they return the same structure written with a separate
  coefficient for each variable and an offset, for example
  `0.00110682 + 4.97878 * sqrt((0.20002 * v2 - 0.201187 * v3)² + (0.201046 * v1 - 0.200601 * v0)²)`,
  which is near but not exact. These constants are the same in several seeds.
  The final selection of 1.2.0 chooses among candidates tracked during the
  run, polished, then compared on the hold-out. A longer run tracks more of
  them, which may be how a near formula comes to win. That is a hypothesis;
  this study does not test it.
- **U41:** no law exact at T is lost. Four fits become exact: I.11.19
  (1 to 3), I.16.6 (4 to 5) and I.37.4 (0 to 1).
- **F41N1 and F41N10:** no structure retrieved at T is lost. Three and five
  more are retrieved at 10T.
- **R6 folds:** of the 30 folds, 15 return the same model at all three
  budgets. Among the other 15, 12 rise and 3 fall. Both folds at the median
  (228_elusage fold 2, 712_chscase_geyser1 fold 4) return the same model at
  every budget, so the median does not move. The mean of the folds rises
  from 0.7763 to 0.7873. The plan decides on the median, not the mean.

## Beside, deciding nothing

- **Collapses out of domain:** these are fits with R² below zero on the 20 %
  of rows farthest from the centre, in R6 and R7raw together. They grow with
  the time, from 10 to 16 to 22:
  - 228_elusage, 7 to 9;
  - 210_cloud, 2 to 5;
  - 561_cpu, 0 to 5;
  - 547_no2 and 690_visualizing_galaxy, 0 to 1 each.

  As the plan suspected, more time fits the training range more closely and
  collapses more outside it.
- **TF78, the frozen test set:** 214, 227 and 233 exact laws. No law exact
  at T is lost, and 19 fits become exact on nine equations. This set decides
  nothing.
- **Sizes:** the median size of the noisy and real formulas grows from 15
  to 16.

## Deviations

- **Restarts of the container:** it restarted four times during the run:
  - between 15:59 and 17:51 UTC on 6 November;
  - between 19:52 and 20:01;
  - at 21:05;
  - at 02:52 on 7 November.

  Each time the records were checked whole and the driver was started again.
  The fits running at the restart left no record and were run again. Each
  restart is noted in `driver.log`. About two hours were lost, most of them
  at the first restart.
- **Processor:** the processor did not change. The `lscpu` written at each
  start (`machine_*.txt`, five files) is the same every time.
- **Kernel:** the kernel of the container changed twice. It was
  6.18.44-fc-v242 when the session began, 6.18.44-fc-v260 after the restart
  of 21:05, and 6.18.44-fc-v310 after that of 02:52. It was not read at the
  first two restarts, so the first period counts as fc-v242 as far as is
  known.
- **Fits on each kernel:** `by_kernel.py`, written after the change and
  deciding nothing, gives the fits run on each kernel (`by_kernel.txt`):

  | kernel | T | 3T | 10T |
  |---|---|---|---|
  | fc-v242 | 565 | 564 | 562 |
  | fc-v260 | 250 | 250 | 250 |
  | fc-v310 | 525 | 526 | 528 |

  - 1,334 of the 1,340 triples ran wholly on one kernel. The other six were
    split by a restart: three of I.15.10 in F41N1 and three of
    feynman_I_34_14 in TF78.
  - On the 1,334 triples within one kernel, the criteria read the same
    figures: F41 163 to 164, U41 165 to 169, F41N10 85 to 90, R6 0.8126 to
    0.8126. F41N1 is 108 to 111 of 202, against 205 on all triples.

## What follows

As the plan and the roadmap say:
- if more time adds little, a faster engine would add little;
- a plan for an optional accelerator is not called for by these figures;
- the work stays on the search itself.

The figures point to two places for that work, for the author to weigh:
- the final selection, which loses I.8.14 when the run is longer;
- the collapses out of domain, which grow with the time.

The author decides what comes next.

## Files

- `PLAN.md`: the plan, committed before the first fit.
- `compare_budget.py`: written before the run; `compare_budget.txt` is its
  output.
- `by_kernel.py`: written after the kernel change; `by_kernel.txt` is its
  output.
- `campaign.jsonl`: the 4,020 records. Each carries its `budget_factor`.
- `driver.sh`, `checkpoint.sh`, `driver.log` and `machine_*.txt`: how the
  campaign was run, and the machine.
- `mechanics/`: the checks before the first fit, A (without the option) and
  B (with the factors).
