# How GP_ELITE is measured

Part of the documentation of GP_ELITE: back to the [README](../README.md); [version française](fr/mesures.md).

## The size of the data

On five Feynman equations (without normalisation), the returned model recovers the exact law of four of them at every size from 25 to 10,000 points, in every run; the fifth, the nested rational form I.16.6, comes back exact at 1,000 points and more (at 5,000 in a form other than the textbook one), and in 6 of the 13 runs below (at 200 points once in such a form). The five fits take 40 s in total at 1,000 points and 100 s at 10,000 on one core of our 4-core machine (`benchmarks/feynman_scaling.py`, version 1.4.0; the times depend on the machine).


## Is it solid?

A fair question for a project you have never heard of. Here is where it stands
against the alternatives, and where it does not.

| | GP_ELITE | Neural networks | PySR (state of the art) |
|---|---|---|---|
| Output | **readable formula** | black box | readable formula |
| Installation | `pip install` (pure Python) | heavy | requires **Julia** |
| Held-out validation | **built in** (used for model selection) | do it yourself | do it yourself |
| Physical units | **hard constraint during search** (`units=`) | no | soft penalty (`X_units=`) |
| Stability of the answer | **bootstrap report** (`stability_analysis`) | no | no |
| Speed and accuracy at scale | lower | — | **higher** |

The last row is not a measurement of this project: it is a concession, from the
published results of the compiled engines.

**How changes are decided.** Since 0.8, a change meant to improve the search or
the final selection becomes part of the default behaviour only if it passes a
comparison written in advance: the hypothesis and the decision criteria are
committed before the first run
([`benchmarks/results_0.8/PLAN.md`](https://github.com/ariel95500-create/gp-elite/blob/main/benchmarks/results_0.8/PLAN.md);
the plan of the first campaign was committed six minutes after its first fit had
started), the engine with the change is compared with the engine without it on 41
Feynman equations and on real datasets (six standardised, seven in their own
units) at 30 seconds per fit, one process per fit, and the results are published
whatever they are
([`RESULTS.md`](https://github.com/ariel95500-create/gp-elite/blob/main/benchmarks/results_0.8/RESULTS.md)),
including the changes that did not pass. When a change failed and a restricted
version of it was then tested, the restriction was designed after seeing the
failure and measured on the same problems; `RESULTS.md` says where. Corrections of
defects are not decided this way; the files of `benchmarks/results_0.8/` show what
they change. The changes of 1.0 were decided the same way
([`benchmarks/results_0.9/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks/results_0.9),
`PLAN_PHASE4.md` and `PLAN_PHASE5.md`), and since 0.9 each release is also
measured once on a test set frozen before any decision and never used to make
one: 78 other Feynman equations, 14 Strogatz systems and 25 real datasets. On its
Feynman equations, 1.0 recovers 213 exact laws of 390 against 145 for 0.9 measured
beside it; on its Strogatz systems, 7 exact fits of 70 against 8; on its real
datasets, the same median R² within 0.004 and the same number of collapses out of
the training range
([`release_1.0/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks/results_0.9/release_1.0)).
The change of 1.1 was decided the same way
([`benchmarks/results_1.1/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks/results_1.1)).
Measured beside 1.0 for the release of 1.1, both versions give the same counts of
exact laws without units on the frozen set (213 exact laws of 390 on its Feynman equations, 8
of 70 on its Strogatz systems: under a time budget the counts move a little from
one campaign to the next), and with their units 1.1 recovers 226 exact laws of 390
against 169. The changes of 1.2 were decided the same way
([`benchmarks/results_1.2/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks/results_1.2));
measured beside 1.1 for the release of 1.2, both versions give the same counts on
the frozen set, with and without units (214 exact laws of 390 on its Feynman
equations, 10 of 70 on its Strogatz systems, and 229 of 390 with units). The
change of 1.3 was decided the same way
([`benchmarks/results_1.3/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks/results_1.3)).
Measured beside 1.2 for the release of 1.3, on the frozen set, 1.3 recovers
214 exact laws of 390 on its Feynman equations against 213, 8 of 70 on its
Strogatz systems with both versions, and 228 of 390 with units against 229.
The 213 and 8 of 1.2 in this campaign, against 214 and 10 in its own release,
are the time budget moving the counts from one campaign to the next.
The change of 1.4 was decided the same way
([`benchmarks/results_1.4/`](https://github.com/ariel95500-create/gp-elite/tree/main/benchmarks/results_1.4)),
where three of the four changes measured were not adopted. Measured beside 1.3
for the release of 1.4, on the frozen set, both versions recover 214 exact laws
of 390 on its Feynman equations and 228 with units, and 1.4 has 10 exact fits of
70 on its Strogatz systems against 9. Before any change of 1.4, its Feynman
equations were also frozen with 1 % and 10 % noise on their target: there 1.4
retrieves the structure of the law in 37 and 28 fits of 78 against 34 and 27,
and with units in 37 and 33 against 35 and 32.

GP_ELITE's niche: **zero barrier to entry**. A lab engineer, a student, or a technician points at a CSV file and gets a validated law back — without becoming a developer. `PySR` and `Operon` are faster and more accurate on large or hard problems; GP_ELITE does not claim otherwise.


## What is GP_ELITE good (and less good) at?

**Good at**: physical / engineering laws with multiplicative or exponential structure, modest-size experimental data, problems where interpretability matters most.

On the frozen **Feynman benchmark** (15 physics equations, `restarts=4`, one seed),
judged on the model it returns: **15/15 exact symbolic recoveries** (1−R² < 1e-9 on
held-out data), against 12/15 for 0.9; the three it adds are I.16.6 (relativistic
velocity addition, a nested rational form that is not among the forms 1.0 fits
directly, reached by the search) and two laws with a sine or a cosine, I.18.12
(r·F·sin θ) and III.15.12, which 1.0 fits directly. Head-to-head against
**gplearn** on identical data and splits (population 2000 × 30 generations), each
method judged on its returned model: **15/15 against 6/15** exact, 15/15 against 7/15
within 1e-3 — GP_ELITE ahead on 9 equations and tied on 6. Up to 0.9, a law with an
angle inside a sine or a cosine called for `normalize='none'`, since dividing an
angle by its largest value changes the period the sine has to find (measured for
0.9 on the ten trigonometric laws of the 41-equation bench with five seeds each: 13
of 50 fits exact against 2 of 50 with the default; on real data, leaving the columns
of close scales as given, `normalize='smart'`, predicted worse out of the training
range,
[`benchmarks/results_0.9/PLAN_TRIG.md`](https://github.com/ariel95500-create/gp-elite/blob/main/benchmarks/results_0.9/PLAN_TRIG.md));
with 1.0 the default returns the three laws of this showcase that have one, and
`normalize='none'` remains worth a try when such a law does not come back. With the
physical units declared (`units=`, same budget, no normalisation), 15/15 come back
exact (`benchmarks/feynman_units.py`), 14 in their textbook form; I.16.6, missed up
to 1.0, comes back with a factor 1.00755 above and below that cancels (1.00758 with 1.3). One seed on
fifteen equations is
a showcase, not a statistical comparison:
[`benchmarks/results_0.8/RESULTS.md`](https://github.com/ariel95500-create/gp-elite/blob/main/benchmarks/results_0.8/RESULTS.md)
measures 0.7.0 and each change of 0.8 to the search and the final selection on 41
equations with five seeds at 30 s per fit, and 0.7.0 against 0.8.0 side by side at
equal work on these fifteen equations with five seeds and on six real datasets.
Reproduce: `python benchmarks/feynman_bench.py 0 15` and `python benchmarks/duel.py`.

**Less good at**: chaotic sequences (e.g. Collatz flight time — an intrinsically random component), >15–20 variables (the search space explodes — though `units=` substantially narrows it when physical units are known), large datasets where raw accuracy outweighs interpretability (ensemble models dominate there).
