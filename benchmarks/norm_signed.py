"""Normalisation des donnees SIGNEES : minmax (choix actuel de 'auto') ou divmax ?

Hypothese (ecrite avant de mesurer) : sur des entrees signees, la division par
max|x| (sans decalage) cherche au moins aussi bien que min-max, parce qu'elle
preserve la structure multiplicative (x*y reste un produit) au lieu de
transformer chaque variable en a*(x - x0).

Critere de decision (fixe avant) : passer 'auto' a divmax pour toutes les
donnees si
  (A) lois synthetiques signees : recuperations exactes divmax >= minmax au
      total, et aucune loi ou divmax perd 2 seeds ou plus sur 5 ;
  (B) donnees reelles standardisees comme dans SRBench : R2 test median divmax
      >= minmax - 0.005, et pas plus d'effondrements (R2 < 0).
Sinon, statu quo.

Resultat (0.7.0, archive dans results_0.7/norm_signed.jsonl) : critere
rempli, 'auto' passe a divmax. Detail dans le CHANGELOG 0.7.0.

Usage : python norm_signed.py A <law_index> <arm>      (5 seeds, arm = minmax|divmax)
        python norm_signed.py B <dataset> <arm>         (5 plis, seed 0)
        ... [--out fichier]                             (defaut : results_0.7/norm_signed.jsonl)
        python norm_signed.py --summary [fichier]       (tableaux du CHANGELOG)
Un processus par point de mesure (regle 4 du protocole) ; PYTHONHASHSEED=0.
Toute la campagne : 8 lois + 6 jeux, deux bras, environ 2 h sur un coeur.
"""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pmlb_frozen
import provenance
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results_0.7", "norm_signed.jsonl")

LAWS = [  # (nom, n_var, f, pool)
    ("x0*x1",            2, lambda X: X[:, 0] * X[:, 1], "physical"),
    ("x0^2 + x1^2",      2, lambda X: X[:, 0] ** 2 + X[:, 1] ** 2, "physical"),
    ("x0^3 - x0",        1, lambda X: X[:, 0] ** 3 - X[:, 0], "physical"),
    ("exp(-x0^2/2)",     1, lambda X: np.exp(-X[:, 0] ** 2 / 2), "physical"),
    ("x0*x1 + x2",       3, lambda X: X[:, 0] * X[:, 1] + X[:, 2], "physical"),
    ("x1*sin(x0)",       2, lambda X: X[:, 1] * np.sin(X[:, 0]), "trig"),
    ("vdp: 10*(x1 - x0^3/3 + x0)", 2, lambda X: 10 * (X[:, 1] - X[:, 0] ** 3 / 3 + X[:, 0]), "physical"),
    ("lv: 3*x0 - 2*x0*x1 - x0^2", 2, lambda X: 3 * X[:, 0] - 2 * X[:, 0] * X[:, 1] - X[:, 0] ** 2, "physical"),
]
DATASETS = ["210_cloud", "228_elusage", "712_chscase_geyser1", "561_cpu",
            "690_visualizing_galaxy", "547_no2"]      # voir pmlb_frozen.py


def one_minus_r2(y, p):
    v = float(np.var(y)) or 1e-30
    with np.errstate(all="ignore"):
        e = float(np.mean((p - y) ** 2) / v)
    return e if np.isfinite(e) else 1e30


def run_A(i, arm):
    from gp_elite import symbolic_regression
    name, nv, f, pool = LAWS[i]
    out = []
    for seed in range(5):
        rng = np.random.RandomState(500 + 17 * i + seed)
        X = rng.uniform(-3, 3, (200, nv)); y = f(X)
        tr, te = np.arange(140), np.arange(140, 200)
        r = symbolic_regression(X[tr], y[tr], operators=pool, normalize=arm,
                                generations=40, speed="fast", restarts=1,
                                parallel=False, seed=seed)
        e = one_minus_r2(y[te], r.predict(X[te]))
        out.append(dict(part="A", law=name, arm=arm, seed=seed, err=e,
                        size=int(r.size), raw_size=int(_size(r.formula.tree)) if r.formula else None,
                        exact=bool(r.formula_exact), expr=r.expression[:160]))
        print("%-28s %-7s seed %d  1-R2=%.2e  size=%d  %s" % (name, arm, seed, e, r.size, r.expression[:70]), flush=True)
    return out


def _size(t):
    from gp_elite import core
    return core.tree_size(t)


def run_B(name, arm):
    from gp_elite import symbolic_regression
    from sklearn.model_selection import KFold
    from sklearn.preprocessing import StandardScaler
    X, y = pmlb_frozen.load(name)
    out = []
    for k, (tr, te) in enumerate(KFold(5, shuffle=True, random_state=0).split(X)):
        sx, sy = StandardScaler(), StandardScaler()       # comme evaluate_model.py
        Xtr = sx.fit_transform(X[tr]); Xte = sx.transform(X[te])
        ytr = sy.fit_transform(y[tr].reshape(-1, 1)).ravel()
        from gp_elite import core as _C
        ex0 = getattr(_C, "_EXACT_PRIORITY_SWAPS", 0)
        r = symbolic_regression(Xtr, ytr, operators="physical", normalize=arm,
                                generations=40, speed="fast", restarts=1,
                                parallel=False, seed=0)
        exact_prio = getattr(_C, "_EXACT_PRIORITY_SWAPS", 0) > ex0
        p = sy.inverse_transform(r.predict(Xte).reshape(-1, 1)).ravel()
        r2 = 1.0 - one_minus_r2(y[te], p) * 1.0
        out.append(dict(part="B", dataset=name, arm=arm, fold=k, r2=r2,
                        exact_priority=bool(exact_prio),
                        size=int(r.size), raw_size=int(_size(r.formula.tree)) if r.formula else None,
                        exact=bool(r.formula_exact), expr=r.expression[:160]))
        print("%-24s %-7s fold %d  R2=%.4f  size=%d" % (name, arm, k, r2, r.size), flush=True)
    return out


def summary(path=OUT):
    import collections
    rows = [json.loads(l) for l in open(path) if l.strip()]
    A = [r for r in rows if r["part"] == "A"]
    B = [r for r in rows if r["part"] == "B"]
    print("A. Lois a entrees signees, 5 seeds : exact (1-R2 < 1e-9) / proche (< 1e-3)")
    tot = {"minmax": [0, 0], "divmax": [0, 0]}
    for name, *_ in LAWS:
        line = "  %-28s" % name
        for arm in ("minmax", "divmax"):
            v = [r for r in A if r["law"] == name and r["arm"] == arm]
            ex = sum(r["err"] < 1e-9 for r in v); ne = sum(r["err"] < 1e-3 for r in v)
            tot[arm][0] += ex; tot[arm][1] += ne
            line += "   %s %d/%d exact, %d proches" % (arm, ex, len(v), ne)
        print(line)
    print("  TOTAL exact : minmax %d, divmax %d ; proches : minmax %d, divmax %d"
          % (tot["minmax"][0], tot["divmax"][0], tot["minmax"][1], tot["divmax"][1]))
    print("\nB. Donnees reelles standardisees (comme evaluate_model de SRBench), 5 plis")
    by = collections.defaultdict(dict)
    for r in B:
        by[(r["dataset"], r["fold"])][r["arm"]] = r
    keys = sorted(k for k in by if len(by[k]) == 2)
    m = np.array([by[k]["minmax"]["r2"] for k in keys])
    d = np.array([by[k]["divmax"]["r2"] for k in keys])
    for arm, v in (("minmax", m), ("divmax", d)):
        print("  %s : moyenne %.4f  mediane %.4f  pire %.4f  effondrements (R2<0) %d"
              % (arm, v.mean(), np.median(v), v.min(), int((v < 0).sum())))
    diff = d - m
    print("  apparie divmax - minmax : mediane %+.4f, divmax meilleur sur %d/%d plis"
          % (np.median(diff), int((diff > 0).sum()), len(diff)))
    rs = lambda arm: int(np.median([by[k][arm]["raw_size"] for k in keys]))
    print("  taille mediane de la formule livree : minmax %d, divmax %d" % (rs("minmax"), rs("divmax")))


if __name__ == "__main__":
    if "--out" in sys.argv:                      # fichier de resultats choisi
        i = sys.argv.index("--out")
        OUT = os.path.abspath(sys.argv[i + 1])
        del sys.argv[i:i + 2]
    if sys.argv[1:2] == ["--summary"]:
        summary(sys.argv[2] if len(sys.argv) > 2 else OUT)
        sys.exit(0)
    part, what, arm = sys.argv[1], sys.argv[2], sys.argv[3]
    rows = run_A(int(what), arm) if part == "A" else run_B(what, arm)
    prov = provenance.fields()
    with open(OUT, "a") as fh:
        for r in rows:
            r.update(prov)
            fh.write(json.dumps(r) + "\n")
