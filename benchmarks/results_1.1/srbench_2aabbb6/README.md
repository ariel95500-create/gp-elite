# What was read in cavalab/srbench, master at 2aabbb6

`../ROADMAP.md` relies on four files of https://github.com/cavalab/srbench at
commit 2aabbb60dad41d6e5d52779ce134191a874b756c ("Merge pull request #232 from
cavalab/dev"), read in a clone on 28 October 2026. This record was written on
30 October 2026, after the first review of M5 of 1.1.0 asked for one. SRBench is
under the GPL 3.0, so the files are not copied here: each is named by its link at
that commit and its git blob hash, with the lines the roadmap uses.

- `README.md`, blob 04e517d3ae72f5fdd7b4a10f67d671c5a7b2f00a,
  https://github.com/cavalab/srbench/blob/2aabbb60dad41d6e5d52779ce134191a874b756c/README.md,
  line 39: "GP-ELITE and Pantara are staged for benchmarking and are covered by
  the container build and test workflows; they are not included in the SRBench
  2025 result figures above."
- `algorithms/gp-elite/requirements.txt`, blob
  c8146f9c6a57083b45fa4a83a78644065ab9afc9,
  https://github.com/cavalab/srbench/blob/2aabbb60dad41d6e5d52779ce134191a874b756c/algorithms/gp-elite/requirements.txt:
  `gp-elite>=0.8.0`.
- `algorithms/gp-elite/metadata.yml`, blob
  4771c694a936128a04dc77e26044184f4acbbada,
  https://github.com/cavalab/srbench/blob/2aabbb60dad41d6e5d52779ce134191a874b756c/algorithms/gp-elite/metadata.yml,
  lines 11 to 13: "can deduce the units and value of a law's missing physical
  constant (not used here, as the harness does not pass units)."
- `experiment/methods/gp-elite/regressor.py`, blob
  cbf170f9be251dc44169ceba8ff4be3cb0289619,
  https://github.com/cavalab/srbench/blob/2aabbb60dad41d6e5d52779ce134191a874b756c/experiment/methods/gp-elite/regressor.py:
  the estimator is built with `operators="physical"`, `generations=60`,
  `max_time=3600` and `restarts=10` (lines 40 to 46), and line 139 reads
  `{"operators": ("physical", "full"), "generations": (30, 60)},`, the grid of
  `hyper_params`.
