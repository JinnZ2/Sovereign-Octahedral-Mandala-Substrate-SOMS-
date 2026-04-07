"""Tests for resilience_core.py — advanced resilience primitives."""

import hashlib
import secrets
import time
import pytest

from src.service_reconfig import ResourceType
from src.resilience_core import (
    HybridLogicalClock,
    ByzantineError, ByzantineVerifier, VerifiedShare,
    CircuitBreaker,
    AuditEntry, AuditTrail,
    EpochSeed, KeyRotationManager,
    EmergencyOverride, EmergencyRecovery,
    ResourceReservation,
    TimingJitter,
    FencedComponent, FencingManager,
    MerkleNode, ShareMerkleTree,
)


# ============================================================================
# HybridLogicalClock
# ============================================================================

class TestHybridLogicalClock:
    def test_tick_advances(self):
        hlc = HybridLogicalClock("node_0")
        pt1, lt1 = hlc.tick()
        pt2, lt2 = hlc.tick()
        assert (pt2, lt2) >= (pt1, lt1)

    def test_update_from_future(self):
        hlc = HybridLogicalClock("node_0")
        future_pt = time.time() + 1000
        hlc.update(future_pt, 5)
        assert hlc.pt >= future_pt

    def test_timestamp_bytes(self):
        hlc = HybridLogicalClock("node_0")
        ts = hlc.timestamp()
        assert isinstance(ts, bytes)
        assert b"node_0" in ts


# ============================================================================
# ByzantineVerifier
# ============================================================================

class TestByzantineVerifier:
    @pytest.fixture
    def verifier(self):
        return ByzantineVerifier(threshold=2)

    def _make_share(self, share_data: bytes, signer: str) -> VerifiedShare:
        ts = b"t0"
        message = share_data + ts
        sig = hashlib.blake2b(message + signer.encode(), digest_size=32).digest()[:16]
        commitment = hashlib.blake2b(share_data, digest_size=16).digest()
        return VerifiedShare(
            share=share_data,
            signature=sig,
            signer_id=signer,
            timestamp=ts,
            commitment=commitment,
        )

    def test_register_seed(self, verifier):
        commits = [hashlib.blake2b(b"s1", digest_size=16).digest()]
        verifier.register_seed("seed_a", commits)
        assert "seed_a" in verifier.commitments

    def test_verify_valid_share(self, verifier):
        share_data = b"share_content"
        share = self._make_share(share_data, "signer_0")
        commitment = hashlib.blake2b(share_data, digest_size=16).digest()
        verifier.register_seed("seed_a", [commitment])
        assert verifier.verify_share("seed_a", share)

    def test_verify_bad_signature(self, verifier):
        share = VerifiedShare(
            share=b"data", signature=b"\x00" * 16,
            signer_id="s", timestamp=b"t", commitment=b"\x00" * 16,
        )
        verifier.register_seed("seed_a", [b"\x00" * 16])
        assert not verifier.verify_share("seed_a", share)

    def test_verify_unregistered_seed(self, verifier):
        share = self._make_share(b"data", "s")
        assert not verifier.verify_share("unknown", share)

    def test_reconstruct_insufficient(self, verifier):
        with pytest.raises(ByzantineError):
            verifier.reconstruct_with_byzantine_check([], "seed_a")


# ============================================================================
# CircuitBreaker
# ============================================================================

class TestCircuitBreaker:
    def test_allows_under_limit(self):
        cb = CircuitBreaker(max_attempts=3, window_seconds=60)
        assert cb.allow("comp_0")
        assert cb.allow("comp_0")
        assert cb.allow("comp_0")

    def test_blocks_over_limit(self):
        cb = CircuitBreaker(max_attempts=2, window_seconds=60)
        assert cb.allow("comp_0")
        assert cb.allow("comp_0")
        assert not cb.allow("comp_0")

    def test_reset_clears(self):
        cb = CircuitBreaker(max_attempts=1, window_seconds=60)
        cb.allow("comp_0")
        assert not cb.allow("comp_0")
        cb.reset("comp_0")
        assert cb.allow("comp_0")

    def test_independent_components(self):
        cb = CircuitBreaker(max_attempts=1, window_seconds=60)
        assert cb.allow("comp_0")
        assert cb.allow("comp_1")  # different component


# ============================================================================
# AuditTrail
# ============================================================================

class TestAuditTrail:
    def _make_entry(self, op_type: str = "reconfig", seed_id: str = "seed_a") -> AuditEntry:
        op_id = secrets.token_hex(8)
        ts = time.time()
        details = {"test": True}
        message = f"{op_id}:{op_type}:initiator:{seed_id}:{ts}"
        sig = hashlib.blake2b(
            message.encode() + str(details).encode(), digest_size=32
        ).digest()[:16]
        return AuditEntry(
            operation_id=op_id, operation_type=op_type,
            initiator="initiator", seed_id=seed_id,
            timestamp=ts, signature=sig, details=details,
        )

    def test_log_and_count(self):
        trail = AuditTrail()
        trail.log(self._make_entry())
        trail.log(self._make_entry())
        assert len(trail.entries) == 2

    def test_verify_chain_valid(self):
        trail = AuditTrail()
        trail.log(self._make_entry())
        trail.log(self._make_entry())
        assert trail.verify_chain()

    def test_verify_chain_tampered(self):
        trail = AuditTrail()
        entry = self._make_entry()
        trail.log(entry)
        entry.signature = b"\x00" * 16  # tamper
        assert not trail.verify_chain()

    def test_max_entries_cap(self):
        trail = AuditTrail(max_entries=5)
        for _ in range(10):
            trail.log(self._make_entry())
        assert len(trail.entries) == 5

    def test_get_by_seed(self):
        trail = AuditTrail()
        trail.log(self._make_entry(seed_id="seed_a"))
        trail.log(self._make_entry(seed_id="seed_b"))
        trail.log(self._make_entry(seed_id="seed_a"))
        assert len(trail.get_operations_by_seed("seed_a")) == 2


# ============================================================================
# KeyRotationManager
# ============================================================================

class TestKeyRotationManager:
    def test_create_epoch_seed(self):
        mgr = KeyRotationManager(epoch_duration_seconds=3600)
        seed = mgr.create_epoch_seed(b"raw_seed_data_16")
        assert seed.epoch == 1
        assert seed.seed_id in mgr.active_seeds

    def test_lineage_increments_epoch(self):
        mgr = KeyRotationManager()
        s1 = mgr.create_epoch_seed(b"first_seed_12345")
        s2 = mgr.create_epoch_seed(b"second_seed_1234", previous_seed_id=s1.seed_id)
        assert s2.epoch == 2
        assert s2.rotated_from == s1.seed_id

    def test_rotate_expired(self):
        mgr = KeyRotationManager(epoch_duration_seconds=0)  # expires immediately
        s1 = mgr.create_epoch_seed(b"expiring_seed_16")
        time.sleep(0.01)
        rotated = mgr.rotate_expired()
        assert len(rotated) == 1
        assert rotated[0].epoch == 2

    def test_no_rotation_if_not_expired(self):
        mgr = KeyRotationManager(epoch_duration_seconds=9999)
        mgr.create_epoch_seed(b"long_lived_seed!")
        rotated = mgr.rotate_expired()
        assert len(rotated) == 0


# ============================================================================
# EmergencyRecovery
# ============================================================================

class TestEmergencyRecovery:
    def test_request_returns_id(self):
        er = EmergencyRecovery(["hsm1", "hsm2"], threshold=2)
        req_id = er.request_emergency_recovery("seed_a", "operator_1")
        assert isinstance(req_id, str)
        assert req_id in er.pending_requests

    def test_execute_without_approval(self):
        er = EmergencyRecovery(["hsm1"], threshold=2)
        req_id = er.request_emergency_recovery("seed_a", "op")
        assert er.execute_emergency_recovery(req_id) is None


# ============================================================================
# ResourceReservation
# ============================================================================

class TestResourceReservation:
    def test_reserve_and_release(self):
        rr = ResourceReservation()
        assert rr.reserve(ResourceType.CPU_IDLE, 0.2, "task_a")
        rr.release(ResourceType.CPU_IDLE, "task_a")

    def test_reserve_over_cap(self):
        rr = ResourceReservation()
        assert not rr.reserve(ResourceType.CPU_IDLE, 0.6, "too_much")

    def test_available_after_reservation(self):
        rr = ResourceReservation()
        rr.reserve(ResourceType.CPU_IDLE, 0.2, "task_a")
        avail = rr.available(ResourceType.CPU_IDLE, total=1.0)
        # total(1.0) - reserved(0.2) - guaranteed_min(0.1) = 0.7
        assert avail == pytest.approx(0.7)

    def test_cumulative_reservation(self):
        rr = ResourceReservation()
        assert rr.reserve(ResourceType.MEMORY, 0.3, "a")
        assert rr.reserve(ResourceType.MEMORY, 0.2, "b")
        assert not rr.reserve(ResourceType.MEMORY, 0.1, "c")  # 0.3+0.2+0.1 > 0.5


# ============================================================================
# TimingJitter
# ============================================================================

class TestTimingJitter:
    def test_jitter_positive(self):
        jitter = TimingJitter(max_jitter_seconds=0.1)
        result = jitter.add_jitter(0.5)
        assert result >= 0.001

    def test_jitter_varies(self):
        jitter = TimingJitter(max_jitter_seconds=0.5)
        results = {jitter.add_jitter(1.0) for _ in range(20)}
        assert len(results) > 1  # should get different values


# ============================================================================
# FencingManager
# ============================================================================

class TestFencingManager:
    def test_register_returns_generation(self):
        fm = FencingManager()
        gen = fm.register("comp_0")
        assert gen == 1

    def test_re_register_increments(self):
        fm = FencingManager()
        fm.register("comp_0")
        gen2 = fm.register("comp_0")
        assert gen2 == 2

    def test_validate_current(self):
        fm = FencingManager()
        gen = fm.register("comp_0")
        assert fm.validate("comp_0", gen)

    def test_validate_stale(self):
        fm = FencingManager()
        gen1 = fm.register("comp_0")
        fm.register("comp_0")  # gen2
        assert not fm.validate("comp_0", gen1)

    def test_fence_increments(self):
        fm = FencingManager()
        gen = fm.register("comp_0")
        fm.fence("comp_0")
        assert not fm.validate("comp_0", gen)

    def test_validate_unknown(self):
        fm = FencingManager()
        assert not fm.validate("unknown", 1)


# ============================================================================
# ShareMerkleTree
# ============================================================================

class TestShareMerkleTree:
    def test_root_hash_deterministic(self):
        shares = {"seed_a": b"share_a", "seed_b": b"share_b"}
        t1 = ShareMerkleTree(shares)
        t2 = ShareMerkleTree(shares)
        assert t1.root_hash() == t2.root_hash()

    def test_root_hash_differs(self):
        t1 = ShareMerkleTree({"s": b"a"})
        t2 = ShareMerkleTree({"s": b"b"})
        assert t1.root_hash() != t2.root_hash()

    def test_diff_identical(self):
        shares = {"s1": b"d1", "s2": b"d2"}
        t1 = ShareMerkleTree(shares)
        t2 = ShareMerkleTree(shares)
        assert t1.diff(t2) == []

    def test_diff_detects_changes(self):
        t1 = ShareMerkleTree({"s1": b"d1", "s2": b"d2"})
        t2 = ShareMerkleTree({"s1": b"d1", "s2": b"changed"})
        diff = t1.diff(t2)
        assert "s2" in diff
        assert "s1" not in diff

    def test_diff_detects_missing(self):
        t1 = ShareMerkleTree({"s1": b"d1", "s2": b"d2"})
        t2 = ShareMerkleTree({"s1": b"d1"})
        diff = t1.diff(t2)
        assert "s2" in diff

    def test_empty_tree(self):
        t = ShareMerkleTree({})
        assert t.root_hash() == b"\x00" * 16
