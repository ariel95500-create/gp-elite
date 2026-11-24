# The raw runs of A1

What `../../run_a1.sh` wrote for each run of A1, copied here after the
reviews of the release (the first review of M5, finding 5), so that every
comparison of `../` and of `../../../release/` can be made again from the
repository. The `__pycache__` folders were left out; nothing else was
changed.

Each folder holds `engine.txt` (the engine that ran), `started.txt` and
`ended.txt`, `equiv/` and `equiv.log` (the 13 configurations, one record
each), `phase1_defaults.jsonl` and `phase1.log` (F41 in a short run; F41,
U41 and F41N1 in a full run), and, in a full run, `tp.jsonl` and `tp.log`
(the TP diagnostic) and `console/` (the console example).

| folder | engine | run | compared in |
|---|---|---|---|
| `a1_140` | 1.4.0 from PyPI | full | every comparison, as engine A |
| `a1_140b` | 1.4.0 from PyPI, again | full | `../00_baseline_twice.txt` |
| `a1_s1` | the working tree after Split 1 (the shared state) | short | `../01_state.txt` |
| `a1_02_numeric` to `a1_18_console` | the working tree after each move | short | `../02_numeric.txt` to `../18_console.txt` |
| `a1_door` | the door of eb2eac5 | short | `../19_door.txt` |
| `a1_final` | the engine in modules (eb2eac5) | full | `../20_final_full.txt` |
| `a1_rel` | the wheel of the first candidate of 1.5.0 (22f5734) | full | `../../../release/M1_A1.txt` |
| `a1_rel2` | the wheel of the second candidate of 1.5.0 (96ce1b6) | full | `../../../release/candidate2/M1_A1.txt` |

To make a comparison again, from `benchmarks/results_1.5/split/`, with an
environment where `gp_elite` and `pytest` are installed:

    python compare_a1.py a1/runs/a1_140 a1/runs/a1_rel
