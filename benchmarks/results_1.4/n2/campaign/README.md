# Campaign N2: not adopted

Run from 12 November 2026, 22:01 UTC, to 13 November, 06:48 UTC. Plan:
`../../PLAN.md`, "Campaign N2"; mechanics: `../mechanics/README.md`.

- **A** is 1.3.0 installed from PyPI (`/venv13p`).
- **B** is the candidate with N2, the wheel of f748793 in a fresh environment
  with the same packages (`/venv14n2`).
- Every job ran with both at the same time, two jobs at a time, on 4 cores,
  one process per fit, `PYTHONHASHSEED=0`, from a copy of the benches at
  8cc3d26.
- **Dnoise and Dguard:** 1,360 jobs per version (`bench_*.jsonl`).
- **TP:** draws 0 to 4, 400 jobs per version (`tp_*.jsonl`).
- No fit crashed. The comparison is `compare_n2.py`, written before the run;
  its output is `compare_n2.txt`.

**An interruption.** The first run (`driver.sh`, detached) stopped at 00:06:58
UTC with 619 jobs of 1,360 done for both versions, paired. The container of
the session stops when the session is idle, and a detached process does not
keep it running. The bench resumed at 03:42 in slices run as background
tasks of the session (`slice.sh`, logs `driver_first.log` and `driver.log`).
The jobs that were running were run again, for both versions. The machine,
recorded at each start (`machine_*.txt`), is of the same model with the same
kernel. The TP part, the only one with a criterion of time, ran in one go.

## The criteria

| kind | A | B |
|---|---|---|
| F41N1, structure (of 205) | 116 | 144 |
| F41N10, structure (of 205) | 87 | 102 |
| U41N1, structure (of 205) | 121 | 147 |
| U41N10, structure (of 205) | 95 | 103 |
| F41, exact (of 205) | 171 | 166 |
| U41, exact (of 205) | 174 | 174 |

1. **Structure under noise, without units:** 203 → 246, so +43 (the
   criterion asked +15); F41N1 +28, F41N10 +15. Holds.
2. **Under units:** U41N1 121 → 147, U41N10 95 → 103. Holds.
3. **No loss without noise:** **fails.**
   - F41 has 166 exact laws against 171, 5 fewer, and the criterion allows 3.
   - I.26.2 is exact at three seeds in A and at none in B.
   - U41 holds (174 and 174).
4. **Real data:** the median test R² of the R6 folds is 0.8095 for both; R6
   and R7raw have 10 collapses out of domain each. No seed is placed on the
   130 real fits. Holds.
5. **The units guarantee:** the 615 models of B under units on the bench, and
   the 200 of the units arm of TP, pass. Holds.
6. **TP:** the law in 126 → 122 fits (plain) and 120 → 120 (units), within
   the 5 allowed; median time 6.9 s → 7.0 s and 8.1 s → 8.1 s. Holds.

**N2 is not adopted.** As the plan says, it is withdrawn from the
candidate, and its cause goes to the author.

## The cause

On F41 the noise-tolerant stage runs in 15 fits only, those of three
equations (I.16.6, I.26.2 and I.37.4), where no exact seed of the binomial
forms or of the functions of a monomial is placed. All 5 exact laws lost are
there: 7 exact fits among these 15 in A, 2 in B. The other 190 fits of F41
are exact in the same number.

The seeds of these fits, read from the records:
- **I.26.2**, θ1 = arcsin(n·sin θ2): both versions place one seed, of the
  same form, `v0·(a + β·sin(ω·v1) + γ·cos(ω·v1))`. In A its constants are
  those of the finder (a single ω of 4.889). In B they are fitted by the
  engine's fit of constants, which N2 adds (item 3 of N2): the ω of the sine
  and that of the cosine become 4.860 and 4.886. That is the only
  difference at the start, and the search returns the arcsine law at seeds
  1, 2 and 4 in A, at none in B.
- **I.16.6**, (u + v)/(1 + uv/c²): both place binomial seeds; B fits their
  constants and adds the new forms of N2.

`examine/` runs these ten fits again with the wheel of B in three
variants: N2 as measured, N2 without the fit of the constants of each
candidate (`_refit_inner` returns its tree), and N2 switched off:

| | I.16.6, exact of 5 | I.26.2, exact of 5 |
|---|---|---|
| N2 as measured | 2 | 0 |
| N2 without the fit of the constants | 4 | 3 |
| N2 switched off (1.3.0) | 4 | 3 |

On these fits the loss comes from the fit of the constants of the
candidates, and not from the second pass or the scans. A seed that keeps
the constants of its finder (one ω for the sine and the cosine) leads the
search to the exact law more often than the same form with its constants
fitted to the training rows. This reading covers these ten fits only: what
the fit of the constants brings under noise is not measured apart.

## Beside the criteria

The structures move on 12 equations under noise (`compare_n2.txt`). The
largest gains are those the review traced: I.40.1, II.35.18, II.11.27,
I.44.4, I.32.5 and III.19.51 at 1 % noise (0 to 2 structures of 5 in A, 4 or
5 in B), and III.15.12. Losses: I.10.7 at 1 % noise (5 → 3), I.26.2 (3 → 2),
and III.15.12 at 10 % noise (5 → 3).

On TP the law moves by at most 3 fits of 20 in an experiment: the point
source (18 → 15) and the ideal gas (18 → 16) in the plain arm, the spring
14 → 15.
