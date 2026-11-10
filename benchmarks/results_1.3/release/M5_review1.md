# M5, first independent review (9 November 2026)

A second agent, who had not seen the work, reviewed HEAD e598e4d. It checked
about 300 claims of the documents against the records and the code:
- the two READMEs;
- the 1.3.0 entry of the CHANGELOG;
- the pages of the limits;
- the paper;
- the two TP notebooks;
- this folder's README and the READMEs of the two examinations;
- the note of 1.3 in `../../results_1.1/DIAGNOSTIC_TP.md`;
- the comparison script of M2.

It recomputed about 190 of the claims from the records, with read-only
scripts that import nothing of the engine and run no fit (`m5/review1/`).
Every indicator of M2 and the eleven criteria came out the same, and so did
M1, M3, M4, the frozen test set, E1 and E2, and the French pages against the
English. It reported 22 findings (`m5/review1_report.md`). Each was checked
against the record it names and holds. Each is corrected below, in the
commit of this file, or answered.

| # | Finding | What was done |
|---|---|---|
| 1 | The six-laws notebook said GP_ELITE has no arcsine for Snell's law | Section 10: the arcsine is in `trig` and `full` since 1.3, and the law does not come back in the 40 fits of the diagnostic, the noise hiding it |
| 2 | The CHANGELOG said every fit of the pools `physical`, `poly` and `conserve` returns what it returned with 1.2.0; under a budget, 16 fits of the pool `physical` return another formula and 2 change status, and no measurement uses `poly` or `conserve` | "with them, the models of 1.2.0 at equal work", and a bullet on the 16 and the 2 at the budget |
| 3 | "The other eight lose nothing" fails at seeds 5 to 9: I.50.26 loses its one exact fit, III.17.37 gains one | "keep their count of exact fits on both sets (20 and 21)", with the two laws named |
| 4 | The 2 of A1 counted every exact fit, the 3 of A2 the fits with the arcsine | Both with the arcsine: A1 1 of 10, A2 3 |
| 5 | "47 of the 82 with an arcsine" is a lower bound (the bench records 160 characters of a formula, and 77 of the 82 are cut), and the clip was given as the cause | "At least 47", the cut recorded, and "how many depart because the clip acts is not recorded" in the CHANGELOG, both pages of the limits and this README; "the pool `trig`" for "the pools with the arcsine" |
| 6 | With 1.3.0 the notebook of the pool `full` prints a warning at question 1 that it never mentions | Question 1 says what the warning means, and what `formula_exact` and the Pareto front give |
| 7 | The note on the diagnostic said the law came back in none of 10 clean fits with A1; by the test of the law A1 has one, without the arcsine | "no formula with the arcsine", and the one fit of A1 by the test |
| 8 | The CHANGELOG described the arcsine seed as exact only; the noise-tolerant seeds place it too, in 25 fits of M2 | The introduction and "Added" say both, with the 10 and 25 fits; this README gives them |
| 9 | Point 1 of the limits said the arcsine does not reach I.26.2, then that the search reached it in 3 fits of 5 | "Two things the arcsine does not settle", "no seed holds it", with both sets of seeds, in both languages |
| 10 | The CHANGELOG gave the comparison of Snell's curves with the noise as a figure of 1.3.0; it was measured on A1 | "Measured on the first version of the arcsine" |
| 11 | E1: 1.2.0 returns the parabola in 7 of its 8 misses, not 8; the medians of generations; the two machine files are identical | Corrected in `m2/examine/README.md` |
| 12 | "The formula ... to the bit" is checked on the 160 recorded characters; 5 of the 706 are cut | "the recorded formula (its first 160 characters)" in the CHANGELOG and this README, which adds that every other field of those 5 is identical. M1 compares the whole model on the eleven configurations of the pool `physical` |
| 13 | The plan asks for the formulas with the arcsine; `compare.txt` counts them only | `m2/arcsine_formulas.py` and `.txt` list them by suite. The sum of the collapses of R6 and R7raw is the criterion as the plan writes it, as in 1.2; each passes alone too (5 and 5) |
| 14 | The deduced constant of 1.3.0 is listed as new, not among the 57; the third cause of the differences was not named | Corrected: the five new records, and the nine that differ, by cause, the driver being the third |
| 15 | "Two fits change status, both at the budget" while 1.3.0 did not reach it on vdp1 | "each where 1.2.0 reached its budget" |
| 16 | The READMEs put 1.3.0's 174 beside 1.1.0's 165 | "174 and 171, against 166 and 163 for 1.2 measured beside it", in both languages |
| 17 | 1.2.0 on the frozen set is 214 and 10 in one sentence and 213 and 8 in the next | Both READMEs and the paper say these are two campaigns, the time budget moving the counts |
| 18 | "3 fits of 5" for I.26.2 quotes one set of seeds | Both sets, 3 and 2 of 5, in the CHANGELOG and the pages of the limits |
| 19 | Kepler min-max: four configurations, two quoted ambiguously | The CHANGELOG names N1 on and off; this README gives the four |
| 20 | A path of the CHANGELOG did not resolve from the root | `benchmarks/results_1.3/release/m2/examine/` |
| 21 | "Tests green on every commit" overstates; it does not run on document-only commits | "on every commit ... that it ran on", the three named in `m4/ci_runs.txt` |
| 22 | That E2 was started after its plan cannot be read from its records | This README gives the times: the plan at 16:21:31, the run started by the same command after the push, the records without time. For E1, the plan at 14:47:08 and the first record at 14:47:51 |
