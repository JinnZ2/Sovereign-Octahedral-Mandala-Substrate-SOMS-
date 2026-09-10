"""Thin wrapper: the pilot's own selftest, collected by pytest. The package has no SOMS dependency."""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "experiments", "substrate_pilot_v0"))

from selftest import *  # noqa: F401,F403,E402
