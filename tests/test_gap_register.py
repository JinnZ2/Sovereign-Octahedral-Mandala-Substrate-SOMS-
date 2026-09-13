"""Collects the gap_register selftest, the store validate (V1-V9 incl. emission freshness), and the failing demo."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GR = os.path.join(HERE, "experiments", "gap_register", "gap_register.py")


def test_selftest():
    subprocess.run([sys.executable, GR, "selftest"], check=True)


def test_register_validates_with_current_emissions():
    assert subprocess.run([sys.executable, GR, "validate"]).returncode == 0        # V8: committed emissions match the store


def test_demo_fails():
    demo = os.path.join(os.path.dirname(GR), "demo", "REGISTER_failing.jsonl")
    out = subprocess.run([sys.executable, GR, "validate", demo], capture_output=True, text=True)
    assert out.returncode != 0
    for rule in ("V4", "V2", "V7"):
        assert rule in out.stdout
