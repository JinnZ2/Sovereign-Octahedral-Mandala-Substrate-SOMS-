"""Tests for SOMS Experiment 03 isometry and representation controls."""

import numpy as np
import pytest

from src.isometry_controls import (
    CYCLIC_SHIFTS,
    GEOMETRY_TOLERANCES,
    GLOBAL_CYCLIC_SHIFT,
    IDENTITY_PERMUTATION,
    PERMUTATION_COUNT,
    REVERSAL_PERMUTATION,
    SUPPORTED_GEOMETRIES,
    all_permutation_array,
    apply_component_permutation,
    apply_state_label_permutation,
    compare_component_permutation,
    compare_matrices,
    compare_state_label_permutation,
    enumerate_component_permutations,
    enumerate_state_label_symmetries,
    evaluate_e02_cyclic_control,
    geometry_relation_matrix,
    is_state_label_isometry,
    permutation_matrix,
    relation_matrix,
    symmetry_set_comparisons,
)
from src.concurrent_relational_geometries import numeric_state_relation


CANONICAL = np.arange(8)


class TestGeometryNeutralPrimitives:

    def test_relation_matrix_generation(self):
        matrix = relation_matrix([0, 1, 3], numeric_state_relation)
        assert np.array_equal(
            matrix,
            np.array(
                [
                    [0.0, 1.0, 3.0],
                    [1.0, 0.0, 2.0],
                    [3.0, 2.0, 0.0],
                ]
            ),
        )

    def test_state_label_permutation_changes_values_not_indices(self):
        transformed = apply_state_label_permutation(
            CANONICAL,
            GLOBAL_CYCLIC_SHIFT,
        )
        assert np.array_equal(
            transformed,
            np.array([1, 2, 3, 4, 5, 6, 7, 0]),
        )

    def test_component_permutation_reorders_positions(self):
        state = np.array([7, 6, 5, 4, 3, 2, 1, 0])
        reordered = apply_component_permutation(
            state,
            GLOBAL_CYCLIC_SHIFT,
        )
        assert np.array_equal(
            reordered,
            np.array([6, 5, 4, 3, 2, 1, 0, 7]),
        )

    def test_permutation_matrix_matches_component_reordering(self):
        transform = permutation_matrix(GLOBAL_CYCLIC_SHIFT)
        assert np.array_equal(
            transform @ CANONICAL,
            apply_component_permutation(
                CANONICAL,
                GLOBAL_CYCLIC_SHIFT,
            ),
        )

    def test_matrix_comparison_reports_all_required_metrics(self):
        first = np.array([[0.0, 1.0], [1.0, 0.0]])
        second = np.array([[0.0, 2.0], [2.0, 0.0]])
        comparison = compare_matrices(first, second)

        assert not comparison.exact_equal
        assert comparison.frobenius_displacement == pytest.approx(2**0.5)
        assert comparison.maximum_elementwise_displacement == 1.0

    def test_angular_geometry_has_explicit_tolerance(self):
        assert GEOMETRY_TOLERANCES["G3"] == 1e-12


class TestStateLabelControls:

    def test_all_permutations_are_generated_once(self):
        values = all_permutation_array()
        assert values.shape == (PERMUTATION_COUNT, 8)
        assert len({tuple(row) for row in values}) == PERMUTATION_COUNT
        assert tuple(values[0]) == IDENTITY_PERMUTATION
        assert tuple(values[-1]) == REVERSAL_PERMUTATION

    def test_identity_isometry_for_every_geometry(self):
        assert all(
            is_state_label_isometry(
                geometry_id,
                IDENTITY_PERMUTATION,
            )
            for geometry_id in SUPPORTED_GEOMETRIES
        )

    def test_global_shift_is_geometry_specific(self):
        results = {
            geometry_id: compare_state_label_permutation(
                geometry_id,
                GLOBAL_CYCLIC_SHIFT,
            )
            for geometry_id in SUPPORTED_GEOMETRIES
        }

        assert results["G2"].exact_equal
        assert results["G3"].exact_equal
        assert not results["G1"].exact_equal
        assert not results["G4"].exact_equal
        assert not results["G6"].exact_equal

    def test_exhaustive_state_label_enumeration(self):
        results = {
            geometry_id: enumerate_state_label_symmetries(geometry_id)
            for geometry_id in SUPPORTED_GEOMETRIES
        }
        expected_counts = {
            "G1": 2,
            "G2": 16,
            "G3": 16,
            "G4": 48,
            "G6": 2,
        }
        expected_cyclic_shift_counts = {
            "G1": 1,
            "G2": 8,
            "G3": 8,
            "G4": 4,
            "G6": 1,
        }
        expected_reversal_membership = {
            "G1": True,
            "G2": True,
            "G3": True,
            "G4": True,
            "G6": False,
        }

        for geometry_id, result in results.items():
            assert result.permutations_tested == PERMUTATION_COUNT
            assert result.identity_present
            assert result.automorphism_count == expected_counts[geometry_id]
            assert (
                result.cyclic_shift_count
                == expected_cyclic_shift_counts[geometry_id]
            )
            assert (
                result.reversal_present
                == expected_reversal_membership[geometry_id]
            )
            assert len(result.cyclic_shift_membership) == len(CYCLIC_SHIFTS)
        assert results["G2"].global_cyclic_shift_present
        assert results["G3"].global_cyclic_shift_present
        assert set(results["G2"].automorphisms) == set(
            results["G3"].automorphisms
        )

    def test_symmetry_set_intersections_are_reported(self):
        enumerations = {
            geometry_id: enumerate_state_label_symmetries(geometry_id)
            for geometry_id in SUPPORTED_GEOMETRIES
        }
        comparisons = symmetry_set_comparisons(enumerations)

        assert len(comparisons) == 10
        assert comparisons["G2:G3"]["equal_sets"]
        assert comparisons["G2:G3"]["only_first"] == 0
        assert comparisons["G2:G3"]["only_second"] == 0


class TestComponentIndexControls:

    def test_fixed_and_permutation_aware_comparisons_are_separate(self):
        comparison = compare_component_permutation(
            "G1",
            CANONICAL,
            GLOBAL_CYCLIC_SHIFT,
        )

        assert not comparison.fixed_index.exact_equal
        assert comparison.fixed_index.frobenius_displacement > 0.0
        assert comparison.permutation_aware.exact_equal
        assert comparison.permutation_aware.frobenius_displacement == 0.0

    @pytest.mark.parametrize("geometry_id", SUPPORTED_GEOMETRIES)
    def test_permutation_aware_comparison_preserves_structure(
        self,
        geometry_id,
    ):
        comparison = compare_component_permutation(
            geometry_id,
            np.array([0, 0, 1, 1, 2, 2, 3, 3]),
            REVERSAL_PERMUTATION,
        )
        assert comparison.permutation_aware.exact_equal
        assert comparison.permutation_aware.frobenius_displacement == 0.0
        assert (
            comparison.permutation_aware.maximum_elementwise_displacement
            == 0.0
        )

    def test_exhaustive_component_enumeration(self):
        result = enumerate_component_permutations(
            "G4",
            "repeated",
            np.array([0, 0, 1, 1, 2, 2, 3, 3]),
        )

        assert result.permutations_tested == PERMUTATION_COUNT
        assert result.fixed_index_equal_count > 0
        assert result.permutation_aware_equal_count == PERMUTATION_COUNT
        assert result.permutation_aware_frobenius_maximum == 0.0
        assert (
            result.permutation_aware_maximum_elementwise_displacement
            == 0.0
        )

    def test_e02_control_distinguishes_label_and_index_descriptions(self):
        controls = {
            geometry_id: evaluate_e02_cyclic_control(geometry_id)
            for geometry_id in SUPPORTED_GEOMETRIES
        }

        assert controls["G2"].classification == "state-space isometry"
        assert controls["G3"].classification == "state-space isometry"
        for geometry_id in ("G1", "G4", "G6"):
            assert not controls[geometry_id].state_label.exact_equal
            assert controls[
                geometry_id
            ].component_permutation_aware.exact_equal
            assert "non-isometry" in controls[geometry_id].classification
            assert "representation effect" in controls[geometry_id].classification


class TestValidation:

    def test_unavailable_geometry_fails_explicitly(self):
        with pytest.raises(ValueError, match="G5 is unavailable"):
            geometry_relation_matrix("G5", CANONICAL)

    def test_invalid_state_label_permutation_fails(self):
        with pytest.raises(ValueError):
            apply_state_label_permutation(
                CANONICAL,
                [0, 1, 2, 3, 4, 5, 6, 6],
            )

    def test_invalid_component_permutation_fails(self):
        with pytest.raises(ValueError):
            apply_component_permutation(CANONICAL, [0, 1])

    def test_exhaustive_component_control_requires_eight_components(self):
        with pytest.raises(ValueError, match="eight components"):
            enumerate_component_permutations("G1", "short", [0, 1])
