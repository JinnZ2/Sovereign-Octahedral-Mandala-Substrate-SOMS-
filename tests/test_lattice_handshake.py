"""Tests for lattice_handshake module."""

import numpy as np
import pytest
from src.lattice_handshake import (
    OctahedralLattice, PulseChip, feltscore, local_anxiety,
)


class TestOctahedralLattice:
    """CVP-based handshake using octahedral eigenvalue geometry."""

    def test_dimension_matches_cells(self):
        lat = OctahedralLattice(num_cells=8)
        assert lat.dim == 24  # 8 cells × 3 eigenvalues

    def test_encode_returns_correct_shape(self):
        lat = OctahedralLattice(num_cells=8)
        secret = np.random.randn(24)
        encoded = lat.encode(secret)
        assert encoded.shape == (24,)

    def test_decode_recovers_signal(self):
        lat = OctahedralLattice(num_cells=8, noise_scale=0.001)
        secret = np.random.randn(24)
        recovered = lat.decode(lat.encode(secret))
        assert np.linalg.norm(recovered - secret) < 1.0

    def test_handshake_error_is_small(self):
        lat = OctahedralLattice(num_cells=8, noise_scale=0.001)
        secret = np.random.randn(24)
        err = lat.handshake_error(secret)
        assert err < 1.0

    def test_larger_lattice(self):
        lat = OctahedralLattice(num_cells=32)
        assert lat.dim == 96
        secret = np.random.randn(96)
        encoded = lat.encode(secret)
        assert encoded.shape == (96,)

    def test_noise_affects_error(self):
        """Higher noise → higher decode error."""
        np.random.seed(42)
        secret = np.random.randn(24)
        lat_low = OctahedralLattice(num_cells=8, noise_scale=0.0001)
        lat_high = OctahedralLattice(num_cells=8, noise_scale=0.1)
        # Run multiple trials to handle stochastic variation
        low_errors = [lat_low.handshake_error(secret) for _ in range(5)]
        high_errors = [lat_high.handshake_error(secret) for _ in range(5)]
        assert np.median(low_errors) < np.median(high_errors)


class TestPulseChip:
    """Single-pulse hardware coupling model."""

    def test_default_construction(self):
        chip = PulseChip(dim=24)
        assert chip.coupling_matrix.shape == (24, 24)

    def test_pulse_shape(self):
        chip = PulseChip(dim=24)
        v = np.random.randn(24)
        result = chip.pulse(v)
        assert result.shape == (24,)

    def test_from_fret(self):
        j = np.random.randn(10, 10)
        chip = PulseChip.from_fret(j)
        assert chip.dim == 10
        np.testing.assert_array_equal(chip.coupling_matrix, j)

    def test_pulse_is_linear(self):
        chip = PulseChip(dim=12)
        v1 = np.random.randn(12)
        v2 = np.random.randn(12)
        np.testing.assert_allclose(
            chip.pulse(v1 + v2),
            chip.pulse(v1) + chip.pulse(v2),
            atol=1e-10,
        )


class TestFeltscore:
    """Signal coherence metric."""

    def test_constant_signal_is_optimal(self):
        signal = np.ones(100) * 5.0
        assert feltscore(signal) == pytest.approx(1.0, abs=0.01)

    def test_noisy_signal_is_lower(self):
        clean = np.ones(100) * 5.0
        noisy = np.random.randn(100)
        assert feltscore(clean) > feltscore(noisy)

    def test_range_zero_to_one(self):
        for _ in range(20):
            signal = np.random.randn(50) * np.random.uniform(0.1, 10)
            score = feltscore(signal)
            assert 0.0 <= score <= 1.0


class TestLocalAnxiety:
    """High-dimensional divergence metric."""

    def test_identical_points(self):
        p = np.random.randn(24)
        assert local_anxiety(p, p) == pytest.approx(1.0, abs=1e-10)

    def test_divergent_points(self):
        p = np.zeros(24)
        q = np.ones(24) * 10.0
        assert local_anxiety(p, q) > 1.0

    def test_scales_with_dimension(self):
        """Anxiety normalized by dimension, so same-magnitude offset gives similar result."""
        offset = 1.0
        a10 = local_anxiety(np.zeros(10), np.ones(10) * offset)
        a100 = local_anxiety(np.zeros(100), np.ones(100) * offset)
        # Both should be close to exp(1) ≈ 2.718 since ||d||²/dim = offset²
        assert abs(a10 - a100) < 0.5
