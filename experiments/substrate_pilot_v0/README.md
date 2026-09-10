# Substrate coordination pilot v0.1

Build of `SPEC.md` (failure-derived tests + legacy onboarding). CC0, stdlib
only, paper-operable. One failure source: DHS OIG-20-76.

```
                     C2 NEED (declared unit, clock, edges)
                            │  pulls
 origin gate ──FT-01──▶ C1 STATE ──release──▶ IN_TRANSIT ──receiver mark──▶ RECEIVED
   no record = HOLD     two channels            │                 FT-05: no mark = stays IN_TRANSIT
                        FT-03                   │ dwell > limit ──▶ C4 escalation (FT-06)
                        UNKNOWN is a status     │
                        never a location FT-02  ▼
                                          C3 COMMIT ──KEPT──▶ BND settle (FT-11: refused without receipt)
                                                              MONEY_TERM scope required
 FLT: findings close only as RULE_CHANGE or WAIVED(owner,date); open ones shown at activation (FT-09)
 REC: recursion depth 1 in this version
```

| file | what |
|---|---|
| `ledger.py` | the channels; every SPEC §2 shall is a gate (`Refused`) or a `FLAG` record |
| `exercise.py` | SPEC §4 replay, injects I-1..I-13 in order; OIG baselines vs operator `TARGETS`; shall and target columns |
| `selftest.py` | FT-01..FT-18 and V1..V11 as unittest; prints its count |
| `spec_rows.json` | V11: climate of every spec row's baseline |
| `fixtures/*_locus.jsonl`, `locus_tally.py` | V2/V10 LOCUS-coded findings with three graders and a round-2 re-grade (Maria), Katrina and GAO 2018 partial; tallies and agreement computed from the rows |
| `fixtures/maria_verbatim.jsonl`, `fixtures/katrina_passages.jsonl` | verbatim source sentences with pages and record sites (public domain); V2c and V10b grader templates draw from them |
| `v2d_authority/` | V2d authority × source 2×2 on the enum: prompts, plan, scorer, constructed fixture; unrun |
| `CLAIM_TABLE.md`, `BUILD_NOTE_v0.1.md` | claim statuses V1–V10 and nulls N-1..N-4; Q-1 answer and resolutions |
| `forms/` | T-card, gate log, delivery receipt: the physical channel on paper |
| `onboarding/field_map.json` | SPEC §3 field map (Phase 1 ADAPTER) |
| `onboarding/shadow.py` | Phase 0 SHADOW divergence classifier over legacy CSV exports |
| `../../tests/test_substrate_pilot_v0.py` | thin wrapper that collects `selftest.py` under pytest |
| `runs/exercise_v0_1.md` | last replay: verdict per row with row/target/run climate, shall-held separate from target, failures by LOCUS/SITE |

```bash
python experiments/substrate_pilot_v0/exercise.py          # replay, writes runs/
python experiments/substrate_pilot_v0/selftest.py           # FT battery (stdlib), prints its count
python experiments/substrate_pilot_v0/locus_tally.py        # LOCUS tallies, Maria | Katrina | GAO 2018
python experiments/substrate_pilot_v0/onboarding/shadow.py inv.csv rec.csv <ledger_root>
```

## What the replay reports

Two rows fail by construction of the injects and are reported, not waived:
FT-13 (4 of 40 pantries did not co-author the plan) and FT-06 against the
operator dwell target (two units stranded at a staging area; the escalation
fired, so the shall held, the target did not). FT-02 applies to the pilot:
a failed row stays a failed row.

## Not built in v0

- REC beyond depth 1; HF/mesh transport (the ledger is transport-agnostic:
  a line is a line whether it arrives by radio or by hand).
- Phase 3 Choice-type token; Phase 4 MONEY_TERM boundary beyond the single
  settlement gate. `settle()` is the hook.
- Katrina and GAO 2018 intake (next sources per SPEC).

## Placement

Built here because this session can push only to this repository. It has
no dependency on SOMS and belongs beside `Simulators/cooperative-substrate`;
moving the directory is the whole migration.
