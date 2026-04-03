"""Agent's discovered constraint/resonance map."""

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List


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
