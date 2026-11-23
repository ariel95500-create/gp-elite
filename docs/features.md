# Technical features and history

Part of the documentation of GP_ELITE: back to the [README](../README.md); [version française](fr/caracteristiques.md).

## Technical features

- **More noise-tolerant seeds** (v1.4): a second pass that weights the rows by
  y² and does not need the target to keep one sign, scans of the logarithm, the
  sine and the cosine over their whole library, and new forms up to twelve
  seeds in all, every seed 1.3 placed still placed with the constants its
  finder gave; the stage runs when no binomial form and no function of a
  monomial holds the data exactly, with or without noise
- **The arcsine** (v1.3): `arcsin` in the pools `'trig'` and `'full'`, its
  argument clipped to [−1, 1] and given a constant factor that the fit of
  constants adjusts, and among the forms fitted directly the arcsine of a
  monomial, b·f·arcsin(c·g)
- **Stop on patience** (v1.2): when the call sets neither `generations` nor
  `time_limit`, the search stops once its hold-out error (its training error
  when there is no hold-out) has not improved by 1 % in 30 generations
  (`patience=`)
- **Exponentials written as such** (v1.2): a power of a number is printed as an
  exponential, and an exponential of one variable with its scale,
  `exp(-t / τ)`, each kept only if it passes the check against `predict()`
- **Forms fitted directly** (v1.0): a monomial times a power of a binomial,
  b·f·(1 + c·g)^p with p one of −1, −½, ½, 1 (rational laws, 1/√(1 − v²/c²), the
  root of a sum of two terms), and a monomial times a function of a monomial,
  b·f·exp(c·g), b·f·log(c·g), b·f·tanh(c·g), b·f/cosh(c·g) or
  f·(a + β·sin(ω·g) + γ·cos(ω·g)): each is fitted by a one-dimensional search and
  least squares, and placed in the starting population when it holds to numerical
  precision
- **Noise-tolerant seeds** (v1.0): when no form holds exactly, the power law and the
  forms above are sought again with their thresholds lifted, and placed if they
  leave at most 1.5 % of the variance unexplained
- **Power-law seeds** (v0.8): when the data follow a power law, the monomial fitted on the logarithms starts in the population
- **Exact-law polish** (v0.8): finalists get converged constants and a coefficient per term of each sum; a variant is admitted only if it is exact
- **Constants fitted for the judged form** (v0.8): Levenberg–Marquardt in variable projection (the scale and offset of the linear scaling solved inside the residual)
- **Scale-free data** (v0.8): a target of any magnitude is divided internally by a power of ten, and the default normalisation divides each column by its largest absolute value
- **Formula in your variables, checked** (v0.7): the internal rescaling is folded back into the constants; `formula_exact` reports whether the formula reproduces `predict()` on the training data
- **Time budget** (v0.7): `time_limit=` stops cleanly and returns the best model found; under `units=`, the typed start respects it too since v1.2
- **Mystery-constant deduction** (v0.5): the leading constant may carry a dimension, inferred by homogeneity; units and raw value exposed on the estimator, the value read on the predictions when the model is a monomial (v1.0)
- **Dimensionally-constrained search** (v0.4): constructive typed generation, dimension-preserving mutation and crossover, validity gate in `fitness()` — one semantics shared with the post-hoc auditor (v0.7)
- **Scale-only linear scaling under `units=`** (v0.4.1): regression through the origin, so the form that is *scored* is the form that is *delivered*
- **Numerical guard in the LM optimizer** (v0.4): no more float64 overflow on unbounded `sq`/`cube`/`*` chains
- **Post-hoc dimensional audit** (v0.3): `dimensions.py`
- **Levenberg–Marquardt constant optimization** (v0.2): deterministic, LM/Adam switchable
- **Multi-restart + merged candidate archives** (v0.2): seed variance turned into reliability
- **Pareto front API** (v0.2): non-dominated complexity/accuracy staircase
- **Guarded extrapolation / forecasting mode** (v0.2): beyond-domain probes, linear floor, frontier selection
- **Composition motif seeding** (v0.2): Pythagorean, reciprocal-sum, Gaussian templates for nested structures
- **Asymmetric island model** (explorer / cleaner / stigmergic) with periodic migration, in parallel worker processes on machines with four cores or more
- **Linear scaling** (Keijzer 2003): the engine searches for the *shape*; scale and offset are solved in closed form
- **ε-lexicase selection** (La Cava 2016) to preserve behavioral diversity
- **Hold-out validation** + parsimonious champion selection (R² tolerance)
- **Shift-free normalization** preserving multiplicative structure (x·y stays a clean product), for all data since 0.7
- **Stigmergic memory** exportable across runs (grammar export/import) — a documented feature, not a measured performance advantage


## What's new

**1.4 "Signal"** — more noise-tolerant seeds: on the 41 Feynman equations of the
decision bench with Gaussian noise on the target, the structure of the law comes
back in 152 and 95 fits of 205 (1 % and 10 % noise) against 116 and 87 for 1.3
measured beside it, and in 150 and 93 with units against 121 and 95; without
noise, the exact laws of 1.3, 171 and 174 with units. Three other changes were
measured and not adopted. **1.3 "Arc"** — the arcsine, in the pools `trig` and `full`: on the 41 Feynman
equations of the decision bench, its two arcsine laws come back exact in 8
fits of 10, with and without units, where 1.2 had none. That makes 171 exact
laws of 205 against 163, and 174 against 166 with units. The pool
`physical`, the default, is left as it was: with it, the models of 1.2 at
equal work. **1.2 "Classroom"** — a fit under the defaults stops once it no longer improves
(`patience=`): the six laws of the French TP notebook in 48 s, against 194 to
198 s for 1.1.0 on the same machine, with the same formulas; an exponential
comes back written as one, `exp(-t / τ)`, the model unchanged; under `units=`,
Feynman III.19.51 without noise ends in about a second, where 1.1.0 took about
six minutes with a budget of 30 s. With a budget set, the models of 1.1 at equal work,
but for those whose typed start under `units=` the correction changes (III.19.51 on the
bench): in the 2,780 fits of the release measurement, no fit changes status. **1.1 "Coherent"** — the forms 1.0 fits directly act under `units=` too, each placed only if
it passes the gate of dimensions: on the 41 Feynman equations of the decision
bench with their units, 165 exact laws of 205 against 108 for 1.0 measured beside
it; every one of the 1,005 models returned under units in the release
measurement (these equations with and without noise, and the frozen test set)
passed the audit of units; without units, the models of 1.0 at equal work. **1.0 "Families"** — whole families of laws fitted directly (rational forms, roots,
exponentials, logarithms, sines and cosines of a monomial), on noisy data too: on
the 41 Feynman equations of the decision bench, 163 exact laws of 205 against 88
for 0.9 measured beside it, and on 78 other Feynman equations frozen before the
work, 213 of 390 against 145 (on the 14 Strogatz systems frozen with them, 7 of 70
against 8); on real data, the same median R² within 0.004 and the same number of
collapses out of the training range; three case studies on public data and a page of
what the engine does not do. **0.9 "Steady"** — the search with `units=` faster, with the same models (more
than five times on Feynman II.11.3); a formula that departs from the model names
the exact formulas of the Pareto front; a test set frozen before any decision and
never used to make one, on which each release is measured. **0.8 "Swift"** — faster (the speed-ups alone return the same models), more laws
recovered (power laws seeded, right structures finished into exact laws), data of
any scale, inputs checked; every change meant to improve the search decided by a
comparison written before it ran. **0.7 "Sound"** — the formula you get is the model you got: written in your
variables for every normalisation and checked at fit time; a `time_limit=`
budget; dimensional guarantees made strict; every number of its README
re-measured on its final code. **0.6 "Bench"** — physical units in the
console. **0.5 "Unknown"** — units *and* value of a law's missing constant.
**0.4 "Lawful"** — dimensionally-constrained search. **0.3 "Trust"** —
diagnostics and stability.

Full history, with the measurements behind each claim, in
[CHANGELOG.md](https://github.com/ariel95500-create/gp-elite/blob/main/CHANGELOG.md). Every benchmark behind a number here lives in
[`benchmarks/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks), with its raw results.
