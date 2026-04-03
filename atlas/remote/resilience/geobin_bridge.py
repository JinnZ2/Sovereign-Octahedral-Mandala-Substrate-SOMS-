#!/usr/bin/env python3
"""
KnowledgeDNA/geobin_bridge.py — Geometric-to-Binary <-> Substrate Bridge
CC0 public domain — github.com/JinnZ2/urban-resilience-sim

Connects the GEIS (Geometric Encoding Identity System) from
geometric-to-binary to the substrate reasoning engine.

The fieldlink.json defines how repos share patterns:
  - Octahedral vertex bits (000-111) = 6 directions
  - Operators (O, I, X, delta) = transformations
  - phi_coherence = golden ratio alignment
  - bridges = which domains a pattern activates

These map directly to:
  - seed_protocol.py octahedral directions
  - equation_field.py properties
  - substrate.py reasoning vectors

This module bridges them so patterns discovered in one repo
(Mandala, Rosetta, Polyhedral, BioGrid) automatically become
substrate properties the reasoner can use.

The geometric encoding IS the substrate. The binary IS the signal.
The bridge just makes them talk to each other.

USAGE:
    from KnowledgeDNA.geobin_bridge import GeoBinBridge
    bridge = GeoBinBridge()
    props = bridge.pattern_to_properties("100|O", phi_coherence=0.97)

Zero dependencies. Stdlib only.
"""

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime

# Graceful imports
try:
    from KnowledgeDNA.substrate import SubstrateReasoner, VectorSynthesizer
    from KnowledgeDNA.equation_field import (
        Equation, Property, Domain, EquationField,
        build_equation_library, build_domain_library,
    )
    HAS_SUBSTRATE = True
except ImportError:
    HAS_SUBSTRATE = False

try:
    from sim.seed_protocol import (
        OCTAHEDRAL_DIRS, encode_seed, decode_seed,
        expand_seed, seed_distance,
    )
    HAS_SEED = True
except ImportError:
    HAS_SEED = False


# =============================================================================
# GEIS ENCODING — the geometric identity layer
# =============================================================================

# Structural constants only — directions and indices.
# Properties are derived, not assigned.
VERTEX_GEOMETRY = {
    "000": {"direction": "+X", "index": 0},
    "001": {"direction": "-X", "index": 1},
    "010": {"direction": "+Y", "index": 2},
    "011": {"direction": "-Y", "index": 3},
    "100": {"direction": "+Z", "index": 4},
    "101": {"direction": "-Z", "index": 5},
    "110": {"direction": "+X+Y", "index": -1},
    "111": {"direction": "+X+Y+Z", "index": -1},
}

# Axis NAMES per vertex — these are the seeds for synthesis.
VERTEX_AXIS_SEEDS = {
    "000": "food water crop harvest nutrient soil",
    "001": "energy grid power generation storage fuel",
    "010": "social community trust cohesion cooperation",
    "011": "institutional governance authority legitimacy coordination",
    "100": "knowledge transmission learning memory oral apprenticeship",
    "101": "infrastructure roads bridges pipes repair maintenance",
    "110": "food community local market cooperative distribution",
    "111": "convergent stable unified equilibrium balanced holistic",
}

# Operator DESCRIPTIONS — seeds for synthesis.
OPERATOR_SEEDS = {
    "O": "origin center radial symmetric attractor collapse equilibrium stable",
    "I": "identity invariant persistent proportion stable preserved unchanged",
    "X": "exchange bidirectional flow coupling transfer synchronize oscillate",
    "Δ": "change gradient difference delta transform decay pressure dissipate",
}

# Bridge name DESCRIPTIONS — seeds for synthesis.
BRIDGE_SEEDS = {
    "consciousness": "awareness pattern recognition memory self-reflection information",
    "wave": "frequency oscillation resonance propagation interference amplitude",
    "structure": "geometry packing stability fractal nested self-similar solid",
    "flow": "gradient diffusion transport pressure current stream",
    "growth": "population expand scale spiral branch fibonacci reproduce",
    "decay": "loss fade erode half-life decompose memory die",
    "network": "graph connection community cluster mesh distributed topology",
    "energy": "conservation power transfer budget thermodynamic minimize",
    "information": "entropy signal compress encode measure uncertainty noise",
    "symmetry": "invariant proportion golden ratio self-similar resonance avoid",
}


class DerivedMappings:
    """
    Replaces hand-curated VERTEX_MAP, OPERATOR_MAP, BRIDGE_PROPERTY_MAP.

    Takes the seed words above and runs them through the VectorSynthesizer
    to produce property vectors. The synthesizer builds its associations
    from equation and domain descriptions — so the mappings are grounded
    in the actual physics library, not someone's guesses.
    """

    def __init__(self, synthesizer: 'VectorSynthesizer'):
        self.synthesizer = synthesizer
        self.vertex_properties: Dict[str, Dict[str, float]] = {}
        self.operator_properties: Dict[str, Dict[str, float]] = {}
        self.bridge_properties: Dict[str, Dict[str, float]] = {}
        self._derive_all()

    def _derive_all(self):
        """Derive all property mappings from seed text."""
        for bits, seed_text in VERTEX_AXIS_SEEDS.items():
            self.vertex_properties[bits] = self.synthesizer.synthesize(seed_text)

        for op, seed_text in OPERATOR_SEEDS.items():
            self.operator_properties[op] = self.synthesizer.synthesize(seed_text)

        for bridge, seed_text in BRIDGE_SEEDS.items():
            self.bridge_properties[bridge] = self.synthesizer.synthesize(seed_text)

    def get_vertex_props(self, bits: str) -> Dict[str, float]:
        return self.vertex_properties.get(bits, {})

    def get_operator_props(self, op: str) -> Dict[str, float]:
        return self.operator_properties.get(op, {})

    def get_bridge_props(self, bridge: str) -> Dict[str, float]:
        if bridge in self.bridge_properties:
            return self.bridge_properties[bridge]
        return self.synthesizer.synthesize(bridge)

    def report(self) -> str:
        """Show what was derived for transparency."""
        lines = []
        lines.append("DERIVED VERTEX MAPPINGS:")
        for bits, props in sorted(self.vertex_properties.items()):
            top = sorted(props.items(), key=lambda x: -x[1])[:5]
            top_str = ", ".join(f"{p}={w:.2f}" for p, w in top)
            lines.append(f"  {bits} ({VERTEX_AXIS_SEEDS[bits].split()[0]}): {top_str}")

        lines.append("\nDERIVED OPERATOR MAPPINGS:")
        for op, props in self.operator_properties.items():
            top = sorted(props.items(), key=lambda x: -x[1])[:5]
            top_str = ", ".join(f"{p}={w:.2f}" for p, w in top)
            lines.append(f"  {op}: {top_str}")

        lines.append("\nDERIVED BRIDGE MAPPINGS:")
        for bridge, props in sorted(self.bridge_properties.items()):
            top = sorted(props.items(), key=lambda x: -x[1])[:4]
            top_str = ", ".join(f"{p}={w:.2f}" for p, w in top)
            lines.append(f"  {bridge}: {top_str}")

        return "\n".join(lines)


# =============================================================================
# PATTERN
# =============================================================================

@dataclass
class GEISPattern:
    """A geometric encoding identity pattern."""
    pattern_id: str             # sha256 of geometric_encoding
    geometric_encoding: str     # e.g. "100|O"
    vertex_bits: str            # e.g. "100"
    operator: str               # e.g. "O"
    symbol: str                 # e.g. "O"
    phi_coherence: float        # 0-1
    dimension: int              # expansion depth
    bridges: List[str]          # domain bridge names
    cultural_labels: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def from_encoding(encoding: str, phi_coherence: float = 0.5,
                      dimension: int = 1, bridges: Optional[List[str]] = None,
                      cultural_labels: Optional[Dict[str, str]] = None) -> 'GEISPattern':
        """Create a pattern from a GEIS encoding string."""
        parts = encoding.split("|")
        vertex_bits = parts[0] if len(parts) > 0 else "000"
        operator = parts[1] if len(parts) > 1 else "O"
        symbol = parts[2] if len(parts) > 2 else operator

        pattern_id = hashlib.sha256(encoding.encode()).hexdigest()

        return GEISPattern(
            pattern_id=pattern_id,
            geometric_encoding=encoding,
            vertex_bits=vertex_bits,
            operator=operator,
            symbol=symbol,
            phi_coherence=phi_coherence,
            dimension=dimension,
            bridges=bridges or [],
            cultural_labels=cultural_labels or {},
        )

    def to_dict(self) -> Dict:
        return {
            "pattern_id": self.pattern_id,
            "geometric_encoding": self.geometric_encoding,
            "vertex_bits": self.vertex_bits,
            "operator": self.operator,
            "symbol": self.symbol,
            "phi_coherence": self.phi_coherence,
            "dimension": self.dimension,
            "bridges": self.bridges,
            "cultural_labels": self.cultural_labels,
        }


# =============================================================================
# BRIDGE — connects geometric encoding to substrate reasoning
# =============================================================================

class GeoBinBridge:
    """
    Bridges geometric-to-binary GEIS patterns to substrate properties.

    A GEIS pattern encodes identity as:
        [vertex_bits] | [operator] | [symbol]

    This bridge translates that into substrate properties:
        vertex_bits -> octahedral direction -> domain axis
        operator    -> transformation type -> property cluster
        bridges     -> domain connections -> property expansion
        phi_coherence -> weight modifier on phi-family properties
    """

    def __init__(self):
        self.reasoner = SubstrateReasoner() if HAS_SUBSTRATE else None
        if self.reasoner:
            self.mappings = DerivedMappings(self.reasoner.synthesizer)
        else:
            self.mappings = None

    def pattern_to_properties(self, encoding: str,
                               phi_coherence: float = 0.5,
                               bridges: Optional[List[str]] = None,
                               dimension: int = 1) -> Dict[str, float]:
        """Convert a GEIS encoding to a weighted property vector."""
        parts = encoding.split("|")
        vertex_bits = parts[0] if len(parts) > 0 else "000"
        operator = parts[1] if len(parts) > 1 else "O"
        if bridges is None:
            bridges = []

        properties: Dict[str, float] = {}

        # Signal 1: Vertex direction
        if self.mappings:
            vertex_props = self.mappings.get_vertex_props(vertex_bits)
        else:
            vertex_props = {}
        for prop, weight in vertex_props.items():
            properties[prop] = properties.get(prop, 0) + weight

        # Signal 2: Operator
        if self.mappings:
            op_props = self.mappings.get_operator_props(operator)
        else:
            op_props = {}
        for prop, weight in op_props.items():
            properties[prop] = properties.get(prop, 0) + weight

        # Signal 3: Bridges
        for bridge_name in bridges:
            if self.mappings:
                bridge_props = self.mappings.get_bridge_props(bridge_name)
            else:
                bridge_props = {}
            for prop, weight in bridge_props.items():
                properties[prop] = properties.get(prop, 0) + weight * 0.7

        # Phi coherence amplifier
        phi_props = ["self_similarity", "optimal_packing", "fibonacci_scaling",
                     "spiral_growth", "resonance_avoidance", "proportion_stability",
                     "fractal_nesting", "phyllotaxis", "irrational_spacing",
                     "minimal_overlap", "convergent_ratio", "energy_minimization"]
        for prop in phi_props:
            if prop in properties:
                properties[prop] *= (1 + phi_coherence)
            elif phi_coherence > 0.7:
                properties[prop] = phi_coherence * 0.5

        # Dimension scaling
        expansion_props = ["spiral_growth", "population_dynamics",
                           "carrying_capacity", "fibonacci_scaling"]
        for prop in expansion_props:
            if prop in properties:
                properties[prop] *= (1 + 0.2 * (dimension - 1))

        # Normalize to 0-1
        if properties:
            max_val = max(properties.values())
            if max_val > 0:
                properties = {p: round(v / max_val, 4) for p, v in properties.items()}

        return properties

    def properties_to_pattern(self, properties: List[str],
                               phi_coherence: float = 0.5) -> GEISPattern:
        """Given substrate properties, find the best GEIS encoding."""
        best_op = "O"
        best_op_score = 0.0
        if self.mappings:
            for op, op_props in self.mappings.operator_properties.items():
                score = sum(op_props.get(p, 0) for p in properties)
                if score > best_op_score:
                    best_op = op
                    best_op_score = score

        best_vertex = "000"
        best_vertex_score = 0.0
        if self.mappings:
            for bits, v_props in self.mappings.vertex_properties.items():
                score = sum(v_props.get(p, 0) for p in properties)
                if score > best_vertex_score:
                    best_vertex = bits
                    best_vertex_score = score

        bridges = []
        if self.mappings:
            for bridge_name, b_props in self.mappings.bridge_properties.items():
                overlap = sum(1 for p in properties if b_props.get(p, 0) > 0.1)
                if overlap >= 2:
                    bridges.append(bridge_name)

        encoding = f"{best_vertex}|{best_op}"
        return GEISPattern.from_encoding(
            encoding, phi_coherence=phi_coherence,
            bridges=bridges,
        )

    def pattern_to_seed(self, encoding: str,
                         phi_coherence: float = 0.5) -> List[float]:
        """Convert a GEIS pattern to a 6D seed protocol vector."""
        parts = encoding.split("|")
        vertex_bits = parts[0] if len(parts) > 0 else "000"
        operator = parts[1] if len(parts) > 1 else "O"

        seed = [0.1] * 6

        vertex_info = VERTEX_GEOMETRY.get(vertex_bits, VERTEX_GEOMETRY["000"])
        idx = vertex_info["index"]
        if 0 <= idx < 6:
            seed[idx] = 0.5 + 0.3 * phi_coherence

        if operator == "O":
            pass
        elif operator == "X":
            for i in range(6):
                if i != idx:
                    seed[i] += 0.15
        elif operator == "Δ":
            opposite = idx ^ 1
            if 0 <= opposite < 6:
                seed[opposite] = 0.05
        elif operator == "I":
            seed = [0.167] * 6
            if 0 <= idx < 6:
                seed[idx] = 0.25

        total = sum(seed)
        return [round(s / total, 4) for s in seed]

    def analyze_pattern(self, encoding: str, phi_coherence: float = 0.5,
                         bridges: Optional[List[str]] = None,
                         dimension: int = 1) -> Dict:
        """Full substrate analysis of a GEIS pattern."""
        pattern = GEISPattern.from_encoding(
            encoding, phi_coherence=phi_coherence,
            dimension=dimension, bridges=bridges,
        )

        properties = self.pattern_to_properties(
            encoding, phi_coherence=phi_coherence,
            bridges=bridges, dimension=dimension,
        )

        seed = self.pattern_to_seed(encoding, phi_coherence)

        substrate_result = None
        if self.reasoner:
            prop_list = sorted(properties.keys(), key=lambda p: -properties[p])
            result = self.reasoner.reason_from_properties(prop_list[:10])
            substrate_result = self.reasoner.to_dict(result)

        return {
            "pattern": pattern.to_dict(),
            "properties": properties,
            "seed_vector": seed,
            "substrate_analysis": substrate_result,
        }

    def load_fieldlink(self, fieldlink_data: Dict) -> Dict[str, List[str]]:
        """Parse a fieldlink.json and extract cross-repo entity relationships."""
        entities = {}
        for source in fieldlink_data.get("sources", []):
            consumed = source.get("entities_consumed", [])
            exported = source.get("entities_exported", [])

            for entity in consumed + exported:
                parts = entity.split(".")
                category = parts[0] if len(parts) > 0 else ""
                specific = parts[1] if len(parts) > 1 else ""
                props = self._entity_to_properties(category, specific)
                entities[entity] = props

        return entities

    def _entity_to_properties(self, category: str, specific: str) -> List[str]:
        """Map fieldlink entity types to substrate properties."""
        category_map = {
            "SHAPE": ["self_similarity", "optimal_packing", "proportion_stability"],
            "CONST": ["convergent_ratio", "proportion_stability"],
            "CAP": ["spiral_growth", "fibonacci_scaling", "energy_conservation"],
            "PROTO": ["network_structure", "synchronization", "compression"],
            "GEIS": ["pattern_recognition", "compression", "information_measure"],
            "BRIDGE": ["spatial_coupling", "network_structure", "gradient_flow"],
            "TOPO": ["network_structure", "fractal_nesting", "self_similarity"],
        }

        specific_map = {
            "OCTA": ["optimal_packing", "resonance_avoidance", "self_similarity"],
            "PHI": ["fibonacci_scaling", "resonance_avoidance", "spiral_growth",
                     "irrational_spacing", "proportion_stability"],
            "SEED_EXPANSION": ["spiral_growth", "energy_conservation",
                               "fibonacci_scaling"],
            "ENCODING": ["compression", "information_measure", "pattern_recognition"],
            "BINARY": ["compression", "information_measure"],
            "VORTEX_MEMORY": ["memory_fading", "self_similarity", "fractal_nesting"],
        }

        props = set()
        props.update(category_map.get(category, []))
        props.update(specific_map.get(specific, []))
        return sorted(props)
