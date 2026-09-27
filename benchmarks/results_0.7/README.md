# Measurements behind the 0.7.0 README

Every measured figure quoted in `README.md`, `README.fr.md`, the notebooks,
the paper and the "Measured on this release" section of the 0.7.0 entry of
`CHANGELOG.md` comes from one of the files below, produced by the 0.7.0 code
with `PYTHONHASHSEED=0`, one process per measurement, each method judged on
the model it **returns**.

Environment: Linux container with 2 CPU cores, Python 3.11, NumPy 2.4,
scikit-learn 1.8, gplearn 0.4.3, xgboost 3.2. Times depend on the machine; the
other figures do not (runs are deterministic at a given seed).

## Provenance

The measurements were run on 25 and 26 September 2026 with the search and
selection code of commit `871e1e3` ("Selection finale : une loi exacte n'est
plus echangee contre une approximation plus courte"). The commits after it
and before the release change how a formula is printed, the console display,
the validation of option values, the default number of generations of
`speed="thorough"` and the documentation. Apart from that default, which no
measurement here uses, none changes which model a fit returns. Printed formulas stored in the files
(`expr`, `equation`, `expr_full`) may therefore be written slightly
differently by the released version, for the same model.

Spot checks on the released code: the README usage example
(`usage_example.txt`) and the `units=` study runs `untyped`, `untyped_fair`
and `typed` at seed 4 were re-run and returned the same models (same R²
values and sizes). In that study the `untyped_fair` run at seed 4 returns the
same model as the `untyped` run at seed 4: with the same seed, the 120 extra
generations never produced a better candidate.

`scaling.jsonl` was written by an earlier version of `feynman_scaling.py`
that derived `status`, `suspect_ops` and `clean_recovery` from the best point
of the Pareto front (chosen by looking at the test set) instead of the
returned model. Those derived fields were recomputed on 26 September from the
raw fields stored in each record (`one_minus_r2`, `pareto_best`, `expr_full`,
`front`) with the scoring of the current script (`_score`); each record says
so in its `rescored` field. The raw measurements are unchanged, and the
README figures come from `one_minus_r2`, which was always the returned model.

## Files

| File | Claim | Command (from the repository root) |
|---|---|---|
| `feynman15.jsonl` | Feynman 15: 11/15 exact, 13/15 within 1e-3 | `python benchmarks/feynman_bench.py 0 15` |
| `duel_gplearn.jsonl` | 11/15 against 6/15 for gplearn; ahead 8, tied 6, behind 1 | `python benchmarks/duel.py` |
| `feynman15_units.jsonl` | with `units=`: 14/15 exact, textbook forms | `python benchmarks/feynman_units.py --out <file>` |
| `units_ab_ood.jsonl` | II.11.3: 0/5 against 5/5 valid, 1/5 exact law, sizes, times, the violations listed in the README | `python benchmarks/ab_ood.py` |
| `scaling.jsonl` | recovery and time from 25 to 10,000 points | `python benchmarks/feynman_scaling.py --out <file>`; summary: `--out <file> --bilan` |
| `norm_signed.jsonl` | `normalize="auto"` decision: 24/40 against 10/40, real-data R² | `python benchmarks/norm_signed.py A <i> <arm>` / `B <dataset> <arm>`, then `--summary` |
| `near_guard.jsonl` | near-domain guard: never intervenes, no collapse | `python benchmarks/near_guard_study.py <dataset> <seed> on`, then `--summary` |
| `usage_example.txt` | README "Programmatically" example: printed formula, `r2_validation`, size | the code block of that README section, saved as a script and run |
| `robust_example.txt` | robust table and the formulas each mode returns | `python examples/robust_regression.py` |
| `mystery_constant.txt` | Hooke, Newton, ideal gas: units and values | `python benchmarks/test_constante_mystere.py` |
| `battery_example.txt` | simulated battery: interpolation vs extrapolation | `python examples/battery_soh.py` |
| `kepler_demo.txt` | `T = 0.00279171 + 0.999396 * a * sqrt(a)` | `python examples/kepler_demo.py` |
| `console_hooke.txt` | console mode 6 transcript on a Hooke CSV | `gp-elite` (mode 6, units `m` and `N`, deduce the constant) |

Every command runs with `PYTHONHASHSEED=0` set: `PYTHONHASHSEED=0 python ...`
on Linux and macOS, `set "PYTHONHASHSEED=0" && python ...` in the Windows
command prompt (with the quotes: without them `cmd` stores `0 ` with a trailing
space, which Python refuses).

The Nikuradse figures of the notebooks come from `python benchmarks/real_nikuradse.py`,
whose telemetry is `benchmarks/real_nikuradse_auto.json`.

The real datasets (PMLB) are checked by content hash in `benchmarks/pmlb_frozen.py`.
