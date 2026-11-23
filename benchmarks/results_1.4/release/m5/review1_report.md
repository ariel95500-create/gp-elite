# M5 of 1.4.0, first review of the documents

## Summary

- **HEAD reviewed:** the review started on f0e37c9 and was completed on
  31bed58 (branch claude/peaceful-knuth-4q7m4p). Between the two, the
  documents of the scope are unchanged except the release README (parts b
  and c of the verification of L1) and the "Fixed" entry of the CHANGELOG;
  both were reviewed at 31bed58, with the new records of `l1/`.
- **Coverage:** about 380 statements of the documents of the scope were read
  against their records or against the code. About 150 figures were
  recomputed from the raw records (the jsonl of M2, TP and TPT10, the count
  of M4 and of L1, the txt and jsonl of M3 and of `l1/m3/`) by the scripts
  of `m5/review1/`. None of them imports gp_elite or runs a fit.
- **Main conclusion:** no error touches a figure that decides the release or
  a criterion of the plan. The eighteen criteria of PLAN_RELEASE_1.4.md,
  recomputed from the jsonl by code independent of `compare_m2_1.4.py`, are
  all met with the figures `m2/compare.txt` gives, and the release README
  reports them faithfully. Every figure of the tables of the README, the
  CHANGELOG, LIMITATIONS and the paper matches its record. The findings are
  about claims that say more than the records show (1, 2), descriptions of
  the noise-tolerant stage that the code does not bear out (3, 4), limits
  left incomplete (5, 6), and smaller stale or imprecise wording (7 to 13).

## Findings

**1. LIMITATIONS: "leaves the models alone where those seeds are the same" says more than the record**
- **Where:** LIMITATIONS.md lines 57-58, and LIMITATIONS.fr.md lines 62-63
  ("laisse les modèles tels quels là où ces graines sont les mêmes").
- **The record:** the release established identity only where no time budget
  was reached: 782 fits of 3,092 (`m2/compare.txt` line 46). The 2,428 fits
  with the same seeds include budget-bound fits, and these do not keep their
  models:
  - 60 of them return another recorded formula, each one at its time budget
    in at least one version;
  - 3 change status: F41 I.37.4 seed 3 (NEAR → MISS), TF78 feynman_I_13_4
    seed 5 (NEAR → MISS), and TF78 under units feynman_I_13_4 seed 9 (EXACT →
    NEAR).

  Recomputed by `m5/review1/m2_seeds_detail.py` and `m2_recompute.py`.
- **A related attribution on the same page:** the list that follows (lines
  64-73; FR 69-80) groups under "figures that move as they do from one
  campaign to the next" the Strogatz fits, 10 against 9, and the
  main/bonus split of TF78 (203/204, 11/10). Those moves come from 1.4's
  seeds, not from the noise between campaigns:
  - all 9 status changes of TS14 are fits where 1.4.0 places other seeds,
    among them the 6 on the test rows that make 10 against 9;
  - so are 13 of the 14 of TF78. Among them are the two fits behind "31 of
    its equations never recovered against 33", which the page puts in the
    other list.
- **Kind:** unsupported (it says more than the record), and an attribution
  the record contradicts.
- **Correction:** "…and, where those seeds are the same and neither version
  reaches its time budget (782 fits of the release measurement), returns
  the models of 1.3.0 to the bit". The CHANGELOG (lines 26-29) already says
  it this way. Then move the Strogatz and TF78 main/bonus figures to the
  first list, or say that they change on fits where 1.4.0 places other
  seeds.

**2. CHANGELOG "Fixed" (L1): "every public figure" and "no fit had such a column" overstate the verification**
- **Where:**
  - CHANGELOG.md lines 67-70 (at 31bed58): "No fit of the release measurement
    had such a column. The corrected engine returns what the measured one
    returned on its reference configurations, on the 800 fits of the TP
    diagnostic and its frozen set, and on every public figure, times aside";
  - release README lines 328-329: "no pass of N2b raises: all their inputs
    are positive". The same sentence is in the amendment, PLAN_RELEASE_1.4.md
    line 187.
- **The record, for the figures:** the figures of M2 are public figures:
  171, 152/95, 174, 150/93 and 1,161 in the README, the CHANGELOG, LIMITATIONS
  and the paper. The corrected engine did not produce them; the plan says
  "The benches of M2 are not run again". Part b ran each of the 3,892 fits
  for one generation only. It shows:
  - the noise-tolerant stage runs on the same fits as with the measured
    wheel;
  - no pass raises;
  - `l1/count_l1.jsonl` equals `m4/log_scan/count.jsonl` in 3,892 jobs of
    3,892 (recomputed, `m5/review1/l1_m3_check.py`).

  This supports "the measurements of M2 stand for it", as the release README
  says at the end of L1. It does not support "returns what the measured one
  returned". The identity "times aside" is measured for M1, TP and TPT10,
  and the records of M3 (`l1/m3_compare_release_vs_l1.txt`: 57 same, 4
  that differ by timing).
- **The record, for the inputs:**
  - the count records whether a pass raises, not the signs of the inputs;
  - "all their inputs are positive" is false as written: the standardised
    real datasets (R6, TR25; `decision_bench.py` lines 14-16) have negative
    values;
  - the scan only uses columns that keep one sign (`core.py` lines
    5379-5380), which is why their mixed-sign columns cannot raise.
- **Kind:** unsupported (says more than the record), and a reason stated
  wrongly.
- **Correction:** "…on its reference configurations, on the 800 fits of the
  TP diagnostic and its frozen set, and on the records of M3 (the examples,
  notebooks and case studies), times aside. On the 3,092 fits of the benches,
  run for one generation, its noise-tolerant stage runs where the measured
  one ran and no pass raises, so the measured figures stand." Also replace
  "No fit … had such a column" and "all their inputs are positive" with "no
  pass raised on any of the 3,892 fits".

**3. CHANGELOG: when the noise-tolerant stage runs, and the twelve seeds, described otherwise than the code does**
- **Where:**
  - CHANGELOG.md lines 5-6, "When no seed holds the data exactly, the engine
    places … the forms its finders give within 1.5 %";
  - line 42, "The stage runs wherever no exact seed is found";
  - lines 9-10, "up to twelve seeds. Every seed 1.3.0 placed is still
    placed"; also docs/features.md lines 7-10 and caracteristiques.md lines
    7-11.
- **The code, on when it runs:** the stage runs whenever neither the
  binomial finder nor the finder of functions of a monomial placed an exact
  seed. An exact power-law seed does not stop it:
  `_tol = [] if (_binom or _elem) else _make_tolerant_seeds(xs, ys, cfg,
  power_done=bool(_plaw))`, `gp_elite/core.py` lines 10268-10272.
- **The record:** `l1/count_l1.jsonl` shows the stage running on 125 of the
  205 F41 fits, which have no noise. Among them are 70 fits returned exact in
  one generation, every seed of I.12.1, I.12.5, I.14.4, I.39.1 and ten other
  monomials (`m5/review1/l1_m3_check.py`). The release README puts it
  correctly (lines 219-220): "wherever the exact finders of binomials and
  of functions of a monomial place no seed".
- **The code, on the twelve seeds:** twelve is a cap on the new forms only.
  `placed = old + new[:max(0, _TOLERANT_MAX - len(old))]` (`core.py` lines
  5696-5699) keeps every seed of 1.3.0, so more than twelve are placed where
  1.3.0 alone placed more. In M2, 1.3.0 placed at most 9 and 1.4.0 at most
  12 (recomputed).
- **Kind:** wording that misleads (description of behaviour), and
  inconsistent with the release README.
- **Correction:** "When no binomial form and no function of a monomial holds
  the data exactly (an exact power law does not stop it)…", and "up to
  twelve seeds, or more only where 1.3.0's own seeds already number more".

**4. `r2_validation` and `pareto` are None below 30 rows, where the README's own examples sit**
- **Where:**
  - README.md line 73, `print(result.r2_validation)    # its score on rows
    held out of the search`, and README.fr.md line 72;
  - docs/usage.md lines 179-184, `r2_validation` "is a selection score" on
    the hold-out and `result.pareto` "lists the other non-dominated
    candidates"; docs/fr/utilisation.md lines 199-204;
  - related: docs/measurements.md line 19 (mesures.md line 19), "Held-out
    validation: built in".
- **The code:**
  - below 30 rows no rows are held out (`core.py` lines 9626-9629);
  - `r2_validation` stays None (`api.py` lines 953-958);
  - `pareto` is None (`api.py` line 1020; S1 is off).
- **Why it matters:** the README presents GP_ELITE as "built for small
  experimental tables". Its Kepler example has 8 rows and every TP table has
  10 to 20, so the commented line prints `None` for them. DIAGNOSTIC_TP.md
  (lines 131-133) and the TP notebook (section 10) say it; the README and the
  usage page do not.
- **Kind:** wording that misleads.
- **Correction:** add "(None below 30 rows, where none are held out)" to the
  README comment, in both languages, and one sentence under "Reading the
  result" in usage.md and utilisation.md.

**5. LIMITATIONS point 5 misses the measured instance 1.4 adds**
- **Where:** LIMITATIONS.md lines 152-161, LIMITATIONS.fr.md lines 166-177:
  "a seed that only approximates the data can draw the search away from the
  law".
- **The record:** 1.4's added seeds give a new instance on data without
  noise. In the check of `time_limit=` in sequence (3,000 rows of x0·x1/x2 +
  0.3·x3), the stage places 4 seeds against 1, and 1.4.0 runs to its budget
  and returns an approximation of R² 0.9979 at 15.3 s. 1.3.0 returned the
  law at 6.3 s (`m3/time_limit_check.txt`,
  `results_1.3/release/m3/time_limit_check.txt`,
  `m3_examine/seeds_compare.txt`). The CHANGELOG reports it (lines 47-49);
  the page of the limits does not, and point 5 still ends on 1.3.0's min-max
  figure. 1.4.0 gives the same 2 of 10 against 4 there
  (`m3/kepler_minmax_check.txt`, identical to 1.3's).
- **Kind:** stale or incomplete.
- **Correction:** one sentence for 1.4. Its stage places more forms on exact
  data too: the check of `time_limit=` in sequence loses its law, while
  I.16.6 in the scaling bench, the wide-range case of the robustness check
  and the exponential of the small-data check gain. Also add "1.4.0 gives the
  same" for the min-max check.

**6. The point source, "14 fits of 20 against 18", without its arm**
- **Where:** CHANGELOG.md lines 72-75 (Known limits); LIMITATIONS.md lines
  132-137; LIMITATIONS.fr.md lines 144-150.
- **The record:** the point source has 40 fits on TP. The fall from 18 to 14
  is in the plain arm; under units it keeps 20 of 20 with both versions
  (`m2/compare.txt` line 105). The release README (line 130) and
  DIAGNOSTIC_TP.md (line 255) name the arm; these three passages do not.
- **Kind:** wording that misleads (minor).
- **Correction:** "without units, the law came back in 14 of its 20 fits
  against 18 (under units, 20 of 20 with both)".

**7. A figure of 1.0.0 still given as current: the parallel islands' "approximation of R² 0.99998"**
- **Where:** docs/usage.md lines 144-146; docs/fr/utilisation.md lines
  157-159.
- **The record:** this was measured once, for 1.0.0
  (`results_0.9/release_1.0/m3_extra/parallel_islands/`). The second review
  of 1.1 (`results_1.1/release/m5/review2_report.md` lines 389-392) already
  noted that it was not measured again. The M3 of 1.4 runs the examples with
  the islands in sequence (`release_claims/run_claims.py` lines 17-19), and
  the noise-tolerant stage, which 1.4 changes, runs on exact data such as
  this example's.
- **Kind:** stale (not measured for 1.4).
- **Correction:** "(measured with 1.0.0)", or measure it again.

**8. Release README: five smaller inaccuracies or omissions**
(`benchmarks/results_1.4/release/README.md`)

- **a. Lines 34-37 (M1):** "Run again with each version to read its trace,
  1.4.0 places twelve noise-tolerant seeds there, the six of 1.3.0 among
  them, where 1.3.0 places six." No record of that run is in the repository:
  the `M1_equiv_*/C_big.json` files hold no trace, and no other file names
  C_big. The figures fit the code (6 + 6 = the cap of 12), but they are
  unrecorded. Commit the trace, or say that it was read and not kept.
- **b. Line 127:** "Neither version places one on R6, R7raw or TR25." This is
  true, but it leaves out TR25raw, the one suite of real data where seeds
  are placed: in 7 fits with both versions. In 5 of them (four folds of
  first_principles_planck, one of 1096_FacultySalaries), 1.4.0 places other
  seeds and returns another formula; the test R² moves by at most 0.006
  (`m2_seeds_detail.py`). Add it.
- **c. Lines 120-122:** the gains at 10 % noise are listed as I.32.5, I.44.4
  and III.19.51. II.11.27 under units also goes from 0 to 1
  (`m2/compare.txt` line 98).
- **d. Lines 245-250 (small-data check):** "At search seeds 2 and 3, 1.4.0
  returns the law as written … size 8, where 1.3.0 returned two longer
  forms …, sizes 10 and 13". The record moves at seed 1 too: the same
  printed formula, size 9 with 1.3.0 and 8 with 1.4.0
  (`m3/small_data_release.jsonl` against
  `results_1.3/release/m3/small_data_release.jsonl`). Say "at seeds 1 to 3,
  size 8 against 9, 10 and 13".
- **e. Lines 131-132 and 142-144, and DIAGNOSTIC_TP.md lines 259-260:**
  "every other experiment moves by one fit at most" and "By experiment, at
  most 2 fits move" are net counts. Per fit:
  - in TPT10, 10 fits change (5 lose the law, 5 gain it), Kepler's third law
    in 3 of them (2 lost, 1 gained);
  - in TP, 9 fits change (6 lost, 3 gained), the thin lens 2 (1 and 1).

  Recomputed by `m2_recompute.py`. Say "the count moves by at most 1 (2)".

**9. The quick-start notebooks describe the short README by its old content**
- **Where:** examples/quickstart.ipynb cell 17 and quickstart.fr.ipynb cell
  18, "Going further": "README — robust mode, Pareto front, extrapolation,
  dimensional audit" ("mode robuste, front de Pareto, extrapolation, audit
  dimensionnel").
- **What is wrong:**
  - since 1.4 the README holds none of these; they are in
    `docs/robust.md`, `docs/usage.md`, `docs/units.md` and
    `docs/features.md`;
  - the French notebook also points to the English README.
- **Kind:** stale.
- **Correction:** point to the "Documentation" list of the README, or to the
  pages of `docs/` (`docs/fr/` in French).

**10. README: "Every change to the search is decided by a comparison written before it runs"**
- **Where:** README.md lines 46-48; README.fr.md lines 45-47.
- **The record:**
  - docs/measurements.md lines 27-28 and 40-42 restrict it to "a change
    meant to improve the search or the final selection", and add that
    "corrections of defects are not decided this way";
  - 1.4 itself carries one: L1 changes the noise-tolerant stage, was decided
    by the author, and was then verified (PLAN_RELEASE_1.4.md, "Correction
    L1 after M4").
- **Kind:** inconsistent between documents.
- **Correction:** "Every change meant to improve the search is decided by…".

**11. French features page: "ce README"**
- **Where:** docs/fr/caracteristiques.md line 110: "Chaque banc derrière un
  chiffre de ce README".
- **What is wrong:** the page is no longer the README. The English page says
  "a number here" (docs/features.md line 102).
- **Kind:** the French differs from the English (stale).
- **Correction:** "de cette page".

**12. The paper keeps the date of 1.3.0**
- **Where:** paper/paper.md line 17, `date: 10 November 2026`.
- **What is wrong:** the paper now quotes 1.4.0 figures measured from 13 to
  17 November.
- **Kind:** stale. It is probably meant to be set at gate 12, with the
  version's date; listed so that it is not forgotten.

**13. The TP notebook's times: 1.4.0 has four runs, not two**
- **Where:** docs/usage.md lines 108-110 (utilisation.md lines 117-118):
  "with 1.4.0, in its release measurement, they take 52 to 53 s".
- **The record:** the release measurement has two more runs of the six fits
  with this engine: the driver's at 51 s (`m3/notebook_tp_six_lois_1.4.0.txt`)
  and part c of L1 at 50 s (`l1/m3/notebook_tp_six_lois_1.4.0.txt`). The
  52 and 53 s are the paired runs.
- **Kind:** imprecise (minor).
- **Correction:** "52 and 53 s in the paired runs (50 to 53 s over its four
  runs)".
- **Optional, beside it:** examples/tp_six_lois.ipynb still quotes its run
  with 1.2.0 (cell 0: "de 7 à 10 s"; cell 10: the spring in 10 s). That is
  correct as labelled, but M3 shows 1.4.0 returning the same six formulas
  and constants, with the spring at 10 to 11 s. One line, "les mêmes
  formules avec la 1.4.0", would follow the plan's "where their figures
  move".

## Notes, not findings

- **The M3 script and the short README:** `release_claims/run_claims.py`
  takes the usage example from README.md after "### Programmatically"
  (lines 37-39 and 74-75). That section moved to docs/usage.md in a82a292,
  so the M3 of the next release cannot take it from README.md. The records
  of 1.4 are not affected: M3 and part c of L1 ran on copies of fbe9b00 and
  ec44e8e, before the move.
- **The source of the LAPACK messages in M4:** the release README (lines
  305-310) gives `check_positive_only_tag_during_fit` as their source. No
  file of `m4/` records it. It is consistent, though: tests/test_gp_elite.py
  lines 254-260 run `check_estimator`, and the messages disappear with L1
  (`l1/m4_summary.txt`).
- **CITATION.cff**, outside the scope: version 1.4.0 with
  `date-released: 2026-11-10`. Left to gate 12.

## Checked and found right

**README.md and README.fr.md**
- The Kepler snippet and its printed formula (`m3/readme_kepler.txt`).
- Every cell of the table of the release measurement (`m2/compare.txt`,
  recomputed).
- 15 exact laws against 6 for gplearn (`m3/duel_gplearn.txt`).
- "four changes measured, three not adopted" (PLAN.md).
- Python 3.9 to 3.14 (pyproject classifiers; M4 under 3.9, 3.11 and 3.14).
- Mode 6 of the console (`core.py` line 11912).
- Every link resolves in the working tree (`m5/review1/links.py`).
- The French says the same as the English, figure for figure
  (`m5/review1/fr_en_numbers.py`).

**docs/usage.md and docs/fr/utilisation.md**
- The usage example: formula, 1.0, 33 nodes (`m3/usage_example.txt`).
- The 2,291 fits at their budget, 30.5 s at the median and 31.9 s at most
  (recomputed: 30.49 and 31.88).
- The check of `time_limit=` (9.7 s in parallel; 15.3 s and R² 0.9979 in
  sequence; 6.3 s with 1.3.0).
- The console output on Hooke's law (`m3/console_hooke.txt`).
- The presets: 'thorough' with population 400, four islands and 200
  generations, twice the default of 100 (`core.py` lines 11574-11583,
  `api.py` line 668).
- The patience stop does not act on GPEliteRegressor (`sklearn_api.py`
  lines 89-97).
- The guards: the base clipped to [−100, 100], the exponent to [−6, 6], the
  value to 1e6, and a denominator within 1e-8 of zero (`core.py` lines
  2670-2671 and 2747-2778).
- `parallel=None` turns the islands on from four cores, and the workers start
  with `spawn` (`core.py` lines 8382-8392 and 8413).
- The CI matrix (`.github/workflows/tests.yml`).
- The rewriting of the exponential: 0.00614708^(0.2·t) = exp(−t/0.981975),
  checked by hand.

**docs/units.md and docs/fr/unites.md**
- The II.11.3 table (`m3/units_ab_ood.txt`).
- 174 and 171 with 1.4 (M2).
- The table of the deduced constants and the printed constants
  (`m3/mystery_constant.txt`).

**docs/robust.md and docs/fr/robuste.md**
- The table and the formulas (`m3/robust_example.txt`), and "six-fold"
  (1.398 / 0.237 = 5.9).

**docs/examples.md and docs/fr/exemples.md**
- The printed block (`m3/battery_example.txt`), −3.81 against +0.16, and the
  168 cycles of the CSV.
- The cause given: the script is deterministic (`generations=60,
  parallel=False`), and 1.4.0 places other seeds there
  (`m3_examine/seeds_compare.txt`).

**docs/measurements.md and docs/fr/mesures.md**
- The size study (`m3/scaling.txt`):
  - I.16.6 exact in 10 of 17 fits, 6 of the 13 below 1,000 points, in other
    forms at 200 and 5,000 points;
  - the five fits take 40.3 s at 1,000 points and 99.8 s at 10,000.
- The frozen sets: 214, 228, and 10 against 9 Strogatz fits; TF78N, 37/28
  against 34/27, and 37/33 against 35/32.
- Feynman 15, 15 of 15.
- The duel with gplearn: 15 against 6 exact, 15 against 7 within 1e-3, ahead
  on 9 and tied on 6.
- Under units, 15 of 15, 14 in their textbook form, with a factor 1.00755
  (1.00758 with 1.3) (`m3/feynman15_units.jsonl`).

**docs/features.md and docs/fr/caracteristiques.md**
- The v1.4 bullet against `core.py` lines 5508-5545 and 5609-5709 (finding 3
  aside).
- The figures of "What's new" for 1.4.

**CHANGELOG, the 1.4.0 entry**
- All the figures of lines 12-49:
  - from M2, recomputed, the 782 fits included ("most often none": 757 of
    782);
  - from campaign N2b, 247/203, and 192/156 of 328;
  - from M3, I.16.6 in 10 fits of 17 against 9, the case of the robustness
    check, and the check of `time_limit=`.
- Known limits:
  - I.27.6 and III.15.12, by equation;
  - every fit that loses the structure has other seeds (`m2_seeds_detail.py`);
  - the battery example.
- The changes switched off: `_SMALL_CV`, `_E2_SEEDS` and `_TOLERANT_REFIT`
  are False (`core.py` lines 9240, 5241 and 5544).
- W1: the text of the warning (`api.py` lines 999-1008).
- The description of L1 against `git show ec44e8e` and
  `m4/log_scan/negative.txt` (11 cases of 12, 114 messages).

**LIMITATIONS.md and LIMITATIONS.fr.md**
- Every figure of the 1.4 paragraphs against `m2/limits_figures.txt`, and
  recomputed:
  - 31 against 33 equations never recovered;
  - 203/204 and 11/10 in TF78;
  - 10 against 9 Strogatz fits;
  - 10 collapses, the worst at −1,946, and 66 = 38 + 28;
  - 11 against 12 departing formulas of 130, and 65 against 68 of 500;
  - 174, and four equations never recovered.
- Point 3:
  - the formula of I.34.1 is still the one both versions return, at all five
    seeds;
  - the point source: 4 fits lost and none gained, and in each of the four
    1.4.0's training error is lower (`m2_recompute.py`), which supports
    "follows the noise more closely".
- Point 11: S1, 113 against 126 and 1.67 times the time; E2, 18, 11, 7
  against 3, and 18 → 15; N2, I.26.2 from 3 to 0 (each against its campaign
  README).
- Point 12.

**paper/paper.md**
- 247 against 203.
- 15/15 against 6/15, and the budgets of the duel (`duel.py`; the 'fast'
  preset is population 400).
- 174, and 1,161.
- 214, 10 against 9, and 228.
- TF78N, 65 of 156 against 61.
- Kepler within 0.002 % (`m3/case_kepler.txt`, −1.64e-05).
- The deduced constants.
- The three dependencies (pyproject).

**Notebooks**
- tp_six_lois:
  - the six formulas and constants are those of 1.4.0 in M3 and in part c of
    L1;
  - 120 of 120 in the units arm (the six experiments, 20 of 20 each in M2);
  - the capacitor discharge without units at 10 points, 4 of 5 (recomputed
    for 1.4.0).
- tp_regression_symbolique, question 2: the MSE falls, and the size goes
  38 → 46 → 43 (`m3/notebook_snippet_tp.txt`).
- The quick starts:
  - Kepler and Hooke (`notebook_snippet_kepler30.txt`,
    `notebook_snippet_hooke.txt`);
  - every Nikuradse figure (`m3/nikuradse_full.txt`,
    `notebook_snippet_nikuradse.txt`).

**Case studies**
- Kepler: 5.43909e-10, +0.55 %, 5.45416e-10, −0.0016 %, 0.043 %, 0.27 to
  0.28 %, and the C8 and C4 formulas. The record is the same as 1.3's,
  seeds and times aside.
- Hubble: every figure; no noise-tolerant seed is placed there.
- Nikuradse, sections 4 and 5, recomputed by `nikuradse_case.py`:
  - the front starts with the same six-node form;
  - forms of 7 to 9 nodes;
  - the champion has 48 to 70 nodes and R² 0.980 to 0.995;
  - 10 to 13 forms per seed, with level gaps from −1.20 to +0.88 and the
    best between 0.014 and 0.225;
  - two forms of seed 0, at 52 and 59 nodes, beat the textbook relation.

**The release README**
- M1: the comparison files, and 21.8, 21.5 and 26.2 s.
- M2:
  - the table, recomputed;
  - the eighteen criteria, recomputed;
  - 2,428 fits with the same seeds, "none in most" (2,125 of them), and 782
    of them without a budget reached;
  - the 400 TP models are those of campaign N2b;
  - the seeds placed, 165/140, 130/95, 125/95 and 115/85;
  - TPT10 "useful" in 173 fits against 169;
  - the chronology: `compare_m2_1.4.py` was committed at 20:45:58, before
    M2 started at 20:46, and f6a36cd is 227d837 plus the version, the
    CHANGELOG and one comment.
- M3:
  - 44 same, 22 that differ and 4 new, and the six causes add up to 22;
  - in the scaling bench, the 6 fits of I.16.6 that differ are exactly the
    6 with other seeds;
  - the Kepler and Hubble records are the same, seeds and times aside, and
    C8 places 10 seeds against 5;
  - the times, 40/100 s against 41/113 s;
  - the notebook table, 49/54 and 52/53 s, and the driver's run at 51 s.
- M4: 199 tests passed, six DLASCL lines under 3.9 and 3.11, twine, the
  count (3,562 = 2,762 + 800), and the negative cases (11 of 12, 114
  messages).
- L1:
  - two lines in `_elem_log_scan`, and `core.py` is the only file that
    differs from f6a36cd;
  - the environments;
  - part a: M1 identical, the 800 TP and TPT10 models identical, 0 of 24
    negative cases raise, 200 tests under three versions of Python, and
    LAPACK prints nothing;
  - part b: `count_l1.txt` is `count.txt` to the byte, and the jsonl are
    equal job by job;
  - part c: 57 same, 4 that differ by timing only, and 2 compared outside
    the repository.

**DIAGNOSTIC_TP.md, the note for 1.4**
- 123 against 126, and 120 against 120.
- The point source, 18 → 14: 4 fits lost and none gained.
- Snell's law, none.
- TPT10, 107 and 103.

## Scripts of this review (`benchmarks/results_1.4/release/m5/review1/`)

- `m2_recompute.py`: the indicators of M2, the criteria, the figures of the
  limits, the seeds kept and their number, the structures by equation, and
  TP and TPT10 by experiment, with the fits lost and gained.
- `m2_seeds_detail.py`: the same-seed fits, the status changes against the
  seeds, the seeds by suite, TR25raw, the losses at 10 % noise, and U41
  between campaign N2b and M2.
- `l1_m3_check.py`: the count of L1 against that of M4, where the stage runs,
  the counts of the two comparisons of M3, the small-data check, the scaling
  bench, and the six fits of the TP notebook in each run.
- `nikuradse_case.py`: the figures of the Nikuradse case study.
- `links.py`: the links and paths of the documents.
- `fr_en_numbers.py`: the numbers of each English page against its French
  version.
- `dump_notebook.py`: the cells of a notebook as text.
