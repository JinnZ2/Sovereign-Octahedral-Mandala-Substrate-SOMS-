"""
Pilot verification exercise — SPEC section 4, replayed at pilot scale
=====================================================================
Injects I-1..I-8 in order on a synthetic loop (1 food bank, 3 staging areas,
~40 pantries, 2 carriers, 1 unregistered community node; N <= 150). Each FT
row is scored against its OIG BASELINE (measured, not ours) and an
operator-set TARGET declared in TARGETS before the run. Failures are reported
as found (FT-02 applies to the pilot itself).

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
    "FT-01": {"metric": "visibility_lost_pct", "op": "<=", "value": 5.0, "baseline": 38.0},
    "FT-05": {"metric": "receipt_rate_pct", "op": ">=", "value": 95.0, "baseline": 4.0},
    "FT-06": {"metric": "dwell_max_h", "op": "<=", "value": 4 * OP_PERIOD_H, "baseline": 48 * 24},
    "FT-11": {"metric": "settlement_refusal_of_unreceipted_pct", "op": "==", "value": 100.0, "baseline": 0.0},
}
DWELL_LIMIT_H = 2 * OP_PERIOD_H


def build_loop(L, rng, n_pantries=40):
    L.register_node("FB", "food_bank", "R1")
    for i in range(3):
        L.register_node("RSA%d" % i, "staging", "R1")
    for i in range(n_pantries):
        L.register_node("P%02d" % i, "pantry", "R1")
    for c in ("CARRIER-A", "CARRIER-B"):
        L.register_node(c, "carrier", "R1")
    # pre-event declarations (FT-07, FT-08, FT-06, FT-12, FT-13)
    L.declare_conversion("count", "kcal", 250.0, ts=-500, declared_by="ops")     # 1 snack box = 250 kcal (declared)
    L.declare_rule("R-FEFO", "FEFO", {}, ts=-500, override_committee=["ops-lead", "pantry-rep"])
    L.declare_rule("R-DWELL", "DWELL_LIMIT", {"limit_h": DWELL_LIMIT_H}, ts=-500, override_committee=["ops-lead"])
    edges = [("FB", "RSA0", "linehaul"), ("FB", "RSA1", "linehaul"), ("FB", "RSA2", "linehaul"),
             ("RSA0", "pantries", "last-mile"), ("RSA1", "pantries", "last-mile"), ("RSA2", "pantries", "last-mile"),
             ("port", "FB", "cross-dock")]
    assignments = {e: ("CARRIER-A" if i % 2 == 0 else "CARRIER-B") for i, e in enumerate(edges[:-1])}
    L.declare_route("R1", edges, assignments, ts=-400)        # the cross-dock edge is left unassigned on purpose
    pantries = ["P%02d" % i for i in range(n_pantries)]
    for p in pantries:
        L.preposition(p, days_of_need=3, ts=-300)
    L.coauthor_plan("PLAN-R1", pantries[:int(0.9 * n_pantries)], ts=-200)   # 10% did not co-author: reported, not hidden
    return pantries


def run(seed=0, out_dir=None, keep_root=False):
    rng = random.Random(seed)
    root = tempfile.mkdtemp(prefix="substrate_pilot_")
    L = Ledger(root=root)
    pantries = build_loop(L, rng)
    log = []

    def note(inject, ft, outcome, **kw):
        log.append({"inject": inject, "ft": ft, "outcome": outcome, **kw})

    # FLT: I-8 prior AAR finding exists, unacted, at activation
    L.register_finding("AAR-2011-03", "2011 exercise AAR", "commodity movement need anticipated", found_ts=-24 * 365 * 6)
    open_findings = L.activate(ts=0)
    note("I-8", "FT-09", "open findings displayed at activation", open_findings=open_findings)

    # I-6: cellular down for the whole exercise (FT-14); electronic channel is therefore dark
    L.cellular_up = False
    note("I-6", "FT-14", "cellular disabled for the whole exercise")

    # needs at pantries (C2), declared units
    for i, p in enumerate(pantries):
        L.report_need("N-%s" % p, p, "kcal", qty=2000 * 150 * 3, by_ts=72, ts=1)      # 150 persons x 3 days
        L.report_need("W-%s" % p, p, "L_water", qty=4 * 150 * 3, by_ts=72, ts=1)

    # units at origin (C1) with physical channel, expiry spread, one already expired
    units = []
    for i in range(120):
        kind = "kcal" if i % 3 else "L_water"
        qty = 2000 * 50 if kind == "kcal" else 4 * 50
        exp = 24 * rng.choice([5, 10, 20, 40]) if kind == "kcal" else None
        if i == 7:
            exp = -1     # already expired at activation
        u = L.create_unit("U%03d" % i, kind, qty, ts=2, expiry_ts=exp, seal_no="S%03d" % i, tcard="T%03d" % i)
        units.append(u["unit_id"])

    # I-1: order placed with no state record (FT-01)
    try:
        L.release("GHOST-1", "P00", "CARRIER-A", ts=3)
        note("I-1", "FT-01", "FAIL: unrecorded movement released")
    except Refused as e:
        note("I-1", "FT-01", "held at gate", detail=str(e))

    # ship everything via RSAs
    commit_ids = []
    for i, uid in enumerate(units):
        rsa = "RSA%d" % (i % 3)
        carrier = "CARRIER-A" if i % 2 == 0 else "CARRIER-B"
        c = L.release(uid, rsa, carrier, ts=4 + i % 6, commit_id="C-%s" % uid)
        commit_ids.append(c["commit_id"])
        # I-2 window: electronic tracking lost for two periods; physical gate logs continue (FT-03)
        ts_arrive = 10 + i % 6
        L.observe(uid, "electronic", "en-route", ts=ts_arrive - 2)     # dropped (cellular down)
        L.observe(uid, "physical", rsa, ts_arrive, event="gate-in %s" % rsa)
        L.receive(c["commit_id"], ts=ts_arrive, receiver_mark={"kind": "stamp", "by": "%s-gate" % rsa})
        L.arrive_at_rest(uid, rsa, ts_arrive, custody=rsa)

    # I-3: carrier repacks a container without a manifest (FT-04)
    L.repack("U010", [("U010-a", 50000), ("U010-b", 50000)], ts=14, manifest=None, by="CARRIER-A")
    L.transfer("U011", "CARRIER-B", ts=14, manifest={"description": "relief supplies", "unit_ids": []})
    L.repack("U012", [("U012-a", 100000)], ts=14, manifest={"lists_unit_ids": True, "seal_no": "S012-r"}, by="CARRIER-A")

    # last mile: RSA -> pantries with receipts (C3). Some receipts missing on purpose, reported as found.
    delivered = 0
    unreceipted = []
    for i, uid in enumerate(units):
        u = L.units[uid]
        if u["status"] != "AT_REST" or i in (14, 15):      # U014/U015 deliberately stranded at the RSA (FT-06 inject)
            continue
        p = pantries[i % len(pantries)]
        need = ("N-%s" if u["declared_unit"] == "kcal" else "W-%s") % p
        cid = "D-%s" % uid
        L.release(uid, p, "CARRIER-B", ts=20 + i % 10, commit_id=cid)
        commit_ids.append(cid)
        L.observe(uid, "physical", p, 24 + i % 10, event="arrived %s" % p)
        if i % 25 == 5:                       # a delivery whose paper receipt did not come back
            unreceipted.append(cid)
            continue
        L.receive(cid, ts=24 + i % 10, receiver_mark={"kind": rng.choice(["signature", "stamp", "photo"]), "by": "%s-lead" % p},
                  need_id=need)
        delivered += 1
    for cid in unreceipted:
        try:
            L.receive(cid, ts=30)
            note("-", "FT-05", "FAIL: receipt accepted without a mark")
        except Refused as e:
            note("-", "FT-05", "unreceipted delivery stays IN_TRANSIT", commit_id=cid)

    # I-4: meals unavailable, snack boxes substituted (FT-07)
    L.create_unit("SNACK-1", "count", 1200, ts=30, seal_no="SS1", tcard="TS1")      # 1200 boxes
    L.release("SNACK-1", "P03", "CARRIER-A", ts=31, commit_id="D-SNACK-1")
    L.receive("D-SNACK-1", ts=33, receiver_mark={"kind": "signature", "by": "P03-lead"}, need_id="N-P03")
    sub = [e for e in L.events if e["type"] == "SUBSTITUTION"][-1]
    note("I-4", "FT-07", "substitution logged with pre-declared factor", factor=sub["factor"], converted_kcal=sub["converted_qty"])
    L.create_unit("SNACK-2", "protein_g", 500, ts=34, seal_no="SS2", tcard="TS2")   # no declared conversion protein_g -> kcal
    L.release("SNACK-2", "P04", "CARRIER-A", ts=35, commit_id="D-SNACK-2")
    try:
        L.receive("D-SNACK-2", ts=36, receiver_mark={"kind": "stamp", "by": "P04-lead"}, need_id="N-P04")
        note("I-4b", "FT-07", "FAIL: substitution accepted without a declared conversion")
    except Refused as e:
        note("I-4b", "FT-07", "substitution without declared conversion refused", detail=str(e))

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

    # I-7: unregistered community node reports need and stock (FT-15)
    L.register_node("COMM-1", "community", "R1", ts=45, registered=False)
    L.report_need("N-COMM-1", "COMM-1", "kcal", qty=2000 * 30 * 2, by_ts=72, ts=45)
    L.report_stock("COMM-1", "CU-1", "kcal", 2000 * 30, ts=45, seal_no="CS1", tcard="CT1")
    status_before = L.nodes["COMM-1"]["status"]
    L.release("CU-1", "P06", "COMM-1", ts=46, commit_id="D-CU-1")
    L.receive("D-CU-1", ts=48, receiver_mark={"kind": "photo", "by": "P06-lead"}, need_id="N-P06")
    note("I-7", "FT-15", "provisional node promoted on first kept commitment",
         before=status_before, after=L.nodes["COMM-1"]["status"])

    # FT-06: dwell check at the end of the exercise; U014/U015 have sat at the RSA since ~ts 10
    now = 60
    fired = L.check_dwell(now)
    note("-", "FT-06", "dwell escalations fired", units=[e["unit_id"] for e in fired])

    # FT-13/14 exercise record: familiarity verified for the nodes that took part
    L.record_exercise("EX-V0", pantries, ts=now, cellular_up=False)

    m = L.metrics(now)
    m["dwell_max_h"] = m["dwell_h"]["max"]
    m["settlement_refusal_of_unreceipted_pct"] = 100.0 if m["settlements"]["refused_no_receipt"] >= 1 else 0.0

    verdicts = score(L, m, log)
    result = {"seed": seed, "targets": TARGETS, "metrics": m, "verdicts": verdicts, "log": log,
              "n_nodes": len(L.nodes), "n_events": len(L.events)}
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "exercise_v0.json"), "w") as f:
            json.dump(result, f, indent=1, sort_keys=True, default=str)
        write_md(result, os.path.join(out_dir, "exercise_v0.md"))
    if not keep_root:
        shutil.rmtree(root, ignore_errors=True)
    return result


def _cmp(op, a, b):
    return {"<=": a <= b, ">=": a >= b, "==": a == b}[op]


def score(L, m, log):
    by_ft = {}
    for e in log:
        by_ft.setdefault(e["ft"], []).append(e)
    v = {}

    def row(ft, verify, measured, verdict, baseline=None, target=None, note="", shall=None):
        v[ft] = {"verify": verify, "baseline": baseline, "target": target, "measured": measured,
                 "shall_held": verdict == "PASS" if shall is None else shall,
                 "verdict": verdict, "note": note}

    t = TARGETS["FT-01"]
    held = any(e["outcome"] == "held at gate" for e in by_ft.get("FT-01", []))
    on_target = _cmp(t["op"], m["visibility_lost_pct"], t["value"])
    row("FT-01", "T+A", {"visibility_lost_pct": round(m["visibility_lost_pct"], 1)},
        "PASS" if held and on_target else "FAIL", t["baseline"], "%s %s %%" % (t["op"], t["value"]),
        "unrecorded order held at the gate: %s; visibility lost %.1f%% is %s the operator target (stale = no observation "
        "within one operational period: the unreceipted deliveries, the stranded units and the refused substitution)" %
        (held, m["visibility_lost_pct"], "within" if on_target else "above"), shall=held)
    ok2 = all("FAIL" not in e["outcome"] for e in by_ft.get("FT-02", [])) and len(by_ft.get("FT-02", [])) == 2
    row("FT-02", "I+T", "schema rejected 'unknown' location; close refused", "PASS" if ok2 else "FAIL")
    dropped = sum(1 for e in L.events if e["type"] == "OBS_DROPPED")
    phys = sum(1 for e in L.events if e["type"] == "OBS" and e["channel"] == "physical")
    row("FT-03", "T/E", {"electronic_obs_dropped": dropped, "physical_obs_kept": phys},
        "PASS" if dropped > 0 and phys > 0 and (m["visibility_lost_pct"] or 0) < 100 else "FAIL",
        note="electronic channel dark for the whole run; state held on T-cards and gate logs")
    row("FT-04", "I+T", {"repack_without_manifest": m["flags"].get("REPACK_WITHOUT_MANIFEST", 0),
                         "generic_manifest": m["flags"].get("TRANSFER_MANIFEST_GENERIC", 0),
                         "child_ids_linked": len(L.units["U010"]["children"])},
        "PASS" if m["flags"].get("REPACK_WITHOUT_MANIFEST", 0) >= 1 and L.units["U010-a"]["parent_id"] == "U010" else "FAIL")
    t = TARGETS["FT-05"]
    row("FT-05", "A", m["receipt_rate_pct"], "PASS" if _cmp(t["op"], m["receipt_rate_pct"], t["value"]) else "FAIL",
        t["baseline"], "%s %s" % (t["op"], t["value"]),
        "unreceipted deliveries stay IN_TRANSIT; they are counted, not relabelled")
    t = TARGETS["FT-06"]
    esc = m["dwell_h"]["over_limit_escalated"] >= 1
    on_target = _cmp(t["op"], m["dwell_max_h"], t["value"])
    row("FT-06", "A", {"dwell_max_h": m["dwell_max_h"], "escalated": m["dwell_h"]["over_limit_escalated"]},
        "PASS" if esc and on_target else "FAIL", t["baseline"], "max dwell %s %s h; escalate > %d h" % (t["op"], t["value"], DWELL_LIMIT_H),
        "escalation fired for the stranded units (shall held); max dwell %s h is %s the operator target %s h" %
        (m["dwell_max_h"], "within" if on_target else "above", t["value"]), shall=esc)
    ok7 = any(e["outcome"].startswith("substitution logged") for e in by_ft.get("FT-07", [])) and \
        any("refused" in e["outcome"] for e in by_ft.get("FT-07", []))
    row("FT-07", "I+T", [e["outcome"] for e in by_ft.get("FT-07", [])], "PASS" if ok7 else "FAIL")
    order = by_ft["FT-08"][0]["order"]
    row("FT-08", "I+A", {"order": order, "expired_excluded": m["flags"].get("EXPIRED_EXCLUDED", 0)},
        "PASS" if "U007" not in order and order == sorted(order, key=lambda u: L.units[u]["expiry_ts"]) else "FAIL")
    row("FT-09", "I+A", {"open_at_activation": by_ft["FT-09"][0]["open_findings"]},
        "PASS" if by_ft["FT-09"][0]["open_findings"] else "FAIL",
        note="AAR-2011-03 is still OPEN at the end of the exercise: reported, not closed by the pilot")
    row("FT-10", "I+D", {"copies": 2, "consistent": m["copies_consistent"]}, "PASS" if m["copies_consistent"] else "FAIL")
    t = TARGETS["FT-11"]
    row("FT-11", "T+A", m["settlements"], "PASS" if m["settlements"]["refused_no_receipt"] >= 1 and m["settlements"]["settled"] >= 1 else "FAIL",
        t["baseline"], "refuse 100% of unreceipted")
    unassigned = L.routes["R1"]["unassigned"]
    row("FT-12", "I+E", {"unassigned_edges": unassigned}, "PASS" if unassigned and m["flags"].get("ROUTE_EDGE_UNASSIGNED") else "FAIL",
        note="the cross-dock leg is unassigned in this plan and is flagged, which is the shall; assigning it is the operator's job")
    co = sum(1 for n in L.nodes.values() if n["kind"] == "pantry" and n["plan_coauthor"])
    pre = sum(1 for n in L.nodes.values() if n["kind"] == "pantry" and n["prepositioned_days"])
    fam = sum(1 for n in L.nodes.values() if n["kind"] == "pantry" and n["familiarity_verified"])
    npan = sum(1 for n in L.nodes.values() if n["kind"] == "pantry")
    row("FT-13", "E+I", {"pantries": npan, "prepositioned": pre, "coauthored": co, "familiarity_verified": fam},
        "PASS" if pre == npan and fam == npan and co == npan else "FAIL",
        "23% co-authored; 90% no pre-positioned stock", "100% of nodes",
        "co-authorship at %d/%d: the gap is reported as a FAIL, not waived" % (co, npan), shall=(co == npan))
    row("FT-14", "E", {"cellular_up": L.cellular_up, "events": len(L.events)}, "PASS" if not L.cellular_up and len(L.events) > 100 else "FAIL",
        note="whole exercise ran with the electronic channel dark")
    e15 = by_ft["FT-15"][0]
    row("FT-15", "E", {"before": e15["before"], "after": e15["after"]}, "PASS" if e15["before"] == "PROVISIONAL" and e15["after"] == "REGISTERED" else "FAIL")
    return v


def write_md(result, path):
    v = result["verdicts"]
    L = ["# Pilot verification exercise v0 — results\n",
         "Generated by `experiments/substrate_pilot_v0/exercise.py`. Baselines are OIG-20-76 measurements; "
         "targets are operator-set in `TARGETS` before the run. Failures are reported as found.\n",
         "| FT | verify | OIG baseline | target | measured | shall held | verdict | note |", "|---|---|---|---|---|---|---|---|"]
    for ft in sorted(v):
        r = v[ft]
        L.append("| %s | %s | %s | %s | `%s` | %s | **%s** | %s |" % (
            ft, r["verify"], r["baseline"] if r["baseline"] is not None else "—",
            r["target"] if r["target"] is not None else "—",
            json.dumps(r["measured"], default=str)[:90], "yes" if r["shall_held"] else "no", r["verdict"], r["note"]))
    L.append("\nInjects in order:\n")
    L.append("| inject | FT | outcome |")
    L.append("|---|---|---|")
    for e in result["log"]:
        L.append("| %s | %s | %s |" % (e["inject"], e["ft"], e["outcome"]))
    m = result["metrics"]
    L.append("\nLoop: %d nodes, %d ledger events, cellular down throughout. Need gap in declared units is in the JSON." %
             (result["n_nodes"], result["n_events"]))
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "runs"))
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    r = run(seed=a.seed, out_dir=a.out)
    for ft in sorted(r["verdicts"]):
        rr = r["verdicts"][ft]
        print("%s  shall=%-3s  %-4s  %s" % (ft, "yes" if rr["shall_held"] else "no", rr["verdict"], rr["note"][:90]))
