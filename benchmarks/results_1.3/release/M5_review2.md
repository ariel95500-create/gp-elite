# M5, second independent review (9 November 2026)

A third agent reviewed HEAD 16eda39. It had not seen the work, and it was
told not to read the first review. It checked about 230 claims of the same
documents against the records and the code, with `ROADMAP.md` (item 6) and
the two listings of M2 besides. It recomputed about 150 of them from the
records with read-only scripts (`m5/review2/`). Every figure that decides the
release held, the French pages say what the English ones say, and no path
was broken. It reported 10 findings (`m5/review2_report.md`). Each was
checked against the record it names and holds. Each is corrected below, in
the commit of this file, or answered.

| # | Finding | What was done |
|---|---|---|
| 1 | The CHANGELOG placed the noise-tolerant arcsine seed in "25 noisy fits"; 5 of the 25 are feynman_test_1 of TF78, without noise | "the 20 of I.30.5 with noise, and 5 of feynman_test_1 of the frozen test set, which has none" |
| 2 | The READMEs list the safety nets that make the printed formula depart and leave out the clip of the arcsine; the engine's warning names only the power and the division | Both READMEs add "since 1.3, the argument of an arcsine clipped to [−1, 1]". The text of the warning is in the package. Changing it now would change the package after its measurements, so it is left as it is. The author can take it up in a later version |
| 3 | `ROADMAP.md` said nothing is lost on the other laws; on the confirmation, I.50.26 loses its one exact fit | Item 6 says the other eight keep their count, with the two laws named. It also records that the release measurements are done and gate 10 follows |
| 4 | The six-laws notebook gave Snell's curves closer to the law than the noise as a fact of 1.3.0; it was measured on A1 | "avec une première version de l'arc sinus, les courbes que l'outil rendait s'en écartaient moins que le bruit" |
| 5 | The counts by pool of `formula_exact` and of the arcsine seeds had no source in `m2/` | `m2/pool_counts.py` and `.txt`, cited by this README |
| 6 | The CHANGELOG said `poly` and `conserve` give the models of 1.2.0 at equal work; no record measures them | "the change does not reach them in the code, and with the pool `physical`, the one measured, the models are those of 1.2.0 at equal work" |
| 7 | `m3/examine/README.md` cited `e2.log` for times it does not hold | It gives the commit time of the plan, the start after the push, and the file times of the records |
| 8 | Two records of the M3 comparison are not in the repository, and the records of 1.2 with no counterpart are not listed | This README names the two, kept out by `.gitignore` as in 1.2, and the five records of 1.2 with no counterpart |
| 9 | `arcsine_formulas.py` gave the cut formulas of all fits. The bound on hidden arcsines is 180, the fits of the pool `trig` cut with no arcsine visible. The structure of the noisy fits was not shown | The script prints the 180 and the structure beside the status; this README gives the bound |
| 10 | Identical `lscpu` files show the same processor, not the same machine | "The processor was the same as M2's" |
