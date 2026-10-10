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

## Result (10 October 2026, 01:51 to 02:05 UTC)

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
