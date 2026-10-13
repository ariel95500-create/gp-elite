# What GP_ELITE does not do

*[Version française](LIMITATIONS.fr.md)*

This page lists what the engine does not do, or does badly, each point with the
measurement behind it. The figures come from the work that followed 0.9.0, on the
decision bench (41 Feynman equations, five seeds, 30 seconds per fit; 13 real
datasets), in `benchmarks/results_0.9/PLAN_PHASE4.md` and `PLAN_PHASE5.md`. They
will be measured again on the wheel of the next release.

## 1. Laws it still misses

On the 41 equations, the engine returns the exact law in 160 fits of 205. Seven
equations are never recovered:

- **an arcsine**, `I.26.2` arcsin(n·sin θ) and `I.30.5` arcsin(λ/(n·d)): no
  operator pool of the engine has the arcsine;
- **a sum of terms, one of them trigonometric**, `I.37.4`
  I1 + I2 + 2·√(I1·I2)·cos δ and `III.17.37` B·(1 + α·cos θ);
- **nested or shifted arguments**, `I.50.26` x1·(cos ωt + α·cos² ωt) and
  `III.9.52`, a sine of (ω − ω0)·t/2;
- **the root of a sum of three squares**, `III.10.19` m·√(Bx² + By² + Bz²).

A sum of three products, `I.11.19`, comes back once in ten fits.

## 2. The gains rest on the bench they were built for

The changes that took the bench from 86 to 160 exact laws (B1, E1, and N1 for
noisy data) fit families of forms directly; each family was chosen from a
prototype run on the training rows of these 41 equations. They were confirmed on
seeds never run, but on the same equations. Whether laws of these shapes elsewhere
are recovered as well is measured once, with the release, on a test set frozen
before this work (78 other Feynman equations, 14 Strogatz systems, 25 real
datasets), and published whatever it says.

## 3. Noise

With Gaussian noise on the training target, the structure of the law (the model
returned, its constants refitted on clean data, reproduces the clean test rows) is
retrieved in 106 fits of 205 with 1 % noise and 86 with 10 %. The constants of the
returned formula carry the noise: `v0 / (1 - 0.997 * v1 / v2)` for v0/(1 − v1/v2).
Above 10 % the engine has not been measured.

## 4. Real data, out of the training range

A formula that fits is not a law. On the 13 real datasets of the bench, predicting
the 20 % of rows farthest from the others, 10 models of 65 collapse (test R² below
zero), the worst to −233. On the 25 real datasets of the frozen test set, measured
for 0.9.0, 36 of 125; the collapses concentrate on small or mostly categorical
datasets. Keep rows out of the fit to judge a formula, and look at the Pareto
front: on real data the readable answer is often a short entry of the front, not
the returned champion.

## 5. Exact data that no seed covers

When data follow a law exactly but no exact seed covers it, a seed that only
approximates the data can draw the search away from the law. Seen on Kepler's law
normalised by min-max (`normalize="minmax"`): exact in 1 fit of 10 instead of 3 at
40 generations. With the default normalisation, on the bench, no law was lost this
way. `PLAN_PHASE5.md`, mechanics of N1.

## 6. A formula that departs from its predictions

Protected operations (a division by almost zero, a power capped at a million) keep
the predictions finite; when one of them acts on your data, the printed formula
departs from `predict()`. The engine then says so (`formula_exact` is False, with a
warning that names the exact formulas of the Pareto front). On the real data of the
bench this happened in 11 fits of 260.

## 7. The same seed on another machine

From four cores, the islands run in parallel by default and can return another
model than in sequence; with `time_limit=`, the generations reached depend on the
speed of the machine. `parallel=False` and a number of `generations` give the same
model on every run of a given machine; across processors, results can still differ
in the last digits and then in the model.

## 8. Physical units

Under `units=`, the population is typed: the seeds of the power law, of B1, E1 and
N1 do not act, and a typed generation costs about 1.4 times an untyped one
(Feynman II.11.3).

## 9. Size and kind of data

GP_ELITE is plain Python and NumPy. It is meant for a hundred to a few thousand
rows and up to about ten variables; beyond fifteen to twenty variables the search
space explodes. It is not meant for chaotic sequences, nor for large datasets where
raw accuracy matters more than a formula you can read: ensemble models or engines
such as PySR and Operon serve those better.
