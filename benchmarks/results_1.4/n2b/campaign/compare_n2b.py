# -*- coding: utf-8 -*-
"""Campaign N2b (benchmarks/results_1.4/PLAN.md, "Decision of the author
after the campaigns of N2 and S1"): the benches and the six criteria of
campaign N2, then its confirmation on new draws of the noise, read by
compare_n2.py (unchanged) from the paired records of the candidate with the
changes kept so far (A) and of the same with N2b (B). Only the name in the
verdict changes.

  python compare_n2b.py bench_A.jsonl bench_B.jsonl tp_A.jsonl tp_B.jsonl
  python compare_n2b.py --confirmation conf_A.jsonl conf_B.jsonl
"""
import io
import os
import sys
from contextlib import redirect_stdout

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "n2", "campaign"))
import compare_n2 as N                                      # noqa: E402


def main(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        if argv[0] == "--confirmation":
            N.confirmation(argv[1:])
        else:
            N.campaign(argv)
    out = buf.getvalue()
    for old, new in (("N2 NOT ADOPTED", "N2b NOT ADOPTED"),
                     ("N2 ADOPTED", "N2b ADOPTED"),
                     ("N2 NOT KEPT", "N2b NOT KEPT"),
                     ("N2 KEPT", "N2b KEPT"),
                     ("confirmation of N2)", "confirmation of N2b)")):
        out = out.replace(old, new)
    sys.stdout.write(out)


if __name__ == "__main__":
    main(sys.argv[1:])
