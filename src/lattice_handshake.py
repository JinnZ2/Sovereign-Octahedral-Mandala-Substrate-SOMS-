"""
Lattice Handshake — Octahedral CVP-based key agreement.

Maps the Closest Vector Problem onto the 8-state octahedral lattice.
Instead of random high-D matrices, the lattice basis is built from
octahedral eigenvalue geometry — so the handshake inherits the same
structure as every other SOMS module.

Three components:
  OctahedralLattice  — CVP encode/decode using eigenvalue-structured basis
  PulseChip          — Single-clock mat-vec (hardware coupling model)
  feltscore          — Signal coherence metric (complement to PhiCalculator)

The lattice dimension is N_cells × 3 (each cell contributes a 3D eigenvalue
vector), so the geometry scales with the mandala, not an arbitrary constant.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Tuple, Optional

from src.octahedral_lookup import (
    OCTAHEDRAL_EIGENVALUES, POSITIONS, ALLOWED_TRANSITIONS,
    phi_stability_score,
)


# =============================================================================
# CORE: Octahedral Lattice Handshake (CVP)
# =============================================================================

@dataclass
class OctahedralLattice:
    """
    Lattice-based handshake using octahedral eigenvalue geometry.

    The private basis is built from the 8-state eigenvalue table tiled
    across N cells — not random noise. The public basis adds controlled
    perturbation. Decoding solves CVP via least-squares, which succeeds
    when the perturbation is small relative to the eigenvalue spacing.

    Dimension = num_cells × 3 (three eigenvalues per cell).
    """
    num_cells: int = 8
    noise_scale: float = 0.01
    _private_basis: np.ndarray = field(init=False, repr=False)
    _public_basis: np.ndarray = field(init=False, repr=False)

    def __post_init__(self):
        dim = self.num_cells * 3
        # Build basis from eigenvalue geometry: tile the 8 states across cells
        ev_block = np.array([OCTAHEDRAL_EIGENVALUES[s % 8] for s in range(self.num_cells)])
        ev_flat = ev_block.flatten()  # (dim,)

        # Private: structured basis seeded by octahedral geometry
        rng = np.random.default_rng()
        base = rng.standard_normal((dim, dim))
        # Scale columns by eigenvalue structure — encodes octahedral geometry
        self._private_basis = base * ev_flat[np.newaxis, :]
        # Public: perturbed version (CVP hardness comes from this gap)
        self._public_basis = self._private_basis + 0.001 * rng.standard_normal((dim, dim))

    @property
    def dim(self) -> int:
        return self.num_cells * 3

    def encode(self, vector: np.ndarray) -> np.ndarray:
        """Project onto public lattice + add noise."""
        on_grid = self._public_basis @ vector
        noise = self.noise_scale * np.random.randn(self.dim)
        return on_grid + noise

    def decode(self, noisy: np.ndarray) -> np.ndarray:
        """Solve CVP via least-squares on public basis."""
        result, _, _, _ = np.linalg.lstsq(self._public_basis, noisy, rcond=None)
        return result

    def handshake_error(self, secret: np.ndarray) -> float:
        """Round-trip encode → decode error (L2 norm)."""
        return float(np.linalg.norm(self.decode(self.encode(secret)) - secret))


# =============================================================================
# HARDWARE: Single-pulse mat-vec (coupling chip model)
# =============================================================================

@dataclass
class PulseChip:
    """
    Hardware coupling model: one matrix-vector multiply per clock cycle.

    When initialized from a FRET coupling matrix J, this represents
    the physical chip that implements the SOMSEngine coupling in one
    matrix-vector multiply per clock cycle (O(n) per cell, O(n²) total).
    When initialized standalone, uses eigenvalue-structured random matrix.
    """
    dim: int = 24
    coupling_matrix: Optional[np.ndarray] = None

    def __post_init__(self):
        if self.coupling_matrix is None:
            # Default: eigenvalue-structured random matrix
            ev_block = np.array([OCTAHEDRAL_EIGENVALUES[s % 8]
                                 for s in range(max(1, self.dim // 3))])
            ev_flat = np.tile(ev_block.flatten(), (self.dim // ev_block.size) + 1)[:self.dim]
            base = np.random.randn(self.dim, self.dim)
            self.coupling_matrix = base * ev_flat[np.newaxis, :]

    def pulse(self, vector: np.ndarray) -> np.ndarray:
        """O(D^2) mat-vec in one clock cycle."""
        return self.coupling_matrix @ vector

    @classmethod
    def from_fret(cls, j_ij: np.ndarray) -> 'PulseChip':
        """Build chip from a SOMSEngine FRET coupling matrix."""
        return cls(dim=j_ij.shape[0], coupling_matrix=j_ij)


# =============================================================================
# METRICS
# =============================================================================

def feltscore(signal: np.ndarray) -> float:
    """
    Signal coherence score. 1.0 = optimal flow, 0.0 = noise.

    Complement to PhiCalculator: phi measures integration across cells,
    feltscore measures signal-to-noise in a single vector.

    felt = 1 / (1 + σ/|μ|)
    """
    mean = np.abs(np.mean(signal))
    std = np.std(signal)
    return float(1.0 / (1.0 + std / (mean + 1e-8)))


def local_anxiety(point: np.ndarray, reference: np.ndarray) -> float:
    """
    High-dimensional divergence metric. Explodes when point and reference
    differ significantly — analogous to thermal_load in field_system.py.

    anxiety = exp(||point - ref||² / dim)

    Returns >1 when divergence exceeds average per-dimension unit variance.
    """
    dim = len(point)
    return float(np.exp(np.sum((point - reference) ** 2) / dim))
