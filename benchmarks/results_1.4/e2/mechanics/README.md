# Mechanics of E2

Done on 13 November 2026, before any fit of the campaign of E2. Plan:
`../../PLAN.md`, "Mechanics of E2".

N2 and S1 were not adopted and are switched off, so E2 is measured on 1.3.0:
the candidate is the wheel of 476a1a4 (E2 on, N2 and S1 off), installed in a
fresh environment with the packages of 1.3.0 (`/venv14e2`), its 11
`gp_elite/` files identical to that commit.

1. **It finds its law.** On 20 exact points of Newton's cooling,
   θ = 20 + 60·exp(−t/600), the exact seed is placed, with a = 20, b = 60 and
   c = −1/600 to within 1e-9, 1e-9 and 1e-14
   (`test_e2_finds_newtons_cooling`); a fit of 5 generations returns the law
   with `formula_exact` (`test_e2_a_short_fit_returns_newtons_law`).
2. **It places nothing elsewhere on exact data** (`mechanics_e2.py`, output
   `mechanics_e2.txt`):
   - on the exact training rows of the 41 equations of F41 and of U41, the
     finder of E2 returns no exact form, and no noise-tolerant form;
   - the 82 bounded fits of F41 and U41 (seed 0, 20 generations, no time
     limit) return the models of 1.3.0 in 82 of 82.
3. **The real data.** On the 13 real fits (R6 and R7raw at fold 0), E2 makes
   one noise-tolerant candidate, on nikuradse_1, and no seed is placed; the
   13 bounded fits return the models of 1.3.0.
4. **Tests.** The suite passes, 198 tests, with three for E2.
