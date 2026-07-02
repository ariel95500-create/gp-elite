# Changelog

## 0.2.0 — 2026-07-02

### Ajouté
- **Optimisation des constantes Levenberg-Marquardt** (défaut ; `CONST_OPT_LM=False` pour l'ancien Adam). Constantes à précision machine — ex. Coulomb `q1·q2/(4πεr²)` récupérée exactement (1−R² ≈ 8e-32). Runs 6–14× plus rapides sur les problèmes à constantes.
- **Multi-restart natif** (`restarts=N`) : archives de candidats fusionnées entre runs (hold-out déterministe partagé), sélection finale globale. Convertit la variance inter-seeds en fiabilité.
- **Front de Pareto** en sortie (`result.pareto`, objets `ParetoEntry` avec `.predict`) : l'escalier complexité ↔ précision au lieu d'un champion unique.
- **Mode Prévision / extrapolation** : `extrapolate_feature=`, `extrapolate_direction=` — garde anti-divergence par sondes hors-domaine, plancher linéaire, sélection-frontière méta. Nouveau **mode 7** du menu interactif.
- **Seeding de motifs de composition** (pythagoricien, sommes de réciproques, gaussien…) pour les structures imbriquées ; désactivé automatiquement en mode extrapolation.
- Benchmarks reproductibles : `benchmarks/feynman_bench.py` (15 équations, protocole gelé) et `benchmarks/duel.py` (face-à-face gplearn).

### Corrigé
- **Reproductibilité** : workers parallèles à hachage figé ; à seed égal, répétitions identiques dans un même processus. Inter-invocations : lancer avec `PYTHONHASHSEED=0` (documenté).
- Import robuste de `api.py` hors package (usage fichier-à-côté, Windows).
- Interaction motifs × extrapolation (régression de prévision) corrigée.

### Chiffres (protocole gelé, PYTHONHASHSEED=0)
- Feynman 15 éq. : **10/15 récupérations exactes (67 %)**, 14/15 < 1e-3.
- Duel gplearn (mêmes données/splits, budget généreux pour gplearn) : **67 % vs 40 %** exact ; GPE meilleur sur 9 éq., égalité 5, gplearn 1.
- Prévision SOH batterie (extrapolation réelle cycles 119–168) : médiane R² **+0.52** vs +0.34 (régression linéaire), zéro divergence.
