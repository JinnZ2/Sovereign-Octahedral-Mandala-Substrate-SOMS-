"""
Consistent hashing for shard assignment.

Naming note: 'primary' and 'shadow' here are MECHANICAL roles
for a piece of work, not POLITICAL ranks for a node. A node
can be primary for shard X and shadow for shard Y simultaneously.
No node is 'the primary' overall. No node leads.
"""

import hashlib
from typing import List, Dict, Optional


def _hash(key: str) -> int:
    return int(hashlib.sha256(key.encode()).hexdigest(), 16)


class HashRing:
    """Consistent hash ring. Stdlib-only."""

    def __init__(self, virtual_nodes: int = 64):
        self.virtual_nodes = virtual_nodes
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []

    def add_node(self, node_id: str) -> None:
        for v in range(self.virtual_nodes):
            self.ring[_hash(f"{node_id}:{v}")] = node_id
        self.sorted_keys = sorted(self.ring.keys())

    def remove_node(self, node_id: str) -> None:
        self.ring = {k: v for k, v in self.ring.items() if v != node_id}
        self.sorted_keys = sorted(self.ring.keys())

    def primary_for(self, shard_id: str) -> Optional[str]:
        if not self.sorted_keys:
            return None
        h = _hash(shard_id)
        for k in self.sorted_keys:
            if k >= h:
                return self.ring[k]
        return self.ring[self.sorted_keys[0]]  # wrap

    def shadow_for(self, shard_id: str) -> Optional[str]:
        """Next distinct node on the ring after the primary."""
        primary = self.primary_for(shard_id)
        if primary is None:
            return None
        h = _hash(shard_id)
        for k in self.sorted_keys:
            if k >= h and self.ring[k] != primary:
                return self.ring[k]
        for k in self.sorted_keys:
            if self.ring[k] != primary:
                return self.ring[k]
        return None  # only one distinct node in ring (N=1 case)
