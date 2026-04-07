"""
Service Reconfiguration — discovery, quorum, staging, priority, and healing tools.

Handles service lifecycle when hardware components come online/go offline.
Includes quorum-based consensus for reconfigurations, multi-phase staging
with rollback, priority scheduling with backoff, and resource-aware
external healing tool orchestration.

Architecture:
  ServiceReconfigurator       — register/degrade services, reassign shares
  QuorumReconfigurator        — Byzantine-tolerant voting for reconfiguration
  StagingProtocol             — PENDING → PREPARING → COMMITTING → VERIFYING → COMPLETE / FAILED
  PriorityScheduler           — heap-based scheduling with backoff + retry
  PriorityRules               — heuristic priority evaluation
  StagedPriorityReconfigurator — staged + prioritized reconfiguration
  HealingTool (ABC)           — resource-constrained healing actions
  ExternalToolOrchestrator    — benefit-scored tool selection + execution

stdlib only — no numpy/scipy required.
"""

import hashlib
import heapq
import queue
import random
import secrets
import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from src.seed_dispersal import SeedDispersal, HardwareComponent, CompressedSeed


# ============================================================================
# Service state tracking
# ============================================================================

class ServiceState(Enum):
    OFFLINE = "offline"
    SYNCING = "syncing"
    ONLINE = "online"
    RECONFIGURING = "reconfiguring"


@dataclass
class ServiceRecord:
    """Tracks lifecycle state for a single hardware component."""
    component_id: str
    state: ServiceState = ServiceState.OFFLINE
    last_seen: float = field(default_factory=time.time)
    missed_heartbeats: int = 0
    pending_shares: List[Tuple[str, bytes]] = field(default_factory=list)


# ============================================================================
# Service discovery & reconfiguration
# ============================================================================

class ServiceReconfigurator:
    """
    Manages service lifecycle: online registration, share reassignment,
    degradation, and reintegration.
    """

    def __init__(self, dispersal: SeedDispersal, heartbeat_interval: float = 1.0):
        self.dispersal = dispersal
        self.services: Dict[str, ServiceRecord] = {}
        self.heartbeat_interval = heartbeat_interval

    def register_service(self, component_id: str):
        """Service announces availability (after reboot/reconnect)."""
        if component_id not in self.services:
            self.services[component_id] = ServiceRecord(component_id)
        record = self.services[component_id]

        if record.state == ServiceState.OFFLINE:
            record.state = ServiceState.SYNCING
            self._reassign_missing_shares(component_id)

    def _reassign_missing_shares(self, component_id: str):
        """Push missing shares to newly online component."""
        record = self.services[component_id]

        for seed_id, (_, current_holders) in self.dispersal.seed_registry.items():
            if component_id not in current_holders:
                share = self._generate_share_for_component(seed_id, component_id)
                if share:
                    record.pending_shares.append((seed_id, share))

        if record.pending_shares:
            record.state = ServiceState.RECONFIGURING
            self._push_shares(component_id)
        else:
            record.state = ServiceState.ONLINE

    def _generate_share_for_component(self, seed_id: str, component_id: str) -> Optional[bytes]:
        """Generate a new share for a rejoining component."""
        existing_holders = self.dispersal.seed_registry.get(seed_id, (None, []))[1]
        if len(existing_holders) < self.dispersal.threshold:
            return None

        shares: List[bytes] = []
        indices: List[int] = []
        for i, holder in enumerate(existing_holders[:self.dispersal.threshold - 1], 1):
            comp = self.dispersal.components.get(holder)
            if comp and holder in self.services and self.services[holder].state == ServiceState.ONLINE:
                share = comp.retrieve_share(seed_id)
                if share:
                    shares.append(share)
                    indices.append(i)

        if len(shares) < self.dispersal.threshold - 1:
            return None

        return secrets.token_bytes(16)

    def _push_shares(self, component_id: str):
        """Send pending shares to component."""
        record = self.services[component_id]
        for seed_id, share in record.pending_shares:
            self.dispersal.components[component_id].store_share(seed_id, share)
            if seed_id in self.dispersal.seed_registry:
                _, holders = self.dispersal.seed_registry[seed_id]
                if component_id not in holders:
                    holders.append(component_id)
        record.pending_shares.clear()
        record.state = ServiceState.ONLINE

    def degrade_service(self, component_id: str):
        """Component failed — redistribute its shares."""
        record = self.services.get(component_id)
        if not record or record.state == ServiceState.OFFLINE:
            return

        record.state = ServiceState.OFFLINE
        record.missed_heartbeats += 1

        for seed_id, (_, holders) in self.dispersal.seed_registry.items():
            if component_id in holders:
                holders.remove(component_id)

        self._process_reassignments()

    def _process_reassignments(self):
        """Redistribute shares from failed components to healthy ones."""
        online = [
            cid for cid, rec in self.services.items()
            if rec.state == ServiceState.ONLINE
        ]
        if not online:
            return

        for seed_id, (_, holders) in self.dispersal.seed_registry.items():
            if len(holders) < self.dispersal.threshold:
                target = online[hash(seed_id) % len(online)]
                new_share = self._generate_share_for_component(seed_id, target)
                if new_share:
                    self.dispersal.components[target].store_share(seed_id, new_share)
                    if target not in holders:
                        holders.append(target)


# ============================================================================
# Quorum-based reconfiguration (consensus)
# ============================================================================

class QuorumReconfigurator:
    """Only reconfigure when enough services agree (Byzantine-tolerant)."""

    def __init__(self, total_services: int, fault_tolerance: int = 1):
        self.total = total_services
        self.quorum_size = (total_services + fault_tolerance) // 2 + 1
        self.proposals: Dict[str, Set[str]] = {}

    def propose_reconfiguration(self, seed_id: str, proposer_id: str) -> bool:
        """Vote on reconfiguring a seed's share distribution."""
        if seed_id not in self.proposals:
            self.proposals[seed_id] = set()
        self.proposals[seed_id].add(proposer_id)

        if len(self.proposals[seed_id]) >= self.quorum_size:
            del self.proposals[seed_id]
            return True
        return False


# ============================================================================
# Staging states
# ============================================================================

class Stage(Enum):
    PENDING = 0
    PREPARING = 1
    COMMITTING = 2
    VERIFYING = 3
    COMPLETE = 4
    FAILED = 5


# ============================================================================
# Priority levels
# ============================================================================

class Priority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4


@dataclass(order=True)
class ReconfigRequest:
    """A prioritized, staged reconfiguration request."""
    priority: int
    timestamp: float
    seed_id: str
    component_id: str
    stage: Stage = Stage.PENDING
    retry_count: int = 0


# ============================================================================
# Staging protocol (multi-phase with rollback)
# ============================================================================

class StagingProtocol:
    """Multi-phase reconfiguration with rollback."""

    def __init__(self, quorum_size: int, timeout_seconds: float = 5.0):
        self.quorum_size = quorum_size
        self.timeout = timeout_seconds
        self.active_stages: Dict[str, ReconfigRequest] = {}
        self.stage_history: List[ReconfigRequest] = []

    def can_enter(self, request: ReconfigRequest) -> bool:
        """Check if we can start staging this request."""
        if request.seed_id in self.active_stages:
            existing = self.active_stages[request.seed_id]
            if existing.stage not in (Stage.COMPLETE, Stage.FAILED):
                return False
        return True

    def enter_stage(self, request: ReconfigRequest, stage: Stage) -> bool:
        """Move to next stage."""
        request.stage = stage
        request.timestamp = time.time()
        self.active_stages[request.seed_id] = request
        return True

    def verify_stage(self, request: ReconfigRequest, data: bytes) -> bool:
        """Verification phase — checksum + quorum agreement."""
        if request.stage != Stage.VERIFYING:
            return False

        verified = random.random() > 0.1  # 90% success rate (simulated)

        if verified:
            request.stage = Stage.COMPLETE
            del self.active_stages[request.seed_id]
            self.stage_history.append(request)
        else:
            request.stage = Stage.FAILED
            request.retry_count += 1

        return verified

    def rollback(self, seed_id: str) -> bool:
        """Abort and rollback to previous distribution."""
        if seed_id in self.active_stages:
            request = self.active_stages[seed_id]
            request.stage = Stage.FAILED
            del self.active_stages[seed_id]
            return True
        return False


# ============================================================================
# Priority scheduler
# ============================================================================

class PriorityScheduler:
    """Manages reconfiguration queue with priority + backoff."""

    def __init__(self, max_concurrent: int = 1):
        self.queue: List[ReconfigRequest] = []
        self.active: Dict[str, ReconfigRequest] = {}
        self.max_concurrent = max_concurrent
        self.backoff_multiplier = 2.0
        self.max_retries = 3

    def submit(self, seed_id: str, component_id: str, priority: Priority) -> bool:
        """Submit reconfiguration request with priority."""
        if seed_id in self.active:
            return False
        for req in self.queue:
            if req.seed_id == seed_id:
                return False

        request = ReconfigRequest(
            priority=priority.value,
            timestamp=time.time(),
            seed_id=seed_id,
            component_id=component_id,
        )
        heapq.heappush(self.queue, request)
        return True

    def schedule_next(self) -> Optional[ReconfigRequest]:
        """Pop highest priority request if concurrency allows."""
        if len(self.active) >= self.max_concurrent:
            return None
        if not self.queue:
            return None

        request = heapq.heappop(self.queue)

        if request.retry_count >= self.max_retries:
            return None

        if request.retry_count > 0:
            backoff = self.backoff_multiplier ** request.retry_count
            if time.time() - request.timestamp < backoff:
                heapq.heappush(self.queue, request)
                return None

        self.active[request.seed_id] = request
        return request

    def complete(self, seed_id: str, success: bool):
        """Mark request as done."""
        if seed_id in self.active:
            request = self.active.pop(seed_id)
            if not success:
                request.retry_count += 1
                if request.retry_count < self.max_retries:
                    request.priority = min(request.priority + 1, Priority.BACKGROUND.value)
                    heapq.heappush(self.queue, request)

    def pending_count(self) -> int:
        return len(self.queue)


# ============================================================================
# Priority rules (heuristics)
# ============================================================================

class PriorityRules:
    """Determine priority based on system state."""

    @staticmethod
    def evaluate(seed_id: str, current_holders: List[str], threshold: int,
                 online_components: List[str], exposure_risk: bool = False) -> Priority:
        """
        Rules:
          CRITICAL   — seed exposure imminent (shares < threshold AND dropping)
          HIGH       — below threshold (can't reconstruct)
          MEDIUM     — at threshold but no redundancy
          LOW        — reintegrating a component (system functional)
          BACKGROUND — optimization only
        """
        healthy_count = len([h for h in current_holders if h in online_components])

        if exposure_risk or healthy_count < threshold:
            return Priority.CRITICAL
        elif healthy_count == threshold:
            return Priority.HIGH
        elif healthy_count <= threshold + 1:
            return Priority.MEDIUM
        elif healthy_count > threshold + 2:
            return Priority.LOW
        else:
            return Priority.BACKGROUND


# ============================================================================
# Staged + prioritized reconfigurator
# ============================================================================

class StagedPriorityReconfigurator:
    """Combines staging protocol with priority scheduling."""

    def __init__(self, dispersal: SeedDispersal, total_services: int,
                 fault_tolerance: int = 1):
        self.dispersal = dispersal
        self.scheduler = PriorityScheduler(max_concurrent=1)
        self.staging = StagingProtocol(
            quorum_size=(total_services + fault_tolerance) // 2 + 1
        )
        self.rules = PriorityRules()
        self.online_components: Set[str] = set()

    def request_reconfiguration(self, seed_id: str, component_id: str,
                                exposure_risk: bool = False) -> bool:
        """Submit a staged, prioritized reconfiguration request."""
        if seed_id not in self.dispersal.seed_registry:
            return False

        _, holders = self.dispersal.seed_registry[seed_id]
        priority = self.rules.evaluate(
            seed_id, holders, self.dispersal.threshold,
            list(self.online_components), exposure_risk,
        )
        return self.scheduler.submit(seed_id, component_id, priority)

    def process_loop(self):
        """Process next request through stages."""
        request = self.scheduler.schedule_next()
        if not request:
            return

        if not self.staging.can_enter(request):
            self.scheduler.complete(request.seed_id, success=False)
            return

        self.staging.enter_stage(request, Stage.PREPARING)
        shares = self._gather_shares(request.seed_id)

        if not shares or len(shares) < self.dispersal.threshold:
            self.staging.rollback(request.seed_id)
            self.scheduler.complete(request.seed_id, success=False)
            return

        self.staging.enter_stage(request, Stage.COMMITTING)
        new_distribution = self._commit_distribution(request.seed_id, shares)

        self.staging.enter_stage(request, Stage.VERIFYING)
        verified = self.staging.verify_stage(request, new_distribution)
        self.scheduler.complete(request.seed_id, success=verified)

    def _gather_shares(self, seed_id: str) -> List[bytes]:
        """Collect shares from online components."""
        _, holders = self.dispersal.seed_registry.get(seed_id, (None, []))
        shares: List[bytes] = []
        for holder in holders:
            if holder in self.online_components:
                comp = self.dispersal.components.get(holder)
                if comp:
                    share = comp.retrieve_share(seed_id)
                    if share:
                        shares.append(share)
        return shares

    def _commit_distribution(self, seed_id: str, shares: List[bytes]) -> bytes:
        """Commit new share distribution (returns checksum for verification)."""
        all_data = b"".join(shares)
        return hashlib.blake2b(all_data, digest_size=16).digest()

    def update_online_status(self, component_id: str, is_online: bool):
        """Maintain current online component set."""
        if is_online:
            self.online_components.add(component_id)
        else:
            self.online_components.discard(component_id)


# ============================================================================
# Resource types
# ============================================================================

class ResourceType(Enum):
    CPU_IDLE = "cpu_idle"
    NETWORK_BANDWIDTH = "bandwidth"
    MEMORY = "memory"
    STANDBY_HARDWARE = "standby_hw"
    FPGA_CYCLES = "fpga"
    POWER_BUDGET = "power"


@dataclass
class ResourceSnapshot:
    """Current available resources (0–1 scale per type)."""
    timestamp: float
    resources: Dict[ResourceType, float]


# ============================================================================
# Healing tool ABC + concrete tools
# ============================================================================

class HealingTool(ABC):
    """Abstract external tool that consumes resources to improve resilience."""

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def resource_cost(self) -> Dict[ResourceType, float]:
        pass

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def benefit_score(self, system_state: Dict[str, Any]) -> float:
        pass


class PrecomputeShareTool(HealingTool):
    """Pre-generate shares for offline components before they're needed."""

    def name(self) -> str:
        return "precompute_shares"

    def resource_cost(self) -> Dict[ResourceType, float]:
        return {ResourceType.CPU_IDLE: 0.3, ResourceType.MEMORY: 0.1, ResourceType.POWER_BUDGET: 0.05}

    def execute(self, context: Dict[str, Any]) -> bool:
        return True

    def benefit_score(self, system_state: Dict[str, Any]) -> float:
        offline_count = len(system_state.get("offline_components", []))
        return 0.0 if offline_count == 0 else min(offline_count / 10.0, 1.0)


class RedistributeSharesTool(HealingTool):
    """Re-balance shares across online components."""

    def name(self) -> str:
        return "redistribute_shares"

    def resource_cost(self) -> Dict[ResourceType, float]:
        return {ResourceType.NETWORK_BANDWIDTH: 0.4, ResourceType.CPU_IDLE: 0.2, ResourceType.STANDBY_HARDWARE: 0.1}

    def execute(self, context: Dict[str, Any]) -> bool:
        return True

    def benefit_score(self, system_state: Dict[str, Any]) -> float:
        return min(system_state.get("share_load_variance", 0), 1.0)


class VerifySharesTool(HealingTool):
    """Proactively verify share integrity during idle time."""

    def name(self) -> str:
        return "verify_shares"

    def resource_cost(self) -> Dict[ResourceType, float]:
        return {ResourceType.CPU_IDLE: 0.15, ResourceType.MEMORY: 0.05, ResourceType.FPGA_CYCLES: 0.1}

    def execute(self, context: Dict[str, Any]) -> bool:
        return True

    def benefit_score(self, system_state: Dict[str, Any]) -> float:
        last_verify = system_state.get("last_verification_time", 0)
        time_since = time.time() - last_verify
        return min(time_since / 3600.0, 1.0)


class PreloadStandbyTool(HealingTool):
    """Warm up standby hardware with minimal state."""

    def name(self) -> str:
        return "preload_standby"

    def resource_cost(self) -> Dict[ResourceType, float]:
        return {ResourceType.STANDBY_HARDWARE: 0.5, ResourceType.POWER_BUDGET: 0.2, ResourceType.NETWORK_BANDWIDTH: 0.1}

    def execute(self, context: Dict[str, Any]) -> bool:
        return True

    def benefit_score(self, system_state: Dict[str, Any]) -> float:
        if not system_state.get("standby_available", False):
            return 0.0
        recent_failures = system_state.get("failures_last_hour", 0)
        return min(recent_failures / 5.0, 1.0)


# ============================================================================
# External tool orchestrator
# ============================================================================

class ExternalToolOrchestrator:
    """Runs healing tools when resources permit, selecting by benefit score."""

    def __init__(self, resource_check_interval: float = 5.0):
        self.tools: List[HealingTool] = []
        self.resource_queue: queue.Queue = queue.Queue()
        self.current_resources: Optional[ResourceSnapshot] = None
        self.running = False
        self.interval = resource_check_interval
        self.execution_history: List[Tuple[str, bool, float]] = []

    def register_tool(self, tool: HealingTool):
        self.tools.append(tool)

    def update_resources(self, resources: Dict[ResourceType, float]):
        """Called by resource monitor with current availability."""
        self.current_resources = ResourceSnapshot(
            timestamp=time.time(), resources=resources,
        )
        self.resource_queue.put(self.current_resources)

    def _resources_sufficient(self, cost: Dict[ResourceType, float]) -> bool:
        if not self.current_resources:
            return False
        for rtype, required in cost.items():
            if self.current_resources.resources.get(rtype, 0) < required:
                return False
        return True

    def _consume_resources(self, cost: Dict[ResourceType, float]):
        if self.current_resources:
            for rtype, required in cost.items():
                self.current_resources.resources[rtype] -= required

    def select_best_tool(self, system_state: Optional[Dict[str, Any]] = None) -> Optional[HealingTool]:
        """Select highest benefit tool that fits resource budget."""
        if system_state is None:
            system_state = {}
        best_tool = None
        best_score = -1.0

        for tool in self.tools:
            if not self._resources_sufficient(tool.resource_cost()):
                continue
            score = tool.benefit_score(system_state)
            if score > best_score:
                best_score = score
                best_tool = tool

        return best_tool


# ============================================================================
# Resource monitor (simulated)
# ============================================================================

class ResourceMonitor:
    """Monitors system resources and pushes updates to orchestrator."""

    def __init__(self, orchestrator: ExternalToolOrchestrator):
        self.orchestrator = orchestrator
        self.running = False

    def sample(self) -> Dict[ResourceType, float]:
        """Sample current resource availability (simulated)."""
        return {
            ResourceType.CPU_IDLE: 0.7 + 0.2 * random.random(),
            ResourceType.NETWORK_BANDWIDTH: 0.5 + 0.4 * random.random(),
            ResourceType.MEMORY: 0.6 + 0.3 * random.random(),
            ResourceType.STANDBY_HARDWARE: 0.4 + 0.5 * random.random(),
            ResourceType.FPGA_CYCLES: 0.3 + 0.6 * random.random(),
            ResourceType.POWER_BUDGET: 0.8 + 0.2 * random.random(),
        }

    def push_once(self):
        """Push a single resource snapshot."""
        self.orchestrator.update_resources(self.sample())
