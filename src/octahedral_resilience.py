"""
Octahedral Resilience — health monitoring, failover, and auto-recovery.

Provides heartbeat-based liveness checks for octahedral compute nodes,
automatic failover to backup nodes when a primary fails, alerting when
failure counts exceed threshold, and automated recovery by respawning
failed nodes into the backup pool.

Architecture:
  OctahedralNode    — single compute node (simulated local solve)
  HeartbeatMonitor  — periodic liveness checks with timeout
  OctahedralCluster — primary + backup failover pool
  Monitor           — failure counting + alert dispatch
  AutoRecovery      — node respawn into cluster backup pool
  OctahedralResilienceSystem — orchestrates all components

stdlib only — no numpy/scipy required.
"""

import random
import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ============================================================================
# Component health states
# ============================================================================

class Health(Enum):
    """Tri-state health for octahedral nodes."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


# ============================================================================
# Octahedral node (one "local landmark")
# ============================================================================

@dataclass
class OctahedralNode:
    """
    Single octahedral compute node.

    Simulates a local solver that occasionally fails (5% chance)
    and a heartbeat that occasionally misses (3% chance).
    """
    id: str
    lattice_dim: int = 500

    def solve_local(self, target: Optional[List[float]] = None) -> List[float]:
        """Local solve attempt — may fail due to non-locality."""
        if random.random() < 0.05:
            raise RuntimeError(f"Node {self.id}: local solve failed (non-locality)")
        return [0.0] * self.lattice_dim

    def heartbeat(self) -> bool:
        """Simple liveness check."""
        return random.random() > 0.03


# ============================================================================
# Heartbeat monitor
# ============================================================================

@dataclass
class HeartbeatMonitor:
    """
    Periodic heartbeat checker for a pool of octahedral nodes.

    Tracks last-beat timestamps and reports HEALTHY / DEGRADED / FAILED
    based on timeout thresholds.
    """
    nodes: Dict[str, OctahedralNode]
    interval_seconds: float = 1.0
    timeout_seconds: float = 3.0
    last_beat: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for node_id in self.nodes:
            self.last_beat[node_id] = time.time()

    def check(self) -> Dict[str, Health]:
        """Poll all nodes and return health status map."""
        status = {}
        now = time.time()
        for node_id, node in self.nodes.items():
            try:
                if node.heartbeat():
                    self.last_beat[node_id] = now
                    status[node_id] = Health.HEALTHY
                elif now - self.last_beat[node_id] > self.timeout_seconds:
                    status[node_id] = Health.FAILED
                else:
                    status[node_id] = Health.DEGRADED
            except Exception:
                status[node_id] = Health.FAILED
        return status


# ============================================================================
# Redundant resources (failover cluster)
# ============================================================================

class OctahedralCluster:
    """
    Primary + backup failover pool.

    On primary failure, pops the next backup node.
    solve_with_failover() attempts the active node, then fails over once.
    """
    def __init__(self, primary: OctahedralNode, backups: List[OctahedralNode]):
        self.primary = primary
        self.backups = list(backups)
        self.active = primary

    def failover(self) -> bool:
        """Switch to next healthy backup."""
        if self.backups:
            self.active = self.backups.pop(0)
            return True
        return False

    def solve_with_failover(self, target: Optional[List[float]] = None) -> Optional[List[float]]:
        """Attempt solve on active node, failover once on error."""
        try:
            return self.active.solve_local(target)
        except RuntimeError:
            if self.failover():
                return self.active.solve_local(target)
        return None


# ============================================================================
# Monitoring + alerting
# ============================================================================

class Monitor:
    """
    Failure counter with alert dispatch.

    Raises an alert string when any node's consecutive failure count
    reaches alert_threshold.
    """
    def __init__(self, alert_threshold: int = 2):
        self.alert_threshold = alert_threshold
        self.failure_counts: Dict[str, int] = {}
        self.alerts: List[str] = []

    def alert(self, message: str):
        self.alerts.append(message)

    def update(self, status: Dict[str, Health]):
        """Process a health-check round, counting failures."""
        for node_id, health in status.items():
            if health == Health.FAILED:
                self.failure_counts[node_id] = self.failure_counts.get(node_id, 0) + 1
                if self.failure_counts[node_id] >= self.alert_threshold:
                    self.alert(f"Node {node_id} has failed {self.failure_counts[node_id]} times")
            else:
                self.failure_counts[node_id] = 0


# ============================================================================
# Automated recovery
# ============================================================================

class AutoRecovery:
    """Respawn failed nodes into the cluster backup pool."""
    def __init__(self, cluster: OctahedralCluster, monitor: Monitor):
        self.cluster = cluster
        self.monitor = monitor

    def recover(self, failed_node_id: str) -> bool:
        """Attempt to restart or respawn a failed octahedral node."""
        new_node = OctahedralNode(id=f"{failed_node_id}_restarted")
        self.cluster.backups.append(new_node)
        self.monitor.alert(
            f"Recovery attempted for {failed_node_id} — new node {new_node.id} added"
        )
        return True


# ============================================================================
# Main orchestration
# ============================================================================

class OctahedralResilienceSystem:
    """
    Full resilience system: heartbeat + failover + monitoring + auto-recovery.

    Creates a pool of 5 octahedral nodes, a 3-node cluster (1 primary +
    2 backups), a heartbeat monitor, an alert monitor, and auto-recovery.
    """
    def __init__(self, node_count: int = 5):
        self.nodes = {f"oct_{i}": OctahedralNode(f"oct_{i}") for i in range(node_count)}
        node_list = list(self.nodes.values())
        self.heartbeat = HeartbeatMonitor(self.nodes)
        self.cluster = OctahedralCluster(
            primary=node_list[0],
            backups=list(node_list[1:3]),
        )
        self.monitor = Monitor()
        self.recovery = AutoRecovery(self.cluster, self.monitor)
        self.running = False

    def run_health_loop(self):
        """Blocking health-check loop (run in a thread)."""
        self.running = True
        while self.running:
            status = self.heartbeat.check()
            self.monitor.update(status)
            for node_id, health in status.items():
                if health == Health.FAILED:
                    self.recovery.recover(node_id)
            time.sleep(self.heartbeat.interval_seconds)

    def shutdown(self):
        self.running = False
