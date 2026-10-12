# M5, first independent review (12 October 2026)

A second agent, who had not seen the work, checked 284 claims of the
CHANGELOG (section 0.9.0), the two READMEs, the paper, the notebooks, this
folder's README and the results of `PLAN_PHASE3.md` against the records, and
reported 19 findings. Each is corrected or answered below.

| # | Finding | What was done |
|---|---|---|
| 1 | "More than five times faster" with `units=` rests on II.11.3 alone; the unknown-constant mode gains 1 to 2 times | Corrected: the claim names II.11.3 everywhere (CHANGELOG, both READMEs, this folder's README). The CHANGELOG first gave the unknown-constant mode its own times; the second review found them too thin (one unpaired run per law, islands in parallel), and they were removed |
| 2 | A paragraph of the paper kept the 0.8 times (149, 21, 84 s) under a 0.9.0 label | Corrected with the 0.9.0 record: 34 s constrained, 29 s unconstrained, 114 s with four times the generations |
| 3 | "1.2 times longer at equal generations" compares medians of different seeds | Corrected: the paper gives the per-generation ratio of the paired phase 3 timing (1.4, ten seeds side by side) |
| 4 | The paper said its figures are recorded in `results_0.8/` | Corrected: `results_0.8/` and, for 0.9.0, `results_0.9/release/` |
| 5 | Paper dated 30 September, AI use "May to September" | Corrected: 12 October 2026, May to October |
| 6 | "five steps, fifteen minutes" against "quatre étapes, dix minutes" | The step counts are those of each notebook (the French one has no Nikuradse section, a known gap); the durations had no record and are removed, from the READMEs first and, after the second review, from the titles of the notebooks too |
| 7 | "each version is measured once": 0.8.0 was measured twice | Corrected: "never used to make [a decision], on which each release is measured" |
| 8 | The evidence for keeping the default on real data concerns `normalize='smart'`, not `'none'` | Corrected in the CHANGELOG and both READMEs: they now say that leaving columns of close scales as given (`'smart'`) predicted worse out of the training range |
| 9 | "each fit started with both versions at the same time" overstates: only M2 was paired | Corrected: the CHANGELOG says the pairing was on the whole suite of the 0.9 work (M2) |
| 10 | The "Reproduce" scripts leave `parallel=None`, which runs the islands in parallel from four cores | Corrected: `feynman_bench.py`, `duel.py`, `feynman_units.py`, `feynman_scaling.py`, `test_constante_mystere.py` and `examples/robust_regression.py` pass `parallel=False`, as `ab_ood.py` does, and after the second review also `notebook_claims.py`, `real_nikuradse.py`, the README example that prints a model and the notebook cells whose output the text quotes; run again without the switch of M3, they give the records exactly (`m3_rerun/`, recorded after the second review) |
| 11 | TP notebook: "the MSE falls, but the size grows", while nothing changes from 30 to 60 generations | Corrected: "from 10 to 30 generations... from 30 to 60, nothing changes" |
| 12 | TP notebook: the author's measurement (4 problems, 15 datasets, p ≈ 0.24) has no record | Answered: the note is the author's own, uploaded by him (commit `df8b41f`) before this work; its records are not in the repository. Left as written; submitted to the author at gate 3 |
| 13 | Notebook durations ("a minute or two", "one to two minutes") | Corrected: "about half a minute" (34 s recorded) and "a few minutes" |
| 14 | The restarts check bounds the overrun at one generation plus two seconds, not one | Corrected in this folder's README |
| 15 | The robustness and small-data records differ in the engine path and times | Corrected: "identical apart from the engine path and the times" |
| 16 | The CI status had no record in the repository | `M4_ci_runs.txt` lists the runs from the release commit on (all green; one documentation push has no run) |
| 17 | Profile counts misrounded (55 million, 552,000); two figures not in the printed top 25 | Corrected: 56 million and 553,000; the profiles are printed with their 45 largest entries and the shared steps are named with their own times |
| 18 | "105 s under the profiler against 519 s" mixes the process and the fit | Corrected: the fit took 103 s against 519 s |
| 19 | The 0.8.0 baseline quoted as 179, 179.6 and 180 s; the exit table mixed U0 and the paired timing | Corrected: the paired timing everywhere (178.9 s, written 179 s), both columns of the exit table from it |

Outside the scope of figures, the review noted that `CITATION.cff` still said
version 0.8.0: it now says 0.9.0, dated 12 October 2026, to be set to the day
of publication.
