"""
Selftest — SPEC section 2 T rows (FT-01..FT-18) and work-order items V1..V8, plus the
replay. Stdlib unittest. Prints its count.

  python selftest.py
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from ledger import Ledger, Refused, SchemaError, OP_PERIOD_H, check_locus, CLIMATES, LOCI, SITES, LOCUS_DEFINITIONS  # noqa: E402
import json  # noqa: E402
import exercise  # noqa: E402
import locus_tally  # noqa: E402


def fresh():
    L = Ledger()
    L.register_node("FB", "food_bank", "R1")
    L.register_node("P00", "pantry", "R1")
    L.register_node("CAR", "carrier", "R1")
    L.register_node("YARD", "yard", "R1", custodial=False)
    L.declare_rule("R-DWELL", "DWELL_LIMIT", {"limit_h": 2 * OP_PERIOD_H}, ts=-10)
    L.declare_rule("R-FEFO", "FEFO", {}, ts=-10)
    L.declare_trigger_table("ev", {"kcal": ("R1", "urgency"), "L_water": ("R2", "custody"), "count": ("R1", "urgency"),
                                   "protein_g": ("R1", "urgency")}, ts=-10, declared_by="ops")
    L.declare_resolver("RES", {"radio": "ch3", "cellular": "555"}, ts=-10)
    L.activate(0)
    return L


def unit(L, uid="U1", du="kcal", qty=1000, cls="R1", axis="urgency", **kw):
    kw.setdefault("climate", "stable")           # V11: a helper unit declares its climate
    return L.create_unit(uid, du, qty, ts=kw.pop("ts", 0), regime_class=cls, axis=axis, **kw)


class FT01_state_at_origin(unittest.TestCase):
    def test_unrecorded_movement_holds(self):
        L = fresh()
        with self.assertRaises(Refused) as cm:
            L.release("GHOST", "P00", "CAR", ts=1)
        self.assertIn("FT-01", str(cm.exception))

    def test_recorded_movement_releases(self):
        L = fresh(); unit(L)
        c = L.release("U1", "P00", "CAR", ts=1)
        self.assertEqual((c["status"], L.units["U1"]["status"]), ("OPEN", "IN_TRANSIT"))


class FT02_unknown_is_a_status(unittest.TestCase):
    def test_schema_rejects_unknown_location(self):
        L = fresh()
        with self.assertRaises(Refused):
            unit(L, location="unknown FSA")
        unit(L, "U2")
        with self.assertRaises(Refused):
            L.set_status("U2", "UNKNOWN", ts=1, location="Unknown")
        L.set_status("U2", "UNKNOWN", ts=1)

    def test_lost_keeps_last_known_and_close_needs_reconciliation(self):
        L = fresh(); unit(L)
        L.release("U1", "P00", "CAR", ts=1)
        L.observe("U1", "physical", "P00", ts=5)
        self.assertEqual(L.mark_lost("U1", ts=9), {"location": "P00", "ts": 5})
        with self.assertRaises(Refused):
            L.close("U1", ts=10)
        L.close("U1", ts=10, reconciliation={"counted_by": "ops", "qty": 0})
        self.assertEqual(L.units["U1"]["status"], "CLOSED")


class FT03_two_channels(unittest.TestCase):
    def test_electronic_loss_loses_no_state(self):
        L = fresh(); unit(L, seal_no="S1", tcard="T1")
        L.release("U1", "P00", "CAR", ts=1)
        L.electronic_up = False
        self.assertFalse(L.observe("U1", "electronic", "P00", ts=3))
        self.assertTrue(L.observe("U1", "physical", "P00", ts=3, event="gate-in"))
        self.assertEqual(L.units["U1"]["last_known"], {"location": "P00", "ts": 3})


class FT04_identity_survives_transfer(unittest.TestCase):
    def test_repack_without_manifest_flagged_children_linked(self):
        L = fresh(); unit(L, qty=100)
        kids = L.repack("U1", [("U1-a", 60), ("U1-b", 40)], ts=2, manifest=None)
        self.assertEqual([k["parent_id"] for k in kids], ["U1", "U1"])
        self.assertEqual([k["regime_class"] for k in kids], ["R1", "R1"])
        self.assertEqual([f["code"] for f in L.flags], ["REPACK_WITHOUT_MANIFEST"])

    def test_generic_manifest_flagged_identity_kept(self):
        L = fresh(); unit(L, qty=100)
        L.transfer("U1", "CAR", ts=1, manifest={"description": "relief supplies", "unit_ids": []}, signed_by=("origin", "CAR"))
        self.assertEqual(L.flags[-1]["code"], "TRANSFER_MANIFEST_GENERIC")
        self.assertEqual(L.flags[-1]["locus"], "regime.market")


class FT05_receipt(unittest.TestCase):
    def test_no_mark_no_delivery(self):
        L = fresh(); unit(L)
        L.release("U1", "P00", "CAR", ts=1, commit_id="C1")
        with self.assertRaises(Refused):
            L.receive("C1", ts=2)
        with self.assertRaises(Refused):
            L.receive("C1", ts=2, receiver_mark={"kind": "verbal", "by": "x"})
        self.assertEqual(L.units["U1"]["status"], "IN_TRANSIT")
        L.receive("C1", ts=2, receiver_mark={"kind": "photo", "by": "P00-lead"})
        self.assertEqual((L.units["U1"]["status"], L.commits["C1"]["status"]), ("RECEIVED", "KEPT"))


class FT06_dwell(unittest.TestCase):
    def test_over_limit_escalates_once_with_locus(self):
        L = fresh(); unit(L)
        L.release("U1", "P00", "CAR", ts=1)
        L.arrive_at_rest("U1", "P00", ts=2, custody="P00")
        self.assertEqual(L.check_dwell(now=2 + OP_PERIOD_H), [])
        fired = L.check_dwell(now=2 + 3 * OP_PERIOD_H)
        self.assertEqual([(e["unit_id"], e["locus"], e["site"]) for e in fired], [("U1", "regime.urgency", "undamaged")])
        self.assertEqual(L.check_dwell(now=2 + 4 * OP_PERIOD_H), [])


class FT07_declared_units(unittest.TestCase):
    def test_direct_substitution_requires_predeclared_conversion(self):
        L = fresh()
        L.report_need("N1", "P00", "kcal", 1000, by_ts=10, ts=0)
        unit(L, "BOX", "count", 4)
        with self.assertRaises(Refused):
            L.substitute("N1", "BOX", ts=2)
        L.declare_conversion("count", "kcal", 250, ts=-100, declared_by="ops")
        self.assertEqual(L.substitute("N1", "BOX", ts=2, event_ts=0)["converted_qty"], 1000.0)

    def test_q1_receipt_recorded_need_uncredited(self):
        """Q-1: no declared factor at receipt -> delivery RECEIVED, need not credited, failure recorded."""
        L = fresh()
        L.report_need("N1", "P00", "kcal", 1000, by_ts=10, ts=0)
        unit(L, "PRO", "protein_g", 500)
        L.release("PRO", "P00", "CAR", ts=1, commit_id="C1")
        L.receive("C1", ts=2, receiver_mark={"kind": "stamp", "by": "P00-lead"}, need_id="N1")
        self.assertEqual(L.units["PRO"]["status"], "RECEIVED")
        self.assertEqual(L.needs["N1"]["delivered"], 0.0)
        self.assertEqual(L.flags[-1]["code"], "SUBSTITUTION_UNCREDITED")

    def test_post_event_conversion_is_flagged_not_refused(self):
        L = fresh()
        L.report_need("N1", "P00", "kcal", 1000, by_ts=10, ts=0)
        unit(L, "BOX", "count", 4)
        L.declare_conversion("count", "kcal", 250, ts=5, declared_by="ops")
        L.substitute("N1", "BOX", ts=6, event_ts=0)
        self.assertEqual(L.flags[-1]["code"], "CONVERSION_DECLARED_POST_EVENT")

    def test_undeclared_unit_refused(self):
        L = fresh()
        with self.assertRaises(Refused):
            L.create_unit("U", "pounds", 1, ts=0)


class FT08_condition_expiry(unittest.TestCase):
    def test_fefo_and_expired_excluded(self):
        L = fresh()
        L.report_need("N1", "P00", "kcal", 1, by_ts=10, ts=0)
        unit(L, "A", expiry_ts=100); unit(L, "B", expiry_ts=50); unit(L, "X", expiry_ts=5); unit(L, "D", expiry_ts=70, condition="DAMAGED")
        self.assertEqual(L.allocate("N1", ["A", "B", "X", "D"], now=10), ["B", "A"])
        self.assertEqual(sorted(f["code"] for f in L.flags), ["CONDITION_NOT_GOOD", "EXPIRED_EXCLUDED"])


class FT09_finding_register(unittest.TestCase):
    def test_finding_closes_only_as_rule_or_waiver(self):
        L = Ledger()
        L.register_finding("F1", "AAR 2011", "commodity movement", found_ts=-1000)
        with self.assertRaises(Refused):
            L.resolve_finding("F1", ts=0, waived={"owner": "x"})
        with self.assertRaises(Refused):
            L.resolve_finding("F1", ts=0, rule_id="R-NOPE")
        self.assertEqual(L.activate(0)[0]["age_h"], 1000)
        L.declare_rule("R1", "DWELL_LIMIT", {"limit_h": 1}, ts=1)
        L.resolve_finding("F1", ts=2, rule_id="R1")
        self.assertEqual(L.activate(3), [])


class FT10_record_custody(unittest.TestCase):
    def test_two_copies_stay_identical(self):
        L = Ledger(root=tempfile.mkdtemp())
        L.register_node("P00", "pantry", "R1")
        L.create_unit("U1", "kcal", 1, ts=0)
        self.assertTrue(L.copies_consistent())
        self.assertEqual((L.events[-1]["record_custody"], L.events[-1]["custody"]), ("pilot-ops", "origin"))
        with self.assertRaises(ValueError):
            Ledger(root=tempfile.mkdtemp(), copies=("only",))


class FT11_money_behind_physical(unittest.TestCase):
    def test_settlement_refused_without_receipt(self):
        L = fresh(); unit(L)
        L.release("U1", "P00", "CAR", ts=1, commit_id="C1")
        with self.assertRaises(Refused):
            L.settle("C1", 10.0, {"scope": "carrier invoice"}, ts=2)
        self.assertEqual((L.money[-1]["type"], L.money[-1]["locus"]), ("SETTLEMENT_REFUSED", "regime.market"))
        L.receive("C1", ts=3, receiver_mark={"kind": "stamp", "by": "P00-lead"})
        with self.assertRaises(Refused):
            L.settle("C1", 10.0, {}, ts=4)
        self.assertEqual(L.settle("C1", 10.0, {"scope": "carrier invoice"}, ts=4)["type"], "SETTLEMENT")


class FT12_route_edges(unittest.TestCase):
    def test_unassigned_edge_flagged_pre_event(self):
        L = fresh()
        r = L.declare_route("R1", [("FB", "P00", "linehaul"), ("port", "FB", "cross-dock")], {("FB", "P00", "linehaul"): "CAR"}, ts=0)
        self.assertEqual(r["unassigned"], [["port", "FB", "cross-dock"]])
        self.assertEqual((L.flags[-1]["code"], L.flags[-1]["site"]), ("ROUTE_EDGE_UNASSIGNED", "pre-event"))


class FT15_provisional_intake(unittest.TestCase):
    def test_unregistered_node_promoted_on_first_kept_commit(self):
        L = fresh()
        L.register_node("COMM", "community", "R1", ts=1, registered=False)
        L.report_need("N", "COMM", "kcal", 100, by_ts=10, ts=1)
        L.report_stock("COMM", "CU", "kcal", 100, ts=1, regime_class="R1", axis="urgency")
        L.release("CU", "P00", "COMM", ts=2, commit_id="C")
        self.assertEqual(L.nodes["COMM"]["status"], "PROVISIONAL")
        L.receive("C", ts=3, receiver_mark={"kind": "photo", "by": "P00-lead"})
        self.assertEqual(L.nodes["COMM"]["status"], "REGISTERED")


class V1_failure_locus_schema(unittest.TestCase):
    def test_enum_is_defined(self):
        self.assertIn("regime.learning", LOCI); self.assertIn("unknown", SITES)
        for locus in LOCI:
            self.assertTrue(LOCUS_DEFINITIONS.get(locus), locus)
        self.assertEqual(check_locus("regime.learning", "unknown"), ["regime.learning"])

    def test_physical_damage_rejected_off_damaged_site(self):
        for site in ("undamaged", "pre-event", "unknown"):
            with self.assertRaises(SchemaError):
                check_locus("physical_damage", site)
            with self.assertRaises(SchemaError):
                check_locus("mixed(regime.urgency,physical_damage)", site)
        self.assertEqual(check_locus("physical_damage", "damaged"), ["physical_damage"])
        self.assertEqual(check_locus("mixed(regime.custody,physical_damage)", "damaged"), ["regime.custody", "physical_damage"])
        with self.assertRaises(SchemaError):
            check_locus("infrastructure devastation", "damaged")

    def test_every_failure_record_carries_both_fields(self):
        L = fresh(); unit(L)
        L.release("U1", "P00", "CAR", ts=1, commit_id="C1")
        L.mark_lost("U1", ts=2)
        with self.assertRaises(Refused):
            L.settle("C1", 1.0, {"scope": "x"}, ts=3)
        L.declare_route("R2", [("a", "b", "x")], {}, ts=4)
        self.assertGreaterEqual(len(L.failures), 3)
        for f in L.failures:
            self.assertIn("locus", f); self.assertIn("site", f)
            check_locus(f["locus"], f["site"])

    def test_ledger_refuses_physical_damage_at_undamaged_site(self):
        L = fresh(); unit(L)
        with self.assertRaises(SchemaError):
            L.mark_lost("U1", ts=2, locus="physical_damage")          # P00/origin is undamaged
        L.nodes["P00"]["damage_state"] = "damaged"
        L.observe("U1", "physical", "P00", ts=2)
        L.mark_lost("U1", ts=3, locus="physical_damage")             # now allowed


class V2_maria_fixture(unittest.TestCase):
    def test_fixture_loads_validates_and_tallies(self):
        header, body = locus_tally.load(os.path.join(HERE, "fixtures", "maria_locus.jsonl"))
        self.assertIn("single-grader coding", header["_header"]); self.assertIn("second grader required", header["_header"])
        self.assertEqual(len(body), 13)
        t = locus_tally.tally(body)
        self.assertEqual(t["coarse"], {"regime": 10, "mixed": 2, "physical_damage": 1})
        self.assertEqual(t["second_grader_rows"], 0)
        self.assertFalse(header["tally_citable"])
        for r in body:
            self.assertIn("second_grader_locus", r); self.assertIn("disagreement", r)


class V3_regime_class(unittest.TestCase):
    def test_critical_alone_refused_and_axis_required(self):
        L = fresh()
        L.create_unit("U", "kcal", 1, ts=0)
        with self.assertRaises(Refused):
            L.declare_load("U", "critical", ts=0)
        with self.assertRaises(Refused):
            L.declare_load("U", "R2", ts=0)
        with self.assertRaises(Refused):
            L.release("U", "P00", "CAR", ts=1)                          # no class + axis: held
        L.declare_load("U", "R2", "custody", ts=0)
        self.assertEqual((L.units["U"]["regime_class"], L.units["U"]["axis"]), ("R2", "custody"))

    def test_custody_axis_may_not_drop_to_expedite(self):
        L = fresh(); unit(L, cls="R2", axis="custody")
        with self.assertRaises(Refused):
            L.reclass("U1", "R0", ts=1, reason="expedite")
        L.reclass("U1", "R3", ts=1, reason="escort available")
        unit(L, "U2", cls="R2", axis="urgency")
        L.reclass("U2", "R1", ts=1, reason="expedite")                 # urgency axis may


class V4_context_severity(unittest.TestCase):
    def test_event_reclasses_from_precomputed_table_no_manual_step(self):
        L = fresh()
        unit(L, "W", "L_water", 100, cls="R0", axis="urgency")
        unit(L, "K", "kcal", 100, cls="R3", axis="custody")
        with self.assertRaises(Refused):
            L.declare_event("no-such-event", ts=1)
        reclassed = L.declare_event("ev", ts=1, damaged_sites=["P00"])
        self.assertEqual(reclassed, ["W"])
        self.assertEqual((L.units["W"]["regime_class"], L.units["W"]["axis"]), ("R2", "custody"))
        self.assertEqual(L.units["K"]["regime_class"], "R3")             # never lowered
        self.assertEqual(L.events_declared[-1]["manual_steps"], 0)
        self.assertEqual(L.nodes["P00"]["damage_state"], "damaged")


class FT16_named_custodian(unittest.TestCase):
    def test_transfer_needs_signed_handover(self):
        L = fresh(); unit(L)
        with self.assertRaises(Refused):
            L.transfer("U1", "CAR", ts=1, manifest={"unit_ids": ["U1"]})
        L.transfer("U1", "CAR", ts=1, manifest={"unit_ids": ["U1"]}, signed_by=("origin", "CAR"))
        self.assertEqual(L.units["U1"]["custody"], "CAR")

    def test_presence_without_custody_is_unsigned_transfer(self):
        L = fresh(); unit(L)
        L.release("U1", "YARD", "CAR", ts=1)
        L.observe("U1", "physical", "YARD", ts=2, event="dropped", by="CAR")
        self.assertEqual(L.check_presence(now=2), [])                     # within grace
        fired = L.check_presence(now=4)
        self.assertEqual([(f["unit_id"], f["present_at"], f["custodian_of_record"], f["node_custodial"]) for f in fired],
                         [("U1", "YARD", "CAR", False)])
        self.assertEqual(L.check_presence(now=6), [])                     # once


class FT17_heartbeat(unittest.TestCase):
    def test_silence_escalates_within_one_interval(self):
        L = fresh(); unit(L, "W", "L_water", 100, cls="R2", axis="custody", max_silence_h=6)
        L.release("W", "P00", "CAR", ts=0)
        L.checkin("W", ts=3, by="CAR")
        with self.assertRaises(Refused):
            L.checkin("W", ts=4, by="P00")                                 # not the custodian
        self.assertEqual(L.check_heartbeat(now=9), [])                    # exactly at the interval
        fired = L.check_heartbeat(now=11)
        self.assertEqual(len(fired), 1)
        self.assertEqual((fired[0]["detection_latency_h"], fired[0]["within_one_interval"], fired[0]["routed_to"]), (2, True, "RES"))
        unit(L, "K", "kcal", 1, cls="R1", axis="urgency")
        L.release("K", "P00", "CAR", ts=0)
        self.assertEqual([f["unit_id"] for f in L.check_heartbeat(now=100)], [])   # R1 has no heartbeat


class FT18_contested_custody(unittest.TestCase):
    def test_resolver_must_be_reachable_without_cellular(self):
        L = Ledger()
        with self.assertRaises(Refused):
            L.declare_resolver("R", {"cellular": "555", "sms": "555"}, ts=0)
        L.declare_resolver("R", {"radio": "ch3"}, ts=0)
        self.assertEqual(L.resolvers["R"]["non_cellular_paths"], ["radio"])

    def test_competing_claim_routes_and_custody_holds(self):
        L = fresh(); unit(L, "W", "L_water", 100, cls="R2", axis="custody")
        L.release("W", "P00", "CAR", ts=0)
        rec = L.claim_custody("W", "OTHER", ts=1, basis="verbal")
        self.assertEqual((rec["type"], rec["locus"], rec["routed_to"]), ("CONTESTED_CUSTODY", "regime.security", "RES"))
        self.assertEqual(L.units["W"]["custody"], "CAR")
        L.resolve_claim("W", ts=2, resolver_id="RES", award_to="OTHER", signed_by=("RES", "OTHER"))
        self.assertEqual(L.units["W"]["custody"], "OTHER")


class V8_retention(unittest.TestCase):
    def test_missing_assignment_flagged_unless_waived(self):
        L = Ledger()
        L.register_node("P00", "pantry", "R1")
        L.declare_trigger_table("ev", {"kcal": ("R1", "urgency")}, ts=-10, declared_by="ops")
        L.create_unit("K", "kcal", 1, ts=-1); L.create_unit("W", "L_water", 1, ts=-1)
        L.activate(0)
        miss = [f for f in L.failures if f["type"] == "MISSING_CLASS_ASSIGNMENT"]
        self.assertEqual([(f["declared_unit"], f["locus"]) for f in miss], [("L_water", "regime.learning")])
        L.end_event(ts=5)
        self.assertIn("kcal", L.standing_plan)
        with self.assertRaises(Refused):
            L.waive_assignment("L_water", owner="ops", date="", ts=6)
        L.waive_assignment("L_water", owner="ops", date="2026-09-10", ts=6)
        L.activate(7)
        self.assertEqual(sum(1 for f in L.failures if f["type"] == "MISSING_CLASS_ASSIGNMENT"), 1)   # not flagged again


class V11_climate(unittest.TestCase):
    def test_missing_climate_defaults_to_stable_and_flags(self):
        L = fresh()
        L.create_unit("U", "kcal", 1, ts=0)
        self.assertEqual(L.units["U"]["climate"], "stable")
        self.assertEqual([f["code"] for f in L.flags if f["unit_id"] == "U"], ["CLIMATE_DEFAULTED"])
        L.create_unit("V", "kcal", 1, ts=0, climate="partial")
        self.assertEqual(L.units["V"]["climate"], "partial")
        with self.assertRaises(SchemaError):
            L.create_unit("W", "kcal", 1, ts=0, climate="normal")

    def test_event_flips_climate_through_trigger_table(self):
        L = fresh(); unit(L, "W", "L_water", 1, cls="R0", axis="urgency", climate="stable")
        self.assertEqual(L.climate, "stable")
        L.declare_event("ev", ts=1)
        self.assertEqual((L.climate, L.units["W"]["climate"]), ("variable", "variable"))
        self.assertEqual(L.events_declared[-1]["climate"], "variable")
        L2 = Ledger()
        with self.assertRaises(SchemaError):
            L2.declare_trigger_table("ev", {"kcal": ("R1", "urgency")}, ts=0, declared_by="ops", climate="calm")

    def test_field_fix_required_only_under_variable(self):
        L = fresh(); unit(L, climate="stable")
        L.release("U1", "P00", "CAR", ts=1)                              # stable: no check needed
        self.assertEqual([f for f in L.flags if f["code"] == "FIELD_FIX_MISSING"], [])
        L.set_climate("variable", ts=2, reason="test")
        L.observe("U1", "physical", "P00", ts=3, by="CAR")                 # contact with no check -> flagged
        self.assertEqual([f["code"] for f in L.flags if f.get("unit_id") == "U1"], ["FIELD_FIX_MISSING"])
        L.observe("U1", "physical", "P00", ts=4, by="CAR", field_fix={"sign": "CAR", "dof": ["route"], "state_updated": True})
        self.assertEqual(sum(1 for e in L.events if e["type"] == "FIELD_FIX"), 1)
        with self.assertRaises(SchemaError):
            L.observe("U1", "physical", "P00", ts=5, by="CAR", field_fix={"sign": "CAR", "dof": ["route"], "state_updated": False})
        with self.assertRaises(SchemaError):
            L.observe("U1", "physical", "P00", ts=5, by="CAR", field_fix={"sign": "CAR"})

    def test_every_spec_row_and_target_carries_climate(self):
        rows = json.load(open(os.path.join(HERE, "spec_rows.json")))["rows"]
        ids = {r["id"] for r in rows}
        self.assertTrue({"FT-%02d" % i for i in range(1, 19)} <= ids)
        for r in rows:
            self.assertIn(r["climate"], CLIMATES, r["id"])
        for k, t in exercise.TARGETS.items():
            self.assertIn(t["climate"], CLIMATES, k); self.assertTrue(t["measured_in"], k)

    def test_claim_valid_only_inside_declared_climate(self):
        r = exercise.run(seed=0)
        self.assertEqual(r["run_climate"], "variable")
        self.assertEqual(r["verdicts"]["FT-05"]["verdict"], "NOT VALID (climate)")   # stable drill target, variable run
        self.assertEqual(r["verdicts"]["FT-05"]["target_climate"], "stable")
        for k, v in r["verdicts"].items():
            self.assertEqual(v["run_climate"], "variable")
            if k in exercise.TARGETS and exercise.TARGETS[k]["climate"] == "variable":
                self.assertIn(v["verdict"], ("PASS", "FAIL"), k)


class Exercise_replay(unittest.TestCase):
    def test_replay_runs_and_reports_failures_as_found(self):
        r = exercise.run(seed=0)
        v = r["verdicts"]
        self.assertEqual(sorted(k for k in v if k.startswith("FT")), ["FT-%02d" % i for i in range(1, 19)])
        for k in ("V3", "V4", "V8", "V11"):
            self.assertEqual(v[k]["verdict"], "PASS", k)
        for ft in v:
            self.assertEqual(v[ft]["shall_held"], ft != "FT-13", ft)
        self.assertEqual(v["FT-13"]["verdict"], "FAIL")
        self.assertEqual(v["FT-01"]["verdict"], "FAIL")
        self.assertEqual(v["FT-05"]["verdict"], "NOT VALID (climate)")
        self.assertLessEqual(r["n_nodes"], 150)
        for locus in r["failures_by_locus"]:
            self.assertNotEqual(locus, "physical_damage")                  # no damage coded in an undamaged-site run
        self.assertIn("AAR-2011-03", r["metrics"]["open_findings"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    res = unittest.TextTestRunner(verbosity=0).run(suite)
    print("selftest: %d tests, %d failures, %d errors" % (res.testsRun, len(res.failures), len(res.errors)))
    sys.exit(0 if res.wasSuccessful() else 1)
