# What more time brings: plan written before any measurement

Written on 5 November 2026, after gate 8 of 1.2 and before 1.2.0 is on
PyPI. It is item 4 of `../../results_1.1/ROADMAP.md`, decided by the author on
27 October 2026: before any code is written in another language, the engine
of the day is measured with more time, which costs no rewrite, since a faster
engine does in 30 s what this one does in 300 s. Nothing here starts before
1.2.0 is published; this plan is committed before the first fit. Method as
before:
- one process per fit, `PYTHONHASHSEED=0`, one BLAS thread;
- the frozen test set decides nothing;
- times and budgets are compared only within this campaign, on one machine;
- every deviation goes to the author;
- the study decides nothing about the engine: the author decides what
  follows.

## The question

If GP_ELITE ran ten times faster, would it return better models on the
benches the project decides on? A faster engine is not built to answer
that: the engine of 1.2.0 is given ten times, and three times, the budget
of the bench, and what it returns is compared with what it returns at the
usual budget, in the same campaign.

This reads a faster engine as one that does in T what 1.2.0 does in 10 T.
That holds for a speed-up spread evenly over the search. It does not hold
for one that would change the search itself, which is not measured here.

## The engine

1.2.0 installed from PyPI in a fresh environment (`/venv12p`), with the
packages of `/venv12b`. Its `gp_elite/` files are checked identical to those
of the wheel measured for the release (`../release/environments.txt`); if they
are not, the study stops and the author is told.

## The arms

The bench of phase 1 (`../../phase1_bench.py`), which runs each fit with
`time_limit=30` and `generations=1000`, `parallel=False`, one restart. At
30 s a fit with noise reaches a median of 91 to 124 generations (the M2 of
1.2.0), so at 300 s it would reach the cap of 1,000; the generations are
raised with the budget, so that the time stays the bound:

| arm | `time_limit` | `generations` |
|---|---|---|
| T | 30 s | 1,000 |
| 3T | 90 s | 3,000 |
| 10T | 300 s | 10,000 |

The bench gets an option `--budget-factors 1,3,10`: every job runs once per
factor k, with `time_limit` 30 k and `generations` 1,000 k, and each job and
record carries its `budget_factor`. Checked before the first fit:
- without the option the jobs are those of before (done on 5 November 2026
  on a copy of the bench: the 1,775 and 2,780 jobs and their keys identical),
  and three jobs run with 1.2.0 return the models of the M2 of the release
  where neither run reached the budget;
- with it, three jobs run with each factor record the budget asked, and
  reach more generations as the factor grows.

## The suites

Decide, seeds 0 to 4, as in the campaigns of 1.2:
- F41, the 41 Feynman equations (205 fits): exact laws;
- U41, the same with their units (205): exact laws;
- F41N1 and F41N10, F41 with 1 % and 10 % noise (205 each): structure
  retrieved;
- R6 and R7raw, the real data, six standardised datasets and seven in their
  own units (60 and 70 fits): the median test R² of the R6 folds, and the
  collapses out of domain of R6 and R7raw together (R² below zero on the
  20 % of rows farthest from the centre).

Reported, deciding nothing: TF78, the 78 Feynman equations of the frozen
test set, seeds 5 to 9 (390 fits), exact laws. The other suites of the
frozen test set (TS14, TR25, TR25raw) are left out: almost every fit reaches
its budget there, and they would add about ten hours at 10T for a figure
that decides nothing.

Each arm runs the same 1,340 jobs (950 deciding, 390 reported).

## How it is run

The three arms in one campaign, on one machine, four fits at a time on its
four cores. The jobs of the three arms are run interleaved, job by job, in a
fixed order (a job and its three budgets one after the other), so that the
arms share the load and any change of the machine. The run resumes, in
slices under two hours. `lscpu` is recorded at each slice; if the processor
changes during the campaign, the author is told before the results are read,
and the jobs run on each processor are given apart.

Cost, from the fits that reached their budget in the M2 of 1.2.0 (629 of the
950 deciding fits, 173 of TF78): about 18 hours for the deciding suites and
5 more for TF78, about a day in all.

## What is read, and what it means

For each arm: the exact laws of F41, U41 and TF78; the structures of F41N1
and F41N10; the median test R² of the R6 folds; the collapses out of domain
of R6 + R7raw; the generations reached; the time; the sizes; and the
equations that gain or lose exact fits between T and 10T.

Written before the first fit, between the arms T and 10T:

**More time adds much** if any of these holds:
- F41: at least 10 more exact laws (of 205);
- U41: at least 10 more exact laws;
- F41N1 or F41N10: at least 10 more structures;
- R6 folds: the median test R² at least 0.01 higher.

**More time adds little** if none holds.

Ten fits of 205 is two equations gained in all five seeds, or 5 % of the
bench: below it, a gain is within reach of what a time budget moves from one
campaign to the next (at most 3 fits on these suites, for the same version,
between the campaigns of the releases of 1.0, 1.1 and 1.2). The arm 3T says how the gain grows: half of it already at 3T, say, is
another story than all of it only at 10T.

Reported beside, deciding nothing: the collapses out of domain (more time
could fit the training range more closely and collapse more outside it),
the sizes of the formulas, and TF78.

What follows, as the roadmap says:
- if more time adds little, a faster engine would add little, and the work
  stays on the search itself;
- if it adds much, a plan for an optional accelerator is put to the author:
  installed only by those who want it, inside the same package, GP_ELITE
  staying pure Python and NumPy without it, with tests proving that both
  return the same models. A separate second tool is not recommended.

Either way the author decides at each step.

## Records

`budget_study/`: the campaign record (`campaign.jsonl`, the three arms told
apart by `budget_factor`), the driver and its log, the machine, the
comparison script written before the run (`compare_budget.py`, which reads
the criteria above; tested on the records of M2 of the release copied into
three identical arms, where it gives back their figures and "adds little")
and its output, and a README with the figures, written after the run.
