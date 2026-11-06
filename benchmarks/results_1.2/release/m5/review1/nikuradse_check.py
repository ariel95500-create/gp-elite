"""Compare the Nikuradse case-study records of 1.1.0 and 1.2.0 M3 (read-only):
which front entries change their printed expression, and the claims of the
case-study notebook (log of log forms, short forms, champion sizes)."""
import json
import re

B = "/home/user/gp-elite/benchmarks/"
P11 = B + "results_1.1/release/m3/case_nikuradse/real_nikuradse_auto_seed%d.json"
P12 = B + "results_1.2/release/m3/case_nikuradse/real_nikuradse_auto_seed%d.json"


def log_of_log(e):
    # a log( ... ) whose argument contains another log(
    for m in re.finditer(r"log\(", e):
        depth = 0
        i = m.end() - 1
        for j in range(i, len(e)):
            if e[j] == "(":
                depth += 1
            elif e[j] == ")":
                depth -= 1
                if depth == 0:
                    if "log(" in e[i + 1:j]:
                        return True
                    break
    return False


for s in range(5):
    a = json.load(open(P11 % s))
    b = json.load(open(P12 % s))
    print("== seed", s, "champion size", a["champion"]["size"], b["champion"]["size"], "r2", round(a["champion"]["r2"], 4), round(b["champion"]["r2"], 4))
    for part in ("pareto",):
        fa, fb = a[part], b[part]
        assert len(fa) == len(fb)
        for x, y in zip(fa, fb):
            ch = x["expr"] != y["expr"]
            print("  front size %3d r2 %.4f/%.4f %s loglog %s/%s %s" % (x["size"], x["r2"], y["r2"], "CHANGED" if ch else "same   ", log_of_log(x["expr"]), log_of_log(y["expr"]), y["expr"][:80] if x["size"] <= 9 else ""))
    fa, fb = a["holdout"]["pareto"], b["holdout"]["pareto"]
    for x, y in zip(fa, fb):
        ch = x["expr"] != y["expr"]
        print("  holdout size %3d %s loglog %s/%s bias %s" % (x["size"], "CHANGED" if ch else "same   ", log_of_log(x["expr"]), log_of_log(y["expr"]), round(b["holdout"]["bias_gp_sigma"].get(str(x["size"]), float('nan')), 3)))
    print("  seconds", a["seconds"], b["seconds"])
