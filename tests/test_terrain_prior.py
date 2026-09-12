"""Collects the terrain_prior selftest (validation cases A-E) under pytest."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TP = os.path.join(ROOT, "experiments", "terrain_prior", "terrain_prior.py")
sys.path.insert(0, os.path.dirname(TP))


def test_selftest():
    subprocess.run([sys.executable, TP, "selftest"], check=True)


def test_case_A_fires_sensor_inversion_and_returns_low_bearing():
    import terrain_prior as tp
    a = tp.case_A()
    assert "P2_SENSOR_INVERT" in a["flags"] and a["bearing_prior"]["value"].startswith("LOW")


def test_case_C_returns_opposite_directions_not_one_answer():
    import terrain_prior as tp
    c = tp.case_C()
    assert [x["direction"] for x in c["bearing_prior"]["by_platform"]] == ["NOT_SUPPORTED", "SUPPORTED"]
    assert "P3_MORPH_SPLIT" in c["flags"]


def test_case_D_no_mechanism_no_prior():
    import terrain_prior as tp
    d = tp.case_D()
    assert d["flags"] == ["P5_NO_MECHANISM"] and "bearing_prior" not in d
