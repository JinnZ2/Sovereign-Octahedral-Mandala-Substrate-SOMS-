"""
SOMS Experimental Module: Relational Persistence

This module deliberately avoids semantic claims about identity, sovereignty,
consciousness, or integration.

It measures whether relational structure is preserved across state changes.

Given two system states S_t and S_(t+1), we distinguish:

    component change
        from
    relational change

The observer does not decide what preserved relations "mean".

This is an experimental layer and should not replace or modify the historical
SOMS implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np


RelationFunction = Callable[[int, int], float]


@dataclass(frozen=True)
class PersistenceObservation:
    """Raw comparison between two system states."""

    state_distance: float
    relation_distance: float
    relation_similarity: float
    changed_components: int
    total_components: int

    @property
    def component_change_fraction(self) -> float:
        if self.total_components == 0:
            return 0.0
        return self.changed_components / self.total_components


class RelationalPersistenceObserver:
    """
    Compare relational structure between successive system states.

    The observer treats state values as observations, not identities.

    No conclusion about persistence is built into the implementation.
    """

    def __init__(
        self,
        relation: RelationFunction | None = None,
        *,
        normalize: bool = True,
    ):
        self.relation = relation or self._default_relation
        self.normalize = normalize

    @staticmethod
    def _default_relation(a: int, b: int) -> float:
        """
        Default relation: equality.

        This is intentionally weak and neutral. More meaningful SOMS
        relations can be supplied explicitly.
        """
        return 1.0 if a == b else 0.0

    @staticmethod
    def _validate_state(state: Sequence[int]) -> np.ndarray:
        values = np.asarray(state)

        if values.ndim != 1:
            raise ValueError("State must be one-dimensional.")

        return values

    def relation_matrix(
        self,
        state: Sequence[int],
    ) -> np.ndarray:
        """Construct the pairwise relational matrix for a state."""

        values = self._validate_state(state)
        n = len(values)

        matrix = np.empty((n, n), dtype=float)

        for i in range(n):
            for j in range(n):
                matrix[i, j] = self.relation(
                    int(values[i]),
                    int(values[j]),
                )

        return matrix

    @staticmethod
    def _matrix_distance(
        first: np.ndarray,
        second: np.ndarray,
    ) -> float:
        """Normalized Frobenius distance between two relation matrices."""

        if first.shape != second.shape:
            raise ValueError(
                "States must contain the same number of components."
            )

        difference = first - second
        distance = float(np.linalg.norm(difference))

        if distance == 0.0:
            return 0.0

        return distance

    def observe(
        self,
        previous: Sequence[int],
        current: Sequence[int],
    ) -> PersistenceObservation:
        """
        Compare two successive states.

        Returns measurements only. Interpretation is external.
        """

        previous_values = self._validate_state(previous)
        current_values = self._validate_state(current)

        if len(previous_values) != len(current_values):
            raise ValueError(
                "Previous and current states must have equal length."
            )

        total = len(previous_values)

        if total == 0:
            return PersistenceObservation(
                state_distance=0.0,
                relation_distance=0.0,
                relation_similarity=1.0,
                changed_components=0,
                total_components=0,
            )

        changed = int(
            np.count_nonzero(previous_values != current_values)
        )

        state_distance = float(
            np.linalg.norm(
                previous_values.astype(float)
                - current_values.astype(float)
            )
        )

        previous_relations = self.relation_matrix(previous_values)
        current_relations = self.relation_matrix(current_values)

        relation_distance = self._matrix_distance(
            previous_relations,
            current_relations,
        )

        max_relation_distance = float(
            np.linalg.norm(
                np.ones_like(previous_relations)
            )
        )

        if self.normalize and max_relation_distance > 0:
            normalized_distance = min(
                relation_distance / max_relation_distance,
                1.0,
            )
        else:
            normalized_distance = relation_distance

        relation_similarity = 1.0 - normalized_distance

        return PersistenceObservation(
            state_distance=state_distance,
            relation_distance=relation_distance,
            relation_similarity=relation_similarity,
            changed_components=changed,
            total_components=total,
        )


def octahedral_relation(a: int, b: int) -> float:
    """
    Simple SOMS-compatible relation based on octahedral state separation.

    States are represented by indices 0..7 arranged cyclically.

    This function is deliberately only a geometric relation.
    It makes no claim about what the relation represents.
    """

    a = int(a) % 8
    b = int(b) % 8

    distance = abs(a - b)
    cyclic_distance = min(distance, 8 - distance)

    return float(cyclic_distance)


def equality_relation(a: int, b: int) -> float:
    """Binary equality relation."""

    return 1.0 if int(a) == int(b) else 0.0
