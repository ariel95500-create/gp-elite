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


# ── the frozen test set (TF78), written before campaign U1 runs ─────────────
# Same rules as above, on the formula of each dataset in test_set/MANIFEST.json
# (the PMLB Feynman datasets, with their physical constants as columns).
# Column names as in the manifest; units_of_tf() gives them for the columns
# v0, v1, ... of test_set.tf_data. Every one of the 78 is homogeneous; none is
# left out.
ACCEL = ACC
CURRENT = {"A": 1}
CURRENT_DENSITY = {"A": 1, "m": -2}
SURFACE_CHARGE = {"A": 1, "s": 1, "m": -2}
MAGNETIZATION = {"A": 1, "m": -1}
VECTOR_POT = {"kg": 1, "m": 1, "s": -2, "A": -1}     # T·m
GRAV = {"m": 3, "kg": -1, "s": -2}                    # G
DENSITY = {"kg": 1, "m": -3}
DIFFUSIVITY = {"m": 2, "s": -1}
RADIANCE = {"kg": 1, "s": -2}                         # of I.41.16
KGRAV = {"kg": 1, "m": 3, "s": -2}                    # k_G = G·M·m
ENERGY_DENSITY = {"kg": 1, "m": -1, "s": -2}

UNITS_TF78 = {
    "III_12_43": ({"n": NODIM, "h": ACTION}, ACTION, ""),
    "III_13_18": ({"E_n": ENERGY, "d": M, "k": PER_M, "h": ACTION}, VEL, ""),
    "III_14_14": ({"I_0": CURRENT, "q": CHARGE, "Volt": VOLT, "kb": KB,
                   "T": KELVIN}, CURRENT, ""),
    "III_15_14": ({"h": ACTION, "E_n": ENERGY, "d": M}, KG, ""),
    "III_15_27": ({"alpha": NODIM, "n": NODIM, "d": M}, PER_M, ""),
    "III_21_20": ({"rho_c_0": CHARGE_DENSITY, "q": CHARGE,
                   "A_vec": VECTOR_POT, "m": KG}, CURRENT_DENSITY, ""),
    "III_4_32": ({"h": ACTION, "omega": PER_S, "kb": KB, "T": KELVIN},
                 NODIM, ""),
    "III_4_33": ({"h": ACTION, "omega": PER_S, "kb": KB, "T": KELVIN},
                 ENERGY, ""),
    "III_7_38": ({"mom": MAGMOM, "B": BFIELD, "h": ACTION}, PER_S, ""),
    "III_8_54": ({"E_n": ENERGY, "t": {"s": 1}, "h": ACTION}, NODIM, ""),
    "II_10_9": ({"sigma_den": SURFACE_CHARGE, "epsilon": EPS0, "chi": NODIM},
                EFIELD, ""),
    "II_11_20": ({"n_rho": PER_M3, "p_d": DIPOLE, "Ef": EFIELD, "kb": KB,
                  "T": KELVIN}, POLARIZATION, ""),
    "II_11_28": ({"n": PER_M3, "alpha": M3}, NODIM, ""),
    "II_13_17": ({"epsilon": EPS0, "c": VEL, "I": CURRENT, "r": M}, BFIELD,
                 ""),
    "II_13_34": ({"rho_c_0": CHARGE_DENSITY, "v": VEL, "c": VEL},
                 CURRENT_DENSITY, ""),
    "II_15_5": ({"p_d": DIPOLE, "Ef": EFIELD, "theta": NODIM}, ENERGY, ""),
    "II_21_32": ({"q": CHARGE, "epsilon": EPS0, "r": M, "v": VEL, "c": VEL},
                 VOLT, ""),
    "II_27_16": ({"epsilon": EPS0, "c": VEL, "Ef": EFIELD}, INTENSITY, ""),
    "II_27_18": ({"epsilon": EPS0, "Ef": EFIELD}, ENERGY_DENSITY, ""),
    "II_34_11": ({"g_": NODIM, "q": CHARGE, "B": BFIELD, "m": KG}, PER_S, ""),
    "II_34_29a": ({"q": CHARGE, "h": ACTION, "m": KG}, MAGMOM, ""),
    "II_34_29b": ({"g_": NODIM, "h": ACTION, "Jz": ACTION, "mom": MAGMOM,
                   "B": BFIELD}, ENERGY, "Jz an angular momentum"),
    "II_34_2a": ({"q": CHARGE, "v": VEL, "r": M}, CURRENT, ""),
    "II_35_21": ({"n_rho": PER_M3, "mom": MAGMOM, "B": BFIELD, "kb": KB,
                  "T": KELVIN}, MAGNETIZATION, ""),
    "II_36_38": ({"mom": MAGMOM, "H": BFIELD, "kb": KB, "T": KELVIN,
                  "alpha": NODIM, "epsilon": EPS0, "c": VEL,
                  "M": MAGNETIZATION}, NODIM,
                 "H in tesla, as mom*H/(kb*T) is dimensionless"),
    "II_37_1": ({"mom": MAGMOM, "B": BFIELD, "chi": NODIM}, ENERGY, ""),
    "II_38_14": ({"Y": PRESSURE, "sigma": NODIM}, PRESSURE,
                 "Young's modulus, Poisson's ratio"),
    "II_4_23": ({"q": CHARGE, "epsilon": EPS0, "r": M}, VOLT, ""),
    "II_6_11": ({"epsilon": EPS0, "p_d": DIPOLE, "theta": NODIM, "r": M},
                VOLT, ""),
    "II_6_15a": ({"epsilon": EPS0, "p_d": DIPOLE, "r": M, "x": M, "y": M,
                  "z": M}, EFIELD, ""),
    "II_8_31": ({"epsilon": EPS0, "Ef": EFIELD}, ENERGY_DENSITY, ""),
    "II_8_7": ({"q": CHARGE, "epsilon": EPS0, "d": M}, ENERGY, ""),
    "I_12_11": ({"q": CHARGE, "Ef": EFIELD, "B": BFIELD, "v": VEL,
                 "theta": NODIM}, FORCE, ""),
    "I_12_4": ({"q1": CHARGE, "epsilon": EPS0, "r": M}, EFIELD, ""),
    "I_13_12": ({"m1": KG, "m2": KG, "r1": M, "r2": M, "G": GRAV}, ENERGY,
                ""),
    "I_13_4": ({"m": KG, "v": VEL, "u": VEL, "w": VEL}, ENERGY, ""),
    "I_14_3": ({"m": KG, "g": ACCEL, "z": M}, ENERGY, ""),
    "I_15_3t": ({"x": M, "c": VEL, "u": VEL, "t": {"s": 1}}, {"s": 1}, ""),
    "I_15_3x": ({"x": M, "u": VEL, "c": VEL, "t": {"s": 1}}, M, ""),
    "I_18_14": ({"m": KG, "r": M, "v": VEL, "theta": NODIM}, ACTION, ""),
    "I_18_4": ({"m1": KG, "m2": KG, "r1": M, "r2": M}, M, ""),
    "I_24_6": ({"m": KG, "omega": PER_S, "omega_0": PER_S, "x": M}, ENERGY,
               ""),
    "I_29_16": ({"x1": M, "x2": M, "theta1": NODIM, "theta2": NODIM}, M, ""),
    "I_30_3": ({"Int_0": INTENSITY, "theta": NODIM, "n": NODIM}, INTENSITY,
               ""),
    "I_32_17": ({"epsilon": EPS0, "c": VEL, "Ef": EFIELD, "r": M,
                 "omega": PER_S, "omega_0": PER_S}, POWER, ""),
    "I_34_14": ({"c": VEL, "v": VEL, "omega_0": PER_S}, PER_S, ""),
    "I_34_27": ({"omega": PER_S, "h": ACTION}, ENERGY, ""),
    "I_38_12": ({"m": KG, "q": CHARGE, "h": ACTION, "epsilon": EPS0}, M, ""),
    "I_39_11": ({"gamma": NODIM, "pr": PRESSURE, "V": M3}, ENERGY, ""),
    "I_39_22": ({"n": NODIM, "T": KELVIN, "V": M3, "kb": KB}, PRESSURE,
                "n a number of particles"),
    "I_41_16": ({"omega": PER_S, "T": KELVIN, "h": ACTION, "kb": KB,
                 "c": VEL}, RADIANCE, ""),
    "I_43_31": ({"mob": MOBILITY, "T": KELVIN, "kb": KB}, DIFFUSIVITY, ""),
    "I_43_43": ({"gamma": NODIM, "kb": KB, "A": M2, "v": VEL}, THERMAL_COND,
                "A an area"),
    "I_47_23": ({"gamma": NODIM, "pr": PRESSURE, "rho": DENSITY}, VEL, ""),
    "I_48_2": ({"m": KG, "v": VEL, "c": VEL}, ENERGY, ""),
    "I_6_2": ({"sigma": NODIM, "theta": NODIM}, NODIM, ""),
    "I_6_2b": ({"sigma": NODIM, "theta": NODIM, "theta1": NODIM}, NODIM, ""),
    "I_9_18": ({"m1": KG, "m2": KG, "G": GRAV, "x1": M, "x2": M, "y1": M,
                "y2": M, "z1": M, "z2": M}, FORCE, ""),
    "test_1": ({"Z_1": NODIM, "Z_2": NODIM, "alpha": NODIM, "hbar": ACTION,
                "c": VEL, "E_n": ENERGY, "theta": NODIM}, M2,
               "a cross-section"),
    "test_10": ({"c": VEL, "v": VEL, "theta2": NODIM}, NODIM, ""),
    "test_11": ({"I_0": INTENSITY, "alpha": NODIM, "delta": NODIM,
                 "n": NODIM}, INTENSITY, ""),
    "test_12": ({"q": CHARGE, "y": M, "Volt": VOLT, "d": M,
                 "epsilon": EPS0}, FORCE, ""),
    "test_13": ({"q": CHARGE, "r": M, "d": M, "alpha": NODIM,
                 "epsilon": EPS0}, VOLT, ""),
    "test_14": ({"Ef": EFIELD, "theta": NODIM, "r": M, "d": M,
                 "alpha": NODIM}, VOLT, "alpha a ratio of permittivities"),
    "test_15": ({"c": VEL, "v": VEL, "omega": PER_S, "theta": NODIM}, PER_S,
                ""),
    "test_16": ({"m": KG, "c": VEL, "p": MOMENTUM, "q": CHARGE,
                 "A_vec": VECTOR_POT, "Volt": VOLT}, ENERGY, ""),
    "test_17": ({"m": KG, "omega": PER_S, "p": MOMENTUM, "y": M, "x": M,
                 "alpha": NODIM}, ENERGY, ""),
    "test_18": ({"G": GRAV, "k_f": NODIM, "r": M, "H_G": PER_S, "c": VEL},
                DENSITY, ""),
    "test_19": ({"G": GRAV, "k_f": NODIM, "r": M, "H_G": PER_S,
                 "alpha": NODIM, "c": VEL}, PRESSURE, ""),
    "test_2": ({"m": KG, "k_G": KGRAV, "L": ACTION, "E_n": ENERGY,
                "theta1": NODIM, "theta2": NODIM}, PER_M,
               "k_G = G*M*m, L an angular momentum"),
    "test_20": ({"omega": PER_S, "omega_0": PER_S, "alpha": NODIM,
                 "h": ACTION, "m": KG, "c": VEL, "beta": NODIM}, M2,
                "a cross-section"),
    "test_3": ({"d": M, "alpha": NODIM, "theta1": NODIM, "theta2": NODIM},
               M, ""),
    "test_4": ({"m": KG, "E_n": ENERGY, "U": ENERGY, "L": ACTION, "r": M},
               VEL, "L an angular momentum"),
    "test_5": ({"d": M, "G": GRAV, "m1": KG, "m2": KG}, {"s": 1}, ""),
    "test_6": ({"epsilon": EPS0, "L": ACTION, "m": KG, "Z_1": NODIM,
                "Z_2": NODIM, "q": CHARGE, "E_n": ENERGY}, NODIM,
               "L an angular momentum"),
    "test_7": ({"G": GRAV, "rho": DENSITY, "alpha": NODIM, "c": VEL, "d": M},
               PER_S, ""),
    "test_8": ({"E_n": ENERGY, "m": KG, "c": VEL, "theta": NODIM}, ENERGY,
               ""),
    "test_9": ({"G": GRAV, "c": VEL, "m1": KG, "m2": KG, "r": M}, POWER, ""),
}


def units_of_tf(dataset, names):
    """units= and target_units= for the TF78 dataset `dataset` (name as in
    the manifest, with or without "feynman_"), its columns named `names`
    (v0, v1, ... in test_set.tf_data)."""
    import json
    import os
    key = dataset[len("feynman_"):] if dataset.startswith("feynman_") \
        else dataset
    cols, target, _note = UNITS_TF78[key]
    man = json.load(open(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "test_set", "MANIFEST.json")))
    order = man["datasets"]["feynman_" + key]["columns"]
    if len(order) != len(names) or set(order) != set(cols):
        raise ValueError("%s: columns %s, table %s" % (key, order, sorted(cols)))
    return ({n: dict(cols[c]) for n, c in zip(names, order)}, dict(target))


def _formula_tree(text, columns):
    """The engine's tree of a manifest formula (right-hand side), its
    columns mapped to X[0], X[1], ... in manifest order."""
    import ast
    import math
    from gp_elite.core import Node
    ops = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}
    funcs = {"exp": "exp", "sin": "sin", "cos": "cos", "tanh": "tanh",
             "sqrt": "sqrt", "arccos": "cos", "arcsin": "sin"}  # same rule

    def num(n):
        if isinstance(n, ast.Constant):
            return float(n.value)
        if isinstance(n, ast.BinOp) and type(n.op) in ops:
            a, b = num(n.left), num(n.right)
            return {"+": a + b, "-": a - b, "*": a * b, "/": a / b}[ops[type(n.op)]]
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -num(n.operand)
        raise ValueError("exponent %s" % ast.dump(n))

    def conv(n):
        if isinstance(n, ast.Expression):
            return conv(n.body)
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Pow):
            return Node("pow", conv(n.left), Node(num(n.right)))
        if isinstance(n, ast.BinOp):
            return Node(ops[type(n.op)], conv(n.left), conv(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return Node("neg", conv(n.operand))
        if isinstance(n, ast.Call):
            return Node(funcs[n.func.id], conv(n.args[0]))
        if isinstance(n, ast.Name):
            if n.id == "pi":
                return Node(math.pi)
            return Node("X[%d]" % columns.index(n.id))
        if isinstance(n, ast.Constant):
            return Node(float(n.value))
        raise ValueError(ast.dump(n))
    return conv(ast.parse(text.split("=", 1)[1].strip(), mode="eval"))


def check_tf78():
    """Every TF78 row homogeneous by is_typed_valid on the manifest formula;
    returns (names that fail, names of the manifest missing here)."""
    import json
    import os
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    if os.path.isdir(os.path.join(root, "gp_elite")):
        sys.path.insert(0, root)
    from gp_elite.dim_search import is_typed_valid
    man = json.load(open(os.path.join(here, "test_set", "MANIFEST.json")))
    tf = {k[len("feynman_"):]: v for k, v in man["datasets"].items()
          if v["group"] == "TF78"}
    missing = sorted(set(tf) - set(UNITS_TF78))
    bad = []
    for key, (cols, target, _n) in UNITS_TF78.items():
        order = tf[key]["columns"]
        tree = _formula_tree(tf[key]["formula"], order)
        fd = {k: cols[c] for k, c in enumerate(order)}
        if set(order) != set(cols) or not is_typed_valid(tree, fd, target):
            bad.append(key)
    return bad, missing


if __name__ == "__main__":
    for name, (feats, target, note) in UNITS41.items():
        print("%-10s %-60s -> %-28s %s" % (name, feats, target, note))
    bad = check()
    print("\n%d equations, %d not homogeneous%s"
          % (len(UNITS41), len(bad), (": " + ", ".join(bad)) if bad else ""))
    diff = same_as_feynman_units()
    print("rows of feynman_units.py that differ: %s" % (", ".join(diff) or "none"))
    bad, missing = check_tf78()
    print("TF78: %d equations, %d not homogeneous%s, %d missing%s"
          % (len(UNITS_TF78), len(bad), (": " + ", ".join(bad)) if bad else "",
             len(missing), (": " + ", ".join(missing)) if missing else ""))
