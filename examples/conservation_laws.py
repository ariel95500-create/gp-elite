"""
Discovering a conservation law from a trajectory — no target, no seeds.

GP_ELITE recovers the energy invariant E = x² + v² of a harmonic oscillator
from a single time-series trajectory, with NO supervised target and NO seeded
building blocks. The initial population is fully random; the engine discovers
on its own which variables matter, that they must be squared, and that the
squares must be added. This reproduces the kind of result in Schmidt & Lipson
(Science, 2009), in pure Python.

HOW IT WORKS:
  - A custom loss (no y target) enforces the physics definition of a conserved
    quantity H: its total time derivative along the trajectory must vanish,
    dH/dt = 0, while H must still depend on the variables (a constant trivially
    has dH/dt = 0 and is excluded by requiring a non-zero spatial gradient).
  - dH/dt is built via the chain rule from finite-difference partials of H and
    the measured velocities dx/dt, dv/dt. H's partials come from evaluating
    each candidate on slightly perturbed points (stacked into X).
  - A parsimony penalty (Occam's razor) keeps solutions simple — without it,
    large trees exploit numerical noise and "satisfy" dH/dt without being
    truly conserved.
  - Multi-start: each run finds the law with ~50% probability, so we run the
    search several times and keep the candidate that is genuinely best
    conserved (lowest relative spread on the trajectory). Running many starts
    and selecting the best is standard practice for symbolic discovery (e.g.
    Eureqa ran very many restarts).

HONEST SCOPE:
  No seeds are provided here — this is autonomous discovery from a random
  start. The only inputs are the trajectory and the physics criterion
  (dH/dt = 0). Per-run success is stochastic (~50%); the multi-start loop is
  what makes the reported result reliable. Takes ~1-2 minutes.

Requires: pip install gp-elite
Usage:    python examples/conservation_laws.py
"""
import numpy as np
import gp_elite.core as core
from gp_elite import symbolic_regression


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

    print("Harmonic oscillator — autonomous search for a conserved quantity H(x, v)")
    print("(conservation loss, NO target, NO seeds, fully random start)\n")

    # ── Multi-start: no seeds; keep the best-conserved candidate ──
    N_STARTS = 6
    best_expr, best_cv = None, np.inf
    for s in range(N_STARTS):
        core._CUSTOM_SEEDS = None              # no seeds: fully random population
        core._CUSTOM_LOSS_PARSIMONY = 0.05     # reset every run (cleared after each)
        r = symbolic_regression(
            X_stack, y_dummy, feature_names=["x", "v"],
            operators="poly", generations=55, speed="fast",
            validation_split=0.0, seed=s, loss_fn=conservation_loss,
        )
        H = core.evaluate_vector(r.node, np.column_stack([x, v]))
        cv_real = float(np.std(H) / (np.mean(np.abs(H)) + 1e-9))
        flag = "✓" if cv_real < 0.01 else " "
        print(f"  run {s+1}/{N_STARTS}: spread={cv_real:11.5f}  size={r.size:2d}  {flag} {r.expression[:34]}")
        if cv_real < best_cv:
            best_cv, best_expr = cv_real, r.expression

    print("\n" + "=" * 62)
    print("BEST CONSERVED QUANTITY FOUND")
    print("=" * 62)
    print(f"  H(x, v) = {best_expr}")
    print(f"  relative spread along trajectory = {best_cv:.5f}  (0 = perfectly conserved)")
    print()
    print("  Ground truth: E = x² + v²  (oscillator energy)")
    if best_cv < 0.01:
        print("  The engine discovered the energy invariant from a random start,")
        print("  with no target and no seeds — only the physics criterion dH/dt = 0.")
    else:
        print("  (No run converged this time — re-run; per-run success is ~50%.)")


if __name__ == "__main__":
    main()
