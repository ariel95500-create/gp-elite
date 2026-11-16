# Physical units

Part of the documentation of GP_ELITE: back to the [README](../README.md); [version française](fr/unites.md).

## ⚖️ Dimensional constraints (physical laws only)

Declare the units of your inputs and target, and GP_ELITE will only search
expressions that are dimensionally sound — no more formulas that fit the numbers
while being physically meaningless.

```python
from gp_elite import GPEliteRegressor

est = GPEliteRegressor(
    units=["kg", "m/s"],      # units of X0, X1
    target_units="J",         # unit of the target
)
est.fit(X, y)
```

Units accept plain strings — SI bases (`m kg s A K mol cd`), common derived units
(`N J W Pa Hz C V ohm T`), and `* / ^ ( )`: `"m/s"`, `"kg*m/s^2"`, `"s^-1"`,
`"1"` for dimensionless. Dimension dicts (`{"m": 1, "s": -1}`) work too, as do
per-name (`{"X0": "kg"}`) and per-index (`{0: "kg"}`) forms. A malformed string
(`"m/(s"`, `"kg^"`, `"m garbage"`) raises an error instead of being guessed.

**Measured effect** — Feynman II.11.3, `x = q·Ef/(m·(w0²−w²))`, 5 variables,
5 seeds, 40 generations, identical budget for the first two arms:

| | no `units=` | `units=` | no `units=`, 4x generations |
|---|---:|---:|---:|
| dimensionally valid | 5 / 5 | 5 / 5 | 5 / 5 |
| exact law recovered (holds out of domain) | 5 / 5 | 5 / 5 | 5 / 5 |
| median test R² | 1.00000 | 1.00000 | 1.00000 |
| median out-of-domain R² | 1.00000 | 1.00000 | 1.00000 |
| median model size | 20 nodes | 20 nodes | 20 nodes |
| median seconds / run | 0 | 1 | 0 |

Since 1.0 this law is one of the forms the engine fits directly, a monomial times
a power of a binomial, and the fitted form is placed in the starting population.
Since 1.1 this holds under `units=` too, where a fitted form is placed only if it
passes the gate of dimensions every typed tree must pass: both searches return
the law in every run, in about a second. With 1.0, whose fitted forms did not act
under `units=`, the constrained search found it in two runs of five and ended the
other three on approximations (median of its five runs: 27 nodes, 27 s). Up to 0.9 the
unconstrained search returned no valid model on this law, even with four times the
generations: its models took the logarithm of a frequency, added kilograms or
hertz to pure numbers, or raised a quantity to an exponent in coulombs, and the
constraint was the only way to a valid answer. It still is for the laws the
engine does not fit directly. (Since 0.9 a typed generation costs 1.4 times an
untyped one, against 8.5 times with 0.8. With a budget set, as here, a search
stops early only on an exact law, so the runs that end on an approximation, and
every run on noisy data, go through all their generations; `time_limit=` bounds
them, and under the defaults, since 1.2, `patience=` does.)

**What it does *not* do.** On a test set drawn *outside* the training domain (w/w0
pushed from [0.20, 0.67] towards resonance at [0.70, 0.90]), the exact law holds
(R² = 1.00000) and approximations degrade: the three constrained runs of 1.0 that
ended on one had an out-of-domain R² of 0.32 to 0.65. Timings are from a 4-core
Linux machine, two runs at a time, with the islands in sequence
(`parallel=False`). Reproduce with `benchmarks/ab_ood.py`.

**When to use it.** To guarantee that whatever the engine returns is physically
meaningful, and to deduce the units and value of a constant (below, and the
[Kepler case study](https://github.com/ariel95500-create/gp-elite/blob/main/examples/case_studies/kepler_units.ipynb),
where the units also rule out a term the data alone would add). Since 1.1 the
forms the engine fits directly act under `units=` as well: on the 41 Feynman
equations of the decision bench with their units, five seeds at 30 s per fit,
165 exact laws of 205 against 108 with 1.0, and 163 without units. With the
arcsine of 1.3, 174 and 171, against 166 and 163 for 1.2 measured beside it;
1.4 keeps them, 174 and 171 in its release measurement.
**Not** for black-box prediction: the constraint rules out
dimensionally wrong but numerically good approximations, so it can *lower* R²
when fitting is the goal rather than finding a law.

**Laws with a dimensioned constant** (`unknown_constant=`). By default, fitted
constants are dimensionless — the AI Feynman convention — which puts a law like
Hooke's `F = k·x` out of reach: no dimensionless constant can relate metres to
newtons, and the search correctly reports that nothing valid can be built. Set
`unknown_constant=True` and the leading constant is allowed to *carry* a
dimension, deduced by homogeneity:

```python
est = GPEliteRegressor(units=["m"], target_units="N", unknown_constant=True)
est.fit(X, y)
est.constant_units_string()   # '[kg / s^2]'
est.constant_value_           # 250.0
```

The engine then reports not only the shape of the law but the **units and value
of the missing physical constant**. Measured on three reference laws:

| law | structure recovered | deduced units | value | true |
|---|---|---|---|---|
| Hooke `F = k·x` | yes | `kg / s²` | 250 | 250 |
| Newton `F = G·m₁·m₂/r²` | yes | `m³ / kg s²` | 6.674e-11 | 6.674e-11 |
| ideal gas `P = nRT/V` | yes | `kg m² / K mol s²` | 8.314462618 | 8.314462618 |

The returned formula itself carries the physical constant: the benchmark prints
`(249.99999999999997*X0)` for Hooke and `(8.314462617999999*((X0*X1)/X2))` for
the ideal gas.
Budget: 25 generations, two restarts.

Reproduce with `benchmarks/test_constante_mystere.py`. Requires `units=` and
`target_units=`. If the expression is not a monomial in the input columns
(`m₁ + m₂`, say), no single raw constant exists and `constant_value_` is `None`
while the deduced units remain valid.

**Limitation.** Under `units=` the internal linear scaling is multiplicative
only (no additive offset), which keeps every candidate dimensionally homogeneous.
