# A1, the arcsine: the mechanics

Run on 8 November 2026, before any fit of campaign A1
(`../PLAN.md`, *Mechanics*).

- **Engine:** A1 is commit 496704b.
- **Environments:**
  - A, the 1.2.0 wheel from PyPI, in `/venv12p`;
  - B, the candidate, in `/venv13a`. Its wheel was built from 496704b
    (sha256 `0335aa34…9f86`) and installed with the packages of `/venv12p`.
    The two `pip freeze` differ only in that line.
- **The candidate's version** still reads 1.2.0. The number changes at M1 of
  the release, as for 1.2. The records tell the two engines apart by their
  `engine_file`.
- **The machine:** `machine.txt`.

## 1. The pools without the arcsine are untouched: holds

- **The reference configurations** (`compare_1.2.0_vs_a1_equiv.txt`): the
  eleven that use `physical` are identical to the 1.2.0 wheel in every field.
  E_minmax (`full`) and L_standard (`trig`) change, as the plan expected
  (`equiv_changed.txt`):
  - E_minmax: `-11.557 - 15.4828 * (cos(0.136873 * (X0 - 14.9609)) - 0.361898 * X0)`
    becomes `190.408 - 196.336 * cos(0.224029 + 0.0403506 * X0)`;
  - L_standard: a formula with `cos(exp(…))` becomes
    `0.0932769 + 7.40443 * (X0 - 0.0353729) * (0.900884 - cos(-0.00732823 + 0.577175 * X1))`.

  Neither formula has the arcsine. They change because the pool they draw
  from has one more operator.
- **147 fits, all identical in every field** (`compare_mechanics_1.txt`,
  from `mechanics.py`): expression, error, size, `formula_exact`, the
  check of units, the generations, and on TP the errors, the law and the
  stop on patience. The fits:
  - F41 seed 0 and U41 seed 0, the 31 equations of the pool `physical` each,
    bounded by 20 generations with no time limit;
  - R6 and R7raw, fold 0 of each dataset, bounded the same way;
  - the nine experiments of TP of the pool `physical`, both arms, draw 0,
    under the API defaults (72 fits).

## 2. The operator, checked by itself: holds

`tests/test_arcsin.py` (`tests_a1.txt`):
- the guard;
- the folding: `arcsin(0.5)` gives 0.5235987755982989;
- on 200 random trees, every path of evaluation agrees. The arcsine's
  argument falls outside [−1, 1] in 75 of them;
- the formula and its three sympy forms reproduce `predict()` where the
  clip does not act. Where it acts, the printed formula departs from the
  model;
- the units: the argument and the result must be dimensionless;
- the pools: the arcsine is in `trig` and `full` with weight 2, and in no
  other pool;
- the typed start draws the arcsine only where the pool has it.

**Deviation from the wording of the plan.** The plan asked that every path
of evaluation agree to 1e-12, the scalar path among them. The scalar path
(`core.evaluate`, used only for display) already computes a power with a
variable exponent otherwise than the vector paths in 1.2.0, with no
arcsine: 3 rows of 40 on `pow(X2, -pow(X1 / X0, sin(X1)))`, on the 1.2.0
wheel. So the scalar path is compared on the 174 trees without a power. The
interpreter, the compiled code, the compiler of constants and the
incremental plan of the fit of constants are compared on all 200, bit for
bit.

## 3. A fit can find it: holds

`find_I.30.5.jsonl`: I.30.5 with the pool `trig`, `generations=200`, seed 0.
- **It draws the arcsine:** 26 of the 109 candidates offered to the final
  selection have one.
- **The model returned has no arcsine.** It is
  `8.49588e-07 + 0.488738 * v0 / (v1 * v2) / tanh(1.01812 - 0.310433 * v0² / (v1² * v2²)) * (…)`,
  an approximation with 1 − R² of 2.1e-11 on the test rows.
- **What that means for the bench:** this fit counts as exact by the
  bench's threshold (1e-9), and it is not the law. As the plan says, this
  decides nothing. The criteria of the campaign count exact fits by the
  same threshold as the bench, so such a fit would count there too. The
  campaign reports, for each exact fit of the two arcsine laws, whether its
  formula has the arcsine.

## 4. Tests: hold

- With A1, 177 tests pass, 8 of them new (`tests_a1.txt`).
- On the 1.2.0 wheel, 7 of the 8 new tests fail
  (`new_tests_on_1.2.0_wheel.txt`). The one that passes checks that every
  path of evaluation agrees. On 1.2.0 an unknown operator gives 0 on every
  path, so the paths agree there too.

## The options of the benches

`bench_options_check.txt`, from `bench_options_check.py`:
- **Without the new options,** `phase1_bench.py` and `tp_diagnostic.py`
  give the jobs of their versions at 496704b: 1,775 and 2,780 jobs for the
  bench, 400 for TP at draws 0 to 4 and at draws 5 to 9. Every filter of
  kinds and arms keeps the same jobs.
- **`--problems`** with the ten equations of the pool `trig` keeps the 200
  jobs of Dtrig.
- **`--experiments snell`** keeps the 40 jobs of TPsnell.
