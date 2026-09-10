"""
Tests for E07a — symmetry / identifiability / information loss.

The harness is run once at n=4 (about 5 s). Assertions cover the identities
the report relies on, the negative controls, and reproducibility against the
committed results file.
"""
import json
import os
import sys

import numpy as np
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "experiments"))

import run_symmetry_identifiability as e07  # noqa: E402

RESULTS = os.path.join(ROOT, "docs", "experiment_07_symmetry_identifiability_results.json")


@pytest.fixture(scope="module")
def out():
    return e07.run(n=4, seed=0)


def test_single_state_maps_are_bijections():
    for name, d in e07.state_metrics().items():
        # every off-diagonal distance positive: no two states collide on their own
        off = d[~np.eye(8, dtype=bool)]
        assert (off > 0).all(), name


def test_isometry_groups_have_expected_orders():
    m = e07.state_metrics()
    assert len(e07.isometry_group(m["G1_numeric"])) == 2      # id + reflection
    assert len(e07.isometry_group(m["G2_cyclic"])) == 16      # dihedral D8
    assert len(e07.isometry_group(m["G4_gray"])) == 48        # cube group
    assert len(e07.isometry_group(m["G3_angular"])) == 16     # same as G2


def test_information_loss_decomposition_is_exact(out):
    for g, r in out["geometries"].items():
        i = r["information_loss_bits"]
        assert abs(i["L_R"] - (i["L_sym"] + i["L_excess"])) < 1e-9, g
        assert i["L_excess"] >= -1e-9, g


def test_pair_counts_are_consistent(out):
    for g, r in out["geometries"].items():
        assert sum(r["pairs_by_precedence"].values()) == r["colliding_pairs_total"], g
        assert sum(r["pairs_by_lattice"].values()) == r["colliding_pairs_total"], g
        assert r["pairs_by_lattice"].get("genuine", 0) == r["genuine_pairs"], g


def test_vertex_transitive_geometries_have_no_genuine_collisions(out):
    assert out["geometries"]["G2_cyclic"]["genuine_pairs"] == 0
    assert out["geometries"]["G4_gray"]["genuine_pairs"] == 0
    assert out["geometries"]["G2_cyclic"]["information_loss_bits"]["L_excess"] < 1e-9
    assert out["geometries"]["G4_gray"]["information_loss_bits"]["L_excess"] < 1e-9


def test_g3_adds_nothing_to_g2(out):
    c = out["G3_angular_check"]
    assert c["partition_identical_to_G2"] and c["isometry_group_identical_to_G2"]
    assert out["geometries"]["G3_angular"]["n_classes"] == out["geometries"]["G2_cyclic"]["n_classes"]


def test_g2_is_a_function_of_g1(out):
    assert out["G2_is_function_of_G1"] is True


def test_joint_reproduces_e06_count(out):
    j = out["geometries"]["joint"]
    assert j["label_isometry_group_order"] == 1
    assert j["genuine_pairs"] == 548
    assert out["colliding_under_all_equals_joint_colliding"] is True
    # every joint-genuine pair is explained by at least one single-geometry symmetry
    for pattern, count in out["joint_genuine_by_single_geometry_explanation"].items():
        assert "sym" in pattern, pattern


def test_joint_is_the_meet_of_the_partitions(out):
    G = out["geometries"]
    assert G["joint"]["n_classes"] >= max(G[g]["n_classes"] for g in e07.JOINT_MEMBERS)
    assert G["joint"]["information_loss_bits"]["L_R"] <= min(
        G[g]["information_loss_bits"]["L_R"] for g in e07.JOINT_MEMBERS)


def test_more_data_never_exceeds_exhaustive(out):
    md = out["more_data_control"]["same_geometry_more_samples"]
    for g, rows in md.items():
        for N, r in rows.items():
            assert r["classes_observed"] <= r["classes_exhaustive"], (g, N)
        largest = rows[max(rows)]
        assert largest["classes_observed"] == largest["classes_exhaustive"], g
    plus = out["more_data_control"]["same_samples_plus_geometry"]
    assert plus["G1_numeric+G2_cyclic"]["gain"] == 0
    assert plus["G1_numeric+G4_gray"]["gain"] > 0


def test_negative_controls(out):
    c = out["negative_controls"]
    for k in ("1_global_cyclic_shift", "2_pure_component_permutation",
              "3_pure_label_isometry_G4", "6_asymmetric_vector", "7_identical_state_duplicated"):
        assert c[k]["pass"] is True, k
    for k in ("4_E05_known_correspondence", "5_E06_known_genuine_collision"):
        assert c[k]["status"] == "blocked"
    ms = c["6_asymmetric_vector"]["min_stabilizer_by_geometry"]
    assert ms["G4_gray"]["min_stabilizer"] == 2       # no regular cube-group orbit on 4-subsets
    assert ms["joint"]["min_stabilizer"] == 1


def test_readout_quotient_is_coarser_than_joint(out):
    mr = out["measurement_readout"]
    assert mr["readout_classes"] == 16
    assert mr["of_which_joint_M_separates"] > 0
    assert mr["of_which_joint_M_separates"] <= mr["pairs_merged_by_readout"]


def test_branch_set_schema_and_states(out):
    bs = out["branch_set"]
    assert bs["schema_version"] == "1.0"
    ids = [b["id"] for b in bs["branches"]]
    assert len(ids) == len(set(ids)) == 6
    by_id = {b["id"]: b for b in bs["branches"]}
    assert by_id["correspondence_equivalence"]["suppression_cause"] == "access"
    assert by_id["correspondence_equivalence"]["access_kind"] == "instrument_missing"
    assert by_id["representation_collision"]["status"] == "survived"
    for b in bs["branches"]:
        if b["status"] == "eliminated":
            assert b["eliminated_by"]
        else:
            assert b["eliminated_by"] is None


def test_branch_set_round_trips_through_method_layer(out):
    path = os.environ.get("METHOD_LAYER_PATH",
                          os.path.join(ROOT, "..", "jinnz2", "method-layer"))
    if not os.path.isfile(os.path.join(path, "branch_set.py")):
        pytest.skip("method-layer not available; set METHOD_LAYER_PATH")
    sys.path.insert(0, path)
    from branch_set import BranchSet  # noqa: E402
    bs = BranchSet.from_dict(out["branch_set"])
    assert {b.id for b in bs.eliminated_set()} == {"symmetry_equivalence", "state_label_isometry"}
    results = bs.triage(stream=None)
    assert any(r.to_dict()["result"] == "blocked" for r in results)


def test_discriminator_economy_is_reported_not_assumed(out):
    e = out["discriminator_economy"]
    assert set(e["order_cheapest_first"]) == set(e["order_delta_pairs_per_cost"])
    assert isinstance(e["orderings_agree"], bool)
    assert e["discriminators"]["apply E05 correspondence"]["blocked"] is True


def test_results_file_reproduces(out):
    if not os.path.isfile(RESULTS):
        pytest.skip("committed results file missing")
    committed = json.load(open(RESULTS))
    assert e07.content_hash(out) == committed["results_sha256_excluding_timings"]
