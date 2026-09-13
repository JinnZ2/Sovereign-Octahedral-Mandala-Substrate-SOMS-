# durability_register

A mechanism-level failure-mode register for ML components used as infrastructure, scoped to DURABILITY and
RECONSTRUCTABILITY. CC0, stdlib only. The deliverable is `register.jsonl`; everything else is generated from it.

```
NON-GOALS, stated first
  not model behaviour, alignment or misuse · not harm incidents · not a code of ethics
SCOPE
  can the deployed object still be identified, re-produced, load-rated and inspected at t + N years,
  by someone who is not the original author and does not hold the tacit stack
DEPLOYMENT CLASS (step 1, fixed)
  a model in a decision loop with NO human review of individual outputs, whose outputs are consumed by a
  downstream process that acts on them
```

```bash
python experiments/durability_register/failure_register.py validate    # schema, mandatory-field gate, projection cap, header counts
python experiments/durability_register/failure_register.py report      # reconstruction distribution, detection gap, requirement set, null set
python experiments/durability_register/failure_register.py falsifiers  # F_A..F_H, each with its status
python experiments/durability_register/failure_register.py audit       # F_C: random 20%, rejection rate
python experiments/durability_register/failure_register.py coverage    # order section -> artifact, GAP if nothing carries it
python experiments/durability_register/failure_register.py emit        # REGISTER.md + outsider_test.md
python experiments/durability_register/failure_register.py selftest
```

## What came out (rev 7)

```
entries 37     rated 35     unrated parts 2      LENGTH WATCH: 37 of a 40 tripwire
sections       0: 1   3A: 6   3B-W WORKED: 11   3B: 8   3C: 8   6C COMPOUNDING: 3
reconstruction AS-IS: NO 17   PARTIAL 16   NOT_APPLICABLE 4   YES 0
               axes NOT merged: with-control {DUR-001: PARTIAL} · trajectory {DUR-003: PARTIAL -> NO}
detection gap  29 of 37 entries: channel begins NONE, or latency is unbounded
projection     32.4% against a stated 35% cap  (33.3 -> 29.2 -> 25.9 -> 24.1 -> 25.8 -> 30.6 -> 32.4)
citations      36 verified this session   23 named from memory and NOT verified
coverage audit 63 rows, 0 gaps, 1 entry not mapped to an order section (D-105, derived from D-102)
```

### The patch was NOT applied, per its own instruction

The patch targets `WORKORDER_failure_mode_enumeration.md` and says to stop and report if an anchor is not found
exactly once. That file exists in neither repository, and **none of the four anchors was found anywhere**, including
in JinnZ2/Simulators at head b2b1232:

```
target WORKORDER_failure_mode_enumeration.md   ABSENT from SOMS, GlyphAI and Simulators
hunk 1 "...ECONOMICS AND INSTITUTIONS presented as"   0 matches (the text exists only inside this
                                                      register's header as a JSON value, not as a line)
hunk 2 "F_K  AMBIENT SET IS UNBOUNDED."               0 matches
hunk 3 the A-10 block, before "### 9-1  STILL OPEN"   0 matches; no A-series log and no section 9-1 anywhere
hunk 4 the PROVENANCE REGRESS bullet in 9-1           0 matches
```

The patch's target is a third artifact: an operator working copy further ahead than either repository, carrying an
A-numbered correction log to A-10 and a section 9-1. Nothing was guessed. The patch CONTENT is implemented in the
register instead, which is where the previous six revisions landed, and the entry citation records that the patch was
not applied as a patch and why.

### DUR-005-B carrier-side ambient

```
ARTIFACT-SIDE   conditions the OBJECT needs to exist and be read        DUR-005
CARRIER-SIDE    conditions the CARRIER needs to be able to PERFORM      DUR-005-B   (new)
                not reachable by the artifact-side question: a carrier-side condition does not make
                the record unreadable, it makes the method unrunnable while the record stays legible
```

The mechanism is that a reliably produced capacity reads as an intrinsic property of a population rather than as an
output of conditions, so the dependency is never stated, and the precondition that fails sits upstream of every
transmission variable. The transmission chain can be intact throughout. **Loss does not scale with the size of the
cause.**

The DUR-005-C screen has no null result: every capacity scores PRODUCED or FLAGGED, nothing scores clean, and
`validate` enforces that. Then F_M bounds it, and the result is the finding:

```
capacity                                                    screen    F_M
working memory sufficient to audit a representation         PRODUCED  UNINSTRUMENTED, excluded
ability to read low-level implementation                    PRODUCED  UNINSTRUMENTED, excluded
training pipelines producing these at replacement rate      PRODUCED  UNINSTRUMENTED, excluded
working conditions permitting sustained single-task attention PRODUCED UNINSTRUMENTED, excluded
willingness to do maintenance work with no attribution      PRODUCED  ACTIVE - DUR-004 already measures it
```

Four of five have no production-rate measure and are excluded as UNINSTRUMENTED rather than carried as claims. The
one admitted is admitted because DUR-004's bus-factor and time-to-first-modification signals already measure its
local form. The class is real and the instrument for four fifths of it does not exist, which is what the register
records instead of asserting a hazard it cannot bound.

The entry is PROJECTED, not MEASURED. The operator states a documented historical form and does not name the case;
naming it is the cheapest available upgrade to this entry.

### A sibling register exists, and it found a defect in this one

Checking Simulators for the patch target turned up `failure-mode-register/` (WORK_ORDER.md, entries.py, register.py,
test_register.py, CLAIM_TABLE.md) at rev 3 of the order. It is a **conformance instrument over the order, not a
populated register**: it parses the order at call time, reports filing state, vocabulary conformance and step status
over the order's own four ENTRY blocks, and authors nothing. Four entries, projected fraction 0.0.

It does three things better than this register, by this register's own criteria:

- **It derives instead of transcribing.** The order is delivered verbatim in-repo and parsed at call time, nothing
  retyped. This register transcribes entry text into `register.jsonl`, which is a custody weakness of exactly the
  kind DUR-010 describes.
- **It imports `effective-redundancy-audit::n_eff` as code**, where DUR-009 only cross-references that instrument by
  name.
- **It refuses to merge the reconstruction axes**, and that is a real defect it caught here. This register published
  one distribution over cells carrying different axes: an as-is score, a with-control score and a moving score.
  Merging them puts a control state and a date in one column. Fixed: the stored value is the as-is score,
  `reconstruction_with_control` and `reconstruction_trajectory` hold the others, the report publishes the as-is
  distribution labelled as such plus the two other axes separately, and `validate` refuses an entry that declares a
  with-control reading in prose without the field.

What this register has that it lacks: its Step 0 is BLOCKED because its egress refuses the catalogue hosts, so its
F_B is unresolved and it says it is not cleared to ship. The prior-art map here supplies that. Its Step 1 is NOT_RUN
with no deployment class declared. And it holds none of rev 4 to rev 7.

**Recommendation: consolidate into the Simulators copy.** It derives rather than transcribes, it sits beside the
instruments it needs to import, and it already has a conformance layer this register lacks. That requires push access
to JinnZ2/Simulators, which this session does not have: the clone here is read-only. Recorded in `still_open`.

**The expected yield inverted.** Section 8 predicted PARTIAL would dominate and NO would be rare. After rev 6 the
two are tied at 16, and every entry the operator added in this revision scores NO: ambient precondition, custodian
continuity, and all three compounding entries. The prediction was wrong in the direction of optimism, the report
says so in its headline rather than calling PARTIAL modal on a tie, and the selftest asserts the correction so it
cannot quietly revert.

### Rev 6: two id collisions, resolved in the operator's favour

The order assigns DUR-005 to the ambient precondition and DUR-006 to custodian continuity. This register had already
used both numbers for mechanisms of its own. Operator ids are authoritative, so:

```
DUR-005 (mine, correlated substrate and dependency shock)  ->  DUR-009
DUR-006 (mine, no batch record)                            ->  DUR-010
```

Recorded in the header's `id_map_renumbered` and on each moved entry as `renumbered_from` with the reason, so a
reader who saw an earlier revision can follow the move. Every cross-reference, coverage row and selftest assertion
was repointed.

### DUR-005 ambient precondition, and why it sits above the others

It can VOID the controls proposed for DUR-001 through DUR-004 without any of them having failed. The record is
complete on its own terms; what is missing is the world the procedure ran in, and the procedure gives no indication
that a world was required. Its detection channel is NONE **from inside**, for the same structural reason an exclusion
register cannot be generated from inside the frame it excludes from.

The control is the ambient enumeration, and the question is not "what is assumed":

```
ask   WHAT WOULD HAVE TO STOP EXISTING FOR THIS TO BECOME UNREADABLE?
with  participants OUTSIDE the stack — hard requirement, not a preference
bound F_K: a condition enters only if its expected lifetime is within the claimed horizon (10 years here)

admitted   power at current density and cost · fabrication at current tolerance · a network ·
           a machine that reads the format · storage priced as unlimited · compute priced as
           unlimited · a continuing custodian
           the last three are ECONOMICS AND INSTITUTIONS presented as technical background
excluded   the sun · the species · the grid as an institution   (noted once, per F_K)
```

`validate` refuses an ambient set with no horizon, an admitted condition outside the horizon, or a missing exclusion
list, so the bound is demonstrated rather than asserted.

### DUR-006 custodian continuity, and the arithmetic that is not arithmetic

Six transfer modes, all observed, none rare, each moving the artifact without moving the carriers. The important one
for detection is **strategy change**: the artifact is retained and still served, there is no transaction, no filing,
no announcement, no external signal of any kind, and only DUR-004's carrier-side measurements see it. That is why
DUR-006's detection channel is DUR-004's.

The seven-term conjunction is in the header. Every term must hold simultaneously and continuously; nothing in the
arrangement ensures any of them; therefore continuity cannot be claimed. **No number appears anywhere near it**, and
`validate` fails the register if one does. F_L is the reason: the terms are correlated, insolvency drives carrier
loss drives strategy change, so the joint failure probability is higher than a naive product and any naive number is
wrong in the reassuring direction. The conclusion rests on the inability to ensure each term and survives without
arithmetic.

The variable correction is recorded as the order states it: **custodian continuity is the wrong variable, custodian-
independence is the right one.** A single holder is a conjunction and survives only if all terms hold; distributed
retention is a disjunction and survives if any holder persists. A framework that rates custodian quality will rate a
fully distributed arrangement lowest, and that is the framework being wrong rather than the arrangement. The natural
experiment is carried as the operator's instance, unnamed and unverified here, not as a citation.

### 6C compounding: three entries, all PROJECTED, and one rule that bites

```
DUR-015  rate mismatch          the slow layer holds the only shared external referent, and everything
                                carrying meaning moves faster than it. Nothing anchors. INVERTS the
                                classical case, where a slow durable substrate held the referent.
DUR-016  seam multiplication    seams at generation rate, no owner of the boundary has ever existed, and
                                an automated system must return a value: it selects a criterion with no
                                record that a selection occurred.
DUR-017  coupled preemption     two controllers acting on each other's incommensurable output, under load.
                                A wrong research result gets corrected; this fails while the load is on.
```

All three are PROJECTED under F_J, which `validate` enforces: a 6C entry that is not PROJECTED and cites no current
instance is refused. The order says the rate mismatch and the custody choices are observable now and the regress is
not yet; this build cites no measured instance for any of them, so none is scored as measured however strong the
argument reads.

6C-1 also produced a rule with teeth: **an entry may not cite hardware or substrate stability as a custody control.**
`validate` rejects it. Hardware slowness protects nothing if the representation layered on it is redefined between
hardware cycles.

6C-2 closed the gap I flagged in rev 5. DUR-008 was written from two sentences in conversation because section 6C had
not been supplied; it is now re-cited to 6C-2 and 6C-7, and its citation records both that history and the fact the
section arrived later. Its requirement is now the minimal arrest in full: a frozen interchange layer no generation may
redefine, containing identity, envelope and hop log, frozen outside the generating system, with the FORMAT of those
fields inside the frozen set, because under the compounding case DUR-001 and DUR-002 are a contract between
generations rather than between an author and a later reader.

6C-5's correction landed on DUR-004 as a `carrier_definition` field: a carrier is not someone in the field, it is
someone who can read the representation. Carrier population moves from protective to loss-driving, and the header
records the flip so the earlier score does not persist in derived work.

### Rev 5: the degradation / regress class boundary

```
DEGRADATION   loses fidelity per hop, stays measurable       -> DUR-003
              what is missing can be stated and quantified
REGRESS       loses the ability to STATE what was lost       -> DUR-008  (new)
              the naming capacity went across the same hops

              per-hop instrumentation improves the first and does not touch the second:
              a hop log records what its authors could still name, so a regress passes
              through it intact and undocumented
ARREST        freeze WHAT must survive a hop, not HOW the work is done
              frozen from OUTSIDE the generating system, or it is inside the regress   -> DUR-008-N1
```

DUR-008 is the only entry whose detection channel is not the ordinary NONE. Every other gap here could be closed by
an instrument nobody has built yet. This one cannot be closed from inside the system at all, because an instrument
built inside it is subject to the same loss and reports clean. It is also the entry with the widest consequence and
the weakest anchor: PROJECTED, lowest weight, because an anchor would require observing a regress from outside it,
which is the thing the mechanism says cannot be done from inside. And it is the one entry whose own reconstruction
score is subject to the mechanism it describes, which the note says outright.

DUR-008-N1 carries the externality requirement as its own entry, transported from metrological traceability: a
measurement is traceable only to a standard maintained outside the measuring laboratory, and a lab that calibrates
against its own working reference has precision and no traceability. A survival set the generating system can revise
is in the same position. Third-party evaluation commissioned, scoped and paid for by the evaluated party is internal
custody with an external label. A set with no named external holder is recorded as UNFROZEN rather than as a control.

**The register now records the limit of its own coverage check.** `coverage` reports gaps against mechanisms someone
was able to name, so its zero-gap result means no named mechanism is unentered, never that no mechanism is missing.
That line prints with every coverage run so a clean result cannot be read as completeness.

**Length watch.** 31 entries is not short, and section 8 says a long register is a warning sign rather than a
result. The guard in the selftest moved from 30 to 35 and is a tripwire, not a budget. The growth accounting is in
the header and in the emission: every entry after rev 1 was operator-supplied, required by a section that demanded
its own entry, or a named mechanism the coverage audit found unentered. None was self-generated. The next addition
that is neither operator-supplied nor gap-closing should displace an entry instead of extending the list.

### Rev 4: the order arrived unchanged, so the work was verification

The re-issued work order is byte-identical to the one rev 3 was built from. Rebuilding would have produced nothing,
and asserting "already done" would have been a claim with no check behind it. So rev 4 adds the check: `coverage`
maps every section of the order to the entry, header key or code hook that implements it, and reports a GAP for any
named mechanism that no artifact carries. 43 rows. It found two gaps, both in the order's own 3B domain list, both
mechanisms I had silently skipped:

- **DUR-006, no batch record.** The order names "batch records" under pharmaceutical alongside the retained sample,
  and nothing in the register covered it. The mechanism is a record of INTENT standing in for a record of
  EXECUTION: configuration and code are recorded, and the run's restarts, failed shards, skipped batches, node
  substitutions and moved data snapshots are not. In pharma every deviation from the master formula is recorded and
  dispositioned before release; here nothing requires any of it. The detection channel is the run's own logs, whose
  retention is set in weeks while the object serves for years, so the channel closes on a schedule nobody connected
  to the object. When a rebuild then differs, the difference gets attributed to variance (D-101) and closed.
- **DUR-007, load rating lost.** The order names "load rating lost" under structural, and the register only had the
  case where a rating exists and fails to travel (DUR-002). This is the other one: the rating was established, its
  record is gone, and the component stays in service being described as evaluated, because the memory that it was
  once evaluated outlives the evidence of what the evaluation said. The transport is sharp because the home domain
  has a procedure rather than a lament: federal practice directs that a load rating be established for every
  structure in the inventory even where as-built plans are missing, by field measurement with conservative
  era-appropriate assumptions, by load testing, or by documented engineering judgement. Re-rate or post. Never carry
  the belief forward. That is the requirement, transported intact.

One entry, D-105 (readiness is not outcome), maps to no order section. It is derived from D-102 rather than from the
order, and `coverage` reports it rather than hiding it, because a register holding content its order did not ask for
should say so.

### Rev 3: what the new sections forced

**DUR-003 migration attrition** and **DUR-004 stranded under load** entered as the operator supplied them. Two
things in them changed the schema rather than just adding rows.

DUR-003's reconstruction is a trajectory, not a value: it degrades from PARTIAL toward NO with no state change
recorded anywhere on the path. Scoring that as a single value would reproduce the defect the entry describes, so
`reconstruction_trajectory` is now a field, `validate` requires a prose note beside it, and the score stays at its
current value rather than its destination.

DUR-004 is the first entry in the register whose detection channel is real. Bus-factor count,
time-to-first-successful-modification by an engineer who did not build the thing, failed replacement attempts: all
three are measurable today and none is measured. It is also the inverse of the classical case, and that inversion
is now the F_F answer. Pyramids: object retained, load off, comprehension gap harmless. Stranded: object retained,
load **on**, comprehension gap *is* the liability. A surviving artifact is not a recoverable technology.

**DUR-005 correlated substrate and dependency shock** is new and was required by section 6B-2, which says
correlation needs its own entry. It is transported from common-cause failure analysis, where redundant channels are
credited only after shared causes are removed from the count. It points at `effective-redundancy-audit` in
JinnZ2/Simulators, which already computes N_eff from six shared-node classes, rather than re-deriving it.

**The register rule from 6B-2 is enforced in code.** Any entry claiming redundancy as a control must state what
the copies do NOT share, and `validate` rejects one that does not. The selftest proves the rule bites by building a
synthetic entry that claims redundant buckets and checking it is refused.

**The shock re-cut changed an existing entry's text, not just the header.** D-207 no longer reads as decay: the
bits do not rot, the reader is gone, and intact-and-unreadable is a distinct state from decayed that is *worse*
because every inventory, checksum and storage metric reports the deposit as healthy. Carrier shock stays low here;
substrate and dependency shock are high and are scheduled, which ought to make them the easy case and does not,
because a planned shock with no budget line behaves exactly like an unplanned one.

**The accounting is carried in hops, with no numbers invented.** The header holds the hop budget (about 20
generational hops over 500 years against 20 to 50 substrate hops over 10 years, the operator's order-of-magnitude
estimate and labelled as theirs), the expected-count form, and the correction that objects share hops. No value is
supplied for objects, hops or per-hop probability, because putting numbers on that form is exactly the projection
inflation F_D forbids. The two consequences are kept apart: at system level loss is a rate, and at operator level
it still looks rare, so every operator's local experience honestly reports that it does not happen. That second
one is entry D-000 again, one level up.

### Section 3B-W: the operator's worked entries supersede mine

The re-issued work order supplies DUR-001 and DUR-002 filled to schema. They are the authoritative versions of
the two priority transports and they REPLACE the versions this register had built (D-201 retained reference
sample, D-202 stamped validity envelope). The supersession is recorded in the header's `id_map_superseded` and on
each entry's `supersedes` field; the earlier text is in git history, not duplicated in the store, because a second
copy of the same mode is the thing Step 0 forbids.

What the operator's versions add that mine did not have:

- **A proposed detection channel, not just an absent one.** DUR-001 proposes a sealed probe-response record held by
  a party that is not the operator, third-party checkable without re-manufacture. DUR-002 proposes a machine-readable
  envelope attached to the serving interface plus a RETURN CONTRACT in which `OUT_OF_ENVELOPE` is a distinct return
  state rather than a low confidence score. Both fields now read "NONE under current practice. PROPOSED: ...", and
  the gap predicate counts them as gaps today, which is why the detection-gap count went up rather than down.
- **Confidence scores explicitly ruled out.** A confident output inside a distribution the object was never
  characterised on is the failure, not a warning of it.
- **The controls' own failure modes as entries.** DUR-001-N1 (probe leakage), DUR-001-N2 (instance is not
  procedure), DUR-002-N1 (blank envelope read as wide) are entries with mechanisms, detection channels and
  requirements, and they are wired as `control_preconditions` on the entry whose control they threaten. `validate`
  refuses a proposed control that has no stated preconditions.
- **The coupling.** DUR-001 and DUR-002 are a registered pair and `validate` requires the coupling from both
  sides. An envelope without a sample states conditions that cannot later be checked; a sample without an envelope
  is data, not a rating.
- **A fourth reconstruction value.** DUR-002 governs USE, not rebuild, so it scores NOT_APPLICABLE with a stated
  reason rather than a rebuild score it does not measure. Three entries score it and are excluded from the
  headline's denominator, which is now 21 entries rather than 24.
- **PARTIAL where I would have written NONE.** DUR-002's existing control is scored PARTIAL because model cards
  exist, even though they are filed alongside rather than attached. That is the step 7 null-set discipline applied
  inside an entry.

One new measured anchor came out of integrating N1: contamination figures as reported by a 2026 survey (over 16
percent of MMLU samples flagged in the LLaMA-2 report; over 90 percent of QuAC, SQuADv2 and DROP examples in the
GPT-3 study; 13-gram and 50-character overlap thresholds), plus the finding that rephrased samples evade n-gram
decontamination. The survey is a SECONDARY source for each underlying report and the citation says so.

**Nothing scored YES on reconstruction.** Not one of the 32 entries that make a reconstruction claim. The expected-yield note in the work order said PARTIAL
would dominate, and it does, but the absence of a single YES is the sharper result: for this deployment class
there is no failure mode in the register whose retained record is sufficient to identify the object.

**Twenty-eight of thirty-six entries have no detection channel or an unbounded latency.** That is the work order's
Entry 0 reproducing itself through the body of the register. These are the modes that cannot generate the
evidence that would make fixing them mandatory, which is the mechanism by which the enumeration does not get
written.

## Step 0, the prior-art check, in full

The check ran four targeted searches on 2026-09-13 and did not stop the work order. What exists:

- **Harm-scoped and incident-sourced.** The MIT AI Risk Repository (1700+ risks from 74 frameworks, 7 domains,
  24 subdomains, causal taxonomy over entity / intentionality / timing) and the AI Incident Database with the
  MIT AI Incident Tracker (1300+ incidents, 10 harm types). Durability and reconstructability are not a domain
  in either. An incident-sourced catalogue cannot hold a mode whose detection channel is NONE, by construction.
  Microsoft's *Failure Modes in Machine Learning* is security-scoped.
- **Adjacent, covering part of the residual.** Sculley et al. on hidden technical debt is mechanism-level and
  closest in spirit, with no detection-channel field and no reconstruction score. The ML Test Score is a rubric
  of controls, which is the requirement set rather than the enumeration. ReproScore (2026) measures readiness
  against outcome for research software artifacts. Model Cards, Datasheets, Data Statements and FactSheets add
  some of the missing fields and none is mandatory anywhere.
- **Residual this register occupies.** A mechanism-level enumeration scoped to durability and reconstructability,
  carrying a detection channel that is permitted to be NONE and a reconstruction score, for one fixed deployment
  class.

Caveat recorded in the falsifier output: four searches on one day establish that the major catalogues are
harm-scoped. They do not establish that no durability catalogue exists anywhere.

## Falsifiers, as answered

```
F_A  transport valid       PASS. 8 transported entries, all stating an abstract structure (a record insufficient
                           to rebuild the object) rather than a resemblance. The two highest-value transports are
                           the retained reference sample and the stamped validity envelope: both cheap, both
                           mandatory at home, neither exists here.
F_B  prior art             CHECKED against public catalogues AND, as of rev 7, against the ecosystem: a sibling
                           implementation exists at JinnZ2/Simulators failure-mode-register/. Not a second copy of
                           the same list (conformance instrument vs populated register), but two registers for one
                           order is itself a durability hazard, so the consolidation recommendation is recorded.
F_C  unbounded scope       AUDITED, and the sample is reported against the whole register because the mandated 20%
                           sample (7 of 36, seed 13) happened to contain NEITHER rejectable entry and reads 0.0.
                           Whole-register rate: 2 of 36 (5.6%), both already filed as UNRATED PARTS rather than
                           discarded. A 0% sampled rate reported alone would have been the register's own
                           detection gap reproduced in its audit. Author-run, which is the weak case F_G fixes.
F_D  projection inflation  32.4% against a 35% cap, and now close enough that the next unanchored entry must
                           displace one rather than be added. Rev 6 rose
                           because F_J forces all three compounding entries to PROJECTED. That is the falsifier
                           working: the fraction is the price of not scoring a structural argument as measured. because every
                           entry the operator has added is anchored: rev 3 adds two TRANSPORTED, one MEASURED and
                           one TRANSPORTED. Stated in the header.
F_E  not the mechanism     STATED, and the honest answer is mostly nothing. Two real forcing functions exist and
                           both are narrow: EU AI Act Article 12 logging with Article 26 deployer retention of at
                           least six months plus Annex IV documentation, in the Act's high-risk categories; and
                           the FDA Predetermined Change Control Plan final guidance of 2024-12-03, for AI-enabled
                           medical device software. The six-month retention floor is shorter than every
                           reconstruction question here. Publishing this register changes nothing on its own and
                           the deliverable does not claim otherwise. The cheapest available lever is procurement:
                           a buyer can require the retained sample, the stamped envelope and the bill of materials
                           as delivery conditions without any regulator acting, because all three are artifacts.
F_F  artifact present      CHECKED per entry. D-207 is the one mode where the object is retained and the reader is
                           lost, and it names what and where. D-201 and D-301 are worded as WAS NEVER CAPTURED,
                           not WILL BE LOST.
F_G  reader precondition   NOT RUN. The test needs a reader outside the domain; running it on the author would
                           reproduce the blindness it tests for. Packaged as outsider_test.md with three field
                           definitions already known to be weak.
F_I  independence          PASS. The volume form and the correlation correction are in the header together, and
                           the correlation mode has its own entry (DUR-005), so neither can be cited alone. The
                           register rule is enforced by validate, not by prose.
F_J  recursive speculation ENFORCED. Every 6C entry is PROJECTED unless it cites a current instance; validate
                           refuses otherwise, and the selftest proves it with a synthetic MEASURED 6C entry.
F_K  ambient set bounded   BOUNDED. Horizon declared, seven conditions admitted with a horizon judgement each,
                           three out-of-horizon candidates recorded as excluded. validate refuses an unbounded set.
F_M  carrier-side bounded  BOUNDED, and mostly UNINSTRUMENTED: 1 of 5 conditions admitted to the active set, 4
                           excluded for having no production-rate measure. The screen has no null result.
F_L  conjunction arithmetic NO NUMBER PUT ON IT. validate scans the conjunction for any probability or percentage
                           and fails if one appears. The conclusion rests on the inability to ensure each term.
F_H  event definition      DEFINED BEFORE ANY COUNT. An event is a bounded change in the reconstruction state of
                           one identified object: (object, field, earliest date, latest date). A two-year silent
                           drift is one event per changed field with wide bounds. A single wrong output is not an
                           event here at all, because that is fidelity and fidelity is out of scope. No failure
                           count appears anywhere in the deliverable; the only counts are entries and citations.
```

## What this register does not have

**Citations are mostly unverified.** 22 of 34 are named from the executor's training with the primary source not
fetched, and each carries `FROM_MEMORY_UNVERIFIED` in the record. The work order says the MEASURED seeds require
re-verification before the register ships. They have not been re-verified. The 12 verified ones were located this
session and are the only citations that should be quoted.

**One figure has a known discrepancy, recorded rather than resolved.** The leakage entry cites 17 fields and 329
affected papers; an earlier version of the same work reports 294. Both numbers are in the record.

**Two entries are UNRATED PARTS**, filed not discarded, per the schema rule: numeric non-determinism across
accelerator generations, and the component changing the distribution it is rated on. In both the executor could
not state a detection channel without measurement and did not invent one. Their empty fields are distinct from
NONE: NONE is a finding, empty is an unfinished entry, and the emission prints them differently.

## Cross-references rather than re-derivations

Three entries point at instruments already in this repository instead of restating their mechanisms:

- **DUR-001 identity** points at the canary rows in `experiments/substrate_pilot_v0/grading_prompt.py`: a probe
  set with recorded answers, held separately, whose failure marks a run SUSPECT. That is the same construction as
  the sealed probe-response record, one scale down, already built and tested in this repository.
- **DUR-002 envelope** points at `experiments/terrain_prior/`, which already implements the UNRATED-not-degraded
  discipline: a prior outside its stated scope is returned with the mismatch flagged, never suppressed and never
  silently re-rated.
- **D-203 as-built drift** points at the canary mechanism in `experiments/substrate_pilot_v0/grading_prompt.py`
  (known-answer rows, `check_run` returning PASS / FAIL / SUSPECT, `grader_identity {claimed, verified}`) and at
  the paste duplication caught in the round-3 fixtures, plus `gap_register` GR-0007.
- **D-205 latent fault** points at `experiments/trigger_geometry/` (accumulation under a single-instance
  validation, and absence from the validation set returning ABSENT rather than SAFE).
- **D-206 custody** points at `experiments/substrate_pilot_v0/ledger.py` (signed handover at every boundary,
  presence without custody recorded as an unsigned transfer, custody never moving on a claim).

## Files

```
register.jsonl        the store: header (deployment class, non-goals, event definition, composition rule,
                      supersession map, hop budget, volume and correlation accounting, shock re-cut,
                      null set, counts) + 27 entries
failure_register.py   validate / audit / report / falsifiers / emit / selftest
REGISTER.md           build product, human emission
outsider_test.md      build product, the F_G test sheet, unrun
coverage              not a file: `failure_register.py coverage` audits the order against the register, 43 rows
```
