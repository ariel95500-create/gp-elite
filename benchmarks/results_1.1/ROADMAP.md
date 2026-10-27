# What comes after 1.1, in the order the author decided

Kept apart from the plans of 1.1, which this file does not change.

1. **Version 1.1** is released as `PLAN_RELEASE_1.1.md` says (decided on
   26 October 2026).
2. **A plan for a version 1.2 for teaching** is written after gate 6, from
   the list of `DIAGNOSTIC_TP.md` (decided on 26 October 2026).
3. **After 1.2, a measurement of what speed would bring** (decided on
   27 October 2026), described below.

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
