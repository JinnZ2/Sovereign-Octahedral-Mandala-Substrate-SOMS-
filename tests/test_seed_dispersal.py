"""Tests for seed_dispersal.py — seed compression, secret sharing, dispersal."""

import secrets
import pytest

from src.seed_dispersal import (
    CompressedSeed, SeedSplitter, HardwareComponent,
    SeedDispersal, MinimalComms, OctahedralWithSeedSystem,
)


# ============================================================================
# CompressedSeed
# ============================================================================

class TestCompressedSeed:
    def test_verify_intact(self):
        seed = CompressedSeed(b"hello world 1234")
        assert seed.verify()

    def test_verify_tampered(self):
        seed = CompressedSeed(b"hello world 1234")
        seed.checksum = b"\x00" * 16
        assert not seed.verify()

    def test_compress_deterministic(self):
        seed = CompressedSeed(b"test_seed")
        c1 = seed.compress()
        c2 = seed.compress()
        assert c1 == c2
        assert len(c1) == 16

    def test_compress_differs_by_value(self):
        s1 = CompressedSeed(b"seed_a")
        s2 = CompressedSeed(b"seed_b")
        assert s1.compress() != s2.compress()


# ============================================================================
# SeedSplitter
# ============================================================================

class TestSeedSplitter:
    def test_split_count(self):
        seed = secrets.token_bytes(16)
        shares = SeedSplitter.split(seed, total_shares=5, threshold=3)
        assert len(shares) == 5

    def test_split_threshold_exceeds(self):
        with pytest.raises(ValueError):
            SeedSplitter.split(b"x" * 16, total_shares=2, threshold=5)

    def test_shares_are_16_bytes(self):
        shares = SeedSplitter.split(b"\x01" * 16, total_shares=3, threshold=2)
        for share in shares:
            assert len(share) == 16

    def test_rebuild_needs_threshold(self):
        with pytest.raises(ValueError):
            SeedSplitter.rebuild([b"x" * 16], indices=[1], threshold=3)


# ============================================================================
# HardwareComponent
# ============================================================================

class TestHardwareComponent:
    def test_store_and_retrieve(self):
        comp = HardwareComponent("tpm_0")
        comp.store_share("seed_1", b"share_data")
        assert comp.retrieve_share("seed_1") == b"share_data"

    def test_retrieve_missing(self):
        comp = HardwareComponent("tpm_0")
        assert comp.retrieve_share("nonexistent") is None

    def test_heartbeat(self):
        comp = HardwareComponent("tpm_0")
        assert comp.heartbeat() is True


# ============================================================================
# SeedDispersal
# ============================================================================

class TestSeedDispersal:
    @pytest.fixture
    def dispersal(self):
        comps = [HardwareComponent(f"hw_{i}") for i in range(5)]
        return SeedDispersal(comps, total_shares=5, threshold=3)

    def test_disperse_returns_seed_id(self, dispersal):
        seed = CompressedSeed(secrets.token_bytes(16))
        seed_id = dispersal.disperse(seed)
        assert isinstance(seed_id, str)
        assert len(seed_id) == 16  # blake2b hex digest_size=8 -> 16 hex chars

    def test_disperse_registers_seed(self, dispersal):
        seed = CompressedSeed(secrets.token_bytes(16))
        seed_id = dispersal.disperse(seed)
        assert seed_id in dispersal.seed_registry

    def test_disperse_insufficient_components(self):
        comps = [HardwareComponent(f"hw_{i}") for i in range(2)]
        dispersal = SeedDispersal(comps, total_shares=5, threshold=3)
        seed = CompressedSeed(secrets.token_bytes(16))
        with pytest.raises(ValueError):
            dispersal.disperse(seed)

    def test_reconstruct_not_found(self, dispersal):
        assert dispersal.reconstruct("nonexistent") is None


# ============================================================================
# MinimalComms
# ============================================================================

class TestMinimalComms:
    def test_diff_identical(self):
        assert MinimalComms.diff(b"hello", b"hello") == b""

    def test_diff_patch_roundtrip(self):
        old = b"abcdef"
        new = b"xbcdey"
        d = MinimalComms.diff(old, new)
        assert MinimalComms.patch(old, d) == new

    def test_gossip_sends_to_different(self):
        import hashlib
        local = b"my_state"
        local_hash = hashlib.blake2b(local, digest_size=8).digest()
        peers = {
            "peer_a": b"\x00" * 8,  # different hash
            "peer_b": local_hash,   # same hash
        }
        updates = MinimalComms.gossip(peers, local)
        assert "peer_a" in updates
        assert "peer_b" not in updates

    def test_gossip_empty_when_all_synced(self):
        import hashlib
        local = b"synced"
        local_hash = hashlib.blake2b(local, digest_size=8).digest()
        peers = {"p1": local_hash, "p2": local_hash}
        updates = MinimalComms.gossip(peers, local)
        assert len(updates) == 0


# ============================================================================
# OctahedralWithSeedSystem
# ============================================================================

class TestOctahedralWithSeedSystem:
    def test_bootstrap_seed(self):
        system = OctahedralWithSeedSystem()
        seed_id = system.bootstrap_seed(secrets.token_bytes(16))
        assert seed_id in system.active_seeds

    def test_sync_gossip(self):
        system = OctahedralWithSeedSystem()
        system.bootstrap_seed(secrets.token_bytes(16))
        peer_hashes = {"node_a": b"\x00" * 8}
        updates = system.sync_gossip(peer_hashes)
        # Should send state since hashes differ
        assert "node_a" in updates
