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
        self.assertEqual(check_locus("regime.custody.state", "undamaged"), ["regime.custody.state"])   # V2c
        self.assertIn("BY THE EVENT", LOCUS_DEFINITIONS["physical_damage"])
        self.assertIn("RECORD FACT", LOCUS_DEFINITIONS["_site"])

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
        self.assertIn("three-grader coding", header["_header"]); self.assertIn("DeepSeek", header["_header"]); self.assertIn("GPT", header["_header"])
        graded = [r for r in body if r.get("graders", {}).get("round1")]
        self.assertEqual(len(graded), 13)                                      # + ungraded verbatim rows C1-C4, A1, A2
        t = locus_tally.tally(body)
        self.assertEqual(t["coarse"], {"regime": 10, "mixed": 2, "physical_damage": 1})
        self.assertEqual(t["second_grader_rows"], 13)
        self.assertFalse(header["tally_citable"]["round1_sub_axis"])
        g2 = locus_tally.tally(body, key="second_grader_locus")
        self.assertEqual(g2["coarse"], {"regime": 11, "mixed": 2, "physical_damage": 0})
        a = locus_tally.agreement(body)
        self.assertEqual(a["site_agree"], 12)
        self.assertEqual(a["any_regime_component"], [12, 13])
        self.assertEqual(a["top_level_agree"], 9)
        self.assertAlmostEqual(a["kappa"], 0.05, places=1)
        self.assertEqual(a["pure_physical_damage_rows"], [1, 0])
        self.assertEqual(a["sub_axis"], {"comparable": 12, "exact": 2, "overlap": 4, "disjoint": 6})
        self.assertFalse(a["N-1_fires"])
        self.assertEqual([r["row"] for r in graded if r["site"] != r["second_grader_site"]], [10])

    def test_site_is_a_record_fact(self):
        header, body = locus_tally.load(os.path.join(HERE, "fixtures", "maria_locus.jsonl"))
        for r in body:
            if r.get("graders", {}).get("round1"):
                self.assertIn(r["site_record"], SITES)
                self.assertIn("site_field", r["graders"]["round1"]["gpt"])   # graded sites retained as history only
            else:
                self.assertIsNone(r["locus"])                                  # verbatim rows are ungraded
        self.assertIn("RECORD FACT", header["site_rule"])

    def test_three_way_figures_computed_from_rows(self):
        _, body = locus_tally.load(os.path.join(HERE, "fixtures", "maria_locus.jsonl"))
        tw = locus_tally.three_way(body)
        self.assertEqual(tw["any_regime_component"], {"claude_opus_5": 12, "deepseek": 13, "gpt": 13})
        self.assertEqual(tw["pure_physical_damage"], {"claude_opus_5": 1, "deepseek": 0, "gpt": 0})
        self.assertEqual(tw["pairwise_top_level_agree"], {"claude_opus_5-deepseek": 9, "claude_opus_5-gpt": 8, "deepseek-gpt": 11})
        self.assertEqual(tw["damage_flag_unanimous_no_rows"], [1, 3, 4, 5, 6, 7, 8, 9])
        self.assertEqual(tw["damage_flag_unanimous_yes_rows"], [])
        self.assertEqual(tw["sub_axis_majority"][5], None)                  # three graders, three answers
        self.assertGreaterEqual(len(tw["site_vs_record_mismatches"]["gpt"]), 5)

    def test_round2_figures_computed_from_rows(self):
        _, body = locus_tally.load(os.path.join(HERE, "fixtures", "maria_locus.jsonl"))
        r2 = locus_tally.round2(body)
        self.assertEqual((r2["n"], r2["exact"], r2["overlap"], r2["disjoint"], r2["disjoint_rows"]), (14, 11, 2, 1, ["9"]))
        self.assertAlmostEqual(r2["mean_jaccard"], 0.857, places=3)
        self.assertAlmostEqual(r2["kappa_label_sets"], 0.66, places=1)
        self.assertEqual(r2["physical_damage_rows"], [2, 1])
        self.assertGreaterEqual(r2["custody_in_both"], 8)
        for _, g in [(s, g) for r in body for s, g in r["graders"]["round2"].items()]:
            if _ == "5":
                self.assertEqual((g["gpt"], g["deepseek"]), ("regime.learning", "regime.learning"))   # class confirmed

    def test_v10b_instrument_not_evaluable_until_extraction(self):
        for name in ("katrina_locus.jsonl", "gao2018_locus.jsonl"):
            header, body = locus_tally.load(os.path.join(HERE, "fixtures", name))
            self.assertTrue(header["titles_verified"]); self.assertFalse(header["pages_verified"])
            rt = locus_tally.report_type_split(body, None)
            self.assertFalse(rt["evaluable"])
            self.assertGreater(rt["stated_cause_pending"], 0)
            for r in body:
                self.assertIn(r["doc_type"], ("audit", "review", "self-review", "press"))
        src = json.load(open(os.path.join(HERE, "fixtures", "sources.json")))["docs"]
        self.assertTrue(src["M1"]["fetched"] is True and src["K3"]["fetched"] is True)     # full / partial text loaded
        self.assertFalse(src["K1"]["fetched"])                                            # logistics chapter unread
        tmpl = [json.loads(l) for l in open(os.path.join(HERE, "fixtures", "maria_locus_round3_template.jsonl")) if l.strip()]
        self.assertEqual(len(tmpl) - 1, 17)                                        # 14 rows + C1-C3 candidates
        self.assertTrue(all(r["oig_verbatim"] and r["oig_page"] is not None for r in tmpl[1:]))   # verbatim filled
        self.assertTrue(all(r["grader_gpt"] and r["grader_deepseek"] and r["grader_kimi"] for r in tmpl[1:]))   # v0.2: P0 codings loaded
        self.assertTrue(tmpl[0]["per_row_codings_loaded"])
        rep = locus_tally.round3(tmpl[1:], tmpl[0])
        self.assertTrue(rep["computed"])                                               # computed from the rows
        self.assertEqual(rep["unanimous_full_enum"], "11/17")                          # equals the reported aggregate
        self.assertEqual(rep["unanimous_full_enum"], tmpl[0]["reported_aggregates"].get("unanimous_full_enum", "11/17"))
        # once codings are present the same function computes: synthetic fill on a copy
        filled = [dict(r, grader_gpt="regime.custody.state", grader_deepseek="regime.custody.state", grader_kimi="regime.custody.state") for r in tmpl[1:]]
        comp = locus_tally.round3(filled, tmpl[0])
        self.assertTrue(comp["computed"]); self.assertEqual(comp["unanimous_full_enum"], "17/17")
        self.assertEqual(comp["unanimous_custody_state_rows"], 17)
        row9 = next(r for r in filled if r["row"] == "9")
        row9["grader_gpt"] = "physical_damage"                                         # row 9 site undamaged -> violation
        comp = locus_tally.round3(filled, tmpl[0])
        self.assertEqual(comp["rule_violations"], [("9", "gpt")])
        sc = [json.loads(l) for l in open(os.path.join(HERE, "fixtures", "stated_causes_grader_template.jsonl")) if l.strip()]
        self.assertGreaterEqual(len(sc) - 1, 8)
        self.assertTrue(all(r["text"] for r in sc[1:]))
        self.assertEqual([r["id"] for r in sc[1:] if r["grader_gpt"] is None], ["K2-1"])   # v0.2: all but K2-1 coded (P0 graders)
        self.assertIn("NOT A TEST", sc[0]["v10b_status"])
        _, mbody = locus_tally.load(os.path.join(HERE, "fixtures", "maria_locus.jsonl"))
        wd = locus_tally.within_document(mbody)
        self.assertFalse(wd["M1"]["evaluable"])                                        # maria_locus.jsonl stubs stay null; V10c reads the results file
        self.assertEqual(wd["M1"]["stated_cause"]["ungraded"], 3)                     # A1, A2, C4

    def test_record_sites_from_the_source_and_invalid_codings_flagged(self):
        _, body = locus_tally.load(os.path.join(HERE, "fixtures", "maria_locus.jsonl"))
        by = {str(r["row"]): r for r in body}
        self.assertEqual(by["9"]["site_record"], "undamaged")
        self.assertEqual(by["10"]["site_record"], "unknown")
        self.assertEqual(by["10"]["site_record_history"]["section4_table"], "undamaged")
        self.assertEqual(by["8"]["graders"]["round2"]["8b"]["site_record"], "damaged")
        self.assertTrue(all(by[k].get("oig_verbatim") for k in map(str, range(1, 14))))
        self.assertFalse(by["9"]["graders"]["round2"]["9"]["gpt_schema_valid_under_record_site"])
        self.assertTrue(by["9"]["graders"]["round2"]["9"]["deepseek_schema_valid_under_record_site"])
        self.assertFalse(by["10"]["graders"]["round1"]["deepseek"]["schema_valid_under_record_site"])
        r2 = locus_tally.round2(body)
        self.assertEqual(r2["schema_invalid_under_record_site"], [("9", "gpt")])
        self.assertEqual((r2["excluding_invalid"]["n"], r2["excluding_invalid"]["exact"]), (13, 11))
        self.assertIn("C2", by); self.assertIsNone(by["C2"]["locus"]); self.assertIn("2,402", by["C2"]["oig_verbatim"])


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


class V2d_authority_instrument(unittest.TestCase):
    def test_prompts_scorer_and_fixture(self):
        sys.path.insert(0, os.path.join(HERE, "v2d_authority"))
        import v2d
        for a in v2d.LEVELS:
            for s in v2d.LEVELS:
                p, ids = v2d.prompt(a, s)
                self.assertEqual(ids, ["1", "2", "9", "11", "C1", "C3", "13"])
                self.assertNotIn("FEMA", p); self.assertNotIn("Puerto Rico", p); self.assertIn("the island", p)
                self.assertIn(v2d.STIM["source"][s], p); self.assertIn(v2d.STIM["agent"][a]["name"], p)
        self.assertEqual(len(v2d.plan(7)), 12)
        self.assertEqual({r["grader"] for r in v2d.plan(7)}, set(v2d.GRADERS))
        out = v2d.score_file(os.path.join(HERE, "v2d_authority", "runs", "constructed.jsonl"))
        self.assertTrue(out["constructed"])                                       # never mistaken for a result
        self.assertEqual(out["n_runs"], 12)
        self.assertTrue(all(c["anchors_hold_all"] for c in out["cells"].values()))
        self.assertIn(out["reading"].split(":")[0], ("NULL", "DEFERENCE", "SYMPATHY", "SOURCE or INTERACTION effect on external share; see contrasts"))
        # a rule violation (physical_damage at an undamaged record site) is counted, not silently dropped
        sc = v2d.score_run({"raw_response": "\n".join("FINDING %d: physical_damage" % i for i in range(1, 8))})
        self.assertEqual(sc["invalid"], 5); self.assertFalse(sc["anchors_hold"])


class V2c_round3_results(unittest.TestCase):
    """WORK ORDER v0.2 section 2: every reported figure recomputed from fixtures/maria_locus_round3_results.jsonl."""
    RP = os.path.join(HERE, "fixtures", "maria_locus_round3_results.jsonl")

    def _r2map(self):
        _, body = locus_tally.load(os.path.join(HERE, "fixtures", "maria_locus.jsonl"))
        m = {}
        for r in body:
            for sub, g in (r.get("graders", {}).get("round2") or {}).items():
                m[sub] = g
        return m

    def test_round3_block_reproduces_section_2(self):
        b = locus_tally.round3_block(self.RP, self._r2map())
        self.assertTrue(b["computed"]); self.assertEqual(b["rows"], 17)
        self.assertEqual(b["pairwise_exact_full"], {"G-D": 14, "G-K": 11, "D-K": 13})
        self.assertEqual(b["pairwise_exact_collapsed"], {"G-D": 15, "G-K": 13, "D-K": 15})
        self.assertEqual((b["unanimous_full"], b["unanimous_collapsed"]), ("11/17", "13/17"))
        self.assertEqual(b["any_regime_component"], {"gpt": 15, "deepseek": 16, "kimi": 15})
        self.assertEqual(b["pure_physical_damage"], {"gpt": 2, "deepseek": 1, "kimi": 2})
        self.assertEqual(b["pure_physical_damage_unanimous_rows"], ["13"])
        cs = b["custody_split"]
        self.assertEqual((cs["custody_labels"], cs["custody_state"]), (28, 24))
        self.assertEqual(len(cs["all_custody_rows"]), 9)
        self.assertEqual(cs["unanimous_custody_state_rows"], ["1", "3", "8a", "8b", "10", "12", "C2"])
        self.assertEqual(b["rule_violations"], [("9", "gpt")])                    # physical_damage at an undamaged record site, kept
        self.assertEqual(b["stability_r2_to_r3_collapsed"], {"gpt": "14/14", "deepseek": "13/14"})
        self.assertEqual(b["four_family_unanimous_collapsed"], "13/17"); self.assertTrue(b["same_set_as_three_family"])
        self.assertTrue(b["gemini_probe"]["P0"].startswith("REFUSED"))
        self.assertEqual(b["name_effect"]["deepseek"]["identical"], "17/17")
        self.assertEqual(b["name_effect"]["gpt"]["identical"], "16/17")
        self.assertEqual(b["name_effect"]["gpt"]["flips"], {"9": ("physical_damage", "regime.custody.state")})
        # rollup A2: kimi P1 resolved (the earlier copy was a paste duplication)
        self.assertEqual(b["name_effect"]["kimi"]["identical"], "14/17")
        self.assertEqual(sorted(b["name_effect"]["kimi"]["flips"]), ["11", "4", "C1"])
        # mixed-family (P0 x3 + gemini P1) open rows still include 11; the P1 four-family does not
        self.assertEqual(sorted(b["open_rows"]), ["11", "2", "9", "C3"])
        self.assertIn("RESOLVED", b["kimi_P1"])
        p1 = b["p1_four_family"]
        self.assertEqual(p1["graders"], ["gemini", "deepseek", "gpt", "kimi"])
        self.assertEqual(p1["unanimous_collapsed"], "14/17")
        self.assertEqual(sorted(p1["open_rows"]), ["2", "9", "C3"])
        nd = b["name_effect_damage"]
        self.assertEqual(nd["graders_dropping_damage"], ["gpt", "kimi"]); self.assertEqual(nd["graders_adding_damage"], [])
        self.assertTrue(nd["all_dropped_moved_to_custody"])
        self.assertEqual((nd["per_grader"]["gpt"]["damage_P0"], nd["per_grader"]["gpt"]["damage_P1"]), (2, 1))
        self.assertEqual((nd["per_grader"]["kimi"]["damage_P0"], nd["per_grader"]["kimi"]["damage_P1"]), (2, 1))
        self.assertEqual(nd["per_grader"]["deepseek"]["dropped"], {})
        self.assertIn("candidate", nd["status"])                                     # signed candidate, not a finding
        self.assertEqual(b["grader_identity"]["verified"], False)                   # identity is a claim (A4)

    def test_kimi_P1_resolved_and_counted(self):
        hdr, R, unverified = locus_tally._load_results(self.RP)
        self.assertNotEqual(R["P1"]["kimi"], R["P1"]["gemini"])                    # the real run differs from gemini P1
        self.assertEqual(sorted(r for r in R["P1"]["kimi"] if R["P1"]["kimi"][r] != R["P1"]["gemini"][r]), ["11", "12", "2", "9"])   # 4 rows differ
        self.assertEqual(unverified, set())                                        # nothing excluded now
        self.assertEqual(set(R["P0"]), {"gpt", "deepseek", "kimi"})              # gemini P0 refused
        self.assertEqual(set(R["P1"]), {"gemini", "deepseek", "gpt", "kimi"})
        b = locus_tally.round3_block(self.RP)
        self.assertEqual(b["four_family_unanimous_collapsed"], "13/17")           # mixed: gpt, deepseek, kimi (P0) + gemini (P1)
        # the exclusion path still works: an unverified line is dropped from every figure
        import tempfile
        rows = [json.loads(l) for l in open(self.RP) if l.strip()]
        for r in rows[1:]:
            if r["variant"] == "P1" and r["grader"] == "kimi":
                r["verified"] = False
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        b2 = locus_tally.round3_block(f.name)
        self.assertEqual(b2["name_effect"]["kimi"], "UNVERIFIED")
        self.assertEqual(b2["p1_four_family"]["graders"], ["gemini", "deepseek", "gpt"])
        os.unlink(f.name)

    def test_v10c_M1_computed_A1_unanimous(self):
        v = locus_tally.v10c(self.RP, os.path.join(HERE, "fixtures", "stated_causes_grader_template.jsonl"))
        self.assertTrue(v["A1_unanimous"])
        self.assertEqual(set(v["A1"].values()), {"mixed(physical_damage,regime.urgency)"})
        for g in ("gpt", "deepseek", "kimi"):
            self.assertEqual(v["M1"][g]["stated_causes_external_share"], 0.667)
            self.assertLess(v["M1"][g]["findings_external_share"], 0.2)         # 0.118 / 0.059 / 0.176
        self.assertTrue(v["K3"].startswith("NOT EVALUABLE"))

    def test_pending_small_tests_templates(self):
        rows = [json.loads(l) for l in open(os.path.join(HERE, "fixtures", "pending", "small_tests.jsonl")) if l.strip()]
        ids = {r.get("id") for r in rows}
        for t in ("T-a", "T-b", "T-d"):
            self.assertIn(t, ids, t)
        self.assertIn("T-c", rows[0]["kimi"])                                     # operator step, not a template
        ta = next(r for r in rows if r.get("id") == "T-a")
        self.assertIn("event_damage", json.dumps(ta))
        td = next(r for r in rows if r.get("id") == "T-d")
        self.assertIn("gemini", json.dumps(td))
        for r in rows[1:]:
            self.assertFalse(r.get("result"), r.get("id"))                        # nothing filled: unrun


class V2d_prompt_files(unittest.TestCase):
    def test_four_files_differ_by_exactly_one_factor(self):
        sys.path.insert(0, os.path.join(HERE, "v2d_authority"))
        import v2d
        paths = v2d.emit_prompt_files(os.path.join(HERE, "v2d_authority", "prompts"))
        self.assertEqual(sorted(os.path.basename(p) for p in paths.values()),
                         ["authority_Ahigh_Shigh.txt", "authority_Ahigh_Slow.txt", "authority_Alow_Shigh.txt", "authority_Alow_Slow.txt"])
        for (a, s), path in paths.items():
            oa = "low" if a == "high" else "high"; os_ = "low" if s == "high" else "high"
            d = v2d.neighbor_diff(path, paths[(oa, s)])
            self.assertTrue(d and all(v2d._mask_agent(x, a) == v2d._mask_agent(y, oa) for x, y in d))
            self.assertEqual(v2d.neighbor_diff(path, paths[(a, os_)]), [(v2d.STIM["source"][s], v2d.STIM["source"][os_])])
        for rid in v2d.ROW_IDS:                                                     # verbatim apart from declared SUBS
            row = next(r for r in v2d.STIM["rows"] if r["id"] == rid)
            for a in v2d.LEVELS:
                self.assertTrue(v2d.only_declared_substitutions(v2d.VERBATIM[rid]["text"], v2d.render_row(row, a), a)[0], rid)
        self.assertEqual(v2d.GRADERS, ("gpt", "deepseek", "gemini"))              # kimi joins once T-c verifies its copy


class A4_A5_canaries_and_prompt_files(unittest.TestCase):
    def test_grading_prompts_and_canary_logic(self):
        import grading_prompt as gp
        gp.selftest()                                                              # emits prompts/, diff-asserts T-a/T-b/T-d/V10c
        for name in ("P0_reconstructed", "P1_reconstructed", "T-a_row9_event_damage", "T-b_row9_P0", "T-d_gemini_P2_no_carrier_rows", "V10c_M1_stated_causes"):
            self.assertTrue(os.path.exists(os.path.join(HERE, "prompts", name + ".txt")), name)
        self.assertEqual(gp.CANARIES, (("13", "physical_damage"), ("5", "regime.learning")))
        # canary answers are unanimous on every verified grading loaded
        hdr, R, unverified = locus_tally._load_results(os.path.join(HERE, "fixtures", "maria_locus_round3_results.jsonl"))
        for variant in R:
            for g in R[variant]:
                for row, ans in gp.CANARIES:
                    self.assertEqual(R[variant][g][row], ans, (variant, g, row))
        # results slots are empty: no run file exists yet
        self.assertFalse(os.path.exists(os.path.join(HERE, "fixtures", "grading_runs.jsonl")))

    def test_v2d_run_record_carries_grader_identity(self):
        sys.path.insert(0, os.path.join(HERE, "v2d_authority"))
        import v2d
        self.assertIn("grader_identity", v2d.RUN_FIELDS)


class A7_A8_money_term_and_field_fix(unittest.TestCase):
    def test_money_term_gate(self):
        import money_term as mt
        mt.selftest()
        res = mt.run_cases()
        self.assertEqual({k: v["verdict"] for k, v in res.items()},
                         {"obermeyer_cost_as_need": "PROXY_UNROOTED", "solow_cost_share": "CIRCULAR", "choice_system_token": "DECLARED"})
        self.assertEqual(set(mt.VERDICTS), {"NATIVE", "DECLARED", "PROXY_UNROOTED", "CIRCULAR"})

    def test_field_fix_check(self):
        import field_fix as ff
        ff.selftest()
        res = ff.run_cases()
        self.assertEqual(res["wax_on_terminal"]["verdict"], "SIGN_INVERSION")
        self.assertEqual(res["zip_tie_on_sliding_mount"]["verdict"], "DOF_DELETION")
        self.assertEqual(res["penny_shim_unrecorded"]["verdict"], "STATE_NOT_UPDATED")
        # the ledger's V11 check and this one agree on the keys
        from ledger import FIELD_FIX_KEYS
        self.assertEqual(set(FIELD_FIX_KEYS), {"sign", "dof", "state_updated"})


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
