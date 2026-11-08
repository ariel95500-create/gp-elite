# Where the end of the search loses exact laws: the results

The diagnostic of `PLAN.md`, run on 8 November 2026 from 18:15 to 18:53 UTC.
It changes nothing in the engine and decides nothing about it.

## The answer

By the rule the plan wrote before measuring, **the end of the search is not
the main cause.** Of the 40 near fits of T and 10T that kept their status,
35 are in class 1: the search never offered a candidate that the polish
makes exact. Five are in class 3, lost by the pool: they are the five seeds
of I.8.14 at 10T. Classes 2 to 5 hold for 5 fits, below the 10 the plan set.

| class | fits |
|---|---|
| 1, no candidate within reach | 35 |
| 2, turned away by a guard | 0 |
| 3, lost by the pool | 5 |
| 4, not a finalist | 0 |
| 5, cut by the grace | 0 |
| 6, polished and still not exact | 0 |

## How it was run

- **Engine and bench:** 1.2.0 from PyPI (`/venv12p`), observed by `diag.py`,
  which wraps five of its functions from the script. The bench is that of
  the budget study, at commit f581339, four fits at a time. Records are in
  `records.jsonl`, and the classes in `classes.txt`, from `classify.py`.
- **The fits:** 53 fits, with no crash. 50 of the 53 kept the status they
  had in the budget study. Three went from near to miss: I.37.4 seed 0 and
  III.17.37 seed 3 at T, and III.9.52 seed 1 at 10T. Those three are not
  counted.
- **The check of the wrap held** (`check_wrap.jsonl`). On two F41 fits bounded
  by generations only, the wrapped engine returned the same expression, in
  the same generations, as the engine without the wrap.
- **The cost of the wrap:** the fits bounded by time reached a median of
  0.89 of the generations they reached in the budget study (0.84 to 1.00).
  The wrap costs a little. Polishing every candidate after each fit, for up
  to 37 s, also loads the machine while the other three fits run.
- **Within reach:** a candidate is within reach if it comes back exact
  through the engine's own polish (`_polish_finalists`, on that candidate
  alone, with no deadline). That polish includes the fit to convergence and
  the weighted sums. Exact is read by the test of `_track_if_exact`.

## The fits of class 1, by equation

| equation | law | T | 10T |
|---|---|---|---|
| I.30.5 | arcsin(lam/(n d)) | 5 | 5 |
| I.26.2 | arcsin(n sin(th2)) | | 5 |
| I.37.4 | I1 + I2 + 2 sqrt(I1 I2) cos(delta) | 3 | 5 |
| III.10.19 | mom sqrt(Bx² + By² + Bz²) | 1 | 4 |
| III.17.37 | beta (1 + alpha cos(theta)) | | 2 |
| I.16.6 | (u + v) / (1 + u v / c²) | 1 | 1 |
| I.11.19 | x1 y1 + x2 y2 + x3 y3 | | 1 |
| II.2.42 | kappa (T2 - T1) A / d | 1 | |
| III.9.52 | the resonance of III.9.52 | | 1 |

- **The arcsine laws:** 15 of the 35 are the two laws with an arcsine,
  I.30.5 and I.26.2. No operator pool of 1.2.0 has an arcsine, nor an
  arctangent that could write one. At T, those two laws make 10 fits of F41
  that cannot come back exact, at any budget: I.30.5 is near in five seeds
  (1 - R² up to 1e-5), I.26.2 a miss in five (0.004 to 0.006).
- **The other laws:** their operators are in their pool, but the search did
  not offer their structure.

## I.8.14, read apart

- **At T,** in all five seeds, the candidates within reach are in the pool
  when the search stops. They are small trees of 14 to 25 nodes, so they
  are among the 8 smallest finalists. Polished, they come back exact, and
  the selection returns the exact form of 22 nodes.
- **At 3T and 10T,** the same candidates had been offered, and most of them
  had entered the pool. When the search stops, none of them is still in it.
  The pool is full, at 64 places, and all the finalists are larger trees, of
  31 to 74 nodes, with a lower error on the hold-out.
- **The model returned at 3T and 10T** has 14 nodes in seeds 0, 2 and 3, and
  22 in seeds 1 and 4. It is never a finalist. By the code, it can only be
  the champion of the search, which the selection considers beside the
  pool, and it was never polished.
- **Why it is near:** in the engine's internal variables, which are
  standardised, the model of 14 nodes has the structure of the law. Its
  printed formula carries one coefficient per variable, the scales of the
  standardisation, which the polish would have fitted. So it is near, and
  its constants are the same in every seed, since the data are.
- **Seed 1 at 3T** stayed exact: two candidates within reach were still in
  the pool.
- **The grace cut nothing that mattered:** every finalist of I.8.14 was
  fitted to convergence. At 10T, the grace cut part of the polish in 11 of
  the 30 fits, always in a fit with no candidate within reach.

So the answer to the question of the budget study is the pool (P), not the
grace (G). Because the pool keeps the 64 best on the hold-out whatever their
size, a longer run can push the small structure of the law out of it. It
then goes unpolished, while the selection still returns it, near.

## Deviation

`classify.py` was corrected after the run. Its first version counted the
four near fits of I.8.14 at 3T with those of T and 10T, and gave 9 of 44.
The plan counts the fits of T and 10T only and reads 3T apart. The
corrected count is 5 of 40. Both are below 10, and the answer is the same.

## What follows

As the plan says, the work goes to the search itself or to the other items
of the roadmap. The figures point to one item of the roadmap: **the arcsine**,
which the author had listed after 1.2. Without it, 10 fits of F41 at T
cannot come back exact.

The loss of I.8.14 has a clear mechanism, and the change it calls for is
small: the champion, or the smallest candidates of the band, polished
whatever the pool keeps. It acts only in runs longer than those of the
bench, so it is recorded here for later.
