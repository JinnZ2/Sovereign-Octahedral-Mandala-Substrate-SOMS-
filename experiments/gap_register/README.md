# gap_register

A register of MARKS on unmeasured quantities. CC0, stdlib, one file + `REGISTER.jsonl`.

```
measurand   presence/absence of a mark on an unmeasured quantity      NOT: truth of any claim about it
unit        one entry = one (quantity, excluding-method) pair
status      per (entry, field): status_by_field[field] = {status, evidence, assessed}; fields from FIELDS.txt
            OPEN | CLOSED_MEASURED | CLOSED_INSTRUMENT_EXISTS | OUT_OF_ENVELOPE | UNKNOWN   (UNKNOWN is a peer)
            entry rollup DERIVED, never stored: any OPEN -> OPEN | all CLOSED_* -> CLOSED | else UNKNOWN
envelope    IN: methods, standards, code tables, certifications, regulatory channels, benchmarks, corpora
            OUT: intent, motive, fault, what the quantity would show
entry       states the absence · the excluding method · the closing test
            never: wrongdoing · a predicted result · a name in an accusatory position (names live in provenance[])
```

```bash
python experiments/gap_register/gap_register.py validate                 # V1..V6, exit 1 on any failure
python experiments/gap_register/gap_register.py validate demo/REGISTER_failing.jsonl   # exit 1: V4 and V2 trip
python experiments/gap_register/gap_register.py search analgesia coding
python experiments/gap_register/gap_register.py check GR-0004            # closure condition + T4 instruction (build the venue)
python experiments/gap_register/gap_register.py check GR-0002            # same subject, T2 instruction (declare the partition)
python experiments/gap_register/gap_register.py emit --human --machine   # build products: human/REGISTER.md, machine/register.jsonld
python experiments/gap_register/gap_register.py correlate --field human_procedure_coding
python experiments/gap_register/gap_register.py strip GR-0004            # name-strip probe input
python experiments/gap_register/gap_register.py kill-sample              # bare entries, no framing
python experiments/gap_register/gap_register.py selftest
```

## Layout (Addendum A3.1)

```
REGISTER.jsonl            the store: stdlib, phone-buildable, any text editor      <- the only thing edited
FIELDS.txt                controlled field list; append, never rename
gap_register.py           the tool
human/REGISTER.md         emit --human   build product, header carries the store sha256
machine/register.jsonld   emit --machine build product, storeHash + @context from context.jsonld
machine/context.jsonld    hand-authored, version-pinned; schema.org where a term exists, gr: where not,
                          one-line definition per gr: term
demo/REGISTER_failing.jsonl   trips V4, V2, V7; validate exits 1
```

Emissions are never hand-edited. `validate` fails (V8) when either emission's hash differs
from the store; `add` re-emits so the hash stays current.

## Seeds (7), status by field

```
                                                             field                       status
GR-0001  T1  coercion rate in mediation                      mediation_practice          UNKNOWN
GR-0002  T2  human-medical vs veterinary analgesia partition  veterinary_medicine         UNKNOWN
                                                             human_medical_coding        UNKNOWN
GR-0003  T3  frame-holding under hour-based certification     mediation_certification     UNKNOWN
GR-0004  T4  spay/neuter floor vs cervical procedure coding   veterinary_medicine         CLOSED_MEASURED (operator-supplied evidence)
                                                             human_procedure_coding      OPEN
                                                             insurance_adjudication      UNKNOWN
GR-0005  T1  interlocutor-model resolution + update rate      language_model_evaluation   UNKNOWN
GR-0006  T1  located-friction log / release-as-faith-token    negotiation_research        UNKNOWN
GR-0007  T2  instrument stability through a hosted model      language_model_evaluation   OPEN
                                                             substrate_pilot             CLOSED_INSTRUMENT_EXISTS
```

Most fields are UNKNOWN, not OPEN: the case descriptions came from the operator session as
one line each, no document pointer was supplied, and nothing in this build searched the
literature to confirm that the closing observation is absent. GR-0004's veterinary field
carries the evidence string from Addendum A2.1 as the operator supplied it; it was not
fetched here. GR-0007 is the per-field split in miniature: OPEN in the evaluation field,
closed by instrument in the one pilot that built the declaration.

## T2 vs T4 (Addendum A1)

GR-0002 and GR-0004 share a subject and differ in closure. GR-0002 closes by a DECLARATION
that the two floors were set apart on purpose; what remains is a marked, unmeasured quantity.
GR-0004 closes by BUILDING the venue where two already-measured floors appear on one page;
nothing remains. `check` prints the instruction per type, so the two return different kinds
of target.

## Correlation read (Addendum A2.2)

`correlate` prints, per field pair, the entries carrying both fields and how many are OPEN in
both, OPEN in one, closed in both; then the adjacency list: entry pairs sharing two or more
index terms whose statuses differ on a field both carry. Counts only. With seven seeds every
pair count is 0 or 1 and the adjacency list is empty; the read has no signal until the
register has neighbours.

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
V6' every status_by_field entry: status in the enum, field in FIELDS.txt, assessed date present
V7  no stored entry-level status
V8  both emissions carry the current store sha256
V9  every gr: term in register.jsonld is defined in context.jsonld (it caught three of the
    builder's own terms on the first run)
```

V4 is a heuristic: it catches names by capitalisation, so a lower-cased name passes and a
capitalised common noun mid-sentence fails. It fails loud in the second case, which is the
cheaper error. V5 as written ("none of which is a coinage absent from index_terms of any other entry") was
read as: no coined term unique to the entry. Read strictly (no unique term at all) it fails
every seed, since each names something no other entry names (spay, cervical, friction). The
coinage test is a surface heuristic; a coined term made of plain lower-case words passes it.

## Demo that fails

`demo/REGISTER_failing.jsonl`: one entry trips V4 (a council named outside provenance plus
"hides" and "failed to"), one trips V2 (closure condition is only "should care more"), one
trips V7 (a stored `status`). A fourth passing entry keeps V5 satisfiable. `validate` on it
exits 1; the selftest asserts which rule each trips.

## Kill rule (unrun)

A zero-context reader given `kill-sample` output and no framing must restate the absent
quantity and the closing condition for at least 16 of 20 entries. The register holds 7, so
the sample is short; the probe is a template until 20 entries exist. Failure fixes the format.

## Citation confound

Recorded as the `confound` field where it applies (GR-0004 carries it explicitly). The
name-strip probe exists elsewhere in this repo as the V2c name effect
(`substrate_pilot_v0`, P0 vs P1); `strip` emits the entry without provenance as its input.

## Resolved by Addendum A (operator sign-off 2026-09-11)

```
O1  four types kept; T2 and T4 differ in closure kind (declaration vs venue); check emits per type
O2  status per (entry, field); rollup derived; correlate is the overlooked-gap detector
O3  dual emission from one store; JSON-LD with a hand-authored, version-pinned context
```

Not in scope here: migrating other repos to the layout; the name-strip probe as a measurement arm.

## Placement

Built here for push access; no SOMS dependency. Moving the directory is the whole migration.
