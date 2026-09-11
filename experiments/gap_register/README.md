# gap_register

A register of MARKS on unmeasured quantities. CC0, stdlib, one file + `REGISTER.jsonl`.

```
measurand   presence/absence of a mark on an unmeasured quantity      NOT: truth of any claim about it
unit        one entry = one (quantity, excluding-method) pair
status      OPEN | CLOSED_MEASURED | CLOSED_INSTRUMENT_EXISTS | OUT_OF_ENVELOPE | UNKNOWN   (UNKNOWN is a peer)
envelope    IN: methods, standards, code tables, certifications, regulatory channels, benchmarks, corpora
            OUT: intent, motive, fault, what the quantity would show
entry       states the absence · the excluding method · the closing test
            never: wrongdoing · a predicted result · a name in an accusatory position (names live in provenance[])
```

```bash
python experiments/gap_register/gap_register.py validate                 # V1..V6, exit 1 on any failure
python experiments/gap_register/gap_register.py validate demo/REGISTER_failing.jsonl   # exit 1: V4 and V2 trip
python experiments/gap_register/gap_register.py search analgesia coding
python experiments/gap_register/gap_register.py check GR-0007
python experiments/gap_register/gap_register.py export --md
python experiments/gap_register/gap_register.py strip GR-0004            # name-strip probe input
python experiments/gap_register/gap_register.py kill-sample              # bare entries, no framing
python experiments/gap_register/gap_register.py selftest
```

## Seeds (7)

```
GR-0001  T1  coercion rate in mediation                      UNKNOWN
GR-0002  T2  human-medical vs veterinary analgesia partition  UNKNOWN
GR-0003  T3  frame-holding under hour-based certification     UNKNOWN
GR-0004  T4  spay/neuter floor vs cervical procedure coding   UNKNOWN
GR-0005  T1  interlocutor-model resolution + update rate      UNKNOWN
GR-0006  T1  located-friction log / release-as-faith-token    UNKNOWN
GR-0007  T2  instrument stability through a hosted model      OPEN
```

Six seeds are UNKNOWN, not OPEN: their case descriptions came from the operator session as
one line each, no document pointer was supplied, and nothing in this build searched the
literature to confirm that the closing observation is absent. UNKNOWN is the return for an
entry that cannot be evaluated; OPEN would have been the default the order forbids. GR-0007
is OPEN on this session's own records (the paste duplication, the canary build).

## Validator rules as implemented

```
V1  required fields present, non-empty; null only in venue_check, confound; opened YYYY-MM-DD
V2  closure_condition contains an observable noun from OBSERVABLES (record, table, count, rate,
    published, standard, dataset, ...); a modal with no observable fails
V3  refutation non-empty and not equal to closure_condition
V4  proper names outside provenance[]: a capitalised word that is not sentence-initial and not an
    acronym, or two capitalised words in a row anywhere; plus a fault lexicon (blame, fault, failed
    to, conceal, deliberately, ...) in any text field
V5  index_terms >= 3; a term that no other entry indexes AND looks coined (hyphen, digit, capital,
    camelCase, or a 15+ letter token) fails; a plain noun only one entry uses passes; vacuous on a
    1-entry register
V6  status in the enum
```

V4 is a heuristic: it catches names by capitalisation, so a lower-cased name passes and a
capitalised common noun mid-sentence fails. It fails loud in the second case, which is the
cheaper error. V5 as written ("none of which is a coinage absent from index_terms of any other entry") was
read as: no coined term unique to the entry. Read strictly (no unique term at all) it fails
every seed, since each names something no other entry names (spay, cervical, friction). The
coinage test is a surface heuristic; a coined term made of plain lower-case words passes it.

## Demo that fails

`demo/REGISTER_failing.jsonl`: one entry trips V4 (a council named outside provenance plus
"hides" and "failed to"), one trips V2 (closure condition is only "should care more"). A third
passing entry keeps V5 satisfiable for the other two. `validate` on it exits 1; the selftest
asserts which rule each trips.

## Kill rule (unrun)

A zero-context reader given `kill-sample` output and no framing must restate the absent
quantity and the closing condition for at least 16 of 20 entries. The register holds 7, so
the sample is short; the probe is a template until 20 entries exist. Failure fixes the format.

## Citation confound

Recorded as the `confound` field where it applies (GR-0004 carries it explicitly). The
name-strip probe exists elsewhere in this repo as the V2c name effect
(`substrate_pilot_v0`, P0 vs P1); `strip` emits the entry without provenance as its input.

## Open, operator sign-off required

```
O1  four types or three (T4 a special case of T2?)      kept as four; the seeds use all four
O2  status per entry or per (entry, reader)             per entry as built
O3  JSON-LD / schema.org dialect or bare JSONL          bare; a dialect is an export, not a store
```

## Placement

Built here for push access; no SOMS dependency. Moving the directory is the whole migration.
