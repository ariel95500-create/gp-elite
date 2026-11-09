"""Second review of M5: the thirteen reference configurations of M1, compared
again without their time (time_s)."""
import json, os
R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
def L(p):
    d = json.load(open(os.path.join(R, p))); d.pop("time_s", None); return d
ta = tb = 0.0
for n in ("A_feyn", "B_cpu", "C_big", "D_units", "E_minmax", "F_robust", "G_restarts",
          "H_parallel", "I_sklearn", "J_extrap", "K_thorough", "L_standard", "M_twice"):
    a = L("release/M1_equiv_1.2.0/%s.json" % n); b = L("release/M1_equiv_1.3.0/%s.json" % n)
    c = L("a3/equiv_a3/%s.json" % n)
    ta += json.load(open(os.path.join(R, "release/M1_equiv_1.2.0/%s.json" % n)))["time_s"]
    tb += json.load(open(os.path.join(R, "release/M1_equiv_1.3.0/%s.json" % n)))["time_s"]
    pool = {"E_minmax": "full", "L_standard": "trig"}.get(n, "physical")  # speed_equivalence.py CONFIGS
    print("%-11s pool %-8s 1.2.0 == 1.3.0: %-5s  A3 candidate == 1.3.0: %-5s arcsine in 1.3.0: %s" % (
        n, pool, a == b, c == b, "arcsin" in json.dumps(b)))
print("total time %.1f s -> %.1f s" % (ta, tb))
