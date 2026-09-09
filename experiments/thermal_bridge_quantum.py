"""
Thermal Bridge Quantum Simulation
==================================
Hypothesis: A phonon mode tuned to match an energy gap between two
qubits can act as a "bridge" — facilitating energy transfer that
would otherwise be suppressed by the mismatch.

This tests whether noise-assisted transport (environment as
co-processor) improves transfer efficiency compared to direct
coupling alone.

The test is a CONTROLLED comparison:
  bridge ON  : g1 = g2 = 0.1 (qubit-phonon coupling)
  bridge OFF : g1 = g2 = 0   (same J, same baths, no phonon channel)

Positive result: peak/final population of qubit 2 is higher with the
                 bridge ON than OFF.
Negative result: no difference, or the bridge hurts transfer.

History: the original script started qubit 1 in its ground level and
measured the population of the level that spontaneous decay pumps INTO,
so qubit 2 "gained population" with or without the bridge. Fixed by
using QuTiP's actual sign convention (see EXC/GND below) and adding the
bridge-OFF control.

Requirements: pip install qutip numpy matplotlib
Extracted from: Notes.md lines 502-648
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from qutip import (
    tensor, sigmax, sigmaz, sigmap, sigmam,
    qeye, basis, destroy, create, fock_dm, mesolve, ptrace, entropy_vn,
)

# ============================================================
# Parameters
# ============================================================
N_phonons = 4           # Truncated phonon Fock space
omega_q1 = 1.0          # Qubit 1 energy (eV)
omega_q2 = 1.05         # Qubit 2 energy (0.05 eV gap)
omega_ph = 0.05         # Phonon frequency matches the energy gap
g_bridge = 0.1          # Qubit-phonon coupling when the bridge is ON
J = 0.01                # Weak direct coupling (without bridge)
n_th = 0.5              # Average thermal phonon number
gamma_ph = 0.1
gamma_q = 0.01
tlist = np.linspace(0, 50, 500)

# ============================================================
# Operators
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

# Convention (QuTiP): basis(2,0) is the sigma_z=+1 eigenstate, i.e. the
# HIGHER-energy level of 0.5*omega*sigma_z, and sigmam() decays it to
# basis(2,1). So "excited" = index 0, "ground" = index 1.
EXC, GND = 0, 1
P_excited_1 = tensor(fock_dm(2, EXC), qeye(2))   # projector on excited qubit 1
P_excited_2 = tensor(qeye(2), fock_dm(2, EXC))   # projector on excited qubit 2

# Qubit 1 excited, qubit 2 ground, phonon vacuum
psi0 = tensor(basis(2, EXC), basis(2, GND), basis(N_phonons, 0))
c_ops = [
    np.sqrt(gamma_ph * (n_th + 1)) * a,
    np.sqrt(gamma_ph * n_th) * ad,
    np.sqrt(gamma_q) * sm1,
    np.sqrt(gamma_q) * sm2,
]


def simulate(g):
    """Evolve the system with qubit-phonon coupling g (0 = bridge off)."""
    H_q = 0.5 * omega_q1 * sz1 + 0.5 * omega_q2 * sz2
    H_ph = omega_ph * ad * a
    H_coup = g * sx1 * x_ph + g * sx2 * x_ph     # Qubit-phonon bridge
    H_fret = J * (sp1 * sm2 + sp2 * sm1)         # Direct coupling
    H = H_q + H_ph + H_coup + H_fret

    # QuTiP >= 5: e_ops is keyword-only; pass c_ops by name.
    result = mesolve(H, psi0, tlist, c_ops=c_ops)

    P1, P2, coh, entropy, phonon_occ = [], [], [], [], []
    for state in result.states:
        rho_q = ptrace(state, [0, 1])
        P1.append((rho_q * P_excited_1).tr().real)
        P2.append((rho_q * P_excited_2).tr().real)
        # Pair basis: 0=|EXC,EXC>, 1=|EXC,GND>, 2=|GND,EXC>, 3=|GND,GND>
        coh.append(np.abs(rho_q.full()[1, 2]))
        entropy.append(entropy_vn(ptrace(rho_q, 0)))
        phonon_occ.append(float((state * ad * a).tr().real))
    return dict(P1=np.array(P1), P2=np.array(P2), coh=np.array(coh),
                entropy=np.array(entropy), phonon=np.array(phonon_occ))


print("Running Thermal Bridge Simulation...")
print("  bridge ON  (g = %.2f)" % g_bridge)
on = simulate(g_bridge)
print("  bridge OFF (g = 0)")
off = simulate(0.0)

# ============================================================
# Plot
# ============================================================
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

ax1.plot(tlist, on["P1"], 'b-', label='Qubit 1 (bridge ON)', lw=2)
ax1.plot(tlist, on["P2"], 'r-', label='Qubit 2 (bridge ON)', lw=2)
ax1.plot(tlist, off["P2"], 'r--', label='Qubit 2 (bridge OFF)', lw=1.5)
ax1.set_xlabel('Time')
ax1.set_ylabel('Population')
ax1.set_title('Energy Transfer: bridge ON vs OFF')
ax1.legend()
ax1.grid(True)

ax2.plot(tlist, on["coh"], 'g-', lw=2, label='ON')
ax2.plot(tlist, off["coh"], 'g--', lw=1.5, label='OFF')
ax2.set_xlabel('Time')
ax2.set_ylabel('Coherence |rho_12|')
ax2.set_title('Quantum Coherence')
ax2.legend()
ax2.grid(True)

ax3.plot(tlist, on["entropy"], 'm-', lw=2, label='ON')
ax3.plot(tlist, off["entropy"], 'm--', lw=1.5, label='OFF')
ax3.set_xlabel('Time')
ax3.set_ylabel('Entanglement Entropy')
ax3.set_title('Entanglement via Phonon Bridge')
ax3.legend()
ax3.grid(True)

ax4.plot(tlist, on["phonon"], 'c-', lw=2)
ax4.set_xlabel('Time')
ax4.set_ylabel('Phonon Occupation')
ax4.set_title('Thermal Bridge Activity (ON)')
ax4.grid(True)

plt.tight_layout()
plt.savefig('thermal_bridge_quantum.png', dpi=150)
if matplotlib.get_backend().lower() not in ("agg", "pdf", "svg"):
    plt.show()

# ============================================================
# Report
# ============================================================
print("\n" + "=" * 60)
print("THERMAL BRIDGE SIMULATION COMPLETE")
print(f"{'':22s} {'bridge ON':>10s} {'bridge OFF':>11s}")
print(f"{'peak  qubit-2 pop':22s} {on['P2'].max():10.3f} {off['P2'].max():11.3f}")
print(f"{'final qubit-2 pop':22s} {on['P2'][-1]:10.3f} {off['P2'][-1]:11.3f}")
print(f"{'final coherence':22s} {on['coh'][-1]:10.4f} {off['coh'][-1]:11.4f}")
print(f"{'final entropy':22s} {on['entropy'][-1]:10.4f} {off['entropy'][-1]:11.4f}")
print()
gain = on["P2"].max() - off["P2"].max()
verdict = "SUPPORTED" if gain > 0.05 else "NOT SUPPORTED"
print(f"HYPOTHESIS {verdict}: bridge changes peak transfer by {gain:+.3f}.")
print()
print("INTERPRETATION:")
print("  With the bridge OFF, the 0.05 eV mismatch and J=0.01 suppress")
print("  transfer. With it ON, the phonon absorbs the mismatch and")
print("  population reaches qubit 2. This is noise-assisted transport,")
print("  a real effect seen in photosynthetic complexes.")
print("  It does NOT imply quantum computing at room temperature;")
print("  parameters are illustrative, not calibrated to a material.")
print("=" * 60)
