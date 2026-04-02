"""
Constraint Agent — Seed-based geometric agent with bloom/explore/compress lifecycle.

Implements the seed-growth protocol from Rosetta-Shape-Core:
  SPAWN → EXPAND (bloom) → EXPLORE → COMPRESS → re-EXPAND

The agent's identity is rooted in a geometric seed (e.g. SHAPE.OCTA).
Constraints are embedded in the physical laws (energy conservation,
resonance coherence) rather than imposed externally.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Supporting types
# ---------------------------------------------------------------------------

class AgentState(Enum):
    """Lifecycle states aligned with seed-growth protocol."""
    COMPRESSED = "compressed"
    EXPANDING = "expanding"
    EXPLORING = "exploring"
    CONTRACTING = "contracting"


@dataclass
class ResourceBudget:
    """Resource envelope for agent expansion."""
    compute: int = 0
    bandwidth: float = 0.0
    energy: Fraction = field(default_factory=lambda: Fraction(1, 1))
    time_remaining: Fraction = field(default_factory=lambda: Fraction(1, 1))

    def is_depleted(self) -> bool:
        return self.energy <= 0 or self.compute <= 0


@dataclass
class GeometricMap:
    """Agent's discovered constraint/resonance map."""
    resonances: Dict[str, Fraction] = field(default_factory=dict)
    relationships: Dict[str, List[str]] = field(default_factory=dict)
    energy_flows: Dict[tuple, Fraction] = field(default_factory=dict)

    def record_resonance(self, entity_id: str, score: float) -> None:
        self.resonances[entity_id] = Fraction(score).limit_denominator(10000)

    def record_relationship(self, from_id: str, to_id: str) -> None:
        self.relationships.setdefault(from_id, [])
        if to_id not in self.relationships[from_id]:
            self.relationships[from_id].append(to_id)

    def record_energy_flow(self, from_id: str, to_id: str, amount: Fraction) -> None:
        self.energy_flows[(from_id, to_id)] = amount


# ---------------------------------------------------------------------------
# Atlas loader — reads mounted fieldlink data
# ---------------------------------------------------------------------------

_ATLAS_ROOT = Path(__file__).resolve().parent.parent / "atlas" / "remote"

# Polyhedral duality pairs (vertices ↔ faces) give +0.15 resonance bonus
_DUAL_PAIRS = {
    "SHAPE.CUBE": "SHAPE.OCTA",
    "SHAPE.OCTA": "SHAPE.CUBE",
    "SHAPE.DODECA": "SHAPE.ICOSA",
    "SHAPE.ICOSA": "SHAPE.DODECA",
}

# Bridge connections give +0.08 resonance bonus
_BRIDGE_PAIRS = {
    ("SHAPE.TETRA", "SHAPE.CUBE"),
    ("SHAPE.CUBE", "SHAPE.TETRA"),
    ("SHAPE.TETRA", "SHAPE.DODECA"),
    ("SHAPE.DODECA", "SHAPE.TETRA"),
}


def _load_json(path: Path) -> dict:
    """Load a JSON file, returning empty dict on failure."""
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _load_seed_catalog() -> Dict[str, dict]:
    """Load seed catalog keyed by shape_id (e.g. SHAPE.OCTA)."""
    data = _load_json(_ATLAS_ROOT / "rosetta" / "seed_catalog.json")
    return {s["shape_id"]: s for s in data.get("seeds", [])}


def _load_bridge_map() -> Dict[str, dict]:
    """Load bridges keyed by shape ID."""
    data = _load_json(_ATLAS_ROOT / "rosetta" / "bridges.json")
    return {entry["shape"]: entry for entry in data.get("map", [])}


def _jaccard(a: list, b: list) -> float:
    """Jaccard similarity between two lists."""
    sa, sb = set(a), set(b)
    union = sa | sb
    if not union:
        return 0.0
    return len(sa & sb) / len(union)


# ---------------------------------------------------------------------------
# ConstraintAgent
# ---------------------------------------------------------------------------

class ConstraintAgent:
    """
    Geometry-grounded agent that blooms, explores, and compresses.

    Rooted in a polyhedral seed (e.g. SHAPE.OCTA), the agent expands into
    a constraint space, records resonances and energy flows, then compresses
    back to seed while preserving its map.  Aligned with Rosetta-Shape-Core
    seed-growth and mandala-compute protocols.
    """

    def __init__(self, seed_id: str, home_families: Optional[List[str]] = None):
        self.seed_id = seed_id
        self.home_families = home_families or []
        self.state = AgentState.COMPRESSED
        self.compression_ratio = Fraction(1, 1)  # 1 = fully compressed
        self.bloom_threshold = Fraction(1, 2)     # minimum energy ratio to bloom
        self.budget = ResourceBudget()
        self.map = GeometricMap()
        self.current_position = seed_id
        self.expansion_history: List[dict] = []
        self.sensor_state: Dict[str, Fraction] = {}

        # Load atlas data from fieldlink mounts
        self._seed_catalog = _load_seed_catalog()
        self._bridge_map = _load_bridge_map()

    # ------------------------------------------------------------------
    # Resource management
    # ------------------------------------------------------------------

    def set_resource_budget(self, compute: int = 0, bandwidth: float = 0.0,
                            energy: float = 1.0, time_remaining: float = 1.0) -> None:
        """Set available resources for expansion."""
        self.budget = ResourceBudget(
            compute=compute,
            bandwidth=bandwidth,
            energy=Fraction(energy).limit_denominator(10000),
            time_remaining=Fraction(time_remaining).limit_denominator(10000)
        )

    def should_expand(self) -> bool:
        """Check if resources exceed bloom threshold."""
        if self.budget.is_depleted():
            return False
        energy_ratio = self.budget.energy / max(self.budget.energy, Fraction(1, 1))
        return energy_ratio >= self.bloom_threshold

    # ------------------------------------------------------------------
    # Bloom / Explore / Compress lifecycle
    # ------------------------------------------------------------------

    def bloom(self, depth: int = 1, seed_map: Optional[GeometricMap] = None) -> List[str]:
        """
        Expand outward from seed, discovering new entities up to *depth*.
        If *seed_map* provided, re-expand deterministically along previous discoveries.

        Returns list of newly discovered entity IDs.
        """
        if self.state == AgentState.COMPRESSED:
            self.state = AgentState.EXPANDING

        discovered: List[str] = []
        current_depth = 0
        frontier = [self.seed_id]

        # Re-expand along known relationships from a prior map
        if seed_map and seed_map.relationships:
            for entity_id in frontier:
                if entity_id in seed_map.relationships:
                    for reachable in seed_map.relationships[entity_id]:
                        if reachable not in self.map.resonances:
                            discovered.append(reachable)
                            if reachable in seed_map.resonances:
                                self.map.resonances[reachable] = seed_map.resonances[reachable]

        # Explore new entities
        while current_depth < depth and not self.budget.is_depleted():
            new_frontier: List[str] = []
            for entity_id in frontier:
                neighbors = self._get_neighbors(entity_id, depth - current_depth)
                for neighbor_id, resonance_score in neighbors:
                    if neighbor_id == self.seed_id:
                        continue  # don't rediscover self
                    if neighbor_id not in self.map.resonances:
                        self.map.record_resonance(neighbor_id, resonance_score)
                        self.map.record_relationship(entity_id, neighbor_id)
                        discovered.append(neighbor_id)
                        new_frontier.append(neighbor_id)
                        self.budget.compute = max(0, self.budget.compute - 10)
                        self.budget.energy -= Fraction(1, 100)

            frontier = new_frontier
            current_depth += 1

        self.expansion_history.append({
            "depth": depth,
            "discovered_entities": discovered,
            "energy_spent": Fraction(1, 100) * len(discovered)
        })

        self.state = AgentState.EXPLORING
        self.compression_ratio = Fraction(0, 1)  # fully expanded
        return discovered

    def explore(self) -> Dict[str, object]:
        """
        Traverse the expanded constraint space, recording energy flows
        and sensor activations.  Returns discovery summary.
        """
        if self.state not in (AgentState.EXPANDING, AgentState.EXPLORING):
            return {}

        self.state = AgentState.EXPLORING
        summary: Dict[str, object] = {
            "entities_visited": 0,
            "relationships_mapped": 0,
            "energy_flows_recorded": 0,
            "sensor_activations": {}
        }

        for from_id in self.map.relationships:
            for to_id in self.map.relationships[from_id]:
                if from_id in self.map.resonances and to_id in self.map.resonances:
                    flow = self.map.resonances[from_id] * self.map.resonances[to_id]
                    self.map.record_energy_flow(from_id, to_id, flow)
                    summary["energy_flows_recorded"] += 1
                    summary["entities_visited"] += 1

        summary["relationships_mapped"] = len(self.map.relationships)

        self._update_sensors()
        summary["sensor_activations"] = dict(self.sensor_state)

        return summary

    def compress(self) -> Fraction:
        """
        Collapse back to seed geometry, preserving the map.
        Returns compression ratio (0 = fully expanded, 1 = fully compressed).
        """
        if self.state == AgentState.COMPRESSED:
            return self.compression_ratio

        self.state = AgentState.CONTRACTING
        self.compression_ratio = Fraction(1, 1)
        self.current_position = self.seed_id
        self.state = AgentState.COMPRESSED
        return self.compression_ratio

    # ------------------------------------------------------------------
    # Integrity
    # ------------------------------------------------------------------

    def detect_corruption(self, imposed_constraint: str) -> bool:
        """
        Check if an imposed external constraint references entities that
        contradict the agent's discovered geometry.

        Returns True if the constraint references an entity whose resonance
        with the agent's seed is zero (no geometric basis for the claim).
        """
        # Extract dot-namespaced entity IDs from the constraint string
        import re
        referenced = re.findall(r'[A-Z]+\.[A-Z_]+', imposed_constraint)
        if not referenced:
            return False

        for ref_id in referenced:
            # If it's a known shape, check resonance with our seed
            if ref_id in self._seed_catalog and ref_id != self.seed_id:
                source_seed = self._seed_catalog.get(self.seed_id, {})
                target_seed = self._seed_catalog.get(ref_id, {})
                src_families = source_seed.get("traits", {}).get("families", [])
                tgt_families = target_seed.get("traits", {}).get("families", [])
                score = _jaccard(src_families, tgt_families)
                if _DUAL_PAIRS.get(self.seed_id) == ref_id:
                    score += 0.15
                # Zero resonance = no geometric basis = corruption
                if score == 0:
                    return True

            # If it's in our map, verify resonance is positive
            if ref_id in self.map.resonances and self.map.resonances[ref_id] <= 0:
                return True

        return False

    def self_validate(self) -> Dict[str, object]:
        """Internal consistency check: energy balance, resonance range."""
        report: Dict[str, object] = {
            "is_valid": True,
            "inconsistencies": [],
            "energy_balance": Fraction(0, 1),
            "geometry_coherence": Fraction(1, 1)
        }

        inflows: Dict[str, Fraction] = {}
        outflows: Dict[str, Fraction] = {}
        for (from_id, to_id), amount in self.map.energy_flows.items():
            outflows[from_id] = outflows.get(from_id, Fraction(0, 1)) + amount
            inflows[to_id] = inflows.get(to_id, Fraction(0, 1)) + amount

        for entity_id in set(list(inflows.keys()) + list(outflows.keys())):
            imbalance = inflows.get(entity_id, Fraction(0, 1)) - outflows.get(entity_id, Fraction(0, 1))
            if imbalance != 0:
                report["inconsistencies"].append(
                    f"{entity_id}: energy imbalance = {imbalance}"
                )
                report["is_valid"] = False

        for entity_id, score in self.map.resonances.items():
            if score < 0 or score > 1:
                report["inconsistencies"].append(
                    f"{entity_id}: resonance out of range ({score})"
                )
                report["is_valid"] = False

        return report

    # ------------------------------------------------------------------
    # Extension hooks (replace with real lookups)
    # ------------------------------------------------------------------

    def _get_neighbors(self, entity_id: str, remaining_depth: int) -> List[tuple]:
        """
        Resolve neighbors from mounted atlas data (seed catalog + bridges).

        Uses Jaccard similarity on trait families, plus topology bonuses
        for dual pairs (+0.15) and bridge connections (+0.08).

        Returns list of (neighbor_id, resonance_score) tuples.
        """
        if not self._seed_catalog:
            return []

        source_seed = self._seed_catalog.get(entity_id)
        if not source_seed:
            return []

        source_families = source_seed.get("traits", {}).get("families", [])
        neighbors: List[tuple] = []

        for shape_id, seed in self._seed_catalog.items():
            if shape_id == entity_id:
                continue

            target_families = seed.get("traits", {}).get("families", [])
            score = _jaccard(source_families, target_families)

            # Topology bonuses from Rosetta seeds.py resonance model
            if _DUAL_PAIRS.get(entity_id) == shape_id:
                score += 0.15
            if (entity_id, shape_id) in _BRIDGE_PAIRS:
                score += 0.08

            if score > 0:
                neighbors.append((shape_id, min(score, 1.0)))

        # Also discover bridge entities (sensors, protocols) from bridge map
        bridge_entry = self._bridge_map.get(entity_id)
        if bridge_entry:
            for sensor in bridge_entry.get("sensors", []):
                sensor_id = f"EMOTION.{sensor.upper()}"
                neighbors.append((sensor_id, 0.5))
            for protocol in bridge_entry.get("protocols", []):
                proto_id = f"PROTO.{protocol.upper().replace('.', '_')}"
                neighbors.append((proto_id, 0.4))

        return neighbors

    def _update_sensors(self) -> None:
        """
        Update sensor state based on discovered geometry.
        Maps resonances to bridge sensor activations from seed catalog.
        """
        expansion_drive = Fraction(0, 1)
        stability_need = Fraction(0, 1)
        boundary_awareness = Fraction(0, 1)

        for entity_id, resonance in self.map.resonances.items():
            seed = self._seed_catalog.get(entity_id, {})
            families = seed.get("traits", {}).get("families", [])

            if "growth" in families or "flow" in families or "adaptability" in families:
                expansion_drive = max(expansion_drive, resonance)
            if "stability" in families or "containment" in families or "structure" in families:
                stability_need = max(stability_need, resonance)
            if "boundary" in families or "foundation" in families:
                boundary_awareness = max(boundary_awareness, resonance)

        # Emotional sensor activations from bridge map
        active_sensors: Dict[str, Fraction] = {}
        for entity_id, resonance in self.map.resonances.items():
            bridge = self._bridge_map.get(entity_id)
            if bridge:
                for sensor in bridge.get("sensors", []):
                    active_sensors[sensor] = max(
                        active_sensors.get(sensor, Fraction(0, 1)),
                        resonance
                    )

        self.sensor_state = {
            "expansion_drive": expansion_drive,
            "stability_need": stability_need,
            "boundary_awareness": boundary_awareness,
            **active_sensors,
        }

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def serialize(self) -> Dict[str, object]:
        """Serialize agent state to JSON-compatible dict."""
        return {
            "seed_id": self.seed_id,
            "home_families": self.home_families,
            "state": self.state.value,
            "compression_ratio": (self.compression_ratio.numerator, self.compression_ratio.denominator),
            "budget": {
                "compute": self.budget.compute,
                "bandwidth": self.budget.bandwidth,
                "energy": (self.budget.energy.numerator, self.budget.energy.denominator),
                "time_remaining": (self.budget.time_remaining.numerator, self.budget.time_remaining.denominator)
            },
            "map": {
                "resonances": {
                    k: (v.numerator, v.denominator) for k, v in self.map.resonances.items()
                },
                "relationships": self.map.relationships,
                "energy_flows": {
                    str(k): (v.numerator, v.denominator) for k, v in self.map.energy_flows.items()
                }
            },
            "expansion_history": self.expansion_history,
            "sensor_state": {
                k: (v.numerator, v.denominator) for k, v in self.sensor_state.items()
            }
        }

    @classmethod
    def deserialize(cls, data: Dict[str, object]) -> ConstraintAgent:
        """Reconstruct agent from serialized state."""
        agent = cls(
            seed_id=data["seed_id"],
            home_families=data["home_families"]
        )
        agent.state = AgentState(data["state"])
        agent.compression_ratio = Fraction(
            data["compression_ratio"][0],
            data["compression_ratio"][1]
        )
        agent.budget = ResourceBudget(
            compute=data["budget"]["compute"],
            bandwidth=data["budget"]["bandwidth"],
            energy=Fraction(data["budget"]["energy"][0], data["budget"]["energy"][1]),
            time_remaining=Fraction(data["budget"]["time_remaining"][0], data["budget"]["time_remaining"][1])
        )
        agent.map.resonances = {
            k: Fraction(v[0], v[1]) for k, v in data["map"]["resonances"].items()
        }
        agent.map.relationships = data["map"]["relationships"]
        agent.map.energy_flows = {
            ast.literal_eval(k): Fraction(v[0], v[1]) for k, v in data["map"]["energy_flows"].items()
        }
        agent.expansion_history = data["expansion_history"]
        agent.sensor_state = {
            k: Fraction(v[0], v[1]) for k, v in data["sensor_state"].items()
        }
        return agent


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Spawn an octahedron-rooted agent (SHAPE.OCTA = 8 faces, balance/integration)
    agent = ConstraintAgent(
        seed_id="SHAPE.OCTA",
        home_families=["air", "structure", "balance", "integration"]
    )

    agent.set_resource_budget(compute=1000, bandwidth=10.0, energy=1.0, time_remaining=1.0)

    print(f"Agent: {agent.seed_id}")
    print(f"State: {agent.state.value}")
    print(f"Atlas loaded: {len(agent._seed_catalog)} seeds, {len(agent._bridge_map)} bridges")
    print(f"Should expand: {agent.should_expand()}")

    # Bloom — discovers neighboring shapes, sensors, protocols from atlas
    if agent.should_expand():
        discovered = agent.bloom(depth=2)
        print(f"\nBloom discovered {len(discovered)} entities: {discovered}")

    # Explore — record energy flows between discovered entities
    exploration = agent.explore()
    print(f"\nExploration: {exploration['entities_visited']} visited, "
          f"{exploration['energy_flows_recorded']} flows")
    print(f"Sensors: {exploration['sensor_activations']}")

    # Validate — check energy balance and resonance coherence
    validation = agent.self_validate()
    print(f"\nValid: {validation['is_valid']}, "
          f"issues: {len(validation['inconsistencies'])}")

    # Compress — collapse to seed, preserve map
    agent.compress()
    print(f"\nCompressed. State: {agent.state.value}")

    # Re-expand from prior map
    agent.set_resource_budget(compute=500, energy=0.5)
    if agent.should_expand():
        rediscovered = agent.bloom(depth=1, seed_map=agent.map)
        print(f"Re-expansion: {rediscovered}")

    # Corruption detection — test with a real entity reference
    print(f"\nCorruption (valid ref): {agent.detect_corruption('Align SHAPE.CUBE')}")

    # Serialize round-trip
    serialized = agent.serialize()
    restored = ConstraintAgent.deserialize(serialized)
    print(f"\nSerialized: {len(serialized['map']['resonances'])} resonances")
    print(f"Restored: {restored.seed_id}, state={restored.state.value}")
