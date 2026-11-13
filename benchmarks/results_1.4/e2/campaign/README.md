# Campaign E2: not adopted

Run on 13 November 2026, from 07:49 to 13:07 UTC. Plan: `../../PLAN.md`,
"Change E2" and "Campaign E2"; mechanics: `../mechanics/README.md`.

- **A** is 1.3.0 installed from PyPI (`/venv13p`), the candidate before E2:
  N2 and S1 are withdrawn.
- **B** is the candidate with E2, the wheel of 476a1a4 in a fresh
  environment with the same packages (`/venv14e2`).
- Every job ran with both at the same time, two jobs at a time, on 4 cores,
  one process per fit, `PYTHONHASHSEED=0`, from a copy of the benches at
  6c0820c (`slice.sh`, log `driver.log`).
- **TP:** draws 0 to 4, 400 jobs per version (`tp_main_*.jsonl`), run first
  and in one go, from 07:49 to 08:21.
- **Dnoise and Dguard:** 1,360 jobs per version (`bench_*.jsonl`), in
  slices from 08:24 to 13:07.
- No fit crashed. The comparison is `compare_e2.py`, written before the run;
  its output is `compare_e2.txt`.

**An interruption.** The container restarted at about 10:22 UTC, during the
second slice of the benches, with 584 jobs of 1,360 done for both versions,
paired and intact. The benches resumed at 10:23; the jobs that were running
were run again, for both versions. The machine, recorded at each start
(`machine_*.txt`), is of the same model. TP, the only part with a criterion
of time, had ended before.

## The criteria

| | A | B |
|---|---|---|
| TP, Newton's cooling, plain arm, the law (of 20) | 3 | 7 |
| TP, plain arm, the law (of 200) | 126 | 122 |
| TP, units arm, the law (of 200) | 120 | 120 |
| F41N1, structure (of 205) | 115 | 116 |
| F41N10, structure (of 205) | 87 | 87 |
| U41N1, structure (of 205) | 121 | 121 |
| U41N10, structure (of 205) | 95 | 95 |
| F41, exact (of 205) | 171 | 171 |
| U41, exact (of 205) | 173 | 173 |

1. **Newton's cooling, plain arm:** the law in 7 fits of 20 (A 3); the plan
   asks 10. **Fails.**
2. **No loss on TP:** in the plain arm the point source falls from 18 to 15,
   by more than 2. **Fails.** The thin lens (2 → 0), the capacitor
   discharge (15 → 13) and the ideal gas (18 → 17) stay within 2. The units
   arm holds: 120 and 120, and its 200 models are those of A.
3. **No loss on the benches:** the four kinds under noise move by at most one
   structure; the exact laws are 171 and 173 for both; the median test R² of
   the R6 folds is 0.8095 for both, with 10 collapses out of domain each;
   the 615 models of B under units on the benches and the 200 of the units
   arm of TP pass. Holds.
4. **Time:** the median time of a fit of TP is 7.2 s for A and 7.0 s for B in
   the plain arm, 8.5 s for both under units. Holds.

**E2 is not adopted.** As the plan says, it is withdrawn from the candidate
(`_E2_SEEDS` False, its code kept), its confirmation is not run, and its
cause goes to the author.

A has one structure and one exact law fewer here than in campaign N2
(F41N1 116 → 115, U41 exact 174 → 173), with the same engine: the fits of the
benches have a time budget, and timing alone moves a few from one run to the
next. The fits of TP do not move: A returns the same 400 models in both
campaigns.

## The cause

`examine/` runs the 200 fits of the plain arm of TP again with A and B and
records the seeds each places (`examine.py`, output `examine.txt`). Each
version returns the models of the campaign again in 200 fits of 200, so
what differs between A and B comes from E2.

- **E2 adds seeds and removes none.** B places seeds of E2 in 139 fits of
  the 200, 222 in all, on all ten experiments; every seed of A is placed by
  B too. The form a + b·exp(c·g) comes within the threshold of 1.5 % on laws
  that are not exponentials: on the point source, exp(0.21/d) leaves
  0.03 % on 10 points with 2 % noise.
- **Where A had the law, these seeds move the search.** On the point source,
  A places forms built on 1/d² in its 20 fits; B adds two forms of E2 in all
  20, 14 models change, and the law is lost in 4 fits and gained in 1
  (18 → 15). The thin lens and the ideal gas are of the same kind.
- **Where E2 places the structure of the law, the search mostly does not
  keep it.** On Newton's cooling, A places no seed. B places exp(c·t),
  which with the scaling of the search is the structure of the law, in 18
  fits of 20; in the other 2 (20 points, 5 % noise) its form leaves more
  than 1.5 %. The law comes back in 7 of these 18 fits: 5 at 2 % noise and 2
  at 5 %. In the other 11 the search returns a form that follows the 10 or
  20 noisy points more closely, such as
  78.75 − 154.17·tanh(0.000556·t/exp(t/1800)). The capacitor discharge, a
  pure exponential, is alike: A places no seed and finds the law in 15 fits;
  B places its structure in all 20 and finds it in 13.

On these tables the seed does not decide; the final choice among the forms
of the search does, as campaign S1 found. A variant of E2 placed only where
the stage of 1.3.0 places nothing would act on TP only in the fits of the
cooling and of the discharge, where B's seeds of E2 are placed alone. The
fits being reproducible, its result there is that of B: 7 fits of 20 for
the cooling, and its criterion 1 would fail in the same way.

This reading covers the plain arm of TP, draws 0 to 4.
