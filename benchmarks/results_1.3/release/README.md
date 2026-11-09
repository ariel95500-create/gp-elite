# Measurements of the release 1.3.0

What `../PLAN_RELEASE_1.3.md` asks before gate 10, as it was measured. The
machine has 4 cores (`m2/machine_20261109T0435.txt`: an Intel Xeon under
KVM). Every fit runs in its own process with `PYTHONHASHSEED=0`. The
container does not always run on the same host, so the versions are compared
within one campaign or one day, never across days.

## The release candidate

Commit 5492296 carries the engine of 492863e (A1, A2 and A3). It changes the
version number and opens the CHANGELOG. Its wheel and source archive were
built from a clean export. `environments.txt` gives their SHA-256 and the
`uv pip freeze` of the environments:
- `/venv13r`: the wheel alone (Python 3.11.18, NumPy 2.4.6, SciPy 1.17.1,
  scikit-learn 1.9.1);
- `/venv13rx`: the same, with the packages the scripts of M3 use;
- `/venv12p`: gp-elite 1.2.0 installed from PyPI, with the same packages.
  Its `gp_elite/` files are those of the published wheel.

`twine check --strict` passes for both files.

## M1, equivalence (9 November 2026)

`M1_equiv_1.2.0/` and `M1_equiv_1.3.0/` hold the thirteen reference
configurations of `benchmarks/speed_equivalence.py`. They were run with
`/venv12p` and `/venv13r` by `run_m1.sh` (`M1.log`). As the plan expected:
- **the eleven of the pool `physical`** are identical to 1.2.0
  (`M1_compare_1.2.0_vs_1.3.0.txt`);
- **E_minmax (`full`) and L_standard (`trig`)** differ from 1.2.0, and are
  identical to the candidate of A3 (`M1_compare_a3_vs_1.3.0.txt`).

The thirteen take 22.0 s with 1.2.0 and 22.4 s with 1.3.0.

## M2, campaign R paired with 1.2.0 (9 November 2026)

`m2/campaignR_1.2.0.jsonl` and `m2/campaignR_1.3.0.jsonl`: 1.2.0 from PyPI
(`/venv12p`) against the candidate (`/venv13r`), 2,780 fits per version with
a budget T of 30 s per fit:
- the whole suite of phase 1 (F41, F41N1, F41N10, R6, R7raw, and the frozen
  test set TF78, TS14, TR25, TR25raw: 1,775 fits);
- U41, U41N1 and U41N10 (615);
- TF78 under units (390, seeds 5 to 9).

The campaign was run by `phase1_bench.py run-paired` (`m2/driver.sh`), from a
copy of `benchmarks/` of commit 7a09425 with the data cache of the M2 of 1.2.
Each job started with both versions at the same time, two jobs at a time, in
time slices of 6,300 s (`m2/driver.log`). It ran from 04:35 to 13:43 on
9 November (times of the machine, UTC). The container did not restart. At
the end: 2,780 jobs in each file, the same jobs in both, none twice, no
crash. Of the 2,780 jobs, 2,250 use the pool `physical` and 530 the pool
`trig`; none uses `full`.

`m2/tables_*.md` are the tables of `benchmarks/phase1_report.py` for each
version. `m2/compare.txt` holds the comparison and the criteria of the plan
(`benchmarks/release_claims/compare_m2_1.3.py`, committed before the records
were read). `m2/details.txt` is the script of the release of 1.1 on these
records, and `m2/limits_figures.txt` gives the figures of the pages of the
limits.

| indicator | 1.2.0 | 1.3.0 |
|---|---|---|
| F41 exact laws (205 fits) | 163 | 171 |
| structure retrieved, F41N1 / F41N10 (205 fits each) | 108 / 85 | 116 / 87 |
| R6 folds, median test R² | 0.8095 | 0.8095 |
| R6 + R7raw, collapses out of domain (65 fits) | 10 | 10 |
| U41 exact laws (205 fits) | 166 | 174 |
| structure retrieved, U41N1 / U41N10 (205 fits each) | 113 / 98 | 121 / 95 |
| fits under units passing `check_dimensions` | 1,005 of 1,005 | 1,005 of 1,005 |
| fits under units, median time (s) | 30.2 | 30.2 |
| fits under units, longest (s) | 31.5 | 31.6 |
| frozen test set, deciding nothing: | | |
| TF78 exact laws (390 fits) | 213 | 214 |
| TS14 exact on the test rows (70 fits) | 8 | 8 |
| TR25 folds, median test R² | 0.7692 | 0.7692 |
| TF78 under units, exact laws (390 fits) | 229 | 228 |

**Criteria of the plan:** the eleven are met (`m2/compare.txt`).
- **The pool `physical`:** on the 706 fits where neither version reached its
  budget, the recorded formula, the error on the test rows and
  `formula_exact` are those of 1.2.0, to the bit. The bench records the first
  160 characters of a formula, so for the 5 of the 706 whose formula is
  longer, a prefix is compared; every other field of their records is
  identical too. The same recorded formula comes back in 2,234 of the 2,250
  fits. Two fits change status, each where 1.2.0 reached its budget:
  - Strogatz vdp1, seed 9, goes from missed to exact, where 1.2.0 reached its
    budget and 1.3.0 did not;
  - U41 I.6.20a, seed 4, goes from missed to near, where both reached it.
- **F41,** not more than 3 exact laws below 1.2.0: 163 and 171.
- **F41N1 and F41N10,** not more than 3 structures below: 108 and 116, 85
  and 87.
- **The R6 median** within 0.005: identical.
- **The collapses of R6 + R7raw** not above 1.2.0 plus 2: 10 and 10.
- **The two arcsine laws of F41** exact with the arcsine in at least 5 of
  10: 8. I.30.5 is exact in all five seeds, written `arcsin(v0 / (v1 * v2))`.
  I.26.2 is exact at seeds 1, 2 and 4, written `arcsin(v0 * sin(v1))` or an
  equal form.
- **U41,** not more than 3 exact laws below: 166 and 174. The two laws are
  exact with the arcsine in 8 fits of 10 here too.
- **U41N1 and U41N10,** not more than 3 structures below: 113 and 121, 98
  and 95.
- **Every model returned under units passes `check_dimensions`:** 1,005 of
  1,005.

**The pool `trig`, by suite** (`m2/compare.txt`, `m2/details.txt`):
- F41 and U41 gain the eight fits of the two arcsine laws and lose none;
- F41N1 and U41N1 gain the structure of I.26.2 and I.30.5 in 8 fits each;
- F41N10 gains 2 (III.15.12 and I.26.2, one fit each);
- U41N10 loses 3: I.18.12 loses 4, II.6.15b loses 1, and III.15.12 gains 2.

**I.18.12 with 10 % noise under units** was examined after M2
(`m2/examine/`). Its plan was committed at 14:47:08, and the first record
is dated 14:47:51. On twenty seeds never run in M2, each version keeps the
structure in 12 fits of 20. In 7 of its 8 other fits, 1.2.0 returns the same
parabola in θ that 1.3.0 returned at seeds 0 to 3 of M2. By
the reading written before, the fall of M2 is the draw of its five seeds.

**The printed formula.** `formula_exact` is False:
- with the pool `physical`, in 102 fits with each version;
- with the pool `trig`, in 82 of the 530 fits with 1.3.0, against 27 with
  1.2.0. At least 47 of the 82 have an arcsine. 77 of the 82 recorded
  formulas are cut at 160 characters, among them the 35 without an arcsine
  in their visible part.

The plan expected the printed formula to depart more often where the clip
of the arcsine acts. Whether the clip acts in a given fit is not recorded.
The pages of the limits say so (point 6).

**The formulas with the arcsine** are listed by suite in
`m2/arcsine_formulas.txt` (`m2/arcsine_formulas.py`, written after the first
review of M5, which found that `m2/compare.txt` gives their count only). The
recorded text has an arcsine in 105 fits of 1.3.0, a lower bound for the
same reason:
- 11 in F41, 18 in U41;
- 12 in F41N1, 17 in U41N1, 12 in F41N10, 8 in U41N10;
- 3 in TF78, 16 in TF78 under units, and 8 in TS14.

**The seeds of the arcsine** (`elementary_seed` and `tolerant_seed` in the
records). The exact seed was placed in the 10 fits of I.30.5 without noise,
in F41 and U41. The noise-tolerant seed was placed in 25 fits: I.30.5 in
F41N1, F41N10, U41N1 and U41N10, and feynman_test_1 of TF78, five seeds
each.

**The frozen test set** decides nothing and is published as measured:
- TF78: 213 and 214 exact laws, of which 15 and 16 on its 17 equations of
  the pool `trig`;
- its arccosine law, feynman_test_10: near at one seed with 1.2.0, and never
  near or exact with 1.3.0, without units or under units;
- TS14: 8 and 8 exact on the test rows. On its systems of the pool `trig`,
  8 of 60 fits change status, both ways, and the one exact fit of 1.2.0
  (glider1, seed 9) is missed with 1.3.0. Out of domain, 30 and 27
  collapses of 70;
- TR25: median 0.7692 and 0.7692;
- TF78 under units: 229 and 228 exact laws. feynman_III_8_54 goes from 2
  exact fits to 0 under units, and from 0 to 1 without.

## M3, every public figure measured again (9 November 2026)

`m3/` holds the records of the figures of the READMEs, the notebooks, the
case studies and the paper. They were produced by `m3/m3_driver.sh` with
`/venv13rx`, one step after the other, from 14:58 to 15:36, with nothing
else on the machine. The driver runs the steps of the M3 of 1.2 on a copy of
`benchmarks/`, `examples/` and the READMEs of commit a0935be, without the
package beside them. It runs one step more: the TP notebook four times,
1.2.0 (`/venv12bx`) and 1.3.0 in turn (`m3/tp_timing/notebook_pair/`). The
notebook is run as the script of its code cells without the `pip` line
(`m3/tp_six_lois.py`), which is the script of the M3 of 1.2 to the byte.

**Against the M3 of 1.2.** `m3_compare.py` compares each record with the one
of 5 November once times, dates, the paths of the environments and folders,
and the version numbers are masked (`m3_compare_1.2.0_vs_1.3.0.txt`). 57
records are the same: every law, formula, error, size and count. Among them:
- the Kepler, Hubble and Nikuradse case studies;
- Feynman 15 (15 of 15 exact) and Feynman 15 with `units=` (15 of 15);
- the duel with gplearn (15 of 15 against 6 of 15);
- the mystery constant, the examples of the README and the snippets of the
  notebooks but one;
- the deduced constant with 1.2.0.

The comparison lists five records as new. Among them is the deduced constant
with 1.3.0 (`m3/deduced_constant_venv13rx.txt`), which differs from the one
of 1.2.0 only by the line of the version. The other four are the machine and
the runs of the TP notebook with 1.3.0, below.

Nine records differ, for three causes:
- the pool `full`, two records;
- timing, five records;
- the driver itself, `m3_driver.sh` and its log, whose steps and dates
  differ.

**The pool `full`, which has the arcsine.** Two records use it:
- `kepler_minmax_check.txt`, Kepler's law normalised by min-max, ten seeds.
  Exact fits of 10, 1.3.0 then 1.2.0, without the noise-tolerant seeds (N1)
  and with them:
  - at 10 generations, 2 and 0 without N1, 0 and 0 with N1;
  - at 40 generations, 4 and 3 without N1, 2 and 1 with N1.

  Point 5 of the pages of the limits quotes it;
- `notebook_snippet_tp.txt`, parts 1 and 2 of
  `examples/tp_regression_symbolique.ipynb`, seed 0. With 1.3.0, the fit of
  part 1 returns a formula with the arcsine, which departs from `predict()`
  on 15 of 200 rows. The MSE of part 2 is 5.654e-02, 1.628e-02 and
  1.281e-03 at 10, 30 and 60 generations, against 9.706e-03, 1.784e-04 and
  1.784e-04.

The plan did not expect the second. It was examined after M3
(`m3/examine/`), on ten seeds. Its plan and scripts were committed at
16:21:31 (7fe0665). The run was started by the same command, after the push.
Its records carry no time, so they cannot show that order themselves.
- **The MSE:**
  at each budget, 1.3.0 has the higher MSE in 6, 8 and 7 seeds of 10. By the
  sign test of the notebook (p of 0.75, 0.11 and 0.34), no difference is
  shown.
- **The printed formula:** it departs in 1, 4 and 2 fits of 10 with 1.3.0,
  and 1, 1 and 1 with 1.2.0. 6 of the 7 of 1.3.0 have an arcsine. The search
  can use the clip, which makes the arcsine of the model flat at ±π/2 where
  its argument leaves [−1, 1], and the printed formula has no clip. Whether
  the clip is the cause in each of the six is not recorded.

The text of question 2 of the notebook ("from 30 to 60, nothing changes")
was brought to what 1.3.0 gives at seed 0. After the first review of M5,
question 1 also says what the warning means, since with 1.3.0 the formula of
part 1 departs from `predict()` on 15 of 200 rows.

**Timing:**
- the console example, run on three parallel islands: the order of the
  islands' prints and the statistics of the stigmergic memory. The final
  result is the same: `force = 250 * elongation`, constant 250 kg/s²;
- `time_limit_check.py`: 14 of 16 checks, against 13 of 16 on 5 November.
  The check of `GPEliteRegressor` with a budget of 6 s, which varied
  between runs of the same version in the M3 of 1.2, passes this time;
- the times of `import_time.txt`, `scaling.txt` and the log of the console.
  The five fits of `feynman_scaling.py`, with the same models, take 41 s at
  1,000 points and 113 s at 10,000, against 38 s and 103 s on 5 November.
  The exact law of `time_limit_check.py` comes back at 6.3 s in sequence and
  13.2 s in parallel, against 6.3 s and 12.5 s. These are two days, on
  hosts that may differ, so the times do not compare the versions.

**The TP notebook of the six laws.** The six fits return the formulas and
the deduced constants of 1.2.0, in the same times. The same day, one version
after the other, alone on the machine:

| fit | 1.2.0, run 1 / run 2 (s) | 1.3.0, run 1 / run 2 (s) |
|---|---|---|
| pendulum | 8 / 8 | 8 / 8 |
| spring | 11 / 11 | 11 / 11 |
| free fall | 8 / 9 | 8 / 8 |
| power | 8 / 8 | 8 / 8 |
| gas | 8 / 9 | 9 / 9 |
| illuminance | 7 / 7 | 7 / 7 |
| in all | 50 / 52 | 51 / 51 |

Every fit returns the same formula in the four runs. The notebook uses the
pool `physical`, which 1.3.0 leaves as it was.

The figures of the pages of the limits read from the records of M2 are
given with the documents.

## SRBench, a correction of the plan

The plan says, for gate 10, that the SRBench wrapper tries
`operators="full"`, so that once 1.3.0 is on PyPI, those runs would have the
arcsine. That holds for the grid as written, not for the grid as SRBench
reads it. The study of 1.1 (`../../results_1.1/srbench_settings/PLAN.md` and
`README.md`) found that `optimize_model.py` of SRBench 2025 reads the grid of
GP_ELITE as one configuration. So it tunes nothing and fits the default
estimator, `operators="physical"`, which 1.3.0 leaves as it was. With the
code of SRBench as read on 2 November 2026, 1.3.0 changes nothing there.
If the grid were written as intended, its configurations with `"full"`
would have the arcsine.

## M4, tests (9 November 2026)

`m4/summary.txt` gives the test suite of 695d2ff, run against the wheel of
5492296 by `m4/run.sh`. The wheel was installed in a fresh environment for
each of Python 3.9.25, 3.11.18 and 3.14.6, with the pins of the M4 of 1.2
(`m4/requirements_*.txt`), each importing the installed package. 182 tests
pass under the three versions, 13 of them new with the arcsine
(`tests/test_arcsin.py`). `twine check --strict` passes for the wheel and
the source archive (`m4/twine_check.txt`), whose SHA-256 are those of
`environments.txt`. The **Tests** workflow of the repository is green on
every commit of the branch since the candidate that it ran on
(`m4/ci_runs.txt`). It does not run on commits that change documents only,
three of them here. It is checked again on the commit of the release, and
the files handed over for PyPI, built again from that commit, are checked
again too.
