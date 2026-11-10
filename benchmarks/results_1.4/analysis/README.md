# Where 1.3.0 is weak: what the records say

Written on 10 November 2026, the day 1.3.0 was published. The author asked
for a review of the weaknesses of the engine and for technical answers to
them. This page reads records that exist and the code of 1.3.0. It changes
nothing in the engine and decides nothing: the plan it leads to is
`../PLAN.md`.

- **Records read:**
  - the M2 of 1.3.0 (`../../results_1.3/release/m2/`), on the kinds of the
    decision bench only;
  - campaign H1 of 1.2 and its confirmation on the TP diagnostic
    (`../../results_1.2/h1/campaign/`).
- **The frozen test set is not read.**
- **Two traces** of one generation each, with 1.3.0 installed from PyPI
  (`/venv13p`), read what the seed finders return (`seed_traces.py`).

Each script prints the file of the same name, `.txt`.

## The answer: the first weakness is noise

| | fits of 205 |
|---|---|
| exact laws, without noise (F41) | 171 |
| structure retrieved with 1 % noise (F41N1) | 116 |
| structure retrieved with 10 % noise (F41N10) | 87 |

On the small tables of the TP diagnostic (10 and 20 points, 2 % and 5 %
noise, plain arm, 40 fits per experiment), the law comes back in:
- 38 and 39 fits for the free fall and the electric power;
- 29 to 34 for the pendulum, the spring, the ideal gas, the point source and
  the capacitor;
- 9 for Newton's cooling, 2 for the thin lens, and none for Snell's law.

Under units the six laws within reach come back in 239 fits of 240, and the
capacitor, the cooling and the lens in none of 120, with a useful model in
4 of them (`tp_by_experiment.txt`).

More time is not the answer: with ten times the budget, 1.2.0 retrieved 3
and 5 more structures of 205 (`../../results_1.2/budget_study/README.md`).

## Under noise, the seeds decide

The records of M2 keep the seeds each fit placed at its start
(`noise_by_equation.txt`). With 1 % noise, without units:
- a noise-tolerant seed was placed in 140 fits, and the structure came back
  in 108 of them;
- no seed was placed in 65 fits, and the structure came back in 8.

With 10 % noise: 65 of 95 with a seed, 22 of 110 without. Ten equations
that are exact in at least four fits of five without noise have their
structure in none of five fits at 1 % noise, and fourteen at 10 %.

The noise of the bench is drawn once per equation: the five seeds of an
equation fit the same noisy targets. So these counts move by five fits at a
time, and they hold 41 draws of the noise at each level, not 205.

## Three causes in the seed finders, each checked

The noise-tolerant stage (phase 5 of 1.0) runs the finders of the exact
seeds with their thresholds lifted. Those finders were written for exact
data, and three of their rules fail under noise.

1. **A threshold fixed for the noise of the bench.** A tolerant seed is
   placed when it leaves at most 1.5 % of the variance unexplained
   (`_TOLERANT_REL`). The threshold was set so that no seed is placed on the
   real data of the bench, whose best candidate leaves 2.6 %. On a pendulum
   table with 5 % noise, the true law itself leaves 2.4 % (10 points) and
   3.5 % (20 points) in the median, above the threshold in all 20 draws
   (`tp_true_law_share.txt`). The same holds for the spring in 18 draws of
   20, and for the lens in 14. On such a table no seed is placed, and the fit
   returns a line or a tanh (`seed_traces.txt`, `tp_by_experiment.txt`).
2. **A target that must keep one sign.** The finders of the power law, of
   the binomial forms and of the functions of a monomial work on log|y| and
   stop when the target changes sign. With 1 % noise, 7 equations of 41 lose
   the single sign of their target, by 1 to 15 rows of 140, and 14 equations
   with 10 % (`sign_rows.txt`). Among them are two plain monomials, I.32.5
   and III.19.51, and I.40.1, II.35.18 and II.11.27, none of which keeps its
   structure at 1 % noise.
3. **The first form that passes, not the best.** With its threshold lifted,
   the trigonometric finder returns the first argument of its library whose
   coarse fit passes. On III.15.12 with 1 % noise it returns a form in k
   alone, which is not placed. The form in k·d, the law, leaves 1.1e-4 and is
   never tried. With 10 % noise the first that passes is the law
   (`seed_traces.txt`). The structure comes back in 0 fits of 5 at 1 % noise
   and 5 of 5 at 10 %. The finder of the logarithm has the same loop (read
   in the code, not traced).

## On small tables, the choice

Below 30 rows the engine keeps no hold-out (`_split_holdout`). It then
tracks no candidate, polishes no finalist and applies no rule of parsimony:
it returns the best individual of the search on the training rows, and
`pareto` is None.
- **The lens:** on the table traced, the seed of the law is placed
  (`1/(1 − 0.168/p)`, 0.3 % unexplained), and the fit returns another
  formula. The law comes back in 2 fits of 40.
- **Terms that follow the noise:** the point source returns
  `-0.139271 + 0.808722 / d² + 0.107035 * sqrt(d)` on one table.
- **No family for a constant plus an exponential:** Newton's cooling has no
  seed, and comes back in 9 fits of 40.
- **An additive constant the law does not have:** in all 233 plain fits
  that return a law without one, for instance `-0.0290401 + 2.03646 * sqrt(L)`.
  Under units the scaling has no such constant, and the six laws print in
  their textbook form.

## Elsewhere, for later

- **Constants with units inside a function or a sum:** under units, the
  capacitor, the cooling and the lens return a poor formula with no warning.
- **Laws the search never builds:** I.37.4, I.50.26, III.9.52 and III.17.37
  are exact in no fit, with or without units, and III.10.19 in 2 of 10. They
  are sums of terms, or a function of a sum.
- **Constants left by the scaling of each column:** I.8.14 at 1 % noise
  returns the form of the law with unequal coefficients,
  `sqrt((0.20002 * v2 - 0.201187 * v3)² + …)`, and the test of structure does
  not count it.
- **Real data:** 7 of the 10 collapses out of the training range are on one
  dataset of 44 training rows, with models of up to 65 nodes
  (`real_collapses.txt`). With ten times the budget the collapses go from 10
  to 22.

## Beyond the engine

- **Every result on teaching comes from simulated tables.** The TP
  diagnostic draws Gaussian noise on exact inputs. Real tables of students
  are missing.
- **The noisy benches hold one draw of the noise per equation,** and the
  threshold of the tolerant seeds was set on them.
- **No measured comparison with PySR or Operon** on small noisy tables or
  under units.
- **SRBench** has not answered the question on its calendar.
