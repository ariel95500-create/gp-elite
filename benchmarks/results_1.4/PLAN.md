# Plan of version 1.4: noise and small tables

Written on 10 November 2026, before any change to the engine and before any
measurement of this phase. Method as for 1.3:
- one process per fit, `PYTHONHASHSEED=0`, one BLAS thread;
- the criteria are written here before the measurement they judge;
- the frozen test sets are never used to decide;
- times are compared only between fits run on the same machine, in the same
  campaign;
- every deviation from this plan goes to the author.

The author validates this plan before any change (gate 11). He decides the
publication of 1.4 after its measurement (gate 12).

Gate 11: the author validated this plan in full on 11 November 2026. He
could not gather tables measured by students, so 1.4 is measured without
them.

Amendment of 11 November 2026, after gate 11 and before any change: a frozen
noisy test set, TF78N, is added to the benches (its section is below). The
rest of the plan is as validated.

## What 1.4 has to do

On 10 November 2026, the day 1.3.0 was published, the author asked for a
review of the weaknesses of the engine, and then for this plan. The review
is `analysis/README.md`, with its scripts. It reads the records of 1.3.0 on
the decision bench and those of the TP diagnostic. What it found:

- **The first weakness is noise.** 1.3.0 returns 171 exact laws of 205
  without noise. It retrieves the structure of the law in 116 fits with 1 %
  noise and 87 with 10 %.
- **Under noise the seeds decide.** With 1 % noise, the structure comes back
  in 108 of the 140 fits where a noise-tolerant seed was placed, and in 8 of
  the 65 where none was.
- **Three rules of the seed finders fail under noise:**
  - a threshold fixed for the noise of the bench, which refuses the true law
    on a pendulum table with 5 % noise;
  - a target that must keep one sign, which the noise breaks near zero;
  - the first form that passes kept for the best.
- **On tables below 30 rows there is no choice of model.** The engine keeps
  no hold-out, tracks no candidate and returns the best individual of the
  search on the training rows. On the TP diagnostic, plain arm:
  - the thin lens comes back in 2 fits of 40, though its seed is placed;
  - Newton's cooling, which has no seed, in 9 of 40;
  - the pendulum in 30 of 40 and the spring in 29;
  - every law returned is printed with an additive constant, which only
    Newton's cooling has.

Teaching is the first audience of GP_ELITE (decision of 26 October 2026),
and a table of students is small and noisy. So 1.4 has three changes, each
measured and adopted by itself, in this order:
- **N2:** the noise-tolerant seed finders see through the noise;
- **S1:** on tables below 30 rows, the candidates compete in a
  cross-validation;
- **E2:** a seed for a constant plus an exponential.

It also has one correction of a text, W1, below.

Not in 1.4:
- constants with units inside a function or a sum. Under units, the
  capacitor, Newton's cooling and the thin lens still return a poor formula;
- the threshold of the noise-tolerant seeds on tables of 30 rows and more.
  It stays at 1.5 % of the variance, which protects the real data;
- the choice between forms that the data cannot tell apart on such tables,
  and the unequal coefficients that the scaling of each column leaves in a
  sum (I.8.14 under noise);
- the laws the search never builds (I.37.4, I.50.26, III.9.52, III.17.37,
  III.10.19);
- the size of the models on small real datasets, and their collapses out of
  the training range;
- a printed formula that shows the clip of the arcsine, and the pool of 64
  candidates at the end of the search.

## The benches

- **Dnoise.** The kinds feyn_n1, feyn_n10, ufeyn_n1 and ufeyn_n10 of
  `phase1_bench.py`: the 41 equations of the decision bench with 1 % and
  10 % noise, without and with units, seeds 0 to 4. That makes 820 fits per
  version, at 30 s.
- **Dguard.** The kinds feyn, ufeyn, real and realraw: 540 fits per version.
- **TP.** The TP diagnostic (`tp_diagnostic.py`): ten experiments, 10 and 20
  points, 2 % and 5 % noise, two arms, under the API defaults. Draws 0 to 4
  decide, 400 fits per version. The confirmations use draws 10 to 14, which
  no version has run.
- **New draws of the noise.** The noisy kinds draw their noise once per
  equation: the five seeds of an equation fit the same noisy targets. A
  confirmation on new seeds would fit the same data again. `phase1_bench.py`
  gets a `--noise-draws` option that draws other noises, checked to leave
  its jobs and data unchanged without it.

### A frozen test set for teaching, TPT10

The TP diagnostic is now a design set: its failures were read to choose the
changes of this plan. So ten other classic experiments are frozen here,
before any change, and never used to decide. They are added to
`tp_diagnostic.py` as a second list, with the protocol of the diagnostic: 10
and 20 points, 2 % and 5 % noise, draws 0 to 4, two arms, 400 fits.

| key | experiment | law | inputs and ranges (SI) | under units |
|---|---|---|---|---|
| ohm | Ohm's law | U = R·I, R = 47 Ω | I, 0.01 to 0.20 A | within reach |
| torricelli | draining tank | v = √(2·g·h) | h, 0.05 to 0.50 m | within reach |
| boyle | Boyle's law | P = k/V, k = 6 J | V, 2e-5 to 6e-5 m³ | within reach |
| kepler3 | Kepler's third law | T = 2π·√(a³/GM), GM = 1.32712e20 m³/s² | a, 5.8e10 to 1.43e12 m | within reach |
| interfrange | Young's fringes | i = λ·D/a | λ, 4.5e-7 to 6.5e-7 m; D, 1 to 2 m; a, 1e-4 to 5e-4 m | within reach |
| malus | Malus's law | I = I0·cos²θ, I0 = 800 W/m² | θ, 0 to 1.5 rad (pool `trig`) | within reach |
| charge | capacitor charge | u = E·(1 − exp(−t/τ)), E = 5 V, τ = 1 s | t, 0 to 5 s | not within reach |
| michaelis | enzyme kinetics | v = Vmax·S/(Km + S), Vmax = 0.01 mol/(m³·s), Km = 2 mol/m³ | S, 0.5 to 10 mol/m³ | not within reach |
| ph | pH of a strong acid | pH = −log10(c), c in mol/L | c, 0.001 to 0.1 | not within reach |
| thermistance | thermistor | R = R0·exp(B·(1/T − 1/T0)), R0 = 10 kΩ, B = 3950 K, T0 = 298.15 K | T, 283.15 to 353.15 K | not within reach |

- **Data:** the generator of the diagnostic, with these experiments
  numbered 10 to 19 after its ten.
- **Baseline:** measured with 1.3.0 from PyPI before any change of the
  engine. Only its table of counts is read.
- **At the release:** measured again and published as measured.
- **Real tables.** If the author gives tables measured by students before
  the campaign of S1, they form a third set. It is frozen the day it is
  received, measured the same way, and decides nothing.

### A frozen noisy test set, TF78N (amendment of 11 November 2026)

At gate 11 the author proposed the noisy files of the AI Feynman repository
in the place of real tables. That repository holds no such file: its 61
files were listed on 11 November 2026, and none has a noise suffix. The
bench draws its own noise anyway. His proposal points to something the plan
lacks, though:
- N2 was designed on the noisy records of the 41 equations of F41;
- its confirmation draws new noises on those same 41 equations;
- so nothing measures N2 on equations it was not designed on.

The 78 equations of the frozen test set TF78 therefore get the noise of the
decision kinds:
- **Kinds:** tf_n1 and tf_n10 without units, utf_n1 and utf_n10 under
  units. They have 1 % and 10 % Gaussian noise on the training targets,
  drawn once per equation as for F41, and one seed, 5, the first of the test
  seeds. That makes 156 fits without units and 156 under units, at 30 s.
  They run on request only.
- **Baseline:** measured with 1.3.0 from PyPI before any change of the
  engine. Only its counts by kind are read.
- **It never decides.** At the release, M2 measures it again, paired with
  1.3.0, and it is published as measured.
- **It does not stand for real tables.** It holds laws of the Feynman
  lectures with a Gaussian noise on exact inputs, as the decision bench
  does. That every result on teaching comes from simulated tables stays a
  limit, written in the documents of 1.4.
- **Cost:** about 40 minutes for the baseline, and about 80 minutes in the
  M2 of the release.

## Change N2: the noise-tolerant finders see through the noise

The noise-tolerant stage keeps its place: it runs when no exact seed of the
binomial forms or of the functions of a monomial was placed. It keeps its
score, 1 − R² after linear scaling on the training rows, and its threshold
of 1.5 %. N2 changes how its candidates are made.

1. **A second pass, which noise near zero does not stop.** Each finder runs
   as today, and once more:
   - with its least squares on logarithms weighted by y²;
   - without the condition that the target keep one sign.

   A noise of constant size σ moves log|y| by about σ/|y|, so the weight y²
   is the one such a noise calls for. The rows near zero, where the noise
   changes the sign, then weigh almost nothing. Today's pass is right for a
   noise proportional to the value. The candidates of both passes go on.
2. **Every argument tried, the best kept.** In this stage, the finders of
   the sine and cosine and of the logarithm go through their whole library.
   They return their three best forms by the score, and the first that
   passes with them.
3. **The inner constant fitted before the score.** Each candidate has its
   inner constants (the c of b·f·φ(c·g), the ω of the sine) fitted on the
   training rows by the engine's fit of constants. Its exponents stay the
   half-integers the finder rounded.
4. **Placed as today:** the candidates are deduplicated by their form, and
   those within the threshold are placed, the best first, twelve at most.

**What N2 does not change:**
- the exact seeds and their thresholds, and every fit where one is placed;
- the search, the final selection and the printed formula.

N2 only adds candidates and scores them better: every seed 1.3.0 places is
still placed.

### Mechanics of N2, before any fit of its campaign

1. **The exact seeds are untouched.** Fits bounded by 20 generations, with
   no time limit: F41 and U41 at seed 0, R6 and R7raw at fold 0 (95 fits).
   Where the noise-tolerant stage of 1.3.0 does not run, the model must be
   that of 1.3.0. The other fits are reported.
2. **No seed is lost.** On the 82 noisy targets of F41 (41 equations, 1 %
   and 10 %), every seed that 1.3.0 places is placed by the candidate.
3. **The second pass.** On the noisy targets of I.40.1, II.35.18, II.11.27,
   I.32.5 and III.19.51, a candidate with the form of the law is made, and
   it is placed wherever the law itself is within the threshold.
4. **The best kept.** On III.15.12 with 1 % noise, the seed in k·d is
   placed. On I.44.4 with 1 % noise, the form with the logarithm is among
   the candidates.
5. **The real data.** The candidates on the 13 real fits of item 1 are
   reported with their scores. With 1.3.0 none is within the threshold.
6. **The time of the stage** is reported on these fits.
7. **Tests:** the test suite passes, with new tests of items 2 to 4.

Note of 12 November 2026, after the mechanics of N2 and before any fit of
its campaign (`n2/mechanics/README.md`):
- **One rule beyond the letter of N2.** The mechanics found a fourth rule of
  the finders that fails under noise: the finder of the logarithm took the
  smallest coefficient above 1e-6 as the unit of the exponents of g, and an
  exponent that is zero has, under noise, a coefficient of the order of the
  noise (on I.44.4 with 1 % noise, the exponents 564 and −566 instead of 1
  and −1). In the noise-tolerant stage only, a coefficient below a twelfth
  of the largest now counts as zero. The exact finders are unchanged.
- **Item 3 holds at 1 % noise, not at 10 %** for I.40.1, II.35.18 and
  II.11.27: there the law is within the threshold, but no candidate has its
  form. With 10 % noise the least squares on logarithms still give the
  wrong exponents. Choosing by the score in every finder was tried on the
  same targets and is not kept: three more targets at 10 % of 41, none of
  these three, for twice the time of the stage.
- **The other items hold.**

The criteria of the campaign are unchanged.

### Campaign N2 (decides)

A is 1.3.0 from PyPI (`/venv13p`). B is the wheel of the candidate, in a
fresh environment with the same packages. The two run paired on Dnoise,
Dguard and TP. The figures of A are those of the campaign.

N2 is adopted when all of these hold:
1. **Structure under noise, without units:** F41N1 and F41N10 together have
   at least 15 more structures than A (of 410), and neither has fewer than A
   minus 3.
2. **Structure under noise, under units:** U41N1 and U41N10 each have no
   fewer structures than A minus 3.
3. **No loss without noise:** F41 and U41 each have no fewer exact laws
   than A minus 3. No equation exact at three seeds or more in A falls to
   one seed or none.
4. **Real data:** the median test R² of the R6 folds is not more than 0.005
   below A's. R6 and R7raw have not more than 2 more collapses out of domain
   than A.
5. **The units guarantee:** every model returned under units passes
   `check_dimensions`.
6. **TP:** in each arm, the law comes back in no fewer fits than A minus 5
   (of 200), and the median time of a fit is at most 1.5 times A's.

Reported beside the criteria, deciding nothing:
- the structures by equation;
- the seeds placed, and the real fits where one is placed;
- the sizes of the formulas, and how often `formula_exact` is False.

**Confirmation.** New draws of the noise, 1 to 4, on feyn_n1 and feyn_n10 at
seed 0: 328 fits per version. N2 is kept when B has at least 10 more
structures than A over the 328 fits, and no fewer than A minus 3 on each of
the two kinds.

If N2 is not adopted or not kept, the cause is examined and goes to the
author. Its parts can then be measured one by one.

Campaign N2, 12 and 13 November 2026 (`n2/campaign/README.md`): **not
adopted.** Criteria 1, 2, 4, 5 and 6 hold (the structure under noise 203 →
246 of 410 without units). Criterion 3 fails: F41 has 166 exact laws
against 171, and I.26.2 falls from three exact seeds to none. The cause,
examined on the fits concerned, is the fit of the constants of each
candidate (item 3 of N2). N2 is withdrawn from the candidate, and the
confirmation is not run; the cause goes to the author. The campaigns of S1
and E2 take 1.3.0 as their base.

## Change S1: on small tables, the candidates compete in a cross-validation

S1 acts only on tables below 30 rows, where the engine keeps no hold-out.

1. **The candidates.**
   - *The family forms.* For these tables the threshold of 1.5 % is not
     used. The eight best candidates of the noise-tolerant stage that
     explain at least half of the variance are placed at the start, and
     kept for the end.
   - *The champions of the search:* each new best individual on the
     training rows, 64 at most, as the hold-out pool keeps them today.
   - *Variants* of each finalist: without the additive constant of the
     final scaling, and with each fitted exponent set to the nearest
     half-integer.
2. **The finalists,** 40 at most: the family forms, the 8 best of the
   search on the training rows, the 8 smallest within the tolerance band,
   and their variants.
3. **The cross-validation.** K = min(n, 10) folds; the fold of row i is
   i mod K, so no number is drawn. For each fold the constants of the
   candidate are fitted again on the other rows, and its squared errors on
   the rows of the fold are kept. Its error is their mean over the table.
4. **The choice.** Among the candidates within one standard error of the
   best, or within the tolerance of 0.003 in R² that the hold-out uses, the
   model returned is the one with the fewest fitted constants, then the
   smallest, then the most accurate. The priority to an exact law and the
   tie-breaks of today (a formula that reproduces the model, stable near
   the domain) are kept.
5. **The list of candidates.** `result.pareto`, None below 30 rows today,
   holds the front of these candidates by size and cross-validated error.
6. **Bounds:** the cross-validation respects the deadline of `time_limit=`
   as the final polish does, and is not run with a custom loss.

**What S1 does not change:** every fit of 30 rows or more.

### Mechanics of S1

1. **Tables of 30 rows and more are untouched.** The 95 bounded fits of the
   mechanics of N2, and the reference configurations of
   `speed_equivalence.py` that have 30 training rows or more, return the
   models of the candidate without S1.
2. **The cross-validation by itself.** Its folds are the same from one run
   to the next. On 12 exact points of a known law, the law is chosen, with
   an error of zero to numerical precision.
3. **The variants.** On exact points of T = 2π·√(L/g), a candidate
   `a + b·sqrt(L)` loses to its variant without the constant. A candidate
   with the exponent 1.96 on exact points of d = ½·g·t² loses to its variant
   with the exponent 2.
4. **The list.** On a table of 10 points, `pareto` is a list, and each
   entry gives its formula and its error.
5. **Under units,** every candidate of the cross-validation passes the gate
   of dimensions.
6. **Tests:** the test suite passes, with new tests of items 1 to 5.

### Campaign S1 (decides)

A is the candidate before S1: with N2 if N2 is kept, 1.3.0 otherwise. B adds
S1. The two run paired on TP, draws 0 to 4. The other benches have no table
below 30 rows, and item 1 of the mechanics stands for them.

S1 is adopted when all of these hold:
1. **TP, plain arm:** the law comes back in at least 15 more fits than A
   (of 200).
2. **No experiment falls:** in the plain arm, no experiment has the law in
   more than 2 fewer fits than A (of 20).
3. **TP, units arm:** the law comes back in no fewer fits than A minus 3
   (of 200), and every model passes `check_dimensions`.
4. **Time:** in each arm, the median time of a fit is at most 1.5 times
   A's.

Reported beside the criteria, deciding nothing:
- the law by experiment, number of points and noise;
- among the plain fits with the law, those printed without an additive
  constant;
- how often the law is on the front returned;
- whether the model returned is a family form, a champion of the search or
  a variant.

**Confirmation.** Draws 10 to 14. S1 is kept when criteria 1 to 3 hold
there.

Campaign S1, 13 November 2026 (`s1/campaign/README.md`): **not adopted.**
A was 1.3.0, N2 being withdrawn. Criteria 1, 2 and 4 fail: the law in 113
fits of 200 against 126 in the plain arm, five experiments fall by more
than 2, and the median time is 1.67 times A's. The units arm holds. The
cause: where the law is lost, the cross-validation chose structures the
search had found on the same few points, whose error it underestimates.
Where it is gained, S1 returns textbook laws (the thin lens in 5 fits,
Newton's cooling in 3). S1 is withdrawn, its confirmation is not run, and
its cause goes to the author. The campaign of E2 takes 1.3.0 as its base.

## Decision of the author after the campaigns of N2 and S1

On 13 November 2026 the author approved the two proposals made to him:
- **N2 is measured again without the fit of the constants of each
  candidate** (item 3 of N2), the part that made the exact laws fall. This
  is N2b: the second pass, the scans of the trigonometric and logarithm
  finders (with the rule of their exponents found by the mechanics), the
  deduplication and the twelve seeds at most, the seeds of 1.3.0 always
  placed. Its mechanics are those of N2 without item 3; its campaign has the
  benches and the six criteria of campaign N2, then its confirmation on new
  draws of the noise. It is measured after E2, on the candidate with the
  changes kept so far.
- **S1 is postponed to the next version,** with a design written in advance
  that answers the cause found by its campaign. Its code stays in the
  engine, switched off, and is not part of 1.4.

## Change E2: a seed for a constant plus an exponential

A new kind among the functions of a monomial: y = a + b·exp(c·g).
- **g** is a column to the power 1 or −1. For tables of at most eight
  columns it can also be the product or the ratio of two columns, as in the
  library of the sine and cosine.
- **c** is found on a grid, then by golden section, on the residual of the
  least squares in (a, b). The fit is in the data: no logarithm of the
  target is taken, so the target need not keep one sign.
- **As an exact seed,** it is placed when it holds to numerical precision
  and its constant a is not zero. With a zero it is the exponential that
  1.0 already fits.
- **In the noise-tolerant stage,** it is a candidate like the others.
- **Only where the pool has the exponential.** Under units it is placed only
  if it passes the gate of dimensions.

### Mechanics of E2

1. **It finds its law.** On 20 exact points of Newton's cooling,
   θ = 20 + 60·exp(−t/600), the exact seed is placed, with a = 20, b = 60
   and c = −1/600 to numerical precision.
2. **It places nothing elsewhere on exact data.** On the exact data of the
   41 equations of F41, no seed of this kind is placed, and the 82 bounded
   fits of F41 and U41 return the models of the candidate without E2.
3. **The real data.** On the 13 real fits, its candidates are reported with
   their scores.
4. **Tests:** the test suite passes, with new tests of items 1 and 2.

### Campaign E2 (decides)

A is the candidate before E2, B adds E2. The two run paired on TP, Dnoise
and Dguard.

E2 is adopted when all of these hold:
1. **Newton's cooling, plain arm:** the law comes back in at least 10 of
   its 20 fits.
2. **No loss on TP:** in the plain arm, no other experiment has the law in
   more than 2 fewer fits than A. In the units arm, the law comes back in no
   fewer fits than A minus 3 (of 200).
3. **No loss on the benches:** F41N1, F41N10, U41N1 and U41N10 each have no
   fewer structures than A minus 3, and criteria 3 to 5 of N2 hold.
4. **Time:** in each arm of TP, the median time of a fit is at most 1.5
   times A's.

**Confirmation.** Draws 10 to 14 of TP. E2 is kept when criteria 1 and 2
hold there.

Campaign E2, 13 November 2026 (`e2/campaign/README.md`): **not adopted.**
A was 1.3.0, N2 and S1 being withdrawn. Criteria 1 and 2 fail: Newton's
cooling has the law in 7 fits of 20 in the plain arm (A 3, the plan asks
10), and the point source falls from 18 to 15. Criteria 3 and 4 hold. The
cause: the seed of E2 has the structure of the law in 18 fits of the
cooling, but on 10 or 20 noisy points the search returns another form in 11
of them, as campaign S1 found; and its form comes within the threshold on
all ten experiments, where its seeds, added to those of 1.3.0, move the
search. E2 is withdrawn, its confirmation is not run, and its cause goes to
the author. The campaign of N2b takes 1.3.0 as its base.

## Correction W1: the warning names the arcsine

The warning of a formula that departs from `predict()` lists the guards
that can act: a power capped or clipped, a division by a denominator near
zero. Since 1.3 the clip of the arcsine is one of them and the text does
not say so. W1 adds it. It changes no model, and a test reads the text.

## Order, and what follows a failure

- The three changes are measured in the order N2, S1, E2. Each campaign
  takes the candidate with the changes kept so far.
- A change that is not adopted, or not kept at its confirmation, is
  withdrawn from the candidate, and its cause goes to the author.
- The engine stays pure Python and NumPy.

## The release of 1.4

As for 1.3 (`../results_1.3/PLAN_RELEASE_1.3.md`): M1 to M5, then gate 12.
Its plan is written before its first measurement, with 1.3.0 from PyPI as
the reference. What 1.4 adds:
- **M2** also runs TP and TPT10, and the real tables if there are any;
- **M3** measures again every public figure, among them the small tables of
  the READMEs and the notebooks, which S1 can change;
- **the documents:** the READMEs, the pages of the limits (points 3 and 10,
  and what stays out of 1.4), the CHANGELOG, the TP notebooks, a note on
  `DIAGNOSTIC_TP.md`, and the paper where its figures move.

## Cost

Estimated on 4 cores, two paired jobs at a time, from the times of the
campaigns of 1.3:
- the bench options, TPT10 and its baseline: about an hour;
- N2: its mechanics, about an hour; its campaign, about 6 hours; its
  confirmation, about 1.5 hours;
- S1: its campaign and its confirmation, about half an hour each;
- E2: its campaign, about 6 hours; its confirmation, about half an hour;
- the release, M1 to M3: about 16 hours.

About 33 hours of machine time in all, beside the work on the engine.
