# M5, first independent review (14 October 2026)

A second agent, who had not seen the work, checked about 400 claims (250
distinct) of the two READMEs, the 1.0.0 section of the CHANGELOG, the pages of
the limits, the paper, the notebooks and case studies, this folder's README and
the results and launch sections of `PLAN_PHASE6.md` against the records. It
confirmed the headline figures (163/205 against 88, 213/390 against 145, 105/85
against 67/66, 15/15 against 6/15, the lines of `m2/compare.txt`, every number
of the case studies, recomputed from the records) and reported 20 findings.
Each is corrected or answered below.

| # | Finding | What was done |
|---|---|---|
| 1 | `README.fr.md` said "quatre étapes" for the quickstart, which has five | Corrected: "cinq étapes" |
| 2 | Real datasets miscounted: "38" in the CHANGELOG, "13 of the bench" in the limits; the bench has 7 (six of them also standardised), the test set 25 (also in their own units); the limits counted both versions on the bench but one on the test set | Corrected: 32 datasets, 7 of the bench and 25 of the test set; point 4 of the limits counts both versions on both (11 of 65; 64 of 250, 37 and 27) |
| 3 | "Real data unchanged" overstates the records: 15 of 630 real-data fits return another expression, the TR25raw median moves by 0.004 | Corrected in both READMEs, the paper and this folder's README to "the same median R² within 0.004 and the same number of collapses"; the CHANGELOG adds the 15 of 630; the B1 entry no longer says "whose results are those of 0.9.0" |
| 4 | The parallel-islands statement of the README rested on a 0.9.0 record | Measured on 1.0.0 (`m3_extra/parallel_islands/`): the same approximation, R² 0.9999765, 14 nodes; the README Kepler block, `kepler_demo.py` and `pools_check.py` unchanged |
| 5 | "Nine of eleven targets" did not follow the table of gate 2 | Corrected: the ten rows of the table, eight met and two missed, the units row (27 s) and the flagged-formula row included; the eleven lines of `compare.txt` explained |
| 6 | "The sixteen unusual inputs" listed as unchanged while one of them changed | Corrected: 15 of the sixteen |
| 7 | The paper said the SRBench integration was merged; no record in the repository | Corrected to what the records support: proposed to that project (cavalab/srbench, pull request 227). Whether it has been merged is asked to the author at gate 4 (answered: merged, `M5_review2.md`, finding 4) |
| 8 | 0.9 quoted as 88 and 145 (paired run) against 86 and 144 in its own entry, without saying why | Corrected: "measured beside it" in the READMEs and the paper; the CHANGELOG gives both measurements and the reason |
| 9 | The 1.0.0 time-limit run overlapped another script; "found the exact law" was inferred | Run again alone (`m3_extra/time_limit_check_alone.txt`): 16.9 s in parallel, 10.2 s in sequence; the README quotes that run and says "a model of R² 1.0000, before the budget, as a search does only on an exact law" |
| 10 | Point 4 of the limits rested on a 0.8.0 reading ("small or mostly categorical") and described the split loosely | Corrected from the 1.0.0 records: six of the 25 datasets make 28 of the 37 collapses; "farthest from the centre of the data" |
| 11 | Nikuradse, section 6: the log-of-log forms were counted on the fronts of section 4 only | Corrected in both languages and in `PLAN_PHASE6.md`: the forms of section 5 (12, 37 and 39 nodes) and their gaps on the removed roughness (1.20, 0.48, 0.63 standard deviations), and the seven-node form of the quickstart's shorter run |
| 12 | Kepler fits "a few seconds" (9 to 16 s recorded); Jupiter's mass "in the same file" (not in the repository's file); Reynolds "about 4 000" (record 4,270) | Corrected: one to about fifteen seconds; "in the table of masses of the same source file, `plan94.c`"; about 4,300, as the quickstart |
| 13 | `PLAN_PHASE6.md`: "four months after the first release"; 41 stars without record; no seed placed under units without record for Kepler; notebook runs without record | Corrected: four months after the repository was created, first release 2 July; `../launch/baseline_2026-10-13.txt` records the counts; the typed fits of `hubble.txt` record that no seed acts under units; the notebooks were run again on the wheel with their output kept (`m3_extra/notebooks/`) |
| 14 | The paper's design paragraph said every family becomes a straight line in log scale; the trigonometric form is searched on a grid | Corrected: the grid for sines and cosines, the log-linear form for the others |
| 15 | The "20 % off" of the old code had no record in `M4`; the label of a line of `compare.txt` counts folds only | Corrected: the record of 0.9.0 cited (`m3/deduced_constant_venv09p.txt`); the label explained in this folder's README |
| 16 | The README did not say that I.16.6 at 2,000 points is exact in a non-canonical form | Corrected in both READMEs |
| 17 | Point 5 of the limits cited the branch record for a figure measured on the wheel | Corrected: `release_1.0/m3/kepler_minmax_check.txt`, and "no equation has fewer exact fits than with 0.9.0" |
| 18 | The comparison with PySR and Operon is not measured | Answered and marked: the README says under its table that the last row is a concession, from the published results of the compiled engines, not a measurement of this project; the launch texts present it the same way |
| 19 | The machine description had no record | Recorded: `m3_extra/machine.txt` (Intel Xeon at 2.1 GHz, 4 cores, AVX-512, 15 GB) |
| 20 | `CITATION.cff` gave the 0.9.0 date | Set to 14 October 2026, to be set to the day of publication |
