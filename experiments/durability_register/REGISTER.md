# Durability and reconstructability failure-mode register

BUILD PRODUCT of `failure_register.py emit`; never hand-edit. The store is `register.jsonl`.

```
artifact      durability and reconstructability failure-mode register for ML components used as infrastructure
deployment class
  STEP 1 FIXED: a model in a decision loop with NO human review of individual outputs, whose outputs are consumed by a downstream process that acts on them. Chosen because it is the narrowest of the work order's two examples that still has a population-scale consequence path, and because the absence of per-output human review is what removes the incidental detection channel a reviewer would have supplied.

NON-GOALS
  - not model behaviour, alignment, or misuse
  - not harm incidents
  - not a code of ethics
  - scope is DURABILITY and RECONSTRUCTABILITY only: can the deployed object still be identified, re-produced, load-rated and inspected at t + N years, by someone who is not the original author and does not hold the tacit stack

entries 21 (rated 19, unrated parts 2) | projected 33.3% of a 35% cap | detection gap 16 entries
reconstruction  NO 7  PARTIAL 14
citations  verified this session 12 | from memory, unverified 22
```

FIDELITY and CUSTODY are separate axes. FIDELITY (is the reported result true of the object produced) and CUSTODY (can the object be identified and re-produced later, by someone else) are separate axes and are not combined in any field. Custody is unmeasured in current practice, which is being read as adequate; an unmeasured variable is not absent, it is set to zero, which is a positive claim nobody licensed.

EVENT DEFINITION (F_H). An EVENT in this register is a bounded change in the RECONSTRUCTION STATE of one identified deployed object: (object id, field that changed, earliest possible date, latest possible date). A silent drift over two years is one event per changed field with wide date bounds. A single wrong output is NOT an event here at all: that is fidelity, which is out of scope. No count of failures appears anywhere in this deliverable; the only counts are counts of ENTRIES.

## Entry 0 - the detection gap itself

### D-000  the detection gap itself

- mechanism: An ML infrastructure failure need not produce an event. Degradation appears as slightly worse decisions distributed across a population, and the population is not instrumented to separate the component's contribution from everything else moving at the same time. With no event there is no dated, located failure, so nothing forces an entry into any register, including this one.
- load condition: any deployment where the component's output is consumed without a per-decision ground truth arriving later on a known clock
- onset: drift | evidence: PROJECTED | reconstruction: NO
- detection channel: NONE
- detection latency: UNBOUNDED
- attribution: the last hop: whoever was holding the output when a decision went wrong
- consequence: the register is incomplete by construction, and the incompleteness is invisible from inside it. Every mode below with detection_channel NONE cannot generate the evidence that would make fixing it mandatory.
- existing control: NONE for the general case. Narrow exceptions exist where a regulator mandates logging (EU AI Act Article 12) or a post-market surveillance duty attaches.
- validity range: deployments without an independent later-arriving ground-truth channel
- minimum artifact that would close it: a detection channel is a deliverable, not an assumption: for each deployed component, name the signal that would reveal degradation and its latency, or record NONE. NONE is a rateable answer; an empty field is not.
- citation [VERIFIED_2026-09-13]: EU AI Act Article 12 (record-keeping) and Article 26 (deployer log retention, at least 6 months) (https://artificialintelligenceact.eu/article/12/)
- note: This entry is PROJECTED and is the register's own load-bearing claim. It is first because every detection_channel NONE below inherits from it.

## 3A MEASURED

### D-101  run-to-run variance exceeds the reported difference

- mechanism: Training under an identical stated configuration produces different objects: seed, data order, non-deterministic kernels and hardware all move the result. A single reported number therefore does not identify the object that was produced, and cannot be used later to check whether the object in front of you is the one that was reported.
- load condition: the deployed object was selected or accepted on a point estimate, and no distribution over identical-configuration runs was recorded
- onset: immediate | evidence: MEASURED | reconstruction: PARTIAL
- detection channel: repeat the training run under the stated configuration and compare the distribution against the reported point
- detection latency: one training budget, if the configuration is complete enough to repeat at all (see D-102)
- attribution: the team that later cannot reproduce the number, who are read as having made an error
- consequence: the identity of the load-bearing object is unestablished at the moment of deployment; no later inspection can tell drift from the variance that was always there
- existing control: PARTIAL: seed recording and multi-seed reporting are standard in some venues, absent in others; no deployment gate requires either
- validity range: stochastic training procedures; does not apply to deterministic fits with a closed-form solution
- minimum artifact that would close it: record the seed, the distribution over at least n identical-configuration runs, and the variance, as part of the as-built. A point estimate without them does not identify an object.
- citation [FROM_MEMORY_UNVERIFIED]: Bouthillier et al., Accounting for Variance in Machine Learning Benchmarks (MLSys 2021)
- citation [FROM_MEMORY_UNVERIFIED]: Henderson et al., Deep Reinforcement Learning That Matters (AAAI 2018)
- citation [FROM_MEMORY_UNVERIFIED]: Dodge et al., Show Your Work: Improved Reporting of Experimental Results (EMNLP 2019)
- citation [FROM_MEMORY_UNVERIFIED]: Reimers and Gurevych, Reporting Score Distributions Makes a Difference (EMNLP 2017)

### D-102  the software stack is not stated, so exact re-execution is impossible in principle

- mechanism: Reports and deployment records omit dependency versions, compiler and driver versions, accelerator model and numeric mode. The omission is not a gap in diligence but a gap in the record FORMAT: there is no field for it, so its absence is not visible as an absence. Re-execution then fails for reasons the record cannot distinguish from a real difference in the method.
- load condition: the deployed object is expected to be rebuildable, and the retained record is a report or a model file rather than a pinned environment
- onset: dormant-until-triggered | evidence: MEASURED | reconstruction: NO
- detection channel: attempt a cold rebuild from the retained record on a machine the author never touched
- detection latency: UNBOUNDED until someone attempts the rebuild; the attempt is usually made years later, by which time the missing versions are no longer obtainable
- attribution: the person attempting the rebuild, who is read as lacking skill
- consequence: the object cannot be reproduced, so it cannot be re-rated, re-inspected, or compared against its own deployed successor
- existing control: PARTIAL: container digests, lockfiles and content-addressed images solve this technically and are widely available; nothing requires their retention past the deployment window
- validity range: any deployment whose retained record is not a pinned, content-addressed environment
- minimum artifact that would close it: deposit the environment, not a description of it: a content-addressed image digest or lockfile set, stored where it outlives the depositing entity.
- citation [FROM_MEMORY_UNVERIFIED]: Gundersen and Kjensmo, State of the Art: Reproducibility in Artificial Intelligence (AAAI 2018)
- citation [FROM_MEMORY_UNVERIFIED]: Pineau et al., Improving Reproducibility in Machine Learning Research (JMLR 2021 / NeurIPS reproducibility program)
- citation [VERIFIED_2026-09-13]: Samuel, Mietchen, Kim, Ahmed, Gaedke, ReproScore: Separating Readiness from Outcome in Research Software Reproducibility Assessment (arXiv 2605.13275, May 2026): 26 readiness sub-metrics over 423 repositories; the environment category is the one that discriminates failure mode (https://arxiv.org/abs/2605.13275)

### D-103  data leakage propagates across fields and survives peer review

- mechanism: Information from the evaluation partition reaches the fitting procedure through a path the report does not describe: temporal ordering, duplicate records, preprocessing applied before the split, or a feature computed over the whole set. The reported number is then true of no object. The defect propagates because downstream work inherits the pipeline, not the check.
- load condition: performance was established on a split whose construction is not recorded in enough detail to audit
- onset: immediate | evidence: MEASURED | reconstruction: PARTIAL
- detection channel: reanalysis with the split reconstructed from the record; where the split cannot be reconstructed, the channel is NONE
- detection latency: years, and only where a reanalyst can obtain the data
- attribution: the field, collectively, after correction; individual attribution rarely lands anywhere
- consequence: claimed superiority over older and cheaper statistical methods evaporates on correction, after the method has already been adopted
- existing control: PARTIAL: leakage taxonomies and model-info sheets are published; no deployment gate requires the split's construction to be recorded
- validity range: supervised fits evaluated on a held-out partition; established in ML-based science, transported to deployment only where the deployment inherits such a fit
- minimum artifact that would close it: record the split construction as a reproducible artifact (the exact partition, or the code and seed that generate it) alongside the number it produced.
- citation [VERIFIED_2026-09-13]: Kapoor and Narayanan, Leakage and the Reproducibility Crisis in ML-based Science (arXiv 2207.07048; Patterns 2023): a taxonomy of 8 leakage types; errors found in 17 fields affecting 329 papers (an earlier version of the same work reports 294; the discrepancy is recorded rather than resolved) (https://arxiv.org/abs/2207.07048)

### D-104  no agreed significance measure, so point estimates ship without a distribution

- mechanism: There is no settled convention for what counts as a difference in reported performance, so numbers are compared directly. A deployment decision is then made on a comparison whose uncertainty was never characterised, and the absence of a characterisation is invisible because no field was left empty.
- load condition: a component was chosen over an alternative on a difference in reported performance
- onset: immediate | evidence: MEASURED | reconstruction: PARTIAL
- detection channel: re-run both arms and compute a distribution; requires the configuration to be complete (D-102)
- detection latency: one training budget per arm, if repeatable
- attribution: nobody: the comparison is treated as settled and the question is not reopened
- consequence: the load-bearing choice between two components rests on a difference that may be inside the noise of either
- existing control: NONE as a gate. Statistical-comparison methods have existed for decades and are not required at deployment.
- validity range: comparative selection decisions; not applicable where only one candidate existed
- minimum artifact that would close it: state the distribution and the comparison procedure with the selection decision, or record the selection as UNRATED.
- citation [FROM_MEMORY_UNVERIFIED]: Demsar, Statistical Comparisons of Classifiers over Multiple Data Sets (JMLR 2006)
- citation [FROM_MEMORY_UNVERIFIED]: Dietterich, Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms (Neural Computation 1998)
- citation [FROM_MEMORY_UNVERIFIED]: Bouthillier et al. 2021 (as D-101)

### D-105  readiness is not outcome: a complete-looking record still does not execute

- mechanism: Static completeness of the retained record (a README, a requirements file, a listed license) is used as the proxy for whether the object can be re-produced. Measured against actual execution, the proxy carries almost no information. The record looks adequate from inside precisely when it is not tested.
- load condition: an organisation judges its own reconstructability by an artifact checklist rather than by attempting a rebuild
- onset: dormant-until-triggered | evidence: MEASURED | reconstruction: PARTIAL
- detection channel: an execution probe: attempt the rebuild in a sandbox that does not contain the author's machine
- detection latency: one rebuild attempt; UNBOUNDED if no attempt is ever scheduled
- attribution: the curator or archivist who reports the artifact as available
- consequence: reconstruction is scored YES on paper and NO in fact; the error is systematically in the reassuring direction
- existing control: PARTIAL: readiness checklists are common; execution probes are rare and need sandbox infrastructure
- validity range: research software artifacts (where it was measured); transported to deployment records by the same mechanism, which is an untested transport
- minimum artifact that would close it: schedule a rebuild attempt as an inspection, on a cadence, from the deposit only. A checklist is not evidence of reconstructability; a successful cold rebuild is.
- citation [VERIFIED_2026-09-13]: ReproScore (arXiv 2605.13275, May 2026): the readiness score exhibits near-zero correlation with binary execution success across 423 repositories, quantifying the readiness-outcome gap (https://arxiv.org/abs/2605.13275)

### D-106  the defect is not visible from reading the report

- mechanism: Every mode above shares one structure: the record format has no field whose emptiness would expose the defect. A reader auditing the report cannot see the missing variance, the missing versions, the unauditable split. Audit therefore returns clean, and the clean return is what makes the enumeration unnecessary-looking.
- load condition: the audit instrument is the deployment record itself
- onset: immediate | evidence: MEASURED | reconstruction: NO
- detection channel: NONE from the record. Only a rebuild attempt or an independent re-measurement reveals it.
- detection latency: UNBOUNDED
- attribution: nobody. A clean audit produces no finding to attribute.
- consequence: the absence of findings is read as the absence of defects, so no forcing function ever forms
- existing control: NONE
- validity range: report and documentation formats that lack provenance fields; a format WITH the fields moves this entry to PARTIAL
- minimum artifact that would close it: add the fields, then treat an empty field as a finding. The register's own schema rule (an entry missing a field is an UNRATED PART, filed as such) is the same mechanism applied to itself.
- citation [VERIFIED_2026-09-13]: the compounding claim of the seed set in the work order, section 3A, final item
- citation [FROM_MEMORY_UNVERIFIED]: Model Cards (Mitchell et al. 2019), Datasheets for Datasets (Gebru et al.), Data Statements (Bender and Friedman 2018), FactSheets (Arnold et al. 2019): documentation templates that add some of the missing fields and are not mandatory anywhere

## 3B TRANSPORTED

### D-201  no retained reference sample

- mechanism: Nothing is kept that the deployed object can later be tested against. When behaviour is questioned at t+N, there is no preserved specimen of the object as deployed and no preserved specimen of the inputs it was rated on, so the question cannot be answered even in principle.
- load condition: any deployment expected to be answerable for its past behaviour
- onset: dormant-until-triggered | evidence: TRANSPORTED | reconstruction: NO
- detection channel: ask for the reference sample. The absence is immediately visible ONCE ASKED, which makes this one of the few modes with a cheap detection channel.
- detection latency: immediate on request; UNBOUNDED if nobody requests it
- attribution: the operator at the time of the question, who cannot produce what was never kept
- consequence: no re-test, no before-and-after comparison, no way to separate a change in the object from a change in the world
- existing control: NONE as a requirement. Model registries can hold artifacts; retention past the product's commercial life is not required anywhere.
- validity range: deployments whose behaviour may be questioned after the deploying team has moved on
- transported from pharmaceutical manufacturing: a retained reference sample of each batch is kept for a defined period so the batch can be re-tested after release
- why it carries: the abstract structure is: an object was released on the strength of a test, and the object itself is not retained, so the test cannot be repeated on the thing that was released. That structure is about the record and the specimen, not about chemistry. It holds identically for weights plus input sample.
- minimum artifact that would close it: a retained reference sample: the exact deployed weights plus a frozen input sample and its outputs, deposited with a stated retention period that exceeds the deployment's expected life.
- citation [FROM_MEMORY_UNVERIFIED]: pharmaceutical retained-sample practice, named as a transport source in the work order section 3B

### D-202  no stamped validity envelope: outside the range the component is UNRATED, not degraded

- mechanism: The input distribution and the decision-consequence range within which performance was established are not recorded on the object. Downstream the component is used outside that range, and the reported performance travels with it as though it still applied. There is no marking that says where the rating stops.
- load condition: the component is reachable by inputs outside the distribution it was measured on, which is the normal case for anything deployed
- onset: immediate | evidence: TRANSPORTED | reconstruction: PARTIAL
- detection channel: compare live input statistics against the recorded rating envelope. Requires the envelope to exist; where it does not, the channel is NONE.
- detection latency: immediate where an envelope exists and inputs are monitored; UNBOUNDED otherwise
- attribution: the operator whose inputs drifted, described as using the tool wrong
- consequence: a component with no applicable rating carries load while being reported as rated. The failure is not that performance degraded; it is that no performance was ever claimed for this condition.
- existing control: PARTIAL: model cards have an intended-use section, unenforced and usually prose. Drift monitoring exists in mature deployments and is compared against training data, not against a stated rating envelope.
- validity range: all deployed components with an input surface
- transported from pressure vessel certification: the vessel carries a stamped plate: certified pressure, temperature, medium. Outside the stamped envelope the certification does not apply and the vessel is uncertified, not merely weaker.
- why it carries: the abstract structure is: a test established a claim under stated conditions, and the claim is transported outside those conditions because the conditions were not attached to the object. Nothing in that depends on steel. The UNRATED/degraded distinction is the part that carries and the part currently missing.
- minimum artifact that would close it: a stamped envelope on the object: input distribution, decision-consequence range, and the date the rating was established. Outside it, the component returns UNRATED rather than a number.
- citation [FROM_MEMORY_UNVERIFIED]: pressure-vessel stamped envelope, named as a transport source in the work order section 3B
- citation [FROM_MEMORY_UNVERIFIED]: Model Cards for Model Reporting (Mitchell et al., FAT* 2019): intended use and out-of-scope sections

### D-203  as-built drift: the deployed object diverges from the documented one

- mechanism: Updates, patches, fine-tunes, prompt changes, retrievals, and silent substitution of a served model move the deployed object away from the documented one, with no record that a change occurred. The documentation continues to describe an object that is no longer in the load path.
- load condition: the served object can be changed without a record being written, which is the default for hosted endpoints
- onset: drift | evidence: TRANSPORTED | reconstruction: NO
- detection channel: a known-answer probe on a fixed schedule: a canary set whose answers are recorded, re-run against the live endpoint. A grader or endpoint that fails a canary it previously passed is the signal.
- detection latency: one probe interval, IF a canary set exists; UNBOUNDED without one
- attribution: the downstream user who notices results changed, attributed to their own pipeline
- consequence: the as-built record no longer identifies the load-bearing object; every claim referencing it is about a different thing
- existing control: PARTIAL: version pinning where an API exposes versions; FDA PCCP requires a pre-authorised modification protocol for AI-enabled device software, which is the closest existing forcing function and covers only that sector
- validity range: hosted or updatable components; not applicable to a frozen artifact shipped once and never patched
- transported from structural and civil engineering: as-built drawings, and the treatment of undocumented field modification as a defect in its own right, independent of whether the modification was an improvement
- why it carries: the abstract structure is: the object in service differs from the record of the object, and the difference is undocumented. The civil case is load-bearing steel and this case is a served model; the record insufficiency is identical.
- minimum artifact that would close it: a change record per served object plus a canary set with recorded answers and a probe cadence. The canary mechanism already exists in this repository; adopt it rather than re-deriving it.
- cross-reference (not re-derived): experiments/gap_register/REGISTER.jsonl GR-0007 (instrument stability of results collected through a hosted model; OPEN in language_model_evaluation); experiments/substrate_pilot_v0/grading_prompt.py (canary rows, check_run -> PASS | FAIL | SUSPECT; grader_identity {claimed, verified}); experiments/substrate_pilot_v0/fixtures/maria_locus_round3_results.jsonl (a paste duplication found by comparing two graders' outputs byte for byte)
- citation [VERIFIED_2026-09-13]: FDA, Marketing Submission Recommendations for a Predetermined Change Control Plan for Artificial Intelligence-Enabled Device Software Functions, final guidance 2024-12-03: a PCCP states the planned modifications, the protocol to validate them, and an impact assessment (https://www.fda.gov/regulatory-information/search-fda-guidance-documents/marketing-submission-recommendations-predetermined-change-control-plan-artificial-intelligence)
- citation [VERIFIED_2026-09-13]: silent model routing, cross-referenced rather than re-derived (work order section 5)

### D-204  no configuration control and no part traceability for the stack

- mechanism: The deployed system is an assembly: weights, tokeniser, preprocessing, retrieval index, prompt template, serving runtime, hardware. No part carries an identity that is recorded at assembly time, so the assembly cannot be enumerated later. Changing one part changes the object with no trace.
- load condition: more than one part can change independently, which is every real deployment
- onset: drift | evidence: TRANSPORTED | reconstruction: PARTIAL
- detection channel: a bill of materials diff between two dates. Requires a bill of materials to have been recorded at both.
- detection latency: one diff interval where a bill of materials exists; UNBOUNDED otherwise
- attribution: whoever last touched any part, usually the most recent committer
- consequence: no part can be recalled, because no record says which assemblies contain it
- existing control: PARTIAL: SBOM practice, content-addressed images and model registries provide the mechanism; no requirement attaches it to a deployed ML assembly, and the non-code parts (index, prompt, preprocessing) are usually outside the SBOM's scope
- validity range: composed deployments; a single self-contained binary is a different case
- transported from aviation maintenance: configuration control and part traceability: every part carries a number and a history, and the aircraft's configuration is a record, so a defective part can be traced to every airframe holding it
- why it carries: the abstract structure is: a composed object whose composition is not recorded cannot be re-composed or recalled. The parts here are digital, and digital parts have cheaper identity (content addressing) than physical ones, which makes the absence of the record harder to excuse rather than easier.
- minimum artifact that would close it: a bill of materials for the assembly, content-addressed per part, recorded at deploy time, with the non-code parts (index, prompt, preprocessing, tokeniser) in scope.
- citation [FROM_MEMORY_UNVERIFIED]: aviation configuration control and part traceability, named as a transport source in the work order section 3B
- citation [FROM_MEMORY_UNVERIFIED]: SBOM practice (NTIA minimum elements; SPDX and CycloneDX), reproducible builds, SLSA provenance levels

### D-205  latent fault dormant until an unusual load combination

- mechanism: A defect is present from the start and produces no signal because the input combination that expresses it does not occur during validation. Validation ran the geometry it could construct; the deployment meets combinations nobody enumerated, including repeated or accumulating ones.
- load condition: the validation set was a single instance or a sampled set, and the deployment sees repeated, compounding, or reversing input sequences
- onset: dormant-until-triggered | evidence: TRANSPORTED | reconstruction: PARTIAL
- detection channel: a combination or sequence probe designed from the geometry the deployment actually operates in, not from the validation distribution
- detection latency: UNBOUNDED: the latency is the waiting time for the triggering combination, which is unknown by construction
- attribution: the operator present when it finally expresses, described as an unusual case
- consequence: a fault that was always there is recorded as a new event, so the record of when it entered service is wrong
- existing control: NONE as a requirement. Red-teaming and adversarial evaluation exist and are not envelope-scoped.
- validity range: deployments whose input sequences can repeat or accumulate; a single-shot stateless call is a weaker case
- transported from aviation (latent failure conditions; the dormancy interval in certification analysis): latent faults are enumerated explicitly, and inspection intervals are set by the dormancy period rather than by the fault's likelihood alone
- why it carries: the abstract structure is: a defect exists before it is expressed, and the validating test's envelope did not contain the expressing condition. The mechanism is about the relation between a validation envelope and an operating envelope, which is not physical.
- minimum artifact that would close it: state the validation envelope's instance count and sequence structure, and mark any operating geometry absent from it as ABSENT rather than safe. The check exists in this repository already.
- cross-reference (not re-derived): experiments/trigger_geometry/ (T1_ACCUMULATION: a response validated on a single instance, operated in a reversing geometry; T6_GEOMETRY_ABSENT: absence from the validation set returns ABSENT, never SAFE)
- citation [FROM_MEMORY_UNVERIFIED]: aviation latent-fault enumeration, named as a transport source in the work order section 3B

### D-206  custody breaks at every handoff and no handoff is documented

- mechanism: An object moves between teams, vendors, acquisitions and repositories. Each move is an opportunity to lose the environment, the data pointer, the rating envelope or the deposit itself, and no move is recorded as a handoff with a named holder on both sides. Presence in a registry is read as custody.
- load condition: the object outlives the team that produced it, or crosses an organisational boundary
- onset: drift | evidence: TRANSPORTED | reconstruction: NO
- detection channel: a custody audit: for each boundary crossing, is there a signed record naming the holder before and after
- detection latency: immediate on audit; UNBOUNDED because the audit is not scheduled anywhere
- attribution: the current holder, who inherited an object with no history and is asked to account for it
- consequence: the object is present and unidentifiable: it cannot be tied back to the record that rated it
- existing control: PARTIAL: registries record uploads; acquisitions and vendor changes are not handoff events anywhere in ML practice
- validity range: objects that cross a team or organisational boundary at least once
- transported from nuclear material transport: continuous custody with a documented handoff at every stop; custody never moves on a claim, only on a signed transfer
- why it carries: the abstract structure is: an object's identity is only as good as the chain of recorded transfers behind it, and an unsigned transfer breaks the chain whether or not the object is physically intact. Nothing in that requires radioactivity.
- minimum artifact that would close it: a signed handover record at every boundary: named holder before, named holder after, date, and what was transferred (weights, environment, data pointer, rating envelope, reference sample).
- cross-reference (not re-derived): experiments/substrate_pilot_v0/ledger.py (signed handover at every boundary; presence without custody is recorded as UNSIGNED_TRANSFER; a competing claim routes to a resolver and custody never moves on the claim)
- citation [FROM_MEMORY_UNVERIFIED]: nuclear-transport custody practice, named as a transport source in the work order section 3B

### D-207  format obsolescence: the object survives and the reader does not

- mechanism: Weights are retained in a serialisation format that depends on a specific library version to load, and on a runtime that depends on a driver that depends on hardware. The bytes persist; the ability to interpret them expires. This is the one mode where the object IS retained, which is why it is recoverable in principle and why its neglect is cheapest to fix.
- load condition: retention is planned in years while the loader's support horizon is months
- onset: dormant-until-triggered | evidence: TRANSPORTED | reconstruction: PARTIAL
- detection channel: a scheduled load test of the deposit on a current runtime
- detection latency: one test interval; UNBOUNDED if never scheduled, and the discovery point is usually the moment the object is needed
- attribution: the archivist or the successor team, who are read as having lost the file they in fact still hold
- consequence: a retained deposit that cannot be executed is a record of an object, not the object
- existing control: PARTIAL: open exchange formats and framework-independent serialisations exist; migration of deposits on a schedule is not practised
- validity range: any deposit intended to outlive its framework's support window
- transported from digital archives and civil records: format obsolescence is a named preservation risk; formats are migrated on a schedule and independent-of-reader representations are preferred
- why it carries: the abstract structure is: retention of bytes is not retention of the object when interpretation requires an artifact that is not retained. The mechanism is about the dependency between a record and its reader.
- minimum artifact that would close it: store the deposit in a reader-independent representation where one exists, and schedule a load test plus migration decision on an interval shorter than the framework's support horizon.
- citation [FROM_MEMORY_UNVERIFIED]: OAIS reference model (ISO 14721) and digital-preservation format-obsolescence practice

### D-208  no inspection interval and no action threshold

- mechanism: Nothing states when the component is re-measured, against what, or what happens at what result. Monitoring, where it exists, watches inputs and system health rather than re-rating the component against a held reference, and no threshold is bound to an action.
- load condition: the component stays in service across changes in its input population
- onset: drift | evidence: TRANSPORTED | reconstruction: PARTIAL
- detection channel: the inspection itself. Absent an interval, there is no channel: the mode is defined by the channel's absence.
- detection latency: UNBOUNDED
- attribution: the operator who eventually reports worse outcomes, without a baseline to compare against
- consequence: degradation accumulates with no point at which anyone is obliged to look
- existing control: PARTIAL: production ML monitoring is common in mature organisations; a mandated interval with a pre-committed action threshold is not standard, and EU AI Act post-market monitoring is the nearest requirement in the sectors it covers
- validity range: components in sustained service; not applicable to a one-shot analysis
- transported from structural inspection regimes (bridge inspection intervals): a mandated interval, a defined inspection, a rating, and an action threshold tied to the rating
- why it carries: the abstract structure is: a component under sustained load with no scheduled re-measurement and no pre-committed action threshold. The load is decisions rather than traffic; the scheduling gap is identical.
- minimum artifact that would close it: an inspection interval, a held reference set that the component was never fitted on, a re-measurement procedure, and an action threshold stated before the first inspection.
- citation [FROM_MEMORY_UNVERIFIED]: bridge inspection intervals, named as a transport source in the work order section 3B
- citation [VERIFIED_2026-09-13]: EU AI Act post-market monitoring and Article 12 logging (https://artificialintelligenceact.eu/article/12/)

## 3C PROJECTED and UNRATED PARTS

### D-301  the reconstruction path runs through a single commercial entity

- mechanism: Everything needed to rebuild the object (weights, data, environment, the endpoint itself) sits inside one firm, behind a boundary engineered to be impermeable, where impermeability is the asset. Transmission is actively prevented rather than merely neglected, so the loss timescale is set by corporate events (a fold, an acquisition, a strategy change) rather than by decay.
- load condition: any deployment whose rebuild would require artifacts held only by a vendor
- onset: dormant-until-triggered | evidence: PROJECTED | reconstruction: NO
- detection channel: NONE. The absence of the artifacts is not observable from outside the boundary, and inside it the artifacts are present until the moment they are not.
- detection latency: UNBOUNDED (by the rule in the work order section 6)
- attribution: the customer, at the moment of discontinuation, described as having chosen a vendor badly
- consequence: reconstruction is NO by default, and the default is invisible while the vendor is healthy
- existing control: NONE. Escrow arrangements exist in other software sectors and are not standard for models.
- validity range: vendor-hosted or vendor-trained components; not applicable where the operator holds weights, data and environment
- minimum artifact that would close it: an escrow deposit outside the vendor, or an explicit recorded acceptance that reconstruction is NO. The second is cheap and is currently made by silence rather than by decision.
- citation [VERIFIED_2026-09-13]: the proprietary-boundary custody term, work order section 6

### D-302  what was excluded from the training data is not recorded

- mechanism: Material provenance records what went in, at best. What was filtered, deduplicated, down-weighted or declined is not recorded, so the object's blind regions cannot be enumerated later and the filter cannot be re-applied when rebuilding. Two rebuilds with the same included set and different exclusions are different objects that document identically.
- load condition: the training corpus passed through any filtering step, which is universal at scale
- onset: immediate | evidence: PROJECTED | reconstruction: PARTIAL
- detection channel: NONE from the record. A behavioural probe can find a blind region without ever establishing that an exclusion caused it.
- detection latency: UNBOUNDED
- attribution: the downstream user who hits the blind region, attributed to their unusual input
- consequence: material provenance is incomplete in a way that prevents rebuild and prevents rating the object's coverage
- existing control: NONE. Datasheets ask about collection and curation; exclusion records are not required or typically kept as re-appliable artifacts.
- validity range: filtered corpora; not applicable to a fully enumerated small dataset
- minimum artifact that would close it: retain the exclusion filters as executable artifacts with the corpus pointer, so the same corpus plus the same filters is a reproducible input.
- citation [VERIFIED_2026-09-13]: walked backwards from the reconstruction field per work order section 3C; anchored only by the material-provenance definition in section 5

### D-303  the deployed object is the pipeline, and only the model is versioned

- mechanism: Preprocessing, tokenisation, retrieval contents, prompt templates and post-processing all sit in the load path and change on their own schedules. Versioning is applied to the weights, so the record tracks the part that changed least. The object that made the decision is never the object that was recorded.
- load condition: the component is wrapped by any transformation that can change independently of the weights
- onset: drift | evidence: PROJECTED | reconstruction: PARTIAL
- detection channel: a fixed-input, fixed-expected-output probe through the WHOLE pipeline rather than against the model alone
- detection latency: one probe interval where such a probe exists; NONE and UNBOUNDED where monitoring targets the model in isolation
- attribution: the model team, whose weights did not change
- consequence: a change with real decision consequences is invisible in the version record
- existing control: PARTIAL: pipeline versioning is possible and practised unevenly; retrieval corpus state is rarely versioned at all
- validity range: pipelines with independently mutable stages
- minimum artifact that would close it: version the assembly, not the model: one identifier covering weights, preprocessing, retrieval state, prompt and post-processing, recorded per decision batch.
- citation [VERIFIED_2026-09-13]: walked backwards from the reconstruction field per work order section 3C
- citation [FROM_MEMORY_UNVERIFIED]: Sculley et al., Hidden Technical Debt in Machine Learning Systems (NeurIPS 2015): changing anything changes everything, entanglement, undeclared consumers, configuration debt

### D-304  the inspection reference stops being held-out

- mechanism: The reference set used for re-measurement leaks into training, tuning or selection over time, through reuse, contamination from a crawled corpus, or simple accumulation of decisions made against it. The inspection instrument then reports a healthy component because the component has seen the exam.
- load condition: an inspection regime exists and uses a reference set that is reused across intervals
- onset: drift | evidence: PROJECTED | reconstruction: PARTIAL
- detection channel: NONE for the contamination itself once it has happened; a fresh reference set built after the fact can detect the discrepancy without dating it
- detection latency: UNBOUNDED
- attribution: nobody: the inspection is passing
- consequence: the one control that would catch the other modes degrades silently, and its degradation is in the reassuring direction
- existing control: NONE as a requirement. Benchmark-contamination work exists in evaluation research; inspection reference custody is not a practice.
- validity range: reused reference sets; not applicable where a fresh set is drawn per inspection and its provenance is recorded
- minimum artifact that would close it: custody rules for the reference set: sealed, dated, never in a training or selection path, with a replacement schedule and a record of each use.
- citation [VERIFIED_2026-09-13]: walked backwards from the inspection-interval requirement per work order section 3C

### D-401  numeric non-determinism across accelerator generations  [UNRATED PART]

- mechanism: The same weights and the same inputs produce different outputs across accelerator generations, library kernels and numeric modes, so 'the same object' is not well defined across hardware migrations.
- load condition: the deployment migrates hardware during the component's service life
- onset: dormant-until-triggered | evidence: PROJECTED | reconstruction: PARTIAL
- detection channel: EMPTY (unrated part)
- detection latency: EMPTY (unrated part)
- attribution: the platform team performing the migration
- consequence: a bit-exact reconstruction test fails for reasons unrelated to the record's completeness, so the reconstruction score itself becomes ambiguous
- existing control: EMPTY (unrated part)
- validity range: EMPTY (unrated part)
- citation [FROM_MEMORY_UNVERIFIED]: no source located this session
- note: Filed as an UNRATED PART, not discarded (schema rule, section 2). detection_channel, detection_latency, existing_control, validity_range and requirement are left EMPTY because the executor cannot state them without measurement. Empty is distinct from NONE: NONE is a finding, empty is an unfinished entry.

### D-402  the component changes the distribution it is rated on  [UNRATED PART]

- mechanism: Decisions made by the component alter the population that generates its future inputs, so the rating envelope moves as a function of the component's own operation rather than of anything external.
- load condition: the component's outputs influence the process that produces its inputs
- onset: drift | evidence: PROJECTED | reconstruction: PARTIAL
- detection channel: EMPTY (unrated part)
- detection latency: EMPTY (unrated part)
- attribution: unclear: the operator, the population, or the component, with no record that separates them
- consequence: an inspection against a fixed reference cannot distinguish a component that drifted from a world the component moved
- existing control: EMPTY (unrated part)
- validity range: EMPTY (unrated part)
- citation [FROM_MEMORY_UNVERIFIED]: performative prediction and feedback-loop literature, not located this session
- note: Filed as an UNRATED PART. The executor cannot state a detection channel that separates the component's contribution from the population's movement, and will not invent one.

## Requirement set (step 6)

Modes with no existing control, and the minimum artifact that would close each:

- **D-000 the detection gap itself** -> a detection channel is a deliverable, not an assumption: for each deployed component, name the signal that would reveal degradation and its latency, or record NONE. NONE is a rateable answer; an empty field is not.
- **D-104 no agreed significance measure, so point estimates ship without a distribution** -> state the distribution and the comparison procedure with the selection decision, or record the selection as UNRATED.
- **D-106 the defect is not visible from reading the report** -> add the fields, then treat an empty field as a finding. The register's own schema rule (an entry missing a field is an UNRATED PART, filed as such) is the same mechanism applied to itself.
- **D-201 no retained reference sample** -> a retained reference sample: the exact deployed weights plus a frozen input sample and its outputs, deposited with a stated retention period that exceeds the deployment's expected life.
- **D-205 latent fault dormant until an unusual load combination** -> state the validation envelope's instance count and sequence structure, and mark any operating geometry absent from it as ABSENT rather than safe. The check exists in this repository already.
- **D-301 the reconstruction path runs through a single commercial entity** -> an escrow deposit outside the vendor, or an explicit recorded acceptance that reconstruction is NO. The second is cheap and is currently made by silence rather than by decision.
- **D-302 what was excluded from the training data is not recorded** -> retain the exclusion filters as executable artifacts with the corpus pointer, so the same corpus plus the same filters is a reproducible input.
- **D-304 the inspection reference stops being held-out** -> custody rules for the reference set: sealed, dated, never in a training or selection path, with a replacement schedule and a record of each use.

Modes with a partial control, where the mechanism exists and nothing attaches it:

- **D-101 run-to-run variance exceeds the reported difference** -> record the seed, the distribution over at least n identical-configuration runs, and the variance, as part of the as-built. A point estimate without them does not identify an object.
- **D-102 the software stack is not stated, so exact re-execution is impossible in principle** -> deposit the environment, not a description of it: a content-addressed image digest or lockfile set, stored where it outlives the depositing entity.
- **D-103 data leakage propagates across fields and survives peer review** -> record the split construction as a reproducible artifact (the exact partition, or the code and seed that generate it) alongside the number it produced.
- **D-105 readiness is not outcome: a complete-looking record still does not execute** -> schedule a rebuild attempt as an inspection, on a cadence, from the deposit only. A checklist is not evidence of reconstructability; a successful cold rebuild is.
- **D-202 no stamped validity envelope: outside the range the component is UNRATED, not degraded** -> a stamped envelope on the object: input distribution, decision-consequence range, and the date the rating was established. Outside it, the component returns UNRATED rather than a number.
- **D-203 as-built drift: the deployed object diverges from the documented one** -> a change record per served object plus a canary set with recorded answers and a probe cadence. The canary mechanism already exists in this repository; adopt it rather than re-deriving it.
- **D-204 no configuration control and no part traceability for the stack** -> a bill of materials for the assembly, content-addressed per part, recorded at deploy time, with the non-code parts (index, prompt, preprocessing, tokeniser) in scope.
- **D-206 custody breaks at every handoff and no handoff is documented** -> a signed handover record at every boundary: named holder before, named holder after, date, and what was transferred (weights, environment, data pointer, rating envelope, reference sample).
- **D-207 format obsolescence: the object survives and the reader does not** -> store the deposit in a reader-independent representation where one exists, and schedule a load test plus migration decision on an interval shorter than the framework's support horizon.
- **D-208 no inspection interval and no action threshold** -> an inspection interval, a held reference set that the component was never fitted on, a re-measurement procedure, and an action threshold stated before the first inspection.
- **D-303 the deployed object is the pipeline, and only the model is versioned** -> version the assembly, not the model: one identifier covering weights, preprocessing, retrieval state, prompt and post-processing, recorded per decision batch.

## Null set (step 7): modes checked and found already controlled

- **N-01** storage-level corruption of a retained deposit (bit rot, partial write, silent truncation)
    - content addressing and checksums detect it cheaply, are built into standard object stores and model registries, and are used by default rather than by decision (CONTROLLED, mechanism default-on)
    - residual: detection requires the deposit to exist; this entry says nothing about whether one was made (see D-201)
- **N-02** identity of the source code at a point in time
    - content-addressed version control gives every tree an identity, and commit hashes are recorded as a side effect of normal work (CONTROLLED where version control is used)
    - residual: the hash identifies the code and not the environment it ran in (D-102) or the data it read (D-302)
- **N-03** identity of a container or runtime image
    - OCI image digests are content-addressed and are produced automatically by the build; pinning by digest rather than tag is a one-line practice (CONTROLLED, mechanism available and cheap)
    - residual: retention of the image past the deployment window is not covered by the digest
- **N-04** recording that a use of a high-risk system occurred, in the sectors the EU AI Act covers
    - Article 12 mandates automatic logging over the system's lifetime and Article 26 obliges deployers to retain logs; this is an actual forcing function, not a recommendation (CONTROLLED BY REGULATION, within scope only)
    - residual: the minimum deployer retention is six months, which is shorter than any reconstruction question this register asks, and the scope is the Act's high-risk categories rather than deployed ML generally

## Headline

PARTIAL is the modal score (14 of 21): enough of the record exists to rebuild something approximate, not enough to identify the object. PARTIAL looks like adequacy from inside, which is why it is the class most likely to be under-reported.

