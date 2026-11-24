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

Version 1.3 adds the arcsine to the pools `trig` and `full`, and leaves the
pool `physical`, the default, as it was: with it, the models of 1.2 at equal
work. Measured beside 1.2.0 for the release of 1.3
(`benchmarks/results_1.3/release/`, the figures in `m2/limits_figures.txt`),
1.3.0 gives:
- 171 exact laws of 205 on the decision bench against 163, with five
  equations never recovered against seven (point 1);
- 116 and 87 structures under noise against 108 and 85;
- under units, 174 exact laws of 205 against 166, with four equations never
  recovered against six.

Elsewhere the two versions give the same figures, or figures that move as
they do from one campaign to the next. The figures of 1.3.0 are given first:
- on the test set, 214 exact laws of 390 against 213 (204 and 203 of 290, 10
  and 10 of 100), with 33 of its equations never recovered against 34;
- 8 exact Strogatz fits of 70 with both;
- 10 collapses of 65 with both (the worst to −1,946), and 65 of 250 on the
  test set with both (37 standardised, 28 in their own units);
- 11 departing formulas of 130 with both, and 65 of 500 against 64.

Version 1.4 gives the noise-tolerant seeds more forms. Where those seeds are
the same in both versions and neither reaches its time budget, the recorded
formula (its first 160 characters), the error on the test rows and
`formula_exact` are those of 1.3.0, to the bit (782 fits of the release
measurement). Measured
beside 1.3.0 for the release of 1.4 (`benchmarks/results_1.4/release/`, the
figures in `m2/limits_figures.txt`), 1.4.0 gives:
- 152 and 95 structures under noise against 116 and 87 (point 3);
- on the test set, 31 of its equations never recovered against 33, 203 and
  11 exact laws on its main and bonus parts against 204 and 10 (214 of 390
  with both), and 10 exact Strogatz fits of 70 against 9. The fits that change
  status there are, but one, fits where 1.4.0 places other seeds.

Elsewhere the two versions give the same figures, or figures that move as
they do from one campaign to the next. The figures of 1.4.0 are given first:
- 171 exact laws of 205 on the decision bench with both, and the same five
  equations never recovered; under units, 174 with both, and four equations
  never recovered;
- 10 collapses of 65 with both (the worst to −1,946), and 66 of 250 on the
  test set with both (38 standardised, 28 in their own units);
- 11 departing formulas of 130 against 12, and 65 of 500 against 68.

Version 1.5 changes the organisation of the code only: at equal seed and
equal work it returns the models of 1.4.0, bit for bit
(`benchmarks/results_1.5/split/`), so the figures of 1.4.0 hold for it,
within what the budget of 30 s moves from one campaign to the next (above).
Point 9 adds what the size study of 1.5 measured on 1.4.0.

## 1. Laws it still misses

On the 41 equations, the engine returns the exact law in 163 fits of 205 (0.9.0:
88). Seven equations are never recovered:

- **an arcsine**, `I.26.2` arcsin(n·sin θ) and `I.30.5` arcsin(λ/(n·d)): no
  operator pool of 1.0 had the arcsine. Since 1.3, both come back (below);
- **a sum of terms, one of them trigonometric**, `I.37.4`
  I1 + I2 + 2·√(I1·I2)·cos δ and `III.17.37` B·(1 + α·cos θ);
- **nested or shifted arguments**, `I.50.26` x1·(cos ωt + α·cos² ωt) and
  `III.9.52`, a sine of (ω − ω0)·t/2;
- **the root of a sum of three squares**, `III.10.19` m·√(Bx² + By² + Bz²).

A sum of three products, `I.11.19`, comes back once in five fits. On the 78
equations of the test set, 34 are never recovered.

**Since 1.3, the arcsine.** The pools `trig` and `full` have the operator,
and the seeds hold the arcsine of a monomial. In the release measurement of
1.3, `I.30.5` comes back exact in 5 fits of 5, and `I.26.2` in 3 of 5. The
engine then returns 171 exact laws of 205, and five equations are never
recovered. Two things the arcsine does not settle:
- **an arcsine whose argument is not a monomial,** such as the n·sin θ of
  `I.26.2`. No seed holds it, so the search must build it: at 30 s it did so
  in 3 fits of 5 at seeds 0 to 4, and in 2 of 5 at seeds 5 to 9;
- **Snell's law on a few noisy points,** i2 = arcsin(sin(i1)/n). With 10 or
  20 points at 2 % or 5 % noise, the curves returned stand closer to the law
  than the noise added (measured on a first version of the arcsine,
  `benchmarks/results_1.3/a1/examine/`). The law comes back in none of the
  40 fits of the TP diagnostic, with 1.2.0 or 1.3.0, on two sets of draws.

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
retrieved in 105 fits of 205 with 1 % noise and 85 with 10 % (0.9.0: 67 and 66),
and with 1.4.0 in 152 and 95 (1.3.0 beside it: 116 and 87).
The constants of the returned formula carry the noise: with 1 % noise,
`0.00115247 + 1.00099 * v0 / (1 - 0.997137 * v1 / v2)` for v0/(1 − v1/v2)
(Feynman I.34.1).
Above 10 % the engine has not been measured.

Since 1.4 the noise-tolerant seeds hold more forms. Two things they do not
settle:
- **at 10 % noise, two equations lose fits with the structure of the law:**
  I.27.6 goes from 2 fits of 5 to none without units and from 5 to 1 with
  them, III.15.12 from 5 to 2 and from 5 to 1. In all twenty of these fits
  1.4.0 places other seeds (one where 1.3.0 placed none on I.27.6, three
  against one on III.15.12), and campaign N2b gave the same counts: the
  likely cause, not examined;
- **on a few noisy points, a seed with the structure of the law does not make
  the search keep it.** On the TP diagnostic (10 or 20 points with 2 % or 5 %
  noise), the point source has the law without units in 14 fits of 20
  against 18 with 1.3.0 (with units, 20 of 20 with both).
  The seeds 1.4 adds there, forms of 1/d² with a small correction, move the
  search, and in 4 fits it ends on a form that follows the noise more closely
  (`benchmarks/results_1.4/n2b/campaign/examine/`). The two changes of 1.4 meant
  for such tables were not adopted (point 11).

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
40 generations (`benchmarks/results_0.9/release_1.0/m3/kepler_minmax_check.txt`). The check uses the pool
`full`; with its arcsine, 1.3.0 gives 2 of 10 instead of 4
(`benchmarks/results_1.3/release/m3/kepler_minmax_check.txt`), and 1.4.0 the
same (`benchmarks/results_1.4/release/m3/kepler_minmax_check.txt`). With the default
normalisation, on the bench, no law was lost this way: no equation has fewer exact
fits than with 0.9.0. `PLAN_PHASE5.md`, mechanics of N1.

Since 1.4 the noise-tolerant stage places more forms on exact data too, where
no exact seed covers it. Among the public figures measured again for the
release of 1.4.0 (M3), one loses its law that way: on the 3,000 rows of x0·x1/x2 + 0.3·x3 of
`benchmarks/time_limit_check.py`, the stage places 4 seeds against 1, and in
sequence 1.4.0 runs to its budget of 15 s and returns an approximation of R²
0.9979, where 1.3.0 returned the law at 6.3 s. Three come out better:
Feynman I.16.6 in the scaling bench, exact in 10 fits of 17 against 9; a case
of the robustness check whose input spans 1e-3 to 1e6, which returns its law
where 1.3.0 returned an approximation; and an exponential of the small-data
check, written as the law where 1.3.0 wrote longer forms of it
(`benchmarks/results_1.4/release/m3_examine/`). On the frozen test set of the
release measurement, without units, 4 fits lose their exact law (2 of TF78, 2
of the Strogatz systems) and 6 gain one (2 and 4, one of them on the rows out
of the domain), all where 1.4.0 places other seeds.

## 6. A formula that departs from its predictions

Protected operations (a division by almost zero, a power capped at a million) keep
the predictions finite; when one of them acts on your data, the printed formula
departs from `predict()`. The engine then says so (`formula_exact` is False, with a
warning that names the exact formulas of the Pareto front). On the real data this
happened in 7 fits of 130 on the bench and 61 of 500 on the test set.

Since 1.3, the arcsine is one of these guards: in the model its argument is
clipped to [−1, 1], and in the printed formula it is not. In the pool
`trig`, in the release measurement of 1.3, the formula departs in 82 fits of
530, against 27 for 1.2.0. At least 47 of the 82 have an arcsine (the records
keep the first 160 characters of a formula). How many depart because the
clip acts is not recorded. The search can use the clip: where the argument
leaves [−1, 1], the arcsine of the model is flat at ±π/2. On the problem of
the French TP notebook of the
pool `full` (`examples/tp_regression_symbolique.ipynb`, ten seeds), 1.3.0
had the higher error in 6 to 8 seeds of 10 at each budget. Ten seeds do not
show that difference, by the sign test of the notebook
(`benchmarks/results_1.3/release/m3/examine/`).

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
rows and up to about ten variables. The size study of 1.5 measured 1.4.0 beyond
(`benchmarks/results_1.5/size/`), on the 41 Feynman equations of the decision
bench without noise, five seeds, 30 s per fit:
- **rows:** 165 exact laws of 205 at 100 rows, 168 at 1,000, 161 at 10,000 and
  154 at 100,000. The seeds find the same laws at every size; the search loses
  the others: the fits that run to their budget reach a median of 3 generations
  at 100,000 rows, against 116 at 100. Ten times the time gives 160: of the 12
  fits lost at 100,000 rows, 6 come back.
- **variables that play no part in the law:** with 5, 10 and 20 of them added to
  1,000 rows, 144, 139 and 108 exact laws against 168, and ten times the time
  gives 120: of the 61 fits lost with 20 added, 10 come back, 4 others become
  exact and 2 are lost. The seed finders limit their combinations of columns
  as the columns grow, and lose a third of their laws with 20 added; 26
  returned formulas take in an added variable.

Beyond these sizes nothing is measured. It is not meant for chaotic sequences,
nor for large datasets where raw accuracy matters more than a formula you can
read: ensemble models or engines such as PySR and Operon serve those better.

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

## 11. What 1.4 measured and left out

Three changes were measured for 1.4 and not adopted
(`benchmarks/results_1.4/PLAN.md`). Their code stays in the engine, switched
off:
- **a cross-validation on tables below 30 rows (S1).** It chose structures the
  search had found on the same few points, whose error it underestimated: in
  the plain arm of the TP diagnostic the law came back in 113 fits of 200
  against 126, and the median fit took 1.67 times as long;
- **a seed for a constant plus an exponential (E2),** as in Newton's cooling.
  The seed had the structure of the law in 18 fits of 20, but in 11 of them the
  search returned another form, closer to the noise: the law came back in 7
  fits of 20 against 3. Its form, close to many laws on a few noisy points,
  also took the search away from the point source (18 fits of 20 to 15);
- **the fit of the constants of each noise-tolerant candidate,** a part of the
  first version of the change of 1.4. It lost exact laws without noise
  (I.26.2 went from three exact fits of five to none).

S1 and E2 are postponed to the next version: both meet the same cause, the
final choice among the forms of the search on a few noisy points.

## 12. The tables of the teaching results are simulated

Every result on teaching comes from simulated tables: the TP diagnostic, its
frozen set TPT10 and the noisy frozen set TF78N draw a Gaussian noise on exact
laws, as the decision bench does with the Feynman equations. No table
measured by students could be gathered for 1.4.
