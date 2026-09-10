# Build note — v0.1

## Q-1 (blocking): which path produced a refusal?

Two paths existed in v0, and the stale set named the second:

```
 path A  factor declared AFTER the event      -> FLAG  CONVERSION_DECLARED_POST_EVENT, need credited
 path B  NO factor declared for the pair      -> receive() raised Refused; unit stayed IN_TRANSIT
                                                 (SNACK-2: protein_g against a kcal need)
```

Path B was not a leftover; it was intended as "conversion required". But it had a
side effect the v0 note did not state: refusing the *receipt* left a unit that was
physically at the pantry recorded as IN_TRANSIT. That is the physical ledger being
held hostage to the unit ledger, the same shape as FT-02.

v0.1 resolution, built and rerun:

```
 receive(need_id=...)   receipt recorded, unit RECEIVED, signed handover to the receiver   (physical fact)
                        need credit attempted via substitute()
                          factor present, pre-event   -> credited
                          factor present, post-event  -> credited + FLAG CONVERSION_DECLARED_POST_EVENT
                          no factor                   -> NOT credited + FLAG SUBSTITUTION_UNCREDITED
 substitute() direct    no factor -> Refused (the T row "inject substitution -> conversion required")
```

The stale set in the v0.1 replay no longer contains a refused substitution; it contains
the unreceipted deliveries, the unsigned drops (I-12) and the silent load (I-9).

## What I-12 does to the table

At 20% custodian availability, 23 last-mile loads are dropped at pantries with no one
to sign. Every one is detected as an unsigned transfer (FT-16 shall and target hold),
and every one is an open commitment, so the receipt rate falls to about 88% and FT-05
fails its 95% target while its shall holds. FT-01's stale set grows the same way. Those
two FAILs are the Maria availability figure propagating through the ledger, reported as
found.

CRIT-1, an R2 custody-axis load declared at origin and never checked on, is the first
heartbeat escalation of the run (period-2 sweep). That is finding #3's shape: a critical
load sitting in a CONUS yard with nobody's silence being abnormal.

## Resolutions carried from v0 (accepted)

shall/target split (now every row); gate-in = delivery; `record_custody` ≠ unit
`custody`; post-event conversion = flag; failures by inject construction reported, not waived.

## New resolutions in v0.1

- **Failure record = one validator.** Nine record types (FLAG, LOST, BROKEN,
  SETTLEMENT_REFUSED, ESCALATION, HEARTBEAT_MISSED, CONTESTED_CUSTODY, UNSIGNED_TRANSFER,
  MISSING_CLASS_ASSIGNMENT) go through `_failure()`, which runs `check_locus`. SITE is
  derived from the node's damage state, or `pre-event` before activation, unless given.
- **Ledger-generated failures carry a locus from the finding they trace to.** Manifest
  and settlement failures are `regime.market` (findings #2, #4); dwell is `regime.urgency`
  (#11's regime half); identity, records and heartbeat are `regime.custody`; a competing
  claim is `regime.security`. These are codings and can be re-coded in one place each.
- **Class assignment lives on the unit and is inherited by repack children.**
- **Presence without custody uses a 1 h grace** so a gate-in and its receipt in the same
  hour do not fire. Longer than that with no handover is an unsigned transfer.
- **The heartbeat sweep is the detector.** `check_heartbeat(now)` must be called at least
  once per interval; the `within_one_interval` field records whether it was.
- **V10 sources could not be fetched.** The Katrina and GAO fixtures are coded from
  recall, with `titles_verified: false`, `pages_verified: false`, per-row confidence, and
  `tally_citable: false`. They are placeholders in the schema, not results.

## V11 (added after the v0.1 order)

- **Climate is a ledger state, a load field and a trigger-table field.** `declare_event` flips
  all three in the same step as the V4 reclass; `climate_changed` is recorded on the EVENT
  record beside `manual_steps`.
- **A load created with no climate gets `stable` and a `CLIMATE_DEFAULTED` flag.** CRIT-1 in
  the replay shows it.
- **Targets carry `climate` and `measured_in`.** The verdict function compares the target's
  climate to the run's; a mismatch is `NOT VALID (climate)` with the measured value still
  shown. FT-05's 95% receipt target was a pre-event drill figure. In v0.1 it read FAIL under
  I-12; under V11 it reads not valid, which is the truer statement: nobody measured 95% at 20%
  custodian availability. A variable-climate receipt target has to be declared before it can
  fail.
- **Spec rows carry the climate of their baseline** in `spec_rows.json` (OIG rows variable;
  pre-event and design rows stable). The results table shows row climate, target climate and
  run climate side by side.
- **Field-fix check = {sign, dof, state_updated}.** Under variable climate every handover and
  every physical contact takes one; absent -> `FIELD_FIX_MISSING`; malformed -> SchemaError.
  The replay's unattended drops are contacts with no node to run it, and they flag twice
  (unsigned transfer, field-fix missing), which is two different shalls failing on one event.
  DOF is recorded as the list of things the node could still change; the ledger does not
  judge the list.
