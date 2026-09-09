"""
SOMS Experiment 04: Temporal Relational Continuity.

This module measures complete relational trajectories. It retains every
per-state relation matrix, every adjacent displacement, and every displacement
from the initial state. Summary statistics remain geometry-specific and do not
form a universal continuity score.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from src.isometry_controls import (
    GEOMETRY_TOLERANCES,
    SUPPORTED_GEOMETRIES,
    apply_component_permutation,
    compare_matrices,
    geometry_relation_matrix,
    permutation_matrix,
)


State = tuple[int, ...]
Permutation = tuple[int, ...]


@dataclass(frozen=True)
class TemporalGeometryProfile:
    """Complete temporal data and derived metrics for one geometry."""

    geometry_id: str
    relation_matrices: tuple[np.ndarray, ...]
    local_displacements: tuple[float, ...]
    cumulative_displacements: tuple[float, ...]
    path_length: float
    endpoint_displacement: float
    maximum_local_displacement: float
    maximum_cumulative_displacement: float
    mean_local_displacement: float
    standard_deviation_local_displacement: float
    zero_displacement_transitions: int
    nonzero_displacement_transitions: int


@dataclass(frozen=True)
class TemporalTrajectory:
    """One state trajectory measured under every supported geometry."""

    name: str
    states: tuple[State, ...]
    geometries: Mapping[str, TemporalGeometryProfile]

    @property
    def transition_count(self) -> int:
        return max(len(self.states) - 1, 0)


@dataclass(frozen=True)
class EndpointPathComparison:
    """Comparison of two trajectories with identical endpoints."""

    geometry_id: str
    endpoint_displacement_a: float
    endpoint_displacement_b: float
    endpoint_displacements_equal: bool
    path_length_a: float
    path_length_b: float
    path_length_difference: float
    path_lengths_equal: bool
    maximum_local_displacement_a: float
    maximum_local_displacement_b: float
    maximum_local_displacements_equal: bool
    maximum_cumulative_displacement_a: float
    maximum_cumulative_displacement_b: float
    intermediate_relational_sequences_equal: bool


@dataclass(frozen=True)
class ReversalComparison:
    """Forward/reverse local-displacement sequence comparison."""

    geometry_id: str
    forward_sequence: tuple[float, ...]
    reverse_sequence: tuple[float, ...]
    reverse_sequence_in_forward_order: tuple[float, ...]
    sequences_match: bool
    path_lengths_match: bool
    maximum_discrepancy: float


@dataclass(frozen=True)
class RepresentationGeometryProfile:
    """Fixed-index and permutation-aware temporal controls."""

    geometry_id: str
    fixed_index_displacements: tuple[float, ...]
    permutation_aware_displacements: tuple[float, ...]
    fixed_index_cumulative_displacements: tuple[float, ...]
    permutation_aware_cumulative_displacements: tuple[float, ...]
    fixed_index_maximum_elementwise: tuple[float, ...]
    permutation_aware_maximum_elementwise: tuple[float, ...]
    fixed_index_equal: tuple[bool, ...]
    permutation_aware_equal: tuple[bool, ...]
    fixed_index_path_length: float
    permutation_aware_path_length: float
    fixed_index_endpoint_displacement: float
    permutation_aware_endpoint_displacement: float
    fixed_index_maximum_local_displacement: float
    permutation_aware_maximum_local_displacement: float
    fixed_index_maximum_cumulative_displacement: float
    permutation_aware_maximum_cumulative_displacement: float
    fixed_index_mean_local_displacement: float
    permutation_aware_mean_local_displacement: float
    fixed_index_standard_deviation_local_displacement: float
    permutation_aware_standard_deviation_local_displacement: float
    fixed_index_zero_transitions: int
    permutation_aware_zero_transitions: int
    fixed_index_nonzero_transitions: int
    permutation_aware_nonzero_transitions: int


@dataclass(frozen=True)
class RepresentationControlTrajectory:
    """A trajectory generated solely by component-index permutations."""

    name: str
    trajectory: TemporalTrajectory
    permutations: tuple[Permutation, ...]
    geometries: Mapping[str, RepresentationGeometryProfile]


def _validate_trajectory(
    states: Sequence[Sequence[int]],
) -> tuple[State, ...]:
    if not states:
        raise ValueError("Trajectory must contain at least one state.")

    validated: list[State] = []
    expected_length: int | None = None

    for state in states:
        values = np.asarray(state)
        if values.ndim != 1:
            raise ValueError("Every trajectory state must be one-dimensional.")
        if not np.issubdtype(values.dtype, np.integer):
            raise ValueError("Trajectory state values must be integers.")
        if np.any((values < 0) | (values >= 8)):
            raise ValueError("Trajectory state values must be in the range 0..7.")

        if expected_length is None:
            expected_length = len(values)
        elif len(values) != expected_length:
            raise ValueError("Every trajectory state must have equal length.")

        validated.append(tuple(int(value) for value in values))

    return tuple(validated)


def _displacement(
    first: np.ndarray,
    second: np.ndarray,
) -> float:
    return float(np.linalg.norm(second - first))


def _temporal_geometry_profile(
    geometry_id: str,
    states: tuple[State, ...],
) -> TemporalGeometryProfile:
    matrices = tuple(
        geometry_relation_matrix(geometry_id, state)
        for state in states
    )
    local = tuple(
        _displacement(first, second)
        for first, second in zip(matrices, matrices[1:])
    )
    cumulative = tuple(
        _displacement(matrices[0], matrix)
        for matrix in matrices
    )
    tolerance = GEOMETRY_TOLERANCES[geometry_id]
    local_values = np.asarray(local, dtype=float)

    if len(local_values) == 0:
        maximum_local = 0.0
        mean_local = 0.0
        standard_deviation = 0.0
    else:
        maximum_local = float(np.max(local_values))
        mean_local = float(np.mean(local_values))
        standard_deviation = float(np.std(local_values))

    zero_count = int(np.count_nonzero(local_values <= tolerance))

    return TemporalGeometryProfile(
        geometry_id=geometry_id,
        relation_matrices=matrices,
        local_displacements=local,
        cumulative_displacements=cumulative,
        path_length=float(np.sum(local_values)),
        endpoint_displacement=cumulative[-1],
        maximum_local_displacement=maximum_local,
        maximum_cumulative_displacement=max(cumulative),
        mean_local_displacement=mean_local,
        standard_deviation_local_displacement=standard_deviation,
        zero_displacement_transitions=zero_count,
        nonzero_displacement_transitions=len(local) - zero_count,
    )


def analyze_trajectory(
    name: str,
    states: Sequence[Sequence[int]],
) -> TemporalTrajectory:
    """Measure and retain a complete trajectory under every geometry."""

    validated = _validate_trajectory(states)
    geometries = {
        geometry_id: _temporal_geometry_profile(
            geometry_id,
            validated,
        )
        for geometry_id in SUPPORTED_GEOMETRIES
    }
    return TemporalTrajectory(
        name=name,
        states=validated,
        geometries=geometries,
    )


def compare_endpoint_equivalent_paths(
    first: TemporalTrajectory,
    second: TemporalTrajectory,
) -> Mapping[str, EndpointPathComparison]:
    """Compare temporal histories only after confirming equal endpoints."""

    if first.states[0] != second.states[0]:
        raise ValueError("Trajectories must have the same initial state.")
    if first.states[-1] != second.states[-1]:
        raise ValueError("Trajectories must have the same final state.")

    comparisons: dict[str, EndpointPathComparison] = {}
    for geometry_id in SUPPORTED_GEOMETRIES:
        first_profile = first.geometries[geometry_id]
        second_profile = second.geometries[geometry_id]
        tolerance = GEOMETRY_TOLERANCES[geometry_id]

        if len(first_profile.relation_matrices) != len(
            second_profile.relation_matrices
        ):
            intermediate_equal = False
        else:
            intermediate_equal = all(
                compare_matrices(
                    first_matrix,
                    second_matrix,
                    atol=tolerance,
                ).exact_equal
                for first_matrix, second_matrix in zip(
                    first_profile.relation_matrices[1:-1],
                    second_profile.relation_matrices[1:-1],
                )
            )

        comparisons[geometry_id] = EndpointPathComparison(
            geometry_id=geometry_id,
            endpoint_displacement_a=(
                first_profile.endpoint_displacement
            ),
            endpoint_displacement_b=(
                second_profile.endpoint_displacement
            ),
            endpoint_displacements_equal=bool(
                np.isclose(
                    first_profile.endpoint_displacement,
                    second_profile.endpoint_displacement,
                    rtol=0.0,
                    atol=tolerance,
                )
            ),
            path_length_a=first_profile.path_length,
            path_length_b=second_profile.path_length,
            path_length_difference=(
                first_profile.path_length - second_profile.path_length
            ),
            path_lengths_equal=bool(
                np.isclose(
                    first_profile.path_length,
                    second_profile.path_length,
                    rtol=0.0,
                    atol=tolerance,
                )
            ),
            maximum_local_displacement_a=(
                first_profile.maximum_local_displacement
            ),
            maximum_local_displacement_b=(
                second_profile.maximum_local_displacement
            ),
            maximum_local_displacements_equal=bool(
                np.isclose(
                    first_profile.maximum_local_displacement,
                    second_profile.maximum_local_displacement,
                    rtol=0.0,
                    atol=tolerance,
                )
            ),
            maximum_cumulative_displacement_a=(
                first_profile.maximum_cumulative_displacement
            ),
            maximum_cumulative_displacement_b=(
                second_profile.maximum_cumulative_displacement
            ),
            intermediate_relational_sequences_equal=intermediate_equal,
        )

    return comparisons


def compare_forward_reverse(
    forward: TemporalTrajectory,
    reverse: TemporalTrajectory,
) -> Mapping[str, ReversalComparison]:
    """Test whether reverse local displacements invert the forward sequence."""

    if reverse.states != tuple(reversed(forward.states)):
        raise ValueError("Reverse trajectory must exactly reverse the states.")

    comparisons: dict[str, ReversalComparison] = {}
    for geometry_id in SUPPORTED_GEOMETRIES:
        forward_profile = forward.geometries[geometry_id]
        reverse_profile = reverse.geometries[geometry_id]
        reverse_in_forward_order = tuple(
            reversed(reverse_profile.local_displacements)
        )
        differences = np.abs(
            np.asarray(forward_profile.local_displacements)
            - np.asarray(reverse_in_forward_order)
        )
        tolerance = GEOMETRY_TOLERANCES[geometry_id]
        maximum_discrepancy = (
            float(np.max(differences))
            if differences.size
            else 0.0
        )

        comparisons[geometry_id] = ReversalComparison(
            geometry_id=geometry_id,
            forward_sequence=forward_profile.local_displacements,
            reverse_sequence=reverse_profile.local_displacements,
            reverse_sequence_in_forward_order=reverse_in_forward_order,
            sequences_match=bool(
                np.allclose(
                    forward_profile.local_displacements,
                    reverse_in_forward_order,
                    rtol=0.0,
                    atol=tolerance,
                )
            ),
            path_lengths_match=bool(
                np.isclose(
                    forward_profile.path_length,
                    reverse_profile.path_length,
                    rtol=0.0,
                    atol=tolerance,
                )
            ),
            maximum_discrepancy=maximum_discrepancy,
        )

    return comparisons


def analyze_component_permutation_trajectory(
    name: str,
    initial_state: Sequence[int],
    permutations: Sequence[Sequence[int]],
) -> RepresentationControlTrajectory:
    """Measure a trajectory generated only by component-index permutations."""

    initial = _validate_trajectory([initial_state])[0]
    states = [initial]
    validated_permutations: list[Permutation] = []

    for permutation in permutations:
        reordered = apply_component_permutation(states[-1], permutation)
        validated_permutation = tuple(int(value) for value in permutation)
        validated_permutations.append(validated_permutation)
        states.append(tuple(int(value) for value in reordered))

    trajectory = analyze_trajectory(name, states)
    geometry_profiles: dict[str, RepresentationGeometryProfile] = {}

    for geometry_id in SUPPORTED_GEOMETRIES:
        temporal_profile = trajectory.geometries[geometry_id]
        matrices = temporal_profile.relation_matrices
        tolerance = GEOMETRY_TOLERANCES[geometry_id]
        fixed_displacements: list[float] = []
        aware_displacements: list[float] = []
        aware_cumulative: list[float] = [0.0]
        fixed_maximums: list[float] = []
        aware_maximums: list[float] = []
        fixed_equal: list[bool] = []
        aware_equal: list[bool] = []
        cumulative_transform = np.eye(len(initial), dtype=float)

        for current, following, permutation in zip(
            matrices,
            matrices[1:],
            validated_permutations,
        ):
            transform = permutation_matrix(permutation)
            expected = transform @ current @ transform.T
            fixed_comparison = compare_matrices(
                following,
                current,
                atol=tolerance,
            )
            aware_comparison = compare_matrices(
                following,
                expected,
                atol=tolerance,
            )
            fixed_displacements.append(
                fixed_comparison.frobenius_displacement
            )
            aware_displacements.append(
                aware_comparison.frobenius_displacement
            )
            fixed_maximums.append(
                fixed_comparison.maximum_elementwise_displacement
            )
            aware_maximums.append(
                aware_comparison.maximum_elementwise_displacement
            )
            fixed_equal.append(fixed_comparison.exact_equal)
            aware_equal.append(aware_comparison.exact_equal)
            cumulative_transform = transform @ cumulative_transform
            expected_from_initial = (
                cumulative_transform
                @ matrices[0]
                @ cumulative_transform.T
            )
            aware_cumulative.append(
                compare_matrices(
                    following,
                    expected_from_initial,
                    atol=tolerance,
                ).frobenius_displacement
            )

        fixed_values = np.asarray(fixed_displacements, dtype=float)
        aware_values = np.asarray(aware_displacements, dtype=float)
        fixed_zero_count = int(
            np.count_nonzero(fixed_values <= tolerance)
        )
        aware_zero_count = int(
            np.count_nonzero(aware_values <= tolerance)
        )

        geometry_profiles[geometry_id] = RepresentationGeometryProfile(
            geometry_id=geometry_id,
            fixed_index_displacements=tuple(fixed_displacements),
            permutation_aware_displacements=tuple(aware_displacements),
            fixed_index_cumulative_displacements=(
                temporal_profile.cumulative_displacements
            ),
            permutation_aware_cumulative_displacements=tuple(
                aware_cumulative
            ),
            fixed_index_maximum_elementwise=tuple(fixed_maximums),
            permutation_aware_maximum_elementwise=tuple(aware_maximums),
            fixed_index_equal=tuple(fixed_equal),
            permutation_aware_equal=tuple(aware_equal),
            fixed_index_path_length=temporal_profile.path_length,
            permutation_aware_path_length=float(np.sum(aware_values)),
            fixed_index_endpoint_displacement=(
                temporal_profile.endpoint_displacement
            ),
            permutation_aware_endpoint_displacement=aware_cumulative[-1],
            fixed_index_maximum_local_displacement=(
                temporal_profile.maximum_local_displacement
            ),
            permutation_aware_maximum_local_displacement=(
                max(aware_displacements, default=0.0)
            ),
            fixed_index_maximum_cumulative_displacement=(
                temporal_profile.maximum_cumulative_displacement
            ),
            permutation_aware_maximum_cumulative_displacement=max(
                aware_cumulative
            ),
            fixed_index_mean_local_displacement=(
                temporal_profile.mean_local_displacement
            ),
            permutation_aware_mean_local_displacement=(
                float(np.mean(aware_values))
                if aware_values.size
                else 0.0
            ),
            fixed_index_standard_deviation_local_displacement=(
                temporal_profile.standard_deviation_local_displacement
            ),
            permutation_aware_standard_deviation_local_displacement=(
                float(np.std(aware_values))
                if aware_values.size
                else 0.0
            ),
            fixed_index_zero_transitions=fixed_zero_count,
            permutation_aware_zero_transitions=aware_zero_count,
            fixed_index_nonzero_transitions=(
                len(fixed_displacements) - fixed_zero_count
            ),
            permutation_aware_nonzero_transitions=(
                len(aware_displacements) - aware_zero_count
            ),
        )

    return RepresentationControlTrajectory(
        name=name,
        trajectory=trajectory,
        permutations=tuple(validated_permutations),
        geometries=geometry_profiles,
    )
