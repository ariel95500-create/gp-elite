"""Tests de non-régression et de correction pour GP_ELITE.

Lancer : pytest -q   (depuis la racine du dépôt)
Ces tests sont volontairement rapides (peu de générations) — ils vérifient
la correction structurelle et les invariants, pas la performance ultime.
"""
import random

import numpy as np
import pytest

from gp_elite import symbolic_regression, core


def _seed(s=0):
    random.seed(s)
    np.random.seed(s)


def test_import_and_version():
    import gp_elite
    assert isinstance(gp_elite.__version__, str)
    assert hasattr(gp_elite, "symbolic_regression")


def test_simplify_rules():
    N = core.Node
    cases = [
        (N("+", N("x"), N(0.0)), "x"),
        (N("-", N("x"), N("x")), "0.0"),
        (N("neg", N("neg", N("x"))), "x"),
    ]
    for tree, expected in cases:
        assert core.to_string(core.simplify(tree)) == expected


def test_simplify_no_recursion_error_on_deep_tree():
    # Les structures profondes ne doivent pas lever RecursionError
    deep = core.Node("x")
    for _ in range(4000):
        deep = core.Node("neg", deep)
    deep.structural_hash()
    deep.copy()
    core.simplify(deep)


def test_simplify_returns_independent_objects():
    N = core.Node
    a = core.simplify(N("+", N("x"), N(0.0)))
    b = core.simplify(N("+", N("x"), N(0.0)))
    assert a is not b  # le cache ne doit jamais exposer d'objet partagé


def test_shift_free_scaler_preserves_products():
    # divmax ne décale pas → x*y reste un produit propre
    X = np.random.uniform(1, 5, (50, 2))
    sc = core._ShiftFreeScaler()
    Xs = sc.fit_transform(X)
    # reconstruction exacte
    assert np.allclose(sc.inverse_transform(Xs), X)
    # pas de décalage : 0 reste 0 (colonne positive → min > 0, mais ratio conservé)
    assert np.allclose(Xs * sc.scale_, X)


def test_auto_normalization_choice():
    pos = np.random.uniform(1, 5, (40, 2))
    signed = np.random.uniform(-3, 3, (40, 2))
    sc_pos, desc_pos = core._choose_scaler(pos, "auto", (-2, 2))
    sc_sig, desc_sig = core._choose_scaler(signed, "auto", (-2, 2))
    assert "divmax" in desc_pos      # features positives → shift-free
    assert "minmax" in desc_sig      # features signées → minmax


def test_symbolic_regression_linear_law():
    # loi additive simple : doit atteindre un très bon R²
    _seed(0)
    X = np.random.uniform(-2, 2, (200, 2))
    y = 1.5 * X[:, 0] - 2.0 * X[:, 1] + 0.5
    r = symbolic_regression(X, y, feature_names=["u", "v"],
                            operators="poly", generations=30, seed=0)
    assert r.r2_validation is not None
    assert r.r2_validation > 0.95
    assert r.size >= 1


def test_symbolic_regression_multiplicative_law():
    # loi multiplicative : la normalisation shift-free doit éviter le bloat
    _seed(1)
    X = np.random.uniform(1, 5, (200, 3))
    y = X[:, 0] * X[:, 1] / X[:, 2]
    r = symbolic_regression(X, y, feature_names=["a", "b", "c"],
                            operators="poly", generations=35, seed=1)
    assert r.r2_validation > 0.99
    # arbre raisonnablement compact (pas un monstre de termes croisés)
    assert r.size < 40


def test_feature_names_in_expression():
    _seed(0)
    X = np.random.uniform(1, 5, (150, 2))
    y = X[:, 0] + X[:, 1]
    r = symbolic_regression(X, y, feature_names=["alpha", "beta"],
                            operators="poly", generations=20, seed=0)
    assert "X[" not in r.expression  # noms réels, pas X[i]


def test_predict_is_finite_and_shaped():
    _seed(0)
    X = np.random.uniform(1, 5, (120, 2))
    y = X[:, 0] * 2 + X[:, 1]
    r = symbolic_regression(X, y, operators="poly", generations=20, seed=0)
    # predict attend des features normalisées : on réutilise l'échelle divmax
    Xs = X / np.max(np.abs(X), axis=0)
    preds = r.predict(Xs)
    assert preds.shape == (120,)
    assert np.all(np.isfinite(preds))


def test_validation_can_be_disabled():
    _seed(0)
    X = np.random.uniform(1, 5, (120, 2))
    y = X[:, 0] + X[:, 1]
    r = symbolic_regression(X, y, operators="poly", generations=15,
                            validation_split=0.0, seed=0)
    assert r.r2_validation is None  # pas de hold-out demandé


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
