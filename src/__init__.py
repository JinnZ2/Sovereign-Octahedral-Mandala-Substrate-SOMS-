# SOMS — Sovereign Octahedral Mandala Substrate
"""
Core modules for octahedral-mandala physics simulation.

Modules:
    octahedral_physics  — FRET coupling and energy landscape (SOMSEngine)
    mandala_structure   — Fibonacci-scaled 8-petal mandala geometry (MandalaMap)
    phi_calculator      — Integrated Information (Φ) metric (PhiCalculator)
"""

from src.octahedral_physics import SOMSEngine
from src.mandala_structure import MandalaMap
from src.phi_calculator import PhiCalculator

__all__ = ["SOMSEngine", "MandalaMap", "PhiCalculator"]
