"""
Substrate coordination pilot v0 — ledger
=========================================
Stdlib only. Append-only event log with >= 2 copies (FT-10), paper-operable
(every record is one JSON line; forms/ holds the printable equivalents).

Channels
  C1 STATE      units: identity, qty, declared unit, condition, expiry, custody, location
  C2 NEED       needs with declared unit, clock, dependency edges
  C3 COMMIT     commitments; KEPT only on a receiver mark
  C4 ARBITRATE  declared rules (FEFO, dwell limit) + escalations + override committee
  FLT           finding register -> rule change or WAIVED
  BND           MONEY_TERM settlements, blocked without a C3 receipt

Every shall in SPEC.md section 2 is a gate here. A gate that holds raises
Refused; a shall that only flags appends a FLAG record. Nothing is relabelled:
a LOST unit stays LOST with its last-known position and time.

Time is an integer number of hours from activation. An operational period is
OP_PERIOD_H hours.
"""
import json
import os
from collections import defaultdict

OP_PERIOD_H = 12
STATUSES = ("AT_ORIGIN", "IN_TRANSIT", "AT_REST", "RECEIVED", "REPACKED", "LOST", "UNKNOWN", "CLOSED")
DECLARED_UNITS = ("kcal", "protein_g", "L_water", "count")
RECEIVER_MARKS = ("signature", "stamp", "photo")
NODE_STATUS = ("REGISTERED", "PROVISIONAL")


class Refused(Exception):
    """A gate held. The message names the FT row and what was missing."""


class Ledger:
    def __init__(self, root=None, copies=("primary", "mirror"), custody="pilot-ops"):
        self.root = root
        self.copies = tuple(copies)
        if root is not None:
            if len(self.copies) < 2:
                raise ValueError("FT-10: records need >= 2 copies in separate places")
            for c in self.copies:
                os.makedirs(os.path.join(root, c), exist_ok=True)
        self.custody = custody
        self.events = []
        self.units = {}
        self.needs = {}
        self.commits = {}
        self.nodes = {}
        self.rules = {}
        self.findings = {}
        self.money = []
        self.flags = []
        self.escalations = []
        self.conversions = {}
        self.routes = {}
        self.plans = {}
        self.exercises = []
        self.electronic_up = True
        self.cellular_up = True
        self.activated_at = None
        self._seq = 0

    # ------------------------------------------------------------------ events
    def _event(self, rec_type, ts, **fields):
        """Append one record to every copy. `record_custody` (FT-10) is the ledger's declared
        custodian and is distinct from a unit's physical `custody`."""
        self._seq += 1
        rec = dict(fields)
        rec.update({"seq": self._seq, "type": rec_type, "ts": int(ts), "record_custody": self.custody})
        self.events.append(rec)
        if self.root is not None:
            line = json.dumps(rec, sort_keys=True)
            for c in self.copies:
                with open(os.path.join(self.root, c, "ledger.jsonl"), "a") as f:
                    f.write(line + "\n")
        return rec

    def flag(self, ts, code, **fields):
        rec = self._event("FLAG", ts, code=code, **fields)
        self.flags.append(rec)
        return rec

    def copies_consistent(self):
        """FT-10 D: every copy holds the same lines."""
        if self.root is None:
            return None
        blobs = []
        for c in self.copies:
            p = os.path.join(self.root, c, "ledger.jsonl")
            blobs.append(open(p).read() if os.path.exists(p) else "")
        return all(b == blobs[0] for b in blobs)

    # ------------------------------------------------------------------ nodes / C2
    def register_node(self, node_id, kind, region, ts=0, registered=True):
        status = "REGISTERED" if registered else "PROVISIONAL"        # FT-15
        self.nodes[node_id] = {"node_id": node_id, "kind": kind, "region": region,
                               "status": status, "prepositioned_days": None,
                               "plan_coauthor": False, "familiarity_verified": False}
        self._event("NODE", ts, node_id=node_id, kind=kind, region=region, status=status)
        return self.nodes[node_id]

    def report_need(self, need_id, node_id, declared_unit, qty, by_ts, ts, edges=()):
        if node_id not in self.nodes:
            raise Refused("C2: unknown node; register it (PROVISIONAL is allowed, FT-15)")
        if declared_unit not in DECLARED_UNITS:
            raise Refused("FT-07: need must be denominated in a declared unit %s" % (DECLARED_UNITS,))
        self.needs[need_id] = {"need_id": need_id, "node_id": node_id, "declared_unit": declared_unit,
                               "qty": float(qty), "by_ts": int(by_ts), "edges": list(edges),
                               "delivered": 0.0}
        self._event("NEED", ts, **self.needs[need_id])
        return self.needs[need_id]

    def report_stock(self, node_id, unit_id, declared_unit, qty, ts, **kw):
        """A node (registered or PROVISIONAL) declares stock it holds. Creates a C1 record."""
        if node_id not in self.nodes:
            raise Refused("C1: unknown node")
        return self.create_unit(unit_id, declared_unit, qty, ts, custody=node_id, location=node_id, **kw)

    # ------------------------------------------------------------------ C1
    def create_unit(self, unit_id, declared_unit, qty, ts, condition="GOOD", expiry_ts=None,
                    custody="origin", location="origin", seal_no=None, tcard=None, parent_id=None):
        if declared_unit not in DECLARED_UNITS:
            raise Refused("FT-07: unit must carry a declared unit %s" % (DECLARED_UNITS,))
        self._check_location(location)
        u = {"unit_id": unit_id, "parent_id": parent_id, "declared_unit": declared_unit,
             "qty": float(qty), "condition": condition, "expiry_ts": expiry_ts,
             "custody": custody, "location": location, "status": "AT_ORIGIN",
             "created_ts": int(ts), "rest_since_ts": int(ts),
             "last_known": {"location": location, "ts": int(ts)},
             "channels": {"electronic": {"last_seen_ts": int(ts), "location": location},
                          "physical": {"seal_no": seal_no, "tcard": tcard,
                                       "gate_log": [{"ts": int(ts), "location": location, "event": "created"}],
                                       "last_seen_ts": int(ts), "location": location}},
             "children": [], "receipt": None, "reconciliation": None}
        self.units[unit_id] = u
        self._event("UNIT", ts, **{k: v for k, v in u.items() if k != "channels"})
        return u

    @staticmethod
    def _check_location(location):
        if location is None or str(location).strip().lower().startswith("unknown"):
            raise Refused("FT-02: UNKNOWN is a status, never a location")

    def release(self, unit_id, to_node, carrier, ts, commit_id=None):
        """Origin gate. FT-01: no state record -> held."""
        u = self.units.get(unit_id)
        if u is None:
            raise Refused("FT-01: unit %s has no state record; movement held at the gate" % unit_id)
        if u["status"] not in ("AT_ORIGIN", "AT_REST"):
            raise Refused("C1: unit %s is %s, cannot release" % (unit_id, u["status"]))
        u["status"] = "IN_TRANSIT"
        u["custody"] = carrier
        self._touch(u, "physical", u["location"], ts, event="gate-out to %s" % to_node)
        cid = commit_id or "C-%s" % unit_id
        self.commits[cid] = {"commit_id": cid, "actor": carrier, "unit_id": unit_id, "to_node": to_node,
                             "by_ts": None, "status": "OPEN", "receipt": None, "opened_ts": int(ts)}
        self._event("COMMIT", ts, **self.commits[cid])
        return self.commits[cid]

    def _touch(self, u, channel, location, ts, event=None):
        ch = u["channels"][channel]
        ch["last_seen_ts"] = int(ts)
        ch["location"] = location
        if channel == "physical" and event:
            ch["gate_log"].append({"ts": int(ts), "location": location, "event": event})
        u["last_known"] = {"location": location, "ts": int(ts)}
        u["location"] = location

    def observe(self, unit_id, channel, location, ts, event=None):
        """A state observation on one channel. FT-03: losing the electronic channel loses no state."""
        u = self.units[unit_id]
        self._check_location(location)
        if channel == "electronic" and not (self.electronic_up and self.cellular_up):
            self._event("OBS_DROPPED", ts, unit_id=unit_id, channel=channel, reason="electronic channel down")
            return False
        self._touch(u, channel, location, ts, event=event)
        self._event("OBS", ts, unit_id=unit_id, channel=channel, location=location)
        return True

    def arrive_at_rest(self, unit_id, location, ts, custody):
        u = self.units[unit_id]
        self._check_location(location)
        u["status"] = "AT_REST"
        u["custody"] = custody
        u["rest_since_ts"] = int(ts)
        self._touch(u, "physical", location, ts, event="gate-in")
        self._event("REST", ts, unit_id=unit_id, location=location, custody=custody)

    def set_status(self, unit_id, status, ts, location=None):
        if status not in STATUSES:
            raise Refused("C1: unknown status %s" % status)
        if location is not None:
            self._check_location(location)
        u = self.units[unit_id]
        u["status"] = status
        if location is not None:
            self._touch(u, "physical", location, ts)
        self._event("STATUS", ts, unit_id=unit_id, status=status)

    def mark_lost(self, unit_id, ts):
        """FT-02: LOST keeps last-known position + time; nothing is overwritten."""
        u = self.units[unit_id]
        u["status"] = "LOST"
        self._event("LOST", ts, unit_id=unit_id, last_known=dict(u["last_known"]))
        return u["last_known"]

    def close(self, unit_id, ts, reconciliation=None):
        """FT-02: closure requires physical reconciliation."""
        u = self.units[unit_id]
        if not reconciliation or not reconciliation.get("counted_by") or reconciliation.get("qty") is None:
            raise Refused("FT-02: cannot close %s without physical reconciliation (counted_by, qty)" % unit_id)
        u["reconciliation"] = dict(reconciliation, ts=int(ts))
        u["status"] = "CLOSED"
        self._event("CLOSE", ts, unit_id=unit_id, reconciliation=u["reconciliation"])

    def repack(self, parent_id, children, ts, manifest=None, by="carrier"):
        """FT-04: repack creates child IDs linked to the parent; no manifest -> flagged."""
        p = self.units[parent_id]
        if manifest is None or not manifest.get("lists_unit_ids"):
            self.flag(ts, "REPACK_WITHOUT_MANIFEST", parent_id=parent_id, by=by,
                      manifest=manifest)
        out = []
        for child_id, qty in children:
            c = self.create_unit(child_id, p["declared_unit"], qty, ts, condition=p["condition"],
                                 expiry_ts=p["expiry_ts"], custody=p["custody"], location=p["location"],
                                 parent_id=parent_id, seal_no=(manifest or {}).get("seal_no"))
            c["status"] = p["status"]
            p["children"].append(child_id)
            out.append(c)
        p["status"] = "REPACKED"
        self._event("REPACK", ts, parent_id=parent_id, children=[c[0] for c in children],
                    manifest=manifest, by=by)
        return out

    def transfer(self, unit_id, to_custody, ts, manifest=None):
        """Custody transfer. Identity survives; a manifest that does not name the unit is flagged."""
        u = self.units[unit_id]
        if manifest is None or unit_id not in manifest.get("unit_ids", []):
            self.flag(ts, "TRANSFER_MANIFEST_GENERIC", unit_id=unit_id, to_custody=to_custody, manifest=manifest)
        u["custody"] = to_custody
        self._touch(u, "physical", u["location"], ts, event="custody -> %s" % to_custody)
        self._event("TRANSFER", ts, unit_id=unit_id, to_custody=to_custody, manifest=manifest)

    # ------------------------------------------------------------------ FT-07 conversions
    def declare_conversion(self, from_unit, to_unit, factor, ts, declared_by):
        self.conversions[(from_unit, to_unit)] = {"factor": float(factor), "declared_ts": int(ts),
                                                  "declared_by": declared_by}
        self._event("CONVERSION", ts, from_unit=from_unit, to_unit=to_unit, factor=float(factor),
                    declared_by=declared_by)

    def substitute(self, need_id, unit_id_in, ts, event_ts=0):
        """Deliver a unit of a different declared unit against a need. Conversion must be declared
        pre-event and is logged at substitution time."""
        need = self.needs[need_id]
        u = self.units[unit_id_in]
        key = (u["declared_unit"], need["declared_unit"])
        if u["declared_unit"] == need["declared_unit"]:
            return {"converted_qty": u["qty"], "factor": 1.0}
        conv = self.conversions.get(key)
        if conv is None:
            raise Refused("FT-07: substitution %s -> %s has no declared conversion factor" % key)
        if conv["declared_ts"] > event_ts:
            self.flag(ts, "CONVERSION_DECLARED_POST_EVENT", need_id=need_id, unit_id=unit_id_in,
                      declared_ts=conv["declared_ts"], event_ts=event_ts)
        converted = u["qty"] * conv["factor"]
        self._event("SUBSTITUTION", ts, need_id=need_id, unit_id=unit_id_in, from_unit=key[0],
                    to_unit=key[1], factor=conv["factor"], converted_qty=converted)
        return {"converted_qty": converted, "factor": conv["factor"]}

    # ------------------------------------------------------------------ C3
    def receive(self, commit_id, ts, receiver_mark=None, need_id=None):
        """FT-05: delivery = receiver mark. State stays IN_TRANSIT until the receipt exists."""
        c = self.commits[commit_id]
        if not receiver_mark or receiver_mark.get("kind") not in RECEIVER_MARKS or not receiver_mark.get("by"):
            raise Refused("FT-05: no receiver mark (signature/stamp/photo + by); unit stays IN_TRANSIT")
        u = self.units[c["unit_id"]]
        c["status"] = "KEPT"
        c["receipt"] = dict(receiver_mark, ts=int(ts))
        u["status"] = "RECEIVED"
        u["receipt"] = c["receipt"]
        u["custody"] = c["to_node"]
        self._touch(u, "physical", c["to_node"], ts, event="received")
        if need_id and need_id in self.needs:
            need = self.needs[need_id]
            if u["declared_unit"] == need["declared_unit"]:
                need["delivered"] += u["qty"]
            else:
                need["delivered"] += self.substitute(need_id, u["unit_id"], ts, event_ts=self.activated_at or 0)["converted_qty"]
        self._event("RECEIPT", ts, commit_id=commit_id, unit_id=u["unit_id"], receipt=c["receipt"])
        self._maybe_promote(c["actor"], ts)
        return c

    def break_commit(self, commit_id, ts, reason):
        c = self.commits[commit_id]
        c["status"] = "BROKEN"
        self._event("BROKEN", ts, commit_id=commit_id, reason=reason)

    def _maybe_promote(self, node_id, ts):
        """FT-15: a PROVISIONAL node is promoted on its first kept commitment."""
        n = self.nodes.get(node_id)
        if n and n["status"] == "PROVISIONAL":
            n["status"] = "REGISTERED"
            self._event("PROMOTE", ts, node_id=node_id, reason="first kept commitment")

    # ------------------------------------------------------------------ C4
    def declare_rule(self, rule_id, kind, params, ts, override_committee=()):
        self.rules[rule_id] = {"rule_id": rule_id, "kind": kind, "params": dict(params),
                               "override_committee": list(override_committee), "declared_ts": int(ts)}
        self._event("RULE", ts, **self.rules[rule_id])

    def dwell_h(self, unit_id, now):
        u = self.units[unit_id]
        if u["status"] in ("AT_REST", "AT_ORIGIN"):
            return now - u["rest_since_ts"]
        return 0

    def check_dwell(self, now):
        """FT-06: dwell over the declared limit escalates to C4 automatically."""
        limit = None
        for r in self.rules.values():
            if r["kind"] == "DWELL_LIMIT":
                limit = r["params"]["limit_h"]
        if limit is None:
            return []
        fired = []
        already = {e["unit_id"] for e in self.escalations}
        for uid, u in self.units.items():
            d = self.dwell_h(uid, now)
            if d > limit and uid not in already:
                e = self._event("ESCALATION", now, unit_id=uid, dwell_h=d, limit_h=limit, to="C4")
                self.escalations.append(e)
                fired.append(e)
        return fired

    def allocate(self, need_id, candidate_unit_ids, now):
        """FT-08: FEFO; expired units excluded and flagged; condition tracked."""
        fefo = any(r["kind"] == "FEFO" for r in self.rules.values())
        cands = []
        for uid in candidate_unit_ids:
            u = self.units[uid]
            if u["expiry_ts"] is not None and u["expiry_ts"] <= now:
                self.flag(now, "EXPIRED_EXCLUDED", unit_id=uid, expiry_ts=u["expiry_ts"])
                continue
            if u["condition"] != "GOOD":
                self.flag(now, "CONDITION_NOT_GOOD", unit_id=uid, condition=u["condition"])
                continue
            cands.append(u)
        if fefo:
            cands.sort(key=lambda u: (u["expiry_ts"] if u["expiry_ts"] is not None else float("inf")))
        self._event("ALLOCATION", now, need_id=need_id, order=[u["unit_id"] for u in cands], fefo=fefo)
        return [u["unit_id"] for u in cands]

    # ------------------------------------------------------------------ FLT
    def register_finding(self, finding_id, source, text, found_ts):
        self.findings[finding_id] = {"finding_id": finding_id, "source": source, "text": text,
                                     "found_ts": int(found_ts), "status": "OPEN", "rule_id": None,
                                     "waived": None}
        self._event("FINDING", found_ts, **self.findings[finding_id])

    def resolve_finding(self, finding_id, ts, rule_id=None, waived=None):
        f = self.findings[finding_id]
        if rule_id:
            if rule_id not in self.rules:
                raise Refused("FLT: rule %s must exist before a finding is closed against it" % rule_id)
            f["status"], f["rule_id"] = "RULE_CHANGE", rule_id
        elif waived and waived.get("owner") and waived.get("date"):
            f["status"], f["waived"] = "WAIVED", dict(waived)
        else:
            raise Refused("FT-09: a finding closes only as a tracked rule change or a WAIVED record with owner + date")
        self._event("FINDING_RESOLVED", ts, finding_id=finding_id, status=f["status"])

    def activate(self, ts):
        """FT-09: open findings are displayed at activation."""
        self.activated_at = int(ts)
        open_ = [{"finding_id": f["finding_id"], "source": f["source"], "age_h": ts - f["found_ts"]}
                 for f in self.findings.values() if f["status"] == "OPEN"]
        self._event("ACTIVATION", ts, open_findings=open_)
        return open_

    # ------------------------------------------------------------------ BND
    def settle(self, commit_id, amount, money_term, ts):
        """FT-11: no settlement for a delivery lacking a C3 receipt."""
        c = self.commits.get(commit_id)
        if c is None or c["status"] != "KEPT" or not c["receipt"]:
            rec = self._event("SETTLEMENT_REFUSED", ts, commit_id=commit_id, amount=amount, reason="no C3 receipt")
            self.money.append(rec)
            raise Refused("FT-11: settlement for %s refused; the money ledger may not close ahead of the physical one" % commit_id)
        if not money_term or not money_term.get("scope"):
            raise Refused("BND: settlement needs a MONEY_TERM scope declaration")
        rec = self._event("SETTLEMENT", ts, commit_id=commit_id, amount=amount, money_term=money_term)
        self.money.append(rec)
        return rec

    # ------------------------------------------------------------------ FT-12 routes
    def declare_route(self, region, edges, assignments, ts):
        unassigned = [e for e in edges if tuple(e) not in {tuple(k) for k in assignments}]
        self.routes[region] = {"edges": [list(e) for e in edges],
                               "assignments": {"|".join(k): v for k, v in assignments.items()},
                               "unassigned": [list(e) for e in unassigned]}
        for e in unassigned:
            self.flag(ts, "ROUTE_EDGE_UNASSIGNED", region=region, edge=list(e))
        self._event("ROUTE", ts, region=region, n_edges=len(edges), unassigned=len(unassigned))
        return self.routes[region]

    # ------------------------------------------------------------------ FT-13 plan
    def preposition(self, node_id, days_of_need, ts):
        self.nodes[node_id]["prepositioned_days"] = float(days_of_need)
        self._event("PREPOSITION", ts, node_id=node_id, days_of_need=float(days_of_need))

    def coauthor_plan(self, plan_id, node_ids, ts):
        self.plans[plan_id] = {"plan_id": plan_id, "coauthors": list(node_ids)}
        for n in node_ids:
            self.nodes[n]["plan_coauthor"] = True
        self._event("PLAN", ts, plan_id=plan_id, coauthors=list(node_ids))

    def record_exercise(self, exercise_id, node_ids, ts, cellular_up):
        for n in node_ids:
            self.nodes[n]["familiarity_verified"] = True
        rec = self._event("EXERCISE", ts, exercise_id=exercise_id, nodes=list(node_ids), cellular_up=cellular_up)
        self.exercises.append(rec)

    # ------------------------------------------------------------------ metrics
    def metrics(self, now, sample_commit_ids=None):
        shipped = [u for u in self.units.values() if u["status"] not in ("AT_ORIGIN",) and u["parent_id"] is None]
        lost = [u for u in shipped if u["status"] in ("LOST", "UNKNOWN")]
        stale = [u for u in shipped if now - u["last_known"]["ts"] > OP_PERIOD_H
                 and u["status"] not in ("RECEIVED", "CLOSED", "REPACKED")]
        commits = list(self.commits.values()) if sample_commit_ids is None else \
            [self.commits[c] for c in sample_commit_ids]
        receipted = [c for c in commits if c["receipt"]]
        dwell = sorted(self.dwell_h(uid, now) for uid, u in self.units.items()
                       if u["status"] in ("AT_REST",))
        refused = [m for m in self.money if m["type"] == "SETTLEMENT_REFUSED"]
        settled = [m for m in self.money if m["type"] == "SETTLEMENT"]
        need_gap = {nid: max(0.0, n["qty"] - n["delivered"]) for nid, n in self.needs.items()}

        def pct(a, b):
            return (100.0 * a / b) if b else None

        return {
            "units_shipped": len(shipped),
            "visibility_lost_pct": pct(len(lost) + len(stale), len(shipped)),
            "receipt_rate_pct": pct(len(receipted), len(commits)),
            "dwell_h": {"n": len(dwell), "max": dwell[-1] if dwell else 0,
                        "median": dwell[len(dwell) // 2] if dwell else 0,
                        "over_limit_escalated": len(self.escalations)},
            "settlements": {"settled": len(settled), "refused_no_receipt": len(refused),
                            "refusal_rate_pct": pct(len(refused), len(refused) + len(settled))},
            "flags": _count(self.flags, "code"),
            "open_findings": [f["finding_id"] for f in self.findings.values() if f["status"] == "OPEN"],
            "provisional_nodes": [n for n, v in self.nodes.items() if v["status"] == "PROVISIONAL"],
            "need_gap_declared_units": need_gap,
            "copies_consistent": self.copies_consistent(),
        }


def _count(records, key):
    out = defaultdict(int)
    for r in records:
        out[r[key]] += 1
    return dict(out)
