# trigger_geometry

Was this RESPONSE validated in THIS geometry? CC0, stdlib only, no network.

It does not evaluate the sensor and does not evaluate the threshold. It evaluates the inference between
the reading and the action.

```
THE FAILURE CLASS       SENSOR CORRECT + MODEL INVERTED

 reading (correct) ──▶ inference ──▶ response ──▶ effect in THIS geometry
                           │                          │
                    derived in geometry X              └── transfers load/energy
                    applied in geometry Y                  INTO the next input cycle
                           │                                     │
                    T6 absent ≠ safe                       T2 positive feedback
                           │
                    validated on ONE instance, operated in REVERSALS  ──▶ T1 accumulation
                    (the single case damps; passing it is what hides the failure)

 redundancy ──X──▶ this class.  Two sensors agreeing on the same correct reading feed the same wrong
 inference; a third makes the wrong action more confident. Agreement lowers no flag (asserted).
```

```bash
python experiments/trigger_geometry/trigger_geometry.py cases      # validation cases A-E
python experiments/trigger_geometry/trigger_geometry.py selftest
python experiments/trigger_geometry/trigger_geometry.py evaluate trigger.json geometry.json
```

## Files

```
couplings.jsonl        responses that transfer load or energy into the next input cycle; mechanism mandatory
proxies.jsonl          sensed quantities that stand for a different state; mechanism mandatory
trigger_geometry.py    the tool
```

## Checks

```
T1_ACCUMULATION            geometry reverses AND the response was validated on a SINGLE instance. Highest severity.
                           An UNSPECIFIED instance count is treated as SINGLE: a repeated test that was run
                           would have been stated.
T2_RESPONSE_COUPLES        a coupling entry matches the response. The coupling is a fact about the system;
                           whether it is a POSITIVE FEEDBACK term depends on there being a next cycle to feed,
                           so it invalidates the response where the input repeats and is recorded where it does not.
T3_ENVELOPE_UNSTATED       no envelope stated -> UNRATED, and T3 fires ALONE. No failure is inferred from an absence.
T4_PROXY_STATE             the observable stands for the state and they decouple silently -> an independent
                           verification path is returned, from the entry, not from code.
T5_DEGRADATION_CORRELATION sensor DEGRADED here; an availability figure averaged over the envelope reports the
                           inverse of the truth at its edges. Whether consequence is highest here is not inferred.
T6_GEOMETRY_ABSENT         this geometry class is not in the validation set. ABSENT, never SAFE.
INTAKE_INCOMPLETE          reversal_period or system_relaxation_time unmeasured. A finding, never an estimate.
REDUNDANCY_NOT_MITIGATION  redundancy was declared; it changed nothing.
COUPLING_SCOPE_UNCONFIRMED the coupling fired on the response alone because the trigger states no system.
RELIABILITY_FIGURE_REJECTED an averaged figure was passed in and was refused as input.
```

## Validation cases, as run

```
A  serpentine grade, brake on lateral displacement
     T1 + T2 + T6 + INTAKE_INCOMPLETE; response_validated_here False
     operator_correction_required: "push through" -- the field that says what a human currently supplies
     two times: both unmeasured here. Supplied as 6 s reversal against 11 s relaxation, the return states
     that the next reversal arrives while the previous one is still carried.
B  single curve, flat, same trigger
     T1 does NOT fire; T2 recorded with the note that there is no next cycle to feed; validated True
C  fifth wheel coupling attached
     T4; independent verification required (a load path check, not a position check); validated False
D  falsifier: correct sensor, response derived in this geometry class, repeated instance, stated envelope
     flags empty, validated True. Something has to be able to come back clean or the instrument is an
     objection generator.
E  envelope not stated
     T3 alone, UNRATED. Unrated is a finding, not an accusation.
```

Three verdicts always, never one score: sensor (echoed, not evaluated), inference, response. `invalidated_by`
lists the checks that actually invalidated the response here, and `failure_mode_if_inverted` is composed from
those checks only.

## Two design decisions worth stating

**T1 is about the test, not the times.** A geometry with a long reversal period and a short relaxation time
still fires T1 when the validating test was a single instance: the two times say whether accumulation is
physically expected, and T1 says the operating case was never run. The selftest holds both.

**T2's severity is geometric.** The order defines T2 as a transfer into the next input cycle. Where the
input does not repeat there is no next cycle, so a matching coupling is flagged and reported without
invalidating the response. That is what makes case B discriminate instead of firing everywhere.

## Hard constraints, as implemented

```
no single safety score                         three verdicts; the selftest asserts no score/rating key exists
redundancy is never mitigation                 same flags with and without unanimous agreement, plus a flag saying so
absence returns ABSENT, never SAFE             T6 on a class mismatch and on a missing class on either side
reliability figures are not inputs             keys matching reliability/availability/MTBF/uptime are refused
no enum of geometry classes                    free text both sides; the selftest runs an unseen class
                                               (a multi-sump cave traverse) through the same logic
```

## Open (from the work order, unchanged)

reversal_period and system_relaxation_time will usually be unmeasured; the instrument returns
INTAKE_INCOMPLETE and records it rather than estimating. The geometries most likely to be absent from a
validation set are the ones their terrain forced, which is why `constructibility_note` is carried into
every return: it is the field that stops such a geometry being filed as an edge case. Getting those
geometries in front of the people writing trigger logic is an intake problem and is not solved here.
