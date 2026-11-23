# Régression robuste

Partie de la documentation de GP_ELITE : retour au [README](../../README.fr.md) ; [English version](../robust.md).

## 🛡️ Régression robuste (loss résistante aux valeurs aberrantes)

Les données réelles sont sales. Quelques points aberrants suffisent à faire dévier un ajustement aux moindres carrés loin de la vraie relation. GP_ELITE propose un **mode robuste** activable par un seul paramètre, conçu pour suivre la masse des données plutôt que quelques points extrêmes.

```python
resultat = symbolic_regression(X, y, feature_names=["x"], robust=True)
```

En interne, `robust=True` bascule l'objectif vers une **loss de Huber** et recale les coefficients finaux par **IRLS (moindres carrés repondérés itérativement)**. Le résultat reste une formule compacte et lisible.

**Comportement mesuré** (récupération de `y = 2x + 1` ; RMSE contre la *vraie* loi sur les points propres, plus bas = meilleur ; cinq seeds, médiane et pire seed) :

| valeurs aberrantes | défaut (MSE) | `robust=True` |
|-------------------:|-------------:|--------------:|
|                0 % | 0.063 [0.063] | 0.063 [0.063] |
|               10 % | 1.398 [1.398] | **0.237** [0.237] |
|               20 % | 1.925 [1.925] | 1.925 [1.925] |

Sur données propres, les deux modes rendent des droites légèrement différentes, aussi
proches l'une que l'autre de la vraie loi. Avec 10 % de valeurs aberrantes, le mode
robuste divise l'erreur par six. Avec 20 %, sur cet exemple, il ne fait pas mieux que le
défaut : le défaut rend la même droite pour les cinq seeds, tirée par les valeurs
aberrantes (`y = 4.23319 + 1.32825 * x`), et le mode robuste la même droite pour quatre
seeds sur cinq. La robustesse est un outil à essayer
quand on soupçonne des valeurs aberrantes, pas une garantie — comparez les deux modes
sur vos propres données.
(Jusqu'en 0.6, ce tableau montrait le meilleur de trois runs, choisi en comparant avec
la vraie loi, ce qu'aucun utilisateur ne peut faire.)

Reproduire : `python examples/robust_regression.py`.
