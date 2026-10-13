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

### Mechanics of N1, result (12 and 13 October 2026)

Flag off: the thirteen reference configurations identical to the 0.9.0
wheel (`phase5/mechanics/compare_0.9.0_vs_N1_off.txt`) and the test suite
passing (150 tests, the two of N1 included; `tests_N1_off.txt`). Flag on
(`compare_0.9.0_vs_N1_on.txt`, `trace_N1_on.jsonl`): a tolerant seed was
placed in two configurations, which return another model; the eleven others
are identical to the wheel. **Holds**, as written. The two changes:

- `C_big`, X0·X1/X2 with noise on 5,000 rows: 0.9.0 returned an
  approximation of 17 nodes (hold-out MSE 0.00295); with N1 the law itself,
  `1.00045 * X0 * X1 / X2` (9 nodes, 0.00223).
- `E_minmax`, Kepler's law a^1.5 without noise, normalised by min-max: a
  trigonometric form fits the training rows to 2.5e-5 and was placed; 0.9.0
  returned the exact law (10 generations), the engine with N1 a
  trigonometric approximation (hold-out MSE 1.86). Fitted again, seeds 0 to
  9, outside any measurement (`kepler_minmax_check.txt`): exact law in 0
  and 0 fits of 10 at 10 generations without and with N1, in 3 and 1 at 40.
  On exact data that no exact seed covers, a tolerant seed can draw the
  search away from the law. On F41, with the default normalisation, only
  three equations are in that case, and the engine finds none of them
  exactly; the campaign's criterion 2 watches the rest. A guard telling
  noisy data from exact data by an estimate of the noise taken from the data
  alone (local linear fits, `noise_estimate_check.py`) was tried outside any
  measurement: it separates them in one dimension (Kepler, 8.5e-6) but not
  in three to six (exact F41 laws estimated as noisy as 1 % noise), so none
  is added. This limit is reported with the campaign.

The fit of I.34.1 with 1 % noise, seed 0, 30 s, outside any measurement: A
returns an approximation of 70 nodes (structure not retrieved, 1.7e-3 on
the clean test rows), N1 `0.00115247 + 1.00099 * v0 / (1 - 0.997137 * v1 /
v2)` (13 nodes, structure retrieved), six tolerant seeds placed in 0.17 s.
The campaign is run.

### Campaign N1, result (13 October 2026)

Run from 23:32 on 12 October to 02:52 UTC, 1,750 fits, 875 complete pairs,
no crash (`phase5/campaign_N1.jsonl`; `python benchmarks/phase2_bench.py
summary campaignn1 benchmarks/results_0.9/phase5/campaign_N1.jsonl`). The
machine of the session restarted at about 00:52 UTC after 872 fits: the fits
running at that moment left no record and were run again in full when the
campaign resumed at 00:53 (`phase5/campaign_N1_driver.log`). A is the engine
with B1 and E1. The criteria are applied as written.

1. Structure retrieved: with 1 % noise 69 in A, **106 in N1** (+37); with
   10 % noise 68 in A, **86 in N1** (+18). **Holds.** With 1 % noise,
   `I.10.7`, `I.12.2`, `I.34.1`, `II.13.23` and `II.24.17` go from 0 to 5
   seeds, `II.6.15b` from 1 to 5, `I.18.12`, `I.27.6` and `II.15.4` from 2
   to 5, and `III.19.51` falls from 2 to 1; with 10 %, `I.34.1` 0 to 5,
   `III.15.12` 0 to 4, `I.12.2`, `I.18.12` and `II.15.4` 2 to 5.
2. F41 without noise: exact 157 in A, 160 in N1; no law lost. **Holds.**
   (`I.16.6`, (u + v)/(1 + u·v/c²), from 0 to 3: the tolerant seed placed
   on these exact data led to the law.)
3. Real data in the domain: median paired difference over the folds +0.0000
   with each pool (worst +0 with the default pool, −0.078 with `"trig"`).
   **Holds.**
4. Out of domain: collapses 10 in both arms with the default pool, 13 in
   both with `"trig"`; medians 0.647 and 0.647, 0.629 and 0.694. **Holds.**
5. Formulas flagged inexact on the 260 real fits: 11 in both. **Holds.**

**N1 is adopted by the campaign**; the confirmation on new seeds follows.
The targets of gate 2, 80 and 77 fits with the structure, are passed in
this campaign (106 and 86). Beside the criteria: a tolerant seed was placed
in 140 fits of 205 with 1 % noise, 95 with 10 %, 20 on F41 without noise
(`I.16.6`, `I.26.2`, `I.30.5`, `I.37.4`), and in none of the 260 real fits;
the search took 0.17 s in the median with noise (0.34 s at most). 256 of the
260 real fits return the same expression in both arms; in the four others no
seed was placed and the arms reached another number of generations in their
30 s.
