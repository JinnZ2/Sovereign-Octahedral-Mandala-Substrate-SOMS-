"""Tests for SOMS Experiment 05 relational correspondence controls."""

import numpy as np
import pytest

from src.isometry_controls import (
    IDENTITY_PERMUTATION,
    PERMUTATION_COUNT,
    SUPPORTED_GEOMETRIES,
)
from src.relational_correspondence import (
    analyze_ambiguity,
    analyze_residual,
    analyze_temporal_correspondence,
    apply_correspondence,
    apply_correspondence_and_mutations,
    compare_collision,
    compare_correspondence,
    exact_state_correspondences,
    recover_correspondences,
    state_stabilizer,
)


CANONICAL = np.arange(8)
NONUNIFORM = (2, 5, 1, 7, 0, 6, 4, 3)
REPEATED = np.array([0, 0, 0, 0, 4, 4, 4, 4])
REPEATED_STABILIZER_MEMBER = (1, 2, 3, 0, 5, 6, 7, 4)
COLLISION_A = np.array([0, 0, 1, 1, 2, 2, 3, 3])
COLLISION_B = np.array([1, 1, 2, 2, 3, 3, 4, 4])


class TestCorrespondenceControls:

    def test_identity_correspondence_matches_fixed_index_comparison(self):
        target = CANONICAL.copy()
        target[0] = 1

        for geometry_id in SUPPORTED_GEOMETRIES:
            result = compare_correspondence(
                geometry_id,
                CANONICAL,
                target,
                IDENTITY_PERMUTATION,
            )
            assert (
                result.correspondence_displacement
                == result.fixed_index_displacement
            )

    def test_known_permutation_removes_pure_reindexing(self):
        target = apply_correspondence(CANONICAL, NONUNIFORM)

        for geometry_id in SUPPORTED_GEOMETRIES:
            result = compare_correspondence(
                geometry_id,
                CANONICAL,
                target,
                NONUNIFORM,
            )
            assert result.correspondence_exact
            assert result.correspondence_displacement == 0.0
            assert result.correspondence_maximum_elementwise == 0.0

    def test_permutation_plus_mutation_leaves_residual(self):
        target = apply_correspondence_and_mutations(
            CANONICAL,
            NONUNIFORM,
            {0: 3},
        )

        for geometry_id in SUPPORTED_GEOMETRIES:
            result = compare_correspondence(
                geometry_id,
                CANONICAL,
                target,
                NONUNIFORM,
            )
            assert not result.correspondence_exact
            assert result.correspondence_displacement > 0.0


class TestExhaustiveRecovery:

    @pytest.mark.parametrize("geometry_id", SUPPORTED_GEOMETRIES)
    def test_hidden_pure_permutation_is_among_exact_minimizers(
        self,
        geometry_id,
    ):
        target = apply_correspondence(CANONICAL, NONUNIFORM)
        recovery = recover_correspondences(
            geometry_id,
            CANONICAL,
            target,
            true_permutation=NONUNIFORM,
        )

        assert recovery.permutations_tested == PERMUTATION_COUNT
        assert recovery.minimum_displacement == 0.0
        assert recovery.true_permutation_among_minimizers
        assert recovery.minimizing_count > 1

    def test_repeated_state_stabilizer_is_measured_exactly(self):
        stabilizer = state_stabilizer(REPEATED)
        correspondences = exact_state_correspondences(REPEATED, REPEATED)

        assert len(stabilizer) == 576
        assert len(correspondences) == 576
        assert REPEATED_STABILIZER_MEMBER in stabilizer

    @pytest.mark.parametrize("geometry_id", SUPPORTED_GEOMETRIES)
    def test_repeated_relational_ambiguity_exceeds_state_equality(
        self,
        geometry_id,
    ):
        ambiguity = analyze_ambiguity(
            geometry_id,
            REPEATED,
            REPEATED,
            true_permutation=REPEATED_STABILIZER_MEMBER,
        )

        assert ambiguity.state_stabilizer_count == 576
        assert ambiguity.exact_state_correspondence_count == 576
        assert ambiguity.relational_minimizer_count == 1152
        assert ambiguity.relational_ambiguity_exceeds_state_equality
        assert ambiguity.minimum_relational_displacement == 0.0


class TestMutationResiduals:

    @pytest.mark.parametrize("geometry_id", SUPPORTED_GEOMETRIES)
    def test_single_mutation_residual_is_local_to_affected_component(
        self,
        geometry_id,
    ):
        target = CANONICAL.copy()
        target[0] = 1
        residual = analyze_residual(
            geometry_id,
            CANONICAL,
            target,
            IDENTITY_PERMUTATION,
        )

        assert residual.frobenius_norm > 0.0
        assert residual.nonzero_element_count > 0
        assert all(0 in pair for pair in residual.affected_component_pairs)
        assert residual.affected_components[0] == 0

    def test_pure_permutation_has_zero_residual_under_true_mapping(self):
        target = apply_correspondence(CANONICAL, NONUNIFORM)
        residual = analyze_residual(
            "G4",
            CANONICAL,
            target,
            NONUNIFORM,
        )

        assert residual.frobenius_norm == 0.0
        assert residual.maximum_absolute_element == 0.0
        assert residual.nonzero_element_count == 0
        assert residual.affected_component_pairs == ()


class TestCollisionControl:

    def test_v6_distinct_states_collide_under_numeric_geometry(self):
        collision = compare_collision("G1", COLLISION_A, COLLISION_B)

        assert not collision.states_equal
        assert collision.relation_matrices_equal
        assert collision.frobenius_displacement == 0.0

    def test_v6_collision_has_no_exact_state_correspondence(self):
        state_correspondences = exact_state_correspondences(
            COLLISION_A,
            COLLISION_B,
        )
        recovery = recover_correspondences(
            "G1",
            COLLISION_A,
            COLLISION_B,
        )

        assert state_correspondences == ()
        assert recovery.minimum_displacement == 0.0
        assert recovery.minimizing_count == 32
        assert not recovery.unique

    def test_collision_is_measured_per_geometry(self):
        collisions = {
            geometry_id: compare_collision(
                geometry_id,
                COLLISION_A,
                COLLISION_B,
            )
            for geometry_id in SUPPORTED_GEOMETRIES
        }

        assert collisions["G1"].relation_matrices_equal
        assert collisions["G2"].relation_matrices_equal
        assert collisions["G3"].relation_matrices_equal
        assert any(
            not result.relation_matrices_equal
            for result in collisions.values()
        )


class TestTemporalCorrespondence:

    def test_temporal_profile_separates_fixed_true_and_best_paths(self):
        state_1 = apply_correspondence(CANONICAL, NONUNIFORM)
        state_2 = apply_correspondence_and_mutations(
            state_1,
            IDENTITY_PERMUTATION,
            {0: 3},
        )
        state_3 = apply_correspondence_and_mutations(
            state_2,
            tuple(reversed(range(8))),
            {1: 2},
        )
        profiles = analyze_temporal_correspondence(
            [CANONICAL, state_1, state_2, state_3],
            [
                NONUNIFORM,
                IDENTITY_PERMUTATION,
                tuple(reversed(range(8))),
            ],
        )

        for profile in profiles.values():
            assert len(profile.steps) == 3
            assert profile.fixed_index_path_length >= 0.0
            assert profile.true_correspondence_path_length >= 0.0
            assert profile.best_correspondence_path_length >= 0.0
            assert profile.steps[0].best_correspondence_displacement == 0.0
            assert profile.steps[0].true_permutation_among_minimizers


class TestValidation:

    def test_invalid_correspondence_fails(self):
        with pytest.raises(ValueError):
            compare_correspondence(
                "G1",
                CANONICAL,
                CANONICAL,
                [0, 1],
            )

    def test_exhaustive_recovery_requires_eight_components(self):
        with pytest.raises(ValueError, match="eight components"):
            recover_correspondences("G1", [0, 1], [1, 0])

    def test_temporal_profile_requires_one_mapping_per_transition(self):
        with pytest.raises(ValueError, match="One true correspondence"):
            analyze_temporal_correspondence(
                [CANONICAL, CANONICAL],
                [],
            )
