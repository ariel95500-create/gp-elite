# Decision bench for 0.8 — plan written before any measurement

Written on 29 September 2026, before the first run of the campaign. The
criteria below decide; they are not adjusted after the results are seen.

## What is compared

| Arm | Engine |
|---|---|
| A | gp-elite 0.7.0 (commit `e847605`) |
| B | 0.8 development branch at commit `c7b5934` |

Between A and B, every change but one returns the same model at equal seed
(checked bit for bit on 13 reference configurations and by
`tests/test_speed_equivalence.py`): they only make the engine faster. The
exception is the fix of commit `aaa5f79`: the square of a negative constant
was evaluated negative during the search (0.8 % of the trees evaluated). At
equal work, any difference of quality between A and B comes from that fix;
at equal time, it also comes from the extra generations B runs.

## Problems

**F41.** The 41 equations of `benchmarks/feynman_bench.py` (the 15 of the
README and the 26 added to cover rational forms, roots, exponentials...).
As in that bench: 200 points per equation drawn with the data seed
`1000 + i`, 140 for training and 60 for the test, operator pool of the
equation. Out of domain: 200 more points where each variable is drawn from
its range extended by 30 % of its width above the maximum, kept when at
least one variable exceeds its training range and the law is finite there.

**R6.** The six real PMLB datasets of `benchmarks/pmlb_frozen.py`, frozen by
content hash. Five folds (`KFold(5, shuffle=True, random_state=0)`), inputs
and target standardised on the training part as SRBench's `evaluate_model`
does. Out of domain: one split per dataset, training on the 80 % of rows
closest to the centre (Euclidean norm of the standardised inputs), testing on
the 20 % farthest.

Every fit: `symbolic_regression` defaults otherwise (`speed="fast"`, one
restart, 20 % internal hold-out), `parallel=False`, one process per fit,
`PYTHONHASHSEED=0`, two fits at a time on the two cores of the machine.
Engine seeds 0 to 4 (Feynman and the out-of-domain real splits); seed 0 for
the real folds, the five folds providing the replication.

## Budgets

**T, equal time (the headline).** `time_limit=30` seconds per fit,
`generations=1000` so that the clock stops the search. F41 x 5 seeds, R6 x 5
folds, R6 out of domain x 5 seeds.

**G, equal work.** `generations=100`, the default of `speed="fast"`. The 15
equations of the README x 5 seeds, and R6 x 5 folds.

## Hypotheses and decision criteria

**H1, speed (budget G).** B is faster at equal work: the median of the
per-fit time ratios B/A is at most 0.6 on F15 and on R6. Refuted above 0.8.

**H2, the negative-square fix does not cost quality (budget G).** On F15,
exact recoveries of B are at least those of A minus 4 (out of 75 runs). On R6,
the median of the paired per-fold differences of test R² (B - A) is at least
-0.01 and B has at most one more collapse (test R² < 0) than A. A violation
does not remove the fix (it corrects a wrong evaluation) but is investigated
and reported.

**H3, more is found in the same time (budget T).** On F41, B recovers at least
8 more exact laws than A over the 205 runs, and is ahead on more equations
than it is behind. On R6 (folds and out of domain together), the median of
the paired differences of test R² is at least 0 and B has no more collapses
than A. Refuted if B recovers no more exact laws than A.

Exact law: 1 - R² < 1e-9 on the held-out test points, judged on the model
the fit returns. Also reported, without deciding anything: close
(1 - R² < 1e-3), out-of-domain error of the models that are not exact,
model size, generations completed in the time budget, and the count of
out-of-domain collapses.

---

# Campaign 2 — two quality changes, written before its first run

Written on 29 September 2026, while campaign 1 was running and before any
run of campaign 2. None of its results had been seen.

| Arm | Engine |
|---|---|
| B1 | 0.8 branch at commit `cf7a7d3`: campaign 1's B, plus the input checks and the tree hashes made independent of PYTHONHASHSEED |
| C1 | commit `580aabf`: B1 plus two changes that alter the search |

The two changes of C1:

- **Relative early stop.** The search stopped as soon as the hold-out MSE
  fell under 1e-6, an absolute value that depends on the unit of y. On a
  target of variance 0.02 (Feynman I.6.20a), a model at 1 - R² = 6e-5
  reached it at the sixth generation, and the final selection returned an
  approximation at 1 - R² = 2e-3 while the exact law was within reach. C1
  stops early only on a law exact to numerical precision (1 - R² <= 1e-12
  on the hold-out).
- **Levenberg-Marquardt in variable projection.** The constants were fitted
  so that the tree alone matches y, while the search judges the tree after
  the implicit linear scaling a + b·f. On y = 3 sin(2x) + 1, the tree
  sin(c·x) converged to c = 1.878 (MSE 0.16); fitting a and b by least
  squares inside the residual gives c = 2 exactly.

Same problems, budget T (30 s per fit), seeds and protocol as campaign 1.

**H4, C1 finds more exact laws in the same time without losing elsewhere.**
Decision criteria: on F41, exact recoveries of C1 exceed those of B1 by at
least 6 over the 205 runs, and C1 is ahead on more equations than it is
behind. On R6 (folds and out of domain together), the median of the paired
differences of test R² (C1 - B1) is at least -0.005, and C1 has no more
collapses (test R² < 0) than B1. Refuted if C1 recovers no more exact laws
than B1, or if the median real-data difference is below -0.01; in either
case both changes are left out of the release unless a separate campaign
supports one of them on its own. The early stop can only make fits longer:
the median time of the Feynman fits is reported, and the out-of-domain
error of the models that are not exact is reported for both arms.

---

# Campaign 3 — grouped normalisation, written before its first run

Written on 29 September 2026, before any run of campaign 3 and before the
results of campaign 2. Only one fit of the change had been run, the one
quoted below (it motivated the change, so it is not evidence).

| Arm | Engine |
|---|---|
| C1 | commit `580aabf` (campaign 2's C1) |
| C8 | commit `a16deab`: C1 plus the change below |

**The change.** `normalize="auto"` divided every column by its own max|x|.
That keeps products as products but not sums and differences of variables of
the same kind: on Feynman I.8.14, sqrt((x2-x1)² + (y2-y1)²) with column
maxima 4.97 and 4.99 becomes another function of the normalised variables,
which the search only approached to 1e-4 (0 exact laws out of 5 seeds in
campaign 1, arm B). C8 gives one common factor, the largest max|x|, to the
columns whose max|x| lie within a factor 10 of each other; columns of very
different magnitudes keep their own. One fit of C8 on I.8.14 (seed 0) returned
sqrt((v2 - v3)² + (v1 - v0)²) in 1.2 s.

Same problems, budget T, protocol as campaigns 1 and 2.

**H5, grouped normalisation finds more exact laws without losing on real
data.** On F41, exact recoveries of C8 exceed those of C1 by at least 6 of the
205 runs, and C8 is ahead on more equations than it is behind. On R6 (folds
and out of domain together), the median of the paired differences of test R²
(C8 - C1) is at least -0.005, and C8 has no more collapses than C1. Refuted if
C8 recovers no more exact laws than C1, or if the median real-data difference
is below -0.01. Reported without deciding: the equations gained and lost,
model sizes, the out-of-domain error of the models that are not exact.

To halve the cost, C1's fits are those of campaign 2; C8's fits run two at a
time, as every fit of these campaigns does (two processes on the two cores).

---

# Amendment to budget G, written before any run of it

Written on 29 September 2026 at 08:15, before budget G was run. Campaign 1
compared A and B at equal time; since then, campaign 2 changed the engine
(C1 kept), so an equal-work comparison of A with B (`c7b5934`) would describe
an engine that will not be released. Budget G will compare A (0.7.0) with F,
the release candidate at the end of the quality campaigns, on the same
problems (F15 x 5 seeds, R6 x 5 folds, 100 generations, no time limit).

**H1', speed at equal work.** The median of the per-fit time ratios F/A is at
most 0.6 on F15 and on R6. Refuted above 0.8.

**H2', quality at equal work.** On F15, exact recoveries of F are at least
those of A. On R6, the median of the paired differences of test R² (F - A) is
at least -0.005 and F has no more collapses than A.

---

# Campaign 3b — confirmation on new seeds, written before it runs

Written on 29 September 2026 at 09:05, after the Feynman part of campaign 3
(C8 75 exact laws, C1 69: +6, exactly the threshold of H5; 6 equations ahead,
4 behind; runs exact for one arm only: 14 for C8, 8 for C1, two-sided sign
test p = 0.29) and before its real-data part and before any run of 3b.
Campaigns 1 and 2 showed that two arms that should be equivalent differ by
about six exact laws on 205 runs: a +6 is within that scatter, so H5 is not
decided on seeds 0 to 4 alone (protocol rule 7: an ambiguous cell is run
again with more seeds before anything is said about it).

Arms C1 (`580aabf`) and C8 (`a16deab`), F41 with engine seeds 5 to 9 (205
runs per arm, side by side), budget T.

**Decision.** The grouped normalisation becomes the default only if (i) on
seeds 5 to 9 alone C8 recovers more exact laws than C1, (ii) over seeds 0 to 9
(410 paired runs) the two-sided sign test on the runs exact for one arm only
gives p < 0.10 in favour of C8, and (iii) the real-data criteria of H5 hold in
campaign 3. Otherwise `normalize="auto"` keeps one factor per column.

---

# Decision on campaign 3, and campaign 4 — written before campaign 4 runs

Written on 29 September 2026 at 09:35. Campaign 3 has ended: on real data,
C8 has 6 collapses against 4 for C1, so H5 fails on its own criteria (iii of
3b) whatever the Feynman confirmation would have given. The grouped
normalisation does not become the default, and campaign 3b, whose outcome
could no longer change that decision, was stopped after 47 fits (its records
are kept, and used for nothing).

**Campaign 4.** Arms C1 (`580aabf`) and C4 (`ff32450`): C1 plus two changes.

- **Formula-faithful tie-break.** Among the candidates the final selection
  cannot tell apart, the smallest was returned even when a numerical safety
  net of the engine acted on the data, so that the delivered formula departs
  from `predict()` (`formula_exact` False: 22 of C1's 205 Feynman fits and 6
  of its 60 real-data fits in campaign 2). C4 prefers the smallest candidate
  whose formula reproduces the model.
- **Companion lookup.** The co-occurrence graph is indexed by canonical hash
  but was queried with the structural hash: a fragment containing a constant
  was never found (3,281 companions found out of 6,650 lookups on a 25
  generation run of I.12.2, 6,798 out of 6,798 after the fix).

C1's fits are those of campaign 2; C4 runs its 265 fits two at a time.

**H6.** Both changes are kept if: C4 returns at most half as many inexact
formulas as C1 over the 265 fits (at most 14 against 28); its exact laws on
F41 are at least those of C1 minus 6 (the scatter measured between
equivalent arms); on R6 the median paired difference of test R² is at least
-0.005 and C4 has no more collapses than C1 (4). If only the inexact-formula
criterion fails, the tie-break is dropped and the companion fix is kept if
the other criteria hold; if the exact-law or real-data criteria fail, both
are dropped.

---

# Decision on campaign 4, and campaign 5 — written before campaign 5 runs

Written on 29 September 2026 at 09:24. Campaign 4 has ended and H6 holds
(`RESULTS.md`): C4 (`ff32450`) is merged into the 0.8 branch. Its analysis
found a fault introduced by campaign 2's variable projection (the scale and
offset carried by a finalist or by the final champion are left stale by
Levenberg-Marquardt). No Feynman or PMLB fit of the change below has been
run; it was checked on constructed cases (tests) and on four fits of 25
points, quoted below because they show the fault, not as evidence of a gain.

| Arm | Engine |
|---|---|
| C4 | commit `ff32450` (campaign 4) |
| C5a | commit `788d09d`: C4 plus the correction alone |
| C5 | commit `b2f78c0`: C4 plus the correction and the polish |

**The correction** (`_refit_scaling`). After Levenberg-Marquardt, the scale
and offset materialised in the final champion and in each polished finalist
are refitted into the tree's own constants. On y = 3 sin(2x) + 1 with 25
points (no hold-out), seeds 0 to 3: training R² -48.8, 1.000, 1.000, -234.8
before, 0.961, 1.000, 1.000, 0.892 after. It is kept whatever the outcome of
this campaign (it corrects an evaluation); its effect is reported (C5a
against C4) and investigated if it costs more than 6 exact laws, more than
0.01 of median paired R², or more than one collapse.

**The polish** (what this campaign decides; `FINAL_POLISH`). For each of the
eight finalists of the final selection, two more kinds of candidates: the
same tree with its constants fitted by Levenberg-Marquardt for up to 100
iterations instead of 20, and variants in which each term of a sum or a
difference carries its own coefficient (A ± B becomes a·A ± b·B; one variant
for the innermost sums only, one for all sums), fitted the same way. They go
through the same final selection as every other candidate. Motivation, from
campaign 2's C1: I.8.14, sqrt((x2-x1)² + (y2-y1)²), came back 5 times out of
5 as sqrt((x2' - x3')² + (x1' - x0')²) on the normalised columns (1 - R² =
1.8e-4), where each column's own factor 1/max|x| calls for a coefficient on
each term of the differences; II.2.42 likewise; II.15.4 as
-μB·sin(-10.985 - 1.00432 θ), the right form with unfinished constants.
Expected: gains on I.8.14, II.2.42 and II.15.4, no loss elsewhere.

**Problems.** Budget T, as in campaigns 1 to 4. F41 (seeds 0 to 4) and R6
(5 folds and the out-of-domain split, seeds 0 to 4) for C5a and C5, side by
side (530 fits); C4's are those of campaign 4. R7raw, new (`--raw-real` of
`decision_bench.py`): the six PMLB datasets and nikuradse_1 in their own
units, not standardised, 5 folds and the out-of-domain split (seeds 0 to 4),
C5a and C5 side by side, then C4 alone two fits at a time (210 fits).
Reported without deciding: `benchmarks/small_data_check.py` (five laws, 25
points, four seeds, no hold-out) for the three arms.

**H7, the polish finds more exact laws without losing on real data (C5
against C5a).** On F41, C5 recovers at least 6 more exact laws than C5a (the
scatter measured between equivalent arms) and is ahead on more equations
than it is behind. On real data (R6 and R7raw together, 130 paired fits), the
median of the paired differences of test R² is at least -0.005 and C5 has no
more collapses (test R² < 0) than C5a. Refuted if C5 recovers no more exact
laws than C5a, or if the median real-data difference is below -0.01; the
polish is then left out (`FINAL_POLISH` off) and only the correction ships.
Reported without deciding: runtime of the final selection (fit time beyond
the budget), sizes, equations gained and lost, out-of-domain errors.

**Amendment, 29 September 2026 at 09:33, before the campaign was run
again.** Campaign 5 was first started at 09:24 with arms `f250f5d` and
`106f616`, in which the polish acted on the eight best candidates on the
hold-out only. After seven equations, I.8.14 was still returned inexact by
C5; a single diagnostic run showed why: its right structure (14 nodes,
1 - R² = 1.8e-4) was not among those eight (all 48 to 68 nodes), so it was
never weighted, and the parsimony rule then delivered it unpolished. The
campaign was stopped (72 records, kept apart and not used), and the polish now
also takes the eight smallest candidates of the tolerance band in which the
final selection chooses (`_finalists`); with the correction alone (C5a) the
finalists are unchanged. Arms, problems and criteria are otherwise those
written above, and the campaign is run again from the start.

---

# Decision on campaign 5, and campaign 5b — written before campaign 5b runs

Written on 29 September 2026 at 12:15, after the runs of C5a and C5 (the
R7raw runs of C4, which only serve the report on the correction, were still
going) and before any run of campaign 5b.

**H7 fails** on its collapse criterion. On F41, C5 recovers 75 exact laws
against 64 for C5a (+11; runs exact for one arm only: 11 against 0), ahead on
4 equations and behind on none; on real data (R6 and R7raw, 130 paired fits)
the median paired difference is +0.000, but C5 has 12 collapses against 11.
The polish is not kept as it was measured. The extra collapse, and more real
fits worse than better (17 against 13), come from polished variants that win
the final selection on the hold-out and extrapolate worse (547_no2, out of
domain, seed 1: R² 0.362 with C5a, -0.359 with C5).

**Campaign 5b** tests a restriction of the polish that removes that
mechanism: a polished variant (converged constants, weighted sums) enters the
final selection only if it reproduces the hold-out to numerical precision,
under the floor below which the selection keeps only exact laws (1e-12 times
the variance of the hold-out). The polish can then turn a right structure into
an exact law, and never replaces an approximate model by another one. On
measured data no variant reaches that floor, and the fit is the one of C5a.

| Arm | Engine |
|---|---|
| C5a | commit `788d09d` (campaign 5: the correction alone) |
| C5x | commit `0b23fed`: C5 with the restriction |

**Problems.** Budget T. F41, R6 (folds and out of domain) and R7raw: C5x's
335 fits, two at a time; C5a's are those of campaign 5. Reported without
deciding: the number of polished variants admitted on real data (expected:
none; recorded as `polish_admitted`), and `small_data_check.py`.

**H7b.** The restricted polish is kept if, on F41, C5x recovers at least 6
more exact laws than C5a and is ahead on more equations than it is behind,
and, on real data (R6 and R7raw together, 130 paired fits), the median paired
difference of test R² is at least -0.005 and C5x has no more collapses than
C5a (11). Otherwise only the correction ships.
