# I.18.12 with 10 % noise under units: plan written before the fits

Written on 9 November 2026, after M2 (`../compare.txt`) and before any fit
below. It decides nothing about the release: the criteria of M2 are met,
and what follows goes to the author at gate 10 with M2.

## What M2 saw

Feynman I.18.12, τ = r·F·sin θ, θ drawn in [0, 3.14], is in the pool
`trig`. Its structure is retrieved in every fit of F41N1, F41N10 and U41N1
with both versions, but on U41N10 (10 % noise, under units, seeds 0 to 4)
in 5 fits with 1.2.0 and 1 with 1.3.0. Every one of these fits reached its
budget of 30 s, with both versions.
- **1.2.0** returns `1.00965 * v0 * v1 * sin(0.999585 * v2)` at every seed.
- **1.3.0** returns that formula at seed 4. At seeds 0 to 3 it returns a
  parabola in θ, such as `(1.24557 * v2 - 0.397444 * v2²) * v1 * v0`. On
  [0, π] that parabola stays close to sin θ.

The two versions see the same data. One question follows: is it a loss of
1.3.0 on this law, or the draw of five seeds, under a time budget, of two
searches whose random draws differ once the pool has one more operator?
In all, U41N10 has 3 fewer structures (98 to 95), at the limit of the
criterion: I.18.12 loses 4, II.6.15b loses 1, and III.15.12 gains 2.

## E1, twenty new seeds

The bench of M2 (`phase1_bench.py run-paired`, from the same copy of
`benchmarks/` of commit 7a09425, `/home/user/m2_13_run`). The engines are
those of M2: 1.2.0 in `/venv12p`, 1.3.0 in `/venv13r`. Each job runs with
both versions at the same time, two jobs at a time, T of 30 s:
- `--problems I.18.12`;
- `--kinds ufeyn_n10,feyn_n10`, the second as a control without units;
- `--seeds 5,...,24`: 20 seeds never run in M2, so 40 jobs per version,
  about 10 minutes.

Records: `e1_1.2.0.jsonl` and `e1_1.3.0.jsonl` in this folder. The
comparison is `examine.py`, written and committed before the records are
read.

## How it is read, written before

On U41N10, over the 20 new seeds:
- **A loss of 1.3.0:** 1.3.0 retrieves the structure in at least 4 fewer
  fits than 1.2.0. Then the pages of the limits and the CHANGELOG say so,
  with these figures, and the author decides at gate 10 whether to publish
  as is.
- **The draw of the seeds of M2:** the difference is 3 fits or fewer. Then
  M2 is reported as measured, with this result beside it.

F41N10 is reported the same way. Reported beside:
- the formulas of the fits without the structure;
- how many of them have the arcsine;
- the generations run.
