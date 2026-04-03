"""
Octahedral Lookup Tables — Mandala-to-Octahedral correspondence,
Gray codes, eigenvalue tables, phi-stability analysis, and
nearest-state lookup.

Ported from Geometric-to-Binary-Computational-Bridge/Mandala/octahedral_lookup.py
to serve as SOMS's canonical reference for state properties.
"""

import math
from typing import Dict, List, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PHI = (1 + math.sqrt(5)) / 2   # 1.618033988749895
INV_PHI = 1.0 / PHI            # 0.618033988749895
TETRAHEDRAL_ANGLE = 109.4712   # degrees — silicon sp3 hybridisation

# ---------------------------------------------------------------------------
# 1. Mandala <-> Octahedral Correspondence Table
# ---------------------------------------------------------------------------

MANDALA_OCTAHEDRAL_MAP: List[Dict[str, str]] = [
    {
        "mandala_concept": "8 Sacred Petals",
        "octahedral_substrate": "8 O_h vertex states",
        "physical_mechanism": "Electron tensor eigenvalue configurations",
    },
    {
        "mandala_concept": "Golden Ratio phi",
        "octahedral_substrate": "Fibonacci eigenvalue ratios",
        "physical_mechanism": "Minimum strain energy",
    },
    {
        "mandala_concept": "Fractal Depth",
        "octahedral_substrate": "Number of coupled cells",
        "physical_mechanism": "FRET-like tensor-tensor coupling",
    },
    {
        "mandala_concept": "Dimensional Fold",
        "octahedral_substrate": "Eigenspace dimensions",
        "physical_mechanism": "Tensor rank (3D -> ND extensions)",
    },
    {
        "mandala_concept": "Memory Amplification",
        "octahedral_substrate": "Exponential state capacity",
        "physical_mechanism": "8^N states from N cells",
    },
    {
        "mandala_concept": "Navigation Layer",
        "octahedral_substrate": "State transition pathways",
        "physical_mechanism": "Allowed transitions per O_h symmetry",
    },
    {
        "mandala_concept": "Reflection Field",
        "octahedral_substrate": "Topological protection",
        "physical_mechanism": "Berry phase, winding number",
    },
    {
        "mandala_concept": "Symbol Core",
        "octahedral_substrate": "Initial state encoding",
        "physical_mechanism": "Binary pattern -> tensor configuration",
    },
    {
        "mandala_concept": "Bloom Engine",
        "octahedral_substrate": "Tensor state expansion",
        "physical_mechanism": "Radial coupling from centre cell",
    },
]

# ---------------------------------------------------------------------------
# 2. Vertex Positions (O_h geometry)
# ---------------------------------------------------------------------------

POSITIONS: Dict[int, Tuple[int, int, int]] = {
    0: ( 1,  0,  0),   # +x
    1: (-1,  0,  0),   # -x
    2: ( 0,  1,  0),   # +y
    3: ( 0, -1,  0),   # -y
    4: ( 0,  0,  1),   # +z
    5: ( 0,  0, -1),   # -z
    6: ( 1,  1,  0),   # diagonal +x+y
    7: (-1, -1,  0),   # diagonal -x-y
}

# ---------------------------------------------------------------------------
# 3. Gray Code Tables
# ---------------------------------------------------------------------------

GRAY_CODES: Dict[int, str] = {
    0: "000",
    1: "001",
    2: "011",
    3: "010",
    4: "110",
    5: "111",
    6: "101",
    7: "100",
}

GRAY_CODE_TO_STATE: Dict[str, int] = {v: k for k, v in GRAY_CODES.items()}


def _hamming(a: str, b: str) -> int:
    """Hamming distance between two equal-length binary strings."""
    return sum(x != y for x, y in zip(a, b))


GRAY_TRANSITION_TABLE: List[List[int]] = [
    [_hamming(GRAY_CODES[i], GRAY_CODES[j]) for j in range(8)]
    for i in range(8)
]


def gray_adjacent(state_a: int, state_b: int) -> bool:
    """Return True if two states are Gray-adjacent (hamming distance == 1)."""
    return GRAY_TRANSITION_TABLE[state_a][state_b] == 1

# ---------------------------------------------------------------------------
# 4. Eigenvalue Lookup Table
#    Calibrated against DFT at optimal geometry
#    (strain eps* = 1.2%, Er-P distance d* = 4.8 A)
# ---------------------------------------------------------------------------

OCTAHEDRAL_EIGENVALUES: Dict[int, Tuple[float, float, float]] = {
    0: (0.33, 0.33, 0.33),  # Spherical
    1: (0.50, 0.25, 0.25),  # Elongated +x
    2: (0.25, 0.50, 0.25),  # Elongated +y
    3: (0.25, 0.25, 0.50),  # Elongated +z
    4: (0.45, 0.40, 0.15),  # Compressed -z
    5: (0.40, 0.40, 0.20),  # Biaxial xy
    6: (0.45, 0.30, 0.25),  # Asymmetric
    7: (0.40, 0.35, 0.25),  # Near-biaxial
}

EIGENVALUE_CHARACTERS: Dict[int, str] = {
    0: "Spherical",
    1: "Elongated +x",
    2: "Elongated +y",
    3: "Elongated +z",
    4: "Compressed -z",
    5: "Biaxial xy",
    6: "Asymmetric",
    7: "Near-biaxial",
}

# ---------------------------------------------------------------------------
# 5. Allowed Single-Step Transitions (12 edges of octahedron)
# ---------------------------------------------------------------------------

ALLOWED_TRANSITIONS: Dict[int, List[int]] = {
    0: [2, 3, 4, 5],   # +x  -> +/-y, +/-z
    1: [2, 3, 4, 5],   # -x  -> +/-y, +/-z
    2: [0, 1, 4, 5],   # +y  -> +/-x, +/-z
    3: [0, 1, 4, 5],   # -y  -> +/-x, +/-z
    4: [0, 1, 2, 3],   # +z  -> +/-x, +/-y
    5: [0, 1, 2, 3],   # -z  -> +/-x, +/-y
    6: [0, 2, 4, 7],   # diagonal -> neighbours
    7: [1, 3, 5, 6],   # diagonal -> neighbours
}

# ---------------------------------------------------------------------------
# 6. Nearest-State Lookup
# ---------------------------------------------------------------------------

def nearest_octahedral_state(eigenvalues: Tuple[float, float, float]) -> int:
    """
    Return the state index whose reference eigenvalues are closest
    (Euclidean L2) to the given eigenvalue tuple.
    """
    best_state = 0
    best_dist = float("inf")
    for state, ref_ev in OCTAHEDRAL_EIGENVALUES.items():
        dist = sum((eigenvalues[j] - ref_ev[j]) ** 2 for j in range(3))
        if dist < best_dist:
            best_dist = dist
            best_state = state
    return best_state


def nearest_octahedral_state_with_distance(
    eigenvalues: Tuple[float, float, float],
) -> Tuple[int, float]:
    """Like nearest_octahedral_state but also returns the squared L2 distance."""
    best_state = 0
    best_dist = float("inf")
    for state, ref_ev in OCTAHEDRAL_EIGENVALUES.items():
        dist = sum((eigenvalues[j] - ref_ev[j]) ** 2 for j in range(3))
        if dist < best_dist:
            best_dist = dist
            best_state = state
    return best_state, best_dist

# ---------------------------------------------------------------------------
# 7. Golden Ratio (phi) Stability Analysis
# ---------------------------------------------------------------------------

def phi_deviation(state: int) -> Dict[str, float]:
    """
    Compute the closest golden-ratio deviation for a single state.

    For each pair of adjacent eigenvalues, the ratio and its reciprocal
    are compared to phi.  The minimum absolute deviation is returned.
    """
    ev = OCTAHEDRAL_EIGENVALUES[state]
    ratios = {}
    candidates = []

    if ev[0] != 0:
        r01 = ev[1] / ev[0]
        ratios["lambda2/lambda1"] = r01
        candidates.append(r01)
        candidates.append(1.0 / r01)
    if ev[1] != 0:
        r12 = ev[2] / ev[1]
        ratios["lambda3/lambda2"] = r12
        candidates.append(r12)
        candidates.append(1.0 / r12)
    if ev[0] != 0 and ev[2] != 0:
        r02 = ev[2] / ev[0]
        ratios["lambda3/lambda1"] = r02
        candidates.append(r02)
        candidates.append(1.0 / r02)

    if not candidates:
        return {"closest_deviation": float("inf"), "best_ratio": 0.0, "ratios": ratios}

    deviations = [abs(r - PHI) for r in candidates]
    min_idx = int(np.argmin(deviations))
    return {
        "closest_deviation": deviations[min_idx],
        "best_ratio": candidates[min_idx],
        "ratios": ratios,
    }


def phi_stability_report() -> List[Dict]:
    """
    Full golden-ratio stability analysis for all 8 octahedral states.

    States with eigenvalue ratios close to phi = 1.618... show:
      - Longer coherence times (T2)
      - Lower transition error rates
      - Maximum information density per unit energy
    """
    report = []
    for state in range(8):
        info = phi_deviation(state)
        report.append({
            "state": state,
            "gray_code": GRAY_CODES[state],
            "character": EIGENVALUE_CHARACTERS[state],
            "eigenvalues": OCTAHEDRAL_EIGENVALUES[state],
            "closest_phi_deviation": info["closest_deviation"],
            "best_ratio": info["best_ratio"],
            "is_anchor": info["closest_deviation"] < 0.05,
        })
    report.sort(key=lambda r: r["closest_phi_deviation"])
    return report


def phi_stability_score(eigenvalues: Tuple[float, float, float]) -> float:
    """
    Return a 0-1 score indicating how close a set of eigenvalues is to
    golden-ratio optimality.  1.0 = perfect phi ratio, 0.0 = far from phi.
    """
    candidates = []
    pairs = [(0, 1), (1, 2), (0, 2)]
    for i, j in pairs:
        if eigenvalues[i] != 0:
            r = eigenvalues[j] / eigenvalues[i]
            candidates.append(abs(r - PHI))
            candidates.append(abs(1.0 / r - PHI) if r != 0 else float("inf"))
    if not candidates:
        return 0.0
    min_dev = min(candidates)
    return math.exp(-2.0 * min_dev)

# ---------------------------------------------------------------------------
# 8. State Capacity (Information Density)
# ---------------------------------------------------------------------------

def state_capacity(n_cells: int) -> Dict[str, object]:
    """Compute total state capacity for N octahedral cells."""
    return {
        "n_cells": n_cells,
        "total_states": 8 ** n_cells,
        "bits_per_cell": 3,
        "total_bits": 3 * n_cells,
    }
