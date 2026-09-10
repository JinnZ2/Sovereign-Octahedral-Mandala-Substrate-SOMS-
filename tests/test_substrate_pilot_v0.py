"""
Failure-derived test set, SPEC section 2, T rows: inject and observe.
Stdlib unittest; pytest collects it too. Each test names its FT row.
"""
import os
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "experiments", "substrate_pilot_v0"))

from ledger import Ledger, Refused, OP_PERIOD_H  # noqa: E402
import exercise  # noqa: E402


def fresh():
    L = Ledger()
    L.register_node("FB", "food_bank", "R1")
    L.register_node("P00", "pantry", "R1")
    L.register_node("CAR", "carrier", "R1")
    L.declare_rule("R-DWELL", "DWELL_LIMIT", {"limit_h": 2 * OP_PERIOD_H}, ts=-10)
    L.declare_rule("R-FEFO", "FEFO", {}, ts=-10)
    L.activate(0)
    return L


class FT01_state_at_origin(unittest.TestCase):
    def test_unrecorded_movement_holds(self):
        L = fresh()
        with self.assertRaises(Refused) as cm:
            L.release("GHOST", "P00", "CAR", ts=1)
        self.assertIn("FT-01", str(cm.exception))

    def test_recorded_movement_releases(self):
        L = fresh()
        L.create_unit("U1", "kcal", 1000, ts=0)
        c = L.release("U1", "P00", "CAR", ts=1)
        self.assertEqual(c["status"], "OPEN")
        self.assertEqual(L.units["U1"]["status"], "IN_TRANSIT")


class FT02_unknown_is_a_status(unittest.TestCase):
    def test_schema_rejects_unknown_location(self):
        L = fresh()
        with self.assertRaises(Refused):
            L.create_unit("U1", "kcal", 1, ts=0, location="unknown FSA")
        L.create_unit("U2", "kcal", 1, ts=0)
        with self.assertRaises(Refused):
            L.set_status("U2", "UNKNOWN", ts=1, location="Unknown")
        L.set_status("U2", "UNKNOWN", ts=1)          # as a status it is fine

    def test_lost_keeps_last_known_and_close_needs_reconciliation(self):
        L = fresh()
        L.create_unit("U1", "kcal", 1, ts=0)
        L.release("U1", "P00", "CAR", ts=1)
        L.observe("U1", "physical", "RSA0", ts=5)
        lk = L.mark_lost("U1", ts=9)
        self.assertEqual(lk, {"location": "RSA0", "ts": 5})
        with self.assertRaises(Refused):
            L.close("U1", ts=10)
        L.close("U1", ts=10, reconciliation={"counted_by": "ops", "qty": 0})
        self.assertEqual(L.units["U1"]["status"], "CLOSED")


class FT03_two_channels(unittest.TestCase):
    def test_electronic_loss_loses_no_state(self):
        L = fresh()
        L.create_unit("U1", "kcal", 1, ts=0, seal_no="S1", tcard="T1")
        L.release("U1", "P00", "CAR", ts=1)
        L.electronic_up = False
        self.assertFalse(L.observe("U1", "electronic", "RSA0", ts=3))
        self.assertTrue(L.observe("U1", "physical", "RSA0", ts=3, event="gate-in"))
        self.assertEqual(L.units["U1"]["last_known"], {"location": "RSA0", "ts": 3})
        self.assertEqual(L.units["U1"]["channels"]["physical"]["gate_log"][-1]["event"], "gate-in")


class FT04_identity_survives_transfer(unittest.TestCase):
    def test_repack_without_manifest_flagged_children_linked(self):
        L = fresh()
        L.create_unit("U1", "kcal", 100, ts=0)
        kids = L.repack("U1", [("U1-a", 60), ("U1-b", 40)], ts=2, manifest=None)
        self.assertEqual([k["parent_id"] for k in kids], ["U1", "U1"])
        self.assertEqual(L.units["U1"]["children"], ["U1-a", "U1-b"])
        self.assertEqual(L.units["U1"]["status"], "REPACKED")
        self.assertEqual([f["code"] for f in L.flags], ["REPACK_WITHOUT_MANIFEST"])

    def test_generic_manifest_flagged_identity_kept(self):
        L = fresh()
        L.create_unit("U1", "kcal", 100, ts=0)
        L.transfer("U1", "CAR", ts=1, manifest={"description": "relief supplies", "unit_ids": []})
        self.assertIn("U1", L.units)
        self.assertEqual(L.flags[-1]["code"], "TRANSFER_MANIFEST_GENERIC")


class FT05_receipt(unittest.TestCase):
    def test_no_mark_no_delivery(self):
        L = fresh()
        L.create_unit("U1", "kcal", 1, ts=0)
        L.release("U1", "P00", "CAR", ts=1, commit_id="C1")
        with self.assertRaises(Refused):
            L.receive("C1", ts=2)
        with self.assertRaises(Refused):
            L.receive("C1", ts=2, receiver_mark={"kind": "verbal", "by": "x"})
        self.assertEqual(L.units["U1"]["status"], "IN_TRANSIT")
        L.receive("C1", ts=2, receiver_mark={"kind": "photo", "by": "P00-lead"})
        self.assertEqual(L.units["U1"]["status"], "RECEIVED")
        self.assertEqual(L.commits["C1"]["status"], "KEPT")


class FT06_dwell(unittest.TestCase):
    def test_over_limit_escalates_once(self):
        L = fresh()
        L.create_unit("U1", "kcal", 1, ts=0)
        L.release("U1", "P00", "CAR", ts=1)
        L.arrive_at_rest("U1", "RSA0", ts=2, custody="RSA0")
        self.assertEqual(L.check_dwell(now=2 + OP_PERIOD_H), [])
        fired = L.check_dwell(now=2 + 3 * OP_PERIOD_H)
        self.assertEqual([e["unit_id"] for e in fired], ["U1"])
        self.assertEqual(L.check_dwell(now=2 + 4 * OP_PERIOD_H), [])


class FT07_declared_units(unittest.TestCase):
    def test_substitution_requires_predeclared_conversion(self):
        L = fresh()
        L.report_need("N1", "P00", "kcal", 1000, by_ts=10, ts=0)
        L.create_unit("BOX", "count", 4, ts=1)
        with self.assertRaises(Refused):
            L.substitute("N1", "BOX", ts=2)
        L.declare_conversion("count", "kcal", 250, ts=-100, declared_by="ops")
        r = L.substitute("N1", "BOX", ts=2, event_ts=0)
        self.assertEqual(r["converted_qty"], 1000.0)
        self.assertEqual([e for e in L.events if e["type"] == "SUBSTITUTION"][-1]["factor"], 250.0)

    def test_post_event_conversion_is_flagged(self):
        L = fresh()
        L.report_need("N1", "P00", "kcal", 1000, by_ts=10, ts=0)
        L.create_unit("BOX", "count", 4, ts=1)
        L.declare_conversion("count", "kcal", 250, ts=5, declared_by="ops")   # after activation
        L.substitute("N1", "BOX", ts=6, event_ts=0)
        self.assertEqual(L.flags[-1]["code"], "CONVERSION_DECLARED_POST_EVENT")

    def test_undeclared_unit_refused(self):
        L = fresh()
        with self.assertRaises(Refused):
            L.create_unit("U", "pounds", 1, ts=0)
        with self.assertRaises(Refused):
            L.report_need("N", "P00", "boxes", 1, by_ts=1, ts=0)


class FT08_condition_expiry(unittest.TestCase):
    def test_fefo_and_expired_excluded(self):
        L = fresh()
        L.report_need("N1", "P00", "kcal", 1, by_ts=10, ts=0)
        L.create_unit("A", "kcal", 1, ts=0, expiry_ts=100)
        L.create_unit("B", "kcal", 1, ts=0, expiry_ts=50)
        L.create_unit("X", "kcal", 1, ts=0, expiry_ts=5)
        L.create_unit("D", "kcal", 1, ts=0, expiry_ts=70, condition="DAMAGED")
        order = L.allocate("N1", ["A", "B", "X", "D"], now=10)
        self.assertEqual(order, ["B", "A"])
        self.assertEqual(sorted(f["code"] for f in L.flags), ["CONDITION_NOT_GOOD", "EXPIRED_EXCLUDED"])


class FT09_finding_register(unittest.TestCase):
    def test_finding_closes_only_as_rule_or_waiver_and_shows_at_activation(self):
        L = Ledger()
        L.register_finding("F1", "AAR 2011", "commodity movement", found_ts=-1000)
        with self.assertRaises(Refused):
            L.resolve_finding("F1", ts=0, waived={"owner": "x"})        # no date
        with self.assertRaises(Refused):
            L.resolve_finding("F1", ts=0, rule_id="R-NOPE")             # rule must exist
        shown = L.activate(0)
        self.assertEqual(shown[0]["finding_id"], "F1")
        self.assertEqual(shown[0]["age_h"], 1000)
        L.declare_rule("R1", "DWELL_LIMIT", {"limit_h": 1}, ts=1)
        L.resolve_finding("F1", ts=2, rule_id="R1")
        self.assertEqual(L.activate(3), [])


class FT10_record_custody(unittest.TestCase):
    def test_two_copies_stay_identical(self):
        root = tempfile.mkdtemp()
        L = Ledger(root=root)
        L.register_node("P00", "pantry", "R1")
        L.create_unit("U1", "kcal", 1, ts=0)
        self.assertTrue(L.copies_consistent())
        self.assertEqual(L.events[-1]["record_custody"], "pilot-ops")
        self.assertEqual(L.events[-1]["custody"], "origin")           # the unit's own custody survives
        with self.assertRaises(ValueError):
            Ledger(root=root, copies=("only",))


class FT11_money_behind_physical(unittest.TestCase):
    def test_settlement_refused_without_receipt(self):
        L = fresh()
        L.create_unit("U1", "kcal", 1, ts=0)
        L.release("U1", "P00", "CAR", ts=1, commit_id="C1")
        with self.assertRaises(Refused):
            L.settle("C1", 10.0, {"scope": "carrier invoice"}, ts=2)
        self.assertEqual(L.money[-1]["type"], "SETTLEMENT_REFUSED")
        L.receive("C1", ts=3, receiver_mark={"kind": "stamp", "by": "P00-lead"})
        with self.assertRaises(Refused):
            L.settle("C1", 10.0, {}, ts=4)                                  # MONEY_TERM scope required
        rec = L.settle("C1", 10.0, {"scope": "carrier invoice"}, ts=4)
        self.assertEqual(rec["type"], "SETTLEMENT")


class FT12_route_edges(unittest.TestCase):
    def test_unassigned_edge_flagged(self):
        L = fresh()
        r = L.declare_route("R1", [("FB", "RSA0", "linehaul"), ("port", "FB", "cross-dock")],
                            {("FB", "RSA0", "linehaul"): "CAR"}, ts=0)
        self.assertEqual(r["unassigned"], [["port", "FB", "cross-dock"]])
        self.assertEqual(L.flags[-1]["code"], "ROUTE_EDGE_UNASSIGNED")


class FT15_provisional_intake(unittest.TestCase):
    def test_unregistered_node_accepted_and_promoted_on_first_kept_commit(self):
        L = fresh()
        L.register_node("COMM", "community", "R1", ts=1, registered=False)
        L.report_need("N", "COMM", "kcal", 100, by_ts=10, ts=1)
        L.report_stock("COMM", "CU", "kcal", 100, ts=1)
        self.assertEqual(L.nodes["COMM"]["status"], "PROVISIONAL")
        L.release("CU", "P00", "COMM", ts=2, commit_id="C")
        self.assertEqual(L.nodes["COMM"]["status"], "PROVISIONAL")         # not yet: commit is OPEN
        L.receive("C", ts=3, receiver_mark={"kind": "photo", "by": "P00-lead"})
        self.assertEqual(L.nodes["COMM"]["status"], "REGISTERED")


class Exercise_replay(unittest.TestCase):
    def test_replay_runs_and_reports_failures_as_found(self):
        r = exercise.run(seed=0)
        v = r["verdicts"]
        self.assertEqual(sorted(v), ["FT-%02d" % i for i in range(1, 16)])
        for ft in ("FT-02", "FT-03", "FT-04", "FT-05", "FT-07", "FT-08", "FT-09", "FT-10", "FT-11", "FT-12", "FT-14", "FT-15"):
            self.assertEqual(v[ft]["verdict"], "PASS", ft)
        # every mechanism held except the co-authorship gap
        for ft in v:
            self.assertEqual(v[ft]["shall_held"], ft != "FT-13", ft)
        # injected gaps are reported against the operator targets, not relabelled
        self.assertEqual(v["FT-13"]["verdict"], "FAIL")
        self.assertEqual(v["FT-01"]["verdict"], "FAIL")                     # visibility target missed by the injects
        self.assertGreater(r["metrics"]["visibility_lost_pct"], 0)
        self.assertLessEqual(r["n_nodes"], 150)
        self.assertIn("AAR-2011-03", r["metrics"]["open_findings"])


if __name__ == "__main__":
    unittest.main()
