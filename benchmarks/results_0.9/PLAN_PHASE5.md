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

## Diagnostic D5, result (12 October 2026)

Run from 21:24 to 22:24 UTC, 410 fits, no crash (`phase5/diag5.jsonl`;
`python benchmarks/phase2_bench.py summary diag5
benchmarks/results_0.9/phase5/diag5.jsonl`).

| | 1 % noise | 10 % noise |
|---|---|---|
| S, structure retrieved | 66 | 63 |
| P-band, in the pool and in the band, a smaller one preferred | 3 | 1 |
| P-out, in the pool, outside the band | 0 | 0 |
| N, not in the pool | 136 | 141 |

The expectation on S holds (66 and 63, against 70 and 67 for 0.8.0 on the
machine of its baseline); the one on P-band does not: **the final selection
loses the structure in 3 fits of 205 at 1 % noise and 1 at 10 %**. In two
fits of three the structure is not among the candidates at all. Setting the
selection on the level of the noise, the lever the plan of 0.9 named, could
recover at most those 4 fits, far from the 14 and 14 the targets ask of the
current engine.

Where the structure could come from instead: the seeds of the power law, B1
and E1 have thresholds set in log scale or at numerical precision, which
noise defeats (with noise added to y, log|y| is far noisier where y is
small). With the thresholds lifted, and each seed judged by its relative
error after linear scaling on the training rows (outside the engine's
search, `phase5/seed_ceiling.py`, `phase5/seed_ceiling.jsonl`), a seed with
the structure of the law exists for 23 equations at 1 % noise, at the level
of the noise (relative error 0.8e-4 to 1.2e-4), and for 12 at 10 % (0.8e-2
to 1.4e-2, and 3.1e-2 for `I.27.6`). Counting the fits the engine misses on
those equations, the ceiling is 54 more fits at 1 % noise and 13 at 10 %.
On the real training rows of R6 and R7raw, the best such seeds fit with a
relative error of 0.026 at least (power law, `nikuradse_1`) and 0.032 (B1
and E1; `phase5/finders_real.jsonl`).

This changes the lever of phase 5; the choice goes to the author.

## Decision of the author (12 October 2026)

Asked whether to keep the lever of the plan (the final selection, at most 4
fits) or to let the seeds of the power law, B1 and E1 tolerate noise, the
author chose the seeds. What follows replaces the lever named in the plan of
0.9 for phase 5.

## Change N1: seeds that tolerate noise, plan written before it is implemented (12 October 2026)

**The change.** When neither B1 nor E1 placed a seed (no form holds to
numerical precision), the three finders are run again with their thresholds
lifted: the power law without its log-log R² of 0.999, B1 and E1 without
their threshold of numerical precision (the guard that leaves an exact power
law to its own seeds is kept). Each form they return is judged as the data
judge it: its relative error after linear scaling on the training rows,
1 − R². It becomes a seed only if that error is at most 0.015. The threshold
is set between the two measurements of D5: the seeds with the structure of
the law fit 10 % noise at 0.008 to 0.014 (1 % noise at about 1e-4), and on
the real training rows of R6 and R7raw no such seed fits better than 0.026.
One copy per island after the other seeds, judged like every other
individual; the guards of B1 and E1 (generic CSV mode, not under `units=`,
not in extrapolation mode). No random number is drawn. Flag
`_TOLERANT_SEEDS` in `gp_elite/core.py`, off by default; the finders gain a
threshold argument whose default keeps them as they are.

Checked before this plan, outside the engine, on the noiseless training
rows of F41: three equations without an exact seed would receive a tolerant
one (`I.16.6` at 0.005, `I.26.2` at 0.005, `I.37.4` at 0.008), all three
exact in none of the fits of the engine with B1 and E1.

**Mechanics, before any fit.** Flag off: the thirteen reference
configurations identical to the 0.9.0 wheel and the test suite passing. Flag
on: for each configuration, whether a seed was placed; every configuration
without one identical to the 0.9.0 wheel. One fit of 30 generations of
I.34.1 with 1 % noise, outside any measurement.

**Campaign N1** (decides). A (the engine with B1 and E1, flag off) against
N1 side by side, budget T, four fits at a time: F41, F41 with 1 % and 10 %
noise, R6 and R7raw with the default pool, R6 and R7raw with `"trig"`,
seeds 0 to 4 (875 jobs). N1 is adopted when all hold:

1. **structure under noise:** with 1 % noise, the structure retrieved in at
   least 10 more fits than A; with 10 % noise, in no fewer than A's minus 2;
2. **exact laws:** on F41 without noise, no more than 3 fewer than A, and no
   equation exact in A at three seeds or more falls to one seed or none;
3. **real data in the domain:** with each pool, the median paired difference
   of test R² over the folds at least −0.005;
4. **out of domain:** with each pool, no more than 2 collapses more than A,
   and the median R² no lower than A's by more than 0.01;
5. **formulas:** no more than 3 formulas flagged inexact more than A on the
   260 real fits.

Reported beside the criteria: the fits on which a tolerant seed was placed,
and the time the search took.

**Confirmation on new seeds**, if the campaign adopts N1: the same jobs with
seeds 5 to 9 (folds with seed 5). N1 is kept when, with 1 % noise, the
structure is retrieved in at least 5 more fits than A and, with 10 %, in no
fewer than A's minus 2; F41 exact no more than 3 fewer than A; and with each
pool the median paired difference over the folds at least −0.005 and out of
domain no more than 2 collapses more than A.

The targets of gate 2 (80 and 77 fits with the structure) are read on the
campaign and the confirmation; the ceiling measured above (54 and 13 more
fits) says the second may stay out of reach.
