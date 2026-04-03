# physical_coupling_matrix.py
# First-Principles Energy Coupling
# Interactions between fundamental physical fields

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print(f"Note: {__file__} requires numpy for matrix operations")
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any
import math

# ---------------------------
# 1. Fundamental Nodes (Physical Fields)
# ---------------------------

class PhysicalNode:
    """A fundamental physical field that carries or transfers energy."""

    def __init__(self, name: str, description: str, entropy_rank: int):
        self.name = name
        self.description = description
        self.entropy_rank = entropy_rank  # 0 = lowest entropy, higher = more degraded
        self.energy = 0.0  # MW

# Define the physical nodes
nodes = {
    "EM": PhysicalNode("EM", "Organized electromagnetic transport (grid)", entropy_rank=0),
    "M": PhysicalNode("M", "Structured mechanical motion", entropy_rank=1),
    "C": PhysicalNode("C", "Chemical potential (bonds, gradients)", entropy_rank=2),
    "T": PhysicalNode("T", "Thermal reservoir (disordered EM)", entropy_rank=3),
    "R": PhysicalNode("R", "Radiative field (solar, IR)", entropy_rank=1),
    "F": PhysicalNode("F", "Fluid dynamics (wind, pressure)", entropy_rank=2),
    "G": PhysicalNode("G", "Gravitational potential", entropy_rank=0),
    "K": PhysicalNode("K", "Kinetic (Coriolis, rotation)", entropy_rank=1),
}

node_list = ["EM", "M", "C", "T", "R", "F", "G", "K"]
n_nodes = len(node_list)

# ---------------------------
# 2. Coupling Matrix (Physical Interactions)
# ---------------------------

class PhysicalCouplingMatrix:
    """
    Coupling matrix based on fundamental physics.
    Each entry represents the maximum theoretical efficiency of converting
    one physical field to another.
    """

    def __init__(self):
        self.matrix = np.zeros((n_nodes, n_nodes))
        self._build_matrix()

    def _build_matrix(self):
        """Build coupling matrix from first principles."""

        # Map node names to indices
        idx = {name: i for i, name in enumerate(node_list)}

        # ========== EM (Organized Electromagnetic) ==========
        self.matrix[idx["EM"], idx["M"]] = 0.92
        self.matrix[idx["EM"], idx["C"]] = 0.80
        self.matrix[idx["EM"], idx["T"]] = 0.98
        self.matrix[idx["EM"], idx["R"]] = 0.60

        # ========== M (Mechanical Motion) ==========
        self.matrix[idx["M"], idx["EM"]] = 0.90
        self.matrix[idx["M"], idx["T"]] = 0.95
        self.matrix[idx["M"], idx["C"]] = 0.75
        self.matrix[idx["M"], idx["F"]] = 0.85

        # ========== C (Chemical Potential) ==========
        self.matrix[idx["C"], idx["T"]] = 0.93
        self.matrix[idx["C"], idx["EM"]] = 0.65
        self.matrix[idx["C"], idx["M"]] = 0.35

        # ========== T (Thermal Reservoir) ==========
        self.matrix[idx["T"], idx["EM"]] = 0.12
        self.matrix[idx["T"], idx["M"]] = 0.20
        self.matrix[idx["T"], idx["R"]] = 0.65

        # ========== R (Radiative Field) ==========
        self.matrix[idx["R"], idx["EM"]] = 0.20
        self.matrix[idx["R"], idx["T"]] = 0.70
        self.matrix[idx["R"], idx["C"]] = 0.05

        # ========== F (Fluid Dynamics) ==========
        self.matrix[idx["F"], idx["M"]] = 0.50
        self.matrix[idx["F"], idx["T"]] = 0.90
        self.matrix[idx["F"], idx["EM"]] = 0.15

        # ========== G (Gravitational) ==========
        self.matrix[idx["G"], idx["M"]] = 0.90
        self.matrix[idx["G"], idx["T"]] = 0.95

        # ========== K (Kinetic/Coriolis) ==========
        self.matrix[idx["K"], idx["F"]] = 0.00  # Modulator, not conversion
        self.matrix[idx["K"], idx["EM"]] = 0.85

    def get_efficiency(self, from_node: str, to_node: str) -> float:
        """Get coupling efficiency between two physical nodes."""
        idx = {name: i for i, name in enumerate(node_list)}
        return self.matrix[idx[from_node], idx[to_node]]

    def get_physical_path(self, from_node: str, to_node: str,
                          intermediate: str = None) -> float:
        """Calculate efficiency of multi-step conversion."""
        if intermediate:
            return (self.get_efficiency(from_node, intermediate) *
                    self.get_efficiency(intermediate, to_node))
        return self.get_efficiency(from_node, to_node)


# ---------------------------
# 3. Source Terms (External Inputs)
# ---------------------------

@dataclass
class SourceTerm:
    """External energy input to the system."""
    node: str
    power_mw: float
    description: str
    variability: float  # 0-1, 1 = constant


class SourceTerms:
    """Define external sources based on location and conditions."""

    @staticmethod
    def desert_coast_sources() -> List[SourceTerm]:
        """Sources typical of desert coastal location."""
        return [
            SourceTerm("R", 50.0, "Solar radiation (peak)", variability=0.7),
            SourceTerm("F", 15.0, "Coastal winds", variability=0.5),
            SourceTerm("G", 5.0, "Tidal gravitational", variability=0.3),
            SourceTerm("C", 2.0, "Biomass potential", variability=0.4),
        ]

    @staticmethod
    def geothermal_sources() -> List[SourceTerm]:
        """Geothermal sources from bedrock."""
        return [
            SourceTerm("T", 60.0, "Geothermal heat flux", variability=0.95),
        ]

    @staticmethod
    def all_sources() -> List[SourceTerm]:
        """Combine all realistic sources."""
        sources = SourceTerms.desert_coast_sources()
        sources.extend(SourceTerms.geothermal_sources())
        return sources


# ---------------------------
# 4. Coupling Modulators
# ---------------------------

@dataclass
class CouplingModulator:
    """
    A physical effect that modulates coupling efficiency between nodes.
    These are NOT nodes—they shape the interactions.
    """
    name: str
    description: str
    affects: List[Tuple[str, str]]  # (from_node, to_node)
    modulation_function: callable


class Modulators:
    """
    Physical effects that modulate coupling efficiency.
    Includes harmonic resonance, Coriolis, gravity gradients, etc.
    """

    @staticmethod
    def harmonic_resonance(frequency: float, natural_freq: float) -> float:
        """Harmonic resonance multiplier (1 at resonance, <1 elsewhere)."""
        if frequency == 0:
            return 1.0
        ratio = frequency / natural_freq
        return 1.0 / (1.0 + 10.0 * (ratio - 1.0)**2)

    @staticmethod
    def coriolis_effect(latitude: float, velocity: float) -> float:
        """Coriolis effect modulates fluid dynamics (F) to mechanical (M)."""
        coriolis = abs(math.sin(math.radians(latitude)))
        return min(1.0, coriolis * (1 + velocity / 50))

    @staticmethod
    def gravitational_gradient(delta_z: float) -> float:
        """Gravity gradient affects gravitational to mechanical conversion."""
        return min(1.0, delta_z / 100)

    @staticmethod
    def thermal_gradient(delta_t: float, source_temp: float) -> float:
        """Thermal gradient affects T -> EM and T -> M conversions."""
        if source_temp <= 0:
            return 0
        carnot_limit = 1 - (300 / (source_temp + 273))
        actual_gradient = min(1.0, delta_t / 500)
        return carnot_limit * actual_gradient

    @staticmethod
    def get_all_modulators() -> List[CouplingModulator]:
        """Return all coupling modulators."""
        return [
            CouplingModulator(
                "Harmonic Resonance",
                "Resonant coupling improves mechanical <-> EM conversion",
                [("M", "EM"), ("EM", "M")],
                lambda f=60: Modulators.harmonic_resonance(f, 60)
            ),
            CouplingModulator(
                "Coriolis Effect",
                "Planetary rotation shapes fluid dynamics",
                [("F", "M")],
                lambda lat=30, v=10: Modulators.coriolis_effect(lat, v)
            ),
            CouplingModulator(
                "Gravity Gradient",
                "Elevation difference enables gravitational energy",
                [("G", "M")],
                lambda dz=50: Modulators.gravitational_gradient(dz)
            ),
            CouplingModulator(
                "Thermal Gradient",
                "Temperature difference enables heat engine efficiency",
                [("T", "EM"), ("T", "M")],
                lambda dt=200, T_hot=500: Modulators.thermal_gradient(dt, T_hot)
            ),
        ]


# ---------------------------
# 5. Physical Energy Flow Model
# ---------------------------

class PhysicalEnergyFlow:
    """
    Energy flow model based on physical interactions.
    Follows: Energy is conserved; utility is lost when structure collapses into thermal equilibrium.
    """

    def __init__(self, coupling_matrix: PhysicalCouplingMatrix, sources: List[SourceTerm]):
        self.coupling = coupling_matrix
        self.sources = sources
        self.energy = {node: 0.0 for node in node_list}
        self._initialize_sources()

    def _initialize_sources(self):
        """Apply external sources."""
        for source in self.sources:
            self.energy[source.node] += source.power_mw

    def apply_couplings(self, modulators: List[CouplingModulator] = None):
        """
        Propagate energy through couplings.
        Energy flows from higher-entropy to lower-entropy (when possible),
        but more importantly, it degrades toward thermal equilibrium.
        """
        thermal_accumulation = 0.0
        structured_nodes = ["EM", "M", "C", "R", "F", "G", "K"]

        for from_node in structured_nodes:
            if self.energy[from_node] <= 0:
                continue

            for to_node in structured_nodes:
                if from_node == to_node:
                    continue

                eff = self.coupling.get_efficiency(from_node, to_node)
                if eff > 0:
                    transfer = self.energy[from_node] * eff * 0.1
                    self.energy[from_node] -= transfer
                    self.energy[to_node] += transfer

        for from_node in structured_nodes:
            if self.energy[from_node] <= 0:
                continue

            eff_to_thermal = self.coupling.get_efficiency(from_node, "T")
            if eff_to_thermal > 0:
                transfer = self.energy[from_node] * eff_to_thermal * 0.2
                self.energy[from_node] -= transfer
                thermal_accumulation += transfer

        thermal_available = self.energy["T"] + thermal_accumulation

        for to_node in structured_nodes:
            eff = self.coupling.get_efficiency("T", to_node)
            if eff > 0:
                max_transfer = thermal_available * eff * 0.05
                self.energy[to_node] += max_transfer
                thermal_available -= max_transfer

        self.energy["T"] = thermal_available

    def iterate(self, iterations: int = 50, modulators: List[CouplingModulator] = None):
        """Iterate the energy flow model until convergence."""
        history = []

        for i in range(iterations):
            self.apply_couplings(modulators)
            history.append(self.energy.copy())

            if i > 5:
                delta = sum(abs(history[-1][k] - history[-2][k]) for k in node_list)
                if delta < 0.01:
                    break

        return history

    def get_results(self) -> Dict:
        """Get final energy distribution."""
        mapping = {
            "EM": "G (Grid)",
            "M": "M (Mobility)",
            "C": "C (Chemical/Biological)",
            "T": "T (Thermal)",
            "R": "R (Radiative)",
            "F": "F (Fluid)",
            "G": "G (Gravitational)",
            "K": "K (Kinetic/Coriolis)"
        }

        result = {}
        for node, energy in self.energy.items():
            result[mapping.get(node, node)] = energy

        return {
            "distribution": result,
            "total_power": sum(self.energy.values()),
            "thermal_power": self.energy["T"],
            "structured_power": sum(self.energy[n] for n in ["EM", "M", "C", "R", "F", "G", "K"])
        }
