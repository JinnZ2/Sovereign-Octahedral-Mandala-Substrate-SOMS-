"""Run and serialize SOMS Experiment 05 correspondence controls."""

from __future__ import annotations

import json
from dataclasses import asdict

import numpy as np

from src.concurrent_relational_geometries import GEOMETRY_SPECS
from src.isometry_controls import (
    GEOMETRY_TOLERANCES,
    IDENTITY_PERMUTATION,
    PERMUTATION_COUNT,
    SUPPORTED_GEOMETRIES,
)
from src.relational_correspondence import (
    analyze_ambiguity,
    analyze_residual,
    analyze_temporal_correspondence,
    apply_correspondence,
    apply_correspondence_and_mutations,
    compare_collision,
    compare_correspondence,
    exact_state_correspondences,
    recover_correspondences,
    state_stabilizer,
)


CANONICAL = np.arange(8)
NONUNIFORM = (2, 5, 1, 7, 0, 6, 4, 3)
REPEATED = np.array([0, 0, 0, 0, 4, 4, 4, 4])
REPEATED_PERMUTATION = (4, 0, 5, 1, 6, 2, 7, 3)
REVERSAL = tuple(reversed(range(8)))
PAIR_SWAPS = (1, 0, 3, 2, 5, 4, 7, 6)
COLLISION_A = np.array([0, 0, 1, 1, 2, 2, 3, 3])
COLLISION_B = np.array([1, 1, 2, 2, 3, 3, 4, 4])


V1 = apply_correspondence(CANONICAL, NONUNIFORM)
V2 = apply_correspondence_and_mutations(
    CANONICAL,
    IDENTITY_PERMUTATION,
    {0: 1},
)
V3 = apply_correspondence_and_mutations(
    CANONICAL,
    NONUNIFORM,
    {0: 3},
)
V4 = apply_correspondence_and_mutations(
    CANONICAL,
    NONUNIFORM,
    {0: 3, 1: 4},
)
V5 = apply_correspondence(REPEATED, REPEATED_PERMUTATION)


CASES = {
    "V1_pure_component_permutation": {
        "source": CANONICAL,
        "target": V1,
        "true_permutation": NONUNIFORM,
        "mutations": {},
        "repeated_values": False,
        "expected_ambiguity": "geometry automorphisms may make recovery nonunique",
    },
    "V2_single_mutation": {
        "source": CANONICAL,
        "target": V2,
        "true_permutation": IDENTITY_PERMUTATION,
        "mutations": {0: 1},
        "repeated_values": True,
        "expected_ambiguity": "mutation creates a repeated state value",
    },
    "V3_permutation_plus_mutation": {
        "source": CANONICAL,
        "target": V3,
        "true_permutation": NONUNIFORM,
        "mutations": {0: 3},
        "repeated_values": True,
        "expected_ambiguity": "mutation may change the optimal correspondence set",
    },
    "V4_permutation_plus_multiple_mutations": {
        "source": CANONICAL,
        "target": V4,
        "true_permutation": NONUNIFORM,
        "mutations": {0: 3, 1: 4},
        "repeated_values": True,
        "expected_ambiguity": "multiple mutations may change the optimal correspondence set",
    },
    "V5_repeated_state_permutation": {
        "source": REPEATED,
        "target": V5,
        "true_permutation": REPEATED_PERMUTATION,
        "mutations": {},
        "repeated_values": True,
        "expected_ambiguity": "within-block permutations and relational symmetries",
    },
}


def serialize_recovery(recovery):
    return {
        "geometry_id": recovery.geometry_id,
        "permutations_tested": recovery.permutations_tested,
        "minimum_displacement": recovery.minimum_displacement,
        "minimizing_count": recovery.minimizing_count,
        "minimizing_permutations": [
            list(permutation)
            for permutation in recovery.minimizing_permutations
        ],
        "best_permutation": list(recovery.best_permutation),
        "fixed_index_displacement": recovery.fixed_index_displacement,
        "true_permutation": (
            list(recovery.true_permutation)
            if recovery.true_permutation is not None
            else None
        ),
        "true_permutation_among_minimizers": (
            recovery.true_permutation_among_minimizers
        ),
        "unique": recovery.unique,
    }


def serialize_residual(residual):
    return {
        "geometry_id": residual.geometry_id,
        "permutation": list(residual.permutation),
        "frobenius_norm": residual.frobenius_norm,
        "maximum_absolute_element": residual.maximum_absolute_element,
        "nonzero_element_count": residual.nonzero_element_count,
        "changed_entries": [
            [row, column, value]
            for row, column, value in residual.changed_entries
        ],
        "affected_component_pairs": [
            list(pair)
            for pair in residual.affected_component_pairs
        ],
        "affected_components": list(residual.affected_components),
        "residual_matrix": residual.residual_matrix.tolist(),
    }


def serialize_temporal_profile(profile):
    return {
        "geometry_id": profile.geometry_id,
        "steps": [
            {
                **asdict(step),
                "source_state": list(step.source_state),
                "target_state": list(step.target_state),
                "true_permutation": list(step.true_permutation),
                "best_permutation": list(step.best_permutation),
            }
            for step in profile.steps
        ],
        "fixed_index_path_length": profile.fixed_index_path_length,
        "true_correspondence_path_length": (
            profile.true_correspondence_path_length
        ),
        "best_correspondence_path_length": (
            profile.best_correspondence_path_length
        ),
    }


def main():
    known_correspondence_controls = {}
    recoveries = {}
    residuals = {}

    for case_name, case in CASES.items():
        known_correspondence_controls[case_name] = {}
        recoveries[case_name] = {}
        for geometry_id in SUPPORTED_GEOMETRIES:
            known_correspondence_controls[case_name][geometry_id] = asdict(
                compare_correspondence(
                    geometry_id,
                    case["source"],
                    case["target"],
                    case["true_permutation"],
                )
            )
            recoveries[case_name][geometry_id] = serialize_recovery(
                recover_correspondences(
                    geometry_id,
                    case["source"],
                    case["target"],
                    true_permutation=case["true_permutation"],
                )
            )

        if case_name in {
            "V2_single_mutation",
            "V3_permutation_plus_mutation",
            "V4_permutation_plus_multiple_mutations",
        }:
            residuals[case_name] = {}
            for geometry_id in SUPPORTED_GEOMETRIES:
                best = tuple(
                    recoveries[case_name][geometry_id]["best_permutation"]
                )
                residuals[case_name][geometry_id] = {
                    "best_correspondence": serialize_residual(
                        analyze_residual(
                            geometry_id,
                            case["source"],
                            case["target"],
                            best,
                        )
                    ),
                    "true_correspondence": serialize_residual(
                        analyze_residual(
                            geometry_id,
                            case["source"],
                            case["target"],
                            case["true_permutation"],
                        )
                    ),
                }

    ambiguity = {
        geometry_id: asdict(
            analyze_ambiguity(
                geometry_id,
                REPEATED,
                V5,
                true_permutation=REPEATED_PERMUTATION,
            )
        )
        for geometry_id in SUPPORTED_GEOMETRIES
    }

    collisions = {
        geometry_id: asdict(
            compare_collision(
                geometry_id,
                COLLISION_A,
                COLLISION_B,
            )
        )
        for geometry_id in SUPPORTED_GEOMETRIES
    }
    collision_recoveries = {
        geometry_id: serialize_recovery(
            recover_correspondences(
                geometry_id,
                COLLISION_A,
                COLLISION_B,
            )
        )
        for geometry_id in SUPPORTED_GEOMETRIES
    }

    temporal_state_1 = V1
    temporal_state_2 = apply_correspondence_and_mutations(
        temporal_state_1,
        IDENTITY_PERMUTATION,
        {0: 3},
    )
    temporal_state_3 = apply_correspondence_and_mutations(
        temporal_state_2,
        REVERSAL,
        {1: 2},
    )
    temporal_state_4 = apply_correspondence_and_mutations(
        temporal_state_3,
        PAIR_SWAPS,
        {4: 7, 6: 0},
    )
    temporal_states = [
        CANONICAL,
        temporal_state_1,
        temporal_state_2,
        temporal_state_3,
        temporal_state_4,
    ]
    temporal_true_permutations = [
        NONUNIFORM,
        IDENTITY_PERMUTATION,
        REVERSAL,
        PAIR_SWAPS,
    ]
    temporal_profiles = analyze_temporal_correspondence(
        temporal_states,
        temporal_true_permutations,
    )

    results = {
        "experiment": "SOMS Experiment 05 — Correspondence and Relational Lineage Controls",
        "branch": "experiment/05-correspondence-relational-lineage",
        "base_commit": "f2f3afe02642762b7442cbfdf266625def969b08",
        "correspondence_convention": (
            "p maps target index i to source index p(i): target[i] = source[p(i)]; "
            "P[i,p(i)] = 1"
        ),
        "supported_geometries": list(SUPPORTED_GEOMETRIES),
        "unavailable_geometries": {
            "G5": GEOMETRY_SPECS["G5"].unavailable_reason,
        },
        "geometry_tolerances": dict(GEOMETRY_TOLERANCES),
        "g3_equivalence": {
            "equivalent_to": "G2",
            "raw_scale_factor": 45.0,
        },
        "permutations_per_recovery": PERMUTATION_COUNT,
        "transformation_summary": {
            **{
                case_name: {
                    "source": case["source"].tolist(),
                    "target": case["target"].tolist(),
                    "true_permutation": list(case["true_permutation"]),
                    "mutations": {
                        str(index): value
                        for index, value in case["mutations"].items()
                    },
                    "repeated_values": case["repeated_values"],
                    "expected_ambiguity": case["expected_ambiguity"],
                    "source_stabilizer_count": len(
                        state_stabilizer(case["source"])
                    ),
                    "exact_state_correspondence_count": len(
                        exact_state_correspondences(
                            case["source"],
                            case["target"],
                        )
                    ),
                }
                for case_name, case in CASES.items()
            },
            "V6_collision_case": {
                "source": COLLISION_A.tolist(),
                "target": COLLISION_B.tolist(),
                "true_permutation": None,
                "mutations": None,
                "repeated_values": True,
                "expected_ambiguity": (
                    "distinct states can have identical relation matrices "
                    "without any exact state-vector correspondence"
                ),
                "source_stabilizer_count": len(
                    state_stabilizer(COLLISION_A)
                ),
                "exact_state_correspondence_count": len(
                    exact_state_correspondences(
                        COLLISION_A,
                        COLLISION_B,
                    )
                ),
            },
        },
        "correspondence_conditions": {
            "C0_identity": (
                "V2 uses identity correspondence with one state mutation."
            ),
            "C1_known_permutation": (
                "V1 supplies the nonuniform generating permutation."
            ),
            "C2_hidden_correct_permutation": (
                "V1, V3, and V4 enumerate all candidates while retaining the hidden true mapping for evaluation."
            ),
            "C3_ambiguous_repeated_states": (
                "V5 measures state stabilizer, exact state correspondences, and relational minimizers."
            ),
        },
        "known_correspondence_controls": known_correspondence_controls,
        "correspondence_recovery": {
            **recoveries,
            "V6_collision_case": collision_recoveries,
        },
        "mutation_residuals": residuals,
        "repeated_state_ambiguity": {
            "source": REPEATED.tolist(),
            "target": V5.tolist(),
            "state_stabilizer_count": len(state_stabilizer(REPEATED)),
            "exact_state_correspondence_count": len(
                exact_state_correspondences(REPEATED, V5)
            ),
            "by_geometry": ambiguity,
        },
        "collision_case": {
            "first_state": COLLISION_A.tolist(),
            "second_state": COLLISION_B.tolist(),
            "exact_state_correspondence_count": len(
                exact_state_correspondences(
                    COLLISION_A,
                    COLLISION_B,
                )
            ),
            "by_geometry": collisions,
            "correspondence_recovery": collision_recoveries,
        },
        "temporal_correspondence": {
            "states": [state.tolist() for state in temporal_states],
            "true_permutations": [
                list(permutation)
                for permutation in temporal_true_permutations
            ],
            "by_geometry": {
                geometry_id: serialize_temporal_profile(profile)
                for geometry_id, profile in temporal_profiles.items()
            },
        },
        "enumeration_totals": {
            "case_recoveries": (
                (len(CASES) + 1)
                * len(SUPPORTED_GEOMETRIES)
                * PERMUTATION_COUNT
            ),
            "ambiguity_recoveries": (
                len(SUPPORTED_GEOMETRIES) * PERMUTATION_COUNT
            ),
            "temporal_recoveries": (
                (len(temporal_states) - 1)
                * len(SUPPORTED_GEOMETRIES)
                * PERMUTATION_COUNT
            ),
        },
    }

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
