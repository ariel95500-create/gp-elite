# M5, first independent review: the documents against the records (24 November 2026)

An agent that had seen neither the work nor the other review checked the
claims about 1.5 in thirteen documents, HEAD 6950444: 210 statements, of
which 289 figures were recomputed from their raw records with read-only
scripts that import nothing of the engine and run no fit (`m5/review1/`).
Every French page was compared with its English page, sentence by sentence
and figure by figure. It disclosed that one `grep` over this folder printed
six comment lines of a file the other reviewer had just created; nothing
else of that review was read. No figure stated in the documents is wrong
when recomputed from its raw record, and the two languages never differ. It
reported 27 findings (`m5/review1_report.md`): sentences that claim more than
the records show, statements about the code that the code contradicts, and
claims without a committed record. Each was checked against the record or
the code it names, and holds. Each is corrected, in the commits of this
file, or answered below.

| # | Finding | What was done |
|---|---|---|
| 1 | The architecture pages advised replacing a function "where it lives" to observe it during a fit; `search` and `parallel` import `evolve_island` by name, so that reaches none of the calls of a fit | Both pages: set it on `gp_elite.core`, which passes it on to every module of the engine that holds it; replacing it only in the module where it lives is not enough, and why |
| 2 | The pages said `split/layout_core.py` checks the order of the modules; it checks the plan of 1.4.0's single file | A new test, `tests/test_layering.py`, reads the modules: each imports only the modules above it in the table, none imports `gp_elite.core`, and a module outside the engine only inside a function; it also holds the table's list against the files of the package and against the door. Its negative control (`m5/after/layering_negative_control.*`) plants four faults, all caught. The pages cite the test |
| 3 | "None imports `core.py`": three modules import, inside functions, `dim_search`, `formula` and `dimensions`, which import `gp_elite.core` | Both pages say which functions import modules outside the engine, and that these import `gp_elite.core`; the test allows it only inside a function |
| 4 | "Up to 100,000 rows, little": the reading written before the run gives "mostly brute force" (L = 11, R = 6) | The CHANGELOG, both feature pages and the size README give the pre-registered reading, by a margin of one fit, and the 11 exact laws of 205 |
| 5 | The raw runs of A1 were not committed, though the plan lists them | `split/a1/runs/`: the 23 runs of the split and of the first candidate, and the run of the second, with a README that maps each to its comparison. `M1_A1.txt` was made again from the copies: the same |
| 6 | The CI claims of the split had no committed record; the failing run read "55 failed, 145 passed, 6 errors"; no record showed `test_door.py` failing on the former door under pytest 9.2 | `ci_runs.txt`: the runs of the branch, the jobs of the run of 3190a7c and the summary line of its job under Python 3.11. The split README: every run from the push of Split 1 to 6ba1356 failed, 7 of 8 jobs in the run read, 55 tests of 200 and 6 errors at teardown, the job under Python 3.9 (pytest 8.4) passing. `split/former_door_check.*`: the test of eb2eac5 on the former door, 63 failed and 61 errors under pytest 9.2.0, 69 passed under 8.4.2 |
| 7 | "Green on every commit since eb2eac5": four commits that change only `.md` files have no run, and the sentence was written before two runs had ended | This README: green on every commit of the branch that has a run, read after the runs ended (`ci_runs.txt`); the workflow does not run on commits that change documents only, and those commits are named |
| 8 | "Field by field" overstates: the console is compared on its result lines, and the records of the 615 fits keep the first 160 characters of a formula | The CHANGELOG, this README and the split README say what A1 compares: the 13 configurations whole, the records field by field with their formulas to 160 characters, and the console on its result and the formula it writes |
| 9 | "61 names change while a fit runs": 9 are switches only the tests set | The CHANGELOG and both architecture pages: 52 change while a fit runs, and 9 are switches of the seeds and of the final choice that only the tests set |
| 10 | "Scripts written for 1.4.0 work unchanged": only the tests were run unchanged, the benches were changed (f0681bb), and a script that reads the module's dictionary no longer finds the state | "The tests of 1.4.0 pass unchanged", and what the door does not keep is listed (the CHANGELOG, both architecture pages, with the second review) |
| 11 | "Ten times the time gives back 12 of the 60" is a difference of counts | `size/fit_by_fit.py` and `.txt`: of the 61 fits lost with 20 added variables, 10 come back at 10T (2 through a formula on an added variable), 4 others become exact and 2 exact at T are lost; of the 12 fits lost at 100,000 rows, 6 come back. In the size README, both limits pages and the CHANGELOG |
| 12 | "Nothing a user can observe changes": the import takes 0.102 s against 0.093 s, and `gp_elite.core` is an instance of `_Door` | The CHANGELOG and both architecture pages: the models, the interface and the speed do not change, and the changes visible from inside `gp_elite.core` are listed, the import time among them |
| 13 | The READMEs: "these figures hold for it" should say within the noise of a time budget | Both READMEs and both limits pages: within what a budget of 30 s per fit moves between two campaigns of the same version (up to three fits on these suites) |
| 14 | "The same formula in all 205 jobs": the records keep the first 160 characters | This README: the same first 160 characters, which is what the records keep |
| 15 | The amendment of the plan said `map.txt` was corrected in 81ed9c3 and c7e00fa; it changed in c7e00fa only | The amendment: `map.txt` made again in c7e00fa by the script corrected in 81ed9c3 |
| 16 | "The budget study of 1.2 measured up to three fits": it cites that figure from the release campaigns of 1.0 to 1.2 | The size README says so |
| 17 | "Ten equations ... fall to 0 or 1", then I.8.14 apart: by that criterion there are eleven | The size README: eleven, ten whose law the seeds held, and I.8.14, whose law the search finds |
| 18 | "The time of a fit hardly grows" with added variables: I.8.14 takes 7.0 s without them and 4.4 s, 3.9 s and 4.1 s with them | The size README: its time falls |
| 19 | The ratios of cProfile were given as single values | The size README: 2.26 to 2.40 at 100 rows, 1.05 to 1.17 at 100,000 |
| 20 | "Two lambdas": 22 lambdas in two tables | The split README: the parameters (`a`, `b`) of the 22 lambdas of `_SYMPY_UNARY` and `_SYMPY_BINARY` |
| 21 | "The order of the commits of a move changed once": no move was committed with its check | The split README tells it as it was: the first design of `run_moves.py` (2df5225), changed in bcbac70 before any move was committed; Split 1 committed while its check ran (71902c3), its check in 0068717 |
| 22 | "Every fit in its own process": configuration M_twice runs two fits in one process | This README says so |
| 23 | The cores, the Python of the environments, the restart before the first candidate and the end of M4 had no record | `machine.txt` and the environments of the second candidate record the cores, the processor, the kernel and the Python of each environment; this README gives the end of M4 as the time of its last file, 08:15:48, and says where the time of the restart comes from |
| 24 | The uptime and the kernel in the deviations of the size study had no record | The size README gives what `profiles.jsonl` shows, the times of the records around the stop, and says the kernel was not recorded |
| 25 | "The container did not restart", left from before a correction | The size README: the machine did not restart during the campaign, one driver process from the first fit to the last |
| 26 | The docstring of `state.py` said the memories are made by `gp_elite.core` | Corrected in f5fc346: by `gp_elite.memory`, each after its class |
| 27 | The comment of `test_door.py` said "pytest 9" | Corrected in f5fc346: since pytest 9.2 |
