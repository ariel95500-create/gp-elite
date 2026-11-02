# M5, first independent review (30 October 2026)

A second agent, who had not seen the work, checked about 480 claims (about 250
distinct) of the two READMEs, the 1.1.0 entry of the CHANGELOG, the pages of the
limits, the paper, the TP notebook and the case studies, this folder's README,
`../PLAN_U2.md` and `../ROADMAP.md` against the records. It recomputed the
headline figures from the records and confirmed them: the seven criteria of M2,
U41 108 to 165, the five families 16 to 57, 1,005 of 1,005 models passing the
audit, TF78 under units 169 to 226, 47 of 1,775 jobs differing without units,
all at the budget; the II.11.3 table, Feynman 15 with units, the scaling, the
TP notebook and its pair of runs, the U2 check, every figure of the Kepler and
Hubble studies. It reported 17 findings (its report: `m5/review1_report.md`).
Each is corrected or answered below.

| # | Finding | What was done |
|---|---|---|
| 1 | The limits said 1.1 returns "the same figures" without units; measured beside 1.0.0, both give 108/86 structures, 8 Strogatz fits, 10 collapses, where the page quotes 1.0.0's own campaign (105/85, 7, 11) | Corrected in both languages: the models of 1.0.0 at equal work; under the budget the counts move a little between campaigns for both versions, with the figures of this campaign |
| 2 | README "Is it solid?" and the paper said "the figures of 1.0" next to "7 of 70" | Corrected in both READMEs and the paper: both versions give the same counts in this campaign, 213 of 390 and 8 of 70, the budget moving counts between campaigns |
| 3 | The paper said the typed population does not use the fitted forms yet | Corrected: since 1.1 it uses them, each kept only if it passes the gate |
| 4 | The Hubble notebooks said no seed finder acts under units | Corrected in both languages: the seeds place nothing, with or without units |
| 5 | This README said every suite out of domain has the same collapses; TS14 has one more (27 to 28) | Corrected; `m2/details.py` now counts TS14 too (`m2/details.txt`) |
| 6 | The CHANGELOG said "the same counts" without units; one TS14 collapse and six formula_exact differ, all among the 47 at the budget | Corrected: the same exact laws, structures, medians and real-data collapses, and the two exceptions named |
| 7 | II.11.28 under units: four seeds become exact, not one | Corrected here and in `candidate1/README.md` (1 to 4) |
| 8 | The free-fall trace had no record | Recorded (`m3_extra/fall_trace_1.0.0.txt`, `fall_trace_1.1.0.txt`): with 1.1.0 the power law finder makes one seed, `(t)²`; with 1.0.0 none. This README cites them |
| 9 | Kepler notebooks: 1.0 already wrote the textbook form at seed 3 | Corrected in both languages: other forms at four seeds of five, the same at seed 3 |
| 10 | Kepler notebooks pointed to the 0.9 output only; "one to about fifteen seconds" is stale | Corrected in both languages: the 1.1.0 output named beside the first one, and "under a second to about ten seconds" |
| 11 | The CHANGELOG said "the typed fits" of Kepler changed; only the fit on the inner planets did | Corrected |
| 12 | The paper's "1,005 typed models of that measurement" read as the 205 fits | Corrected in the paper and in the "What's new" of both READMEs: the release measurement, these equations with and without noise and the frozen test set |
| 13 | The `time_limit` figures came from a run beside other scripts | Run again alone (`m3_extra/time_limit_check_alone.txt`): 17.0 s in parallel with R² 1.0000, 9.4 s in sequence, 15 of 16. Both READMEs quote that run |
| 14 | The processor (2.8 GHz) had no record for these measurements; the container reports 2.10 GHz on 30 October | Recorded (`m3_extra/machine.txt`). This README says the processor was not recorded on the days of M1 to M3, that `../PLAN.md` recorded 2.8 GHz on 26 October, and that the container does not always run on the same host; the TP timings are compared within a day only |
| 15 | The list of what differs between the candidates omitted `scaling.txt`, the console's log and the driver files | Added |
| 16 | The battery example said "the equation 1.0 returns" | Corrected in both READMEs: 1.0 and 1.1 |
| 17 | The reading of SRBench in `../ROADMAP.md` had no record | Recorded in `../srbench_2aabbb6/README.md`: the four files by link and blob hash at 2aabbb6, with the lines used (SRBench is under the GPL, so the files are not copied) |

Also, from the reviewer's notes: the TP notebook now says that its 120 of 120
come from the diagnostic made with 1.0.0, and that the check of U2 gives 120 of
120 with 1.1.0 (`../PLAN_U2.md`).
