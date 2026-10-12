# Phase 3 (the units mode) — plan written before any measurement

Written on 11 October 2026, when the author chose phase 3 after phase 4a.
Method as in the earlier phases: this plan and its criteria are committed
before the first fit of the phase, one process per fit, `PYTHONHASHSEED=0`,
paired arms side by side, median and worst case reported, the frozen test
set never used.

## What phase 3 has to do

The target of gate 2: with `units=` declared, Feynman II.11.3
(`x = q·Ef/(m·(w0² − w²))`, five variables, 40 generations, the typed arm of
`benchmarks/ab_ood.py`) takes at most 60 s per run, with every model
dimensionally valid and at least 2 exact laws in 5 runs. 0.8.0 took 149 s per
run (median, 5 seeds, on a 2-core container in September). The plan of 0.9
gives the phase two steps, in this order, and an exit criterion: a typed
generation costs at most three times an untyped one.

- **3a, speed-ups that change no model.** Profile the typed search, then
  make faster only what can be made faster without changing a single
  returned model (rule 5 of the plan: a speed-up returns the same models bit
  for bit, otherwise it is a change of the search and goes through a
  campaign).
- **3b, a plateau stop proper to the typed mode.** A change of the search,
  decided by campaign U1. It runs only if 3a leaves II.11.3 above 60 s.

Why it is slow, from the 0.8 diagnostic D2
(`benchmarks/results_0.8/typed_generations.jsonl`): 0.8.0 stops a search
early only on an exact law, so a typed run that ends on an approximation goes
through its 40 generations, at 3.6 to 4.1 s each; the untyped arm takes
about 0.5 s per generation on the same data (21 s for 40 generations in the
README table). Reaching 60 s for 40 generations means 1.5 s per typed
generation, which is also what the exit criterion asks (three times 0.5 s).

What the code suggests before any profile (`gp_elite/dim_search.py`): the
reachability test solves a least-squares system at each call, with a cache
that is rebuilt at every mutation; the dimension of each subtree is inferred
again from the leaves for every node that `typed_mutate` and
`typed_crossover` look at, a cost quadratic in the size of the tree; and the
validity gate infers the dimension of every candidate at every fitness call,
before the fitness cache is consulted. Each is a pure function of its inputs
that draws nothing from the random generators. The profile decides which of
them matter.

## U0, the baseline on this machine (before any change)

gp-elite 0.8.0 installed from PyPI in a fresh environment, the 4-core
machine of phases 1, 2 and 4. II.11.3 exactly as `ab_ood.py` builds it (200
training points, test and out-of-domain sets of 200 points, `operators=
"physical"`, `generations=40`, `speed="fast"`, `restarts=1`), seeds 0 to 9.
Two arms per seed: typed (`units=`, `target_units=`) and untyped (the same
call without them). One process per fit, two fits at a time (the typed and
untyped fits of one seed side by side, the two other cores idle), so that
every timing of the phase is taken under the same load.

Recorded for each fit (`benchmarks/phase3_bench.py`, `u0_0.8.0.jsonl`):
seconds, generations run (the counter of `typed_generations_check.py`),
seconds per generation, dimensionally valid, exact law recovered (out-of-
domain R² above 0.999 and valid, the criterion of `ab_ood.py`), test and
out-of-domain R², size, the printed equation, a SHA-256 of the predictions
on the test and out-of-domain sets, and the generations at which the best
model improved (the engine's own log, captured). Reported: median and worst
time, the per-seed ratio of typed to untyped seconds per generation, valid
and exact counts. This is the "measured again in phase 3" of the gate 2
table.

Note added on 11 October 2026, before the first fit of U0: every fit of the
phase passes `parallel=False`, as in phase 1. `ab_ood.py` leaves the
default, which runs the islands in parallel processes from four cores up;
the 0.8 figures came from a 2-core container, where the same default runs
them in sequence. Without it, each fit would take three cores here and
return other models than the published ones. One smoke fit of the bench
(untyped, seed 0, not recorded in U0) showed it: its generation counter
stayed at zero, the islands having run in other processes.

## 3a: profile, then speed-ups that change no model

**Profile (diagnostic, decides nothing).** `cProfile` on the typed fit of
seed 0, 0.8.0 engine; the functions that take the time, cumulative and own.

**What may change.** Only computations whose result is a pure function of
their inputs, that draw nothing from `random` or NumPy's generators, and that
leave every draw in the same order. A cache is keyed on everything its
result depends on. No change to what the search builds, keeps or returns.

**Equivalence, all required, checked before any timing is reported:**

1. E1: the thirteen reference configurations of
   `benchmarks/speed_equivalence.py` return the same models as 0.8.0
   (`benchmarks/results_0.9/repro/default`). One of them, `D_units`, runs
   the typed search.
2. E2: the typed fits of II.11.3, seeds 0 to 9, return the same equation,
   the same size and predictions identical bit for bit (same SHA-256 on the
   test and out-of-domain sets) as in U0.
3. E3: the unknown-constant mode, which shares the typed generator, returns
   the same models as 0.8.0 on the three laws of
   `benchmarks/test_constante_mystere.py` (Hooke, Newton, ideal gas) with
   the script's defaults.
4. E4: the test suite passes (140 tests).

Any difference refuses the change, which is corrected or dropped before
anything else runs (the risk "a cache changes a model" of the plan).

**Timing (once E1 to E4 hold).** The typed fits of seeds 0 to 9 run again,
the new engine and 0.8.0 side by side for each seed (two fits at a time):
the paired speed-up, median and worst. Then the typed and untyped fits of
the new engine side by side: the per-seed ratio of seconds per generation,
median and worst.

**Adoption of 3a.** E1 to E4 hold, and the median paired typed time falls
by at least 10 % (below that, the extra code is not worth carrying). The
models being identical, the number of generations is too, so time per run
and time per generation fall by the same factor.

**Expectation, not a criterion.** The 60 s target may be out of reach of 3a
alone: if the profile shows that the time goes into the evaluation of the
trees (the same interpreter as the untyped search) rather than into the
typed operators, 3a will gain little and 3b becomes necessary.

## 3b: a plateau stop for the typed mode (campaign U1)

Run only if, after 3a, the median of II.11.3 stays above 60 s. Its exact
rule is written and committed before it is implemented, from the U0 logs of
seeds 0 to 4 only (the generations at which the best model improved, and at
which the exact laws appeared). Seeds 5 to 9 and the fifteen Feynman
equations with units are kept for the decision, as rule 4 of the plan asks
of a variant designed on known cases.

Fixed now:

- The stop acts only in typed mode (`units=` declared). The untyped search
  is untouched: the twelve reference configurations other than `D_units`
  return the same models as 0.8.0.
- It never stops a run before a fixed minimum number of generations, and it
  is judged on the hold-out, relative to the variance of the target, like
  the exact-law stop of 0.8.0, never on an absolute threshold (the unit of
  y must not matter).

**Criteria of U1, all required:**

1. II.11.3, typed, seeds 0 to 9, against the U0 fits of 0.8.0 (or of 3a,
   identical): median time at most 60 s.
2. 10 of 10 dimensionally valid.
3. Exact laws: at least as many as 0.8.0 on seeds 0 to 9 less one, and at
   least 2 of 5 on seeds 0 to 4 (the gate 2 target). A stop truncates a
   run, so a seed can lose its law only if the law came after the stop;
   the margin of one is for that case and nothing else.
4. The fifteen Feynman equations with units (`benchmarks/feynman_units.py`,
   seed 0, four restarts, as published): exact laws at most one fewer than
   0.8.0 measured on this machine before U1 (14 of 15 in 0.8). With four
   restarts the stop of one restart changes the random state of the next,
   so these runs are not truncations of each other: the margin of one
   allows that noise, the lesson of phase 4.
5. Median out-of-domain R² on II.11.3 not lower than 0.8.0's by more than
   0.01 (an earlier stop must not trade the law for a worse approximation).

If U1 fails, 3b is not adopted and the phase ends with 3a and what it
measured.

## Exit of the phase

The gate 2 indicator (median time, valid, exact on seeds 0 to 4) and the
ratio typed to untyped are reported as measured, met or not. The README
table and the CHANGELOG are updated only with numbers measured on the
engine that is kept.

## Results (11 October 2026)

Records in `benchmarks/results_0.9/phase3/`. The container was replaced
before this phase: the machine has four cores like the one of phases 1, 2
and 4, but an Intel Xeon at 2.8 GHz with AVX-512 (that one ran at 2.1 GHz),
with the same Python 3.11.15, NumPy 2.4.6 and scikit-learn 1.9.1. Before U0,
gp-elite 0.8.0 installed from PyPI returned on it the same models as on that
machine for the thirteen reference configurations
(`compare_E0_0.8.0_this_machine.txt`, models in `equiv_0.8.0_this_machine/`).

### U0, gp-elite 0.8.0 (`u0_0.8.0.jsonl`)

| arm | median s | worst s | median s per generation | valid | exact | median out-of-domain R² |
|---|---|---|---|---|---|---|
| typed | 179.6 | 205.4 | 5.12 | 10 of 10 | 4 of 10 | 0.668 |
| untyped | 24.2 | 34.5 | 0.605 | 0 of 10 | 0 of 10 | 0.336 |

The four exact laws are seeds 1, 4, 7 and 9 (2 of 5 on seeds 0 to 4, as in
the README); those runs stop on the law after 5, 22, 8 and 14 generations,
the six others go through the 40. Per seed, a typed generation cost 8.47
times an untyped one (median; worst 13.67). This machine is slower per fit
than the 2-core container of 0.8: 0.605 s per untyped generation against
0.53 s (21 s for 40 generations in the README table), and the typed median
of U0, 179.6 s, against the 149 s of the README.

### Profile (`profile_0.8.0_typed_seed0.txt`)

Under the profiler, the typed fit of seed 0 took 519 s, of which 448 s in
`typed_mutate`, almost all of it in `_build` (8.1 million calls for 8,745
mutations): 244 s computing the keys of dimension dicts (56 million calls,
most of them for the features, the same at every call) and 125 s testing
reachability (553,000 least-squares solves, and keys of their own: the two
times overlap).
The crossover took 14 s and the validity gate 5 s; among the steps the
untyped search shares, the fitting of constants by Levenberg-Marquardt took
16 s, the simplification 12 s and the fitness 9 s. The
expectation that 3a might gain little was wrong: the time went into the
typed operators.

### 3a, what changed (commit 118a42d)

- `gp_elite/dim_search.py`: what `_build` computed again at each call is
  computed once per set of units and pool of operators, and kept: the keys of
  the feature dimensions and the features of each dimension, the
  reachability of each target dimension, and the list of productions, copied
  before each shuffle. A dimension travels through `_build` as its exact key
  (the sorted items of its dict, floats untouched); the dimension of each
  product, quotient and power is computed from the same floats as before,
  then kept.
- `typed_crossover` infers the dimension of every subtree in one pass from
  the leaves instead of once per ancestor. `dimensions._infer` is split into
  `_leaf_dim` and `_combine`, its own rules, which both use: the auditor and
  the search keep one source of truth.
- `tests/test_speed_equivalence.py`: two tests compare with the 0.8.0 code
  copied verbatim. The builder and the typed mutation, on three sets of units
  and three pools, build the same trees and leave the random generator in the
  same state after every call; the inference of every subtree and the
  crossover agree on 900 random trees, sound or not.

### Equivalence: all four hold

1. E1: the thirteen configurations return the same models
   (`compare_E1_13_configurations.txt`).
2. E2: on the ten seeds, the typed fits of 3a return the same equation, the
   same size and the same predictions (same SHA-256) as U0, with the same log
   of improvements generation by generation; so did both timed runs.
3. E3: the three laws of the unknown-constant mode return the same models,
   constant units and value included (`compare_E3_unknown_constant.txt`).
4. E4: 142 tests pass (the 140 and the two above).

### Timing

0.8.0 and 3a side by side on the typed fits (`e2_timing_080_vs_3a.jsonl`):
median 178.9 s to 33.5 s, worst 211.4 s to 42.8 s; per seed, 3a is 5.86
times faster (median), 4.77 times at least. 3a typed and untyped side by
side (`ratio_3a_typed_vs_untyped.jsonl`): typed 31.8 s (worst 42.4 s),
untyped 22.7 s; a typed generation costs 1.44 times an untyped one per seed
(median), 1.74 at worst. The profile of 3a (`profile_3a_typed_seed0.txt`):
the fit took 103 s under the profiler against 519 s, `_build` 39 s.

**Decision: 3a adopted.** E1 to E4 hold and the median time falls by 81 %
(178.9 s to 33.5 s), well beyond the 10 % asked.

### 3b not run

The plan runs 3b only if II.11.3 stays above 60 s after 3a; it takes 33.5 s.
Campaign U1 is not needed, and the plateau stop stays an idea, not measured.

### Exit of the phase

| | 0.8.0 (this machine) | after 3a | target |
|---|---|---|---|
| II.11.3, median s per run (paired timing) | 178.9 | 33.5 | at most 60 |
| worst s per run (paired timing) | 211.4 | 42.8 | — |
| valid | 10 of 10 | 10 of 10 | 5 of 5 |
| exact, seeds 0 to 4 | 2 of 5 | 2 of 5 | at least 2 of 5 |
| typed / untyped s per generation | 8.47 | 1.44 (worst 1.74) | at most 3 |

All met, with the same models as 0.8.0, so the same laws. The README table
of 0.8 (149 s on a 2-core container) describes the published version and is
measured again on the 0.9 release, like every public figure; the CHANGELOG
has an entry.

Corrections of 12 October 2026, after the first independent review of the
release: the counts of the profile are rounded as the records give them (56
million calls, 553,000 solves; they read 55 million and 552,000), the steps
outside the typed operators are named with their own times from the profile,
now printed with its 45 largest entries, the time of 3a under the profiler
is that of the fit (103 s; 105 s was the whole process), and both columns of
the exit table come from the paired timing (the median was U0's 179.6 s).
