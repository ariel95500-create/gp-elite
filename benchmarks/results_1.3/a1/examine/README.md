# Why A1 was not adopted: the results

The examination of `PLAN.md`, run on 9 November 2026 after campaign A1
(`../campaign/compare_a1.txt`). It decides nothing; the author decides what
follows.

## The answer

The search does draw the arcsine: 24 of the 200 formulas of B on Dtrig have
one. But two things stand in the way of the laws.

1. **The laws need the arcsine with constants inside it, and the search
   rarely builds them.** The engine divides each variable by its largest
   value before the search (`_ShiftFreeScaler`). So in its internal
   variables, the law needs a constant inside the arcsine to undo those
   scales:
   - I.26.2 is arcsin(0.988 · X0 · sin(4.97 · X1));
   - I.30.5 is arcsin(c · X0 / (X1 · X2));
   - Snell's law is arcsin(c · sin(c′ · X0)).

   The fit of constants, and the polish, adjust the constants a formula has.
   They cannot add one it lacks. Meanwhile the search finds algebraic curves
   very close to the laws first. Some come within the thresholds of the
   benches: I.30.5 seed 0 is exact by the bench's test (1 − R² of 3.4e-11)
   with tanh, and one fit of E2a passes the TP law test with no arcsine.
2. **On the TP, the noise hides the law.** In all 40 fits of TPsnell, the
   formula returned differs from the law by less than the noise added. So
   even the form of the law, if it were offered, could not win the
   selection: the selection keeps the smallest formula among those the data
   cannot tell apart.

## E1, the arcsine laws of F41

`e1_records.jsonl`, `e1_classes.txt`, from the tool of
`../../../results_1.2/end_of_search/`. All ten fits kept their status of
the campaign.

- **I.26.2 seed 4 and I.30.5 seed 0** are exact. Only I.26.2 seed 4 writes
  the law, `arcsin(sin(v1) * v0)`.
- **The eight others** are in class 1: no candidate that the polish makes
  exact was ever offered.
- **I.26.2 seed 2 is the closest:** it returns
  `0.982939 * arcsin(1.0119 * v0 * sin(0.999714 * v1))`, near at 1 − R² of
  8e-4. Its internal tree is `-0.000573 + 0.982939 * arcsin(X0 * sin(4.964236 * X1))`.
  There is no constant on X0 inside the arcsine, and the printed 1.0119 is
  the scale of X0, 1/0.98824. Given that constant, the engine's own polish
  makes the form exact from three starts, as far off as 0.9 and 1.05: 1 − R²
  of 0 to 1.3e-31 on the test rows.

## E2a, Snell's law on clean data

`e2a_A.jsonl`, `e2a_B.jsonl`: the plain arm under the API defaults, without
noise, 10 and 20 points, seeds 0 to 4.

| | fits | formulas with the arcsine | law by the TP test |
|---|---|---|---|
| A, 1.2.0 | 10 | 0 | 0 |
| B, with the arcsine | 10 | 0 | 1, with no arcsine (2.4e-10) |

On clean data the formulas of B are within 2.4e-10 to 8.4e-6 of the law
(`err_law`), and none is the law. The search under the defaults stops after
20 to 59 generations, and it has not built arcsin(c · sin(c′ · X0)) by
then.

## E2b, how far the law stands from the curves returned

`e2b.txt`, the 40 fits of TPsnell in B. The table compares two figures:
- the noise added, as 1 − R² of the noisy targets against the law, from
  1.3e-3 to 2.3e-2;
- the error of the formula returned, refitted on the clean rows, from
  2.6e-4 to 1.6e-2.

The second is below the first in all 40 fits: a median of 0.2 of the
noise, and at most 0.99. With 10 or 20 points at 2 % or 5 % noise, the data
cannot tell the law from the curve returned.

## What could follow

For the author to weigh:
- **(a) An arcsine with its constant.** The search would draw the arcsine of
  a constant times its argument, arcsin(c · u). That is the form all three
  laws need, and it would need a plan of its own, measured as A1 was. It
  would not change E2b: on the TP, the law would still lie within the noise
  of a smaller curve.
- **(b) A seed of the arcsine of a monomial,** beside the seeds of phase 4a,
  which already offer a function of a monomial. It would reach I.30.5, whose
  argument λ/(n·d) is a monomial. It would not reach I.26.2 or Snell's law.
- **(c) A1 left out of 1.3,** as C1 was left out of 1.2. Its code is
  withdrawn, its scripts and records stay, and the page of the limits says
  why the arcsine laws are missed, with these figures.
