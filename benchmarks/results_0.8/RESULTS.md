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
