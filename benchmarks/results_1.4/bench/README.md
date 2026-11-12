# The benches of 1.4, and the baselines of its two frozen test sets

Done on 11 November 2026, after gate 11 and before any change to the engine
(plan: `../PLAN.md`, "The benches").

## What was added to the benches

- **`phase1_bench.py`:**
  - `--noise-draws 1,2,3,4` gives every job of a noisy kind once per draw of
    the noise. A job of draw d carries `"noise_draw": d`.
  - The kinds of TF78N, the frozen noisy test set: `tf_n1`, `tf_n10`,
    `utf_n1` and `utf_n10`. They run on request only.
- **`tp_diagnostic.py`:**
  - `--set tpt10` runs TPT10, the frozen test set for teaching: the ten
    experiments of the plan, numbered 10 to 19 in the generator of the data.
  - The units arm records a new field, `units_gate` (see below).

## The benches of before are unchanged

`check_unchanged.py` compares the two files with those of the commit before
(f93f77b). Its output is `check_unchanged.txt`, and all of it holds:
- **`phase1_bench.py`:** without the new options, the 1,775 jobs (2,780
  with the units kinds) are the same list, with the same keys. The data of
  their 808 distinct tables are identical, byte for byte.
- **`tp_diagnostic.py`:** the 1,200 jobs of draws 0 to 14 are the same, and
  the data of their 600 distinct tables are identical.
- **The new jobs** are those the plan counts: 328 for the confirmation of
  N2, 312 for TF78N, 400 for TPT10.
- **The new draws of the noise** keep the inputs, the test rows and the
  clean targets of draw 0, and change the noisy targets in every job.
- **TF78N** has the inputs and the test rows of TF78. Its generators of the
  noise are not those of F41.
- **TPT10** shares no generator with a table of the diagnostic.

## The baselines, with 1.3.0 from PyPI

Run by `baseline.sh` with `/venv13p`, on 4 cores, 4 fits at a time. Every
record names the engine it used: the 712 fits ran `gp_elite` 1.3.0 from
`/venv13p/lib/python3.11/site-packages`, with `PYTHONHASHSEED=0`, and none
crashed. Only the tables of counts below were read.

### TPT10 (`tpt10_1.3.0.jsonl`, `tpt10_1.3.0.txt`)

Fits with the law, of 20 per experiment and arm:

| experiment | plain arm | units arm |
|---|---|---|
| ohm | 19 | 20 |
| torricelli | 17 | 20 |
| boyle | 12 | 20 |
| kepler3 | 10 | 20 |
| interfrange | 16 | 19 |
| malus | 5 | 3 |
| charge | 7 | 0 (not within reach under units) |
| michaelis | 0 | 0 (not within reach under units) |
| ph | 17 | 1 (not within reach under units) |
| thermistance | 4 | 0 (not within reach under units) |
| **in all, of 200** | **107** | **103** |

Under units, the six experiments within reach have the law in 102 fits of
120. The median time of a fit is 7.1 s in the plain arm and 8.9 s in the
units arm.

### TF78N (`tf78n_1.3.0.jsonl`, `tf78n_1.3.0.txt`)

Fits with the structure of the law, of 78 per kind:

| kind | noise | units | structure |
|---|---|---|---|
| tf_n1 | 1 % | no | 34 |
| tf_n10 | 10 % | no | 27 |
| utf_n1 | 1 % | yes | 35 |
| utf_n10 | 10 % | yes | 32 |

Under units, the 156 models pass `check_dimensions`.

Both sets are measured again at the release, paired with 1.3.0, and
published as measured. They never decide.

## The check of dimensions on the TP bench: one wording of the plan made exact

The plan asks, for the units arm of the TP bench, that "every model passes
`check_dimensions`" (campaign S1, criterion 3). As the bench records it
since 1.3 (`units_ok`), that check compares the units of the model with
those of the target. Eight of the ten experiments of the diagnostic, and
nine of the ten of TPT10, are fitted with `unknown_constant=True`. There
the constant in front carries units, and the guarantee of the engine is
that the model is consistent, not that it has the units of the target. So
`units_ok` is False there by construction, for 1.3.0 as for any candidate:
on the pendulum, `1.99895 * sqrt(L)` is the law and has the units m^0.5.

The criterion is therefore read on the guarantee the engine gives, recorded
from now on as `units_gate`:
- where the experiment has no unknown constant, the check against the
  target, as before;
- where it has one, the internal consistency of the model
  (`check_dimensions` with no target), which is the gate the engine itself
  applies under `unknown_constant=True`.

This is noted here before the first campaign of 1.4. The records of the
baseline of TPT10 were written before the field. Their strict check, where
it applies (interfrange, 20 fits), holds in 20 of 20.
