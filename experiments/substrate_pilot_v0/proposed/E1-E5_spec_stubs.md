# Proposed tests E1–E5 — spec stubs only (rollup group E, 2026-09-11)

Design only. Nothing here is built, run, or claimed. Each stub names the measurand, the
prediction as written in the rollup, the null, and what would have to exist before it is specced.

```
E1  DEPENDENCY COUNT BY CHANNEL
    measurand   per person, the count of dependencies by channel: named persons | paid |
                institutions | environment
    predict     total >= in WEIRD samples; named-person share lower; self-report tracks the
                named share (people report the dependencies they can name)
    null        totals equal across samples, or self-report tracks the paid share instead
    needs       a channel definition that survives a second coder; a non-WEIRD sample with
                consent and custody declared (T3 D_community family applies); MONEY_TERM
                declaration for the "paid" channel (money_term.py)

E2  INNOVATION CROSSING SHARE BY ORIGIN
    measurand   for each innovation that crossed into wide use, its origin class:
                firm | user | free/household | commons
    predict     not stated; the share table is the result
    null        the origin class is not codable from the record (attribution absent)
    needs       a crossing definition with a threshold; a source list with fetched text
                (group C discipline: locus null until loaded)

E3  DELIBERATION HOURS PER COORDINATED FLOW
    measurand   hours of deliberation per flow, money-denominated vs non-money, on the same
                ledger (substrate C1..C4 gives the flow record; hours are a new field)
    predict     a crossover N (flows per period) may exist where money-denominated
                coordination costs fewer hours; report the curve, not the crossover
    null        no crossover inside the observed N
    needs       an hours field on C3 COMMIT and C4 ARBITRATE records; two pilots or one pilot
                with both flow types; climate declared per row (V11)

E4  RELATION-STATE LABELING BEFORE THE EVENT
    measurand   the labeling ontology a group uses for relation states, recorded BEFORE a
                conflict event; then escalation / recurrence per event
    predict     not stated; the pre-event record is the instrument, the per-event rate is
                the measure
    null        the ontology cannot be recorded without changing it (observer effect)
    needs       a labeling schema with a second coder; a pre-registration date on every
                ontology record; FT-09 style register so labels close only as RULE_CHANGE
                or WAIVED

E5  REPORT-TYPE RELABEL (V10b) AT N > 1 PER DOC TYPE
    measurand   locus share by document type (audit | review | self-review) once C1–C2 land
    predict     review and self-review code heavier on damage than audits (V10b as written)
    null        no difference at N > 1, or N stays 1 (then V10b stays NOT A TEST)
    needs       group C fetches C1 (H. Rept. 109-377 logistics chapter) and C2 (OIG-06-32
                pp. 66-77, 128-134) loaded as verbatim rows and graded by two families
```
