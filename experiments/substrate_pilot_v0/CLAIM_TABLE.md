# CLAIM TABLE — substrate pilot v0.1 (+V11)

Status vocabulary: BUILT (selftest asserts it) | PARTIAL (built, coverage declared) |
UNRUN (instrument exists, no run) | BLOCKED (reason). Nulls N-1..N-4 have their own rows.

| id | claim | status | evidence | note |
|---|---|---|---|---|
| Q-1 | refusal path identified | ANSWERED | BUILD_NOTE_v0.1.md | two paths; physical-ledger side effect fixed and injects rerun |
| V1 | every failure record carries LOCUS + SITE; physical_damage rejected off damaged sites; enum defined (learning added, site unknown added) | BUILT | selftest `V1_failure_locus_schema` incl. `test_enum_is_defined` | 9 failure record types route through one validator; `LOCUS_DEFINITIONS` in ledger.py; the two-grader result (2/12 exact, 6/12 disjoint) is why the definitions exist; ledger-emitted FLT failures recoded custody -> learning; Maria row 5 retained as the table's custody with an editor note for the second grader |
| V2 | OIG-20-76 coded fixture, 13 rows, header, tally per LOCUS, empty second-grader slots | BUILT | `fixtures/maria_locus.jsonl`, `locus_tally.py`, selftest `V2_maria_fixture` | tally 10/2/1 is single-grader; `tally_citable: false` |
| V3 | class + axis per load; "critical" alone refused; custody axis may not drop | BUILT | selftest `V3_regime_class`; I-13 | release gate also holds a classless load |
| V4 | event declaration reclasses from precomputed table with zero manual steps; water -> R2 min | BUILT | selftest `V4_context_severity`; I-11 | `manual_steps` recorded on the EVENT record (N-3 watch) |
| V5 / FT-16 | signed handover at every boundary; presence without custody = unsigned transfer | BUILT | selftest `FT16_named_custodian`; I-12 | grace 1 h before a drop reads as a transfer |
| V6 / FT-17 | declared silence interval on R2/R3; escalation within one interval; latency metric | BUILT | selftest `FT17_heartbeat`; I-9 | detection depends on the sweep running each interval |
| V7 / FT-18 | competing claim routes to resolver; cellular-only resolver refused | BUILT | selftest `FT18_contested_custody`; I-10 | custody never moves on a claim, only on resolution |
| V8 | assignments persist post-event; missing + no WAIVED -> flagged at activation | BUILT | selftest `V8_retention` | protein_g left unassigned in the replay on purpose |
| V9 | I-9..I-13 run; results with shall and target columns | BUILT | `runs/exercise_v0_1.md` | FT-01 and FT-13 fail target by inject construction |
| V10 | Katrina intake, LOCUS-coded, separate fixture; GAO 2018 third fixture | PARTIAL | `fixtures/katrina_locus.jsonl` (10 rows), `fixtures/gao2018_locus.jsonl` (4 rows) | titles and pages NOT verified (egress blocked); rows recalled, not extracted; confidence per row; single-grader; not citable |
| V11 | CLIMATE on every spec row, load and trigger table; missing -> stable + flagged; event flips climate via V4 table; targets carry their climate; claim valid only inside its climate; field-fix check at every contact under variable | BUILT | selftest `V11_climate`; `spec_rows.json`; replay row V11 | FT-05's stable drill target now reads NOT VALID (climate) in the variable run instead of FAIL; unattended drops are the field-fix-missing contacts |
| N-1 | second grader moves >= 3 Maria rows to physical_damage | OPEN | second-grader slots empty | cannot be evaluated until a second grader codes |
| N-2 | Katrina tally majority physical_damage at damaged sites | NOT TRIGGERED (provisional) | katrina fixture: 7 regime / 2 mixed / 1 physical_damage of 10 | provisional: partial coverage, unverified sources; re-evaluate after extraction from the texts |
| N-3 | I-11 reclass requires a manual step | NOT TRIGGERED | EVENT record `manual_steps: 0` | reclass is one call on a table declared pre-event |
| N-4 | heartbeat escalation fires but no resolver acts within the interval | NOT TRIGGERED in this run | FT-18 row: resolver acted at 4 h | the row splits shall/target so a silent resolver shows as shall held, target failed |

Out of scope (unchanged): REC beyond depth 1, HF/mesh transport, Phase 3 Choice token, Phase 4 beyond the single settlement gate.
