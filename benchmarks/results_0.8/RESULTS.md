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
