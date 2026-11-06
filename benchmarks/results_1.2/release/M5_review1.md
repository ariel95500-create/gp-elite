# M5, first independent review (5 November 2026)

A second agent, who had not seen the work, checked about 280 claims of the two
READMEs, the 1.2.0 entry of the CHANGELOG, the pages of the limits, the paper,
the TP notebook, the case studies, this folder's README and the note on
`../../results_1.1/DIAGNOSTIC_TP.md`, against the records and the code. It
recomputed about 170 of them from the records, with read-only scripts and no
fit (`m5/review1/`). Every figure of M2 and the thirteen criteria of the plan
came out the same; the figures of the limits, M1, M4, the times of M3, the X1
examples, the French pages against the English, the case studies and every
path held. It reported 19 findings (its report: `m5/review1_report.md`). Each
was checked against the record it names and holds; each is corrected below,
in the commit of this file.

| # | Finding | What was done |
|---|---|---|
| 1 | Point 10 of the limits gave 9 collapses against 11 to the six standardised datasets; they are R6 and R7raw together, 65 fits (3 against 4 on R6 alone) | Corrected in both languages: "on the 65 fits out of the training range of the seven real datasets, 9 collapses against 11" |
| 2 | 0.810 for the R6 median of 1.1.0 in campaign H1 rounds 0.8095 twice; it is 0.809459 | 0.809 in both pages of the limits and in the CHANGELOG; `../PLAN.md` keeps its text with a dated note (the criterion holds either way: 0.802 is 0.0073 below) |
| 3 | 10 of the 38 "other models at the budget" are III.19.51 under units with noise, where 1.1.0 ran one generation and 1.2.0 35 to 40: D0 changes them, not the load | This README and the CHANGELOG: 28 at the budget in both versions, 12 III.19.51 under units changed by D0 (two exact in both, ten with noise) |
| 4 | "Version 1.2 leaves the models alone when the call sets its budget" (limits) and "With a budget set, nothing changes" (CHANGELOG) are false for D0, and for an explicit `patience=` | Limits, both languages: with a budget set and `patience=` left alone, no change without units; under units, only the fits whose typed start needs 9 to 12 factors or reaches its deadline. CHANGELOG: "With a budget set and no `patience=`, the stop does not act" |
| 5 | The `speed="thorough"` bullet promises 200 generations; without `generations=` or `time_limit=` the stop acts there too | Both READMEs: one sentence added to the bullet; the `patience=` bullet names the budget, `generations=` or `time_limit=` |
| 6 | The paper says a ten-point table comes back "with the same formulas"; the records give it for the six laws of the notebook, not for every table (25 other formulas on the 200 ten-point fits of the diagnostic) | "(with the same formulas on the six laws of its French lab notebook)" |
| 7 | This README said the notebook quotes the run of 1.1.0; since the documents it quotes the run of M3 | Corrected |
| 8 | The Nikuradse formulas X1 rewrites have sizes 13 to 72, not 13 to 69 | Corrected |
| 9 | The CHANGELOG said the TP fits of the mechanics of D0 ran with 20 generations; they ran under the defaults | "(seed 0, 20 generations, no time limit)" for U41, "(draw 0, under the defaults)" for the TP fits |
| 10 | The X1 example of the note on the diagnostic and of the notebook was already an exponential in 1.1.0; X1 only gave it its scale | The note quotes the diagnostic's own formula, `-0.0146989 + 4.86249 * 0.00784758^(0.2 * t)`, and what it becomes, `-0.0146989 + 4.86249 * exp(-t / 1.03145)`; the notebook, a fit at 10 points and 2 % that 1.1 printed as a power (draw 1), with its constant term |
| 11 | The notebook said 1.2 settled "two points of this list", which no longer holds them | "deux défauts que notre diagnostic signalait aussi … Les points de cette liste restent à faire" |
| 12 | The II.11.3 table gives 1 / 1 / 1 seconds; the M3 of 1.2.0 measured 0 / 1 / 0 | Both READMEs give the measurement of 1.2.0 |
| 13 | This README counted the table of `units=` on II.11.3 among the records that are the same; its text differs by the seconds | "the records of the table … (its text differs by the seconds, below)" |
| 14 | "III.19.51 ends in about a second" holds without noise only; the CHANGELOG's "with noise, in 30.1 to 30.5 s" reads as exact | "without noise" in both READMEs and the CHANGELOG; "with noise, where neither version returns the exact law, it runs its budget" |
| 15 | The paper's sentence on X1 merges its two rewritings | "a power of a number is printed as an exponential, and an exponential of one variable with its scale" |
| 16 | The README's X1 example is a fragment of the record | The whole formula, with its constant term, in both READMEs |
| 17 | The stop reads the training error when there are no hold-out rows | "(the training rows when there are none)" in both READMEs, both pages of the limits, the CHANGELOG and the note |
| 18 | "Point 8 is measured on 1.1.0" no longer holds for its first bullet | Both pages of the limits: "but for the times of its first bullet, measured on 1.2.0 beside 1.1.0; point 10 on the campaign that decided the stop of 1.2" |
| 19 | The feature list of the READMEs has no entry for 1.2 | Two entries (the stop on patience, the exponentials) and the time budget extended to the typed start, in both languages |

The reviewer also recalled that the date of the paper and of `CITATION.cff`
are those of 1.1.0; they are left to gate 8, with the name of the version.
