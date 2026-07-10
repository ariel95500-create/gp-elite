# Release v0.3.0 "Trust" — mode d'emploi (10-15 minutes)

## Ce que contient cette release
GP_ELITE v0.3.0 répond directement aux retours du lancement HN/Reddit :
- `result.diagnostics(X, y)` — diagnostics de résidus (sinuhe69)
- `stability_analysis(X, y)` — stabilité structurelle par bootstrap (srean, gus_massa)
- `check_dimensions()` / `audit_pareto()` — audit dimensionnel (ziofill, nyrikki)
- `GPEliteRegressor` — wrapper scikit-learn conforme (check_estimator passé),
  base du travail SRBench à venir
- `benchmarks/srbench_dryrun.py` — répétition du protocole SRBench

## 1. Mettre à jour ton clone local
1. Ouvre GitHub Desktop → Repository → **Pull origin** (toujours en premier,
   pour éviter le décalage qu'on a eu une fois).
2. Décompresse `gp-elite_v0.3.0_release.zip` **à la racine de ton clone**,
   en écrasant les fichiers existants (Ctrl+A, Ctrl+C dans le dossier extrait,
   Ctrl+V dans le clone → "Remplacer les fichiers dans la destination").

Fichiers concernés :
  MODIFIÉS : gp_elite/api.py · gp_elite/__init__.py · pyproject.toml ·
             CHANGELOG.md · tests/test_gp_elite.py
  NOUVEAUX : gp_elite/stability.py · gp_elite/dimensions.py ·
             gp_elite/sklearn_api.py · examples/residual_diagnostics.py ·
             examples/stability_bootstrap.py · examples/dimensional_audit.py ·
             benchmarks/srbench_dryrun.py

## 2. Vérifier (recommandé)
Dans GitHub Desktop → Repository → Open in Command Prompt (Open without Git) :
    py -m pytest tests/ -q
Attendu : 19 passed (peut prendre 1-2 minutes, c'est normal — les tests
sklearn/stability sont plus lourds).

## 3. Publier sur GitHub
GitHub Desktop → tu dois voir 12 fichiers changés → message de commit :
    Release v0.3.0 "Trust" — diagnostics, stability, dimensions, sklearn wrapper
→ Commit to main → Push origin.
Puis sur github.com : Releases → Draft a new release → tag `v0.3.0` →
titre `v0.3.0 "Trust" — diagnostics, stability, dimensional audit, sklearn`
→ colle la section 0.3.0 du CHANGELOG.md → Publish release.

## 4. Publier sur PyPI (mêmes commandes qu'avant)
    py -m build
    py -m twine upload dist/gp_elite-0.3.0*
(jeton PyPI habituel ; recrée-en un frais sur pypi.org si 403)

## 5. Vérifier
    py -m pip install -U gp-elite
    py -c "import gp_elite; print(gp_elite.__version__)"    # -> 0.3.0
    py -c "from gp_elite import GPEliteRegressor; print('sklearn wrapper OK')"
