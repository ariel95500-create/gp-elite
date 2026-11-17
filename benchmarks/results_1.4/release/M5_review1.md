# M5, first independent review (16 and 17 November 2026)

A second agent, who had not seen the work, reviewed the documents of 1.4.0.
It started on f0e37c9 and stopped at 22:35 on 16 November on a usage limit
of the agent, before its report; it resumed on 17 November, after part c of
the verification of L1, and finished on 31bed58, where it read the release
README and the entry of L1 in the CHANGELOG again. It checked about 380
claims of the documents against the records and the code:
- the two READMEs and the pages of `docs/`, in both languages;
- the 1.4.0 entry of the CHANGELOG;
- the pages of the limits;
- the paper;
- the notebooks: the two TP notebooks, the two quick starts, and the case
  studies;
- this folder's README, and the note of 1.4 in
  `../../results_1.1/DIAGNOSTIC_TP.md`.

It recomputed about 150 figures from the raw records, with read-only scripts
that import nothing of the engine and run no fit (`m5/review1/`). The
eighteen criteria of the plan, recomputed from the jsonl by code independent
of `compare_m2_1.4.py`, are all met with the figures of `m2/compare.txt`, and
every figure of the tables of the README, the CHANGELOG, the limits and the
paper matches its record. No finding touches a figure that decides the
release or a criterion of the plan. It reported 13 findings
(`m5/review1_report.md`). Each was checked against the record or the code it
names and holds. Each is corrected, in the commit of this file, or answered
below.

| # | Finding | What was done |
|---|---|---|
| 1 | The limits said 1.4 "leaves the models alone where those seeds are the same"; that holds only where neither version reaches its budget (782 fits): of the 2,428 fits with the same seeds, 60 return another formula, each at a budget, and 3 change status. The Strogatz 10 against 9 and the main and bonus parts of TF78 were filed among the figures that move from one campaign to the next, though they move on fits where 1.4.0 places other seeds | "Where those seeds are the same in both versions and neither reaches its time budget, it returns the models of 1.3.0 to the bit (782 fits)", and the test-set figures moved to the first list, with "the fits that change status there are, but one, fits where 1.4.0 places other seeds"; in both languages |
| 2 | The entry of L1 in the CHANGELOG said the corrected engine returns what the measured one did "on every public figure", but the benches of M2 were not run again; "no fit had such a column" and "all their inputs are positive" (this README, and the amendment of the plan) go beyond the record: the standardised real datasets have negative values | The CHANGELOG names what was checked: the reference configurations, TP and TPT10, the records of the examples, notebooks and case studies, and, on the benches run for one generation, the same fits running the stage with no pass raising; "no pass of the scan raised on any fit of the release measurement". This README drops "all their inputs are positive" and adds a correction of the plan: the scans use only the columns that keep one sign, so the fault needs a column negative throughout |
| 3 | The CHANGELOG said the stage runs when no seed holds the data exactly; in the code an exact power law does not stop it (it runs on 125 of the 205 fits of F41, without noise). "Up to twelve seeds" caps only the new forms: every seed of 1.3.0 is kept even beyond twelve | "When no binomial form and no function of a monomial holds the data exactly (an exact power law does not stop it)", "new forms up to twelve seeds in all", in the CHANGELOG and the pages of the features, in both languages |
| 4 | `r2_validation` and `result.pareto` are None below 30 rows, which covers the README's own Kepler example and every TP table; the README and the usage page did not say so | The comment of the README says "(None below 30 rows)", the usage page has a bullet "Below 30 rows, nothing is held out", and the comparison table says "built in from 30 rows"; in both languages |
| 5 | Point 5 of the limits, exact data that no seed covers, lacked the instance 1.4 adds: the check of `time_limit=` in sequence loses its law; and the min-max check was given for 1.3.0 only | A paragraph for 1.4: the stage places more forms on exact data too; the check of `time_limit=` loses its law (4 seeds against 1, R² 0.9979 at 15 s against the law at 6.3 s), and three figures come out better (I.16.6, the wide range of the robustness check, the exponential of the small-data check); "and 1.4.0 the same" for the min-max check; in both languages |
| 6 | "14 fits of 20 against 18" for the point source did not name its arm | "without units", and "with units, 20 of 20 with both", in the CHANGELOG and both pages of the limits |
| 7 | The usage page gave the parallel islands' approximation of R² 0.99998 as current; it was measured once, with 1.0.0 | "when measured with 1.0.0 (not measured again since)", in both languages |
| 8a | This README gave the twelve seeds of C_big in M1, the six of 1.3.0 among them, from a trace that was not kept | `m1_examine/cbig_seeds.py`, committed before its run (b35566a), records them on one generation of each version: 6 with 1.3.0, 12 with 1.4.0, the six of 1.3.0 among them (`m1_examine/`) |
| 8b | "Neither version places one on R6, R7raw or TR25" left out TR25raw, where seeds are placed | Added: on TR25raw, seeds are placed in 7 fits, and in 5 of them 1.4.0 places other seeds and returns another formula, the test R² moving by 0.006 at most |
| 8c | The gains at 10 % noise left out II.11.27 under units (0 → 1) | Added |
| 8d | The small-data check moves at seed 1 too: the same printed formula, from a model of size 9 with 1.3.0 and 8 with 1.4.0 | "At search seeds 1 to 3", with the sizes 9, 10 and 13 |
| 8e | "Every other experiment moves by one fit at most" and "at most 2 fits move" are net counts | "The count moves by one (two) at most", and the fits that change: 9 on TP (6 lose the law, 3 gain it) and 10 on TPT10 (5 and 5), all in the plain arm; also in `DIAGNOSTIC_TP.md` |
| 9 | The quick-start notebooks described the README by its old content (robust mode, Pareto front, extrapolation, audit), and the French one pointed to the English README | "Going further" points to the pages of `docs/` that hold them, the French notebook to `README.fr.md` and `docs/fr/` |
| 10 | The README said every change to the search is decided by a comparison written before it runs; `docs/measurements.md` restricts it to changes meant to improve the search, and L1 is a correction | "Every change meant to improve the search", and in the section on measurement: "The correction of a fault is checked against the measured release instead, as for the one found in 1.4 before its release"; in both languages |
| 11 | The French page of the features said "ce README" | "cette page" |
| 12 | The paper keeps the date of 1.3.0, 10 November | Left to gate 12, with the date of the version, as `date-released` in `CITATION.cff` |
| 13 | The usage page gave the TP notebook 52 to 53 s with 1.4.0, the paired runs only; the release measurement has four runs | "52 and 53 s in the two runs paired with 1.3.0 the same day, against 49 and 54 s (50 to 53 s over the four runs of 1.4.0)", in both languages. The notebook's own times, from its run with 1.2.0, stay: M3 shows 1.4.0 returning its six formulas and constants |

**Its notes, beside the findings:**
- `release_claims/run_claims.py` takes the usage example from `README.md`,
  where it no longer is: it moved to `docs/usage.md` with the short README.
  The records of 1.4 are not touched (M3 and part c ran on copies of
  fbe9b00 and ec44e8e, before the move). The script and the driver that
  copies the READMEs are to be brought to `docs/` in the plan of the next
  release.
- The source of the LAPACK messages in M4, `check_positive_only_tag_during_fit`,
  is not recorded in `m4/`; the reviewer found it consistent with the tests
  and with L1, after which the messages are gone (`l1/m4_summary.txt`).
- `CITATION.cff` gives 1.4.0 with the date of 1.3.0: left to gate 12.

Two shorthand paths of this README were made complete on the way
(`../../results_1.3/release/m3/examine/` and
`m3/case_nikuradse/nikuradse_seed1.txt`), and one of the pages of the limits
(`benchmarks/results_0.9/release_1.0/m3/kepler_minmax_check.txt`).
