# Release v0.2.0 — mode d'emploi (10 minutes)

## 1. Mettre à jour ton clone local
Décompresse ce zip **à la racine de ton clone** `gp-elite` (celui de GitHub Desktop)
en écrasant les fichiers existants. Fichiers concernés :

MODIFIÉS : gp_elite/core.py · gp_elite/api.py · gp_elite/__init__.py ·
           pyproject.toml · README.md · README.fr.md · tests/test_gp_elite.py
NOUVEAUX : CHANGELOG.md · benchmarks/feynman_bench.py · benchmarks/duel.py ·
           benchmarks/results_frozen_v0.2.0.jsonl · examples/forecast_battery_soh.py

## 2. Vérifier (optionnel mais recommandé)
Dans PowerShell, à la racine du clone :
    $env:PYTHONHASHSEED="0"
    py -m pytest tests/ -q        # attendu : 14 passed

## 3. Publier sur GitHub
GitHub Desktop → tu verras les 12 fichiers → message de commit :
    Release v0.2.0 — LM constants, restarts+Pareto, forecast mode, reproducibility
→ Commit to main → Push origin.
Puis sur github.com : Releases → "Draft a new release" → tag `v0.2.0`
→ colle la section 0.2.0 du CHANGELOG → Publish.

## 4. Publier sur PyPI (mêmes commandes que la 0.1.0)
    py -m pip install --upgrade build twine
    py -m build
    py -m twine upload dist/gp_elite-0.2.0*
(ton jeton pypi.org habituel). Vérification finale :
    py -m pip install -U gp-elite
    py -c "import gp_elite; print(gp_elite.__version__)"   # → 0.2.0
