"""Tests for immune_system.py — adaptive geometric security."""

import pytest

from src.geometric_security import (
    PHI, generate_temporal_handshake, BRIDGE_SIGNATURES,
)
from src.immune_system import OctahedralImmuneSystem, ImmuneMemory


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def immune():
    return OctahedralImmuneSystem()


@pytest.fixture
def valid_args():
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


# ============================================================================
# ImmuneMemory
# ============================================================================

class TestImmuneMemory:
    def test_add_valid(self):
        mem = ImmuneMemory()
        mem.add_valid(12345, 0.62)
        assert len(mem.valid_signatures) == 1

    def test_add_attack(self):
        mem = ImmuneMemory()
        mem.add_attack(["parity"], 99999, 0.5)
        assert len(mem.attack_patterns) == 1

    def test_is_known_valid(self):
        mem = ImmuneMemory()
        mem.add_valid(12345, 0.62)
        assert mem.is_known_valid(12345, 0.63)
        assert not mem.is_known_valid(99999, 0.62)

    def test_memory_cap(self):
        mem = ImmuneMemory(max_valid=5)
        for i in range(10):
            mem.add_valid(i, 0.62)
        assert len(mem.valid_signatures) == 5

    def test_health_ratio(self):
        mem = ImmuneMemory()
        mem.add_valid(1, 0.62)
        mem.add_valid(2, 0.62)
        mem.add_attack(["parity"], 3, 0.5)
        assert mem.health_ratio == pytest.approx(2.0)


# ============================================================================
# OctahedralImmuneSystem
# ============================================================================

class TestImmuneSystem:
    def test_accept_valid(self, immune, valid_args):
        response = immune.immune_response(**valid_args)
        assert response["passed"]
        assert response["action"] == "accept"
        assert response["confidence"] == 1.0

    def test_quarantine_on_failure(self, immune, valid_args):
        valid_args["clusters"] = [[1, 0, 0, 0]]  # bad parity
        valid_args["radii"] = [0.8, 2.0, 3.0, 5.0]  # bad phi
        valid_args["noise_level"] = 0.1  # bad noise
        response = immune.immune_response(**valid_args)
        assert not response["passed"]
        assert response["action"] == "quarantine"

    def test_investigate_partial_failure(self, immune, valid_args):
        # Only one layer fails -> investigate, not quarantine
        valid_args["noise_level"] = 0.1  # bad noise, rest valid
        response = immune.immune_response(**valid_args)
        assert not response["passed"]
        assert response["action"] == "investigate"
        assert response["confidence"] >= 0.67

    def test_memory_learns_valid(self, immune, valid_args):
        immune.immune_response(**valid_args)
        assert immune.memory.valid_signatures
        assert immune.memory.health_ratio >= 1.0

    def test_memory_remembers_attack(self, immune, valid_args):
        valid_args["clusters"] = [[1, 0, 0, 0]]
        valid_args["radii"] = [0.8, 2.0, 3.0, 5.0]
        valid_args["noise_level"] = 0.1
        immune.immune_response(**valid_args)
        assert len(immune.memory.attack_patterns) == 1

    def test_tolerances_tighten(self, immune, valid_args):
        orig_phi = immune.phi_tolerance
        # Simulate 15 attacks to trigger tightening
        valid_args["clusters"] = [[1, 0, 0, 0]]
        valid_args["radii"] = [0.8, 2.0, 3.0, 5.0]
        valid_args["noise_level"] = 0.1
        for _ in range(15):
            immune.immune_response(**valid_args)
        assert immune.phi_tolerance < orig_phi

    def test_tolerances_have_floor(self, immune, valid_args):
        valid_args["clusters"] = [[1, 0, 0, 0]]
        valid_args["radii"] = [0.8, 2.0, 3.0, 5.0]
        valid_args["noise_level"] = 0.1
        for _ in range(500):
            immune.immune_response(**valid_args)
        assert immune.phi_tolerance >= 0.01
        assert immune.noise_tolerance >= 0.03

    def test_investigate_known_valid(self, immune, valid_args):
        # First: learn valid state
        immune.immune_response(**valid_args)
        # Now break one layer but keep same eigenvalues
        valid_args["noise_level"] = 0.1
        response = immune.immune_response(**valid_args)
        assert response["action"] == "investigate"

    def test_report(self, immune, valid_args):
        response = immune.immune_response(**valid_args)
        report = immune.report(response)
        assert "ACCEPT" in report
        assert "PASS" in report
        assert "Confidence" in report
