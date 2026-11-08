# Plan of version 1.3: the arcsine

Written on 8 November 2026, before any change to the engine and before any
measurement of this phase. Method as for 1.2:
- one process per fit, `PYTHONHASHSEED=0`, one BLAS thread;
- the criteria are written here before the measurement they judge;
- the frozen test set is never used to decide;
- times are compared only between fits run on the same machine, in the same
  campaign;
- every deviation from this plan goes to the author.

The author validates this plan before any change (gate 9). He decides the
publication of 1.3 after its measurement (gate 10).

Gate 9: the author validated this plan in full on 8 November 2026.

## What 1.3 has to do

On 8 November 2026 the author left the choice of what follows the budget
study to Claude (`../results_1.1/ROADMAP.md`, item 5). The diagnostic of
the end of the search (`../results_1.2/end_of_search/README.md`) found that
in 35 of the 40 near fits of F41 the search never offered the structure of
the law. 15 of those 35 are the two laws with an arcsine, and no operator
pool of 1.2.0 can write an arcsine. So Claude chose the arcsine, which the
author had listed after 1.2 (item 3 of the roadmap).

What the arcsine costs today, with 1.2.0:
- **F41 at 30 s** (M2 of the release): I.26.2, arcsin(n·sin θ2), and I.30.5,
  arcsin(λ/(n·d)), are exact in none of their 10 fits. I.30.5 comes back near
  in all five seeds, and I.26.2 is a miss in all five.
- **U41:** the same two laws, 0 of 10.
- **The TP diagnostic:** Snell's law, i2 = arcsin(sin(i1)/n), comes back in
  0 of the 20 fits of each arm, at draws 0 to 4 and at draws 5 to 9 (the
  campaigns of 1.2, `../results_1.2/h1/campaign/`). The approximations it
  returns are useful: 18 and 19 of 20 within 1 % of the law.
- **The page of the limits** names the two laws among the seven equations of
  F41 never recovered, "no operator pool of the engine has the arcsine".

Not in 1.3:
- the change at the end of the search that I.8.14 calls for (the pool of 64
  candidates), recorded in `../results_1.2/end_of_search/README.md`;
- the arctangent and the arccosine as operators. An arccosine is within
  reach of the arcsine and a constant: arccos(x) = π/2 − arcsin(x);
- the other items of the roadmap: constants with units inside a function or
  a sum, a front of candidate laws on small tables, the retrieval of
  structure under noise.

## Change A1: the arcsine

**The operator.** A new operator of one argument, `arcsin`.
- **On the data:** it computes the arcsine of its argument, clipped to
  [−1, 1]. The clip is its guard, as the other operators have theirs: the
  division, the logarithm, the root and the power.
- **The pools:** it joins the pools `trig` and `full`, with weight 2. That is
  the weight of exp, log, sqrt, tanh and sq in `trig`, and of sin, cos, log,
  exp, sqrt and tanh in `full`. It does not join `physical` (the default),
  `poly` or `conserve`.
- **No new seed or template of the search:** the search meets the arcsine
  only by drawing it, as it draws every other operator.

**Everywhere the engine handles an operator,** `arcsin` is handled like `tan`,
the other operator with a guard:
- the evaluation, scalar, vector, compiled and interpreted, and the compiler
  of constants used by the fit of constants;
- the folding of constants;
- the membership lists used by the printing and the mutations;
- the printed formula, `arcsin(…)`, and its sympy form, `asin(…)`;
- the check of the formula against `predict()`. The formula is evaluated
  without the guard, so where the clip acts on the data the formula departs
  from the model and `formula_exact` is False, as for the other guards;
- the units: the argument must be dimensionless, and so is the result, in
  `check_dimensions` and in the typed start (`dim_search`). The typed start
  draws it only where the pool has it.

**What does not change:** every fit run with `physical`, `poly` or `conserve`.
Those pools draw from their own lists, which A1 leaves as they are. The
default pool is `physical`. So are:
- the 31 other equations of F41;
- the real data of the decision bench;
- nine of the ten experiments of the TP diagnostic;
- the TP notebook.

The mechanics below check this to the bit.

**What changes beyond the benches:** the SRBench wrapper tries
`operators="full"` among its settings
(`../results_1.1/srbench_2aabbb6/`). Once 1.3 is on PyPI, those runs have
the arcsine. The author is told before the publication (gate 10).

## Mechanics, before any fit of the campaign

1. **The pools without the arcsine are untouched.**
   - The thirteen reference configurations of `speed_equivalence.py` are
     compared with the 1.2.0 wheel. The eleven that use `physical` must be
     identical. E_minmax (`full`) and L_standard (`trig`) may change, and
     what they return is reported.
   - Fits bounded by 20 generations, with no time limit, so that the
     comparison does not depend on timing, must return the models of the
     1.2.0 wheel run the same way:
     - F41 seed 0, the 31 equations of the pool `physical`;
     - U41 seed 0, the same 31;
     - R6 and R7raw, fold 0 of each dataset.
   - The nine experiments of the TP diagnostic that use `physical`, both
     arms, draw 0, under the defaults: the models of 1.2.0.
2. **The operator, checked by itself.**
   - On 200 random trees with `arcsin`, whose argument falls inside and
     outside [−1, 1], every path of evaluation agrees to 1e-12: scalar,
     vector, compiled, interpreted, and the compiler of constants.
   - `arcsin(0.5)` folds to 0.5235987755982989.
   - The printed formula and its sympy form reproduce `predict()` where the
     argument stays in [−1, 1], and `formula_exact` is False where the clip
     acts on the data.
   - `check_dimensions` accepts the arcsine of a dimensionless quantity and
     refuses the arcsine of a length.
3. **A fit can find it:** a fit of I.30.5 with the pool `trig` and
   `generations=200` draws the arcsine. Whether it returns the law is
   reported, and decides nothing.
4. **Tests:** the test suite passes, with new tests:
   - the evaluation and the guard of the arcsine;
   - the formula and its sympy form;
   - the units;
   - its absence from the pool `physical`.

**Mechanics held on 8 November 2026** (commit 496704b, `a1/README.md`):
1. **The pools without the arcsine are untouched.** The eleven reference
   configurations of the pool `physical` are identical to the 1.2.0 wheel.
   E_minmax and L_standard change, with no arcsine in their formulas. The
   147 fits are identical in every field.
2. **The operator holds**, with one deviation from the wording above. The
   scalar path, used only for display, already computes a power with a
   variable exponent otherwise than the other paths in 1.2.0. So it is
   compared on the 174 trees of 200 without a power. The other paths are
   compared on all 200, bit for bit.
3. **The fit of I.30.5 draws the arcsine** in 26 of its 109 candidates. It
   returns an approximation with tanh, with 1 − R² of 2.1e-11, which counts
   as exact by the bench's threshold. So the campaign reports, for each
   exact fit of the two arcsine laws, whether its formula has the arcsine.
4. **The tests:** 177 pass. 7 of the 8 new tests fail on the 1.2.0 wheel.

The options of the benches leave their other runs unchanged
(`a1/bench_options_check.txt`).

## The benches

- **Dtrig.** The kinds feyn, ufeyn, feyn_n1 and feyn_n10 of
  `phase1_bench.py`, restricted to the ten equations of F41 whose pool is
  `trig`, seeds 0 to 4: 200 fits per version. The settings are those of the
  bench: 30 s, 1,000 generations, `parallel=False`. These ten equations are
  II.15.4, I.18.12, III.15.12, I.26.2, I.30.5, I.37.4, I.50.26, II.6.15b,
  III.9.52 and III.17.37. `phase1_bench.py` gets a `--problems` option for
  this, checked to leave its jobs unchanged without it.
- **TPsnell.** Snell's law in `tp_diagnostic.py`: both arms, 10 and 20
  points, 2 % and 5 % noise, draws 0 to 4 (40 fits per version), under the
  API defaults, so that the stop of 1.2 acts. `tp_diagnostic.py` gets an
  `--experiments` option for this, checked to give the same jobs and data
  without it.

## Campaign A1 (decides)

A is the 1.2.0 wheel from PyPI (`/venv12p`). B is the wheel of the candidate,
built from the commit of A1 in a fresh environment with the same packages.
The two run paired, each job started with both at the same time, on Dtrig
and TPsnell.

With 1.2.0 (M2 of the release and the campaigns of 1.2), on the ten
equations of the pool `trig`:

| kind | exact or structure retrieved, of 50 | of which the arcsine laws, of 10 |
|---|---|---|
| F41 | 20 | 0 |
| U41 | 20 | 0 |
| F41N1 | 15 | 0 |
| F41N10 | 14 | 0 |

The figures of A are those of this campaign, not of this table.

A1 is adopted when all of these hold:
1. **The arcsine laws on F41:** I.26.2 and I.30.5 are exact in at least 5 of
   their 10 fits.
2. **Snell's law on TP:** the law comes back, by the test of the
   diagnostic, in at least 10 of the 40 fits, both arms together.
3. **No loss on the other laws of the pool `trig`:** on the eight other
   equations, F41 and U41 each have no fewer exact laws than A minus 2. No
   equation exact at three seeds or more in A falls to one seed or none.
4. **Structure under noise:** on the ten equations, F41N1 and F41N10 each
   have no fewer structures retrieved than A minus 2.
5. **Useful on TP:** Snell's law within 1 % of the law in no fewer fits than
   A minus 2, in each arm.
6. **The units guarantee:** every model returned under units passes
   `check_dimensions`, on U41 and on the units arm of TP.
7. **Time on TP:** the median time of a fit of Snell's law at most 1.5 times
   A's, in each arm.

Reported beside the criteria, deciding nothing:
- the arcsine laws under units;
- the sizes of the formulas;
- how often `formula_exact` is False, and why;
- the fits where the clip acts on the data;
- the times on Dtrig;
- the fits where A and B return different laws.

**Confirmation on new seeds and draws,** if the campaign adopts A1. A and B
run again on Dtrig's kinds feyn, feyn_n1 and feyn_n10 with seeds 5 to 9, and
on TPsnell with draws 5 to 9. A1 is kept when criteria 1 to 5 hold there,
without the parts under units.

If A1 is not adopted, or not kept, the cause is examined and reported to
the author before any second version: another weight, a seed of the search
for the arcsine, or anything else.

## The release of 1.3

As for 1.2 (`../results_1.2/release/README.md`): M1 to M5, then gate 10.
What 1.3 adds:
- **M1** expects the eleven reference configurations of the pool
  `physical` identical to 1.2.0. E_minmax and L_standard are reported.
- **M2**, campaign R paired with 1.2.0 on the whole suite of phase 1 and
  U41 at 30 s, with the thresholds of the release of 1.2:
  - the fits of the pool `physical` return the same models, up to the
    timing of the time budgets;
  - the fits of the pool `trig` are judged by the criteria of A1 above, not
    by identity;
  - the frozen test set is published as measured and decides nothing. It
    has 17 equations of the pool `trig`, and one arccosine law,
    feynman_test_10.
- **M3** measures again every public figure that the arcsine moves.
- **Documents:**
  - the READMEs (the operators of `trig` and `full`, the counts of F41);
  - the pages of the limits (point 1, where the two arcsine laws leave the
    list if they come back);
  - the CHANGELOG;
  - `DIAGNOSTIC_TP.md`, left as written, with a note;
  - the paper, if its figures move.

## Cost

Estimated from the times of the campaigns of 1.2, on 4 cores, in slices of
under two hours whose records resume:
- the mechanics: about an hour;
- campaign A1: Dtrig for A and B (400 fits at 30 s), about an hour, and
  TPsnell (80 fits), a few minutes;
- the confirmation: about 45 minutes;
- the release, M1 to M3, as for 1.2: about 15 hours.

About 18 hours of machine time in all. The engine work (A1 and its tests)
comes after gate 9 and before the mechanics.
