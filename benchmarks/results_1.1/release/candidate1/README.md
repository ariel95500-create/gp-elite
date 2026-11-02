# Measurements of the release 1.1.0, first candidate (engine U1)

These measurements were made on the first release candidate (commit 2c277df,
engine U1). M3 found the TP notebook slower; the author chose to correct it
before the release, and change U2 was adopted (`../../PLAN_U2.md`). The release
then started again from a second candidate (`../README.md`). The records were
moved here on 29 October 2026; paths below that begin with `../` are now one
level deeper (`../../`).

What `../PLAN_RELEASE_1.1.md` asks before gate 6, as it was measured. The
machine is an Intel Xeon at 2.8 GHz (as `../../PLAN.md` recorded on 26 October;
not recorded on the days of these measurements), 4 cores, AVX-512; every fit runs in its own
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
1.1.0 (II.11.28, seed 5), and the four other seeds of the same equation become
exact (1 to 4; corrected on 30 October 2026 after the first review of M5 of the
second candidate, which first read "another seed").
Under units the median fit ends at once: the seed placed first is the exact law,
and the search stops on it.

**Criteria of the plan**: the seven are met.
- F41 not more than 3 exact laws below 1.0.0: 163 and 163.
- F41N1 and F41N10 not more than 3 structures below: identical.
- R6 median within 0.005: identical.
- Collapses of R6 + R7raw not above 1.0.0 plus 2: 11 for 10.
- U41 at least 10 exact laws above 1.0.0: 108 to 165.
- Every model returned under units passes `check_dimensions`: 1,005 of 1,005.

## M3, every public figure measured again (28 October 2026)

`m3/` holds the records of the figures of the READMEs, the notebooks, the case
studies and the paper. They were produced by `m3/m3_driver.sh`, one step after
the other, from 00:24 to 01:17 on 28 October, with `/venv11x`, on a copy of
`benchmarks/`, `examples/` and the READMEs of commit 82f303e without the package
beside them. The steps:
- `benchmarks/release_claims/run_claims.py` with the commands of 1.0.0;
- the three case studies;
- the check of Kepler normalised by min-max;
- `deduced_constant_check.py` with 1.0.0 and with 1.1.0;
- the French TP notebook, run as a script (`m3/tp_six_lois.py`, its code cells
  without the `pip` line; output in `m3/notebook_tp_six_lois_1.1.0.txt`).

The records of 1.0.0 are `../../results_0.9/release_1.0/m3/`, measured on the
same machine.

**Without units, the same.** Every law, formula, error, size and count:
- Feynman 15 and the duel with gplearn (15/15 against 6/15);
- the size study, the battery example, the robust regression;
- the README examples, the console, the 1,500 printed formulas, the operator
  pools, the unusual inputs, the scales, the small data;
- Nikuradse under the full protocol, the notebook snippets, min-max Kepler;
- `time_limit=`, 15 of 16 checks as for 1.0.0 (the fit in sequence stops at
  8.7 s on an exact law, before the budget).

Times move by a second or two either way. `import gp_elite` takes a median of
0.11 s (0.18 s).

**With units, what changes** (U1, the seeds of 1.0 under units):
- Feynman 15 with `units=` (`feynman15_units.txt`): 15/15 exact, against 14/15;
  I.16.6 becomes exact in 32 s (near, 59 s).
- The table of `units=` on II.11.3 (`units_ab_ood.txt`): with units, 5/5 laws
  recovered out of domain in 20 nodes and about a second per run, against 2/5,
  27 nodes and 27 s. It is now the same as without units.
- Kepler (`case_kepler.txt`, `deduced_constant_venv11.txt`): the typed fit on
  the four inner planets returns the textbook form `5.45416e-10 * X0 * sqrt(X0)`
  at every seed, in under a second; the typed fit on the eight planets returns
  `5.43909e-10 * X0 * sqrt(X0)` in 8 to 10 s, as with 1.0.0 (corrected on 30
  October 2026 after the second review of M5 of the second candidate, which
  first read "the typed fits"). 1.0.0 returned the same constant in forms such as
  `sqrt(sqrt(X0)) * sqrt(X0) * sqrt(X0) * sqrt(sqrt(X0))`, and on seed 4 of the
  case study a two-term formula. G·M☉ is unchanged (−1.64e-05 from IAU).
- Hubble (`case_hubble.txt`): the same models and the same constant.
- The console example and the mystery constant: the same laws and constants
  (250 kg/s², G), written `(249.99999999999997*X0)` and
  `6.674e-11*((X0*X1)/((X2)**2))`.
- The torque snippet with units: `r * F * sin(theta)`, in 6 nodes as before.

**The TP notebook: the same laws, slower.** The six fits return the same
formulas and the same deduced constants as with 1.0.0 (g 9.81 and 9.74, R 8.250,
P 10.02 W), in 41, 50, 54, 44, 85 and 46 s, against 33, 47, 41, 37, 48 and 37 s
(320 s in all against 243 s).

The gas law was timed again alone, three times with each version
(`m3/tp_timing/timings.txt`): 50 to 51 s with 1.0.0, 77 to 79 s with 1.1.0.
The cause, read from a profile:
- the power law seed of U1 places, beside `n * T / V`, a seed with fitted
  non-integer exponents, `pow(n, 1.0041) * pow(T, 0.9174) * pow(V, -0.9852)`.
  It passes the gate of dimensions, because the unknown constant can carry any
  units;
- the mutations of its descendants ask the typed builder for subtrees of
  fractional units, which it rarely reaches before its budget runs out
  (`_build_ek`, ten times the calls).

With noise there is no exact law to stop on, so the cost stays. The plan
expected the times of the TP notebook to change. This slowdown on the first
audience of GP_ELITE is put to the author before M4.
