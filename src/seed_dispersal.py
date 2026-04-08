"""
Seed Dispersal — automatic seed compression, secret sharing, and hardware dispersal.

Implements Shamir-like threshold secret sharing for lattice keys,
dispersal of shares across hardware components (TPM, FPGA, secure
enclaves), and minimal-bandwidth gossip communication for peer sync.

Architecture:
  CompressedSeed  — BLAKE2b-checksummed seed with SHA-256 compression
  SeedSplitter    — polynomial evaluation secret sharing (split / rebuild)
  HardwareComponent — share storage per component
  SeedDispersal   — split + disperse + reconstruct across hardware pool
  MinimalComms    — XOR diff / patch + Merkle-like gossip protocol

stdlib only — no numpy/scipy required.
"""

import hashlib
import secrets
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ============================================================================
# Compressed seed with integrity check
# ============================================================================

@dataclass
class CompressedSeed:
    """
    A seed that can be split, compressed, and verified.

    Uses BLAKE2b-16 for integrity checksum and SHA-256 truncated
    to 16 bytes for non-reversible compression.
    """
    value: bytes
    checksum: bytes = field(init=False)

    def __post_init__(self):
        self.checksum = hashlib.blake2b(self.value, digest_size=16).digest()

    def verify(self) -> bool:
        """Check integrity against stored checksum."""
        return hashlib.blake2b(self.value, digest_size=16).digest() == self.checksum

    def compress(self) -> bytes:
        """Non-reversible compression: SHA-256 truncated to 16 bytes."""
        return hashlib.sha256(self.value).digest()[:16]


# ============================================================================
# Shamir-like secret sharing (XOR-based polynomial evaluation)
# ============================================================================

class SeedSplitter:
    """
    Split a seed into M shares where any K can rebuild.

    Uses polynomial evaluation over Python big-ints (simplified
    Shamir scheme — for production, use GF(2^128)).
    """

    # Large prime for modular arithmetic (2^127 - 1, Mersenne prime)
    PRIME = (1 << 127) - 1

    @staticmethod
    def split(seed: bytes, total_shares: int, threshold: int) -> List[bytes]:
        """Generate shares — any `threshold` shares reconstruct the seed."""
        if threshold > total_shares:
            raise ValueError("Threshold cannot exceed total shares")

        P = SeedSplitter.PRIME
        coeffs = [int.from_bytes(secrets.token_bytes(16), "big") % P for _ in range(threshold)]
        coeffs[0] = (
            int.from_bytes(seed, "big") if len(seed) <= 16
            else int.from_bytes(seed[:16], "big")
        ) % P

        shares = []
        for x in range(1, total_shares + 1):
            y = sum(coeff * pow(x, i, P) for i, coeff in enumerate(coeffs)) % P
            shares.append(y.to_bytes(16, "big"))
        return shares

    @staticmethod
    def rebuild(shares: List[bytes], indices: List[int], threshold: int) -> bytes:
        """Rebuild seed from at least `threshold` shares via Lagrange interpolation."""
        if len(shares) < threshold:
            raise ValueError(f"Need at least {threshold} shares, got {len(shares)}")

        P = SeedSplitter.PRIME
        points = [(indices[i], int.from_bytes(shares[i], "big") % P) for i in range(threshold)]
        secret = 0
        for i, (xi, yi) in enumerate(points):
            num, den = 1, 1
            for j, (xj, _) in enumerate(points):
                if i != j:
                    num = (num * (-xj)) % P
                    den = (den * (xi - xj)) % P
            secret = (secret + yi * num * pow(den, P - 2, P)) % P
        return secret.to_bytes(16, "big")


# ============================================================================
# Hardware component (share storage)
# ============================================================================

@dataclass
class HardwareComponent:
    """
    A hardware component (TPM, FPGA, secure enclave) that stores
    seed shares keyed by seed_id.
    """
    id: str
    shares_held: Dict[str, bytes] = field(default_factory=dict)

    def store_share(self, seed_id: str, share: bytes):
        self.shares_held[seed_id] = share

    def retrieve_share(self, seed_id: str) -> Optional[bytes]:
        return self.shares_held.get(seed_id)

    def heartbeat(self) -> bool:
        """Liveness check (simulated)."""
        return True


# ============================================================================
# Seed dispersal across hardware pool
# ============================================================================

class SeedDispersal:
    """
    Disperse compressed seeds across hardware components.

    Splits a seed into `total_shares` shares, distributes them
    round-robin across components, and can reconstruct from any
    `threshold` available shares.
    """

    def __init__(self, components: List[HardwareComponent],
                 total_shares: int = 5, threshold: int = 3):
        self.components: Dict[str, HardwareComponent] = {c.id: c for c in components}
        self.total_shares = total_shares
        self.threshold = threshold
        self.seed_registry: Dict[str, Tuple[bytes, List[str]]] = {}

    def disperse(self, seed: CompressedSeed) -> str:
        """Split seed into shares, disperse to components. Returns seed_id."""
        seed_id = hashlib.blake2b(seed.value, digest_size=8).hexdigest()
        shares = SeedSplitter.split(seed.value, self.total_shares, self.threshold)

        component_ids = list(self.components.keys())
        if len(component_ids) < self.total_shares:
            raise ValueError(f"Need {self.total_shares} components, have {len(component_ids)}")

        assigned: List[str] = []
        for i, share in enumerate(shares):
            comp_id = component_ids[i % len(component_ids)]
            self.components[comp_id].store_share(seed_id, share)
            assigned.append(comp_id)

        compressed = seed.compress()
        self.seed_registry[seed_id] = (compressed, assigned)
        return seed_id

    def reconstruct(self, seed_id: str) -> Optional[CompressedSeed]:
        """Pull shares from components and rebuild."""
        if seed_id not in self.seed_registry:
            return None

        compressed, component_ids = self.seed_registry[seed_id]

        shares: List[bytes] = []
        indices: List[int] = []
        for i, comp_id in enumerate(component_ids[:self.threshold], start=1):
            share = self.components[comp_id].retrieve_share(seed_id)
            if share:
                shares.append(share)
                indices.append(i)

        if len(shares) < self.threshold:
            return None

        rebuilt_bytes = SeedSplitter.rebuild(shares, indices, self.threshold)
        candidate = CompressedSeed(rebuilt_bytes)

        if candidate.compress() == compressed and candidate.verify():
            return candidate
        return None


# ============================================================================
# Minimal communication (gossip + diff)
# ============================================================================

class MinimalComms:
    """
    Low-bandwidth, high-latency tolerant communication.

    Provides XOR-based diff/patch and Merkle-like gossip that only
    sends state to peers whose hash differs from the local hash.
    """

    @staticmethod
    def diff(old: bytes, new: bytes) -> bytes:
        """XOR diff between two byte strings."""
        if old == new:
            return b""
        return bytes(a ^ b for a, b in zip(old, new))

    @staticmethod
    def patch(base: bytes, diff_bytes: bytes) -> bytes:
        """Apply XOR diff to base."""
        return bytes(a ^ b for a, b in zip(base, diff_bytes))

    @staticmethod
    def gossip(peer_states: Dict[str, bytes], local_state: bytes) -> Dict[str, bytes]:
        """Only send state to peers whose hash differs."""
        updates: Dict[str, bytes] = {}
        local_hash = hashlib.blake2b(local_state, digest_size=8).digest()
        for peer_id, peer_hash in peer_states.items():
            if peer_hash != local_hash:
                updates[peer_id] = local_state
        return updates


# ============================================================================
# Integration: Octahedral + Seed system
# ============================================================================

class OctahedralWithSeedSystem:
    """
    Combines hardware component pool with seed dispersal and gossip comms.

    bootstrap_seed()  — compress, split, disperse a new seed
    refresh_seed()    — reconstruct + verify from hardware
    sync_gossip()     — minimal peer sync
    """

    def __init__(self):
        self.hw_components = [
            HardwareComponent("tpm_0"),
            HardwareComponent("tpm_1"),
            HardwareComponent("fpga_0"),
            HardwareComponent("fpga_1"),
            HardwareComponent("secure_enclave"),
        ]
        self.dispersal = SeedDispersal(self.hw_components, total_shares=5, threshold=3)
        self.comms = MinimalComms()
        self.active_seeds: Dict[str, CompressedSeed] = {}

    def bootstrap_seed(self, raw_seed: bytes) -> str:
        """Compress, split, disperse a new seed. Returns seed_id."""
        compressed = CompressedSeed(raw_seed)
        seed_id = self.dispersal.disperse(compressed)
        self.active_seeds[seed_id] = compressed
        return seed_id

    def refresh_seed(self, seed_id: str) -> bool:
        """Reconstruct from hardware, verify, update active."""
        recovered = self.dispersal.reconstruct(seed_id)
        if recovered and recovered.verify():
            self.active_seeds[seed_id] = recovered
            return True
        return False

    def sync_gossip(self, peer_hashes: Dict[str, bytes]) -> Dict[str, bytes]:
        """Minimal sync — only send what's missing."""
        my_state = b"".join(s.compress() for s in self.active_seeds.values())
        return self.comms.gossip(peer_hashes, my_state)
