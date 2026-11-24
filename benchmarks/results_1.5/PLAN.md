# Plan of version 1.5: the engine in modules, and what size costs

Written on 23 November 2026, the day 1.4.0 was published, before any change
to the engine and before any measurement of this phase. Method as before:
- one process per fit, `PYTHONHASHSEED=0`, one BLAS thread;
- the criteria are written here before the measurement they judge;
- the frozen test sets are never used to decide;
- times are compared only between fits run on the same machine, in the same
  campaign;
- every deviation from this plan goes to the author.

The author validates this plan before any change (gate 13), and decides the
publication of 1.5 after its measurement (gate 14).

Gate 13: the author validated this plan in full on 23 November 2026.

Amendment of 24 November 2026, approved by the author before any move:
- the map of `core.py` (`split/map.txt`, made again in c7e00fa by the
  script corrected in 81ed9c3) counts 66 run-time names, not the 45 of the first reading given under
  "The shared state": 44 rebound by core's own functions (through `global`
  or through `globals()`), 12 set on `core` by the package and 32 by the
  tests; 61 hold data, and 5 are functions of `core.py` that the tests
  replace;
- the order of steps 2 and 3 under "How" changes: the shared state goes
  first to its own module, every function still in `core.py`, in one
  commit checked by the short version of A1; then every group moves, each
  move a plain move, checked the same way. The criteria do not change.

## What 1.5 has to do

The strategic plan the author approved on 23 November 2026 puts the split of
the engine first: `gp_elite/core.py` holds 12,999 lines, and the reviewers of
a journal such as JOSS read the code. The same day the author asked a
question: why is GP_ELITE effective on small tables only, and is that a
matter of brute force or of the algorithm? So 1.5 has two parts, in this
order of work:
- **Part B, what size costs:** a diagnostic. Beyond the range where GP_ELITE
  is measured, does it lose laws as the data grows, in rows or in
  variables, and does ten times the time give them back? It changes nothing
  in the engine and decides nothing about it.
- **Part A, the engine in modules:** `core.py` split into modules, without a
  single result changed.

Part B runs first because it needs the machine alone for about half a day;
the first step of Part A, the map below, needs none.

Not in 1.5:
- any change to the search, to the seeds or to the final choice;
- the work on small noisy tables, which follows, informed by Part B;
- a faster engine or code in another language;
- the submission to JOSS, after 1.5.0 is published.

## What is already known

Within the measured range, more computing does not bring more laws:
- **campaign 1 of 0.8** (`../results_0.8/RESULTS.md`, H3 refuted): twice
  the generations in the same time, 64 exact laws of 205 either way;
- **the budget study of 1.2** (`../results_1.2/budget_study/`): ten times
  the time, at most five more models of 205 on any deciding suite (F41, 163
  and 164 exact laws), the same median R² on the real data, and more
  collapses out of domain (10 and 22);
- **the end of the search, 1.2** (`../results_1.2/end_of_search/`): of 40
  near fits, 35 never had a candidate the polish makes exact.

The size study (`../feynman_scaling.py`, measured again with 1.4.0,
`docs/measurements.md`) returns the exact law of four of its five Feynman
equations at every size from 25 to 10,000 rows. Beyond 10,000 rows and about ten variables nothing
is measured (`LIMITATIONS.md`, point 9). The phrase of the README that PySR
and Operon serve large data better rests on their published results, not on
a measurement of this project.

## Part B: what size costs

### The question

Beyond its measured range, does GP_ELITE return fewer exact laws as the
data grows, in rows or in variables? Where it does, does ten times the time
give them back (then a faster engine would help: brute force), or not (then
the algorithm is what limits)?

### The engine

1.4.0 installed from PyPI (`/venv14p`). Its 11 files in `gp_elite/` are
checked identical to those of `main` at the merge of 1.4.0 before the first
fit and again after the last; if they are not, the study stops and the
author is told. Part A returns the same models at equal work, so what Part B
finds holds for 1.5.

### The data

The 41 equations of F41 (`../feynman_bench.py`): their samplers, their laws,
their pools of operators, no noise. For each equation and each size, one
draw of the data, seeded by the equation and the size, the same for every
budget and every seed of the fit: n training rows, and 1,000 test rows drawn
the same way.

- **Rows:** n = 100, 1,000, 10,000 and 100,000, no variable added.
- **Variables:** n = 1,000, and k = 0, 5, 10 and 20 variables added, which
  take no part in the law. The added column j is drawn uniformly over the
  range of the equation's variable j modulo its number of variables, and the
  columns are put in an order drawn for the equation, so that the variables
  of the law are not always the first. The columns are named v0, v1, ….
  F41 has equations of 1 to 6 variables (1, 8, 15, 11, 4 and 2 of them), so
  with 20 added a table has 21 to 26 columns.

### The arms

| arm | `time_limit` | `generations` |
|---|---|---|
| T | 30 s | 1,000 |
| 10T | 300 s | 10,000 |

As in the budget study, the time is the bound. Each fit: `parallel=False`,
one restart, the pool of operators of its equation, seeds 0 to 4. The cells,
205 fits each:
- rows: T at 100, 1,000, 10,000 and 100,000 rows, and 10T at 100,000;
- variables: T at k = 0 (the cell of 1,000 rows above), 5, 10 and 20, and
  10T at k = 20.

Nine cells, 1,845 fits. Cost: about 12 hours of fits at T and 34 at 10T,
four at a time, so about half a day, more if fits run past their budget
(the final choice and its polish run after the deadline, and the seeds are
placed before the first generation). Guard: the first ten fits of each cell
are timed, and if their median passes twice the budget, the author is told
before the campaign goes on.

### How it is run

A bench script in this folder, `size/size_bench.py`, builds the data above
and runs each fit as `../phase1_bench.py` does (`run_one`): the same count
of generations through `evolve_island`, the same status on the test rows
(EXACT if 1 − R² is below 1e-9, NEAR below 1e-3, MISS otherwise), the same
fields. It also records:
- the time from the start of the fit to its first generation, which is the
  setup and the placing of the seeds;
- the seeds the fit placed, as `phase1_bench.py` records them;
- whether the model returned uses an added variable.

One process per fit, `PYTHONHASHSEED=0`, one BLAS thread, four fits at a
time on the four cores of one machine. The cells are interleaved job by job,
so that they share the load and any change of the machine. The run resumes,
in slices under two hours; `lscpu` is recorded at each slice, and if the
processor changes, the author is told before the results are read. While
the campaign runs, no other measurement or test runs on the machine.

Checked before the first fit: the data of three jobs (their sizes, the
added columns, their ranges and order), and three fits, which must record a
count of generations above zero and a time to the first generation.

After the campaign, deciding nothing: three equations of F41, the first with
two, four and six variables, are profiled at each size of each axis
(`cProfile`, 20 generations, one fit each), for the share of the time spent
evaluating formulas, fitting constants, placing seeds and in the final
choice.

### What is read, and what it means

Written before the first fit. E(cell) is the number of exact laws of a cell,
of 205. For each axis, between its reference (100 rows; k = 0) and its
largest size (100,000 rows; k = 20):
- the loss at T: L = E(reference, T) − E(largest, T);
- what ten times the time gives back: R = E(largest, 10T) − E(largest, T).

| result | reading |
|---|---|
| L below 10 | up to that size, size costs little on this axis |
| L at least 10, R at least L / 2 | mostly brute force: a faster engine would give back most of what size costs |
| L at least 10, R below L / 4 | mostly the algorithm: more time does not give it back |
| otherwise | both |

Ten fits of 205 is the threshold of the budget study: two equations in all
five seeds, and more than what a time budget moves between two campaigns of
the same version (at most three fits on these suites).

Reported beside, deciding nothing: E at every size, so where a loss starts;
the generations reached; the time to the first generation; the seeds
placed; the models that use an added variable; the near fits; the fits past
their budget; and the profiles.

What follows is the author's decision, for example:
- **brute force:** a cheaper evaluation on large tables, such as a sample of
  the rows during the search, is planned and measured, GP_ELITE staying
  plain Python and NumPy;
- **the algorithm:** the next plan starts from what the indicators show, for
  example seeds no longer placed once variables are added;
- **size costs little:** the limits page can state a wider measured range.

## Part A: the engine in modules

### Why

`core.py` is one file of 12,999 lines: 231 functions and classes, from the
tree of a formula to the interactive console. That is hard to read, to
review and to change safely. The split changes how the code is organised,
and nothing that a user, a bench or a test can observe.

### What does not change

- **Every result:** at equal seed and equal work, the engine of 1.5 returns
  the model 1.4.0 returns, bit for bit: the tree with its constants, the
  printed formula, the errors, the size, `formula_exact`, the Pareto front.
- **The interface:** what `gp_elite` exports, its arguments and defaults,
  the scikit-learn estimator, the console.
- **`gp_elite.core` as a door:** every name it has in 1.4.0 can still be
  read on it, and a name that changes at run time, set on it, still sets the
  engine's. The benches and scripts of earlier phases read and set some of
  them.
- **The dependencies:** Python and NumPy.
- **The speed** (criterion A3).

### The shared state

By a first reading of its syntax tree (the map below gives the exact
count), 45 module-level names of `core.py` change at run time: 37 are
rebound by its own functions (`global`), 16 are set on `core` from outside,
12 of them by the other modules of the package and the rest by the tests
(8 names are both). 63 of the 231 functions and classes use them (5,487
lines); the other 168 (5,203 lines) do not. Moved naively, a function would read a copy
of such a name, taken at import, and the engine would change without an
error.

So these names live in one module, which every function that reads or sets
them reads and sets at the moment it runs, never through a copy; and every
assignment from outside goes to that module, `gp_elite.core` passing on to
it the names set on it.

### How

1. **The map, before any move.** A script reads `core.py` (its syntax tree,
   without running it) and lists, for each function and class: its lines,
   the run-time names it reads and those it sets, and where it would go. The
   script and its output are committed before the first move.
2. **The functions free of run-time state move first,** into modules by
   role: the tree of a formula and its text, the protected operators, the
   evaluation, the seed finders, the fragment memory, the fitting of
   constants, the simplification, the genetic operators. `core.py` imports
   them back, so its names do not change.
3. **Then the shared state** goes to its own module, and the rest by role:
   the islands and the search loop, the final choice, the loading of data,
   the console. `core.py` ends as the door: it gives every name of 1.4.0 and
   holds no engine code. A module of more than about 2,000 lines is the
   exception, and is said; the longest functions (the search loop, 741
   lines; the console menu, 813) move whole, since cutting a function is a
   change of code, not a move.
4. **One commit per group moved,** each checked by the short version of A1
   before the next, so that a difference points to its commit.
5. **A page on the architecture** for contributors, in both languages: the
   modules, what each holds, where the shared state lives.

The benches wrap internal functions: `phase1_bench.py` and
`tp_diagnostic.py` count the generations by wrapping `core.evolve_island`. A
wrap set on `core` reaches only the calls made through `core`. So each bench
that wraps a function wraps it where it lives, and checks after each fit
that its wrap was called (a count of generations above zero); otherwise the
fit is recorded as broken and the run stops. The scripts and records of
earlier phases are not touched: they ran on their own engines.

### The criteria of the split, all of which must hold

- **A1, the same models.** Against 1.4.0 from PyPI, field by field, every
  field but the time, the date and the path and version of the engine:
  - the 13 configurations of `../speed_equivalence.py` (Feynman data, a
    real dataset, 5,000 rows, units, the normalisations, the robust loss,
    restarts, parallel islands, the estimator, extrapolation, the thorough
    preset, two fits in one process);
  - F41, U41 and F41N1 with the defaults of the API, which stop on a number
    of generations and not on the clock (`../phase1_bench.py --defaults`,
    615 fits);
  - the TP diagnostic (`../tp_diagnostic.py`, 400 fits, run with the
    defaults);
  - the console in its generic CSV mode, run by a script that answers its
    questions: the formula it prints and writes, and its errors.

  Without a time limit, the engine reads the clock only to record how long
  steps take, so these runs are deterministic. The short version, after each
  commit: the 13 configurations and F41 with the defaults. A difference is
  not explained away: if 1.4.0 run twice gives it too, it is reported as
  such; otherwise the move that caused it is corrected or undone.
- **A2, the tests.** The test suite passes under Python 3.9, 3.11 and 3.14
  on the machine, and on the matrix of the CI (3.9 to 3.14 on Ubuntu, 3.12
  and 3.14 on Windows).
- **A3, the speed.** F41 with the defaults, run with each engine one fit at
  a time, the two engines interleaved fit by fit in one campaign on one
  machine: the total time of 1.5 within 3 % of that of 1.4.0. The import
  time of `gp_elite` is reported beside (median of 20). If A3 fails, the
  cause is found and corrected, and A1 is run again.
- **A4, the door.** A test lists the names of `gp_elite.core` in 1.4.0
  (from the wheel, committed as a file) and checks that each can be read on
  the engine of 1.5; and that each run-time name, set on `gp_elite.core`,
  reaches the engine.

## The release of 1.5.0

If Part A holds, 1.5.0 is the engine of 1.4.0 in modules: the same models
at equal work, the same speed within 3 %. Before gate 14:
- **M1:** A1, A3 and A4 on the wheel built for the release, installed in a
  fresh environment, against 1.4.0 from PyPI;
- **documents:** the CHANGELOG, the page on the architecture, the pages it
  touches; the figures of the measurement of 1.4.0 stay, said to be of
  1.4.0, since 1.5.0 returns the same models; what Part B found goes where
  it informs, such as point 9 of the limits;
- **M4:** the test suite and the CI as in A2; `twine check --strict`;
- **M5:** two independent reviews, as since 0.9: the claims of the documents
  against the records, and the split itself (is any behaviour changed, does
  the rule of the shared state hold everywhere);
- **gate 14:** the author decides the publication, its name and its date.

No campaign at a time budget (the M2 and M3 of earlier releases): at equal
work the models are the same and the speed is within 3 %, so such a
campaign would measure only the noise of a time budget. If the speed cannot
be kept within 3 %, a campaign is put to the author.

## Records

- `size/`: the bench script, the comparison script written before the run
  (it reads the criteria above; tested on made-up records, where it gives
  back the known answers), the campaign records, the driver and its log, the
  machine, the profiles, and a README with the figures, written after the
  run.
- `split/`: the script of the map and its output, the runs of A1 and their
  comparisons, the timings of A3, the list of names of A4.
