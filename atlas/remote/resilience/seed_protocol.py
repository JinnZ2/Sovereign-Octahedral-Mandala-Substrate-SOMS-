#!/usr/bin/env python3
"""
sim/seed_protocol.py — Stdlib-Only Seed Protocol
CC0 public domain — github.com/JinnZ2/urban-resilience-sim

Physics-compliant seed expansion, packet encoding, mesh networking.
Zero external dependencies. No NumPy. Just Python and math.

This exists because the people who need resilience tools the most
are the ones least likely to have pip install working.

CORE IDEA:
    A seed is 6 proportional amplitudes across octahedral directions.
    40 bits. 5 bytes. Fits in a LoRa packet.
    Any device running the same physics arrives at the same structure.
    Identity, routing, and field reconstruction from a seed alone.

USAGE:
    python -m sim.seed_protocol
"""

import math
import struct
import zlib
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional


# =============================================================================
# STDLIB LINEAR ALGEBRA — replacing NumPy with 50 lines of arithmetic
# =============================================================================

def vec_dot(a: List[float], b: List[float]) -> float:
    """Dot product of two vectors."""
    return sum(x * y for x, y in zip(a, b))


def vec_add(a: List[float], b: List[float]) -> List[float]:
    """Element-wise addition."""
    return [x + y for x, y in zip(a, b)]


def vec_sub(a: List[float], b: List[float]) -> List[float]:
    """Element-wise subtraction."""
    return [x - y for x, y in zip(a, b)]


def vec_scale(a: List[float], s: float) -> List[float]:
    """Scalar multiply."""
    return [x * s for x in a]


def vec_abs_sum(a: List[float]) -> float:
    """L1 norm — used for seed distance."""
    return sum(abs(x) for x in a)


def vec_norm(a: List[float]) -> float:
    """L2 norm — used for spatial distance."""
    return math.sqrt(sum(x * x for x in a))


def mat_vec_mul(M: List[List[float]], v: List[float]) -> List[float]:
    """Matrix-vector multiply. M is list of rows."""
    return [vec_dot(row, v) for row in M]


def vec_zeros(n: int) -> List[float]:
    """Zero vector of length n."""
    return [0.0] * n


# =============================================================================
# GEOMETRY — octahedral directions
# =============================================================================

# 6 unit vectors defining the octahedron.
# These map to resilience domains in seed_mesh.py:
#   +X = food/water    -X = energy
#   +Y = social        -Y = institutional
#   +Z = knowledge     -Z = infrastructure
OCTAHEDRAL_DIRS = [
    [1.0, 0.0, 0.0],    # 0: +X
    [-1.0, 0.0, 0.0],   # 1: -X
    [0.0, 1.0, 0.0],    # 2: +Y
    [0.0, -1.0, 0.0],   # 3: -Y
    [0.0, 0.0, 1.0],    # 4: +Z
    [0.0, 0.0, -1.0],   # 5: -Z
]


# =============================================================================
# CORE EXPANSION PHYSICS
# =============================================================================

@dataclass
class Shell:
    """One shell of expanded seed structure."""
    shell_id: int
    radius: float
    energy: float
    amplitudes: List[float]    # 6 values, sum = energy


def angular_weight(u_i: List[float], u_j: List[float]) -> float:
    """
    How much direction j influences direction i.
    Compatible directions (positive dot product) have influence.
    Opposite directions have zero — you can't push something
    by pulling the other way.
    """
    return max(0.0, vec_dot(u_i, u_j))


def build_influence_matrix() -> List[List[float]]:
    """
    6x6 angular influence matrix. W[i][j] = influence of j on i.
    Row-normalized so each direction's total influence sums to 1.

    For the octahedron:
    - Self-influence = 1 (always)
    - Adjacent directions = 0 (orthogonal)
    - Opposite direction = 0 (anti-aligned)
    So each row has exactly one nonzero entry: W[i][i] = 1.
    """
    W = []
    for i in range(6):
        row = [angular_weight(OCTAHEDRAL_DIRS[i], OCTAHEDRAL_DIRS[j]) for j in range(6)]
        row_sum = sum(row)
        if row_sum > 0:
            row = [x / row_sum for x in row]
        W.append(row)
    return W


def radial_envelope(r_shell: float, r_sample: float, sigma_scale: float = 0.5) -> float:
    """
    How strongly a shell at r_shell influences a point at r_sample.
    Gaussian falloff. Sigma scales with radius so influence range
    is proportional to distance — same physics at every scale.
    """
    sigma = sigma_scale * r_shell
    if sigma < 1e-12:
        return 0.0
    return math.exp(-((r_sample - r_shell) ** 2) / (2 * sigma * sigma))


def field_contribution(amplitudes: List[float], r_shell: float,
                       r_sample: float, sigma_scale: float = 0.5) -> List[float]:
    """Field from one shell at a sample radius."""
    f_r = radial_envelope(r_shell, r_sample, sigma_scale)
    return vec_scale(amplitudes, f_r)


def total_field(shells: List[Shell], r_sample: float,
                W: List[List[float]], sigma_scale: float = 0.5) -> List[float]:
    """
    Total field at r_sample from all inner shells.
    Causality: only shells with r < r_sample contribute.
    You can't be influenced by what's outside you.
    """
    result = vec_zeros(6)
    for shell in shells:
        if shell.radius >= r_sample:
            continue
        contrib = field_contribution(shell.amplitudes, shell.radius,
                                     r_sample, sigma_scale)
        influenced = mat_vec_mul(W, contrib)
        result = vec_add(result, influenced)
    return result


def normalize_to_energy(v: List[float], E: float) -> List[float]:
    """
    Scale amplitudes so they sum to exactly E.
    Negative values clamped to 0. If all zero, distribute uniformly.
    This IS energy conservation — the sum is always what you started with.
    """
    v = [max(0.0, x) for x in v]
    total = sum(v)
    if total < 1e-12:
        return [E / 6.0] * 6
    return [x * (E / total) for x in v]


def expand_seed(seed: List[float], steps: int = 6, E0: float = 1.0,
                r0: float = 1.0, rho: float = 1.5, epsilon: float = 0.6,
                sigma_scale: float = 0.5) -> List[Shell]:
    """
    Expand a seed into a shell structure.

    seed:        6 proportional amplitudes [+X, -X, +Y, -Y, +Z, -Z]
    steps:       number of shells to grow beyond the seed
    E0:          initial energy budget
    r0:          initial radius
    rho:         radial scaling: r_{n+1} = rho * r_n
    epsilon:     energy decay: E_{n+1} = epsilon * E_n
    sigma_scale: influence width as fraction of shell radius

    Returns list of Shell dataclasses. Every shell preserves the
    seed's proportional structure. That's the whole point.
    """
    W = build_influence_matrix()

    S0 = normalize_to_energy(list(seed), E0)
    shells = [Shell(shell_id=0, radius=r0, energy=E0, amplitudes=S0)]

    for n in range(steps):
        r_new = rho * shells[-1].radius
        E_new = epsilon * shells[-1].energy

        if len(shells) == 0:
            S_new = [E_new / 6.0] * 6
        else:
            field_vec = total_field(shells, r_new, W, sigma_scale)
            S_new = normalize_to_energy(field_vec, E_new)

        shells.append(Shell(
            shell_id=n + 1,
            radius=r_new,
            energy=E_new,
            amplitudes=S_new,
        ))

    return shells


# =============================================================================
# SEED ENCODING — 40 bits, 5 bytes
# =============================================================================

def encode_seed(proportions: List[float], bits: int = 8) -> bytes:
    """
    Encode 6 proportions to 5 bytes.
    6th value is implicit: p6 = 1 - sum(p1..p5).
    Total: 40 bits. Fits anywhere.
    """
    total = sum(proportions)
    if total < 1e-12:
        proportions = [1.0 / 6.0] * 6
    else:
        proportions = [p / total for p in proportions]

    max_val = (1 << bits) - 1
    encoded = []
    for i in range(5):
        val = int(proportions[i] * max_val)
        val = max(0, min(max_val, val))
        encoded.append(val)
    return bytes(encoded)


def decode_seed(encoded: bytes, bits: int = 8) -> List[float]:
    """
    Decode 5 bytes back to 6 proportions.
    Reconstruct 6th from remainder. Re-normalize.
    """
    max_val = (1 << bits) - 1
    p = [b / max_val for b in encoded]
    remainder = 1.0 - sum(p)
    p.append(max(0.0, remainder))
    total = sum(p)
    if total < 1e-12:
        return [1.0 / 6.0] * 6
    return [x / total for x in p]


# =============================================================================
# PACKET LAYER — v2 format, 21 bytes
# =============================================================================

VERSION = 2
GRID_SCALE = 100.0  # meters per cell

# struct formats: big-endian
# B=uint8, H=uint16, 5s=5-byte string, b=int8
PACK_FMT_NOCRC = ">BBB5sBHH3bBH"
PACK_FMT_FULL  = ">BBB5sBHH3bBHH"


def position_to_anchor_offset(pos: List[float]) -> Tuple[int, List[int]]:
    """Convert 3D position to coarse anchor cell + local offset."""
    anchor_vals = [int(math.floor(p / GRID_SCALE)) for p in pos]
    anchor_id = (
        ((anchor_vals[0] & 0x1F) << 10) |
        ((anchor_vals[1] & 0x1F) << 5) |
        (anchor_vals[2] & 0x1F)
    )
    local = [pos[i] - (anchor_vals[i] * GRID_SCALE) for i in range(3)]
    offset = [max(-128, min(127, int(l / GRID_SCALE * 127))) for l in local]
    return anchor_id, offset


def anchor_offset_to_position(anchor_id: int, offset: List[int]) -> List[float]:
    """Reverse: anchor cell + offset back to 3D position."""
    x = (anchor_id >> 10) & 0x1F
    y = (anchor_id >> 5) & 0x1F
    z = anchor_id & 0x1F
    base = [x * GRID_SCALE, y * GRID_SCALE, z * GRID_SCALE]
    return [base[i] + (offset[i] / 127.0 * GRID_SCALE) for i in range(3)]


def encode_neighbor_hint(seed: List[float]) -> Tuple[int, int]:
    """Strongest direction + projection magnitude."""
    idx = max(range(len(seed)), key=lambda i: seed[i])
    proj = int(seed[idx] * 65535)
    return idx, proj


def decode_neighbor_hint(idx: int, proj: int) -> Tuple[List[float], float]:
    """Direction vector + strength from hint."""
    return OCTAHEDRAL_DIRS[idx], proj / 65535.0


def pack_packet(seed: List[float], pos: List[float],
                energy: int = 128, epoch: int = 0,
                frame: int = 1, flags: int = 0) -> bytes:
    """Pack seed + position into a 21-byte packet with CRC."""
    seed_bytes = encode_seed(seed)
    anchor, offset = position_to_anchor_offset(pos)
    dir_idx, proj = encode_neighbor_hint(seed)

    header = struct.pack(
        PACK_FMT_NOCRC,
        VERSION, frame, flags, seed_bytes, energy, epoch,
        anchor, offset[0], offset[1], offset[2], dir_idx, proj,
    )
    crc = zlib.crc32(header) & 0xFFFF

    return struct.pack(
        PACK_FMT_FULL,
        VERSION, frame, flags, seed_bytes, energy, epoch,
        anchor, offset[0], offset[1], offset[2], dir_idx, proj, crc,
    )


def unpack_packet(packet: bytes) -> dict:
    """Unpack and verify a 21-byte packet. Raises ValueError on CRC fail."""
    unpacked = struct.unpack(PACK_FMT_FULL, packet)
    (version, frame, flags, seed_bytes, energy, epoch,
     anchor, dx, dy, dz, dir_idx, proj, crc) = unpacked

    header = struct.pack(
        PACK_FMT_NOCRC,
        version, frame, flags, seed_bytes, energy, epoch,
        anchor, dx, dy, dz, dir_idx, proj,
    )
    if (zlib.crc32(header) & 0xFFFF) != crc:
        raise ValueError("CRC mismatch — packet corrupted")

    seed = decode_seed(seed_bytes)
    pos = anchor_offset_to_position(anchor, [dx, dy, dz])
    direction, strength = decode_neighbor_hint(dir_idx, proj)

    return {
        "version": version,
        "frame": frame,
        "flags": flags,
        "seed": seed,
        "energy": energy,
        "epoch": epoch,
        "position": pos,
        "neighbor_direction": direction,
        "neighbor_strength": strength,
    }


# =============================================================================
# IDENTITY + FIELD OPERATIONS
# =============================================================================

def seed_distance(a: List[float], b: List[float]) -> float:
    """L1 distance between two seeds. Lower = more similar."""
    return vec_abs_sum(vec_sub(a, b))


def same_entity(a: List[float], b: List[float], threshold: float = 0.05) -> bool:
    """Two seeds represent the same entity if distance < threshold."""
    return seed_distance(a, b) < threshold


def combine_seeds(seeds: List[List[float]],
                  weights: Optional[List[float]] = None) -> List[float]:
    """
    Superpose multiple seeds into a shared field.
    Weighted sum, re-normalized. This is how mesh nodes
    build shared situational awareness without a server.
    """
    if not seeds:
        return [1.0 / 6.0] * 6
    if weights is None:
        weights = [1.0] * len(seeds)
    result = vec_zeros(6)
    for s, w in zip(seeds, weights):
        result = vec_add(result, vec_scale(s, w))
    total = sum(result)
    if total < 1e-12:
        return [1.0 / 6.0] * 6
    return [x / total for x in result]


def euclidean_distance(a: List[float], b: List[float]) -> float:
    """Euclidean distance between two 3D positions."""
    return vec_norm(vec_sub(a, b))


# =============================================================================
# MESH NODE — the fundamental unit of a seed network
# =============================================================================

@dataclass
class MeshNode:
    """
    A node in a seed mesh network.
    Knows its seed (identity), position (location), and inbox (messages).
    Updates by blending with neighbors. No server needed.
    """
    node_id: int
    position: List[float]
    seed: List[float]
    energy: int = 128
    epoch: int = 0
    inbox: List[dict] = field(default_factory=list)

    def broadcast(self) -> bytes:
        """Create a packet from current state."""
        return pack_packet(
            self.seed, self.position,
            energy=self.energy, epoch=self.epoch,
        )

    def receive(self, packet: bytes) -> bool:
        """Try to receive a packet. Returns True if valid."""
        try:
            data = unpack_packet(packet)
            self.inbox.append(data)
            return True
        except (ValueError, struct.error):
            return False  # corrupted — drop silently

    def update(self, seed_drift: float = 0.02, pos_drift: float = 5.0):
        """
        Update state from inbox: blend seeds, drift toward neighbors.
        This is the core of mesh self-organization.
        No central coordinator. Just physics.
        """
        if not self.inbox:
            return

        neighbor_seeds = [msg["seed"] for msg in self.inbox]
        neighbor_positions = [msg["position"] for msg in self.inbox]

        # Seed update: blend toward neighbors
        combined = combine_seeds([self.seed] + neighbor_seeds)
        self.seed = [
            (1 - seed_drift) * s + seed_drift * c
            for s, c in zip(self.seed, combined)
        ]
        s_total = sum(self.seed)
        if s_total > 0:
            self.seed = [x / s_total for x in self.seed]

        # Position update: drift toward neighbor centroid
        n = len(neighbor_positions)
        avg_pos = [sum(p[i] for p in neighbor_positions) / n for i in range(3)]
        diff = vec_sub(avg_pos, self.position)
        dist = vec_norm(diff)
        if dist > 1e-6:
            direction = vec_scale(diff, 1.0 / dist)
            self.position = vec_add(self.position, vec_scale(direction, pos_drift))

        self.inbox.clear()
        self.epoch += 1


# =============================================================================
# GRADIENT ROUTING — packets move downhill in seed-space
# =============================================================================

def route_greedy(nodes: List[MeshNode], source_id: int, target_id: int,
                 comm_range: float, max_hops: int = 10) -> List[int]:
    """
    Route a packet from source to target using gradient descent
    in seed-space + physical proximity.

    No routing table. No DNS. No server.
    Just: "which neighbor is most similar to where I'm going?"
    """
    current = nodes[source_id]
    target = nodes[target_id]
    path = [current.node_id]

    for _ in range(max_hops):
        neighbors = [
            n for n in nodes
            if n.node_id != current.node_id
            and euclidean_distance(n.position, current.position) < comm_range
        ]
        if not neighbors:
            break

        # Score: 70% seed similarity + 30% spatial proximity
        def hop_score(n):
            sd = seed_distance(n.seed, target.seed)
            pd = euclidean_distance(n.position, target.position)
            return 0.7 * sd + 0.3 * (pd / comm_range)

        next_node = min(neighbors, key=hop_score)
        current = next_node
        path.append(current.node_id)

        if current.node_id == target_id:
            break

    return path


# =============================================================================
# SIMULATION — run a mesh and watch it converge
# =============================================================================

def run_mesh_simulation(num_nodes: int = 20, space_size: float = 1000.0,
                        comm_range: float = 300.0, steps: int = 30,
                        seed_drift: float = 0.02) -> Tuple[List[MeshNode], List[float]]:
    """
    Create nodes with random seeds and positions.
    Simulate broadcast/receive/update cycles.
    Return final nodes and convergence history.
    """
    import random as _rand

    nodes = []
    for i in range(num_nodes):
        pos = [_rand.random() * space_size for _ in range(3)]
        s = [_rand.random() for _ in range(6)]
        s_total = sum(s)
        seed = [x / s_total for x in s]
        nodes.append(MeshNode(node_id=i, position=pos, seed=seed,
                              energy=_rand.randint(80, 200)))

    convergence = []

    for step in range(steps):
        # Broadcast phase
        packets = [(node, node.broadcast()) for node in nodes]

        # Receive phase (range-limited)
        for sender, pkt in packets:
            for receiver in nodes:
                if sender.node_id == receiver.node_id:
                    continue
                if euclidean_distance(sender.position, receiver.position) < comm_range:
                    receiver.receive(pkt)

        # Update phase
        for node in nodes:
            node.update(seed_drift=seed_drift)

        # Convergence metric: average seed variance across dimensions
        if nodes:
            dim_vars = []
            for d in range(6):
                vals = [n.seed[d] for n in nodes]
                mean = sum(vals) / len(vals)
                var = sum((v - mean) ** 2 for v in vals) / len(vals)
                dim_vars.append(var)
            convergence.append(sum(dim_vars) / len(dim_vars))

    return nodes, convergence
