# Phase 2 (reliability) — plan written before any trial

Written on 9 October 2026, after gate 2, before the change below is
implemented and before any fit of this phase. The criteria decide; they are
not adjusted after the results are seen. Method: `PLAN.md` of this
directory and `benchmarks/results_0.8/PLAN.md`; the frozen test set is never
used here.

## The change (F1)

0.8.0 delivers a formula that does not reproduce its model whenever one of
the engine's numerical safety nets acts on the training rows: a power whose
exponent is clipped to ±6 or whose base is clipped to ±100, a result above
1e6 replaced by 1, a division by a denominator below 1e-8, an exponential
clipped at ±88, a tangent above 1e6. The formula is then flagged
(`formula_exact` False) and the fit warns. In the baseline of phase 1 this
happened in 14 fits of 335 on the decision bench (6 of 205 on F41, 8 of 70 on
R7raw).

F1 makes such a candidate invalid during the search: a tree whose value on
the training rows, computed without the safety nets (the semantics of the
printed formula, `gp_elite.formula.evaluate`), departs from its value with
them by more than 1e-7 of the scale of the predictions, or is not finite,
gets an infinite fitness, and is not admitted to the pool from which the
final model and the Pareto front are chosen. The verdict is cached per tree
and per data set. The change sits behind a module flag that is off by
default: with the flag off, the engine must return the same models, bit for
bit, as gp-elite 0.8.0 on the thirteen reference configurations of
`benchmarks/speed_equivalence.py` before any trial runs.

## Arms

A: the engine of this branch with the flag off. F1: the same engine with the
flag on. Same machine as phase 1 (4 cores), budget T (30 s per fit), one
process per fit, `PYTHONHASHSEED=0`, the two arms of a job side by side.

## Targeted trial (sorts the idea, decides nothing)

From the decision bench only, chosen from the phase 1 baseline before this
plan was written:

- **targeted** (the fits where 0.8.0 delivered inexact formulas): F41
  `II.35.18`, seeds 0 to 4; R7raw `nikuradse_1`, folds 0 to 4; R7raw
  `228_elusage`, out of domain, seeds 0 to 4. In the baseline: 8 inexact
  formulas in these 15 fits.
- **controls that already succeed after a long search**: F41 `I.8.14`
  (exact 5 of 5, about 96 generations) and `II.2.42` (exact 4 of 5, about 80
  generations), seeds 0 to 4. A slower search would show there first.
- **real data**: R6 `210_cloud` and `561_cpu`, folds 0 to 4.

35 jobs, 70 fits, about 15 minutes. The trial is **conclusive** when all
three hold:

1. F1 delivers at most 2 inexact formulas in the 15 targeted fits;
2. no control fit that is exact in A is not exact in F1;
3. on the 20 real fits (targeted and real data), the median paired
   difference of test R² (F1 − A) is at least −0.01, and F1 has no collapse
   (R² < 0) that A does not have.

A conclusive trial opens campaign F1; a trial that is not conclusive is
recorded with its numbers and the variant "penalty instead of invalid" (F2,
risk register of the plan) is considered, with a new written plan.

## Campaign F1 (decides)

The whole decision bench, budget T, A against F1: F41 (seeds 0 to 4), R6 and
R7raw (folds and out of domain, seeds 0 to 4). F1 is adopted when all hold:

1. **formula equal to the model:** `formula_exact` True in 130 of the 130
   real fits (R6 and R7raw) and in every F41 fit;
2. **exact laws:** F41 at least 82 of 205, and no more than 3 fits exact in A
   and not in F1;
3. **real data:** median test R² of R6 folds at least 0.804, and the median
   paired difference over R6 and R7raw folds at least −0.005;
4. **collapses:** out of domain, F1 has no more collapses than A on R6 and
   R7raw together, and its worst case is no deeper.

Reported as in phase 1: means, medians and worst cases, paired comparisons,
time beyond the budget, and the cost of the check (median generations in
30 s).

## Targeted trial F1, result (9 October 2026)

Run from 21:01 to 21:11 UTC, 70 fits, 35 complete pairs, no crash
(`phase2_trial_F1.jsonl`; `python benchmarks/phase2_bench.py summary trial
benchmarks/results_0.9/phase2_trial_F1.jsonl`). The criteria are applied as
written above.

1. Targeted fits: inexact formulas 8 of 15 in A, 0 of 15 in F1. **Holds.**
2. Controls: exact 7 of 10 in A, 5 of 10 in F1. Three fits exact in A are
   not exact in F1 (`I.8.14` seed 1, `II.2.42` seeds 0 and 3); one fit exact
   in F1 is only near in A (`I.8.14` seed 3). **Fails.**
3. Real fits: median paired difference of test R² +0.0018; collapses 3 in A,
   2 in F1, none new in F1. **Holds.** The worst case, however, is far deeper
   in F1: `228_elusage` out of domain, seed 4, R² −237,351 against −232.5 in A
   (both arms collapse on that fit). Criterion 4 of the campaign would not
   accept that.

**The trial is not conclusive; campaign F1 is not run.**

Cost of the check, reported as is: median generations in 30 s 61 in A and 45
in F1 (−26 %), median candidates rejected by the check 5,585 per fit. In the
three lost controls F1 ran 53, 43 and 41 generations where A ran 72, 81 and
65. Whether the losses come from the fewer generations or from the rejected
candidates themselves is not known from this trial; it is examined before the
next variant gets its written plan.

## Diagnostic after the trial (9 October 2026, 21:12 to 21:16 UTC)

The ten controls were run again, F1 only, with 42 s per fit (30 s × 61/45),
so that F1 reaches the generations A reached in 30 s
(`phase2_diag_F1_42s.jsonl`; `python benchmarks/phase2_bench.py run diag`).
F1 then ran 58 to 83 generations (A: 61 to 87 in 30 s) and found the same 5
exact laws as in 30 s; none of the three lost controls came back, although
`I.8.14` seed 1 ran 75 generations against 72 in A. The losses do not come
from the cost of the check alone: rejecting candidates during the search
changes the path the search takes, and with it which laws it finds. A penalty
(F2) also changes that path, by reordering the candidates, so the same kind of
loss is to be expected from it; it is not the next variant.

## Variant F3, plan written before any trial (9 October 2026)

**The change.** F1's check, applied only where the delivered model is chosen,
never in the search. A candidate whose formula does not reproduce the engine
(the test of F1) does not enter the pool of the final selection (from which
the Pareto front is also built), is not admitted as champion in that
selection, and does not replace the champion after the final optimisation of
the constants. The fitness, and therefore the whole search, stays that of
0.8.0. The check runs on the candidates that enter the pool, not on every
tree, and also with parallel islands, since the selection runs in the main
process. Flags: `_GUARD_STRICT` on and a new `_GUARD_SEARCH` off (F1 is both
on); both off by default.

**Mechanics, checked before the trial.**

1. Both flags off: the thirteen reference configurations of
   `benchmarks/speed_equivalence.py` return the same models as gp-elite
   0.8.0, bit for bit.
2. F3 on, same thirteen configurations (fixed generations, no time limit):
   every returned model has `formula_exact` True, and a configuration may
   return a model different from (1) only if the check removed at least one
   candidate there (counted by the engine's trace).
3. The power example of F1's mechanics check: `formula_exact` True and no
   inexact entry on the Pareto front.

**Targeted trial F3.** The same 35 jobs as the trial of F1, arms A and F3
side by side, A run again (generations within 30 s depend on the load). The
trial is conclusive when all four hold:

1. F3 delivers at most 2 inexact formulas in the 15 targeted fits;
2. no control fit that is exact in A is not exact in F3;
3. on the 20 real fits, the median paired difference of test R² (F3 − A) is
   at least −0.01, and F3 has no collapse (R² < 0) that A does not have;
4. on the 20 real fits, the worst test R² of F3 is no deeper than that of A
   (added after what the trial of F1 showed, before any fit of F3).

A conclusive trial opens campaign F3, decided by the four criteria of
campaign F1 above, unchanged. A trial that is not conclusive is recorded with
its numbers, and phase 2 goes back to the author before any further variant.

## Mechanics of F3, result (9 October 2026, 21:23 to 21:27 UTC)

Files in `phase2_mechanics/` (the flags are set in each process by
`benchmarks/phase2_flags/sitecustomize.py`).

1. Both flags off against the 0.8.0 wheel (`repro/default`): 13 of 13
   identical (`compare_0.8.0_vs_flags_off.txt`). **Holds.**
2. F3 on: `formula_exact` True in 13 of 13 (`B_cpu` was False with the flags
   off). Two configurations return another model, `B_cpu` (4 candidates
   removed) and `I_sklearn` (Pareto front only, 1 removed); `C_big` had 1
   removed and is unchanged; the ten others had none removed and are
   identical (`compare_flags_off_vs_F3.txt`, `trace_F3.jsonl`). **Holds.**
3. The power example: A `formula_exact` False with 2 inexact entries of 6 on
   the Pareto front; F1 True with 0 of 5; **F3 False**, with a Pareto front of
   one inexact entry (`power_example.txt`). In that fit the check removed all
   27 candidates offered to the pool: the search never tracked a candidate
   whose formula reproduces the engine, the pool was empty, and the selection
   fell back on the champion, as 0.8.0 does. **Fails.**

F3 does not pass its mechanics; its trial is not run, and phase 2 goes back to
the author.

## Variant F3R (F3 with a catch-up), plan written before it is implemented (9 October 2026)

Chosen by the author on 9 October 2026 among three options (F3 with a
catch-up, the trial of F3 as it is, or stopping this work and keeping the
warning of 0.8.0).

**What was looked at before this plan.** One probe, on the power example only
(F3 on, the final island populations read after the fit,
`power_example.py`'s data and settings): 77 of the 375 distinct individuals
of the final populations reproduce the engine, the best of them with training
R² 0.99997, whereas none of the 27 candidates offered to the pool did. No fit
of the decision bench or of the test set was made.

**The change.** F3, plus a catch-up at the end of the search, before the
polishing of the finalists, only in a run where the check removed at least
one candidate (counter reset at each run): the individuals of the final island
populations, with their linear scaling materialised as the search does for
the candidates it tracks, are ranked by training MSE, and the first 8 whose
formula reproduces the engine are offered to the pool of the final selection
through the same door as every other candidate (dimensional gate, numerical
stability, check). At most 200 distinct individuals are examined. Polishing
and selection then run as in F3. A run in which nothing was removed is not
touched, so it stays as in F3, whose search is that of 0.8.0. If no faithful
candidate exists even then, the selection falls back on the champion as 0.8.0
does, with its warning; this is counted. Flags: `_GUARD_STRICT` on,
`_GUARD_SEARCH` off, a new `_GUARD_CATCHUP` on; all three off by default.

**Mechanics, checked before the trial.**

1. All flags off: the thirteen reference configurations return the same
   models as gp-elite 0.8.0, bit for bit.
2. F3R on, the same thirteen configurations: every returned model has
   `formula_exact` True, and a configuration may return a model different
   from (1) only if the check removed at least one candidate there.
3. The power example: `formula_exact` True and no inexact entry on the Pareto
   front. The time the catch-up takes there is reported.

**Targeted trial F3R.** The same 35 jobs, arms A and F3R side by side, and
the same four criteria as the trial of F3 above (at most 2 inexact formulas
in the 15 targeted fits; no control exact in A lost; on the 20 real fits a
median paired difference of test R² of at least −0.01 and no new collapse;
on the same fits a worst test R² no deeper than A's). Reported beside them:
the fits where the catch-up ran, and its time.

A conclusive trial opens campaign F3R, decided by the four criteria of
campaign F1 above, unchanged. Otherwise the trial is recorded with its
numbers and phase 2 goes back to the author.

## The models that collapse out of domain

The second half of phase 2, written separately after campaign F1: the
collapses of the decision bench (10 of 65 out of domain in the baseline) are
examined one by one before any change is proposed for them.
