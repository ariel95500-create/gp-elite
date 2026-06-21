GP_ELITE
Genetic-programming symbolic regression — discover interpretable laws from your experimental data.
🇫🇷 Version française
GP_ELITE searches for a mathematical formula linking your variables to a target, instead of a black box. It is built for small experimental datasets (≤10 variables, 100–5000 points) where you want to understand the relationship: degradation laws, sensor calibration, engineering correlations, dose–response curves, physical laws.
Pure Python / NumPy — no Julia, no compilation, no GPU. `pip install` and you're ready.
![GP_ELITE rediscovers Kepler's Third Law from 8 data points (R² = 1.000000)](assets/kepler_plot.png)
> Given only the 8 planets' distance and orbital period, GP_ELITE rediscovered Kepler's Third Law (`T = a·√a = a^1.5`) in seconds — see [`examples/kepler_demo.py`](examples/kepler_demo.py).
```python
from gp_elite import symbolic_regression

result = symbolic_regression(X, y, feature_names=["cycle", "temperature", "current"])
print(result.expression)        # capacity_SOH = 0.913 - 0.352·tanh(...)
print(result.r2_validation)     # 0.996  (on data never seen during training)
```
---
Why GP_ELITE?
	GP_ELITE	Neural networks	PySR (state of the art)
Output	readable formula	black box	readable formula
Installation	`pip install` (pure Python)	heavy	requires Julia
Overfitting guard	built-in (hold-out)	do it yourself	do it yourself
Variable selection	importance report	no	partial
GP_ELITE's niche: zero barrier to entry. A lab engineer, a student, or a technician points at a CSV file and gets a validated law back — without becoming a developer.
---
Installation
```bash
pip install gp-elite          # from PyPI
# or, from source:
git clone https://github.com/ariel95500-create/gp-elite
cd gp-elite && pip install -e .
```
Dependencies: `numpy`, `pandas`, `scikit-learn`.
---
Usage
One line, on your own data (console UI)
```bash
gp-elite
```
Choose mode 6 (generic CSV), point to your file, and keep the defaults. GP_ELITE detects the columns, holds out a validation set, evolves, and prints the discovered law with its generalization report.
Programmatically (notebooks, pipelines)
```python
import numpy as np
from gp_elite import symbolic_regression

X = np.random.uniform(1, 5, (200, 2))
y = 2.0 + 3.0 * np.sqrt(X[:, 0]) - 0.5 * X[:, 1]

result = symbolic_regression(
    X, y,
    feature_names=["a", "b"],
    operators="physical",   # 'physical' | 'trig' | 'full' | 'poly'
    generations=60,
    speed="fast",           # 'ultrafast' | 'fast' | 'normal'
)

print(result.expression)        # e.g. 2.0 + 3.0·sqrt(a) - 0.5·b
print(result.r2_validation)     # quality on the hold-out set
print(result.size)              # node count (readability)
```
---
Full example: battery degradation (NASA data)
```bash
python examples/battery_soh.py
```
From 168 real charge cycles, GP_ELITE discovers a state-of-health (SOH) law:
```
capacity_SOH ≈ 0.913 − 0.352 · tanh( cycle^((temperature/cycle)^0.485) )

R² validation = 0.996   (on cycles never seen)   12 nodes
```
A saturating degradation with cycle count, modulated by temperature — physically plausible, and certified on unseen data.
---
What is GP_ELITE good (and less good) at?
Good at: physical / engineering laws with multiplicative or exponential structure, modest-size noisy experimental data, problems where interpretability matters most.
On a representative subset of the Feynman Symbolic Regression Benchmark (16 physics equations), in `fast` mode (~15 s/equation): 81% of equations solved at R² > 0.999, mean R² 0.993.
Less good at: chaotic sequences (e.g. Collatz flight time — an intrinsically random component), >15–20 variables (the search space explodes), large datasets where raw accuracy outweighs interpretability (ensemble models dominate there).
---
Technical features
Asymmetric island model (explorer / cleaner / stigmergic) with periodic migration
Linear scaling (Keijzer 2003): the engine searches for the shape; scale and offset coefficients are solved in closed form
ε-lexicase selection (La Cava 2016) to preserve behavioral diversity
Island parallelism (multi-core) — ≈ ×3 measured on 4 cores
Hold-out validation + parsimonious champion selection (R² tolerance): built-in overfitting guard
Shift-free normalization preserving multiplicative structure (x·y stays a clean product)
Transferable stigmergic memory across runs (grammar export/import)
---
Tests
```bash
pip install pytest
pytest -q
```
---
License
MIT — see LICENSE. Free to use, including commercially, with retention of the copyright notice.
Citing GP_ELITE
If GP_ELITE is useful in academic work, see CITATION.cff.
