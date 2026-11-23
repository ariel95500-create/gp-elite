# Robust regression

Part of the documentation of GP_ELITE: back to the [README](../README.md); [version française](fr/robuste.md).

## 🛡️ Robust regression (outlier-resistant custom loss)

Real-world data is dirty. A handful of outliers can drag an ordinary least-squares fit far from the true relationship. GP_ELITE ships a one-switch **robust mode** meant to follow the bulk of the data rather than a few extreme points.

```python
result = symbolic_regression(X, y, feature_names=["x"], robust=True)
```

Under the hood, `robust=True` switches the objective to a **Huber loss** and rescales the final coefficients with an **IRLS (Iteratively Reweighted Least Squares)** procedure. It stays a compact, readable formula.

**Measured behaviour** (recovering `y = 2x + 1`; RMSE against the *true* law on the clean points, lower is better; five seeds, median and worst seed):

| outliers | default (MSE) | `robust=True` |
|---------:|--------------:|--------------:|
|      0 % |   0.063 [0.063] |   0.063 [0.063] |
|     10 % |   1.398 [1.398] | **0.237** [0.237] |
|     20 % |   1.925 [1.925] |   1.925 [1.925] |

On clean data the two modes return slightly different lines, equally close to the true
law. With 10 % outliers, robust mode cuts the error six-fold. With 20 %, on this
example, it does no better than the default: the default returns the same line for all
five seeds, pulled by the outliers (`y = 4.23319 + 1.32825 * x`), and robust mode the same
line for four seeds out of five. Robustness is a tool to try when you suspect outliers,
not a guarantee — compare both modes on data of your own.
(Up to 0.6 this table reported the best of three runs, picked by comparing with the
true law, which no user can do.)

Reproduce: `python examples/robust_regression.py`.
