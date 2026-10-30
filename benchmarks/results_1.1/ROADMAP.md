# What comes after 1.1, in the order the author decided

Kept apart from the plans of 1.1, which this file does not change.

1. **Version 1.1** is released as `PLAN_RELEASE_1.1.md` says (decided on
   26 October 2026).
2. **Two actions for SRBench** (decided on 28 October 2026), described
   below: asking its maintainers for the calendar of the next update, and,
   once the measurements of 1.1 leave the machine free, a study of the
   settings SRBench runs GP_ELITE with.
3. **A plan for a version 1.2 for teaching** is written after gate 6, from
   the list of `DIAGNOSTIC_TP.md` (decided on 26 October 2026).
4. **After 1.2, a measurement of what speed would bring** (decided on
   27 October 2026), described below.

## SRBench

What was read on 28 October 2026 in `cavalab/srbench` (master, 2aabbb6;
the files and lines are recorded in `srbench_2aabbb6/`):
- GP_ELITE is listed among the methods "staged for benchmarking", built
  and tested by the container workflows, absent from the figures of the
  2025 edition. No date for the next update is given in the
  repository.
- `algorithms/gp-elite/requirements.txt` asks for `gp-elite>=0.8.0`: the
  version evaluated is the one on PyPI on the day the containers of the run
  are built.
- The harness passes no units (`metadata.yml` says so). Version 1.1, which
  changes the units mode only, changes nothing there; 1.0.0 does (F41 exact
  laws without units: 88 with 0.9.0, 163 with 1.0.0).
- The wrapper (`experiment/methods/gp-elite/regressor.py`), written for
  0.8.0, runs 10 time-bounded restarts in 3,600 s, and its grid of
  hyperparameters is `operators` in ("physical", "full") by `generations`
  in (30, 60).

The two actions:
1. **The calendar.** Claude drafts a short question to the maintainers, in
   English; the author decides whether and where to send it.
2. **The settings.** After M4 of 1.1, when no measurement of the release
   runs on the machine:
   - the SRBench test of the GP_ELITE wrapper is run with 1.0.0 and 1.1.0;
   - the wrapper, unchanged, is measured with 1.0.0 on the benches of the
     project (exact laws of F41, structures under noise, R6 folds and
     collapses out of domain), not on the datasets of SRBench, under its
     settings and a few others named in a plan committed before the first
     fit, with the criteria that would make one of them better;
   - a final check on public datasets of SRBench (decided on 28 October
     2026), as for the frozen test set of the project: it starts only after
     the choice of setting is committed, it is published as measured, and it
     decides nothing. The protocol of SRBench, 30 runs of up to an hour on
     each of 24 datasets, is about 720 hours per setting and out of reach of
     this machine. The plan of the study names beforehand the reduced check
     it runs: which datasets, how many runs, what budget.

   If one setting is better, a small change of the wrapper is put to the
   author with the final check beside it. The author decides whether to
   propose it to SRBench.

When the plan of 1.2 is written, its items that also act without units
(for instance an earlier stop when the law is found, which SRBench would
see in its training times) are proposed first.

Among them, from M3 of 1.1 (decided on 30 October 2026): on the noisy data
of the TP notebook, version 1.1 places the law at the start for some fits
(traced for the free fall and the gas law), but no law is exact, so the
search runs its whole budget, about 50 s per fit. A stop
when the placed law holds to the noise of the data, if a plan shows it
safe, could bring each fit to a few seconds. The free fall, 7 s slower with
1.1.0 than with 1.0.0 (`release/README.md`, M3), is measured again there.

## What speed would bring

The author asked whether a second GP_ELITE, free of the pure Python rule
and as fast as a compiled engine can be, would be worth building. Before
any code is written in another language, the engine of the day is measured
with more time, which costs no rewrite: a faster engine does in 30 s what
this one does in 300 s.

- The bench of phase 1 (`phase1_bench.py`, 30 s and 1,000 generations per
  fit) is run again with ten times the budget, and with three times, on the
  design sets: the exact laws of F41 and U41, the structures under noise,
  the R6 folds. The frozen test set is reported and decides nothing.
- The generations are raised with the budget, so that the time-bounded
  restarts can use it.
- What is measured, the figures that would call for a faster engine, and
  those that would not, are written in a plan and committed before the
  first fit, as for every measurement of the project.

How the result will be used:
- if ten times the time adds little, a faster engine would add little, and
  the work stays on the search itself;
- if it adds much, a plan for an optional accelerator is put to the author:
  installed only by those who want it, inside the same package, with
  GP_ELITE pure Python and NumPy without it, and with tests proving that
  both return the same models, as the equivalence tests do today. A
  separate second tool is not recommended: it would compete with Operon
  and PySR where they are strongest, and double the code, the measurements
  and the files to publish.

The author decides at each step. Nothing here starts before 1.2 is
released.
