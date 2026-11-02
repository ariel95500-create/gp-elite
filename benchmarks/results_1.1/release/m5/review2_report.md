# M5 of release 1.1.0: second independent review (30 October 2026)

Reviewer: a second agent that had not seen the work. Repository at
`/home/user/gp-elite`, branch `claude/peaceful-knuth-4q7m4p`, HEAD 03a2a3b.
I modified no file and ran no fit. The only scripts I ran read records:
my own recomputation of the M2 records, `m2/details.py` and
`release_claims/compare_m2_1.1.py`. After they ran, `git status` was still
clean.

## Scope and method

I checked these documents:
- `README.md` and `README.fr.md`, in full;
- the 1.1.0 entry of `CHANGELOG.md`;
- `LIMITATIONS.md` and `LIMITATIONS.fr.md`, in full, with the intro and point 8 above all;
- `paper/paper.md`, wherever it describes 1.1 or the units mode, and also its
  provenance and disclosure paragraphs;
- `examples/tp_six_lois.ipynb`;
- the six case-study notebooks (none has stored outputs, so only the text was
  checked);
- `release/README.md`, `M5_review1.md` and `m5/review1_report.md`;
- `../PLAN_U2.md`, `../ROADMAP.md` and `../srbench_2aabbb6/README.md`;
- `candidate1/README.md`, where M5_review1 says it was corrected.

I checked about 520 claim occurrences, about 270 of them distinct, against the
records. I recomputed the following from the raw records:
- every M2 figure, from `m2/campaignR_*.jsonl` and the first candidate's
  `candidate1/m2/*.jsonl`;
- the 1.0.0 release campaign, from `results_0.9/release_1.0/m2/*.jsonl`, to
  trace each figure the limits pages quote;
- the U2 check, from `u2check/*.jsonl`;
- the notebook timing sums;
- the TP notebook's percentages;
- the scaling totals.

I also checked provenance with read-only git commands and the SRBench files
against the clone at 2aabbb6, by blob hash and line number.

## Confirmed (headline)

**M2.** `compare.txt` and `details.txt` are reproduced byte for byte by their
scripts, and my own recomputation from the jsonl agrees:

| indicator | 1.0.0 | 1.1.0 |
|---|---|---|
| F41 exact | 163 | 163 |
| structure, F41N1 / F41N10 | 108 / 86 | 108 / 86 |
| R6 folds, median R² | 0.8095 | 0.8095 |
| R6 + R7raw collapses | 10 | 10 |
| U41 exact | 108 | 165 |
| five families, exact of 90 | 16 | 57 |
| never exact, of 41 | 13 | 6 |
| structure, U41N1 / U41N10 | 79 / 80 | 113 / 99 |
| audit under units | 1,005 of 1,005 | 1,005 of 1,005 |
| U41 median time (s) | 30.1 | 0.52 |
| TF78 exact | 213 | 213 |
| TS14 exact | 8 | 8 |
| TR25 median R² | 0.7657 | 0.7657 |
| TF78 under units, exact | 169 | 226 |
| TF78 under units, median time (s) | 30.3 | 1.6 |

The seven criteria are met.

**Without units** (1,775 jobs):
- 47 jobs return another expression, all at the budget, and none changes status;
- TS14 out of domain goes from 27 to 28 collapses (strogatz_barmag1, seed 8, at
  the budget in both versions);
- formula departures go from 119 to 125. The six changes are all True to
  False, and all six are among the 47.

**Under units:**
- U41: 14 equations gain exact fits and none loses any;
- TF78 under units: 16 equations gain and none loses;
- II.11.28: seed 5 goes from EXACT to NEAR, and seeds 6 to 9 go from MISS to
  EXACT;
- equations never exact on TF78 under units: 37 to 30.

**1.0.0 in two campaigns:**
- 114 jobs differ without units, all at the budget, and 3 go from NEAR to MISS
  (II.2.42 seed 1, strogatz_bacres1 seed 7, strogatz_predprey1 seed 8);
- 43 differ under units;
- R6 collapses 5 then 4, R7raw 5 then 6, TR25 median 0.7691 then 0.7657.

`details.py`, run on the first candidate's records, returns the figures of
`candidate1/README.md`: 35 differing jobs, 15 equations gaining, R7raw 5 to 6
collapses and TR25raw 26 to 27.

**The II.11.3 table.** With 1.1.0, 5/5 runs in all three arms, 20 nodes and
about 1 s per run (typed runs 0.9 to 1.3 s). With 1.0.0 (`release_1.0/m3`),
2/5 recovered, 27 nodes and 27 s, with out-of-domain R² from 0.32 to 0.65 for
the three approximations. With 0.9.0, 0/5 valid, 59 nodes, test R² 0.99157.

**Feynman 15 with units.** 15/15 with 1.1.0 against 14/15 with 1.0.0, 14 in
textbook form. I.16.6 comes back with the factor 1.00758 above and below.

**Feynman 15 and the duel.** 15/15 for GP_ELITE against 6/15 for gplearn, and
15/15 against 7/15 within 1e-3. GP_ELITE is ahead on 9 equations and tied on 6.
0.9.0 had 12/15.

**Scaling.** The five fits take 58.4 s at 1,000 points and 153.4 s at 10,000.
I.16.6 is exact in 5 of the 13 runs below 1,000 points, and its fit at 2,000
points is not in textbook form.

**time_limit, run alone.** 17.0 s in parallel and 9.4 s in sequence, R²
1.0000, 15 of 16 checks, on 3,000 rows.

**Unchanged examples.** These records are the same as in 1.0:
- the README Kepler block;
- the usage example (33 nodes);
- the console (250 kg/s²);
- the mystery constant (250, 6.674e-11, 8.314462617999999);
- the robust table;
- the battery example (+0.162).

**The TP notebook.**
- Every formula, time and percentage in its text matches the record. The six
  fits take 42 to 55 s, 294 s in all.
- Its code cells are identical to `m3/tp_six_lois.py`.
- The notebook pair: 1.0.0 took 285 and 298 s, 1.1.0 took 302 and 300 s
  (means 291.5 and 301).
- The gas law took 48.6, 49.5 and 49.8 s. The free fall took 50.5 to 51.3 s,
  against 43.1 to 44.1 s with 1.0.0.
- With the first candidate, the gas law took 77.0 to 78.9 s, against 49.9 to
  51.2 s with 1.0.0.
- 1.0.0 took 243 s on 27 October.

**The U2 check.**
- 120 of 120 with both engines;
- median time 46.1 s against 44.2 s;
- total time 10,054 s against 9,117 s;
- the gas law median goes from 83.4 s to 43.1 s;
- the same-expression counts match;
- the U2 mechanics: 45.4, 44.3 and 44.3 s.

**The U1 decision.** 107 to 165 on U41, then 107 to 166 on five seeds never run
(`campaign/compare_u1*.txt`).

**Kepler.** Every number in both languages:
- 0.002 %, 0.0016 %, 0.55 %, 0.043 %, 0.27 to 0.28 %;
- 2.6 % and 0.8 %, 0.0068 yr (2.5 days), 0.56 %, 0.08 %;
- the four other forms written by 1.0, with seed 3 the same;
- times "under a second to about ten seconds" (0 to 11 s).

**Hubble.** Every number in both languages: 62 %, 38 %, 423.94, 454.16, 224
and 223, 203 and 231, the move of 2 %, 10 to 20 s per fit, and no seed placed.

**Nikuradse.** The 1.1.0 records equal 1.0.0's except for the paths, and the
spot-checked figures match.

**Provenance:**
- no change to `gp_elite/`, `tests/`, `pyproject.toml` or `CITATION.cff`
  between 26349ef or 6e0e296 and HEAD;
- 82f303e to 66abffa changes only `benchmarks/tp_diagnostic.py` outside
  `results_1.1/`;
- M1: 13/13 identical in both comparisons;
- M4: 154 passed under each of the three Pythons, and twine PASSED;
- 60 M3 records are the same between the candidates;
- the import median is 0.117 s;
- M2 runs from 20:14 to 07:01 with the restart at 01:15/01:16 (`m2/driver.log`);
- every Tests run on the branch since 7133e86 is green
  (`gh run list`). The one commit without a run, 0705868, changes only .md
  files, which the workflow ignores.

**SRBench.** The four blob hashes, the README line 39, `gp-elite>=0.8.0`, the
metadata line and the hyper_params grid all match the clone at 2aabbb6. PR
#212, #227 and #232 are in its history.

## The first review's corrections

Corrections 2 to 16 are right as made. The other two are incomplete:
- **#1, the limits intro.** The qualifier is right for the four figures it
  names, but it omits point 6 (finding 1).
- **#17, the SRBench record.** It exists and the hashes match, but one line
  reference is wrong (finding 3).

Also:
- the fix of #11 (only the inner-planet Kepler fit changed) was made in the
  CHANGELOG but not in `candidate1/README.md` (finding 5);
- the overstatement that #6 fixed in the CHANGELOG ("the same counts") remains
  in both READMEs and the paper (finding 2).

## Findings

### 1. Limits intro: point 6 also moves, and the versions differ there (inconsistency)

**Where.** `LIMITATIONS.md`, intro:
> "under the budget of 30 s, the counts move a little from one campaign to the next, for both versions alike (measured beside 1.0.0 for the release of 1.1, both give 108 and 86 structures under noise, 8 exact Strogatz fits of 70 and 10 collapses of 65, where the points below say 105, 85, 7 and 11)."

`LIMITATIONS.fr.md` has the same sentence.

Point 6 says:
> "On the real data this happened in 7 fits of 130 on the bench and 61 of 500 on the test set."

**Record.** Fits with `formula_exact` False on the real data
(`real` + `realraw` = 130 fits; `tr` + `trraw` = 500 fits):

| campaign | bench, of 130 | test set, of 500 |
|---|---|---|
| `release_1.0/m2`, 1.0.0 (the source of point 6) | 0 + 7 = 7 | 30 + 31 = 61 |
| `release/m2`, 1.0.0 | 0 + 7 = 7 | 31 + 35 = 66 |
| `release/m2`, 1.1.0 | 1 + 7 = 8 | 32 + 35 = 67 |

So in this campaign 1.0.0 gives 7 and 66 and 1.1.0 gives 8 and 67. Point 6
says 7 and 61. Two things are wrong:
- the intro's list of figures that move leaves out point 6;
- "both versions alike" does not hold for these counts.

**Change.** Add to the parenthesis, in both languages: "...and 7 and 66
printed formulas that depart from `predict()` on the real data with 1.0.0,
8 and 67 with 1.1.0, where point 6 says 7 and 61". Limit "for both versions
alike" to the counts it names.

### 2. READMEs and paper: "the same counts" on the frozen set overstates (wording)

**Where.**
- `README.md`, "Is it solid?": "both versions give the same counts without units on the frozen set (213 exact laws of 390 …, 8 of 70 …)".
- `README.fr.md`: "les deux versions donnent sans unités les mêmes comptes sur le jeu figé".
- `paper/paper.md` l. 221–223: "both give the same counts without units (213 exact laws in 390 fits, and 8 in 70 …)".

**Record.** In `release/m2` on the frozen set, 1.1.0 has:
- one more TS14 collapse out of domain (27 to 28);
- five more formula departures (tf 7 to 10, tr 31 to 32, ts 25 to 26).

These are the same differences the first review's #6 made the CHANGELOG
name.

**Change.** "the same exact-law counts without units" (FR: "les mêmes
nombres de lois exactes").

### 3. SRBench record: wrong line reference for the estimator (error)

**Where.** `srbench_2aabbb6/README.md`:
> "the estimator is built with `operators="physical"`, `generations=60`, `max_time=3600` and `restarts=10` (lines 40 to 46)".

**Record.** In the clone at 2aabbb6, `experiment/methods/gp-elite/regressor.py`:
- lines 40–46 are the default arguments of `GPEliteSRBench.__init__`;
- the estimator `est = GPEliteSRBench(...)` is built at lines 129–136, also
  with `speed="fast"` and `random_state=0`.

The values are right.

**Change.** "(lines 129 to 136; the same values are the defaults of
`__init__`, lines 40 to 46)".

### 4. PLAN_U2 and the U2 mechanics point to records that have moved (inconsistency)

**Where.** `PLAN_U2.md`:
- l. 4: "after M3 of the release 1.1.0 (`release/README.md`)";
- l. 10–12: "takes 77 to 79 s against 50 to 51 s (`release/m3/tp_timing/`)".

`mechanics/U2_gas_law.txt` l. 10: "1.1.0 (U1): 77.0, 78.1, 78.9 s (`release/m3/tp_timing/timings.txt`)".

**Record.** The first candidate's records were moved to `release/candidate1/`
on 29 October (`candidate1/README.md` l. 3–8). Now:
- `release/README.md` describes the second candidate;
- `release/m3/tp_timing/` holds the second candidate's `gas_1.1.0.txt`
  (48.6 to 49.8 s);
- `release/m3/tp_timing/timings.txt` no longer exists. The 77 to 79 s are in
  `release/candidate1/m3/tp_timing/timings.txt`.

**Change.**
- `PLAN_U2.md`: point to `release/candidate1/README.md` and
  `release/candidate1/m3/tp_timing/timings.txt`, with a dated note that the
  records moved.
- `mechanics/U2_gas_law.txt`: the same note, or leave the file and add the
  note in PLAN_U2.

### 5. candidate1/README: "the typed fits" of Kepler (error)

**Where.** `release/candidate1/README.md`, M3:
> "Kepler (`case_kepler.txt`, `deduced_constant_venv11.txt`): the typed fits return the textbook form `5.45416e-10 * X0 * sqrt(X0)` at every seed, in under a second."

**Record.**
- `candidate1/m3/case_kepler.txt` (and `m3/case_kepler.txt`): only fit B
  (four inner planets) returns `5.45416e-10 * X0 * sqrt(X0)`, in 0 s. Fit A
  (eight planets, typed) returns `5.43909e-10 * X0 * sqrt(X0)` in 8 to 10 s,
  as with 1.0.0.
- `deduced_constant_venv11.txt`: the typed "README table, 8 planets" fit
  returns `5.45084e-10 * X0 * sqrt(X0)`.

This is the first review's #11, corrected in the CHANGELOG but not here.

**Change.** "the typed fit on the four inner planets returns the textbook
form `5.45416e-10 * X0 * sqrt(X0)` at every seed, in under a second; the
typed fit on the eight planets returns `5.43909e-10 * X0 * sqrt(X0)` as with
1.0.0."

### 6. Paper: the AI disclosure stops at 1.0 (inconsistency, stale)

**Where.** `paper/paper.md` l. 258–280:
> "Its contributions were: … for version 0.8, …; for version 1.0, the families of forms fitted directly, the noise-tolerant seeds, the correction of the deduced constant and the case studies; …"

**Record.** The paper now describes 1.1: l. 57–58, 176–178, 203–210 and
220–225. The 1.1 engine commits are authored by Claude:
- cf29313, U1;
- eb56efd, U1 confirmed;
- 26349ef, U2.

The French TP notebook and the TP diagnostic also came from that work.

**Change.** Add "for version 1.1, the fitted forms acting under units and
the correction of the power-law seed, the French TP notebook and the
diagnostic behind it" after the author confirms.

### 7. LIMITATIONS.fr point 8: "graines aléatoires" (wording, inconsistency between languages)

**Where.** `LIMITATIONS.fr.md`:
> "six équations ne sont jamais retrouvées avec cinq graines aléatoires (1.0.0 : 13)"

**Record.** The English says "in five seeds". The seeds are the fixed values
0 to 4 (`m2/campaignR_*.jsonl`, `ufeyn`), not random ones.

**Change.** "avec cinq graines", as in point 1 and the English.

### 8. CHANGELOG 1.1.0: "They now run as without units" (wording)

**Where.** `CHANGELOG.md`, 1.1.0:
> "They now run as without units, and a seed is placed only if it passes the gate of dimensions …"

**Record.** The same entry's "Fixed before the release" (U2, `PLAN_U2.md`
"The change") says the following. Under units, the power-law finder makes its
fitted-exponent seed only when the exponents that are not half-integers fall
on dimensionless inputs. Without units it always makes it. So under units the
finders do not run exactly as without units.

**Change.** "They now run under units too, and a seed is placed only if …"

### 9. ROADMAP: the law placed at generation 0 is traced for two of the six TP fits (unsupported)

**Where.** `ROADMAP.md` l. 62–64:
> "on the noisy data of the TP notebook, version 1.1 places the law at generation 0, but no law is exact …"

**Record.** Traces exist only for:
- the free fall: `m3_extra/fall_trace_1.1.0.txt`, seed `(t)²`;
- the gas law: `m3/tp_timing/gas_1.1.0.txt`, seed `((n * T) / V)`.

There is no trace for the pendulum, the spring, the power or the
illuminance. The TP notebook itself says only "par exemple pour la chute libre
et le gaz parfait".

**Change.** "places the law at generation 0 in the fits traced (free fall,
gas law)", or record the traces of the other four.

### 10. ROADMAP: "or elsewhere" has no record (unsupported)

**Where.** `ROADMAP.md` l. 22–23:
> "No date for the next update is published, in the repository or elsewhere."

**Record.** `srbench_2aabbb6/README.md` records only the four files of the
repository.

**Change.** Drop "or elsewhere", or record where else was searched and when.

### 11. Release README: the free-fall timings have no driver or log (unsupported)

**Where.** `release/README.md`, M3:
> "Timed alone three times in turn (`m3/tp_timing/fall.py`, `fall_timings.txt`), it takes 50.5 to 51.3 s against 43.1 to 44.1 s with 1.0.0."

**Record.**
- `m3/tp_timing/fall_timings.txt` holds only the six result lines.
- No command, time or "alone" is recorded, unlike `gas_1.1.0.txt`
  (`m3/m3_driver.sh`, `m3_driver.log`) and `notebook_pair/` (`run.sh`,
  `run.log`).
- The file was committed in e026182 (08:30), after the pair ended at 08:22.
- These figures are the "51 s against 44 s" of the CHANGELOG and of both
  LIMITATIONS pages.

**Change.** Add to `fall_timings.txt` the command that ran it, its date and
its times. If none was kept, say so in the README.

### 12. Paper: date (wording, stale)

**Where.** `paper/paper.md`, front matter: `date: 14 October 2026`.

**Record.** The paper now describes 1.1.0, measured on 29 and 30 October
(`release/README.md`).

**Change.** Set the date at gate 6, or keep it if it is meant as the date of
first submission. The author decides.

## Notes (not findings)

- `CITATION.cff` (outside the listed scope) has `version: 1.1.0` with
  `date-released: 2026-10-17`, the date set for 1.0.0. The plan leaves the
  date to the day of publication, so it is to be set at gate 6.
- The Hubble notebooks name only the 0.9 output file (cell 0 and section 8),
  while the Kepler notebooks also name the 1.1.0 file. The figures are the
  same in the 0.9, 1.0.0 and 1.1.0 records, so nothing is wrong. Naming
  `results_1.1/release/m3/case_hubble.txt` would match Kepler.
- README "Programmatically" says the parallel islands return "an approximation
  of R² 0.99998". This was measured for 1.0.0
  (`release_1.0/m3_extra/parallel_islands/`, 0.9999765) and not again for
  1.1.0. That is consistent with M1 (no change without units).
- The TP notebook links to `PLAN_U2.md` for "avec la version 1.1.0 … 120 sur
  120". There, "1.1.0" names the first candidate and "U2" names the released
  engine. Both give 120 of 120, so the claim holds.
- The release README's "the seven are met" is followed by six bullets, with
  F41N1 and F41N10 merged into one. This is correct.
