"""Collects the trigger_geometry selftest (validation cases A-E) under pytest."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TG = os.path.join(ROOT, "experiments", "trigger_geometry", "trigger_geometry.py")
sys.path.insert(0, os.path.dirname(TG))


def test_selftest():
    subprocess.run([sys.executable, TG, "selftest"], check=True)


def test_case_A_fires_accumulation_and_coupling():
    import trigger_geometry as tg
    a = tg.case_A()
    assert {"T1_ACCUMULATION", "T2_RESPONSE_COUPLES"} <= set(a["flags"])
    assert a["response_validated_here"] is False and a["operator_correction_required"]


def test_case_B_does_not_fire_accumulation():
    import trigger_geometry as tg
    assert "T1_ACCUMULATION" not in tg.case_B()["flags"]


def test_case_D_comes_back_clean_and_case_E_is_unrated():
    import trigger_geometry as tg
    assert tg.case_D()["flags"] == [] and tg.case_D()["response_validated_here"] is True
    assert tg.case_E()["flags"] == ["T3_ENVELOPE_UNSTATED"] and tg.case_E()["response_validated_here"] == "UNRATED"


def test_redundancy_lowers_nothing():
    import trigger_geometry as tg
    base = set(tg.case_A()["flags"])
    with_red = set(tg.case_A(trigger={"sensor_redundancy": {"n_sensors": 3, "agreement": "unanimous"}})["flags"])
    assert base <= with_red and "REDUNDANCY_NOT_MITIGATION" in with_red
