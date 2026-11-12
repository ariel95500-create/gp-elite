# Mechanics of N2

Done on 12 November 2026, after N2 was written (commit f748793) and before
any fit of its campaign. Plan: `../../PLAN.md`, "Mechanics of N2".

- **A** is 1.3.0 installed from PyPI (`/venv13p`).
- **The candidate** is this repository at f748793. The wheel built from it
  for the campaign (`/venv14n2`) has its 11 `gp_elite/` files identical to
  that commit.
- Every fit and every stage runs in its own process, `PYTHONHASHSEED=0`, one
  BLAS thread, 4 at a time on 4 cores.
- Scripts: `finders_dump.py` with `compare_dumps.sh` (item 1, the finders),
  and `mechanics.py` (items 1 to 6). Outputs: `compare_dumps.txt`,
  `mechanics.txt`, and the records in `records/`.

## What holds

1. **The exact seeds are untouched.**
   - *The finders.* The power-law, binomial and elementary finders, called
     with their exact thresholds and with their thresholds lifted (the
     first pass of the noise-tolerant stage, the one 1.3.0 runs), return the
     same values with 1.3.0 and with the candidate, byte for byte: 3,960
     calls on 660 tables (F41 with and without noise, the TP tables of draws
     0 to 4, R7raw at fold 0, each raw and scaled).
   - *The 95 bounded fits.* Where the noise-tolerant stage of 1.3.0 does not
     run (32 fits), the model of the candidate is that of 1.3.0 in all 32.
     Where it runs (63 fits), the model is the same in 57. The six others
     are reported in `mechanics.txt`: on I.16.6, I.26.2 and I.37.4, with and
     without units, the test 1 − R² moves between 4e-5 and 0.0135, in both
     directions. The exact laws are 32 of 41 with both, in F41 and in U41.
2. **No seed is lost.** On the 82 noisy targets of F41 (seed 0, 1 % and
   10 %), the stage runs on all 82.
   - With N2 switched off, the candidate prints the seeds 1.3.0 from PyPI
     prints, on 82 of 82.
   - 1.3.0 places a seed on 47 targets, and every form it places is placed
     by the candidate, on 47 of 47.
   - A seed with the structure of the law is placed on 22 targets of 41
     with 1.3.0 and 30 with the candidate at 1 % noise, and on 13 and 19 at
     10 %. None is lost.
3. **The second pass.** At 1 % noise, on the five equations, a candidate
   with the form of the law is made and placed:

   | equation | 1 % noise | 10 % noise |
   |---|---|---|
   | I.40.1 | made and placed | not made (the law leaves 1.2 %) |
   | II.35.18 | made and placed | not made (0.9 %) |
   | II.11.27 | made and placed | not made (1.0 %) |
   | I.32.5 | made and placed | made and placed |
   | III.19.51 | made and placed | made and placed |

   At 10 % noise the item does not hold for three equations: see below.
4. **The best kept.** On III.15.12 with 1 % noise the trigonometric seed in
   k·d is placed (score 1.1e-4). On I.44.4 with 1 % noise the form with the
   logarithm, `n·kb·T·log(4.94·V)` in the internal variables, is among the
   candidates and is placed (score 9.6e-5).
5. **The real data.** On the 13 real fits of item 1, no candidate is within
   the threshold, as with 1.3.0. R6 has no candidate: its columns change
   sign. On R7raw the best scores are 0.039 (561_cpu) and 0.041
   (nikuradse_1); the threshold is 0.015.
6. **The time of the stage.** On the 82 noisy targets, median 0.21 s,
   largest 0.78 s. On the 63 bounded fits where it runs, median 0.002 s and
   largest 0.95 s, against 0.001 s and 0.27 s with 1.3.0.
7. **Tests.** The test suite passes, 188 tests, with six new ones on items 2
   to 4 (`tests/test_guarantees.py`, section "1.4, N2"). One check of
   section 23 was made exact: it read the residual of the first seed on the
   noiseless target with the seed's own constants (below 1e-6). Its
   constants are now fitted on the noisy rows, so that residual is 1.4e-6.
   The check now refits the seed on the noiseless target, as its comment
   always said, and asks for 1e-9.

## One rule beyond the letter of the plan

Item 4 failed at first on I.44.4: no candidate with the logarithm had the
structure of the law. The cause is a fourth rule of the finders written for
exact data. The finder of the logarithm reads the exponents of g from the
coefficients of y/f on the log|x_j|, which are b·e_j, and divides them by
the smallest coefficient above 1e-6. Under noise an exponent that is zero
has a coefficient of the order of the noise, and that coefficient becomes
the divisor: on a table n·log(V2/V1) with 1 % noise, -0.009 for log n, so
that the exponents of V2 and V1 came out as 564 and -566 instead of 1 and
-1, and the form was refused.

In the noise-tolerant stage only (the scan of the logarithm and its second
pass), a coefficient below a twelfth of the largest now counts as zero
(`_log_g_exponents`). The exponents kept, half-integers of at most 6 once
divided by the smallest, are never below a sixth of the largest, so on
exact data the rule gives what the old one gives. The exact finder is
unchanged (item 1).

## What does not hold, and why

Item 3 does not hold at 10 % noise for I.40.1, II.35.18 and II.11.27. Their
law leaves 0.9 % to 1.2 % of the variance, within the threshold, but no
candidate has its form.
- **I.40.1 and II.35.18** decay as exp(−u), with u from 0.04 to 125 on the
  inputs of the bench. Most rows have a target of the order of the noise.
  The informative rows are those where u is small, and there the finder
  works on log(a − log|y|), where a noise of 10 % on y is magnified by
  1/u. The weight y², right for log|y|, is not the weight this nested
  logarithm calls for.
- **II.11.27**: the binomial finder keeps, for each power, the argument g
  that its least squares on logarithms prefer. With 10 % noise it prefers
  n·α·E to n·α and rounds the exponents of f wrongly, so the form of the law
  is never built.

The second pass was designed for the sign that noise breaks near zero, the
cause the review traced at 1 %; at 1 % it holds on all five.

**Tried and not kept.** Choosing by the score in every finder, as the plan
does for the sine, the cosine and the logarithm, was measured on the same 82
targets (the exponential, the hyperbolic tangent, 1/cosh, the arcsine and
the binomial forms returning their three best forms by the score). It
places a seed with the structure on 22 targets at 10 % noise instead of 19
(I.15.10, II.13.23 and II.24.17 more), none of the three above, and the
median time of the stage goes from 0.21 s to 0.45 s. It is not in N2.

## Two effects to know

- **Constants held twice are fitted separately.** The fit of constants of
  the engine fits every constant of a tree, as it does for any tree of the
  search. So the ω of the sine and that of the cosine of a trigonometric
  seed, and the c of the two exponentials of 1/cosh, become separate
  constants: on III.15.12 the seed placed reads
  `v0·(1.002 − 0.828·sin(0.062·v1·v2) − 0.996·cos(3.925·v1·v2))`. Refitted
  on the noiseless target it is the law, to 1e-9.
- **The bounds of the fit.** The fit of constants keeps every constant
  within three times the range of the random constants, ±15. A seed whose
  inner constant the finder put beyond it keeps that constant: the fit
  cannot move it. This was already so in 1.3.0 for every tree of the search.
