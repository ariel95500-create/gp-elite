# A2, the arcsine with its own constant: the mechanics

Run on 9 November 2026, before any fit of campaign A2
(`../PLAN.md`, *Change A2*).

- **Engine:** A1 and A2, commit c6f8668.
- **Environments:**
  - B, the candidate, in `/venv13b`. Its wheel was built from c6f8668
    (sha256 `0b815b07…ed6a`) and installed with the packages of `/venv12p`.
    The two `pip freeze` differ only in the line of gp-elite;
  - A, the 1.2.0 wheel in `/venv12p`. Its records are those of A1's
    mechanics, `../a1/`, run on the same machine the same day
    (`machine.txt` is the same as `../a1/machine.txt`).

## 1. The pools without the arcsine are untouched: holds

- **The reference configurations** (`compare_1.2.0_vs_a2_equiv.txt`): the
  eleven of the pool `physical` are identical to the 1.2.0 wheel. E_minmax
  and L_standard change, as with A1, and have no arcsine
  (`equiv_changed.txt`).
- **The 147 fits** of A1's mechanics are identical in every field
  (`compare_mechanics_1.txt`).

## 2. The rule: holds

`tests/test_arcsin.py` (`tests_a2.txt`):
- arcsin(X0) becomes arcsin(1 · X0);
- arcsin(2 · X0), arcsin(X0 · 3) and arcsin(2 / X0) stay as they are;
- arcsin(X0 · sin(X1)) becomes arcsin(1 · (X0 · sin(X1)));
- simplifying twice gives the same tree;
- arcsin(0.5) still folds to 0.5235987755982989;
- sin(X0) is not touched;
- the eight tests of A1 still pass.

## 3. The form of the examination: holds

`form_of_the_examination.txt`, on the training rows of I.26.2 in the
engine's variables (each column divided by its largest value). The tree is
−0.000573 + 0.982939 · arcsin(X0 · sin(4.964236 · X1)), simplified then
polished by the engine's own steps:
- **with A1 alone:** 1 − R² of 8.1e-4 on the test rows, near;
- **with A2:** 4.3e-31. The fitted factor is 0.988241, the largest value of
  n on these rows, so the formula is the law.

The test `test_the_form_of_the_examination_comes_back_exact` checks the same
on data drawn in the same box.

## 4. Tests: hold

179 pass, 2 of them new (`tests_a2.txt`).
