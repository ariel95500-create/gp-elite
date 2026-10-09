# Phase 2 — the models that collapse out of domain (examination)

Examined on 9 October 2026 with the plan written before it
(`PLAN_PHASE2.md`, "Plan of the examination", commit e079a9a). Nothing in the
engine changes here and nothing is decided: this describes, and a change
gets its own plan, trial and campaign. Decision bench only; the frozen test
set was not opened.

The 65 out-of-domain fits of R6 and R7raw (seeds 0 to 4) were run again with
gp-elite 0.8.0 from PyPI, as in phase 1 (30 s, three at a time, one process
per fit, `PYTHONHASHSEED=0`), from 22:16 to 22:28 UTC, no crash. Raw records,
Pareto fronts included: `collapses_0.8.0.jsonl`; tables:
`python benchmarks/collapse_exam.py report benchmarks/results_0.9/collapses_0.8.0.jsonl`.

## What the examination shows

- **54 of the 65 fits returned the same model as in the baseline**, and 9 of
  its 10 collapses came back identical. One collapse did not come back
  (`nikuradse_1` seed 3) and one appeared (`561_cpu` standardised, seed 3:
  R² 0.903 in the baseline, −2.57 now): 11 collapses in either run.
- **Two kinds, cleanly apart.** Five collapses are deep (R² −2.6 to −233):
  each model contains an exponential or a power, has 46 to 67 nodes, fits the
  training rows well, and its predictions on the out-of-domain rows go 16 to
  20.5 times further from the training mean than any training target. Five are
  mild (R² −0.38 to −0.01): small or smooth models (a line, a product of two
  features, square roots) whose predictions stay within 0.85 to 8 times that
  span and are simply wrong beyond the box.
- **The engine's near-domain guard sees none of them.** It calls all 65
  returned models stable, the 11 collapses included: its probes reach 10 %
  beyond the data, while the out-of-domain rows of these datasets lie up to
  31 % (`228_elusage`), 218 % (`210_cloud`) and 302 % (`561_cpu`) of a
  feature's training width beyond the box.
- **In every deep collapse, the Pareto front of the same fit holds a smaller
  model that does not collapse**, at a cost on the hold-out: `228_elusage`
  seed 4, `282 − 61·log(X0)` (6 nodes, hold-out R² 0.897 against 0.946,
  out-of-domain R² 0.23 against −233); `210_cloud` seed 3, 7 nodes (0.557
  against 0.716 on the hold-out, 0.81 against −19.9 out of domain);
  `561_cpu` seed 3, 8 nodes (0.955 against 0.994, 0.91 against −2.6).
- `228_elusage` alone gives 6 of the 11: 44 training rows and 11 out-of-domain
  rows whose target mean lies 2.6 training standard deviations above the
  training mean. Its mild collapses are R² measured on 11 rows.

## The collapses

Reach: largest distance of an out-of-domain prediction from the training
mean, in units of the largest training one. Beyond the box: out-of-domain
rows with a feature outside the training range, and the largest excess in
units of that feature's training width.

| set | dataset | seed | R² baseline | R² run again | rows ood (train) | beyond the box | reach | size | operators | kind |
|---|---|---|---|---|---|---|---|---|---|---|
| R7raw | 228_elusage | 4 | −232.5 | −232.5 | 11 (44) | 10, 0.31 | 18.2 | 63 | exp, pow, log, sqrt, / | explodes |
| R6 | 228_elusage | 0 | −224.2 | −224.2 | 11 (44) | 10, 0.31 | 20.5 | 46 | exp, pow, / | explodes |
| R7raw | 228_elusage | 2 | −202.9 | −202.9 | 11 (44) | 10, 0.31 | 17.0 | 55 | exp, pow, sqrt, / | explodes |
| R7raw | 210_cloud | 3 | −19.85 | −19.85 | 22 (86) | 17, 2.18 | 16.3 | 64 | exp, pow, tanh | explodes |
| R6 | 561_cpu | 3 | 0.903 | −2.574 | 42 (167) | 34, 3.02 | 16.3 | 67 | exp, pow, sqrt | explodes |
| R7raw | 228_elusage | 0 | −0.383 | −0.383 | 11 (44) | 10, 0.31 | 0.85 | 5 | a line | smooth, wrong beyond |
| R7raw | nikuradse_1 | 3 | −0.381 | 0.392 | 72 (290) | 66, 1.08 | 1.67 | 70 | — | another model when run again |
| R6 | 228_elusage | 1 | −0.131 | −0.131 | 11 (44) | 10, 0.31 | 0.89 | 19 | sqrt, sq | smooth, wrong beyond |
| R7raw | 210_cloud | 4 | −0.103 | −0.103 | 22 (86) | 17, 2.18 | 8.03 | 7 | X2·X3 | smooth, wrong beyond |
| R6 | 210_cloud | 1 | −0.079 | −0.079 | 22 (86) | 17, 2.18 | 1.42 | 38 | tanh, / | smooth, wrong beyond |
| R6 | 228_elusage | 3 | −0.011 | −0.011 | 11 (44) | 10, 0.31 | 0.97 | 12 | exp, tanh, sqrt | smooth, wrong beyond |

How each kind was read. *Explodes*: reach of 16 or more with an exponential
or a power in the formula, while the training R² stays high (0.86 for
`228_elusage` seed 4); the model is sound inside the box and leaves it at
the first rows beyond. *Smooth, wrong beyond*: reach below 1.5, or a
low-degree product (reach 8 for `X2·X3` on rows up to 2.2 widths beyond the
box); no term explodes, the shape is wrong outside, and on `228_elusage` the
out-of-domain mean is shifted by 2.6 standard deviations, which a model fitted
inside cannot know. The third kind of the plan (an out-of-domain set too
small or flat for R² to judge) is not a separate cause here: the flatness
ratios are 1.1 to 31.6, but the five mild collapses are all measured on 11
or 22 rows, with R² between −0.38 and −0.01.

Among the 54 fits that do not collapse, the reach of the returned model has a
median of 1.04; three exceed 5, all on `561_cpu` (7.7 to 10.7, R² 0.56 to
0.88): its targets are skewed and its out-of-domain rows lie up to three
widths beyond the box, so large predictions there are right.

## What simple rules would have done (described, not chosen)

Each rule picks, in each of the 65 fits, a model among the returned one and
its Pareto front. "Reach on the out-of-domain inputs" looks at the
out-of-domain **inputs** (never their targets), which a real fit does not
have: it stands for a test on probes beyond the training box, which is what a
deployable rule would use (as `extrapolate=True` already does along one
feature). The hold-out cost is not shown: in-domain cost needs the fold fits,
which this examination did not run.

| rule | collapses | worst R² | median R² out of domain | models changed | R² out of domain lower by more than 0.05 |
|---|---|---|---|---|---|
| returned model (0.8.0) | 10 | −232.5 | 0.647 | 0 | 0 |
| keep the returned model if its reach is 10 or less, else the best hold-out entry of reach 10 or less | 7 | −1.99 | 0.735 | 6 | 0 |
| the same with reach 5 | 6 | −1.99 | 0.685 | 9 | 1 |
| the same with reach 2 | 6 | −2.57 | 0.514 | 14 | 8 |
| best hold-out entry of 20 nodes or fewer | 6 | −5.14 | 0.735 | 27 | 7 |
| best hold-out entry of 30 nodes or fewer | 7 | −7.73 | 0.735 | 20 | 5 |
| smallest entry within 0.02 of the best hold-out R² | 14 | −253.3 | 0.527 | 53 | 25 |
| smallest entry within 0.05 of the best hold-out R² | 10 | −253.3 | 0.668 | 55 | 25 |

(The counts come from `benchmarks/results_0.9/collapses_rules.py`.)

## What the next plan starts from

- The deep collapses are the ones worth a change: the mild ones are R² near
  zero on 11 to 22 rows whose target lies beyond what the training data
  shows.
- A test of how far the predictions go beyond the training box tells the
  five deep collapses apart on these data, where the near-domain guard tells
  none: with a generous band (reach 10), taking the best Pareto entry within
  it turns them into R² of −2.0 at worst (two stay below zero), changes 6 of
  the 65 models and lowers none by more than 0.05 out of domain. A real fit
  has no out-of-domain inputs: the test would run on probes beyond the box,
  in every direction. How far the probes go, how wide the band
  is, and whether the test filters or only breaks ties are what the next plan
  has to fix in advance, with criteria on the folds (in-domain R²) and on the
  F41 exact laws as well as out of domain.
- Preferring smaller models across the board is not the way: it changes most
  fits and makes collapses more frequent, not less.
