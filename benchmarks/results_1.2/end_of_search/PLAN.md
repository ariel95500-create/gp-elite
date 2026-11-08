# Where the end of the search loses exact laws: plan of a diagnostic

Written on 8 November 2026, before any measurement. On that day the author
left the choice of what follows the budget study to Claude. Claude chose
this diagnostic first, for three reasons:
- it costs about an hour of computing;
- it stays on the decision bench;
- it may show a defect at the end of the search that also costs exact laws
  at the usual budget.

It changes nothing in the engine and decides nothing about it. If it finds
a cause, a plan for a change is written and committed before any change, as
for H1. The author decides at the gates of a release, as before.

Method as before:
- one process per fit, `PYTHONHASHSEED=0`, one BLAS thread;
- four fits at a time, on one machine;
- the frozen test set is not used at all;
- every deviation goes to the author.

## What the budget study showed

In `../budget_study/README.md`, Feynman I.8.14 comes back exact at T (30 s)
in all five seeds, and near at 3T and 10T in all five. The near formula has
the structure of the law, written with a separate coefficient for each
variable and an offset. On F41, 13 fits are near at T and 30 at 10T. A near
fit is one with 1 - R² on the test rows between 1e-9 and 1e-3.

## The end of the search in 1.2.0, as the code reads

Read in `gp_elite/core.py` of 1.2.0, before any measurement:
1. **The pool:** every champion of the search is offered to a pool of
   candidates, with its error on the hold-out rows. The pool keeps at most
   64 candidates (`_VAL_CANDS_MAX`): beyond that, the 64 best on the
   hold-out stay, whatever their size.
2. **The finalists:** once the search stops, the pool gives its finalists
   (`_finalists`). These are the 8 best on the hold-out, and the 8 smallest
   within the tolerance band of the final selection.
3. **The polish:** each finalist is polished (`_polish_finalists`). Its
   constants are fitted, then fitted to convergence, and some sums are
   weighted. A polished variant joins the pool only if it is exact on the
   hold-out. The fit to convergence and the weighted sums stop one second
   after the deadline of `time_limit` (`_POLISH_GRACE_S`). The 8 best come
   first, the 8 smallest after.
4. **The selection:** the selection (`_select_one_se`) returns the smallest
   candidate of the pool within the tolerance band. When the best candidate
   is exact, only exact candidates stay eligible.

From this reading, two ways the law can be lost, written before measuring:
- **P, the pool:** a longer run offers more champions. The small candidate
  with the structure of the law can be pushed out of the 64 by larger trees
  with a lower error on the hold-out. It is then never polished.
- **G, the grace:** after a longer run, the 8 best are larger trees, and
  fitting them to convergence takes longer. The second of grace can run out
  before the 8 smallest are reached, among them the structure of the law.

## What is measured

The engine is 1.2.0 from PyPI in `/venv12p`, its files checked identical to
the wheel of the release. The bench is `../../phase1_bench.py`, with its
settings and budgets, the arms of the budget study. The engine is observed
from the driver script, which wraps its functions. No file of the package
is changed. For each fit, the record holds:
- every candidate offered to the pool, with its size, its error on the
  hold-out and a copy of its tree;
- the pool once the search stops, and the finalists;
- for each finalist, whether the fit to convergence ran, or was skipped by
  the deadline;
- the variants admitted as exact, the model selected, the time and the
  generations;
- the status on the test rows (exact, near, miss), as the bench gives it.

The fits:
- **I.8.14, seeds 0 to 4, at T and at 3T:** 10 fits.
- **Every F41 fit near at T in the budget study:** 13 fits, run at T
  (I.16.6, I.30.5 ×5, I.37.4 ×4, II.2.42, III.10.19, III.17.37).
- **Every F41 fit near at 10T in the budget study:** 30 fits, run at 10T
  (I.11.19, I.16.6, I.26.2 ×5, I.30.5 ×5, I.37.4 ×5, I.8.14 ×5, III.10.19
  ×4, III.17.37 ×2, III.9.52 ×2).

The fits are bounded by time, so a fit run again need not return what it
returned in the budget study. The record gives, for each fit, whether its
status is the same. The classification below is read only on the fits whose
status is the same.

**Checks of the wrap:**
- **Before the fits:** two fits of F41 are bounded by generations only, with
  no `time_limit`, so that they do not depend on the clock. The wrapped
  engine must return the same expression as the engine without the wrap. If
  it does not, the wrap changes the computation. The author is told before
  any further fit.
- **During the fits:** the wrap may cost time. The generations each fit
  reaches are given beside those of the same fit in the budget study.

## How each fit is classified

After the fit, every distinct candidate offered to the pool is fitted to
convergence with the engine's own step (`_lm_to_convergence`, then
`_refit_scaling`), with no deadline. A candidate is "within reach" if the
result is exact on the hold-out, by the test the engine itself applies
(`_track_if_exact`). Each fit that did not return an exact law falls in the
first class that holds:
1. **No candidate within reach:** the search never offered the structure of
   the law. The end of the search is not the cause.
2. **Turned away by a guard:** every candidate within reach was refused by a
   guard of the pool. These are the numerical stability guard and, under
   units, the guard of units.
3. **Lost by the pool (P):** every candidate within reach that passed the
   guards was out of the pool when the search stopped. Either it was pushed
   out, or it was never admitted for being worse than the 64th.
4. **Not a finalist:** a candidate within reach was in the pool, but among
   neither the 8 best nor the 8 smallest.
5. **Cut by the grace (G):** a candidate within reach was a finalist, but its
   fit to convergence was skipped by the deadline.
6. **Polished and still not exact:** a candidate within reach was a finalist
   and fitted to convergence during the fit, and still did not come back
   exact. Something else is at work, and it is described.

## What it means

Written before measuring:
- **If classes 2 to 5 hold for at least 10 of the near fits** that kept their
  status, of T and 10T together: the end of the search loses laws that the
  search had found. A plan for a change of the end of the search is
  written. It is measured on the decision bench with criteria written before
  the change, as for H1, and it goes to the author.
- **If class 1 or 6 holds for most of them:** the end of the search is not
  the main cause. The work goes to the search itself, or to the other items
  of the roadmap, and that is put to the author.

The ten fits of I.8.14 are read apart, to answer the question of the budget
study: why the law is lost with more time.

## Records

Kept in this folder:
- the driver and the classification script, written before the fits;
- the records of the fits, the machine and the log;
- a README with the figures, written after the fits.
