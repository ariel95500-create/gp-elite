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

## M3, every public figure measured again (30 October 2026)

`m3/` holds the records of the figures of the READMEs, the notebooks, the case
studies and the paper, produced by `m3/m3_driver.sh` as for the first candidate,
one step after the other, from 07:02 to 07:58, with `/venv11bx`, on a copy of
`benchmarks/`, `examples/` and the READMEs of commit 66abffa without the package
beside them. Outside `benchmarks/results_1.1/`, those files are the ones of
82f303e, the commit of the first candidate's M3, but for
`benchmarks/tp_diagnostic.py`, which M3 does not run. The driver has one step more: the gas law of the TP notebook
timed alone three times (`m3/tp_timing/gas_1.1.0.txt`).

**The figures of the first candidate.** `m3_compare.py` compares each record
with the first candidate's once times, dates and the paths of the environments
and folders are masked (`m3_compare_candidate1_vs_candidate2.txt`). 60 records
are the same: every law, formula, error, size and count, with units and
without. What differs depends on timing only:
- the order in which the parallel queues of `run_claims.py` ended
  (`claims_queues.txt`);
- in the console example, run on three parallel islands, the order of the
  islands' first prints and the statistics of the stigmergic memory. The final
  result is the same: `force = 250 * elongation`, constant 250 kg/s²;
- the parallel fit of `time_limit_check.txt`, stopped at its deadline: R² 0.9979
  against 1.0000, a pass in both. 15 of 16 checks, as with 1.0.0 and the first
  candidate;
- `import gp_elite` takes a median of 0.12 s.

So everything the first candidate's M3 found with units holds: Feynman 15 with
`units=` 15/15 exact, the table of `units=` on II.11.3 (5/5 out of domain),
Kepler in its textbook form at every seed, Hubble, the console and the mystery
constant.

**The TP notebook.** The six fits return the formulas and the deduced constants
of 1.0.0 (g 9.81 and 9.74, R 8.250, P 10.02 W), in 42, 51, 55, 47, 53 and 46 s,
294 s in all. The gas law takes 53 s against 85 s with the first candidate.
Timed alone three times, it takes 48.6, 49.5 and 49.8 s, against 49.9 to 51.2 s
with 1.0.0 and 77 to 79 s with the first candidate (on 28 October).

The time of 1.0.0 the notebook records, 243 s, was measured on 27 October. To
compare on the same day, the notebook script was run after M3 four times, 1.0.0
(`/venv10x`) and the second candidate in turn, alone on the machine
(`m3/tp_timing/notebook_pair/`):

| fit | 1.0.0, run 1 / run 2 (s) | 1.1.0, run 1 / run 2 (s) |
|---|---|---|
| pendulum | 41 / 43 | 43 / 45 |
| spring | 53 / 56 | 52 / 51 |
| free fall | 46 / 49 | 58 / 55 |
| power | 43 / 46 | 46 / 46 |
| gas | 56 / 60 | 55 / 55 |
| illuminance | 46 / 44 | 48 / 48 |
| in all | 285 / 298 | 302 / 300 |

Every fit returns the same formula in all four runs. Two things follow:
- the machine was faster on 27 October: on 30 October, 1.0.0 itself takes 285
  and 298 s, against 243 s then. The first candidate's comparison, 320 s
  against 243 s, compared two days, and the slowdown of the five laws other
  than the gas law was mostly the machine's. Its diagnosis of the gas law
  stands, being timed on one day with both versions (50 s against 78 s);
- on the same day, the notebook takes with 1.1.0 about the time of 1.0.0, 301 s
  against 292 s on average. The one fit that stays slower is the free fall.
  Timed alone three times in turn (`m3/tp_timing/fall.py`,
  `fall_timings.txt`), it takes 50.5 to 51.3 s against 43.1 to 44.1 s with
  1.0.0. Its trace shows the seed of U1, `(t)²`, placed at generation 0, and no
  seed of fractional units: it is not the case U2 corrects. With noise no law
  is exact, so the search runs its whole budget from that seed. Where the
  7 s go has not been profiled.

The free fall, 7 s slower in six fits of about 50 s, was put to the author
with the rest of M3. On 30 October 2026 he chose to keep the engine as it is:
the 7 s are written in the documents of 1.1.0, and an earlier stop when the
law placed at generation 0 holds on noisy data is proposed in the plan of 1.2
(`../ROADMAP.md`).
