# Measurements of the release 1.0.0

Plan: `../PLAN_RELEASE_1.0.md`, committed before the first measurement of the
release (commit `15e95d8`). Every record here is of gp-elite 1.0.0 **installed
from its wheel** (built from commit `61b78ba`; SHA-256 of the wheel and of the
source archive in `environments.txt`) in a fresh environment, never of the
sources, except where 0.9.0 is named: it is then gp-elite 0.9.0 installed from
PyPI in another fresh environment. `environments.txt` lists the packages of
each environment: `/venv09p` (0.9.0 from PyPI), `/venv10` (the wheel alone,
for M1 and M2) and `/venv10x` (the wheel with the packages some scripts of M3
use). The 0.9.0 wheel on PyPI differs from the one measured for 0.9.0 in its
description only (`environments.txt`).

Machine: Linux, 4 cores (Intel Xeon with AVX-512), 15 GB; Python 3.11.15,
NumPy 2.4.6, scikit-learn 1.9.1, pandas 3.0.6, and for the scripts that use
them sympy 1.14.0, gplearn 0.4.3, xgboost 3.2.0, matplotlib 3.11.2, the
versions of the 0.9.0 measurements. `PYTHONHASHSEED=0`, one process per
measurement, one measurement step at a time on the machine. The scripts ran
from a copy of `benchmarks/`, `examples/` and the two README files of commit
`61b78ba`, without the package beside them, so that none could import the
sources (`m3/m3_driver.sh`).

## M1, equivalence (13 October 2026)

| File | What it shows |
|---|---|
| `M1_compare_13_configurations.txt`, `M1_equiv_1.0.0/` | the thirteen reference configurations of `benchmarks/speed_equivalence.py` return with the wheel the same models as the engine adopted in phase 5 (`../phase5/mechanics/B1_E1_N1_default`) |
| `M1_ii113_1.0.0.jsonl`, `M1_compare_ii113.txt` | the typed fits of Feynman II.11.3, seeds 0 to 9 (`benchmarks/phase3_bench.py`), return the same models as 0.9.0 (`../release/M1_ii113_0.9.0.jsonl`) |

## M3, every public figure measured again (14 October 2026)

`m3/` holds the records of the figures of `README.md`, `README.fr.md`, the
notebooks, the case studies and `paper/paper.md`. They were produced by
`m3/m3_driver.sh`, one step after the other, from 23:57 on 13 October to
00:46 on 14 October: `benchmarks/release_claims/run_claims.py` with the
commands of 0.9.0, in two queues side by side (`m3/claims_queues.txt`), the
islands in sequence under the default `parallel=None` as for 0.9.0; then
`benchmarks/case_studies.py kepler`, `hubble` and `nikuradse`
(`m3/case_*`); then the check of Kepler's law normalised by min-max
(`m3/kepler_minmax_check.txt`). After them,
`benchmarks/release_claims/deduced_constant_check.py` ran with 0.9.0 and with
1.0.0 (`m3/deduced_constant_venv09p.txt`, `m3/deduced_constant_venv10.txt`).

**What changes, and why.** Every change below comes from the forms fitted
directly (B1, E1) and from the deduced constant; the typed search is the same
as in 0.9.0 (M1).

- Feynman 15 (`feynman15.txt`): 15/15 exact and 15/15 within 1e-3 for the
  returned model, against 12/15 and 13/15. I.16.6, I.18.12 and III.15.12
  become exact. With `normalize='none'` the three angle laws stay exact
  (`feynman_angles_normalize_none.txt`): the default now returns them too.
- The duel with gplearn (`duel_gplearn.txt`): 15/15 against 6/15 exact, 15/15
  against 7/15 within 1e-3, GP_ELITE ahead on 9 equations, tied on 6, behind
  on none (against 12/15, ahead on 8, behind on 1).
- The table of `units=` on II.11.3 (`units_ab_ood.txt`): without units, 5/5
  exact laws in about a second per run (median 1 s, 20 nodes), with four times
  the generations as well; 0/5 valid models with 0.9.0. With units, unchanged:
  5/5 valid, 2/5 exact, 27 nodes, median 27 s per run (34 s for 0.9.0, same
  models, M1). Under `units=` the forms fitted directly do not act.
- The size study (`scaling.txt`): I.16.6 exact at 1,000 points and more (at
  2,000 in a form other than the textbook one), and in 5 of the 13 runs below;
  the four other laws exact at every size in every run, as before. The five
  fits take 58 s at 1,000 points and 151 s at 10,000 (139 s and 380 s).
- The battery example (`battery_example.txt`): R² +0.993 on the random split
  (+0.991), +0.162 on the forward split (−0.314), with another equation, in
  the current and the cycle. The tree ensembles are unchanged.
- The notebook snippet of the torque (`notebook_snippet_torque.txt`): without
  units, `r * F * sin(theta)` in 6 nodes instead of `|F * r * sin(theta)|` in 7.
- `robustness_check.txt`: the case without a hold-out on a small signed
  dataset returns the exact law `0.5 + sin(2 * X0)` (R² 0.903 before).
- `small_data_release.txt`: worst train and test R² 1 instead of 0.9974 and
  0.998.
- `time_limit=` (`time_limit_check.txt`, 15 of 16 checks): with a 15 s budget
  the fit in parallel ends at 16.5 s (17.6 s); the fit in sequence finds the
  exact law and ends at 9.2 s, before the budget, so the check that expects the
  budget to be reached fails; three restarts in a 24 s budget end at 21.6 s.
- The deduced constant (`deduced_constant_*.txt`): on seven typed fits of
  Kepler's law in SI units, 0.9.0 reports the coefficient of the law in five
  and departs from it in two (−20 % and +344 %); 1.0.0 reports it in all
  seven. The models are the same in both versions.
- `import gp_elite` takes 0.18 s (median of seven fresh processes; 0.16 s).

**What is the same.** Every other law, formula, error, size and count: the
fifteen equations with `units=` (14/15), the mystery constant (three laws),
the robust regression, the README examples (Kepler
`0.00279171 + 0.999396 * a * sqrt(a)`, the programmatic example), the
examples, the console (the law and the constant), the 1,500 printed formulas,
the 48 fits of the operator pools, the sixteen unusual inputs, the eleven
scales, the missing or infinite values, the notebook snippets other than the
torque, Nikuradse under the full protocol, and the check of min-max Kepler
(exact in 0 and 0 of 10 at 10 generations, 3 and 1 at 40, N1 off and on).
The three case studies return on the wheel what they returned on the branch
(`../case_studies/`), to the last printed digit.
