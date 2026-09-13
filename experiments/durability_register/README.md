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
python experiments/durability_register/failure_register.py emit        # REGISTER.md + outsider_test.md
python experiments/durability_register/failure_register.py selftest
```

## What came out

```
entries 21     rated 19     unrated parts 2      (short by design; a long register is a warning sign)
sections       0: 1   3A MEASURED: 6   3B TRANSPORTED: 8   3C PROJECTED: 6
reconstruction PARTIAL 14   NO 7   YES 0
detection gap  16 of 21 entries have detection_channel NONE or detection_latency UNBOUNDED
projection     33.3% against a stated 35% cap
citations      12 verified this session   22 named from memory and NOT verified
requirements   8 modes with no control at all   11 where the mechanism exists and nothing attaches it
null set       4 modes checked and found already controlled
```

**Nothing scored YES on reconstruction.** Not one entry. The expected-yield note in the work order said PARTIAL
would dominate, and it does, but the absence of a single YES is the sharper result: for this deployment class
there is no failure mode in the register whose retained record is sufficient to identify the object.

**Sixteen of twenty-one entries have no detection channel or an unbounded latency.** That is the work order's
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
F_B  prior art             CHECKED, not redundant, scoped to the residual (above).
F_C  unbounded scope       AUDITED. Full-register audit against the mandatory fields rejects 2 of 21 (9.5%), both
                           already filed as UNRATED PARTS rather than discarded. Author-run, which is the weak
                           case F_G exists to fix.
F_D  projection inflation  33.3% against a 35% cap. Stated in the header. Close enough to the cap that the next
                           projected entry should displace one rather than be added.
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

- **D-203 as-built drift** points at the canary mechanism in `experiments/substrate_pilot_v0/grading_prompt.py`
  (known-answer rows, `check_run` returning PASS / FAIL / SUSPECT, `grader_identity {claimed, verified}`) and at
  the paste duplication caught in the round-3 fixtures, plus `gap_register` GR-0007.
- **D-205 latent fault** points at `experiments/trigger_geometry/` (accumulation under a single-instance
  validation, and absence from the validation set returning ABSENT rather than SAFE).
- **D-206 custody** points at `experiments/substrate_pilot_v0/ledger.py` (signed handover at every boundary,
  presence without custody recorded as an unsigned transfer, custody never moving on a claim).

## Files

```
register.jsonl        the store: header (deployment class, non-goals, event definition, null set, counts) + 21 entries
failure_register.py   validate / audit / report / falsifiers / emit / selftest
REGISTER.md           build product, human emission
outsider_test.md      build product, the F_G test sheet, unrun
```
