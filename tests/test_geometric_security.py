"""Tests for geometric_security.py — 6-layer self-encoded security."""

import math
import pytest

from src.geometric_security import (
    GeometricSecurity,
    tetrahedral_parity,
    verify_cluster_parity,
    verify_all_clusters,
    expected_phi_radius,
    verify_phi_spacing,
    verify_trace_invariant,
    verify_all_traces,
    verify_noise_lock,
    verify_bridge_target,
    verify_all_bridges,
    generate_temporal_handshake,
    verify_temporal_handshake,
    PHI, BRIDGE_SIGNATURES,
)


# ============================================================================
# Layer 1: Tetrahedral Parity
# ============================================================================

class TestTetrahedralParity:
    def test_even_parity(self):
        assert tetrahedral_parity([0, 1, 0, 1]) == 0
        assert tetrahedral_parity([1, 1, 0, 0]) == 0

    def test_odd_parity(self):
        assert tetrahedral_parity([1, 0, 0, 0]) == 1
        assert tetrahedral_parity([1, 1, 1, 0]) == 1

    def test_verify_even(self):
        assert verify_cluster_parity([0, 1, 0, 1], expected=0)
        assert not verify_cluster_parity([1, 0, 0, 0], expected=0)

    def test_verify_all_pass(self):
        clusters = [[0, 1, 0, 1], [1, 0, 1, 0], [0, 0, 0, 0]]
        result = verify_all_clusters(clusters, expected=0)
        assert result["passed"]
        assert result["violations"] == []

    def test_verify_all_fail(self):
        clusters = [[0, 1, 0, 1], [1, 0, 0, 0]]  # second is odd
        result = verify_all_clusters(clusters, expected=0)
        assert not result["passed"]
        assert 1 in result["violations"]


# ============================================================================
# Layer 2: Phi-Spacing
# ============================================================================

class TestPhiSpacing:
    def test_expected_radius(self):
        assert expected_phi_radius(0) == pytest.approx(0.8)
        assert expected_phi_radius(1) == pytest.approx(0.8 * PHI, rel=1e-6)
        assert expected_phi_radius(2) == pytest.approx(0.8 * PHI**2, rel=1e-6)

    def test_valid_radii(self):
        radii = [0.8 * PHI**n for n in range(5)]
        result = verify_phi_spacing(radii, r0=0.8)
        assert result["passed"]

    def test_tampered_radii(self):
        radii = [0.8, 1.5, 2.1, 3.4]  # not phi-spaced
        result = verify_phi_spacing(radii, r0=0.8)
        assert not result["passed"]
        assert len(result["violations"]) > 0

    def test_within_tolerance(self):
        # Slightly off but within 5%
        radii = [0.8 * PHI**n * 1.03 for n in range(3)]
        result = verify_phi_spacing(radii, r0=0.8, tolerance=0.05)
        assert result["passed"]


# ============================================================================
# Layer 3: Trace Invariant
# ============================================================================

class TestTraceInvariant:
    def test_valid_trace(self):
        result = verify_trace_invariant((0.5, 0.3, 0.2))
        assert result["passed"]
        assert result["trace"] == pytest.approx(1.0)

    def test_invalid_trace(self):
        result = verify_trace_invariant((0.5, 0.5, 0.5))
        assert not result["passed"]
        assert result["trace"] == pytest.approx(1.5)

    def test_all_states_valid(self):
        from src.octahedral_lookup import OCTAHEDRAL_EIGENVALUES
        # State 0 uses (0.33, 0.33, 0.33) -> trace=0.99 due to rounding.
        # Use 0.02 tolerance to accommodate the lookup table's precision.
        result = verify_all_traces(list(range(8)), tolerance=0.02)
        assert result["passed"]


# ============================================================================
# Layer 4: Stochastic Resonance Lock
# ============================================================================

class TestNoiseLock:
    def test_optimal_noise(self):
        result = verify_noise_lock(0.62)
        assert result["passed"]

    def test_noise_too_high(self):
        result = verify_noise_lock(1.0)
        assert not result["passed"]

    def test_noise_too_low(self):
        result = verify_noise_lock(0.1)
        assert not result["passed"]

    def test_within_tolerance(self):
        # 0.62 +/- 15% = [0.527, 0.713]
        result = verify_noise_lock(0.55)
        assert result["passed"]


# ============================================================================
# Layer 5: Bridge Authentication
# ============================================================================

class TestBridgeAuth:
    def test_valid_bridge(self):
        result = verify_bridge_target("thermal", 100.0, 0.01)
        assert result["passed"]

    def test_wrong_impedance(self):
        result = verify_bridge_target("thermal", 200.0, 0.01)
        assert not result["passed"]

    def test_unknown_target(self):
        result = verify_bridge_target("unknown", 100.0, 0.01)
        assert not result["passed"]

    def test_all_bridges_valid(self):
        bridges = [(t, r, l) for t, (r, l) in BRIDGE_SIGNATURES.items()]
        result = verify_all_bridges(bridges)
        assert result["passed"]


# ============================================================================
# Layer 6: Temporal Handshake
# ============================================================================

class TestTemporalHandshake:
    def test_deterministic(self):
        t1 = generate_temporal_handshake(42, length=5)
        t2 = generate_temporal_handshake(42, length=5)
        assert t1 == t2

    def test_seed_differs(self):
        t1 = generate_temporal_handshake(42, length=5)
        t2 = generate_temporal_handshake(99, length=5)
        assert t1 != t2

    def test_valid_handshake(self):
        times = generate_temporal_handshake(42, length=5)
        result = verify_temporal_handshake(times, expected_seed=42)
        assert result["passed"]

    def test_replay_fails(self):
        times = generate_temporal_handshake(42, length=5)
        result = verify_temporal_handshake(times, expected_seed=99)
        assert not result["passed"]

    def test_monotonically_increasing(self):
        times = generate_temporal_handshake(42, length=10)
        for i in range(1, len(times)):
            assert times[i] > times[i - 1]


# ============================================================================
# Full System Check
# ============================================================================

class TestGeometricSecurityFull:
    @pytest.fixture
    def security(self):
        return GeometricSecurity()

    @pytest.fixture
    def valid_inputs(self, security):
        seed = 42
        return {
            "clusters": [[0, 1, 0, 1], [1, 0, 1, 0]],
            "radii": [0.8 * PHI**n for n in range(4)],
            "eigenvalues": [(0.5, 0.3, 0.2), (0.33, 0.33, 0.34)],
            "noise_level": 0.62,
            "bridges": [("thermal", 100.0, 0.01), ("electric", 50.0, 0.001)],
            "handshake_seed": seed,
            "handshake_times": generate_temporal_handshake(seed, length=5),
        }

    def test_all_pass(self, security, valid_inputs):
        result = security.full_check(**valid_inputs)
        assert result["all_pass"]

    def test_tampered_parity_fails(self, security, valid_inputs):
        valid_inputs["clusters"] = [[1, 0, 0, 0]]  # odd parity
        result = security.full_check(**valid_inputs)
        assert not result["all_pass"]
        assert not result["tetrahedral_parity"]["passed"]

    def test_tampered_spacing_fails(self, security, valid_inputs):
        valid_inputs["radii"] = [0.8, 2.0, 3.0, 5.0]  # not phi-spaced
        result = security.full_check(**valid_inputs)
        assert not result["all_pass"]
        assert not result["phi_spacing"]["passed"]

    def test_report(self, security, valid_inputs):
        result = security.full_check(**valid_inputs)
        report = security.report(result)
        assert "SECURE" in report
        assert "PASS" in report
