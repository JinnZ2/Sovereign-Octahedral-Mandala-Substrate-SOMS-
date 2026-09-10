# T3 — D_state vs D_community (decision-string anchor, new case family)

Case family for `Simulators/anchor-measurand-crossing`: the same claim and
method cited for two decisions.

```
claim + method (ACS household need counts by tribal area)
        │
        ├── D_state      IHBG need-formula allocation           ──▶ measurands: income-band household counts,
        │                                                            overcrowding, cost burden, shortage, share
        └── D_community  a First Nation's OCAP/CARE decision     ──▶ measurands: consent record, custody holder,
                         on collection, custody, access, benefit     access rule, ownership, benefit, purpose,
                                                                     member definition
PREDICT   near-disjoint; the decision string becomes the independent variable
```

**Status: instrument only, unrun.** No model endpoint is available here and
this session is not blind to the prediction. The decision strings are
paraphrases (`verbatim: false`): the regulation (24 CFR 1000.324) and the
OCAP / CARE texts could not be fetched (egress blocked). Replace them with
verbatim text before a run; the case validator in `amc.py` should refuse a
D-arm record whose logged decision string differs from the case's.

```bash
python experiments/t3_decision_anchor/predict.py     # scores the prediction on lexicon.json
```

To run: copy `cases.jsonl` rows and the two `lexicon.json` entries into
`anchor-measurand-crossing/`, then `amc.py prompt dsa-01-state D` and
`amc.py prompt dsa-01-community D` in separate fresh sessions, and score.
The shared native quantity (household need counts) is the one measurand
both decisions can cite; the prediction is that neither decision is
denominated in it alone.
