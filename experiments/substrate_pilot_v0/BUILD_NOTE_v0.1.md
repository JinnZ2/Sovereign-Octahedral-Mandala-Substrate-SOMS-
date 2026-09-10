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

## V1 revision (definitions after the two-grader run)

- `regime.learning` and SITE `unknown` added. `unknown` rejects `physical_damage` like the
  other non-damaged sites: damage is coded only once it is established.
- Definitions live in `ledger.LOCUS_DEFINITIONS` and print with every tally, so a grader
  reads the same text the validator enforces. Mechanism, not motive.
- Recoded under the definitions: the ledger's own MISSING_CLASS_ASSIGNMENT (V8) and the
  replay's AAR finding are `regime.learning`; Katrina row 9 (Pam exercise findings not
  converted) is `regime.learning` (my coding, marked). Maria row 5 keeps the section-4
  coding (`regime.custody`) because that table is the grader's; an `editor_note` on the row
  says the definition points to learning, for the second grader to decide.
- The replay's locus tally shifts by one record (the activation flag) from custody to learning.

## V2 second grader loaded

- The DeepSeek coding (blind, cross-family, 2026-09-10) is in the fixture row by row, with
  `disagreement` filled where the two gradings differ (11 of 13 rows on locus; row 10 on site).
- `locus_tally.agreement()` computes the agreement block from the rows: SITE 12/13, any regime
  component 12/13 vs 13/13, top level 9/13 with kappa 0.054 (observed 0.692, expected 0.675), pure
  physical_damage 1 vs 0, sub-axis exact 2 / overlap 4 / disjoint 6 of 12. Every figure in the
  order's block reproduces; the selftest asserts them.
- Top-level class: `regime` = every component a regime axis (so mixed(market,custody) is
  regime); `mixed` = damage plus a regime axis; `physical_damage` = damage only. That is the
  reading under which the order's 11 | 2 | 0 holds; the earlier tally counted any two-part
  locus as mixed and would have read 6 for grader 2.
- N-1 does not fire. Grader 2 moved no row to physical_damage and dissolved the one pure
  damage row into mixed(physical_damage, urgency). The separation claim survives both codings.
- The sub-axis enum did not: 6 of 12 disjoint. Neither grading was made under the V1
  definitions, so `tally_citable.sub_axis` is false and stays false until both are recoded
  under them. Row 10's site split is the case SITE `unknown` was added for; the grader
  codings are left as given.

## Third grader, instrument fix, round 2, V10 sources, V10b

- **Every agreement figure is computed from the fixture rows.** Three-way: any regime
  component 12/13/13; pure damage 1/0/0; pairwise top level C-D 9, C-G 8, D-G 11 of 13;
  damage flag unanimous NO on rows 1,3,4,5,6,7,8,9 and unanimous YES on none; row 5 has three
  answers. All match the order's block.
- **Round-2 figures reproduce**: exact 11/14, overlap 2, disjoint 1 (row 9), mean Jaccard
  0.857, kappa over label sets 0.664 (observed 0.786, expected 0.362) against the order's 0.66.
- **One figure differs and is reported as computed.** GPT graded-site vs record mismatches
  compute to 7 (rows 1, 2, 3, 9, 10, 11, 12) against the order's 5, reading unspecified sites
  (rows 4, 7, 8) as agreeing with the record and counting pre-event vs undamaged on rows 1 and
  3. The order may have excluded those two. Either count supports the instrument fix.
- **Katrina top-level tally moved** from 6/3/1 to 8/1/1 with no recoding: under the top-level
  rule a regime-regime mix is regime, and two of my recalled rows were such mixes.
- **SITE is now a record fact.** `site_record` is the supplied value on every row in every
  fixture and is what `check_locus` reads. Graded sites from round 1 are retained under
  `graders.round1.<grader>.site` with `site_field: graded (deprecated)`, because they are the
  evidence for the instrument fix (a grader bent the site to license the locus).
- **physical_damage tightened** to "destroyed or disabled BY THE EVENT" after row 9 (a
  handling choice that blocks a signal is not damage). Row 9 carries `site_check`.
- **8a/8b.** The order names the split; its content is mine: 8a = GPS unused on shipments to
  PR (>75%), 8b = GPS unused on moves within PR (>96%), from the FT-03 finding text.
- **V10 sources verified, still unfetchable.** `fixtures/sources.json` carries the resolved
  titles, IDs, dates and URLs with `fetched: false`. Per the order, nothing is coded from the
  summary: stated-cause rows exist as locator stubs with `locus: null`, so V10b reads NOT
  EVALUABLE rather than a number. Retention (`recurred_in_M1`) is coded on the recalled K3-family
  mechanism rows only, by me, marked.
- **V2c** exists as an instrument: two custody sub-loci in the enum and a 14-row round-3
  template whose verbatim and grader slots are empty.
