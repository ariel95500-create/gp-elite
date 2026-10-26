# -*- coding: utf-8 -*-
"""
Physical units of the 41 Feynman equations of the decision bench
=================================================================
The bench of phase 7 (`benchmarks/results_1.1/PLAN.md`) runs the decision
bench of `decision_bench.py` with `units=` and `target_units=`. This table
gives, for each of the 41 equations of `feynman_bench.PROBS`, the SI units of
each input column and of the target, written before any measurement of
phase 7.

Rules:
- The units are those of the formula the bench generates the data with
  (`feynman_bench.PROBS[i][4]`), which is sometimes simpler than the
  textbook law: I.44.4 takes the ratio V2/V1 as one dimensionless column,
  II.35.18 takes kb*T as one energy column, I.50.26 uses one column both as
  the frequency and as the coefficient alpha, III.9.52 replaces w0 by 1.
  Where the bench formula forces a column to be dimensionless, it is.
- Otherwise each column has the units of the physical quantity its name
  stands for in the Feynman lectures (SI base units kg, m, s, A, K).
- The first fifteen are those of `feynman_units.py`, copied here
  (`same_as_feynman_units()` below checks that they are the same).
- Every row is checked to be dimensionally homogeneous by the engine's own
  audit on the bench formula written as a tree (`check()` below).

    python3 benchmarks/units_table.py      # prints the table and the check
"""

# ── SI units ────────────────────────────────────────────────────────────────
NODIM = {}
KG = {"kg": 1}
M = {"m": 1}
M2 = {"m": 2}
M3 = {"m": 3}
PER_M = {"m": -1}
PER_M3 = {"m": -3}
PER_S = {"s": -1}
KELVIN = {"K": 1}
VEL = {"m": 1, "s": -1}
ACC = {"m": 1, "s": -2}
FORCE = {"kg": 1, "m": 1, "s": -2}
ENERGY = {"kg": 1, "m": 2, "s": -2}            # torque has the same units
POWER = {"kg": 1, "m": 2, "s": -3}
INTENSITY = {"kg": 1, "s": -3}                 # W/m²
MOMENTUM = {"kg": 1, "m": 1, "s": -1}
ACTION = {"kg": 1, "m": 2, "s": -1}            # Planck's constant
CHARGE = {"A": 1, "s": 1}
CHARGE_DENSITY = {"A": 1, "s": 1, "m": -3}
POLARIZATION = {"A": 1, "s": 1, "m": -2}
DIPOLE = {"A": 1, "s": 1, "m": 1}
EFIELD = {"kg": 1, "m": 1, "s": -3, "A": -1}   # V/m
BFIELD = {"kg": 1, "s": -2, "A": -1}           # tesla
EPS0 = {"A": 2, "s": 4, "kg": -1, "m": -3}     # permittivity
VOLT = {"kg": 1, "m": 2, "s": -3, "A": -1}
CAPACITANCE = {"A": 2, "s": 4, "kg": -1, "m": -2}
PRESSURE = {"kg": 1, "m": -1, "s": -2}
STIFFNESS = {"kg": 1, "s": -2}
MOBILITY = {"s": 1, "kg": -1}                  # makes v = mu*q*V/d homogeneous
MAGMOM = {"A": 1, "m": 2}
KB = {"kg": 1, "m": 2, "s": -2, "K": -1}       # Boltzmann's constant
THERMAL_COND = {"kg": 1, "m": 1, "s": -3, "K": -1}

# name -> (units of the input columns, in order; units of the target; note)
UNITS41 = {
    # ── the fifteen of feynman_units.py ──
    "I.12.1": ([NODIM, FORCE], FORCE, "friction coefficient, normal force"),
    "I.12.5": ([CHARGE, EFIELD], FORCE, ""),
    "I.14.4": ([STIFFNESS, M], ENERGY, ""),
    "I.39.1": ([PRESSURE, M3], ENERGY, ""),
    "II.3.24": ([POWER, M], INTENSITY, ""),
    "I.6.20a": ([NODIM], NODIM, ""),
    "I.8.14": ([M, M, M, M], M, ""),
    "I.16.6": ([VEL, VEL, VEL], VEL, ""),
    "I.27.6": ([M, M, NODIM], M, "two focal distances, refractive index"),
    "I.34.8": ([CHARGE, VEL, BFIELD, MOMENTUM], PER_S, ""),
    "I.43.16": ([MOBILITY, CHARGE, VOLT, M], VEL, ""),
    "I.12.2": ([CHARGE, CHARGE, EPS0, M], FORCE, ""),
    "II.15.4": ([MAGMOM, BFIELD, NODIM], ENERGY, ""),
    "I.18.12": ([M, FORCE, NODIM], ENERGY, ""),
    "III.15.12": ([ENERGY, PER_M, M], ENERGY, ""),
    # ── the twenty-six added in 0.8 ──
    "I.10.7": ([KG, VEL, VEL], KG, ""),
    "I.11.19": ([M, M, M, M, M, M], M2, "a dot product of two lengths"),
    "I.15.10": ([KG, VEL, VEL], MOMENTUM, ""),
    "I.25.13": ([CHARGE, CAPACITANCE], VOLT, ""),
    "I.26.2": ([NODIM, NODIM], NODIM, "refractive index, angle"),
    "I.29.4": ([PER_S, VEL], PER_M, ""),
    "I.30.5": ([M, NODIM, M], NODIM, "wavelength, number of slits, spacing"),
    "I.32.5": ([CHARGE, ACC, EPS0, VEL], POWER, ""),
    "I.34.1": ([PER_S, VEL, VEL], PER_S, ""),
    "I.37.4": ([INTENSITY, INTENSITY, NODIM], INTENSITY, ""),
    "I.40.1": ([PER_M3, KG, ACC, M, KB, KELVIN], PER_M3, ""),
    "I.44.4": ([NODIM, KB, KELVIN, NODIM], ENERGY,
               "number of particles; the bench takes V2/V1 as one column"),
    "I.50.26": ([M, NODIM, NODIM], M,
                "the bench uses one column as w and as alpha: both "
                "dimensionless"),
    "II.2.42": ([THERMAL_COND, KELVIN, KELVIN, M2, M], POWER, ""),
    "II.6.15b": ([DIPOLE, NODIM, EPS0, M], EFIELD, ""),
    "II.11.3": ([CHARGE, EFIELD, KG, PER_S, PER_S], M, ""),
    "II.11.27": ([PER_M3, M3, EPS0, EFIELD], POLARIZATION,
                 "number density, polarizability (a volume)"),
    "II.13.23": ([CHARGE_DENSITY, VEL, VEL], CHARGE_DENSITY, ""),
    "II.24.17": ([PER_S, VEL, M], PER_M, ""),
    "II.34.2": ([CHARGE, VEL, M], MAGMOM, ""),
    "II.35.18": ([PER_M3, MAGMOM, BFIELD, ENERGY], PER_M3,
                 "the bench takes kb*T as one column"),
    "II.38.3": ([PRESSURE, M2, M, M], FORCE, "Young's modulus"),
    "III.9.52": ([DIPOLE, EFIELD, NODIM, ACTION, NODIM], PER_S,
                 "the bench replaces w0 by 1: w and t dimensionless"),
    "III.10.19": ([MAGMOM, BFIELD, BFIELD, BFIELD], ENERGY, ""),
    "III.17.37": ([NODIM, NODIM, NODIM], NODIM,
                  "beta, alpha and the angle, dimensionless in the lectures"),
    "III.19.51": ([KG, CHARGE, EPS0, ACTION, NODIM], ENERGY,
                  "n the principal quantum number"),
}


def units_of(name, names):
    """units= and target_units= for equation `name`, the columns named
    `names` (as in decision_bench.feyn_data)."""
    feats, target, _note = UNITS41[name]
    if len(feats) != len(names):
        raise ValueError("%s: %d units for %d columns"
                         % (name, len(feats), len(names)))
    return ({n: dict(u) for n, u in zip(names, feats)}, dict(target))


# The bench formulas written as trees over x0, x1, ... in the engine's syntax,
# for the check below only (the data are generated by feynman_bench.PROBS).
TREES = {
    "I.12.1": "x0*x1", "I.12.5": "x0*x1", "I.14.4": "x0*x1*x1",
    "I.39.1": "x0*x1", "II.3.24": "x0/(x1*x1)", "I.6.20a": "exp(x0*x0)",
    "I.8.14": "sqrt((x1-x0)*(x1-x0)+(x3-x2)*(x3-x2))",
    "I.16.6": "(x0+x1)/(1+x0*x1/(x2*x2))", "I.27.6": "1/(1/x0+x2/x1)",
    "I.34.8": "x0*x1*x2/x3", "I.43.16": "x0*x1*x2/x3",
    "I.12.2": "x0*x1/(x2*x3*x3)", "II.15.4": "x0*x1*cos(x2)",
    "I.18.12": "x0*x1*sin(x2)", "III.15.12": "x0*(1-cos(x1*x2))",
    "I.10.7": "x0/sqrt(1-x1*x1/(x2*x2))", "I.11.19": "x0*x1+x2*x3+x4*x5",
    "I.15.10": "x0*x1/sqrt(1-x1*x1/(x2*x2))", "I.25.13": "x0/x1",
    "I.26.2": "x0*sin(x1)", "I.29.4": "x0/x1", "I.30.5": "x0/(x1*x2)",
    "I.32.5": "x0*x0*x1*x1/(x2*x3*x3*x3)", "I.34.1": "x0/(1-x1/x2)",
    "I.37.4": "x0+x1+sqrt(x0*x1)*cos(x2)",
    "I.40.1": "x0*exp(x1*x2*x3/(x4*x5))", "I.44.4": "x0*x1*x2*log(x3)",
    "I.50.26": "x0*(cos(x1*x2)+x1*cos(x1*x2)*cos(x1*x2))",
    "II.2.42": "x0*(x1-x2)*x3/x4", "II.6.15b": "x0*cos(x1)*sin(x1)/(x2*x3*x3*x3)",
    "II.11.3": "x0*x1/(x2*(x3*x3-x4*x4))",
    "II.11.27": "x0*x1*x2*x3/(1-x0*x1)",
    "II.13.23": "x0/sqrt(1-x1*x1/(x2*x2))",
    "II.24.17": "sqrt(x0*x0/(x1*x1)-1/(x2*x2))", "II.34.2": "x0*x1*x2",
    "II.35.18": "x0/(exp(x1*x2/x3)+exp(x1*x2/x3))", "II.38.3": "x0*x1*x2/x3",
    "III.9.52": "x0*x1*x2/x3*sin((x4-1)*x2)*sin((x4-1)*x2)",
    "III.10.19": "x0*sqrt(x1*x1+x2*x2+x3*x3)", "III.17.37": "x0*(1+x1*cos(x2))",
    "III.19.51": "x0*x1*x1*x1*x1/(x2*x2*x3*x3*x4*x4)",
}
# I.26.2 and I.30.5 are arcsines in the bench; the check takes their argument,
# which must be dimensionless, with a dimensionless target.


def _tree(text):
    """The engine's Node tree of `text` (x0, x1, ... become X[0], X[1], ...;
    + - * / and sin, cos, exp, log, sqrt)."""
    import ast
    from gp_elite.core import Node
    ops = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}

    def conv(n):
        if isinstance(n, ast.Expression):
            return conv(n.body)
        if isinstance(n, ast.BinOp):
            return Node(ops[type(n.op)], conv(n.left), conv(n.right))
        if isinstance(n, ast.Call):
            return Node(n.func.id, conv(n.args[0]))
        if isinstance(n, ast.Name):
            return Node("X[%d]" % int(n.id[1:]))
        if isinstance(n, ast.Constant):
            return Node(float(n.value))
        raise ValueError(ast.dump(n))
    return conv(ast.parse(text, mode="eval"))


def check():
    """Every row homogeneous by gp_elite.dim_search.is_typed_valid on the
    bench formula; returns the names that fail."""
    import os
    import sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.isdir(os.path.join(root, "gp_elite")):
        sys.path.insert(0, root)
    from gp_elite.dim_search import is_typed_valid
    bad = []
    for name, (feats, target, _n) in UNITS41.items():
        tree = _tree(TREES[name])
        fd = {k: u for k, u in enumerate(feats)}
        if not is_typed_valid(tree, fd, target):
            bad.append(name)
    return bad


def same_as_feynman_units():
    """The names of the fifteen rows of feynman_units.py that differ here."""
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    argv, sys.argv = sys.argv, sys.argv[:1]
    try:
        import feynman_units as FU
    finally:
        sys.argv = argv
    return [p[0] for p in FU.PROBS
            if (list(p[6]), p[7]) != (UNITS41[p[0]][0], UNITS41[p[0]][1])]


if __name__ == "__main__":
    for name, (feats, target, note) in UNITS41.items():
        print("%-10s %-60s -> %-28s %s" % (name, feats, target, note))
    bad = check()
    print("\n%d equations, %d not homogeneous%s"
          % (len(UNITS41), len(bad), (": " + ", ".join(bad)) if bad else ""))
    diff = same_as_feynman_units()
    print("rows of feynman_units.py that differ: %s" % (", ".join(diff) or "none"))
