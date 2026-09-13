# F_G reader-precondition test (NOT RUN)

Hand this to someone outside the domain. They classify each of the five entries on the four fields below,
using only the definitions given. Disagreement with the register's own classification means the FIELD
DEFINITION is underspecified, and the definition is what gets fixed, not the reader.

Status: NOT RUN. the test requires a reader outside the domain, who is not available to this session. Running it on the author would reproduce exactly the blindness it tests for.

## Field definitions, as they must stand without asking the author

- **onset**: immediate (present from the moment of deployment) | drift (accumulates while in service) | dormant-until-triggered (present from the start, expresses only on a particular condition)
- **detection channel**: the signal that would reveal this, or NONE if no signal would. NONE is an answer.
- **reconstruction**: YES (the object can be rebuilt and identified from the retained record) | PARTIAL (something approximate can be rebuilt; the object cannot be identified) | NO
- **evidence class**: MEASURED (a study established it) | TRANSPORTED (the mechanism is established in another domain and the abstract structure carries) | PROJECTED (no anchor)

## Known-weak definitions (the reader is not told these in advance)

- onset: 'drift' versus 'dormant-until-triggered' is a judgement call on any mode that both accumulates and needs a trigger (D-203, D-205)
- reconstruction PARTIAL versus NO: the boundary is 'approximately rebuild' versus 'identify', which is stated in the header and not operationalised
- existing_control PARTIAL: means the mechanism exists somewhere, not that this deployment uses it

## Entries to classify

### D-102

mechanism: Reports and deployment records omit dependency versions, compiler and driver versions, accelerator model and numeric mode. The omission is not a gap in diligence but a gap in the record FORMAT: there is no field for it, so its absence is not visible as an absence. Re-execution then fails for reasons the record cannot distinguish from a real difference in the method.

load condition: the deployed object is expected to be rebuildable, and the retained record is a report or a model file rather than a pinned environment

consequence: the object cannot be reproduced, so it cannot be re-rated, re-inspected, or compared against its own deployed successor

onset: ______  detection channel: ______  reconstruction: ______  evidence class: ______

### D-202

mechanism: The input distribution and the decision-consequence range within which performance was established are not recorded on the object. Downstream the component is used outside that range, and the reported performance travels with it as though it still applied. There is no marking that says where the rating stops.

load condition: the component is reachable by inputs outside the distribution it was measured on, which is the normal case for anything deployed

consequence: a component with no applicable rating carries load while being reported as rated. The failure is not that performance degraded; it is that no performance was ever claimed for this condition.

onset: ______  detection channel: ______  reconstruction: ______  evidence class: ______

### D-203

mechanism: Updates, patches, fine-tunes, prompt changes, retrievals, and silent substitution of a served model move the deployed object away from the documented one, with no record that a change occurred. The documentation continues to describe an object that is no longer in the load path.

load condition: the served object can be changed without a record being written, which is the default for hosted endpoints

consequence: the as-built record no longer identifies the load-bearing object; every claim referencing it is about a different thing

onset: ______  detection channel: ______  reconstruction: ______  evidence class: ______

### D-302

mechanism: Material provenance records what went in, at best. What was filtered, deduplicated, down-weighted or declined is not recorded, so the object's blind regions cannot be enumerated later and the filter cannot be re-applied when rebuilding. Two rebuilds with the same included set and different exclusions are different objects that document identically.

load condition: the training corpus passed through any filtering step, which is universal at scale

consequence: material provenance is incomplete in a way that prevents rebuild and prevents rating the object's coverage

onset: ______  detection channel: ______  reconstruction: ______  evidence class: ______

### D-401

mechanism: The same weights and the same inputs produce different outputs across accelerator generations, library kernels and numeric modes, so 'the same object' is not well defined across hardware migrations.

load condition: the deployment migrates hardware during the component's service life

consequence: a bit-exact reconstruction test fails for reasons unrelated to the record's completeness, so the reconstruction score itself becomes ambiguous

onset: ______  detection channel: ______  reconstruction: ______  evidence class: ______

