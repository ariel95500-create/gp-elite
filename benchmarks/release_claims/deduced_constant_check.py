"""The correction of the deduced constant (CHANGELOG 1.0.0, Fixed), measured on
both versions: the same typed fits (the typed search is the same in 0.9.0 and
1.0.0, M1 of PLAN_RELEASE_1.0.md), the constant each version reports, and the
coefficient the law has on the data (median of predict(X) / X^1.5).

  PYTHONHASHSEED=0 python benchmarks/release_claims/deduced_constant_check.py

Run once with the interpreter of 0.9.0 and once with that of 1.0.0.
"""
import io
import os
import warnings
from contextlib import redirect_stdout

import numpy as np
import pandas as pd

import gp_elite
from gp_elite import GPEliteRegressor

warnings.simplefilter("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "examples", "case_studies", "data",
                    "planets_simon1994.csv")
AU, YEAR = 149597870700.0, 365.25 * 86400.0

# The table of the README and quickstart (au, years), and that of the case study.
readme_a = np.array([0.387, 0.723, 1.000, 1.524, 5.203, 9.537, 19.191, 30.069]) * AU
readme_T = np.array([0.241, 0.615, 1.000, 1.881, 11.862, 29.457, 84.011, 164.79]) * YEAR
df = pd.read_csv(DATA, comment="#")
case_a = df["a_au"].to_numpy() * AU
case_T = 1296000000.0 / df["mean_motion"].to_numpy() * YEAR

print("gp_elite", gp_elite.__version__, gp_elite.__file__)
for label, a, T, seeds in (("README table, 8 planets", readme_a, readme_T, (0, 1)),
                           ("case study, Mercury to Mars", case_a[:4], case_T[:4],
                            range(5))):
    for s in seeds:
        est = GPEliteRegressor(units=["m"], target_units="s", unknown_constant=True,
                               generations=30, speed="fast", random_state=s,
                               parallel=False)
        with redirect_stdout(io.StringIO()):
            est.fit(a.reshape(-1, 1), T)
        coef = float(np.median(est.predict(a.reshape(-1, 1)) / a ** 1.5))
        c = est.constant_value_
        print("%-28s seed %d  %s\n    reported %r %s   coefficient on the data %.6e   "
              "reported / coefficient - 1 = %s" % (
                  label, s, est.equation_, c, est.constant_units_string(), coef,
                  "%.2e" % (c / coef - 1) if c else "-"))
