# M5 of 1.5.0, review 1: the claims of the documents against the records

- **HEAD reviewed:** 6950444 (branch claude/peaceful-knuth-4q7m4p), "Release 1.5.0: M4 ended at 08:16, not 08:17".
- **Date:** 24 November 2026.
- **Claims checked:** 210 statements about 1.5 in the 13 documents (CHANGELOG 28, the two READMEs 7, the architecture pages 62, the two feature pages 7, the two limits pages 21, the amendment of the plan 10, the size README 42, the split README 18, the release README 15). A table drawn from one record counts as one statement; its figures are counted below. Every French page was compared with its English page, sentence by sentence and figure by figure.
- **Figures recomputed from raw records:** 289, counting a figure once each time a document states it: 239 from `size/campaign.jsonl`, 27 from `size/profiles.jsonl`, 11 from `split/a3_timing.jsonl` and `release/M1_A3_timing.jsonl`, and 12 from the raw runs of A1, which are not committed (they are in `/home/user/a1_140`, `a1_140b`, `a1_final` and `a1_rel`; see finding 5).
- **Method:** read-only scripts in `release/m5/review1/` (`size_recompute.py`, `a3_recompute.py`, `a1_recompare.py`, `map_counts.py`, `modules_ast.py`, `state_rule_ast.py`, `wheel_and_names.py`, `en_fr_numbers.py`, each with its `.txt` output). None imports `gp_elite` and none runs a fit; the code was read as text or with `ast`, the history with `git log` and `git show`. Two sources outside the repository were read and are labelled as such: the uncommitted A1 runs in `/home/user`, and the history of the Tests workflow on GitHub (`review1/ci_runs_github.txt`).
- **Note on independence:** one recursive `grep` over `release/` (looking for "06:52") also printed six comment lines of `release/m5/review2/core_1.4.0.py`, a file the other reviewer had just created (a copy of the 1.4.0 `core.py`, by its name and content). Nothing else under `review2` was read, and every later search left that folder out.

## Findings

No figure stated in the documents is wrong when recomputed from its raw record: every count, median, total and ratio of the size study and of A3 comes back. The findings are about what the sentences claim beyond the records, statements about the code that the code contradicts, and claims without a committed record. They are ordered by weight. Each finding on an architecture page holds for the English and the French page alike; the two languages never differ.

| # | document and line | the claim | what the record or the code shows (with the file) | kind |
|---|---|---|---|---|
| 1 | `docs/architecture.md` 91-92; `docs/fr/architecture.md` 92-94 | "To observe a function during a fit, for example to count the generations, replace it where it lives, or set it on `gp_elite.core`, which passes it on." | `evolve_island` lives in `gp_elite/islands.py`, but `search.py` (line 35, call at 683) and `parallel.py` (line 22, call at 109) import it by name and call their own reference. Replacing it only in `gp_elite.islands` reaches none of the calls of a fit: the count of generations stays at zero. The benches' `_wrap` (`benchmarks/phase1_bench.py`) and `_holders` in `tests/test_door.py` set it in every module that holds it, which is what works. Only the second half of the advice (set it on `gp_elite.core`) is right. | says more than the records show (the code contradicts it) |
| 2 | `docs/architecture.md` 89-90; `docs/fr/architecture.md` 90-91 | "A module imports only from the modules above it in the table. `benchmarks/results_1.5/split/layout_core.py` checks the order." | `layout_core.py` reads `core.py` at 6dc1e35 through `git show` (`map_core.REV`, `map_core.py` line 32) and the plan `layout.txt`, whose order even starts with `core`. It checks the planned layout of the single file of 1.4.0, not the modules in `gp_elite/`, so it cannot check a contributor's change. | says more than the records show |
| 3 | `docs/architecture.md` 15-16 and 89; `docs/fr/architecture.md` 15-17 and 90 | "A module uses only the modules above it in this table, never one below it, and none imports `core.py`." | True of the imports between the modules of the table (`review1/modules_ast.txt`). But three of them import, inside functions, modules that are not in the table: `config._ds` imports `dim_search` (`config.py` 92), `final_choice._formula_faithful` imports `formula` (`final_choice.py` 69), `console` imports `dim_search`, `dimensions` and `formula` (`console.py` 1212, 1319, 1353, 1385, 1387). Each of these imports `gp_elite.core` at its top (`dim_search.py` 33 `from .core import Node`, `formula.py` 37, `dimensions.py` 19). So the engine still reaches `core.py`, through them. | says more than the records show |
| 4 | `CHANGELOG.md` 27-28; `docs/features.md` 65; `docs/fr/caracteristiques.md` 67; `size/README.md` 18-19 and 25-27 | "up to 100,000 rows, little, and mostly time"; "costs little up to 100,000 rows" | The reading written before the run (`size/compare_size.py`, output `size/reading.txt`) gives "mostly brute force" for rows (L = 11, R = 6). In the plan's table, "size costs little" is the reading for L below 10 only. The size README says the margin (one fit above the threshold); the CHANGELOG and both feature pages state "little" without it, a verdict the pre-registered rule did not give. | says more than the records show |
| 5 | `split/README.md` 17, 47-50, 54-55; `release/README.md` 26-30; `CHANGELOG.md` 12-16 | A1 "all identical", field by field, in the split, on the wheel, and for 1.4.0 run twice | Only the outputs of the comparisons are committed (`split/a1/*.txt`, `release/M1_A1.txt`). The runs themselves (`phase1_defaults.jsonl`, `tp.jsonl`, `equiv/*.json`, `console/`) are not, although `PLAN.md` ("Records") lists "the runs of A1 and their comparisons" under `split/`. A reader cannot recompute A1 from the repository. Compared again from the uncommitted copies in `/home/user` by `review1/a1_recompare.py`: all identical (13 configurations, 615 and 400 records, the console's result), for 1.4.0 twice, for the split and for the wheel. | no committed record |
| 6 | `split/README.md` 18, 59-69 | "the CI green on its whole matrix since eb2eac5" (record cited: `a2_local.txt`); "The CI failed from Split 1 to eb2eac5 ... 55 tests of 200 failed"; `test_door.py` "fails on the former door under pytest 9.2" | `a2_local.txt` holds the runs on the machine and one sentence on the CI ("55 tests of 200 in the CI"), no CI result. The GitHub history (outside the repository, `review1/ci_runs_github.txt`) supports the substance: failures from the push of Split 1 (head 2df5225) to 6ba1356, green from eb2eac5. But the log of a failing run (3190a7c, py3.11/ubuntu) reads "55 failed, 145 passed, 6 errors": 6 teardown errors more than the README says. No record shows `test_door.py` failing on the former door under pytest 9.2. | no committed record |
| 7 | `release/README.md` 53-57 | "The Tests workflow ... is green on every commit of the branch since eb2eac5 ...; from the first commit of the split to that one, it failed under pytest 9.2" | No committed record. The workflow ignores pushes that change only `*.md` files (`.github/workflows/tests.yml`, `paths-ignore`), so 4 of the 14 commits since eb2eac5 have no run at all: 8b405b0, f6a3134, 32d3dce and 6950444, the HEAD. The sentence was written at 08:08 (32d3dce) and kept at 08:16 (5210b72, 6950444), before the runs of 4685af2 (ended 08:12:43) and 5210b72 (ended 08:22:24) had ended; both ended green. "The first commit of the split": the commits of Part A before Split 1 that have a run (f0681bb to 5387f42) were green. "It failed under pytest 9.2": in the failing run read (3190a7c), 7 of the 8 jobs failed and py3.9 passed. | says more than the records show |
| 8 | `CHANGELOG.md` 12-16; `release/README.md` 29-30 | "the same models, field by field and to the bit, at equal seed and equal work: ... the TP diagnostic (400 fits) and the console"; "all identical, field by field" | `split/compare_a1.py` says the console fixes no seed, and compares only the lines of its result (6 lines, 3 of them prompts) and the file it writes, not field by field. Two runs of the same 1.4.0 differ in 19 of the 185 lines of the console's output (its islands, its memories; `/home/user/a1_140` against `a1_140b`, uncommitted). Its printed errors happen to agree in all four runs, but they are not compared. The phase1 records keep only the first 160 characters of a formula (68 of the 615 are cut); only the 13 configurations compare whole trees. | says more than the records show |
| 9 | `CHANGELOG.md` 23; `docs/architecture.md` 51; `docs/fr/architecture.md` 52 | "The 61 names that change while a fit runs" / "61 names change while a fit runs" | `split/map.txt` defines the 61 as run-time names: rebound by the engine, or set on `core` by the package or by the tests. Nine of them are switches that no fit changes, set only by the tests ("rebound by -; set by tests/test_guarantees.py"): `_BINOMIAL_SEEDS`, `_ELEMENTARY_SEEDS`, `_E2_SEEDS`, `_TOLERANT_SEEDS`, `_TOLERANT_N2`, `_TOLERANT_REFIT`, `_SEEDS_UNDER_UNITS`, `_SMALL_CV`, `_POLISH_GRACE_S`. | imprecise or stale wording |
| 10 | `CHANGELOG.md` 19-21; `docs/architecture.md` 71-72; `docs/fr/architecture.md` 72-73 | "so that scripts written for 1.4.0 work unchanged"; "Scripts, benches and tests written for 1.4.0 ... work unchanged" | The tests of 1.4.0 do: unchanged since 6dc1e35, they pass (269 with `test_door.py`). No script or bench of 1.4.0 was run unchanged on 1.5: `phase1_bench.py` and `tp_diagnostic.py`, which A1 and A3 run, were changed in f0681bb to set their wrap in every module. By design, a script that reads the module's dictionary (`vars(gp_elite.core)`, `gp_elite.core.__dict__`) no longer finds the 61 names of the state there (`tests/test_door.py` 38 asserts it). | says more than the records show |
| 11 | `LIMITATIONS.md` 256-257; `LIMITATIONS.fr.md` 282-283; also `CHANGELOG.md` 31 | "ten times the time gives back 12 of the 60" | R = 12 is a difference of counts (120 - 108). Fit by fit (`size/campaign.jsonl`, `review1/size_recompute.py`), 10 of the 61 fits lost at k = 20 are exact at 10T. 4 fits exact at 10T were not exact at 1,000 rows, 2 of them formulas built on an added variable that pass the threshold (II.24.17 seed 0, III.15.12 seed 4), and 2 fits exact at T are not at 10T. For rows, "6 of the 11" holds: 6 of the 12 fits lost come back. | imprecise or stale wording |
| 12 | `CHANGELOG.md` 7-8; `docs/architecture.md` 7; `docs/fr/architecture.md` 8 | "Nothing a user can observe changes" / "nothing a user can observe" | `release/M1_A3.txt`: the import of `gp_elite` takes 0.102 s against 0.093 s for 1.4.0 (median of 20; `split/a3.txt`: 0.106 against 0.102). By design, `gp_elite.core` is now an instance of the class `_Door`, and its dictionary no longer holds the names of the state. Small, but observable. | says more than the records show |
| 13 | `README.md` 106-108; `README.fr.md` 104-106 | "1.5 ... at the same speed, so these figures hold for it" | The figures of the table come from campaigns at 30 s per fit, a time budget. A1 shows the same models at equal work without a time limit, and A3 the same speed within 0.3 %. Under a time budget the counts move from one campaign to the next: `LIMITATIONS.md` (introduction) says so, and the plan of the budget study of 1.2 puts it at up to three fits. "Hold for it" should say: within that noise. | says more than the records show |
| 14 | `release/README.md` 37-38 | "the same formula in all 205 jobs (`M1_A3.txt`, `M1_A3_timing.jsonl`)" | The timing records keep the first 160 characters of each formula; 25 of the 205 are cut (the same in `split/a3_timing.jsonl`). The records show the same first 160 characters. | says more than the records show |
| 15 | `PLAN.md` 18 (amendment) | "the map of `core.py` (`split/map.txt`, corrected in 81ed9c3 and c7e00fa)" | 81ed9c3 changes `map_core.py` and `deps_core.py`, not `map.txt`: at 81ed9c3, `map.txt` still reads 45 run-time names. `map.txt` changes only in c7e00fa (`review1/map_counts.txt`). | imprecise or stale wording |
| 16 | `size/README.md` 20-21 | "The budget study of 1.2 measured up to three fits between two campaigns of the same version." | `results_1.2/budget_study/PLAN.md` 111-114 cites that figure from the release campaigns of 1.0, 1.1 and 1.2; the budget study did not measure it. (`PLAN.md` of 1.5, lines 171-173, words it correctly.) | imprecise or stale wording |
| 17 | `size/README.md` 115-119 | "ten equations exact in all five seeds without added variables fall to 0 or 1 ... I.8.14 falls from 5 to 1 from 5 added variables" | By that criterion there are eleven: I.8.14 (5 at 1,000 rows; 1, 1 and 0 with 5, 10 and 20 added) also falls to 1. The ten are the equations whose law the seeds held; I.8.14's law is found by the search (83 to 100 generations at 1,000 rows). The sentence does not say what sets the ten apart. | imprecise or stale wording |
| 18 | `size/README.md` 167-168 | "With added variables the time of a fit hardly grows (I.8.14: 4.4 s, 3.9 s and 4.1 s with 5, 10 and 20)" | Without added variables, at 1,000 rows, the same fit takes 6.95 s (`size/profiles.jsonl`; line 159 of the README gives "7.0 s at 1,000"). With added variables its time falls by 37 to 45 %. | imprecise or stale wording |
| 19 | `size/README.md` 172-173 | "a profiled fit takes 2.4 times its plain time at 100 rows and 1.05 times at 100,000" | `size/profiles.jsonl`: from 2.26 to 2.40 at 100 rows, and from 1.05 to 1.17 at 100,000 (I.12.1: 1.17). The two figures are the extremes, given as single values. | imprecise or stale wording |
| 20 | `split/README.md` 71-73 | "`move_group.py` read the parameters of two lambdas at the top of the tree section" | `gp_elite/tree.py`: 22 lambdas in two tables, 15 in `_SYMPY_UNARY` and 7 in `_SYMPY_BINARY`, with parameters `a` and `b`. 398e94d says "the parameters of the lambdas in `_SYMPY_UNARY` and `_SYMPY_BINARY` (a, b)". | wrong figure |
| 21 | `split/README.md` 75-77 | "The order of the commits of a move changed once (bcbac70): at first a move was committed with its check" | Committing a move with its check was the first design of `run_moves.py` (2df5225). It was stopped during its first check (numeric) and changed in bcbac70 before any move was committed. Split 1 was committed while its check ran (71902c3: "The short A1 is running"), and its check came in 0068717. No move was ever committed with its check. | imprecise or stale wording |
| 22 | `release/README.md` 4-5 | "Every fit runs in its own process with `PYTHONHASHSEED=0` and one BLAS thread." | Configuration M_twice of `benchmarks/speed_equivalence.py` (lines 113-118), part of A1, runs two fits in one process, by design. | imprecise or stale wording |
| 23 | `release/README.md` 4, 15-16, 20-21, 49 | "The machine has 4 cores"; `/venv15r` "(Python 3.11.18 ...)"; "The machine restarted at about 06:52 UTC ...; nothing was running"; M4 "from 08:05 to 08:16" | None of these is in a committed record of `release/`. `M1.log` gives the processor's name and the kernel, not the cores. `environments.txt` lists packages, not Python, and `M1.log` shows only the path `python3.11`. No record has the restart. `m4/summary.txt` records the start of M4 only; on disk the M4 files were last written at 08:15:48, which is 08:15 by the truncated minutes the other records use (`M1.log`, `size/driver.log`). | no committed record |
| 24 | `size/README.md` 178-185 | "(its uptime counts from 02:00 UTC)"; "the kernel, read after the restart, is 6.18.44-fc-v819" | No record in `size/` has the uptime or the kernel. The only kernel record, `release/M1.log`, was read at 07:04, after a later restart. The profile records are consistent with the rest of the paragraph: last record before the stop at 01:28:31, the rerun of I.8.14 at 100,000 rows started near 02:00:43, 21 of 42 records before it. | no committed record |
| 25 | `size/README.md` 74-75 | "The container did not restart: one driver process ran from the first fit to the last." | 12299bc changed "container" to "machine" in the Deviations ("the machine of the session restarted after 01:28 UTC"; "no restart of the machine during the campaign") but left this sentence. Read alone, it contradicts the Deviations; it should speak of the campaign and of the machine. `size/driver.log` does show one driver process (one header line). | imprecise or stale wording |
| 26 | `gp_elite/state.py` 8-10 (docstring; outside the listed documents) | "The three memories (FRAGMENT_LIB, COGRAPH, SEQ_MEM) are made by gp_elite.core when it is imported, at the place where 1.4.0 made them." | Since Split 11 they are made by `gp_elite/memory.py` at its import (lines 446, 870, 1336). | imprecise or stale wording |
| 27 | `tests/test_door.py` 40 (comment; outside the listed documents) | "(pytest 9 puts back what it read in the module's own dictionary, ...)" | `split/a2_local.txt`: the former door failed from pytest 9.2, and passed under 9.1.1. It asks for "since pytest 9.2, not since pytest 9" in the message of eb2eac5; the comment of the test has the same error. | imprecise or stale wording |

## What was checked and found to agree

**CHANGELOG, the 1.5.0 entry**
- `core.py` of 1.4.0 has 12,999 lines (6dc1e35).
- The 17 modules match the 17 roles of the map besides its header, plus `state.py`.
- M1 on the wheel: A1 all identical (13 configurations, 615 fits of F41, U41 and F41N1, 400 TP fits, the console), in `M1_A1.txt` and in my comparison of the raw runs.
- A3 recomputed: 694.66 s against 695.86 s, ratio 0.99828; the engines ran interleaved fit by fit as the script says (205 of 205, read from the order of the keys).
- `test_door.py` is new: 69 tests, 421 names.
- The 61 names: none is copied anywhere. No module binds a state name at its top, imports from `state`, declares it `global` or reads `state.NAME` at import (`review1/state_rule_ast.txt`). The four names read through `getattr(state, ...)` are read at run time.
- The size figures 154 and 165, 6 of 11, 108 and 168, 12 are recomputed. The seed finders' caps are as stated (`seeds.py` 359-418, 629-643).

**README.md and README.fr.md**
- The note on 1.5 and the link in the Documentation list, both present.
- The two languages say the same.

**docs/architecture.md and docs/fr/architecture.md**
- 12,999 lines; "within 0.3 %" (ratios 1.0028 and 0.9983, both recomputed).
- The 19 line counts, by `wc -l`.
- Each description matches the module's top-level names (`review1/modules_ast.txt`).
- No module of the table imports core or a module below it directly.
- `api`, `sklearn_api`, `formula`, `dimensions`, `dim_search`, `stability` and `cli` are unchanged since 1.4.0 (hashes in `environments.txt` equal to 6dc1e35).
- `api.py` calls `core.evolve`.
- `_USE_LINEAR_SCALING` and `_TIME_LIMIT_HIT` exist in `state.py`.
- The three rules of the door match `core.py` 518-603: descriptors for the 61 names, passing on to the modules that hold the same object.
- `test_door.py` checks the 421 names, sets and puts back each state name (deletion included, for the names no fit has set yet, as when it runs alone in M1), and checks the 5 replaced functions and the wrap.
- 43 figures, equal in both languages.

**docs/features.md and docs/fr/caracteristiques.md**
- 12,999 lines, 17 modules, the same models, every name kept, the two directions of the size study.
- Links and anchors resolve.
- Same text in both languages.

**LIMITATIONS.md and LIMITATIONS.fr.md**
- The note: the split's A1 is identical.
- Point 9:
  - 165, 168, 161 and 154.
  - The same 150 fits exact at the first generation at every number of rows, each with a seed recorded.
  - Medians 3 and 116 of the fits that run to their budget.
  - 6 of 11.
  - 144, 139 and 108 against 168.
  - "A third": 50 of 150.
  - 26 formulas on an added variable.
- The 33 figures are equal in both languages.

**PLAN.md, the amendment**
- Recounted from the table of `map.txt` at HEAD and at c7e00fa: 66, of which 44 rebound inside core, 12 set by the package, 32 by the tests, 61 hold data and 5 are functions replaced by the tests.
- 45 at 0a0090e.
- 8dc5435 is the parent of Split 1 (71902c3, the same second), which is one commit checked by the short A1 (0068717). Splits 2 to 18 follow, each a move then a check.

**size/README.md**
- Every table recomputed from `campaign.jsonl`: the verdict, the origin of the exact laws, the figures of `reading.txt`.
- The text:
  - the same 150 fits;
  - 2 to 136 generations;
  - the medians 116, 83, 31, 3 and 30, and 89 against 83, and 708;
  - the losses 15, 20 and 50;
  - the guard, 0.3 to 5.3 s;
  - 1,845 records, each job once, no crash, at least one generation;
  - Python 3.11.18 and NumPy 2.4.6;
  - first and last fits at 21:11:34 and 01:23:24, three slices, the records committed after each;
  - the four `lscpu` identical; the engine identical before and after.
- Beside:
  - the four equations lost by rows;
  - 5.0 s and 32 s;
  - five fits late, four of I.11.19 and one of III.9.52;
  - 45 fits past the budget, by 8.1 s and 16 s;
  - the seeds placed: 40, 35, 30, 30 and 15, 25, 30, 55;
  - the laws the seeds lose by finder: 40 and 10, 10 and 5, 10 and 10;
  - I.34.1 at 3, 13 and 23 columns, I.27.6 at 3 and 8;
  - 12, 16, 26 and 10 formulas on an added variable, four exact;
  - the near fits.
- The code:
  - the caps of the finders (4·23 + 8·23·22 = 4,140 > 4,096 monomials at 23 columns);
  - the tolerant seed tried only when neither finder returns a seed (`search.py` 614);
  - `select` is the ε-lexicase over the rows.
- Commit times: `compare_size.py` before the first fit, `beside.py` after the run, `profile_size.py` before the profiles.
- The profiles: every time and share quoted, the same formula in all 21 pairs, the same processor in 42 records.

**split/README.md**
- `core.py`: 849 lines, and its content as listed.
- Every module under 2,000 lines, the longest `seeds.py` at 1,623.
- A2 as in `a2_local.txt`: 269 passed three times, under pytest 8.4.2 and 9.1.1.
- A3 recomputed: 678.23 s and 680.12 s, ratio 1.00279. Beside: median 1.0000, mean 1.0036, and the 53 fits over 2 s.
- A4 has 69 tests.
- The map: 45 at 0a0090e, then 66 = 61 + 5. `deps.txt` shows one cycle; 25 parts moved out of their section; no link up the order (`layout_check.txt`).
- Split 1 makes `state.py`: 55 names defined there, the 3 memories and 3 names set only by a fit give 61.
- Splits 2 to 18 each have their check commit; `a1/02` to `a1/19` and `00_baseline_twice` are identical.
- The contents of 4fe34dc, 398e94d and bcbac70 are as told.
- The two copies of the 421 names are identical.

**release/README.md**
- 22f5734 changes only the version number in three files, and `gp_elite/` and `tests/` do not change after it.
- The 29 hashes of the wheel equal the files of 22f5734.
- `/venv14p` holds the 11 files of 6dc1e35.
- M1 ran from 07:04 to 08:05.
- A1 identical; 21.2 s and 27.0 s.
- A3 recomputed; the import medians as in `M1_A3.txt`.
- A4: 69 passed.
- M4: 269 passed three times on the wheel; the hash prefix matches; the pins are those of 1.4; `twine` passes.
- The CI matrix is as in `tests.yml`.
