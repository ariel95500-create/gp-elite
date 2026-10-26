# Plan of version 1.1: the forms of 1.0 under units

Written on 26 October 2026, before any change to the engine and before any
measurement of this phase. The prototype below ran gp-elite 1.0.0 as it is
and decides nothing. Method as for 0.9 and 1.0:
- one process per fit, `PYTHONHASHSEED=0`;
- the criteria are written here before the measurement they judge;
- the frozen test set is never used to decide;
- every deviation from this plan goes to the author.

The author validates this plan before any change (gate 5). He decides the
publication of 1.1 after its measurement (gate 6).

## What 1.1 has to do

Version 1.0 fits whole families of laws directly and places them in the
starting population (B1, E1, N1, beside the power-law seeds of 0.8). Under
`units=` the population is typed: every tree must have the target's
dimensions. The four seed finders then return nothing: each starts with a
guard `_dim_active(cfg)` (`gp_elite/core.py`, `_make_power_law_seeds`,
`_make_binomial_seeds`, `_make_elementary_seeds`, `_make_tolerant_seeds`).

The cost was measured on the 1.0.0 package (`../results_0.9/release_1.0/m3/units_ab_ood.txt`).
On Feynman II.11.3 the search without units returns the exact law in 5 runs
of 5, in about a second each. With units it does so in 2 runs of 5, in 3.2 s
and 15.5 s; the three others end on approximations after 27 to 32 s. Point 8
of the limits pages says so. Units are what sets GP_ELITE apart: a user who
declares them should not get less than one who does not.

## Prototype, before this plan (26 October 2026, decides nothing)

`prototype/seeds_under_units.py`, output in `prototype/seeds_under_units.txt`
and `.json`. For each of the 41 equations of the decision bench, on its
training rows, it ran one fit of 1.0.0 with units and `generations=1`. The
units come from `../units_table.py` (below). Each finder was called as it
would be without units, on the rows and columns the engine gives it. Each
tree it returned was judged by the engine's own gate,
`dim_search.is_typed_valid`, the gate every typed tree must pass. The
finders' output was then dropped, so the fits are those of 1.0.0.

- **Seeds of the three finders that do not tolerate noise.** The power law
  places a seed when a monomial explains 99.9 % of the variance of log|y|;
  B1 and E1 when their form holds to numerical precision. On 30 of the 41
  equations one of them returns a seed. All 30 keep at least one seed that
  passes the gate. One seed fails it: a power law with fitted exponents on
  I.15.10 (`pow(v0, 0.9981) * pow(v1, 1.0635) * pow(v2, -0.0773)`), whose
  units do not add up. The B1 seed of the same equation passes.
- **Noise-tolerant seeds (N1).** Of the 11 equations without an exact seed,
  three receive tolerant seeds, all of which pass the gate: I.16.6 (four),
  I.26.2 (one), I.37.4 (one).
- **What passes.** It includes II.11.3, `q·Ef/(m·w0²)/(1 + c·w²/w0²)` with
  c fitted on the scaled columns, the rational and root families, the exponentials and
  logarithms of I.40.1, II.35.18 and I.44.4, and the trigonometric seeds of
  II.15.4, I.18.12, III.15.12 and II.6.15b.

Gate and finder agree for a reason: in a homogeneous law, the binomial and
the argument of a function are dimensionless, and the monomial factor
carries the target's units. When the data follow such a law exactly, the
form that fits them is that law.

## The bench under units, fixed before any measurement

**The units.** `../units_table.py` gives the SI units of each input column
and of the target of the 41 equations. The rules are in its docstring:
- the units are those of the formula the bench generates the data with;
- the first fifteen are those of `feynman_units.py`, checked identical;
- every row is checked homogeneous by the engine's gate on the bench
  formula.

On 26 October all 41 rows pass the check and the fifteen are identical.

**U41.** The decision bench of `decision_bench.py`, unchanged otherwise:
- the same data, splits and seeds 0 to 4;
- budget T, 30 s per fit;
- the pool of each equation, `parallel=False`, the other defaults;
- `units=` and `target_units=` from the table, `unknown_constant=False`.

U41N1 and U41N10 are U41 with 1 % and 10 % Gaussian noise on the training
targets, with "structure retrieved" measured as for F41N1 and F41N10
(`phase1_bench.py`). A job kind of `phase1_bench.py` runs them (`ufeyn`,
`ufeyn_n1`, `ufeyn_n10`), with `run-paired` as in M2 of 1.0. The script is
changed for this before the mechanics, and checked to run the untyped kinds
as before.

**Real data under units.** The typed fits of the two case studies, seeds 0
to 4 (`case_studies.py`):
- Kepler A, the eight planets;
- Kepler B, fitted on the four inner planets, with the error on the four
  outer ones;
- Hubble A, the 24 galaxies;
- Hubble CA, fitted on the 18 nearest, with the RMSE on the six farthest.

These four use `unknown_constant=True`, as the studies do.

**Machine.** Linux, 4 cores (Intel Xeon at 2.8 GHz with AVX-512), 15 GB.
That is not the processor of the 1.0 measurements: the comparison is the
paired one below, both versions side by side on this machine.

## Change U1, plan written before it is implemented

**The change.** Under `units=`, the four finders run as without units, on
the same rows, with the same thresholds and the same order. Each tree they
return is kept only if it passes `dim_search.is_typed_valid(tree, FEAT_DIMS,
TARGET_DIM, UNKNOWN_CONST)`. That is the gate of `fitness()` and of the
typed operators. N1 still runs only when B1 and E1 kept no seed, counted
after the gate. The kept seeds go to the same slots, one copy per island,
judged like every other individual.

Nothing changes without units: the guard becomes the gate, which applies
only when units are declared. No random number is drawn. The flag is
`_SEEDS_UNDER_UNITS` in `gp_elite/core.py`, off by default until the
campaign decides.

**Mechanics, before any fit:**
1. Flag off: the thirteen reference configurations of
   `speed_equivalence.py` are identical to the 1.0.0 wheel, and the test
   suite passes.
2. Flag on: every configuration without units is identical to the 1.0.0
   wheel. For the typed ones, whether a seed was placed is reported.
3. Flag on, on the training rows of U41: the seeds placed are those the
   prototype found valid.
4. One fit of II.11.3 with units, 30 generations, outside any measurement:
   whether the seed reaches the returned model.

New tests check two things: a seed is placed under units only when it
passes the gate, and the model returned under units on II.11.3 passes the
audit `check_dimensions`.

**Campaign U1** (decides). A, the 1.0.0 wheel (`/venv10`, the wheel
measured for the release), against U1 with the flag on. Side by side,
`run-paired`, two jobs at a time: U41, U41N1 and U41N10, seeds 0 to 4 (615
jobs per version), and the 20 typed fits of the case studies. U1 is adopted
when all of these hold:

1. **Exact laws under units.**
   - U41 exact in U1 at least 10 more than in A.
   - Among them, at least 5 more in the five families at zero in 0.8.0
     (racine, rationnelle, trig, exponentielle, logarithme; 90 fits).
   - No equation exact in A at three seeds or more falls to one seed or
     none.
2. **Structure under noise:** with 1 % and with 10 % noise, the structure is
   retrieved in no fewer fits than A's minus 2.
3. **The units guarantee.** Every model U1 returns on U41, U41N1 and U41N10
   passes `check_dimensions(node, units, target_units)`, with no exception.
   For the typed fits of the case studies, internal consistency is checked
   instead, as `unknown_constant=True` asks.
4. **Real data under units:**
   - on Kepler B (largest relative error on the outer planets) and Hubble
     CA (RMSE on the six farthest), the median over the seeds is no more
     than 10 % above A's;
   - no fit of the 20 has an error more than ten times A's on the same
     seed.
5. **Formulas:** no more than 3 formulas flagged inexact more than A on the
   615 fits.

Reported beside the criteria:
- the fits on which a seed was placed;
- the time the search for seeds took;
- the exact laws of II.11.3 and their times;
- the deduced constants of Kepler A and Hubble A.

**Confirmation on new seeds**, if the campaign adopts U1: the same U41,
U41N1 and U41N10 jobs with seeds 5 to 9. U1 is kept when:
- U41 exact in U1 is at least 5 more than in A;
- criterion 2 holds;
- criterion 3 holds.

If U1 is not adopted, the cause is examined and reported to the author
before any second change. One candidate is left for that case: restricting
the monomials g of B1 and E1 under units to the dimensionless ones, so that
the forms the search refines are valid ones. It is not tried unless the
campaign says the valid forms were missed.

## The release of 1.1

As for 1.0 (`../results_0.9/PLAN_RELEASE_1.0.md`):
- M1 to M5: equivalence, campaign R paired with 1.0.0, every public figure
  measured again, tests on the wheel, two independent reviews;
- gate 6 decides the publication.

Two things are added:

- **The frozen test set under units.** A units table for the 78 Feynman
  equations of the test set (TF78), with the rules of `units_table.py`. It
  is written and committed before campaign U1 runs, so that nothing
  measured in this phase can shape it. It is measured once, at the
  release, 1.0.0 and 1.1.0 side by side, seeds 5 to 9, and decides nothing.
  Equations to which the rules give no consistent units are left out and
  listed.
- **What 1.1 changes in the documents.** Expected, if U1 is adopted:
  - point 8 of the limits pages;
  - the table of `units=` on II.11.3 in the READMEs and the paper;
  - the typed fits of the Kepler and Hubble case studies, measured again
    and their text updated;
  - the CHANGELOG.

  Without units, every figure of 1.0 stays as measured, and M1 and M2
  check it.

## Cost

615 jobs per version at 30 s, two pairs at a time on 4 cores, about 2.6
hours for the campaign, as much for the confirmation, and 20 short typed
fits.
