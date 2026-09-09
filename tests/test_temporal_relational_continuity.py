"""Tests for SOMS Experiment 04 temporal relational continuity."""

import numpy as np
import pytest

from src.isometry_controls import SUPPORTED_GEOMETRIES
from src.temporal_relational_continuity import (
    analyze_component_permutation_trajectory,
    analyze_trajectory,
    compare_endpoint_equivalent_paths,
    compare_forward_reverse,
)


INITIAL = np.arange(8)
ENDPOINT = (INITIAL + 1) % 8
NONUNIFORM = np.array([2, 5, 1, 7, 0, 6, 4, 3])
CYCLIC_COMPONENT_PERMUTATION = tuple([1, 2, 3, 4, 5, 6, 7, 0])
REVERSAL = tuple(reversed(range(8)))
PAIR_SWAPS = (1, 0, 3, 2, 5, 4, 7, 6)


def progressive_trajectory():
    states = []
    for changed_components in range(9):
        current = INITIAL.copy()
        current[:changed_components] = (
            current[:changed_components] + 1
        ) % 8
        states.append(current)
    return states


class TestTemporalProfiles:

    def test_static_trajectory_has_zero_local_and_cumulative_change(self):
        trajectory = analyze_trajectory(
            "T0",
            [INITIAL.copy() for _ in range(9)],
        )

        assert trajectory.transition_count == 8
        for profile in trajectory.geometries.values():
            assert profile.local_displacements == (0.0,) * 8
            assert profile.cumulative_displacements == (0.0,) * 9
            assert profile.path_length == 0.0
            assert profile.zero_displacement_transitions == 8
            assert profile.nonzero_displacement_transitions == 0

    def test_cyclic_progression_retains_complete_temporal_profile(self):
        states = [
            (INITIAL + offset) % 8
            for offset in range(9)
        ]
        trajectory = analyze_trajectory("T1", states)

        assert len(trajectory.states) == 9
        assert trajectory.states[0] == trajectory.states[-1]
        for geometry_id in SUPPORTED_GEOMETRIES:
            profile = trajectory.geometries[geometry_id]
            assert len(profile.relation_matrices) == 9
            assert len(profile.local_displacements) == 8
            assert len(profile.cumulative_displacements) == 9
            assert profile.endpoint_displacement == 0.0
        assert trajectory.geometries["G2"].path_length == 0.0
        assert trajectory.geometries["G3"].path_length == 0.0
        assert trajectory.geometries["G1"].path_length > 0.0
        assert trajectory.geometries["G4"].path_length > 0.0
        assert trajectory.geometries["G6"].path_length > 0.0

    def test_progressive_trajectory_separates_local_and_cumulative_change(self):
        trajectory = analyze_trajectory("T2", progressive_trajectory())
        profile = trajectory.geometries["G2"]

        assert len(profile.local_displacements) == 8
        assert len(profile.cumulative_displacements) == 9
        assert profile.local_displacements != profile.cumulative_displacements[1:]
        assert profile.endpoint_displacement == 0.0
        assert profile.path_length > profile.endpoint_displacement

    def test_g3_is_exact_scalar_multiple_of_g2_for_current_metric(self):
        trajectory = analyze_trajectory("T2", progressive_trajectory())
        cyclic = np.asarray(
            trajectory.geometries["G2"].local_displacements
        )
        angular = np.asarray(
            trajectory.geometries["G3"].local_displacements
        )
        cyclic_cumulative = np.asarray(
            trajectory.geometries["G2"].cumulative_displacements
        )
        angular_cumulative = np.asarray(
            trajectory.geometries["G3"].cumulative_displacements
        )

        assert np.allclose(angular, 45.0 * cyclic, rtol=0.0, atol=1e-12)
        assert np.allclose(
            angular_cumulative,
            45.0 * cyclic_cumulative,
            rtol=0.0,
            atol=1e-12,
        )

    def test_continuity_diagnostics_do_not_collapse_sequence(self):
        trajectory = analyze_trajectory("T2", progressive_trajectory())
        for profile in trajectory.geometries.values():
            assert profile.mean_local_displacement == pytest.approx(
                np.mean(profile.local_displacements)
            )
            assert (
                profile.standard_deviation_local_displacement
                == pytest.approx(np.std(profile.local_displacements))
            )
            assert (
                profile.zero_displacement_transitions
                + profile.nonzero_displacement_transitions
                == len(profile.local_displacements)
            )


class TestPathDependence:

    def test_same_endpoints_can_have_different_temporal_histories(self):
        path_a = analyze_trajectory("T3A", progressive_trajectory())
        path_b = analyze_trajectory(
            "T3B",
            [INITIAL, NONUNIFORM, ENDPOINT],
        )
        comparisons = compare_endpoint_equivalent_paths(path_a, path_b)

        assert path_a.states[0] == path_b.states[0]
        assert path_a.states[-1] == path_b.states[-1]
        for comparison in comparisons.values():
            assert comparison.endpoint_displacements_equal
            assert not comparison.intermediate_relational_sequences_equal
        assert any(
            not comparison.path_lengths_equal
            for comparison in comparisons.values()
        )
        assert any(
            not comparison.maximum_local_displacements_equal
            for comparison in comparisons.values()
        )

    def test_path_comparison_rejects_different_endpoints(self):
        first = analyze_trajectory("first", [INITIAL, ENDPOINT])
        second = analyze_trajectory("second", [INITIAL, NONUNIFORM])

        with pytest.raises(ValueError, match="same final state"):
            compare_endpoint_equivalent_paths(first, second)


class TestReversal:

    def test_forward_and_reverse_local_sequences_match_in_reverse_order(self):
        states = progressive_trajectory()
        forward = analyze_trajectory("T4-forward", states)
        reverse = analyze_trajectory("T4-reverse", list(reversed(states)))
        comparisons = compare_forward_reverse(forward, reverse)

        for comparison in comparisons.values():
            assert comparison.sequences_match
            assert comparison.path_lengths_match
            assert comparison.maximum_discrepancy == 0.0
            assert comparison.forward_sequence == tuple(
                reversed(comparison.reverse_sequence)
            )

    def test_reversal_comparison_requires_exact_reverse_states(self):
        forward = analyze_trajectory("forward", [INITIAL, ENDPOINT])
        not_reverse = analyze_trajectory("not-reverse", [INITIAL, ENDPOINT])

        with pytest.raises(ValueError, match="exactly reverse"):
            compare_forward_reverse(forward, not_reverse)


class TestRepresentationControl:

    def test_component_permutation_trajectory_has_zero_aware_displacement(self):
        control = analyze_component_permutation_trajectory(
            "T5",
            INITIAL,
            [CYCLIC_COMPONENT_PERMUTATION, REVERSAL, PAIR_SWAPS],
        )

        assert control.trajectory.transition_count == 3
        for profile in control.geometries.values():
            assert profile.permutation_aware_equal == (True, True, True)
            assert profile.permutation_aware_displacements == (0.0, 0.0, 0.0)
            assert (
                profile.permutation_aware_cumulative_displacements
                == (0.0, 0.0, 0.0, 0.0)
            )
            assert profile.permutation_aware_path_length == 0.0
            assert profile.permutation_aware_endpoint_displacement == 0.0
            assert (
                profile.permutation_aware_maximum_cumulative_displacement
                == 0.0
            )
            assert profile.permutation_aware_mean_local_displacement == 0.0
            assert (
                profile.permutation_aware_standard_deviation_local_displacement
                == 0.0
            )
            assert profile.permutation_aware_zero_transitions == 3
            assert profile.permutation_aware_nonzero_transitions == 0
        assert any(
            profile.fixed_index_path_length > 0.0
            for profile in control.geometries.values()
        )

    def test_representation_control_records_full_fixed_trajectory(self):
        control = analyze_component_permutation_trajectory(
            "T5",
            INITIAL,
            [CYCLIC_COMPONENT_PERMUTATION],
        )

        for geometry_id in SUPPORTED_GEOMETRIES:
            temporal = control.trajectory.geometries[geometry_id]
            representation = control.geometries[geometry_id]
            assert (
                representation.fixed_index_displacements
                == temporal.local_displacements
            )
            assert (
                representation.fixed_index_cumulative_displacements
                == temporal.cumulative_displacements
            )
            assert (
                representation.fixed_index_endpoint_displacement
                == temporal.endpoint_displacement
            )
            assert len(temporal.relation_matrices) == 2


class TestValidation:

    def test_empty_trajectory_fails(self):
        with pytest.raises(ValueError, match="at least one state"):
            analyze_trajectory("empty", [])

    def test_different_state_lengths_fail(self):
        with pytest.raises(ValueError, match="equal length"):
            analyze_trajectory("bad", [[0, 1], [0, 1, 2]])

    def test_invalid_state_values_fail(self):
        with pytest.raises(ValueError, match="range 0..7"):
            analyze_trajectory("bad", [[0, 8]])

    def test_invalid_component_permutation_fails(self):
        with pytest.raises(ValueError):
            analyze_component_permutation_trajectory(
                "bad",
                INITIAL,
                [[0, 1]],
            )
