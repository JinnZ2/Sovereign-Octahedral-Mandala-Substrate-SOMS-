"""
SOMS Experiment 02: Concurrent Relational Geometries.

This module measures one state transformation under several independent
relations. It does not combine the measurements into a universal score and it
assigns no semantic meaning to relational similarity.

Experiment 01 remains the frozen measurement baseline. This module imports its
relation-matrix observer without modifying that implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Callable, Mapping, Sequence

import numpy as np

from src.geometric_state_algebra import GeometricState, OhGroup
from src.octahedral_lookup import GRAY_TRANSITION_TABLE
from src.octahedral_physics import SOMSEngine
from src.relational_persistence import (
    RelationalPersistenceObserver,
    octahedral_relation,
)


RelationFunction = Callable[[int, int], float]
GEOMETRY_ORDER = ("G1", "G2", "G3", "G4", "G5", "G6")
STATE_COUNT = 8


@dataclass(frozen=True)
class GeometrySpec:
    """Definition and availability of one independently callable geometry."""

    identifier: str
    name: str
    relation: RelationFunction | None
    source: str
    unavailable_reason: str | None = None

    @property
    def available(self) -> bool:
        return self.relation is not None


@dataclass(frozen=True)
class GeometryMeasurement:
    """One geometry's measurement for a state transformation."""

    identifier: str
    name: str
    available: bool
    displacement: float | None
    similarity: float | None
    maximum_pairwise_separation: float | None
    note: str | None = None


@dataclass(frozen=True)
class RelationalProfile:
    """Independent measurements of the same state transformation."""

    component_displacement: float
    changed_components: int
    total_components: int
    geometries: Mapping[str, GeometryMeasurement]

    @property
    def component_change_fraction(self) -> float:
        if self.total_components == 0:
            return 0.0
        return self.changed_components / self.total_components


def numeric_state_relation(a: int, b: int) -> float:
    """G1: ordinary numerical separation of integer state labels."""

    return float(abs(int(a) - int(b)))


def cyclic_octahedral_relation(a: int, b: int) -> float:
    """G2: Experiment 01's established cyclic eight-state separation."""

    return octahedral_relation(a, b)


def angular_relation(a: int, b: int) -> float:
    """G3: circular angular separation in degrees using SOMS angles."""

    angle_a = int(SOMSEngine.ANGLES[int(a)])
    angle_b = int(SOMSEngine.ANGLES[int(b)])
    raw_separation = abs(angle_a - angle_b) % 360
    return float(min(raw_separation, 360 - raw_separation))


def gray_code_relation(a: int, b: int) -> float:
    """G4: Hamming distance from the canonical SOMS Gray-code table."""

    return float(GRAY_TRANSITION_TABLE[int(a)][int(b)])


def cayley_group_relation(a: int, b: int) -> float:
    """G6: Cayley distance between existing classical-state embeddings."""

    group = OhGroup.instance()
    first = GeometricState.from_classical_state(group, int(a))
    second = GeometricState.from_classical_state(group, int(b))
    return first.cayley_distance_to(second)


MANDALA_UNAVAILABLE_REASON = (
    "MandalaMap assigns repeated state labels to cells on multiple rings. "
    "The repository does not define a unique state-to-position selection for "
    "an arbitrary state vector; choosing a ring or scale would add an "
    "unsupported assumption."
)


GEOMETRY_SPECS: Mapping[str, GeometrySpec] = {
    "G1": GeometrySpec(
        "G1",
        "Numeric state geometry",
        numeric_state_relation,
        "Integer state representation",
    ),
    "G2": GeometrySpec(
        "G2",
        "Cyclic octahedral geometry",
        cyclic_octahedral_relation,
        "src.relational_persistence.octahedral_relation",
    ),
    "G3": GeometrySpec(
        "G3",
        "Angular geometry",
        angular_relation,
        "src.octahedral_physics.SOMSEngine.ANGLES",
    ),
    "G4": GeometrySpec(
        "G4",
        "Gray-code geometry",
        gray_code_relation,
        "src.octahedral_lookup.GRAY_TRANSITION_TABLE",
    ),
    "G5": GeometrySpec(
        "G5",
        "Mandala geometry",
        None,
        "src.mandala_structure.MandalaMap",
        MANDALA_UNAVAILABLE_REASON,
    ),
    "G6": GeometrySpec(
        "G6",
        "Cayley/group geometry",
        cayley_group_relation,
        "src.geometric_state_algebra.GeometricState",
    ),
}


def _validate_state(state: Sequence[int]) -> np.ndarray:
    values = np.asarray(state)

    if values.ndim != 1:
        raise ValueError("State must be one-dimensional.")
    if not np.issubdtype(values.dtype, np.integer):
        raise ValueError("State values must be integers.")
    if np.any((values < 0) | (values >= STATE_COUNT)):
        raise ValueError("State values must be in the range 0..7.")

    return values.astype(int, copy=False)


def _maximum_pairwise_separation(relation: RelationFunction) -> float:
    return max(
        relation(first, second)
        for first in range(STATE_COUNT)
        for second in range(STATE_COUNT)
    )


def _measure_geometry(
    spec: GeometrySpec,
    previous: np.ndarray,
    current: np.ndarray,
) -> GeometryMeasurement:
    if spec.relation is None:
        return GeometryMeasurement(
            identifier=spec.identifier,
            name=spec.name,
            available=False,
            displacement=None,
            similarity=None,
            maximum_pairwise_separation=None,
            note=spec.unavailable_reason,
        )

    observer = RelationalPersistenceObserver(relation=spec.relation)
    previous_matrix = observer.relation_matrix(previous)
    current_matrix = observer.relation_matrix(current)
    displacement = observer._matrix_distance(
        previous_matrix,
        current_matrix,
    )
    maximum_separation = _maximum_pairwise_separation(spec.relation)

    if len(previous) == 0 or maximum_separation == 0.0:
        similarity = 1.0
    else:
        maximum_matrix_displacement = len(previous) * maximum_separation
        normalized_displacement = displacement / maximum_matrix_displacement
        similarity = 1.0 - min(max(normalized_displacement, 0.0), 1.0)

    return GeometryMeasurement(
        identifier=spec.identifier,
        name=spec.name,
        available=True,
        displacement=displacement,
        similarity=similarity,
        maximum_pairwise_separation=maximum_separation,
    )


def observe_relational_profile(
    previous: Sequence[int],
    current: Sequence[int],
) -> RelationalProfile:
    """Measure one transformation under every geometry independently."""

    previous_values = _validate_state(previous)
    current_values = _validate_state(current)

    if len(previous_values) != len(current_values):
        raise ValueError("Previous and current states must have equal length.")

    geometries = {
        identifier: _measure_geometry(
            GEOMETRY_SPECS[identifier],
            previous_values,
            current_values,
        )
        for identifier in GEOMETRY_ORDER
    }

    component_displacement = float(
        np.linalg.norm(
            previous_values.astype(float) - current_values.astype(float)
        )
    )

    return RelationalProfile(
        component_displacement=component_displacement,
        changed_components=int(
            np.count_nonzero(previous_values != current_values)
        ),
        total_components=len(previous_values),
        geometries=geometries,
    )


def geometry_divergences(profile: RelationalProfile) -> Mapping[str, float]:
    """
    Return absolute differences between available raw displacements.

    This diagnostic is deliberately unit-dependent: the geometries measure
    label steps, cyclic steps, degrees, Gray-code bits, or Cayley steps. A
    value therefore records numerical separation between raw measurements;
    it is not a scale-independent score, error, or truth assessment.
    """

    available = [
        measurement
        for measurement in profile.geometries.values()
        if measurement.available and measurement.displacement is not None
    ]

    return {
        f"{first.identifier}:{second.identifier}": abs(
            first.displacement - second.displacement
        )
        for first, second in combinations(available, 2)
    }
