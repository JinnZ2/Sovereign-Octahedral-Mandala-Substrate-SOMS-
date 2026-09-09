"""Tests for SOMS Experiment 02: concurrent relational geometries."""

import numpy as np
import pytest

from src.concurrent_relational_geometries import (
    GEOMETRY_ORDER,
    GEOMETRY_SPECS,
    angular_relation,
    cayley_group_relation,
    cyclic_octahedral_relation,
    geometry_divergences,
    gray_code_relation,
    numeric_state_relation,
    observe_relational_profile,
)


INITIAL = np.arange(8)
GLOBAL_CYCLIC = (INITIAL + 1) % 8
LOCAL_PERTURBATION = np.array([1, 1, 2, 3, 4, 5, 6, 7])
MULTIPLE_PERTURBATIONS = np.array([0, 2, 2, 4, 4, 6, 6, 0])
GLOBAL_PERMUTATION = np.array([2, 5, 1, 7, 0, 6, 4, 3])
AVAILABLE_GEOMETRIES = {"G1", "G2", "G3", "G4", "G6"}


class TestIndependentRelations:

    def test_numeric_relation_is_not_cyclic(self):
        assert numeric_state_relation(0, 7) == 7.0

    def test_cyclic_relation_wraps_at_eight(self):
        assert cyclic_octahedral_relation(0, 7) == 1.0
        assert cyclic_octahedral_relation(7, 0) == 1.0

    def test_angular_relation_uses_circular_distance(self):
        assert angular_relation(0, 7) == 45.0
        assert angular_relation(0, 4) == 180.0

    def test_gray_relation_reuses_hamming_distance(self):
        assert gray_code_relation(0, 7) == 1.0
        assert gray_code_relation(0, 2) == 2.0

    def test_cayley_relation_is_symmetric_and_reflexive(self):
        assert cayley_group_relation(0, 0) == 0.0
        assert cayley_group_relation(0, 7) == cayley_group_relation(7, 0)

    def test_each_available_geometry_remains_callable(self):
        for identifier in AVAILABLE_GEOMETRIES:
            relation = GEOMETRY_SPECS[identifier].relation
            assert callable(relation)
            assert relation(0, 1) >= 0.0

    def test_mandala_geometry_is_explicitly_unavailable(self):
        specification = GEOMETRY_SPECS["G5"]
        assert not specification.available
        assert specification.relation is None
        assert "unsupported assumption" in specification.unavailable_reason


class TestControlledTransformations:

    @staticmethod
    def assert_complete_profile(profile):
        assert tuple(profile.geometries) == GEOMETRY_ORDER
        for identifier in AVAILABLE_GEOMETRIES:
            measurement = profile.geometries[identifier]
            assert measurement.available
            assert measurement.displacement is not None
            assert measurement.displacement >= 0.0
            assert 0.0 <= measurement.similarity <= 1.0
        assert not profile.geometries["G5"].available
        assert profile.geometries["G5"].displacement is None
        assert profile.geometries["G5"].similarity is None

    def test_case_a_no_transformation(self):
        profile = observe_relational_profile(INITIAL, INITIAL.copy())

        self.assert_complete_profile(profile)
        assert profile.component_displacement == 0.0
        assert profile.changed_components == 0
        assert profile.component_change_fraction == 0.0
        for identifier in AVAILABLE_GEOMETRIES:
            assert profile.geometries[identifier].displacement == 0.0
            assert profile.geometries[identifier].similarity == 1.0

    def test_case_b_global_cyclic_transformation(self):
        profile = observe_relational_profile(INITIAL, GLOBAL_CYCLIC)

        self.assert_complete_profile(profile)
        assert profile.changed_components == 8
        assert profile.component_change_fraction == 1.0
        assert profile.geometries["G1"].displacement > 0.0
        assert profile.geometries["G2"].displacement == 0.0
        assert profile.geometries["G3"].displacement == 0.0
        assert profile.geometries["G4"].displacement > 0.0
        assert profile.geometries["G6"].displacement > 0.0

    @pytest.mark.parametrize(
        "current, expected_changed",
        [
            (LOCAL_PERTURBATION, 1),
            (MULTIPLE_PERTURBATIONS, 4),
            (GLOBAL_PERMUTATION, 8),
        ],
    )
    def test_cases_c_d_and_e_produce_complete_profiles(
        self,
        current,
        expected_changed,
    ):
        profile = observe_relational_profile(INITIAL, current)

        self.assert_complete_profile(profile)
        assert profile.changed_components == expected_changed
        assert all(
            profile.geometries[identifier].displacement > 0.0
            for identifier in AVAILABLE_GEOMETRIES
        )

    def test_case_e_exposes_geometry_specific_measurements(self):
        profile = observe_relational_profile(INITIAL, GLOBAL_PERMUTATION)
        displacements = {
            round(profile.geometries[identifier].displacement, 12)
            for identifier in AVAILABLE_GEOMETRIES
        }

        assert len(displacements) > 1

    def test_case_f_progressive_transformation(self):
        profiles = []

        for changed_components in range(9):
            current = INITIAL.copy()
            current[:changed_components] = (
                current[:changed_components] + 1
            ) % 8
            profiles.append(observe_relational_profile(INITIAL, current))

        assert [
            profile.changed_components
            for profile in profiles
        ] == list(range(9))
        for profile in profiles:
            self.assert_complete_profile(profile)
        assert profiles[0].geometries["G2"].similarity == 1.0
        for profile in profiles[1:-1]:
            assert all(
                profile.geometries[identifier].displacement > 0.0
                for identifier in AVAILABLE_GEOMETRIES
            )
        assert profiles[-1].geometries["G2"].similarity == 1.0
        assert profiles[-1].geometries["G3"].similarity == 1.0
        assert profiles[-1].geometries["G1"].displacement > 0.0
        assert profiles[-1].geometries["G4"].displacement > 0.0
        assert profiles[-1].geometries["G6"].displacement > 0.0

    def test_geometry_divergence_is_descriptive_pairwise_difference(self):
        profile = observe_relational_profile(INITIAL, GLOBAL_CYCLIC)
        divergences = geometry_divergences(profile)

        assert len(divergences) == 10
        assert divergences["G1:G2"] == abs(
            profile.geometries["G1"].displacement
            - profile.geometries["G2"].displacement
        )
        assert all("G5" not in pair for pair in divergences)


class TestValidation:

    def test_mismatched_lengths_fail(self):
        with pytest.raises(ValueError):
            observe_relational_profile([0, 1], [0])

    def test_non_integer_states_fail(self):
        with pytest.raises(ValueError):
            observe_relational_profile([0.0, 1.0], [0.0, 1.0])

    def test_out_of_range_states_fail(self):
        with pytest.raises(ValueError):
            observe_relational_profile([0, 8], [0, 1])

    def test_non_1d_states_fail(self):
        with pytest.raises(ValueError):
            observe_relational_profile([[0, 1]], [0, 1])
