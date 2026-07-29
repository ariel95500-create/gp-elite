---
title: 'gp-elite: pure-Python symbolic regression with gradient-refined constants and dimensionally-constrained search'
tags:
  - Python
  - symbolic regression
  - genetic programming
  - interpretable machine learning
  - dimensional analysis
  - equation discovery
authors:
  - name: Sabri Hakou
    orcid: 0009-0007-6229-5157
    affiliation: 1
affiliations:
  - index: 1
    name: Independent Researcher, France
date: 28 July 2026
bibliography: paper.bib
---

# Summary

Symbolic regression searches the space of mathematical expressions for a formula
that fits a dataset, returning a closed-form equation instead of the opaque
weights of a black-box model. It is attractive wherever the relationship itself
is the object of interest rather than the prediction: a degradation law, a sensor
calibration curve, an engineering correlation, a candidate physical law.

`gp-elite` is a symbolic-regression library written entirely in Python and NumPy
[@harris2020numpy]. It evolves expressions by genetic programming [@koza1992gp]
and refines the numerical constants of every candidate with a
Levenberg–Marquardt least-squares optimizer [@levenberg1944; @marquardt1963], so
that the evolutionary search concentrates on finding the right *structure* while
a dedicated numerical routine finds the right *coefficients*. It exposes a
scikit-learn-compatible estimator [@pedregosa2011sklearn], installs with
`pip install gp-elite` with no compiler and no second language runtime, and
holds out a validation split by default so that the returned model comes with an
out-of-sample score rather than a training-set fit.

Since version 0.4, users may declare the physical units of their input columns
and of the target. The search is then restricted to dimensionally consistent
expressions: generation, mutation and crossover all preserve dimensions, and a
validity gate rejects unsound candidates on every code path. The engine can no
longer return a formula that fits the numbers while adding hertz to a
dimensionless quantity.

Version 0.5 extends this to laws whose constant is itself dimensioned: the
leading constant may carry a dimension, deduced by homogeneity, so the engine
reports not only the shape of a law but the **units and value of its missing
physical constant** — recovering the gravitational constant, and its units,
from masses and distances alone.

# Statement of need

Users who want an interpretable model — laboratory scientists, engineers,
students of evolutionary computation — share a practical need: a
symbolic-regression tool that installs in one command, can be read and modified
in the language they already use, and still recovers precise numerical
constants. These requirements are usually in tension. Engines that fit constants
well tend to rely on compiled or non-Python backends; pure-Python engines that
are easy to install tend not to fit constants at all, leaving the evolutionary
search to assemble numerical values out of random terminals.

`gp-elite` targets that gap. It is aimed at small-to-medium experimental
datasets — roughly up to ten variables and a few thousand rows — where
interpretability matters more than raw predictive accuracy, and where the
analyst can reasonably be expected to know what their columns mean physically.

The dimensional mode addresses a second, more specific problem. In scientific
applications, an expression that is numerically excellent but dimensionally
incoherent is not a partial success: it is not a candidate law at all. Making
dimensional consistency a hard constraint of the search, rather than a
post-hoc filter, follows a line of work opened by dimensionally aware genetic
programming [@keijzer1999dimensional] and by the unit-based decomposition used
in AI Feynman [@udrescu2020feynman], and makes the guarantee available from a
scikit-learn estimator with a single `units=` argument.

That line of work carries a restriction this implementation initially inherited:
fitted constants are dimensionless. Under it, a law as elementary as Hooke's
`F = k·x` is unreachable, since no dimensionless constant relates metres to
newtons — yet much of physics is written with dimensioned constants. Lifting it
turns the constraint into an instrument: the analyst supplies what they know,
the units of their columns, and the engine returns what they do not.

# State of the field

The strongest contemporary engines are backed by compiled code: `Operon` is
implemented in C++ [@burlacu2020operon] and `PySR` drives a Julia backend
[@cranmer2023pysr]. Both are faster and, on large benchmarks, more accurate than
a pure-Python implementation can be. They also require a toolchain beyond
`pip`, which raises the barrier for a user who wants to inspect, teach from, or
modify the search itself. At the other end, `gplearn` [@gplearn] is pure Python
and widely used for teaching, but does not perform gradient-based constant
optimization, which limits it on problems whose constants are not small
integers.

`gp-elite` is positioned deliberately between the two: pure Python and
`pip`-installable like `gplearn`, but with Levenberg–Marquardt constant
refinement, linear scaling [@keijzer2003scaling], and $\epsilon$-lexicase
selection [@lacava2016lexicase] as in the compiled engines. On a frozen
15-equation subset of the Feynman benchmark, under identical data and splits and
with a generous budget granted to the baseline, it recovers 10/15 equations
exactly at machine precision against 6/15 for `gplearn`. The claim made here is
not that it competes with `Operon` or `PySR` on speed or on large-scale
accuracy — it does not — but that it occupies a niche neither of them fills.

The dimensional mode has no equivalent among the packages above: none of them
constrains the search by declared physical units.

# Software design

Three design decisions shaped the library.

*Separating structure from coefficients.* Rather than letting evolution
discover numerical constants by drift, `gp-elite` treats every candidate as a
parametric template whose constants are fitted by Levenberg–Marquardt, with
scale and offset additionally solved in closed form via linear scaling. Search
pressure is thereby spent on shape, which is what genetic programming is good
at, and not on arithmetic, which it is bad at.

*Constraining rather than filtering.* Dimensional consistency could have been
implemented as a post-hoc audit of the final model. That was in fact the v0.3
behaviour, and it proved unsatisfying: on the tested problem it reported that
none of the returned models were physically meaningful, without offering a
remedy. Version 0.4 moves the check inside the search, reusing the same
dimensional algebra so that auditor and engine cannot diverge. The cost is a
roughly fourfold slowdown; the benefit is that every returned model is valid by
construction.

*Deducing rather than requiring.* Under `unknown_constant=True` the validity
gate no longer requires an expression to *reach* the target dimension, only to
*have* a well-defined one; the leading constant absorbs the difference, and its
dimension follows as `target / dim(f)`. Typed generation draws random reachable
surrogate targets, so the population spans several dimension classes and
selection retains the one that fits.

*Reporting honestly by default.* The estimator holds out a validation split,
selects a parsimonious champion within an $R^2$ tolerance, and exposes a
complexity/accuracy Pareto front. The intent is that a user who does nothing
special still receives a model whose reported score was not measured on its own
training data.

# Research impact statement

The software is released on PyPI under the MIT licence and is accompanied by a
test suite and by benchmark scripts that regenerate every number quoted in its
documentation.

The dimensional mode has been evaluated in a controlled A/B experiment on
Feynman equation II.11.3, with five seeds and an identical budget per arm
(`benchmarks/ab_ood.py`). Without constraints, 0/5 returned models are
dimensionally valid; with `units=`, 5/5 are valid, and they are 2.6 times
smaller (22 versus 58 nodes) at a slightly better test $R^2$. A third arm gives
the unconstrained search four times the number of generations, equalising
wall-clock time: it still returns 0/5 valid models, and larger ones. The same
experiment also bounds the claim. On a test set drawn *outside* the training
domain, every arm collapses, and no arm recovers the target law exactly at the
budgets tested; a large-budget run confirms this, converging reproducibly to a
denominator that is linear where the true law is a difference of squares.
The constraint therefore buys physically coherent and compact approximations,
not the law itself.

The mystery-constant mode is validated on three reference laws whose answer is
known in advance (`benchmarks/test_constante_mystere.py`, 20 generations, one
restart). Hooke's law returns `kg·s⁻²` and 250.0 for a true 250; Newton's law of
gravitation returns `m³·kg⁻¹·s⁻²` and 6.674e-11 for a true 6.674e-11; the ideal
gas law returns `kg·m²·s⁻²·mol⁻¹·K⁻¹` and 8.31446 for a true 8.314463. Structure
is exact and $R^2 = 1.000000$ in all three cases, on two independent platforms.

An integration for the SRBench living benchmark [@lacava2021srbench] has been
submitted as a pull request and builds successfully in that project's continuous
integration.

# AI usage disclosure

Generative AI was used extensively in the development of this software, and in
the writing of its documentation and of this paper. The assistant was Claude
(Anthropic), used across several model versions between May and July 2026.

The project began as the author's own work, before any AI involvement: the
expression representation and tree-generation strategies, the protected
operator set, the asymmetric island model, gradient-based constant optimization
using Adam, the seeding mechanism, the interactive console interface and the
benchmark problem suite all predate that phase and, in modified form, remain in
the released version.

From that point onward the assistant acted as a development collaborator. Its
contributions were: co-design and implementation of the stigmergic layer — the
pheromone-weighted fragment library, its evaporation and pruning dynamics, the
fragment co-occurrence graph, the sequence memory, and the stigmergic island;
the refactor from single-variable to multi-variable regression; the subsequent
numerical and statistical layers, namely Levenberg–Marquardt constant
refinement replacing Adam, linear scaling, the Pareto front, $\epsilon$-lexicase
selection, the robust loss, the dimensionally-constrained search and the
deduction of dimensioned constants; diagnosis and correction of specific
defects, including a float64 overflow in the Levenberg–Marquardt optimizer and
two defects in the dimensional mode;
packaging and release engineering; the benchmark and non-regression scripts
distributed in the repository; and the drafting of the documentation and of
this paper.

All AI-assisted output was reviewed and validated by the author before
inclusion, and the direction of the work — which mechanisms to pursue, which
results to trust, which claims to make — remained the author's throughout.
Every correction was accompanied by an executable check: the overflow was
reproduced before being fixed and re-tested afterwards, and the absence of
regression was verified by comparing fits before and after each change on a
fixed set of seeds. The benchmark figures quoted in this paper were produced by
the author on their own machine using the scripts in the repository, and the
project's test suite passes on the released version. The scientific claims and
their stated limits are the author's own, as is responsibility for the whole.

# Acknowledgements

This work received no financial support.

# References
