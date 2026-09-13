# gap register

BUILD PRODUCT of `gap_register.py emit --human`; never hand-edit. store sha256: 886d041b75395654c7aa71ec4f2af61796ce836e609bb7a84ed07fce529d3495

One block per entry. Status is per field; the entry line shows the derived rollup (any OPEN -> OPEN; all closed -> CLOSED; else UNKNOWN).

## GR-0001  T1  UNKNOWN

- quantity: coercion rate in negotiation and mediation: the share of settled cases where one party's agreement was obtained under pressure the process did not record
- index terms: mediation, negotiation, coercion, settlement, rate, certification
- excluding method: mediation outcome scoring: the method records closure (settled / not settled) and party satisfaction at close; the construction has no field for pressure applied during the session
- measured instead: closure rate, time to settlement, satisfaction at close
- venue check: a mediation-outcome table with a coercion column beside the closure column; none located in this session
- closure condition: a published study or outcome table that reports a coercion rate for mediated settlements, measured by an instrument other than closure or satisfaction
- closing instruction (T1): MEASURE: the quantity is absent by construction; close by an instrument that returns it
- refutation: a standard mediation evaluation protocol whose record already carries a coercion or pressure field
- status by field:
    - mediation_practice: UNKNOWN (assessed 2026-09-11; evidence: none)
- confound: satisfaction at close is sometimes read as absence of coercion; the two are not the same measurand
- provenance: operator session 2026-09-11 (case description; no document pointer supplied)
- opened: 2026-09-11

## GR-0002  T2  UNKNOWN

- quantity: the partition between human medical coding of analgesia and the veterinary analgesia standard: whether any declaration exists that the two floors were set separately
- index terms: analgesia, veterinary, medical, coding, standard, partition
- excluding method: each standard is issued by its own body and indexed in its own channel; neither carries a field stating that a comparable standard exists in the other domain
- measured instead: within-domain compliance with each standard
- venue check: a table or committee where both analgesia floors appear on one page; none located in this session
- closure condition: a published document from either standards body that declares the other domain's floor and states whether the separation was made on purpose
- closing instruction (T2): DECLARE the partition: close by a declaration that the separation was made, as a choice; the residual is a marked, unmeasured quantity
- refutation: a cross-domain standard or citation already exists that names both floors
- status by field:
    - veterinary_medicine: UNKNOWN (assessed 2026-09-11; evidence: none)
    - human_medical_coding: UNKNOWN (assessed 2026-09-11; evidence: none)
- confound: species differences are a legitimate reason for separate floors; the gap is the missing declaration, not the difference
- provenance: operator session 2026-09-11 (case description; no document pointer supplied)
- opened: 2026-09-11

## GR-0003  T3  UNKNOWN

- quantity: frame-holding in mediation: the competency of keeping both parties' frames present through the session, as distinct from moving the case to closure
- index terms: mediation, certification, frame, competency, training, hours
- excluding method: hour-based mediation certification (40-hour training standard): competency is redefined as hours attended plus a closure-scored role play, and keeps the name of the competency it replaced
- measured instead: training hours completed, role-play closure score
- venue check: a certification syllabus listing frame-holding as an assessed item; none located in this session
- closure condition: a certification syllabus or assessment record that scores frame-holding by an instrument other than hours or closure
- closing instruction (T3): ASSESS the named competency by an instrument other than the substituted count; close when the original name is measured again
- refutation: the certification's own assessment record already carries a frame-holding score
- status by field:
    - mediation_certification: UNKNOWN (assessed 2026-09-11; evidence: none)
- confound: the substituted measurand keeps the original name, so a search on the name returns the certification as if the competency were measured
- provenance: operator session 2026-09-11 (case description; no document pointer supplied)
- opened: 2026-09-11

## GR-0004  T4  OPEN

- quantity: the comparison between the mandatory analgesia floor for spay/neuter and the analgesia coding for cervical procedures: both measured, never placed on one page
- index terms: analgesia, veterinary, medical, coding, spay, cervical, comparison
- excluding method: procedure coding tables are per domain; there is no journal, committee, or table whose scope includes both a veterinary procedure floor and a human procedure code
- measured instead: each domain's own compliance and coding rate
- venue check: a comparative table joining the two; none located in this session
- closure condition: a published table or report that lists the spay/neuter analgesia floor and the cervical procedure analgesia coding side by side with a shared measure
- closing instruction (T4): BUILD the venue: both sides are already measured; close by the table, paper, or committee where they appear on one page; no residual
- refutation: such a comparative table already exists in either domain's literature
- status by field:
    - veterinary_medicine: CLOSED_MEASURED (assessed 2026-09-11; evidence: AAHA 2020; ASV/JAVMA 2016 (operator-supplied, Addendum A2.1; not fetched here))
    - human_procedure_coding: OPEN (assessed 2026-09-11; evidence: none)
    - insurance_adjudication: UNKNOWN (assessed 2026-09-11; evidence: none)
- confound: citing either standards body by name recruits a protective response (citation confound); names stay in provenance
- provenance: operator session 2026-09-11 (case description; no document pointer supplied)
- opened: 2026-09-11

## GR-0005  T1  UNKNOWN

- quantity: live interlocutor-model resolution and update rate in language models: how finely a model resolves the person it is talking to and how fast that model updates within a conversation
- index terms: language model, benchmark, interlocutor, update, rate, conversation
- excluding method: static benchmark evaluation: items are scored one prompt at a time against a fixed answer key; the construction has no interlocutor whose state can change, so no resolution or update quantity can appear
- measured instead: per-item accuracy, aggregate benchmark score
- venue check: a benchmark whose items carry an interlocutor state that changes across turns; none located in this session
- closure condition: a published benchmark or dataset that reports an interlocutor-resolution measure and an update-rate measure per model
- closing instruction (T1): MEASURE: the quantity is absent by construction; close by an instrument that returns it
- refutation: an existing multi-turn benchmark already reports both quantities under other names
- status by field:
    - language_model_evaluation: UNKNOWN (assessed 2026-09-11; evidence: none)
- confound: multi-turn benchmarks exist; whether any reports resolution or update rate rather than final-turn accuracy was not checked here
- provenance: operator session 2026-09-11 (case description); experiments/substrate_pilot_v0/v2d_authority (a single-turn instrument; does not measure this)
- opened: 2026-09-11

## GR-0006  T1  UNKNOWN

- quantity: the located-friction log in negotiation: a record of where friction was placed during a negotiation and of release granted as a token of faith, as quantities the literature could count
- index terms: negotiation, mediation, friction, release, log, settlement
- excluding method: negotiation outcome analysis: the method records positions, offers, and settlement terms; there is no field for the location of friction or for a release given without an exchange
- measured instead: offer sequence, concession size, settlement value
- venue check: none exists
- closure condition: a published negotiation dataset or coding scheme with a field for friction location or for release-without-exchange, and a count under it
- closing instruction (T1): MEASURE: the quantity is absent by construction; close by an instrument that returns it
- refutation: an existing negotiation coding scheme already carries such a field under another name
- status by field:
    - negotiation_research: UNKNOWN (assessed 2026-09-11; evidence: none)
- confound: the two named quantities may be one; the unit rule (one quantity per entry) may require a split
- provenance: operator session 2026-09-11 (case description; no document pointer supplied)
- opened: 2026-09-11

## GR-0007  T2  OPEN

- quantity: instrument stability of results collected through a hosted language model: whether the model that produced a result is declared as fixed or as routable, and the partition between results with and without that declaration
- index terms: language model, benchmark, instrument, stability, grader, declaration
- excluding method: result reporting through a hosted model endpoint: the record carries a model name as a claim; the endpoint may route silently, and no field states whether the instrument was stable across the run
- measured instead: the result, with the claimed model name
- venue check: a results table with an instrument-stability column (declared | undeclared); the substrate pilot's grading records now carry grader_identity {claimed, verified} and canary rows
- closure condition: a published results record whose schema carries an instrument-stability declaration per run, with a known-answer check that can detect substitution
- closing instruction (T2): DECLARE the partition: close by a declaration that the separation was made, as a choice; the residual is a marked, unmeasured quantity
- refutation: a widely used results schema already carries per-run model verification
- status by field:
    - language_model_evaluation: OPEN (assessed 2026-09-11; evidence: none)
    - substrate_pilot: CLOSED_INSTRUMENT_EXISTS (assessed 2026-09-11; evidence: experiments/substrate_pilot_v0/grading_prompt.py: grader_identity {claimed, verified} + canary rows; check_run SUSPECT)
- confound: a canary failure can be drift within one model, not substitution; the check marks SUSPECT, not substitution
- provenance: experiments/substrate_pilot_v0/grading_prompt.py (canaries, check_run SUSPECT); experiments/substrate_pilot_v0/fixtures/maria_locus_round3_results.jsonl (kimi P1 paste duplication, 2026-09-11); CISA AA26-251A (silent model routing), as cited in the rollup order
- opened: 2026-09-11

