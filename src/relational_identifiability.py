"""
SOMS Experiment 06: Relational Identifiability and Information Loss.

The module enumerates bounded state spaces, groups states by exact relation
matrices, and distinguishes component reordering, state-label isometry, combined
symmetry, and representation collisions. Equality of relation matrices is not
state-vector equality.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations, product
from typing import Iterable, Mapping, Sequence

import numpy as np

from src.isometry_controls import (
    GEOMETRY_TOLERANCES,
    SUPPORTED_GEOMETRIES,
    enumerate_state_label_symmetries,
    geometry_relation_matrix,
    permutation_matrix,
)


State = tuple[int, ...]
Permutation = tuple[int, ...]
JOINT_GEOMETRIES = ("G1", "G2", "G4", "G6")
PAIR_CLASSIFICATIONS = (
    "component_permutation",
    "label_isometry",
    "component_permutation_and_label_isometry",
    "representation_collision",
)


@dataclass(frozen=True)
class PairClassification:
    """Symmetry classification for one equal-relation state pair."""

    first: State
    second: State
    classification: str
    component_permutation: Permutation | None
    label_automorphism: Permutation | None


@dataclass(frozen=True)
class EquivalenceClass:
    """One nonempty relation-matrix equivalence class."""

    class_id: str
    relation_matrix: np.ndarray | tuple[np.ndarray, ...]
    members: tuple[State, ...]
    pair_relationships: tuple[PairClassification, ...]
    pair_classification_counts: Mapping[str, int]
    symmetry_explainable: bool
    contains_representation_collision: bool

    @property
    def size(self) -> int:
        return len(self.members)


@dataclass(frozen=True)
class EnumerationSummary:
    """Complete equivalence-class enumeration for one representation."""

    representation_id: str
    vector_length: int
    total_state_vectors: int
    distinct_relation_matrices: int
    equivalence_class_count: int
    singleton_class_count: int
    singleton_fraction: float
    singleton_fraction_of_classes: float
    singleton_state_fraction: float
    nontrivial_class_count: int
    maximum_class_size: int
    mean_class_size: float
    symmetry_explainable_class_count: int
    genuine_collision_class_count: int
    classes: tuple[EquivalenceClass, ...]

    @property
    def nontrivial_classes(self) -> tuple[EquivalenceClass, ...]:
        return tuple(item for item in self.classes if item.size > 1)


@dataclass(frozen=True)
class MinimalCollisionResult:
    """Smallest tested length with a genuine representation collision."""

    representation_id: str
    lengths_tested: tuple[int, ...]
    genuine_collision_classes_by_length: Mapping[int, int]
    minimum_collision_length: int | None
    first: State | None
    second: State | None
    relation_matrix: np.ndarray | tuple[np.ndarray, ...] | None
    pair_classification: str | None


@dataclass(frozen=True)
class CrossGeometryMeasurement:
    """Fixed-index separation of one state pair under all geometries."""

    first: State
    second: State
    displacements: Mapping[str, float]
    indistinguishable_geometries: tuple[str, ...]
    distinguishable_geometries: tuple[str, ...]


@dataclass(frozen=True)
class TemporalInstant:
    """Instantaneous relation comparison for one pair of state sequences."""

    time: int
    state_a: State
    state_b: State
    relation_matrix_a: np.ndarray
    relation_matrix_b: np.ndarray
    equivalent: bool
    intertrajectory_displacement: float
    relationship: str | None
    supplied_correspondence: Permutation | None
    correspondence_validated: bool | None
    correspondence_aware_displacement: float | None
    correspondence_aware_equivalent: bool | None


@dataclass(frozen=True)
class TemporalTransition:
    """Within-sequence displacement from one time to the next."""

    source_time: int
    target_time: int
    displacement_a: float
    displacement_b: float


@dataclass(frozen=True)
class TemporalIdentifiabilityProfile:
    """One paired trajectory under one relational geometry."""

    scenario: str
    intended_transition_type: str
    geometry_id: str
    instants: tuple[TemporalInstant, ...]
    transitions: tuple[TemporalTransition, ...]


def enumerate_states(
    vector_length: int,
    *,
    state_count: int = 8,
) -> tuple[State, ...]:
    """Enumerate every bounded state vector in lexicographic order."""

    if vector_length <= 0:
        raise ValueError("Vector length must be positive.")
    if state_count <= 0:
        raise ValueError("State count must be positive.")
    return tuple(product(range(state_count), repeat=vector_length))


def relation_matrix_key(matrix: np.ndarray, *, atol: float = 0.0) -> tuple:
    """Return a deterministic exact or tolerance-normalized matrix key."""

    values = np.asarray(matrix, dtype=float)
    if atol < 0.0:
        raise ValueError("Absolute tolerance must be nonnegative.")
    if atol == 0.0:
        return tuple(float(value) for value in values.ravel())
    quantized = np.rint(values / atol).astype(np.int64)
    return tuple(int(value) for value in quantized.ravel())


@lru_cache(maxsize=None)
def geometry_automorphisms(geometry_id: str) -> tuple[Permutation, ...]:
    """Return the validated E03 state-label automorphism group."""

    return enumerate_state_label_symmetries(geometry_id).automorphisms


@lru_cache(maxsize=1)
def joint_automorphisms() -> tuple[Permutation, ...]:
    """Return state-label automorphisms shared by all joint geometries."""

    groups = [set(geometry_automorphisms(item)) for item in JOINT_GEOMETRIES]
    return tuple(sorted(set.intersection(*groups)))


def _component_mapping(first: State, second: State) -> Permutation | None:
    """Find one p satisfying second[i] = first[p(i)], if one exists."""

    if sorted(first) != sorted(second):
        return None
    available: dict[int, list[int]] = defaultdict(list)
    for index, value in enumerate(first):
        available[value].append(index)
    for indices in available.values():
        indices.reverse()
    return tuple(available[value].pop() for value in second)


def _label_mapping(
    first: State,
    second: State,
    automorphisms: Sequence[Permutation],
) -> Permutation | None:
    for automorphism in automorphisms:
        if tuple(automorphism[value] for value in first) == second:
            return automorphism
    return None


def _combined_label_mapping(
    first: State,
    second: State,
    automorphisms: Sequence[Permutation],
) -> Permutation | None:
    target_multiset = sorted(second)
    for automorphism in automorphisms:
        transformed = tuple(automorphism[value] for value in first)
        if sorted(transformed) == target_multiset:
            return automorphism
    return None


def classify_equal_relation_pair(
    first: Sequence[int],
    second: Sequence[int],
    automorphisms: Sequence[Permutation],
) -> PairClassification:
    """Classify a distinct equal-relation pair without semantic inference."""

    first_state = tuple(int(value) for value in first)
    second_state = tuple(int(value) for value in second)
    if first_state == second_state:
        raise ValueError("Pair classification requires distinct states.")

    component = _component_mapping(first_state, second_state)
    if component is not None:
        return PairClassification(
            first=first_state,
            second=second_state,
            classification="component_permutation",
            component_permutation=component,
            label_automorphism=None,
        )

    label = _label_mapping(first_state, second_state, automorphisms)
    if label is not None:
        return PairClassification(
            first=first_state,
            second=second_state,
            classification="label_isometry",
            component_permutation=None,
            label_automorphism=label,
        )

    combined_label = _combined_label_mapping(
        first_state,
        second_state,
        automorphisms,
    )
    if combined_label is not None:
        transformed = tuple(combined_label[value] for value in first_state)
        return PairClassification(
            first=first_state,
            second=second_state,
            classification="component_permutation_and_label_isometry",
            component_permutation=_component_mapping(
                transformed,
                second_state,
            ),
            label_automorphism=combined_label,
        )

    return PairClassification(
        first=first_state,
        second=second_state,
        classification="representation_collision",
        component_permutation=None,
        label_automorphism=None,
    )


def _geometry_key(geometry_id: str, state: State) -> tuple:
    return relation_matrix_key(
        geometry_relation_matrix(geometry_id, state),
        atol=GEOMETRY_TOLERANCES[geometry_id],
    )


def _joint_key(state: State) -> tuple[tuple, ...]:
    return tuple(_geometry_key(geometry_id, state) for geometry_id in JOINT_GEOMETRIES)


def _matrix_for_representation(
    representation_id: str,
    state: State,
) -> np.ndarray | tuple[np.ndarray, ...]:
    if representation_id == "joint":
        return tuple(
            geometry_relation_matrix(geometry_id, state)
            for geometry_id in JOINT_GEOMETRIES
        )
    return geometry_relation_matrix(representation_id, state)


def _automorphisms_for_representation(
    representation_id: str,
) -> tuple[Permutation, ...]:
    if representation_id == "joint":
        return joint_automorphisms()
    return geometry_automorphisms(representation_id)


@lru_cache(maxsize=None)
def enumerate_equivalence_classes(
    representation_id: str,
    vector_length: int = 4,
) -> EnumerationSummary:
    """Enumerate and classify every class in a bounded state space."""

    if representation_id != "joint" and representation_id not in SUPPORTED_GEOMETRIES:
        raise KeyError(f"Unknown representation: {representation_id}")

    states = enumerate_states(vector_length)
    grouped: dict[tuple, list[State]] = defaultdict(list)
    key_function = _joint_key if representation_id == "joint" else (
        lambda state: _geometry_key(representation_id, state)
    )
    for state in states:
        grouped[key_function(state)].append(state)

    automorphisms = _automorphisms_for_representation(representation_id)
    classes: list[EquivalenceClass] = []
    symmetry_explainable_count = 0
    genuine_count = 0

    sorted_groups = sorted(grouped.values(), key=lambda members: members[0])
    for index, members_list in enumerate(sorted_groups):
        members = tuple(members_list)
        relationships = tuple(
            classify_equal_relation_pair(first, second, automorphisms)
            for first, second in combinations(members, 2)
        )
        counts = Counter(item.classification for item in relationships)
        complete_counts = {
            category: counts.get(category, 0)
            for category in PAIR_CLASSIFICATIONS
        }
        contains_genuine = complete_counts["representation_collision"] > 0
        symmetry_explainable = len(members) > 1 and not contains_genuine
        if symmetry_explainable:
            symmetry_explainable_count += 1
        if contains_genuine:
            genuine_count += 1
        classes.append(
            EquivalenceClass(
                class_id=f"{representation_id}-n{vector_length}-{index:04d}",
                relation_matrix=_matrix_for_representation(
                    representation_id,
                    members[0],
                ),
                members=members,
                pair_relationships=relationships,
                pair_classification_counts=complete_counts,
                symmetry_explainable=symmetry_explainable,
                contains_representation_collision=contains_genuine,
            )
        )

    class_sizes = np.asarray([item.size for item in classes], dtype=float)
    singleton_count = int(np.count_nonzero(class_sizes == 1))
    total = len(states)
    return EnumerationSummary(
        representation_id=representation_id,
        vector_length=vector_length,
        total_state_vectors=total,
        distinct_relation_matrices=len(classes),
        equivalence_class_count=len(classes),
        singleton_class_count=singleton_count,
        singleton_fraction=singleton_count / len(classes),
        singleton_fraction_of_classes=singleton_count / len(classes),
        singleton_state_fraction=singleton_count / total,
        nontrivial_class_count=len(classes) - singleton_count,
        maximum_class_size=int(np.max(class_sizes)),
        mean_class_size=float(total / len(classes)),
        symmetry_explainable_class_count=symmetry_explainable_count,
        genuine_collision_class_count=genuine_count,
        classes=tuple(classes),
    )


def find_minimal_genuine_collision(
    representation_id: str,
    *,
    maximum_length: int = 4,
) -> MinimalCollisionResult:
    """Exhaustively search lengths 1..maximum_length for a genuine collision."""

    if maximum_length <= 0:
        raise ValueError("Maximum length must be positive.")
    counts: dict[int, int] = {}
    first_collision: tuple[State, State, object] | None = None

    for vector_length in range(1, maximum_length + 1):
        summary = enumerate_equivalence_classes(
            representation_id,
            vector_length,
        )
        counts[vector_length] = summary.genuine_collision_class_count
        if first_collision is None:
            for equivalence_class in summary.nontrivial_classes:
                for relationship in equivalence_class.pair_relationships:
                    if relationship.classification == "representation_collision":
                        first_collision = (
                            relationship.first,
                            relationship.second,
                            equivalence_class.relation_matrix,
                        )
                        break
                if first_collision is not None:
                    break

    if first_collision is None:
        return MinimalCollisionResult(
            representation_id=representation_id,
            lengths_tested=tuple(range(1, maximum_length + 1)),
            genuine_collision_classes_by_length=counts,
            minimum_collision_length=None,
            first=None,
            second=None,
            relation_matrix=None,
            pair_classification=None,
        )

    first, second, matrix = first_collision
    minimum_length = next(length for length, count in counts.items() if count > 0)
    return MinimalCollisionResult(
        representation_id=representation_id,
        lengths_tested=tuple(range(1, maximum_length + 1)),
        genuine_collision_classes_by_length=counts,
        minimum_collision_length=minimum_length,
        first=first,
        second=second,
        relation_matrix=matrix,
        pair_classification="representation_collision",
    )


def measure_cross_geometry(
    first: Sequence[int],
    second: Sequence[int],
) -> CrossGeometryMeasurement:
    """Measure one fixed-index pair under every supported geometry."""

    first_state = tuple(int(value) for value in first)
    second_state = tuple(int(value) for value in second)
    if len(first_state) != len(second_state):
        raise ValueError("States must have equal length.")
    displacements: dict[str, float] = {}
    indistinguishable: list[str] = []
    distinguishable: list[str] = []
    for geometry_id in SUPPORTED_GEOMETRIES:
        difference = (
            geometry_relation_matrix(geometry_id, second_state)
            - geometry_relation_matrix(geometry_id, first_state)
        )
        displacement = float(np.linalg.norm(difference))
        displacements[geometry_id] = displacement
        if displacement <= GEOMETRY_TOLERANCES[geometry_id]:
            indistinguishable.append(geometry_id)
        else:
            distinguishable.append(geometry_id)
    return CrossGeometryMeasurement(
        first=first_state,
        second=second_state,
        displacements=displacements,
        indistinguishable_geometries=tuple(indistinguishable),
        distinguishable_geometries=tuple(distinguishable),
    )


def analyze_temporal_pair(
    scenario: str,
    intended_transition_type: str,
    states_a: Sequence[Sequence[int]],
    states_b: Sequence[Sequence[int]],
    *,
    correspondences: Sequence[Sequence[int] | None] | None = None,
) -> Mapping[str, TemporalIdentifiabilityProfile]:
    """Compare paired trajectories, validating optional A-to-B correspondences."""

    first_trajectory = tuple(tuple(int(value) for value in state) for state in states_a)
    second_trajectory = tuple(tuple(int(value) for value in state) for state in states_b)
    if len(first_trajectory) != len(second_trajectory) or not first_trajectory:
        raise ValueError("Paired trajectories must have equal nonzero length.")
    if any(len(a) != len(b) for a, b in zip(first_trajectory, second_trajectory)):
        raise ValueError("Paired states must have equal lengths.")
    supplied = tuple(correspondences or [None] * len(first_trajectory))
    if len(supplied) != len(first_trajectory):
        raise ValueError("One optional correspondence is required per instant.")
    validated_correspondences: list[Permutation | None] = []
    for state, correspondence in zip(first_trajectory, supplied):
        if correspondence is None:
            validated_correspondences.append(None)
            continue
        mapping = tuple(int(value) for value in correspondence)
        if len(mapping) != len(state) or sorted(mapping) != list(range(len(state))):
            raise ValueError(
                "Each supplied correspondence must be a component permutation."
            )
        validated_correspondences.append(mapping)

    profiles: dict[str, TemporalIdentifiabilityProfile] = {}
    for geometry_id in SUPPORTED_GEOMETRIES:
        automorphisms = geometry_automorphisms(geometry_id)
        matrices_a = tuple(
            geometry_relation_matrix(geometry_id, state)
            for state in first_trajectory
        )
        matrices_b = tuple(
            geometry_relation_matrix(geometry_id, state)
            for state in second_trajectory
        )
        instants: list[TemporalInstant] = []
        for time, (state_a, state_b, matrix_a, matrix_b, correspondence) in enumerate(
            zip(
                first_trajectory,
                second_trajectory,
                matrices_a,
                matrices_b,
                validated_correspondences,
            )
        ):
            displacement = float(np.linalg.norm(matrix_b - matrix_a))
            equivalent = displacement <= GEOMETRY_TOLERANCES[geometry_id]
            correspondence_displacement = None
            correspondence_equivalent = None
            if correspondence is not None:
                transform = permutation_matrix(correspondence)
                expected_b = transform @ matrix_a @ transform.T
                correspondence_displacement = float(
                    np.linalg.norm(matrix_b - expected_b)
                )
                correspondence_equivalent = bool(
                    correspondence_displacement
                    <= GEOMETRY_TOLERANCES[geometry_id]
                )
            relationship = None
            if state_a != state_b and equivalent:
                relationship = classify_equal_relation_pair(
                    state_a,
                    state_b,
                    automorphisms,
                ).classification
            elif state_a == state_b:
                relationship = "exact_state_equality"
            instants.append(
                TemporalInstant(
                    time=time,
                    state_a=state_a,
                    state_b=state_b,
                    relation_matrix_a=matrix_a,
                    relation_matrix_b=matrix_b,
                    equivalent=equivalent,
                    intertrajectory_displacement=displacement,
                    relationship=relationship,
                    supplied_correspondence=(
                        correspondence
                    ),
                    correspondence_validated=(
                        True if correspondence is not None else None
                    ),
                    correspondence_aware_displacement=(
                        correspondence_displacement
                    ),
                    correspondence_aware_equivalent=(
                        correspondence_equivalent
                    ),
                )
            )
        transitions = tuple(
            TemporalTransition(
                source_time=index,
                target_time=index + 1,
                displacement_a=float(
                    np.linalg.norm(matrices_a[index + 1] - matrices_a[index])
                ),
                displacement_b=float(
                    np.linalg.norm(matrices_b[index + 1] - matrices_b[index])
                ),
            )
            for index in range(len(first_trajectory) - 1)
        )
        profiles[geometry_id] = TemporalIdentifiabilityProfile(
            scenario=scenario,
            intended_transition_type=intended_transition_type,
            geometry_id=geometry_id,
            instants=tuple(instants),
            transitions=transitions,
        )
    return profiles


__all__ = [
    "CrossGeometryMeasurement",
    "EnumerationSummary",
    "EquivalenceClass",
    "JOINT_GEOMETRIES",
    "MinimalCollisionResult",
    "PAIR_CLASSIFICATIONS",
    "PairClassification",
    "TemporalIdentifiabilityProfile",
    "analyze_temporal_pair",
    "classify_equal_relation_pair",
    "enumerate_equivalence_classes",
    "enumerate_states",
    "find_minimal_genuine_collision",
    "geometry_automorphisms",
    "joint_automorphisms",
    "measure_cross_geometry",
    "relation_matrix_key",
]
