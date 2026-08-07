# DOSSIER — bug `robust=True` (gp_elite 0.6.0)

Date : 2026-08-06 · Instruit sur : conteneur Linux, gp_elite 0.6.0, PYTHONHASHSEED=0
Découvert par : banc de bruit `feynman_noise.py` (régime outlier, bras robust)

---

## 1. Résumé

`robust=True` rend la fitness dépendante de l'ÉCHELLE de y. Conséquence :
sur toute cible dont l'écart-type est petit (std(y) ≲ 2 dans nos cas), le
moteur renvoie une **constante ou une droite triviale**, même sur des données
parfaitement propres — la recherche n'a pas lieu. Sur le banc : contrôle à
bruit nul à 6/15 EXACT (robust) contre 12/15 (défaut) ; I.8.14 → la constante
`2.08813` ; I.12.2 et I.16.6 → droites à une variable, erreur ~0.5.

Cause racine (bug n°1, **patché et validé ci-dessous**) :

    fitness = Huber(résidus BRUTS) + 0.5 × taille_arbre
              ^ dépend de l'unité de y   ^ pénalité ABSOLUE

La perte de Huber n'est pas normalisée par l'échelle de y (contrairement au
1−R² du mode standard), tandis que la parcimonie coûte 0.5 par nœud en
absolu. Dès que std(y) est petit, la perte totale évitable (~0.5·var(y))
vaut moins qu'UN nœud : la forme vraie ne peut mathématiquement pas battre
une constante.

Un second défaut, distinct, a été mis au jour pendant l'instruction
(bug n°2, **non patché — décision de conception à prendre**) : le polissage
final des constantes (`optimize_constants_lm`) minimise le SSE brut dans
tous les modes. En présence d'outliers, il écrase le calage robuste IRLS et
recontamine les constantes du champion. Preuve en §6.

---

## 2. Reproduction minimale (bug n°1)

```python
import numpy as np
from gp_elite import symbolic_regression
rng = np.random.RandomState(1006)
X = rng.uniform(1, 5, (350, 4))
y = np.sqrt((X[:,1]-X[:,0])**2 + (X[:,3]-X[:,2])**2)   # I.8.14, SANS bruit
for rob in (False, True):
    r = symbolic_regression(X, y, operators="physical", normalize="none",
                            generations=30, speed="fast", seed=0,
                            restarts=4, robust=rob)
    print(rob, r.size, r.expression)
# robust=False -> sqrt(((v2-v3))² + ((v1-v0))²)    exacte
# robust=True  -> 2.08813                           constante (0.6.0 non patchée)
```

Vérifié insensible à `normalize` ("none" et "auto" : même constante).

---

## 3. Mécanisme prouvé

### 3a. Arithmétique de domination (données réelles du banc, N=350)

fitness = Huber_brut + 0.5 × taille ; plus bas gagne.

| équation | std(y) | fit(constante, S=1) | fit(forme exacte) | gagnant |
|---|---|---|---|---|
| I.8.14   | 1.04 | **1.015** | 5.00 (S=10) | constante |
| I.16.6   | 0.36 | **0.564** | 6.50 (S=13) | constante |
| I.12.2   | 0.15 | **0.511** | 5.50 (S=11) | constante |
| I.12.1   | 5.11 | 5.231 | **1.50** (S=3) | forme exacte |

Le motif observé sur le banc (I.12.1 et III.15.12 épargnées, les trois
autres effondrées) est reproduit à 100 % par ce seul calcul.

### 3b. Test croisé prédictif — l'échelle seule bascule le résultat

| run (robust=True, sans bruit) | résultat |
|---|---|
| I.8.14, y brut (std 1.0) | constante `1.689`, err = 1.21 |
| I.8.14, **y × 10** (std 10) | **exacte** `10·sqrt(…)`, err = 2.1e-31 |
| I.12.1, y brut (std 5.1) | exacte `v0·v1` |
| I.12.1, **y ÷ 10** (std 0.5) | **cassée** : droite `0.061+0.27·v0`, err = 0.54 |

Multiplier y par une constante répare ou casse le moteur. CQFD.

---

## 4. Patch (bug n°1) — deux blocs dans `gp_elite/api.py`

### Bloc A — la perte : standardiser les résidus (échelle robuste 1.4826·MAD)

AVANT :
```python
            _delta_h = 1.345
            def _huber(preds, X, y, _d=_delta_h):
                r = preds - y; a = np.abs(r)
                return float(np.mean(np.where(a <= _d, 0.5 * r**2, _d * (a - 0.5 * _d))))
```

APRÈS :
```python
            _delta_h = 1.345
            def _huber(preds, X, y, _d=_delta_h):
                # [FIX-ROBUST] Résidus STANDARDISÉS par une échelle robuste de y
                # (1.4826·MAD ≈ sigma). Sans cela la perte dépend de l'UNITÉ de y,
                # et la pénalité de parcimonie absolue domine toute structure dès
                # que std(y) est petit -> le moteur renvoie des constantes.
                # delta=1.345 retrouve ainsi son sens statistique (résidus en sigma).
                med = float(np.median(y))
                s = 1.4826 * float(np.median(np.abs(y - med)))
                if not (s > 0.0 and np.isfinite(s)):
                    s = float(np.std(y)) or 1.0
                r = (preds - y) / s; a = np.abs(r)
                return float(np.mean(np.where(a <= _d, 0.5 * r**2, _d * (a - 0.5 * _d))))
```

### Bloc B — la parcimonie : recalibrer à l'échelle de la perte standardisée

AVANT :
```python
        core._CUSTOM_LOSS_PARSIMONY = 0.5
```

APRÈS :
```python
        # [FIX-ROBUST] La loss standardisée vit dans ~[0, 1] (0.5 ≈ modèle
        # constant). L'ancienne pénalité 0.5/nœud la DOMINAIT : une forme vraie
        # de 10 nœuds (coût 5.0) ne pouvait jamais battre une constante
        # (coût ~1.0). 0.005/nœud garde le rasoir d'Ockham (arbre-monstre de
        # 60 nœuds : +0.30) sans interdire la forme vraie (+0.05).
        core._CUSTOM_LOSS_PARSIMONY = 0.005
```

Périmètre : uniquement le bloc `if robust:` — aucun autre mode touché.
Le calage IRLS (`_robust_scale_params`) n'est PAS modifié : il standardise
déjà ses résidus en interne et n'est pas en cause.

---

## 5. Validation du patch (conteneur, protocole du banc, seed=0)

| test | avant patch | après patch |
|---|---|---|
| I.8.14 propre | constante, err 1.21 | **exacte**, err 0.0, S=10 |
| I.12.1 propre (non-régression) | exacte | **exacte**, S=3 |
| I.12.1 ÷10 (invariance d'échelle) | droite, err 0.54 | **exacte** `0.1·(v0·v1)`, 3.8e-32 |
| I.12.2 propre | droite, err 0.52 | **exacte** 2.2e-31 (0.1378/1.7312 = 1/4π) |
| I.16.6 propre | droite, err 0.48 | recherche réelle, err 1.4e-2 (MISS, comme en défaut — équation insoluble connue) |

Zéro régression, invariance d'échelle restaurée.

---

## 6. Bug n°2 (résiduel, non patché) — le polissage final annule la robustesse

**Symptôme** : sur I.8.14 + 10 % d'outliers (±10σ), les champions des DEUX
modes (défaut et robust patché) sont identiques à 6 décimales :
`-0.464875 + 1.175519·sqrt(…)` — alors que défaut cale par OLS et robust
par IRLS.

**Preuve** (mêmes données) :

| calage | a | b |
|---|---|---|
| OLS sur y corrompu | −0.490 | 1.221 |
| **champions rapportés (2 modes)** | **−0.465** | **1.176** |
| IRLS robuste du moteur | −0.080 | 1.036 ← quasi la vérité (0, 1) |

Les constantes rapportées sont de la famille OLS-sur-corrompu ; l'IRLS,
correct, est écrasé en aval.

**Localisation** (`core.py`) : `optimize_constants_lm` (≈ l.4044) minimise
`r @ r` (SSE brut) sans conscience du mode robuste ; appelé sur le champion
final (≈ l.6768) et sur chaque membre du front (≈ l.6788) ; l'acceptation
elle-même est jugée au `raw_mse` (≈ l.6770).

**Piste de correctif** (décision de conception à prendre par le mainteneur) :
quand `_CUSTOM_LOSS_ROBUST` est actif, faire le LM en version repondérée
(IRLS-LM : poids de Huber sur résidus standardisés par MAD, 2-3 itérations
externes), et juger l'acceptation à la perte de Huber standardisée plutôt
qu'au `raw_mse`. Alternative minimale : sauter le polish MSE en mode robust
(constantes issues de l'évolution + wrap IRLS) — plus sûr, moins précis.
À trancher avant implémentation ; `optimize_constants_lm` est sur le chemin
chaud de l'évolution (l.5527/5560), le patch doit rester conditionnel.

**Conséquence pratique tant que non corrigé** : en présence d'outliers, le
mode robust patché retrouve la bonne STRUCTURE mais ses constantes restent
biaisées comme celles du mode défaut (b=1.18 au lieu de 1.0 dans la repro).

---

## 7. Annexes

- Incohérence mineure : l'IRLS de `_robust_scale_params` utilise delta=0.5
  (agressif) là où la perte utilise 1.345, et `std(r)` (non robuste) comme
  échelle interne au lieu du MAD. Sans lien avec les bugs ci-dessus ;
  amélioration possible, non urgente.
- Les fichiers `feyn_noise.jsonl` contenant le bras robust 0.6.0 documentent
  la version buggée : à archiver tels quels (c'est la télémétrie de la
  découverte), ne pas les mélanger aux runs post-patch.
- Le contrôle attendu après patch sur machine de référence : bras
  `--noise outlier --robust`, niveau 0.0 → retour à ~12/15 EXACT
  (contre 6/15 en 0.6.0 non patchée).
