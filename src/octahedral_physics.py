import numpy as np


class SOMSEngine:
    """Octahedral substrate engine with FRET coupling and energy landscape."""

    def __init__(self, num_cells=100):
        self.phi = (1 + 5**0.5) / 2
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
