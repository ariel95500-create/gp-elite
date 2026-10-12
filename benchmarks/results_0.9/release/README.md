# Measurements of the release 0.9.0

Plan: `../PLAN_RELEASE_0.9.md`, committed before the first measurement of the
release. Every record here is of gp-elite 0.9.0 **installed from its wheel**
(built from commit `0ae3e9f`, SHA-256 of the wheel `999288fc…a6bd55e`) in a
fresh environment, never of the sources, except where 0.8.0 is named: it is
then gp-elite 0.8.0 installed from PyPI in another fresh environment.

Machine: Linux, 4 cores (Intel Xeon at 2.8 GHz with AVX-512), 15 GB; Python
3.11.15, NumPy 2.4.6, scikit-learn 1.9.1, pandas 3.0.6, and for the scripts
that use them sympy 1.14.0, gplearn 0.4.3, xgboost 3.2.0, matplotlib 3.11.2.
`PYTHONHASHSEED=0`, one process per measurement. This is not the machine of
the 0.8 figures (a 2-core container): times are not comparable with them,
the other figures are.

## M1, equivalence (11 October 2026)

| File | What it shows |
|---|---|
| `M1_compare_13_configurations.txt` | the thirteen reference configurations of `benchmarks/speed_equivalence.py` return with the wheel the same models as 0.8.0 (`../repro/default`) |
| `M1_ii113_0.9.0.jsonl`, `M1_compare_ii113.txt` | the typed fits of Feynman II.11.3, seeds 0 to 9 (`benchmarks/phase3_bench.py`), return the same models as 0.8.0 in phase 3 (`../phase3/u0_0.8.0.jsonl`) |

## M3, every public figure measured again (11 October 2026)

`m3/` holds the records of every figure quoted in `README.md`,
`README.fr.md`, the notebooks and `paper/paper.md`, produced by
`benchmarks/release_claims/run_claims.py` in two queues side by side (the
start of each command is in `m3/claims_queues.txt`), with the commands listed
in `../../results_0.8/README.md`. The scripts ran from a copy of
`benchmarks/` and `examples/` without the package beside them, so that none
could import the sources. The islands ran in sequence under the default
`parallel=None`, as on the 2-core machine of the 0.8 figures, through
`benchmarks/release_claims/sitecustomize.py`; an explicit `parallel=True`
still ran them in parallel. `benchmarks/ab_ood.py` now passes
`parallel=False` itself, which is the same thing.

**What is the same as for 0.8.0.** Every law, formula, error, size and count
of the records: Feynman 15 (12/15 exact, 13/15 within 1e-3), the three angle
laws with `normalize='none'`, the duel with gplearn (12/15 against 6/15),
the fifteen equations with `units=` (14/15), the table of `units=` on
II.11.3 (0/5 against 5/5 valid, 2/5 exact, sizes 59 and 27, the same test
and out-of-domain R²), the size study (the same 85 fits), the sixteen
unusual inputs, the five laws on 25 points, the eleven scales, the 1,500
printed formulas, the 48 fits of the operator pools, the README examples,
the examples, the console (the law and the constant; the console fixes no
seed, so the internal statistics it prints differ from one run to the next),
the notebook snippets, the missing or infinite values and Nikuradse.

**What differs, and why.**

- Times. This machine runs one fit about 30 % slower than the 2-core
  container of 0.8 (the size study takes 139 s at 1,000 points and 380 s at
  10,000, against 108 s and 284 s), and the typed search more than five times
  faster than 0.8.0 (phase 3): the table of `units=` gives 29 s, 34 s and
  114 s per run (median) for its three arms, against 21 s, 149 s and 84 s.
- `time_limit=`: for a 15 s budget the fits end at 17.4 s in sequence and
  17.6 s in parallel (`m3/time_limit_check.txt`, 13 of 16 checks), and at
  17.0 s and 17.5 s when run again (`m3/time_limit_check_rerun.txt`, 15 of
  16). gp-elite 0.8.0 on this machine ends at 17.5 s and 17.6 s
  (`m3/time_limit_check_0.8.0_rerun.txt`, 14 of 16): the checks that fail
  bound the overrun at one generation plus one second, and the final
  selection takes longer on this machine whatever the version. The README
  now says two to three seconds instead of under two.
- The battery example: the random forest it compares with gives R² −2.521 on
  the forward split with scikit-learn 1.9.1, against −2.515 with
  scikit-learn 1.8; the figures of gp-elite and of XGBoost are unchanged.
- `import gp_elite` takes 0.16 s here (median of seven fresh processes); the
  figure of 0.08 s is quoted only in the 0.8.0 entry of the CHANGELOG, which
  describes that release and its machine.
- `robustness_check.txt` and `small_data_release.txt` are the summaries the
  scripts print today, with more fields than in 0.8; their records
  (`.jsonl`) are identical.

## M2, campaign R paired with 0.8.0 (11 and 12 October 2026)

`m2/campaignR_0.8.0.jsonl` and `m2/campaignR_0.9.0.jsonl`: the whole suite of
phase 1 (F41, F41 with 1 % and 10 % noise, R6, R7raw, and the frozen test set
TF78, TS14, TR25, TR25raw: 1,775 fits per version, budget T of 30 s per fit),
run by `benchmarks/phase1_bench.py run-paired`, each job started with both
versions at the same time, two jobs at a time, from 20:44 on 11 October to
03:55 on 12 October, in four time slices (the bench resumes). No crash.
`m2/tables_*.md` are the tables of `benchmarks/phase1_report.py` for each
version; `m2/compare.txt` the comparison and the criteria of the plan
(`benchmarks/release_claims/compare_m2.py`).

| indicator | 0.8.0 | 0.9.0 |
|---|---|---|
| F41 exact laws (205 fits) | 86 | 86 |
| structure retrieved, F41N1 / F41N10 (205 fits each) | 66 / 62 | 66 / 62 |
| R6 folds, median test R² | 0.8095 | 0.8095 |
| R6 + R7raw, collapses out of domain (65 fits), worst R² | 10, −232.5 | 10, −232.5 |
| TF78 exact laws (390 fits) | 144 | 144 |
| TS14 exact laws (70 fits) | 7 | 7 |
| TR25 folds, median test R² | 0.7466 | 0.7466 |
| TR25, collapses out of domain (125 fits) | 37 | 36 |

The two versions return the same expression on 1,746 of the 1,775 jobs; the
29 others differ where the deadline of 30 s falls (the untyped search returns
the same models at equal work, M1). The four criteria of the plan are met.

Against phase 1 (0.8.0 on another machine, at 2.1 GHz): 86 exact laws on F41
instead of 88, 66 and 62 structures instead of 70 and 67, 144 on TF78
instead of 145, and a median R² of 0.747 on the TR25 folds instead of 0.766,
with the same engine. Under a time budget the figures depend on the machine;
the comparison of versions is the paired one above.

## M4, tests (12 October 2026)

`M4_wheel_tests.txt`: the test suite against the wheel installed in a fresh
environment, 142 passed under Python 3.9.23, 3.11.15 and 3.14.0rc2 (the 3.14
build uv provides here), each importing the installed package; `twine check`
passes for the wheel and the source archive. The **Tests** workflow of the
repository (Linux, Python 3.9 to 3.14; Windows, 3.12 and 3.14) is green on
the release commit `0ae3e9f` and on every later commit of the branch.
