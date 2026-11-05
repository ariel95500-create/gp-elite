# Release 1.2.0, M5: second independent review

Reviewer: a second agent who had not seen the work. Date: 5 November 2026.
Repository: `/home/user/gp-elite`, branch `claude/peaceful-knuth-4q7m4p`, HEAD 45b8282
(working tree clean; nothing in the repository was modified).

## Scope and method

Documents checked, as `PLAN_RELEASE_1.2.md` (M5) and the request list them:
- `README.md` and `README.fr.md`: every figure, every sentence 1.2 could make false, and the
  French against the English, passage by passage;
- the 1.2.0 entry of `CHANGELOG.md`;
- `LIMITATIONS.md` and `LIMITATIONS.fr.md`, the whole of both: the introduction and points 1
  to 10, against the records of the releases of 1.0, 1.1 and 1.2 and of campaign H1;
- `paper/paper.md`, the whole of it;
- `examples/tp_six_lois.ipynb`, every cell, against `m3/notebook_tp_six_lois_1.2.0.txt`,
  `m3/tp_timing/notebook_pair/` and, for section 10, `x1/x1_tp_check.txt`,
  `h1/campaign/compare_h1*.txt` and `results_1.1/tp/tp_1.0.0.jsonl`;
- `examples/quickstart.ipynb`, `quickstart.fr.ipynb` and the six case-study notebooks, against
  the M3 records of 1.2.0;
- `benchmarks/results_1.2/release/README.md` and `M5_review1.md`, every figure;
- the note at the end of `benchmarks/results_1.1/DIAGNOSTIC_TP.md`;
- the corrections of the first review (`git show 45b8282`), each of the 19.

Method. No summary was trusted, the release record's included. Read-only git (`log`, `show`,
`diff`) only. Small read-only scripts run with `python3 -I`, which read the JSON and text
records and import nothing of the engine; no fit was run. The scripts and their outputs are
in this folder:
- `m2_check.py` / `.out`: every M2 indicator of both versions from
  `release/m2/campaignR_1.1.0.jsonl` and `campaignR_1.2.0.jsonl` (2,780 + 2,780 records):
  pairing, suites and counts, statuses and structures, NEAR, medians, collapses and their sets,
  the units audit, medians and maxima of time, fits at the budget, expression differences
  split by cause, X1 rewrites by suite, the `formula_exact` / `expr_11` checks, the fits where
  neither version reached its budget, and the 15 fits of III.19.51 with their generations;
- `h1_check.py` / `.out`: campaign H1 and its confirmation (`h1/campaign/D_*.jsonl`,
  `tp_*.jsonl`): exact laws, structures, NEAR, medians and maxima of time, generations,
  R6 and R7raw medians and collapses, equations whose exact seeds change, the longest fit under
  units, and the TP fits whose formula or law differs;
- `limits11.py` / `.out`: the counting of `release/m2/limits_figures.py`, re-implemented, on
  the records of the releases of 1.0 (`results_0.9/release_1.0/m2/`), 1.1
  (`results_1.1/release/m2/`) and 1.2, plus the I.34.1 formula of point 3;
- `misc_check.py` / `.out`: the TP notebook times (pair and single run), the scaling sums,
  the import medians, the X1 arithmetic (τ of every quoted example), the constants of the
  notebook, and the R6 medians of campaign H1.

Besides: the M3 diffs (`m3_compare_1.1.0_vs_1.2.0.txt`, and the scaling, Nikuradse and
small-data records compared entry by entry with those of 1.1), `time_limit_check.txt` of both
M3 and the four runs of `m3_extra/time_limit_pair/`, the M1, M2 and M3 driver logs,
`removed_for_the_data_cache.jsonl`, `environments.txt`, M4 records, `d0/D0.md`,
`fix/compare_mechanics.txt` and `fix/mechanics_fix.py/.jsonl`, `x1/x1_tp_check.txt`, every
path cited by the documents in scope (all exist), and the code: `api.py` 493–667 (signature,
`patience`), `core.py` `_Patience`, `_holdout_mse`, `_split_holdout` and both generation
loops, `Island.initialize` (typed start and deadline), `dim_search._monomial_tree`,
`typed_random_tree` and `_surrogate_target`, `formula.py` 468–535 and `raw_formula`
(X1), `sklearn_api.py` (`_resolve_generations`), the presets of `duel.py`,
`feynman_bench.py`, `feynman_units.py` and of every example script and notebook (whether H1
can act on them).

Judged by the method of the project: times compared only within one campaign or one day;
the frozen test set decides nothing and is published as measured; a changed figure is
published as measured with its reason.

## Claims checked

About 450 claims (figures, formulas, paths, statements about behaviour) were checked; about
220 of them were recomputed from the records rather than read from a summary: every M2
indicator and count in every document that quotes it, the III.19.51 table and its ratios,
the times at the budget, every figure of point 10 of the limits and of the CHANGELOG's H1
paragraph, every figure of the limits pages against the records of 1.0, 1.1 and 1.2, the TP
notebook times and constants, the scaling sums, the import medians, the X1 arithmetic of every
quoted example, the Nikuradse sizes, R², gaps and forms of the five seeds, the R6 medians of
campaign H1. The rest were checked by reading the record they cite (M1, M4, driver logs,
D0, fix, x1, case-study and snippet records that M3 marks "same").

## Parts with nothing wrong

- **M2 figures**, wherever they appear (release README table and text, CHANGELOG, both
  READMEs, both pages of the limits, paper): 2,780 paired jobs, none twice, no crash; F41 163
  and 163; F41N1 / F41N10 108 / 85; R6 median 0.8095 (0.809459); collapses 5, 5, 38, 28, 28,
  the same sets in both versions; U41 166; U41N1 / U41N10 113 / 98; 1,005 of 1,005 under
  the audit; median under units 30.2 and 30.19; longest 420.73 and 31.55; 31.5 and 31.55
  without III.19.51; TF78 214, TS14 10 of 70, TR25 0.7692, utf 229; no status or structure
  change; 316 other expressions = 276 by X1 alone (257 + 19) + 40 other models (22 + 18);
  287 rewrites (267 + 20), 11 of them on the 40 other models; 1,360 `expr_11` present,
  `formula_exact` never changed; 316 + 471 = 787 fits with neither version at its budget and
  no difference; 1,993 and 1,987 at the budget; 30.5 s median and 31.94 s maximum of
  1.2.0's; III.19.51 0.99–1.16 s, 30.12–30.46 s, 30.05–30.40 s against 342–387, 334–421,
  341–384 s; 1 generation against 35–40; I.6.20a seed 1; 17 removed jobs (13 + 16 crashes);
  806 and 2,229 pairs at the restarts; the 13 criteria. All correct.
- **Campaign H1 and its confirmation** (CHANGELOG, LIMITATIONS point 10, DIAGNOSTIC note,
  notebook cell 0): 6.8 / 22.8 s, 8.1 / 32.2 s, 126 / 119, 120 of 120, 119 of 120 on the
  new draws, 161 / 163, 166 / 167, 83 / 85, 100 / 99, NEAR 146 / 153, 0.802 / 0.809,
  9 / 11 collapses on the 65 out-of-domain fits (3 / 4 on R6), 7.4–9.4 s against 24.7–34.9 s.
  All correct.
- **The pages of the limits, points 1 to 7 and 9**, against `results_0.9/release_1.0/m2/`:
  163 (0.9.0: 88, +85 %), the seven equations, I.11.19 once, 34 never on the test set, 213
  of 390 (145, +47 %), 203 of 290 (144), 10 of 100 (1), 7 Strogatz of 70 (8), 105 and 85
  structures (67 and 66), the I.34.1 formula, 11 collapses of 65 to −233, 64 of 250 (37 and
  27), six datasets with 28 of 37, 7 of 130 and 61 of 500, the min-max Kepler check 1 of 10
  against 3. The 1.1 introduction (108 / 86, 8, 10, 7 / 66, 8 / 67) against the records of the
  release of 1.1, point 8 (165 / 108, 6 / 13; TP times 7–10 s against 28–37 s) and the 1.2
  paragraph (214, 204 / 290, 10 / 100, 33, 10, 108 / 85, 10 of 65 to −1,946, 66 = 38 + 28,
  12 / 130, 65 / 500, 166) against `m2/limits_figures.txt`, recomputed independently. All
  correct.
- **M1, M3 and M4 of the release README**: 13 identical, 21.7 and 21.1 s; 40 records the
  same, 22 differ, 9 new; 38.0 / 103.1 s against 58.4 / 153.4 s; import 0.073 against
  0.117 s; one generation 0.6 against 1.0 s; 13 of 16 against 15 of 16, 6.3 and 12.5 s, the
  three failing checks named rightly, 13 / 14 and 13 / 13 in the pair; the notebook 8, 10, 8,
  8, 8, 7 = 49 s, the pair 198 / 194 against 48 / 48; the X1 examples (1.939, 6.98808,
  1.42857, sizes 13 to 72); 169 tests under 3.9.25, 3.11.18 and 3.14.6, `twine` PASSED, the
  engine identical from a263177 to HEAD but for the version number.
- **The TP notebook**: every quoted formula, time, constant and percentage of cells 0 to 22
  matches its M3 run (g 9.814 within 0.1 %, factor 6.30042 = 2π + 0.27 %, g 9.741 0.70 %
  under, R 0.77 % under, P 10.02 W); section 10: the capacitor 4 of 5 at 10 points without
  units (both versions, both sets of draws), the example of draw 1 and its τ = 1.03105, the
  1.0.0 / 1.1.0 power it replaces (the same constants in `tp_1.0.0.jsonl` and `tp_A.jsonl`),
  no front below 30 rows.
- **The quickstart and the case studies (English and French)**: every figure and formula
  still holds on the M3 records of 1.2.0 (Kepler 30 generations, Hooke 250.0, the Nikuradse
  short run with its 304 rows and its seven-node log of a log; Kepler 0.0016 %; Hubble; the
  Nikuradse front, champion 48–70 nodes at 0.980–0.995, 10 to 13 forms, gaps −1.20 to +0.88,
  best 0.014 to 0.225, identical in the five seeds' files). Every notebook but the TP one sets
  its budget, so H1 never acts on them. Their texts claim identity up to 1.1.0, which is true;
  1.2.0 prints some long Nikuradse formulas differently (X1), which none of the texts quotes.
  The French notebooks carry exactly the numbers of the English ones.
- **French against English**: the two READMEs (every passage 1.2 touched, line by line) and
  the two pages of the limits (the whole) say the same things; no translation error found.
- **The DIAGNOSTIC note**: correct (points 2 and 4, the times, the formula of draw 1 and its
  τ, C1, points 3 and 5).
- **The paper**: the duel (15/15 against 6/15, versions 1.0.0 to 1.2.0), 166 of 205 and the
  1,005 audits, the frozen set (214, 10, 229), the case studies, the mystery constant, the
  list of records (every folder exists). Apart from finding 8, correct.
- **Paths and links**: every path cited by the documents in scope exists.
- **Code against the documents**: H1 acts only when neither `generations` nor `time_limit`
  is given (`api.py` 657–664), 1 % gain (`_PATIENCE_GAIN`), 30 generations, polishing and
  selection after the stop, an integer k whatever the budget, 0 off, a bool or negative value
  refused; `GPEliteRegressor` always passes its generations; X1 is tried only when the formula
  passes its check and kept only if the rewritten one passes it; D0 accepts up to 12 factors,
  each exponent at most 4, and an island stops drawing at the deadline once it has a tree;
  the typed start is the only caller of `typed_random_tree`. Apart from findings 1 to 3, the
  documents describe them correctly.
- **The corrections of the first review** (commit 45b8282): 15 of the 19 are right and
  complete as made. Finding 2's record carries a new rounding error (finding 6 below);
  finding 3's correction leaves a count that reads wrongly in the CHANGELOG (finding 5);
  finding 17's precision was not carried into the two feature entries the same commit added
  (finding 3), nor into the release README's sentence on the notebook (finding 2); finding 4
  was not carried into the READMEs, where the first review judged the sentence accurate
  (finding 1).

## Findings

Kinds: wrong figure, unsupported figure, stale sentence, translation, wording, missing
record, broken path. Ordered by weight.

1. **`README.md` 562–563, `README.fr.md` 602–604 ("What's new", 1.2): "With a budget set,
   the models of 1.1 at equal work".** D0 changes models with a budget set, at equal work. In
   M2, at `time_limit=30`, III.19.51 under units, U41 seeds 0 and 3, both versions ran one
   generation (`generations` 1 and 1 in both records) and return other expressions:
   1.1.0 `-0.00316629 * v0 / (v2 * v4 / (v1 / (v3 / v1)))²` and
   `-0.00316629 * v0 * (|v1 / v4| * v1 / (v2 * v3))²`, 1.2.0
   `-0.00316629 * v0 * (v1²)² / (v2² * v3² * v4²)` (`m2_check.out`); and by its code the
   widened fast path changes any typed start drawing a product of 9 to 12 factors, whatever
   the budget (`dim_search._monomial_tree`, `max_terms=12`). The same sentence was corrected
   in both pages of the limits and in the CHANGELOG after the first review (its finding 4,
   which judged the READMEs' sentence accurate); the READMEs still say it. Kind: **stale
   sentence** (a claim the records and the code contradict).

2. **`benchmarks/results_1.2/release/README.md` 226–228: "That is H1: the notebook sets
   neither `generations` nor `time_limit`, so each search stops once its error on the
   hold-out rows has not improved by 1 % in 30 generations."** The notebook's tables have ten
   rows. Below 30 rows the engine keeps no hold-out (`core._split_holdout`: `n < 30` returns
   the rows unsplit; `results_1.1/DIAGNOSTIC_TP.md`, "One deviation"), so for these six fits
   the stop reads the training error (`core._holdout_mse`, fallback `_pure_mse`). The first
   review's finding 17 added "(the training rows when there are none)" to the general
   statements, but this sentence is about the very case where there are none, and was left
   as it was. Kind: **wording** (a claim the code contradicts).

3. **`README.md` 514–516, `README.fr.md` 553–555 (feature list, entries added by 45b8282):
   "the search stops once its hold-out error has not improved by 1 % in 30 generations" /
   "son erreur sur les lignes mises de côté".** The same commit added the training-rows
   fallback to every other statement of the rule (first review, finding 17); these two
   entries, written in that commit, omit it, and for the lab tables the stop is made for
   (10 or 20 rows) there is no hold-out at all (finding 2). Kind: **wording** (introduced by
   the correction).

4. **`CHANGELOG.md` 57–61 (Fixed): "fell to a blind search with no bound in time, 430 to
   735 s with `time_limit=30` (`benchmarks/results_1.2/d0/D0.md`)".** `D0.md` gives 443.5 s
   (a fit of 444.6 s) on its machine and 600 to 735 s on the first machine of the
   prototypes; it does not give 430 s. 430 s is in `fix/compare_mechanics.txt`, a fit of the
   1.1.0 wheel run with 20 generations and **no** time limit (`fix/mechanics_fix.py` lines
   49–54, test `u41` of `mechanics_fix.jsonl`), so neither the record nor the condition is
   the one cited. The measurement of the release, side by side on one machine, gives 334 to
   421 s (M2; 342 to 387 s without noise), as the release README itself says ("the figures
   that compare are those of this campaign"). Kind: **unsupported figure** (wrong record and
   wrong condition).

5. **`CHANGELOG.md` 35–40 and `release/README.md` 105–107: "40 fits return another model: 28
   reached the budget in both versions … and the other 12 are III.19.51 under units".** 38 of
   the 40 reached the budget in both versions: the 28, and the ten noisy fits of III.19.51
   (`m2_check.out`: "other: both at budget 38"; `details_x1.txt`: 22 + 16). The split is by
   cause, but it is written as a count; in the CHANGELOG nothing then says that the ten also
   reached it, so the reader takes 12 fits not at the budget. The release README's next
   sentences say so ("reached the budget in both versions, but 1.1.0 spent it in its typed
   start"); the CHANGELOG's parenthesis does not. Kind: **wording** (introduced by the
   correction of the first review's finding 3).

6. **`benchmarks/results_1.2/release/M5_review1.md` 18: "the criterion holds either way:
   0.802 is 0.0074 below".** 0.809459 − 0.802117 = 0.00734, that is 0.0073
   (`misc_check.out`). 0.0074 is 0.8095 − 0.8021, the double rounding the row corrects.
   Kind: **wrong figure** (rounding).

7. **`release/README.md` 183–184: "The printed formula, where X1 writes a power of a number
   as an exponential. The models … are those of 1.1:"**, followed by examples several of which
   hold no power of a number and only get their scale: the battery,
   `exp(0.51573 * courant)` → `exp(courant / 1.939)`; two of the four small-data fits,
   `0.3 + 2.5 * exp(-0.7 * X0)` → `0.3 + 2.5 * exp(-X0 / 1.42857)` and
   `0.3 + 2.5 / exp(0.7 * X0)` → `0.3 + 2.5 / exp(X0 / 1.42857)`
   (`m3/small_data_release.jsonl`); Nikuradse seed 1, `exp(-0.00197239 * r_k)` →
   `exp(-r_k / 507)`. The sentence merges X1's two rewritings, as the paper did before the
   first review's finding 15. Kind: **wording**.

8. **`paper/paper.md` 293–295 (AI disclosure): "for version 1.2, the stop on patience, the
   exponential printed with its scale and the correction of the typed start under a time
   limit".** The first half merges X1's two rewritings, the point the first review corrected
   at lines 189–192 (its finding 15) but not here; and D0's main correction, the fast path
   widened to 12 factors, acts with or without a time limit (it is what ends III.19.51 in a
   second; the deadline is the second part). Kind: **wording**.

9. **`LIMITATIONS.md` 34–35, `LIMITATIONS.fr.md` 37–38: "What 1.2 changes is the time of a fit
   under the defaults (points 8 and 10)."** Point 10 itself gives what else 1.2 changes under
   the defaults: the models (161 exact laws against 163, the structure in 83 fits against 85,
   R² 0.802 against 0.809), and the paragraph's own first sentence says that under units it
   changes models with a budget set too. Kind: **wording** (understatement; minor).

10. **`CHANGELOG.md` 49–50: "confirmed on draws and seeds never run".** The TP draws 5 to 9
    had never been run; the F41 seeds 5 to 9 had, in earlier phases
    (`results_0.8/campaign3b_T_stopped.jsonl`, `results_0.9/retest_T1.jsonl`,
    `confirm_B1.jsonl`, `confirm_E1.jsonl`, `phase5/confirm_N1.jsonl`), and the CHANGELOG's own entries of 1.0.0 (lines 170, 182, 215) and 1.1.0
    (line 116) already call seeds 5 to 9 "five seeds never run" for their confirmations. `PLAN.md` says only
    that they were new to the choice of P ("Confirmation on new draws and seeds"). Kind:
    **wording** (minor).

11. **`release/README.md` 256–258: "The **Tests** workflow of the repository is green on every
    commit of the branch since the candidate".** No record of these runs is in the release
    folder (`m4/` holds the local test runs only; the release of 1.0 kept `M4_ci_runs.txt`).
    The plan asks for the workflow on the commit of the release, which is still to come; the
    statement about the commits so far has nothing behind it in the repository. Kind:
    **missing record** (minor).

## Summary

11 findings: 1 stale sentence (1), 1 unsupported figure (4), 1 wrong figure (6), 1 missing
record (11), and 7 of wording (2, 3, 5, 7, 8, 9, 10), two of which (2, 3) are claims about
H1 that the code contradicts for the lab tables, and three of which (3, 5, 6) were introduced
by the corrections of the first review. No translation error and no broken path. Every
figure of M2, of campaign H1, of the pages of the limits, of M1, M3 and M4, of the TP
notebook and of the case studies recomputes exactly.
