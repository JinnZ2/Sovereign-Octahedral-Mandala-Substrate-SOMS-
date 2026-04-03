"""Resource envelope for agent expansion."""

from dataclasses import dataclass, field
from fractions import Fraction


@dataclass
class ResourceBudget:
    """Resource envelope for agent expansion."""
    compute: int = 0
    bandwidth: float = 0.0
    energy: Fraction = field(default_factory=lambda: Fraction(1, 1))
    time_remaining: Fraction = field(default_factory=lambda: Fraction(1, 1))

    def is_depleted(self) -> bool:
        return self.energy <= 0 or self.compute <= 0
