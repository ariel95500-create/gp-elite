# Trigonometric laws and the scaling of the inputs — diagnostic, plan written before it

Written on 10 October 2026, before any fit of this diagnostic. It decides
nothing: it tests an explanation, and a change it may suggest gets its own
plan, trial and campaign (phase 4 of the plan).

## Why

The comparison with gplearn (`COMPARE_GPLEARN.md`) found six trigonometric
laws that gplearn recovers and gp-elite does not (`I.18.12` r·F·sin θ and
`II.15.4` −μ·B·cos θ). gplearn sees the variables as given; gp-elite, with
`normalize="auto"`, divides each column by its largest absolute value before
the search, so `sin(θ)` must be written `sin(k·u)` with an unknown `k`
inside the function, and its formulas show it looking for that constant.
Explanation tested: the scaling of the inputs is why gp-elite misses these
laws.

## The fits

- The ten F41 equations whose operator pool is `"trig"` (`II.15.4`,
  `I.18.12`, `III.15.12`, `I.26.2`, `I.30.5`, `I.37.4`, `I.50.26`,
  `II.6.15b`, `III.9.52`, `III.17.37`), seeds 0 to 4, and the two controls of
  phase 2 (`I.8.14`, `II.2.42`, seeds 0 to 4): 60 jobs.
- Two arms side by side, as in phase 2: A, the engine of this branch (that
  of 0.8.0) with `normalize="auto"`; N, the same with `normalize="none"`
  (the variables as given). Budget T (30 s), one process per fit,
  `PYTHONHASHSEED=0`, four fits at a time. No engine change.

## What is reported

Exact, near and missed laws per arm, by equation and fit by fit, with the
formulas. Expectation written before: if the explanation holds, N finds
several of the trigonometric laws that A misses (A found 2 of 50 in the
baseline, gplearn 7); the controls show what `normalize="none"` costs
elsewhere, which a change would have to avoid.

## Result (10 October 2026, 01:47 to 02:01 UTC)

120 fits, 60 complete pairs, no crash (`trig_diag.jsonl`; `python
benchmarks/phase2_bench.py summary trig benchmarks/results_0.9/trig_diag.jsonl`).

| group | arm | EXACT | NEAR | MISS | median generations |
|---|---|---|---|---|---|
| ten "trig" laws (50 fits) | A, `normalize="auto"` | 2 | 5 | 43 | 70 |
| | N, `normalize="none"` | **13** | 8 | 29 | 68 |
| controls (10 fits) | A | 7 | 2 | 1 | 78 |
| | N | 8 | 0 | 2 | 23 |

- **The explanation holds.** With the variables as given, `I.18.12` is
  exact at 5 seeds of 5 (1 in A) and `II.15.4` at 5 of 5 (1 in A), as plain
  formulas: `v0 * v1 * sin(v2)`, `-v0 * v1 * cos(v2)`; `III.17.37` 2 of 5 and
  `III.15.12` 1 of 5, from 0. Five of the ten laws stay at zero in both arms
  (`I.26.2`, `I.30.5`, `I.37.4`, `I.50.26`, `III.9.52`).
- **The controls are not hurt here**: `I.8.14` exact at 5 seeds of 5 (4 in
  A), found in a few seconds (median generations 23: the search stops on the
  exact law), written without constants, `sqrt((v0 - v1)² + (v3 - v2)²)`;
  `II.2.42` 3 of 5 in both arms, not the same seeds.
- This is ten equations of F41 and two controls: what the scaling does to
  the rest of F41 and to real data is not known from it.

Under `normalize="smart"` (an option of the engine since 0.7: no scaling when
the standard deviations of the columns are within a factor 10 of each other,
`divmax` otherwise), every F41 equation and every R6 dataset would be fitted
unscaled, and four of the seven R7raw datasets (`561_cpu`, `547_no2` and
`nikuradse_1` keep `divmax`, their columns differing in scale by 190 to
1,660 times). The next step is the campaign of that default.

## Change S1, plan written before its campaign (10 October 2026)

**The change.** The default of `normalize` becomes `"smart"` instead of
`"auto"` (`divmax`): the inputs are left as given when their columns have
comparable scales (standard deviations within a factor 10), and divided by
their largest absolute value otherwise, as today. No other change; the
explicit options keep their meaning. Measured through the public argument
(arm S: `normalize="smart"`; arm A: the default of 0.8.0), so the engine is
not modified before the decision.

The diagnostic above, whose numbers were read before this plan, stands for
the targeted trial: S1 goes to the campaign.

**Campaign S1** (decides). The decision bench, A against S side by side,
budget T, four fits at a time: F41, R6 and R7raw, seeds 0 to 4 (335 jobs).
S1 is adopted when all hold:

1. **exact laws:** F41 exact in S at least 10 more than in A, and no equation
   exact in A at three seeds or more falls to one seed or none in S (a
   change of the search paths reshuffles single seeds; a law must not be
   lost);
2. **real data in the domain:** R6 folds median test R² at least 0.804, and
   the median paired difference over R6 and R7raw folds at least −0.005;
3. **out of domain:** on R6 and R7raw together, no more collapses than A, and
   the median R² no lower than A's by more than 0.01;
4. **formulas:** no more formulas flagged inexact on the 335 fits than in A.

**Confirmation on new seeds**, if the campaign adopts S1: the same 335 jobs
with seeds 5 to 9 (folds with seed 5), never run before. S1 is kept when F41
exact in S is at least 5 more than in A, the median paired difference over
the folds is at least −0.005, and out of domain S has no more collapses than
A. Otherwise S1 is not adopted.

The frozen test set is measured once, with the version, as the plan of 0.9
says.

## Campaign S1, result (10 October 2026)

Run from 02:03 to 03:13 UTC, 670 fits, 335 complete pairs, no crash; the
machine of the session restarted once, after 323 fits, and the run resumed
(`campaign_S1.jsonl`; `python benchmarks/phase2_bench.py summary campaigns1
benchmarks/results_0.9/campaign_S1.jsonl`). The criteria are applied as
written.

1. Exact laws: F41 87 in A, **103 in S** (+16); no law lost (`I.18.12` 1 to
   5 seeds, `II.15.4` 1 to 5, `I.44.4` 0 to 4, `III.17.37` 0 to 2,
   `III.15.12` 0 to 1, `I.6.20a` and `I.8.14` 4 to 5; `I.11.19` 1 to 0).
   **Holds.**
2. Real data in the domain: R6 folds median 0.810 in A, 0.831 in S; median
   paired difference over the folds +0.0000 (worst −0.097). **Holds.**
3. Out of domain: collapses 10 in A, 11 in S, and the median R² 0.647 in A,
   0.574 in S. **Fails.** S removes the deep collapses of A on `228_elusage`
   (−232.5 to −0.11, −224.2 to −1.37), `210_cloud` (−19.9 to 0.09) and
   `561_cpu` (−2.57 to 0.97), and creates others, deepest `210_cloud` in its
   units, seed 2 (0.685 to −183.8).
4. Formulas flagged inexact: 15 in A, 25 in S. **Fails.** The new ones are
   on real data left unscaled (`210_cloud`, `690_visualizing_galaxy`,
   `228_elusage`), whose values reach 9 to 133: the engine's safety nets
   (a power's base clipped at 100, a value capped at a million) were set for
   inputs scaled to about 1, and act more often on raw values.

**S1 is not adopted.** On F41 it is the largest gain measured on this bench
since 0.8; on real data it changes most models (55 of 60 R6 fits, 31 of 70
R7raw fits) without a gain in the domain and with losses out of domain. The
benefit lies with laws of physical quantities of moderate size, and above
all with angles inside trigonometric functions; the cost with real data
whose raw values are large.

## Change S2, plan written before it is implemented (10 October 2026)

**The change.** With an operator pool that contains trigonometric functions
(`"trig"` or `"full"`), `normalize="auto"` behaves as `"smart"`: inputs whose
columns have comparable scales are left as given. With every other pool,
including the default `"physical"`, nothing changes. The reason: scaling an
input multiplies it by a constant, which a product, a quotient or a power
absorbs into its own constant, but which changes the period of a sine or a
cosine; that is where the diagnostic and campaign S1 found the gain. The
rule is derived from S1, whose numbers were read before this plan, so it is
confirmed on new seeds before adoption. Flag `_TRIG_SMART` in
`gp_elite/core.py`, off by default, read by `symbolic_regression`.

**Mechanics, before any fit.** With the flag on, the thirteen reference
configurations return the same models as gp-elite 0.8.0 (none of them uses a
trigonometric pool with `normalize="auto"`), and the test suite passes.

**Campaign S2** (decides), A against S2 side by side, budget T, four fits at
a time. The decision bench is unchanged by construction outside the ten F41
laws of the `"trig"` pool, so the campaign runs:

- part 1: those ten laws, seeds 0 to 4 (50 jobs);
- part 2: R6 and R7raw, folds and out of domain, seeds 0 to 4, with
  `operators="trig"` in both arms (130 jobs), for a user who asks for
  trigonometric functions on real data.

S2 is adopted when all hold:

1. part 1: exact laws in S2 at least 5 more than in A, and no law exact in
   A at three seeds or more falls to one or none;
2. part 2, in the domain: the median paired difference of test R² over the
   folds at least −0.005;
3. part 2, out of domain: no more collapses than A, and the median R² no
   lower than A's by more than 0.01;
4. part 2: no more formulas flagged inexact than in A.

**Confirmation on new seeds**, if the campaign adopts S2: part 1 with seeds
5 to 9; S2 is kept when its exact laws are at least 5 more than A's.

### Mechanics of S2, result (10 October 2026, 03:17 to 03:24 UTC)

With the flag on, the thirteen reference configurations return the same
models as the 0.8.0 wheel (`phase2_mechanics/compare_0.8.0_vs_S2_on.txt`);
the test suite passes with the flag off (140 tests). **Holds.** The campaign
is run.
