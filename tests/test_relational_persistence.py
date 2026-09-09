"""Tests for the neutral relational-persistence experiment."""

import numpy as np
import pytest

from src.relational_persistence import (
    RelationalPersistenceObserver,
    equality_relation,
    octahedral_relation,
)


class TestRelationalPersistenceObserver:

    def test_identical_states_have_zero_change(self):
        observer = RelationalPersistenceObserver(
            relation=equality_relation
        )

        state = np.array([0, 1, 2, 3, 4, 5, 6, 7])

        result = observer.observe(state, state.copy())

        assert result.state_distance == 0.0
        assert result.relation_distance == 0.0
        assert result.relation_similarity == 1.0
        assert result.changed_components == 0

    def test_global_cyclic_transformation_preserves_relations(self):
        observer = RelationalPersistenceObserver(
            relation=octahedral_relation
        )

        previous = np.arange(8)
        current = (previous + 1) % 8

        result = observer.observe(previous, current)

        assert result.changed_components == 8
        assert result.component_change_fraction == 1.0
        assert result.state_distance > 0.0
        assert result.relation_distance == 0.0
        assert result.relation_similarity == 1.0

    def test_local_perturbation_changes_relations(self):
        observer = RelationalPersistenceObserver(
            relation=octahedral_relation
        )

        previous = np.arange(8)
        current = previous.copy()
        current[0] = 1

        result = observer.observe(previous, current)

        assert result.changed_components == 1
        assert result.total_components == 8
        assert result.component_change_fraction == 0.125
        assert result.state_distance > 0.0
        assert result.relation_distance > 0.0
        assert 0.0 <= result.relation_similarity < 1.0

    def test_multiple_nonuniform_perturbations_change_relations(self):
        observer = RelationalPersistenceObserver(
            relation=octahedral_relation
        )

        previous = np.arange(8)
        current = np.array([0, 2, 2, 4, 4, 6, 6, 0])

        result = observer.observe(previous, current)

        assert result.changed_components == 4
        assert result.component_change_fraction == 0.5
        assert result.state_distance > 0.0
        assert result.relation_distance > 0.0
        assert 0.0 <= result.relation_similarity < 1.0

    def test_progressive_perturbation_trajectory_is_not_monotonic(self):
        observer = RelationalPersistenceObserver(
            relation=octahedral_relation
        )

        initial = np.arange(8)
        trajectory = []

        for changed_components in range(9):
            current = initial.copy()
            current[:changed_components] = (
                current[:changed_components] + 1
            ) % 8
            trajectory.append(observer.observe(initial, current))

        similarities = [
            observation.relation_similarity
            for observation in trajectory
        ]

        assert [
            observation.changed_components
            for observation in trajectory
        ] == list(range(9))
        assert similarities[0] == 1.0
        assert min(similarities[1:-1]) < 1.0
        assert similarities[-1] == 1.0

    def test_relation_matrix_shape(self):
        observer = RelationalPersistenceObserver(
            relation=equality_relation
        )

        state = np.array([0, 1, 2, 3, 4])

        matrix = observer.relation_matrix(state)

        assert matrix.shape == (5, 5)

    def test_relation_matrix_is_symmetric_for_equality(self):
        observer = RelationalPersistenceObserver(
            relation=equality_relation
        )

        state = np.array([0, 1, 2, 3])

        matrix = observer.relation_matrix(state)

        assert np.array_equal(matrix, matrix.T)

    def test_empty_states(self):
        observer = RelationalPersistenceObserver()

        result = observer.observe(
            np.array([], dtype=int),
            np.array([], dtype=int),
        )

        assert result.state_distance == 0.0
        assert result.relation_distance == 0.0
        assert result.relation_similarity == 1.0
        assert result.total_components == 0

    def test_mismatched_state_lengths_fail(self):
        observer = RelationalPersistenceObserver()

        with pytest.raises(ValueError):
            observer.observe(
                np.array([0, 1, 2]),
                np.array([0, 1]),
            )

    def test_non_1d_state_fails(self):
        observer = RelationalPersistenceObserver()

        with pytest.raises(ValueError):
            observer.observe(
                np.array([[0, 1], [2, 3]]),
                np.array([0, 1, 2, 3]),
            )

    def test_similarity_is_bounded(self):
        observer = RelationalPersistenceObserver(
            relation=octahedral_relation
        )

        previous = np.array([0, 1, 2, 3, 4, 5, 6, 7])
        current = np.array([7, 6, 5, 4, 3, 2, 1, 0])

        result = observer.observe(previous, current)

        assert 0.0 <= result.relation_similarity <= 1.0
