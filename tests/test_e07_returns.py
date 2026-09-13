"""Rollup group D: the E07/E09 returns file exists and its figures are internally consistent.
Recomputation is experiments/e07_returns.py (~30 s); this test reads the written JSON."""
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "docs", "experiment_07_returns.json")


@pytest.fixture(scope="module")
def returns():
    if not os.path.exists(PATH):
        pytest.skip("docs/experiment_07_returns.json not generated")
    return json.load(open(PATH))


def test_d1_split_sums_to_85(returns):
    d = returns["D1_85_pair_split"]
    assert d["G1_sym_only"] + d["G6_sym_only"] + d["both"] == 85
    assert d["G1_sym_only"] + d["G6_sym_only"] + d["both"] + d["neither"] == returns["joint_genuine_pairs"] == 548
    assert d["both"] == 0


def test_d2_same_sigma_is_a_refutation_not_a_pass(returns):
    d = returns["D2_same_sigma_H"]
    assert d["H_order"] == 8 and d["pairs_in_H_x_Sn_orbit"] < d["of"]
    assert d["status"].startswith("REFUTED")


def test_d3_universes_declared(returns):
    d = returns["D3_readout_quotient"]
    assert d["readout_merged_and_joint_does_not_separate"] == 230
    assert d["readout_merged_and_joint_separates"] + 230 == d["readout_merged_pairs"] == 522240
    assert d["universe_all_pairs"] == 4096 * 4095 // 2
    assert 230 <= d["joint_colliding_pairs"] == 668


def test_d5_hash_matches_pair_file(returns):
    import hashlib
    p = os.path.join(ROOT, "docs", "experiment_07_joint_genuine_pairs.json")
    pairs = json.load(open(p))["pairs"]
    assert len(pairs) == 548 and pairs == sorted(pairs)
    assert hashlib.sha256(json.dumps(pairs).encode()).hexdigest() == returns["D5_sorted_pair_list_sha256"]["sha256"]


def test_d6_every_energy_term_is_d_minus_6(returns):
    d = returns["D6_E09_units"]
    assert {d["power_of_d"][k] for k in ("J_ij", "angular", "tensor", "cayley")} == {-6}
    assert d["cutoff"]["in_code"] is False
    assert abs(d["T_star"]["T_start_5.0"] * d["J_scale"] - 5.0) < 1e-9
