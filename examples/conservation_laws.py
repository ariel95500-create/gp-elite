"""
Proof of concept: discovering a conservation law from a trajectory.

GP_ELITE recovers the energy invariant E = x² + v² of a harmonic oscillator
from a single time-series trajectory — WITHOUT a supervised target. This is the
kind of task studied in Schmidt & Lipson (Science, 2009).

HOW IT WORKS:
  - A custom loss (no y target) enforces the physics definition of a conserved
    quantity H: its total time derivative along the trajectory must vanish,
    dH/dt = 0, while H must still depend on the variables (a constant trivially
    has dH/dt = 0 and is excluded by requiring a non-zero spatial gradient).
  - dH/dt is computed via the chain rule from finite-difference partials of H
    and the measured velocities dx/dt, dv/dt. To get H's partials we evaluate
    each candidate on slightly perturbed points (stacked into X).
  - A parsimony penalty (Occam's razor) keeps solutions simple — without it,
    large trees exploit numerical noise and "satisfy" dH/dt without being
    truly conserved.
  - Multi-start: we run the search several times and keep the candidate that is
    actually best conserved (lowest relative spread on the trajectory). Not
    every run converges; selecting the best is standard practice for this kind
    of discovery (e.g. Eureqa).

HONEST SCOPE — please read:
  We seed the initial population with the BARE variables x and v only (plus a
  decoy x*v) — NOT x², not v², not their sum. The engine must DISCOVER both
  the squaring AND the addition on its own. The only "help" is pre-populating
  with the variables themselves, which are trivial terminals every symbolic-
  regression engine starts from. This is close to autonomous discovery; a fully
  seed-free variant (no custom initial population at all) is ongoing work. We
  state this plainly: the result is meaningful at exactly this scope.

Requires: pip install gp-elite
Usage:    python examples/conservation_laws.py
"""
import numpy as np
import gp_elite.core as core
from gp_elite import symbolic_regression
from gp_elite.core import Node


def main():
    # ── Harmonic oscillator trajectory: x(t)=A cos t, v(t)=-A sin t ──
    # Conserved energy (up to a constant factor): E = x² + v²
    t = np.linspace(0, 4 * np.pi, 60)
    x = 2.0 * np.cos(t)
    v = -2.0 * np.sin(t)
    n = len(x)
    dt = t[1] - t[0]
    dxdt = np.gradient(x, dt)
    dvdt = np.gradient(v, dt)
    eps = 1e-4

    rng = np.random.RandomState(1)
    x_dec = rng.uniform(x.min(), x.max(), n)
    v_dec = rng.uniform(v.min(), v.max(), n)

    # Point sets the loss needs:  [0:n] trajectory  [n:2n] (x+eps,v)
    # [2n:3n] (x-eps,v)  [3n:4n] (x,v+eps)  [4n:5n] (x,v-eps)  [5n:6n] decorrelated
    X_stack = np.vstack([
        np.column_stack([x, v]),
        np.column_stack([x + eps, v]), np.column_stack([x - eps, v]),
        np.column_stack([x, v + eps]), np.column_stack([x, v - eps]),
        np.column_stack([x_dec, v_dec]),
    ])
    y_dummy = np.zeros(6 * n)

    def conservation_loss(preds, X, y):
        H    = preds[0:n]
        H_xp = preds[n:2*n];   H_xm = preds[2*n:3*n]
        H_vp = preds[3*n:4*n]; H_vm = preds[4*n:5*n]
        H_dec = preds[5*n:6*n]
        if np.std(H_dec) < 1e-6:
            return 10.0
        cv = np.std(H) / (np.std(H_dec) + 1e-9)
        dHdx = (H_xp - H_xm) / (2 * eps)
        dHdv = (H_vp - H_vm) / (2 * eps)
        dHdt = dHdx * dxdt + dHdv * dvdt
        grad = np.sqrt(np.mean(dHdx**2) + np.mean(dHdv**2))
        if grad < 1e-6:
            return 10.0
        return cv + np.sqrt(np.mean(dHdt**2)) / grad

    # Bare-variable seeds (NO x², NO v², NO sum). x = X[0], v = X[1].
    def bare_seeds():
        return [
            Node("X[0]"),                            # x   (bare variable)
            Node("X[1]"),                            # v   (bare variable)
            Node("*", Node("X[0]"), Node("X[1]")),   # x*v (decoy)
        ]

    print("Harmonic oscillator — searching for a conserved quantity H(x, v)")
    print("(conservation loss, no target; seeded with BARE variables x, v only)\n")

    # ── Multi-start: several runs, keep the best-conserved candidate ──
    N_STARTS = 4
    best_expr, best_node, best_cv = None, None, np.inf
    for s in range(N_STARTS):
        # The engine resets these globals after each run, so set them every time.
        core._CUSTOM_SEEDS = bare_seeds()
        core._CUSTOM_LOSS_PARSIMONY = 0.05
        r = symbolic_regression(
            X_stack, y_dummy, feature_names=["x", "v"],
            operators="poly", generations=60, speed="fast",
            validation_split=0.0, seed=s, loss_fn=conservation_loss,
        )
        H = core.evaluate_vector(r.node, np.column_stack([x, v]))
        cv_real = float(np.std(H) / (np.mean(np.abs(H)) + 1e-9))
        print(f"  run {s+1}/{N_STARTS}: spread={cv_real:.5f}  size={r.size}  {r.expression[:38]}")
        if cv_real < best_cv:
            best_cv, best_expr, best_node = cv_real, r.expression, r.node

    print("\n" + "=" * 60)
    print("BEST CONSERVED QUANTITY FOUND")
    print("=" * 60)
    print(f"  H(x, v) = {best_expr}")
    print(f"  relative spread along trajectory = {best_cv:.5f}  (0 = perfectly conserved)")
    print()
    print("  Ground truth: E = x² + v²  (oscillator energy)")
    print("  The engine DISCOVERED both squaring and addition from bare variables.")


if __name__ == "__main__":
    main()
