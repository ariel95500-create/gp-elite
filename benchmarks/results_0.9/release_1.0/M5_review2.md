# M5, second independent review (14 October 2026)

A third agent, who had seen neither the work nor the first review, checked
about 380 claims (about 260 distinct) of the same documents after the
corrections of the first review, and the answers of `M5_review1.md`. It
recounted the headline figures from their records and found them right: the
lines of M2 from `m2/campaignR_*.jsonl` (163/205 against 88, 213/390 against
145, 105/85 against 67/66, 55/90, the targets of gate 2, the 15 of 630 real
fits that differ), the records of M3 (15/15 against 6/15, 14/15 with units,
58.2 s and 150.6 s for the size study, the time-limit figures, −20 % and
+344 % for the deduced constant, the import time, the battery, the robust
table, the console), every number of the case studies, recomputed from the
data files and the telemetry, and the agreement of the English and French
texts number for number.

## The corrections of the first review

17 of the 20 held, two held in part (5 and 11) and one did not (7).

| # | Verdict of the review | What was done |
|---|---|---|
| 3 | Held; this folder's README says "does not change these counts" rather than the wording `M5_review1.md` gives, which is harmless | Nothing; new findings 7 and 8 take up what was left |
| 5 | Held in part: the count of targets is right, but the same paragraph says 0.9.0 measured on "the same machine type" and leaves out its own TR25 count | New finding 1 |
| 7 | Not held: the SRBench pull request has no record in the repository | New finding 4 |
| 11 | Held in part: two more forms meet the test of section 6 | New finding 6 |
| 12 | Held; Jupiter's mass still has no record in the repository | New finding 11 |
| 13 | Held; the evidence cited for "no seed under units" does not show it | New finding 12 |
| 18 | Held in both READMEs; "the launch texts present it the same way" cannot be checked from the repository | Answered: the launch texts are not in the repository; they are delivered to the author with the release, outside it, and say "PySR is faster and more accurate at scale, and I say so in the README" |
| 20 | Held as answered: the date of `CITATION.cff` is set to the day of publication | Nothing |
| 1, 2, 4, 6, 8, 9, 10, 14, 15, 16, 17, 19 | Held | Nothing |

## New findings

| # | Finding | What was done |
|---|---|---|
| 1 | This folder's README said 0.9.0 measured its release "on the same machine type"; it ran on an Intel Xeon at 2.8 GHz, 1.0.0 on one at 2.1 GHz. The TR25 target is said missed by both versions, while 0.9.0's own release measured 36, which met it. The differences between 0.9.0 here and its release leave out TS14 (7 → 8), the R7raw collapses (5 → 6) and TR25 (36 → 37). The 0.9.0 times in parentheses come from the 2.8 GHz machine without saying so. `PLAN_RELEASE_1.0.md` says the starting values of gate 2 were measured on another processor, while they were measured on the 2.1 GHz type | Corrected in this folder's README (M3: the parentheses come from the release of 0.9.0, on the 2.8 GHz processor, and its times do not compare directly; M2: 10 and 36 for the release of 0.9.0, both targets met then, and the full list of differences). `PLAN_RELEASE_1.0.md` keeps its sentence, written before the measurements, and gains a dated note that corrects it |
| 2 | The READMEs, the paper and the CHANGELOG gave the frozen test set for Feynman and the real datasets only, leaving out TS14, where 1.0.0 is below 0.9.0: 7 exact fits of 70 against 8 | Added in both READMEs (the paragraph of the test set and the entry of 1.0), the paper and the summary of the CHANGELOG |
| 3 | I.16.6 was called "a form 1.0 fits directly only without units"; it is not one of the forms fitted directly, it is reached by the search (41 s in `m3/feynman15.txt`), and `PLAN_PHASE5.md` credits N1 with it. This folder's README credited every change to B1 and E1 | Corrected in both READMEs: a nested rational form that is not among the forms 1.0 fits directly, reached by the search; the sentence on its miss with units no longer explains it. This folder's README names N1 and cites `PLAN_PHASE5.md` |
| 4 | The paper's sentence on the SRBench integration has no record in the repository | The paper gives the address of the pull request (https://github.com/cavalab/srbench/pull/227), which the reader can open; it is on another project, outside what this work can read. The sentence is the author's: it is put to him at gate 4, with the question whether the integration has been merged, and removed if he does not confirm it. *Answered on 14 October, at gate 4:* the author read the page of pull request 227, "Merged" by a maintainer (gAldeia) into the `dev` branch of cavalab/srbench, one commit from `ariel95500-create:claude/peaceful-knuth-4q7m4p` (`4b4a142` in the author's fork, ariel95500-create/srbench). The fork records the integration itself too: the merge commit of pull request 212, of 17 September 2026 (`409beb3`), in the history of cavalab's `master`. The paper says so, with both addresses |
| 5 | "With units in 2 of 5, in 27 seconds (median)" reads as the time to find the law; 27 s is the median of the five runs, the two exact ones took 3.2 s and 15.5 s | Corrected in both limits pages: in 3 and 16 seconds; the three others end on approximations after 27 to 32 seconds |
| 6 | Nikuradse: the count of log-of-log forms leaves out seed 1's 41-node form of the random split and its 69-node form of the removed roughness (gap −0.197) | Corrected in both notebooks and `PLAN_PHASE6.md`: 30 and 41 nodes for seed 1 and 70 for seed 4 on the random split; 12, 14 and 69 nodes for seed 1 and 37 and 39 for seed 3 on the removed roughness, which miss its level by 0.20 to 1.20 standard deviations. The conclusion is unchanged |
| 7 | The B1 entry of the CHANGELOG said "on real or noisy data nothing changes", against its summary and the N1 entry | Corrected: on real or noisy data this change alone places nothing; the noise-tolerant seeds lift that threshold |
| 8 | "The same number of collapses" unqualified in the READMEs; the count of negative R² on the TR25raw folds moves from 7 to 8 | Corrected in both READMEs, in both places: "out of the training range", as the CHANGELOG and the paper say |
| 9 | This folder's README said the test had failed on GitHub since its commit; run 66 passed | Corrected: 6 of the 7 runs, run 66 passed |
| 10 | The limits pages promised a 1.0.0 measurement for every point; point 9 had none, point 8's 1.4 comes from phase 3 | Corrected in both languages: "unless a point says otherwise"; point 8 cites phase 3 and says the typed search of 1.0 is the same; point 9 gives the range of the measurements (10,000 rows at most, in the size study), says nothing is measured beyond it, and no longer says the search space "explodes" beyond fifteen to twenty variables |
| 11 | The Kepler notebook's 1/1047 for Jupiter had no record in the repository | Recorded: the header of `examples/case_studies/data/planets_simon1994.csv` quotes the inverse masses of the same source file; the notebook gives 1/1047.355 and cites that header. 1/1047.355 is 0.095 %, the "about 0.1 %" of the text. `examples/case_studies/README.md`, which said every figure of the notebooks comes from `case_studies.py`, now says every measured figure does, and that the data files give their sources |
| 12 | `PLAN_PHASE6.md` cited `hubble.txt` for "the seed functions return nothing under units"; on those data the untyped fits place nothing either | Corrected: the plan cites the code, where each of the four seed functions returns nothing when `_dim_active` holds (`gp_elite/core.py`) |
| 13 | `PLAN_PHASE6.md` said the notebook scripts used data from the files of the repository, while Nikuradse's came from the PMLB file outside it; this folder's README said the notebooks print every figure their text quotes | Corrected: the plan names the PMLB file the benchmarks check by SHA-256; this folder's README says the notebooks print the figures of seed 0, and that the others (seeds 1 to 4, the inner planets without units) come from `benchmarks/case_studies.py` |
| 14 | The READMEs said the case studies show "what it returns on real measurements"; the Kepler notebook says its table is not raw observations | Corrected in both READMEs: "on public data" |

None of these corrections touches the package: `gp_elite/` is the same as in
the wheel measured in M1 to M4.
