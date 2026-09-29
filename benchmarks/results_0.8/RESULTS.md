# Decision bench for 0.8 — results

Each campaign is judged against the criteria written before it ran, in
`PLAN.md`. Raw records: one JSON line per fit. Summaries:
`python benchmarks/decision_bench.py summary <records> --budget T`.

## Campaign 1 — 0.7.0 (A) against the faster engine (B), 30 s per fit

Records: `campaign1_T.jsonl` (530 fits, 29 September 2026, 03:36 to 05:42,
two fits at a time on a 2-core Linux container). Summary:
`campaign1_T_summary.txt`.

B completes twice as many generations as A in the 30 seconds (median 84
against 42 on Feynman, 100 against 55 on real data).

| | A (0.7.0) | B |
|---|---|---|
| Feynman, exact laws (205 runs) | 64 | 64 |
| ahead / behind on equations | | 5 / 5 |
| Real data, 5 folds: test R² median (mean, worst) | 0.808 (0.782, 0.406) | 0.812 (0.727, -0.527) |
| paired folds, B better / worse | | 7 / 16 |
| Real data, out of domain: test R² median | 0.640 | 0.409 |
| collapses (test R² < 0), folds + out of domain | 7 | 9 |

**H3 is refuted.** B recovers no more exact laws than A (64 each), and on real
data it has two more collapses. Twice the generations in the same time does not
find more laws: the search stops improving well before the end of the budget,
and on real data the extra generations tend to produce larger models that
generalise no better (561_cpu: median size 37 against 20, fold R² 0.926 against
0.978). The speed-up stands (same models at equal seed and equal work, in less
time), but it is not, by itself, better results in the same time. What limits
the results is the search and the selection, which is what campaigns 2 and 3
test.

Out of domain, both engines collapse on the same kind of models: formulas
built on `exp(c*x)` or on powers with a variable exponent, fine inside the
data and exploding beyond it (210_cloud: R² -42.9 for A, -9.4 for B;
561_cpu: -40.9 for A, -8.8 for B).

## Campaign 2 — relative early stop and variable projection (C1) against B1

Records: `campaign2_T.jsonl` (530 fits, 29 September 2026, 05:47 to 08:03).
Summary: `campaign2_T_summary.txt`.

| | B1 | C1 |
|---|---|---|
| Feynman, exact laws (205 runs) | 58 | 69 |
| runs exact for one arm only | 4 | 15 (two-sided sign test p = 0.019) |
| ahead / behind on equations | | 7 / 2 |
| Real data, 5 folds: test R² median (mean) | 0.807 (0.759) | 0.810 (0.750) |
| Real data, out of domain: test R² median | 0.548 | 0.630 |
| paired difference, folds + out of domain: median | | +0.000 |
| collapses (test R² < 0), folds + out of domain | 4 | 4 |

**H4 is confirmed** on each of its criteria: 11 more exact laws (6 required),
ahead on 7 equations and behind on 2 (I.6.20a goes from 0 to 5 of 5, the case
that motivated the relative early stop), a median real-data difference of
+0.000 (at least -0.005 required) and no additional collapse. Both changes
are kept.

Two remarks on the size of the effects. B1 differs from campaign 1's B only by
changes that permute the random draws (tree hashes) and by input checks, and
it recovers 58 laws where B recovered 64: about six laws is the scatter of
this count between two arms that should be equivalent. C1's 11 is twice that,
and the paired test above says the same. Out of domain, one B1 model reached
R² = -1.7e6 (`4.80648^exp(0.447 X2 - 1.90)`, a double exponential); C1's worst
is -64.

**A diagnostic that was measured and dropped.** Every fit of this campaign
records how much wider the range of its predictions becomes over a box 25 %
larger than the training data (`growth_box25`). It was meant as a warning
for users about to extrapolate. It does not predict failure: on the real
out-of-domain splits, flagging models whose range grows more than tenfold
catches 3 of the 8 collapses and raises 5 false alarms, and on Feynman exact
laws themselves grow that much (median 4, 90th percentile 362, as q^4 does).
No such warning is shipped.

## Campaign 3 — one scale factor for comparable columns (C8) against C1

Records: `campaign3_T.jsonl` (C8's 265 fits; C1's are those of campaign 2).
Summary: `campaign3_T_summary.txt`.

| | C1 | C8 |
|---|---|---|
| Feynman, exact laws (205 runs) | 69 | 75 |
| runs exact for one arm only | 8 | 14 (sign test p = 0.29) |
| ahead / behind on equations | | 6 / 4 |
| Real data, 5 folds: test R² median (mean, worst) | 0.810 (0.750, 0.016) | 0.813 (0.786, 0.262) |
| Real data, out of domain: test R² median | 0.630 | 0.695 |
| collapses (test R² < 0), folds + out of domain | 4 | 6 |

**H5 fails** on its real-data criterion: C8 has two more collapses than C1
(criterion: none more), although its median test R² is higher both in the
folds and out of domain. On Feynman its gain (+6) sits exactly at the
threshold and within the scatter between equivalent arms. The gains are where
the change was meant to act, laws that add or subtract variables of the same
kind (I.8.14: 0 to 5 of 5; II.2.42: 1 to 3; II.15.4: 0 to 2), and the losses
are not explained (I.27.6: 3 to 0). The grouped factor is therefore **not the
default**; it is offered as an option, `normalize="grouped"`, with these
numbers. The confirmation campaign on seeds 5 to 9 (3b) was stopped after 47
fits once the decision no longer depended on it (`campaign3b_T_stopped.jsonl`,
not used).

## Campaign 4 — formula-faithful tie-break and companion lookup (C4) against C1

Records: `campaign4_T.jsonl` (C4's 265 fits, 29 September 2026, 08:17 to
09:15; C1's are those of campaign 2). Eight Feynman fits (I.11.19 seeds 1 to
4, I.15.10 seeds 0 to 3) ran while a micro-benchmark was also using the
machine; they were run again after the campaign, and their first records are
kept apart (`campaign4_T_perturbed_replaced.jsonl`, not used; no exact
outcome differs between the two). Summary: `campaign4_T_summary.txt`.

| | C1 | C4 |
|---|---|---|
| inexact formulas (`formula_exact` False), 265 fits | 28 | 11 |
| of which on real data (60 fits) | 6 | 0 |
| Feynman, exact laws (205 runs) | 69 | 63 |
| runs exact for one arm only | 11 | 5 (sign test p = 0.21) |
| ahead / behind on equations | | 3 / 6 |
| Real data, 5 folds: test R² median (mean, worst) | 0.810 (0.750, 0.016) | 0.810 (0.771, 0.372) |
| Real data, out of domain: test R² median (worst) | 0.630 (-64.1) | 0.630 (-224.1) |
| paired difference, folds + out of domain: median | | +0.000 |
| collapses (test R² < 0), folds + out of domain | 4 | 4 |

**H6 holds** on each of its criteria: 11 inexact formulas against 28 (at
most 14 required), 63 exact laws against 69 (at least 63 required: the loss
sits exactly at the tolerance set from the scatter between equivalent arms),
a median real-data difference of +0.000 (at least -0.005 required) and as many
collapses. Both changes are kept.

The laws lost deserve a remark, because one of them exposed a defect. On
I.6.20a, seeds 3 and 4, the search found a numerically exact form (hold-out
MSE 2.6e-12 times the variance) just above the floor under which the final
selection keeps only exact candidates (1e-12); the tolerance of 0.3 % of R²
then admitted a shorter approximation, returned at 1 - R² = 2.3e-3. The
polish of the finalists, which could have brought that form under the floor,
produced candidates the selection discarded as divergent: Levenberg-Marquardt
in variable projection (kept after campaign 2) fits a' + b'·tree, and on a
finalist that already carries its scale and offset, a + b·f, the fitted tree
kept the old a and b, which drift to the bounds of the constants (±15). The
same fault reaches the user directly when a fit has no hold-out (fewer than
30 points, or `validation_split=0`): the champion polished at the end is then
delivered as it is. On y = 3 sin(2x) + 1 with 25 points, two seeds out of
four returned a model with R² = -48.8 and -234.8 on its own training points.
The correction is measured in campaign 5 and kept whatever its outcome, as a
correction of an evaluation.

## Campaign 5 — correction of the scale after Levenberg-Marquardt (C5a), and polish of the finalists (C5)

Records: `campaign5_T.jsonl` (C5a and C5 side by side on F41, R6 and R7raw,
740 fits with the R7raw runs of C4, 29 September 2026, 09:36 to 12:24; C4's
F41 and R6 fits are those of campaign 4). The first start of the campaign,
stopped after 72 fits and amended before the restart (`PLAN.md`), is kept in
`campaign5_T_stopped.jsonl` and not used. Small data: `small_data_C5.jsonl`
(`benchmarks/small_data_check.py`).

**The correction (C5a against C4)** is kept, as planned. It costs nothing
measurable: 64 exact laws against 63 on F41 (ahead on one equation, behind on
none), and on real data (R6 and R7raw, 130 paired fits) a median paired
difference of +0.000 and 11 collapses on each side. On the small-data check
(five laws, 25 points, four seeds, no hold-out), C4 delivered two models whose
scale and offset were stale, with test R² -1403 and -9.3; C5a, none (worst
test R² 0.998).

**The polish (C5 against C5a):**

| | C5a | C5 |
|---|---|---|
| Feynman, exact laws (205 runs) | 64 | 75 |
| runs exact for one arm only | 0 | 11 (sign test p = 0.001) |
| ahead / behind on equations | | 4 / 0 |
| R6 (60 fits): paired difference, median (better / worse) | | +0.000 (9 / 7) |
| R6 collapses | 5 | 6 |
| R7raw (70 fits): paired difference, median (better / worse) | | +0.000 (4 / 10) |
| R7raw collapses | 6 | 6 |
| inexact formulas, 335 fits | 21 | 21 |
| time beyond the 30 s budget, median | 0.4 s | 1.1 s |

The gains are where the polish was meant to act: I.8.14 goes from 0 to 5 exact
laws out of 5, II.2.42 from 0 to 4, I.32.5 from 0 to 1 and I.6.20a from 3 to
4. **H7 fails** on its collapse criterion nonetheless (12 against 11 on real
data), and C5 is worse than C5a on more real fits than it is better (17
against 13): variants of the polish win the final selection on the hold-out
and extrapolate worse (547_no2, out of domain, seed 1: R² 0.362 with C5a,
-0.359 with C5). The polish as measured is not kept; campaign 5b tests a
restriction of it that removes this mechanism.

## Corrections made outside the campaigns

These change what a fit returns only on data that none of the campaign
problems contain, where the engine failed; they are measured on that data.

**The scale of the data.** On 0.7.0 and on the 0.8 branch until this
correction, y = s·x0²/x1 came back as a constant or a wrong straight line,
with a negative R² on the training points and no warning, for target scales
s = 1e-9, 1e-19, 1e-30, 1e20 and 1e30; a column whose values were of the order
of 1e-19 (a charge in coulombs) was left unscaled by the normalisation, and
predictions above 1e12 were clipped by the engine's safety bounds. The search
now works on y divided by a power of ten when the standard deviation of y lies
outside [1e-3, 1e3] (every campaign target lies inside, so nothing changed
there), the model is returned in the units of y, and only a null column keeps
the factor 1 in the division by max|x|. `benchmarks/scale_check.py`, eleven
input and target scales from 1e-34 to 1e30: before, the law was recovered at
2 scales out of 11 (training R² from -1.99 to 1.000); after, at 10 out of 11,
the eleventh returning an approximation at R² = 0.99991, and every formula
reproduces predict(). Output: `scale_check.txt`.

**The rounding noise of constants in the printed formula.** An exact law was
printed 8.88178e-16 + v1 * v2 / v3; a constant term that is at most 1e-12 of
the sum it belongs to is no longer printed. The model and predict() do not
change, and the printed formula is still checked against predict().

**The note about PYTHONHASHSEED**, printed once per process even with
`verbose=False` and asking to launch Python with PYTHONHASHSEED=0, is gone:
`seed=` alone reproduces a fit since the tree hashes stopped depending on
Python's string hashing (tested with PYTHONHASHSEED 0, 1, 12345 and unset).

## Campaign 5b — the polish, restricted to exact laws (C5x) against C5a

Records: `campaign5b_T.jsonl` (C5x's 335 fits, 29 September 2026, 12:25 to
13:48; C5a's are those of campaign 5). While it ran, measurements of
another kind were made on the same machine for about ten minutes; the 37 fits
whose 30 seconds overlapped them were run again once the campaign had ended,
and their first records are kept apart (`campaign5b_T_perturbed_replaced.jsonl`,
not used). Summary: `campaign5b_T_summary.txt`.

| | C5a | C5x |
|---|---|---|
| Feynman, exact laws (205 runs) | 64 | 75 |
| runs exact for one arm only | 0 | 11 (sign test p = 0.001) |
| ahead / behind on equations | | 4 / 0 |
| real data, R6 and R7raw (130 fits): paired difference, median (better / worse) | | +0.000 (5 / 7) |
| collapses (test R² < 0), R6 and R7raw | 11 | 11 |
| polished variants admitted into the selection, real data | | 0 (in 130 fits) |
| polished variants admitted, Feynman | | 221 (in 42 fits) |
| inexact formulas, 335 fits | 21 | 21 |
| time beyond the 30 s budget, median | 0.4 s | 1.1 s |

**H7b holds** on each of its criteria: 11 more exact laws (I.8.14 from 0 to 5
of 5, II.2.42 from 0 to 4, I.32.5 from 0 to 1, I.6.20a from 3 to 4), none
lost, a median real-data difference of +0.000 and as many collapses. On real
data no polished variant reached the exact floor, so the delivered models are
those C5a delivers; the few differences come from the search itself, whose
number of generations in 30 seconds varies with the load of the machine. The
restricted polish is kept. Its cost is the time of the final selection: about
0.7 s more per fit at these sizes (140 to 500 rows).
