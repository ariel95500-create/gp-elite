# M5, second independent review (12 October 2026)

A second agent, who had seen neither the work nor the first review, checked
about 462 claims of the same documents after the corrections of the first
review, and the answers of `M5_review1.md`. Every number of M2, M3 and phase
3 recomputed exactly from its record; 19 findings concern the claims around
them. Each is corrected or answered below.

| # | Finding | What was done |
|---|---|---|
| 1 | The CHANGELOG said `date-released` is 5 October while `CITATION.cff` now gives 12 October | Corrected: the entry says the date of 0.8.0 was corrected to 5 October and that the file now gives 0.9.0 and the day of its publication |
| 2 | The notebook titles still gave durations ("fifteen minutes", "dix minutes"), and "a few seconds" for the install | Corrected: the titles give the steps only, and the install line no duration |
| 3 | The answer to #6 of the first review said the durations were removed | True now; the answer says when |
| 4 | The answer to #10 cited reruns that had no record; five scripts behind other records still left `parallel=None` | The reruns are recorded in `m3_rerun/` (with `run_info.txt`), and `notebook_claims.py` and `real_nikuradse.py` now pass `parallel=False`; `kepler_demo.py`, `kepler_plot.py` and `pools_check.py` give the same results with the islands in parallel (`m3_rerun/parallel_islands/`) |
| 5 | The README examples print outputs measured with the islands in sequence, while their code runs them in parallel from four cores | Checked on this machine: the Kepler block returns the same law in parallel; the "Programmatically" example returns another model (an approximation of validation R² 0.99998, 14 nodes). It now passes `parallel=False`, and the README says why; its sentence "finishes on one core with the same result" is corrected (the sequential islands can give another model). The notebook cells whose output the text quotes (Nikuradse short run, three cells of the TP) also pass `parallel=False`; in the TP, the monkeypatch of its experiment would not reach parallel workers anyway |
| 6 | "78 Feynman equations the engine was not developed on": nine are in an old development file | Corrected: "absent from the decision bench", the definition of the test set |
| 7 | "Every figure ... measured again on the wheel" | Corrected in the CHANGELOG and this folder's README: the figures 0.8.0 had measured; the new ones come from the records of the 0.9 work, those describing 0.7 or the 0.8 campaigns are kept as measured |
| 8 | The times of the unknown-constant mode rest on one unpaired run per law, islands in parallel | Removed from the CHANGELOG |
| 9 | "the same least-squares test, millions of times": 552,547 solves under a cache | Corrected: "the same test of whether a dimension can be built from the inputs (hundreds of thousands of least-squares solves)" |
| 10 | The overrun of `time_limit=` includes the generation under way | Corrected in both READMEs: "the generation under way and the final selection", 17.0 to 17.7 s with the reruns below |
| 11 | The paper sends the 0.9.0 figures to `release/`, while the ratio comes from `phase3/` | Corrected: `benchmarks/results_0.9/` (`phase3/` and `release/`) |
| 12 | PLAN_PHASE3: the check of 0.8.0 on this machine had no record | Recorded: `phase3/compare_E0_0.8.0_this_machine.txt` and the models in `phase3/equiv_0.8.0_this_machine/` (run on 11 October before U0) |
| 13 | PLAN_PHASE3: the times of the keys and of reachability overlap | Corrected: the text says they overlap and no longer derives "the rest" |
| 14 | PLAN_PHASE3: "hence 180 s for the 149 s" | Corrected: 0.605 s against 0.53 s per untyped generation, and U0's 179.6 s against the README's 149 s |
| 15 | The reruns of `time_limit_check` had no provenance | Run again alone, 0.8.0 then 0.9.0, with engine, version, date and command in the files (`m3_rerun/time_limit_check_*.txt`: 0.8.0 17.2 s and 17.2 s, 0.9.0 17.7 s and 17.1 s, 15 of 16 each); the two files without provenance are removed |
| 16 | SHA-256 of the wheel, package versions and time slices had no record | `environments.txt` (hashes, `pip freeze` of the three environments), `m2/driver.log` (five slices, not four: corrected) |
| 17 | The TP note of the author (4 problems, 15 datasets, p ≈ 0.24) has no record | Answered as in the first review: the author's own text, uploaded by him; submitted to him at gate 3 |
| 18 | "departs from `predict()` on exactly those rows": the record gives two equal counts, not the rows | Corrected: "on 304 rows too" |
| 19 | The Windows runner event of the CHANGELOG had no record | The CHANGELOG cites the run: https://github.com/ariel95500-create/gp-elite/actions/runs/37277459477 (started by the tag v0.8.0, Python 3.14 on Windows, failed) |

Found while answering #5: the warning the engine prints when parallel
islands cannot start (no `if __name__ == "__main__":` guard) says "results
are identical, only slower", which is not true of the model (the islands in
sequence take another path). It is text of the engine, in the wheel that was
measured; changing it is left to the author at gate 3.
