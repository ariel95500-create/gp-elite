# Change U2: no fractional units from the power law seed

Written on 29 October 2026, before any change of the engine, after M3 of the
release 1.1.0 (`release/README.md`, now `release/candidate1/README.md`). The author chose on 28 October to correct
before the release ("B") rather than to publish 1.1.0 as measured.

## What M3 found

The French TP notebook returns with 1.1.0 the laws and constants of 1.0.0, but
its six fits take 320 s against 243 s. The gas law, timed alone three times
with each version, takes 77 to 79 s against 50 to 51 s
(`release/m3/tp_timing/`, now `release/candidate1/m3/tp_timing/`).

The cause, read from the trace and a profile of that fit:
- under units, U1 lets the power law finder run. Beside the seed with exponents
  rounded to half-integers, `n * T / V`, the finder makes a second seed with the
  fitted exponents, `pow(n, 1.0041) * pow(T, 0.9174) * pow(V, -0.9852)`;
- that seed passes the gate of dimensions only because `unknown_constant=True`
  lets the leading constant carry any units, here fractional ones;
- its descendants then ask the typed builder for subtrees of fractional units,
  which it rarely reaches before its budget runs out. `dim_search._build_ek`
  is called ten times as often;
- with noisy data no law is exact, the search never stops early, and the cost
  stays.

## The change

Under units, the second seed of `_make_power_law_seeds` (fitted exponents) is
made only if it carries no fractional units. Every factor whose fitted exponent
is not a half-integer (the same test of 0.04 as today) must be a dimensionless
input. The seed with half-integer exponents is unchanged. Without units nothing
changes: the new test is reached only when `_dim_active(cfg)`.

A law whose units hold has rational exponents on its dimensioned inputs. A
fitted exponent such as 1.0041 on moles is noise, and seed 1 already holds its
rounded value.

Which fits can change:
- fits under units with `unknown_constant=True`, where the power law fits
  above its threshold with exponents that are not half-integers on dimensioned
  inputs: lab data with noise, such as the TP notebook;
- without `unknown_constant`, such a seed already fails the gate, unless its
  non-half-integer exponents fall on dimensionless inputs, in which case it is
  kept, as today. The units kinds of the bench (U41, U41N1, U41N10, TF78 under
  units) run without `unknown_constant`, so their models are expected to stay
  the same.

## Mechanics, before any measurement

1. The thirteen reference configurations of `speed_equivalence.py` return the
   models of the adopted engine (`mechanics/equiv_U1_default`): identical.
2. The gas law of the TP notebook (`release/m3/tp_timing/gas.py`, now under
   `release/candidate1/`) returns
   `8.24992 * n * T / V`, its trace shows one power law seed, and, timed alone
   three times, it takes at most 1.0.0's median time plus 10 % (50.2 s there,
   so at most 55.2 s).
3. The test suite passes, with a new test: under units with
   `unknown_constant=True`, on data whose fitted exponents are not
   half-integers, the power law finder makes no seed carrying fractional units;
   without units it still makes it.

If one of them fails, the change is examined before anything else runs.

## Targeted check, deciding adoption

The units arm of the TP diagnostic (`benchmarks/tp_diagnostic.py`):
- the ten experiments, 10 and 20 points, 2 % and 5 % noise, five draws: 200
  fits;
- run with 1.1.0 (its wheel, `/venv11`) and with U2, side by side, each job
  with both at the same time, two jobs at a time.

U2 is adopted if all three hold:
1. **No law lost.** On the six laws reachable under units, the law is
   recovered in at least as many fits as with 1.1.0. On the four others,
   none recovered with 1.1.0 is lost.
2. **Faster.** The median time of the 200 fits is lower than with 1.1.0.
3. **The constants.** The constants deduced where the law is recovered (g, R)
   have, across the fits, the same median relative error as with 1.1.0,
   within 0.1 point.

Corrected on 29 October 2026, before the check ran: the diagnostic has ten
experiments, not nine (Snell's law is the fourth one out of reach under units),
so the arm has 200 fits; this version of the plan first said nine and 180.

## Then the release again

U2 changes the engine after M1, M2 and M3, so as `PLAN_RELEASE_1.1.md` says:
- a new release candidate (version still 1.1.0, never published) and new
  environments;
- M1, M2 (the 2,780 fits, paired with 1.0.0, now from PyPI) and M3, then M4 and
  M5;
- the stop criteria of M2 are unchanged.

1.0.0 was published on PyPI on 29 October 2026. As the plan says, it is
installed from PyPI for the comparison, and its `gp_elite/` files were checked
identical to the measured wheel's.

If U2 is not adopted, the engine stays U1, the measurements of 1.1.0 stand, and
the slowdown is published with its cause, as the author's option "A".

## Mechanics, result (29 October 2026)

All three held (`mechanics/`):
1. `compare_U1_default_vs_U2.txt`: the thirteen configurations are identical
   to the adopted engine U1.
2. `U2_gas_law.txt`: the gas law returns `8.24992 * n * T / V` with one power
   law seed, in 45.4, 44.3 and 44.3 s (at most 55.2 s asked; 1.0.0 took 50 s,
   1.1.0 78 s).
3. The suite passes, 154 tests. The new test,
   `test_no_power_law_seed_with_fractional_units`, fails on the engine before
   the change.

## Targeted check, result (29 October 2026)

`u2check/`: the units arm of the TP diagnostic, 200 fits per engine, 1.1.0
(`/venv11`) and U2 (`/venvU2`, the wheel of 26349ef, the same packages
otherwise), each job with both at the same time, from 18:37 to 20:02. No
crash. `compare_u2.py` reads the criteria (`compare_u2.txt`).

| experiment | law, 1.1.0 | law, U2 | median time 1.1.0 (s) | U2 (s) | same expression |
|---|---|---|---|---|---|
| pendule | 20/20 | 20/20 | 41.0 | 40.9 | 20/20 |
| ressort | 20/20 | 20/20 | 46.0 | 45.9 | 20/20 |
| chute | 20/20 | 20/20 | 43.8 | 42.9 | 20/20 |
| puissance | 20/20 | 20/20 | 42.4 | 42.4 | 20/20 |
| gaz | 20/20 | 20/20 | 83.4 | 43.1 | 18/20 |
| eclairement | 20/20 | 20/20 | 39.7 | 37.7 | 17/20 |
| rc | 0/20 | 0/20 | 60.1 | 59.9 | 20/20 |
| refroidissement | 0/20 | 0/20 | 49.9 | 50.3 | 20/20 |
| lentille | 0/20 | 0/20 | 58.8 | 58.8 | 20/20 |
| snell | 0/20 | 0/20 | 22.8 | 22.7 | 20/20 |

The three criteria are met:
1. No law is lost: 120 of 120 on the six reachable laws with both engines,
   and none recovered on the four others with either.
2. U2 is faster: the median time of the 200 fits is 44.2 s against 46.1 s.
   The total is 9,117 s against 10,054 s. The gain is on the gas law, whose
   median falls from 83.4 s to 43.1 s; elsewhere the times are those of
   1.1.0.
3. The constants hold: the median relative error of g and R is 0.98 % with
   both engines, on 60 fits each.

**U2 is adopted.** It becomes part of the engine of 1.1.0, and the release
starts again from a new candidate, as written above.
