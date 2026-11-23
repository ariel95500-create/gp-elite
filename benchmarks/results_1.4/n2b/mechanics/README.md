# Mechanics of N2b

Done on 13 November 2026, after the decision of the author
(`../../PLAN.md`, "Decision of the author after the campaigns of N2 and
S1") and before any fit of the campaign of N2b.

N2b is N2 without the fit of the constants of its candidates: every
candidate keeps the constants of its finder, and a form that the finders
of 1.3.0 give keeps their tree, constants included (40f83d3). The mechanics
are those of N2 (`../../n2/mechanics/`), run with `N2B_MECHANICS=1`: the
candidate is this repository with N2b on and E2 and S1 off, so that it is
compared with 1.3.0 from PyPI (`/venv13p`). Output: `mechanics.txt`;
records: `records/`.

1. **The exact seeds are untouched.** The 95 bounded fits (F41 and U41 at
   seed 0, R6 and R7raw at fold 0, 20 generations, no time limit) return
   the models of 1.3.0 in all 95, the 63 where the noise-tolerant stage
   runs included (N2 changed 6 of them). The exact finders are those of N2,
   identical to 1.3.0 (`../../n2/mechanics/compare_dumps.txt`).
2. **No seed is lost.** On the 82 noisy targets of F41 (seed 0), with N2b
   off the seeds printed are those of 1.3.0 on 82 of 82, and every form
   1.3.0 places is placed by N2b, on 47 of 47. A seed with the structure of
   the law is placed on 30 targets of 41 at 1 % noise (22 with 1.3.0, 30
   with N2) and 17 at 10 % (13 with 1.3.0, 19 with N2). None is lost.
3. **The second pass.** At 1 % noise, on I.40.1, II.35.18, II.11.27, I.32.5
   and III.19.51, a candidate with the form of the law is made and placed.
   At 10 % noise it holds for III.19.51 only: I.40.1, II.35.18 and II.11.27
   as with N2 (no candidate has the form), and I.32.5, whose candidate with
   the form of the law is made but not placed, the twelve seeds being taken
   by forms with a lower score.
4. **The best kept.** On III.15.12 with 1 % noise the trigonometric seed in
   k·d is placed; on I.44.4 with 1 % noise the form with the logarithm is
   among the candidates and placed.
5. **The real data.** On the 13 real fits no candidate is within the
   threshold (best score 0.042, on nikuradse_1); no seed is placed.
6. **The time of the stage:** a median 0.18 s on the 82 noisy targets
   (0.72 s at most), 0.21 s with N2.
7. **Tests:** the suite passes against the repository at 40f83d3, with the
   tests of N2 running N2b and one test checking that the seeds of 1.3.0
   are placed with their own constants.
