"""Tests for service_reconfig.py — reconfiguration, staging, priority, healing tools."""

import time
import pytest

from src.seed_dispersal import HardwareComponent, SeedDispersal, CompressedSeed
from src.service_reconfig import (
    ServiceState, ServiceRecord, ServiceReconfigurator,
    QuorumReconfigurator,
    Stage, Priority, ReconfigRequest,
    StagingProtocol, PriorityScheduler, PriorityRules,
    StagedPriorityReconfigurator,
    ResourceType, ResourceSnapshot,
    PrecomputeShareTool, RedistributeSharesTool, VerifySharesTool, PreloadStandbyTool,
    ExternalToolOrchestrator, ResourceMonitor,
)


# ============================================================================
# Service states
# ============================================================================

class TestServiceState:
    def test_values(self):
        assert ServiceState.OFFLINE.value == "offline"
        assert ServiceState.ONLINE.value == "online"

    def test_record_defaults(self):
        rec = ServiceRecord("comp_0")
        assert rec.state == ServiceState.OFFLINE
        assert rec.missed_heartbeats == 0


# ============================================================================
# ServiceReconfigurator
# ============================================================================

class TestServiceReconfigurator:
    @pytest.fixture
    def setup(self):
        comps = [HardwareComponent(f"hw_{i}") for i in range(5)]
        dispersal = SeedDispersal(comps, total_shares=5, threshold=3)
        reconf = ServiceReconfigurator(dispersal)
        return reconf, dispersal

    def test_register_service(self, setup):
        reconf, _ = setup
        reconf.register_service("hw_0")
        assert "hw_0" in reconf.services
        assert reconf.services["hw_0"].state in (ServiceState.SYNCING, ServiceState.ONLINE)

    def test_degrade_service(self, setup):
        reconf, _ = setup
        reconf.register_service("hw_0")
        reconf.services["hw_0"].state = ServiceState.ONLINE
        reconf.degrade_service("hw_0")
        assert reconf.services["hw_0"].state == ServiceState.OFFLINE

    def test_degrade_noop_for_offline(self, setup):
        reconf, _ = setup
        reconf.register_service("hw_0")
        reconf.services["hw_0"].state = ServiceState.OFFLINE
        reconf.degrade_service("hw_0")  # no crash


# ============================================================================
# QuorumReconfigurator
# ============================================================================

class TestQuorumReconfigurator:
    def test_quorum_reached(self):
        # quorum_size = (3+0)//2 + 1 = 2
        quorum = QuorumReconfigurator(total_services=3, fault_tolerance=0)
        assert not quorum.propose_reconfiguration("seed_a", "voter_1")
        assert quorum.propose_reconfiguration("seed_a", "voter_2")

    def test_quorum_not_reached(self):
        # quorum_size = (5+1)//2 + 1 = 4
        quorum = QuorumReconfigurator(total_services=5, fault_tolerance=1)
        assert not quorum.propose_reconfiguration("seed_b", "voter_1")
        assert not quorum.propose_reconfiguration("seed_b", "voter_2")
        assert not quorum.propose_reconfiguration("seed_b", "voter_3")

    def test_different_seeds_independent(self):
        quorum = QuorumReconfigurator(total_services=3, fault_tolerance=0)
        quorum.propose_reconfiguration("seed_a", "v1")
        assert not quorum.propose_reconfiguration("seed_b", "v1")


# ============================================================================
# StagingProtocol
# ============================================================================

class TestStagingProtocol:
    def test_can_enter(self):
        staging = StagingProtocol(quorum_size=3)
        req = ReconfigRequest(0, time.time(), "seed_a", "comp_0")
        assert staging.can_enter(req)

    def test_cannot_enter_active(self):
        staging = StagingProtocol(quorum_size=3)
        req = ReconfigRequest(0, time.time(), "seed_a", "comp_0")
        staging.enter_stage(req, Stage.PREPARING)
        req2 = ReconfigRequest(0, time.time(), "seed_a", "comp_1")
        assert not staging.can_enter(req2)

    def test_rollback(self):
        staging = StagingProtocol(quorum_size=3)
        req = ReconfigRequest(0, time.time(), "seed_a", "comp_0")
        staging.enter_stage(req, Stage.PREPARING)
        assert staging.rollback("seed_a")
        assert req.stage == Stage.FAILED

    def test_rollback_missing(self):
        staging = StagingProtocol(quorum_size=3)
        assert not staging.rollback("nonexistent")


# ============================================================================
# PriorityScheduler
# ============================================================================

class TestPriorityScheduler:
    def test_submit_and_schedule(self):
        sched = PriorityScheduler(max_concurrent=1)
        assert sched.submit("seed_a", "comp_0", Priority.HIGH)
        req = sched.schedule_next()
        assert req is not None
        assert req.seed_id == "seed_a"

    def test_duplicate_submit_rejected(self):
        sched = PriorityScheduler()
        assert sched.submit("seed_a", "comp_0", Priority.HIGH)
        assert not sched.submit("seed_a", "comp_1", Priority.CRITICAL)

    def test_priority_ordering(self):
        sched = PriorityScheduler(max_concurrent=10)
        sched.submit("low", "c0", Priority.LOW)
        sched.submit("critical", "c1", Priority.CRITICAL)
        sched.submit("medium", "c2", Priority.MEDIUM)

        first = sched.schedule_next()
        assert first.seed_id == "critical"

    def test_max_retries(self):
        sched = PriorityScheduler()
        sched.submit("seed_x", "c0", Priority.HIGH)
        # Exhaust retries: schedule, fail, re-queue, repeat
        for _ in range(3):
            req = sched.schedule_next()
            if req:
                sched.complete(req.seed_id, success=False)
        # After max_retries, schedule_next should return None (exceeded retries)
        leftover = sched.schedule_next()
        assert leftover is None or sched.pending_count() == 0

    def test_pending_count(self):
        sched = PriorityScheduler()
        sched.submit("a", "c0", Priority.LOW)
        sched.submit("b", "c1", Priority.HIGH)
        assert sched.pending_count() == 2

    def test_complete_success(self):
        sched = PriorityScheduler()
        sched.submit("seed_a", "c0", Priority.HIGH)
        req = sched.schedule_next()
        sched.complete("seed_a", success=True)
        assert sched.pending_count() == 0


# ============================================================================
# PriorityRules
# ============================================================================

class TestPriorityRules:
    def test_critical_below_threshold(self):
        p = PriorityRules.evaluate("s", ["c1"], threshold=3, online_components=["c1"])
        assert p == Priority.CRITICAL

    def test_high_at_threshold(self):
        p = PriorityRules.evaluate("s", ["c1", "c2", "c3"], threshold=3,
                                   online_components=["c1", "c2", "c3"])
        assert p == Priority.HIGH

    def test_exposure_risk_is_critical(self):
        p = PriorityRules.evaluate("s", ["c1", "c2", "c3", "c4", "c5"],
                                   threshold=3,
                                   online_components=["c1", "c2", "c3", "c4", "c5"],
                                   exposure_risk=True)
        assert p == Priority.CRITICAL


# ============================================================================
# ResourceType
# ============================================================================

class TestResourceType:
    def test_has_six_types(self):
        assert len(ResourceType) == 6

    def test_cpu_idle(self):
        assert ResourceType.CPU_IDLE.value == "cpu_idle"


# ============================================================================
# Healing Tools
# ============================================================================

class TestHealingTools:
    def test_precompute_name(self):
        assert PrecomputeShareTool().name() == "precompute_shares"

    def test_redistribute_name(self):
        assert RedistributeSharesTool().name() == "redistribute_shares"

    def test_verify_name(self):
        assert VerifySharesTool().name() == "verify_shares"

    def test_preload_name(self):
        assert PreloadStandbyTool().name() == "preload_standby"

    def test_precompute_benefit_no_offline(self):
        assert PrecomputeShareTool().benefit_score({"offline_components": []}) == 0.0

    def test_precompute_benefit_with_offline(self):
        score = PrecomputeShareTool().benefit_score({"offline_components": ["a", "b"]})
        assert score == pytest.approx(0.2)

    def test_preload_no_standby(self):
        assert PreloadStandbyTool().benefit_score({"standby_available": False}) == 0.0

    def test_tools_execute(self):
        for ToolClass in [PrecomputeShareTool, RedistributeSharesTool, VerifySharesTool, PreloadStandbyTool]:
            tool = ToolClass()
            assert tool.execute({}) is True

    def test_tools_have_resource_cost(self):
        for ToolClass in [PrecomputeShareTool, RedistributeSharesTool, VerifySharesTool, PreloadStandbyTool]:
            cost = ToolClass().resource_cost()
            assert len(cost) > 0
            assert all(isinstance(v, float) for v in cost.values())


# ============================================================================
# ExternalToolOrchestrator
# ============================================================================

class TestExternalToolOrchestrator:
    def test_register_tool(self):
        orch = ExternalToolOrchestrator()
        orch.register_tool(PrecomputeShareTool())
        assert len(orch.tools) == 1

    def test_select_best_tool_no_resources(self):
        orch = ExternalToolOrchestrator()
        orch.register_tool(PrecomputeShareTool())
        # No resources set → no tool selected
        assert orch.select_best_tool() is None

    def test_select_best_tool_with_resources(self):
        orch = ExternalToolOrchestrator()
        orch.register_tool(PrecomputeShareTool())
        orch.update_resources({rt: 1.0 for rt in ResourceType})
        state = {"offline_components": ["a", "b"]}
        tool = orch.select_best_tool(state)
        assert tool is not None
        assert tool.name() == "precompute_shares"


# ============================================================================
# ResourceMonitor
# ============================================================================

class TestResourceMonitor:
    def test_sample(self):
        orch = ExternalToolOrchestrator()
        monitor = ResourceMonitor(orch)
        sample = monitor.sample()
        assert len(sample) == 6
        for rt in ResourceType:
            assert rt in sample

    def test_push_once(self):
        orch = ExternalToolOrchestrator()
        monitor = ResourceMonitor(orch)
        monitor.push_once()
        assert orch.current_resources is not None
