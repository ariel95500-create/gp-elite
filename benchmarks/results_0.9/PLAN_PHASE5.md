# Phase 5 (noisy data) — plan written before any measurement

Written on 12 October 2026, after phase 4 (`PLAN_PHASE4.md`: B1 and E1
adopted). Method as in the earlier phases: a plan and its criteria committed
before each measurement, one process per fit, `PYTHONHASHSEED=0`, the frozen
test set never used to decide.

## What phase 5 has to do

The target of gate 2: on the decision bench with Gaussian noise on the
training targets, the structure of the law retrieved (the returned model,
its constants refitted on the clean training targets, reproduces the clean
test rows to 1 − R² < 1e-9) in at least 80 fits of 205 with 1 % noise and 77
with 10 %. gp-elite 0.8.0 retrieved it in 70 and 67 (`BASELINE.md`). The plan
of 0.9 names the lever: the early stop and the final selection, designed for
exact laws, set on the level of noise estimated on the hold-out.

What the engine does today, read in the code before this plan:

- the search stops early only on a law exact to numerical precision, which
  noisy data never reach: every noisy fit runs to its budget;
- the final selection (`_select_one_se`) takes, among the candidates whose
  hold-out error is within max(one standard error, 0.3 % of the variance) of
  the best, the smallest; with 1 % noise the noise is about 0.01 % of the
  variance, so the band of 0.3 % admits approximations far coarser than the
  noise, which may cost the structure; with 10 % noise (1 % of the variance)
  the band is narrower than the noise;
- the seeds of B1 and E1, and the power-law seeds (whose threshold is a
  log-log R² of 0.999), act only when a form holds to numerical precision:
  with noise, B1 and E1 never act.

## Step 1: diagnostic D5 (decides nothing)

Before any change, the current engine (B1 and E1 on) is measured on F41
with 1 % and 10 % noise, seeds 0 to 4 (410 fits, budget T, one arm, four
fits at a time). Besides the usual record and the structure of the returned
model, each fit records the pool of candidates the final selection chose
from (up to 64), and for each candidate whether its structure is the law's
(the same test as for the returned model). Each fit is classified:

- **S**: the returned model has the structure;
- **P**: a candidate of the pool has it, the returned model does not; split
  into **P-band** (that candidate was within the selection's band and a
  smaller one was preferred) and **P-out** (it was outside the band);
- **N**: no candidate of the pool has it (the search did not find it).

Also recorded, for each fit, how well the forms of B1 and E1 fit the noisy
training rows when the threshold of numerical precision is lifted (the
relative error of the best form after linear scaling), and the same on the
training rows of R6 and R7raw (no fit of the engine): whether a threshold
set on the level of the noise could let them act on noisy laws without
acting on real data.

Expectations, written before: S near the 70 and 67 of 0.8.0 (B1 and E1 do
not act on noise); P-band frequent at 1 % noise, rare at 10 %; most of the
rest N.

The changes N1 and N2 are planned from this diagnostic, each with its own
criteria, before it is implemented.
