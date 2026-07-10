"""Dimensional consistency audit [v0.3].

Answers the launch critique: an exponent like temperature/cycle is physically
meaningless. Declare your columns' units and this flags which Pareto forms are
dimensionally sound (candidate laws) versus empirical-only (still maybe useful,
but not physics).

Run: python examples/dimensional_audit.py
"""
import gp_elite.core as C
from gp_elite import check_dimensions, unit


def main():
    # The exact case from the Hacker News thread:
    # exp( cycle ^ (temperature / cycle) ) — argument of exp is not dimensionless
    bad = C.Node('exp', C.Node('pow', C.Node('X[0]'),
                               C.Node('/', C.Node('X[1]'), C.Node('X[0]'))))
    ok, msg = check_dimensions(bad, {0: unit('cycle'), 1: unit('temperature')})
    print("Battery-style formula  exp(cycle^(temperature/cycle)):")
    print(f"  sound = {ok}  ->  {msg}\n")

    # Kepler, by contrast, is internally consistent:
    kepler = C.Node('*', C.Node('sqrt', C.Node('X[0]')), C.Node('X[0]'))
    ok2, msg2 = check_dimensions(kepler, {0: unit('m')})
    print("Kepler  a*sqrt(a):")
    print(f"  sound = {ok2}  ->  {msg2}")

    print("\nThe first is a fit on normalized magnitudes, not a law. The audit")
    print("makes that explicit instead of letting a high R² imply physics.")


if __name__ == "__main__":
    main()
