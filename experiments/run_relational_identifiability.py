"""Run and serialize SOMS Experiment 06 relational identifiability."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict

import numpy as np

from src.concurrent_relational_geometries import GEOMETRY_SPECS
from src.isometry_controls import GEOMETRY_TOLERANCES, SUPPORTED_GEOMETRIES
from src.relational_identifiability import (
    JOINT_GEOMETRIES,
    analyze_temporal_pair,
    classify_equal_relation_pair,
    enumerate_equivalence_classes,
    find_minimal_genuine_collision,
    geometry_automorphisms,
    joint_automorphisms,
    measure_cross_geometry,
)


IMPLEMENTATION_COMMIT = "pending"
STATE_VALUES = tuple(range(8))
VECTOR_LENGTH = 4

E05_V6_A = (0, 0, 1, 1, 2, 2, 3, 3)
E05_V6_B = (1, 1, 2, 2, 3, 3, 4, 4)
CANONICAL_8 = tuple(range(8))
NONUNIFORM_PERMUTATION = (2, 5, 1, 7, 0, 6, 4, 3)
CANONICAL_8_REINDEXED = tuple(
    CANONICAL_8[index]
    for index in NONUNIFORM_PERMUTATION
)
CYCLIC_SHIFTED_8 = tuple((value + 1) % 8 for value in CANONICAL_8)
DELIBERATE_COLLISION_A = (0, 0, 1, 1, 2, 2, 3, 3)
DELIBERATE_COLLISION_B = (4, 4, 5, 5, 6, 6, 7, 7)


def matrix_to_data(matrix):
    if isinstance(matrix, tuple):
        return [item.tolist() for item in matrix]
    return matrix.tolist()


def cross_geometry_data(first, second):
    measurement = measure_cross_geometry(first, second)
    return {
        "displacements": dict(measurement.displacements),
        "indistinguishable_geometries": list(
            measurement.indistinguishable_geometries
        ),
        "distinguishable_geometries": list(
            measurement.distinguishable_geometries
        ),
    }


def serialize_relationship(relationship, *, include_cross_geometry=True):
    result = {
        "first": list(relationship.first),
        "second": list(relationship.second),
        "classification": relationship.classification,
        "component_permutation": (
            list(relationship.component_permutation)
            if relationship.component_permutation is not None
            else None
        ),
        "label_automorphism": (
            list(relationship.label_automorphism)
            if relationship.label_automorphism is not None
            else None
        ),
    }
    if include_cross_geometry:
        result["cross_geometry"] = cross_geometry_data(
            relationship.first,
            relationship.second,
        )
    return result


def serialize_summary(summary):
    return {
        "representation_id": summary.representation_id,
        "vector_length": summary.vector_length,
        "total_state_vectors": summary.total_state_vectors,
        "distinct_relation_matrices": summary.distinct_relation_matrices,
        "equivalence_class_count": summary.equivalence_class_count,
        "singleton_class_count": summary.singleton_class_count,
        "singleton_fraction": summary.singleton_fraction,
        "singleton_fraction_denominator": "equivalence classes",
        "singleton_fraction_of_classes": (
            summary.singleton_fraction_of_classes
        ),
        "singleton_state_fraction": summary.singleton_state_fraction,
        "nontrivial_class_count": summary.nontrivial_class_count,
        "maximum_class_size": summary.maximum_class_size,
        "mean_class_size": summary.mean_class_size,
        "symmetry_explainable_class_count": (
            summary.symmetry_explainable_class_count
        ),
        "genuine_collision_class_count": (
            summary.genuine_collision_class_count
        ),
        "nontrivial_classes": [
            {
                "class_id": equivalence_class.class_id,
                "relation_matrix": matrix_to_data(
                    equivalence_class.relation_matrix
                ),
                "members": [
                    list(member)
                    for member in equivalence_class.members
                ],
                "size": equivalence_class.size,
                "pair_classification_counts": dict(
                    equivalence_class.pair_classification_counts
                ),
                "symmetry_explainable": (
                    equivalence_class.symmetry_explainable
                ),
                "contains_representation_collision": (
                    equivalence_class.contains_representation_collision
                ),
                "pair_relationships": [
                    serialize_relationship(relationship)
                    for relationship in equivalence_class.pair_relationships
                ],
            }
            for equivalence_class in summary.nontrivial_classes
        ],
    }


def serialize_minimal_collision(result):
    payload = {
        "representation_id": result.representation_id,
        "lengths_tested": list(result.lengths_tested),
        "genuine_collision_classes_by_length": {
            str(length): count
            for length, count in result.genuine_collision_classes_by_length.items()
        },
        "minimum_collision_length": result.minimum_collision_length,
        "first": list(result.first) if result.first is not None else None,
        "second": list(result.second) if result.second is not None else None,
        "relation_matrix_first": (
            matrix_to_data(result.relation_matrix)
            if result.relation_matrix is not None
            else None
        ),
        "pair_classification": result.pair_classification,
    }
    if result.first is not None and result.second is not None:
        representation_ids = (
            JOINT_GEOMETRIES
            if result.representation_id == "joint"
            else (result.representation_id,)
        )
        second_matrices = tuple(
            GEOMETRY_SPECS[geometry_id].relation
            for geometry_id in representation_ids
        )
        relation_matrices_second = []
        for relation in second_matrices:
            matrix = np.asarray(
                [
                    [relation(a, b) for b in result.second]
                    for a in result.second
                ],
                dtype=float,
            )
            relation_matrices_second.append(matrix.tolist())
        payload["relation_matrix_second"] = (
            relation_matrices_second
            if result.representation_id == "joint"
            else relation_matrices_second[0]
        )
        automorphisms = (
            joint_automorphisms()
            if result.representation_id == "joint"
            else geometry_automorphisms(result.representation_id)
        )
        classification = classify_equal_relation_pair(
            result.first,
            result.second,
            automorphisms,
        )
        payload["symmetry_tests"] = serialize_relationship(
            classification,
            include_cross_geometry=False,
        )
        payload["exact_relation_equality"] = bool(
            np.array_equal(
                np.asarray(payload["relation_matrix_first"]),
                np.asarray(payload["relation_matrix_second"]),
            )
        )
        payload["cross_geometry"] = cross_geometry_data(
            result.first,
            result.second,
        )
    return payload


def serialize_selected_length8_pair(name, first, second):
    geometries = {}
    for geometry_id in SUPPORTED_GEOMETRIES:
        first_matrix = np.asarray(
            [
                [GEOMETRY_SPECS[geometry_id].relation(a, b) for b in first]
                for a in first
            ],
            dtype=float,
        )
        second_matrix = np.asarray(
            [
                [GEOMETRY_SPECS[geometry_id].relation(a, b) for b in second]
                for a in second
            ],
            dtype=float,
        )
        displacement = float(np.linalg.norm(second_matrix - first_matrix))
        equivalent = displacement <= GEOMETRY_TOLERANCES[geometry_id]
        relationship = None
        if equivalent and first != second:
            relationship = serialize_relationship(
                classify_equal_relation_pair(
                    first,
                    second,
                    geometry_automorphisms(geometry_id),
                ),
                include_cross_geometry=False,
            )
        geometries[geometry_id] = {
            "equivalent": equivalent,
            "frobenius_displacement": displacement,
            "relation_matrix_first": first_matrix.tolist(),
            "relation_matrix_second": second_matrix.tolist(),
            "relationship": relationship,
        }
    return {
        "name": name,
        "first": list(first),
        "second": list(second),
        "geometries": geometries,
        "cross_geometry": cross_geometry_data(first, second),
    }


def temporal_scenarios():
    collision_a = (0, 0, 1, 1)
    collision_b = (1, 1, 2, 2)
    next_collision_a = (2, 2, 3, 3)
    next_collision_b = (3, 3, 4, 4)
    distinguishable_b = (1, 1, 2, 3)
    permutation_a = (0, 1, 2, 3)
    permutation_b = (3, 2, 1, 0)
    return {
        "collision_to_collision": {
            "transition_type": "collision -> collision",
            "states_a": [collision_a, next_collision_a],
            "states_b": [collision_b, next_collision_b],
            "correspondences": [None, None],
        },
        "collision_to_distinguishable": {
            "transition_type": "collision -> distinguishable",
            "states_a": [collision_a, collision_a],
            "states_b": [collision_b, distinguishable_b],
            "correspondences": [None, None],
        },
        "distinguishable_to_collision": {
            "transition_type": "distinguishable -> collision",
            "states_a": [collision_a, collision_a],
            "states_b": [distinguishable_b, collision_b],
            "correspondences": [None, None],
        },
        "permutation_to_collision": {
            "transition_type": "permutation -> collision",
            "states_a": [permutation_a, collision_a],
            "states_b": [permutation_b, collision_b],
            "correspondences": [(3, 2, 1, 0), None],
        },
        "mutation_to_collision": {
            "transition_type": "mutation -> collision",
            "states_a": [collision_a, collision_a],
            "states_b": [distinguishable_b, collision_b],
            "correspondences": [(0, 1, 2, 3), None],
        },
    }


def serialize_temporal_profile(profile):
    return {
        "scenario": profile.scenario,
        "intended_transition_type": profile.intended_transition_type,
        "geometry_id": profile.geometry_id,
        "instants": [
            {
                "time": instant.time,
                "state_a": list(instant.state_a),
                "state_b": list(instant.state_b),
                "relation_matrix_a": instant.relation_matrix_a.tolist(),
                "relation_matrix_b": instant.relation_matrix_b.tolist(),
                "equivalent": instant.equivalent,
                "intertrajectory_displacement": (
                    instant.intertrajectory_displacement
                ),
                "relationship": instant.relationship,
                "supplied_correspondence": (
                    list(instant.supplied_correspondence)
                    if instant.supplied_correspondence is not None
                    else None
                ),
            }
            for instant in profile.instants
        ],
        "transitions": [
            {
                "source_time": transition.source_time,
                "target_time": transition.target_time,
                "displacement_a": transition.displacement_a,
                "displacement_b": transition.displacement_b,
            }
            for transition in profile.transitions
        ],
    }


def main():
    summaries = {
        representation_id: enumerate_equivalence_classes(
            representation_id,
            VECTOR_LENGTH,
        )
        for representation_id in (*SUPPORTED_GEOMETRIES, "joint")
    }
    minimal_collisions = {
        representation_id: find_minimal_genuine_collision(
            representation_id,
            maximum_length=VECTOR_LENGTH,
        )
        for representation_id in (*SUPPORTED_GEOMETRIES, "joint")
    }

    genuine_pair_origins: dict[tuple[tuple[int, ...], tuple[int, ...]], list[dict]] = defaultdict(list)
    for representation_id, summary in summaries.items():
        for equivalence_class in summary.nontrivial_classes:
            for relationship in equivalence_class.pair_relationships:
                if relationship.classification == "representation_collision":
                    pair = (relationship.first, relationship.second)
                    genuine_pair_origins[pair].append(
                        {
                            "representation_id": representation_id,
                            "class_id": equivalence_class.class_id,
                        }
                    )

    cross_geometry_genuine_pairs = [
        {
            "first": list(first),
            "second": list(second),
            "origins": origins,
            **cross_geometry_data(first, second),
        }
        for (first, second), origins in sorted(genuine_pair_origins.items())
    ]

    selected_length8 = [
        serialize_selected_length8_pair(
            "E05_V6_collision",
            E05_V6_A,
            E05_V6_B,
        ),
        serialize_selected_length8_pair(
            "canonical_component_permutation",
            CANONICAL_8,
            CANONICAL_8_REINDEXED,
        ),
        serialize_selected_length8_pair(
            "canonical_global_cyclic_shift",
            CANONICAL_8,
            CYCLIC_SHIFTED_8,
        ),
        serialize_selected_length8_pair(
            "deliberate_half_cycle_collision_candidate",
            DELIBERATE_COLLISION_A,
            DELIBERATE_COLLISION_B,
        ),
    ]

    temporal_results = {}
    for scenario, specification in temporal_scenarios().items():
        profiles = analyze_temporal_pair(
            scenario,
            specification["transition_type"],
            specification["states_a"],
            specification["states_b"],
            correspondences=specification["correspondences"],
        )
        temporal_results[scenario] = {
            "intended_transition_type": specification["transition_type"],
            "by_geometry": {
                geometry_id: serialize_temporal_profile(profile)
                for geometry_id, profile in profiles.items()
            },
        }

    payload = {
        "experiment": "SOMS Experiment 06 — Relational Identifiability and Information Loss",
        "branch": "experiment/06-relational-identifiability",
        "base_commit": "ec224ddb5837efea6aaf258afa0c0c5d10c28984",
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "reproducibility_command": (
            "PYTHONPATH=. python3 experiments/run_relational_identifiability.py "
            "> docs/experiment_06_relational_identifiability_results.json"
        ),
        "parameters": {
            "state_values": list(STATE_VALUES),
            "vector_length": VECTOR_LENGTH,
            "state_space_size": len(STATE_VALUES) ** VECTOR_LENGTH,
            "state_space_definition": "all vectors in {0,...,7}^4",
            "deterministic": True,
        },
        "geometry_definitions": {
            geometry_id: {
                "name": GEOMETRY_SPECS[geometry_id].name,
                "available": GEOMETRY_SPECS[geometry_id].available,
                "tolerance": GEOMETRY_TOLERANCES[geometry_id],
            }
            for geometry_id in SUPPORTED_GEOMETRIES
        },
        "unavailable_geometries": {
            "G5": GEOMETRY_SPECS["G5"].unavailable_reason,
        },
        "g3_scale_control": {
            "equivalent_to": "G2",
            "scale_factor": 45.0,
            "counted_as_independent_information": False,
        },
        "joint_representation": {
            "geometries": list(JOINT_GEOMETRIES),
            "excludes": ["G3"],
            "shared_state_label_automorphism_count": len(
                joint_automorphisms()
            ),
        },
        "enumerations": {
            representation_id: serialize_summary(summary)
            for representation_id, summary in summaries.items()
        },
        "minimal_collision_search": {
            representation_id: serialize_minimal_collision(result)
            for representation_id, result in minimal_collisions.items()
        },
        "cross_geometry_genuine_collision_pairs": (
            cross_geometry_genuine_pairs
        ),
        "cross_geometry_genuine_collision_pair_count": len(
            cross_geometry_genuine_pairs
        ),
        "selected_length8_controls": selected_length8,
        "temporal_identifiability_controls": temporal_results,
        "interpretation_boundary": {
            "correspondence_is_not_identity": True,
            "relational_equivalence_does_not_establish_state_equivalence": True,
            "semantic_claims_made": False,
        },
    }

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    payload["result_sha256"] = {
        "algorithm": "SHA-256",
        "scope": "canonical compact JSON with result_sha256 omitted",
        "value": hashlib.sha256(canonical).hexdigest(),
    }
    print(json.dumps(payload, separators=(",", ":")))


if __name__ == "__main__":
    main()
