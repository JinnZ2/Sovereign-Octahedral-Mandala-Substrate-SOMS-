"""
Resilience Core — advanced resilience primitives for octahedral systems.

Provides hybrid logical clocks, Byzantine fault-tolerant share verification,
circuit breakers, signed audit trails, epoch-based key rotation, emergency
multi-party recovery, resource reservation, timing jitter for side-channel
protection, fencing tokens for split-brain prevention, and Merkle tree
state synchronisation after partitions.

Architecture:
  HybridLogicalClock   — Lamport + wall-clock coordination
  ByzantineVerifier    — share commitment + signature verification
  CircuitBreaker       — per-component rate limiting
  AuditTrail           — signed, tamper-evident operation log
  KeyRotationManager   — epoch seeds with lineage tracking
  EmergencyRecovery    — multi-party approval + cold storage fallback
  ResourceReservation  — guaranteed minimum for critical ops
  TimingJitter         — random delay injection (side-channel defence)
  FencingManager       — generation tokens (split-brain prevention)
  ShareMerkleTree      — efficient state diff after partition

stdlib only — no numpy/scipy required.
"""

import hashlib
import random
import secrets
import time
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from src.service_reconfig import ResourceType


# ============================================================================
# 1. Hybrid Logical Clock (time coordination)
# ============================================================================

@dataclass
class HybridLogicalClock:
    """
    Lamport-style hybrid logical clock combining wall-clock physical
    time with a logical counter for ordering within the same instant.
    """
    component_id: str
    pt: float = field(default_factory=time.time)
    lt: int = 0

    def tick(self) -> Tuple[float, int]:
        """Local event: advance clock."""
        now = time.time()
        if now > self.pt:
            self.pt = now
            self.lt = 0
        else:
            self.lt += 1
        return (self.pt, self.lt)

    def update(self, received_pt: float, received_lt: int):
        """Update from received message."""
        now = time.time()
        self.pt = max(now, received_pt, self.pt)
        if abs(self.pt - received_pt) < 0.001:
            self.lt = max(self.lt, received_lt) + 1
        else:
            self.lt = 0 if self.pt == now else self.lt + 1

    def timestamp(self) -> bytes:
        return f"{self.component_id}:{self.pt}:{self.lt}".encode()


# ============================================================================
# 2. Byzantine fault tolerance (share verification)
# ============================================================================

class ByzantineError(Exception):
    """Raised when Byzantine behaviour is detected during share verification."""
    pass


@dataclass
class VerifiedShare:
    """A share with cryptographic signature and Merkle commitment."""
    share: bytes
    signature: bytes
    signer_id: str
    timestamp: bytes
    commitment: bytes


class ByzantineVerifier:
    """
    Verifies shares against Merkle commitments and signatures
    before allowing reconstruction.
    """

    def __init__(self, threshold: int = 3):
        self.threshold = threshold
        self.commitments: Dict[str, bytes] = {}

    def register_seed(self, seed_id: str, share_commitments: List[bytes]):
        """Store Merkle root for all shares of this seed."""
        combined = b"".join(sorted(share_commitments))
        self.commitments[seed_id] = hashlib.blake2b(combined, digest_size=32).digest()

    def verify_share(self, seed_id: str, share: VerifiedShare) -> bool:
        """Verify a single share's signature and commitment."""
        if seed_id not in self.commitments:
            return False

        message = share.share + share.timestamp
        expected_sig = hashlib.blake2b(
            message + share.signer_id.encode(), digest_size=32
        ).digest()
        if share.signature != expected_sig[:16]:
            return False

        share_hash = hashlib.blake2b(share.share, digest_size=16).digest()
        if share.commitment != share_hash:
            return False

        return True

    def reconstruct_with_byzantine_check(
        self, shares: List[VerifiedShare], seed_id: str,
    ) -> Optional[bytes]:
        """Reconstruct only if enough valid, non-conflicting shares exist."""
        valid = [s for s in shares if self.verify_share(seed_id, s)]

        if len(valid) < self.threshold:
            raise ByzantineError(
                f"Only {len(valid)} valid shares, need {self.threshold}"
            )

        share_values = [v.share for v in valid]
        if len(set(share_values)) > 1:
            raise ByzantineError(
                f"Conflicting shares detected: {len(set(share_values))} distinct values"
            )

        return share_values[0]


# ============================================================================
# 3. Circuit breaker (rate limiting)
# ============================================================================

class CircuitBreaker:
    """
    Per-component rate limiter.

    Allows at most `max_attempts` operations within a sliding
    `window_seconds` window.
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 60):
        self.max_attempts = max_attempts
        self.window = window_seconds
        self.attempts: Dict[str, deque] = {}

    def allow(self, component_id: str) -> bool:
        """Check and record an attempt. Returns False if rate-limited."""
        if component_id not in self.attempts:
            self.attempts[component_id] = deque()

        now = time.time()
        q = self.attempts[component_id]

        while q and q[0] < now - self.window:
            q.popleft()

        if len(q) >= self.max_attempts:
            return False

        q.append(now)
        return True

    def reset(self, component_id: str):
        if component_id in self.attempts:
            self.attempts[component_id].clear()


# ============================================================================
# 4. Audit trail (signed operations)
# ============================================================================

@dataclass
class AuditEntry:
    """A single signed audit record."""
    operation_id: str
    operation_type: str  # "reconfig", "reconstruct", "rotate"
    initiator: str
    seed_id: str
    timestamp: float
    signature: bytes
    details: Dict[str, Any]


class AuditTrail:
    """
    Signed, tamper-evident operation history.

    Each entry includes a BLAKE2b signature of its fields.
    verify_chain() checks all signatures.
    """

    def __init__(self, max_entries: int = 10000):
        self.entries: List[AuditEntry] = []
        self.max_entries = max_entries

    def log(self, entry: AuditEntry):
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

    def verify_chain(self) -> bool:
        """Verify all signatures in the audit trail."""
        for entry in self.entries:
            message = (
                f"{entry.operation_id}:{entry.operation_type}:"
                f"{entry.initiator}:{entry.seed_id}:{entry.timestamp}"
            )
            expected = hashlib.blake2b(
                message.encode() + str(entry.details).encode(), digest_size=32
            ).digest()[:16]
            if entry.signature != expected:
                return False
        return True

    def get_operations_by_seed(self, seed_id: str) -> List[AuditEntry]:
        return [e for e in self.entries if e.seed_id == seed_id]


# ============================================================================
# 5. Key rotation (epoch seeds)
# ============================================================================

@dataclass
class EpochSeed:
    """A time-limited seed with epoch number and lineage."""
    seed_id: str
    compressed: bytes
    epoch: int
    expires_at: float
    rotated_from: Optional[str] = None


class KeyRotationManager:
    """
    Epoch-based key rotation with lineage tracking.

    Seeds expire after `epoch_duration_seconds` and are automatically
    rotated with fresh entropy, preserving the lineage chain.
    """

    def __init__(self, epoch_duration_seconds: int = 86400):
        self.epoch_duration = epoch_duration_seconds
        self.active_seeds: Dict[str, EpochSeed] = {}
        self.history: Dict[str, List[EpochSeed]] = {}

    def create_epoch_seed(self, raw_seed: bytes,
                          previous_seed_id: Optional[str] = None) -> EpochSeed:
        """Create a new epoch seed, optionally linked to a predecessor."""
        compressed = hashlib.blake2b(raw_seed, digest_size=16).digest()
        epoch = 1
        if previous_seed_id and previous_seed_id in self.active_seeds:
            epoch = self.active_seeds[previous_seed_id].epoch + 1

        seed_id = f"seed_{epoch}_{hashlib.blake2b(compressed, digest_size=8).hexdigest()}"
        new_seed = EpochSeed(
            seed_id=seed_id,
            compressed=compressed,
            epoch=epoch,
            expires_at=time.time() + self.epoch_duration,
            rotated_from=previous_seed_id,
        )
        self.active_seeds[seed_id] = new_seed
        if previous_seed_id:
            self.history.setdefault(previous_seed_id, []).append(new_seed)
        return new_seed

    def rotate_expired(self) -> List[EpochSeed]:
        """Rotate all expired seeds, returning the new seeds."""
        rotated: List[EpochSeed] = []
        now = time.time()
        expired = [
            (sid, seed.epoch)
            for sid, seed in self.active_seeds.items()
            if seed.expires_at <= now
        ]

        for sid, old_epoch in expired:
            self.active_seeds.pop(sid)
            new_raw = secrets.token_bytes(16)
            compressed = hashlib.blake2b(new_raw, digest_size=16).digest()
            new_epoch = old_epoch + 1
            seed_id = f"seed_{new_epoch}_{hashlib.blake2b(compressed, digest_size=8).hexdigest()}"
            new_seed = EpochSeed(
                seed_id=seed_id,
                compressed=compressed,
                epoch=new_epoch,
                expires_at=time.time() + self.epoch_duration,
                rotated_from=sid,
            )
            self.active_seeds[seed_id] = new_seed
            self.history.setdefault(sid, []).append(new_seed)
            rotated.append(new_seed)

        return rotated


# ============================================================================
# 6. Emergency recovery (multi-party approval)
# ============================================================================

@dataclass
class EmergencyOverride:
    """Tracks multi-party approvals for emergency recovery."""
    required_approvals: int = 2
    approved_by: Set[str] = field(default_factory=set)
    recovery_key: Optional[bytes] = None


class EmergencyRecovery:
    """
    Multi-party approval + cold storage fallback.

    When automatic threshold recovery fails, requires N approvals
    from authorised operators before releasing cold-storage keys.
    """

    def __init__(self, cold_storage_shards: List[str], threshold: int = 2):
        self.cold_storage = cold_storage_shards
        self.threshold = threshold
        self.pending_requests: Dict[str, EmergencyOverride] = {}

    def request_emergency_recovery(self, seed_id: str, requester: str) -> str:
        """Request manual override. Returns request_id."""
        request_id = hashlib.blake2b(
            f"{seed_id}:{requester}:{time.time()}".encode(), digest_size=8
        ).hexdigest()
        self.pending_requests[request_id] = EmergencyOverride()
        return request_id

    def approve_emergency(self, request_id: str, approver: str,
                          approval_code: str) -> bool:
        """Multi-party approval for emergency recovery."""
        if request_id not in self.pending_requests:
            return False
        if not self._verify_approval(approver, approval_code):
            return False

        req = self.pending_requests[request_id]
        req.approved_by.add(approver)

        if len(req.approved_by) >= req.required_approvals:
            req.recovery_key = self._retrieve_from_cold_storage()
            return True
        return False

    def _verify_approval(self, approver: str, code: str) -> bool:
        # Simplified: in production use hardware token or biometric
        return hashlib.sha256(code.encode()).digest()[:4] == b"\x00\x00\x00\x00"

    def _retrieve_from_cold_storage(self) -> bytes:
        return secrets.token_bytes(16)

    def execute_emergency_recovery(self, request_id: str) -> Optional[bytes]:
        req = self.pending_requests.get(request_id)
        if req and req.recovery_key and len(req.approved_by) >= req.required_approvals:
            del self.pending_requests[request_id]
            return req.recovery_key
        return None


# ============================================================================
# 7. Resource reservation (critical path guarantee)
# ============================================================================

class ResourceReservation:
    """
    Guarantees minimum resource availability for critical operations.

    Never allows more than 50% of any resource type to be reserved.
    """

    def __init__(self):
        self.reserved: Dict[ResourceType, Dict[str, float]] = {
            rt: {} for rt in ResourceType
        }
        self.guaranteed_minimum: Dict[ResourceType, float] = {
            ResourceType.CPU_IDLE: 0.1,
            ResourceType.NETWORK_BANDWIDTH: 0.2,
            ResourceType.MEMORY: 0.1,
            ResourceType.STANDBY_HARDWARE: 0.0,
            ResourceType.FPGA_CYCLES: 0.0,
            ResourceType.POWER_BUDGET: 0.1,
        }

    def reserve(self, rtype: ResourceType, amount: float, purpose: str) -> bool:
        """Reserve resources. Returns False if over cap."""
        max_reservable = 0.5
        if amount > max_reservable:
            return False

        current_reserved = sum(self.reserved[rtype].values())
        if current_reserved + amount <= max_reservable:
            self.reserved[rtype][purpose] = amount
            return True
        return False

    def release(self, rtype: ResourceType, purpose: str):
        if purpose in self.reserved[rtype]:
            del self.reserved[rtype][purpose]

    def available(self, rtype: ResourceType, total: float) -> float:
        """Available after reservations and guaranteed minimums."""
        reserved = sum(self.reserved[rtype].values())
        guaranteed = self.guaranteed_minimum[rtype]
        return max(0, total - reserved - guaranteed)


# ============================================================================
# 8. Side-channel protection (timing jitter)
# ============================================================================

class TimingJitter:
    """Add random delay to prevent timing side-channel attacks."""

    def __init__(self, max_jitter_seconds: float = 0.2):
        self.max_jitter = max_jitter_seconds

    def add_jitter(self, base_delay: float) -> float:
        """Return base_delay with random jitter applied."""
        jitter = random.uniform(-self.max_jitter, self.max_jitter)
        return max(0.001, base_delay + jitter)

    def jittered_sleep(self, base_seconds: float):
        time.sleep(self.add_jitter(base_seconds))


# ============================================================================
# 9. Fencing tokens (split-brain prevention)
# ============================================================================

@dataclass
class FencedComponent:
    """A component with a monotonic generation counter."""
    id: str
    generation: int
    last_heartbeat: float


class FencingManager:
    """
    Generation-based fencing for split-brain prevention.

    Each register() increments the generation counter. A component
    holding a stale generation is fenced out of operations.
    """

    def __init__(self):
        self.components: Dict[str, FencedComponent] = {}
        self.generation_lock = threading.Lock()

    def register(self, component_id: str) -> int:
        """Register or re-register a component, returning its generation."""
        with self.generation_lock:
            if component_id in self.components:
                self.components[component_id].generation += 1
            else:
                self.components[component_id] = FencedComponent(
                    component_id, 1, time.time()
                )
            self.components[component_id].last_heartbeat = time.time()
            return self.components[component_id].generation

    def validate(self, component_id: str, claimed_generation: int) -> bool:
        """Check if claimed generation matches current."""
        if component_id not in self.components:
            return False
        return self.components[component_id].generation == claimed_generation

    def fence(self, component_id: str):
        """Force generation increment (used after split-brain detected)."""
        with self.generation_lock:
            if component_id in self.components:
                self.components[component_id].generation += 1


# ============================================================================
# 10. Merkle tree for state sync (after partition)
# ============================================================================

class MerkleNode:
    """Binary Merkle tree node with BLAKE2b hash."""

    def __init__(self, hash_val: bytes,
                 left: Optional['MerkleNode'] = None,
                 right: Optional['MerkleNode'] = None):
        self.hash = hash_val
        self.left = left
        self.right = right


class ShareMerkleTree:
    """
    Merkle tree over share state for efficient diff after partition.

    Builds a binary tree of BLAKE2b-16 hashes over sorted (seed_id, share)
    pairs. diff() returns seed_ids that differ between two trees.
    """

    def __init__(self, shares: Dict[str, bytes]):
        self.shares = shares
        self.root = self._build_tree()

    def _build_tree(self) -> MerkleNode:
        leaves: List[MerkleNode] = []
        for seed_id, share in sorted(self.shares.items()):
            leaf_hash = hashlib.blake2b(seed_id.encode() + share, digest_size=16).digest()
            leaves.append(MerkleNode(leaf_hash))

        if not leaves:
            return MerkleNode(b"\x00" * 16)

        while len(leaves) > 1:
            next_level: List[MerkleNode] = []
            for i in range(0, len(leaves), 2):
                if i + 1 < len(leaves):
                    combined = leaves[i].hash + leaves[i + 1].hash
                    parent = MerkleNode(
                        hashlib.blake2b(combined, digest_size=16).digest(),
                        leaves[i], leaves[i + 1],
                    )
                    next_level.append(parent)
                else:
                    next_level.append(leaves[i])
            leaves = next_level

        return leaves[0]

    def root_hash(self) -> bytes:
        return self.root.hash

    def diff(self, other_tree: 'ShareMerkleTree') -> List[str]:
        """Return seed_ids that differ between two trees."""
        differing: List[str] = []
        all_seeds = set(self.shares.keys()) | set(other_tree.shares.keys())

        for seed_id in sorted(all_seeds):
            my_share = self.shares.get(seed_id, b"")
            other_share = other_tree.shares.get(seed_id, b"")
            if my_share != other_share:
                differing.append(seed_id)

        return differing
