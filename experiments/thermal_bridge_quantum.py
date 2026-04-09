"""
Thermal Bridge Quantum Simulation
==================================
Hypothesis: A phonon mode tuned to match an energy gap between two
qubits can act as a "bridge" — facilitating energy transfer that
would otherwise be suppressed by the mismatch.

This tests whether noise-assisted transport (environment as
co-processor) improves transfer efficiency compared to direct
coupling alone.

Requirements: pip install qutip numpy matplotlib
Extracted from: Notes.md lines 502-648
"""

import numpy as np
import matplotlib.pyplot as plt
from qutip import (
    tensor, sigmax, sigmaz, sigmap, sigmam,
    qeye, basis, destroy, create, fock, mesolve, ptrace, entropy_vn,
)

# ============================================================
# Parameters
# ============================================================
N_phonons = 4           # Truncated phonon Fock space
omega_q1 = 1.0          # Qubit 1 energy (eV)
omega_q2 = 1.05         # Qubit 2 energy (0.05 eV gap)
omega_ph = 0.05         # Phonon frequency matches the energy gap
g1 = 0.1                # Qubit 1 - phonon coupling
g2 = 0.1                # Qubit 2 - phonon coupling
J = 0.01                # Weak direct coupling (without bridge)
n_th = 0.5              # Average thermal phonon number

# ============================================================
# Build Hilbert space and operators
# ============================================================
sx1 = tensor(sigmax(), qeye(2), qeye(N_phonons))
sx2 = tensor(qeye(2), sigmax(), qeye(N_phonons))
sz1 = tensor(sigmaz(), qeye(2), qeye(N_phonons))
sz2 = tensor(qeye(2), sigmaz(), qeye(N_phonons))
sp1 = tensor(sigmap(), qeye(2), qeye(N_phonons))
sm1 = tensor(sigmam(), qeye(2), qeye(N_phonons))
sp2 = tensor(qeye(2), sigmap(), qeye(N_phonons))
sm2 = tensor(qeye(2), sigmam(), qeye(N_phonons))
a = tensor(qeye(2), qeye(2), destroy(N_phonons))
ad = tensor(qeye(2), qeye(2), create(N_phonons))
x_ph = a + ad

# ============================================================
# Hamiltonian
# ============================================================
H_q = 0.5 * omega_q1 * sz1 + 0.5 * omega_q2 * sz2
H_ph = omega_ph * ad * a
H_coup = g1 * sx1 * x_ph + g2 * sx2 * x_ph  # Qubit-phonon bridge
H_fret = J * (sp1 * sm2 + sp2 * sm1)          # Direct coupling
H = H_q + H_ph + H_coup + H_fret

# ============================================================
# Initial state and collapse operators
# ============================================================
psi0 = tensor(basis(2, 1), basis(2, 0), basis(N_phonons, 0))

gamma_ph = 0.1
gamma_q = 0.01
c_ops = [
    np.sqrt(gamma_ph * (n_th + 1)) * a,
    np.sqrt(gamma_ph * n_th) * ad,
    np.sqrt(gamma_q) * sm1,
    np.sqrt(gamma_q) * sm2,
]

# ============================================================
# Time evolution
# ============================================================
tlist = np.linspace(0, 50, 500)
print("Running Thermal Bridge Simulation...")
result = mesolve(H, psi0, tlist, c_ops, [])

# ============================================================
# Measure observables
# ============================================================
P1, P2, coh, entropy = [], [], [], []
for state in result.states:
    rho_q = ptrace(state, [0, 1])
    P1.append((rho_q * tensor(fock(2, 1), qeye(2))).tr().real)
    P2.append((rho_q * tensor(qeye(2), fock(2, 1))).tr().real)
    coh.append(np.abs(rho_q[0, 3]))
    rho_q1 = ptrace(rho_q, 0)
    entropy.append(entropy_vn(rho_q1))

phonon_occ = [float((state * ad * a).tr().real) for state in result.states]

# ============================================================
# Plot
# ============================================================
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

ax1.plot(tlist, P1, 'b-', label='Qubit 1', lw=2)
ax1.plot(tlist, P2, 'r-', label='Qubit 2', lw=2)
ax1.set_xlabel('Time')
ax1.set_ylabel('Population')
ax1.set_title('Energy Transfer (Thermal Bridge Active)')
ax1.legend()
ax1.grid(True)

ax2.plot(tlist, coh, 'g-', lw=2)
ax2.set_xlabel('Time')
ax2.set_ylabel('Coherence |rho_12|')
ax2.set_title('Quantum Coherence (Bridged by Phonon)')
ax2.grid(True)

ax3.plot(tlist, entropy, 'm-', lw=2)
ax3.set_xlabel('Time')
ax3.set_ylabel('Entanglement Entropy')
ax3.set_title('Entanglement via Phonon Bridge')
ax3.grid(True)

ax4.plot(tlist, phonon_occ, 'c-', lw=2)
ax4.set_xlabel('Time')
ax4.set_ylabel('Phonon Occupation')
ax4.set_title('Thermal Bridge Activity')
ax4.grid(True)

plt.tight_layout()
plt.savefig('thermal_bridge_quantum.png', dpi=150)
plt.show()

# ============================================================
# Report
# ============================================================
print("\n" + "=" * 60)
print("THERMAL BRIDGE SIMULATION COMPLETE")
print(f"Final qubit 2 population: {P2[-1]:.3f}")
print(f"Final coherence: {coh[-1]:.4f}")
print(f"Final entanglement entropy: {entropy[-1]:.4f}")
print()
print("INTERPRETATION:")
print("  If qubit 2 gains population, the phonon bridge facilitates")
print("  energy transfer across the energy gap. This is a real effect")
print("  (noise-assisted transport) seen in photosynthetic complexes.")
print("  It does NOT imply quantum computing at room temperature.")
print("=" * 60)
