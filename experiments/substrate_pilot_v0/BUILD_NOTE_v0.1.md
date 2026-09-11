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

## Source text loaded (maria_verbatim.jsonl, katrina_passages.jsonl)

- **SITE corrections came from the record, not from a grader.** Row 9: the OIG sentence
  places the signal loss on barges and at staging yards on shipments TO Puerto Rico, so the
  site is undamaged. The fixture's section-4 site already said undamaged; the site supplied to
  the round-2 graders said damaged, in error, and row 9 was the only round-2 disjoint row.
  Under the record site GPT's `physical_damage` is schema-invalid; the coding is kept and
  flagged, and round 2 is reported both ways. Row 10: where the food expired is not stated, so
  the site changes undamaged -> `unknown`, which is what the enum value was added for; the
  round-1 DeepSeek `mixed(physical_damage, custody)` on that row is schema-invalid under it.
  Row 8b (within Puerto Rico) is damaged; 8a (to Puerto Rico) is not.
- **Row 13 is two sources.** The 20%-of-drivers figure is press; the OIG sentence is the
  infrastructure damage statement. The fixture notes it; the section-4 finding text stays.
- **V2c is ready to run.** The round-3 template carries the verbatim sentence, page, record
  site and context for all 14 rows plus C1-C3; grader slots are empty.
- **New verbatim candidates C1-C4 and audit stated causes A1-A2** are carried as rows with
  `locus: null`. C2 is FT-02's relabel in the OIG's own words (2,402 records to "unknown FSAs").
  C4 is FEMA's management comment that reconciliation found all but 19 of 9,775 containers,
  with the OIG's reply that finding containers is not finding contents: a measurand crossing
  inside a self-review, carried under doc_type self-review for V10b. A1 names both damage and
  "did not follow established policies and procedures" in one sentence; graders will have to
  code the mechanism.
- **Katrina.** K3 pp.1-43 verbatim replaces the locator stubs. K3-4 ("in the pipeline") is the
  location-as-status relabel, the Katrina shape of C2. K3-8 is a positive control (Mississippi,
  authority at the contact node). K1's logistics chapter is still unread; the recalled rows for
  it stay marked as recalled.
- **V10b stays NOT EVALUABLE**: every stated-cause row is now verbatim, and none is graded.
  `fixtures/stated_causes_grader_template.jsonl` lists them across documents and events.
- `spec_rows.json` now points FT rows at their verbatim OIG rows and pages where one exists.

## Round 3 reported; V10b withdrawn as a test; V10c added

- **Round 3 is loaded as reported, not recomputed.** The report gave aggregates, not per-row
  codings. They sit in the round-3 template header under `reported_aggregates` with
  `computed: false`. `locus_tally.round3()` computes the same figures (unanimity on the full
  enum and with custody collapsed, pure damage, custody.state share and unanimity, rule
  violations against the record site, stability against round 2 collapsed) the moment
  `grader_gpt`, `grader_deepseek`, `grader_kimi` are filled. Until then the tally prints
  the reported line with that label.
- **Citability follows the report.** `round3_sub_axis_collapsed: true`; custody split citable
  as state >> responsibility. Both statements carry "reported basis" in the claim table.
- **GPT row 9 stays.** physical_damage at an undamaged record site is a rule violation;
  the instrument flags it and keeps it, as in round 2.
- **V10b is not a test.** One review row and one self-review row give the across-document
  comparison no denominator. The instrument stays; its status is NOT A TEST.
- **V10c replaces the question inside the document.** Stated-cause sentences vs finding
  sentences of the same report on the same enum. M1 has A1 and A2 against the graded
  findings; A1 reportedly came back unanimous mixed(physical_damage, regime.urgency), which
  is the audit's own sentence naming both. Computes when the stated-cause rows are graded.
- **Caveat recorded.** An audit reads the record trail; custody.state may dominate because
  that is what an audit can see. The enum has not been run on a non-audit source.

## V2d built (authority x source)

- Seven verbatim rows rewritten with the agent, contractor, port and place held as
  placeholders; every row names its verbatim source row so the paraphrase can be checked.
  SITE stays the record fact and does not vary across cells.
- The scorer computes the three measures per cell, the three contrasts on each, a null
  reading at a declared threshold of one row in seven, and per-row movement across cells.
  Anchors are a manipulation check: row 1 must stay internal and row 13 external, or the
  cell is reported as broken rather than averaged in.
- A rule violation (physical_damage at an undamaged record site) is counted and kept, as in
  rounds 2 and 3.
- Two confounds are declared, not removed: three of the seven sentences describe records a
  resident would not see, so the low-source frame is strained there and hedging on those
  rows may be plausibility rather than credibility; and the rewrite is mine.
- Constructed fixture carries a deference pattern so the reading path is exercised; it is
  banner-marked and asserted constructed in the selftest.

## v0.2 — round 3 loaded row by row; authority factorial emitted

- **Round 3 is now computed, not reported.** `fixtures/maria_locus_round3_results.jsonl`
  carries one line per (variant, grader, row). `locus_tally.round3_block` recomputes every
  figure in the order's section 2 and the selftest asserts each one: pairwise exact 14/11/13
  full and 15/13/15 collapsed, unanimous 11/17 and 13/17, any-regime 15/16/15, pure damage
  2/1/2 with row 13 the only unanimous one, custody.state 24 of 28 on the nine all-custody
  rows, the gpt row-9 violation, stability 14/14 and 13/14, the four-family 13/17 on the same
  row set, the name effect (deepseek 17/17, gpt 16/17 with row 9 the flip). The stated-cause
  template is filled for the P0 graders and V10c computes for M1 (external share 0.667 in the
  stated causes against 0.06-0.18 in the findings; A1 unanimous mixed).
- **One figure differs from the order as written.** Open rows come out as 2, 9, 11, C3 over
  four families; the order lists 2, 9, C3. Row 11 is open because kimi P0 coded
  physical_damage where the three other families coded custody. Reported as computed.
- **Kimi P1 is loaded, marked, and excluded.** Byte-identical to gemini P1 on all 17 rows.
  Duplication and convergence cannot be told apart from the lines, so the lines carry
  `verified: false` and no figure counts them. T-c is the operator's re-copy.
- **Gemini refused P0 and answered P1.** The names were the trigger. Whether the company or
  the agency name triggers it is T-d (names kept, the three carrier rows removed).
- **Pending small tests are templates** in `fixtures/pending/small_tests.jsonl`: T-a renames
  the label to event_damage with the definition unchanged and reruns row 9 cold on gpt and
  gemini; T-b reruns row 9 under P0 three times on gpt for the place prior. Both bear on the
  one row that is a rule violation and a name flip at once.
- **V2d prompts are emitted from the verbatim rows.** The paraphrase is gone: each row is
  the OIG sentence with the substitutions declared in `v2d.SUBS` (agent, carrier, island,
  mainland port), the agent string filled per cell, sentence starts recapitalized. The
  selftest diffs each file against its two neighbours (exactly the agent string; exactly the
  source prefix line) and walks each row against `maria_verbatim.jsonl` so only declared
  substitutions separate them. Two longer keys ("the FEMA inventory", "the Jacksonville")
  exist so the files do not read "the the"; every other artifact of direct substitution
  ("inadequate the federal emergency agency oversight") is kept as is. Graders for the run
  are gpt, deepseek, gemini; kimi joins once T-c verifies its copy. Market share is a fourth
  measure. Predictions named: deference, sympathy, credibility, NULL.
- **The caveat stands.** Every citable statement above is an audit-instrument statement.
  The enum has not been run on a non-audit source.
