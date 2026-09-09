"""
SOMS Experiment 05: Correspondence and Relational Lineage Controls.

A correspondence permutation maps each target component index to one source
component index. With S'[i] = S[p(i)], its permutation matrix satisfies
R_expected = P R_source P.T. Fixed-index and correspondence-aware displacement
remain separate measurements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from src.isometry_controls import (
    GEOMETRY_TOLERANCES,
    IDENTITY_PERMUTATION,
    PERMUTATION_COUNT,
    SUPPORTED_GEOMETRIES,
    all_permutation_array,
    apply_component_permutation,
    compare_matrices,
    geometry_relation_matrix,
    permutation_matrix,
)


State = tuple[int, ...]
Permutation = tuple[int, ...]


@dataclass(frozen=True)
class CorrespondenceComparison:
    """Fixed and supplied-correspondence measurements for one transition."""

    geometry_id: str
    permutation: Permutation
    fixed_index_displacement: float
    correspondence_displacement: float
    displacement_removed: float
    fixed_index_exact: bool
    correspondence_exact: bool
    fixed_index_maximum_elementwise: float
    correspondence_maximum_elementwise: float


@dataclass(frozen=True)
class CorrespondenceRecovery:
    """Exhaustive correspondence-search result for one geometry."""

    geometry_id: str
    permutations_tested: int
    minimum_displacement: float
    minimizing_permutations: tuple[Permutation, ...]
    fixed_index_displacement: float
    true_permutation: Permutation | None
    true_permutation_among_minimizers: bool | None

    @property
    def minimizing_count(self) -> int:
        return len(self.minimizing_permutations)

    @property
    def unique(self) -> bool:
        return self.minimizing_count == 1

    @property
    def best_permutation(self) -> Permutation:
        return self.minimizing_permutations[0]


@dataclass(frozen=True)
class ResidualAnalysis:
    """Locations and magnitude of a correspondence-adjusted residual."""

    geometry_id: str
    permutation: Permutation
    frobenius_norm: float
    maximum_absolute_element: float
    nonzero_element_count: int
    changed_entries: tuple[tuple[int, int, float], ...]
    affected_component_pairs: tuple[tuple[int, int], ...]
    affected_components: tuple[int, ...]
    residual_matrix: np.ndarray


@dataclass(frozen=True)
class AmbiguityAnalysis:
    """Direct state and relational correspondence multiplicities."""

    geometry_id: str
    state_stabilizer_count: int
    exact_state_correspondence_count: int
    relational_minimizer_count: int
    relational_ambiguity_exceeds_state_equality: bool
    minimum_relational_displacement: float


@dataclass(frozen=True)
class CollisionComparison:
    """Fixed-index comparison of two distinct state configurations."""

    geometry_id: str
    states_equal: bool
    relation_matrices_equal: bool
    frobenius_displacement: float
    maximum_elementwise_displacement: float


@dataclass(frozen=True)
class TemporalCorrespondenceStep:
    """Known and recovered correspondence data for one temporal transition."""

    step: int
    geometry_id: str
    source_state: State
    target_state: State
    true_permutation: Permutation
    best_permutation: Permutation
    fixed_index_displacement: float
    true_correspondence_displacement: float
    best_correspondence_displacement: float
    minimizing_count: int
    true_permutation_among_minimizers: bool
    unique: bool


@dataclass(frozen=True)
class TemporalCorrespondenceProfile:
    """Geometry-specific correspondence measurements across a trajectory."""

    geometry_id: str
    steps: tuple[TemporalCorrespondenceStep, ...]
    fixed_index_path_length: float
    true_correspondence_path_length: float
    best_correspondence_path_length: float


def _validate_state(state: Sequence[int]) -> np.ndarray:
    values = np.asarray(state)
    if values.ndim != 1:
        raise ValueError("State must be one-dimensional.")
    if not np.issubdtype(values.dtype, np.integer):
        raise ValueError("State values must be integers.")
    if np.any((values < 0) | (values >= 8)):
        raise ValueError("State values must be in the range 0..7.")
    return values.astype(int, copy=False)


def _validate_states(
    source: Sequence[int],
    target: Sequence[int],
) -> tuple[np.ndarray, np.ndarray]:
    source_values = _validate_state(source)
    target_values = _validate_state(target)
    if len(source_values) != len(target_values):
        raise ValueError("Source and target states must have equal length.")
    return source_values, target_values


def _permutation_tuple(permutation: Sequence[int], size: int) -> Permutation:
    values = np.asarray(permutation)
    if values.ndim != 1 or len(values) != size:
        raise ValueError(f"Correspondence must contain exactly {size} entries.")
    if not np.issubdtype(values.dtype, np.integer):
        raise ValueError("Correspondence entries must be integers.")
    result = tuple(int(value) for value in values)
    if sorted(result) != list(range(size)):
        raise ValueError(
            f"Correspondence must contain each index 0..{size - 1} once."
        )
    return result


def apply_correspondence(
    source: Sequence[int],
    permutation: Sequence[int],
) -> np.ndarray:
    """Apply a target-index-to-source-index correspondence to a state."""

    return apply_component_permutation(source, permutation)


def apply_correspondence_and_mutations(
    source: Sequence[int],
    permutation: Sequence[int],
    mutations: Mapping[int, int] | None = None,
) -> np.ndarray:
    """Reorder source components, then set explicit target-index values."""

    target = apply_correspondence(source, permutation).copy()
    for index, value in (mutations or {}).items():
        if index < 0 or index >= len(target):
            raise ValueError("Mutation index is outside the target state.")
        if value < 0 or value >= 8:
            raise ValueError("Mutation value must be in the range 0..7.")
        target[index] = value
    return target


def compare_correspondence(
    geometry_id: str,
    source: Sequence[int],
    target: Sequence[int],
    permutation: Sequence[int],
) -> CorrespondenceComparison:
    """Measure fixed-index and supplied-correspondence displacement."""

    source_values, target_values = _validate_states(source, target)
    mapping = _permutation_tuple(permutation, len(source_values))
    source_matrix = geometry_relation_matrix(geometry_id, source_values)
    target_matrix = geometry_relation_matrix(geometry_id, target_values)
    transform = permutation_matrix(mapping)
    expected = transform @ source_matrix @ transform.T
    tolerance = GEOMETRY_TOLERANCES[geometry_id]
    fixed = compare_matrices(target_matrix, source_matrix, atol=tolerance)
    correspondence = compare_matrices(
        target_matrix,
        expected,
        atol=tolerance,
    )

    return CorrespondenceComparison(
        geometry_id=geometry_id,
        permutation=mapping,
        fixed_index_displacement=fixed.frobenius_displacement,
        correspondence_displacement=(
            correspondence.frobenius_displacement
        ),
        displacement_removed=(
            fixed.frobenius_displacement
            - correspondence.frobenius_displacement
        ),
        fixed_index_exact=fixed.exact_equal,
        correspondence_exact=correspondence.exact_equal,
        fixed_index_maximum_elementwise=(
            fixed.maximum_elementwise_displacement
        ),
        correspondence_maximum_elementwise=(
            correspondence.maximum_elementwise_displacement
        ),
    )


def recover_correspondences(
    geometry_id: str,
    source: Sequence[int],
    target: Sequence[int],
    *,
    true_permutation: Sequence[int] | None = None,
    batch_size: int = 2048,
) -> CorrespondenceRecovery:
    """Enumerate all 40,320 candidate correspondences and retain all minima."""

    source_values, target_values = _validate_states(source, target)
    if len(source_values) != 8:
        raise ValueError("Exhaustive recovery requires eight components.")
    if batch_size <= 0:
        raise ValueError("Batch size must be positive.")

    true_mapping = (
        _permutation_tuple(true_permutation, 8)
        if true_permutation is not None
        else None
    )
    source_matrix = geometry_relation_matrix(geometry_id, source_values)
    target_matrix = geometry_relation_matrix(geometry_id, target_values)
    candidates = all_permutation_array()
    tolerance = GEOMETRY_TOLERANCES[geometry_id]
    minimum = float("inf")
    minimizers: list[Permutation] = []

    for start in range(0, PERMUTATION_COUNT, batch_size):
        batch = candidates[start:start + batch_size].astype(int)
        expected = source_matrix[
            batch[:, :, None],
            batch[:, None, :],
        ]
        differences = target_matrix - expected
        displacements = np.linalg.norm(differences, axis=(1, 2))
        batch_minimum = float(np.min(displacements))

        if batch_minimum < minimum - tolerance:
            minimum = batch_minimum
            minimizers = []

        selected = np.flatnonzero(
            np.isclose(
                displacements,
                minimum,
                rtol=0.0,
                atol=tolerance,
            )
        )
        for offset in selected:
            minimizers.append(
                tuple(int(value) for value in batch[offset])
            )

    minimizer_tuple = tuple(sorted(set(minimizers)))
    fixed = compare_matrices(
        target_matrix,
        source_matrix,
        atol=tolerance,
    )

    return CorrespondenceRecovery(
        geometry_id=geometry_id,
        permutations_tested=PERMUTATION_COUNT,
        minimum_displacement=minimum,
        minimizing_permutations=minimizer_tuple,
        fixed_index_displacement=fixed.frobenius_displacement,
        true_permutation=true_mapping,
        true_permutation_among_minimizers=(
            true_mapping in minimizer_tuple
            if true_mapping is not None
            else None
        ),
    )


def analyze_residual(
    geometry_id: str,
    source: Sequence[int],
    target: Sequence[int],
    permutation: Sequence[int],
) -> ResidualAnalysis:
    """Locate nonzero entries after applying one correspondence."""

    source_values, target_values = _validate_states(source, target)
    mapping = _permutation_tuple(permutation, len(source_values))
    source_matrix = geometry_relation_matrix(geometry_id, source_values)
    target_matrix = geometry_relation_matrix(geometry_id, target_values)
    transform = permutation_matrix(mapping)
    residual = target_matrix - transform @ source_matrix @ transform.T
    tolerance = GEOMETRY_TOLERANCES[geometry_id]
    locations = np.argwhere(np.abs(residual) > tolerance)
    changed_entries = tuple(
        (int(row), int(column), float(residual[row, column]))
        for row, column in locations
    )
    affected_pairs = tuple(
        sorted(
            {
                (min(int(row), int(column)), max(int(row), int(column)))
                for row, column in locations
                if row != column
            }
        )
    )
    affected_components = tuple(
        sorted(
            {
                int(index)
                for row, column in locations
                for index in (row, column)
            }
        )
    )

    return ResidualAnalysis(
        geometry_id=geometry_id,
        permutation=mapping,
        frobenius_norm=float(np.linalg.norm(residual)),
        maximum_absolute_element=(
            float(np.max(np.abs(residual)))
            if residual.size
            else 0.0
        ),
        nonzero_element_count=len(changed_entries),
        changed_entries=changed_entries,
        affected_component_pairs=affected_pairs,
        affected_components=affected_components,
        residual_matrix=residual,
    )


def state_stabilizer(state: Sequence[int]) -> tuple[Permutation, ...]:
    """Return every p satisfying S[p] = S."""

    values = _validate_state(state)
    if len(values) != 8:
        raise ValueError("Stabilizer enumeration requires eight components.")
    candidates = all_permutation_array().astype(int)
    stable = np.all(values[candidates] == values, axis=1)
    return tuple(
        tuple(int(value) for value in candidate)
        for candidate in candidates[stable]
    )


def exact_state_correspondences(
    source: Sequence[int],
    target: Sequence[int],
) -> tuple[Permutation, ...]:
    """Return every p satisfying source[p] = target."""

    source_values, target_values = _validate_states(source, target)
    if len(source_values) != 8:
        raise ValueError("Correspondence enumeration requires eight components.")
    candidates = all_permutation_array().astype(int)
    matching = np.all(source_values[candidates] == target_values, axis=1)
    return tuple(
        tuple(int(value) for value in candidate)
        for candidate in candidates[matching]
    )


def analyze_ambiguity(
    geometry_id: str,
    source: Sequence[int],
    target: Sequence[int],
    *,
    true_permutation: Sequence[int] | None = None,
) -> AmbiguityAnalysis:
    """Compare state-level correspondence multiplicity with relational minima."""

    recovery = recover_correspondences(
        geometry_id,
        source,
        target,
        true_permutation=true_permutation,
    )
    stabilizer = state_stabilizer(source)
    exact_correspondences = exact_state_correspondences(source, target)

    return AmbiguityAnalysis(
        geometry_id=geometry_id,
        state_stabilizer_count=len(stabilizer),
        exact_state_correspondence_count=len(exact_correspondences),
        relational_minimizer_count=recovery.minimizing_count,
        relational_ambiguity_exceeds_state_equality=(
            recovery.minimizing_count > len(exact_correspondences)
        ),
        minimum_relational_displacement=(
            recovery.minimum_displacement
        ),
    )


def compare_collision(
    geometry_id: str,
    first: Sequence[int],
    second: Sequence[int],
) -> CollisionComparison:
    """Test whether distinct states have the same fixed-index relation matrix."""

    first_values, second_values = _validate_states(first, second)
    first_matrix = geometry_relation_matrix(geometry_id, first_values)
    second_matrix = geometry_relation_matrix(geometry_id, second_values)
    comparison = compare_matrices(
        first_matrix,
        second_matrix,
        atol=GEOMETRY_TOLERANCES[geometry_id],
    )
    return CollisionComparison(
        geometry_id=geometry_id,
        states_equal=bool(np.array_equal(first_values, second_values)),
        relation_matrices_equal=comparison.exact_equal,
        frobenius_displacement=comparison.frobenius_displacement,
        maximum_elementwise_displacement=(
            comparison.maximum_elementwise_displacement
        ),
    )


def analyze_temporal_correspondence(
    states: Sequence[Sequence[int]],
    true_permutations: Sequence[Sequence[int]],
) -> Mapping[str, TemporalCorrespondenceProfile]:
    """Recover correspondence independently at every temporal transition."""

    if len(states) < 2:
        raise ValueError("Temporal correspondence requires at least two states.")
    if len(true_permutations) != len(states) - 1:
        raise ValueError("One true correspondence is required per transition.")

    validated_states = tuple(
        tuple(int(value) for value in _validate_state(state))
        for state in states
    )
    if any(
        len(state) != len(validated_states[0])
        for state in validated_states
    ):
        raise ValueError("Every temporal state must have equal length.")

    profiles: dict[str, TemporalCorrespondenceProfile] = {}
    for geometry_id in SUPPORTED_GEOMETRIES:
        steps: list[TemporalCorrespondenceStep] = []
        for step, (source, target, true_permutation) in enumerate(
            zip(
                validated_states,
                validated_states[1:],
                true_permutations,
            ),
            start=1,
        ):
            true_mapping = _permutation_tuple(
                true_permutation,
                len(source),
            )
            known = compare_correspondence(
                geometry_id,
                source,
                target,
                true_mapping,
            )
            recovery = recover_correspondences(
                geometry_id,
                source,
                target,
                true_permutation=true_mapping,
            )
            steps.append(
                TemporalCorrespondenceStep(
                    step=step,
                    geometry_id=geometry_id,
                    source_state=source,
                    target_state=target,
                    true_permutation=true_mapping,
                    best_permutation=recovery.best_permutation,
                    fixed_index_displacement=(
                        known.fixed_index_displacement
                    ),
                    true_correspondence_displacement=(
                        known.correspondence_displacement
                    ),
                    best_correspondence_displacement=(
                        recovery.minimum_displacement
                    ),
                    minimizing_count=recovery.minimizing_count,
                    true_permutation_among_minimizers=bool(
                        recovery.true_permutation_among_minimizers
                    ),
                    unique=recovery.unique,
                )
            )

        profiles[geometry_id] = TemporalCorrespondenceProfile(
            geometry_id=geometry_id,
            steps=tuple(steps),
            fixed_index_path_length=sum(
                item.fixed_index_displacement
                for item in steps
            ),
            true_correspondence_path_length=sum(
                item.true_correspondence_displacement
                for item in steps
            ),
            best_correspondence_path_length=sum(
                item.best_correspondence_displacement
                for item in steps
            ),
        )

    return profiles


__all__ = [
    "AmbiguityAnalysis",
    "CollisionComparison",
    "CorrespondenceComparison",
    "CorrespondenceRecovery",
    "IDENTITY_PERMUTATION",
    "ResidualAnalysis",
    "TemporalCorrespondenceProfile",
    "TemporalCorrespondenceStep",
    "analyze_ambiguity",
    "analyze_residual",
    "analyze_temporal_correspondence",
    "apply_correspondence",
    "apply_correspondence_and_mutations",
    "compare_collision",
    "compare_correspondence",
    "exact_state_correspondences",
    "recover_correspondences",
    "state_stabilizer",
]
