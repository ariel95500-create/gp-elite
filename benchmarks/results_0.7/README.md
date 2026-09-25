# Measurements behind the 0.7.0 README

Every number quoted in `README.md`, `README.fr.md`, the notebooks and the
0.7.0 entry of `CHANGELOG.md` comes from one of the files below, produced by
the released code (gp-elite 0.7.0) with `PYTHONHASHSEED=0`, one process per
measurement, each method judged on the model it **returns**.

Environment: Linux container with 2 CPU cores, Python 3.11, NumPy 2.4,
scikit-learn 1.8, gplearn 0.4.3, xgboost 3.2 — September 2026. Times depend on
the machine; the other figures do not (runs are deterministic at a given seed).

| File | Claim | Command (from the repository root) |
|---|---|---|
| `feynman15.jsonl` | Feynman 15: 11/15 exact, 13/15 within 1e-3 | `python benchmarks/feynman_bench.py 0 15` |
| `duel_gplearn.jsonl` | 11/15 against 6/15 for gplearn; ahead 8, tied 6, behind 1 | `python benchmarks/duel.py` |
| `feynman15_units.jsonl` | with `units=`: 14/15 exact, textbook forms | `python benchmarks/feynman_units.py --out <file>` |
| `units_ab_ood.jsonl` | II.11.3: 0/5 against 5/5 valid, 1/5 exact law, sizes, times | `python benchmarks/ab_ood.py` |
| `scaling.jsonl` | recovery and time from 25 to 10,000 points | `python benchmarks/feynman_scaling.py --out <file>` |
| `norm_signed.jsonl` | `normalize="auto"` decision: 24/40 against 10/40, real-data R² | `python benchmarks/norm_signed.py A <i> <arm>` / `B <dataset> <arm>`, then `--summary` |
| `near_guard.jsonl` | near-domain guard: never intervenes, no collapse | `python benchmarks/near_guard_study.py <dataset> <seed> on`, then `--summary` |
| `robust_example.txt` | robust table | `python examples/robust_regression.py` |
| `mystery_constant.txt` | Hooke, Newton, ideal gas: units and values | `python benchmarks/test_constante_mystere.py` |
| `battery_example.txt` | simulated battery: interpolation vs extrapolation | `python examples/battery_soh.py` |
| `kepler_demo.txt` | `T = 0.00279171 + 0.999396 * a * sqrt(a)` | `python examples/kepler_demo.py` |
| `console_hooke.txt` | console mode 6 transcript on a Hooke CSV | `gp-elite` (mode 6, units `m` and `N`, deduce the constant) |

The Nikuradse figures of the notebooks come from `python benchmarks/real_nikuradse.py`,
whose telemetry is `benchmarks/real_nikuradse_auto.json`.

The real datasets (PMLB) are checked by content hash in `benchmarks/pmlb_frozen.py`.
