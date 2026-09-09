"""
Firefly Swarm Stochastic Resonance Simulation
==============================================
Hypothesis: Coupled oscillators with intermediate noise synchronize
BETTER than with zero noise (stochastic resonance). At zero noise,
the system gets stuck in local clusters. At high noise, order is
destroyed. The "sweet spot" is in between.

Model: N pulse-coupled phase oscillators on a 2D plane. When oscillator
j fires (phase crosses 2π) it delivers an impulse
    Δθ_i = ε · exp(-d_ij/λ) · sin(θ_i - θ_j)
to every neighbour i. Between flashes each phase drifts at its own
frequency ω_i plus Gaussian noise of amplitude σ.

Positive result: R(σ) has an interior maximum — some σ>0 beats σ=0.
Negative result: R(σ) is monotone decreasing — noise only hurts here.

Observed (this model, N=200, ε=0.8, λ=2): NEGATIVE.
    σ=0.0 → R≈0.71,  σ=0.6 → R≈0.69,  σ=1.2 → R≈0.64,  σ=2.5 → R≈0.48
No interior peak. This swarm is not frustrated enough at σ=0 for noise
to help; stochastic resonance needs a landscape with trapped clusters
(e.g. weaker/longer-range coupling, bimodal frequencies, or a
sub-threshold periodic drive). See README "Results".

History: the original script multiplied the flash impulse by dt, which
capped each kick at ~0.008 rad. With that bug no σ produced R > 0.07,
so the three "regimes" in the old docstring were never reproducible.

Usage:
    python firefly_swarm.py            # single run at sigma=1.2
    python firefly_swarm.py 0.0        # single run at given sigma
    python firefly_swarm.py --sweep    # R vs sigma across 5 values

Requirements: pip install numpy matplotlib scipy
Extracted from: Notes.md lines 807-948
"""

import sys
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform

# ============================================================
# Parameters
# ============================================================
N = 200                 # Number of fireflies
L = 10.0                # Space size
dt = 0.01               # Time step
T_max = 100.0           # Total simulation time
omega_mean = 2.0        # Mean intrinsic frequency
omega_std = 0.3         # Disorder in frequencies
epsilon = 0.8           # Coupling strength (impulse per flash)
lambd = 2.0             # Spatial interaction range
SWEEP_SIGMAS = [0.0, 0.3, 0.6, 1.2, 2.5]


def compute_order_parameter(ph):
    """Kuramoto order parameter R in [0, 1]. R~1 = synchronized."""
    return np.abs(np.sum(np.exp(1j * ph))) / len(ph)


def simulate(sigma, seed=42, verbose=True):
    """Run one swarm at noise amplitude sigma. Returns (times, R values)."""
    rng = np.random.RandomState(seed)
    positions = rng.uniform(0, L, (N, 2))
    omegas = np.maximum(rng.normal(omega_mean, omega_std, N), 0.5)
    phases = rng.uniform(0, 2 * np.pi, N)

    dist_matrix = squareform(pdist(positions))
    influence_matrix = np.exp(-dist_matrix / lambd)
    np.fill_diagonal(influence_matrix, 0)

    if verbose:
        print(f"Running firefly simulation: N={N}, sigma={sigma}")
    n_steps = int(T_max / dt)
    time_vals, R_vals = [], []

    for step in range(n_steps):
        t = step * dt

        # Phase advance + noise
        phases += omegas * dt + sigma * np.sqrt(dt) * rng.randn(N)

        # Flash detection and pulse coupling.
        # A flash is an event, not a rate: the impulse is NOT scaled by dt.
        flashes = phases >= 2 * np.pi
        if np.any(flashes):
            for j in np.where(flashes)[0]:
                phase_diff = phases - phases[j]
                phases += epsilon * influence_matrix[:, j] * np.sin(phase_diff)
            phases[flashes] -= 2 * np.pi

        if step % 100 == 0:
            time_vals.append(t)
            R_vals.append(compute_order_parameter(phases))

    return np.array(time_vals), np.array(R_vals)


def tail_mean(R_vals):
    return float(np.mean(R_vals[-max(1, len(R_vals) // 10):]))


def report(sigma, R_vals):
    mean_R_last = tail_mean(R_vals)
    print("\n" + "=" * 60)
    print("FIREFLY SIMULATION COMPLETE")
    print(f"Noise level sigma = {sigma}")
    print(f"Final R = {R_vals[-1]:.3f}")
    print(f"Mean R (last 10%) = {mean_R_last:.3f}")
    print()
    if mean_R_last > 0.8:
        print("RESULT: Strong global synchronization.")
    elif mean_R_last > 0.4:
        print("RESULT: Partial synchronization (clusters).")
    else:
        print("RESULT: No coherent synchronization (noise-dominated).")
    print()
    print("Run with --sweep to test the stochastic-resonance hypothesis")
    print("(an interior peak of R vs sigma).")
    print("=" * 60)


def run_single(sigma):
    time_vals, R_vals = simulate(sigma)
    plt.figure(figsize=(10, 5))
    plt.plot(time_vals, R_vals, 'b-', lw=1.5)
    plt.xlabel('Time')
    plt.ylabel('Order Parameter R')
    plt.title(f'Firefly Synchronization (N={N}, sigma={sigma})')
    plt.ylim(0, 1)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'firefly_swarm_sigma{sigma}.png', dpi=150)
    if matplotlib.get_backend().lower() not in ("agg", "pdf", "svg"):
        plt.show()
    report(sigma, R_vals)


def run_sweep():
    results = []
    for s in SWEEP_SIGMAS:
        _, R_vals = simulate(s, verbose=False)
        results.append(tail_mean(R_vals))
        print(f"  sigma={s:<4}  mean R (last 10%) = {results[-1]:.3f}")

    plt.figure(figsize=(7, 4))
    plt.plot(SWEEP_SIGMAS, results, 'o-', lw=2)
    plt.xlabel('Noise amplitude sigma')
    plt.ylabel('Order parameter R (tail mean)')
    plt.title('Stochastic resonance test: R vs sigma')
    plt.ylim(0, 1)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('firefly_swarm_sweep.png', dpi=150)

    best = int(np.argmax(results))
    print("\n" + "=" * 60)
    print("STOCHASTIC RESONANCE SWEEP COMPLETE")
    print(f"Best sigma = {SWEEP_SIGMAS[best]} (R={results[best]:.3f}); "
          f"sigma=0 gives R={results[0]:.3f}")
    if best > 0 and results[best] > results[0] + 0.05:
        print("HYPOTHESIS SUPPORTED: intermediate noise beats zero noise.")
    else:
        print("HYPOTHESIS NOT SUPPORTED: no interior peak — noise only degrades")
        print("sync in this model. Stochastic resonance needs a frustrated")
        print("zero-noise state (trapped clusters); this swarm is not frustrated.")
    print("=" * 60)


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--sweep" in args:
        run_sweep()
    else:
        run_single(float(args[0]) if args else 1.2)
