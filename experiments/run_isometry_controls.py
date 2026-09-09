"""Run and serialize SOMS Experiment 03 exhaustively."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from math import lcm

import numpy as np

from src.concurrent_relational_geometries import GEOMETRY_SPECS
from src.isometry_controls import (
    CYCLIC_SHIFTS,
    GEOMETRY_TOLERANCES,
    GLOBAL_CYCLIC_SHIFT,
    IDENTITY_PERMUTATION,
    PERMUTATION_COUNT,
    REVERSAL_PERMUTATION,
    SUPPORTED_GEOMETRIES,
    compare_component_permutation,
    compare_state_label_permutation,
    enumerate_component_permutations,
    enumerate_state_label_symmetries,
    evaluate_e02_cyclic_control,
    symmetry_set_comparisons,
)


TEST_VECTORS = {
    "V0_canonical": np.array([0, 1, 2, 3, 4, 5, 6, 7]),
    "V1_global_cyclic_shift": np.array([1, 2, 3, 4, 5, 6, 7, 0]),
    "V2_single_perturbation": np.array([1, 1, 2, 3, 4, 5, 6, 7]),
    "V3_multiple_perturbation": np.array([0, 2, 2, 4, 4, 6, 6, 0]),
    "V4_nonuniform_permutation": np.array([2, 5, 1, 7, 0, 6, 4, 3]),
    "V5_repeated_states": np.array([0, 0, 0, 0, 4, 4, 4, 4]),
}


def cycle_lengths(permutation):
    visited = set()
    lengths = []
    for start in range(len(permutation)):
        if start in visited:
            continue
        current = start
        length = 0
        while current not in visited:
            visited.add(current)
            current = permutation[current]
            length += 1
        lengths.append(length)
    return tuple(sorted(lengths, reverse=True))


def permutation_order(permutation):
    order = 1
    for length in cycle_lengths(permutation):
        order = lcm(order, length)
    return order


def comparison_dict(comparison):
    return asdict(comparison)


def named_permutation_metrics(geometry_id):
    return {
        "identity": comparison_dict(
            compare_state_label_permutation(
                geometry_id,
                IDENTITY_PERMUTATION,
            )
        ),
        "cyclic_shifts": [
            {
                "offset": offset,
                **comparison_dict(
                    compare_state_label_permutation(
                        geometry_id,
                        permutation,
                    )
                ),
            }
            for offset, permutation in enumerate(CYCLIC_SHIFTS)
        ],
        "reversal": comparison_dict(
            compare_state_label_permutation(
                geometry_id,
                REVERSAL_PERMUTATION,
            )
        ),
    }


def named_component_metrics(geometry_id, state):
    return {
        "identity": asdict(
            compare_component_permutation(
                geometry_id,
                state,
                IDENTITY_PERMUTATION,
            )
        ),
        "cyclic_shifts": [
            {
                "offset": offset,
                **asdict(
                    compare_component_permutation(
                        geometry_id,
                        state,
                        permutation,
                    )
                ),
            }
            for offset, permutation in enumerate(CYCLIC_SHIFTS)
        ],
        "reversal": asdict(
            compare_component_permutation(
                geometry_id,
                state,
                REVERSAL_PERMUTATION,
            )
        ),
    }


def serialize_symmetry(result):
    cycle_type_counts = Counter(
        cycle_lengths(permutation)
        for permutation in result.automorphisms
    )
    order_counts = Counter(
        permutation_order(permutation)
        for permutation in result.automorphisms
    )
    return {
        "geometry_id": result.geometry_id,
        "geometry_name": GEOMETRY_SPECS[result.geometry_id].name,
        "tolerance": GEOMETRY_TOLERANCES[result.geometry_id],
        "permutations_tested": result.permutations_tested,
        "automorphism_count": result.automorphism_count,
        "percentage_of_s8": result.percentage_of_s8,
        "identity_present": result.identity_present,
        "global_cyclic_shift_present": (
            result.global_cyclic_shift_present
        ),
        "cyclic_shift_membership": list(
            result.cyclic_shift_membership
        ),
        "cyclic_shift_count": result.cyclic_shift_count,
        "reversal_present": result.reversal_present,
        "maximum_frobenius_displacement": (
            result.maximum_frobenius_displacement
        ),
        "maximum_elementwise_displacement": (
            result.maximum_elementwise_displacement
        ),
        "cycle_type_counts": {
            "-".join(str(value) for value in key): count
            for key, count in sorted(cycle_type_counts.items())
        },
        "permutation_order_counts": {
            str(order): count
            for order, count in sorted(order_counts.items())
        },
        "automorphisms": [
            list(permutation)
            for permutation in result.automorphisms
        ],
        "named_transformations": named_permutation_metrics(
            result.geometry_id
        ),
    }


def all_geometry_intersection(symmetry_objects):
    sets = [
        set(result.automorphisms)
        for result in symmetry_objects.values()
    ]
    intersection = set.intersection(*sets)
    return {
        "count": len(intersection),
        "permutations": [
            list(permutation)
            for permutation in sorted(intersection)
        ],
    }


def main():
    symmetry_objects = {
        geometry_id: enumerate_state_label_symmetries(geometry_id)
        for geometry_id in SUPPORTED_GEOMETRIES
    }
    state_symmetries = {
        geometry_id: serialize_symmetry(result)
        for geometry_id, result in symmetry_objects.items()
    }

    component_results = {}
    component_named_controls = {}
    for vector_name, state in TEST_VECTORS.items():
        component_results[vector_name] = {}
        component_named_controls[vector_name] = {}
        for geometry_id in SUPPORTED_GEOMETRIES:
            component_results[vector_name][geometry_id] = asdict(
                enumerate_component_permutations(
                    geometry_id,
                    vector_name,
                    state,
                )
            )
            component_named_controls[vector_name][geometry_id] = (
                named_component_metrics(geometry_id, state)
            )

    e02_control = {
        geometry_id: asdict(evaluate_e02_cyclic_control(geometry_id))
        for geometry_id in SUPPORTED_GEOMETRIES
    }

    results = {
        "experiment": "SOMS Experiment 03 — Isometry and Representation Controls",
        "branch": "experiment/03-isometry-representation-controls",
        "baseline_commits": {
            "experiment_01": "eb57c6d430f176bf762a8a760c9fa3321e6e71fd",
            "experiment_02": "4feb9e80bb8db8f07b5836c1898af1d46b1e3577",
        },
        "state_count": 8,
        "permutations_per_enumeration": PERMUTATION_COUNT,
        "supported_geometries": list(SUPPORTED_GEOMETRIES),
        "unavailable_geometries": {
            "G5": GEOMETRY_SPECS["G5"].unavailable_reason,
        },
        "tolerances": dict(GEOMETRY_TOLERANCES),
        "test_vectors": {
            name: state.tolist()
            for name, state in TEST_VECTORS.items()
        },
        "evaluation_totals": {
            "state_label_permutations": (
                len(SUPPORTED_GEOMETRIES) * PERMUTATION_COUNT
            ),
            "component_index_permutations": (
                len(SUPPORTED_GEOMETRIES)
                * len(TEST_VECTORS)
                * PERMUTATION_COUNT
            ),
        },
        "state_label_symmetries": state_symmetries,
        "symmetry_set_comparisons": symmetry_set_comparisons(
            symmetry_objects
        ),
        "all_geometry_symmetry_intersection": (
            all_geometry_intersection(symmetry_objects)
        ),
        "component_permutation_results": component_results,
        "component_named_controls": component_named_controls,
        "e02_global_cyclic_control": e02_control,
    }

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
