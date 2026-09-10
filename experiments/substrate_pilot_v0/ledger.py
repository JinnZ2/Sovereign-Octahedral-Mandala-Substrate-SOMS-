"""
Substrate coordination pilot v0.1 — ledger
===========================================
Stdlib only. Append-only event log with >= 2 copies (FT-10), paper-operable
(every record is one JSON line; forms/ holds the printable equivalents).
Transport-agnostic: a line is a line whether it arrives by radio or by hand.

Channels
  C1 STATE      units: identity, qty, declared unit, condition, expiry, custody, location
  C2 NEED       needs with declared unit, clock, dependency edges
  C3 COMMIT     commitments; KEPT only on a receiver mark
  C4 ARBITRATE  declared rules (FEFO, dwell limit) + escalations + override committee + resolver
  FLT           finding register -> rule change or WAIVED; class assignments retained (V8)
  BND           MONEY_TERM settlements, blocked without a C3 receipt

v0.1 additions
  V1  every failure record carries LOCUS + SITE; physical_damage only at a damaged site
  V3  every load carries a regime class R0..R3 and an axis (urgency | custody)
  V4  event declaration reclasses loads from a precomputed trigger table, no deliberation
  V5  custody moves only by signed handover; presence without custody is an unsigned transfer
  V6  R2/R3 loads declare a max silence interval; a missed check-in escalates within one interval
  V7  a competing custody claim routes to a resolver reachable without cellular
  V8  class assignments persist in the standing plan; missing + not WAIVED -> flagged at activation
  V11 CLIMATE (stable | partial | variable) on the ledger, every load and every trigger table;
      a load with no climate defaults to stable and is flagged; event declaration flips climate
      through the trigger table; under variable climate every contact/custody node runs the
      field-fix check (sign | DOF | state updated) or the contact is flagged

Every shall is a gate here. A gate that holds raises Refused; a shall that only
flags appends a failure record. Nothing is relabelled.

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

# V1 failure locus schema. Definitions added after the two-grader run (sub-axis agreement 2/12
# exact, 6/12 disjoint): the enum was undefined. Code the MECHANISM that failed; motive goes in a note.
LOCI = ("physical_damage", "regime.market", "regime.urgency", "regime.security", "regime.custody", "regime.learning")
LOCUS_DEFINITIONS = {
    "physical_damage": "the site itself is damaged; only codable when SITE = damaged",
    "regime.market": "allocation/priority set by commercial terms, price, contract, vendor capacity",
    "regime.urgency": "speed prioritized over control; controls dropped to expedite",
    "regime.security": "protection against theft, diversion, tampering BY OTHERS",
    "regime.custody": "continuous state record + responsibility held by a named party",
    "regime.learning": "a known finding not converted to a rule (FLT)",
    "_rule": "motive vs mechanism: code the MECHANISM that failed; motive goes in a note",
}
SITES = ("damaged", "undamaged", "pre-event", "unknown")

# V3 regime classes, ordered: a lower index drops custody
REGIME_CLASSES = ("R0", "R1", "R2", "R3")      # drop-and-hook | signed tally | constant custody | dual/escort
AXES = ("urgency", "custody")

# V11 climate
CLIMATES = ("stable", "partial", "variable")
FIELD_FIX_KEYS = ("sign", "dof", "state_updated")

# failure record types (every one carries locus + site)
FAILURE_TYPES = ("FLAG", "LOST", "BROKEN", "SETTLEMENT_REFUSED", "ESCALATION", "HEARTBEAT_MISSED",
                 "CONTESTED_CUSTODY", "UNSIGNED_TRANSFER", "MISSING_CLASS_ASSIGNMENT")


class Refused(Exception):
    """A gate held. The message names the row and what was missing."""


class SchemaError(ValueError):
    """A record violated the schema (V1 locus/site, V3 class/axis)."""


def parse_locus(locus):
    """'regime.custody' -> ['regime.custody']; 'mixed(regime.urgency,physical_damage)' -> both."""
    if isinstance(locus, (list, tuple)):
        parts = list(locus)
    elif isinstance(locus, str) and locus.startswith("mixed(") and locus.endswith(")"):
        parts = [p.strip() for p in locus[6:-1].split(",") if p.strip()]
        if len(parts) < 2:
            raise SchemaError("V1: mixed(...) needs at least two loci")
    else:
        parts = [locus]
    for p in parts:
        if p not in LOCI:
            raise SchemaError("V1: unknown locus %r" % p)
    return parts


def check_locus(locus, site):
    """V1 rule: a failure at an undamaged site or pre-event may not be coded physical_damage."""
    parts = parse_locus(locus)
    if site not in SITES:
        raise SchemaError("V1: unknown site %r" % site)
    if "physical_damage" in parts and site != "damaged":
        # undamaged, pre-event and unknown all reject: damage has to be established before it is coded
        raise SchemaError("V1: physical_damage coded at site %r; damage and regime are separate ledgers" % site)
    return parts


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
        self.failures = []
        self.escalations = []
        self.conversions = {}
        self.routes = {}
        self.plans = {}
        self.exercises = []
        self.resolvers = {}
        self.trigger_table = {}          # event_type -> declared_unit -> (min_class, axis)
        self.standing_plan = {}          # declared_unit -> {"class","axis"} (V8, persists post-event)
        self.waived_assignments = {}     # declared_unit -> {"owner","date"}
        self.events_declared = []
        self.climate = "stable"
        self.climate_history = []
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

    def _failure(self, rec_type, ts, locus, site, **fields):
        """V1: every failure record carries locus + site and passes the schema check."""
        if rec_type not in FAILURE_TYPES:
            raise SchemaError("V1: %s is not a failure record type" % rec_type)
        check_locus(locus, site)
        rec = self._event(rec_type, ts, locus=locus, site=site, **fields)
        self.failures.append(rec)
        return rec

    def flag(self, ts, code, locus, site=None, **fields):
        site = site or self._site_for(fields.get("location") or fields.get("node_id"), ts)
        return self._failure("FLAG", ts, locus, site, code=code, **fields)

    @property
    def flags(self):
        return [f for f in self.failures if f["type"] == "FLAG"]

    def _site_for(self, where, ts):
        """SITE of a failure: pre-event before activation; else the damage state of the node."""
        if self.activated_at is None or ts < self.activated_at:
            return "pre-event"
        n = self.nodes.get(where)
        return "damaged" if n and n.get("damage_state") == "damaged" else "undamaged"

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
    def register_node(self, node_id, kind, region, ts=0, registered=True, custodial=True):
        status = "REGISTERED" if registered else "PROVISIONAL"        # FT-15
        self.nodes[node_id] = {"node_id": node_id, "kind": kind, "region": region,
                               "status": status, "custodial": bool(custodial), "damage_state": "undamaged",
                               "prepositioned_days": None, "plan_coauthor": False, "familiarity_verified": False,
                               "available": True}
        self._event("NODE", ts, node_id=node_id, kind=kind, region=region, status=status, custodial=bool(custodial))
        return self.nodes[node_id]

    def set_availability(self, node_id, available, ts):
        self.nodes[node_id]["available"] = bool(available)
        self._event("AVAILABILITY", ts, node_id=node_id, available=bool(available))

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
        if node_id not in self.nodes:
            raise Refused("C1: unknown node")
        return self.create_unit(unit_id, declared_unit, qty, ts, custody=node_id, location=node_id, **kw)

    # ------------------------------------------------------------------ C1
    def create_unit(self, unit_id, declared_unit, qty, ts, condition="GOOD", expiry_ts=None,
                    custody="origin", location="origin", seal_no=None, tcard=None, parent_id=None,
                    regime_class=None, axis=None, max_silence_h=None, climate=None):
        if declared_unit not in DECLARED_UNITS:
            raise Refused("FT-07: unit must carry a declared unit %s" % (DECLARED_UNITS,))
        self._check_location(location)
        climate_defaulted = climate is None
        if climate_defaulted:
            climate = "stable"                                  # V11: defaults to stable AND is flagged
        if climate not in CLIMATES:
            raise SchemaError("V11: unknown climate %r" % climate)
        u = {"unit_id": unit_id, "parent_id": parent_id, "declared_unit": declared_unit,
             "qty": float(qty), "condition": condition, "expiry_ts": expiry_ts,
             "custody": custody, "location": location, "status": "AT_ORIGIN",
             "created_ts": int(ts), "rest_since_ts": int(ts),
             "last_known": {"location": location, "ts": int(ts)},
             "channels": {"electronic": {"last_seen_ts": int(ts), "location": location},
                          "physical": {"seal_no": seal_no, "tcard": tcard,
                                       "gate_log": [{"ts": int(ts), "location": location, "event": "created"}],
                                       "last_seen_ts": int(ts), "location": location}},
             "children": [], "receipt": None, "reconciliation": None,
             "regime_class": None, "axis": None, "max_silence_h": None, "last_checkin_ts": int(ts),
             "claims": [], "climate": climate}
        self.units[unit_id] = u
        if climate_defaulted:
            self.flag(ts, "CLIMATE_DEFAULTED", "regime.custody", unit_id=unit_id, defaulted_to="stable", location=location)
        if regime_class is not None or axis is not None:
            self._assign_class(u, regime_class, axis, ts, max_silence_h, source="intake")
        self._event("UNIT", ts, **{k: v for k, v in u.items() if k != "channels"})
        return u

    @staticmethod
    def _check_location(location):
        if location is None or str(location).strip().lower().startswith("unknown"):
            raise Refused("FT-02: UNKNOWN is a status, never a location")

    # ------------------------------------------------------------------ V3 / V4 regime classes
    def _assign_class(self, u, regime_class, axis, ts, max_silence_h=None, source="intake"):
        if regime_class not in REGIME_CLASSES:
            raise Refused("V3: %r is not a regime class %s; 'critical' alone is invalid" % (regime_class, REGIME_CLASSES))
        if axis not in AXES:
            raise Refused("V3: load %s declared %s with no axis (urgency | custody); refused at intake" % (u["unit_id"], regime_class))
        if regime_class in ("R2", "R3") and max_silence_h is None:
            max_silence_h = u.get("max_silence_h") or OP_PERIOD_H
        u["regime_class"], u["axis"], u["max_silence_h"] = regime_class, axis, max_silence_h
        self._event("CLASS", ts, unit_id=u["unit_id"], regime_class=regime_class, axis=axis,
                    max_silence_h=max_silence_h, source=source)

    def declare_load(self, unit_id, regime_class, axis=None, ts=0, max_silence_h=None):
        """V3: class + axis at intake. 'critical' alone (no axis) is refused."""
        self._assign_class(self.units[unit_id], regime_class, axis, ts, max_silence_h, source="declared")

    def reclass(self, unit_id, new_class, ts, reason, source="operator"):
        """V3 rule: a custody-axis load may not drop custody to expedite."""
        u = self.units[unit_id]
        if new_class not in REGIME_CLASSES:
            raise Refused("V3: %r is not a regime class" % new_class)
        cur = u["regime_class"]
        if u["axis"] == "custody" and cur is not None and REGIME_CLASSES.index(new_class) < REGIME_CLASSES.index(cur):
            raise Refused("V3: %s is on the custody axis at %s; dropping to %s (%s) is refused" % (unit_id, cur, new_class, reason))
        self._assign_class(u, new_class, u["axis"] or "urgency", ts, u["max_silence_h"], source=source)

    def set_climate(self, climate, ts, reason, unit_ids=None):
        """V11: set the ambient climate and the climate of open loads (all, or the given ids)."""
        if climate not in CLIMATES:
            raise SchemaError("V11: unknown climate %r" % climate)
        self.climate = climate
        self.climate_history.append({"ts": int(ts), "climate": climate, "reason": reason})
        changed = []
        for uid, u in self.units.items():
            if unit_ids is not None and uid not in unit_ids:
                continue
            if u["status"] in ("RECEIVED", "CLOSED", "REPACKED"):
                continue
            if u["climate"] != climate:
                u["climate"] = climate
                changed.append(uid)
        self._event("CLIMATE", ts, climate=climate, reason=reason, loads_changed=changed)
        return changed

    def declare_trigger_table(self, event_type, table, ts, declared_by, climate="variable"):
        """V4: precomputed before the event. table: declared_unit -> (min_class, axis).
        V11: the table carries the climate the event declaration flips to."""
        for du, (cls, axis) in table.items():
            if du not in DECLARED_UNITS or cls not in REGIME_CLASSES or axis not in AXES:
                raise SchemaError("V4: bad trigger row %r -> %r" % (du, (cls, axis)))
        if climate not in CLIMATES:
            raise SchemaError("V11: trigger table for %r has no valid climate" % event_type)
        self.trigger_table[event_type] = {du: {"min_class": c, "axis": a} for du, (c, a) in table.items()}
        self.trigger_table[event_type]["_climate"] = climate
        for du, row in self.trigger_table[event_type].items():
            if du.startswith("_"):
                continue
            self.standing_plan[du] = {"class": row["min_class"], "axis": row["axis"], "event_type": event_type}
        self._event("TRIGGER_TABLE", ts, event_type=event_type, table=self.trigger_table[event_type],
                    declared_by=declared_by, climate=climate)

    def declare_event(self, event_type, ts, damaged_sites=()):
        """V4: reclass every load from the trigger table in one step. No deliberation, no manual step.
        Also marks damaged sites for V1 SITE coding."""
        table = self.trigger_table.get(event_type)
        if table is None:
            raise Refused("V4: no precomputed trigger table for event %r; declare it before the event" % event_type)
        for n in damaged_sites:
            if n in self.nodes:
                self.nodes[n]["damage_state"] = "damaged"
        climate_changed = self.set_climate(table["_climate"], ts, reason="event:" + event_type)   # V11 flip, same step
        reclassed = []
        for u in self.units.values():
            row = table.get(u["declared_unit"])
            if row is None or u["status"] in ("RECEIVED", "CLOSED", "REPACKED"):
                continue
            cur = u["regime_class"]
            if cur is None or REGIME_CLASSES.index(row["min_class"]) > REGIME_CLASSES.index(cur):
                self._assign_class(u, row["min_class"], row["axis"], ts, u["max_silence_h"], source="event:" + event_type)
                reclassed.append(u["unit_id"])
        rec = self._event("EVENT", ts, event_type=event_type, damaged_sites=list(damaged_sites),
                          reclassed=reclassed, climate=table["_climate"], climate_changed=len(climate_changed),
                          manual_steps=0)
        self.events_declared.append(rec)
        return reclassed

    def end_event(self, ts):
        """V8: class assignments persist in the standing plan; nothing is cleared here."""
        self._event("EVENT_END", ts, standing_plan=dict(self.standing_plan))

    def waive_assignment(self, declared_unit, owner, date, ts):
        if not owner or not date:
            raise Refused("V8: a waiver needs owner + date")
        self.waived_assignments[declared_unit] = {"owner": owner, "date": date}
        self._event("WAIVED_ASSIGNMENT", ts, declared_unit=declared_unit, owner=owner, date=date)

    # ------------------------------------------------------------------ movement
    def release(self, unit_id, to_node, carrier, ts, commit_id=None, field_fix=None):
        """Origin gate. FT-01: no state record -> held. V3: a load without class + axis -> held."""
        u = self.units.get(unit_id)
        if u is None:
            raise Refused("FT-01: unit %s has no state record; movement held at the gate" % unit_id)
        if u["status"] not in ("AT_ORIGIN", "AT_REST"):
            raise Refused("C1: unit %s is %s, cannot release" % (unit_id, u["status"]))
        if u["regime_class"] is None or u["axis"] is None:
            raise Refused("V3: load %s has no regime class + axis; held at the gate" % unit_id)
        u["status"] = "IN_TRANSIT"
        self._handover(u, u["custody"], carrier, ts, signed_by=(u["custody"], carrier), kind="release", field_fix=field_fix)
        cid = commit_id or "C-%s" % unit_id
        self.commits[cid] = {"commit_id": cid, "actor": carrier, "unit_id": unit_id, "to_node": to_node,
                             "by_ts": None, "status": "OPEN", "receipt": None, "opened_ts": int(ts)}
        self._event("COMMIT", ts, **self.commits[cid])
        return self.commits[cid]

    def field_fix(self, node_id, unit_id, ts, check=None):
        """V11 NODE rule: under variable climate every contact/custody node runs the field-fix check
        (sign | DOF | state updated). Missing -> flagged. Malformed -> SchemaError."""
        if self.climate != "variable":
            return None
        if check is None:
            return self.flag(ts, "FIELD_FIX_MISSING", "regime.custody", node_id=node_id, unit_id=unit_id, climate=self.climate)
        if set(check) != set(FIELD_FIX_KEYS) or not check["sign"] or not isinstance(check["dof"], (list, tuple)) \
                or check["state_updated"] is not True:
            raise SchemaError("V11: field-fix check needs sign (who), dof (list of what could be changed), state_updated True")
        return self._event("FIELD_FIX", ts, node_id=node_id, unit_id=unit_id, sign=check["sign"],
                           dof=list(check["dof"]), state_updated=True, climate=self.climate)

    def _handover(self, u, from_c, to_c, ts, signed_by, kind, field_fix=None):
        """V5 / FT-16: custody changes only by a signed handover naming both parties.
        V11: under variable climate the receiving node runs the field-fix check."""
        if not signed_by or len(signed_by) != 2 or not all(signed_by):
            raise Refused("FT-16: custody transfer of %s needs a handover signed by both parties" % u["unit_id"])
        u["custody"] = to_c
        self.field_fix(to_c, u["unit_id"], ts, field_fix)
        u["last_checkin_ts"] = int(ts)
        self._touch(u, "physical", u["location"], ts, event="%s: custody %s -> %s" % (kind, from_c, to_c))
        self._event("HANDOVER", ts, unit_id=u["unit_id"], from_custody=from_c, to_custody=to_c,
                    signed_by=list(signed_by), kind=kind)

    def _touch(self, u, channel, location, ts, event=None):
        ch = u["channels"][channel]
        ch["last_seen_ts"] = int(ts)
        ch["location"] = location
        if channel == "physical" and event:
            ch["gate_log"].append({"ts": int(ts), "location": location, "event": event})
        u["last_known"] = {"location": location, "ts": int(ts)}
        u["location"] = location

    def observe(self, unit_id, channel, location, ts, event=None, by=None, field_fix=None):
        """A state observation on one channel. FT-03: losing the electronic channel loses no state.
        A physical observation by the custodian counts as a check-in (V6)."""
        u = self.units[unit_id]
        self._check_location(location)
        if channel == "electronic" and not (self.electronic_up and self.cellular_up):
            self._event("OBS_DROPPED", ts, unit_id=unit_id, channel=channel, reason="electronic channel down")
            return False
        self._touch(u, channel, location, ts, event=event)
        if channel == "physical" and (by is None or by == u["custody"]):
            u["last_checkin_ts"] = int(ts)
        if channel == "physical":
            self.field_fix(by or location, unit_id, ts, field_fix)     # a contact under variable climate
        self._event("OBS", ts, unit_id=unit_id, channel=channel, location=location, by=by)
        return True

    def checkin(self, unit_id, ts, by):
        """V6: a custodian check-in on an R2/R3 load."""
        u = self.units[unit_id]
        if by != u["custody"]:
            raise Refused("V6: check-in on %s by %s who is not the custodian (%s)" % (unit_id, by, u["custody"]))
        u["last_checkin_ts"] = int(ts)
        self._event("CHECKIN", ts, unit_id=unit_id, by=by)

    def arrive_at_rest(self, unit_id, location, ts, custody, signed_by=None, field_fix=None):
        u = self.units[unit_id]
        self._check_location(location)
        u["status"] = "AT_REST"
        u["rest_since_ts"] = int(ts)
        if custody != u["custody"]:
            self._handover(u, u["custody"], custody, ts, signed_by or (u["custody"], custody), kind="gate-in", field_fix=field_fix)
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

    def mark_lost(self, unit_id, ts, locus="regime.custody", site=None):
        """FT-02: LOST keeps last-known position + time; nothing is overwritten."""
        u = self.units[unit_id]
        u["status"] = "LOST"
        self._failure("LOST", ts, locus, site or self._site_for(u["last_known"]["location"], ts),
                      unit_id=unit_id, last_known=dict(u["last_known"]))
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
        """FT-04: repack creates child IDs linked to the parent; no manifest -> flagged (regime.custody)."""
        p = self.units[parent_id]
        if manifest is None or not manifest.get("lists_unit_ids"):
            self.flag(ts, "REPACK_WITHOUT_MANIFEST", "regime.custody", parent_id=parent_id, by=by,
                      manifest=manifest, location=p["location"])
        out = []
        for child_id, qty in children:
            c = self.create_unit(child_id, p["declared_unit"], qty, ts, condition=p["condition"],
                                 expiry_ts=p["expiry_ts"], custody=p["custody"], location=p["location"],
                                 parent_id=parent_id, seal_no=(manifest or {}).get("seal_no"),
                                 regime_class=p["regime_class"], axis=p["axis"], max_silence_h=p["max_silence_h"],
                                 climate=p["climate"])
            c["status"] = p["status"]
            p["children"].append(child_id)
            out.append(c)
        p["status"] = "REPACKED"
        self._event("REPACK", ts, parent_id=parent_id, children=[c[0] for c in children], manifest=manifest, by=by)
        return out

    def transfer(self, unit_id, to_custody, ts, manifest=None, signed_by=None, field_fix=None):
        """Custody transfer by signed handover (FT-16). A manifest that does not name the unit is
        flagged (regime.market: the carrier's commercial frame in the critical path, finding #2)."""
        u = self.units[unit_id]
        if manifest is None or unit_id not in manifest.get("unit_ids", []):
            self.flag(ts, "TRANSFER_MANIFEST_GENERIC", "regime.market", unit_id=unit_id, to_custody=to_custody,
                      manifest=manifest, location=u["location"])
        self._handover(u, u["custody"], to_custody, ts, signed_by, kind="transfer", field_fix=field_fix)
        self._event("TRANSFER", ts, unit_id=unit_id, to_custody=to_custody, manifest=manifest)

    # ------------------------------------------------------------------ V5 presence without custody
    def check_presence(self, now, grace_h=1):
        """FT-16: a unit whose last physical observation is at a node that is not its custodian, older
        than grace_h, with no handover since, is an unsigned transfer."""
        fired = []
        already = {f["unit_id"] for f in self.failures if f["type"] == "UNSIGNED_TRANSFER"}
        for uid, u in self.units.items():
            if u["status"] in ("RECEIVED", "CLOSED", "REPACKED", "LOST") or uid in already:
                continue
            loc = u["channels"]["physical"]["location"]
            node = self.nodes.get(loc)
            if node is None or loc == u["custody"]:
                continue
            seen = u["channels"]["physical"]["last_seen_ts"]
            if now - seen >= grace_h and self._last_handover_ts(uid) < seen:
                rec = self._failure("UNSIGNED_TRANSFER", now, "regime.custody", self._site_for(loc, now),
                                    unit_id=uid, present_at=loc, custodian_of_record=u["custody"],
                                    node_custodial=node["custodial"], since_ts=seen)
                fired.append(rec)
        return fired

    def _last_handover_ts(self, unit_id):
        ts = -10 ** 9
        for e in self.events:
            if e["type"] == "HANDOVER" and e["unit_id"] == unit_id:
                ts = e["ts"]
        return ts

    # ------------------------------------------------------------------ V6 heartbeat
    def check_heartbeat(self, now):
        """FT-17: silence is never a normal state. An R2/R3 load silent past its interval escalates
        to the resolver; detection latency is recorded."""
        fired = []
        # a missed record is "open" until the next check-in; after a check-in a new silence fires again
        last_missed = {}
        for f in self.failures:
            if f["type"] == "HEARTBEAT_MISSED":
                last_missed[f["unit_id"]] = f["ts"]
        for uid, u in self.units.items():
            if u["regime_class"] not in ("R2", "R3") or u["status"] in ("RECEIVED", "CLOSED", "REPACKED", "LOST"):
                continue
            if last_missed.get(uid, -10 ** 9) >= u["last_checkin_ts"]:
                continue
            silence = now - u["last_checkin_ts"]
            if silence > u["max_silence_h"]:
                latency = silence - u["max_silence_h"]
                rec = self._failure("HEARTBEAT_MISSED", now, "regime.custody", self._site_for(u["location"], now),
                                    unit_id=uid, silence_h=silence, max_silence_h=u["max_silence_h"],
                                    detection_latency_h=latency, routed_to=self._resolver_id(),
                                    within_one_interval=latency <= u["max_silence_h"])
                fired.append(rec)
        return fired

    # ------------------------------------------------------------------ V7 resolver + contested custody
    def declare_resolver(self, resolver_id, contact_paths, ts):
        """FT-18: the resolver must be reachable without cellular."""
        non_cell = {k: v for k, v in contact_paths.items() if k not in ("cellular", "sms", "mobile")}
        if not non_cell:
            raise Refused("FT-18: resolver %s has a cellular-only contact record" % resolver_id)
        self.resolvers[resolver_id] = {"resolver_id": resolver_id, "contact_paths": dict(contact_paths),
                                       "non_cellular_paths": list(non_cell)}
        self._event("RESOLVER", ts, **self.resolvers[resolver_id])

    def _resolver_id(self):
        return next(iter(self.resolvers), None)

    def claim_custody(self, unit_id, claimant, ts, basis=""):
        """FT-18: a competing claim on an R2/R3 load routes to the resolver; custody does not move."""
        u = self.units[unit_id]
        if claimant == u["custody"]:
            return None
        u["claims"].append({"claimant": claimant, "ts": int(ts), "basis": basis})
        if u["regime_class"] in ("R2", "R3"):
            rid = self._resolver_id()
            if rid is None:
                raise Refused("FT-18: contested custody on %s with no declared resolver" % unit_id)
            return self._failure("CONTESTED_CUSTODY", ts, "regime.security", self._site_for(u["location"], ts),
                                 unit_id=unit_id, claimant=claimant, custodian_of_record=u["custody"],
                                 routed_to=rid, resolver_paths=self.resolvers[rid]["non_cellular_paths"])
        return self._event("CLAIM_NOTED", ts, unit_id=unit_id, claimant=claimant)

    def resolve_claim(self, unit_id, ts, resolver_id, award_to, signed_by, field_fix=None):
        u = self.units[unit_id]
        if resolver_id not in self.resolvers:
            raise Refused("FT-18: %s is not a declared resolver" % resolver_id)
        if award_to != u["custody"]:
            self._handover(u, u["custody"], award_to, ts, signed_by, kind="resolved", field_fix=field_fix)
        self._event("CLAIM_RESOLVED", ts, unit_id=unit_id, resolver_id=resolver_id, award_to=award_to)

    # ------------------------------------------------------------------ FT-07 conversions
    def declare_conversion(self, from_unit, to_unit, factor, ts, declared_by):
        self.conversions[(from_unit, to_unit)] = {"factor": float(factor), "declared_ts": int(ts),
                                                  "declared_by": declared_by}
        self._event("CONVERSION", ts, from_unit=from_unit, to_unit=to_unit, factor=float(factor), declared_by=declared_by)

    def substitute(self, need_id, unit_id_in, ts, event_ts=0):
        """Credit a unit of a different declared unit against a need. No declared factor -> Refused.
        A factor declared after the event -> credited and flagged (regime.market, finding #7)."""
        need = self.needs[need_id]
        u = self.units[unit_id_in]
        key = (u["declared_unit"], need["declared_unit"])
        if u["declared_unit"] == need["declared_unit"]:
            return {"converted_qty": u["qty"], "factor": 1.0}
        conv = self.conversions.get(key)
        if conv is None:
            raise Refused("FT-07: substitution %s -> %s has no declared conversion factor" % key)
        if conv["declared_ts"] > event_ts:
            self.flag(ts, "CONVERSION_DECLARED_POST_EVENT", "regime.market", need_id=need_id, unit_id=unit_id_in,
                      declared_ts=conv["declared_ts"], event_ts=event_ts, location=u["location"])
        converted = u["qty"] * conv["factor"]
        self._event("SUBSTITUTION", ts, need_id=need_id, unit_id=unit_id_in, from_unit=key[0],
                    to_unit=key[1], factor=conv["factor"], converted_qty=converted)
        return {"converted_qty": converted, "factor": conv["factor"]}

    # ------------------------------------------------------------------ C3
    def receive(self, commit_id, ts, receiver_mark=None, need_id=None, field_fix=None):
        """FT-05: delivery = receiver mark. State stays IN_TRANSIT until the receipt exists.
        Q-1 (v0.1): the receipt records the physical fact. If the unit cannot be credited against the
        need (no declared conversion), the delivery is still RECEIVED; the need is not credited and
        the failure is recorded. The physical ledger is not held hostage to the unit ledger."""
        c = self.commits[commit_id]
        if not receiver_mark or receiver_mark.get("kind") not in RECEIVER_MARKS or not receiver_mark.get("by"):
            raise Refused("FT-05: no receiver mark (signature/stamp/photo + by); unit stays IN_TRANSIT")
        u = self.units[c["unit_id"]]
        c["status"] = "KEPT"
        c["receipt"] = dict(receiver_mark, ts=int(ts))
        u["status"] = "RECEIVED"
        u["receipt"] = c["receipt"]
        self._handover(u, u["custody"], c["to_node"], ts, signed_by=(u["custody"], receiver_mark["by"]), kind="receipt", field_fix=field_fix)
        if need_id and need_id in self.needs:
            need = self.needs[need_id]
            try:
                need["delivered"] += self.substitute(need_id, u["unit_id"], ts, event_ts=self.activated_at or 0)["converted_qty"]
            except Refused as e:
                self.flag(ts, "SUBSTITUTION_UNCREDITED", "regime.market", need_id=need_id, unit_id=u["unit_id"],
                          reason=str(e), location=c["to_node"])
        self._event("RECEIPT", ts, commit_id=commit_id, unit_id=u["unit_id"], receipt=c["receipt"])
        self._maybe_promote(c["actor"], ts)
        return c

    def break_commit(self, commit_id, ts, reason, locus="regime.custody", site=None):
        c = self.commits[commit_id]
        c["status"] = "BROKEN"
        self._failure("BROKEN", ts, locus, site or self._site_for(c["to_node"], ts), commit_id=commit_id, reason=reason)

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
        """FT-06: dwell over the declared limit escalates to C4 automatically (regime.urgency)."""
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
                e = self._failure("ESCALATION", now, "regime.urgency", self._site_for(u["location"], now),
                                  unit_id=uid, dwell_h=d, limit_h=limit, to="C4")
                self.escalations.append(e)
                fired.append(e)
        return fired

    def allocate(self, need_id, candidate_unit_ids, now):
        """FT-08: FEFO; expired units excluded and flagged; condition tracked (regime.custody)."""
        fefo = any(r["kind"] == "FEFO" for r in self.rules.values())
        cands = []
        for uid in candidate_unit_ids:
            u = self.units[uid]
            if u["expiry_ts"] is not None and u["expiry_ts"] <= now:
                self.flag(now, "EXPIRED_EXCLUDED", "regime.custody", unit_id=uid, expiry_ts=u["expiry_ts"], location=u["location"])
                continue
            if u["condition"] != "GOOD":
                self.flag(now, "CONDITION_NOT_GOOD", "regime.custody", unit_id=uid, condition=u["condition"], location=u["location"])
                continue
            cands.append(u)
        if fefo:
            cands.sort(key=lambda u: (u["expiry_ts"] if u["expiry_ts"] is not None else float("inf")))
        self._event("ALLOCATION", now, need_id=need_id, order=[u["unit_id"] for u in cands], fefo=fefo)
        return [u["unit_id"] for u in cands]

    # ------------------------------------------------------------------ FLT
    def register_finding(self, finding_id, source, text, found_ts, locus=None, site=None):
        self.findings[finding_id] = {"finding_id": finding_id, "source": source, "text": text,
                                     "found_ts": int(found_ts), "status": "OPEN", "rule_id": None,
                                     "waived": None, "locus": locus, "site": site}
        if locus is not None:
            check_locus(locus, site)
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
        """FT-09: open findings displayed at activation. V8: a declared unit in use with no standing
        class assignment and no WAIVED record is flagged."""
        self.activated_at = int(ts)
        open_ = [{"finding_id": f["finding_id"], "source": f["source"], "age_h": ts - f["found_ts"]}
                 for f in self.findings.values() if f["status"] == "OPEN"]
        missing = []
        in_use = {u["declared_unit"] for u in self.units.values()} | {n["declared_unit"] for n in self.needs.values()}
        for du in sorted(in_use):
            if du not in self.standing_plan and du not in self.waived_assignments:
                self._failure("MISSING_CLASS_ASSIGNMENT", ts, "regime.learning", "pre-event", declared_unit=du)
                missing.append(du)
        self._event("ACTIVATION", ts, open_findings=open_, missing_class_assignments=missing)
        return open_

    # ------------------------------------------------------------------ BND
    def settle(self, commit_id, amount, money_term, ts):
        """FT-11: no settlement for a delivery lacking a C3 receipt (regime.market, finding #4)."""
        c = self.commits.get(commit_id)
        if c is None or c["status"] != "KEPT" or not c["receipt"]:
            site = self._site_for(c["to_node"] if c else None, ts)
            rec = self._failure("SETTLEMENT_REFUSED", ts, "regime.market", site, commit_id=commit_id, amount=amount,
                                reason="no C3 receipt")
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
            self.flag(ts, "ROUTE_EDGE_UNASSIGNED", "regime.market", site="pre-event", region=region, edge=list(e))
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
                 and u["status"] not in ("RECEIVED", "CLOSED", "REPACKED", "LOST", "UNKNOWN")]
        commits = list(self.commits.values()) if sample_commit_ids is None else \
            [self.commits[c] for c in sample_commit_ids]
        receipted = [c for c in commits if c["receipt"]]
        dwell = sorted(self.dwell_h(uid, now) for uid, u in self.units.items() if u["status"] in ("AT_REST",))
        refused = [m for m in self.money if m["type"] == "SETTLEMENT_REFUSED"]
        settled = [m for m in self.money if m["type"] == "SETTLEMENT"]
        need_gap = {nid: max(0.0, n["qty"] - n["delivered"]) for nid, n in self.needs.items()}
        hb = [f for f in self.failures if f["type"] == "HEARTBEAT_MISSED"]

        def pct(a, b):
            return (100.0 * a / b) if b else None

        return {
            "units_shipped": len(shipped),
            "visibility_lost_pct": pct(len(lost) + len(stale), len(shipped)),
            "stale_units": [u["unit_id"] for u in stale], "lost_units": [u["unit_id"] for u in lost],
            "receipt_rate_pct": pct(len(receipted), len(commits)),
            "dwell_h": {"n": len(dwell), "max": dwell[-1] if dwell else 0,
                        "median": dwell[len(dwell) // 2] if dwell else 0,
                        "over_limit_escalated": len(self.escalations)},
            "settlements": {"settled": len(settled), "refused_no_receipt": len(refused),
                            "refusal_rate_pct": pct(len(refused), len(refused) + len(settled))},
            "flags": _count(self.flags, "code"),
            "failures_by_type": _count(self.failures, "type"),
            "failures_by_locus": _count(self.failures, "locus"),
            "failures_by_site": _count(self.failures, "site"),
            "heartbeat": {"missed": len(hb), "detection_latency_h_max": max([f["detection_latency_h"] for f in hb] or [0]),
                          "all_within_one_interval": all(f["within_one_interval"] for f in hb) if hb else None},
            "open_findings": [f["finding_id"] for f in self.findings.values() if f["status"] == "OPEN"],
            "provisional_nodes": [n for n, v in self.nodes.items() if v["status"] == "PROVISIONAL"],
            "need_gap_declared_units": need_gap,
            "copies_consistent": self.copies_consistent(),
            "climate": self.climate,
            "climate_history": list(self.climate_history),
            "loads_by_climate": _count(list(self.units.values()), "climate"),
            "field_fix_checks": sum(1 for e in self.events if e["type"] == "FIELD_FIX"),
        }


def _count(records, key):
    out = defaultdict(int)
    for r in records:
        out[str(r[key])] += 1
    return dict(out)
