"""[v0.3] Structural stability under resampling.

The launch feedback kept circling one honest weakness: on noisy data a
symbolic regressor can return a formula that fits well but is essentially
arbitrary — resample the data and you get a different equation. Rather than
pretend that away, this measures it.

`stability_analysis` runs the search on many bootstrap resamples of the data
and reports how often each *structural form* (constants ignored) comes back.
A law that reappears in 90% of resamples is a real signal; one that shows up
in 8% is the model reading noise. It turns "trust me" into a number.

This is the trust-first counterpart to the accuracy metrics: it does not make
recovery more robust, it tells you how robust it actually was.
"""
from collections import Counter
import numpy as np

from . import core
from .api import symbolic_regression


def _canonical_form(node):
    """A readable label for a structural class, built by walking the tree so
    there's no ambiguity: numeric *constants* become 'C', variables keep their
    identity (X0, X1, ...), operators stay as-is. Two fits differing only in
    fitted constants share a label; different variables or structure do not."""
    def walk(nd):
        if nd is None:
            return ""
        # leaf
        if nd.left is None and nd.right is None:
            v = nd.value
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return "C"
            return str(v)            # variable token, e.g. 'X[0]' or a name
        if nd.right is None:         # unary
            return "%s(%s)" % (nd.value, walk(nd.left))
        return "(%s %s %s)" % (walk(nd.left), nd.value, walk(nd.right))
    return walk(node)


def stability_analysis(X, y, *, n_bootstrap=20, feature_names=None,
                       operators="physical", generations=30, speed="fast",
                       seed=0, verbose=True, **kwargs):
    """Resample (X, y) with replacement `n_bootstrap` times, refit each time,
    and report how often each structural form of the winning expression recurs.

    Returns a dict:
        forms         : list of (canonical_form, frequency, example_expr),
                        sorted by frequency descending
        top_form      : the most frequent canonical form
        top_frequency : its frequency in [0, 1]
        n_bootstrap   : number of resamples actually completed

    Notes
    -----
    - Cost is ~n_bootstrap search runs; keep generations/speed modest.
    - Frequency is over the *champion* of each run. Interpreting it: >0.7 is a
      stable law, 0.3-0.7 is fragile, <0.3 means the data barely constrains the
      form (treat any single result as a guess).
    """
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    y = np.asarray(y, dtype=float).ravel()
    n = X.shape[0]
    rng = np.random.RandomState(seed)

    forms = Counter()
    examples = {}
    r2s = []
    completed = 0
    for b in range(n_bootstrap):
        idx = rng.randint(0, n, size=n)          # bootstrap resample
        Xb, yb = X[idx], y[idx]
        try:
            r = symbolic_regression(
                Xb, yb, feature_names=feature_names, operators=operators,
                generations=generations, speed=speed,
                seed=int(rng.randint(0, 1_000_000)), **kwargs)
        except Exception:
            continue
        form = _canonical_form(r.node)
        forms[form] += 1
        examples.setdefault(form, r.expression)
        # fit quality of this run's champion on the ORIGINAL (unresampled) data
        try:
            yhat = r.predict(X)
            ss = float(np.sum((y - y.mean()) ** 2)) or 1e-30
            r2s.append(1.0 - float(np.sum((y - yhat) ** 2) / ss))
        except Exception:
            pass
        completed += 1
        if verbose:
            print(f"  bootstrap {b + 1}/{n_bootstrap}: {form}")

    if completed == 0:
        if verbose:
            print("Stability: all runs failed.")
        return dict(forms=[], top_form=None, top_frequency=0.0, n_bootstrap=0)

    ranked = [(f, c / completed, examples[f])
              for f, c in forms.most_common()]
    top_form, top_freq, _ = ranked[0]
    med_r2 = float(np.median(r2s)) if r2s else float("nan")

    if verbose:
        print("\nStructural stability  (%d resamples, %d distinct forms)"
              % (completed, len(ranked)))
        for form, freq, ex in ranked[:6]:
            bar = "#" * int(round(freq * 30))
            print(f"  {freq:5.0%} {bar:<30} {form}")
        if len(ranked) > 6:
            print(f"  ... and {len(ranked) - 6} rarer forms")
        print(f"  median fit across resamples: R² = {med_r2:.4f}")
        # Two axes: does one form dominate, AND do the fits track the data?
        if med_r2 < 0.80:
            verdict = ("unreliable — even the recurring form fits the data "
                       "poorly (low R²). The signal is too weak to trust any "
                       "form, however often it repeats")
        elif top_freq >= 0.7:
            verdict = "stable — one form dominates and fits well; trust it"
        elif med_r2 >= 0.95:
            verdict = ("degenerate — several forms all fit well (R² high). "
                       "The law is real but not uniquely identified; pick by "
                       "parsimony from the Pareto front")
        else:
            verdict = ("fragile — forms scatter and fits are only fair. "
                       "Treat any single result with caution")
        print(f"  => top form {top_freq:.0%}, median R² {med_r2:.2f}: {verdict}")

    return dict(forms=ranked, top_form=top_form, top_frequency=top_freq,
                median_r2=med_r2, n_bootstrap=completed)
