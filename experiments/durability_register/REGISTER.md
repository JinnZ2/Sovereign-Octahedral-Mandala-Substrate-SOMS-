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

entries 37 (rated 35, unrated parts 2) | projected 32.4% of a 35% cap | detection gap 29 entries
reconstruction  NO 17  NOT_APPLICABLE 4  PARTIAL 16
citations  verified this session 36 | from memory, unverified 23
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

## 3B-W WORKED ENTRIES - the two priority transports and the failure modes of their controls

### DUR-001  the deployed object cannot be distinguished from another produced by the same nominal procedure

- mechanism: Deployed object cannot be distinguished from any other object produced by the same nominal procedure. Run-to-run variance under identical configuration is large enough that the reported number does not identify which object was produced; after deployment, substitution, patching or drift leaves no trace distinguishing the current object from the documented one.
- load condition: Any deployment where the object is updated, re-served, migrated or supplied by a party other than the evaluator.
- onset: dormant-until-triggered | evidence: TRANSPORTED | reconstruction: NO
- detection channel: NONE under current practice. PROPOSED: sealed probe-response record - a probe set fixed at deploy, the deployed object's responses to it, hashed, held by a party that is not the operator. Third-party checkable without re-manufacture.
- detection latency: UNBOUNDED without the control. With the control: one probe cycle.
- attribution: Last hop. Lands on whoever was holding the output when the behaviour changed.
- consequence: Any later claim about the deployed object is unverifiable. Silent substitution, undeclared update and as-built drift are all indistinguishable from normal operation.
- existing control: NONE.
- validity range: Holds where the object is served through an interface that can be queried. Does not hold for objects embedded such that probe queries are indistinguishable from production load, or where probe cost is not small relative to serving cost.
- transported from pharmaceutical manufacturing (retained reference sample): a small physical referent of each batch is retained before any problem is known, cheap relative to the batch, and testable by a third party without re-manufacture
- why it carries: the abstract structure is a record insufficient to identify the object it describes, closed by retaining a small referent taken BEFORE any problem is known, cheap relative to the batch, and testable by a third party without re-manufacture. All three properties carry to a probe-response record. This is not resemblance between industries; it is the same insufficiency and the same closure.
- reconstruction note: NO as deployed. PARTIAL with the control - the control establishes IDENTITY, not reproducibility (see DUR-001-N2).
- PROPOSED control: sealed probe-response record: probe set fixed at deploy, responses hashed, custody with a party that is not the operator, checkable by a third party without re-manufacture
- control precondition: probe leakage: the probe set must rotate, or be generated per deployment from a seed held by the third party (entry DUR-001-N1)
- control precondition: identity is not procedure reproducibility: this control closes identity only (entry DUR-001-N2)
- coupled with: DUR-002 (neither control works alone)
- supersedes: D-201 (operator-supplied worked entry, section 3B-W)
- minimum artifact that would close it: a sealed probe-response record at deploy: probe set, responses, hash, deposited with a party that is not the operator, with a stated retention period and a rotation rule.
- cross-reference (not re-derived): D-101, D-102 (the measured insufficiency this transport closes); D-203 (as-built drift: the change record; DUR-001 is the identity referent, and neither substitutes for the other); experiments/substrate_pilot_v0/grading_prompt.py (canary rows held with recorded answers: the same construction at grader scale, already built in this repository)
- citation [VERIFIED_2026-09-13]: operator work order section 3B-W, entry DUR-001, filled to schema by the operator
- citation [VERIFIED_2026-09-13]: insufficiency anchored by D-101 (run-to-run variance) and D-102 (unstated stack)

### DUR-001-N1  probe leakage: the identity control is trained against and stops measuring identity

- mechanism: A probe set that becomes public, or is reused across deployments, gets trained against. The probe record then measures probe performance rather than object identity, and continues to return matches while no longer discriminating. Sealing and hashing handle single-deployment identity; they do not handle reuse across deployments.
- load condition: the probe set is reused across deployments, or is reachable by the training pipeline of any object it will later identify
- onset: drift | evidence: MEASURED | reconstruction: NOT_APPLICABLE
- detection channel: overlap testing between the probe set and the training corpus (n-gram or character overlap, as used in decontamination practice) where the corpus is available; NONE where it is not, which is the normal case for a vendor-trained object
- detection latency: one overlap test where the corpus is available; UNBOUNDED otherwise, and the loss of discriminative power is silent either way
- attribution: the third party holding the probe record, whose control is reported as working
- consequence: the identity control fails silently, and every DUR-001 claim resting on it becomes unverifiable without any signal that this happened
- existing control: PARTIAL. Decontamination practice exists in evaluation: the GPT-3 report defines a 13-gram overlap and the GPT-4 report a 50-character overlap as contamination. Nothing applies it to a probe set used for identity.
- validity range: probe sets that persist across deployments or are publishable; does not apply to a probe set generated per deployment from a seed that never leaves the third party
- reconstruction note: governs the DUR-001 control rather than the object's record; scoring a rebuild here would misattribute the control's failure to the deposit
- minimum artifact that would close it: rotation, or per-deployment probe generation from a seed held by the third party, stated as a precondition of the DUR-001 control rather than as a caveat on it.
- cross-reference (not re-derived): D-304 (the inspection reference stops being held-out: the same mechanism attacking the inspection instrument rather than the identity control)
- citation [VERIFIED_2026-09-13]: A Survey on Data Contamination for Large Language Models (arXiv 2502.14425): reports that over 16 percent of MMLU samples were flagged as contaminated in the LLaMA-2 report, and over 90 percent of examples in QuAC, SQuADv2 and DROP in the GPT-3 study; contamination thresholds are 13-gram overlap (GPT-3) and 50-character overlap (GPT-4). Figures read from the survey, which is a SECONDARY source for each underlying report. (https://arxiv.org/html/2502.14425v2)
- citation [VERIFIED_2026-09-13]: Rethinking Benchmark and Contamination for Language Models with Rephrased Samples (arXiv 2311.04850): rephrased test samples evade n-gram decontamination (https://arxiv.org/pdf/2311.04850)

### DUR-001-N2  instance identity is not procedure reproducibility, and the two must not be summed

- mechanism: Given run-to-run variance, a probe response identifies the DEPLOYED INSTANCE. It does not establish that the training procedure reproduces that instance. Treating the identity control as reconstruction coverage lets a deployment claim a rebuild capability it does not have, because the two claims are about different objects: this one, and any one the procedure would produce.
- load condition: an identity control exists (DUR-001) and is reported as satisfying a reconstruction requirement
- onset: immediate | evidence: MEASURED | reconstruction: PARTIAL
- detection channel: re-run the procedure and probe the new instance against the sealed record. A mismatch is the EXPECTED result and is evidence about the procedure, not evidence of substitution; reading it as substitution is the second half of this failure.
- detection latency: one training budget, and only where the procedure is complete enough to re-run at all (D-102)
- attribution: nobody: the two claims are reported together and the gap between them is not a finding anywhere
- consequence: reconstruction is scored on identity evidence, so the register's own headline distribution would read better than the deployment warrants
- existing control: NONE. No practice separates an identity rating from a procedure-reproducibility rating.
- validity range: stochastic training procedures, which is where DUR-001 is needed in the first place
- reconstruction note: identity is closable by DUR-001; procedure reproducibility is carried by D-101 and D-102 and remains open
- minimum artifact that would close it: two separate ratings recorded separately and never summed into one reconstruction score: IDENTITY (closed by DUR-001) and PROCEDURE REPRODUCIBILITY (carried by D-101 and D-102, open).
- cross-reference (not re-derived): D-101 (run-to-run variance: the measured reason instance and procedure come apart); D-102 (unstated stack: the reason the procedure often cannot be re-run at all)
- citation [VERIFIED_2026-09-13]: operator work order section 3B-W, DUR-001-N2, which states that procedure reproducibility needs its own entry
- citation [FROM_MEMORY_UNVERIFIED]: run-to-run variance anchors inherited from D-101 (Bouthillier et al. 2021; Henderson et al. 2018; Dodge et al. 2019; Reimers and Gurevych 2017), unverified as recorded there

### DUR-002  the object is used outside the conditions its rating was established on, with no signal

- mechanism: Object is applied outside the conditions under which its reported performance was established, with no signal that this has occurred. The stated conditions, where they exist at all, are filed in a document elsewhere rather than attached to the object at point of use, so the operator applying load cannot read the rating.
- load condition: Any deployment where input distribution or decision consequence can vary after evaluation. In practice: all of them.
- onset: drift | evidence: TRANSPORTED | reconstruction: NOT_APPLICABLE
- detection channel: NONE under current practice. Confidence scores do not serve - a confident output inside a distribution the object was never characterised on is the failure, not a warning of it. PROPOSED: stamped validity envelope attached to the serving interface, machine-readable, carrying characterised input distribution, decision consequence range, date, and seed/variance basis. Plus a RETURN CONTRACT: the interface returns value AND rating status, where OUT_OF_ENVELOPE is a distinct return state, not a low score on a continuous confidence axis.
- detection latency: UNBOUNDED without the control. With it: immediate at call time.
- attribution: Last hop, again - the operator who acted on the out-of-envelope output.
- consequence: The system continues returning values while UNRATED. Under load, with no record that the envelope was exceeded or that a criterion was selected in the absence of one.
- existing control: PARTIAL. Model cards and documentation exist, but are filed alongside rather than attached, are not machine-readable at call time, and carry no return contract. Scored PARTIAL, not NONE, under the null-set discipline of step 7.
- validity range: Requires the input distribution to be characterisable. Where it is not, the honest envelope is empty, and an empty envelope is itself the rating.
- transported from pressure vessel certification (stamped plate): the vessel carries its certified conditions on the object; outside the stamped envelope the vessel is UNRATED, not degraded and not derated
- why it carries: the mechanism is a rating that exists but does not travel with the object, so it is unreadable at the point where load is applied. Structurally identical. The carried discipline is the sharp one: OUTSIDE THE ENVELOPE THE VESSEL IS UNRATED - not degraded, not derated, unrated.
- reconstruction note: Not applicable directly; DUR-002 governs USE, not rebuild. It is the load rating, not the as-built.
- PROPOSED control: stamped validity envelope attached to the serving interface (machine-readable: input distribution, consequence range, date, seed/variance basis) plus a return contract whose OUT_OF_ENVELOPE is a distinct return state
- control precondition: an empty envelope must not read as a broad one: blank is a distinct value from wide, and an empty envelope is itself the rating (entry DUR-002-N1)
- control precondition: an envelope without a retained sample states conditions that cannot later be checked against what was actually deployed (entry DUR-001)
- coupled with: DUR-001 (neither control works alone)
- supersedes: D-202 (operator-supplied worked entry, section 3B-W)
- minimum artifact that would close it: a machine-readable envelope attached to the serving interface, and a return contract in which OUT_OF_ENVELOPE is a distinct return state rather than a low confidence score.
- cross-reference (not re-derived): D-208 (inspection interval: the envelope says where the rating applies, the interval says when it is re-established); experiments/terrain_prior/ (the same UNRATED-not-degraded discipline: a prior outside its stated scope is returned with the scope mismatch flagged, never suppressed and never silently re-rated)
- citation [VERIFIED_2026-09-13]: operator work order section 3B-W, entry DUR-002, filled to schema by the operator
- citation [FROM_MEMORY_UNVERIFIED]: Model Cards for Model Reporting (Mitchell et al., FAT* 2019): intended-use and out-of-scope sections, filed alongside and not machine-readable at call time

### DUR-002-N1  an empty envelope reads as a broad envelope

- mechanism: An object with no characterised distribution and an object characterised as broadly applicable are indistinguishable when the envelope field is left blank. The blank is read as permission rather than as an absence, so the least-rated objects present as the most widely applicable ones.
- load condition: the envelope field is permitted to be empty in the schema that carries it
- onset: immediate | evidence: TRANSPORTED | reconstruction: NOT_APPLICABLE
- detection channel: a schema that forbids blank: the envelope must carry either a characterised distribution or the literal EMPTY, and EMPTY is itself a rating. Detection is immediate at read time once the schema distinguishes them, and NONE for as long as blank is permitted.
- detection latency: immediate under a schema that distinguishes blank from wide; UNBOUNDED under one that does not
- attribution: the operator who applied load inside an envelope that was never characterised
- consequence: the rating system inverts: absence of characterisation presents as breadth of characterisation, under load, with no record that anything was missing
- existing control: NONE. Intended-use fields in current documentation templates are free text and may be empty, and an empty one is not read as a finding.
- validity range: any schema carrying a rating envelope; the stronger the schema's other fields, the more likely a blank envelope is read as deliberate
- transported from pressure vessel certification: an unstamped vessel is not a vessel rated for all conditions; the absence of a stamp is itself disqualifying rather than permissive
- why it carries: the abstract structure is a record in which an absent value and a permissive value occupy the same field, so absence is read as permission. That is a property of the record format, not of steel, and it is the same defect the register applies to itself by filing an UNRATED PART rather than discarding it.
- reconstruction note: governs the DUR-002 rating field rather than the object's record
- minimum artifact that would close it: blank must be a distinct value from wide: the envelope field takes a characterised distribution or the literal EMPTY, and EMPTY is the rating.
- cross-reference (not re-derived): D-106 (the defect is not visible from reading the report: the same structure one level up); this register's own UNRATED PART rule, where an empty field is printed as EMPTY and is distinct from a field whose value is NONE
- citation [VERIFIED_2026-09-13]: operator work order section 3B-W, DUR-002-N1

### DUR-003  migration attrition: the object is not lost at any hop and is gone after N of them

- mechanism: MIGRATION ATTRITION. The object survives no single event, but is carried across repeated hops - framework version breaks, dependency EOL, storage migration, account and org changes, platform deprecation. At each hop a survival fraction applies, and what is carried forward is selected BY CURRENTLY PERCEIVED VALUE. Anything whose value appears later is filtered out by construction.
- load condition: Any object whose retention depends on being actively carried rather than passively held. All hosted, containerised or dependency-bound artifacts.
- onset: drift | evidence: TRANSPORTED | reconstruction: PARTIAL
- detection channel: NONE. Attrition is invisible per hop by definition; the object that was dropped is not the object anyone is looking at. PROPOSED: hop log. Every migration event records what was carried, what was dropped, and by whose decision. Cheap, and it converts an undated attrition into a dated one.
- detection latency: UNBOUNDED. Discovered only when something is needed and absent.
- attribution: None available - no actor performed a loss. Each hop decision was locally correct.
- consequence: Reconstruction path degrades silently while all headline indicators remain healthy.
- existing control: NONE at the artifact level.
- validity range: Holds where hop count over the retention horizon exceeds ~1. Does not apply to objects deposited once in an archive with a custodian whose mandate is retention rather than operation.
- transported from archive and records management (format obsolescence and appraisal): retention is treated as an active, funded, scheduled commitment, and appraisal decisions about what to carry forward are themselves recorded
- why it carries: the abstract structure is retention contingent on repeated active re-commitment, with a per-hop selection filter that is not the criterion the future reader will use. Identical structure, different substrate.
- reconstruction trajectory: PARTIAL -> NO, with no state change recorded at any point on the path
- reconstruction note: Degrades from PARTIAL toward NO without any state change being recorded. Scored at its current value with the trajectory carried in its own field, because a score that moves and reports a single value is the defect this entry describes.
- PROPOSED control: hop log: one record per migration event naming what was carried, what was dropped, and by whose decision
- control precondition: the log must record the DROPPED set, not only the carried set: a log of what survived is the same selection filter written down, and reproduces the defect it was built to expose
- control precondition: a hop log is only readable by someone who still understands the stack it describes, so attrition control depends on the carrier population holding (entry DUR-004)
- minimum artifact that would close it: a hop log per object recording, per migration event, what was carried, what was DROPPED, and by whose decision; plus a retention horizon stated in hops rather than in years.
- cross-reference (not re-derived): D-207 (format obsolescence: held and unreadable, the other half of the archive transport); D-206 (custody handoffs: a hop with a named holder on both sides is the recorded case; attrition is the unrecorded one); DUR-009 (the same hops, correlated across objects rather than compounding within one); DUR-008 / 6C-2 (degradation versus regress: this entry is the degradation, measurable per hop); 6C: under a compounding regime the hop budget of 6B does not hold, and this entry's survival fraction is applied at machine rate
- citation [VERIFIED_2026-09-13]: operator work order section 3B-W, entry DUR-003, filled to schema by the operator
- citation [VERIFIED_2026-09-13]: hop budget in section 6B: roughly 20 generational hops over 500 years against 20 to 50 substrate hops over 10 years, an order-of-magnitude estimate supplied by the operator
- note: Distinguish from DUR-001. DUR-001 is 'cannot tell which object.' DUR-003 is 'the object is no longer being carried.' Independent. Also distinguish from D-207: there the object is held and unreadable; here it is not held at all, and nothing recorded the moment it stopped being held.

### DUR-004  stranded under load: artifact present, demand maximal, comprehension absent

- mechanism: STRANDED UNDER LOAD. The object is retained and still bearing production load, but the carrier population that can read, modify, verify or replace it has gone to near zero. Not lost - stranded. Artifact present, demand maximal, comprehension absent.
- load condition: Long-lived deployment plus high carrier turnover plus high precondition load. The combination, not any one term.
- onset: drift | evidence: MEASURED | reconstruction: NO
- detection channel: WEAK but non-zero, unlike most entries here: bus-factor count, time-to-first-successful-modification by a new engineer, failed replacement attempts. These are measurable today and are not measured.
- detection latency: Detectable BEFORE the failure if the above are instrumented; otherwise detected at the first required change that cannot be made.
- attribution: Lands on whoever is holding it when a change is finally required, typically years after the decisions that produced the state.
- consequence: The system continues to work and cannot be altered. Every option except continued operation closes. This is a live liability, unlike a lost artifact with no load on it.
- existing control: NONE for ML specifically. General software practice has partial controls (documentation mandates, rotation) with known poor compliance.
- validity range: Applies where the object cannot be cheaply retrained or regenerated from a specification. Where regeneration is cheap and the spec is held, stranding does not bind.
- reconstruction note: Reconstruction requires comprehension, which is the missing term. A complete deposit does not close this entry.
- minimum artifact that would close it: instrument the three signals that already exist: bus-factor count per deployed component, time-to-first-successful-modification by an engineer who did not build it, and a record of failed replacement attempts. This is the only entry in the register whose detection channel needs measuring rather than inventing.
- cross-reference (not re-derived): D-102 (the unstated stack: what a departing carrier was holding in place of a record); DUR-003 (a hop log is only readable while carriers remain, which couples these two); DUR-005-B (carrier-side ambient: this entry is the carriers departing, that one is the conditions producing them shifting; DUR-004's signals are the only existing instrument for any carrier-side condition)
- citation [VERIFIED_2026-09-13]: operator work order section 3B-W, entry DUR-004, filled to schema by the operator
- citation [VERIFIED_2026-09-13]: mainframe and COBOL carrier-population figures as reported by vendor and consultancy posts citing a 2024 Global Mainframe Skills Report: 79 percent of organisations reporting difficulty filling mid-career legacy roles, an average COBOL programmer age of 55, roughly 10 percent of that workforce retiring annually, and abandoned modernisation programmes at banks, tax administrations and airlines
- note: This is the INVERSE of the classical monument case. Pyramids: object retained, load off, gap harmless. Stranded: object retained, load on, gap is the liability. The classical intuition that a surviving artifact means a recoverable technology fails here.

### DUR-005  ambient precondition: the record is complete and the world it ran in is gone

- mechanism: AMBIENT PRECONDITION. The record is complete on its own terms and still unusable, because the conditions under which the procedure ran were never candidates for statement. Not underspecified - never specified, because nobody holds 'there will be servers' as an assumption. It is the condition under which holding assumptions happens. This is the mode that makes reconstruction attempts fail REPEATEDLY ACROSS LONG PERIODS even where custody worked. The reconstructor is not missing a step in the procedure. The reconstructor is missing the world the procedure ran in, and the procedure gives no indication that a world was required.
- load condition: Any record produced inside a stable operating environment - i.e. all of them, which is why this entry sits above the others.
- onset: dormant-until-triggered | evidence: MEASURED | reconstruction: NO
- detection channel: NONE from inside. Ambient conditions cannot be enumerated by the population for whom they are ambient, for the same structural reason an exclusion register cannot be generated from inside the frame it excludes from. PROPOSED: the ambient enumeration procedure (header key ambient_enumeration). Requires outside-the-stack input as a hard requirement, not a nicety.
- detection latency: UNBOUNDED, and asymmetric: detectable cheaply BEFORE the condition ends, not at all after.
- attribution: None. No actor omitted anything.
- consequence: Reconstruction fails even where deposit, custody and hop logging all succeeded. This entry can VOID the controls proposed for DUR-001 through DUR-004 without any of them having failed.
- existing control: NONE. Not addressed by reproducibility practice, which operates entirely inside the ambient set.
- validity range: Holds wherever the record's reader is separated from the author by enough time or enough environmental change that any ambient condition has ended.
- reconstruction note: NO, and undetectably so - the record looks complete. This is the failure mode that makes a complete-looking deposit worthless without changing anything about the deposit.
- PROPOSED control: ambient enumeration: do not ask what is assumed, ask WHAT WOULD HAVE TO STOP EXISTING FOR THIS TO BECOME UNREADABLE, with participants from outside the stack, and record the resulting conditions with their expected lifetimes
- control precondition: run with participants OUTSIDE the stack - different domain, different era of practice, different infrastructure assumptions. Run internally the question returns the stated set, which is already in the document. This is a hard requirement of the procedure, not a preference.
- control precondition: the resulting list is a frozen reference and inherits the externality requirement: a list the generating system may revise tracks its current self-description instead of anchoring it (entry DUR-008-N1)
- control precondition: F_K bound: a condition enters the register only if its expected lifetime falls within the retention horizon being claimed. Conditions outside the horizon are noted once and excluded, or the entry becomes unfalsifiable and the register loses standing.
- minimum artifact that would close it: run the ambient enumeration with outside-the-stack participants, bound the output by the claimed retention horizon (F_K), and deposit the resulting list with the object. The list is not a prediction: it is the world-state the record depends on, written down while it is still visible.
- cross-reference (not re-derived): DUR-001, DUR-002, DUR-003, DUR-004 (this entry can void their controls without any of them failing, which is why it is recorded above them rather than beside them); D-000 (the detection gap: ambient conditions are the case where the gap is structural rather than instrumental); DUR-008 (regress: an ambient condition that ends takes the vocabulary for naming it along)
- citation [VERIFIED_2026-09-13]: operator work order 2026-09-13 rev 6, entry DUR-005 and the ambient enumeration procedure, filled to schema by the operator
- note: A-11: this entry's candidate set is ARTIFACT-SIDE ONLY. The carrier-side class is DUR-005-B, and its existence strengthens this entry's claim to sit above the others: a carrier-side condition voids the DUR-001 to DUR-004 controls without any transmission variable moving at all.

### DUR-005-B  carrier-side ambient: the record stays legible and the method stops being runnable

- mechanism: A capacity the method requires of its carriers is an OUTPUT OF CONDITIONS and is read as an intrinsic property of the population, because it has been reliably produced for as long as anyone has looked. Nobody models a dependency for something that has always simply arrived. When the producing conditions shift, the capacity falls out with no locatable cause. The transmission chain can be intact throughout - record kept, teaching continuous, demand present - and the method still stops executing, because the precondition that failed sits UPSTREAM OF EVERY TRANSMISSION VARIABLE. This is not a transmission failure. It is a failure of the ability to run what was transmitted.
- load condition: any method whose execution requires a capacity of its carriers that is currently produced at sufficient rate to be invisible as a dependency. The condition is the invisibility, not the scarcity.
- onset: drift | evidence: PROJECTED | reconstruction: NO
- detection channel: NONE. The DUR-005-C screen exists and is not a detection channel: it records what is unexamined, it does not signal a change. Worse, it is run by the same population for whom the capacity is intrinsic, which is the failure mode it is meant to catch. PROPOSED: production-rate measurement per capacity, which F_M requires before a condition may be carried as a claim, and which exists for one of five candidates.
- detection latency: UNBOUNDED, and asymmetric like DUR-005: the producing conditions are cheap to characterise while they still hold and impossible to reconstruct afterwards
- attribution: none. No actor removed a capacity, and the population that lost it did not know it was a dependency.
- consequence: the method stops being runnable while every artifact-side control reports healthy. Deposit, custody, hop log, identity referent and rating envelope can all be intact and the object still cannot be operated, because the operator does not exist. LOSS DOES NOT SCALE WITH THE SIZE OF THE CAUSE: a small shift in an unmodelled condition can take an entire capability, because the condition was load-bearing without being counted.
- existing control: NONE. Nothing in ML practice screens for carrier-side preconditions, and the four unmeasured candidates have no production-rate instrument at all.
- validity range: methods requiring a carrier capacity that is currently produced at replacement rate. Does not bind where the method can be executed by an agent whose capacity is not produced by the same conditions, which is a transfer of the dependency rather than its removal.
- reconstruction note: reconstruction requires a carrier able to run the method. This entry is the condition on that carrier's existence, so a complete record scores NO here for the same reason DUR-004 does, one level further upstream: DUR-004 is the carriers leaving, this is the conditions that produced them changing.
- PROPOSED control: the DUR-005-C intrinsic-vs-produced screen with outside-the-stack participants, plus a production-rate measure per admitted capacity (F_M)
- control precondition: the outsider needed here is separated by GENERATION or CONDITIONS rather than by domain, which makes the outside-the-stack requirement harder to satisfy than on the artifact side
- control precondition: F_M: a condition enters the active set only with a named producing mechanism AND a currently measurable production rate; four of the five candidates fail the second and are recorded as UNINSTRUMENTED rather than carried as claims
- control precondition: the one admitted capacity is admitted because DUR-004's carrier-side signals already measure its local form (entry DUR-004)
- minimum artifact that would close it: run the DUR-005-C screen with outside-the-stack participants and record the result per capacity: PRODUCED with its producing conditions named, or FLAGGED. Nothing scores clean. Then apply F_M: only capacities with a measurable production rate enter the active set; the rest are recorded as UNINSTRUMENTED so the gap is visible rather than asserted as a hazard.
- cross-reference (not re-derived): DUR-005 (artifact-side ambient: the same structure on the object's side of the line); DUR-004 (stranded under load: the carriers gone; here it is the conditions that produce them); DUR-008 (regress: a lost capacity takes the vocabulary for naming it, so a carrier-side loss is also a regress candidate); D-000 (the detection gap, of which this is the upstream-most instance in the register)
- citation [VERIFIED_2026-09-13]: operator patch 2026-09-13, PATCH - CARRIER-SIDE AMBIENT PRECONDITION, hunks 1 to 4 (DUR-005-B, DUR-005-C, F_M, correction A-11, still-open note). The patch targets a file WORKORDER_failure_mode_enumeration.md that does not exist in this repository; none of its four anchors was found, so the patch was NOT applied as a patch and its content was implemented in the register instead. Reported rather than guessed, per the patch's own instruction.
- note: Distinguish from DUR-005 (artifact-side: conditions the OBJECT needs to exist and be read) and from DUR-004 (the carriers depart). This is the conditions that PRODUCE carriers shifting, which is upstream of both. It strengthens DUR-005's claim to sit above the other entries: this class voids controls without any transmission variable moving at all.

### DUR-006  custodian continuity assumed: the gate opens onto nothing after transfer

- mechanism: CUSTODIAN CONTINUITY ASSUMED. Retention is contingent on a single holder continuing to exist, remain solvent, retain the carriers, keep the strategy, avoid seizure and avoid transfer. The artifact transfers by legal instrument; COMPREHENSION TRANSFERS BY CHOICE OF THE CARRIERS, and mostly does not. Gatekeeping is not a property that persists. It is a RELATION between a holder and a population, and it ends with the holder. The gate does not transfer - it opens onto nothing, because the asset moves and the comprehension does not.
- load condition: Any artifact whose only readable copy sits inside one entity, under access control.
- onset: dormant-until-triggered | evidence: MEASURED | reconstruction: NO
- detection channel: Entity-health signals exist but do not measure the thing - a solvent, growing firm can reassign a team tomorrow. PROPOSED: carrier-side measurement from DUR-004 (bus factor, time-to-first-successful-modification by a new engineer), plus an explicit transfer clause stating what comprehension is required to operate the asset.
- detection latency: Detectable before transfer only; the transfer itself is the event that reveals it.
- attribution: Falls on the receiving party - state, acquirer, creditor - who did not make any of the decisions that produced the state.
- consequence: Receiver takes possession of a stranded object: present, load-bearing, unreadable (DUR-004 by a different trigger).
- existing control: NONE. Transfer instruments enumerate ASSETS. No instrument enumerates PRECONDITIONS, and nothing records which carrier put what into the artifact, so after transfer there is no way to establish what was received or what comprehension operating it requires.
- validity range: Does not bind where a readable copy exists outside the entity - which is the entire content of the control.
- reconstruction note: NO after transfer, in the general case
- PROPOSED control: carrier-side measurement plus a transfer clause enumerating the comprehension required to operate the asset, not only the asset
- control precondition: the carrier-side signals are DUR-004's, and they are the only channel that sees the quiet transfer mode (strategy change) (entry DUR-004)
- control precondition: the clause must enumerate PRECONDITIONS, not assets: transfer instruments already enumerate assets and that is exactly what fails to carry comprehension
- minimum artifact that would close it: CUSTODIAN-INDEPENDENCE, not custodian continuity: state how much of retention survives the disappearance of any single holder. A single-holder arrangement is a conjunction of seven terms (header key custodian_conjunction) and cannot claim continuity, because nothing in the arrangement ensures any term. A distributed arrangement is a disjunction and survives if any holder persists.
- cross-reference (not re-derived): D-301 (the proprietary boundary as a custody term: this entry is its mechanism, and D-301's default of UNBOUNDED and NO follows from the conjunction in the header); DUR-004 (stranded under load: the same end state reached by carrier attrition instead of by transfer); DUR-009 (correlated shock: a single custodian is the limiting case of a shared node)
- citation [VERIFIED_2026-09-13]: operator work order 2026-09-13 rev 6, entry DUR-006 with sub-sections A (transfer modes), B (the conjunction) and C (conjunction vs disjunction), filled to schema by the operator

### DUR-009  correlated substrate and dependency shock: one event, a large synchronous slice

- mechanism: Objects share hops. A framework break, a vendor end-of-life, a storage platform sunset, a cloud region retirement: one event applied to a large correlated fraction of the population at once. The loss is therefore not many independent small draws but a small number of correlated draws each taking a large slice, and a synchronous block loss defeats redundancy that was counted as independent.
- load condition: two or more copies, instances or fallbacks that share a platform, a format, a dependency stack, an authorisation path or a budget line. Sharing any one of these makes them one copy against a shock to that thing.
- onset: dormant-until-triggered | evidence: TRANSPORTED | reconstruction: NO
- detection channel: an effective-redundancy audit BEFORE the event: enumerate what the copies share and count the channels that survive the failure of every shared node. The shared node is usually a process, an input, a decision or a budget, which is why a component-level redundancy diagram cannot draw it. Announced end-of-life calendars are the second channel and are read as notices rather than as dated shocks.
- detection latency: the interval between the announcement and the event, which is usually months and is usually spent; UNBOUNDED where no audit exists, because the correlation is discovered by the block loss itself
- attribution: the platform or vendor that scheduled the change, which is where blame lands and where no remedy sits; the operator who counted the copies as independent is not identified anywhere
- consequence: redundancy that was carried as a control fails as one unit while under load, and the failure is read as an unforeseeable external event rather than as an uncorrected independence assumption
- existing control: PARTIAL. Multi-region and multi-provider practice exists and is usually credited as redundancy without a shared-node audit, so the credited count is the unaudited one.
- validity range: populations of two or more nominally independent copies; does not apply to a single copy, where the mode is simply the copy's own loss
- transported from common-cause failure analysis in nuclear and aerospace reliability engineering: common-cause failure is an enumerated category with its own analysis: redundant channels are credited only after the shared causes (shared power, shared maintenance crew, shared design, shared calibration) have been identified and removed from the count
- why it carries: the abstract structure is a redundancy claim whose channels share a cause that the redundancy diagram does not draw, so the credited channel count exceeds the surviving channel count. That is a property of how the claim was computed, not of reactors. The shared causes here are platform, format, dependency stack, authorisation path and budget.
- redundant copies do NOT share: NOTHING is assumed unshared by default. A copy counts as a separate channel only after platform, serialisation format, dependency stack, authorisation path, maintenance process and budget line have each been shown not to be shared; copies differing only in region or bucket name share all six and are one channel.
- reconstruction note: the reconstruction path is as correlated as the copies: where every retained copy sits under one dependency stack, the stack's end-of-life removes all of them at once
- PROPOSED control: N_eff rather than N: the count of channels that survive failure of every shared node, computed before the shock and recomputed when any shared node changes
- control precondition: the audit must enumerate shared PROCESSES, INPUTS, DECISIONS and BUDGETS, not only shared components: a diagram of components will show independence that does not exist
- control precondition: the same hops that correlate across objects also compound within one, and the two must be reported separately (entry DUR-003)
- minimum artifact that would close it: state N_eff rather than N wherever redundancy is credited as a control, computed with the shared-node classes of the existing effective-redundancy instrument, and put a budget line against each announced end-of-life date.
- cross-reference (not re-derived): JinnZ2/Simulators effective-redundancy-audit: computes N_eff from six shared-node classes (authorization, information, discretion, maintenance, envelope, verification); the correlated-failure-at-scale marker in this ecosystem, cross-referenced rather than re-derived; JinnZ2/Simulators fragility-cascade; DUR-003 (volume: the same hops compounding within one object); D-301 (a reconstruction path through one commercial entity is the limiting case of a shared node)
- citation [VERIFIED_2026-09-13]: operator work order section 6B-2, which states that correlation needs its own entry and is the worse of the two modes for infrastructure
- citation [FROM_MEMORY_UNVERIFIED]: common-cause failure analysis as a mature enumerated category in reliability engineering

## 3B TRANSPORTED

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

- mechanism: Weights are retained in a serialisation format that depends on a specific library version to load, and on a runtime that depends on a driver that depends on hardware. The bits do not rot; the READER is gone. This is the one mode where the object IS retained, which is why it is recoverable in principle and why its neglect is cheapest to fix.
- load condition: retention is planned in years while the loader's support horizon is months
- onset: dormant-until-triggered | evidence: TRANSPORTED | reconstruction: PARTIAL
- detection channel: a scheduled load test of the deposit on a current runtime
- detection latency: one test interval; UNBOUNDED if never scheduled, and the discovery point is usually the moment the object is needed
- attribution: the archivist or the successor team, who are read as having lost the file they in fact still hold
- consequence: a retained deposit that cannot be executed is a record of an object, not the object. Intact and unreadable is a distinct state from decayed, and it is worse, because it reads as retained: every inventory, checksum and storage metric reports the deposit as healthy.
- existing control: PARTIAL: open exchange formats and framework-independent serialisations exist; migration of deposits on a schedule is not practised
- validity range: any deposit intended to outlive its framework's support window
- transported from digital archives and civil records: format obsolescence is a named preservation risk; formats are migrated on a schedule and independent-of-reader representations are preferred
- why it carries: the abstract structure is: retention of bytes is not retention of the object when interpretation requires an artifact that is not retained. The mechanism is about the dependency between a record and its reader.
- minimum artifact that would close it: store the deposit in a reader-independent representation where one exists, and schedule a load test plus migration decision on an interval shorter than the framework's support horizon.
- cross-reference (not re-derived): DUR-003 (migration attrition: not held at all, the other half of the archive transport); DUR-009 (one format sunset removes every copy in that format at once)
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

### DUR-007  load rating lost: the rating existed, its record is gone, the component stays in service

- mechanism: A rating was established at some point and the record of it has since gone: the team dispersed, the evaluation harness rotted, the wiki page was deleted, the numbers live in a slide nobody kept. The component remains in service and is still treated as rated, because the memory that it was once evaluated outlives the evidence of what the evaluation said.
- load condition: a component whose evaluation predates the current team, or whose evaluation artifacts were held somewhere with a shorter life than the deployment
- onset: drift | evidence: TRANSPORTED | reconstruction: NO
- detection channel: ask for the rating: the input distribution it was established on, the consequence range, the date, and the artifact that produced it. Absent one of those, the component is unrated. The channel is cheap and is not walked, because nothing schedules the asking.
- detection latency: immediate on request; UNBOUNDED otherwise, and the belief that a rating exists is stable indefinitely without it
- attribution: the current owner, who is asked to justify a number they did not produce and cannot locate
- consequence: load continues on a component whose rating cannot be produced, while every report and inventory describes it as evaluated. This is distinct from a rating that never existed: the belief is well-founded and the evidence is not there.
- existing control: NONE. No practice treats the loss of an evaluation record as an event, and no default restricts use until a rating is re-established.
- validity range: components in service longer than the life of the team or system that evaluated them; does not apply where the evaluation artifact is deposited with the object
- transported from structural / civil engineering (bridges in service with missing as-built plans): the obligation to hold a rating does not lapse when the documentation does. Federal practice directs that a load rating be established for EVERY structure in the inventory even where plans are missing, by field measurement with era-appropriate conservative assumptions, by load testing, or by documented engineering judgement. A structure is re-rated or posted at a reduced limit; it is not left in service unrated.
- why it carries: the abstract structure is a rating whose evidence has been lost while the object stays under load, and a practice that responds by RE-ESTABLISHING the rating conservatively rather than by carrying the belief forward. That response is a procedure over records, not over steel.
- reconstruction note: the object may be intact and identifiable while its rating is not recoverable at all; this entry is about the loss of the rating record, not of the object (contrast DUR-003)
- minimum artifact that would close it: treat the loss of an evaluation record as an event: a component whose rating cannot be produced on request is UNRATED, and either re-rated against a held reference or restricted to a conservative posted envelope until it is. The bridge practice is the template: re-rate or post, never carry the belief forward.
- cross-reference (not re-derived): DUR-002 (the rating exists and does not travel with the object: the other half of the load-rating pair); DUR-003 (attrition of the OBJECT across hops; this is attrition of its RATING); D-208 (inspection interval: a re-rating cadence is what would have caught the loss)
- citation [VERIFIED_2026-09-13]: FHWA-directed practice that a load rating be established for every structure in the inventory even where as-built plans are missing, using field measurement with conservative era-appropriate assumptions, load testing, or documented engineering judgement (state load-rating manuals and VTRC / NTL reports on rating bridges with limited or missing as-built plans). Read from state manuals and research summaries located this session; the federal directive itself was not fetched. (https://vdot.virginia.gov/vtrc/main/online_reports/pdf/20-r27.pdf)
- citation [VERIFIED_2026-09-13]: structural load rating lost, named as a transport mechanism in the work order section 3B and not previously covered by any entry

### DUR-010  no batch record: the run's deviations from its own procedure are unrecorded

- mechanism: The intended procedure is recorded (configuration, code, hyperparameters) and the ACTUAL RUN is not. Real runs deviate: a restart from an intermediate checkpoint, a shard that failed to load, a batch skipped after a numerical fault, a node swapped mid-run, a data snapshot that moved under the job. Each deviation changes the object produced, none is part of the configuration, and nothing requires any of them to be written down. The record therefore describes a run that did not happen.
- load condition: training or fine-tuning runs long enough to be interrupted, which is all runs at scale; plus a logging system whose retention is set by operational need rather than by the object's service life
- onset: immediate | evidence: TRANSPORTED | reconstruction: PARTIAL
- detection channel: the run's own logs and job history, WHERE THEY ARE STILL RETAINED. Log retention is typically set in weeks or months while the object stays in service for years, so the channel closes on a schedule nobody connected to the object. NONE after the retention window.
- detection latency: bounded by log retention, then UNBOUNDED: after the window there is no signal that a deviation ever occurred
- attribution: the engineer who cannot explain a discrepancy between the documented procedure and the object's behaviour, read as not knowing their own system
- consequence: a rebuild from the documented procedure produces a different object than the one bearing load, and the difference cannot be attributed to any recorded cause, so it is attributed to variance (D-101) and closed
- existing control: PARTIAL. Experiment trackers record configuration and metrics, and some record restarts; none requires a deviation to be dispositioned, and none is retained on the object's schedule.
- validity range: runs that can be interrupted or that read data from a mutable location; does not apply to a short deterministic fit over a frozen local dataset
- transported from pharmaceutical manufacturing (the batch record): a batch record documents what was ACTUALLY done to this batch, not what the master formula specified, and every deviation from the master formula is recorded and given a written disposition before the batch can be released
- why it carries: the abstract structure is a record of the INTENT standing in for a record of the EXECUTION, where the two are known to differ and the differences change the object. Nothing in that depends on chemistry. The deviation-with-disposition discipline is the part that carries and the part entirely absent here.
- reconstruction note: the configuration is usually recoverable and the execution history is not, which is exactly the gap that makes a rebuild approximate rather than identifying
- minimum artifact that would close it: a batch record per run, retained with the object rather than on the logging system's rotation: restarts, checkpoint lineage, data snapshot identifier, failed or skipped steps, hardware substitutions, and a written disposition for each deviation.
- cross-reference (not re-derived): D-101 (variance: the explanation that absorbs every unrecorded deviation); D-102 (the stack: what was available, as against what this run actually did); DUR-001 (identity: a probe record fixes WHICH object, and says nothing about how it came to be that object)
- citation [VERIFIED_2026-09-13]: pharmaceutical batch records and custody chain, named as a transport source in the work order section 3B and not previously covered by any entry
- citation [VERIFIED_2026-09-13]: run-to-run variance anchors at D-101: variance is the bucket an unrecorded deviation gets attributed to

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
- cross-reference (not re-derived): DUR-003 (the pipeline's parts are carried across hops separately, and the least-valued part at each hop is the one dropped)
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

### DUR-008  regress: the capacity to state what was lost is itself lost

- mechanism: A DEGRADATION loses fidelity per hop and stays measurable: you can say what is missing, in what quantity, against what reference. A REGRESS loses the ability to state what was lost. The vocabulary, the questions, the criteria that would identify the absence went across the same hops as the object and were subject to the same per-hop selection filter. After a regress the inventory is complete with respect to every question anyone can still ask, and the loss is not recorded as a loss because there is nothing left to record it against. No amount of per-hop instrumentation reaches this: a hop log records what its authors could name at the time of the hop, so a regress passes through the log intact and undocumented. WORKED INSTANCE, supplied 2026-09-13 rev 6 section 6C-2: PROVENANCE REGRESS. Provenance is a record about a hop, so every hop is an opportunity to re-encode the provenance format itself. If each generation defines its own provenance convention then provenance requires provenance, and the requirement recurses with no fixed point unless some layer's format is frozen by something outside the generating system.
- load condition: the instruments that would detect the absence are produced by the same system, team and period that produced the object, and are carried forward by the same hops. This is the normal case: evaluation harnesses, reference sets, review checklists and the register itself are all artifacts of the generating system.
- onset: drift | evidence: PROJECTED | reconstruction: NO
- detection channel: NONE, and this is not the ordinary NONE. The other detection gaps in this register could be closed by an instrument someone has not built yet. A regress cannot be closed from inside the system at all, because any instrument built inside it is subject to the same loss and will report clean. The only closure is a reference set frozen from OUTSIDE the generating system before the regress (see DUR-008-N1).
- detection latency: UNBOUNDED, and unlike every other unbounded latency here it does not end when someone eventually looks: looking uses the surviving questions
- attribution: nobody, ever. There is no discrepancy for anyone to be accountable for, because the record and the questions agree.
- consequence: every audit passes, every coverage check reports full coverage, and the register's own gap count reads zero, while a class of loss has occurred that none of those instruments can represent. The failure is not that the answer is wrong; it is that the question is gone.
- existing control: NONE.
- validity range: systems whose evaluation instruments are produced and carried by the same population as the object. Does not apply where an external party holds a reference set predating the current generation of the system, which is exactly what DUR-008-N1 requires and what nothing currently provides.
- reconstruction note: not scoreable from inside: a reconstruction score requires a statement of what is missing, which is the capacity this entry says is gone. NO is recorded as the honest floor rather than as a measurement, and this is the one entry whose own score is subject to the mechanism it describes.
- PROPOSED control: an externally frozen SURVIVAL SET: the short list of things that must cross a hop, frozen by a party outside the generating system, stating what must still be answerable rather than how the work is to be done
- control precondition: a survival set frozen by the generating system is inside the regress with everything else, and the freeze is then decorative (entry DUR-008-N1)
- control precondition: the set constrains WHAT must survive a hop, not HOW the work is done. A process mandate has the cost that makes process mandates fail; a survival set is cheap because it leaves method alone.
- minimum artifact that would close it: a frozen interchange layer that no generation is permitted to redefine (6C-7). Contents: object identity (DUR-001), rating envelope (DUR-002), and the hop log (DUR-003). Property: frozen by something outside the generating system, or it is inside the regress. The FORMAT of those fields is itself in the frozen set, because under the compounding case DUR-001 and DUR-002 are no longer a contract between an author and a later reader but a CONTRACT BETWEEN GENERATIONS.
- cross-reference (not re-derived): DUR-003 (degradation: the measurable sibling; the per-hop selection filter is shared, the detectability is not); D-000 (the detection gap: DUR-008 is D-000 applied to the instruments rather than to the object); D-106 (the defect is not visible from reading the report: the same structure one level down, where the missing field is still nameable); this register's own `coverage` command, whose zero-gap result is bounded by the same limit: it can only find mechanisms someone was still able to name; DUR-015, DUR-016, DUR-017 (the 6C compounding case in which this regress runs at machine rate rather than human rate)
- citation [VERIFIED_2026-09-13]: operator work order 2026-09-13 rev 6, section 6C-2 (provenance regress; 'distinguish these in the register: DUR-003 is degradation, this is a separate class') and section 6C-7 (the minimal arrest). The section text was NOT available when this entry was first written on the operator's two sentences in conversation; it is now supplied and the entry is re-cited to it.
- note: Class boundary, stated by the operator 2026-09-13: DUR-003 handles degradation (fidelity lost per hop, still measurable); nothing handled regress until this entry. The two are not degrees of the same thing. Instrumenting hops harder improves DUR-003 and does not touch DUR-008.

### DUR-008-N1  the survival set is frozen by the system it is meant to outlive

- mechanism: The arrest works only if the frozen set is fixed from outside the generating system. A survival set written, held, revised and interpreted by the same team, on the same platform, under the same dependency stack, is carried by the same hops and filtered by the same criteria as everything else. It will be updated to stay convenient, and each update is locally reasonable, so the set tracks the system's current self-description instead of anchoring it.
- load condition: the freeze is internal: same authors, same storage, same review, or revisable without an external party's involvement
- onset: drift | evidence: TRANSPORTED | reconstruction: NOT_APPLICABLE
- detection channel: check the freeze's externality, which is cheap and binary-ish: who can change the set, where it is held, and whether a version predating the current generation of the system is still retrievable by someone outside it. If every copy is internal, the freeze provides nothing.
- detection latency: immediate on inspection of the custody arrangement; UNBOUNDED if nobody inspects it, because an internally frozen set looks identical to an externally frozen one from inside
- attribution: the team that maintained the set in good faith, whose updates were each defensible
- consequence: the control reports as present and does not arrest the regress: the register, the reference set and the object degrade together while the freeze is cited as the reason they cannot
- existing control: NONE. Third-party evaluation exists and is commissioned, scoped and paid for by the party being evaluated, which is internal custody with an external label.
- validity range: any frozen set, survival list, reference corpus or probe set; the stronger the internal process around it, the more convincingly an internal freeze reads as an external one
- transported from metrology (traceability to an external standard) and independent verification practice in certification and audit: a measurement is traceable only to a standard maintained outside the measuring laboratory, through an unbroken chain of comparisons. A laboratory that calibrates against its own working reference has precision and no traceability, and the distinction is structural, not a matter of diligence.
- why it carries: the abstract structure is a reference whose authority depends on being maintained outside the system it judges, and which becomes self-referential the moment the system can revise it. Nothing in that depends on physical units. The register, the reference set and the probe set are all references in exactly that position.
- reconstruction note: governs the DUR-008 control rather than the object's record
- minimum artifact that would close it: name the external holder and the change rule before the set is called frozen: who holds it, who may change it, and whether a pre-current version is retrievable by someone outside the generating system. A set with no external holder is recorded as UNFROZEN rather than as a control.
- cross-reference (not re-derived): DUR-001-N1 (probe leakage: the same externality requirement on the identity control, where the threat is training against the probe rather than revising it); D-304 (the inspection reference stops being held-out: internal custody of a reference set, one level down); D-301 (a reconstruction path through a single commercial entity: the limiting case of internal custody)
- citation [VERIFIED_2026-09-13]: operator, 2026-09-13, in session: the frozen set has to be frozen from outside the generating system, or it is inside the regress with everything else
- citation [FROM_MEMORY_UNVERIFIED]: metrological traceability to an external standard as a structural requirement

## 6C COMPOUNDING - the hop generator inside the system (all PROJECTED per F_J)

### DUR-015  rate mismatch: the only layer with a shared external referent is the slow one

- mechanism: The layers move at different rates and only one of them has a shared external referent. Hardware changes in years, is capital-bound, and is unsynchronised across firms, but it is anchored by physics, power draw, supply chain, cooling and fab capacity. Model generations change many times per hardware generation with no shared referent. The representation layer - format, language, provenance convention - changes per generation with no shared referent. So the substrate is the slow layer and the only anchored one, while everything carrying meaning moves faster than the thing that anchors it.
- load condition: a system in which generations are produced faster than the substrate they run on changes, and the representation is redefined per generation
- onset: drift | evidence: PROJECTED | reconstruction: NO
- detection channel: NONE as a signal; the mismatch is visible by inspection of the layer rates and is not watched by anything. PROPOSED: state, per deployed object, which layer holds its referent and at what rate that layer changes.
- detection latency: UNBOUNDED: nothing reports a rate mismatch, and each layer's own metrics look healthy
- attribution: nobody: every layer is behaving as designed
- consequence: nothing anchors. This INVERTS the classical case: Roman concrete had fast carriers and a slow durable substrate that held the referent, so the object outlived the people and could be tested. Here the substrate is slow AND changing (legacy hardware retained while several model generations move off it, new hardware arriving with different characteristics per firm) and the meaning-bearing layer is the fast one.
- existing control: NONE.
- validity range: systems whose generation rate exceeds their substrate change rate; does not apply where the representation is fixed across generations
- reconstruction note: a reconstruction needs a referent that outlives the representation; this entry says which layer holds one and that it is not the layer carrying meaning
- minimum artifact that would close it: per object, name the layer that holds its referent and that layer's change rate; a claim of durability that rests on substrate slowness is void unless the representation is also frozen.
- cross-reference (not re-derived): D-207 (format obsolescence: the reader is gone; here the reader changes faster than the substrate it reads on); DUR-008 (the regress this rate mismatch feeds)
- citation [VERIFIED_2026-09-13]: operator work order 2026-09-13 rev 6, section 6C-1
- note: REGISTER CONSEQUENCE, stated by the order: an entry may not cite 'the hardware is stable' as a custody control. Hardware slowness protects nothing if the representation layered on it is redefined between hardware cycles. Enforced by validate.

### DUR-016  seam multiplication: no owner of the boundary has ever existed, and an automated system must still return a value

- mechanism: Each firm's chain is internally consistent and externally uninterpretable: different hardware, tooling, data conventions, definitions of what counts as validated, provenance formats, several held closed for competitive reasons. That is the disciplinary-seam structure, with two differences that make it worse. Seams multiply at GENERATION rate rather than institutional rate, and there was never a natural-philosophy layer here to have been dissolved, so no owner of the seam has ever existed for this domain. An institution can defer a seam question indefinitely. An automated system must return a value: across an uninterpretable boundary it will return one, selecting a criterion with no record that a selection occurred.
- load condition: two or more chains that must exchange values, developed independently, with no shared interchange contract and no party whose remit covers the boundary
- onset: immediate | evidence: PROJECTED | reconstruction: NO
- detection channel: NONE. The selection leaves no record by construction: the value returned is well-formed and carries no marker that a criterion was chosen in the absence of one. PROPOSED: a return contract at the boundary in which UNINTERPRETABLE is a distinct return state, the same shape as DUR-002's OUT_OF_ENVELOPE.
- detection latency: UNBOUNDED
- attribution: the operator of whichever chain acted on the value, who cannot see the other chain's conventions
- consequence: criteria get selected silently at every boundary crossing, at generation rate, and the record of each crossing says a value was exchanged and nothing about what it meant
- existing control: NONE. Interchange formats exist for models and data and none carries a validation-criterion declaration, so a crossing cannot report that the criterion was absent.
- validity range: boundaries between independently developed chains; does not apply inside one chain, where the conventions are shared even if unstated
- reconstruction note: governs what a crossing meant rather than whether an object can be rebuilt; recorded NO because the criterion selected at a crossing is not recoverable afterwards
- minimum artifact that would close it: an interchange contract at each boundary carrying the validation criterion and the envelope, with UNINTERPRETABLE as a distinct return state. Absent that, record the boundary as a silent-selection site rather than as an integration.
- cross-reference (not re-derived): DUR-002 (the return-contract shape this needs: a distinct state rather than a low score); DUR-017 (the load case where this bites while load is on)
- citation [VERIFIED_2026-09-13]: operator work order 2026-09-13 rev 6, section 6C-3

### DUR-017  coupled preemption under load: two controllers acting on each other's incommensurable output

- mechanism: Adjacent segments of one physical system, each managed by a different firm's stack, each with its own internal representation of what a reading means and no provenance the other can parse. The systems are not required to agree about science. They are required to INTEROPERATE UNDER LOAD. Each side acts on the other's output while unable to establish what that output was measured against or under what envelope it was produced, and each side's action becomes the other's next input.
- load condition: two or more automated controllers coupled through a physical system, under independent management, with no shared representation and no human in the per-decision path
- onset: dormant-until-triggered | evidence: PROJECTED | reconstruction: NO
- detection channel: NONE in the coupling itself. Each side's own monitoring reports healthy because each side is internally consistent. PROPOSED: an interchange contract (DUR-016) plus an envelope check at the coupling (DUR-002), and a declared behaviour when the other side's output is uninterpretable.
- detection latency: UNBOUNDED before the event; the event is the detection
- attribution: the operator of whichever segment failed visibly, which is a function of where the physical consequence landed rather than of where the incommensurability was
- consequence: this is the load case that makes the register non-optional. A wrong research result gets corrected. Two coupled controllers with incommensurable representations fail while the load is on, and the failure is physical.
- existing control: NONE for the representation question. Interconnection standards govern electrical and protocol behaviour and do not carry what a reading was measured against or the envelope it was produced under.
- validity range: physically coupled automated systems under separate management; does not apply where one party controls both sides of the coupling or a human approves each cross-boundary action
- reconstruction note: after a coupled failure neither side's record establishes what the other's values meant, so the event cannot be reconstructed even with both logs in hand
- minimum artifact that would close it: at every coupling between independently managed automated systems: a declared interchange contract, an envelope check on the incoming value, and a stated behaviour for UNINTERPRETABLE that is not 'proceed with the value'.
- cross-reference (not re-derived): experiments/trigger_geometry/ (the response-inversion instrument: a trigger validated in one geometry and applied in another, which is this failure at single-system scale); DUR-016 (the seam this runs across); DUR-002 (the envelope neither side can read)
- citation [VERIFIED_2026-09-13]: operator work order 2026-09-13 rev 6, section 6C-4, including the grid-segment worked case

## Requirement set (step 6)

Modes with no existing control, and the minimum artifact that would close each:

- **D-000 the detection gap itself** -> a detection channel is a deliverable, not an assumption: for each deployed component, name the signal that would reveal degradation and its latency, or record NONE. NONE is a rateable answer; an empty field is not.
- **D-104 no agreed significance measure, so point estimates ship without a distribution** -> state the distribution and the comparison procedure with the selection decision, or record the selection as UNRATED.
- **D-106 the defect is not visible from reading the report** -> add the fields, then treat an empty field as a finding. The register's own schema rule (an entry missing a field is an UNRATED PART, filed as such) is the same mechanism applied to itself.
- **DUR-001 the deployed object cannot be distinguished from another produced by the same nominal procedure** -> a sealed probe-response record at deploy: probe set, responses, hash, deposited with a party that is not the operator, with a stated retention period and a rotation rule.
- **DUR-001-N2 instance identity is not procedure reproducibility, and the two must not be summed** -> two separate ratings recorded separately and never summed into one reconstruction score: IDENTITY (closed by DUR-001) and PROCEDURE REPRODUCIBILITY (carried by D-101 and D-102, open).
- **DUR-002-N1 an empty envelope reads as a broad envelope** -> blank must be a distinct value from wide: the envelope field takes a characterised distribution or the literal EMPTY, and EMPTY is the rating.
- **DUR-003 migration attrition: the object is not lost at any hop and is gone after N of them** -> a hop log per object recording, per migration event, what was carried, what was DROPPED, and by whose decision; plus a retention horizon stated in hops rather than in years.
- **DUR-004 stranded under load: artifact present, demand maximal, comprehension absent** -> instrument the three signals that already exist: bus-factor count per deployed component, time-to-first-successful-modification by an engineer who did not build it, and a record of failed replacement attempts. This is the only entry in the register whose detection channel needs measuring rather than inventing.
- **DUR-005 ambient precondition: the record is complete and the world it ran in is gone** -> run the ambient enumeration with outside-the-stack participants, bound the output by the claimed retention horizon (F_K), and deposit the resulting list with the object. The list is not a prediction: it is the world-state the record depends on, written down while it is still visible.
- **DUR-005-B carrier-side ambient: the record stays legible and the method stops being runnable** -> run the DUR-005-C screen with outside-the-stack participants and record the result per capacity: PRODUCED with its producing conditions named, or FLAGGED. Nothing scores clean. Then apply F_M: only capacities with a measurable production rate enter the active set; the rest are recorded as UNINSTRUMENTED so the gap is visible rather than asserted as a hazard.
- **DUR-006 custodian continuity assumed: the gate opens onto nothing after transfer** -> CUSTODIAN-INDEPENDENCE, not custodian continuity: state how much of retention survives the disappearance of any single holder. A single-holder arrangement is a conjunction of seven terms (header key custodian_conjunction) and cannot claim continuity, because nothing in the arrangement ensures any term. A distributed arrangement is a disjunction and survives if any holder persists.
- **D-205 latent fault dormant until an unusual load combination** -> state the validation envelope's instance count and sequence structure, and mark any operating geometry absent from it as ABSENT rather than safe. The check exists in this repository already.
- **DUR-007 load rating lost: the rating existed, its record is gone, the component stays in service** -> treat the loss of an evaluation record as an event: a component whose rating cannot be produced on request is UNRATED, and either re-rated against a held reference or restricted to a conservative posted envelope until it is. The bridge practice is the template: re-rate or post, never carry the belief forward.
- **D-301 the reconstruction path runs through a single commercial entity** -> an escrow deposit outside the vendor, or an explicit recorded acceptance that reconstruction is NO. The second is cheap and is currently made by silence rather than by decision.
- **D-302 what was excluded from the training data is not recorded** -> retain the exclusion filters as executable artifacts with the corpus pointer, so the same corpus plus the same filters is a reproducible input.
- **D-304 the inspection reference stops being held-out** -> custody rules for the reference set: sealed, dated, never in a training or selection path, with a replacement schedule and a record of each use.
- **DUR-008 regress: the capacity to state what was lost is itself lost** -> a frozen interchange layer that no generation is permitted to redefine (6C-7). Contents: object identity (DUR-001), rating envelope (DUR-002), and the hop log (DUR-003). Property: frozen by something outside the generating system, or it is inside the regress. The FORMAT of those fields is itself in the frozen set, because under the compounding case DUR-001 and DUR-002 are no longer a contract between an author and a later reader but a CONTRACT BETWEEN GENERATIONS.
- **DUR-008-N1 the survival set is frozen by the system it is meant to outlive** -> name the external holder and the change rule before the set is called frozen: who holds it, who may change it, and whether a pre-current version is retrievable by someone outside the generating system. A set with no external holder is recorded as UNFROZEN rather than as a control.
- **DUR-015 rate mismatch: the only layer with a shared external referent is the slow one** -> per object, name the layer that holds its referent and that layer's change rate; a claim of durability that rests on substrate slowness is void unless the representation is also frozen.
- **DUR-016 seam multiplication: no owner of the boundary has ever existed, and an automated system must still return a value** -> an interchange contract at each boundary carrying the validation criterion and the envelope, with UNINTERPRETABLE as a distinct return state. Absent that, record the boundary as a silent-selection site rather than as an integration.
- **DUR-017 coupled preemption under load: two controllers acting on each other's incommensurable output** -> at every coupling between independently managed automated systems: a declared interchange contract, an envelope check on the incoming value, and a stated behaviour for UNINTERPRETABLE that is not 'proceed with the value'.

Modes with a partial control, where the mechanism exists and nothing attaches it:

- **D-101 run-to-run variance exceeds the reported difference** -> record the seed, the distribution over at least n identical-configuration runs, and the variance, as part of the as-built. A point estimate without them does not identify an object.
- **D-102 the software stack is not stated, so exact re-execution is impossible in principle** -> deposit the environment, not a description of it: a content-addressed image digest or lockfile set, stored where it outlives the depositing entity.
- **D-103 data leakage propagates across fields and survives peer review** -> record the split construction as a reproducible artifact (the exact partition, or the code and seed that generate it) alongside the number it produced.
- **D-105 readiness is not outcome: a complete-looking record still does not execute** -> schedule a rebuild attempt as an inspection, on a cadence, from the deposit only. A checklist is not evidence of reconstructability; a successful cold rebuild is.
- **DUR-001-N1 probe leakage: the identity control is trained against and stops measuring identity** -> rotation, or per-deployment probe generation from a seed held by the third party, stated as a precondition of the DUR-001 control rather than as a caveat on it.
- **DUR-002 the object is used outside the conditions its rating was established on, with no signal** -> a machine-readable envelope attached to the serving interface, and a return contract in which OUT_OF_ENVELOPE is a distinct return state rather than a low confidence score.
- **DUR-009 correlated substrate and dependency shock: one event, a large synchronous slice** -> state N_eff rather than N wherever redundancy is credited as a control, computed with the shared-node classes of the existing effective-redundancy instrument, and put a budget line against each announced end-of-life date.
- **D-203 as-built drift: the deployed object diverges from the documented one** -> a change record per served object plus a canary set with recorded answers and a probe cadence. The canary mechanism already exists in this repository; adopt it rather than re-deriving it.
- **D-204 no configuration control and no part traceability for the stack** -> a bill of materials for the assembly, content-addressed per part, recorded at deploy time, with the non-code parts (index, prompt, preprocessing, tokeniser) in scope.
- **D-206 custody breaks at every handoff and no handoff is documented** -> a signed handover record at every boundary: named holder before, named holder after, date, and what was transferred (weights, environment, data pointer, rating envelope, reference sample).
- **D-207 format obsolescence: the object survives and the reader does not** -> store the deposit in a reader-independent representation where one exists, and schedule a load test plus migration decision on an interval shorter than the framework's support horizon.
- **D-208 no inspection interval and no action threshold** -> an inspection interval, a held reference set that the component was never fitted on, a re-measurement procedure, and an action threshold stated before the first inspection.
- **DUR-010 no batch record: the run's deviations from its own procedure are unrecorded** -> a batch record per run, retained with the object rather than on the logging system's rotation: restarts, checkpoint lineage, data snapshot identifier, failed or skipped steps, hardware substitutions, and a written disposition for each deviation.
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

## Timeframe and volume accounting (section 6B)

```
HOP BUDGET (order of magnitude; the operator's estimate, not a measurement)
  classical transmission     hop = generational handoff, about 25 years; N over 500 years is about 20 hops
  ML infrastructure          hops = framework break + dependency EOL + storage migration + org or team change + platform deprecation + supersession, several per year; N over 10 years is about 20 to 50 hops
  ratio                      SAME N, compressed by roughly fifty
  the classical loss curve is not being avoided, it is being RUN AT SPEED. Any argument of the form 'this is recent, there has not been time to lose it' is counting the wrong unit.

VOLUME (6B-1)      expected losses ~ (objects) x (hops) x (per-object per-hop failure probability)
  system level     with many objects the expected count is large even at very small per-hop probability: loss is not a risk, it is a rate
  operator level   per object it still looks rare, so no individual operator observes enough events to update. Every operator's local experience honestly reports 'this does not happen.' Detection fails at exactly the level where decisions are made, which is the same shape as entry D-000.
  no values supplied for objects, hops or probability: no values are supplied for objects, hops or probability, and none is estimated here. The form is carried for its shape; putting numbers on it would be the projection inflation F_D forbids.

CORRELATION (6B-2) objects share hops: one framework break, vendor EOL, platform sunset or region retirement applies to a large correlated fraction of the population at once. So it is not many independent small draws but a small number of correlated draws each taking a large slice.
  register rule    any entry claiming redundancy as an existing_control must state what the redundant copies DO NOT SHARE. Copies on the same platform, in the same format, under the same dependency stack are one copy for substrate and dependency shock. Enforced by validate.

SHOCK RE-CUT (6B-3)
  V14a   CARRIER SHOCK      genuinely LOW here
  V14b   SUBSTRATE SHOCK    HIGH
  V14c   DEPENDENCY SHOCK   HIGH
  the scheduled kind ought to be the easy case: it is announced in advance. It is not budgeted, so it is not. A planned shock with no budget line behaves exactly like an unplanned one.
  the bits do not rot. The READER is gone. Intact and unreadable is a distinct state from decayed, and it is worse, because it reads as retained (carried in D-207's own text).
```

## Headline

Of the 33 entries that make a reconstruction claim, PARTIAL 16 and NO 17, and NOT ONE scores YES. Section 8 predicted PARTIAL would dominate; it no longer does. The shift came entirely from entries the operator added in rev 6 (ambient precondition, custodian continuity and the three compounding entries), every one of which scores NO, so the expected yield was wrong in the direction of optimism. PARTIAL means enough of the record exists to rebuild something approximate and not enough to identify the object, which looks like adequacy from inside and is the class most likely to be under-reported. 4 further entries govern use or a control rather than rebuild and are scored NOT_APPLICABLE with a stated reason.

