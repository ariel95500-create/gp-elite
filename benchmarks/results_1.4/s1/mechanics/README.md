# Mechanics of S1

Done on 13 November 2026, before any fit of the campaign of S1. Plan:
`../../PLAN.md`, "Mechanics of S1".

N2 was not adopted and is withdrawn (`../../n2/campaign/README.md`). So the
candidate before S1 is 1.3.0 itself, and the candidate with S1 is the wheel
of 9d2c96d: S1 on, N2 and E2 off, W1. It is installed in a fresh
environment with the packages of 1.3.0 (`/venv14s1`), and its 11
`gp_elite/` files are identical to that commit.

1. **Tables of 30 rows and more are untouched** (`run.sh`):
   - the 95 bounded fits of the mechanics of N2 (F41 and U41 at seed 0, R6
     and R7raw at fold 0; 20 generations, no time limit) return the models
     of 1.3.0 in 95 of 95 (`bounded_compare.txt`);
   - the 13 reference configurations of `speed_equivalence.py` (60 rows and
     more each) are identical, field by field, to those of 1.3.0
     (`equiv_compare.txt`).
   One fault was found and fixed before this check: S1 decided on the rows
   left after the split of the hold-out, so a table of 30 to 37 rows (a
   hold-out of 8 and 22 to 29 training rows) had S1 change the rule of its
   noise-tolerant seeds. S1 now acts only where no hold-out is kept
   (1f080dc).
2. **The cross-validation by itself.** On 12 exact points of 2.5·x0·x1, the
   law comes back to numerical precision, and two runs give the same model
   and the same front (`test_s1_cross_validation_chooses_an_exact_law_and_repeats`).
3. **The variants.** On exact points of T = 2π·√(L/g), `a + b·sqrt(L)`
   loses to its variant without the constant; on exact points of
   d = ½·g·t², a candidate with the exponent 1.96 loses to its variant with
   the exponent 2, written as a square (the two tests `test_s1_variant_*`).
4. **The list.** On a table of 10 points, `pareto` is a list whose entries
   give their formula and their cross-validated error, by increasing size
   and decreasing error (`test_s1_pareto_lists_the_cross_validated_front`).
5. **Under units,** every candidate of the cross-validation passes the gate
   of dimensions, and so does the model returned
   (`test_s1_candidates_pass_the_gate_of_dimensions`).
6. **Tests.** The suite passes against the repository at 9d2c96d: 197 tests,
   with six new ones for S1.

**Seen while writing S1, to know before its campaign.** On a pendulum table
of 10 points with 2 % noise, the candidates that the search found on the
whole table, refitted on each fold, have a cross-validated error below the
variance of the noise (0.00033 against 0.00076): their structure was chosen
on these same points, and the cross-validation refits only their constants.
The law itself, `b·sqrt(L)`, has 0.00102, and falls out of the tolerance of
the plan by 0.00012. The model chosen there has two fitted constants and
holds the law (the law plus one term whose constant is zero on the
noiseless data), so it counts as the law on the TP bench. The rule is that of
the plan; its campaign measures it.
