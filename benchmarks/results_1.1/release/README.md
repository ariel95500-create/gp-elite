# Measurements of the release 1.1.0

What `../PLAN_RELEASE_1.1.md` asks before gate 6, as it was measured. The
machine is an Intel Xeon at 2.8 GHz, 4 cores, AVX-512; every fit runs in its own
process with `PYTHONHASHSEED=0`.

The first candidate (engine U1) was measured up to M3 (`candidate1/`). M3 found
the TP notebook slower than with 1.0.0. The author chose to correct before the
release, and change U2 was adopted (`../PLAN_U2.md`). Everything below is the
second candidate.

## The release candidate

Commit 6e0e296 carries the engine of 26349ef (U1 and U2); the commits after
26349ef change benchmarks and documents only. Its wheel and source archive,
built from a clean export, are in `environments.txt` with their SHA-256 and the
`uv pip freeze` of three environments:
- `/venv11b`: the wheel alone, with the packages of `/venv11` (Python 3.11.15,
  NumPy 2.4.6, scikit-learn 1.9.1);
- `/venv11bx`: the same, with the packages of `/venv11x`;
- `/venv10p`: gp-elite 1.0.0 installed from PyPI on 29 October 2026, the day it
  was published, with the packages of `/venv10`. Its `gp_elite/` files are
  identical to those of the measured wheel of 1.0.0.

## M1, equivalence (29 October 2026)

`M1_equiv_1.1.0/`: the thirteen reference configurations of
`benchmarks/speed_equivalence.py`, run with the wheel in `/venv11b`.

- `M1_compare_adopted_vs_wheel.txt`: identical to the adopted engine
  (`../mechanics/equiv_U2`).
- `M1_compare_candidate1_vs_candidate2.txt`: identical to the first candidate.
  None of the thirteen configurations reaches the case U2 changes.

## M2, campaign R paired with 1.0.0 (29 and 30 October 2026)

`m2/campaignR_1.0.0.jsonl` and `m2/campaignR_1.1.0.jsonl`: 1.0.0 from PyPI
(`/venv10p`) against the second candidate (`/venv11b`), 2,780 fits per version,
the suites of the first candidate with a budget T of 30 s per fit:
- the whole suite of phase 1 (F41, F41N1, F41N10, R6, R7raw, and the frozen test
  set TF78, TS14, TR25, TR25raw: 1,775 fits);
- U41, U41N1 and U41N10 (615);
- TF78 under units (390, seeds 5 to 9).

They were run by `benchmarks/phase1_bench.py run-paired` (`m2/driver.sh`), each
job started with both versions at the same time, two jobs at a time, from 20:14
on 29 October to 07:01 on 30 October (times of the machine, UTC), in time slices
of 6,300 s (`m2/driver.log`). The container restarted at about 01:15 and stopped
the driver; the 1,475 jobs recorded by then were whole and paired in both
files, the jobs in flight were lost, and the driver started again at 01:16 from
the jobs not recorded. No crash, no job twice.

`m2/tables_*.md` are the tables of `benchmarks/phase1_report.py` for each
version. `m2/compare.txt` holds the comparison and the criteria of the plan
(`benchmarks/release_claims/compare_m2_1.1.py`, the script of the first
candidate). `m2/details.txt` holds the figures below that the criteria do not
give, read by `m2/details.py`; on the records of the first candidate, the same
script returns the figures of its README.

| indicator | 1.0.0 | 1.1.0 |
|---|---|---|
| F41 exact laws (205 fits) | 163 | 163 |
| structure retrieved, F41N1 / F41N10 (205 fits each) | 108 / 86 | 108 / 86 |
| R6 folds, median test R² | 0.8095 | 0.8095 |
| R6 + R7raw, collapses out of domain (65 fits) | 10 | 10 |
| U41 exact laws (205 fits) | 108 | 165 |
| U41, the five families of 1.0, exact (90 fits) | 16 | 57 |
| U41 equations never exact in five seeds (of 41) | 13 | 6 |
| structure retrieved, U41N1 / U41N10 (205 fits each) | 79 / 80 | 113 / 99 |
| fits under units passing `check_dimensions` | 1,005 of 1,005 | 1,005 of 1,005 |
| U41, median time of a fit (s) | 30.1 | 0.5 |
| frozen test set, deciding nothing: | | |
| TF78 exact laws (390 fits) | 213 | 213 |
| TS14 exact on the test rows (70 fits) | 8 | 8 |
| TR25 folds, median test R² | 0.7657 | 0.7657 |
| TF78 under units, exact laws (390 fits) | 169 | 226 |
| TF78 under units, median time of a fit (s) | 30.3 | 1.6 |

Without units, the second candidate does what the first did. Of the 1,775
jobs, 1,728 return the same expression. The 47 that differ all reached the time
budget, in one version or both, and none changes status (exact, near or
missed). Each suite out of domain has the same collapses in both versions.

Under units, the figures of the first candidate, and one more law on the frozen
test set:
- on U41, 14 equations gain exact fits and none loses any, as with the first
  candidate;
- on TF78 under units, 16 equations gain and none loses (15 with the first
  candidate). As then, one fit exact with 1.0.0 is not with 1.1.0 (II.11.28,
  seed 5), and another seed of the same equation becomes exact. 30 equations
  of 78 are never exact in five seeds, against 37 with 1.0.0.

**Criteria of the plan**: the seven are met.
- F41 not more than 3 exact laws below 1.0.0: 163 and 163.
- F41N1 and F41N10 not more than 3 structures below: identical.
- R6 median within 0.005: identical.
- Collapses of R6 + R7raw not above 1.0.0 plus 2: 10 and 10.
- U41 at least 10 exact laws above 1.0.0: 108 to 165.
- Every model returned under units passes `check_dimensions`: 1,005 of 1,005.

**The same 1.0.0, two campaigns.** The figures of 1.0.0 on real data are not
those of the first candidate's campaign: R6 had 5 collapses then and 4 now,
R7raw 5 and 6, and the TR25 median was 0.7691 and is 0.7657. The `gp_elite/`
files are the same, so this is the timing of the fits. A fit that reaches the
budget of 30 s returns the best model found by then, and how far it got depends
on the load of the machine. Between the two campaigns, 114 of the 1,775 jobs
without units return another expression with 1.0.0, all of them at the budget,
and three fits go from near to missed: Feynman II.2.42 seed 1 and two Strogatz
fits. Under units, 43 differ, all at the budget, with the same counts of exact
laws (`m2/details_1.0.0_two_campaigns.txt`). That is why the two versions are
compared within one campaign, each job run with both at the same time.
