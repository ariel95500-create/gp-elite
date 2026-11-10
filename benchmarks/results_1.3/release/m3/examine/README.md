# The TP notebook of the pool `full`: the result

Run on 9 November 2026 as `PLAN.md` says, after M3, with nothing else on
the machine. Neither `e2.log` nor the records carry times. The run was
started by the command that committed and pushed the plan and the scripts
(7fe0665, 16:21:31 UTC), after the push. The two record files were last
written at 16:25:52 (their file times). The records are
`e2_1.2.0.jsonl` and `e2_1.3.0.jsonl`, and the reading is `e2.txt`, from
`e2_read.py`. There are 30 fits per version, the same fits in both, and no
crash.

## The answer: no difference shown, the same direction at each budget

By the reading written in `PLAN.md`, the sign test shows no difference at any
budget. At each budget, though, 1.3.0 has the higher MSE in most seeds, and
its median MSE is the higher:

| generations | 1.3.0 higher / lower, of 10 | p | median MSE, 1.2.0 | median MSE, 1.3.0 |
|---|---|---|---|---|
| 10 | 6 / 4 | 0.75 | 2.96e-02 | 6.31e-02 |
| 30 | 8 / 2 | 0.11 | 1.19e-03 | 4.93e-03 |
| 60 | 7 / 3 | 0.34 | 1.66e-04 | 1.10e-03 |

Ten seeds cannot show a difference of this size. On this problem, the pool
`full` of 1.3.0 is not shown to fit worse, but it does not fit better either.
The median sizes and times are those of 1.2.0, within one node and 0.2 s.

## The printed formula

| generations | formula departs, 1.2.0 | formula departs, 1.3.0 | formulas with the arcsine, 1.3.0 |
|---|---|---|---|
| 10 | 1 | 1 | 3 |
| 30 | 1 | 4 | 4 |
| 60 | 1 | 2 | 3 |

6 of the 7 formulas of 1.3.0 that depart have an arcsine. Two of them show
plainly an argument that leaves [−1, 1] on these data, x in [−3, 3]:
- `arcsin(1.11312 * sin(...))`, whose argument reaches 1.11;
- `arcsin(4.05344 * log(|0.33724 * x|^(0.33724 * x)))`, whose argument
  reaches about ±1.49.

In the model, the clip makes such an arcsine flat at ±π/2 where its argument
leaves [−1, 1], and the search can use it that way. The printed formula has
no clip, so where the clip acts it departs from `predict()`, and the engine
says so. Whether the clip is the cause in each of the six is not recorded.
This is the limit that point 6 of the pages of the limits and the CHANGELOG
describe.

## What the notebook shows, seed 0

At seed 0, the seed of the notebook:
- **Part 1, 40 generations:** 1.3.0 returns a formula with the arcsine,
  which departs from `predict()` on 15 of 200 rows, with the warning
  (`../notebook_snippet_tp.txt`).
- **Part 2:** the MSE goes from 5.654e-02 to 1.628e-02 and then 1.281e-03,
  with sizes 38, 46 and 43. The text of question 2 ("from 30 to 60, nothing
  changes") is brought to that.
