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
