"""
field_fix.py -- field-fix check at contact nodes (ROLLUP A8; SPEC V11 NODE rule: under variable climate
every contact/custody node runs the field-fix check: sign | DOF | state updated).

  component  {id, kind: contact|mount|fastener, function: <tag>, dof_required: [..], state: {...}}
  fix        {what, effect: {sign: <tag the fix produces>, dof_removed: [..]}, recorded: bool}
  history    list of records; the fix must appear there with the component id, or the state was not updated
  check(fix, component, history) -> (verdict, reason)
     SIGN_INVERSION     the fix produces the opposite of the component's function tag
     DOF_DELETION       the fix removes a degree of freedom the component must keep
     STATE_NOT_UPDATED  the fix is not in the component's history
     OK
  order: sign, then DOF, then state. A fix can fail more than one; the first failure is the verdict and
  the rest are listed.

Function tags and their opposites are declared in OPPOSITE. Three worked cases (wax, zip tie, penny) are
the executor's constructions for the selftest, not field records.

  python field_fix.py
"""
import sys

VERDICTS = ("SIGN_INVERSION", "DOF_DELETION", "STATE_NOT_UPDATED", "OK")
OPPOSITE = {"conduct": "insulate", "insulate": "conduct", "open_on_fault": "hold_closed", "hold_closed": "open_on_fault",
            "seal": "vent", "vent": "seal", "hold_fixed": "allow_motion", "allow_motion": "hold_fixed"}


def failures(fix, component, history):
    f = []
    eff = fix.get("effect", {})
    if OPPOSITE.get(component["function"]) == eff.get("sign"):
        f.append(("SIGN_INVERSION", "%s produces %s; %s %s must %s" % (fix["what"], eff["sign"], component["kind"], component["id"], component["function"])))
    lost = [d for d in component.get("dof_required", []) if d in eff.get("dof_removed", [])]
    if lost:
        f.append(("DOF_DELETION", "%s removes %s; %s %s must keep it" % (fix["what"], ", ".join(lost), component["kind"], component["id"])))
    if not any(h.get("component") == component["id"] and h.get("fix") == fix["what"] for h in history):
        f.append(("STATE_NOT_UPDATED", "%s on %s is not in the record" % (fix["what"], component["id"])))
    return f


def check(fix, component, history):
    f = failures(fix, component, history)
    if not f:
        return "OK", "sign holds, DOF kept, state updated"
    return f[0][0], "; ".join(r for _, r in f)


CASES = {
    "wax_on_terminal": {
        "component": {"id": "battery-terminal-B2", "kind": "contact", "function": "conduct", "dof_required": []},
        "fix": {"what": "wax", "effect": {"sign": "insulate", "dof_removed": []}, "note": "wax over a corroding terminal keeps water out and current too"},
        "history": [{"component": "battery-terminal-B2", "fix": "wax"}],
        "expected": "SIGN_INVERSION",
    },
    "zip_tie_on_sliding_mount": {
        "component": {"id": "exhaust-hanger-3", "kind": "mount", "function": "hold_fixed", "dof_required": ["slide_axial"]},
        "fix": {"what": "zip tie", "effect": {"sign": "hold_fixed", "dof_removed": ["slide_axial"]}, "note": "the hanger must let the pipe grow with heat"},
        "history": [{"component": "exhaust-hanger-3", "fix": "zip tie"}],
        "expected": "DOF_DELETION",
    },
    "penny_shim_unrecorded": {
        "component": {"id": "pump-foot-NE", "kind": "mount", "function": "hold_fixed", "dof_required": []},
        "fix": {"what": "penny", "effect": {"sign": "hold_fixed", "dof_removed": []}, "note": "a penny under a foot levels the pump; the next hand does not know it is there"},
        "history": [],
        "expected": "STATE_NOT_UPDATED",
    },
    "penny_in_fuse_holder": {
        "component": {"id": "fuse-F1", "kind": "contact", "function": "open_on_fault", "dof_required": []},
        "fix": {"what": "penny", "effect": {"sign": "hold_closed", "dof_removed": []}},
        "history": [{"component": "fuse-F1", "fix": "penny"}],
        "expected": "SIGN_INVERSION",
    },
}


def run_cases():
    return {k: dict(zip(("verdict", "reason"), check(c["fix"], c["component"], c["history"])), expected=c["expected"]) for k, c in CASES.items()}


def selftest():
    res = run_cases()
    assert all(r["verdict"] == r["expected"] for r in res.values()), res
    c = CASES["penny_shim_unrecorded"]
    assert check(c["fix"], c["component"], [{"component": "pump-foot-NE", "fix": "penny"}])[0] == "OK"   # recorded -> OK
    # a fix failing sign and DOF reports sign first and lists both
    comp = {"id": "x", "kind": "mount", "function": "allow_motion", "dof_required": ["rotate"]}
    v, why = check({"what": "weld", "effect": {"sign": "hold_fixed", "dof_removed": ["rotate"]}}, comp, [])
    assert v == "SIGN_INVERSION" and "removes rotate" in why and "not in the record" in why
    print("field_fix selftest ok")


if __name__ == "__main__":
    selftest()
    for k, v in run_cases().items():
        print("%-26s %-18s %s" % (k, v["verdict"], v["reason"]))
