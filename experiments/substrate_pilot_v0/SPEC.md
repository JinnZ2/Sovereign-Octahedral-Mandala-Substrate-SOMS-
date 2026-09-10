# SPEC — substrate coordination pilot v0: failure-derived tests + legacy onboarding

CC0. Stdlib-buildable. Paper-operable.
Loop: regional food distribution (food bank -> pantries), N <= ~150 nodes.
Skeleton: ICS. C4 reference: Feeding America Choice System (Prendergast, JEP 31(4), 2017).
Failure source for this version: DHS OIG-20-76, "FEMA Mismanaged the Commodity
Distribution Process in Response to Hurricanes Irma and Maria" (2020-09-25).
One source = one case. Katrina (House, "A Failure of Initiative", 2006) and GAO 2018
are the next intake.

## 0. Channels (from prior work)

```
C1 STATE      what exists: stock, condition, location, identity, custody
C2 NEED       what is needed, where, when, in what declared unit + dependency edges
C3 COMMIT     who does what by when; kept/broken; receipts
C4 ARBITRATE  declared rule for contention; residual -> live arbitration
REC           nesting, span 3-7
FLT           failure reports -> rule revision
BND           money/token only at declared boundary (R-09 revised)
```

## 1. Verification methods

```
T test (inject + observe)   A analysis (measured rate)   I inspection (schema/doc)
D demonstration             E exercise (HSEEP-style tabletop or functional)
BASELINE = the OIG-measured value. TARGET = operator-set, declared before the run.
```

## 2. Failure-derived test set

Every row traces to an OIG finding. The shall is ours; the finding and baseline are not.

```
FT-01  FINDING  38% of shipments (4,462) lost visibility; 98% meals + water;
                HQ did not record customer orders timely or at all
       CHANNEL  C1 state not created at origin
       SHALL    no unit releases from origin without a state record; an unrecorded
                movement holds at the gate
       VERIFY   T: inject unrecorded order -> held. A: visibility %. BASELINE 38% lost

FT-02  FINDING  2,402 records edited so final location = "unknown FSA"
       CHANNEL  C1 relabel: loss recorded as a location
       SHALL    UNKNOWN is a status, never a location; LOST records keep last-known
                position + time; closure requires physical reconciliation
       VERIFY   I: schema rejects "unknown" as location. T: attempt close without
                reconciliation -> refused

FT-03  FINDING  GPS unused on >75% of shipments to PR, >96% within PR; vertical
                container stacking blocked signal; GPS data on 3.4% of in-island moves
       CHANNEL  C1 single-sensor dependency; environment defeats sensor
       SHALL    two independent state channels per unit (electronic + physical:
                seal no., T-card, gate log); loss of one loses no state
       VERIFY   T/E: disable electronic channel mid-exercise -> state held on paper

FT-04  FINDING  carrier broke seals, repacked, issued generic "relief supplies"
                manifests; ~1,000 containers may never have left Jacksonville;
                carrier cited balancing commercial and FEMA requirements
       CHANNEL  C1 identity destroyed at transfer + money frame in the critical path
       SHALL    unit identity survives every transfer; repack creates a child ID
                linked to parent; no carrier-side optimization may alter a
                critical-path unit without a recorded manifest
       VERIFY   I: parent/child ID schema. T: repack without manifest -> flagged

FT-05  FINDING  no delivery documentation for 86 of 90 sampled shipments (96%)
       CHANNEL  C3 commit record absent
       SHALL    delivery = receiver mark (signature/stamp/photo of paper receipt);
                state stays IN_TRANSIT until receipt exists
       VERIFY   A: receipt rate on sampled deliveries. BASELINE 4%

FT-06  FINDING  avg 69 days to final destination; ~48 days sitting in custody;
                37% of water and 45% of meals shipped reached RSAs/PODs
       CHANNEL  C2 need not pulling flow; stock at rest unseen
       SHALL    dwell time per unit visible; dwell over a declared limit escalates
                to C4 automatically
       VERIFY   A: dwell distribution. BASELINE 48 d custody dwell

FT-07  FINDING  snack boxes substituted for meals; ~1 meal per 12 boxes;
                conversion factors agreed ~4 months in, cutting reported meals
       CHANNEL  C2 measurand mismatch (boxes counted, nutrition needed)
       SHALL    need and delivery denominated in declared units (kcal, protein,
                L water/person/day); conversion factors declared pre-event;
                any substitution logs its conversion at substitution time
       VERIFY   I: unit declarations. T: inject substitution -> conversion required

FT-08  FINDING  40% of responding municipalities reported significant problems
                with expired food
       CHANNEL  C1 condition not tracked (location + qty only)
       SHALL    condition + expiry per unit; first-expiry-first-out rule in C4
       VERIFY   I, A

FT-09  FINDING  a 2011 exercise AAR anticipated the commodity movement need
       CHANNEL  FLT loop open: finding never became a rule
       SHALL    every AAR finding becomes a tracked rule change OR a WAIVED record
                with owner + date; open findings displayed at activation
       VERIFY   I: finding register. A: open-finding age

FT-10  FINDING  receiving government's records manual, dispersed, one set at a
                personal residence
       CHANNEL  C1 record custody / persistence
       SHALL    records carry declared custody + >=2 copies in separate places;
                paper transcribed or photographed within one operational period
       VERIFY   I, D

FT-11  FINDING  invoices paid / contract ratified without proof of delivery;
                oversight relied on verbal statements and emails
       CHANNEL  money ledger closed while the physical ledger stayed open
       SHALL    no settlement (payment, credit, or token) for a delivery lacking a
                C3 receipt; the money ledger may not close ahead of the physical one
       VERIFY   T: settlement request without receipt -> refused. A: rate

FT-12  FINDING  advance contract omitted cross-docking, port processing, and
                onward transport legs
       CHANNEL  C2 dependency edges not enumerated before the event
       SHALL    route dependency graph enumerated per region in planning; every edge
                has an assigned node; unassigned edges flagged
       VERIFY   I, E

FT-13  FINDING  first food/water ~10 days; 20% of respondents had enough food in
                first delivery; 90% received no pre-positioned commodities;
                27% unfamiliar with the distribution plan, 23% helped write it
       CHANNEL  C1/C2 at the local node; plan authored without the nodes
       SHALL    local nodes hold pre-positioned stock sized in declared days-of-need;
                plan co-authored with each node; familiarity verified by exercise
       VERIFY   E, I

FT-14  FINDING  95% of cell towers out
       CHANNEL  channel dependency
       SHALL    every channel operable with zero cellular (paper + HF/mesh)
       VERIFY   E: full exercise with cellular disabled

FT-15  SOURCE   Natural Hazards Center quick-response report (community food
                provision where agencies did not reach)
       CHANNEL  C1 intake closed to non-enrolled nodes
       SHALL    registry accepts state and need from unregistered nodes as
                PROVISIONAL, promoted on first kept commitment
       VERIFY   E
```

## 3. Legacy onboarding — strangler path

The node that approves onboarding is the legacy operator. Onboarding must never
require that node to approve its own deletion. Entry is through the legacy
system's own pain point: audit exposure. FT-05, FT-10, FT-11 produce exactly the
evidence OIG-20-76 found missing.

```
PHASE 0  SHADOW      substrate ledger reads legacy exports (inventory, orders,
                     receipts); writes NOTHING to legacy
                     metric: divergence between ledgers per operational period
                     = the residual (what the legacy record is not holding)
                     exit: 4 periods reconciled, divergence classified

PHASE 1  ADAPTER     field map legacy -> C1..C4 (table below)
                     legacy compliance outputs (grant, donor, audit) GENERATED
                     from the substrate ledger -> legacy gains an audit trail
                     exit: one compliance report produced and accepted

PHASE 2  STRANGLE    route ONE path (one commodity class OR one pantry route)
                     through substrate routing; legacy stays system of record
                     for money
                     metric: FT-01/05/06/07 rates, same clock, both paths
                     exit: substrate path >= legacy path on declared metrics

PHASE 3  ARBITRATE   Choice-type token for allocation among pantries:
                     need-issued, non-convertible, reset per period, no interest,
                     declared override committee
                     exit: allocation residual (need vs delivered, declared
                     units) reported for 1 season

PHASE 4  BOUNDARY    money appears only at donor/grant boundary, each use
                     carrying a MONEY_TERM scope declaration
                     legacy is UNROUTED, never deleted

ROLLBACK every phase reversible by re-routing; no legacy data destroyed
```

### Field map (generic; adapt per legacy system)

```
LEGACY FIELD                      CHANNEL  SUBSTRATE FORM
item / SKU / qty on hand          C1       unit id, declared unit, qty, condition,
                                           expiry, custody, location
pounds received / distributed     C1/C2    kept for reporting; decisions use
                                           declared nutrition units (FT-07)
agency order / request            C2       need + declared unit + clock + edges
delivery ticket / bill of lading  C3       receipt (receiver mark) (FT-05)
allocation policy / formula       C4       declared rule + override path
volunteer roster / shifts         C1/C3    capability by person + setting;
                                           commitments kept/broken
invoice / grant draw              BND      MONEY_TERM record; blocked without
                                           C3 receipt (FT-11)
```

## 4. Pilot verification exercise (tabletop, then functional)

Replay the OIG sequence at pilot scale. Injects, in order:

```
I-1  order placed with no state record                       FT-01
I-2  electronic tracking lost for 2 operational periods      FT-03
I-3  carrier repacks without manifest                        FT-04
I-4  meals unavailable, snack boxes substituted              FT-07
I-5  settlement requested for an unreceipted delivery        FT-11
I-6  cellular down for the whole exercise                    FT-14
I-7  unregistered community node reports need and stock      FT-15
I-8  prior AAR finding exists, unacted                       FT-09
PASS per FT row against its declared target.
Failures reported as found, not relabelled (FT-02 applies to the pilot itself).
```

## 5. Scope, declared

```
N <= ~150, one loop, recursion depth 1
claims: closure, visibility, dwell, receipt, unit fidelity
NOT claimed: lower total cost; performance at nested scale; transfer beyond
             shared-training populations (Buck, Trainor & Aguirre 2006)
thresholds: OIG baselines are real; targets are operator-set
```

## 6. v0.1 additions (WORK ORDER — substrate pilot v0.1)

```
FT-16  NAMED CUSTODIAN, EVERY BOUNDARY
       SHALL    custody transfers only by signed handover naming both parties; a unit sitting
                with a present-but-noncustodial node (gate guard, unattended yard) reads as an
                unsigned transfer -> flagged
       VERIFY   T: transfer without handover -> refused; presence past grace -> flagged. A: detection %

FT-17  HEARTBEAT
       SHALL    silence is never a normal state; max silence interval declared per R2/R3 load;
                a suppressed check-in escalates within one interval
       VERIFY   T. METRIC detection latency (Maria baseline: months)

FT-18  CONTESTED CUSTODY
       SHALL    any competing claim on an R2/R3 load routes to a pre-declared resolver reachable
                without cellular; custody does not move until resolved
       VERIFY   T: resolver contact record with cellular-only path -> refused at declaration

V1  failure LOCUS + SITE on every failure record; physical_damage only at site = damaged
V3  regime class R0..R3 + axis (urgency | custody) per load; "critical" alone refused; custody axis may not drop
V4  context-severity: event declaration reclasses from a precomputed trigger table, no deliberation
V8  retention: class assignments persist post-event; missing + not WAIVED -> flagged at activation

Injects, appended to section 4 in order:
I-9   suppress one check-in                          FT-17
I-10  competing custody claim at a yard              FT-18
I-11  declare event -> loads reclass                 V4
I-12  local custodian availability set to 20%        FT-16
I-13  load declared "critical", no axis              V3
```

## 7. V11 — CLIMATE field

```
V11  CLIMATE FIELD                           every spec row and every load record
     CLIMATE = stable | partial | variable   carries CLIMATE; missing -> defaults
     STABLE    inputs in spec, parts in      to stable AND is flagged; event
               stock, design fixed, help     declaration flips climate to variable
               reachable in time             via the V4 trigger table (selftest);
     PARTIAL   some of the above fail,       any efficiency/throughput target in
               intermittently or in one      the spec carries the climate it was
               channel                       measured in
     VARIABLE  shortage, off-spec inputs,
               changing environment, novel
               failures
     RULE  a claim is valid only inside its
           declared climate
     NODE  under variable climate, every
           contact/custody node runs the
           field-fix check: sign | DOF |
           state updated
```

Per-row climate is machine-readable in `spec_rows.json`; operator targets carry
`climate` in `exercise.TARGETS`. A verdict against a target declared in a climate
other than the run's is reported as NOT VALID (climate), never as PASS or FAIL.
