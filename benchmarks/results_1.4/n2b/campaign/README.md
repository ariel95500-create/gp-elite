# Campaign N2b: adopted and kept

Run on 13 November 2026, from 13:40 to 18:51 UTC. Plan: `../../PLAN.md`,
"Decision of the author after the campaigns of N2 and S1" (the benches and
the six criteria of campaign N2); mechanics: `../mechanics/README.md`.

- **A** is 1.3.0 installed from PyPI (`/venv13p`), the candidate with the
  changes kept so far: N2, S1 and E2 are withdrawn, and W1 changes no model.
- **B** is the candidate with N2b, the wheel of 227d837 in a fresh
  environment with the same packages (`/venv14n2b`): N2 without the fit of
  the constants of its candidates.
- Every job ran with both at the same time, two jobs at a time, on 4 cores,
  one process per fit, `PYTHONHASHSEED=0`, from a copy of the benches at
  227d837 (`slice.sh`, log `driver.log`).
- **TP:** draws 0 to 4, 400 jobs per version (`tp_*.jsonl`), run first and in
  one go, from 13:40 to 14:11.
- **Dnoise and Dguard:** 1,360 jobs per version (`bench_*.jsonl`), in three
  slices from 14:11 to 18:51, without interruption.
- No fit crashed. The comparison is `compare_n2b.py`, written before the run
  (it reads the criteria with `../../n2/campaign/compare_n2.py`, unchanged);
  its output is `compare_n2b.txt`.

## The criteria

| kind | A | B |
|---|---|---|
| F41N1, structure (of 205) | 116 | 152 |
| F41N10, structure (of 205) | 87 | 95 |
| U41N1, structure (of 205) | 121 | 150 |
| U41N10, structure (of 205) | 95 | 93 |
| F41, exact (of 205) | 171 | 171 |
| U41, exact (of 205) | 173 | 173 |

1. **Structure under noise, without units:** 203 → 247, so +44 (the
   criterion asks +15); F41N1 +36, F41N10 +8. Holds.
2. **Under units:** U41N1 121 → 150, U41N10 95 → 93, within the 3 allowed.
   Holds.
3. **No loss without noise:** F41 has 171 exact laws in both, U41 173 in
   both, and no equation falls. Holds. This is the criterion N2 failed (166
   against 171): its cause, the fit of the constants of the candidates, is
   not in N2b.
4. **Real data:** the median test R² of the R6 folds is 0.8095 for both; R6
   and R7raw have 10 collapses out of domain each. No seed is placed on the
   130 real fits. Holds.
5. **The units guarantee:** the 615 models of B under units on the benches,
   and the 200 of the units arm of TP, pass. Holds.
6. **TP:** the law in 126 → 123 fits (plain) and 120 → 120 (units), within
   the 5 allowed; median time 7.0 s → 7.0 s and 8.4 s → 8.5 s. Holds.

**N2b is adopted.**

## The confirmation

Run on 13 November 2026, from 18:51 to 20:18 UTC, in one slice, as the
campaign (`slice.sh ... conf`, log `driver_conf.log`): the new draws of the
noise 1 to 4 on feyn_n1 and feyn_n10 at seed 0, 328 fits per version
(`conf_*.jsonl`), no crash. Output: `compare_n2b_conf.txt`.

| | A | B |
|---|---|---|
| F41N1, structure (of 164) | 90 | 121 |
| F41N10, structure (of 164) | 66 | 71 |
| both (of 328) | 156 | 192 |

- B has 36 structures more than A over the 328 fits; the plan asks 10.
  Holds.
- F41N1 and F41N10 each have no fewer than A minus 3. Holds.

**N2b is kept.** It is part of the candidate of 1.4. B has more structures
than A in each draw at 1 % noise (+7 to +9), and in three draws of four at
10 % noise (draw 3: 17 → 15).

## Beside the criteria

- **The structures move on nine equations** (`compare_n2b.txt`). At 1 %
  noise, I.40.1, I.44.4, II.11.27, II.11.3, II.35.18 and III.15.12 go from 0
  structures of 5 to 5, I.32.5 and III.19.51 from 2 to 5. At 10 % noise,
  I.32.5, I.44.4 and III.19.51 reach 5. Two equations lose at 10 % noise:
  I.27.6 (2 → 0 without units, 5 → 1 with them) and III.15.12 (5 → 2 and
  5 → 1). The gain is that of N2 (246 structures of 410), without its loss
  of exact laws.
- **The noise-tolerant seeds** are placed in 535 of the 820 noisy fits of
  the benches (A 415), and in none of the 130 real fits.
- **TP:** the law moves by one fit in four experiments, and the point
  source falls from 18 to 14 in the plain arm. Campaigns N2 and E2 lowered it
  too, to 15 each. The criteria of N2 read TP as a whole; this fall is
  reported to the author.

## The point source

`examine/` runs the 20 fits of the plain arm of the point source again with
A and B and records the seeds each places (`examine.py`, output
`examine.txt`). Each version returns the models of the campaign again in 20
fits of 20.

- B places every seed of A in the 20 fits, as N2b promises, and adds others:
  210 seeds in all against 120. Most are forms of 1/d² with a small
  correction, such as (1/d²)·(1 + ε/d²) or (1/d²)·log(K·d) with a very large
  K, that follow the 10 or 20 noisy points as closely as the law.
- 12 models of 20 change. The law is lost in 4 fits and gained in none: B
  returns forms that follow the noise more closely, such as
  0.907/d² + 0.149·d.

As in campaign E2, the added seeds remove nothing but move the search, and
on these few noisy points its final choice can leave the law. The three
campaigns of 1.4 that act on small noisy tables (S1, E2 and, here, N2b)
point to that final choice.
