# Release 1.3.0, M5: first independent review

9 November 2026. Reviewed: branch `claude/peaceful-knuth-4q7m4p` at
**e598e4d**. During the review the author's agent committed 80e804c, which
adds only three files of this review; every document reviewed is that of
e598e4d.

## Scope and method

Documents, as `PLAN_RELEASE_1.3.md` (M5) and the request list them:
- `README.md` and `README.fr.md`: every figure the release touches, and the six
  hunks changed since 5492296, French against English line by line;
- the 1.3.0 entry of `CHANGELOG.md`;
- `LIMITATIONS.md` and `LIMITATIONS.fr.md`: the introduction, points 1, 5 and 6,
  and every change since 5492296, French against English;
- `paper/paper.md`: every change since 5492296;
- `examples/tp_regression_symbolique.ipynb`, `examples/tp_six_lois.ipynb`, and the
  case studies as far as the release figures touch them;
- `benchmarks/results_1.3/release/README.md`, `m2/examine/README.md`,
  `m3/examine/README.md` (and their `PLAN.md`);
- the note for version 1.3 at the end of `benchmarks/results_1.1/DIAGNOSTIC_TP.md`;
- `benchmarks/release_claims/compare_m2_1.3.py` against the criteria of the plan.

Method. Nothing was taken from a summary. The figures were recomputed from the
records with read-only scripts, run with `python3 -I` or `/venv12b/bin/python -I`,
without importing the engine (a stub stands in for `gp_elite` while
`feynman_bench.py` defines `PROBS`) and without any fit. Git was used read-only. The
scripts and their outputs are in `m5/review1/`:

| script | what it recomputes |
|---|---|
| `common.py` | loading of the M2 records; the pool of each job from `PROBS` (field 5) and the manifest |
| `r1_m2_indicators.py` | every indicator of the M2 table, formula_exact by suite and pool |
| `r2_m2_pairs.py` | the pool `physical` at equal work, every status and structure change of the pool `trig`, the arcsine laws, the frozen test set |
| `r3_m2_times.py` | the times of the fits stopped by their budget; the equations never exact |
| `r4_m3_examine.py` | the examination of the TP notebook of the pool `full` (E2) |
| `r5_i1812.py` | I.18.12 in M2 and its examination (E1); sin θ against the parabola |
| `r6_arcsin_seeds.py` | the fits where an arcsine seed was placed, exact or noise-tolerant |
| `r7_frozen_inverse_trig.py` | the inverse trigonometric laws of the frozen set; the trig equations |
| `r8_campaigns_a.py` | campaigns A1, A2, A3 and the confirmation of A3; Snell's law on clean data |
| `r9_m3_misc.py` | scaling, time_limit_check, Kepler min-max, the six laws of the TP notebook, the deduced constant, the duration of E2, the TP notebook at seed 0 |
| `r10_git.sh` | commit times, what 5492296 changes, the engine since 492863e |
| `r11_truncation.py` | the 160-character truncation of `expr` and the counts that read the formula |

About 300 claims checked, about 190 of them recomputed from the records; the rest
checked against the code, the plan or the cited file.

## Findings

Ranked, the most consequential first. Each gives the place, the claim, what the
records or the code say, and why it matters.

**1. `examples/tp_six_lois.ipynb`, cell 24, section 10 (JSON line 323).**
Claim: "La loi de Snell-Descartes, qui demande un arc sinus, que GP_ELITE ne
propose pas." Code: since 1.3.0 the pools `trig` and `full` have `arcsin`
(`gp_elite/core.py`, `_GENCSV_POOLS`). The cell was not changed since 5492296.
Why: a stale sentence that the release makes false, in the notebook given to
students. Snell's law still does not come back on the TP, but for another
reason (the noise, `DIAGNOSTIC_TP.md`, note of 1.3).

**2. `CHANGELOG.md:5-8`.** Claim: "the pool `physical`, the default, and `poly`
and `conserve` are left as they are, so every fit run with them returns what it
returned with 1.2.0." Records: in M2, 16 of the 2,250 fits of the pool
`physical` return another formula and 2 change status (Strogatz vdp1 seed 9,
MISS to EXACT; U41 I.6.20a seed 4, MISS to NEAR), all with a budget reached by
one version or both (`r2_m2_pairs.txt`). No fit of M1, of the 147 fits of the
mechanics, or of M2 uses `poly` or `conserve` (`a3/mech_a3.jsonl`,
`speed_equivalence.py`): for them the sentence rests on the code, which I read
and which agrees. Why: the sentence is unconditional where README, LIMITATIONS
and the paper say "at equal work"; under a time budget it is false for 16 fits
of the release measurement.

**3. `CHANGELOG.md:10-13`.** Claim: the two arcsine laws "come back exact with
the arcsine in 8 and 7 fits of 10, on two sets of seeds, where 1.2.0 had none;
the other eight lose nothing." Records: on the second set (seeds 5 to 9,
`a3/campaign/Dtrig_*_conf.jsonl`), I.50.26 loses its one exact fit (seed 7,
EXACT to MISS) and III.17.37 gains one; the eight stay at 21 against 21
(`r8_campaigns_a.txt`; `compare_a3_conf.txt`). Seeds 0 to 4 and M2 hold. Why:
the sentence claims both sets; on one of them a law does lose its exact fit.
"The eight lose nothing in total" would hold.

**4. `CHANGELOG.md:38-40`.** Claim: "the operator alone (A1), which brought the
arcsine laws back in 2 fits of 10, and the operator with its constant (A2), in
3." Records: two measures are mixed. A1's 2 counts every exact fit, one of them
the tanh approximation of I.30.5 seed 0; with the arcsine, A1 has 1. A2's 3
counts only the exact fits that write the arcsine; A2 is exact in 5 (two tanh
fits of I.30.5) (`r8_campaigns_a.txt`; `a1/campaign/compare_a1.txt`,
`a2/campaign/compare_a2.txt`). Why: set beside "8 and 7 ... with the arcsine",
the reader takes all four figures as one measure. On that measure: A1 1, A2 3,
A3 8 and 7.

**5. `CHANGELOG.md:56-60`, `LIMITATIONS.md:138-143`, `LIMITATIONS.fr.md:152-157`,
`release/README.md:114-119`.** Claims: "in 82 fits of 530 ... against 27 for
1.2.0, 47 of the 82 with an arcsine", followed by the clip as the explanation
("The printed arcsine has no clip, so where the argument leaves [-1, 1] ... the
formula and `predict()` part"; LIMITATIONS: "the arcsine is one of these guards
... The search can use the clip"). Records:
- `expr` is the formula cut at 160 characters (`phase1_bench.py:248`). 77 of the
  82 recorded formulas are cut, and all 35 counted "without an arcsine" are cut
  (`r11_truncation.txt`). So 47 is a lower bound: the records say between 47
  and 82;
- whether the clip acts in any of the 47 is not recorded. The plan said so for
  A2 (`PLAN.md`, campaign A2), and `m3/examine/README.md` says so for its six;
  the CHANGELOG and LIMITATIONS drop that caveat;
- "in the pools with the arcsine": the 530 fits are all of the pool `trig`; no
  fit of M2 uses `full`.

Why: a figure stated as a count is a lower bound, and a cause is stated where
the records show a co-occurrence.

**6. `examples/tp_regression_symbolique.ipynb`, cell 5 (Question 1, JSON lines
77-79).** Claim (premise): "comment expliquez-vous qu'elle ajuste tout de même
correctement les données ?" Records: with 1.3.0 at seed 0, part 1 returns a
formula with an arcsine that departs from `predict()` on 15 of 200 rows,
largest gap inf, and a `RuntimeWarning` is printed. The fits of part 2 at 30 and
60 generations warn too (184 and 15 of 200 rows) (`m3/notebook_snippet_tp.txt`;
`r9_m3_misc.txt`). With 1.2.0 none warned. Only question 2 was adapted. Why:
students now see a warning the notebook never mentions, and the printed
expression does not fit the data on those rows, against the premise of the
question.

**7. `benchmarks/results_1.1/DIAGNOSTIC_TP.md:235-237`.** Claim: "On clean data,
under the defaults, the law came back in none of 10 fits with each of the first
two versions of the arcsine, A1 and A2". Records: by the TP's test, the law
comes back in 1 of 10 with A1 (`a1/examine/e2a_B.jsonl`: 20 points, draw 1,
`err_law` 2.4e-10, a formula without the arcsine). `a1/examine/README.md`
writes it "1, with no arcsine (2.4e-10)". A2: 0 of 10, as written
(`r8_campaigns_a.txt`). Why: the first bullet of the same note counts "by its
test"; by that test this bullet is wrong for A1. "None with the arcsine" would
hold.

**8. `CHANGELOG.md:9-10` and `:46-47`.** Claims: "the seeds that hold a function
of a monomial exactly gain the arcsine of a monomial"; Added: the seed "found
when it holds to numerical precision". Records and code: the noise-tolerant seeds
(phase 5) offer it too (`PLAN.md`, A3: "The seeds that tolerate noise ... offer
it too"). In M2 the noise-tolerant arcsine seed was placed in 25 fits of 1.3.0:
I.30.5 in F41N1, F41N10, U41N1 and U41N10, and TF78 feynman_test_1 at five seeds;
the exact seed in 10 (`r6_arcsin_seeds.txt`). Why: the entry omits a change
that reaches noisy data, and it goes with the gain of I.30.5 under 1 % noise
(5 fits each of F41N1 and U41N1).

**9. `LIMITATIONS.md:77-79`, `LIMITATIONS.fr.md:83-86`.** Claim: "Two things the
arcsine does not reach: an arcsine whose argument is not a monomial, such as
the n·sin θ of I.26.2. The search must build it, and at 30 s it did so in 3
fits of 5". Records: I.26.2 is exact with the arcsine in 3 of 5 (M2), so the
arcsine does reach it. The subject is the seed ("The seed reaches an arcsine of
a monomial only", CHANGELOG), or, as the plan wrote, "an arcsine whose argument
is neither a monomial nor found by the search". Why: the sentence contradicts
itself, in both languages.

**10. `CHANGELOG.md:53-55`.** Claim: "Snell's law on a few noisy points ... the
curves returned differ from the law by less than the noise
(`benchmarks/results_1.3/a1/examine/`)". Records: the comparison with the noise
was measured on the 40 fits of A1 only (`a1/examine/e2b.txt`), not on A3 or
1.3.0. LIMITATIONS says "measured on a first version of the arcsine"; the
CHANGELOG does not. Why: in the entry of 1.3.0 the figure reads as one of 1.3.0.
That the law does not come back with 1.3.0 holds (0 of 40 on two sets of draws,
`a3/campaign/TPsnell_B*.jsonl`).

**11. `release/m2/examine/README.md:14-16` (and lines 5 and 21-23).** Claim:
"1.2.0 returns, in the 8 other fits, a parabola in θ times r·F". Records: 7 of 8.
Seed 11 returns `-1.06594 * v0 * v2 * v1 * tanh(log(v2) - 1.14229)`
(`e1_1.2.0.jsonl`; `r5_i1812.txt`). Beside it, two trivial points:
- "median generations are 97 with both ... and 110 with both": the medians of 20
  are 96.5 and 97, 110 and 109.5 (`examine.py` takes the upper middle value);
- "the same lscpu ... but for the clock rates": the two files are identical.

Why: wrong count; the reading of E1 (12 against 12) is unaffected.

**12. `compare_m2_1.3.py:67-76`, `release/README.md:79-82`, `CHANGELOG.md:27-29`.**
Claim: on the 706 fits of the pool `physical` where neither version reached its
budget, "the formula ... to the bit". Code: the formula compared is `expr`, cut
at 160 characters by the bench. 5 of the 706 are at that length (TF78
feynman_III_4_33 s8, TS14 strogatz_bacres2 ood s6, TF78 under units
feynman_II_11_28 s7 and s8, feynman_I_13_4 s7) (`r11_truncation.txt`). For them,
only a prefix of the formula is compared. Every other recorded field is
bit-identical, `err`, size, r2 and `err_ood` among them (`r2_m2_pairs.txt`), so
the conclusion is very likely right. "The same formula in 2,234 of 2,250" is
counted on the cut text too. Why: the plan's criterion says "the formula ...
differs by a bit"; the script checks the first 160 characters.

**13. `compare_m2_1.3.py` against the plan, item "Reported".** The plan asks for
"the formulas with the arcsine". The script prints a count by suite and the ten
formulas of the arcsine laws of F41. No file of `m2/` lists the other formulas
with the arcsine: 16 of TF78 under units, 8 of TS14, 17 of U41N1, 12 each of
F41N1 and F41N10, all at least, given finding 5. The count "arcsine in B" is a
lower bound for the same reason. A note, not an error: the plan's "R6 and R7raw
have more than 2 more collapses" is computed on their sum, as in 1.2; both
readings pass, 5 to 5 each. The other ten criteria are computed as written
(see below).

**14. `release/README.md:148-158` and `:159`.** Claim: "57 records are the same
... Among them: ... the deduced constant with 1.2.0, and with 1.3.0
(`m3/deduced_constant_venv13rx.txt`)". Record: `m3_compare_1.2.0_vs_1.3.0.txt`
lists that file as "new", not among the 57. It differs from the 1.2.0 record
only in its first line, the version, as the README says (`r9_m3_misc.txt`).
Also: "What differs has three causes". The nine differing records are the pool
`full` (2), timing (5), and `m3_driver.sh`/`m3_driver.log`, the driver itself
(2), which the text does not name. The third heading ("The TP notebook of the
six laws") is about new records, not differing ones. Why: misattributed record;
an unnamed cause.

**15. `release/README.md:82-85`.** Claim: "Two fits change status, both at the
budget: Strogatz vdp1, seed 9 ... where 1.2.0 reached its budget and 1.3.0 did
not". Records: in vdp1 seed 9, 1.3.0 ends at 30.38 s with `time_limit_reached`
False. Why: "both at the budget" reads as both versions, and the same bullet
says otherwise. "Each with a budget reached by one version or both" would hold.

**16. `README.md:335-337`, `README.fr.md:365-367`.** Claim: "165 exact laws of
205 against 108 with 1.0, and 163 without units (with the arcsine of 1.3, 174
and 171)". Records: 165 is 1.1.0 in its own release. 1.2.0, measured beside
1.3.0, gives 166 and 163 (M2). Why: read against 165, the gain under units
looks like +9; the paired gain is +8. "(1.3.0: 174 and 171, against 166 and
163 for 1.2.0 measured beside it)" would hold.

**17. `README.md:466-475`, `README.fr.md:503-512`, `paper/paper.md:241-246`.**
One sentence gives 1.2.0 on the frozen set as 214 of 390 and 10 of 70 (release
of 1.2); the next gives it as 213 and 8 (release of 1.3). Nothing says these
are two campaigns of the same version under a time budget. The sentence on 1.1
in the same paragraph does say so, and LIMITATIONS does too. Why: the two
figures read as inconsistent.

**18. `CHANGELOG.md:50-52`.** Claim: I.26.2 "must be built by the search, which
returns it in 3 fits of 5 at 30 s." Records: 3 of 5 at seeds 0 to 4 (M2, A3); 2
of 5 at seeds 5 to 9 (`compare_a3_conf.txt`; `r8_campaigns_a.txt`). Why: the
same entry cites two sets of seeds for the arcsine laws; this limit quotes the
better one, unlabelled. LIMITATIONS labels it "in the release measurement".

**19. `CHANGELOG.md:62-64`, `release/README.md:162-165`.** The record has four
configurations: 10 and 40 generations, N1 off and on (2/0, 0/0, 4/3, 2/1 for
1.3.0/1.2.0, `m3/kepler_minmax_check.txt`).
- CHANGELOG: "at 40 generations, 1.3.0 is exact in 2 fits of 10 against 1"
  holds for N1 on only; with N1 off, 4 against 3.
- README: "at 10 generations" is N1 off; N1 on at 10 generations (0 and 0) is
  left out.

Why: ambiguous. LIMITATIONS point 5 states it correctly.

**20. `CHANGELOG.md:26`.** The path `m2/examine/` does not resolve from the
CHANGELOG (repository root). It means
`benchmarks/results_1.3/release/m2/examine/`.

**21. `release/README.md:241-243`.** Claim: "The **Tests** workflow ... is green
on every commit of the branch since the candidate (`m4/ci_runs.txt`)". Record:
Tests did not run on the three document-only commits (ea4cec7, 5e5f13e,
73fb518). 131b6d5 is covered by the run of a0935be. The file explains this; the
sentence does not. e598e4d is not in the file; it is green on GitHub (Tests run
42657329654). Why: a small overstatement.

**22. `release/README.md:173-174`, `m3/examine/PLAN.md` ("Both scripts are
committed before the first fit").** Records: the E2 records and `e2.log` carry
no time. The plan and scripts were committed at 16:21:31. The 30 pairs hold
252.7 s of fit time and the last record was written at 16:25:52 (file time), so
the first fit started at about 16:21:25 to 16:21:40, with a few seconds of
process start-up. The records cannot show the order. E1's records carry dates
(first at 14:47:51, after its plan at 14:47:08), which do show it. Why: the
pre-registration of E2 is asserted, not shown.

## Checked and found to hold

- **M2, the release README table:** all 15 rows recomputed (163/171,
  108/116, 85/87, 0.8095, 10/10, 166/174, 113/121, 98/95, 1,005, 30.2, 31.5/31.6,
  213/214, 8/8, 0.7692, 229/228). The 2,780 jobs in each file are the same, with
  none twice, no crash, `PYTHONHASHSEED=0`, the engines `/venv12p` and `/venv13r`,
  dates 04:35 to 13:43. Pools: 2,250 `physical` and 530 `trig`; none uses `full`.
- **M2, the criteria and changes:** the eleven criteria, recomputed
  independently. The pool `physical`: 706 fits without a budget reached, none
  differing in any recorded field; 2,234 of 2,250 with the same text; the two
  status changes.
- **M2, the pool `trig`:**
  - F41 and U41 gain eight exact fits each and lose none;
  - F41N1 and U41N1 gain I.26.2 (3) and I.30.5 (5); F41N10 gains III.15.12 and
    I.26.2 (1 each);
  - U41N10 loses 4 on I.18.12 and 1 on II.6.15b and gains 2 on III.15.12;
  - formula_exact False: 102/102 in `physical` and 82/27 in `trig`;
  - the arcsine laws: I.30.5 at five seeds, I.26.2 at seeds 1, 2 and 4 (F41) and
    2, 3 and 4 (U41).
- **M2, the frozen set:**
  - TF78: 15 and 16 exact on its 17 `trig` equations; feynman_test_10 is its
    only inverse trigonometric law, near once with 1.2.0 and never with 1.3.0;
  - TS14: 8 of 60 change status, glider1 seed 9 is lost, 30 and 27 collapses
    out of domain;
  - feynman_III_8_54 goes 2 to 0 under units and 0 to 1 without;
  - the LIMITATIONS figures (33/34, 204/203, 10/10, 65 = 37 + 28, 11/130,
    65/64, 5 and 7, 4 and 6 equations never exact).
- **Times:** 1,983 fits at budget, median 30.5 s, at most 31.7 s.
  `README.md` and `README.fr.md`: 41 s and 113 s with the same 85 models, I.16.6
  exact in 5 of 13 runs below 1,000 points, 6.3 s and 13.2 s, 14 of 16 against
  13 of 16.
- **M1:** eleven identical; E_minmax and L_standard identical to A3; 22.0 s
  and 22.4 s. 5492296 changes only the version, the CHANGELOG and
  CITATION.cff; its `gp_elite/` is that of 492863e, and e598e4d leaves
  `gp_elite/` and `tests/` unchanged. `arcsin` is in `trig` and `full` only,
  and the A2 rule and the A3 seeds act only where the pool has it.
- **E1 (I.18.12):**
  - 12 and 12 of 20 under units, 20 and 20 without, every fit at its budget,
    no arcsine;
  - the reading against the threshold of 4;
  - sin θ against the parabola: at most 0.045, RMS 0.026, 3.7 %.
- **E2 (TP notebook, pool `full`):**
  - 6, 8 and 7 seeds with the higher MSE, p 0.754, 0.109 and 0.344;
  - medians of MSE and size;
  - formulas departing: 1, 4 and 2 against 1, 1 and 1, and 6 of the 7 with an
    arcsine (E2 records keep the whole formula);
  - arguments reaching 1.11 and ±1.49;
  - seed 0: MSE 5.654e-02, 1.628e-02 and 1.281e-03, sizes 38, 46 and 43, which
    the new text of question 2 matches.
- **M3, the comparison:** 57 same, 9 differ, 5 new. The six laws of the TP
  notebook: all 14 time cells of the table, and the same six formulas in the
  four runs. `tp_six_lois.py` is byte-identical to that of 1.2. The console
  result is 250 kg/s². The case studies are unchanged (all use `physical`).
- **M4:** 182 passed under 3.9.25, 3.11.18 and 3.14.6, 13 of them in
  `tests/test_arcsin.py`. twine PASSED, and the SHA-256 match
  `environments.txt`.
- **SRBench:** the correction agrees with `results_1.1/srbench_settings/PLAN.md`
  (the grid is read as one configuration, the default `est` is `physical`).
- **DIAGNOSTIC_TP, note of 1.3:** 0 of 40 on two sets of draws; 18 and 19, then
  20 and 20, within 1 %; a median of 0.205 of the noise and at most 0.988; 20 to
  59 generations; 2.4e-10 to 8.4e-6. (Finding 7 aside.)
- **README EN/FR:** the six hunks agree line by line, and every figure in them
  holds (finding 16 aside). What's new: 8 of 10 with and without units, 171/163,
  174/166.
- **LIMITATIONS EN/FR:** the introduction and points 1, 5 and 6 agree line by
  line; their 1.3 figures hold (findings 5 and 9 aside). Point 5: 2 of 10
  instead of 4.
- **Paper:** 174/166 and 1,005; 214/213, 8 and 228/229; 6/15 for versions
  1.0.0 to 1.3.0 (the duel record of M3 is unchanged).
- **Pre-registration and paths:**
  - `compare_m2_1.3.py` was committed at 04:36:51, before the first checkpoint
    of records (06:36); the plan of E1 was committed before its first record;
  - every other relative path in the reviewed passages resolves (finding 20
    aside).
- **`compare_m2_1.3.py`:** the pools are taken as the bench takes them
  (`decision_bench.feyn_data` uses `PROBS[i][5]`; `tf_data` and `ts_data` use
  the manifest; real data are `physical`). The ten criteria other than the
  formula identity (finding 12) are computed as the plan writes them:
  - F41 and U41 at minus 3;
  - the structures at minus 3;
  - the R6 median at minus 0.005;
  - the collapses at plus 2;
  - the arcsine laws exact with the arcsine at 5 or more;
  - every model under units passing `check_dimensions`, `utf` included.
