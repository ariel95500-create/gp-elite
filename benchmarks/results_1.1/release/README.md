# Measurements of the release 1.1.0

What `../PLAN_RELEASE_1.1.md` asks before gate 6, as it was measured. The
machine is an Intel Xeon at 2.8 GHz, 4 cores, AVX-512; every fit runs in its own
process with `PYTHONHASHSEED=0`.

## The release candidate

Commit 2c277df sets the version to 1.1.0. Its wheel and source archive, built
from a clean export, and the two environments installed from the wheel are in
`environments.txt`, with their SHA-256 and `uv pip freeze`:
- `/venv11`: the wheel alone, with Python 3.11.15, NumPy 2.4.6 and
  scikit-learn 1.9.1, the versions of the measurements of 1.0.0;
- `/venv11x`: the same, with the packages some scripts of M3 use.

They are identical to `/venv10` and `/venv10x`, those of 1.0.0, except for
gp-elite. 1.0.0 is not yet on PyPI: the comparison is its measured wheel in
`/venv10`.

## M1, equivalence (27 October 2026)

`M1_equiv_1.1.0/`: the thirteen reference configurations of
`benchmarks/speed_equivalence.py`, run with the wheel.

- `M1_compare_adopted_vs_wheel.txt`: all thirteen identical to the adopted
  engine (`../mechanics/equiv_U1_default`).
- `M1_compare_1.0.0_vs_1.1.0.txt`: against 1.0.0, the twelve without units are
  identical. Only `D_units` differs, the one configuration with units, which is
  the configuration U1 acts on.

## M2, campaign R paired with 1.0.0 (27 October 2026)

`m2/campaignR_1.0.0.jsonl` and `m2/campaignR_1.1.0.jsonl`, 2,780 fits per
version with a budget T of 30 s per fit:
- the whole suite of phase 1 (F41, F41N1, F41N10, R6, R7raw, and the frozen test
  set TF78, TS14, TR25, TR25raw: 1,775 fits);
- U41, U41N1 and U41N10 (615);
- TF78 under units (390, seeds 5 to 9).

They were run by `benchmarks/phase1_bench.py run-paired`, each job started with
both versions at the same time, two jobs at a time, from 02:45 to 13:32 on 27
October, in time slices of 6,300 s (`m2/driver.log`). No crash, no job twice.

`m2/tables_*.md` are the tables of `benchmarks/phase1_report.py` for each
version. `m2/compare.txt` holds the comparison and the criteria of the plan
(`benchmarks/release_claims/compare_m2_1.1.py`, committed in c5a3acc before
the campaign ended).

| indicator | 1.0.0 | 1.1.0 |
|---|---|---|
| F41 exact laws (205 fits) | 163 | 163 |
| structure retrieved, F41N1 / F41N10 (205 fits each) | 108 / 86 | 108 / 86 |
| R6 folds, median test R² | 0.8095 | 0.8095 |
| R6 + R7raw, collapses out of domain (65 fits) | 10 | 11 |
| U41 exact laws (205 fits) | 108 | 165 |
| U41, the five families of 1.0, exact (90 fits) | 16 | 57 |
| U41 equations never exact in five seeds (of 41) | 13 | 6 |
| structure retrieved, U41N1 / U41N10 (205 fits each) | 79 / 80 | 113 / 99 |
| fits under units passing `check_dimensions` | 1,005 of 1,005 | 1,005 of 1,005 |
| U41, median time of a fit (s) | 30.1 | 0.5 |
| **frozen test set**, deciding nothing: | | |
| TF78 exact laws (390 fits) | 213 | 213 |
| TS14 exact on the test rows (70 fits) | 8 | 8 |
| TR25 folds, median test R² | 0.7691 | 0.7691 |
| TF78 under units, exact laws (390 fits) | 169 | 225 |
| TF78 under units, median time of a fit (s) | 30.3 | 1.5 |

**Without units**, U1 does not act. Of the 1,775 jobs, 1,740 return the same
expression. The 35 that differ all reached the time budget, in one version or
both, and none changes status (exact, near or missed). That is the timing
effect the plan expected, as between 0.8.0 and 0.9.0 (29 of 1,775). R7raw has
one more collapse out of domain (5 to 6) and TR25raw one more (26 to 27), with
the same worst R² in both versions.

**Under units**, on U41, 14 equations gain exact fits and none loses any. On
TF78 under units, 15 gain and none loses; one fit exact with 1.0.0 is not with
1.1.0 (II.11.28, seed 5), and another seed of the same equation becomes exact.
Under units the median fit ends at once: the seed placed first is the exact law,
and the search stops on it.

**Criteria of the plan**: the seven are met.
- F41 not more than 3 exact laws below 1.0.0: 163 and 163.
- F41N1 and F41N10 not more than 3 structures below: identical.
- R6 median within 0.005: identical.
- Collapses of R6 + R7raw not above 1.0.0 plus 2: 11 for 10.
- U41 at least 10 exact laws above 1.0.0: 108 to 165.
- Every model returned under units passes `check_dimensions`: 1,005 of 1,005.

The release goes on to M3.
