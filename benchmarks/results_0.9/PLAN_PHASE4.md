# Phase 4 (the missing families) — plan written before any change

Written on 10 October 2026, after the author chose to start phase 4 before
phase 3. Method as in phases 1 and 2: a plan and its criteria committed
before each change is implemented, one process per fit, `PYTHONHASHSEED=0`,
paired arms side by side, the frozen test set never used to decide.

## What phase 4 has to do

The target of gate 2: the five families that 0.8.0 never finds (roots,
trigonometry, rational forms, exponentials and logarithms: 18 F41 equations,
0 exact in 90 fits) reach at least 20 of 90, the gain confirmed on seeds 5
to 9, with no regression on real data. The plan of 0.9 names three changes,
each with its own campaign, then their combination: 4a, an adjustable
argument inside sin, cos, exp, log and sqrt; 4b, a rational form
(a + b·f)/(1 + c·g) fitted by least squares; 4c, columns of order one left as
given.

## Where 4a starts: trigonometric functions of a variable in its own units

`PLAN_TRIG.md` measured it three times: with the inputs left as given, 11
more fits of 50 on the ten trigonometric laws of F41 come back exact (2 to
13), because the engine divides each column by its largest value and a sine
of a scaled angle needs a constant inside it that the search does not find;
but leaving every input as given harms real data. The first step of 4a gives
the sine its argument in the variable's own units without touching the
scaling of anything else.

### Change T1, plan written before it is implemented

**The change.** When the operator pool contains `sin` or `cos` (the pools
`"trig"` and `"full"`), the initial population receives seeds in which the
trigonometric function takes a column in its own units. The engine works on
scaled columns `u_j = a_j·x_j + b_j` (`gp_elite/formula.affine_maps`); the
seed writes `x_j` as `(u_j − b_j)/a_j`, which the printed formula folds back
to `x_j`. For each column j: `sin(x_j)` and `cos(x_j)`; the same multiplied
by the product of the other columns (a projection, as in r·F·sin θ); and for
each pair of columns, `cos(x_j·x_k)` and `sin(x_j·x_k)`. At most 32 seeds,
placed round-robin across the islands after the motif seeds, judged like
every other individual (Levenberg-Marquardt may move their constants). Not
injected under `units=` (typed population) or in extrapolation mode, as the
motif seeds. Nothing changes with a pool without `sin` or `cos`, in
particular with the default `"physical"`. Flag `_TRIG_SEEDS` in
`gp_elite/core.py`, off by default.

The seeds' forms come from physics (a function of an angle, a projection,
a phase `k·x`), and three of them match laws of F41 (`I.18.12`, `II.15.4`,
`III.15.12`): this is a prior the bench can reward, which is why the gain
must be confirmed on new seeds before adoption.

**Mechanics, before any fit.** Flag off: the thirteen reference
configurations return the same models as gp-elite 0.8.0 and the test suite
passes. Flag on: the configurations without `sin` or `cos` in their pool are
unchanged (only `E_minmax`, pool `"full"`, and `L_standard`, pool `"trig"`,
may change).

**Campaign T1** (decides), A against T1 side by side, budget T, four fits at
a time. Outside the ten F41 laws of the `"trig"` pool the decision bench is
unchanged by construction, so the campaign runs part 1, those ten laws with
seeds 0 to 4 (50 jobs), and part 2, R6 and R7raw with `operators="trig"` in
both arms (130 jobs). T1 is adopted when all hold:

1. part 1: at least 5 more exact laws than A, and no law exact in A at
   three seeds or more falls to one or none;
2. part 2, in the domain: the median paired difference of test R² over the
   folds at least −0.005;
3. part 2, out of domain: no more collapses than A, and the median R² no
   lower than A's by more than 0.01;
4. part 2: no more formulas flagged inexact than in A.

**Confirmation on new seeds**, if the campaign adopts T1: part 1 with seeds
5 to 9; T1 is kept when its exact laws are at least 5 more than A's.

### Mechanics of T1, result (10 October 2026, 04:41 to 04:49 UTC)

Flag off: the thirteen reference configurations are identical to the 0.8.0
wheel (`phase2_mechanics/compare_0.8.0_vs_T1_off.txt`) and the test suite
passes (140 tests). Flag on: only `E_minmax` (pool `"full"`) and
`L_standard` (pool `"trig"`) return another model; the eleven others are
identical (`compare_0.8.0_vs_T1_on.txt`). **Holds.** Before it, one fit of
20 generations per law, outside any measurement, showed the mechanism: with
the flag on, `I.18.12` and `II.15.4` came back as `v0 * v1 * sin(v2)` and
`-v0 * v1 * cos(v2)`. The campaign is run.

### Campaign T1, result (10 October 2026)

Run from 04:42 to 05:29 UTC, 360 fits, 180 complete pairs, no crash
(`campaign_T1.jsonl`; `python benchmarks/phase2_bench.py summary campaignt1
benchmarks/results_0.9/campaign_T1.jsonl`). The criteria are applied as
written.

1. Part 1, the ten "trig" laws: exact 2 in A, **12 in T1**, no law lost
   (`I.18.12` and `II.15.4` 1 to 5 seeds, `III.17.37` 0 to 2). **Holds.**
2. Part 2 (real data with `operators="trig"`), folds: median paired
   difference +0.0000, mean +0.017, worst −0.100. **Holds.**
3. Part 2, out of domain: collapses 13 in A, 9 in T1; median R² 0.700 in A,
   0.699 in T1. **Holds.** (Not a criterion: the worst case is −78.0 in A,
   −103.8 in T1, `228_elusage` standardised, seed 3.)
4. Part 2, formulas flagged inexact: 4 in A, **5 in T1**. **Fails**, by one
   formula of 130.

**T1 is not adopted**, under the rule written before the campaign. It holds
three criteria of four, with the gain the plan looked for on the
trigonometric laws, fewer collapses out of domain on real data, and an
unchanged median; it fails the fourth by one formula. Whether to test it
again, on seeds never run, goes to the author.

### Decisive test of T1 on new seeds, plan written before it (10 October 2026)

Chosen by the author after campaign T1: one more test, on seeds never run,
with the same four criteria. Campaign T1 stays recorded as not adopted; T1 is
adopted only if this test holds all four, and both are reported.

- Part 1: the ten "trig" laws with seeds 5 to 9 (50 jobs).
- Part 2: R6 and R7raw with `operators="trig"` in both arms, out of domain
  with seeds 5 to 9 and folds with seed 5 (130 jobs).
- A against T1 side by side, budget T, four fits at a time, as the campaign.

T1 is adopted when all hold, on these fits alone:

1. part 1: at least 5 more exact laws than A, and no law exact in A at
   three seeds or more falls to one or none;
2. part 2, in the domain: the median paired difference of test R² over the
   folds at least −0.005;
3. part 2, out of domain: no more collapses than A, and the median R² no
   lower than A's by more than 0.01;
4. part 2: no more formulas flagged inexact than in A.

If any fails, T1 is not adopted and 4a moves on without it.

### Decisive test of T1, result (10 October 2026)

Run from 05:39 to 06:26 UTC, 360 fits, 180 complete pairs, no crash
(`retest_T1.jsonl`; `python benchmarks/phase2_bench.py summary retestt1
benchmarks/results_0.9/retest_T1.jsonl`). The criteria are applied as
written.

1. Part 1, the ten "trig" laws with seeds 5 to 9: exact 7 in A, 11 in T1
   (+4; `I.18.12` 2 to 5, `II.15.4` 4 to 5, `III.17.37` 0 to 1, `I.50.26` 1
   to 0); no law lost. **Fails**: at least +5 was required.
2. Part 2, folds: median paired difference −0.0001 (worst −1.78,
   `228_elusage` in its units, fold 2). **Holds.**
3. Part 2, out of domain: collapses 17 in A, 10 in T1; median R² 0.440 in A,
   0.735 in T1. **Holds.**
4. Part 2, formulas flagged inexact: 5 in A, 6 in T1. **Fails**, again by
   one formula of 130.

**T1 is not adopted**, and its flag is removed from the engine (the code
stays in the history at commit ec02331, where both runs can be repeated).

What the two runs say together, for what it is worth outside the rule:
over seeds 0 to 9 the seeds raise the trigonometric laws from 9 to 23 of
100 fits, and on real data with trigonometric functions they cut the
collapses out of domain from 30 to 19 of 130 with a median R² out of domain
no lower; but they add one formula flagged inexact in each run. The
trigonometric laws themselves vary much from seed to seed in the engine of
0.8.0 (2 of 50 on seeds 0 to 4, 7 of 50 on seeds 5 to 9).

## Change A1 (the adjustable argument of 4a), plan written before it is implemented (10 October 2026)

Chosen by the author after T1. A lesson of T1 is applied from here on, in
advance: counts as small as the formulas flagged inexact (4 to 6 of 130) move
by one or two from run to run, so criteria on such counts allow that much.

**The change.** A new mutation, `argument_mutation`: in a tree that contains
`sin`, `cos`, `exp`, `log` or `sqrt` (those of the active pool), one such
node whose argument is not already of the form `a·g + b` gets its argument
`g` replaced by `a·g + b`, and the constants of the whole tree are fitted at
once by the engine's Levenberg-Marquardt step (`optimize_constants_adam`, as
for the elite children). Starting values: for `sin` or `cos` of a lone
column, `a` and `b` put the column back in its own units (the lesson of
`PLAN_TRIG.md` and of T1: `sin(x_j)` with `x_j = (u_j − b_j)/a_j`);
otherwise `a = 1.05`, `b = 0.05` (values that the simplifier does not erase,
so that the step has something to move). It is drawn with probability 0.08
at each mutation, before the usual ones; when the tree has no eligible node,
the mutation proceeds as in 0.8.0. Not under `units=` (typed mutations) and
not in the parallel islands (their workers do not receive the engine's
flags, a known limit of this measurement, to be closed before any release).
Flag `_ARG_MUT` in `gp_elite/core.py`, off by default; with it off, no random
number is drawn, so the engine is that of 0.8.0.

This acts with the default pool `"physical"` (which has `exp`, `log` and
`sqrt`), so it changes most fits: it is measured on the whole decision bench.

**Mechanics, before any fit.** Flag off: the thirteen reference
configurations identical to gp-elite 0.8.0, the test suite passing. Flag on:
reported field by field; `H_parallel` must stay identical (parallel islands)
and `D_units` too (typed).

**Campaign A1** (decides). The decision bench, A against A1 side by side,
budget T, four fits at a time: F41, R6 and R7raw, seeds 0 to 4 (335 jobs).
A1 is adopted when all hold:

1. **exact laws:** F41 exact in A1 at least 8 more than in A, among which at
   least 4 more in the five families at zero (roots, trigonometry, rational
   forms, exponentials, logarithms: 18 equations, 90 fits); and no equation
   exact in A at three seeds or more falls to one seed or none;
2. **real data in the domain:** R6 folds median test R² at least 0.804, and
   the median paired difference over R6 and R7raw folds at least −0.005;
3. **out of domain:** on R6 and R7raw, no more than 2 collapses more than A,
   and the median R² no lower than A's by more than 0.01;
4. **formulas:** no more than 3 formulas flagged inexact more than A on the
   335 fits.

**Confirmation on new seeds**, if the campaign adopts A1: the same 335 jobs
with seeds 5 to 9 (folds with seed 5). A1 is kept when F41 exact in A1 is at
least 5 more than in A, the median paired difference over the folds is at
least −0.005, and out of domain A1 has no more than 2 collapses more than A.

### Mechanics of A1, result (10 October 2026)

Flag off: the thirteen reference configurations identical to the 0.8.0
wheel (`phase2_mechanics/compare_0.8.0_vs_A1_off.txt`), the test suite
passing (140 tests). Flag on (`compare_0.8.0_vs_A1_on.txt`): `H_parallel`
and `D_units` identical, as required, and `A_feyn`, `F_robust`, `K_thorough`
too; the eight others return another model (`B_cpu` now with an exact
formula, `C_big` now with an inexact one). **Holds.** Before it, outside any
measurement, one fit of 30 generations on `I.18.12` came back exact with the
flag on (1 − R² 1e-16, a sine of the angle in its own units) and one on
`I.40.1` did not improve. The campaign is run.

### Campaign A1, result (10 October 2026)

Run from 08:46 to 09:58 UTC, 670 fits, 335 complete pairs, no crash
(`campaign_A1.jsonl`; `python benchmarks/phase2_bench.py summary campaigna1
benchmarks/results_0.9/campaign_A1.jsonl`). The criteria are applied as
written.

1. Exact laws: F41 86 in A, 91 in A1 (+5, at least +8 required); the five
   zero families 0 in A, 1 in A1 (`III.15.12`; at least +4 required);
   `II.2.42` falls from 3 seeds to 1. **Fails.** (`I.18.12` 1 to 5 seeds,
   `II.15.4` 1 to 2, `I.6.20a` 4 to 5, `II.11.27` 0 to 1; `I.11.19` 1 to 0.)
2. Real data in the domain: R6 folds median 0.810 in A, 0.804 in A1; median
   paired difference over the folds +0.0000. **Holds**, at the edge.
3. Out of domain: collapses 10 in A, **18 in A1**; median R² 0.647 in A,
   0.482 in A1; worst −2.1e8 (R6). **Fails**, widely.
4. Formulas flagged inexact: 15 in both. **Holds.**

**A1 is not adopted**, and its flag is removed from the engine (the code
stays in the history at commit 878fd47). The median generations fall from
60 to 45 in 30 s (the fit of the constants after each such mutation). The
adjustable argument helps the trigonometric laws, as the seeds of T1 did,
but freer exponentials and logarithms fit the training rows of real data
better and extrapolate much worse.

### Where 4a stands

Five measurements (`PLAN_TRIG.md`, T1 twice, A1) agree on one point: giving
the sine and the cosine their argument in the variable's own units recovers
trigonometric laws that 0.8.0 misses. Every way of doing it tried so far also
touched something else (the scaling of all inputs, or exp and log) or moved
a small count by one, and none was adopted. Users can already get the gain
with `normalize="none"`, as the README now says.

## 4b: a monomial times a power of a binomial (change B1), plan written before it is implemented (12 October 2026)

Phase 4 resumes after the release of 0.9.0, as the plan of 0.9 says. 4b is
the rational form of that plan, (a + b·f)/(1 + c·g), taken in the shape
physical laws give it: y = b·f·(1 + c·g)^p, with f and g monomials of the
inputs and p one of −1, −½, ½, 1. With p = −1 it is the rational form (the
offset a is left to the engine's linear scaling); with p = −½ the factor
1/√(1 − v²/c²) of the laws of the "racine" family; with p = ½ the square
root of a sum of two terms; with p = 1 a sum of two terms.

**Why a direct fit and not a search.** Such a law becomes a straight line
once the binomial is known: log|y| − p·log(1 + c·g) = log|b| + Σ e_j·log|x_j|.
For a given g, the best c is a search in one dimension, and the exponents
then follow by least squares, as for the power-law seeds of 0.8. The engine
divides each column by its largest value, which only changes b and c.

**What a prototype showed, before this plan.** A prototype outside the
engine (no fit of the engine, no test rows, the frozen test set untouched)
was run on the training rows of the decision bench: F41, and every fold and
the out-of-domain split of R6 and R7raw, the columns divided by their
largest value as the engine does. It holds to numerical precision (residual
variance of log|y| below 1e-29 of its variance) on eight F41 equations, and
on none of the 130 real training sets:

| equation | family | p | 0.8.0 exact (baseline) |
|---|---|---|---|
| I.34.1 om0/(1 − v/c) | rationnelle | −1 | 0 of 5 |
| II.11.3 q·Ef/(m·(w0² − w²)) | rationnelle | −1 | 0 of 5 |
| II.11.27 n·α·ε·Ef/(1 − n·α/3) | rationnelle | −1 | 0 of 5 |
| I.10.7 m/√(1 − v²/c²) | racine | −½ | 0 of 5 |
| I.15.10 m·v/√(1 − v²/c²) | racine | −½ | 0 of 5 |
| II.13.23 ρ/√(1 − v²/c²) | racine | −½ | 0 of 5 |
| II.24.17 √(ω²/c² − π²/d²) | racine | ½ | 0 of 5 |
| I.27.6 1/(1/d1 + n/d2) | historique | −1 | 2 of 5 |

The next best fit on F41 is far from it (relative residual 7e-7 at best).
It costs 0.1 s per fit in the median on F41 (0.46 s at most), and 0.85 s at
most on the real data. That seven of the eighteen equations at zero have
this form is what the prototype found; whether the engine recovers them
once seeded is what the campaign measures.

**The change.** `_make_binomial_seeds(xs, ys, cfg)` in `gp_elite/core.py`,
called beside the power-law seeds, on the same rows and with the same
guards. On the scaled columns of constant sign and a target of constant
sign, for t = |y| and t = y², for both directions of the binomial, and for
each monomial g of one to three such columns with exponents in {−2, −1, 1,
2} (three columns only when at most six qualify; at most 4,096 monomials),
c is searched on a fixed grid refined by golden section, and the
exponents of f are fitted by least squares on the logarithms. The best g is
kept only if the residual variance of log t is below 1e-12 of its variance;
the exponents of f are then rounded (half-integers in y) and the form must
still hold below 1e-12 with c fitted again. Each form that holds becomes a
tree, f/(1 + c·g), f·(1 + c·g), f/√(1 + c·g) or f·√(1 + c·g), with the
operators of the active pool (none if a needed operator is missing), and
one copy is placed in each island after the power-law seeds, judged like
every other individual (Levenberg-Marquardt may move c). No random number is
drawn: on data that do not follow such a law to numerical precision, which
includes all real data and all noisy data, nothing is injected and the fit
is that of 0.9.0. Not under `units=` (typed population), not in
extrapolation mode, not outside the generic CSV mode, as the power-law
seeds. Flag `_BINOMIAL_SEEDS` in `gp_elite/core.py`, off by default.

**Mechanics, before any fit.** Flag off: the thirteen reference
configurations identical to the 0.9.0 wheel and the test suite passing. Flag
on: for each configuration, whether a seed was injected; every
configuration without a seed identical to the 0.9.0 wheel. One fit of 30
generations of I.34.1, outside any measurement, shows whether the seed
reaches the returned model.

**Campaign B1** (decides). The decision bench, A (flag off) against B1 side
by side, budget T, four fits at a time: F41, R6 and R7raw, seeds 0 to 4 (335
jobs). The criteria are those of A1, written before it, including the
allowance on small counts. B1 is adopted when all hold:

1. **exact laws:** F41 exact in B1 at least 8 more than in A, among which at
   least 4 more in the five families at zero; and no equation exact in A at
   three seeds or more falls to one seed or none;
2. **real data in the domain:** R6 folds median test R² at least 0.804, and
   the median paired difference over R6 and R7raw folds at least −0.005;
3. **out of domain:** on R6 and R7raw, no more than 2 collapses more than A,
   and the median R² no lower than A's by more than 0.01;
4. **formulas:** no more than 3 formulas flagged inexact more than A on the
   335 fits.

Reported beside the criteria: the fits on which a seed was injected (the
prototype expects none of the 130 real fits), and the time the search for
seeds took.

**Confirmation on new seeds**, if the campaign adopts B1: the same 335 jobs
with seeds 5 to 9 (folds with seed 5). B1 is kept when F41 exact in B1 is at
least 5 more than in A, the median paired difference over the folds is at
least −0.005, and out of domain B1 has no more than 2 collapses more than
A.

The frozen test set is measured once, with the version, as for every change.

### Mechanics of B1, result (12 October 2026)

Flag off: the thirteen reference configurations identical to the 0.9.0
wheel (`phase4_mechanics/compare_0.9.0_vs_B1_off.txt`) and the test suite
passing (145 tests, the three of B1 included; `phase4_mechanics/tests_B1_off.txt`). Flag on: no seed injected in any of the thirteen
configurations (none follows such a form; `trace_B1_on.jsonl`), and all
thirteen identical to the 0.9.0 wheel (`compare_0.9.0_vs_B1_on.txt`).
**Holds.** The fit of I.34.1, 30 generations, seed 0, outside any
measurement (`one_fit_I.34.1.txt`): flag off, an approximation of 1 − R²
9e-3 on the test rows in 11.8 s; flag on, `v0 / (1 - v1 / v2)` exact (1 − R²
2e-28) in 0.6 s, the seed found in 0.09 s. Three tests are added to
`tests/test_guarantees.py` (section 21): the three shapes found exactly, no
seed with the flag off, with 1 % noise, on a power law, on a target that
changes sign or under `units=`, and a short fit of II.11.3. The campaign is
run.

### Campaign B1, result (12 October 2026)

Run from 13:09 to 14:16 UTC, 670 fits, 335 complete pairs, no crash
(`campaign_B1.jsonl`; `python benchmarks/phase2_bench.py summary campaignb1
benchmarks/results_0.9/campaign_B1.jsonl`). The criteria are applied as
written.

1. Exact laws: F41 86 in A, **124 in B1** (+38); the five families at zero
   0 in A, **35 of 90 in B1**; no law lost. The eight equations of the
   prototype go to 5 seeds of 5 each (`I.10.7`, `I.15.10`, `II.13.23`,
   `II.24.17`, `I.34.1`, `II.11.3`, `II.11.27` from 0, `I.27.6` from 2), and
   no other equation changes. **Holds.**
2. Real data in the domain: R6 folds median 0.8095 in both arms; median
   paired difference over the folds +0.0000 (mean +0.0005, worst +0).
   **Holds.**
3. Out of domain: collapses 10 in both arms; median R² 0.647 in both.
   **Holds.**
4. Formulas flagged inexact: 16 in both. **Holds.**

**B1 is adopted by the campaign**; the confirmation on new seeds follows, as
written. Beside the criteria: a seed was injected in 40 fits of 205 on F41,
exactly the eight equations at all five seeds, and in none of the 130 real
fits. Each of the 40 came back exact at the first generation, in 0.8 s at
most, written in the user's variables: `v0 / (1 - v1 / v2)`,
`v0 / sqrt(1 - v1² / v2²)`, `v0 * v1 / (v2 * v3²) / (1 - v4² / v3²)`,
`v0 * v1 * v2 * v3 / (1 - 0.333333 * v0 * v1)`, `v0 / v1 * sqrt(1 - 9.8696
* v1² / (v0² * v2²))` (9.8696 = π²). The search for seeds took 0.09 s in the
median (0.23 s at most); on the real data it does not run when no column or
target has a constant sign (R6, standardised) and takes 0.09 s otherwise
(R7raw). 128 of the 130 real fits return the same expression in both arms;
in the two others no seed was found either, and the arms reached another
number of generations in their 30 s (57 and 55 on `690_visualizing_galaxy`
fold 3, 47 and 48 on `nikuradse_1` fold 1).

The gain is concentrated on the equations the change was built for, found
by a prototype on the training rows of this bench: whether laws of this
shape elsewhere are recovered as well, the frozen test set will say, once,
with the version.

### Confirmation of B1 on new seeds, result (12 October 2026)

Run from 14:17 to 15:24 UTC, 670 fits, 335 complete pairs, no crash
(`confirm_B1.jsonl`; `python benchmarks/phase2_bench.py summary confirmb1
benchmarks/results_0.9/confirm_B1.jsonl`), seeds 5 to 9 never run on this
bench.

1. F41 exact: 86 in A, **126 in B1** (+40, at least +5 required); the five
   families at zero 0 in A, 36 in B1: the same eight equations at all five
   seeds (`I.27.6` from 1), and `I.50.26` once (seed 7, a trigonometric law
   on which no seed was placed: the run-to-run variation of the search).
   **Holds.**
2. Folds: median paired difference +0.0000. **Holds.**
3. Out of domain: collapses 17 in both arms. **Holds.**

**B1 is confirmed and adopted.** Again a seed was placed in exactly 40 F41
fits, each exact at the first generation (1 s at most), and in none of the
130 real fits; 127 of these return the same expression in both arms, the
three others reaching another number of generations in their 30 s.

The flag `_BINOMIAL_SEEDS` is now on by default. With it on, the thirteen
reference configurations are still identical to the 0.9.0 wheel
(`phase4_mechanics/compare_0.9.0_vs_B1_default.txt`, none of them has such a
form) and the test suite passes (145 tests,
`phase4_mechanics/tests_B1_default.txt`). The campaign and the confirmation
can be run again from this commit (`campaignb1`, `confirmb1`: arm A turns
the flag off); in every other run, arm A is the engine as it stands, B1
included. The frozen test set is measured with the next version.

### Where phase 4 stands

The target of gate 2 for the five families at zero, at least 20 of 90 with
the gain confirmed on seeds 5 to 9, is met by B1 alone: 35 of 90, then 36 on
the new seeds. What remains at zero: the trigonometric laws (where the
measurements of 4a stand), the exponentials and the logarithm, and
`III.10.19` (a root of a sum of three squares). Next in the plan: 4c,
columns of order one left as given.
