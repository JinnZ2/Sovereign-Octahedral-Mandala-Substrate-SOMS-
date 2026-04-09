"""
Octahedral Physics Engine — Dual-pathway relaxation inspired by protein folding.

Like a protein that holds both its amino-acid sequence (discrete) and its 3D
conformation (continuous) simultaneously — letting the energy landscape decide
which degrees of freedom dominate — this engine maintains two representations
of each cell and selects the coupling pathway based on the problem type.

Pathway A — Angular (continuous):
    States are angles [0°, 45°, ..., 315°].
    Coupling: E = J_ij * sin²(θ_i - θ_j).
    Best for: smooth optimization, SAT, TSP — problems where the energy
    landscape is continuous and gradient-like.

Pathway B — Tensor (discrete):
    States are eigenvalue triples from the octahedral lookup table.
    Coupling: E = J_ij * ||λ_i - λ_j||².
    Best for: factorization, graph coloring, constraint satisfaction —
    problems where discrete state identity matters more than angular distance.

The engine holds BOTH representations at all times (like primary sequence +
3D fold).  The problem's fitness function determines which pathway's energy
dominates the Metropolis acceptance criterion — the "folding funnel" picks
the path.
"""

import numpy as np

from src.octahedral_lookup import (
    OCTAHEDRAL_EIGENVALUES, GRAY_CODES, EIGENVALUE_CHARACTERS,
    ALLOWED_TRANSITIONS, phi_stability_score,
)


class SOMSEngine:
    """
    Dual-pathway octahedral substrate engine.

    Each cell simultaneously holds:
        - An angular state (0°–315°, continuous coupling)
        - A tensor state index (0–7, discrete eigenvalue coupling)

    The problem type biases which pathway dominates relaxation,
    just as a protein's sequence context biases which conformational
    degrees of freedom dominate the folding funnel.
    """

    PHI = (1 + 5**0.5) / 2

    # The 8 octahedral angles — one per face
    ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315])

    # Eigenvalue matrix: row i = eigenvalues of state i
    _EV_MATRIX = np.array([OCTAHEDRAL_EIGENVALUES[s] for s in range(8)])

    # Problem types and their natural pathway biases
    # alpha = 1.0 → pure angular, alpha = 0.0 → pure tensor
    PROBLEM_PROFILES = {
        "OPTIMIZATION":    {"alpha": 0.8, "description": "Smooth landscape, angular dominates"},
        "SAT":             {"alpha": 0.7, "description": "Boolean constraint, mostly angular"},
        "TSP":             {"alpha": 0.6, "description": "Route optimization, mixed"},
        "GRAPH_COLORING":  {"alpha": 0.3, "description": "Discrete states, tensor dominates"},
        "FACTORIZATION":   {"alpha": 0.2, "description": "Number structure, tensor dominates"},
        "PROTEIN_FOLDING": {"alpha": 0.5, "description": "Equal weighting — nature's balance"},
    }

    def __init__(self, num_cells=100, problem_type="PROTEIN_FOLDING"):
        self.phi = self.PHI
        self.num_cells = num_cells
        self.problem_type = problem_type

        # Pathway mixing ratio: how much angular vs tensor
        profile = self.PROBLEM_PROFILES.get(problem_type, self.PROBLEM_PROFILES["PROTEIN_FOLDING"])
        self.alpha = profile["alpha"]

        # === DUAL REPRESENTATION ===
        # Discrete state indices (0-7) — the "primary sequence"
        self.state_indices = np.random.randint(0, 8, size=num_cells)
        # Angular representation — derived from state indices
        self.orientations = self.ANGLES[self.state_indices]

    @property
    def states(self):
        """Backward-compatible: the 8 angle values."""
        return self.ANGLES

    # ------------------------------------------------------------------
    # Dual-state synchronization
    # ------------------------------------------------------------------

    def _sync_angle_to_index(self, cell_idx):
        """After an angular change, snap to nearest octahedral state."""
        self.state_indices[cell_idx] = self.orientations[cell_idx] // 45

    def _sync_index_to_angle(self, cell_idx):
        """After an index change, update the angle."""
        self.orientations[cell_idx] = self.ANGLES[self.state_indices[cell_idx]]

    # ------------------------------------------------------------------
    # State accessors
    # ------------------------------------------------------------------

    def cell_gray_code(self, cell_idx):
        """Gray code for a cell's current state."""
        return GRAY_CODES[self.state_indices[cell_idx]]

    def cell_eigenvalues(self, cell_idx):
        """Eigenvalue triple for a cell's current state."""
        return OCTAHEDRAL_EIGENVALUES[self.state_indices[cell_idx]]

    def cell_character(self, cell_idx):
        """Eigenvalue character label."""
        return EIGENVALUE_CHARACTERS[self.state_indices[cell_idx]]

    def cell_phi_score(self, cell_idx):
        """Golden-ratio stability score (0-1) for a cell."""
        return phi_stability_score(self.cell_eigenvalues(cell_idx))

    # ------------------------------------------------------------------
    # Pathway A — Angular coupling (continuous)
    # ------------------------------------------------------------------

    def fret_coupling(self, dist_matrix):
        """Compute 1/r^6 dipole-dipole coupling matrix (FRET-inspired, not true FRET)."""
        with np.errstate(divide='ignore'):
            j_ij = 1.0 / np.power(dist_matrix, 6)
        j_ij[np.isinf(j_ij)] = 0
        return j_ij

    def angular_energy(self, j_ij):
        """Pathway A: E = sum J_ij * sin²(θ_i - θ_j)."""
        total_e = 0
        for i in range(len(self.orientations)):
            diffs = np.radians(self.orientations[i] - self.orientations)
            total_e += np.sum(j_ij[i] * (np.sin(diffs) ** 2))
        return total_e / 2

    def _angular_local_energy(self, cell_idx, j_ij):
        """Local angular energy for one cell."""
        diffs = np.radians(self.orientations[cell_idx] - self.orientations)
        return np.sum(j_ij[cell_idx] * (np.sin(diffs) ** 2))

    # ------------------------------------------------------------------
    # Pathway B — Tensor coupling (discrete)
    # ------------------------------------------------------------------

    def tensor_energy(self, j_ij):
        """Pathway B: E = sum J_ij * ||λ_i - λ_j||²."""
        ev = self._EV_MATRIX[self.state_indices]  # (N, 3)
        total_e = 0
        for i in range(len(self.state_indices)):
            diffs = ev[i] - ev  # (N, 3)
            sq_dists = np.sum(diffs ** 2, axis=1)  # (N,)
            total_e += np.sum(j_ij[i] * sq_dists)
        return total_e / 2

    def _tensor_local_energy(self, cell_idx, j_ij):
        """Local tensor energy for one cell."""
        ev = self._EV_MATRIX[self.state_indices]
        diff = ev[cell_idx] - ev
        sq_dists = np.sum(diff ** 2, axis=1)
        return np.sum(j_ij[cell_idx] * sq_dists)

    # ------------------------------------------------------------------
    # Combined energy — the folding funnel
    # ------------------------------------------------------------------

    def energy_landscape(self, j_ij):
        """
        Combined energy: α * E_angular + (1-α) * E_tensor.

        The mixing ratio α is set by the problem type, just as a protein's
        folding funnel is shaped by the interplay of backbone angles
        (continuous) and side-chain contacts (discrete).
        """
        E_ang = self.angular_energy(j_ij)
        E_ten = self.tensor_energy(j_ij)
        return self.alpha * E_ang + (1 - self.alpha) * E_ten

    def _local_energy(self, cell_idx, j_ij):
        """Combined local energy for one cell."""
        E_ang = self._angular_local_energy(cell_idx, j_ij)
        E_ten = self._tensor_local_energy(cell_idx, j_ij)
        return self.alpha * E_ang + (1 - self.alpha) * E_ten

    # ------------------------------------------------------------------
    # Relaxation — Metropolis-Hastings with dual-path proposals
    # ------------------------------------------------------------------

    def relax_step(self, j_ij, temperature=1.0):
        """
        One Metropolis sweep with pathway-aware proposals.

        Like protein folding, the proposal mechanism respects both
        representations:
        - Angular path: propose any of the 7 other angles
        - Tensor path: propose only O_h-allowed transitions (preserving
          geometric adjacency, like side-chain rotamer flips)

        The acceptance criterion uses combined energy.
        """
        n = len(self.orientations)
        accepted = 0

        for i in np.random.permutation(n):
            old_index = self.state_indices[i]
            old_angle = self.orientations[i]
            old_e = self._local_energy(i, j_ij)

            # Pathway-biased proposal:
            # With probability α, propose freely (angular); else
            # propose only O_h-adjacent states (tensor-respecting)
            if np.random.random() < self.alpha:
                # Angular proposal: any state except current
                candidates = np.arange(8)
                candidates = candidates[candidates != old_index]
                new_index = np.random.choice(candidates)
            else:
                # Tensor proposal: only allowed transitions
                allowed = ALLOWED_TRANSITIONS.get(old_index, list(range(8)))
                if not allowed:
                    allowed = list(range(8))
                new_index = np.random.choice(allowed)

            # Apply proposal to BOTH representations
            self.state_indices[i] = new_index
            self.orientations[i] = self.ANGLES[new_index]
            new_e = self._local_energy(i, j_ij)

            dE = new_e - old_e
            if dE <= 0 or np.random.random() < np.exp(-dE / max(temperature, 1e-12)):
                accepted += 1  # keep new state
            else:
                # Revert BOTH representations
                self.state_indices[i] = old_index
                self.orientations[i] = old_angle

        return self.energy_landscape(j_ij), accepted

    def anneal(self, j_ij, T_start=5.0, T_final=0.1, n_steps=200):
        """
        Simulated annealing with dual-pathway relaxation.

        The cooling schedule guides the system down the folding funnel.
        At high T, both pathways explore freely.
        At low T, the dominant pathway crystallizes the solution.
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

    # ------------------------------------------------------------------
    # Pathway C — Cayley coupling (group-geometric)
    # ------------------------------------------------------------------

    _cayley_energy_cache = None

    def _get_cayley_energy(self):
        """Lazy-load the CayleyEnergy model (builds O_h once)."""
        if SOMSEngine._cayley_energy_cache is None:
            from src.geometric_state_algebra import OhGroup, CayleyEnergy
            SOMSEngine._cayley_energy_cache = CayleyEnergy(OhGroup.instance())
        return SOMSEngine._cayley_energy_cache

    def cayley_energy(self, j_ij):
        """
        Pathway C: E = sum J_ij * (φ · d_cayley(g_i, g_j) / diam)².

        Uses the Cayley graph of O_h to measure the true geometric
        distance between symmetry operations, not just |s_i - s_j|.
        """
        ce = self._get_cayley_energy()
        dm = ce.cayley_distance_matrix(self.state_indices)
        diam = ce._diameter
        total_e = 0.0
        n = len(self.state_indices)
        for i in range(n):
            for j in range(i + 1, n):
                norm = dm[i][j] / max(diam, 1)
                total_e += j_ij[i, j] * (self.PHI * norm) ** 2
        return total_e

    # ------------------------------------------------------------------
    # Pathway diagnostics
    # ------------------------------------------------------------------

    def pathway_report(self, j_ij):
        """
        Report energy contribution from each pathway independently.
        Shows which pathway is "winning" — like measuring backbone
        vs side-chain contributions to protein stability.
        """
        E_ang = self.angular_energy(j_ij)
        E_ten = self.tensor_energy(j_ij)
        E_combined = self.alpha * E_ang + (1 - self.alpha) * E_ten

        # Average phi-stability across all cells
        phi_scores = [self.cell_phi_score(i) for i in range(self.num_cells)]
        avg_phi = np.mean(phi_scores)

        report = {
            "problem_type": self.problem_type,
            "alpha": self.alpha,
            "angular_energy": E_ang,
            "tensor_energy": E_ten,
            "combined_energy": E_combined,
            "angular_contribution": self.alpha * E_ang,
            "tensor_contribution": (1 - self.alpha) * E_ten,
            "dominant_pathway": "angular" if self.alpha * E_ang > (1 - self.alpha) * E_ten else "tensor",
            "avg_phi_stability": avg_phi,
        }

        # Include Cayley pathway energy when available
        try:
            E_cay = self.cayley_energy(j_ij)
            report["cayley_energy"] = E_cay
        except Exception:
            pass

        return report
