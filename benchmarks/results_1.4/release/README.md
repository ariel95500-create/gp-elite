# Measurements of the release 1.4.0

What `../PLAN_RELEASE_1.4.md` asks before gate 12, as it was measured. The
machine has 4 cores (an Intel Xeon under KVM). Every fit runs in its own
process with `PYTHONHASHSEED=0`. The container does not always run on the same
host, so the versions are compared within one campaign or one day, never
across days.

## The release candidate

Commit f6a36cd carries the engine of 227d837, the candidate of the campaign
of N2b. It changes the version number, opens the CHANGELOG and rewrites one
comment of `gp_elite/core.py`. Its wheel and source archive were built from a
clean export. `environments.txt` gives their SHA-256 and the `uv pip freeze`
of the environments:
- `/venv14r`: the wheel alone, with the packages of `/venv13r` (Python
  3.11.18, NumPy 2.4.6, SciPy 1.17.1, scikit-learn 1.9.1);
- `/venv14rx`: the same, with the packages of `/venv13rx`, for M3;
- `/venv13p`: gp-elite 1.3.0 installed from PyPI. Its `gp_elite/` files are
  those of the published wheel, downloaded again and checked against its
  SHA-256.

`twine check --strict` passes for both files.

## M1, equivalence (13 November 2026)

`M1_equiv_1.3.0/`, `M1_equiv_n2b/` and `M1_equiv_1.4.0/` hold the thirteen
reference configurations of `benchmarks/speed_equivalence.py`. They were run
with `/venv13p`, `/venv14n2b` and `/venv14r` by `run_m1.sh`, from a copy of
`benchmarks/` of f6a36cd (`M1.log`). As the plan expected:
- **the thirteen of 1.4.0** are identical to those of the candidate of N2b
  (`M1_compare_n2b_vs_1.4.0.txt`);
- **against 1.3.0** (`M1_compare_1.3.0_vs_1.4.0.txt`), twelve are identical,
  and C_big differs in its Pareto front only: its model is the same. C_big is
  a noisy table, 5,000 rows of x0·x1/x2 with Gaussian noise. Run again with
  each version to read its trace, 1.4.0 places twelve noise-tolerant seeds
  there, the six of 1.3.0 among them, where 1.3.0 places six.

The thirteen took 21.8 s with 1.3.0, 21.5 s with the candidate of N2b and
26.2 s with 1.4.0, run in that order. The last two have the same engine, so
these times say nothing about it.

## M2, campaign R paired with 1.3.0 (13 and 14 November 2026)

`m2/campaignR_1.3.0.jsonl` and `m2/campaignR_1.4.0.jsonl`: 1.3.0 from PyPI
(`/venv13p`) against the candidate (`/venv14r`), 3,092 fits per version with
a budget T of 30 s per fit:
- the whole suite of phase 1 (F41, F41N1, F41N10, R6, R7raw, and the frozen
  test set TF78, TS14, TR25, TR25raw: 1,775 fits);
- U41, U41N1 and U41N10 (615);
- TF78 under units (390, seeds 5 to 9);
- TF78N, the frozen noisy test set (312).

`m2/tp_*.jsonl` and `m2/tpt10_*.jsonl` hold the two sets of TP, 400 fits per
version each.

The campaign was run by `m2/slice.sh`, from a copy of `benchmarks/` of
commit 796b31c with the data cache of the M2 of 1.3. Each job started with
both versions at the same time, two jobs at a time (`m2/driver.log`, times
of the machine, UTC):
- TP and TPT10 in one go, from 20:46 to 21:52 on 13 November;
- the benches in six slices of at most 6,300 s, from 21:53 to 08:19 on
  14 November.

The container did not restart, and the machine recorded at each slice is of
the same model (`m2/machine_*.txt`). At the end, each set has the same jobs
in both files, and no fit crashed.

`m2/compare.txt` holds the comparison and the criteria of the plan
(`benchmarks/release_claims/compare_m2_1.4.py`, committed before any record
of M2 existed). To check that it runs, it was tried before on records of
earlier campaigns: those of the M2 of 1.3 for the benches, those of campaign
N2b for TP, and the baseline of TPT10 against itself. That printed the
counts of the baseline of TPT10 by experiment, which its plan had left
unread; no change of the engine followed, and TPT10 decides nothing.

| indicator | 1.3.0 | 1.4.0 |
|---|---|---|
| F41 exact laws (205 fits) | 171 | 171 |
| structure retrieved, F41N1 / F41N10 (205 fits each) | 116 / 87 | 152 / 95 |
| R6 folds, median test R² | 0.8095 | 0.8095 |
| R6 + R7raw, collapses out of domain (65 fits) | 10 | 10 |
| U41 exact laws (205 fits) | 174 | 174 |
| structure retrieved, U41N1 / U41N10 (205 fits each) | 121 / 95 | 150 / 93 |
| fits under units passing `check_dimensions`, TF78N included | 1,161 of 1,161 | 1,161 of 1,161 |
| TP, the law, plain arm / units arm (200 fits each) | 126 / 120 | 123 / 120 |
| TP, median time of a fit, plain arm / units arm (s) | 7.0 / 8.3 | 7.0 / 8.4 |
| frozen test sets, deciding nothing: | | |
| TF78 exact laws (390 fits) | 214 | 214 |
| TS14 exact on the test rows (70 fits) | 9 | 10 |
| TR25 folds, median test R² | 0.7692 | 0.7692 |
| TF78 under units, exact laws (390 fits) | 228 | 228 |
| TF78N, structure retrieved, 1 % / 10 % noise (78 fits each) | 34 / 27 | 37 / 28 |
| TF78N under units, the same | 35 / 32 | 37 / 33 |
| TPT10, the law, plain arm / units arm (200 fits each) | 107 / 103 | 107 / 103 |

**Criteria of the plan:** the eighteen are met (`m2/compare.txt`).
- **Where 1.4 does not act:** 2,428 fits of 3,092 place the same
  noise-tolerant seeds in both versions, none in most of them. On the 782 of
  these where neither version reached its budget, the recorded formula, the
  error on the test rows and `formula_exact` are those of 1.3.0, to the bit.
- **TP:** the 400 models of 1.4.0 are those of the candidate of N2b in its
  campaign, as expected: the fits of TP are reproducible. The law comes back
  in 123 fits against 126 in the plain arm and 120 against 120 under units,
  within the 5 allowed; the median time is 7.0 s against 7.0 s and 8.4 s
  against 8.3 s; the 200 models of the units arm pass their gate.
- **Without units:** F41 keeps its 171 exact laws, and no equation falls.
  F41N1 and F41N10 have 247 structures against 203, the gain of N2b (+44,
  the plan asks +15). The R6 median and the collapses out of domain are
  unchanged.
- **Under units:** U41 keeps its 174 exact laws, and no equation falls.
  U41N1 has 150 structures against 121, U41N10 93 against 95, within the 3
  allowed. The 1,161 models returned under units pass `check_dimensions`.

The counts under noise are those of campaign N2b to the unit, for both
versions. U41 has one exact law more in each version than in that campaign
(174 against 173), which timing alone moves.

**Beside, deciding nothing** (`m2/compare.txt`):
- The structures move on nine equations, as in campaign N2b: gains at 1 %
  noise on I.32.5, I.40.1, I.44.4, II.11.27, II.11.3, II.35.18, III.15.12 and
  III.19.51, and at 10 % on I.32.5, I.44.4 and III.19.51; losses at 10 %
  noise on I.27.6 (2 → 0 without units, 5 → 1 with them) and III.15.12 (5 → 2
  and 5 → 1).
- The noise-tolerant seeds are placed in more fits with 1.4.0: 165 against
  140 in F41N1, 130 against 95 in F41N10, 125 against 95 in U41N1, 115
  against 85 in U41N10. Neither version places one on R6, R7raw or TR25.
- `formula_exact` is False about as often with both versions, suite by
  suite.
- On TP, the point source has the law in 14 fits of 20 against 18 in the
  plain arm (`../n2b/campaign/examine/`); every other experiment moves by one
  fit at most.

**The frozen test sets,** published as measured, decide nothing:
- TF78, TS14, TR25 and TF78 under units hardly move. TF78 keeps its 214
  exact laws, though 14 of its fits change status, and TF78 under units its
  228. TS14 has one exact fit more, and TR25 the same median.
- TF78N, the noisy set N2b was not designed on: the structure comes back in
  37 and 28 fits of 78 against 34 and 27, and under units in 37 and 33
  against 35 and 32.
- TPT10: the law comes back in the same number of fits, 107 and 103; it is
  useful in 173 fits against 169 in the plain arm. By experiment, at most 2
  fits move (the capacitor charge 7 → 9, Kepler's third law 10 → 9, the
  thermistor 4 → 3).

## M4, tests (14 November 2026)

`m4/summary.txt` gives the test suite of f005aab, run against the wheel of
f6a36cd by `m4/run.sh`, from 09:00 to 09:10, after M3. The wheel was
installed in a fresh environment for each of Python 3.9.25, 3.11.18 and
3.14.6, with the pins of the M4 of 1.2 and 1.3 (`m4/requirements_*.txt`),
each importing the installed package. 199 tests pass under the three versions
(`m4/pytest_*.txt`). `twine check --strict` passes for the wheel and the
source archive (`m4/twine_check.txt`), whose SHA-256 are those of
`environments.txt`.

Under 3.9 and 3.11, LAPACK printed "On entry to DLASCL ..." six times during
the tests, so the last line of their output, which `summary.txt` keeps, is
that message; the line before it reads "199 passed". The messages come from
a check of scikit-learn that the tests run,
`check_positive_only_tag_during_fit`: there the new scan of the logarithm met
a form it could not evaluate. That was a fault of N2b, below.

## The fault of the scan of the logarithm, and correction L1 (16 November 2026)

Where an input column is negative throughout, a monomial of that column with
a fractional exponent is not a number. The scan of the logarithm of N2b
(`_elem_log_scan`) passed such a form to `np.linalg.lstsq`, which raised. The
try/except of the noise-tolerant stage then dropped every form of that pass,
the scans of the sine and the cosine included, and LAPACK printed its message
on the console. Two scripts, which decide nothing, measured it
(`m4/log_scan/`):
- `negative.py`: on noisy data whose first input column is negative
  throughout, six laws at 1 % and 10 % noise, a pass of N2b raised in 11
  cases of 12, and LAPACK printed its message 114 times. With the column
  positive, no pass raised.
- `count.py`: the 3,892 fits of M2, TP and TPT10, run again with 1.4.0 for
  one generation, which runs the noise-tolerant stage on the data of each
  fit. The stage runs in 3,562 of them (2,762 of the 3,092 of the benches,
  and the 800 of TP and TPT10), and no pass of N2b raises: all their inputs
  are positive. The fault touched no fit of the measurements.

The author decided to correct it and to check the corrected engine by a
targeted verification rather than run the measurements again
(`../PLAN_RELEASE_1.4.md`, "Correction L1 after M4", written before the
verification ran). L1 (ec44e8e) adds two lines to `_elem_log_scan`: a form
whose logarithm is not finite on the data is skipped. A test checks it on a
negative column (`test_l1_log_scan_skips_a_form_it_cannot_evaluate` in
`tests/test_guarantees.py`). The wheel and the source archive were built
again from ec44e8e, with the same version number, 1.4.0. `l1/environments.txt`
gives their SHA-256, `twine check --strict` passing for both, and the eleven
files of `gp_elite/`, identical in the wheel and in the environments to those
of the commit. `core.py` is the only one that differs from f6a36cd. The wheel
was installed in two fresh environments with the packages of `/venv14r` and
`/venv14rx`: `/venv14r2` and `/venv14r2x`.

`l1/verify.sh` runs the verification in three parts, from a copy of
`benchmarks/`, `examples/`, `tests/` and the READMEs of ec44e8e, without the
package beside them (`l1/verify.log`).

**Part a** (16 November, 20:56 to 22:09):
- **M1:** the thirteen reference configurations are those of the measured
  release, to the bit (`l1/M1_compare_release_vs_l1.txt`).
- **TP and TPT10:** the 800 models are those of 1.4.0 in M2, on every field of
  their records but the time, the date and the path of the engine
  (`l1/compare_tp_l1.py`, `l1/compare_tp_l1.txt`).
- **The 24 cases of `negative.py`:** no pass of N2b raises, and LAPACK prints
  nothing (`l1/negative_l1.txt`).
- **M4 again,** with fresh environments and the tests of ec44e8e: 200 tests
  pass under Python 3.9.25, 3.11.18 and 3.14.6, the test of L1 among them,
  and LAPACK prints nothing (`l1/m4_summary.txt`, `l1/m4_pytest_*.txt`,
  `l1/m4_requirements_*.txt`).
