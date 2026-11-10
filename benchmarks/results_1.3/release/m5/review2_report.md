# Release 1.3.0, M5: the second independent review

9 November 2026. Branch `claude/peaceful-knuth-4q7m4p`, HEAD **16eda39**
reviewed; candidate 5492296, engine 492863e.

## Scope and method

**Documents:** `README.md`, `README.fr.md`, the 1.3.0 entry of `CHANGELOG.md`,
`LIMITATIONS.md` and `LIMITATIONS.fr.md` (introduction, points 1, 5, 6 and every
change since 5492296), `paper/paper.md` (changes since 5492296),
`examples/tp_regression_symbolique.ipynb`, `examples/tp_six_lois.ipynb`, the case
studies, `benchmarks/results_1.3/release/README.md` and the READMEs of
`m2/examine/` and `m3/examine/`, the note of 1.3 in
`benchmarks/results_1.1/DIAGNOSTIC_TP.md`, item 6 of
`benchmarks/results_1.1/ROADMAP.md`, and the scripts
`benchmarks/release_claims/compare_m2_1.3.py` and `m2/arcsine_formulas.py`.
The French passages changed since 5492296 were read line by line against the
English.

**Method.** Read-only. No engine import, no fit. Each figure was recomputed from
the JSON records with the scripts of `review2/`, run with `python3 -I -B`
(`/venv12b/bin/python -I -B` for `r6`, which needs NumPy). The pools were read
from the source of `feynman_bench.py` (with `ast`) and from
`test_set/MANIFEST.json`, so that no bench module is imported. Claims about
behaviour were checked in `gp_elite/` (the pools, the clip, the printed and sympy
forms, the units, the A2 rule, the A3 seeds, the traced seeds). The commit times
come from `git log`. The 11 `gp_elite/` files of `/venv13r` were compared with
HEAD by SHA-256: identical.

| script | what it recomputes |
|---|---|
| `common.py` | loading, pools without import |
| `r1_m2.py` | every indicator of M2, the pool `physical` (706 / 2,234 / 2 status), the pool `trig` by suite and by problem, `formula_exact` by pool, the arcsine in the text, the seeds, the frozen test set |
| `r2_seeds.py` | the arcsine seeds, exact and noise-tolerant, by suite and problem |
| `r3_two_campaigns.py` | 1.2.0 in the M2 of 1.2 against 1.2.0 in the M2 of 1.3; the fits stopped by the budget (1,983, 30.5 s, 31.7 s) |
| `r4_limits.py` | the figures of the pages of the limits (equations never exact, TF78 main and bonus, collapses, departing formulas) |
| `r5_m3_examine.py` | E2: sign tests, departures, arcsines, seed 0 |
| `r6_i1812.py` | I.18.12 in M2 and in E1; the parabola against sin θ |
| `r7_paths.py` | every path quoted in the added lines of the documents |
| `r8_cut.py` | the cut formulas by pool; arcsine formulas with the structure |
| `r9_m1.py` | the thirteen configurations of M1, without their times |

About 230 claims were read against the records or the code. About 150 of them
were recomputed from the records.

**Independence.** I did not open `M5_review1.md`, `m5/review1_report.md` or
`m5/review1/`. One repository-wide `grep` for "82 of" printed a single line of
`M5_review1.md` among its matches. I neither opened the file nor used the line.

## Findings

Most consequential first.

**1. The CHANGELOG calls the 25 fits of the noise-tolerant arcsine seed "noisy";
5 of them are not.**
- *Where:* `CHANGELOG.md:53-55`.
- *Claim:* "the noise-tolerant one in 25 noisy fits."
- *Records:* the arcsine is in `tolerant_seed` in 25 fits of 1.3.0. 20 of them
  are noisy: I.30.5 in F41N1, F41N10, U41N1 and U41N10. The other 5 are
  `feynman_test_1` of TF78, seeds 5 to 9, which has no noise
  (`phase1_bench.py:71-72`: `NOISE` covers only the `*_n1` and `*_n10` kinds).
  See `review2/r2_seeds.txt`. The release README says it correctly
  (`release/README.md:139-142`).
- *Why it matters:* the public changelog misstates where the new seed acts. It
  also acts on noiseless data where no exact form holds. The CHANGELOG
  contradicts the release README.

**2. Stale in both READMEs: the list of the safety nets that make the printed
formula depart from `predict()` leaves out the clip of the arcsine.**
- *Where:* `README.md:212-218`, `README.fr.md:233-238`.
- *Claim:* "where one of the engine's numerical safety nets acts on your data (a
  power clipped …; a division by a denominator within 1e-8 of zero) … it departs
  from `predict()`."
- *Code:* since 1.3 the model clips the argument of the arcsine
  (`core.py:2816-2819`) and the printed formula does not (`formula.py:596`, "no
  clip").
- *Records:* in the pool `trig` the printed formula departs in 82 fits of 530
  against 27, and at least 47 of the 82 have an arcsine (`r1_m2.txt`). In the TP
  notebook of the pool `full`, 6 of the 7 departures have one (`r5_m3_examine.txt`).
- *Why it matters:* `LIMITATIONS.md` point 6 and the CHANGELOG were brought up to
  date; the READMEs were not. The engine's warning (`api.py:973-977`) also names
  only the power and the division, and question 1 of
  `tp_regression_symbolique.ipynb` now asks students to read that warning.

**3. ROADMAP item 6 says nothing is lost on the other laws; the confirmation of
A3 shows a loss, which the CHANGELOG reports.**
- *Where:* `benchmarks/results_1.1/ROADMAP.md:46`.
- *Claim:* "nothing is lost on the other laws."
- *Records:* in the confirmation (`a3/campaign/compare_a3_conf.txt`), I.50.26 on
  F41 goes from 1 exact fit to 0, and III.17.37 on F41N1 loses its one structure
  (1 → 0). `CHANGELOG.md:14-15` itself says "I.50.26 loses its one exact fit".
  M2 then shows U41N10 3 structures down (I.18.12 −4, II.6.15b −1, III.15.12 +2;
  `r1_m2.txt`).
- *Why it matters:* the sentence overstates, and two documents disagree. The
  criterion that held is weaker: the counts of the eight other laws (20 and 20,
  21 and 21), and no equation falling from three seeds or more to one or none.

**4. The six-laws notebook says, of the current tool, what was measured on A1
only.**
- *Where:* `examples/tp_six_lois.ipynb`, cell 24, source lines 17-18 (file
  lines 326-327).
- *Claim:* "le bruit la cache, car les courbes que l'outil rend s'en écartent
  moins que le bruit des mesures."
- *Records:* E2b (`a1/examine/e2b.txt`) measured the first version, A1, at draws
  0 to 4. It was not measured on 1.3.0. `LIMITATIONS.md:82-84`,
  `CHANGELOG.md:63-65` and the note of `DIAGNOSTIC_TP.md` all say "measured on a
  first version".
- *Why it matters:* a measurement is attributed to the wrong version, in a
  document written for students.

**5. Several M2 figures of the documents come from no committed script or
output.**
- *Where:*
  - `release/README.md:118-123` and `LIMITATIONS.md:141-143`, with
    `LIMITATIONS.fr.md:155-157`;
  - `CHANGELOG.md:66-69` (the formula figures) and `CHANGELOG.md:53-55` (the
    seeds);
  - `release/README.md:138-142` (the seeds).
- *Claims:*
  - `formula_exact` False in 102 fits of the pool `physical` with each version,
    and in 82 of 530 of the pool `trig` against 27;
  - 47 of the 82 with an arcsine, 77 cut at 160 characters, 35 cut with no
    visible arcsine;
  - the arcsine seed placed in 10 fits (exact) and in 25 (noise-tolerant).
- *Records:* every figure holds when recomputed (`r1_m2.txt`, `r2_seeds.txt`). But
  `m2/compare.txt` gives `formula_exact` by suite, with the pools mixed, and no
  file of `m2/` prints the seeds. `m2/arcsine_formulas.txt` gives neither.
- *Why it matters:* the method of the release is that each published figure is
  read from a committed output. A reader cannot reproduce these from `m2/`.

**6. The CHANGELOG states, for `poly` and `conserve`, an identity that no record
measures.**
- *Where:* `CHANGELOG.md:6-8`.
- *Claim:* "The pool `physical`, the default, and `poly` and `conserve` are left
  as they are: with them, the models of 1.2.0 at equal work."
- *Records:* M1, M2 and the mechanics of A1 to A3 check the pool `physical`
  only. `pools_check.py` runs `poly`, but its record keeps only "ajustements :
  48 | violations : 0".
- *Code:* the code supports the claim. The draw lists of `poly` and `conserve`
  are unchanged (`core.py:2100-2107`). `ALL_UNARY_OPS` is used for membership
  only. The A2 rule and the A3 seeds act only on `arcsin`, and `dim_search`
  filters by the pool.
- *Why it matters:* a reasoned claim is worded like a measured one. Either cite
  the code or soften the wording.

**7. `m3/examine/README.md` cites `e2.log` for times it does not hold, against
the release README.**
- *Where:* `m3/examine/README.md:3-4`.
- *Claim:* "Run on 9 November 2026, from 16:21 to 16:26 (UTC) … (`e2.log`)."
- *Records:* `e2.log` is 30 lines of the form "g=… s=… done", with no time.
  `release/README.md:209` says "Its records carry no time".
- *What does support it:* the times are consistent with git. The plan was
  committed at 16:21:31 (7fe0665). 13 of the 30 record pairs were already in
  commit 6b44873 at 16:22:27, which needs about 46 s of fit time. The 30 pairs
  take about 253 s.
- *Why it matters:* two documents disagree, and the file cited does not hold
  the claim. Git could be cited instead.

**8. The M3 comparison counts two records that are not in the repository.**
- *Where:* `release/README.md:169-189`, `m3_compare_1.2.0_vs_1.3.0.txt:189-194`.
- *Claim:* "57 records are the same … Nine records differ … timing, five
  records."
- *Records:* `gp_elite_best.txt` (counted as "same") and `gp_elite_log.csv`
  (counted as "differs", one of the five of timing) are untracked. The csv is
  ignored (`.gitignore:14`).
- *Script:* `m3_compare.py:57-60` walks only the second folder. So the five
  records of the M3 of 1.2 with no counterpart are not listed:
  `deduced_constant_venv11p.txt`, `m3_nohup.txt`,
  `notebook_tp_six_lois_1.2.0.txt` and the two runs of 1.1.0.
- *Why it matters:* 2 of the 71 compared records cannot be checked by a reader,
  and the partition 57 / 5 / 9 is of the 1.3 folder only.

**9. `arcsine_formulas.py` prints a count of cut formulas that is not the bound
it is quoted for.**
- *Where:* `m2/arcsine_formulas.py:31-34` and `:38-39`.
- *Claim:* the docstring says "a formula cut before its first arcsine is not
  listed; the count of the fits whose text is cut is given", and the README
  calls the 105 "a lower bound".
- *Records:* the printed 590 counts all 2,780 fits, 354 of them in the pool
  `physical`, where no arcsine can appear. The fits that could hide an arcsine
  are the 180 of the pool `trig` that are cut with no visible arcsine
  (`r8_cut.txt`).
- *A second gap:* for the noisy suites the script prints the status, never the
  structure. 8 of the 12 F41N1 arcsine formulas retrieve the structure, and the
  listing cannot show it.
- *Why it matters:* the script does what its docstring says, but not what its
  number is used for.

**10. "The same machine" overstates what identical `lscpu` output shows.**
- *Where:* `m2/examine/README.md:4-5`.
- *Claim:* "The machine was the same as M2's: `machine_20261109T1447.txt` is
  identical to `../machine_20261109T0435.txt`."
- *Records:* the two files are identical. But `lscpu` holds no host identity,
  and `release/README.md:6-7` says the container does not always run on the same
  host.
- *Why it matters:* the README should say "the same processor and flags".

**No finding in these classes:**
- *French against English:* every passage changed since 5492296 in `README.fr.md`
  and `LIMITATIONS.fr.md` says what the English says, figure for figure.
- *Broken paths:* none in the added lines (`r7_paths.txt`). Its two "MISS" are
  older short references (`release_1.0/…`, relative to `results_0.9/`) and
  globs.

## Checked and found to hold

**M1.** The eleven configurations of the pool `physical` are identical to 1.2.0.
E_minmax and L_standard differ from 1.2.0, are identical to the candidate of
A3, and have no arcsine. The thirteen take 22.0 s and 22.4 s (`r9_m1.txt`).

**M2, the run.**
- 2,780 jobs per version, the same in both, none twice, no crash.
- The engines are `/venv12p` 1.2.0 and `/venv13r` 1.3.0.
- 2,250 jobs of the pool `physical`, 530 of `trig`, none of `full`.
- From 04:35:30 to 13:43:37, in continuous slices (`driver.log`).
- `compare_m2_1.3.py` is unchanged since b724372 (04:36:51), before the first
  checkpoint of records (06:36:10).

**M2, the table of the release README** (`release/README.md:61-76`):
- F41 163 and 171; F41N1 and F41N10 108 / 85 and 116 / 87;
- R6 median 0.8095; collapses 10 and 10 of 65;
- U41 166 and 174; U41N1 and U41N10 113 / 98 and 121 / 95;
- 1,005 of 1,005 under units, with a median of 30.22 and 30.19 s and a longest
  of 31.53 and 31.6 s;
- TF78 213 and 214; TS14 8 and 8; TR25 0.7692; TF78 under units 229 and 228.

**M2, the pool `physical`.**
- 706 fits where neither version reached its budget; none differs in formula,
  `err` or `formula_exact`.
- 5 of them have a formula of 160 characters. Every other field of these 5 is
  identical, apart from the time, the date and the engine fields.
- 2,234 of the 2,250 return the same formula.
- Two fits change status: vdp1 seed 9 (budget True and False) and U41 I.6.20a
  seed 4 (True and True).

**M2, the pool `trig`.**
- F41 and U41: 20 exact fits become 28, with no loss.
- F41N1 and U41N1 gain 8 structures each (I.26.2 +3, I.30.5 +5).
- F41N10 gains 2 (III.15.12, I.26.2). U41N10 loses 3 (I.18.12 −4, II.6.15b −1,
  III.15.12 +2).
- The arcsine laws: 8 of 10 on F41 and 8 on U41. I.26.2 is exact at seeds 1, 2
  and 4 on F41, and 2, 3 and 4 on U41. I.30.5 is exact at every seed, as
  `arcsin(v0 / (v1 * v2))`.
- `formula_exact` is False in 102 and 102 fits of `physical`, 27 and 82 of
  `trig`, with the 47 / 77 / 35 above.
- The text has an arcsine in 105 fits of 1.3.0, by suite 11, 18, 12, 17, 12, 8,
  3, 16 and 8.
- The exact seed is placed in the 10 fits of I.30.5 on F41 and U41.

**M2, the frozen test set.**
- TF78: 15 and 16 exact fits on its 17 equations of the pool `trig`.
- feynman_test_10: NEAR at seed 5 with 1.2.0, then MISS everywhere.
- TS14: 8 of its 60 fits of the pool `trig` change status, both ways; glider1
  seed 9 goes from EXACT to MISS; out of domain, 30 and 27 collapses.
- feynman_III_8_54: 2 → 0 under units, 0 → 1 without.

**The time budget across campaigns.**
- 1.2.0 counts 214 and 213 exact fits on TF78, and 10 and 8 on TS14, between
  the two campaigns. Each of the 3 fits it loses reached its budget in the M2 of
  1.3, and not in that of 1.2.
- Where neither campaign reached the budget, 789 fits, the formulas are
  identical (`r3_two_campaigns.txt`).
- The 1,983 fits stopped by the budget take 30.54 s at the median and 31.71 s
  at most.

**The pages of the limits** (`r4_limits.txt`):
- 7 and 5 equations never exact on F41, 6 and 4 on U41;
- TF78: 34 and 33 never exact, 203 and 204 of 290 (main), 10 and 10 of 100
  (bonus);
- 11 departing formulas of 130 with each version, 64 and 65 of 500;
- collapses 37 and 28 out of 125, worst −1,946;
- I.11.19 is exact once in five;
- I.26.2 is exact with the arcsine at 3 of seeds 0 to 4 (M2) and at 2 of seeds
  5 to 9 (seeds 7 and 9, A3 confirmation).

**E1 (I.18.12).**
- Its plan was committed at 14:47:08; the first record is dated 14:47:51, at
  the end of a fit of 30 s.
- 40 jobs per version. 12 of 20 structures with each version. 7 of 8 parabolas
  with 1.2.0 (seed 11 gives a tanh), 8 of 8 with 1.3.0. No arcsine.
- The F41N10 control: 20 of 20, every fit at its budget. Median generations
  96.5 / 97 and 110 / 109.5.
- The parabola against sin θ on [0, 3.14]: at most 0.0453 apart, root-mean-square
  0.0261, 3.7 % of that of sin θ.
- In M2, 1.3.0 returns the same parabola at seeds 0 to 3.

**E2 and M3.**
- E2: 6/4, 8/2 and 7/3, with p of 0.754, 0.109 and 0.344. The formula departs
  in 1 / 4 / 2 fits with 1.3.0 and 1 / 1 / 1 with 1.2.0; 6 of the 7 have an
  arcsine. Median sizes within one node, median times within 0.2 s. At seed 0,
  the MSE and sizes are those of the notebook snippet. The arguments 1.11 and
  ±1.49 hold.
- M3:
  - the partition 57 / 5 / 9 holds;
  - `kepler_minmax_check`: 2 / 0 / 4 / 2 against 0 / 0 / 3 / 1;
  - the scaling: 41.2 s and 113.4 s against 38.0 s and 103.1 s, with all 85
    models identical, III.15.12 of the pool `trig` among them;
  - `time_limit_check`: 14 of 16, 6.3 s and 13.2 s;
  - the TP table, 50 / 52 against 51 / 51, with the same formulas in all four
    runs;
  - the deduced constant differs only by the line of the version;
  - `tp_six_lois.py` holds the notebook's code cells.

**M4.** 182 tests pass under 3.9.25, 3.11.18 and 3.14.6, 13 of them in
`test_arcsin.py`. The pins are those of the M4 of 1.2. `twine check` passes on
both files. CI is green on 5492296 to 6bf3804, and does not run on the three
commits that change documents only.

**The code.**
- `arcsin` has weight 2 in `trig` and `full` only.
- The model clips its argument; the printed formula does not.
- The sympy form is `asin`.
- Under units, the argument must be dimensionless, and so is the result.
- The A2 rule writes arcsin(u) as arcsin(1 · u).
- The A3 seed is b·f·arcsin(c·g), with b of at least 2/π times the largest
  |y/f|, the plain form tried first, and only where the pool has `arcsin`. It is
  among the noise-tolerant seeds too.

**The scripts.** `compare_m2_1.3.py` computes what `release/README.md` says. Its
criteria follow the plan, its pools come from the bench, and it compares the
formula on its first 160 characters, as the documents state. `arcsine_formulas.py`
does what its docstring says, apart from finding 9.

**The other documents.**
- *README.md and README.fr.md:* every changed figure holds, apart from finding 2:
  41 s / 113 s, version 1.3.0; 1,983, 30.5 s and 31.7 s; 13.2 s; 174 / 171
  against 166 / 163; 214 / 213, 8 / 8, 228 / 229, and the reason given for the
  213 and 8. So do the arcsine bullet and the entry of 1.3 in what's new.
- *The paper:* its four changed passages hold.
- *DIAGNOSTIC_TP.md:* the note holds: 0 of 40 on two sets of draws; 18 / 19
  and 20 / 20 within 1 %; E2b with a median of 0.205 and at most 0.988; E2a with
  1 of 10 for A1 (2.4e-10, 20 to 59 generations, up to 8.4e-6) and 0 of 10 for
  A2.
- *The CHANGELOG:* its figures hold, apart from findings 1 and 6: 8 and 7, 20
  and 21, I.50.26 and III.17.37; A1 with 1 of 10 and A2 with 3; 2 against 1 and
  4 against 3 on Kepler.
- *The SRBench section:* it agrees with `results_1.1/srbench_settings/README.md`
  and `srbench_2aabbb6/README.md`.
- *The case studies:* they are unchanged and use the default pool. Their records
  are "same" in M3.
- *The notebooks:* the new question 2 matches seed 0 with 1.3.0 (MSE
  5.654e-02 → 1.628e-02 → 1.281e-03, sizes 38 / 46 / 43). So does the new text
  of question 1.

**Two notes, not findings.**
- The Snell figures said "with 1.3.0" come from the candidate of A3
  (`/venv13c`, commit 492863e). Its records carry `engine_version` 1.2.0. Its
  engine is that of 1.3.0, since 5492296 changes only the version number.
- The "48 s" of the TP notebook (`README.md:158-159`) and the "7 to 10 s" of
  `LIMITATIONS.md:173-174` are the figures of 1.2.0 of 5 November. The M3 of 1.3
  measures 51 s and 7 to 11 s with each version that day. This is not an effect
  of the version.
