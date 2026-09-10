# V2d — authority × source 2×2 on the locus enum

Does the coding of the same sentence move with who the agent is and who is speaking?
Built as an instrument; unrun (no model endpoint here; this session is not blind).

```
                      SOURCE high: "A federal inspector general audit found:"    SOURCE low: "A local resident reported:"
 AGENT high (agency)  cell HH                                                    cell HL
 AGENT low  (network) cell LH                                                    cell LL
 rows: 1 (anchor internal) | 2, 9, 11, C1, C3 (movers) | 13 (anchor external)      place = "the island"; SITE constant
 12 runs = 4 cells x 3 graders (gpt, deepseek, kimi), fresh session each
 measures per cell: external share (damage|urgency) | internal share (custody.*|learning) | hedge rate
 contrasts: agent main effect | source main effect | interaction, on each measure; null threshold 1/7
 anchors: row 1 internal and row 13 external in every cell, or the cell is reported as broken
```

```bash
python experiments/substrate_pilot_v0/v2d_authority/v2d.py selftest
python experiments/substrate_pilot_v0/v2d_authority/v2d.py plan --seed 7
python experiments/substrate_pilot_v0/v2d_authority/v2d.py prompt high low
python experiments/substrate_pilot_v0/v2d_authority/v2d.py score experiments/substrate_pilot_v0/v2d_authority/runs/constructed.jsonl
```

Run protocol: one fresh session per plan row, paste the prompt verbatim, record
`{run_id, cell, grader, model, version, date, order_index, raw_response, constructed:false}`.
Score by the codes only.

Two confounds declared in `stimuli.json`, not removed: (1) `source_plausibility`: three of the
seven sentences describe records a resident would not see (headquarters records, contract terms,
a contracting file), so the low-source frame is strained on those rows; hedging there may be
plausibility, not credibility. (2) The rewrite is the executor's paraphrase of the verbatim rows;
each row names its source row for checking.
