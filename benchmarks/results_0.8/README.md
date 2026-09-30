# Measurements behind 0.8.0

This folder holds two kinds of records.

**The decisions.** Every change of 0.8.0 meant to improve the search or the
final selection was decided by a comparison whose hypothesis and criteria were
written before it ran; the corrections of defects were not, and `RESULTS.md`
gives what they change. The plans are in `PLAN.md`, in the order they were
written (the repository history gives the time each was committed, by the
machine's clock). The results, the raw records (`campaign*_T.jsonl`,
`budgetG.jsonl`, `small_data_*.jsonl`) and their summaries (`*_summary.txt`)
are described in `RESULTS.md`, including the changes that did not meet their
criteria. Records set aside are kept apart and not used: `*_perturbed_replaced.jsonl`
holds fits disturbed by another measurement on the machine, which were run
again; `*_stopped.jsonl` holds runs stopped before their end (campaign 3b, once
its decision no longer depended on it, and the first start of campaign 5,
before its amendment).

**The public figures.** Every measured figure quoted in `README.md`,
`README.fr.md`, the notebooks, `paper/paper.md` and the 0.8.0 entry of
`CHANGELOG.md` comes from `RESULTS.md`, from one of the files listed below, or,
when it is attributed to 0.7.0, from `../results_0.7/`. The files below were
produced with `PYTHONHASHSEED=0`, one process per measurement, each method
judged on the model it **returns**.

Environment: Linux container with 2 CPU cores (two measurements at a time, one
per core), Python 3.11, NumPy 2.4, scikit-learn 1.8, gplearn 0.4.3,
xgboost 3.2, pandas 3.0, sympy 1.14. Times depend on the machine and vary from
run to run; the other figures do not, except where a fit has a time limit
(runs are deterministic at a given seed; the console fixes no seed, so the
internal statistics it prints differ from one run to the next, while the law
and the constant quoted from it come out the same).

## Provenance

The re-measurement of the public figures ran on 30 September 2026 between
00:22 and 01:16, two queues side by side (`claims_queues.txt` gives the start
of each command), with the engine of commit `cdddaf0`, the last change to
`gp_elite/` before the release; the commits after it change documentation,
tests and benchmark scripts only. The records that carry a `commit` field
show `cdddaf0`. Later measurements with the same engine:
`feynman_angles_normalize_none.*` at 01:22 (documentation check D1),
`nikuradse_full.txt` from 01:27 to 01:29, after the printed reading of the
script was reworded (a first run, from 00:59 to 01:01, gave the same models and
figures: `nikuradse_full_first_run.txt`), `typed_generations.*` from 01:55 to
02:02 (diagnostic D2), `bad_inputs.txt` and `import_time.txt` at 02:04 and
02:05, campaign R (`campaignR_T.jsonl`, described in `RESULTS.md`) from 02:05 to
04:21, `speed_equivalence.txt` from 04:32 to 04:36 (on the engines it compares),
`typed_generations_stop_0.7.txt` from 04:38 to 04:41, and `kepler_plot.txt` and
`notebook_snippets.txt` after them, at the times they print. An earlier
re-measurement of the same figures (29 September, 23:23, to 30 September,
00:16, with the engine before commit `cdddaf0`) gave the same models; it is
superseded by this one and not kept.

## Files

| File | Claim | Command (from the repository root) |
|---|---|---|
| `feynman15.jsonl`, `feynman15.txt` | Feynman 15: 12/15 exact, 13/15 within 1e-3; I.16.6 and I.18.12 missed, III.15.12 within 1e-3 | `python benchmarks/feynman_bench.py 0 15` |
| `feynman_angles_normalize_none.jsonl`, `.txt` | the three laws with a sine or a cosine exact with `normalize='none'` | `python benchmarks/feynman_bench.py 12 15 --normalize none` |
| `duel_gplearn.jsonl`, `duel_gplearn.txt` | 12/15 against 6/15 for gplearn; ahead 8, tied 6, behind 1 (I.18.12) | `python benchmarks/duel.py 0 15` |
| `feynman15_units.jsonl`, `feynman15_units.txt` | with `units=`: 14/15 exact, textbook forms | `python benchmarks/feynman_units.py --out <file>` |
| `units_ab_ood.jsonl`, `units_ab_ood.txt` | II.11.3: 0/5 against 5/5 valid, 2/5 exact law, median sizes 59 and 27, median times 21 s and 149 s | `python benchmarks/ab_ood.py --out <file>` |
| `typed_generations.jsonl`, `typed_generations.txt` | why the typed search takes longer than with 0.7.0 (diagnostic D2): generations run and time per generation | `PYTHONPATH=<engine> python benchmarks/typed_generations_check.py <seed>` |
| `typed_generations_stop_0.7.txt` | 0.7.0 stops the typed search when the hold-out MSE falls below 1e-6 | the same, with `--verbose`, on 0.7.0 |
| `scaling.jsonl`, `scaling.txt` | four equations exact at every size from 25 to 10,000 points, I.16.6 at none; the five fits take 108 s at 1,000 points and 284 s at 10,000 | `python benchmarks/feynman_scaling.py --out <file>` |
| `readme_kepler.txt` | README first example: `0.00279171 + 0.999396 * a * sqrt(a)`, formula exact | the README's first code block, plus `print(result.formula_exact)` |
| `usage_example.txt` | README "Programmatically" example: `2 + 3 * sqrt(a) - 0.5 * b`, `r2_validation` 1.0, size 33 | the code block of that README section, saved as a script and run |
| `robust_example.txt` | robust table and the formulas each mode returns | `python examples/robust_regression.py` |
| `mystery_constant.txt` | Hooke, Newton, ideal gas: units and values | `python benchmarks/test_constante_mystere.py` |
| `battery_example.txt` | simulated battery: interpolation vs extrapolation (R² -0.314 on the forward split) | `python examples/battery_soh.py` |
| `kepler_demo.txt` | `T = 0.00279171 + 0.999396 * a * sqrt(a)` | `python examples/kepler_demo.py` |
| `console_hooke.txt` | console mode 6 transcript on a Hooke CSV: `force = 250 * elongation`, `[kg / s^2]` | `gp-elite` (mode 6, units `m` and `N`, deduce the constant) |
| `formula_fuzz.txt` | 1,500 random trees: 1,461 formulas exact, all matching `predict()` through sympy; 38 inexact because of a safety net, 1 because of the rewriting | `python benchmarks/formula_fuzz.py` |
| `pools_check.txt` | `operators=` respected: 48 fits, 0 out-of-pool operator | `python benchmarks/pools_check.py` |
| `time_limit_check.txt` | `time_limit=`: 16.7 s sequential and parallel for a 15 s budget; 16/16 checks | `python benchmarks/time_limit_check.py` |
| `robustness_check.jsonl`, `robustness_check.txt` | 16 unusual inputs: a model with finite predictions each time, 15 formulas out of 16 reproduce `predict()` | `python benchmarks/robustness_check.py --out <file>`; summary: `--summary <file>` |
| `bad_inputs.txt` | missing or infinite values: 0.7.0 fits them (an unrelated formula for a NaN in y or in a column the law uses) and stops on a non-numeric column with an error that does not name it; the release refuses all of them and names the row and column; `predict()` on a row with a NaN: 0 with 0.7.0, NaN now | `PYTHONPATH=<engine> python benchmarks/bad_input_check.py` |
| `import_time.txt` | `import gp_elite`: 0.92 s with 0.7.0, 0.08 s now (medians of seven fresh processes) | the command at the top of the file, with `PYTHONPATH=<engine>` |
| `scale_check_release.txt` | eleven input and target scales from 1e-34 to 1e30: the law at all eleven | `python benchmarks/scale_check.py` |
| `small_data_release.jsonl`, `small_data_release.txt` | five laws on 25 points, four seeds: the returned model as fitted | `python benchmarks/small_data_check.py --arm F --out <file>` |
| `notebook_snippets.txt` | the figures in the notebooks' text (Kepler, Hooke, Coulomb, torque, Nikuradse short run...) | `python benchmarks/notebook_claims.py <snippet>` |
| `nikuradse_full.txt` | Nikuradse under the full protocol: front, champion, held-out roughness | `python benchmarks/real_nikuradse.py` (telemetry: `benchmarks/real_nikuradse_auto.json`) |
| `speed_equivalence.txt` | the speed-ups return the same models, bit for bit, on 13 configurations (three pairs of engines) | `PYTHONPATH=<engine> python benchmarks/speed_equivalence.py run <dir>` for each engine, then `compare <dirA> <dirB>` |
| `kepler_plot.txt` | the figure at the top of the README, `kepler_plot.png` | `python examples/kepler_plot.py` |

`<engine>` is a directory holding the `gp_elite` package of the version to
measure (a git worktree of its commit): 0.7.0 is commit `e847605`.

Every command runs with `PYTHONHASHSEED=0` set: `PYTHONHASHSEED=0 python ...`
on Linux and macOS, `set "PYTHONHASHSEED=0" && python ...` in the Windows
command prompt (with the quotes: without them `cmd` stores `0 ` with a trailing
space, which Python refuses). Since 0.8.0, `seed=` alone reproduces a fit
whatever `PYTHONHASHSEED` is; the benchmarks keep setting it so that their
records compare with those of earlier releases.

The real datasets (PMLB) are checked by content hash in `benchmarks/pmlb_frozen.py`.
