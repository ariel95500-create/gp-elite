"""The TP diagnostic by experiment, read from the records of campaign H1 of
1.2 and of its confirmation (../../results_1.2/h1/campaign/tp_H1*.jsonl):
draws 0 to 9, 10 and 20 points, 2 % and 5 % noise, under the defaults. The
engine is the candidate of that campaign, the engine of 1.1.0 with the stop
on patience of 1.2; its version string still reads 1.1.0. Since then, 1.2.0
changed the printed formula only (X1) and 1.3.0 left the pool `physical` as
it was, so for nine of the ten experiments these are the models of 1.3.0.
Snell's law uses the pool `trig`; with the arcsine of 1.3 its law comes back
in none of 40 fits either (../../results_1.3/a3/campaign/).

  python tp_by_experiment.py > tp_by_experiment.txt
"""
import json
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CAMP = os.path.normpath(os.path.join(HERE, "..", "..", "results_1.2", "h1", "campaign"))


def main():
    recs = []
    for name in ("tp_H1.jsonl", "tp_H1_conf.jsonl"):
        recs += [json.loads(line) for line in open(os.path.join(CAMP, name))]
    print("%d fits, version string of the engine %s (the candidate of campaign H1)"
          % (len(recs), sorted({r["engine_version"] for r in recs})))
    t = defaultdict(lambda: [0, 0, 0])
    for r in recs:
        k = (r["exp"], r["arm"])
        t[k][0] += 1
        t[k][1] += bool(r.get("law"))
        t[k][2] += bool(r.get("useful"))
    order = []
    for r in recs:
        if r["exp"] not in order:
            order.append(r["exp"])
    print("\nexperiment        plain: law / useful, of 40   units: law / useful, of 40")
    for e in order:
        p, u = t[(e, "plain")], t[(e, "units")]
        print("  %-16s %2d / %2d                      %2d / %2d" % (e, p[1], p[2], u[1], u[2]))
    for arm in ("plain", "units"):
        print("%s arm: the law in %d fits of %d" % (
            arm, sum(t[(e, arm)][1] for e in order), sum(t[(e, arm)][0] for e in order)))

    print("\nplain arm, the fits without the law, by points and noise, and what "
          "they return (the first four):")
    for e in order:
        rr = [r for r in recs if r["exp"] == e and r["arm"] == "plain"]
        bad = [r for r in rr if not r.get("law")]
        if not bad:
            continue
        by = Counter((r["n"], r["noise"]) for r in bad)
        print("  %s: %d of %d; %s" % (e, len(bad), len(rr), ", ".join(
            "%d at %d points and %g %%" % (c, k[0], 100 * k[1])
            for k, c in sorted(by.items()))))
        for r in sorted(bad, key=lambda r: (r["noise"], r["n"], r["draw"]))[:4]:
            print("      %d points, %g %%, draw %d: %s" % (
                r["n"], 100 * r["noise"], r["draw"], r["expr"][:96]))
    print("\nplain arm, formulas that carry an additive constant among the fits "
          "with the law (their text starts with a number followed by + or -):")
    import re
    pat = re.compile(r"^-?\d[\d.e+-]*\s[+-]\s")
    tot = [0, 0]
    for e in order:
        ok = [r for r in recs if r["exp"] == e and r["arm"] == "plain" and r.get("law")]
        if ok:
            c = sum(bool(pat.match(r["expr"])) for r in ok)
            print("  %-16s %2d of %2d" % (e, c, len(ok)))
            if e != "refroidissement":        # its law has an additive constant
                tot[0] += c
                tot[1] += len(ok)
    print("  the experiments whose law has no additive constant (all but "
          "refroidissement): %d of %d" % tuple(tot))


if __name__ == "__main__":
    main()
