# SOMS — Sovereign Octahedral Mandala Substrate
"""
Core modules for octahedral-mandala physics simulation.

Modules:
    octahedral_physics       — FRET coupling and energy landscape (SOMSEngine)
    mandala_structure        — Fibonacci-scaled 8-petal mandala geometry (MandalaMap)
    phi_calculator           — Integrated Information (Φ) metric (PhiCalculator)
    constraint_agent         — Seed-based geometric agent lifecycle (ConstraintAgent)
    octahedral_lookup        — Gray codes, eigenvalue tables, φ-stability (from G2B bridge)
    geometric_encoder        — Bidirectional geometric token ↔ binary encoding (from G2B bridge)
    geometric_state_algebra  — O_h symmetry group, group ring Z[O_h], Cayley coupling
    holographic_engine       — Holographic boundary encoding + renormalization solver
    geometric_bridge         — Geometric Binary Bridge: sensor decode + actuator control (8 targets)
    geometric_security       — 6-layer self-encoded security (parity, phi, trace, noise, bridge auth, handshake)
    immune_system            — Adaptive geometric security with immune memory and tolerance evolution
    octahedral_session_cache — Constraint-coherent LRU cache with octahedral invalidation graph
    octahedral_resilience    — Health monitoring, heartbeat, failover, auto-recovery
    seed_dispersal           — Shamir-like secret sharing, hardware dispersal, gossip comms
    service_reconfig         — Service discovery, quorum consensus, staging, priority scheduling, healing tools
    resilience_core          — HLC, Byzantine verification, circuit breaker, audit trail, key rotation, fencing, Merkle
"""

from src.octahedral_physics import SOMSEngine
from src.mandala_structure import MandalaMap
from src.phi_calculator import PhiCalculator
from src.resource_budget import ResourceBudget
from src.geometric_map import GeometricMap
from src.constraint_agent import ConstraintAgent, AgentState
from src.octahedral_lookup import (
    GRAY_CODES, GRAY_CODE_TO_STATE, OCTAHEDRAL_EIGENVALUES,
    EIGENVALUE_CHARACTERS, ALLOWED_TRANSITIONS, POSITIONS,
    MANDALA_OCTAHEDRAL_MAP, GRAY_TRANSITION_TABLE,
    gray_adjacent, nearest_octahedral_state, phi_stability_report,
    phi_stability_score, phi_deviation, state_capacity,
)
from src.geometric_encoder import GeometricEncoder
from src.lattice_handshake import OctahedralLattice, PulseChip, feltscore, local_anxiety
from src.geometric_state_algebra import (
    OhElement, OhGroup, GroupRingElement, GeometricState, CayleyEnergy,
)
from src.holographic_engine import HolographicEngine, HolographicRing, EntanglementLink
from src.geometric_security import (
    GeometricSecurity,
    tetrahedral_parity, verify_cluster_parity, verify_all_clusters,
    verify_phi_spacing, verify_trace_invariant,
    verify_noise_lock, verify_bridge_target,
    generate_temporal_handshake, verify_temporal_handshake,
    BRIDGE_SIGNATURES,
)
from src.immune_system import OctahedralImmuneSystem, ImmuneMemory
from src.octahedral_session_cache import (
    OctState, CacheEntry, InvalidationGraph, SessionCache,
)
from src.octahedral_resilience import (
    Health, OctahedralNode, HeartbeatMonitor, OctahedralCluster,
    Monitor, AutoRecovery, OctahedralResilienceSystem,
)
from src.seed_dispersal import (
    CompressedSeed, SeedSplitter, HardwareComponent,
    SeedDispersal, MinimalComms, OctahedralWithSeedSystem,
)
from src.service_reconfig import (
    ServiceState, ServiceReconfigurator, QuorumReconfigurator,
    Stage, Priority, ReconfigRequest,
    StagingProtocol, PriorityScheduler, PriorityRules,
    StagedPriorityReconfigurator,
    ResourceType, ResourceSnapshot,
    HealingTool, ExternalToolOrchestrator,
    PrecomputeShareTool, RedistributeSharesTool, VerifySharesTool, PreloadStandbyTool,
)
from src.resilience_core import (
    HybridLogicalClock, ByzantineVerifier, VerifiedShare, ByzantineError,
    CircuitBreaker, AuditEntry, AuditTrail,
    EpochSeed, KeyRotationManager,
    EmergencyOverride, EmergencyRecovery,
    ResourceReservation, TimingJitter,
    FencedComponent, FencingManager,
    MerkleNode, ShareMerkleTree,
)
from src.geometric_bridge import (
    GeometricBridge, SensorDecoder, ActuatorController,
    decode_hardware, decode_electric, BridgeHeader,
    Modality, BridgeTarget, DrillDepth, HardwareData, ElectricData,
    gray_to_binary, binary_to_gray, gray_to_value, value_to_gray,
    component_health_score, drift_percent, lifetime_estimate_hours,
    noise_power, confidence_from_noise,
    ohms_law, power_dissipation, coulomb_force,
    electric_field_magnitude, skin_depth,
)

__all__ = [
    "SOMSEngine", "MandalaMap", "PhiCalculator",
    "ConstraintAgent", "AgentState", "ResourceBudget", "GeometricMap",
    "GeometricEncoder",
    "OctahedralLattice", "PulseChip", "feltscore", "local_anxiety",
    "GRAY_CODES", "GRAY_CODE_TO_STATE", "OCTAHEDRAL_EIGENVALUES",
    "EIGENVALUE_CHARACTERS", "ALLOWED_TRANSITIONS", "POSITIONS",
    "MANDALA_OCTAHEDRAL_MAP", "GRAY_TRANSITION_TABLE",
    "gray_adjacent", "nearest_octahedral_state", "phi_stability_report",
    "phi_stability_score", "phi_deviation", "state_capacity",
    # Geometric State Algebra (O_h group)
    "OhElement", "OhGroup", "GroupRingElement", "GeometricState", "CayleyEnergy",
    # Holographic Engine
    "HolographicEngine", "HolographicRing", "EntanglementLink",
    # Geometric Binary Bridge
    "GeometricBridge", "SensorDecoder", "ActuatorController",
    "decode_hardware", "decode_electric", "BridgeHeader",
    "Modality", "BridgeTarget", "DrillDepth", "HardwareData", "ElectricData",
    "gray_to_binary", "binary_to_gray", "gray_to_value", "value_to_gray",
    "component_health_score", "drift_percent", "lifetime_estimate_hours",
    "noise_power", "confidence_from_noise",
    "ohms_law", "power_dissipation", "coulomb_force",
    "electric_field_magnitude", "skin_depth",
    # Geometric Security (6-layer integrity)
    "GeometricSecurity",
    "tetrahedral_parity", "verify_cluster_parity", "verify_all_clusters",
    "verify_phi_spacing", "verify_trace_invariant",
    "verify_noise_lock", "verify_bridge_target",
    "generate_temporal_handshake", "verify_temporal_handshake",
    "BRIDGE_SIGNATURES",
    # Immune System (adaptive security)
    "OctahedralImmuneSystem", "ImmuneMemory",
    # Session Cache (constraint-coherent caching)
    "OctState", "CacheEntry", "InvalidationGraph", "SessionCache",
    # Octahedral Resilience (health + failover + recovery)
    "Health", "OctahedralNode", "HeartbeatMonitor", "OctahedralCluster",
    "Monitor", "AutoRecovery", "OctahedralResilienceSystem",
    # Seed Dispersal (secret sharing + hardware dispersal)
    "CompressedSeed", "SeedSplitter", "HardwareComponent",
    "SeedDispersal", "MinimalComms", "OctahedralWithSeedSystem",
    # Service Reconfiguration (staging + priority + healing)
    "ServiceState", "ServiceReconfigurator", "QuorumReconfigurator",
    "Stage", "Priority", "ReconfigRequest",
    "StagingProtocol", "PriorityScheduler", "PriorityRules",
    "StagedPriorityReconfigurator",
    "ResourceType", "ResourceSnapshot",
    "HealingTool", "ExternalToolOrchestrator",
    "PrecomputeShareTool", "RedistributeSharesTool", "VerifySharesTool", "PreloadStandbyTool",
    # Resilience Core (advanced primitives)
    "HybridLogicalClock", "ByzantineVerifier", "VerifiedShare", "ByzantineError",
    "CircuitBreaker", "AuditEntry", "AuditTrail",
    "EpochSeed", "KeyRotationManager",
    "EmergencyOverride", "EmergencyRecovery",
    "ResourceReservation", "TimingJitter",
    "FencedComponent", "FencingManager",
    "MerkleNode", "ShareMerkleTree",
]
