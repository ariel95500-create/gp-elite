# Diagnostic TP: does GP_ELITE return the textbook law on student lab data?

Written on 27 October 2026, before the script is run. The diagnostic changes
nothing in the engine and decides nothing about it. It answers a question of
strategy, put by the author on 26 October: should GP_ELITE be presented first
to physics teaching, the practical sessions (TP) of secondary school and
university?

Its measurements are what this file writes down here, before they exist. It
runs before the implementation of plan 1.1 (`PLAN.md`), on the author's
choice.

## Why this question needs a measurement

The engine's measured strengths fit teaching:
- simple physical laws recovered exactly;
- physical units;
- pure Python.

But a student's table is small and imprecise: 8 to 20 points, a few per cent
of error. The smallest check so far (`small_data_check.py`) used 25 points
without noise. If the engine returns long formulas that follow the noise,
instead of the law of the textbook, the idea does not hold as it stands.

## The experiments

Ten classic experiments of physics teaching, each with its law and the units
of its columns (`benchmarks/tp_diagnostic.py`, list `EXPERIMENTS`):

| key | experiment | law | inputs | constant not in the data | reachable under units |
|---|---|---|---|---|---|
| pendule | simple pendulum | T = 2π√(L/g) | L | g | yes, its units deduced |
| ressort | mass on a spring | T = 2π√(m/k) | m, k | none | yes |
| chute | free fall | d = ½·g·t² | t | g | yes, its units deduced |
| puissance | electric power | P = U²/R | U, R | none | yes |
| gaz | ideal gas | P = n·R·T/V | n, T, V | R | yes, its units deduced |
| eclairement | point source | E = P/(4π·d²) | d | P | yes, its units deduced |
| rc | capacitor discharge | u = E·exp(−t/τ) | t | E, τ | no |
| refroidissement | Newton's cooling | θ = θa + (θ0 − θa)·exp(−t/τ) | t | θa, θ0, τ | no |
| lentille | thin lens | q = p·f/(p − f) | p | f | no |
| snell | refraction | i2 = arcsin(sin(i1)/n) | i1 | n, dimensionless | no |

"Reachable under units" is read from the rules of the engine before any
fit:
- under `units=` a fitted constant is dimensionless, except the leading one
  with `unknown_constant=True`;
- the offset of the final scaling is not allowed;
- so a constant with units inside a function or a sum (τ, θa, f) cannot be
  built;
- no pool has the arcsine, so Snell's law cannot be built without units
  either.

These four are measured all the same. Their results say what a teacher
would get.

## Data and fits

- **Points:** n = 10 and n = 20. For one input they are evenly spaced over
  its range, as a student chooses them. For two or three inputs they are
  drawn uniformly in the box.
- **Noise:** multiplicative, y·(1 + ε) with ε Gaussian of standard
  deviation 2 % or 5 %. The inputs are exact.
- **Draws:** five, numbered 0 to 4. The noise and the engine's seed both
  take the draw's number.
- **Two arms:**
  - *plain*: `symbolic_regression(X, y, feature_names=...)` with the
    defaults, as a first user calls it;
  - *units*: the same call with `units=` and `target_units=`, and
    `unknown_constant=True` where a constant with units is not in the
    data (all but ressort, puissance and snell).

  Everything else is the default: pool `"physical"`, except `"trig"` for
  Snell, the pool the README advises for an angle; 100 generations; speed
  `"fast"`.
- **One exception to the defaults:** `parallel=False`, so that each fit
  gives the same result when it is run again.

That makes 10 experiments × 2 sizes × 2 noises × 5 draws × 2 arms = 400
fits. Each runs in its own process with `PYTHONHASHSEED=0`. The engine is
gp-elite 1.0.0 from its wheel (`/venv10`), the version about to be
published.

## What is measured

For each fit, against the noiseless law on 200 points spread over the same
box:

- **law**: the returned model has the structure of the law. Its constants
  are fitted again on the noiseless values of its training points, with the
  engine's own finishing step. It must then reproduce the 200 points to
  1 − R² < 1e-9. This is the test of "structure retrieved" of
  `phase1_bench.py`.
- **front**: some entry of the returned Pareto front passes the same test.
  A teacher shown the front can pick it.
- **useful**: the returned model reproduces the 200 noiseless points with
  R² ≥ 0.99, whatever its form.
- the size of the returned model, against the size of the smallest entry
  that passes "front";
- the time of the fit.

## How it will be read, written before the run

The reading uses the plain arm with 2 % noise, on the nine experiments whose
law can be built without units. An experiment counts when its law is
returned, or on the front, in at least 3 of the 5 draws.

- **Favourable:** at least 6 of the 9 count, both at 10 points and at 20
  points.
- **Unfavourable:** fewer than 4 of the 9 count at 20 points.
- **Mixed:** anything else. The experiments that fail then say what would
  have to improve first.

Reported beside the reading, and deciding nothing:
- 5 % noise;
- the units arm;
- the experiments where the law is on the front but another model is
  returned (the right answer is offered but not chosen);
- the four experiments not reachable under units.

The result goes to the author, who decides whether teaching becomes the
first audience of GP_ELITE.
