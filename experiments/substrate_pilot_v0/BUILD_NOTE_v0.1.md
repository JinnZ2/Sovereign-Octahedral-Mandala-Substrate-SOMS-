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
