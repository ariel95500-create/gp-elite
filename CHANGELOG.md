# Changelog

## 0.2.2 — 2026-07-06

### Fixed
- **Exports can no longer crash a finished run.** `export_grammar` (meta-
  learning JSON) previously raised on `PermissionError` and destroyed the
  results of a completed evolution. All exports now fall back to the system
  temp directory, and on total failure print a clear warning with a hint
  (OneDrive / Windows "Controlled Folder Access" can block Python writes)
  — the run always completes. Reported on Windows, mode 1 + SEQ transfer.
- One missed French string in benchmark mode translated.

## 0.2.1 — 2026-07-02

### Changed
- **English user interface**: all runtime messages, the interactive menu
  (including mode 7 FORECAST), prompts, reports, warnings, public docstrings
  and error messages are now in English (~150 strings). Yes/no prompts accept
  `y`/`yes` (mapped safely — `y` still selects *poly* in the operator-pool
  choice). French code comments are retained for now; internal i18n is on the
  roadmap. `README.fr.md` continues to serve French readers.

### Fixed
- `examples/kepler_demo.py`: pass raw units to `predict()` (the scaler is
  applied internally). Restores the showcase R² = 1.000000.

## 0.2.0 — 2026-07-02

### Added
- **Levenberg–Marquardt constant fitting** (default; `CONST_OPT_LM=False`
  reverts to legacy Adam). Machine-precision constants — e.g. Coulomb's
  `q1·q2/(4πεr²)` recovered exactly (1−R² ≈ 8e-32). 6–14× faster on
  constant-heavy problems.
- **Native multi-restart** (`restarts=N`): candidate archives merged across
  runs (shared deterministic hold-out), one global selection. Turns seed
  variance into reliability.
- **Pareto front output** (`result.pareto`, `ParetoEntry` objects with their
  own `.predict`): the full complexity ↔ accuracy staircase.
- **Forecast / extrapolation mode**: `extrapolate_feature=`,
  `extrapolate_direction=` — beyond-domain divergence probes, linear safety
  floor, frontier meta-selection. New **mode 7** in the interactive menu.
- **Composition motif seeding** (Pythagorean, reciprocal sums, Gaussian…) for
  nested structures; automatically disabled in extrapolation mode.
- Reproducible benchmarks: `benchmarks/feynman_bench.py` (15 equations,
  frozen protocol) and `benchmarks/duel.py` (gplearn head-to-head).

### Fixed
- **Reproducibility**: parallel workers now use a fixed hash seed; identical
  results per seed within a process. Across invocations: run with
  `PYTHONHASHSEED=0` (documented).
- Robust `api.py` import outside a package (file-next-to-file usage, Windows).
- Motif × extrapolation interaction (forecast regression).

### Numbers (frozen protocol, PYTHONHASHSEED=0)
- Feynman, 15 equations: **10/15 exact recoveries (67%)**, 14/15 < 1e-3.
- gplearn head-to-head (same data/splits, generous budget for gplearn):
  **67% vs 40%** exact; GP_ELITE ahead on 9 equations, tied 5, behind 1.
- Battery SOH forecasting (true extrapolation, unseen cycles): median R²
  **+0.52** vs +0.34 (linear regression), zero divergent models.
