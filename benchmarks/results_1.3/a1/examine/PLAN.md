# Why A1 was not adopted: plan of the examination

Written on 9 November 2026, after campaign A1 (`../campaign/compare_a1.txt`)
and before any fit of this examination. The plan of 1.3 says: "If A1 is not
adopted, the cause is examined and reported to the author before any second
version." This examination decides nothing and changes nothing in the
engine. The frozen test set is not used. Method as before: one process per
fit, `PYTHONHASHSEED=0`, one BLAS thread, four fits at a time.

## The two failures

1. **The arcsine laws of F41:** 2 exact of 10 in B. Only one writes the
   arcsine (I.26.2 seed 4); I.30.5 seed 0 is an approximation with tanh.
2. **Snell's law on TP:** 0 of 40 in B. One model of 40 has an arcsine.

## E1, the arcsine laws of F41

The ten fits of I.26.2 and I.30.5 at 30 s, seeds 0 to 4, are run again with
B. The tool of the diagnostic of the end of the search
(`../../../results_1.2/end_of_search/diag.py`) observes them, and
`classify.py` puts each fit that is not exact in one of its six classes. It
answers whether the search offered a candidate that the polish makes exact,
and if so where it was lost. The expressions of the candidates within reach
say whether they write the arcsine.

## E2, Snell's law on TP

Two questions:
- **E2a, clean data:** the fits of TPsnell's plain arm under the API
  defaults, with A and with B, on the same rows without noise: 10 and 20
  points, with the seeds of draws 0 to 4, so 10 fits per engine (with one
  input the rows are the same at every draw, only the seed changes). If B
  returns the law on clean data and not with noise, the search finds the
  arcsine, and the noise is what hides it.
- **E2b, how far the law stands from the curves returned:** on each of the
  40 fits of TPsnell in B, the noise added, as 1 − R² of the noisy targets
  against the law on the training rows, beside the error of the formula
  returned, refitted on the clean rows (`err_law`, recorded by the
  campaign). When the second is well below the first, the data cannot tell
  the two apart: with 10 or 20 points, the law and the curve differ by less
  than the noise. E2b runs no fit.

## Records

In this folder: the scripts, the records, and a README with the figures,
written after the fits. The cause is reported to the author with them.
