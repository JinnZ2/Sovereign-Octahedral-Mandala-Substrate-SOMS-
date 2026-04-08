"""Tests for octahedral_resilience.py — health monitoring, failover, recovery."""

import pytest

from src.octahedral_resilience import (
    Health, OctahedralNode, HeartbeatMonitor, OctahedralCluster,
    Monitor, AutoRecovery, OctahedralResilienceSystem,
)


# ============================================================================
# Health enum
# ============================================================================

class TestHealth:
    def test_values(self):
        assert Health.HEALTHY.value == "healthy"
        assert Health.DEGRADED.value == "degraded"
        assert Health.FAILED.value == "failed"

    def test_three_states(self):
        assert len(Health) == 3


# ============================================================================
# OctahedralNode
# ============================================================================

class TestOctahedralNode:
    def test_create(self):
        node = OctahedralNode(id="test_0")
        assert node.id == "test_0"
        assert node.lattice_dim == 500

    def test_solve_local_returns_list(self):
        node = OctahedralNode(id="n0", lattice_dim=10)
        # May raise RuntimeError (5% chance), so retry up to 50 times
        result = None
        for _ in range(50):
            try:
                result = node.solve_local()
                break
            except RuntimeError:
                continue
        assert result is not None
        assert len(result) == 10
        assert all(v == 0.0 for v in result)

    def test_heartbeat_returns_bool(self):
        node = OctahedralNode(id="n0")
        # Run many times — should return True most of the time (97%)
        beats = [node.heartbeat() for _ in range(100)]
        assert any(beats)  # at least one True in 100 tries


# ============================================================================
# HeartbeatMonitor
# ============================================================================

class TestHeartbeatMonitor:
    def test_check_returns_all_nodes(self):
        nodes = {f"n{i}": OctahedralNode(f"n{i}") for i in range(3)}
        monitor = HeartbeatMonitor(nodes=nodes)
        status = monitor.check()
        assert set(status.keys()) == {"n0", "n1", "n2"}

    def test_check_values_are_health(self):
        nodes = {"n0": OctahedralNode("n0")}
        monitor = HeartbeatMonitor(nodes=nodes)
        status = monitor.check()
        assert status["n0"] in (Health.HEALTHY, Health.DEGRADED, Health.FAILED)


# ============================================================================
# OctahedralCluster
# ============================================================================

class TestOctahedralCluster:
    def test_failover(self):
        primary = OctahedralNode("primary")
        backups = [OctahedralNode("backup_0"), OctahedralNode("backup_1")]
        cluster = OctahedralCluster(primary, backups)
        assert cluster.active.id == "primary"
        assert cluster.failover()
        assert cluster.active.id == "backup_0"

    def test_failover_exhausted(self):
        primary = OctahedralNode("primary")
        cluster = OctahedralCluster(primary, [])
        assert not cluster.failover()

    def test_solve_with_failover(self):
        primary = OctahedralNode("p", lattice_dim=5)
        backups = [OctahedralNode("b", lattice_dim=5)]
        cluster = OctahedralCluster(primary, backups)
        # Should succeed at least once in many tries
        results = [cluster.solve_with_failover() for _ in range(20)]
        assert any(r is not None for r in results)


# ============================================================================
# Monitor
# ============================================================================

class TestMonitor:
    def test_alert_threshold(self):
        monitor = Monitor(alert_threshold=2)
        # Two consecutive failures should trigger alert
        monitor.update({"n0": Health.FAILED})
        assert len(monitor.alerts) == 0
        monitor.update({"n0": Health.FAILED})
        assert len(monitor.alerts) == 1
        assert "n0" in monitor.alerts[0]

    def test_healthy_resets_count(self):
        monitor = Monitor(alert_threshold=3)
        monitor.update({"n0": Health.FAILED})
        monitor.update({"n0": Health.FAILED})
        monitor.update({"n0": Health.HEALTHY})  # reset
        monitor.update({"n0": Health.FAILED})
        # Counter reset, so only 1 failure — no alert yet
        assert len(monitor.alerts) == 0


# ============================================================================
# AutoRecovery
# ============================================================================

class TestAutoRecovery:
    def test_recover_adds_backup(self):
        cluster = OctahedralCluster(OctahedralNode("p"), [])
        monitor = Monitor()
        recovery = AutoRecovery(cluster, monitor)
        assert len(cluster.backups) == 0
        recovery.recover("failed_node")
        assert len(cluster.backups) == 1
        assert cluster.backups[0].id == "failed_node_restarted"

    def test_recover_logs_alert(self):
        cluster = OctahedralCluster(OctahedralNode("p"), [])
        monitor = Monitor()
        recovery = AutoRecovery(cluster, monitor)
        recovery.recover("nx")
        assert len(monitor.alerts) == 1


# ============================================================================
# OctahedralResilienceSystem
# ============================================================================

class TestOctahedralResilienceSystem:
    def test_creates_nodes(self):
        system = OctahedralResilienceSystem(node_count=5)
        assert len(system.nodes) == 5

    def test_cluster_has_primary(self):
        system = OctahedralResilienceSystem()
        assert system.cluster.active is not None

    def test_shutdown(self):
        system = OctahedralResilienceSystem()
        system.running = True
        system.shutdown()
        assert not system.running
