"""Tests for SOMS Experiment 06 relational identifiability."""

import numpy as np
import pytest

from src.isometry_controls import SUPPORTED_GEOMETRIES
from src.relational_identifiability import (
    JOINT_GEOMETRIES,
    analyze_temporal_pair,
    classify_equal_relation_pair,
    enumerate_equivalence_classes,
    enumerate_states,
    find_minimal_genuine_collision,
    geometry_automorphisms,
    joint_automorphisms,
    measure_cross_geometry,
)


class TestBoundedEnumeration:

    def test_length_four_space_contains_all_4096_vectors(self):
        states = enumerate_states(4)

        assert len(states) == 4096
        assert states[0] == (0, 0, 0, 0)
        assert states[-1] == (7, 7, 7, 7)
        assert len(set(states)) == 4096

    @pytest.mark.parametrize("geometry_id", SUPPORTED_GEOMETRIES)
    def test_equivalence_classes_partition_entire_state_space(
        self,
        geometry_id,
    ):
        summary = enumerate_equivalence_classes(geometry_id, 2)
        members = [
            member
            for equivalence_class in summary.classes
            for member in equivalence_class.members
        ]

        assert summary.total_state_vectors == 64
        assert len(members) == 64
        assert len(set(members)) == 64
        assert summary.distinct_relation_matrices == len(summary.classes)
        assert (
            summary.singleton_class_count
            + sum(item.size for item in summary.nontrivial_classes)
            == 64
        )

    def test_every_nontrivial_pair_has_one_classification(self):
        summary = enumerate_equivalence_classes("G1", 2)

        for equivalence_class in summary.nontrivial_classes:
            expected_pairs = (
                equivalence_class.size * (equivalence_class.size - 1) // 2
            )
            assert len(equivalence_class.pair_relationships) == expected_pairs
            assert (
                sum(equivalence_class.pair_classification_counts.values())
                == expected_pairs
            )


class TestCollisionClassification:

    def test_component_permutation_is_separate_from_collision(self):
        result = classify_equal_relation_pair(
            (0, 1),
            (1, 0),
            geometry_automorphisms("G1"),
        )

        assert result.classification == "component_permutation"
        assert result.component_permutation == (1, 0)

    def test_label_isometry_is_separate_from_collision(self):
        result = classify_equal_relation_pair(
            (0, 1),
            (7, 6),
            geometry_automorphisms("G1"),
        )

        assert result.classification == "label_isometry"
        assert result.label_automorphism is not None

    def test_numeric_translation_is_genuine_under_full_space_symmetries(self):
        result = classify_equal_relation_pair(
            (0, 1),
            (2, 3),
            geometry_automorphisms("G1"),
        )

        assert result.classification == "representation_collision"

    def test_g3_and_g2_have_equal_bounded_class_partitions(self):
        cyclic = enumerate_equivalence_classes("G2", 2)
        angular = enumerate_equivalence_classes("G3", 2)

        assert [item.members for item in cyclic.classes] == [
            item.members for item in angular.classes
        ]


class TestJointRepresentation:

    def test_joint_uses_no_independent_g3_component(self):
        assert JOINT_GEOMETRIES == ("G1", "G2", "G4", "G6")
        assert "G3" not in JOINT_GEOMETRIES

    def test_joint_automorphisms_preserve_every_joint_geometry(self):
        shared = set(joint_automorphisms())

        assert shared
        for geometry_id in JOINT_GEOMETRIES:
            assert shared <= set(geometry_automorphisms(geometry_id))

    def test_joint_classes_partition_state_space(self):
        summary = enumerate_equivalence_classes("joint", 2)

        assert sum(item.size for item in summary.classes) == 64
        assert summary.maximum_class_size >= 1


class TestMinimalCollisionSearch:

    def test_numeric_geometry_has_bounded_genuine_collision(self):
        result = find_minimal_genuine_collision("G1", maximum_length=2)

        assert result.minimum_collision_length is not None
        assert result.first is not None
        assert result.second is not None
        assert result.pair_classification == "representation_collision"

    def test_invalid_search_bound_fails(self):
        with pytest.raises(ValueError, match="positive"):
            find_minimal_genuine_collision("G1", maximum_length=0)


class TestCrossGeometryAndTemporalControls:

    def test_e05_v6_separation_signature_is_reproduced(self):
        measurement = measure_cross_geometry(
            (0, 0, 1, 1, 2, 2, 3, 3),
            (1, 1, 2, 2, 3, 3, 4, 4),
        )

        assert measurement.indistinguishable_geometries == ("G1", "G2", "G3")
        assert measurement.distinguishable_geometries == ("G4", "G6")

    def test_temporal_control_records_relation_matrices_and_displacements(self):
        profiles = analyze_temporal_pair(
            "collision-to-distinguishable",
            "collision -> distinguishable",
            [(0, 0, 1, 1), (0, 0, 1, 1)],
            [(1, 1, 2, 2), (1, 1, 2, 3)],
        )
        numeric = profiles["G1"]

        assert [instant.equivalent for instant in numeric.instants] == [True, False]
        assert all(instant.relation_matrix_a.shape == (4, 4) for instant in numeric.instants)
        assert len(numeric.transitions) == 1
        assert numeric.transitions[0].displacement_b > 0.0

    def test_temporal_control_validates_paired_lengths(self):
        with pytest.raises(ValueError, match="equal nonzero length"):
            analyze_temporal_pair(
                "bad",
                "bad",
                [(0, 1)],
                [(0, 1), (1, 2)],
            )
