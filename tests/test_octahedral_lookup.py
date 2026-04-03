"""Tests for octahedral_lookup — Gray codes, eigenvalues, phi-stability."""

import pytest
from src.octahedral_lookup import (
    GRAY_CODES, GRAY_CODE_TO_STATE, OCTAHEDRAL_EIGENVALUES,
    ALLOWED_TRANSITIONS, POSITIONS, GRAY_TRANSITION_TABLE,
    gray_adjacent, nearest_octahedral_state,
    nearest_octahedral_state_with_distance,
    phi_deviation, phi_stability_report, phi_stability_score,
    state_capacity, PHI,
)


class TestGrayCodes:
    def test_eight_states(self):
        assert len(GRAY_CODES) == 8

    def test_all_3bit(self):
        for code in GRAY_CODES.values():
            assert len(code) == 3
            assert all(c in '01' for c in code)

    def test_unique_codes(self):
        codes = list(GRAY_CODES.values())
        assert len(set(codes)) == 8

    def test_reverse_map(self):
        for state, code in GRAY_CODES.items():
            assert GRAY_CODE_TO_STATE[code] == state

    def test_adjacent_states_differ_by_one_bit(self):
        """Adjacent states in Gray code should differ by exactly 1 bit."""
        for i in range(7):
            code_a = GRAY_CODES[i]
            code_b = GRAY_CODES[i + 1]
            hamming = sum(a != b for a, b in zip(code_a, code_b))
            assert hamming == 1, f"States {i},{i+1}: {code_a},{code_b} differ by {hamming}"


class TestEigenvalues:
    def test_eight_states(self):
        assert len(OCTAHEDRAL_EIGENVALUES) == 8

    def test_trace_conservation(self):
        """All eigenvalue triples should sum to ~1.0."""
        for state, ev in OCTAHEDRAL_EIGENVALUES.items():
            assert abs(sum(ev) - 1.0) < 0.02, f"State {state}: sum={sum(ev)}"

    def test_all_positive(self):
        for state, ev in OCTAHEDRAL_EIGENVALUES.items():
            for val in ev:
                assert val > 0, f"State {state}: negative eigenvalue {val}"

    def test_spherical_state(self):
        """State 0 should be spherical (all equal)."""
        ev = OCTAHEDRAL_EIGENVALUES[0]
        assert ev[0] == ev[1] == ev[2]


class TestTransitions:
    def test_edge_count(self):
        """Verify total directed edges (includes diagonal states 6,7)."""
        total = sum(len(v) for v in ALLOWED_TRANSITIONS.values())
        # 6 core vertices x 4 neighbors + 2 diagonal vertices x 4 neighbors = 32
        assert total == 32

    def test_core_symmetric(self):
        """Core 6 states (0-5) should have symmetric transitions."""
        for state in range(6):
            for n in ALLOWED_TRANSITIONS[state]:
                if n < 6:
                    assert state in ALLOWED_TRANSITIONS[n], \
                        f"Asymmetric: {state}->{n} but not reverse"

    def test_no_self_transitions(self):
        for state, neighbors in ALLOWED_TRANSITIONS.items():
            assert state not in neighbors


class TestGrayAdjacent:
    def test_same_state(self):
        assert not gray_adjacent(0, 0)

    def test_known_adjacent(self):
        assert gray_adjacent(0, 1)  # 000 vs 001

    def test_transition_table_shape(self):
        assert len(GRAY_TRANSITION_TABLE) == 8
        assert all(len(row) == 8 for row in GRAY_TRANSITION_TABLE)


class TestNearestState:
    def test_exact_match(self):
        for state, ev in OCTAHEDRAL_EIGENVALUES.items():
            assert nearest_octahedral_state(ev) == state

    def test_with_distance_zero_for_exact(self):
        for state, ev in OCTAHEDRAL_EIGENVALUES.items():
            ns, dist = nearest_octahedral_state_with_distance(ev)
            assert ns == state
            assert dist == 0.0

    def test_near_state_0(self):
        # Slightly perturbed spherical eigenvalues should still map to state 0
        assert nearest_octahedral_state((0.34, 0.33, 0.33)) == 0


class TestPhiStability:
    def test_report_length(self):
        report = phi_stability_report()
        assert len(report) == 8

    def test_sorted_by_deviation(self):
        report = phi_stability_report()
        devs = [r["closest_phi_deviation"] for r in report]
        assert devs == sorted(devs)

    def test_deviation_keys(self):
        info = phi_deviation(0)
        assert "closest_deviation" in info
        assert "best_ratio" in info
        assert "ratios" in info

    def test_score_range(self):
        for state in range(8):
            ev = OCTAHEDRAL_EIGENVALUES[state]
            score = phi_stability_score(ev)
            assert 0.0 <= score <= 1.0, f"State {state}: score={score}"


class TestStateCapacity:
    def test_single_cell(self):
        sc = state_capacity(1)
        assert sc["total_states"] == 8
        assert sc["bits_per_cell"] == 3
        assert sc["total_bits"] == 3

    def test_ten_cells(self):
        sc = state_capacity(10)
        assert sc["total_states"] == 8 ** 10
        assert sc["total_bits"] == 30

    def test_hundred_cells(self):
        sc = state_capacity(100)
        assert sc["total_bits"] == 300


class TestPositions:
    def test_eight_positions(self):
        assert len(POSITIONS) == 8

    def test_unit_vectors(self):
        """Core 6 positions should be unit vectors on axes."""
        for state in range(6):
            pos = POSITIONS[state]
            norm_sq = sum(x ** 2 for x in pos)
            assert norm_sq == 1, f"State {state}: norm^2={norm_sq}"
