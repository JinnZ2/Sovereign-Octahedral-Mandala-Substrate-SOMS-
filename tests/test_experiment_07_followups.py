"""Tests for the E07 follow-ups T1 (perturbation mechanism) and T2 (Rosenblatt-Seymour)."""
import os
import sys

import itertools

import numpy as np
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "experiments"))

import run_symmetry_identifiability as e07  # noqa: E402
import t1_perturbation_mechanism as t1  # noqa: E402
import t2_rosenblatt_seymour as t2  # noqa: E402


# ---------------- T1 ----------------

@pytest.fixture(scope="module")
def t1_out():
    return t1.run(n=3, seed=0, geometries=("G1_numeric", "G4_gray"))


def test_t1_level_noise_keeps_ties_and_isometries():
    m = e07.state_metrics()
    rng = np.random.RandomState(1)
    d = t1.perturb(m["G1_numeric"], "level", rng)
    off = ~np.eye(8, dtype=bool)
    # same number of distinct levels, same isometry group
    assert len(set(d[off].tolist())) == len(set(m["G1_numeric"][off].tolist()))
    assert len(e07.isometry_group(d)) == len(e07.isometry_group(m["G1_numeric"]))


def test_t1_pair_noise_is_generic():
    m = e07.state_metrics()
    rng = np.random.RandomState(1)
    d = t1.perturb(m["G1_numeric"], "pair", rng)
    off = ~np.eye(8, dtype=bool)
    assert len(set(d[off].tolist())) == 28          # all 28 pair distances distinct
    assert len(e07.isometry_group(d)) == 1


def test_t1_vector_readout_ignores_additive_relations(t1_out):
    for g, v in t1_out["verdicts"].items():
        assert v["vector_additive_contribution"] == 0, g
        assert v["multiset_additive_contribution"] == 0, g


def test_t1_equality_floor_is_28_times_1_plus_n(t1_out):
    for g, v in t1_out["verdicts"].items():
        assert v["equality_floor_pairs"] == 28 * (1 + 3), g


def test_t1_g1_is_tie_degeneracy(t1_out):
    v = t1_out["verdicts"]["G1_numeric"]
    assert v["vector_tie_contribution"] > 0
    assert v["mechanism_for_E07a_readout"].startswith("(b-tie)")


# ---------------- T2 ----------------

def test_t2_homometry_tables_match_reference():
    m = e07.state_metrics()
    ring, _, _ = t2.homometry_table(m["G2_cyclic"], e07.isometry_group(m["G2_cyclic"]), "ring")
    cube, _, _ = t2.homometry_table(m["G4_gray"], e07.isometry_group(m["G4_gray"]), "cube")
    assert (ring["pairs_same_multiset"], ring["pairs_via_isometry"], ring["pairs_non_isometric"]) == (423, 359, 64)
    assert (cube["pairs_same_multiset"], cube["pairs_via_isometry"], cube["pairs_non_isometric"]) == (611, 611, 0)
    assert cube["multiset_complete"]


def test_t2_overlay_depends_on_labeling():
    ov = t2.overlay_check(e07.state_metrics())
    assert ov["binary"]["D8_cap_B3_order"] == 4
    assert ov["binary"]["pairs_in_common_D8_orbit_and_common_B3_orbit"] == 155
    assert ov["gray"]["D8_cap_B3_order"] == 8


def test_t2_z8_has_one_nonisometric_homometric_class():
    m = e07.state_metrics()
    _, non_iso, canon = t2.homometry_table(m["G2_cyclic"], e07.isometry_group(m["G2_cyclic"]), "ring")
    classes = {tuple(sorted((canon[tuple(a)], canon[tuple(b)]))) for a, b in non_iso}
    assert len(classes) == 1
    assert classes == {((0, 1, 2, 5), (0, 1, 3, 4))}


def test_t2_spectral_search_recovers_constructed_factorizations():
    mc = t2.mechanics_control(n=8, k=4, bound=1, seed=11, draws=100000)
    assert mc["checked"], "no constructed (PQ, PQ*) pairs found; widen draws"
    assert mc["all_recovered"] is True


def test_t2_set_level_lemma_holds_numerically():
    # B - {0,c} is always a translate of B + {0,c}: no 2x2 set factorization can be non-isometric
    n = 8
    canon = t2.dihedral_canon(n, 4)
    for B in itertools.combinations(range(n), 2):
        for c in range(1, n):
            S = {(b + x) % n for b in B for x in (0, c)}
            T = {(b - x) % n for b in B for x in (0, c)}
            if len(S) == 4 and len(T) == 4:
                assert canon[tuple(sorted(S))] == canon[tuple(sorted(T))]
