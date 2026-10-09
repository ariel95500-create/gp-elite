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

## The models that collapse out of domain

The second half of phase 2, written separately after campaign F1: the
collapses of the decision bench (10 of 65 out of domain in the baseline) are
examined one by one before any change is proposed for them.
