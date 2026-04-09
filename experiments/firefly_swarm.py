"""
Firefly Swarm Stochastic Resonance Simulation
==============================================
Hypothesis: Coupled oscillators with intermediate noise synchronize
BETTER than with zero noise (stochastic resonance). At zero noise,
the system gets stuck in local clusters. At high noise, order is
destroyed. The "sweet spot" is in between.

This is a well-established phenomenon in nonlinear dynamics.
The simulation tests three regimes:
  - sigma=0.0  : frustrated, partial sync (local clusters)
  - sigma=1.2  : stochastic resonance, global synchronization
  - sigma=2.5  : noise-dominated, no coherent structure

Note: The analogy to "time crystals" is poetic. True time crystals
break continuous time-translation symmetry; firefly phase-locking
is a driven dissipative phenomenon, not a discrete time crystal.

Requirements: pip install numpy matplotlib scipy
Extracted from: Notes.md lines 807-948
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import pdist, squareform

# ============================================================
# Parameters (try sigma = 0.0, 1.2, 2.5)
# ============================================================
N = 200                 # Number of fireflies
L = 10.0                # Space size
dt = 0.01               # Time step
T_max = 100.0           # Total simulation time
omega_mean = 2.0        # Mean intrinsic frequency
omega_std = 0.3         # Disorder in frequencies
epsilon = 0.8           # Coupling strength
lambd = 2.0             # Spatial interaction range
sigma = 1.2             # Noise amplitude (KEY PARAMETER)

# ============================================================
# Initialize
# ============================================================
np.random.seed(42)
positions = np.random.uniform(0, L, (N, 2))
omegas = np.maximum(np.random.normal(omega_mean, omega_std, N), 0.5)
phases = np.random.uniform(0, 2 * np.pi, N)
last_flash_time = np.zeros(N)

dist_matrix = squareform(pdist(positions))
influence_matrix = np.exp(-dist_matrix / lambd)
np.fill_diagonal(influence_matrix, 0)


def compute_order_parameter(ph):
    """Kuramoto order parameter R in [0, 1]. R~1 = synchronized."""
    return np.abs(np.sum(np.exp(1j * ph))) / N


# ============================================================
# Simulation loop (headless — no animation dependency)
# ============================================================
print(f"Running firefly simulation: N={N}, sigma={sigma}")
n_steps = int(T_max / dt)
time_vals = []
R_vals = []

for step in range(n_steps):
    t = step * dt

    # Phase advance + noise
    phases += omegas * dt + sigma * np.sqrt(dt) * np.random.randn(N)

    # Flash detection and coupling
    flashes = phases >= 2 * np.pi
    if np.any(flashes):
        last_flash_time[flashes] = t
        for j in np.where(flashes)[0]:
            phase_diff = phases - phases[j]
            influence = epsilon * influence_matrix[:, j] * np.sin(phase_diff)
            phases += influence * dt
        phases[flashes] -= 2 * np.pi

    # Record order parameter periodically
    if step % 100 == 0:
        R = compute_order_parameter(phases)
        time_vals.append(t)
        R_vals.append(R)

# ============================================================
# Plot
# ============================================================
plt.figure(figsize=(10, 5))
plt.plot(time_vals, R_vals, 'b-', lw=1.5)
plt.xlabel('Time')
plt.ylabel('Order Parameter R')
plt.title(f'Firefly Synchronization (N={N}, sigma={sigma})')
plt.ylim(0, 1)
plt.grid(True)
plt.tight_layout()
plt.savefig(f'firefly_swarm_sigma{sigma}.png', dpi=150)
plt.show()

# ============================================================
# Report
# ============================================================
mean_R_last = np.mean(R_vals[-max(1, len(R_vals) // 10):])
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
print("Try running with sigma=0.0 and sigma=2.5 to compare.")
print("Stochastic resonance predicts a peak at intermediate noise.")
print("=" * 60)
