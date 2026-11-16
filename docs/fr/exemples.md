# Exemples

Partie de la documentation de GP_ELITE : retour au [README](../../README.fr.md) ; [English version](../examples.md).

## Exemple sur des données de vieillissement de batterie simulées

```bash
python examples/battery_soh.py
```

Le fichier [`examples/nasa_battery_simulation.csv`](../../examples/nasa_battery_simulation.csv)
contient 168 cycles de charge **simulés** (numéro de cycle, température, courant,
état de santé de la capacité). Son origine n'est pas documentée au-delà de son nom :
considérez-le comme une démonstration de la démarche, pas comme un résultat sur de
vraies batteries. Le script y affiche (extrait) :

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

Un découpage aléatoire de données séquentielles est de l'interpolation, qui flatte
toutes les méthodes. Sur le découpage chronologique, les forêts d'arbres ne peuvent
que répéter des valeurs vues à l'entraînement et passent loin sous la moyenne.
L'équation que rend la 1.4, avec une puissance du cycle, fait pire encore
(R² −3,81) : ses nouvelles graines ont mené la recherche sur ces données
bruitées vers une autre formule (`benchmarks/results_1.4/release/`). Celle que
rendaient les versions 1.0 à 1.3 (la 1.2 écrit son exponentielle avec son
échelle), en fonction du courant et du cycle, faisait mieux que les forêts
d'arbres, mais pas bien (R² +0,16) ; la 0.8 et la 0.9 en rendaient une à R² −0,31, sous la
moyenne elle aussi, et la 0.7 une en fonction du cycle et du courant qui continuait de
suivre la tendance (R² +0,594). Une formule peut
extrapoler là où une forêt d'arbres ne le peut pas ; qu'elle le fasse dépend de la
formule que rend la recherche — sur ce jeu simulé, à vérifier sur les vôtres.


## Études de cas sur données publiques

Trois [études de cas sur données publiques](https://github.com/ariel95500-create/gp-elite/tree/main/examples/case_studies)
(la loi de Kepler avec les unités, les mesures de Hubble en 1929, les tuyaux de
Nikuradse) montrent ce qu'il rend sur des données publiques et ce qu'il ne trouve pas, et
[ce que GP_ELITE ne fait pas](https://github.com/ariel95500-create/gp-elite/blob/main/LIMITATIONS.fr.md)
liste ses limites connues, chacune avec la mesure qui la fonde.
