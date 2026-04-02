import numpy as np


class SOMSEngine:
    """
    Octahedral substrate engine with FRET coupling, energy landscape,
    and Metropolis-Hastings relaxation.

    Energy model (from Mandala-Computing / G2B bridge):
        E_coupling = J_ij * sin(|s_i - s_j| * pi/4)^2
        J_ij = 1/r^6  (FRET dipole-dipole)
        Metropolis acceptance: dE < 0 ? accept : accept with P=exp(-dE/T)
    """

    PHI = (1 + 5**0.5) / 2

    def __init__(self, num_cells=100):
        self.phi = self.PHI
        self.states = np.array([0, 45, 90, 135, 180, 225, 270, 315])  # 8 octahedral tensor angles
        self.orientations = np.random.choice(self.states, size=num_cells)

    def fret_coupling(self, dist_matrix):
        """Compute 1/r^6 dipole-dipole (FRET) coupling matrix."""
        with np.errstate(divide='ignore'):
            j_ij = 1.0 / np.power(dist_matrix, 6)
        j_ij[np.isinf(j_ij)] = 0
        return j_ij

    def energy_landscape(self, j_ij):
        """Compute total energy: E = sum J_ij * sin^2(theta_i - theta_j)."""
        total_e = 0
        for i in range(len(self.orientations)):
            diffs = np.radians(self.orientations[i] - self.orientations)
            total_e += np.sum(j_ij[i] * (np.sin(diffs)**2))
        return total_e / 2

    def _local_energy(self, cell_idx, j_ij):
        """Energy contribution from a single cell."""
        diffs = np.radians(self.orientations[cell_idx] - self.orientations)
        return np.sum(j_ij[cell_idx] * (np.sin(diffs)**2))

    def relax_step(self, j_ij, temperature=1.0):
        """
        One Metropolis-Hastings sweep: attempt to flip each cell to a
        random new octahedral state, accepting if dE < 0 or with
        probability exp(-dE/T).

        Returns (energy_after, n_accepted).
        """
        n = len(self.orientations)
        accepted = 0

        for i in np.random.permutation(n):
            old_state = self.orientations[i]
            old_e = self._local_energy(i, j_ij)

            # Propose random new state (different from current)
            candidates = self.states[self.states != old_state]
            new_state = np.random.choice(candidates)
            self.orientations[i] = new_state
            new_e = self._local_energy(i, j_ij)

            dE = new_e - old_e
            if dE <= 0 or np.random.random() < np.exp(-dE / max(temperature, 1e-12)):
                accepted += 1  # keep new state
            else:
                self.orientations[i] = old_state  # revert

        return self.energy_landscape(j_ij), accepted

    def anneal(self, j_ij, T_start=5.0, T_final=0.1, n_steps=200):
        """
        Simulated annealing: exponential cooling from T_start to T_final.

        Drives the system through thermodynamic relaxation to ground state.
        Cooling schedule matches KT annealer convention from G2B bridge:
            T(t) = T_start * (T_final / T_start)^(t/N)

        Returns list of (step, temperature, energy, accepted) tuples.
        """
        history = []
        T = T_start
        N = max(1, n_steps - 1)
        ratio = (T_final / T_start) ** (1.0 / N)

        for step in range(n_steps):
            energy, accepted = self.relax_step(j_ij, temperature=T)
            history.append((step, T, energy, accepted))
            T *= ratio

        return history
