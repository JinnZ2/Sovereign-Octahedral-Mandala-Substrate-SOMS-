"""Collects the gap_register selftest and the failing demo under pytest."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GR = os.path.join(HERE, "experiments", "gap_register", "gap_register.py")


def test_selftest():
    subprocess.run([sys.executable, GR, "selftest"], check=True)


def test_register_validates_and_demo_fails():
    assert subprocess.run([sys.executable, GR, "validate"]).returncode == 0
    demo = os.path.join(os.path.dirname(GR), "demo", "REGISTER_failing.jsonl")
    assert subprocess.run([sys.executable, GR, "validate", demo], capture_output=True).returncode != 0
