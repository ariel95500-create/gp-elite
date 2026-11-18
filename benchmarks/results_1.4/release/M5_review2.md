# M5, second independent review (17 and 18 November 2026)

A third agent, who had seen neither the work nor the first review, reviewed
HEAD d0051ea, where the corrections of the first review were in. It stopped
at its start on 17 November on a usage limit of the agent and resumed on 18
November on the same HEAD. It disclosed that one `grep` across this folder
printed a single line of `M5_review1.md` before it excluded the file; the
finding that touches the same sentence (11 b) it reached from the records.
It checked about 240 claims of the same documents as the first review, and
recomputed about 150 figures from the records with read-only scripts that
import nothing of the engine and run no fit (`m5/review2/`). The eighteen
criteria of the plan, recomputed by code of its own, are met with the
figures of `m2/compare.txt`; the README table, the CHANGELOG, the pages of
the limits and the paper agree with the records, and so do the records of
the verification of L1. No finding touches a figure that decides the
release or a criterion of the plan. It reported 13 findings
(`m5/review2_report.md`). Each was checked against the record or the code it
names and holds. Each is corrected, in the commit of this file, or answered
below.

| # | Finding | What was done |
|---|---|---|
| 1 | The CHANGELOG said no pass of the scan raised on any fit of the release measurement, while the fault was found because it raised in the test suite (M4); the record covers the 3,892 fits run again for one generation | "The fault showed in a check of the test suite (M4); on the 3,892 fits of the benches and of the TP diagnostic of the release measurement, run again for one generation, no pass of the scan raised." This README: "The fault touched none of these fits; it showed in the test suite" |
| 2 | Point 5 of the limits said "one figure loses its law" on exact data; that holds for the public figures of M3, while on the frozen test set of M2, 4 fits lose their exact law and 6 gain one, all where 1.4.0 places other seeds | "Among the public figures measured again (M3), one loses its law that way", and a sentence for the frozen test set: 4 lost (2 of TF78, 2 of the Strogatz systems) and 6 gained (2 and 4, one on the rows out of the domain), all where 1.4.0 places other seeds; in both languages (recomputed: `m5/review2/extra_checks.py`, item 3) |
| 3 | The usage page gave "50 to 53 s over the four runs of 1.4.0", mixing the corrected wheel's run of 17 November with the three runs of 14 November | "51 to 53 s over its three runs of the day, 52 and 53 s in the two paired with 1.3.0, against 49 and 54 s", in both languages |
| 4 | Point 3 of the limits said two equations "lose their structure" at 10 % noise, and gave as a fact that the new seeds take the search elsewhere, which was not examined | "lose fits with the structure of the law", and "in all twenty of these fits 1.4.0 places other seeds (one where 1.3.0 placed none on I.27.6, three against one on III.15.12), and campaign N2b gave the same counts: the likely cause, not examined"; in both languages (checked on the records of M2) |
| 5 | The note of 1.4 in `DIAGNOSTIC_TP.md` said the final choice, "not the seeds", decides whether the law comes back, against its own first bullet and the campaigns | "a seed with the structure of the law does not make the search keep it, and the final choice among the forms of the search decides whether the law comes back", as the limits and the CHANGELOG put it |
| 6 | The limits said that where the seeds are the same and no budget is reached, 1.4.0 "returns the models of 1.3.0 to the bit"; what was compared is the recorded formula, its first 160 characters (3 of the 782 are cut), the error on the test rows and `formula_exact` | Said so in the limits (both languages), the CHANGELOG and this README |
| 7 | This README said the examination of M3 builds the data of every fit of five scripts and the battery example; it builds 111 fits, and the random split of the battery, which moved too, was not examined | The coverage as it is: the 85 fits of the scaling bench, the 20 of the small-data check, I.16.6 under units, the wide range of the robustness check, the three tables of the check of `time_limit=`, and the forward split of the battery; "the random split of the battery example, which moved too (+0.993 to +0.992), was not examined" |
| 8 | The gains at 10 % noise mixed the arms: under units I.44.4 gains too (0 → 5), and I.32.5 and III.19.51 do not move | The gains by arm, at 1 % and at 10 % |
| 9 | M4 did not report the Tests workflow, which the plan asks for | M4 cites `m4/ci_runs.txt`: green on every commit of the branch since the candidate that it ran on, and checked again on the commit of the release with the pull request |
| 10 | "On every check of the amendment, the corrected engine gives what the measured release gave" does not hold for the cases with a negative column, by design | "gives what the amendment expects: what the measured release gave, times aside, and, on the cases with a negative column, no pass that raises" |
| 11a | No script in the folder of 1.4 writes `m2/limits_figures.txt` | It is the output of `../../results_1.3/release/m2/limits_figures.py campaignR_1.3.0.jsonl campaignR_1.4.0.jsonl`, run from `m2/`, to the byte; this README names the command |
| 11b | The attribution of the LAPACK messages of M4 to `check_positive_only_tag_during_fit` was not recorded | `m4/log_scan/sklearn_check.py`, committed before its run (1a83cb3, and 3e5ed99 for a guard of its top level before running it again), runs that check alone on the estimator of the test: six messages with the measured wheel, as in M4 under 3.11, and none with the corrected one (`m4/log_scan/sklearn_check_*.txt`) |
| 11c | The comparison of the console example's two files with the copies of the measured M3 was not recorded | `l1/m3_console_files_compare.txt`: `gp_elite_best.txt` the same, `gp_elite_log.csv` differing by the order and timing of the islands' rows |
| 12 | Point 11 of the limits gave the TP figures of S1 without their arm, and "a fit took 1.67 times as long" for the median of the plain arm | "in the plain arm of the TP diagnostic", "the median fit took 1.67 times as long"; in both languages |
| 13 | No sentence of the READMEs said what 1.4 changes, which the plan asks for | One sentence under the table: 1.4 places more noise-tolerant seeds at the start of the search, hence the gains under noise, with links to what's new and to the CHANGELOG; in both languages |
