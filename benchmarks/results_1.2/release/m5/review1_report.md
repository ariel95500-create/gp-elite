# Release 1.2.0, M5: first independent review

Reviewer: a second agent who had not seen the work. Date: 5 November 2026.
Repository: `/home/user/gp-elite`, branch `claude/peaceful-knuth-4q7m4p`, HEAD 66ee1b9.

## Scope and method

Documents checked, as `PLAN_RELEASE_1.2.md` (M5) and the request list them:
`README.md` and `README.fr.md` (every figure, and the French line by line against the
English); the 1.2.0 entry of `CHANGELOG.md`; `LIMITATIONS.md` and `LIMITATIONS.fr.md`
(the introduction, points 8 and 10, and the figures the release touches); `paper/paper.md`
(version 1.2, the time of a fit, the printed formula, the units mode, the frozen test set,
the AI disclosure); `examples/tp_six_lois.ipynb`; `examples/case_studies/*.ipynb` (English
and French); `benchmarks/results_1.2/release/README.md` (every figure); the note at the end
of `benchmarks/results_1.1/DIAGNOSTIC_TP.md`.

Method. No summary was trusted. Read-only git (`log`, `show`, `diff`) to see what the
documents commit 971bcec changed. Small read-only scripts (`python3 -I`), which read the
JSON records only and import nothing of the engine. No fit was run. The scripts and their
outputs are in this folder:
- `m2_recompute.py` / `.out`: every M2 indicator of both versions from
  `release/m2/campaignR_1.1.0.jsonl` and `campaignR_1.2.0.jsonl` (2,780 + 2,780 records):
  pairing, statuses, structures, medians, collapses, units audit, times at the budget,
  expression differences, X1 rewrites, the `formula_exact`/`expr_11` checks, III.19.51;
- `model_diff.py` / `.out`: the 40 jobs whose formula without X1 differs from 1.1.0, with
  the generations each version ran;
- `h1_recompute.py` / `.out`: campaign H1 and its confirmation (`h1/campaign/D_*.jsonl`,
  `tp_*.jsonl`): exact laws, structures, NEAR, R6/R7raw medians and collapses, medians of
  time, the formulas A against H1 on TP;
- `limits_on_11.py`: the counting of `limits_figures.py`, re-implemented, on the records of
  the release of 1.1 (it gives back 7/66 and 8/67, 108/86, 8, 213, 34, as the pages say);
- `nikuradse_check.py` / `.out`: the five Nikuradse records of M3 1.1 against 1.2, and the
  claims of the case-study notebook (sizes, R², gaps, forms with a log of a log).
Besides: sums of the M3 records (scaling times at 1,000 and 10,000 points, TP times,
import times, units A/B times), the diffs of `m3_compare_1.1.0_vs_1.2.0.txt`, the M4
records, every path the changed text cites (all exist), and the code of H1
(`api.py` 657–667, `core.py` `_Patience` and both loops), X1 (`formula.py` 468–535 and
`raw_formula`), D0 (`dim_search._monomial_tree`, `core.py` 6883–6890) and
`sklearn_api.py` (`_resolve_generations`).

Judged by the project's method: times compared only within a campaign or a day; the
frozen test set decides nothing and is published as measured; a changed figure is published
as measured with its reason.

## Claims checked

About 280 claims (figures, formulas, paths, statements about behaviour) were checked; about
170 of them were recomputed from the records rather than read from a summary (all M2
indicators and counts, the III.19.51 table, the times at the budget, the H1 figures of point
10 and of the CHANGELOG, the TP times and constants, the scaling sums, the Nikuradse
figures, the X1 examples' arithmetic). The rest were checked against a record by reading
it (M1, M4, driver logs, x1/fix/d0 records, case-study records that M3 marks "same").

## Parts with nothing wrong

- **M2 figures** everywhere they appear (release README table and text, CHANGELOG, READMEs,
  LIMITATIONS introduction, paper): 163/163, 108/85, 0.8095, 10/10, 166/166, 113/98,
  1,005 of 1,005, medians 30.2/30.19, longest 420.73/31.55, TF78 214, TS14 10, TR25 0.7692,
  utf 229, collapses 5/5/38/28/28, 316 jobs with another expression (276 X1 alone: 257 + 19;
  40 another model: 22 + 18), 287 rewrites (267 + 20), `formula_exact` never changed,
  316 + 471 = 787 fits with neither at budget and no difference, 1,993 and 1,987 at the
  budget, median 30.5 s and at most 31.94 s for 1.2.0's, III.19.51 times (0.99–1.16,
  30.12–30.46, 30.05–30.40; 1.1.0 334–421), "eleven to fourteen times", 31.6/31.5 without
  III.19.51, 17 removed jobs (13 + 16 crashes), 806 and 2,229 pairs at the restarts. All
  recomputed and correct. The limits figures (`limits_figures.txt`) recompute exactly.
- **M1, M4**: correct as stated (13 identical; 21.7 s and 21.1 s; 169 passed under 3.9.25,
  3.11.18, 3.14.6; twine PASSED; engine unchanged since c3ea7fc).
- **M3 times and X1 examples**: 38.0 s and 103.1 s (against 58.4 and 153.4); import 0.073
  against 0.117; one generation 0.6 against 1.0 s; time_limit_check 13/16 against 15/16,
  6.3 s and 12.5 s; the pair runs 13/14 and 13/13; TP 8/10/8/8/8/7 = 49 s, pair 48/48
  against 198/194; battery `exp(courant / 1.939)` (1/0.51573 = 1.93900); robustness
  6.98808; small data 1.42857; I.6.20a `exp(-0.5 * v0²)`; README example τ = 0.981975.
- **The French READMEs and pages of the limits** say what the English say in every passage
  1.2 changed (the time-limit and patience bullets, X1, the units aside, battery, frozen set,
  "Nouveautés", the 1.2 paragraph and points 8 and 10): no translation error found. The
  findings below on the English text apply to the French one at the lines given.
- **Case studies.** Kepler and Hubble (EN/FR): M3 1.2 records are identical to 1.1's; every
  figure still holds. Nikuradse (EN/FR): every figure of the text still holds on the 1.2
  records (front of six nodes `1.10108 - 0.133625 * log(r_k)` R² 0.9357 at all seeds; the
  forms at seven to nine nodes; champion 48 to 70 nodes, R² 0.980 to 0.995; 10 to 13 forms,
  gaps −1.20 to +0.88, best 0.014 to 0.225, two forms of seed 0 at 52 and 59 nodes; log of a
  log at 30/41 (seed 1) and 70 (seed 4), and 12/14/69 (seed 1), 37/39 (seed 3) with gaps
  0.20 to 1.20). None of the formulas the text quotes is one that X1 rewrites. The text
  claims identity only for versions up to 1.1.0, which is true; if it is extended to 1.2.0,
  the printed long forms of seeds 0, 1, 3 and 4 differ by X1 (not their figures). The
  English and French notebooks carry the same figures.
- **Code against the documents.** H1 acts only when the call passes neither `generations`
  nor `time_limit` (api.py 657–664), 1 % and 30 generations, polishing and selection
  after the stop, integer k whatever the budget, 0 off; `GPEliteRegressor` always passes
  its generations (sklearn_api.py 120); X1 is tried only when the formula passes and kept
  only if it passes again (formula.py 920–925); D0 accepts up to 12 factors, each exponent
  at most 4, and an island stops drawing at the deadline once it has a tree. The documents
  describe these correctly, apart from findings 3, 4 and 17.
- **Paths and links**: every path in the changed text exists in the repository.
- **Dates**: the paper's `date: 2 November 2026` and CITATION's `date-released:
  2026-11-02` are those of 1.1.0; the commits say the dates and the name are left to
  gate 8, so this is not counted as a finding, only recalled.

## Findings

Kinds: wrong figure, unsupported figure, stale sentence, translation, wording, missing
record, broken path. Ordered by weight.

1. **`LIMITATIONS.md` 149–150, `LIMITATIONS.fr.md` 163–164: collapses attributed to the
   wrong datasets.** The text: "on the six standardised real datasets, a median test R² of
   0.802 against 0.810, and 9 collapses out of the training range against 11". The record
   (`h1/campaign/D_A.jsonl`, `D_H1.jsonl`; `compare_h1.txt`, criterion 5 "collapses out of
   domain (R² < 0, R6 and R7raw) 9 against 11"): 9 and 11 are R6 and R7raw together, 65
   out-of-domain fits; on the six standardised datasets alone they are 3 against 4 (R7raw
   6 against 7). Recomputed in `h1_recompute.out`. Kind: **wrong figure** (wrong
   attribution).

2. **`LIMITATIONS.md` 150, `LIMITATIONS.fr.md` 163, `CHANGELOG.md` 64: "0.810".** The
   median test R² of the R6 folds of 1.1.0 in campaign H1 is 0.809459…
   (`D_A.jsonl`, 30 folds), which is 0.809 at three decimals; 0.810 comes from rounding
   the 0.8095 of `compare_h1.txt` a second time. (`PLAN.md` 272 has the same 0.810.)
   Kind: **wrong figure** (double rounding).

3. **`benchmarks/results_1.2/release/README.md` 105–108 (and `CHANGELOG.md` 33–34): the
   cause given for 10 of the 38 "other models" is wrong.** The text: "38 of them reached the
   time budget in both versions: a fit stopped at its budget returns the best model found by
   then, and that depends on the load of the machine. The other two are III.19.51 under
   units". The records (`model_diff.out`): 10 of the 38 are III.19.51 under units with noise
   (U41N1 and U41N10, all five seeds), where 1.1.0 ran **1 generation** (its typed start took
   334–421 s) and 1.2.0 ran **35 to 40**; their models differ because of D0, not the load of
   the machine (`PLAN_RELEASE_1.2.md` itself expected D0 to change "those that reach their
   deadline during it"). So 12 of the 40 other models are III.19.51 under units, not 2. The
   CHANGELOG's "38 reached the budget in both versions, and the other two are III.19.51
   under units" is true word for word but leads the reader to the same wrong split.
   `m2/details_x1.txt` ("16 with both versions at the budget") is the source of the
   classification. Kind: **wording / wrong attribution of a record**.

4. **`LIMITATIONS.md` 21, `LIMITATIONS.fr.md` 23, `CHANGELOG.md` 9: "Version 1.2 leaves the
   models alone when the call sets its budget" / "With a budget set, nothing changes".**
   D0 acts with a budget set: in M2, at `time_limit=30`, 12 of the 15 fits of III.19.51 under
   units return another model (seeds 0 and 3 of U41, and the ten noisy fits, finding 3), and
   the code of D0 (`dim_search._monomial_tree` max_terms 12; `core.py` 6883–6890) changes
   any product of 9 to 12 factors and any start that reaches its deadline, whatever the
   budget. Also, an explicit `patience=k` stops a search that set its budget (api.py
   659–664). The READMEs' "the models of 1.1 at equal work" is accurate; these two sentences
   are not. Kind: **stale sentence / claim the code contradicts** (D0).

5. **`README.md` 143–146, `README.fr.md` 150–153 (and `README.md` 140, `README.fr.md`
   147): `speed="thorough"` "(population 400, four islands, 200 generations)… with twice
   the default number of generations".** In 1.2 the stop is decided on the call's own
   `generations` argument before the preset fills it in (api.py 657–667): a call with
   `speed="thorough"` and no `generations`/`time_limit` gets `patience` 30, so it runs 200
   generations only while it keeps gaining 1 % in 30. The bullet, and "`restarts=` and
   `speed="thorough"` spend more compute on the exact form", say nothing of it, and the
   `patience=` bullet's "A call that sets its budget gets all of it" does not cover a preset
   that names generations. Kind: **stale sentence**.

6. **`paper/paper.md` 59–61: "so a fit of a ten-point laboratory table takes seconds
   instead of about half a minute, with the same formulas".** The records support "the same
   formulas" for the six fits of the TP notebook (M3 pair) and, nearly, for the six laws
   within reach under units (119 of 120 and 120 of 120 in campaign H1); on the 200
   ten-point fits of the TP diagnostic (draws 0–4) the stop returns another formula in 25
   and changes whether the law is found in 7 (`h1_recompute.py`; `compare_h1.txt` lists 11
   fits with the law gained or lost over 400). Stated as a general property of a ten-point
   table, it is not what the campaign measured. Kind: **unsupported claim (wording)**.

7. **`benchmarks/results_1.2/release/README.md` 235–237: stale sentence.** "Its text
   quotes the run of 1.1.0 on another day (42 to 55 s a fit): those times compare with
   neither column." Since 971bcec the notebook's text quotes the M3 run of 1.2.0 (7 to 10
   s, cells 0, 7, 10, 13, 16, 19, 22). True when M3 was written, no longer of the
   documents of the release. Kind: **stale sentence**.

8. **`benchmarks/results_1.2/release/README.md` 181: "formulas of size 13 to 69".** In
   `m3/case_nikuradse/`, the entries whose printed formula X1 changes have sizes 13 to
   **72**: seed 3's held-out front entry of size 72 changes (`exp(0.00197239 * r_k)` →
   `exp(r_k / 507)`), as do sizes 13–69 elsewhere (`nikuradse_check.py`). Kind: **wrong
   figure**.

9. **`CHANGELOG.md` 57–59: "Run with 20 generations and no time limit, seed 0, the other
   40 equations of the bench with their units and the 40 units fits of the TP diagnostic
   return the models of 1.1.0".** The TP fits of that mechanic ran under the API defaults
   (100 generations), not with 20 (`fix/mechanics_fix.py` lines 6–7, 53 and 58–67;
   `PLAN.md` 551–553). Only the U41 fits ran with 20. Kind: **wording**.

10. **`benchmarks/results_1.1/DIAGNOSTIC_TP.md` 210–212 and `examples/tp_six_lois.ipynb`
    (cell 24, JSON lines 319–322): the X1 example.** "the capacitor discharge comes back as
    `4.96444 * exp(-t / 1.01302)` rather than as a power of a number" / "par exemple
    `4.96444 * exp(-t / 1.01302)` … et non plus comme une puissance d'un nombre
    (0,0078^(0,2·t))". That fit (rc, 10 points, 2 %, draw 0) was already printed as an
    exponential without X1: `-0.00664979 + 4.96444 * exp(-0.987144 * t)` in 1.1.0
    (`h1/campaign/tp_A.jsonl`) and in `x1/x1_tp_check.txt`; X1 only gave it its scale. The
    fit whose 1.1 formula is the power the diagnostic quotes, `4.86249 *
    0.00784758^(0.2 * t)` (20 points, 2 %, draw 1), comes back as `4.86249 * exp(-t /
    1.03145)`. Both texts also drop the constant term. Kind: **wording** (example does not
    show what the sentence says).

11. **`examples/tp_six_lois.ipynb`, cell 24 (JSON lines 328–330): "La version 1.2 a réglé
    deux points de cette liste : la durée d'une recherche … et l'écriture de
    l'exponentielle."** The same commit removed the bullet "La durée" from the list, and the
    exponential is a sentence inside the first bullet, not a point of the list; the list as
    it stands has three points (constants with units, Snell, several formulas), none of
    which 1.2 settled. Kind: **wording**.

12. **`README.md` 302, `README.fr.md` 325: "median seconds / run | 1 | 1 | 1".** The M3 of
    1.2.0 measured medians of 0.4, 0.7 and 0.4 s, printed 0, 1, 0 (`m3/units_ab_ood.jsonl`,
    `units_ab_ood.txt`); 1/1/1 is the M3 of 1.1.0 (0.7, 1.0, 0.6). The table names no
    version, the release record notes the change ("round to 0 or 1"), but the page was not
    brought to the measurement. Kind: **unsupported figure** (not the release's record).

13. **`release/README.md` 173: "the table of `units=` on II.11.3" among the 40 records that
    are the same.** `units_ab_ood.jsonl` is the same; `units_ab_ood.txt`, which holds the
    table, is listed "differs" (its seconds row, finding 12). Kind: **wording**.

14. **`README.md` 553, `README.fr.md` 590, `CHANGELOG.md` 14: "Feynman III.19.51 [under
    units] ends in about a second, where 1.1.0 took about six minutes".** True of the five
    fits without noise; with noise (10 of the 15 fits) 1.2.0 runs its 30 s budget (30.05–30.46
    s), against 334–421 s. And `CHANGELOG.md` 35–37, "comes back exact in 0.99 to 1.16 s at
    five seeds …; with noise, in 30.1 to 30.5 s", reads as exact with noise; those fits are
    NEAR with the structure retrieved. Kind: **wording**.

15. **`paper/paper.md` 189–191: "since version 1.2 a power of a number is printed as an
    exponential with its scale, $\exp(-t/\tau)$".** The code does two things: a power of a
    number becomes an exponential (with no scale unless its argument is a number times one
    variable, e.g. I.6.20a `exp(-0.5 * v0²)`), and an exponential of one variable, power or
    not before, gets its scale (`exp(-0.987144 * t)` → `exp(-t / 1.01302)`). The READMEs
    and the CHANGELOG say it correctly. Kind: **wording**.

16. **`README.md` 208–209, `README.fr.md` 225–226: the X1 example
    `5.05644 * 0.00614708^(0.2 * t)` → `5.05644 * exp(-t / 0.981975)`.** The record is
    `0.00538504 + 5.05644 * 0.00614708^(0.2 * t)` (`x1/x1_tp_check.txt`, rc 20 points 5 %
    draw 0); the quoted formula is a fragment that no fit "comes back as". The arithmetic is
    right. Kind: **wording** (minor).

17. **`README.md` 155, `README.fr.md` 163, `LIMITATIONS.md` 142, `LIMITATIONS.fr.md` 155,
    `CHANGELOG.md` 8, `DIAGNOSTIC_TP.md` 206–207: "its error on the hold-out rows".** The
    stop reads the hold-out MSE when there is a hold-out and the training MSE otherwise
    (`core._holdout_mse`, `_Patience` docstring); with `validation_split=0` the stop still
    acts, on the training error. Kind: **wording** (minor precision).

18. **`LIMITATIONS.md` 18–19, `LIMITATIONS.fr.md` 20–21: "Point 8 is measured on the package
    of 1.1.0, side by side with 1.0.0".** Point 8's first bullet now gives the TP times of
    1.2.0 against 1.1.0 (M3 of 1.2). The new 1.2 paragraph says "points 8 and 10", so the
    reader can work it out, but the 1.1 sentence is no longer exact. Kind: **stale
    sentence** (minor).

19. **`README.md` 512–540 (the feature list) and `README.fr.md` (same list, "Budget de
    temps" at 564):** no entry for
    1.2 (the stop on patience, the exponential written as such, the typed start bounded by
    `time_limit=`), while every earlier version has its entries; and "**Time budget** (v0.7):
    `time_limit=` stops cleanly" was not true under units for III.19.51 until 1.2. Kind:
    **wording / omission** (minor).

## Summary

19 findings: 3 wrong figures (1, 2, 8), 1 unsupported figure (12), 4 stale sentences
(4, 5, 7, 18), and 11 of wording (3, 6, 9, 10, 11, 13, 14, 15, 16, 17, 19), finding 3
being a wrong attribution of the cause of 10 records. No translation error, no broken path,
no missing record. Every M2 figure and every criterion of the plan recompute exactly.
