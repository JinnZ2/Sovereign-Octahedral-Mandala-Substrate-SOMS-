"""Tests for SOMSEngine, MandalaMap, and PhiCalculator."""

import numpy as np
import pytest
from scipy.spatial import distance_matrix

from src.octahedral_physics import SOMSEngine
from src.mandala_structure import MandalaMap
from src.phi_calculator import PhiCalculator


class TestSOMSEngine:
    def test_initial_orientations(self):
        engine = SOMSEngine(num_cells=50)
        assert len(engine.orientations) == 50
        valid = {0, 45, 90, 135, 180, 225, 270, 315}
        assert set(engine.orientations).issubset(valid)

    def test_fret_coupling_shape(self):
        engine = SOMSEngine(num_cells=10)
        d = np.random.rand(10, 10) + 0.1
        np.fill_diagonal(d, 0)
        j = engine.fret_coupling(d)
        assert j.shape == (10, 10)
        assert np.all(np.diag(j) == 0)

    def test_fret_coupling_positive(self):
        engine = SOMSEngine(num_cells=5)
        d = np.random.rand(5, 5) + 0.5
        np.fill_diagonal(d, 0)
        j = engine.fret_coupling(d)
        # Off-diagonal should all be positive
        mask = ~np.eye(5, dtype=bool)
        assert np.all(j[mask] > 0)

    def test_energy_nonnegative(self):
        engine = SOMSEngine(num_cells=10)
        d = np.random.rand(10, 10) + 0.5
        np.fill_diagonal(d, 0)
        d = (d + d.T) / 2
        j = engine.fret_coupling(d)
        E = engine.energy_landscape(j)
        assert E >= 0

    def test_relax_step_returns_tuple(self):
        engine = SOMSEngine(num_cells=10)
        d = np.random.rand(10, 10) + 0.5
        np.fill_diagonal(d, 0)
        d = (d + d.T) / 2
        j = engine.fret_coupling(d)
        energy, accepted = engine.relax_step(j, temperature=1.0)
        assert isinstance(energy, float)
        assert isinstance(accepted, int)
        assert accepted >= 0

    def test_anneal_reduces_energy(self):
        np.random.seed(42)
        engine = SOMSEngine(num_cells=20)
        m = MandalaMap(u=1, depth=2)
        d = distance_matrix(m.pos, m.pos)
        engine = SOMSEngine(num_cells=len(m.pos))
        j = engine.fret_coupling(d)
        E_initial = engine.energy_landscape(j)
        history = engine.anneal(j, T_start=10.0, T_final=0.01, n_steps=100)
        E_final = history[-1][2]
        assert E_final <= E_initial

    def test_anneal_history_format(self):
        engine = SOMSEngine(num_cells=10)
        d = np.random.rand(10, 10) + 0.5
        np.fill_diagonal(d, 0)
        d = (d + d.T) / 2
        j = engine.fret_coupling(d)
        history = engine.anneal(j, n_steps=10)
        assert len(history) == 10
        step, T, E, acc = history[0]
        assert step == 0


class TestMandalaMap:
    def test_root_at_origin(self):
        m = MandalaMap(u=1, depth=1)
        assert m.pos[0][0] == 0
        assert m.pos[0][1] == 0

    def test_cell_count(self):
        m = MandalaMap(u=1, depth=3)
        # 1 root + 8 petals * 3 depths = 25
        assert len(m.pos) == 25

    def test_ring_radii_phi_scaled(self):
        m = MandalaMap(u=10, depth=3)
        phi = m.phi
        for d in range(1, 4):
            expected_r = 10 * phi ** d
            # Check first petal of ring d (angle=0, so y=0, x=r)
            idx = 1 + (d - 1) * 8  # first petal of ring d
            actual_r = np.sqrt(m.pos[idx][0] ** 2 + m.pos[idx][1] ** 2)
            assert abs(actual_r - expected_r) < 1e-6

    def test_eight_petals_per_ring(self):
        m = MandalaMap(u=1, depth=2)
        # Ring 1: indices 1-8, Ring 2: indices 9-16
        ring1 = m.pos[1:9]
        assert len(ring1) == 8


class TestPhiCalculator:
    def test_sovereign_with_high_entropy(self):
        # Spread across all 8 states => high entropy => high phi
        state = np.array([0, 45, 90, 135, 180, 225, 270, 315] * 10)
        phi_val, is_sovereign = PhiCalculator(state).evaluate_integration()
        assert isinstance(phi_val, float)

    def test_threshold(self):
        calc = PhiCalculator(np.array([0, 45, 90]))
        assert calc.phi_threshold == 3.0

    def test_returns_tuple(self):
        calc = PhiCalculator(np.random.choice([0, 45, 90, 135], size=50))
        result = calc.evaluate_integration()
        assert len(result) == 2
        phi_val, is_sov = result
        assert isinstance(phi_val, float)
        assert is_sov in (True, False)  # numpy bool_ is truthy but not isinstance bool
