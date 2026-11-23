# M5 of 1.4.0, second review

## Summary

- **Reviewed:** HEAD d0051ea of branch claude/peaceful-knuth-4q7m4p. The
  documents and records are as committed there. The engine at HEAD is that
  of ec44e8e (the corrected wheel): `git diff ec44e8e d0051ea -- gp_elite/ tests/`
  is empty.
- **The repository moved during the review.** When I finished, HEAD was
  1d70d64 (18 November). I looked only at its list of files, not at its
  message. It adds the scripts of this review and one record,
  `m4/ci_runs.txt`, and changes none of the documents reviewed:
  `git diff d0051ea 1d70d64` on them is empty. Finding 9 takes the new
  record into account.
- **Done independently.** I did not read the first review
  (`M5_review1.md`, `m5/review1_report.md`, `m5/review1/`) or the message of
  HEAD. One disclosure: early on, a `grep` across the release folder printed
  a single line of `M5_review1.md` (line 56) before I excluded the file. That
  line names the source of the LAPACK messages of M4 as one of its topics.
  Finding 11 (b) touches the same sentence; I reached it from the records
  alone.
- **Scale:** about 240 claims and figures checked. About 150 of them were
  recomputed from the records (jsonl, txt) by the scripts in
  `m5/review2/` (list at the end). None of the scripts imports gp_elite or
  runs a fit; they run under the system `python3 -I`.
- **Main conclusion: no error touches a figure that decides the release, or
  a criterion of the plan.**
  - The eighteen criteria of `PLAN_RELEASE_1.4.md` were recomputed from
    `m2/campaignR_*.jsonl` and `m2/tp*_*.jsonl` with code of my own. All
    eighteen are met, with the values printed in `m2/compare.txt`.
  - `compare_m2_1.4.py` implements each criterion as the plan words it, and
    it was committed (20:45:58) before M2 started (20:46).
  - The README table, the list of the CHANGELOG, the figures of the limits
    pages and of the paper, and the records of the L1 verification all agree
    with the records. In particular, TP and TPT10 are identical on every
    field but time, date and engine path, and the count is identical job by
    job.
- **What the findings are:** sentences that say more than the records show,
  one time range that cannot be traced, one incomplete list, and two items
  of the plan that are not reported. The French pages give the same figures
  as the English ones.

## Findings (most important first)

### 1. CHANGELOG: "No pass of the scan raised on any fit of the release measurement"

- **Where:** `CHANGELOG.md:68`, and in the same spirit
  `benchmarks/results_1.4/release/README.md:339-340`.
- **As written:** "No pass of the scan raised on any fit of the release
  measurement." The release README has: "...and no pass of N2b raises. The
  fault touched no fit of the measurements."
- **What the records show:**
  - The same CHANGELOG paragraph begins "Found by the release measurement"
    (line 63).
  - The fault was found because the scan raised in M4, during fits run by
    the test suite. `m4/pytest_3.9.25.txt` and `m4/pytest_3.11.18.txt` each
    hold six "On entry to DLASCL" lines, and release README:316-321 explains
    them that way.
  - The record behind "no pass raised" is `m4/log_scan/count.txt` (the same,
    byte for byte, as `l1/count_l1.txt`). It covers only the 3,892 fits of
    M2, TP and TPT10, run again for one generation.
  - The fits of M3 were not counted. The only evidence for them is
    indirect: no DLASCL line in any record of `m3/` or `l1/m3/`.
- **Kind:** wording that misleads (it contradicts the sentence that
  introduces it), and unsupported beyond the 3,892 fits.
- **Suggested correction:** "No pass of the scan raised on the 3,892 fits of
  the benches, TP and TPT10 of the release measurement, run again for one
  generation. One did in the test suite (M4), which is how the fault was
  found." In the release README: "The fault touched none of these fits."

### 2. LIMITATIONS point 5: "one figure loses its law that way"

- **Where:** `LIMITATIONS.md:167-172` (`LIMITATIONS.fr.md:185-190`).
- **As written:** "Since 1.4 the noise-tolerant stage places more forms on
  exact data too ... In the release measurement of 1.4.0, one figure loses
  its law that way: [the check of time_limit=] ... Three come out better."
- **What the records show:** "one" holds for the public figures of M3 only.
  - In M2 (`m2/campaignR_*.jsonl`), on the exact data of the frozen test
    set, 4 fits lose their exact law where 1.4.0 places other seeds:
    - TF78 `feynman_III_4_32` seed 5 and `feynman_III_4_33` seed 8, EXACT to
      NEAR;
    - TS14 `strogatz_lv1` test seeds 5 and 6, EXACT to MISS.
  - In all four, 1.3.0 had not reached its budget.
  - 6 fits gain an exact law, all where 1.4.0 places other seeds
    (`review2/extra_checks.py`, item 3).
  - The introduction of the page gives the net counts and says that the
    status changes come, but one, from other seeds. Point 5 is the place
    that describes the effect on exact data, and it says "one".
- **Kind:** wording that misleads (a count that holds for M3 is given for
  the whole release measurement).
- **Suggested correction:** "Among the public figures measured again (M3),
  one loses its law that way ... On the frozen test set of M2 the stage also
  costs 4 exact fits (TF78 2, TS14 2) and brings 6, all where 1.4.0 places
  other seeds." The same in French.

### 3. "50 to 53 s over the four runs of 1.4.0"

- **Where:** `docs/usage.md:108-111` (`docs/fr/utilisation.md:117-119`).
- **As written:** "...they take 52 and 53 s in the two runs paired with
  1.3.0 the same day, against 49 and 54 s, with the same formulas (50 to 53 s
  over the four runs of 1.4.0)."
- **What the records show:**
  - M3 ran the notebook three times with 1.4.0, all on 14 November:
    - the run of the driver, 51 s (`m3/notebook_tp_six_lois_1.4.0.txt`);
    - the two runs of the pair, 52 s and 53 s (`m3/tp_timing/notebook_pair/`).
  - The only 1.4.0 run of 50 s is the corrected wheel in part c of L1, on
    17 November (`l1/m3/notebook_tp_six_lois_1.4.0.txt`;
    `review2/extra_checks.py`, item 1).
  - The release README never gives that 50 s. Its "four runs" (line 301)
    are the two runs of 1.3.0 and the two of 1.4.0.
  - So the range mixes two days and two wheels, against the rule stated in
    release README:5-7.
- **Kind:** a figure that cannot be traced, and inconsistent with the
  release README.
- **Suggested correction:** "(51 to 53 s over the three runs of 1.4.0 that
  day)". If the 50 s stays, name it: "and 50 s with the corrected wheel on
  17 November, `benchmarks/results_1.4/release/l1/m3/`". The same in French.

### 4. LIMITATIONS point 3: "two equations lose their structure ... the new seeds take the search elsewhere"

- **Where:** `LIMITATIONS.md:131-133` (`LIMITATIONS.fr.md:145-147`).
- **As written:** "at 10 % noise, two equations lose their structure: ...
  III.15.12 from 5 to 2 and from 5 to 1; the new seeds take the search
  elsewhere".
- **What the records show:**
  - III.15.12 keeps the structure in 2 fits of 5, and 1 of 5 under units.
    `CHANGELOG.md:82-84` words it correctly: "lose fits with the structure
    of the law".
  - The cause is inferred, not examined. No record runs these 20 fits with
    the seeds of 1.3.0, and all 20 are at their 30 s budget in both
    versions.
  - What the records do show (`m2/campaignR_*.jsonl`,
    `review2/m2_recount.py`):
    - 1.4.0 places other seeds in all 20 fits: on I.27.6, one seed where
      1.3.0 places none; on III.15.12, three against one;
    - campaign N2b gave the same four counts (`n2b/campaign/compare_n2b.txt`).
- **Kind:** wording that says more than the record (overstated, and a cause
  asserted but not measured).
- **Suggested correction:** "two equations lose fits with the structure ...;
  in all twenty of these fits 1.4.0 places other seeds, and campaign N2b
  gave the same counts. That is the likely cause; it was not examined."

### 5. DIAGNOSTIC_TP note: "the final choice ..., not the seeds, decides"

- **Where:** `benchmarks/results_1.1/DIAGNOSTIC_TP.md:267-271`.
- **As written:** "Both found the same cause: on 10 or 20 noisy points, the
  final choice among the forms of the search, not the seeds, decides
  whether the law comes back."
- **What the records show:** the claim contradicts the note itself and the
  campaigns.
  - The note's own first bullet (lines 255-259) says the new seeds of N2b
    move the search and cost the point source 4 fits (18 to 14,
    `n2b/campaign/examine/`).
  - Campaign E2 found its seeds took the point source from 18 to 15
    (`e2/campaign/README.md`).
  - What the campaigns found is that a seed with the structure of the law
    is not enough:
    - E2 placed the structure of the law in 18 fits, and the law came back
      in 7;
    - S1's cross-validation chose structures the search had found.
- **Kind:** wording that misleads (overstated, and inconsistent within the
  note).
- **Suggested correction:** "...a seed with the structure of the law does
  not make the search keep it: the final choice among the forms of the
  search decides whether the law comes back". This is how LIMITATIONS
  point 3 and the CHANGELOG put it.

### 6. LIMITATIONS: "it returns the models of 1.3.0 to the bit"

- **Where:** `LIMITATIONS.md:57-59` (`LIMITATIONS.fr.md:62-65`).
- **As written:** "Where those seeds are the same in both versions and
  neither reaches its time budget, it returns the models of 1.3.0 to the bit
  (782 fits of the release measurement)."
- **What the records show:**
  - `compare_m2_1.4.py` compares three things: the recorded formula, the
    error on the test rows, and `formula_exact`. It does not compare the
    models.
  - The record keeps only the first 160 characters of a formula
    (`benchmarks/phase1_bench.py:286`).
  - 3 of the 782 recorded formulas are cut: utf `feynman_II_11_28` seeds 7
    and 8, and `feynman_I_13_4` seed 7 (`review2/extra_checks.py`, item 4).
  - `CHANGELOG.md:27-30` and release README:100-103 say only what was
    recorded.
- **Kind:** wording that says more than the record (an identity claimed
  beyond what was compared).
- **Suggested correction:** "the recorded formula, the error on the test rows
  and `formula_exact` are those of 1.3.0, to the bit (782 fits ...)".

### 7. Release README: what the examination of M3 covers

- **Where:** `benchmarks/results_1.4/release/README.md:231-237`.
- **As written:** "`m3_examine/seeds.py` ... builds the data of every fit of
  those five scripts and of the battery example as M3 does ... Every fit
  whose record moved is one where 1.4.0 places other noise-tolerant seeds".
- **What the records show:** `seeds.py` builds 111 fits
  (`m3_examine/seeds_1.4.0.jsonl`; `review2/extra_checks.py`, item 7):

  | script | fits examined |
  |---|---|
  | scaling bench | all 85 |
  | small-data check | all 20 |
  | `feynman_units.py` | 1 of 15 equations (I.16.6) |
  | `robustness_check.py` | 1 of 16 cases |
  | `time_limit_check.py` | 3 data sets |
  | `examples/battery_soh.py` | the forward split only |

  - The random split of the battery moved too (+0.993 to +0.992,
    `m3/battery_example.txt`), and its seeds were not recorded. So the
    sentence "every fit whose record moved ..." is not shown for that fit.
  - For the fits examined, the conclusion holds. I checked that the 6 fits
    of the scaling bench that return another model are exactly the 6 with
    other seeds (`review2/m3_records.py`).
- **Kind:** unsupported (the coverage is overstated, and one moved fit was
  not examined).
- **Suggested correction:** state the coverage as it is: the 85 fits of the
  scaling bench, the 20 of the small-data check, I.16.6 under units, the
  case of a wide range, the three data sets of the check of `time_limit=`,
  and the forward split of the battery. Then either examine the random
  split or say it was not examined.

### 8. Release README: the equations whose structures move

- **Where:** `benchmarks/results_1.4/release/README.md:122-127`.
- **As written:** "gains ... and at 10 % on I.32.5, I.44.4 and III.19.51, and
  under units on II.11.27 (0 → 1)".
- **What the records show:** `m2/compare.txt` and
  `review2/m2_recount.py` give, under units at 10 % noise (U41N10):
  - I.44.4 gains as well, 0 to 5;
  - I.32.5 and III.19.51 do not move there (5 to 5).

  From the list as written, U41N10 cannot be brought to 95 → 93.
- **Kind:** incomplete list.
- **Suggested correction:** "...and at 10 % on I.32.5, I.44.4 and III.19.51
  without units, and on I.44.4 (0 → 5) and II.11.27 (0 → 1) under units".

### 9. M4 of the plan: the Tests workflow is not reported

- **Where:** `benchmarks/results_1.4/release/README.md:305-321`, against
  `benchmarks/results_1.4/PLAN_RELEASE_1.4.md:160-164`.
- **The plan:** M4 includes "the **Tests** workflow green on the commit of
  the release".
- **What the release README says:** it reports the test suite under Python
  3.9, 3.11 and 3.14 and `twine check`. It says nothing about the workflow,
  either as done or as left for the pull request.
- **The record now exists.** `m4/ci_runs.txt` was added in 1d70d64, after
  this review started. It records the Tests workflow green on f6a36cd (the
  measured wheel), on ec44e8e (the correction L1) and on every commit up to
  d0051ea, apart from two that change only documents. The release README
  neither reports nor cites it.
- **Kind:** omission (an item of the plan that is not reported).
- **Suggested correction:** add one line to the section on M4 that cites
  `m4/ci_runs.txt`. Add that the run on the commit of the release itself
  comes with the pull request.

### 10. Release README: "on every check of the amendment"

- **Where:** `benchmarks/results_1.4/release/README.md:405-407`.
- **As written:** "The verification holds: on every check of the
  amendment, the corrected engine gives what the measured release gave,
  times aside."
- **What the records show:** on the check of the cases with a negative
  column, the corrected engine does not give what the measured release
  gave, and it is not meant to.
  - The measured wheel raised in 11 cases of 12, and LAPACK printed 114
    messages (`m4/log_scan/negative.txt`).
  - The corrected wheel raises in none (`l1/negative_l1.txt`).
- **Kind:** wording that misleads (a minor slip).
- **Suggested correction:** "...the corrected engine gives what the
  amendment expects: what the measured release gave, times aside, and, on
  the cases with a negative column, no pass that raises."

### 11. Release README: three statements that no record in the repository shows

- **Where:** `benchmarks/results_1.4/release/README.md:155-157`, `316-321`
  and `401-403`.
- **(a) `m2/limits_figures.txt`.** No script in the 1.4 folder writes it.
  The M2 of 1.3 has `m2/limits_figures.py`, which reads the version from
  the records. I recomputed every line of the table with
  `review2/limits_recount.py` and `review2/m2_recount.py`, and every line
  agrees.
- **(b) The source of the LAPACK messages.** "The messages come from a check
  of scikit-learn that the tests run, `check_positive_only_tag_during_fit`."
  - The pytest output does not name the test, and no record shows the
    attribution.
  - It is plausible: that check fits on the iris data minus their mean, and
    the fourth column is then negative throughout.
- **(c) The console example's output files.** "Both were compared with the
  copies the measured M3 left outside the repository" (`gp_elite_best.txt`,
  `gp_elite_log.csv`). The committed comparison,
  `l1/m3_compare_release_vs_l1.txt`, lists both files as "new".
- **Kind:** unsupported (traceability).
- **Suggested correction:**
  - for (a), name the script and the command that wrote the table;
  - for (b), write "attributed to ... from what that check does", or record
    it;
  - for (c), commit the result of that comparison, or say it is not
    recorded.

### 12. LIMITATIONS point 11: the times of S1

- **Where:** `LIMITATIONS.md:264-267` (`LIMITATIONS.fr.md:289-293`).
- **As written:** "on the TP diagnostic the law came back in 113 fits of 200
  against 126, and a fit took 1.67 times as long".
- **What the record shows:** `s1/campaign/README.md`.
  - Both figures are of the plain arm, where the median fit went from 7.0 s
    to 11.7 s.
  - In the units arm the law came back in 119 fits against 120, with a
    median of 8.3 s against 8.2 s.
- **Kind:** wording that says more than the record (minor).
- **Suggested correction:** "in the plain arm of the TP diagnostic ..., and
  the median fit took 1.67 times as long".

### 13. README: nothing says what 1.4 changes

- **Where:** `README.md` and `README.fr.md`, against
  `PLAN_RELEASE_1.4.md:220-221`.
- **The plan:** the READMEs are brought up to date with "what's new, N2b;
  the counts of structures under noise".
- **What the READMEs say:** the short README gives the counts (table, lines
  94-100), but no sentence says what changed. A reader of the PyPI page sees
  the gain under noise with no explanation. "What's new" is only in
  `docs/features.md` and the CHANGELOG.
- **Kind:** omission against the plan (minor).
- **Suggested correction:** add one line under the table, for example "1.4
  gives the noise-tolerant seeds more forms (docs/features.md)", and the
  same in French.

## Checked and found right, by document

### README.md and README.fr.md

- **The table:** 171 and 171, 116 and 152, 87 and 95, 174 and 174, and
  1,161 of 1,161, recomputed from M2.
- **Examples and comparisons:**
  - the Kepler example's output (`m3/readme_kepler.txt`) and the R² of the
    plot (`m3/kepler_plot.txt`);
  - 15 exact laws against 6 for gplearn (`m3/duel_gplearn.txt`).
- **Code and packaging:**
  - `r2_validation` is None below 30 rows (the hold-out split in `core.py`
    returns early for n < 30);
  - Python 3.9 to 3.14 (`pyproject.toml`, M4, `tests.yml`);
  - "four changes measured, three not adopted" (`PLAN.md`).
- **Links and French:** every link and path exists (`review2/links.py`),
  and the French page gives the same figures.

### docs/usage.md and utilisation.md

- **The budget of 30 s:** 2,291 fits reached it, with a median of 30.49 s
  and a maximum of 31.88 s.
- **The check of `time_limit=`:** 9.7 s, 15.3 s, R² 0.9979, and 6.3 s with
  1.3.0.
- **The TP notebook:** 52 and 53 s against 49 and 54 s, and 48 s against 194
  to 198 s (in `results_1.2`).
- **The usage example:** 33 nodes, `r2_validation` 1.0.
- **The safety nets, against the code:** base clipped at 100, exponent at 6,
  value at 1e6, division within 1e-8 of zero, and the arcsine clip.
- **Settings, against the code:**
  - patience of 30 generations and 1 %;
  - `thorough` is 400 individuals, 4 islands and 200 generations;
  - `GPEliteRegressor` always sets its number of generations.
- **The rest:** the CI matrix, and the console example
  (`m3/console_hooke.txt`).

### docs/units.md and unites.md

- the II.11.3 table (`m3/units_ab_ood.txt`);
- 174 and 171 in the release measurement;
- the table of the mystery constant (`m3/mystery_constant.txt`).

### docs/robust.md and robuste.md

- the table, and "four seeds out of five" (`m3/robust_example.txt`).

### docs/examples.md and exemples.md

- the battery output and figures. The forward split runs a fixed number of
  generations and places other seeds with 1.4.0, so attributing the change
  to the new seeds holds for it.

### docs/measurements.md and mesures.md

- **The scaling paragraph:**
  - 6 of the 13 runs below 1,000 points, and 10 of 17 against 9;
  - the forms at 200 and 5,000 points;
  - 40 s and 100 s, summed from `m3/scaling.txt` (the bench runs on one
    core, `parallel=False`).
- **The frozen sets:** 214, 228, and 10 against 9. TF78N: 37 and 28 against
  34 and 27; under units 37 and 33 against 35 and 32.
- **Feynman 15:** 15 of 15. The duel: 15 against 6, 7 within 1e-3, ahead on
  9, tied on 6. I.16.6 under units: factor 1.00755 against 1.00758.

### docs/features.md and caracteristiques.md

- **The 1.4 bullet, against `_make_tolerant_seeds`:**
  - the second pass weights the rows by |y|/max|y| in the QR, that is a
    least squares weighted by y², and it lifts the condition on the sign;
  - the scans of the logarithm, the sine and the cosine;
  - `_TOLERANT_MAX = 12`, with the forms of 1.3.0 always placed;
  - the stage is called only when no binomial or elementary seed was placed
    (`core.py:10271`).
- **What's new:** the figures of 1.4 are right.

### CHANGELOG, 1.4.0 entry

- **The figures:** every bullet, recomputed. 247 against 203, and 192
  against 156 (`n2b/campaign/compare_n2b*.txt`).
- **The code:**
  - S1, E2 and the refit are off (`_SMALL_CV`, `_E2_SEEDS` and
    `_TOLERANT_REFIT` are False);
  - the text of W1 (`api.py`);
  - L1 is two lines (`git diff f6a36cd ec44e8e`).
- **"Every seed 1.3.0 placed is still placed":**
  - no fit among the 3,092 of M2 lacks a seed of 1.3.0, compared as
    strings;
  - the same holds for the point source (`n2b/campaign/examine/`), C_big
    (`m1_examine/`) and the 111 fits of `m3_examine/`.
  - Two limits of the design were never observed: forms are deduplicated
    with every constant treated alike, and the cap of twelve is exceeded if
    1.3.0 alone placed more than twelve.

### LIMITATIONS.md and LIMITATIONS.fr.md

- **The paragraph on 1.4:**
  - 31 against 33 equations never recovered; 203 and 11 against 204 and 10;
    10 against 9 on the Strogatz systems;
  - the five and four equations never recovered;
  - 10 collapses of 65, the worst at -1,946; 66 of 250 (38 and 28);
  - 11 against 12 departing formulas of 130, and 65 against 68 of 500;
  - the status changes: 23 in TF78 and TS14, one of them with the same
    seeds.
- **Point 3:** 14 against 18 on the point source. In the 4 lost fits, B's
  error on the training rows is lower than A's.
- **Point 5:** `kepler_minmax_check` 2 of 10 against 4; the figures of
  `time_limit=`, I.16.6, the wide range and the small-data exponential.
- **Points 11 and 12:** against the campaign READMEs of S1, E2 and N2.

### paper/paper.md

- 247 against 203;
- the duel and its budgets (`duel.py`);
- the dependencies numpy, pandas and scikit-learn;
- 1,161 models under units; 214, 228, and 10 against 9;
- 65 of 156 against 61;
- G·M☉ within 0.002 % (`m3/case_kepler.txt`: -1.64e-05);
- the mystery constants.

### Notebooks and case studies, against M3

- **tp_six_lois:**
  - its formulas and constants;
  - `m3/tp_six_lois.py` is its code cells exactly, apart from whitespace and
    the `pip` line;
  - "7 à 10 s" is from its run with 1.2.0, as the notebook says.
- **tp_regression_symbolique:** question 2 (sizes 38, 46, 43;
  `m3/notebook_snippet_tp.txt`).
- **quickstart, English and French:** the Kepler, Hooke and Nikuradse
  snippets, and the 13 forms ranging 0.01 to 1.12 (`case_nikuradse/`).
- **Kepler case study:** every figure.
- **Hubble case study:** the figures, and "these seeds place nothing" (0
  noise-tolerant seeds in every call).
- **Nikuradse case study:** the figures of seed 0.

### benchmarks/results_1.4/release/README.md

- **M1:** the compare files and the times.
- **M2:**
  - the table and the criteria;
  - 2,428 fits with the same seeds, 2,125 of them with none, 782 at no
    budget, 0 that differ;
  - TP: 9 fits change, 6 lose the law and 3 gain it;
  - TPT10: 10 fits change, Kepler's law 2 lost and 1 gained;
  - TR25raw: 5 fits, the test R² moving by 0.0060 at most;
  - U41 at 174 against 173 by timing: ufeyn I.11.19 seed 0, at its budget,
    with the same seeds (`review2/m2_vs_n2b.py`).
- **M3:**
  - 44 records the same, 22 that differ, 4 new, for six causes;
  - the scaling bench, small data, the wide range, `time_limit=` (15 of 16
    against 14 of 16), and the timing table.
- **M4:** 199 tests pass; 6 DLASCL messages under Python 3.9 and 3.11.
- **L1:**
  - the files and environments;
  - the times of parts a, b and c (`l1/verify.log`);
  - the count is identical job by job;
  - TP and TPT10 are identical on every field but time, date and engine
    path (`review2/tp_identity.py`, which also finds the TP of M2 identical
    to campaign N2b, for A and for B);
  - M3: 57 records the same, 4 that differ by timing, 2 new.
- **The plan's correction:** the sentence "all their inputs are positive"
  is corrected; the code does use only columns that keep one sign.

### DIAGNOSTIC_TP.md, note for 1.4

- the figures: 123 against 126, 120 against 120, 18 to 14, 2 fits lost and 3
  gained, Snell's law in none, 107 and 103.

### Moved sections

- `review2/readme_moved.py`: every paragraph of the README at ec44e8e is in
  the new README or in `docs/`, apart from three things:
  - the rewritten introduction;
  - the block that installs from source;
  - the list of the dependencies by name.

  Beyond those, the only changes are the figures brought to 1.4.

## Scripts of this review (`m5/review2/`)

- `m2_recount.py`: M2 counted again (indicators, criteria, where 1.4 does not
  act, structures by equation, the seeds of 1.3.0 kept, TP and TPT10 fit by
  fit).
- `limits_recount.py`: the lines of `m2/limits_figures.txt` that the first
  script does not give.
- `m2_vs_n2b.py`: the benches of M2 against campaign N2b, same engines.
- `tp_identity.py`: TP of M2 against campaign N2b, and TP and TPT10 of L1
  against M2.
- `m3_records.py`: the scaling bench and the small-data check, 1.3 against
  1.4, and the fits with other seeds.
- `extra_checks.py`: the notebook times, the point source, the exact laws
  lost or gained, the cut formulas, the count of L1, I.16.6 under units, and
  the coverage of `m3_examine`.
- `links.py`: the paths and links of the documents and notebooks.
- `fr_en_numbers.py`: the figures of the French and English pages.
- `readme_moved.py`: the old README against the new README and `docs/`.
- `nbdump.py`: prints the cells of a notebook.
