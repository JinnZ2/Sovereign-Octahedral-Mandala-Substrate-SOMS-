"""
SOMS Experiment 03: Isometry and Representation Controls.

This module separates transformations of state labels from permutations of
component indices. It enumerates all 8! permutations without combining the
available relational geometries into a single score.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations, permutations
from math import factorial
from typing import Mapping, Sequence

import numpy as np

from src.concurrent_relational_geometries import (
    GEOMETRY_SPECS,
    RelationFunction,
)


STATE_COUNT = 8
PERMUTATION_COUNT = factorial(STATE_COUNT)
SUPPORTED_GEOMETRIES = tuple(
    identifier
    for identifier in ("G1", "G2", "G3", "G4", "G6")
    if GEOMETRY_SPECS[identifier].available
)
GEOMETRY_TOLERANCES: Mapping[str, float] = {
    "G1": 0.0,
    "G2": 0.0,
    "G3": 1e-12,
    "G4": 0.0,
    "G6": 0.0,
}

IDENTITY_PERMUTATION = tuple(range(STATE_COUNT))
GLOBAL_CYCLIC_SHIFT = tuple(
    (state + 1) % STATE_COUNT
    for state in range(STATE_COUNT)
)
REVERSAL_PERMUTATION = tuple(reversed(range(STATE_COUNT)))
CYCLIC_SHIFTS = tuple(
    tuple(
        (state + offset) % STATE_COUNT
        for state in range(STATE_COUNT)
    )
    for offset in range(STATE_COUNT)
)


@dataclass(frozen=True)
class MatrixComparison:
    """Exactness and displacement between two relation matrices."""

    exact_equal: bool
    frobenius_displacement: float
    maximum_elementwise_displacement: float


@dataclass(frozen=True)
class ComponentPermutationComparison:
    """Fixed-index and permutation-aware views of one reordering."""

    fixed_index: MatrixComparison
    permutation_aware: MatrixComparison


@dataclass(frozen=True)
class SymmetryEnumeration:
    """Exhaustive state-label symmetry result for one geometry."""

    geometry_id: str
    permutations_tested: int
    automorphisms: tuple[tuple[int, ...], ...]
    percentage_of_s8: float
    identity_present: bool
    global_cyclic_shift_present: bool
    cyclic_shift_membership: tuple[bool, ...]
    reversal_present: bool
    maximum_frobenius_displacement: float
    maximum_elementwise_displacement: float

    @property
    def automorphism_count(self) -> int:
        return len(self.automorphisms)

    @property
    def cyclic_shift_count(self) -> int:
        return sum(self.cyclic_shift_membership)


@dataclass(frozen=True)
class ComponentEnumeration:
    """Exhaustive component-index permutation result."""

    geometry_id: str
    vector_name: str
    permutations_tested: int
    fixed_index_equal_count: int
    permutation_aware_equal_count: int
    fixed_frobenius_minimum: float
    fixed_frobenius_maximum: float
    fixed_frobenius_mean: float
    fixed_maximum_elementwise_displacement: float
    permutation_aware_frobenius_maximum: float
    permutation_aware_maximum_elementwise_displacement: float


@dataclass(frozen=True)
class E02CyclicControl:
    """State-label and component-index controls for the E02 cyclic result."""

    geometry_id: str
    state_label: MatrixComparison
    component_fixed_index: MatrixComparison
    component_permutation_aware: MatrixComparison
    classification: str


def _validate_state(state: Sequence[int]) -> np.ndarray:
    values = np.asarray(state)

    if values.ndim != 1:
        raise ValueError("State must be one-dimensional.")
    if not np.issubdtype(values.dtype, np.integer):
        raise ValueError("State values must be integers.")
    if np.any((values < 0) | (values >= STATE_COUNT)):
        raise ValueError("State values must be in the range 0..7.")

    return values.astype(int, copy=False)


def _validate_permutation(
    permutation: Sequence[int],
    size: int,
) -> np.ndarray:
    values = np.asarray(permutation)

    if values.ndim != 1 or len(values) != size:
        raise ValueError(f"Permutation must contain exactly {size} entries.")
    if not np.issubdtype(values.dtype, np.integer):
        raise ValueError("Permutation entries must be integers.")
    if sorted(int(value) for value in values) != list(range(size)):
        raise ValueError(f"Permutation must contain each index 0..{size - 1} once.")

    return values.astype(int, copy=False)


def _geometry_relation(geometry_id: str) -> RelationFunction:
    if geometry_id not in GEOMETRY_SPECS:
        raise KeyError(f"Unknown geometry: {geometry_id}")

    specification = GEOMETRY_SPECS[geometry_id]
    if specification.relation is None:
        raise ValueError(
            f"{geometry_id} is unavailable: {specification.unavailable_reason}"
        )

    return specification.relation


def relation_matrix(
    state: Sequence[int],
    relation: RelationFunction,
) -> np.ndarray:
    """Build a pairwise relation matrix for an arbitrary valid state vector."""

    values = _validate_state(state)
    matrix = np.empty((len(values), len(values)), dtype=float)

    for row, first in enumerate(values):
        for column, second in enumerate(values):
            matrix[row, column] = relation(int(first), int(second))

    return matrix


def geometry_relation_matrix(
    geometry_id: str,
    state: Sequence[int],
) -> np.ndarray:
    """Build a relation matrix using one supported Experiment 02 geometry."""

    return relation_matrix(state, _geometry_relation(geometry_id))


def compare_matrices(
    first: np.ndarray,
    second: np.ndarray,
    *,
    atol: float = 0.0,
) -> MatrixComparison:
    """Compare matrices exactly or with an explicit absolute tolerance."""

    first_values = np.asarray(first, dtype=float)
    second_values = np.asarray(second, dtype=float)

    if first_values.shape != second_values.shape:
        raise ValueError("Matrices must have equal shape.")
    if atol < 0.0:
        raise ValueError("Absolute tolerance must be nonnegative.")

    difference = first_values - second_values
    absolute_difference = np.abs(difference)

    if atol == 0.0:
        exact_equal = bool(np.array_equal(first_values, second_values))
    else:
        exact_equal = bool(
            np.allclose(first_values, second_values, rtol=0.0, atol=atol)
        )

    return MatrixComparison(
        exact_equal=exact_equal,
        frobenius_displacement=float(np.linalg.norm(difference)),
        maximum_elementwise_displacement=(
            float(np.max(absolute_difference))
            if absolute_difference.size
            else 0.0
        ),
    )


def apply_state_label_permutation(
    state: Sequence[int],
    permutation: Sequence[int],
) -> np.ndarray:
    """Apply p(label) to every state value while retaining component indices."""

    values = _validate_state(state)
    mapping = _validate_permutation(permutation, STATE_COUNT)
    return mapping[values]


def apply_component_permutation(
    state: Sequence[int],
    permutation: Sequence[int],
) -> np.ndarray:
    """Return S' with S'[i] = S[p(i)]."""

    values = _validate_state(state)
    ordering = _validate_permutation(permutation, len(values))
    return values[ordering]


def permutation_matrix(permutation: Sequence[int]) -> np.ndarray:
    """Construct P such that reordered_vector = P @ original_vector."""

    ordering = _validate_permutation(permutation, len(permutation))
    matrix = np.zeros((len(ordering), len(ordering)), dtype=float)
    matrix[np.arange(len(ordering)), ordering] = 1.0
    return matrix


def compare_state_label_permutation(
    geometry_id: str,
    permutation: Sequence[int],
) -> MatrixComparison:
    """Compare R[a,b] with R[p(a),p(b)] over the complete state space."""

    mapping = _validate_permutation(permutation, STATE_COUNT)
    original = geometry_relation_matrix(geometry_id, range(STATE_COUNT))
    transformed = original[np.ix_(mapping, mapping)]
    return compare_matrices(
        original,
        transformed,
        atol=GEOMETRY_TOLERANCES[geometry_id],
    )


def is_state_label_isometry(
    geometry_id: str,
    permutation: Sequence[int],
) -> bool:
    """Return whether a state-label permutation preserves every relation."""

    return compare_state_label_permutation(
        geometry_id,
        permutation,
    ).exact_equal


def compare_component_permutation(
    geometry_id: str,
    state: Sequence[int],
    permutation: Sequence[int],
) -> ComponentPermutationComparison:
    """Compare a component reordering at fixed and permutation-aware indices."""

    values = _validate_state(state)
    ordering = _validate_permutation(permutation, len(values))
    original = geometry_relation_matrix(geometry_id, values)
    reordered = apply_component_permutation(values, ordering)
    transformed = geometry_relation_matrix(geometry_id, reordered)
    transform = permutation_matrix(ordering)
    expected_reindexing = transform @ original @ transform.T
    tolerance = GEOMETRY_TOLERANCES[geometry_id]

    return ComponentPermutationComparison(
        fixed_index=compare_matrices(
            transformed,
            original,
            atol=tolerance,
        ),
        permutation_aware=compare_matrices(
            transformed,
            expected_reindexing,
            atol=tolerance,
        ),
    )


@lru_cache(maxsize=1)
def all_permutation_array() -> np.ndarray:
    """Return all 8! permutations in deterministic lexicographic order."""

    values = np.fromiter(
        (
            value
            for permutation in permutations(range(STATE_COUNT))
            for value in permutation
        ),
        dtype=np.int8,
        count=PERMUTATION_COUNT * STATE_COUNT,
    ).reshape(PERMUTATION_COUNT, STATE_COUNT)
    values.setflags(write=False)
    return values


def _batch_equal(differences: np.ndarray, atol: float) -> np.ndarray:
    axes = tuple(range(1, differences.ndim))
    if atol == 0.0:
        return np.all(differences == 0.0, axis=axes)
    return np.all(np.abs(differences) <= atol, axis=axes)


def enumerate_state_label_symmetries(
    geometry_id: str,
    *,
    batch_size: int = 2048,
) -> SymmetryEnumeration:
    """Exhaustively test all 40,320 state-label permutations."""

    if batch_size <= 0:
        raise ValueError("Batch size must be positive.")

    original = geometry_relation_matrix(geometry_id, range(STATE_COUNT))
    all_permutations = all_permutation_array()
    tolerance = GEOMETRY_TOLERANCES[geometry_id]
    automorphisms: list[tuple[int, ...]] = []
    maximum_frobenius = 0.0
    maximum_elementwise = 0.0

    for start in range(0, PERMUTATION_COUNT, batch_size):
        batch = all_permutations[start:start + batch_size].astype(int)
        transformed = original[
            batch[:, :, None],
            batch[:, None, :],
        ]
        differences = transformed - original
        equal = _batch_equal(differences, tolerance)

        for offset in np.flatnonzero(equal):
            automorphisms.append(
                tuple(int(value) for value in batch[offset])
            )

        frobenius = np.linalg.norm(differences, axis=(1, 2))
        maximum_frobenius = max(
            maximum_frobenius,
            float(np.max(frobenius)),
        )
        maximum_elementwise = max(
            maximum_elementwise,
            float(np.max(np.abs(differences))),
        )

    automorphism_tuple = tuple(automorphisms)
    automorphism_set = set(automorphism_tuple)

    return SymmetryEnumeration(
        geometry_id=geometry_id,
        permutations_tested=PERMUTATION_COUNT,
        automorphisms=automorphism_tuple,
        percentage_of_s8=(
            len(automorphism_tuple) / PERMUTATION_COUNT * 100.0
        ),
        identity_present=IDENTITY_PERMUTATION in automorphism_set,
        global_cyclic_shift_present=(
            GLOBAL_CYCLIC_SHIFT in automorphism_set
        ),
        cyclic_shift_membership=tuple(
            shift in automorphism_set
            for shift in CYCLIC_SHIFTS
        ),
        reversal_present=REVERSAL_PERMUTATION in automorphism_set,
        maximum_frobenius_displacement=maximum_frobenius,
        maximum_elementwise_displacement=maximum_elementwise,
    )


def enumerate_component_permutations(
    geometry_id: str,
    vector_name: str,
    state: Sequence[int],
    *,
    batch_size: int = 2048,
) -> ComponentEnumeration:
    """Exhaustively compare all 40,320 component-index permutations."""

    if batch_size <= 0:
        raise ValueError("Batch size must be positive.")

    values = _validate_state(state)
    if len(values) != STATE_COUNT:
        raise ValueError("Exhaustive component control requires eight components.")

    lookup = geometry_relation_matrix(geometry_id, range(STATE_COUNT))
    original = lookup[values[:, None], values[None, :]]
    all_permutations = all_permutation_array()
    tolerance = GEOMETRY_TOLERANCES[geometry_id]

    fixed_equal_count = 0
    aware_equal_count = 0
    fixed_frobenius_minimum = float("inf")
    fixed_frobenius_maximum = 0.0
    fixed_frobenius_sum = 0.0
    fixed_maximum_elementwise = 0.0
    aware_frobenius_maximum = 0.0
    aware_maximum_elementwise = 0.0

    for start in range(0, PERMUTATION_COUNT, batch_size):
        batch = all_permutations[start:start + batch_size].astype(int)
        reordered_states = values[batch]
        transformed = lookup[
            reordered_states[:, :, None],
            reordered_states[:, None, :],
        ]
        expected_reindexing = original[
            batch[:, :, None],
            batch[:, None, :],
        ]

        fixed_differences = transformed - original
        aware_differences = transformed - expected_reindexing
        fixed_equal = _batch_equal(fixed_differences, tolerance)
        aware_equal = _batch_equal(aware_differences, tolerance)
        fixed_frobenius = np.linalg.norm(
            fixed_differences,
            axis=(1, 2),
        )
        aware_frobenius = np.linalg.norm(
            aware_differences,
            axis=(1, 2),
        )

        fixed_equal_count += int(np.count_nonzero(fixed_equal))
        aware_equal_count += int(np.count_nonzero(aware_equal))
        fixed_frobenius_minimum = min(
            fixed_frobenius_minimum,
            float(np.min(fixed_frobenius)),
        )
        fixed_frobenius_maximum = max(
            fixed_frobenius_maximum,
            float(np.max(fixed_frobenius)),
        )
        fixed_frobenius_sum += float(np.sum(fixed_frobenius))
        fixed_maximum_elementwise = max(
            fixed_maximum_elementwise,
            float(np.max(np.abs(fixed_differences))),
        )
        aware_frobenius_maximum = max(
            aware_frobenius_maximum,
            float(np.max(aware_frobenius)),
        )
        aware_maximum_elementwise = max(
            aware_maximum_elementwise,
            float(np.max(np.abs(aware_differences))),
        )

    return ComponentEnumeration(
        geometry_id=geometry_id,
        vector_name=vector_name,
        permutations_tested=PERMUTATION_COUNT,
        fixed_index_equal_count=fixed_equal_count,
        permutation_aware_equal_count=aware_equal_count,
        fixed_frobenius_minimum=fixed_frobenius_minimum,
        fixed_frobenius_maximum=fixed_frobenius_maximum,
        fixed_frobenius_mean=(
            fixed_frobenius_sum / PERMUTATION_COUNT
        ),
        fixed_maximum_elementwise_displacement=(
            fixed_maximum_elementwise
        ),
        permutation_aware_frobenius_maximum=(
            aware_frobenius_maximum
        ),
        permutation_aware_maximum_elementwise_displacement=(
            aware_maximum_elementwise
        ),
    )


def symmetry_set_comparisons(
    enumerations: Mapping[str, SymmetryEnumeration],
) -> Mapping[str, Mapping[str, int | bool]]:
    """Return pairwise intersections and set differences of symmetry sets."""

    results: dict[str, Mapping[str, int | bool]] = {}
    for first_id, second_id in combinations(enumerations, 2):
        first = set(enumerations[first_id].automorphisms)
        second = set(enumerations[second_id].automorphisms)
        results[f"{first_id}:{second_id}"] = {
            "intersection": len(first & second),
            "only_first": len(first - second),
            "only_second": len(second - first),
            "equal_sets": first == second,
        }
    return results


def evaluate_e02_cyclic_control(geometry_id: str) -> E02CyclicControl:
    """Evaluate the E02 global shift as label change and component reindexing."""

    canonical = np.arange(STATE_COUNT)
    state_label = compare_state_label_permutation(
        geometry_id,
        GLOBAL_CYCLIC_SHIFT,
    )
    component = compare_component_permutation(
        geometry_id,
        canonical,
        GLOBAL_CYCLIC_SHIFT,
    )

    if state_label.exact_equal:
        classification = "state-space isometry"
        if not component.fixed_index.exact_equal:
            classification += " with a fixed-index representation effect"
    elif component.permutation_aware.exact_equal:
        classification = (
            "state-space non-isometry and component-index representation effect"
        )
    else:
        classification = "state-space non-isometry"

    return E02CyclicControl(
        geometry_id=geometry_id,
        state_label=state_label,
        component_fixed_index=component.fixed_index,
        component_permutation_aware=component.permutation_aware,
        classification=classification,
    )
