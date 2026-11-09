# A3, the arcsine of a monomial among the seeds: the mechanics

Run on 9 November 2026, before any fit of campaign A3
(`../PLAN.md`, *Change A3*).

- **Engine:** A1, A2 and A3, commit 492863e.
- **Environments:**
  - B, the candidate, in `/venv13c`. Its wheel was built from 492863e
    (sha256 `703db7b1…aa36`) and installed with the packages of `/venv12p`.
    The two `pip freeze` differ only in the line of gp-elite;
  - A, the 1.2.0 wheel. Its records are those of A1's mechanics, on the same
    machine (`machine.txt`, the same as `../a1/machine.txt`).

## 1. The pools without the arcsine are untouched: holds

- **The reference configurations** (`compare_1.2.0_vs_a3_equiv.txt`): the
  eleven of the pool `physical` are identical to the 1.2.0 wheel. E_minmax
  and L_standard change, as with A1 and A2.
- **The 147 fits** are identical in every field (`compare_mechanics_1.txt`).

## 2. The finder: holds

`tests/test_arcsin.py` (`tests_a3.txt`):
- **On y = 2·arcsin(0.7·x0/(x1·x2)),** it returns the arcsine form with
  f = 1, the exponents of g (1, −1, −1), and c = 0.7. Without the arcsine
  among its kinds, it returns nothing.
- **It returns no arcsine** on arcsin(x0·sin(x1)), on data with no such
  form, or on an arcsine law with 1 % noise.
- **tanh and exp** are found as before.
- **The arcsine seed is placed with the pool `trig`,** and fits the law
  after linear scaling to 1e-20. With the pool `physical` it is not placed.

**One test needed other data,** and that is not a change: on inputs from
1 to 5, tanh(0.3·x0·x1) saturates, and 1.2.0 finds no form there either.
The test of tanh uses the inputs of the first test.

## 3. I.30.5 on the bench rows: holds

`I.30.5_seed0.txt`: pool `trig`, seed 0, 30 s, with the wheel of `/venv13c`.
- The seed placed is `arcsin((0.080928 * (v0 / (v1 * v2))))`.
- The fit returns `arcsin(v0 / (v1 * v2))`, with 1 − R² of 3.9e-27 on the
  test rows, and `formula_exact` True.

## 4. Tests: hold

182 pass, 3 of them new (`tests_a3.txt`).

## The records of the bench

For the report of campaign A3, every record of `phase1_bench.py` now also
carries the seeds of phases 4a and 5 that the fit placed (`elementary_seed`,
`tolerant_seed`). On two fits bounded by 20 generations, every other field
is the same as with the bench of 492863e (`record_fields_check.txt`).
