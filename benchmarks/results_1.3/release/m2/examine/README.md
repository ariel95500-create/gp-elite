# I.18.12 with 10 % noise under units: the result

Run on 9 November 2026, from 14:47 to 14:57 (UTC), as `PLAN.md` says, after
M2. The processor was the same as M2's: `machine_20261109T1447.txt` is
identical to `../machine_20261109T0435.txt`. The log
is `run_e1.log`, the records are `e1_1.2.0.jsonl` and `e1_1.3.0.jsonl`, and
the reading is `e1.txt`, from `examine.py`. There are 40 jobs per version,
the same jobs in both, and no crash.

## The answer: the draw of the seeds of M2

On twenty seeds never run in M2 (5 to 24), each version retrieves the
structure of I.18.12 with 10 % noise under units in 12 fits of 20.
- **1.2.0** returns, in 7 of the 8 other fits, a parabola in θ times r·F,
  such as `(1.24557 * v2 - 0.397444 * v2²) * v1 * v0`. That is the formula
  1.3.0 returned at seeds 0 to 3 of M2. At seed 11 it returns
  `-1.06594 * v0 * v2 * v1 * tanh(log(v2) - 1.14229)`.
- **1.3.0** returns the parabola in its 8 other fits.
- **No formula of either version has the arcsine.**

Without units, the control F41N10 retrieves the structure in 20 fits of 20
with both versions. Every fit reached its budget of 30 s. The median
generations are 96.5 with 1.2.0 and 97 with 1.3.0 under units, and 110 and
109.5 without (`e1.txt` prints the upper of the two middle values).

The fall from 5 fits to 1 at seeds 0 to 4 in M2 is the draw of those five
seeds. It is not a loss of 1.3.0: by the reading written in `PLAN.md`, the
difference is 0, against a threshold of 4.

## What it shows of both versions

On [0, 3.14], the range of θ, sin θ and the parabola
1.24557·θ − 0.397444·θ² differ by at most 0.045. Their root-mean-square
difference is 0.026, about 4 % of that of sin θ. The noise added is 10 % of
the standard deviation of the targets. Under units, both versions return the
parabola in about four fits of ten (7 and 8 of 20). This belongs to point 3 of the pages of
the limits, the noise, and is not new in 1.3.0.
