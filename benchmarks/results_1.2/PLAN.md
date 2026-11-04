# Plan of version 1.2: the lab tables of teaching

Written on 3 and 4 November 2026, before any change to the engine and before
any measurement of this phase. The prototypes below ran gp-elite 1.1.0 as it
is and decide nothing. Method as for 1.1:
- one process per fit, `PYTHONHASHSEED=0`;
- the criteria are written here before the measurement they judge;
- the frozen test set is never used to decide;
- times are compared only between fits run on the same machine
  (`machine.txt` of each campaign); a pair split by a change of machine is
  run again for its time;
- every deviation from this plan goes to the author.

The author validates this plan before any change (gate 7). He decides the
publication of 1.2 after its measurement (gate 8).

Gate 7: the author validated this plan in full on 4 November 2026, and chose
(b) for the time limit of the typed start (see the end of this plan).

## What 1.2 has to do

Teaching became the first audience of GP_ELITE on 26 October 2026
(`../results_1.1/DIAGNOSTIC_TP.md`). The diagnostic of the lab sessions
listed what would have to improve first. On 3 November 2026 the author chose
three of its points for 1.2 (`../results_1.1/ROADMAP.md`, item 3):

1. **H1, a stop when the law holds.** A fit of a student's table takes about
   a minute: 61 s in the median without units and 88 s with them, with
   1.0.0; 62 s and 83 s with 1.1.0 (prototype 1 below). Most of that minute
   changes nothing.
2. **X1, the exponential written as such.** The capacitor discharge comes
   back as `4.86249 * 0.00784758^(0.2 * t)`; a student expects
   E·exp(−t/τ).
3. **C1, an honest message under units.** Under `units=` a constant with
   units cannot sit inside a function or a sum (a time constant τ, an offset
   θa, a focal length f). On those three laws the units mode returns poor
   formulas without a word.

Not in 1.2, by the same choice: building such constants under units, a front
of candidate laws on small tables, the arcsine, and the retrieval of
structure under noise.

## Prototypes, before this plan (decide nothing)

All four ran gp-elite 1.1.0 from PyPI (`/venv11p`), wrapped from outside
without changing what it returns, on the machine of `prototype/machine.txt`
(4 cores, Intel Xeon at 2.80 GHz, AVX-512). The container restarted during
prototype 4; its last 327 fits ran on another machine (Xeon at 2.10 GHz,
AVX-512, which runs these fits faster), whose times are not compared.
Records and scripts are in `prototype/`; `prototype/analysis.txt` is the
output of `prototype/analyse.py`.

**Prototype 1, when the champion reaches its final form**
(`champion_trace.py`, 940 fits). The 400 fits of the TP diagnostic, and the
noisy and real kinds of the decision bench (F41N1, F41N10, R6, R7raw, 30 s
each). At each generation it records the champion the early stop reads.

- TP, plain arm: the first generation's champion already has the final form
  in 77 fits of 200; the form is final from generation 3 in the median (43
  at the 90th percentile), at 2.2 s of a fit of 62 s. Units arm: 85 of 200,
  generation 1, 2.1 s of 83 s.
- Many late changes are rewritings with the same error
  (`sqrt(m) / sqrt(k)` then `sqrt(m / k)`).
- Some late changes lose the law. Gas law, 10 points, 2 % noise, draw 0:
  `n·T/V` is the champion from generation 0; at generation 94 it gives way
  to `n·exp(T)/V`, which follows the noise more closely and is returned.
- On the decision bench a fit at 30 s runs about 50 generations (median 47
  to 51), always up to the time limit. The final form is reached at a median
  of 8 to 20 generations, 39 to 48 at the 90th percentile.

Replayed on these traces (approximate: changes of the constants alone are
not recorded), a stop after P generations without a gain of error of more
than 1 %:
- TP: P = 20 runs a median of 21 % of the generations. It cuts a later gain
  in 52 fits; in 3 of them the final model has the law (the spring, whose
  `sqrt(m/k)` comes at generations 22 to 34). In several others the
  champion at the stop has the law and the final model does not (gas law,
  point source).
- Decision bench at 30 s: P = 20 runs about half the generations and cuts 1
  and 3 retrieved structures on F41N1 and F41N10; P = 30 runs two thirds to
  four fifths and cuts none.

**Prototype 2, under units, what the seed finders find and the gate of
dimensions sets aside** (`units_rejected.py`, 815 fits: the units arm of
the TP diagnostic, and U41, U41N1, U41N10). After the fit, each seed the
gate rejected is scored on the rows its finder saw, beside the model returned
(1 − R² on the training rows).
- The rejected seeds cannot carry a message. On the six laws within reach,
  every fit has some, and all fit worse than the model returned (the best of
  them, median 1 − R² from 0.16 to 3.5, against 0.0002 to 0.013 for the
  model). On the capacitor and Newton's cooling the finders propose nothing
  at all; on the lens what they propose is far worse (median 555). On the
  615 fits of U41, U41N1 and U41N10, a rejected seed fits better in 15, all
  on two equations with noise (I.25.13 and I.29.4), by 5 to 10 %, following
  the noise; never on U41 without noise.
- The error of the model returned does not separate either: up to 0.059 on
  the pendulum (5 % noise, 10 points, the law), from 0.02 on the capacitor
  and 0.0025 on cooling. What comes back on the three limited laws ranges
  from close (cooling, 2 fits of 20 useful) to absurd (`0.0964394 * t` for
  the discharge, 1 − R² = 1.55; `log(|t / t|)` inside another).
- Against the noise actually added (known to the bench, not to the engine),
  the six laws sit at 0.03 to 1.0 times it and the three limited laws at
  0.6 to 15,000 times (median 11 to 90).
- Found on the way: III.19.51 under units takes 600 to 735 s with
  `time_limit=30` (one generation), as in 1.0.0. See *Found during the
  prototypes* below.

**Prototype 3, the plateaus before the exact laws of F41**
(`plateau_trace.py`, 205 fits at 30 s, the error of the champion at every
generation, as 1 − R²). 156 fits of 205 are exact.
- 150 exact fits have the law as champion in the loop, almost always at
  once (generation 0 at the 90th percentile, 28 at most); the loop then ends
  on its exact early stop. In 6 the law comes only after the loop, from the
  polishing and the final selection, on I.8.14, I.16.6 and II.2.42.
- Replayed on these errors (exact up to the end of the loop; what a fit
  stopped earlier would return is not known), a stop on patience stops 49
  fits at P = 20, a median of 55 % into the generations they ran, and stops
  3 exact fits before their final form (I.8.14 seed 4, I.16.6 seed 2,
  II.2.42 seed 0); at P = 30, 34 fits and one exact fit (II.2.42 seed 0); at
  P = 40, none.
- These fits ran about 50 generations (30 s). Under the defaults they run
  100, and what a stop would cut between generation 50 and 100 is not in
  this record; campaign D measures it.

**Prototype 4, the stop on patience tried on the TP fits**
(`patience_try.py`, the 400 fits of the TP diagnostic for each of P = 10, 20
and 30, 1,200 fits, no crash). The rule of H1 below, applied from outside
the engine, against 1.1.0 on the same fits (prototype 1). "Reading": the
experiments whose law comes back in at least 3 of 5 draws at 2 % noise, at
10 and at 20 points, as in the diagnostic.

| arm | P | law (of 200) | useful (of 200) | reading 10 / 20 points | median time |
|---|---|---|---|---|---|
| plain | 1.1.0 | 119 | 175 | 7 / 8 | 62.3 s |
| plain | 10 | 126 | 167 | 7 / 7 | 5.5 s |
| plain | 20 | 125 | 169 | 7 / 8 | 11.0 s |
| plain | 30 | 126 | 174 | 7 / 8 | 15.1 s (73 fits; 61.5 s in 1.1.0) |
| units | 1.1.0 | 120 | 140 | 6 / 6 | 83.1 s |
| units | 10 | 119 | 138 | 6 / 6 | 5.4 s |
| units | 20 | 120 | 140 | 6 / 6 | 11.6 s |
| units | 30 | 120 | 139 | 6 / 6 | not on the first machine |

- At P = 30 every fit ends on the patience, at generation 30 in the median
  (43 to 44 at the 90th percentile).
- The law, plain arm, P = 30: gained in 9 fits, where 1.1.0 lost it late
  (gas law 3, point source 3, capacitor 1, lens 1, electric power 1); lost
  in 2, the spring at 10 points (2 % draw 1, 5 % draw 3), whose `sqrt(m/k)`
  comes late. At P = 20 the spring loses 4. Units arm: the six laws within
  reach come back in 120 of 120 at P = 20 and 30, 119 at P = 10.
- Useful, P = 30: the plain arm loses the 2 spring fits and gains the
  electric power (−1); the units arm loses one cooling fit, a law units
  limit (`0.0239217 * t`, −1). At P = 20 the plain arm loses 7 and gains 1
  (−6): the 4 spring fits, one cooling and two lens fits.

**The choice of P = 30.** At P = 20 the plain arm loses 6 useful fits and 4
spring laws, and prototype 3 puts 3 exact fits of F41 at risk; at P = 30, 1
useful fit, 2 spring laws and 1 exact fit (II.2.42 seed 0), for a fit about
four times faster than 1.1.0. P = 40 was not tried on the TP fits. P was
chosen on draws 0 to 4 of TP and on the records of F41: the criteria on TP
are therefore checked again on draws 5 to 9, and campaign D measures the
defaults for the first time.

## Change H1: a stop on patience, when the engine chooses the budget

**The rule.** In the generation loop, the error the early stop already
reads (the hold-out MSE when there is a hold-out, the training MSE
otherwise) counts as a gain when it falls below 0.99 times the best error
seen in this run. When P generations pass without a gain, the loop ends as
it does on an exact law, and the fit goes on to its usual end: constants
polished, final selection, formula. P = 30. In the parallel loop, which
advances by rounds of several generations, the generations are counted the
same way at the end of each round. Each restart counts its own patience.

**When it applies.** Only when the call gives neither `generations` nor
`time_limit`, that is when the engine chooses the budget, as a teacher's
call does. A call that sets a budget gets the search of 1.1 in full: the
decision bench (30 s and 1,000 generations), the SRBench wrapper, the case
studies, every script that names its budget. A new parameter
`patience=None` says so: `None` is this rule, an integer k applies a
patience of k generations whatever the budget, 0 turns it off.

Why not everywhere: on the decision bench a fit at 30 s runs only about 50
generations, the stop would save little there, and prototype 1 shows it
would cut late gains. A user who names a budget asks for it to be used.

**Mechanics, before any fit of the campaign:**
1. `patience=0`: the thirteen reference configurations of
   `speed_equivalence.py` return the models of the 1.1.0 wheel, and the test
   suite passes.
2. Default patience, on the same configurations, all of which set their
   budget: identical to the 1.1.0 wheel.
3. A default call on the gas law of the TP diagnostic (10 points, 2 %,
   draw 0): the loop ends 30 generations after the last gain, and the model
   is the one prototype 4 recorded for that fit.
4. The same call with `parallel=True`: the stop acts in the parallel loop.

New tests: the stop acts only under the defaults or an explicit
`patience`; `patience=0` and any explicit budget leave the run of 1.1.

**The benches.**
- **TP.** `tp_diagnostic.py` as in the diagnostic: 10 experiments, 10 and
  20 points, 2 % and 5 % noise, the plain and the units arms, the API
  defaults with `parallel=False`. Draws 0 to 4 decide (the prototypes used
  them); draws 5 to 9 confirm. The script gets a `--draws` option for this,
  checked to give the same jobs and data for draws 0 to 4.
- **D, the decision bench under the defaults.** The kinds feyn, feyn_n1,
  feyn_n10, real, realraw, ufeyn, ufeyn_n1 and ufeyn_n10 of
  `phase1_bench.py`, seeds 0 to 4 (1,360 fits per version), with the API
  defaults: no `generations`, no `time_limit`, the pool of each problem,
  `parallel=False`. `phase1_bench.py` gets a `--defaults` option for this,
  checked to leave its other runs unchanged. It is the regime where H1
  acts, on the laws and real data the project measures everything on.

**Campaign H1** (decides). A, the 1.1.0 wheel from PyPI, against the
candidate with H1, paired, on TP (draws 0 to 4, 400 fits) and D (1,360).
H1 is adopted when all of these hold:

1. **Time.** On TP, the median time of a fit is at most a third of A's, in
   each arm.
2. **The law on TP.**
   - Plain arm: the law is returned in no fewer fits than A's minus 2 (of
     200), and the reading of the diagnostic counts no fewer experiments
     than A at 10 and at 20 points.
   - Units arm: the six laws within reach come back in no fewer than 118 of
     their 120 fits.
   - "Useful" (R² ≥ 0.99 on the noiseless law): no fewer than A's minus 3
     in each arm.
3. **Exact laws on D.** F41 and U41: no fewer than A's minus 3 each, and no
   equation exact in A at three seeds or more falls to one seed or none.
4. **Structure under noise on D.** F41N1, F41N10, U41N1 and U41N10: no fewer
   than A's minus 3 each.
5. **Real data on D.** The median test R² of the R6 folds no more than 0.01
   below A's; R6 and R7raw together no more than 2 more collapses out of
   domain.
6. **The units guarantee.** Every model returned under units on D passes
   `check_dimensions`.

Reported beside the criteria: the times on D, the sizes, the generation of
the stop, the reading per experiment, and the fits where A and H1 return
different laws.

**Confirmation on new draws and seeds**, if the campaign adopts H1: TP with
draws 5 to 9, and D's kinds feyn, feyn_n1 and feyn_n10 with seeds 5 to 9,
A against H1 again. H1 is kept when criteria 1 and 2 hold on TP, and 3 and 4
on the F41 kinds.

If H1 is not adopted, or not kept, the cause is examined and reported to the
author before any second rule or any other P.

## Change X1: the exponential written as such

X1 changes the printed formula only; the model, `predict()` and the search
are those of 1.1.

**The rewriting.** In `formula.raw_formula`, after the formula has passed
its check against `predict()`:
1. each power with a numeric base, `c^u`, becomes `exp(ln|c| · u)`, its
   constants folded again (`0.00784758^(0.2 * t)` becomes
   `exp(-0.970 * t)`);
2. each exponential of a number times one variable, `exp(k · x)`, is
   written with its scale, `exp(-x / τ)` with τ = −1/k when k < 0, and
   `exp(x / τ)` with τ = 1/k when k > 0 (`exp(-t / 1.031)`).

The rewritten formula is kept only if it passes the same check, to 1e-7 of
the scale of the predictions, as every other rewriting of the formula. The
sympy form follows the same tree.

**Checks** (decide): the models, the predictions and `formula_exact` are
those of 1.1.0 on every fit of M2 of the release; on TP, every plain fit of
the capacitor and of Newton's cooling whose model is an exponential of t
prints `exp(-t / τ)` and no power with a numeric base; new tests check the
two rewritings, their refusal when the check fails, and the parsable form.

## Change C1: an honest message under units

C1 adds a message; the model returned under units, its formula, `predict()`
and the guarantee of dimensions stay those of the fit under units.

**What it rests on.** Prototype 2 rules out the seeds the gate sets aside
and any fixed threshold on the error. What separates the limited laws is a
fit of the same rows without units: on the capacitor, cooling and the lens
the plain arm returns a formula that follows the data, and the units arm
does not. Prototype 4 gives that comparison on the 200 fits of the units
arm with both arms stopped at P = 30, as C1 would run under the defaults.
The error under units over the error without units (1 − R², training rows)
has a median of 1.05 on the six laws within reach (at most 3.95), 1.02 on
Snell's law (at most 1.27), and 72 on the three limited laws (at least
1.61). With a message when the error under units is above 0.001 and at
least k times the other:

| k | six laws within reach | Snell's law | three limited laws | limited, where the fit without units has the law |
|---|---|---|---|---|
| 3 | 3 of 120 | 0 of 20 | 59 of 60 | 20 of 20 |
| 5 | 0 of 120 | 0 of 20 | 56 of 60 | 20 of 20 |
| 10 | 0 of 120 | 0 of 20 | 53 of 60 | 20 of 20 |

The four limited fits without a message at k = 5 are at 5 % noise: two of
the lens, where neither formula follows the data (1 − R² of 0.18 and 0.29
under units, 0.04 and 0.07 without), and two of cooling, where the formula
under units is nearly as close (ratios 3.9 and 1.6). The highest ratios
within reach are 3.95 (point source, whose error under units, 0.0002, is
below the floor), 3.69 (fall) and 3.53 (gas law).

**The check.** Under `units=`, once the fit is done, the engine fits the
same rows without units: the same operators, the same seed, the same rule
of budget (under the defaults, the stop of H1). It compares the error of
the two models on the training rows (1 − R²). When the error under units is
above 0.001 and at least 5 times that of the fit without units, a warning
(`UserWarning`, as the other warnings of the engine) says so in these terms:
under units the formula found fits these data less well than a formula
found without them (both errors, and that formula); under units a constant
with units cannot sit inside a function or a sum (a time constant, an
offset, a focal length); if the law expected has one, the formula without
units may be the closer one. The fit without units is kept on the result
(`units_check`: its formula and the two errors), and is not returned as the
model.

**When it runs.** As H1, only when the engine chooses the budget. A new
parameter `units_check=None`: `None` runs it under the defaults, `True` runs
it whatever the budget (with the same budget as the fit, which doubles the
time), `False` never. Without `units=` it does nothing.

**Mechanics:**
1. Under units, the model returned, its formula, `predict()` on the
   training rows and `check_dimensions` are the same with `units_check`
   True and False, on the units arm of TP (draw 0) and U41 seed 0; a fit
   run after another in the same process returns the same as alone.
2. Without units and with an explicit budget, nothing runs (the thirteen
   reference configurations as in H1).
3. On the capacitor (10 points, 2 %, draw 0) the warning comes and names an
   exponential formula; on the pendulum it does not.

**Campaign C1** (decides), on the candidate with H1 and C1, against the
records of campaign H1 for the same fits: the units arm of TP, draws 0 to 9
(400 fits), and D's kinds ufeyn, ufeyn_n1 and ufeyn_n10 (615). k was chosen
on draws 0 to 4, so criteria 2 and 3 are judged on draws 5 to 9. C1 is
adopted when all hold:
1. **Same models.** Every model returned under units is the one of the
   candidate with H1 alone on the same fit (formula and predictions).
2. **No message where units hold.** On the six laws within reach and on
   Snell's law, a message in at most 2 of the 140 fits of draws 5 to 9; on
   U41 without noise, no message on an exact fit.
3. **A message where units limit.** On the capacitor, cooling and the lens,
   draws 5 to 9: a message on every fit where the fit without units kept
   on the result returns the law (by the diagnostic's test of the law), and
   on at least 45 of the 60 fits.
4. **Time.** On TP, the median time of a fit of the units arm with the check
   is at most half that of 1.1.0 (campaign H1, arm A). Prototype 4 timed
   the fit without units at 15.1 s at P = 30 and the units fit at 11.6 s at
   P = 20 (not at P = 30 on the first machine), against 83 s.

Reported beside: the messages on draws 0 to 4, on U41N1 and on U41N10, and
for each message the formula without units it names.

## Found during the prototypes: a time limit that does not bound the typed start

Under `units=`, III.19.51 takes 600 to 735 s with `time_limit=30` and runs
a single generation, in U41, U41N1 and U41N10, at every seed. 1.0.0 did the
same (596 s, `../results_1.1/campaign/U41_A_1.0.0.jsonl`). Stacks sampled
during such a fit put the time in the building of the typed starting
population: `Island.initialize` draws typed random trees until the
population is full or 20 draws per place have failed
(`dim_search._build_ek`), and that step does not look at the deadline. The
README says that `time_limit=` stops the search cleanly at the deadline;
here it does not. The TP laws are not concerned: their units fits run their
hundred generations in about 80 s.

The author chooses, with this plan (nothing of it in 1.2 without that
decision):
- (a) say it, in the README and the page of the limits, with this figure;
- (b) correct it: the typed start looks at the deadline and, once it is
  reached, completes the population with copies, as it already does after
  its failed draws. That changes the models of III.19.51 under units; M2
  would name them, and the campaigns above would run with the correction.

**Decided by the author on 4 November 2026: (b).** His reason is not the
README: a behaviour that is not explained may hide others. So the
correction comes after a diagnostic, D0, which explains it first.

**D0, the typed start** (decides nothing; before any change to the engine).
On 1.1.0, wrapped from outside as the prototypes, `time_limit=30`, seed 0:
1. III.19.51 under units: the size of the population asked, the number of
   typed draws, how many fail and why (`dim_search._build_ek`), the time of
   a draw that succeeds and of one that fails, and where that time goes.
2. The time of the typed start on every equation of U41 and on the units
   arm of the TP laws (draw 0), to see whether III.19.51 is alone or the
   largest of several.
3. What in III.19.51 makes the typed draws hard (its variables, their
   dimensions, the dimension of the target), against the equations that
   start fast.

D0 is recorded in `d0/` and reported to the author with its explanation.

**D0 done, 4 November 2026** (`d0/D0.md`). The fast path of the typed start
refuses products of more than 8 factors; III.19.51 needs 9 and falls to a
blind search with no bound in time, which is also what builds its law. The
author chose, the same day, both corrections D0 proposed, which replace the
correction (b) below:
- **(b2)** the fast path accepts products of up to 12 factors (each exponent
  at most 4, as before);
- **(b1)** the typed start looks at the deadline: once it is reached, an
  island stops drawing as soon as it has one tree, and is completed with
  copies, as after its failed draws.

Mechanics of the correction, before H1:
1. III.19.51 under units with `time_limit=30`, U41 seed 0: the fit ends
   within the limit, the model passes `check_dimensions`, and the law is
   exact.
2. U41, seed 0, with 20 generations and no time limit, so that the
   comparison does not depend on timing: every equation other than
   III.19.51 returns the model of the 1.1.0 wheel, run the same way; and the
   units arm of the TP diagnostic at draw 0, under the defaults, returns the
   models of 1.1.0.
3. Without `units=`, the thirteen reference configurations are unchanged,
   and the test suite passes.
4. New tests: a product of 9 to 12 factors comes from the fast path; a
   target whose product needs more than 12 factors, with a deadline already
   passed, ends its start with no empty island.

**Mechanics held on 4 November 2026** (commit 9a794a3, `fix/`): III.19.51
exact in 1.2 s (430 s on the wheel), its model passing `check_dimensions`;
40 of 41 U41 equations and 40 of 40 TP units fits the same as the wheel, to
the bit; the thirteen reference configurations identical; 156 tests pass,
and the two new ones fail on the 1.1.0 wheel (`fix/compare_mechanics.txt`,
`fix/compare_1.1.0_vs_fix.txt`, `fix/tests_fix.txt`,
`fix/new_tests_on_wheel.txt`). The campaigns below run with this
correction.

The original text of (b) follows, for the record.
If it finds a fault beyond the missing look at the deadline, that fault goes
to the author before any correction. Otherwise the correction (b) is made as
written above, with these mechanics:
1. III.19.51 under units with `time_limit=30`: the fit ends within the
   limit, up to its usual end (polishing, selection, formula), and its model
   passes `check_dimensions`.
2. U41, seed 0, at 30 s: every equation other than III.19.51 returns the
   model of 1.1.0.
3. Without `units=`, the thirteen reference configurations are unchanged.

## The release of 1.2

As for 1.1 (`../results_1.1/PLAN_RELEASE_1.1.md`): M1 to M5, then gate 8.
What 1.2 adds:
- **M1** expects the reference configurations identical to 1.1.0, all of
  them setting their budget.
- **M2**, campaign R paired with 1.1.0 on the whole suite of phase 1 and
  U41 at 30 s: H1 and C1 do not act there, so the two versions return the
  same models at equal work, up to the timing of the time budgets, with the
  thresholds of the release of 1.1. X1 is checked on these fits. The frozen
  test set is published as measured and decides nothing.
- **M3** measures again every public figure, and the TP notebook
  (`examples/tp_six_lois.ipynb`), whose times and formulas change.
- **Documents:** the READMEs (time of a fit, the exponential, the message
  under units, the two new parameters), the pages of the limits (the units
  mode and constants with units), the CHANGELOG, the TP notebook and its
  text, `DIAGNOSTIC_TP.md` left as written with a note.

## Cost

Estimated from the times of 1.1.0 and of the prototypes, on 4 cores, run in
slices of under two hours whose records resume:
- campaign H1: TP for A and H1 (800 fits), about 3 hours; D for A and H1
  (2,720 fits, never run under the defaults; III.19.51 under units takes
  at least 10 minutes a fit), about 10 hours;
- confirmation: TP draws 5 to 9 and the F41 kinds with seeds 5 to 9, for A
  and H1, about 7 hours;
- campaign C1: about 4 hours;
- the release, M1 to M3, as for 1.1, about 15 hours.

About 40 hours of machine time in all, over several days, and about an hour
for D0. The engine work itself (D0 and the correction (b), H1, X1, C1, their
tests) comes before the campaigns.
