# M5, second independent review (5 November 2026)

A second agent, who had seen neither the work nor the first review, checked
about 450 claims of the two READMEs, the 1.2.0 entry of the CHANGELOG, the
whole pages of the limits, the whole paper, the TP notebook, the quickstart
and case-study notebooks, this folder's README, `M5_review1.md`, the note on
`../../results_1.1/DIAGNOSTIC_TP.md` and each of the 19 corrections of the
first review (45b8282). It recomputed about 220 of them from the records, with
read-only scripts and no fit (`m5/review2/`). Every figure of M2, of campaign
H1, of the pages of the limits, of M1, M3 and M4, of the TP notebook and of the
case studies came out the same; no translation error and no broken path. It
reported 11 findings, all in sentences, three of them brought by the
corrections of the first review (its report: `m5/review2_report.md`). Each was
checked against the record or the code it names and holds; each is corrected
below, in the commit of this file.

| # | Finding | What was done |
|---|---|---|
| 1 | "What's new" of both READMEs: "With a budget set, the models of 1.1 at equal work"; D0 changes the models of III.19.51 under units at equal work (U41 seeds 0 and 3, one generation in both versions, another expression) | Both READMEs: "but for those whose typed start under `units=` the correction changes (III.19.51 on the bench)" |
| 2 | This README said the notebook's fits stop on the hold-out error; ten rows keep no hold-out (below 30 rows, `core._split_holdout`), so they stop on the training error | Corrected, with the reason |
| 3 | The two entries of the feature lists added in 45b8282 lacked the training-rows case | Added in both languages |
| 4 | The CHANGELOG gave "430 to 735 s with `time_limit=30`" citing `d0/D0.md`, which gives 443.5 s and 600 to 735 s; 430 s was a fit of the mechanics with 20 generations and no time limit | "334 to 421 s in the release measurement of 1.1.0, and 600 to 735 s on the first machine of the prototypes" |
| 5 | "28 reached the budget in both versions … the other 12 are III.19.51" reads as a count, where 38 did; the CHANGELOG did not say the ten noisy III.19.51 fits reached it too | The CHANGELOG says the ten "reached the budget in both versions too"; this README: "38 of them reached the time budget in both versions. For 28 of those, the cause is the budget" |
| 6 | `M5_review1.md`, row 2: 0.809459 − 0.802117 is 0.0073, not 0.0074 | Corrected |
| 7 | This README's sentence on the formulas X1 rewrites merged its two rewritings; several examples only gain their scale | "where X1 writes a power of a number as an exponential, or an exponential of one variable with its scale" |
| 8 | The AI disclosure of the paper merged the two rewritings, and named D0 a correction "under a time limit", where its widened fast path acts with or without one | "the exponential printed as such and with its scale, and the correction of the typed start under declared units" |
| 9 | The limits said "What 1.2 changes is the time of a fit under the defaults"; point 10 shows that some models change too | "the time of a fit under the defaults, and with it some of the models (points 8 and 10)", in both languages |
| 10 | The CHANGELOG said the stop was confirmed on "seeds never run"; the seeds 5 to 9 of the bench were run in earlier phases | "confirmed on five other draws of the TP diagnostic and five other seeds of the bench" |
| 11 | "The Tests workflow is green on every commit since the candidate" had no record | `m4/ci_runs.txt`: the runs 222 to 234, all green, read from the GitHub API. It also records what this check found before the candidate: the two commits of the campaign C1 (runs 219 and 220) failed on 6 and 5 of their 8 jobs, all on one test of C1 that left with it; noted in `../PLAN.md` |
