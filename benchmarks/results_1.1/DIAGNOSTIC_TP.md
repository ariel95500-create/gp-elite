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

## Result (26 October 2026)

**The run.** 400 fits from 04:45 to 06:52 UTC, no crash, gp-elite 1.0.0
from its wheel (`tp/tp_1.0.0.jsonl`, summary in `tp/summary_1.0.0.txt`). It
ran in two parts. The runner was stopped at 374 fits by the two-hour limit of
a background task in this session; it resumed and ran the 26 left, which it
had not started. The machine is that of `PLAN.md`.

**One deviation.** Below 30 points the engine keeps no hold-out and returns
no Pareto front (`pareto` is None). The measure "front" is therefore empty
on every fit, and the reading rests on "law" alone. That is stricter than
the rule written above, and the verdict holds under it.

**The reading: favourable.** Plain arm, 2 % noise: the textbook law comes
back in at least 3 of 5 draws for 7 of the 9 experiments at 10 points and
8 of 9 at 20 points. The rule asked for at least 6 of 9 at both sizes.

Exact law in 5 draws, and in parentheses the fits whose model reproduces the
noiseless law with R² ≥ 0.99 whatever its form:

| experiment | plain 10 pts 2 % | plain 20 pts 2 % | plain 10 pts 5 % | plain 20 pts 5 % | units 10 pts 2 % | units 20 pts 2 % | units 10 pts 5 % | units 20 pts 5 % |
|---|---|---|---|---|---|---|---|---|
| pendule | 5 (5) | 5 (5) | 3 (4) | 4 (4) | 5 (5) | 5 (5) | 5 (5) | 5 (5) |
| ressort | 4 (4) | 5 (5) | 3 (3) | 4 (4) | 5 (5) | 5 (5) | 5 (5) | 5 (5) |
| chute | 5 (5) | 4 (5) | 5 (5) | 5 (5) | 5 (5) | 5 (5) | 5 (5) | 5 (5) |
| puissance | 5 (5) | 5 (5) | 5 (5) | 4 (4) | 5 (5) | 5 (5) | 5 (5) | 5 (5) |
| gaz | 3 (5) | 5 (5) | 4 (5) | 3 (4) | 5 (5) | 5 (5) | 5 (5) | 5 (5) |
| eclairement | 4 (5) | 4 (5) | 3 (4) | 4 (5) | 5 (5) | 5 (5) | 5 (4) | 5 (5) |
| rc | 4 (5) | 4 (5) | 2 (5) | 4 (5) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| refroidissement | 0 (3) | 3 (5) | 0 (3) | 0 (2) | 0 (1) | 0 (0) | 0 (0) | 0 (1) |
| lentille | 0 (5) | 1 (5) | 0 (0) | 0 (3) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| snell | 0 (5) | 0 (5) | 0 (3) | 0 (5) | 0 (5) | 0 (5) | 0 (4) | 0 (5) |

**Beside the reading, deciding nothing:**

- **With units, the six laws within reach come back every time**: 120 fits
  of 120, at both sizes and both noise levels. They come back in their
  textbook form, for instance `2.01981 * sqrt(L)` and `8.39929 * T * n / V`.
  Without units the same laws often carry an offset that the law does not
  have (`-0.0256563 + 2.05312 * sqrt(L)`, `-793.918 + 8.47651 * n / V * T`).
  The test of structure accepts it, but a student reads it.
- **The deduced constant.** With units, g from the pendulum and from free
  fall, and R from the ideal gas, are within 0.3 % to 1.6 % of their values
  in the median, and 4.7 % at worst, on 60 fits.
- **The three laws with a constant inside a function or a sum** (rc,
  refroidissement, lentille) never come back with units, as the rules said.
  What the units arm returns instead is poor: R² below 0.99 on all but two
  of the 60 fits. Some formulas exploit a safety net of the engine, for
  instance `exp(-t / (t - |t|))`, in which t − |t| is zero.
- **Without units, the exponentials come back written as a power.** The
  capacitor discharge is returned as `4.86249 * 0.00784758^(0.2 * t)`
  rather than as an exponential of −t/τ. Newton's cooling is not found at
  10 points; at 20 points it is found in 3 draws of 5 at 2 % noise.
- **The thin lens is found once in 40 plain fits.** Snell's law is never
  found, as no pool has the arcsine; its approximations are good.
- **Time.** A fit takes 61 s in the median without units and 88 s with
  them (172 s at most), on 10 or 20 points. A student waits about a minute.

**What would have to improve first for teaching**, in the order the
measurements suggest:
1. under units, constants with units inside a function or a sum (a time
   constant τ, an offset θa, a focal length f), or at least an honest
   message instead of a poor formula;
2. the time of a fit on a small table;
3. a front of candidate laws on small tables;
4. the exponential written as such;
5. the arcsine.
