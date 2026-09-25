"""Garde pres du domaine (0.7) : etude appariee sur donnees reelles PMLB.

Meme seed, meme pli : bras ON (garde active) et bras OFF (sondes desactivees).
Seul le choix final peut differer ; les fronts de Pareto doivent etre
identiques. Criteres fixes avant : fronts identiques, aucun effondrement
ajoute, R2 median non degrade ; au niveau des candidats, precision/rappel du
drapeau « stable » contre l'explosion reelle sur le test (ecart > 50 plages
de y, ou non fini).

Resultat (0.7.0, results_0.7/near_guard.jsonl) : 6 jeux x 2 seeds x 5 plis,
285 candidats du front. La garde n'a jamais agi : fronts et modeles rendus
identiques dans les 60 plis ; aucun candidat ne s'est effondre sur le test
(ecart max 4.7 plages de y). Cout mesure nul ; benefice non observable a ce
regime (preset fast, 40 generations). Mesure faite avec le candidat 0.7
d'avant le passage de normalize='auto' a divmax (commit 3a00929) ; a refaire
sur la version publiee avant de citer ces chiffres pour elle.

Usage : python near_guard_study.py <dataset> <seed> <on|off>
        python near_guard_study.py --summary [fichier]
"""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pmlb_frozen
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results_0.7", "near_guard.jsonl")

def load(name):
    return pmlb_frozen.load(name)

def r2(y, p):
    ss = float(np.sum((y - y.mean()) ** 2)) or 1e-30
    with np.errstate(all="ignore"):
        v = 1 - float(np.sum((y - p) ** 2) / ss)
    return v if np.isfinite(v) else -1e30

def main():
    name, seed, arm = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    import gp_elite.core as C
    from gp_elite.api import symbolic_regression
    if arm == "off":
        C._build_near_probes = lambda *a, **k: None          # garde desactivee
    from sklearn.model_selection import KFold
    X, y = load(name)
    out = []
    for k, (tr, te) in enumerate(KFold(5, shuffle=True, random_state=seed).split(X)):
        swaps0 = C._NEAR_GUARD_SWAPS
        res = symbolic_regression(X[tr], y[tr], generations=40, speed="fast",
                                  restarts=1, parallel=False, seed=seed)
        c, rngy = float(np.median(y[tr])), max(float(np.ptp(y[tr])), 1e-12)
        cands = []
        for e in (res.pareto or []):
            with np.errstate(all="ignore"):
                p = np.asarray(e.predict(X[te]), float)
            dev = float(np.max(np.abs(p - c)) / rngy) if np.all(np.isfinite(p)) else float("inf")
            cands.append(dict(expr=e.expression, size=int(e.size),
                              stable=bool(C._near_domain_stable(e.node)) if arm == "on" else None,
                              test_r2=r2(y[te], p), test_dev=dev))
        with np.errstate(all="ignore"):
            pc = np.asarray(res.predict(X[te]), float)
        out.append(dict(dataset=name, seed=seed, fold=k, arm=arm,
                        champ_expr=res.expression, champ_size=int(res.size),
                        champ_test_r2=r2(y[te], pc), swapped=C._NEAR_GUARD_SWAPS > swaps0,
                        pareto_sig=[x["expr"] for x in cands], cands=cands))
    with open(OUT, "a") as fh:
        for o in out: fh.write(json.dumps(o) + "\n")
    print(name, seed, arm, ["%.3g" % o["champ_test_r2"] for o in out], flush=True)

def summary(path=OUT):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    key = lambda r: (r["dataset"], r["seed"], r["fold"])
    on = {key(r): r for r in rows if r["arm"] == "on"}
    off = {key(r): r for r in rows if r["arm"] == "off"}
    ks = sorted(set(on) & set(off))
    print("plis apparies            :", len(ks))
    print("fronts identiques        :", sum(on[k]["pareto_sig"] == off[k]["pareto_sig"] for k in ks))
    print("modeles rendus identiques:", sum(on[k]["champ_expr"] == off[k]["champ_expr"] for k in ks))
    print("interventions de la garde:", sum(on[k]["swapped"] for k in ks))
    c = [x for k in ks for x in on[k]["cands"]]
    expl = lambda x: (not np.isfinite(x["test_dev"])) or x["test_dev"] > 50
    print("candidats du front       : %d ; instables %d ; effondres sur le test %d ; ecart max %.1f plages de y"
          % (len(c), sum(not x["stable"] for x in c), sum(expl(x) for x in c), max(x["test_dev"] for x in c)))
    for arm, d in (("on", on), ("off", off)):
        v = np.array([d[k]["champ_test_r2"] for k in ks])
        print("R2 test %-3s : moyenne %.4f  mediane %.4f  pire %.4f  effondrements %d"
              % (arm, v.mean(), np.median(v), v.min(), int((v < 0).sum())))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--summary"]:
        summary(sys.argv[2] if len(sys.argv) > 2 else OUT)
    else:
        main()
