"""Run and serialize SOMS Experiment 04 trajectories."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict

import numpy as np

from src.concurrent_relational_geometries import GEOMETRY_SPECS
from src.isometry_controls import GEOMETRY_TOLERANCES, SUPPORTED_GEOMETRIES
from src.temporal_relational_continuity import (
    TemporalGeometryProfile,
    analyze_component_permutation_trajectory,
    analyze_trajectory,
    compare_endpoint_equivalent_paths,
    compare_forward_reverse,
)


INITIAL = np.arange(8)
ENDPOINT = (INITIAL + 1) % 8
NONUNIFORM = np.array([2, 5, 1, 7, 0, 6, 4, 3])
CYCLIC_COMPONENT_PERMUTATION = (1, 2, 3, 4, 5, 6, 7, 0)
REVERSAL = tuple(reversed(range(8)))
PAIR_SWAPS = (1, 0, 3, 2, 5, 4, 7, 6)


def progressive_states():
    states = []
    for changed_components in range(9):
        current = INITIAL.copy()
        current[:changed_components] = (
            current[:changed_components] + 1
        ) % 8
        states.append(current)
    return states


def build_trajectories():
    t0 = analyze_trajectory(
        "T0_static_control",
        [INITIAL.copy() for _ in range(9)],
    )
    t1 = analyze_trajectory(
        "T1_cyclic_progression",
        [(INITIAL + offset) % 8 for offset in range(9)],
    )
    t2 = analyze_trajectory(
        "T2_progressive_partial",
        progressive_states(),
    )
    t3a = analyze_trajectory(
        "T3_path_a_gradual",
        progressive_states(),
    )
    t3b = analyze_trajectory(
        "T3_path_b_large_intermediate",
        [INITIAL, NONUNIFORM, ENDPOINT],
    )
    t4_forward = analyze_trajectory(
        "T4_forward",
        progressive_states(),
    )
    t4_reverse = analyze_trajectory(
        "T4_reverse",
        list(reversed(progressive_states())),
    )
    t5 = analyze_component_permutation_trajectory(
        "T5_component_reindexing",
        INITIAL,
        [CYCLIC_COMPONENT_PERMUTATION, REVERSAL, PAIR_SWAPS],
    )
    return {
        "T0": t0,
        "T1": t1,
        "T2": t2,
        "T3A": t3a,
        "T3B": t3b,
        "T4_forward": t4_forward,
        "T4_reverse": t4_reverse,
        "T5": t5.trajectory,
    }, t5


def matrix_digest(matrix):
    values = np.asarray(matrix, dtype=np.float64)
    return hashlib.sha256(values.tobytes()).hexdigest()


def serialize_profile(profile: TemporalGeometryProfile):
    return {
        "geometry_id": profile.geometry_id,
        "relation_matrices": [
            matrix.tolist()
            for matrix in profile.relation_matrices
        ],
        "relation_matrix_sha256": [
            matrix_digest(matrix)
            for matrix in profile.relation_matrices
        ],
        "local_displacements": list(profile.local_displacements),
        "cumulative_displacements": list(
            profile.cumulative_displacements
        ),
        "path_length": profile.path_length,
        "endpoint_displacement": profile.endpoint_displacement,
        "maximum_local_displacement": (
            profile.maximum_local_displacement
        ),
        "maximum_cumulative_displacement": (
            profile.maximum_cumulative_displacement
        ),
        "mean_local_displacement": profile.mean_local_displacement,
        "standard_deviation_local_displacement": (
            profile.standard_deviation_local_displacement
        ),
        "zero_displacement_transitions": (
            profile.zero_displacement_transitions
        ),
        "nonzero_displacement_transitions": (
            profile.nonzero_displacement_transitions
        ),
    }


def serialize_trajectory(trajectory):
    return {
        "name": trajectory.name,
        "states": [list(state) for state in trajectory.states],
        "state_count": len(trajectory.states),
        "transition_count": trajectory.transition_count,
        "initial_state": list(trajectory.states[0]),
        "final_state": list(trajectory.states[-1]),
        "geometries": {
            geometry_id: serialize_profile(profile)
            for geometry_id, profile in trajectory.geometries.items()
        },
    }


def main():
    trajectories, representation = build_trajectories()
    endpoint_comparison = compare_endpoint_equivalent_paths(
        trajectories["T3A"],
        trajectories["T3B"],
    )
    reversal_comparison = compare_forward_reverse(
        trajectories["T4_forward"],
        trajectories["T4_reverse"],
    )

    results = {
        "experiment": "SOMS Experiment 04 — Temporal Relational Continuity",
        "branch": "experiment/04-temporal-relational-continuity",
        "base_commit": "82da1f2",
        "supported_geometries": list(SUPPORTED_GEOMETRIES),
        "unavailable_geometries": {
            "G5": GEOMETRY_SPECS["G5"].unavailable_reason,
        },
        "geometry_tolerances": dict(GEOMETRY_TOLERANCES),
        "g3_equivalence": {
            "equivalent_to": "G2",
            "raw_scale_factor": 45.0,
            "statement": (
                "For the present pairwise metric, every G3 relation matrix "
                "and displacement is G2 multiplied by 45."
            ),
        },
        "trajectory_summaries": {
            identifier: {
                "name": trajectory.name,
                "state_count": len(trajectory.states),
                "transition_count": trajectory.transition_count,
                "initial_state": list(trajectory.states[0]),
                "final_state": list(trajectory.states[-1]),
                "same_endpoints_as": (
                    "T3B"
                    if identifier == "T3A"
                    else "T3A"
                    if identifier == "T3B"
                    else "T4_reverse"
                    if identifier == "T4_forward"
                    else "T4_forward"
                    if identifier == "T4_reverse"
                    else None
                ),
            }
            for identifier, trajectory in trajectories.items()
        },
        "trajectories": {
            identifier: serialize_trajectory(trajectory)
            for identifier, trajectory in trajectories.items()
        },
        "endpoint_equivalent_path_comparison": {
            geometry_id: asdict(comparison)
            for geometry_id, comparison in endpoint_comparison.items()
        },
        "forward_reverse_comparison": {
            geometry_id: asdict(comparison)
            for geometry_id, comparison in reversal_comparison.items()
        },
        "representation_control": {
            "name": representation.name,
            "permutations": [
                list(permutation)
                for permutation in representation.permutations
            ],
            "states": [
                list(state)
                for state in representation.trajectory.states
            ],
            "geometries": {
                geometry_id: asdict(profile)
                for geometry_id, profile in representation.geometries.items()
            },
        },
    }

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
