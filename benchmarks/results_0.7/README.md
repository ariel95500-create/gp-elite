# Measurements behind the 0.7.0 README

Every measured figure quoted in `README.md`, `README.fr.md`, the notebooks,
the paper and the "Measured on this release" section of the 0.7.0 entry of
`CHANGELOG.md` comes from one of the files below, produced by the 0.7.0 code
with `PYTHONHASHSEED=0`, one process per measurement, each method judged on
the model it **returns**.

Environment: Linux container with 2 CPU cores (two measurements at a time, one
per core), Python 3.11, NumPy 2.4, scikit-learn 1.8, gplearn 0.4.3,
xgboost 3.2. Times depend on the machine; the other figures do not (runs are
deterministic at a given seed).

## Provenance

Everything here was measured on 27 September 2026, between 21:31 and 23:07,
with the search and selection code of commit `c4578a2` (the last change to the
search: a power with a variable exponent is `|u|^v` on every row). Records
that carry a `commit` field show `39d731c` or `8430393`: those two commits
only add benchmark scripts and change how a formula is printed
(`a * (1 / b)` is written `a / b`); `39d731c+modified` marks the few records
written while that printing change was in the working tree, before it was
committed. The commits after them, up to the release,
change documentation and docstrings, add the warning given when a formula
departs from `predict()`, and change how parallel workers receive their data
and whether they print; none changes which model a fit returns (the
measurements here run sequentially, and a parallel fit was checked to return
the same model before and after).

An earlier campaign (25 and 26 September, before the change to the power
operator) is superseded by this one and is not kept here.

`scaling.jsonl`: the field `in_readme_claim` of the 25-point records was
recomputed after the range cited by the README became 25 to 10,000 points
(field `rescored`); every other field is as measured.

## Files

| File | Claim | Command (from the repository root) |
|---|---|---|
| `feynman15.jsonl` | Feynman 15: 12/15 exact, 13/15 within 1e-3; misses I.16.6 and III.15.12 | `python benchmarks/feynman_bench.py 0 15` |
| `duel_gplearn.jsonl` | 12/15 against 6/15 for gplearn; ahead 7, tied 8, behind 0 | `python benchmarks/duel.py` |
| `feynman15_units.jsonl` | with `units=`: 14/15 exact, textbook forms | `python benchmarks/feynman_units.py --out <file>` |
| `units_ab_ood.jsonl` | II.11.3: 0/5 against 5/5 valid, 2/5 exact law, sizes, times, the violations listed in the README | `python benchmarks/ab_ood.py --out <file>` |
| `scaling.jsonl` | four equations exact at every size from 25 to 10,000 points, I.16.6 missed at every size, median time ×2 from 1,000 to 10,000 | `python benchmarks/feynman_scaling.py --out <file>`; summary: `--out <file> --bilan` |
| `norm_signed.jsonl` | `normalize="auto"` decision: 20/40 against 7/40, real-data R² 0.808 against 0.808; `formula_exact` False in 6 of the 70 default-normalisation fits | `python benchmarks/norm_signed.py A <i> <arm>` / `B <dataset> <arm>`, then `--summary` |
| `near_guard.jsonl` | near-domain guard: never intervenes, 299 candidates, no explosion; one poor fold (210_cloud) | `python benchmarks/near_guard_study.py <dataset> <seed> on`, then `--summary` |
| `readme_kepler.txt` | README first example: `0.00279171 + 0.999396 * a * sqrt(a)` | the README's first code block, plus `print(result.formula_exact)` |
| `usage_example.txt` | README "Programmatically" example: printed formula, `r2_validation`, size | the code block of that README section, saved as a script and run |
| `robust_example.txt` | robust table and the formulas each mode returns | `python examples/robust_regression.py` |
| `mystery_constant.txt` | Hooke, Newton, ideal gas: units and values | `python benchmarks/test_constante_mystere.py` |
| `battery_example.txt` | simulated battery: interpolation vs extrapolation | `python examples/battery_soh.py` |
| `kepler_demo.txt` | `T = 0.00279171 + 0.999396 * a * sqrt(a)` | `python examples/kepler_demo.py` |
| `console_hooke.txt` | console mode 6 transcript on a Hooke CSV | `gp-elite` (mode 6, units `m` and `N`, deduce the constant) |
| `notebook_snippets.txt` | the figures in the notebooks' text (Kepler, Hooke, Coulomb, torque, Nikuradse short run...) | `python benchmarks/notebook_claims.py <snippet>` |

Every command runs with `PYTHONHASHSEED=0` set: `PYTHONHASHSEED=0 python ...`
on Linux and macOS, `set "PYTHONHASHSEED=0" && python ...` in the Windows
command prompt (with the quotes: without them `cmd` stores `0 ` with a trailing
space, which Python refuses).

The Nikuradse figures of the notebooks under the full protocol come from
`python benchmarks/real_nikuradse.py`, whose telemetry is
`benchmarks/real_nikuradse_auto.json`; `kepler_plot.png` comes from
`python examples/kepler_plot.py`.

The real datasets (PMLB) are checked by content hash in `benchmarks/pmlb_frozen.py`.
