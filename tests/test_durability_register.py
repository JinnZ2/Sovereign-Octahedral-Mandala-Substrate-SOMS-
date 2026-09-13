"""Collects the durability register's validator and selftest under pytest."""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR = os.path.join(ROOT, "experiments", "durability_register", "failure_register.py")
sys.path.insert(0, os.path.dirname(FR))


def test_selftest():
    subprocess.run([sys.executable, FR, "selftest"], check=True)


def test_register_validates():
    assert subprocess.run([sys.executable, FR, "validate"]).returncode == 0


def test_projection_cap_and_no_yes_reconstruction():
    import failure_register as fr
    hdr, entries = fr.load()
    assert hdr["projected_fraction"] <= hdr["projected_cap"]
    rep = fr.report()
    assert "YES" not in rep["reconstruction_distribution"]        # headline: nothing is fully reconstructable
    # section 8 predicted PARTIAL would dominate. After rev 6 it does not, and the report states that rather
    # than calling PARTIAL modal on a tie.
    assert rep["expected_yield_check"]["status"].startswith("PREDICTION NO LONGER HOLDS")


def test_falsifiers_report_status_including_not_run():
    import failure_register as fr
    f = fr.falsifiers()
    assert f["F_A_bridge_transport_valid"]["status"] == "PASS"
    assert f["F_G_reader_precondition_blindness"]["status"] == "NOT RUN"
    assert "changes nothing on its own" in f["F_E_the_enumeration_is_not_the_mechanism"]["what_would_make_this_binding"]


def test_coverage_audit_has_no_gaps():
    """The work order was re-issued unchanged; this is the check that it is fully implemented."""
    import failure_register as fr
    c = fr.coverage()
    assert c["n_gaps"] == 0, c["gaps"]
    assert c["n_rows"] >= 40
    ids = {r_id for r in c["rows"] for r_id in r["entries"]}
    assert {"DUR-006", "DUR-007"} <= ids                      # the two gaps the audit found, now closed
