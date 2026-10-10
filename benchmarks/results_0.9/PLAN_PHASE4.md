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
