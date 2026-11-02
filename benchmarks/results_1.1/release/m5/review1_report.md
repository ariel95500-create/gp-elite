# M5 of release 1.1.0: first independent review (30 October 2026)

Reviewer: a second agent that had not seen the work. It did not modify any file
in the repository, ran only read-only git commands (`log`, `diff --stat`) and
did not run any fits. Recomputations were done with small read-only scripts
(`/venv10x/bin/python -I`) on the records in
`benchmarks/results_1.1/release/m2/*.jsonl`, `u2check/*.jsonl` and
`release_1.0/m2/*.jsonl`.

## Scope and method

Documents checked: `README.md`, `README.fr.md` (line by line against the
English), the 1.1.0 entry of `CHANGELOG.md`, `LIMITATIONS.md` and
`LIMITATIONS.fr.md`, `paper/paper.md` (the version 1.1 and units passages),
`examples/tp_six_lois.ipynb`, `examples/case_studies/*.ipynb` (Kepler, Hubble,
Nikuradse, EN and FR), `benchmarks/results_1.1/release/README.md`,
`PLAN_U2.md` and `ROADMAP.md`.

About 480 claims were checked (about 250 distinct ones; the French pages
repeat the English). Where a record allowed it, the figure was recomputed:
- M2: counts, medians, gains and losses, never-exact equations, families,
  structures, audits, collapses, formula_exact, paired differences, the two
  1.0.0 campaigns, and candidate 1 against candidate 2;
- M3: sums and ranges of times (scaling, TP notebook, notebook pair, gas
  and fall timings), the Kepler percentages, the Hubble ratios, the TP
  constants;
- u2check: medians, totals, constant errors.

The Nikuradse figures were spot-checked only. Their records are identical to
the 0.9 outputs the notebooks quote, apart from paths and times (checked with
`diff`).

## Confirmed (headline)

- **M2** (`m2/campaignR_*.jsonl`, 2,780 paired jobs, no duplicates, no crash).
  All of these recompute exactly:
  - F41 163/163;
  - F41N1/N10 108/86 for both versions;
  - R6 folds median 0.8095;
  - R6 + R7raw collapses 10/10;
  - U41 108 to 165;
  - the five families 16 to 57 (racine 2 to 22, rationnelle 12 to 15, trig 1
    to 5, exponentielle 0 to 10, logarithme 1 to 5);
  - never exact 13 to 6;
  - U41N1/N10 79/80 to 113/99;
  - 1,005 of 1,005 `units_ok`;
  - U41 median time 30.1 to 0.52 s;
  - TF78 213/213;
  - TS14 test 8/8;
  - TR25 median 0.7657;
  - TF78 under units 169 to 226, median 30.3 to 1.6 s, 16 equations gain, never
    exact 37 to 30;
  - 47 of 1,775 differ, all at budget, none changes status;
  - the two 1.0.0 campaigns: 114 differ, 3 near to missed, 43 under units at
    budget; R6 5 to 4, R7raw 5 to 6, TR25 0.7691 to 0.7657;
  - the seven criteria.
- **CHANGELOG decision figures**: 107 to 165, then 107 to 166
  (`campaign/compare_u1*.txt`).
- **Scaling** (`m3/scaling.txt`):
  - four equations exact at every size and run;
  - I.16.6 exact in 5 of the 13 runs below 1,000 points, exact from 1,000
    points on, non-canonical at 2,000;
  - 1.6+10.1+2.7+1.4+42.6 = 58.4 s, and 3.8+14.0+5.7+3.2+126.7 = 153.4 s.
- **`units=` on II.11.3**:
  - 1.1.0 (`m3/units_ab_ood.txt`): 5/5/5 in every row, 20 nodes, 1 s;
  - 1.0.0 (`release_1.0/m3/units_ab_ood.txt`): 2/5, 27 nodes, 27 s, out of
    domain 0.31874 to 0.65087.
- **Feynman 15 with units 15/15** (`m3/feynman15_units.*`):
  - 14 in textbook form;
  - I.16.6 is `1.00758 * (v1 + v0) / (1.00758 + 1.00758 * v0 * v1 / v2²)`;
  - 1.0.0 was NEAR.
- **Feynman 15** 15/15, and the duel 15/15 against 6/15 (7/15 within 1e-3,
  ahead on 9, tied on 6).
- **`time_limit`**: 16.7 s parallel, 9.3 s sequential, R² 1.0000, 3,000 rows,
  15/16.
- **Mystery constant**: 250, 6.674e-11, 8.31446, and the printed formulas.
- **Unchanged README examples**: console, usage, Kepler snippet, robust table
  (1.398/0.237 = 5.9), battery.
- **TP notebook** (`m3/notebook_tp_six_lois_1.1.0.txt`):
  - fits of 42, 51, 55, 47, 53 and 46 s, 294 s in all;
  - g 9.814 (0.04 %), factor 0.27 %, g 9.741 (0.70 %), R 8.250 (0.77 %),
    P 10.023 W;
  - 120/120 and 4.69 % at worst also hold for 1.1 (u2check, both engines).
- **Notebook pair**: 285/298 against 302/300, mean 291.5 against 301.
- **Gas timings** 48.6, 49.5 and 49.8 s; **fall timings** 50.5 to 51.3 s
  against 43.1 to 44.1 s.
- **Candidate 1**: 320 against 243 s; gas 77 to 79 s against 49.9 to 51.2 s.
- **U2 check**: medians 46.1 and 44.2 s, totals 10,054 and 9,117 s, constant
  error 0.98 % (60 fits each), 120/120.
- **Kepler** (`m3/case_kepler.txt`): every number of the text (0.0016 %, 0.55 %,
  0.043 %, 0.27 to 0.28 %, 2.6 %, 0.8 %, 0.0068 yr = 2.5 d, 0.56 %, 0.08 %).
- **Hubble** (`m3/case_hubble.txt`): every number (424, 62 %, 38 %, 203/231,
  2 %).
- **Provenance**:
  - no change of `gp_elite/` between 26349ef, 6e0e296 and HEAD;
  - 82f303e to 66abffa changes only `benchmarks/tp_diagnostic.py` outside
    `results_1.1/`;
  - M1 13/13 identical (both comparisons);
  - M4 154 passed ×3, twine PASSED;
  - `m3_compare`: 60 records the same;
  - import median 0.117 s.
- **French pages**: no figure differs from the English in the READMEs, the
  limits pages or the case studies.

## Findings

### 1. LIMITATIONS: 1.1.0 does not return "the same figures" as the page (error)

- **Where.** `LIMITATIONS.md` and `LIMITATIONS.fr.md`, intro: "Version 1.1
  changes the units mode only: without units it returns the same figures" /
  "sans unités, elle rend les mêmes chiffres".
- **Records.** The page quotes 1.0.0 in its own campaign
  (`release_1.0/m2`). Measured in M2, 1.1.0 gives:

  | point | figure | page | 1.1.0 measured |
  |---|---|---|---|
  | 2 | Strogatz, exact on the test rows | 7 of 70 | 8 of 70 |
  | 3 | structures, 1 % and 10 % noise | 105 and 85 | 108 and 86 |
  | 4 | R6 + R7raw collapses | 11 of 65 | 10 of 65 |
  | 6 | formula_exact False, bench | 7 of 130 | 8 of 130 |
  | 6 | formula_exact False, test set | 61 of 500 | 67 of 500 |

  Recomputed from `m2/campaignR_1.1.0.jsonl`. 1.0.0 in the same campaign gives
  8, 108/86, 10, 7/130 and 66/500. The differences are timing between
  campaigns (`details_1.0.0_two_campaigns.txt`), not the engine.
- **Change.** Write "without units it returns the models of 1.0.0 at equal
  work; under the 30 s budget the counts move with the load of the machine
  (measured beside 1.0.0 in 2026-10: 108 and 86 structures, 8 Strogatz
  fits, 10 collapses, for both versions)". Or say that the figures are those
  of 1.0.0's own campaign.

### 2. README and paper: "the figures of 1.0" next to a Strogatz count 1.1 does not reproduce (inconsistency)

- **Where.**
  - `README.md` / `README.fr.md`, "Is it solid?": "…on its Strogatz systems, 7
    exact fits of 70 against 8 … without units, the figures of 1.0" / "sans
    unités, les chiffres de la 1.0".
  - `paper/paper.md` l. 215–219: "… 7 against 8 in 70 on its Strogatz systems
    … Version 1.1.0 … returns the same figures without units".
- **Record.** `m2/compare.txt`: TS14 test exact is 8 for 1.1.0, and 8 for
  1.0.0 in the same campaign. Read in context, "the figures of 1.0" means
  7 of 70.
- **Change.** "Without units, the figures of 1.0.0 measured beside it" and
  give the Strogatz count of that campaign (8 of 70 for both). The cause is
  the same as in finding 1.

### 3. Paper: stale sentence on the typed population (error)

- **Where.** `paper/paper.md` l. 176–177: "The typed population of the
  dimensional mode does not use them yet."
- **Record.** It contradicts l. 57–58 and 202–204 of the same paper and the
  1.1 change itself: `PLAN.md`, U1 adopted; `m2/compare.txt`, U41 108 to 165.
- **Change.** "Since version 1.1 the typed population uses them too, each
  kept only if it passes the dimensional gate." Or delete the sentence.

### 4. Hubble notebooks: "under units none of them acts" is stale (error)

- **Where.** `hubble_1929.ipynb`, cell 10: "…these seeds place nothing, and
  neither do the exact ones (without units; under units none of them acts)."
  `hubble_1929.fr.ipynb`, the same: "(sans les unités ; avec les unités, aucune
  d'elles n'agit)".
- **Records.**
  - In 1.1 the finders act under units. `m3/case_hubble.txt`, row A (typed):
    seven finder calls, all placing 0, the same list as the untyped row B.
  - In 1.0 (`release_1.0/m3/case_hubble.txt`), row A shows four calls.
- **Change.** "…and neither do the exact ones, with or without units."

### 5. Release README: TS14 out of domain gains one collapse (error)

- **Where.** `release/README.md` l. 82: "Each suite out of domain has the same
  collapses in both versions."
- **Records.**
  - `m2/tables_1.0.0.md` and `m2/tables_1.1.0.md`, row "TS14 | out of
    domain": 27 collapses against 28.
  - The fit is `ts strogatz_barmag1 ood seed 8`, R² 0.829 to −2.358, both at
    the budget. `details.py` checks only real, realraw, tr and trraw.
- **Change.** "R6, R7raw, TR25 and TR25raw have the same collapses in both
  versions; TS14 out of domain one more (27 to 28), a fit at the budget."

### 6. CHANGELOG: "the same counts" overstates (wording)

- **Where.** `CHANGELOG.md` 1.1.0: "without units, the same counts on the
  1,775 fits of the bench and the frozen test set".
- **Records.**
  - Exact, near and missed, structures, medians and R6/R7raw/TR collapses are
    the same.
  - TS14 out-of-domain collapses are 27 against 28 (finding 5).
  - formula_exact False is 119 against 125 fits. The 6 that change are among
    the 47 at the budget:
    - TF78: 7 to 10;
    - R6 folds: 0 to 1;
    - TR25 folds: 18 to 19;
    - TS14 out of domain: 13 to 14.
- **Change.** "The same counts of exact laws and structures, the same medians
  and collapses on the real data of the bench and the test set; the 47 fits
  …". Or name the two exceptions.

### 7. Release README: II.11.28 under units gains four seeds, not one (error)

- **Where.** `release/README.md` l. 88–90: "As then, one fit exact with 1.0.0
  is not with 1.1.0 (II.11.28, seed 5), and another seed of the same equation
  becomes exact."
- **Record.** `m2/campaignR_*.jsonl`, `utf feynman_II_11_28`:
  - 1.0.0: seed 5 EXACT, seeds 6 to 9 MISS;
  - 1.1.0: seed 5 NEAR, seeds 6 to 9 EXACT.

  That is 1 to 4: four other seeds become exact. The first candidate is the
  same, and `candidate1/README.md` carries the same sentence.
- **Change.** "…and the four other seeds of the same equation become exact
  (1 to 4)."

### 8. The free-fall trace has no record (unsupported)

- **Where.**
  - `release/README.md` l. 175–176: "Its trace shows the seed of U1, `(t)²`,
    placed at generation 0, and no seed of fractional units."
  - It underpins `examples/tp_six_lois.ipynb`, cell 24: "(depuis la version
    1.1, c'est le cas par exemple pour la chute libre et le gaz parfait)".
  - It also underpins `ROADMAP.md` l. 62: "version 1.1 places the law at
    generation 0".
- **Record.**
  - `m3/tp_timing/fall.py` prints the trace, but `fall_timings.txt` holds
    only the six result lines. No other record (u2check, mechanics) has a
    free-fall trace.
  - The gas law is recorded (`gas_1.1.0.txt`: one seed, `((n * T) / V)`).
- **Change.** Keep the full output of `fall.py` (one more run, a few seconds
  of reading) beside `fall_timings.txt`. Or cite only the gas law.

### 9. Kepler notebooks: 1.0 did not write a^1.5 differently "at each seed" (error)

- **Where.** `kepler_units.ipynb`, cell 11: "Version 1.0 returned the same
  constant but wrote a^1.5 in a different way at each seed: as a product of
  four roots of *a*, as `sqrt(X0 * X0 * X0)`, or as the difference of two
  terms in a^1.5." `kepler_units.fr.ipynb`, the same ("d'une façon différente
  à chaque graine").
- **Record.** `release_1.0/m3/case_kepler.txt`, the B rows. Seed 3 already
  returned the textbook form 1.1 returns.

  | seed | form returned by 1.0, fit B |
  |---|---|
  | 0 | four roots |
  | 1 | `sqrt(X0) * X0` |
  | 2 | `sqrt(X0 * X0 * X0)` |
  | 3 | `5.45416e-10 * X0 * sqrt(X0)` |
  | 4 | two terms |

  The French text before this release listed them correctly
  (`git diff 66abffa HEAD`).
- **Change.** "…wrote a^1.5 in other forms at four of the five seeds (seed 3
  already as `X0 * sqrt(X0)`): …".

### 10. Kepler notebooks: stale output pointer and fit times (inconsistency)

- **Where.**
  - `kepler_units.ipynb` and `.fr.ipynb`, cell 0: "Every figure in the text
    was measured with `benchmarks/case_studies.py kepler` … (output in
    `benchmarks/results_0.9/case_studies/kepler.txt`)".
  - Cell 16: "The full output: `benchmarks/results_0.9/case_studies/kepler.txt`."
  - Cell 0: "The fits take from one to about fifteen seconds each" / "d'une à
    une quinzaine de secondes".
- **Records.**
  - The text now quotes `5.45416e-10 * X0 * sqrt(X0)` at all five seeds.
    `results_0.9/case_studies/kepler.txt` has it at seed 3 only. The 1.1
    output is `benchmarks/results_1.1/release/m3/case_kepler.txt`.
  - 1.1 times: A 8 to 10 s, B 0 s, C8 9 to 11 s, C4 0 s.
- **Change.**
  - Point cells 0 and 16 at `results_1.1/release/m3/case_kepler.txt` (the 0.9
    file as history).
  - "Under a second to about ten seconds".

### 11. CHANGELOG: only one of the two typed Kepler fits changed (wording)

- **Where.** `CHANGELOG.md` 1.1.0: "the typed fits of the Kepler case study
  write the law `5.45416e-10 * X0 * sqrt(X0)` at every seed, with the constant
  of 1.0."
- **Record.** `m3/case_kepler.txt`:
  - the typed fit on the eight planets (A) writes `5.43909e-10 * X0 *
    sqrt(X0)`, unchanged from 1.0;
  - only the fit on the four inner planets (B) writes `5.45416e-10 …` and
    changed.
- **Change.** "the typed fit on the four inner planets writes the law
  `5.45416e-10 * X0 * sqrt(X0)` at every seed (1.0: other forms), with the
  constant of 1.0".

### 12. Paper: where the 1,005 audited models come from (wording)

- **Where.** `paper/paper.md` l. 204–207: "On the 41 equations of the decision
  bench with their units, the constrained search recovers the exact law in 165
  of 205 fits …, and each of the 1,005 typed models of that measurement passes
  the dimensional audit".
- **Record.** 1,005 = U41 + U41N1 + U41N10 (615) + TF78 under units (390)
  (`m2/compare.txt`). "That measurement" reads as the 205 fits.
- **Change.** "…and each of the 1,005 models returned under units in the
  release measurement (these equations with and without noise, and the frozen
  test set) passes the dimensional audit". The README "What's new" (EN and FR)
  would gain from the same clause.

### 13. README `time_limit=`: the quoted run overlapped other scripts (wording)

- **Where.** `README.md` / `README.fr.md`, `time_limit=`: "(16.7 s for a 15 s
  budget on 3,000 rows in the measurement of 1.1.0, islands in parallel; in
  sequence, the same fit stopped at 9.3 s …)".
- **Records.**
  - `m3/claims_queues.txt`: `time_limit` ran in queue 2 from 07:23:24 to
    07:24:50. Beside it, queue 1 ran robustness, scale, small data, bad
    inputs and Nikuradse full.
  - Finding 9 of 1.0's M5 rejected an overlapped run for this sentence, and
    1.0 quoted a run alone (`release_1.0/m3_extra/time_limit_check_alone.txt`:
    16.9 s / 10.2 s).
  - The parallel fit's R² 0.9979, against 1.0000 before, shows the load.
- **Change.** Run `time_limit_check.py` alone on the wheel and quote that run.
  Or keep the 1.0.0 run alone: the engine without units is the same (M1).

### 14. Release README: the machine description has no record (unsupported)

- **Where.** `release/README.md` l. 4: "The machine is an Intel Xeon at
  2.8 GHz, 4 cores, AVX-512".
- **Records.**
  - No record in `results_1.1/` gives the processor; the M2 records carry
    only `avx512`/`avx2`.
  - 1.0 recorded it (`release_1.0/m3_extra/machine.txt`: "Intel(R) Xeon(R)
    Processor @ 2.10GHz").
  - This review's container (30 October) reports "Intel(R) Xeon(R) Processor
    @ 2.10GHz", 4 CPUs, AVX-512. That contradicts PLAN.md's "That is not the
    processor of the 1.0 measurements". It also bears on the explanation that
    "the machine was faster on 27 October" (l. 166): the container restarted
    during M2 and may not be the same host from day to day.
- **Change.** Record `lscpu` and `nproc` in `results_1.1/release/` (as
  `machine.txt` for 1.0) for the M2/M3 days if still possible. Otherwise
  state the processor as unrecorded, and say that a change of host is a
  possible cause of the 27 to 30 October timing difference.

### 15. Release README: list of what differs between candidates is incomplete (wording)

- **Where.** `release/README.md` l. 128–137: "What differs depends on timing
  only:" followed by four items (queues, console, `time_limit`, import time).
- **Record.** `m3_compare_candidate1_vs_candidate2.txt` also lists:
  - `scaling.txt`: column width of a time of 10 s or more after masking,
    I.8.14 at 1,000 points;
  - `gp_elite_log.csv`: the console's log;
  - `m3_driver.sh` and `.log`.

  All of them are timing or driver; nothing else.
- **Change.** Add "the width of one masked time in `scaling.txt`, the
  console's log file, and the driver files".

### 16. README battery example: version reference (wording)

- **Where.** `README.md`: "The equation 1.0 returns, in the current and the
  cycle, does better than them…". `README.fr.md`: "L'équation que rend la 1.0".
- **Record.** `m3/battery_example.txt`: 1.1.0 returns the same equation (R²
  +0.162). The record is identical between the two candidates, and to 1.0.
- **Change.** "The equation 1.0 and 1.1 return" / "que rendent la 1.0 et la
  1.1".

### 17. ROADMAP: the SRBench reading has no record (unsupported)

- **Where.** `ROADMAP.md` l. 18–32: the reading of `cavalab/srbench` (master,
  2aabbb6):
  - "staged for benchmarking";
  - `gp-elite>=0.8.0`;
  - the harness passes no units;
  - "10 time-bounded restarts in 3,600 s";
  - the grid of `operators` × `generations`.
- **Record.** None in the repository. The strings occur only in `ROADMAP.md`.
- **Change.** Keep the files read, or their URLs at 2aabbb6, under
  `results_1.1/`, before the SRBench study relies on them.

## Not findings, for the record

- "Without units, the models of 1.0" (README "What's new", CHANGELOG) rests on
  M1:
  - candidate 1 had 12 of 12 configurations without units identical to 1.0.0;
  - candidate 2 has 13 of 13 identical to candidate 1.

  At equal work this holds; finding 6 concerns counts under a time budget.
- The TP notebook's 120/120 and 4.7 % come from the 1.0.0 diagnostic. They
  also hold for 1.1 (`u2check`, both engines, 4.69 % at worst). Citing
  `u2check` there would make the version explicit.
