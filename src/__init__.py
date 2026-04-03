# SOMS — Sovereign Octahedral Mandala Substrate
"""
Core modules for octahedral-mandala physics simulation.

Modules:
    octahedral_physics  — FRET coupling and energy landscape (SOMSEngine)
    mandala_structure   — Fibonacci-scaled 8-petal mandala geometry (MandalaMap)
    phi_calculator      — Integrated Information (Φ) metric (PhiCalculator)
    constraint_agent    — Seed-based geometric agent lifecycle (ConstraintAgent)
    octahedral_lookup   — Gray codes, eigenvalue tables, φ-stability (from G2B bridge)
    geometric_encoder   — Bidirectional geometric token ↔ binary encoding (from G2B bridge)
"""

from src.octahedral_physics import SOMSEngine
from src.mandala_structure import MandalaMap
from src.phi_calculator import PhiCalculator
from src.constraint_agent import (
    ConstraintAgent, AgentState, ResourceBudget, GeometricMap,
)
from src.octahedral_lookup import (
    GRAY_CODES, GRAY_CODE_TO_STATE, OCTAHEDRAL_EIGENVALUES,
    EIGENVALUE_CHARACTERS, ALLOWED_TRANSITIONS, POSITIONS,
    MANDALA_OCTAHEDRAL_MAP, GRAY_TRANSITION_TABLE,
    gray_adjacent, nearest_octahedral_state, phi_stability_report,
    phi_stability_score, phi_deviation, state_capacity,
)
from src.geometric_encoder import GeometricEncoder

__all__ = [
    "SOMSEngine", "MandalaMap", "PhiCalculator",
    "ConstraintAgent", "AgentState", "ResourceBudget", "GeometricMap",
    "GeometricEncoder",
    "GRAY_CODES", "GRAY_CODE_TO_STATE", "OCTAHEDRAL_EIGENVALUES",
    "EIGENVALUE_CHARACTERS", "ALLOWED_TRANSITIONS", "POSITIONS",
    "MANDALA_OCTAHEDRAL_MAP", "GRAY_TRANSITION_TABLE",
    "gray_adjacent", "nearest_octahedral_state", "phi_stability_report",
    "phi_stability_score", "phi_deviation", "state_capacity",
]
