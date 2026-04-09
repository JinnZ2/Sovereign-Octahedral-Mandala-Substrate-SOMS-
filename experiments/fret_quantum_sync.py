"""
FRET Quantum Synchronization Simulation
========================================
Hypothesis: Dipole-dipole (1/r^6) coupling between qubits with slight
energy disorder can sustain coherence at room temperature via the
Lindblad master equation.

This is a HYPOTHESIS TEST, not a proof. The simulation checks whether
coherence survives under realistic decay and dephasing. Results depend
heavily on parameter choices (coupling strength, noise rates).

Requirements: pip install qutip numpy matplotlib
Extracted from: Notes.md lines 277-380
"""

import numpy as np
import matplotlib.pyplot as plt
from qutip import (
    tensor, sigmax, sigmay, sigmaz, sigmam, sigmap,
    qeye, basis, mesolve, ptrace,
)

# ============================================================
# Parameters
# ============================================================
N_qubits = 3
tlist = np.linspace(0, 100, 1000)

# Energy levels (eV, slight disorder — real dipole systems have this)
energies = [1.0, 1.05, 0.98]

# Dipole-dipole coupling strengths (1/r^6 motivated, not true FRET)
J_12 = 0.1   # Between qubit 1 and 2
J_23 = 0.08  # Between qubit 2 and 3
J_13 = 0.01  # Far apart, weak coupling

# ============================================================
# Build Hamiltonian (XY coupling, no external drive)
# ============================================================
H = 0
for i, e in enumerate(energies):
    H += e * tensor([sigmaz() if j == i else qeye(2) for j in range(N_qubits)])

# XX coupling terms
for (a, b, J) in [(0, 1, J_12), (1, 2, J_23), (0, 2, J_13)]:
    H += J * tensor([sigmax() if i == a else (sigmax() if i == b else qeye(2)) for i in range(N_qubits)])

# YY coupling terms (full XY model)
for (a, b, J) in [(0, 1, J_12), (1, 2, J_23), (0, 2, J_13)]:
    H += J * tensor([sigmay() if i == a else (sigmay() if i == b else qeye(2)) for i in range(N_qubits)])

# ============================================================
# Noise via Lindblad collapse operators
# ============================================================
gamma_decay = 0.01    # Spontaneous emission rate
gamma_dephase = 0.05  # Dephasing from thermal bath

c_ops = []
for i in range(N_qubits):
    c_ops.append(np.sqrt(gamma_decay) * tensor(
        [sigmam() if j == i else qeye(2) for j in range(N_qubits)]))
    c_ops.append(np.sqrt(gamma_dephase) * tensor(
        [sigmaz() if j == i else qeye(2) for j in range(N_qubits)]))

# ============================================================
# Initial state: single excitation on qubit 1
# ============================================================
psi0 = basis(2, 1)
for i in range(1, N_qubits):
    psi0 = tensor(psi0, basis(2, 0))

# ============================================================
# Run simulation
# ============================================================
print("Running dipole-coupled quantum synchronization simulation...")
result = mesolve(H, psi0, tlist, c_ops, [])

# ============================================================
# Measure coherence and entanglement entropy
# ============================================================
coherence = []
entropies = []
for t_idx in range(len(tlist)):
    rho = result.states[t_idx]
    rho_12 = ptrace(rho, [0, 1])
    coh = np.abs(rho_12[0, 1])
    coherence.append(coh)

    rho_1 = ptrace(rho, [0])
    entropy = -np.real(np.trace(rho_1 * np.log(rho_1 + 1e-12)))
    entropies.append(entropy)

# ============================================================
# Plot
# ============================================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

ax1.plot(tlist, coherence, 'b-', lw=2)
ax1.set_xlabel('Time')
ax1.set_ylabel('Coherence |rho_12|')
ax1.set_title('Dipole-Coupled Quantum Synchronization (Room Temp Parameters)')
ax1.grid(True)

ax2.plot(tlist, entropies, 'r-', lw=2)
ax2.set_xlabel('Time')
ax2.set_ylabel('Entanglement Entropy')
ax2.set_title('Entanglement Emergence via Dipole Coupling')
ax2.grid(True)

plt.tight_layout()
plt.savefig('fret_quantum_sync.png', dpi=150)
plt.show()

# ============================================================
# Report
# ============================================================
print("\n" + "=" * 60)
print("SIMULATION COMPLETE")
print(f"Final coherence: {coherence[-1]:.4f}")
print(f"Final entanglement entropy: {entropies[-1]:.4f}")
print()
print("INTERPRETATION:")
print("  If coherence > 0.01 at t=100, dipole coupling sustains")
print("  some coherence under these noise parameters.")
print("  This does NOT prove room-temperature quantum computing —")
print("  real FRET coherence times are picoseconds, and this model")
print("  uses dimensionless time units with tuned parameters.")
print("=" * 60)
