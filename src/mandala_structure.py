import numpy as np

from src.octahedral_lookup import (
    GRAY_CODES, ALLOWED_TRANSITIONS, OCTAHEDRAL_EIGENVALUES,
    EIGENVALUE_CHARACTERS, gray_adjacent,
)


class MandalaMap:
    """
    Generate Fibonacci-scaled 8-petal mandala geometry in 2D.

    Each petal index (0-7) maps to an octahedral state via the G2B
    bridge encoding.  Cells carry their state index, Gray code, and
    eigenvalue character.  Adjacency respects O_h transition rules.
    """

    def __init__(self, u=20, depth=7):
        self.u = u  # Unit scale (nm)
        self.phi = (1 + 5**0.5) / 2
        self.depth = depth
        self.pos = [[0, 0]]  # Root cell at origin
        self.cell_states = [0]  # Root is state 0

        for d in range(1, depth + 1):
            r = self.u * (self.phi**d)
            for p in range(8):
                theta = (2 * np.pi / 8) * p
                self.pos.append([r * np.cos(theta), r * np.sin(theta)])
                self.cell_states.append(p)

        self.pos = np.array(self.pos)

    @property
    def num_cells(self):
        return len(self.pos)

    def cell_gray_code(self, cell_idx):
        """Return the Gray code for a cell's octahedral state."""
        return GRAY_CODES[self.cell_states[cell_idx]]

    def cell_eigenvalues(self, cell_idx):
        """Return eigenvalue triple for a cell's state."""
        return OCTAHEDRAL_EIGENVALUES[self.cell_states[cell_idx]]

    def cell_character(self, cell_idx):
        """Return eigenvalue character label for a cell's state."""
        return EIGENVALUE_CHARACTERS[self.cell_states[cell_idx]]

    def allowed_neighbors(self, cell_idx):
        """
        Return cell indices that are allowed transition targets
        based on O_h adjacency rules.

        Checks same-ring and adjacent-ring cells whose petal states
        are in the ALLOWED_TRANSITIONS graph.
        """
        state = self.cell_states[cell_idx]
        allowed_states = set(ALLOWED_TRANSITIONS.get(state, []))
        neighbors = []
        for j, other_state in enumerate(self.cell_states):
            if j != cell_idx and other_state in allowed_states:
                neighbors.append(j)
        return neighbors

    def gray_adjacent_cells(self, cell_idx):
        """
        Return cell indices whose states are Gray-adjacent
        (differ by exactly 1 bit in Gray code).
        """
        state = self.cell_states[cell_idx]
        neighbors = []
        for j, other_state in enumerate(self.cell_states):
            if j != cell_idx and gray_adjacent(state, other_state):
                neighbors.append(j)
        return neighbors

    def ring_cells(self, ring_depth):
        """Return cell indices for a given ring (0 = root, 1+ = petal rings)."""
        if ring_depth == 0:
            return [0]
        start = 1 + (ring_depth - 1) * 8
        end = start + 8
        return list(range(start, min(end, len(self.pos))))
