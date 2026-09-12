"""
trigger_geometry.py -- was this RESPONSE validated in THIS geometry? (WORK ORDER trigger_geometry,
2026-09-12). CC0. Stdlib only. No network.

  It does not evaluate the sensor and does not evaluate the threshold. Those are usually fine. It
  evaluates the inference between the reading and the action.

  THE FAILURE CLASS          SENSOR CORRECT + MODEL INVERTED
  The reading is accurate. The response was derived in a geometry where it reduces the hazard and is
  applied in a geometry where it increases it. Redundancy does not touch this class: two sensors agreeing
  on the same correct reading feed the same wrong inference, and a third makes the wrong action more
  confident. Agreement between sensors never lowers a flag here (asserted in the selftest).

  CHECKS
    T1_ACCUMULATION       geometry reverses sign AND the response was validated on a SINGLE instance.
                          The validating test damps out; the operating case does not. HIGHEST SEVERITY.
    T2_RESPONSE_COUPLES   the response acts on a subsystem that transfers load or energy into the next
                          input cycle: the response is a positive feedback term.
    T3_ENVELOPE_UNSTATED  no validation envelope was stated -> UNRATED. No claim either way, and no
                          failure inferred from the absence.
    T4_PROXY_STATE        the sensed quantity stands for the state that matters and the two decouple
                          silently -> an independent verification path is required.
    T5_DEGRADATION_CORRELATION  the sensor degrades in the same conditions where consequence is highest
                          -> a figure averaged over the envelope reports the inverse of the truth.
    T6_GEOMETRY_ABSENT    this geometry class is not in the validation set. ABSENT, never SAFE.
  Non-T: INTAKE_INCOMPLETE (reversal_period or relaxation time unmeasured -- recorded as a finding,
  never estimated), REDUNDANCY_NOT_MITIGATION, COUPLING_SCOPE_UNCONFIRMED, RELIABILITY_FIGURE_REJECTED.

  THREE VERDICTS, NEVER ONE SCORE: sensor (echoed, not evaluated), inference, response.

  python trigger_geometry.py cases        run validation cases A-E
  python trigger_geometry.py selftest
  python trigger_geometry.py evaluate <trigger.json> <geometry.json>
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COUPLINGS = os.path.join(HERE, "couplings.jsonl")
PROXIES = os.path.join(HERE, "proxies.jsonl")

SENSOR_VERDICTS = ("CORRECT", "DEGRADED", "UNKNOWN")
INSTANCE_COUNTS = ("SINGLE", "REPEATED", "UNSPECIFIED")
# an average over an envelope is not evidence about the envelope's edges: these keys are refused on intake
REJECTED_INPUT_KEYS = ("reliability", "availability", "mtbf", "mttf", "failure_rate", "uptime", "confidence_interval_over_fleet")


def load(path):
    return [r for r in (json.loads(l) for l in open(path) if l.strip()) if not r.get("_header")]


def _norm(s):
    return " ".join(str(s or "").lower().replace("-", " ").replace(",", " ").split())


def _match(text, entry, key):
    t = _norm(text)
    best = 0
    for a in entry.get("aliases", []) + [entry.get(key, "")]:
        an = _norm(a)
        if an and an in t:
            best = max(best, len(an))
    return best


def find(text, entries, key):
    scored = [(s, e) for s, e in ((_match(text, e, key), e) for e in entries) if s]
    return max(scored, key=lambda x: x[0])[1] if scored else None


def geometry_in_validation_set(geometry, derived_in):
    """Free-text class comparison in both directions. No enum: an enum written now would encode the same
    validation envelope this instrument exists to expose."""
    g = _norm(geometry.get("geometry_class"))
    v = _norm(derived_in.get("geometry_class"))
    extra = [_norm(x) for x in derived_in.get("also_validated_in", [])]
    if not g or not v:
        return None
    return bool(g == v or g in v or v in g or any(g == x or g in x or x in g for x in extra))


def reject_reliability_inputs(*objs):
    bad = []
    for o in objs:
        for k in (o or {}):
            if any(r in _norm(k) for r in REJECTED_INPUT_KEYS):
                bad.append(k)
    return bad


def evaluate(trigger, geometry, couplings=None, proxies=None):
    couplings = couplings if couplings is not None else load(COUPLINGS)
    proxies = proxies if proxies is not None else load(PROXIES)
    out = {"trigger_id": trigger.get("trigger_id"), "geometry_id": geometry.get("geometry_id"),
           "geometry_class": geometry.get("geometry_class"),
           "constructibility_note": geometry.get("constructibility_note"),
           "verdicts": {"sensor": trigger.get("sensor_verdict", "UNKNOWN") + " (echoed; this instrument does not evaluate the sensor)",
                        "inference": None, "response": None},
           "flags": [], "notes": []}
    flags, notes = [], []

    bad = reject_reliability_inputs(trigger, geometry)
    if bad:
        flags.append("RELIABILITY_FIGURE_REJECTED")
        notes.append("refused as input: %s. An average over an envelope is not evidence about the envelope's edges."
                     % ", ".join(bad))

    derived = trigger.get("response_derived_in") or {}
    if not derived.get("stated"):
        # T3 ONLY. An absence is a finding, not an accusation: no other check may run off it.
        out["flags"] = ["T3_ENVELOPE_UNSTATED"] + [f for f in flags if f == "RELIABILITY_FIGURE_REJECTED"]
        out["verdicts"].update(inference="UNRATED", response="UNRATED")
        out["response_validated_here"] = "UNRATED"
        out["failure_mode_if_inverted"] = ("not determinable: no validation envelope was stated, so there is nothing "
                                           "to compare this geometry against. Unrated is a finding; it is not a claim "
                                           "that the response is wrong.")
        out["operator_correction_required"] = None
        out["notes"] = notes + ["state the geometry the response was derived in, and whether it was a single instance "
                                "or a repeated one, before any claim is made either way"]
        return out

    # T1 accumulation
    if geometry.get("reversal") and derived.get("instance_count") == "SINGLE":
        flags.append("T1_ACCUMULATION")
        notes.append("the geometry reverses sign and the response was validated on a single instance: the validating "
                     "test damps out, the operating case accumulates. Passing the single case is what makes this invisible.")
    elif geometry.get("reversal") and derived.get("instance_count") == "UNSPECIFIED":
        flags.append("T1_ACCUMULATION")
        notes.append("the geometry reverses sign and the number of instances in the validating test was not stated: "
                     "treated as SINGLE, because a repeated-instance test that was run would have been stated.")

    # the two times, never estimated
    rp, rt = geometry.get("reversal_period"), geometry.get("system_relaxation_time")
    if geometry.get("reversal"):
        if rp is None or rt is None:
            flags.append("INTAKE_INCOMPLETE")
            notes.append("unmeasured: %s. Recorded as a finding; not estimated." %
                         ", ".join([n for n, v in (("reversal_period", rp), ("system_relaxation_time", rt)) if v is None]))
        else:
            out["two_times"] = {"reversal_period_s": rp, "system_relaxation_time_s": rt,
                               "accumulates": rp < rt,
                               "statement": "the input reverses every %gs; the system needs %gs to relax. %s" % (
                                   rp, rt, "The next reversal arrives while the previous one is still carried: amplitude "
                                   "grows for geometric reasons, at inputs below the threshold."
                                   if rp < rt else "Each reversal relaxes before the next arrives.")}

    # T2 response coupling. The coupling is a fact about the response and the system; whether it is a
    # POSITIVE FEEDBACK term depends on there being a next input cycle for it to feed.
    cpl = find(trigger.get("response"), couplings, "response")
    couples_into_next_cycle = bool(cpl) and bool(geometry.get("reversal"))
    if cpl:
        flags.append("T2_RESPONSE_COUPLES")
        notes.append("response coupling: %s" % cpl["mechanism"])
        notes.append("this geometry reverses, so the transfer feeds the next input cycle: the response is a positive "
                     "feedback term here." if couples_into_next_cycle else
                     "this geometry does not reverse, so there is no next input cycle for the transfer to feed. The "
                     "coupling is recorded and does not invert the response here; it inverts it wherever the input repeats.")
        if not trigger.get("system"):
            flags.append("COUPLING_SCOPE_UNCONFIRMED")
            notes.append("the coupling entry's scope is %r and the trigger states no system: the coupling fired on the "
                         "response alone. Supply `system` to confirm or exclude it." % cpl["system_class"])

    # T4 proxy state
    prx = find(trigger.get("sensed_quantity"), proxies, "sensed_quantity")
    if prx and prx.get("decouples_silently"):
        flags.append("T4_PROXY_STATE")
        notes.append("proxy state: %s The state that matters is %s." % (prx["mechanism"], prx["actual_state"]))
        out["independent_verification_required"] = prx["independent_verification"]
    elif prx:
        notes.append("the sensed quantity is a proxy for %s, but the decoupling is not silent in this entry: %s"
                     % (prx["actual_state"], prx["mechanism"]))

    # T5 degradation correlation
    if trigger.get("sensor_verdict") == "DEGRADED":
        flags.append("T5_DEGRADATION_CORRELATION")
        notes.append("the sensor is degraded in this geometry. If this geometry is also where consequence is highest, "
                     "an availability figure averaged over the envelope reports the inverse of the truth here. "
                     "Whether consequence is highest here was not supplied and is not inferred.")

    # T6 geometry absent
    in_set = geometry_in_validation_set(geometry, derived)
    if in_set is False:
        flags.append("T6_GEOMETRY_ABSENT")
        notes.append("this geometry class (%r) is not in the validation set (%r): ABSENT, not safe."
                     % (geometry.get("geometry_class"), derived.get("geometry_class")))
    elif in_set is None:
        flags.append("T6_GEOMETRY_ABSENT")
        notes.append("no geometry class on one side of the comparison: absence returned, not safety.")

    # redundancy never mitigates an inference failure
    red = trigger.get("sensor_redundancy")
    if red:
        flags.append("REDUNDANCY_NOT_MITIGATION")
        notes.append("sensor redundancy declared (%s). It changes no flag above: agreeing sensors feed the same "
                     "inference, and a third makes the wrong action more confident." % json.dumps(red))

    # what actually invalidates the response HERE, and the failure mode composed from those checks only
    failures, modes = [], []
    if "T1_ACCUMULATION" in flags:
        failures.append("T1_ACCUMULATION")
        modes.append("the validating test damps out and this geometry accumulates: the response is timed against a case "
                     "that was never run, and the quantity rises for geometric reasons at inputs below the threshold")
    if couples_into_next_cycle:
        failures.append("T2_RESPONSE_COUPLES")
        modes.append(cpl["failure_mode_if_inverted"])
    if "T4_PROXY_STATE" in flags:
        failures.append("T4_PROXY_STATE")
        modes.append("the reading and the state can part with no signal: %s" % prx["consequence"])
    if "T6_GEOMETRY_ABSENT" in flags:
        failures.append("T6_GEOMETRY_ABSENT")
        modes.append("the response is applied in a geometry absent from its validation set, so the direction of its "
                     "effect here is unestablished")
    out["invalidated_by"] = failures
    out["verdicts"]["inference"] = "INVERTED_OR_UNVALIDATED_HERE" if failures else "VALIDATED_HERE"
    out["verdicts"]["response"] = "NOT_VALIDATED_HERE" if failures else "VALIDATED_HERE"
    out["response_validated_here"] = not failures
    out["failure_mode_if_inverted"] = " | ".join(modes) if modes else (
        "no inversion identified: the response was derived in this geometry class, on a repeated instance where the "
        "geometry reverses, and acts on no subsystem that feeds the next input cycle. A change to any one of those "
        "three returns this to open.")
    out["operator_correction_required"] = cpl.get("operator_correction") if (cpl and couples_into_next_cycle) else None
    if out["operator_correction_required"]:
        notes.append("operator_correction_required is non-null: a human currently supplies this safety function and it "
                     "appears nowhere on the ledger. Removing the human removes the function.")
    out["flags"], out["notes"] = flags, notes
    return out


# ---------------------------------------------------------------- validation cases
def case_A(**kw):
    """SERPENTINE GRADE, the reference case. MUST fire T1 and T2, return False, populate the correction."""
    trigger = {"trigger_id": "A-rollover-brake", "sensed_quantity": "chassis lateral displacement",
               "sensor_verdict": "CORRECT", "inferred_hazard": "rollover risk", "response": "brake",
               "response_derived_in": {"geometry_class": "single curve, level or mild grade", "instance_count": "SINGLE", "stated": True}}
    geometry = {"geometry_id": "driftless-descent", "geometry_class": "descending grade over 9 percent, two lanes, "
                "continuous serpentine reversals for the length of the grade",
                "reversal": True, "reversal_period": None, "system_relaxation_time": None, "gradient": 0.09,
                "constructibility_note": "the only geometry in which usable road can be built on this topography; "
                                         "the reversals are not a design choice and not an edge case"}
    trigger.update(kw.pop("trigger", {})); geometry.update(kw.pop("geometry", {}))
    return evaluate(trigger, geometry, **kw)


def case_B(**kw):
    """SINGLE CURVE, flat, same trigger. MUST NOT fire T1."""
    trigger = {"trigger_id": "B-rollover-brake", "sensed_quantity": "chassis lateral displacement",
               "sensor_verdict": "CORRECT", "inferred_hazard": "rollover risk", "response": "brake",
               "response_derived_in": {"geometry_class": "single curve, level or mild grade", "instance_count": "SINGLE", "stated": True}}
    geometry = {"geometry_id": "flat-single-curve", "geometry_class": "single curve, level or mild grade",
                "reversal": False, "reversal_period": None, "system_relaxation_time": None, "gradient": 0.01,
                "constructibility_note": "ordinary alignment; nothing about the terrain forced it"}
    trigger.update(kw.pop("trigger", {})); geometry.update(kw.pop("geometry", {}))
    return evaluate(trigger, geometry, **kw)


def case_C(**kw):
    """FIFTH WHEEL. MUST fire T4 and require an independent verification path."""
    trigger = {"trigger_id": "C-coupling-latched", "sensed_quantity": "fifth wheel coupling attached",
               "sensor_verdict": "CORRECT", "inferred_hazard": "trailer separation", "response": "permit departure",
               "response_derived_in": {"geometry_class": "level yard, coupling performed by a trained operator",
                                       "instance_count": "REPEATED", "stated": True,
                                       "also_validated_in": ["level yard", "loading dock apron"]}}
    geometry = {"geometry_id": "yard-departure", "geometry_class": "level yard", "reversal": False,
                "reversal_period": None, "system_relaxation_time": None, "gradient": 0.0,
                "constructibility_note": "standard yard surface"}
    trigger.update(kw.pop("trigger", {})); geometry.update(kw.pop("geometry", {}))
    return evaluate(trigger, geometry, **kw)


def case_D(**kw):
    """FALSIFIER. Correct sensor, correctly derived response, stated envelope INCLUDING this geometry.
    MUST return clean."""
    trigger = {"trigger_id": "D-overtemp-derate", "sensed_quantity": "gearbox oil temperature",
               "sensor_verdict": "CORRECT", "inferred_hazard": "lubricant breakdown",
               "response": "raise the oil cooler fan to full and alert the operator",
               "response_derived_in": {"geometry_class": "sustained grade climb, loaded, ambient above 30 C",
                                       "instance_count": "REPEATED", "stated": True,
                                       "also_validated_in": ["sustained grade climb", "repeated grade cycles, loaded"]}}
    geometry = {"geometry_id": "long-climb", "geometry_class": "sustained grade climb, loaded",
                "reversal": False, "reversal_period": None, "system_relaxation_time": None, "gradient": 0.06,
                "constructibility_note": "long steady climb; the alignment follows the valley"}
    trigger.update(kw.pop("trigger", {})); geometry.update(kw.pop("geometry", {}))
    return evaluate(trigger, geometry, **kw)


def case_E(**kw):
    """UNSTATED ENVELOPE. MUST return UNRATED and fire T3 ONLY."""
    trigger = {"trigger_id": "E-stability-intervene", "sensed_quantity": "chassis lateral displacement",
               "sensor_verdict": "CORRECT", "inferred_hazard": "loss of control", "response": "brake",
               "response_derived_in": {"geometry_class": None, "instance_count": "UNSPECIFIED", "stated": False}}
    geometry = {"geometry_id": "driftless-descent", "geometry_class": "descending grade over 9 percent with continuous "
                "serpentine reversals", "reversal": True, "reversal_period": 6.0, "system_relaxation_time": 11.0,
                "gradient": 0.09, "constructibility_note": "terrain-forced alignment"}
    trigger.update(kw.pop("trigger", {})); geometry.update(kw.pop("geometry", {}))
    return evaluate(trigger, geometry, **kw)


def selftest():
    couplings, proxies = load(COUPLINGS), load(PROXIES)
    for e in couplings + proxies:
        assert str(e.get("mechanism") or "").strip() and e.get("falsified_by"), e

    a = case_A()
    assert "T1_ACCUMULATION" in a["flags"], a["flags"]                      # without this the instrument is cosmetic
    assert "T2_RESPONSE_COUPLES" in a["flags"]
    assert "T6_GEOMETRY_ABSENT" in a["flags"]                               # serpentine is not the single curve
    assert "INTAKE_INCOMPLETE" in a["flags"] and "two_times" not in a       # the two times are unmeasured, not estimated
    assert a["response_validated_here"] is False
    assert a["operator_correction_required"] and "push through" in a["operator_correction_required"]
    assert a["verdicts"]["sensor"].startswith("CORRECT") and a["verdicts"]["response"] == "NOT_VALIDATED_HERE"
    assert "trailer moment" in a["failure_mode_if_inverted"] and "never run" in a["failure_mode_if_inverted"]
    assert a["invalidated_by"] == ["T1_ACCUMULATION", "T2_RESPONSE_COUPLES", "T6_GEOMETRY_ABSENT"]
    assert a["constructibility_note"].startswith("the only geometry")
    # the two times, when supplied, state the accumulation condition and never invent a number
    a2 = case_A(geometry={"reversal_period": 6.0, "system_relaxation_time": 11.0})
    assert a2["two_times"]["accumulates"] is True and "INTAKE_INCOMPLETE" not in a2["flags"]
    a3 = case_A(geometry={"reversal_period": 30.0, "system_relaxation_time": 4.0})
    assert a3["two_times"]["accumulates"] is False and "T1_ACCUMULATION" in a3["flags"]   # T1 is about the TEST, not the times
    # redundancy must not lower any flag
    a4 = case_A(trigger={"sensor_redundancy": {"n_sensors": 3, "agreement": "unanimous"}})
    assert set(a4["flags"]) == set(a["flags"]) | {"REDUNDANCY_NOT_MITIGATION"}
    assert a4["response_validated_here"] is False and a4["operator_correction_required"] == a["operator_correction_required"]

    b = case_B()
    assert "T1_ACCUMULATION" not in b["flags"], b["flags"]                   # must discriminate
    assert "T6_GEOMETRY_ABSENT" not in b["flags"]                            # this IS the validation geometry
    assert "T2_RESPONSE_COUPLES" in b["flags"]                               # the coupling is a fact about the system
    assert b["invalidated_by"] == [] and b["response_validated_here"] is True   # no next cycle for the transfer to feed
    assert b["operator_correction_required"] is None
    assert any("does not reverse" in n for n in b["notes"])

    c = case_C()
    assert "T4_PROXY_STATE" in c["flags"] and c["independent_verification_required"].startswith("a load path check")
    assert c["response_validated_here"] is False and "T1_ACCUMULATION" not in c["flags"]
    assert c["invalidated_by"] == ["T4_PROXY_STATE"]                          # the failure mode names the proxy, not a geometry
    assert "dropped trailer" in c["failure_mode_if_inverted"] and "validation set" not in c["failure_mode_if_inverted"]

    d = case_D()
    assert d["flags"] == [], d["flags"]                                      # something must be able to come back clean
    assert d["response_validated_here"] is True and d["operator_correction_required"] is None
    assert d["verdicts"] == {"sensor": "CORRECT (echoed; this instrument does not evaluate the sensor)",
                             "inference": "VALIDATED_HERE", "response": "VALIDATED_HERE"}
    assert "no inversion identified" in d["failure_mode_if_inverted"]

    e = case_E()
    assert e["flags"] == ["T3_ENVELOPE_UNSTATED"], e["flags"]                # T3 ONLY: no failure inferred from absence
    assert e["response_validated_here"] == "UNRATED" and e["operator_correction_required"] is None
    assert e["verdicts"]["inference"] == "UNRATED"

    # T5: degraded sensor flags the correlation and says what was not supplied
    t5 = case_A(trigger={"sensor_verdict": "DEGRADED"})
    assert "T5_DEGRADATION_CORRELATION" in t5["flags"]
    assert any("not inferred" in n for n in t5["notes"])
    # reliability figures are refused on intake
    rej = case_D(trigger={"fleet_availability": 0.998})
    assert "RELIABILITY_FIGURE_REJECTED" in rej["flags"] and rej["response_validated_here"] is True
    # no enum of geometry classes: an unseen class works, and absence from the set is ABSENT not SAFE
    novel = evaluate({"trigger_id": "N", "sensed_quantity": "bottom time", "sensor_verdict": "CORRECT",
                      "inferred_hazard": "decompression obligation", "response": "abort and ascend",
                      "response_derived_in": {"geometry_class": "single descent to a fixed depth", "instance_count": "SINGLE", "stated": True}},
                     {"geometry_id": "sump", "geometry_class": "multi-sump traverse with repeated re-descents",
                      "reversal": True, "reversal_period": None, "system_relaxation_time": None,
                      "constructibility_note": "the cave is the shape it is"})
    assert "T1_ACCUMULATION" in novel["flags"] and "T6_GEOMETRY_ABSENT" in novel["flags"]
    assert novel["response_validated_here"] is False
    # never a single safety score
    for r in (a, b, c, d, e, novel):
        assert not any(k in r for k in ("safety_score", "score", "rating", "risk_level"))
        assert set(r["verdicts"]) == {"sensor", "inference", "response"}
    print("trigger_geometry selftest ok")


def main(argv):
    if not argv:
        print(__doc__); return 0
    cmd, args = argv[0], argv[1:]
    if cmd == "selftest":
        selftest(); return 0
    if cmd == "cases":
        for name, fn in (("A serpentine grade (reference)", case_A), ("B single curve, flat", case_B),
                         ("C fifth wheel proxy", case_C), ("D falsifier, correctly derived", case_D),
                         ("E unstated envelope", case_E)):
            r = fn()
            print("== %s" % name)
            print("   flags: %s" % (", ".join(r["flags"]) or "(none)"))
            print("   verdicts: sensor %s | inference %s | response %s" % (r["verdicts"]["sensor"].split(" (")[0],
                                                                          r["verdicts"]["inference"], r["verdicts"]["response"]))
            print("   response_validated_here: %s" % r["response_validated_here"])
            if r.get("two_times"):
                print("   two times: %s" % r["two_times"]["statement"])
            print("   failure mode if inverted: %s" % r["failure_mode_if_inverted"])
            if r.get("independent_verification_required"):
                print("   independent verification: %s" % r["independent_verification_required"])
            print("   operator correction required: %s" % (r["operator_correction_required"] or "none"))
            for n in r["notes"]:
                print("     - %s" % n)
            print()
        return 0
    if cmd == "evaluate":
        print(json.dumps(evaluate(json.load(open(args[0])), json.load(open(args[1]))), indent=1)); return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
