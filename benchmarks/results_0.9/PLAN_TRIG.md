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
