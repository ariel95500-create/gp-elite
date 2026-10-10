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
