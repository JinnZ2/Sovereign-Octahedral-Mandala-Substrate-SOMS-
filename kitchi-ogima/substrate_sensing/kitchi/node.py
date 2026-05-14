"""
Sovereign node and its capacity. Renamed from ChiefCapacity.
Old name kept as deprecated alias so batch-1 code still imports.
"""

from dataclasses import dataclass, field
from typing import Set, Dict, List
import uuid


@dataclass
class SovereignCapacity:
    """
    What a node can contribute to pack coordination.

    Note: this is a PROPERTY every node has, not a rank.
    Higher capacity = more shards held, not more authority.
    All nodes are sovereign regardless of capacity value.
    """
    compute:       float = 0.0
    memory:        int   = 0
    senses_local:  List[str] = field(default_factory=list)
    senses_remote: List[str] = field(default_factory=list)
    uptime_score:  float = 0.0
    energy_budget: float = 0.0


# Backward-compat alias — keep batch-1 imports working.
# Marked deprecated; new code should use SovereignCapacity.
ChiefCapacity = SovereignCapacity


@dataclass
class Node:
    """
    A sovereign pack member. Whole at N=1, coordinates at N≥2.
    No node type is special. No leader. No chief.
    """
    node_id:    str = field(default_factory=lambda: str(uuid.uuid4()))
    capacity:   SovereignCapacity = field(default_factory=SovereignCapacity)
    senses:     Dict[str, "SenseChannel"] = field(default_factory=dict)
    role_held:  Set[str] = field(default_factory=set)   # shard ids owned
    shadow_for: Set[str] = field(default_factory=set)   # shard ids mirrored

    def read_all(self) -> dict:
        return {
            name: (ch.buffer[-1] if ch.buffer else None)
            for name, ch in self.senses.items()
        }

    def is_alone(self, pack_size: int) -> bool:
        """N=1 is a legal sovereign state, not a degenerate one."""
        return pack_size == 1
