# Campaign S1: not adopted

Run on 13 November 2026, 07:01 to 07:39 UTC. Plan: `../../PLAN.md`,
"Campaign S1"; mechanics: `../mechanics/README.md`.

- **A** is 1.3.0 from PyPI (`/venv13p`): N2 was withdrawn, so the candidate
  before S1 is 1.3.0.
- **B** is the candidate with S1, the wheel of 9d2c96d (`/venv14s1`).
- The TP diagnostic, draws 0 to 4, 400 jobs per version, every job with both
  at the same time, two jobs at a time, from a copy of the benches at
  010881b (`run.sh`).
- No fit crashed. The comparison is `compare_s1.py`, written before the run;
  its output is `compare_s1.txt`.

## The criteria

| arm | law A | law B | median time A | B |
|---|---|---|---|---|
| plain | 126 | 113 | 7.0 s | 11.7 s |
| units | 120 | 119 | 8.2 s | 8.3 s |

1. **The plain arm:** the law in 113 fits of 200 against 126. The criterion
   asked at least 141. **Fails.**
2. **No experiment falls:** five fall by more than 2 fits of 20, the free
   fall 19 → 16, the ideal gas 18 → 15, the pendulum 17 → 13, the capacitor
   15 → 12, the spring 14 → 10. **Fails.**
3. **The units arm:** the law in 119 fits against 120, and every model of B
   passes its gate of dimensions (200 of 200). Holds.
4. **Time:** in the plain arm the median goes from 7.0 s to 11.7 s, 1.67
   times A's. **Fails.** In the units arm, 8.2 s and 8.3 s.

**S1 is not adopted.** As the plan says, it is withdrawn from the candidate,
its confirmation is not run, and its cause goes to the author.

## The cause

In the plain arm the law is lost in 29 fits and gained in 16.

**Where it is lost**, the model chosen is in 24 of 29 a structure the search
found on the whole table ("search" or "band" in the trace of S1), with 6 to
10 fitted constants. On the pendulum with 10 points and 2 % noise:
`0.376326 + 0.46721 / (0.177928 / L + 4.35408 * L / (15…`, where 1.3.0
returned `-0.0290401 + 2.03646 * sqrt(L)`. The law is on the front of B in
28 of these 29 fits: it was among the candidates and was not chosen. The
search chose these structures on the same 10 or 20 points, and the
cross-validation refits only their constants, so their error is
optimistic. The law falls out of the tolerance of the best, one standard
error or 0.003 in R², and the rule of the fewest constants never reaches
it. The mechanics had seen it on one pendulum table
(`../mechanics/README.md`).

**Where it is gained**, the model is what S1 was for, a textbook law with
no constant it does not have:
- the thin lens, in 5 fits, `0.0986121 / (1.00142 - 0.0995573 / p)`
  (1.3.0 had it in 2 fits of 20, and keeps 2 in A);
- Newton's cooling, in 3 fits, `20.5482 + 59.83 * exp(-t / 576.348)`;
- the pendulum `2.02585 * sqrt(L)`, the spring `6.33339 * sqrt(m / k)`, the
  free fall `4.90445 * t²`, the point source `0.782319 / d²`, the capacitor
  `5.10037 * exp(-t / 0.97218)`.

Of the 113 fits of B with the law, 101 print it without an additive
constant; none of the 126 of A does. The law is on the front returned in
155 fits of 200 with B; below 30 rows, 1.3.0 had no front.

**The time:** the cross-validation of S1 takes a median 4.2 s per fit in the
plain arm (14.1 s at most), for up to 40 candidates and 10 folds.
