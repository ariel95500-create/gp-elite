"""
Exemple : découverte d'une loi de dégradation de batterie (données NASA).

Charge le CSV fourni, lance la régression symbolique, affiche la loi trouvée
et son rapport de généralisation (R² sur des données jamais vues).

Usage :
    python examples/battery_soh.py
"""
import os
import numpy as np
import pandas as pd

from gp_elite import symbolic_regression

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "nasa_battery_simulation.csv")


def main():
    df = pd.read_csv(CSV)
    feature_cols = ["cycle", "temperature", "courant"]
    target_col = "capacity_SOH"

    X = df[feature_cols].values
    y = df[target_col].values

    print(f"Données : {len(y)} cycles de batterie")
    print(f"Cible   : {target_col} ∈ [{y.min():.3f}, {y.max():.3f}]\n")

    result = symbolic_regression(
        X, y,
        feature_names=feature_cols,
        operators="physical",     # exp/log/sqrt/tanh — physique de dégradation
        normalize="auto",         # shift-free (features positives)
        generations=60,
        speed="fast",
        seed=1234,
    )

    print("─" * 60)
    print("LOI DÉCOUVERTE")
    print("─" * 60)
    print(f"  {target_col} = {result.expression}")
    print()
    print(f"  R² validation : {result.r2_validation:.4f}   (données jamais vues)")
    print(f"  MSE train     : {result.mse_train:.3e}")
    print(f"  Taille        : {result.size} nœuds")
    print("─" * 60)
    print("  Note : features normalisées (divmax). La forme structurelle est")
    print("  ce qui compte ; les coefficients absorbent les échelles.")


if __name__ == "__main__":
    main()
