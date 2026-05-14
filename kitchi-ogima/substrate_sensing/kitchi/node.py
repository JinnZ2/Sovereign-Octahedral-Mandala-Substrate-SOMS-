"""
Node + ChiefCapacity dataclasses.
The minimum representation of a pack member.
"""

from dataclasses import dataclass, field
from typing import Set, Dict, List
import uuid


@dataclass
class ChiefCapacity:
    """What a node can contribute to chief work."""
    compute:       float = 0.0    # ops/sec available
    memory:        int   = 0      # bytes free for buffers
    senses_local:  List[str] = field(default_factory=list)
    senses_remote: List[str] = field(default_factory=list)
    uptime_score:  float = 0.0    # rolling 0.0–1.0
    energy_budget: float = 0.0    # mW available for chief work


@dataclass
class Node:
    """One pack member. Salvaged hardware or simulated."""
    node_id:    str = field(default_factory=lambda: str(uuid.uuid4()))
    capacity:   ChiefCapacity = field(default_factory=ChiefCapacity)
    senses:     Dict[str, "SenseChannel"] = field(default_factory=dict)
    role_held:  Set[str] = field(default_factory=set)   # shard ids owned
    shadow_for: Set[str] = field(default_factory=set)   # shard ids mirrored

    def read_all(self) -> dict:
        """Snapshot of every sense channel's latest value."""
        return {
            name: (ch.buffer[-1] if ch.buffer else None)
            for name, ch in self.senses.items()
        }

    def is_alone(self, pack_size: int) -> bool:
        return pack_size == 1
