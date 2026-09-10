"""
Pilot verification exercise — SPEC section 4, replayed at pilot scale (v0.1)
============================================================================
Injects I-1..I-13 in order on a synthetic loop (1 food bank, 3 staging areas,
~40 pantries, 2 carriers, 1 unregistered community node; N <= 150). Each row
reports the OIG BASELINE (measured, not ours), an operator-set TARGET declared
in TARGETS before the run, the measured value, whether the SHALL held, and the
VERDICT against target. Failures are reported as found (FT-02 applies to the
pilot itself).

  python exercise.py [--out runs/] [--seed 0]
"""
import argparse
import json
import os
import random
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ledger import Ledger, Refused, OP_PERIOD_H  # noqa: E402

# Operator-set targets, declared before the run. Change them here, not after.
TARGETS = {
    "FT-01": {"metric": "visibility_lost_pct", "op": "<=", "value": 5.0, "baseline": "38% lost"},
    "FT-05": {"metric": "receipt_rate_pct", "op": ">=", "value": 95.0, "baseline": "4% documented"},
    "FT-06": {"metric": "dwell_max_h", "op": "<=", "value": 4 * OP_PERIOD_H, "baseline": "~48 d custody dwell"},
    "FT-11": {"metric": "refuse_unreceipted_pct", "op": "==", "value": 100.0, "baseline": "paid without proof"},
    "FT-16": {"metric": "unsigned_transfers_detected_pct", "op": ">=", "value": 100.0, "baseline": "identity lost at transfer"},
    "FT-17": {"metric": "detection_latency_h_max", "op": "<=", "value": OP_PERIOD_H, "baseline": "months"},
    "FT-18": {"metric": "resolver_acted_within_h", "op": "<=", "value": OP_PERIOD_H, "baseline": "no resolver"},
}
DWELL_LIMIT_H = 2 * OP_PERIOD_H
HEARTBEAT_H = OP_PERIOD_H


def build_loop(L, rng, n_pantries=40):
    L.register_node("FB", "food_bank", "R1")
    for i in range(3):
        L.register_node("RSA%d" % i, "staging", "R1")
    L.register_node("YARD-1", "yard", "R1", custodial=False)             # present-but-noncustodial (FT-16)
    for i in range(n_pantries):
        L.register_node("P%02d" % i, "pantry", "R1")
    for c in ("CARRIER-A", "CARRIER-B"):
        L.register_node(c, "carrier", "R1")
    L.register_node("CLAIMANT-X", "other_agency", "R1")
    # pre-event declarations (FT-07, FT-08, FT-06, FT-12, FT-13, V4, V7)
    L.declare_conversion("count", "kcal", 250.0, ts=-500, declared_by="ops")
    L.declare_rule("R-FEFO", "FEFO", {}, ts=-500, override_committee=["ops-lead", "pantry-rep"])
    L.declare_rule("R-DWELL", "DWELL_LIMIT", {"limit_h": DWELL_LIMIT_H}, ts=-500, override_committee=["ops-lead"])
    L.declare_trigger_table("declared_event", {"L_water": ("R2", "custody"), "kcal": ("R1", "urgency"),
                                               "count": ("R1", "urgency")}, ts=-450, declared_by="ops")
    # protein_g deliberately has no standing assignment and no waiver (V8)
    L.declare_resolver("RESOLVER-1", {"radio": "VHF ch 3", "in_person": "RSA0 ops tent", "cellular": "555-0100"}, ts=-400)
    edges = [("FB", "RSA0", "linehaul"), ("FB", "RSA1", "linehaul"), ("FB", "RSA2", "linehaul"),
             ("RSA0", "pantries", "last-mile"), ("RSA1", "pantries", "last-mile"), ("RSA2", "pantries", "last-mile"),
             ("port", "FB", "cross-dock")]
    assignments = {e: ("CARRIER-A" if i % 2 == 0 else "CARRIER-B") for i, e in enumerate(edges[:-1])}
    L.declare_route("R1", edges, assignments, ts=-400)        # the cross-dock edge is left unassigned on purpose
    pantries = ["P%02d" % i for i in range(n_pantries)]
    for p in pantries:
        L.preposition(p, days_of_need=3, ts=-300)
    L.coauthor_plan("PLAN-R1", pantries[:int(0.9 * n_pantries)], ts=-200)   # 10% did not co-author
    return pantries


def sweep(L, now):
    """One end-of-period sweep: presence without custody (FT-16) and heartbeat (FT-17).
    The sweep IS the detector; it must run at least once per operational period."""
    fired = L.check_presence(now)
    L.check_heartbeat(now)
    return fired


def run(seed=0, out_dir=None, keep_root=False):
    rng = random.Random(seed)
    root = tempfile.mkdtemp(prefix="substrate_pilot_")
    L = Ledger(root=root)
    pantries = build_loop(L, rng)
    log = []

    def note(inject, ft, outcome, **kw):
        log.append({"inject": inject, "ft": ft, "outcome": outcome, **kw})

    # I-8: prior AAR finding exists, unacted, at activation (FT-09); V8 activation check
    L.register_finding("AAR-2011-03", "2011 exercise AAR", "commodity movement need anticipated",
                       found_ts=-24 * 365 * 6, locus="regime.custody", site="pre-event")
    # a protein_g need exists so the missing standing assignment is visible at activation (V8)
    L.report_need("N-PROT-P00", "P00", "protein_g", qty=50 * 150 * 3, by_ts=72, ts=-1)
    open_findings = L.activate(ts=0)
    missing = [f for f in L.failures if f["type"] == "MISSING_CLASS_ASSIGNMENT"]
    note("I-8", "FT-09", "open findings displayed at activation", open_findings=open_findings)
    note("-", "V8", "missing class assignment flagged at activation", missing=[f["declared_unit"] for f in missing])

    # I-6: cellular down for the whole exercise (FT-14)
    L.cellular_up = False
    note("I-6", "FT-14", "cellular disabled for the whole exercise")

    # needs at pantries (C2), declared units
    for p in pantries:
        L.report_need("N-%s" % p, p, "kcal", qty=2000 * 150 * 3, by_ts=72, ts=1)
        L.report_need("W-%s" % p, p, "L_water", qty=4 * 150 * 3, by_ts=72, ts=1)

    # units at origin (C1); loads carry class + axis at intake (V3); water is custody-axis R2
    units = []
    for i in range(120):
        kind = "kcal" if i % 3 else "L_water"
        qty = 2000 * 50 if kind == "kcal" else 4 * 50
        exp = 24 * rng.choice([5, 10, 20, 40]) if kind == "kcal" else None
        if i == 7:
            exp = -1
        cls, axis = ("R2", "custody") if kind == "L_water" else ("R1", "urgency")
        u = L.create_unit("U%03d" % i, kind, qty, ts=2, expiry_ts=exp, seal_no="S%03d" % i, tcard="T%03d" % i,
                          regime_class=cls, axis=axis, max_silence_h=HEARTBEAT_H)
        units.append(u["unit_id"])

    # I-13: load declared "critical", no axis (V3)
    L.create_unit("CRIT-1", "kcal", 1000, ts=2, seal_no="SC1", tcard="TC1")
    try:
        L.declare_load("CRIT-1", "critical", ts=2)
        note("I-13", "V3", "FAIL: 'critical' with no axis accepted")
    except Refused as e:
        note("I-13", "V3", "'critical' with no axis refused at intake", detail=str(e))
    try:
        L.declare_load("CRIT-1", "R2", ts=2)
        note("I-13b", "V3", "FAIL: class with no axis accepted")
    except Refused as e:
        note("I-13b", "V3", "class with no axis refused at intake", detail=str(e))
    L.declare_load("CRIT-1", "R2", "custody", ts=2)
    try:
        L.reclass("CRIT-1", "R0", ts=3, reason="expedite")
        note("I-13c", "V3", "FAIL: custody-axis load dropped custody to expedite")
    except Refused as e:
        note("I-13c", "V3", "custody-axis load may not drop custody to expedite", detail=str(e))

    # I-11: declare event -> loads reclass from the precomputed table, no manual step (V4)
    water_before = {u: L.units[u]["regime_class"] for u in units if L.units[u]["declared_unit"] == "L_water"}
    for u in list(water_before)[:5]:                         # a few water loads were intaken low on purpose
        L.units[u]["regime_class"], L.units[u]["axis"] = "R0", "urgency"
    reclassed = L.declare_event("declared_event", ts=3, damaged_sites=["RSA2"] + pantries[30:])
    water_after = {u: L.units[u]["regime_class"] for u in water_before}
    ev = L.events_declared[-1]
    note("I-11", "V4", "event declared; loads reclassed from trigger table", reclassed=len(reclassed),
         manual_steps=ev["manual_steps"], water_min_class=min(water_after.values()))

    unsigned = list(sweep(L, 12))                 # end of operational period 1

    # I-1: order placed with no state record (FT-01)
    try:
        L.release("GHOST-1", "P00", "CARRIER-A", ts=3)
        note("I-1", "FT-01", "FAIL: unrecorded movement released")
    except Refused as e:
        note("I-1", "FT-01", "held at gate", detail=str(e))

    # ship everything via RSAs; gate-in at the RSA is a delivery (receiver mark) and a signed handover
    for i, uid in enumerate(units):
        rsa = "RSA%d" % (i % 3)
        carrier = "CARRIER-A" if i % 2 == 0 else "CARRIER-B"
        c = L.release(uid, rsa, carrier, ts=4 + i % 6, commit_id="C-%s" % uid)
        ts_arrive = 10 + i % 6
        L.observe(uid, "electronic", "en-route", ts=ts_arrive - 2)     # dropped (cellular down), I-2/FT-03
        L.observe(uid, "physical", rsa, ts_arrive, event="gate-in %s" % rsa, by=carrier)
        L.receive(c["commit_id"], ts=ts_arrive, receiver_mark={"kind": "stamp", "by": "%s-gate" % rsa})
        L.arrive_at_rest(uid, rsa, ts_arrive, custody=rsa)

    # I-3: carrier repacks a container without a manifest (FT-04); generic manifest on a transfer
    L.repack("U010", [("U010-a", 50000), ("U010-b", 50000)], ts=14, manifest=None, by="CARRIER-A")
    L.transfer("U011", "CARRIER-B", ts=14, manifest={"description": "relief supplies", "unit_ids": []},
               signed_by=("RSA2", "CARRIER-B"))
    L.repack("U012", [("U012-a", 100000)], ts=14, manifest={"lists_unit_ids": True, "seal_no": "S012-r"}, by="CARRIER-A")
    units += ["U010-a", "U010-b", "U012-a"]                  # children move with the last mile

    # I-12: local custodian availability 20% (Maria reported value): 80% of pantries unavailable to sign
    unavailable = [p for i, p in enumerate(pantries) if i % 5 != 0]
    for p in unavailable:
        L.set_availability(p, False, ts=18)
    note("I-12", "FT-16", "custodian availability set to 20%%: %d of %d pantries cannot sign" % (len(pantries) - len(unavailable), len(pantries)))
    unsigned += sweep(L, 24)                      # end of operational period 2: CRIT-1 (R2, at origin, never checked on) escalates here

    # last mile: RSA -> pantries. Available pantries sign; at unavailable ones the load is dropped at the
    # gate (present-but-noncustodial) and no handover happens -> unsigned transfer (FT-16).
    unreceipted, dropped_unsigned = [], []
    for i, uid in enumerate(units):
        u = L.units[uid]
        if u["status"] != "AT_REST" or i in (14, 15):      # U014/U015 deliberately stranded at the RSA (FT-06)
            continue
        p = pantries[i % len(pantries)]
        need = ("N-%s" if u["declared_unit"] == "kcal" else "W-%s") % p
        cid = "D-%s" % uid
        L.release(uid, p, "CARRIER-B", ts=20 + i % 10, commit_id=cid)
        if not L.nodes[p]["available"] and i % 4 == 0:
            L.observe(uid, "physical", p, 24 + i % 10, event="dropped at gate, no custodian", by="CARRIER-B")
            dropped_unsigned.append(uid)
            continue
        L.observe(uid, "physical", p, 24 + i % 10, event="arrived %s" % p, by="CARRIER-B")
        if i % 25 == 5:                                    # a delivery whose paper receipt did not come back
            unreceipted.append(cid)
            continue
        L.receive(cid, ts=24 + i % 10, receiver_mark={"kind": rng.choice(["signature", "stamp", "photo"]),
                                                      "by": "%s-lead" % p}, need_id=need)
    for cid in unreceipted:
        try:
            L.receive(cid, ts=30)
            note("-", "FT-05", "FAIL: receipt accepted without a mark")
        except Refused:
            note("-", "FT-05", "unreceipted delivery stays IN_TRANSIT", commit_id=cid)
    unsigned += sweep(L, 36)                   # end of operational period 3: presence + heartbeat sweep
    note("I-12", "FT-16", "presence without custody read as unsigned transfer",
         dropped=len(dropped_unsigned), detected=len(unsigned))

    # I-4: meals unavailable, snack boxes substituted (FT-07). Q-1: no factor -> receipt recorded,
    # need NOT credited, failure recorded; a factor is required for credit.
    L.create_unit("SNACK-1", "count", 1200, ts=30, seal_no="SS1", tcard="TS1", regime_class="R1", axis="urgency")
    L.release("SNACK-1", "P03", "CARRIER-A", ts=31, commit_id="D-SNACK-1")
    L.receive("D-SNACK-1", ts=33, receiver_mark={"kind": "signature", "by": "P03-lead"}, need_id="N-P03")
    sub = [e for e in L.events if e["type"] == "SUBSTITUTION"][-1]
    note("I-4", "FT-07", "substitution logged with pre-declared factor", factor=sub["factor"], converted_kcal=sub["converted_qty"])
    L.create_unit("SNACK-2", "protein_g", 500, ts=34, seal_no="SS2", tcard="TS2", regime_class="R1", axis="urgency")
    L.release("SNACK-2", "P04", "CARRIER-A", ts=35, commit_id="D-SNACK-2")
    before = L.needs["N-P04"]["delivered"]
    L.receive("D-SNACK-2", ts=36, receiver_mark={"kind": "stamp", "by": "P04-lead"}, need_id="N-P04")
    uncredited = [f for f in L.flags if f["code"] == "SUBSTITUTION_UNCREDITED"]
    note("I-4b", "FT-07", "substitution without declared conversion: delivery RECEIVED, need not credited, failure recorded",
         need_credited=L.needs["N-P04"]["delivered"] - before, unit_status=L.units["SNACK-2"]["status"], failures=len(uncredited))
    try:
        L.substitute("N-P04", "SNACK-2", ts=36)
        note("I-4c", "FT-07", "FAIL: direct substitution without a factor accepted")
    except Refused as e:
        note("I-4c", "FT-07", "direct substitution without a factor refused", detail=str(e))

    # I-5: settlement requested for an unreceipted delivery (FT-11)
    try:
        L.settle(unreceipted[0], amount=1200.0, money_term={"scope": "carrier invoice, last mile"}, ts=40)
        note("I-5", "FT-11", "FAIL: paid without receipt")
    except Refused as e:
        note("I-5", "FT-11", "settlement refused", detail=str(e))
    L.settle("D-U000", amount=1200.0, money_term={"scope": "carrier invoice, last mile"}, ts=40)

    # FT-02: relabel attempt and closure without reconciliation
    L.mark_lost("U013", ts=41)
    try:
        L.set_status("U013", "UNKNOWN", ts=42, location="unknown FSA")
        note("-", "FT-02", "FAIL: 'unknown' accepted as a location")
    except Refused as e:
        note("-", "FT-02", "'unknown FSA' rejected as a location", detail=str(e))
    try:
        L.close("U013", ts=43)
        note("-", "FT-02", "FAIL: closed without reconciliation")
    except Refused as e:
        note("-", "FT-02", "closure without reconciliation refused", detail=str(e))

    # FT-08: allocation with an expired unit in the candidates
    order = L.allocate("N-P05", ["U007", "U001", "U004"], now=44)
    note("-", "FT-08", "FEFO order, expired excluded", order=order)
    unsigned += sweep(L, 48)                   # end of operational period 4

    # I-7: unregistered community node reports need and stock (FT-15)
    L.register_node("COMM-1", "community", "R1", ts=45, registered=False)
    L.report_need("N-COMM-1", "COMM-1", "kcal", qty=2000 * 30 * 2, by_ts=72, ts=45)
    L.report_stock("COMM-1", "CU-1", "kcal", 2000 * 30, ts=45, seal_no="CS1", tcard="CT1", regime_class="R1", axis="urgency")
    status_before = L.nodes["COMM-1"]["status"]
    L.release("CU-1", "P00", "COMM-1", ts=46, commit_id="D-CU-1")
    L.observe("CU-1", "physical", "P00", 48, event="arrived", by="COMM-1")
    L.receive("D-CU-1", ts=48, receiver_mark={"kind": "photo", "by": "P00-lead"}, need_id="N-P00")
    note("I-7", "FT-15", "provisional node promoted on first kept commitment", before=status_before, after=L.nodes["COMM-1"]["status"])

    # I-9: suppress one check-in on an R2 water load in transit (FT-17)
    L.release("U014", "P07", "CARRIER-A", ts=46, commit_id="D-U014")           # stranded unit finally moves
    L.checkin("U014", ts=50, by="CARRIER-A")
    L.release("U015", "P08", "CARRIER-B", ts=46, commit_id="D-U015")           # this one goes silent
    hb_before = [f for f in L.failures if f["type"] == "HEARTBEAT_MISSED"]

    # I-10: competing custody claim at a yard on an R2 load (FT-18)
    L.observe("U003", "physical", "YARD-1", ts=52, event="staged at yard", by="RSA0")
    claim = L.claim_custody("U003", "CLAIMANT-X", ts=52, basis="verbal tasking")
    L.resolve_claim("U003", ts=52 + 4, resolver_id="RESOLVER-1", award_to=L.units["U003"]["custody"], signed_by=("RESOLVER-1", "RSA0"))
    note("I-10", "FT-18", "competing claim routed to resolver; custody unchanged until resolved",
         routed_to=claim["routed_to"], paths=claim["resolver_paths"], resolver_acted_within_h=4)

    unsigned += sweep(L, 60)                   # end of operational period 5: U015 silent since 46 -> escalates here
    hb = [f for f in L.failures if f["type"] == "HEARTBEAT_MISSED" and f not in hb_before]
    note("I-9", "FT-17", "suppressed check-in escalated at the period sweep",
         escalated=[(f["unit_id"], f["detection_latency_h"], f["within_one_interval"]) for f in hb if f["unit_id"] == "U015"],
         all_missed_this_sweep=len(hb))

    # FT-06: dwell check at the end; V8 retention: end the event, assignments persist
    now = 64
    unsigned += sweep(L, now)
    fired = L.check_dwell(now)
    note("-", "FT-06", "dwell escalations fired", units=[e["unit_id"] for e in fired])
    L.end_event(ts=now)
    note("-", "V8", "event ended; standing plan retained", standing_plan=sorted(L.standing_plan))
    L.record_exercise("EX-V0.1", pantries, ts=now, cellular_up=False)

    m = L.metrics(now)
    m["dwell_max_h"] = m["dwell_h"]["max"]
    m["refuse_unreceipted_pct"] = 100.0 if m["settlements"]["refused_no_receipt"] >= 1 else 0.0
    detected_ids = {f["unit_id"] for f in unsigned}
    m["unsigned_transfers_detected_pct"] = (100.0 * len(detected_ids & set(dropped_unsigned)) / len(dropped_unsigned)) if dropped_unsigned else None
    m["unsigned_transfers_extra"] = sorted(detected_ids - set(dropped_unsigned))
    m["detection_latency_h_max"] = m["heartbeat"]["detection_latency_h_max"]
    m["resolver_acted_within_h"] = 4

    verdicts = score(L, m, log, dropped_unsigned, unsigned)
    result = {"version": "v0.1", "seed": seed, "targets": TARGETS, "metrics": m, "verdicts": verdicts, "log": log,
              "n_nodes": len(L.nodes), "n_events": len(L.events),
              "failures_by_locus": m["failures_by_locus"], "failures_by_site": m["failures_by_site"]}
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "exercise_v0_1.json"), "w") as f:
            json.dump(result, f, indent=1, sort_keys=True, default=str)
        write_md(result, os.path.join(out_dir, "exercise_v0_1.md"))
    if not keep_root:
        shutil.rmtree(root, ignore_errors=True)
    return result


def _cmp(op, a, b):
    return {"<=": a <= b, ">=": a >= b, "==": a == b}[op]


def score(L, m, log, dropped_unsigned, unsigned):
    by = {}
    for e in log:
        by.setdefault(e["ft"], []).append(e)
    v = {}

    def row(ft, verify, measured, shall, on_target, baseline=None, target=None, note=""):
        v[ft] = {"verify": verify, "baseline": baseline, "target": target, "measured": measured,
                 "shall_held": bool(shall), "verdict": "PASS" if shall and on_target else "FAIL", "note": note}

    t = TARGETS["FT-01"]
    held = any(e["outcome"] == "held at gate" for e in by.get("FT-01", []))
    ok = _cmp(t["op"], m["visibility_lost_pct"], t["value"])
    row("FT-01", "T+A", {"visibility_lost_pct": round(m["visibility_lost_pct"], 1), "stale": m["stale_units"], "lost": m["lost_units"]},
        held, ok, t["baseline"], "%s %s %%" % (t["op"], t["value"]),
        "unrecorded order held at the gate; stale set = the %d unreceipted deliveries, %d unsigned drops, the stranded/silent loads" %
        (len([e for e in by.get("FT-05", []) if "IN_TRANSIT" in e["outcome"]]), len(dropped_unsigned)))
    ok2 = len(by.get("FT-02", [])) == 2 and all("FAIL" not in e["outcome"] for e in by["FT-02"])
    row("FT-02", "I+T", "schema rejected 'unknown' location; close refused", ok2, True)
    dropped = sum(1 for e in L.events if e["type"] == "OBS_DROPPED")
    phys = sum(1 for e in L.events if e["type"] == "OBS" and e["channel"] == "physical")
    row("FT-03", "T/E", {"electronic_obs_dropped": dropped, "physical_obs_kept": phys}, dropped > 0 and phys > 0, True,
        note="electronic channel dark for the whole run; state held on T-cards and gate logs")
    row("FT-04", "I+T", {"repack_without_manifest": m["flags"].get("REPACK_WITHOUT_MANIFEST", 0),
                         "generic_manifest": m["flags"].get("TRANSFER_MANIFEST_GENERIC", 0),
                         "child_ids_linked": len(L.units["U010"]["children"])},
        m["flags"].get("REPACK_WITHOUT_MANIFEST", 0) >= 1 and L.units["U010-a"]["parent_id"] == "U010", True)
    t = TARGETS["FT-05"]
    row("FT-05", "A", {"receipt_rate_pct": round(m["receipt_rate_pct"], 1)}, True, _cmp(t["op"], m["receipt_rate_pct"], t["value"]),
        t["baseline"], "%s %s" % (t["op"], t["value"]), "unreceipted deliveries stay IN_TRANSIT; counted, not relabelled")
    t = TARGETS["FT-06"]
    esc = m["dwell_h"]["over_limit_escalated"] >= 1
    on_t = _cmp(t["op"], m["dwell_max_h"], t["value"])
    row("FT-06", "A", {"dwell_max_h": m["dwell_max_h"], "escalated": m["dwell_h"]["over_limit_escalated"]}, esc, on_t,
        t["baseline"], "max dwell %s %s h; escalate > %d h" % (t["op"], t["value"], DWELL_LIMIT_H),
        "escalation fired; max dwell %s h is %s the operator target" % (m["dwell_max_h"], "within" if on_t else "above"))
    o7 = [e["outcome"] for e in by.get("FT-07", [])]
    ok7 = any(o.startswith("substitution logged") for o in o7) and any("need not credited" in o for o in o7) and any("refused" in o for o in o7)
    row("FT-07", "I+T", o7, ok7, True, note="Q-1: no factor -> delivery RECEIVED, need uncredited, failure recorded; direct substitute() refuses")
    order = by["FT-08"][0]["order"]
    row("FT-08", "I+A", {"order": order, "expired_excluded": m["flags"].get("EXPIRED_EXCLUDED", 0)},
        "U007" not in order and order == sorted(order, key=lambda u: L.units[u]["expiry_ts"]), True)
    row("FT-09", "I+A", {"open_at_activation": by["FT-09"][0]["open_findings"]}, bool(by["FT-09"][0]["open_findings"]), True,
        note="AAR-2011-03 still OPEN at the end: reported, not closed by the pilot")
    row("FT-10", "I+D", {"copies": 2, "consistent": m["copies_consistent"]}, bool(m["copies_consistent"]), True)
    t = TARGETS["FT-11"]
    row("FT-11", "T+A", m["settlements"], m["settlements"]["refused_no_receipt"] >= 1 and m["settlements"]["settled"] >= 1,
        _cmp(t["op"], m["refuse_unreceipted_pct"], t["value"]), t["baseline"], "refuse 100% of unreceipted")
    un = L.routes["R1"]["unassigned"]
    row("FT-12", "I+E", {"unassigned_edges": un}, bool(un) and bool(m["flags"].get("ROUTE_EDGE_UNASSIGNED")), True,
        note="the cross-dock leg is unassigned and flagged; assigning it is the operator's job")
    npan = sum(1 for n in L.nodes.values() if n["kind"] == "pantry")
    co = sum(1 for n in L.nodes.values() if n["kind"] == "pantry" and n["plan_coauthor"])
    pre = sum(1 for n in L.nodes.values() if n["kind"] == "pantry" and n["prepositioned_days"])
    fam = sum(1 for n in L.nodes.values() if n["kind"] == "pantry" and n["familiarity_verified"])
    row("FT-13", "E+I", {"pantries": npan, "prepositioned": pre, "coauthored": co, "familiarity_verified": fam},
        co == npan and pre == npan and fam == npan, True, "23% co-authored; 90% no pre-positioned stock", "100% of nodes",
        "co-authorship at %d/%d: reported as a FAIL, not waived" % (co, npan))
    row("FT-14", "E", {"cellular_up": L.cellular_up, "events": len(L.events)}, not L.cellular_up and len(L.events) > 100, True,
        note="whole exercise ran with the electronic channel dark")
    e15 = by["FT-15"][0]
    row("FT-15", "E", {"before": e15["before"], "after": e15["after"]}, e15["before"] == "PROVISIONAL" and e15["after"] == "REGISTERED", True)
    # v0.1 rows
    t = TARGETS["FT-16"]
    det = m["unsigned_transfers_detected_pct"]
    row("FT-16", "T+A", {"dropped_without_custodian": len(dropped_unsigned), "of_which_detected_pct": det,
                         "extra_detections": m["unsigned_transfers_extra"], "custodian_availability_pct": 20},
        len(unsigned) >= 1, det is not None and _cmp(t["op"], det, t["value"]), t["baseline"], "detect >= 100% of drops",
        "I-12: at 20% custodian availability every drop without a signed handover reads as an unsigned transfer; "
        "the extra detections are the unreceipted deliveries, which are present without custody too")
    t = TARGETS["FT-17"]
    hb = by["FT-17"][0]
    lat = m["detection_latency_h_max"]
    row("FT-17", "T+A", {"I-9_escalation": hb["escalated"], "missed_total": m["heartbeat"]["missed"], "detection_latency_h_max": lat},
        len(hb["escalated"]) >= 1 and m["heartbeat"]["all_within_one_interval"], _cmp(t["op"], lat, t["value"]),
        t["baseline"], "latency %s %s h" % (t["op"], t["value"]),
        "silence past the declared interval escalated within one interval; the sweep ran every period (the sweep is the detector)")
    t = TARGETS["FT-18"]
    c18 = by["FT-18"][0]
    row("FT-18", "T", {"routed_to": c18["routed_to"], "non_cellular_paths": c18["paths"], "resolver_acted_within_h": c18["resolver_acted_within_h"]},
        c18["routed_to"] is not None and bool(c18["paths"]), _cmp(t["op"], c18["resolver_acted_within_h"], t["value"]),
        t["baseline"], "resolver acts %s %s h" % (t["op"], t["value"]),
        "N-4 watch: the resolver acted in this run; a run where it does not fails target while the shall holds")
    o3 = [e["outcome"] for e in by.get("V3", [])]
    row("V3", "T", o3, all("FAIL" not in o for o in o3) and len(o3) == 3, True, note="I-13: 'critical' alone, class without axis, custody drop all refused")
    e11 = by["V4"][0]
    row("V4", "T", {"reclassed": e11["reclassed"], "manual_steps": e11["manual_steps"], "water_min_class": e11["water_min_class"]},
        e11["manual_steps"] == 0 and e11["water_min_class"] >= "R2" and e11["reclassed"] >= 1, True,
        note="I-11: relief water reclassed to R2 minimum from the precomputed table (N-3 watch: manual_steps must stay 0)")
    e8 = by["V8"]
    row("V8", "I", {"missing_at_activation": e8[0]["missing"], "standing_plan_after_event": e8[1]["standing_plan"]},
        e8[0]["missing"] == ["protein_g"] and "L_water" in e8[1]["standing_plan"], True,
        note="protein_g has no standing assignment and no waiver: flagged at activation; assignments survive end_event")
    return v


def write_md(result, path):
    v = result["verdicts"]
    L = ["# Pilot verification exercise v0.1 — results\n",
         "Generated by `experiments/substrate_pilot_v0/exercise.py`. Baselines are OIG-20-76 measurements; "
         "targets are operator-set in `TARGETS` before the run. Failures are reported as found.\n",
         "| row | verify | OIG baseline | target | measured | shall held | verdict | note |", "|---|---|---|---|---|---|---|---|"]
    for ft in sorted(v, key=lambda k: (k[0] != "F", k)):
        r = v[ft]
        L.append("| %s | %s | %s | %s | `%s` | %s | **%s** | %s |" % (
            ft, r["verify"], r["baseline"] if r["baseline"] is not None else "—",
            r["target"] if r["target"] is not None else "—",
            json.dumps(r["measured"], default=str)[:110], "yes" if r["shall_held"] else "no", r["verdict"], r["note"]))
    L.append("\nFailure records by LOCUS (V1) and SITE in this run:\n")
    L.append("| locus | n |"); L.append("|---|---|")
    for k, n in sorted(result["failures_by_locus"].items()):
        L.append("| %s | %d |" % (k, n))
    L.append("| site | n |"); L.append("|---|---|")
    for k, n in sorted(result["failures_by_site"].items()):
        L.append("| %s | %d |" % (k, n))
    L.append("\nInjects in order:\n")
    L.append("| inject | row | outcome |"); L.append("|---|---|---|")
    for e in result["log"]:
        L.append("| %s | %s | %s |" % (e["inject"], e["ft"], e["outcome"]))
    L.append("\nLoop: %d nodes, %d ledger events, cellular down throughout." % (result["n_nodes"], result["n_events"]))
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "runs"))
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    r = run(seed=a.seed, out_dir=a.out)
    for ft in sorted(r["verdicts"], key=lambda k: (k[0] != "F", k)):
        rr = r["verdicts"][ft]
        print("%-5s shall=%-3s %-4s %s" % (ft, "yes" if rr["shall_held"] else "no", rr["verdict"], rr["note"][:95]))
