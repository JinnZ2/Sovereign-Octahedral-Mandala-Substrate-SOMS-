# OPEN ITEMS ROLLUP — status (2026-09-11)

Executor return against the rollup order. Status vocabulary: BUILT (selftest asserts it) |
COMPUTED | TEMPLATE (prompt/fixture present, results slots empty) | BLOCKED (reason) |
SUPPORTED / REFUTED / UNRUN (group D) | STUB (group E). Nothing marked PASS that is unrun.

## A. built now

```
A1  anchor-position fixes W1-W11        BLOCKED   the source document (WORKORDER_anchor_position_fixes.md)
                                                  is in no reachable repo: not in SOMS, not in GlyphAI, not in
                                                  Simulators@04d16d0 (anchor-position/WORK_ORDER.md has no W rows).
                                                  The target code (anchor-position/score.py, normalize.py) lives in
                                                  Simulators, which this session cannot push to. Coding W1-W11 from
                                                  the rollup's one-line summary would be coding from the summary.
                                                  Needs: the W-row document, and a push path or a patch target.
A2  round 3 + kimi P1 resolved          BUILT     fixtures/maria_locus_round3_results.jsonl (kimi P1 real run,
                                                  verified true); locus_tally.round3_block; selftest V2c_round3_results
                                                    name effect  gpt 16/17 (dmg 2->1, row 9)  deepseek 17/17
                                                                 kimi 14/17 (dmg 2->1, row 11; + rows 4, C1 cs->cr)
                                                    dropped damage codes: all to custody; added: none
                                                    P1 four-family unanimous collapsed 14/17; open rows 2, 9, C3
                                                    mixed-family (P0 x3 + gemini P1) stays 13/17 with row 11 open
                                                  status of the name-effect claim: CANDIDATE (signed); T-a/T-b decide
A3  V1-V11 remainder                    BUILT     already in v0.1: CLAIM_TABLE rows V1..V11, selftest classes
                                                  V1_failure_locus_schema, V3_regime_class, V4_context_severity,
                                                  FT16/17/18, V8_retention, V11_climate, Exercise_replay (I-9..I-13)
A4  grader_identity + canaries          BUILT     grading_prompt.py: CANARIES rows 13 (physical_damage) and 5
                                                  (regime.learning), unanimous on every verified grading loaded
                                                  (selftest checks this against the results file); check_run ->
                                                  PASS | FAIL | SUSPECT (a canary failed after being passed by the
                                                  same CLAIMED grader); grader_identity {claimed, verified} on the
                                                  results header, the pending and stated-cause templates, and the
                                                  v2d run record. No run file exists: results slots empty.
A5  pending-test prompt files           TEMPLATE  prompts/: P0_reconstructed, P1_reconstructed, T-a_row9_event_damage,
                                                  T-b_row9_P0, T-d_gemini_P2_no_carrier_rows, V10c_M1_stated_causes
                                                  (+ v2d_authority/prompts/ 4 files). Diff-asserted: T-a vs T-b =
                                                  exactly the label; T-b subset of P0; T-d = P0 minus rows 2, C1, C3.
                                                  P0/P1 are RECONSTRUCTED: the operator's files were not supplied.
                                                  FIX FOUND: the physical_damage definition carried a provenance
                                                  note naming row 9; stripped from every grader-facing prompt
                                                  (ledger.prompt_definitions), v2d prompts re-emitted.
A6  frame_audit v2                      BLOCKED   no frame_audit/ package exists in any reachable repo; the only
                                                  frame_audit.py is Simulators/declared-frame/ (a null-test of
                                                  check_frame.py, not the v1 this v2 would extend). Needs the v1
                                                  source and a push path.
A7  money_term.py                       BUILT     gate -> NATIVE | DECLARED | PROXY_UNROOTED | CIRCULAR; R-09 rule
                                                  set from SPEC Phase 3; three cases: Obermeyer cost-as-need ->
                                                  PROXY_UNROOTED, Solow cost-share -> CIRCULAR, Choice System token
                                                  -> DECLARED. Classifications are the executor's reading of the
                                                  cited sources (locators; not fetched).
A8  field_fix.py                        BUILT     check -> SIGN_INVERSION | DOF_DELETION | STATE_NOT_UPDATED | OK;
                                                  function tags on contacts/mounts/fasteners; wax -> sign inversion,
                                                  zip tie -> DOF deletion, penny shim -> state not updated (penny in
                                                  a fuse holder -> sign inversion). Cases are constructions, not
                                                  field records.
```

## B. needs operator runs

```
B1  T-a, T-b, T-d                        TEMPLATE  prompts/ (above); paste results as lines with grader_identity
B2  authority factorial                  TEMPLATE  v2d_authority/prompts/ 4 files; plan --seed 7; 12 runs (+kimi: 16)
B3  frame_audit blind swap               BLOCKED   with A6
B4  T4 rotation task                     TEMPLATE  experiments/t4_frame_rotation (4 arms, scorer, constructed fixture)
B5  non-audit Maria source               TEMPLATE  fixtures/maria_nonaudit_template.jsonl: 3 locator rows, locus null;
                                                   the caveat test; canaries ride along
```

## C. needs source fetch

```
C1-C5  locator stubs stay locus: null    HELD      fixtures/sources.json K1 (logistics chapter unread), K3 pp.66-77 /
                                                   128-134 unread, OIG-10-101 [locate], Blue Ribbon 2012 + NSF OIG
                                                   (not registered), NIMS 2004/2008/2017 (not registered); selftest
                                                   test_v10b_instrument_not_evaluable_until_extraction holds the nulls
```

## D. SOMS harness returns (experiments/e07_returns.py -> docs/experiment_07_returns.{md,json})

```
D1  85-pair split                        SUPPORTED   G1-sym only 80 | G6-sym only 5 | both 0 | neither 463 (of 548)
D2  same-sigma H = Iso(G2) ∩ Iso(G4)     REFUTED     |H| = 8; 328 of 548 lie in an (H x S_n)-orbit; 220 do not:
                                                     the G2 and G4 explanations of a joint-genuine pair need not
                                                     share an element of the intersection
D3  230 unseparated after the quotient   SUPPORTED   230 = readout-merged AND same joint-M; universe = the 668
                                                     joint-colliding pairs (438 of them readout-separated); the 548
                                                     joint-genuine pairs: 182 readout-merged; 522240 readout-merged
                                                     pairs over all C(4096,2) = 8,386,560
D4  G5 status                            ABSENT      no G5 metric defined; numbering skips G4 -> G6; nothing was
                                                     computed under the name (label gap, not a missing result)
D5  sorted-pair-list hash                COMPUTED    sha256 a043fd9a...b01150 over the sorted [min,max] list;
                                                     docs/experiment_07_joint_genuine_pairs.json; E06 set unreachable
                                                     -> comparison UNRUN
D6  E09 energy terms / cutoff / T*       COMPUTED    every term = J_ij x dimensionless (angular sin^2, tensor |dλ|^2,
                                                     cayley (φ d_c/diam)^2): all power d^-6, no other power;
                                                     no cutoff in code (FRET_CUTOFF 4.854 Å is docs-only and below
                                                     every mandala distance in the mandala's declared nm: units
                                                     UNCONFIRMED); u=20 depth=5: d_nn 20, J_scale 1.5625e-8,
                                                     T*(5.0) = 3.2e8, T*(0.1) = 6.4e6; normalized d/d_nn -> T* = T
D7  T1 / T2                              RUN         T1: G1/G6 genuine collisions are tie degeneracy (vanish under
                                                     pair-noise, not level-noise; additive coincidences 0 under the
                                                     vector readout; 140-pair equality floor). T2: 0/64 ring-type
                                                     set-level RS pairs in Z8 (forced by lemma); 0 of the 548 are
                                                     ring-homometric non-isometric
```

## E. proposed, not specced

```
E1-E5  experiments/substrate_pilot_v0/proposed/E1-E5_spec_stubs.md   STUB
```

## Done-when check

```
A  selftests pass (54 pilot tests; e07_returns run); CLAIM_TABLE rows A2/A4/A5/A7/A8; A1/A6 BLOCKED, not PASS
B  prompt files present + diff-asserted; no results file exists (grading_runs.jsonl absent, asserted)
C  locator stubs locus: null (asserted)
D  each item carries its status and evidence in docs/experiment_07_returns.md
E  stubs only
```

## Found while running (not in the order)

```
lattice_handshake tests    tests/test_lattice_handshake.py test_decode_recovers_signal and
                           test_handshake_error_is_small failed once each across three full pytest
                           runs today. Both draw an unseeded randn secret against an unseeded random
                           basis. Measured over 300 seeds: handshake_error >= 1.0 on 5/300
                           (seeds 33, 38, 85, 103, 233; errors 46.8, 1.6, 9.3, 1.8, 20.8). The decode
                           bound in the test is not a property of the module for every basis; seeding
                           the test would hide that. Left as found; a fix is a decision on what the
                           test should assert (a rate over seeds, or a conditioning bound on the basis).
```
