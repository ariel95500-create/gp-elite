# Examples

Part of the documentation of GP_ELITE: back to the [README](../README.md); [version française](fr/exemples.md).

## Example on simulated battery-ageing data

```bash
python examples/battery_soh.py
```

The file [`examples/nasa_battery_simulation.csv`](https://github.com/ariel95500-create/gp-elite/blob/main/examples/nasa_battery_simulation.csv)
holds 168 **simulated** charge cycles (cycle number, temperature, current, capacity
state of health). Its origin is not documented beyond its name, so treat this as a
demonstration of the workflow, not as a result on real batteries. On it, the script
prints (abridged):

```
PROTOCOL 1 — random split (INTERPOLATION, leaks info)
  GP_ELITE      R² = +0.992
  RandomForest  R² = +0.997
  XGBoost       R² = +0.997

PROTOCOL 2 — forward split (EXTRAPOLATION): train on cycles 1..142, predict 143..168
  RandomForest (300)      R² = -2.521
  XGBoost (300 trees)     R² = -2.324
  GP_ELITE (one equation) R² = -3.812

  Equation: SOH = 0.349119 - 0.223995 * ((0.00704225 * cycle)^(0.51573 * courant) - exp(courant / 1.939))
```

A random split of sequential data is interpolation and flatters every method. On the
forward split, the tree ensembles can only repeat values seen in training and fall far
below the mean. The equation 1.4 returns, with a power of the cycle, does
worse still (R² −3.81): its new seeds took the search on noisy data to another
formula (`benchmarks/results_1.4/release/`). The one 1.0 to 1.3 returned (1.2
writes its exponential with its scale), in the current and the cycle, did
better than the tree ensembles, but not well (R² +0.16); 0.8 and 0.9 returned
one at R² −0.31, below the mean too, and 0.7 one in the cycle and the current
that kept following the trend (R² +0.594). A formula can extrapolate where a
tree ensemble cannot; whether it does depends on which formula the search returns —
on this simulated set, to be checked on yours.


## Case studies on public data

Three [case studies on public data](https://github.com/ariel95500-create/gp-elite/tree/main/examples/case_studies)
(Kepler's law with units, Hubble's measurements of 1929, Nikuradse's pipes) show what
it returns on public data and what it does not find, and
[what GP_ELITE does not do](https://github.com/ariel95500-create/gp-elite/blob/main/LIMITATIONS.md)
lists its known limits, each with the measurement behind it.
