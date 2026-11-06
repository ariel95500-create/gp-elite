# What GP_ELITE does not do

*[Version française](LIMITATIONS.fr.md)*

This page lists what the engine does not do, or does badly, each point with the
measurement behind it. Unless a point says otherwise, the figures were measured on
the package of version 1.0.0,
side by side with 0.9.0, on the decision bench (41 Feynman equations, five seeds,
30 seconds per fit; 7 real datasets) and on a test set frozen before any of the
work of 1.0 (78 other Feynman equations, 14 Strogatz systems, 25 real datasets):
`benchmarks/results_0.9/release_1.0/`. Version 1.1 changes the units mode only.
Without units it returns the models of 1.0.0 at equal work; under the budget of
30 s, the counts move a little from one campaign to the next, for both versions
(measured beside 1.0.0 for the release of 1.1, both give 108 and 86
structures under noise, 8 exact Strogatz fits of 70 and 10 collapses of 65, where
the points below say 105, 85, 7 and 11; on the printed formulas that depart from
their model, point 6, 7 of 130 and 66 of 500 for 1.0.0 and 8 and 67 for 1.1.0,
where it says 7 and 61). Point 8 is measured on the package of
1.1.0, side by side with 1.0.0 (`benchmarks/results_1.1/release/`), but for the
times of its first bullet, measured on 1.2.0 beside 1.1.0; point 10 on the
campaign that decided the stop of 1.2.

With a budget set and `patience=` left alone, version 1.2 leaves the models
alone without units; under units, it changes only the fits whose typed start
needs a product of 9 to 12 factors or reaches its deadline (on the bench,
Feynman III.19.51). Measured
beside 1.1.0 for the release of 1.2 (`benchmarks/results_1.2/release/`, the
figures in `m2/limits_figures.txt`), both versions give the same figure on every
point, and from one campaign to the next the figures move as above: 214 exact
laws of 390 on the test set (204 of 290 and 10 of 100), 33 of its equations
never recovered, 10 exact Strogatz fits of 70, 108 and 85 structures under
noise, 10 collapses of 65 (the worst to −1,946) and 66 of 250 on the test set
(38 standardised, 28 in their own units), 12 departing formulas of 130 and 65 of
500, and under units 166 exact laws of 205. What 1.2 changes is the time of a
fit under the defaults, and with it some of the models (points 8 and 10).

## 1. Laws it still misses

On the 41 equations, the engine returns the exact law in 163 fits of 205 (0.9.0:
88). Seven equations are never recovered:

- **an arcsine**, `I.26.2` arcsin(n·sin θ) and `I.30.5` arcsin(λ/(n·d)): no
  operator pool of the engine has the arcsine;
- **a sum of terms, one of them trigonometric**, `I.37.4`
  I1 + I2 + 2·√(I1·I2)·cos δ and `III.17.37` B·(1 + α·cos θ);
- **nested or shifted arguments**, `I.50.26` x1·(cos ωt + α·cos² ωt) and
  `III.9.52`, a sine of (ω − ω0)·t/2;
- **the root of a sum of three squares**, `III.10.19` m·√(Bx² + By² + Bz²).

A sum of three products, `I.11.19`, comes back once in five fits. On the 78
equations of the test set, 34 are never recovered.

## 2. The gains are smaller away from the bench they were built for

The changes of 1.0 (B1, E1, and N1 for noisy data) fit families of forms directly;
each family was chosen from a prototype run on the training rows of the 41
equations of the bench, where they take the exact laws from 88 to 163 (+85 %). On
the 78 equations of the test set, frozen before this work and measured once, the
exact laws go from 145 to 213 of 390 (+47 %): 203 of 290 fits on the 58 equations of
the main Feynman table (0.9.0: 144), but 10 of 100 on its 20 bonus equations
(0.9.0: 1). On the 14 Strogatz systems, the engine does no better: 7 exact fits of
70 on the test rows, against 8.

## 3. Noise

With Gaussian noise on the training target, the structure of the law (the model
returned, its constants refitted on clean data, reproduces the clean test rows) is
retrieved in 105 fits of 205 with 1 % noise and 85 with 10 % (0.9.0: 67 and 66).
The constants of the returned formula carry the noise: with 1 % noise,
`0.00115247 + 1.00099 * v0 / (1 - 0.997137 * v1 / v2)` for v0/(1 − v1/v2)
(Feynman I.34.1).
Above 10 % the engine has not been measured.

## 4. Real data, out of the training range

A formula that fits is not a law. On the 7 real datasets of the bench (each in its
own units, six of them standardised too), predicting the 20 % of rows farthest
from the centre of the data, 11 models of 65 collapse (test R² below zero), the
worst to −233; on the 25 real datasets of the test set, 64 of 250 (37 of 125
standardised, 27 in their own units). 1.0 changes nothing there: 0.9.0, measured
beside it, gives the same counts. On the test set the collapses concentrate on a
few datasets: six of the 25 account for 28 of the 37. Keep rows out of the fit to judge a formula, and look at the Pareto
front: on real data the readable answer is often a short entry of the front, not
the returned champion.

## 5. Exact data that no seed covers

When data follow a law exactly but no exact seed covers it, a seed that only
approximates the data can draw the search away from the law. Seen on Kepler's law
normalised by min-max (`normalize="minmax"`): exact in 1 fit of 10 instead of 3 at
40 generations (`release_1.0/m3/kepler_minmax_check.txt`). With the default
normalisation, on the bench, no law was lost this way: no equation has fewer exact
fits than with 0.9.0. `PLAN_PHASE5.md`, mechanics of N1.

## 6. A formula that departs from its predictions

Protected operations (a division by almost zero, a power capped at a million) keep
the predictions finite; when one of them acts on your data, the printed formula
departs from `predict()`. The engine then says so (`formula_exact` is False, with a
warning that names the exact formulas of the Pareto front). On the real data this
happened in 7 fits of 130 on the bench and 61 of 500 on the test set.

## 7. The same seed on another machine

From four cores, the islands run in parallel by default and can return another
model than in sequence; with `time_limit=`, the generations reached depend on the
speed of the machine. `parallel=False` and a number of `generations` give the same
model on every run of a given machine; across processors, results can still differ
in the last digits and then in the model.

## 8. Physical units

Under `units=`, the population is typed, and a typed generation costs about 1.4
times an untyped one (measured in phase 3, `PLAN_PHASE3.md`). Since 1.1 the seeds
of the power law, of B1, E1 and N1 act under units too, each placed only if it
passes the gate of dimensions. On the 41 equations with their units, the engine
returns the exact law in 165 fits of 205 (1.0.0: 108), and six equations are never
recovered in five seeds (1.0.0: 13). What remains:

- **noisy data run the whole budget the call sets.** With `generations=` or
  `time_limit=`, a search stops early only on an exact law, and with noise there
  is none, even when the seed placed at the start is the law. Under the
  defaults, since 1.2, the stop of point 10 ends it: the six fits of the French
  TP notebook (`examples/tp_six_lois.ipynb`, ten points and 2 % noise each) take
  7 to 10 s each, against 28 to 37 s with 1.1.0 on the same machine, with the
  same formulas;
- **fitted exponents.** Under units, a seed with exponents fitted to the data is
  placed only if each exponent that is not a half-integer falls on a dimensionless
  input. Exponents such as 1.0041 on a quantity in moles cannot be dimensionally
  sound, and with `unknown_constant=True` such a seed made the typed search look
  for fractional units: the gas law of the TP notebook took 78 s instead of 50 s
  before 1.1.0 was corrected (`benchmarks/results_1.1/PLAN_U2.md`). The seed with
  the exponents rounded to half-integers is placed as before.

## 9. Size and kind of data

GP_ELITE is plain Python and NumPy. It is meant for a hundred to a few thousand
rows and up to about ten variables, the range of its measurements (10,000 rows at
most, in the size study); beyond, nothing is measured, and the search space grows
quickly with the number of variables. It is not meant for chaotic sequences, nor for large datasets where
raw accuracy matters more than a formula you can read: ensemble models or engines
such as PySR and Operon serve those better.

## 10. The stop under the defaults

Since 1.2, a call that sets neither `generations` nor `time_limit` stops its
search once the error on the hold-out rows (on the training rows when there
are none) has not improved by 1 % in 30
generations (`patience=`). The stop can end a search that would still have
improved. On the decision bench run under the defaults, five seeds, against
1.1.0 measured beside it (campaign H1 of `benchmarks/results_1.2/PLAN.md`, on
the candidate with the stop): 161 exact laws of 205 against 163, and 166
against 167 with units; with 10 % noise, the structure in 83 fits against 85,
and 100 against 99 with units; with 1 % noise, a few fewer approximate laws (146
against 153); on the six standardised real datasets, a median test R² of 0.802
against 0.809, and on the 65 fits out of the training range of the seven real
datasets, 9 collapses against 11. The median
fit on noisy and real data took 7 to 9 s against 25 to 35 s. When the result
matters more than the time, set `generations=` or `time_limit=`, or
`patience=0`.
