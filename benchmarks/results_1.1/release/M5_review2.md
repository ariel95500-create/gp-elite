# M5, second independent review (30 October 2026)

Another agent, who had not seen the work nor the first review before its own
check, checked about 520 claims (about 270 distinct) of the same documents,
with `M5_review1.md`, `../srbench_2aabbb6/README.md` and the corrections of the
first review. It recomputed the headline figures and confirmed them: the seven
criteria, U41 108 to 165, the five families 16 to 57, 1,005 of 1,005 models
passing the audit, TF78 under units 169 to 226, 47 of 1,775 jobs differing
without units, all at the budget; `compare.txt` and `details.txt` byte for
byte when their scripts are run again; the II.11.3 table, Feynman 15 with and
without units, the duel, the scaling, `time_limit` run alone, the TP notebook,
its pair of runs, the gas and free-fall timings, the U2 check, the campaign of
the change, every figure of the Kepler and Hubble studies in both languages; no
change of the engine or the tests since the measured candidate; the four
SRBench files by hash. It found the corrections 2 to 16 of the first review
right, and reported 12 findings (its report: `m5/review2_report.md`). Each is
corrected or answered below.

| # | Finding | What was done |
|---|---|---|
| 1 | The intro of the limits omitted point 6, where this campaign gives 7 and 66 departing formulas for 1.0.0 and 8 and 67 for 1.1.0, against 7 and 61; "for both versions alike" did not hold there | Corrected in both languages: point 6 added, "alike" removed |
| 2 | "The same counts without units on the frozen set" overstated in both READMEs and the paper (one Strogatz collapse and five departing formulas more) | Corrected: "the same counts of exact laws" |
| 3 | `../srbench_2aabbb6/README.md` gave the lines of the defaults as those where `est` is built | Corrected: `est` at lines 129 to 136, the defaults at lines 40 to 46 being the same |
| 4 | `../PLAN_U2.md` and `../mechanics/U2_gas_law.txt` pointed to records that moved to `candidate1/` | The new paths added beside the old ones |
| 5 | `candidate1/README.md` said "the typed fits" of Kepler changed; only the fit on the inner planets did | Corrected, with a note |
| 6 | The AI disclosure of the paper listed contributions up to 1.0 | A line for 1.1 added: the seeds under declared units and the restriction of fitted exponents. Put to the author at gate 6, as the disclosure is his |
| 7 | `LIMITATIONS.fr.md`: "cinq graines aléatoires", where the seeds are 0 to 4 | Corrected: "en cinq graines" |
| 8 | The CHANGELOG said the finders "now run as without units", while U2 restricts them under units | Corrected: "now run under units too, on the same rows and with the same thresholds" |
| 9 | `../ROADMAP.md`: "version 1.1 places the law at generation 0" on the TP notebook, traced for two fits only | Corrected: "for some fits (traced for the free fall and the gas law)" |
| 10 | `../ROADMAP.md`: "no date ... in the repository or elsewhere" with no record of where else | Corrected: "no date ... is given in the repository" |
| 11 | The free-fall timings had no command, date or log | `m3/tp_timing/fall_timings.txt` now says when and how they were run; the whole trace of one run per version is in `m3_extra/` |
| 12 | The paper is dated 14 October 2026 | Answered: the date of the paper, like that of `CITATION.cff`, is set to the day of publication at gate 6 |

Also, from the reviewer's notes: the Hubble notebooks now name the 1.1.0 output
beside the first one, as the Kepler notebooks do.
