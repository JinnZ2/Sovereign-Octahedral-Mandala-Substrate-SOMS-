"""
failure_register.py -- the durability / reconstructability failure-mode register for ML components used as
infrastructure (WORK ORDER FAILURE-MODE ENUMERATION FOR ML-AS-INFRASTRUCTURE, 2026-09-13). CC0. Stdlib only.

  The deliverable is register.jsonl. This file validates it, audits it against its own mandatory-field rule,
  and generates the human emission. It makes no claim the register does not carry.

  NON-GOALS (header, repeated here): not model behaviour, alignment or misuse; not harm incidents; not a code
  of ethics. Scope is durability and reconstructability only.

  FIDELITY and CUSTODY are separate axes and are never combined in a field.

  python failure_register.py validate      schema + mandatory-field gate + projection cap + header counts
  python failure_register.py audit         F_C: random 20% audited against the mandatory fields, rejection rate
  python failure_register.py report        reconstruction distribution, detection gap, requirement set, null set
  python failure_register.py falsifiers    F_A..F_H, each with its status and what it rests on
  python failure_register.py coverage      map every section of the work order to the artifact implementing it,
                                          and report any named mechanism with no entry as a GAP
  python failure_register.py emit          write REGISTER.md and outsider_test.md
  python failure_register.py selftest
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "register.jsonl")

# section 2 schema. An entry missing any field is an UNRATED PART and is filed, not discarded.
FIELDS = ("id", "mechanism", "load_condition", "onset", "detection_channel", "detection_latency", "attribution",
          "consequence", "evidence_class", "existing_control", "reconstruction", "validity_range")
# F_C binding constraints: no mechanism, no detection channel, no consequence-under-load, no entry
MANDATORY = ("mechanism", "detection_channel", "consequence")
# section 6B-2 REGISTER RULE: an entry claiming redundancy as a control must say what the copies do NOT share.
# Copies on one platform, in one format, under one dependency stack are ONE copy against substrate and
# dependency shock.
REDUNDANCY_WORDS = ("redundan", "replica", "multiple copies", "several copies", "backup", "mirror")
ONSETS = ("immediate", "drift", "dormant-until-triggered")
EVIDENCE = ("MEASURED", "TRANSPORTED", "PROJECTED")
RECONSTRUCTION = ("YES", "PARTIAL", "NO", "NOT_APPLICABLE")
# NOT_APPLICABLE is for an entry that governs USE or a CONTROL rather than rebuild (section 3B-W, DUR-002).
# It requires a reconstruction_note saying which, so it can never be read as a missing score.
CITATION_STATUS = ("VERIFIED_2026-09-13", "FROM_MEMORY_UNVERIFIED")


def load(path=STORE):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    return rows[0], rows[1:]


def has_detection_gap(e):
    """A detection channel that BEGINS with NONE is a gap even when the field goes on to propose a control:
    'NONE under current practice. PROPOSED: ...' is a gap today and a closure only once the control exists."""
    return str(e.get("detection_channel") or "").strip().upper().startswith("NONE") \
        or "UNBOUNDED" in str(e.get("detection_latency") or "")


def rated(entries):
    return [e for e in entries if e["status"] == "RATED"]


def control_is(e, word):
    """existing_control is prose that begins with its verdict: 'NONE', 'NONE as a gate...', 'PARTIAL: ...'.
    Matching on the prefix rather than on equality is what keeps the requirement set from under-reporting."""
    return str(e.get("existing_control") or "").strip().upper().startswith(word)


def validate(path=STORE):
    hdr, entries = load(path)
    errs = []
    seen = set()
    for e in entries:
        i = e.get("id", "<no id>")
        if i in seen:
            errs.append((i, "duplicate id"))
        seen.add(i)
        missing = [f for f in FIELDS if f not in e]
        if missing:
            errs.append((i, "field absent from the record entirely: %s" % ", ".join(missing)))
        empty = [f for f in MANDATORY if not str(e.get(f) or "").strip()]
        if e["status"] == "RATED" and empty:
            errs.append((i, "RATED entry with an empty mandatory field (%s): must be filed as an UNRATED_PART "
                            "(F_C)" % ", ".join(empty)))
        if e["status"] == "UNRATED_PART" and not empty:
            errs.append((i, "filed UNRATED_PART but every mandatory field is populated: file it as RATED"))
        if e["status"] == "UNRATED_PART" and not e.get("note"):
            errs.append((i, "UNRATED_PART without a note saying which fields are empty and why"))
        if e.get("onset") not in ONSETS:
            errs.append((i, "onset not in %s" % (ONSETS,)))
        if e.get("evidence_class") not in EVIDENCE:
            errs.append((i, "evidence_class not in %s" % (EVIDENCE,)))
        if e.get("reconstruction") not in RECONSTRUCTION:
            errs.append((i, "reconstruction not in %s" % (RECONSTRUCTION,)))
        if e.get("reconstruction") == "NOT_APPLICABLE" and not e.get("reconstruction_note"):
            errs.append((i, "reconstruction NOT_APPLICABLE without a note saying what the entry governs instead"))
        if e.get("reconstruction_trajectory") and not e.get("reconstruction_note"):
            errs.append((i, "a reconstruction trajectory without a note: a score that moves must say so in prose "
                           "as well as in the field (section 3B-W, DUR-003)"))
        ctrl = str(e.get("existing_control") or "").lower()
        if any(w in ctrl for w in REDUNDANCY_WORDS) and not e.get("redundancy_not_shared"):
            errs.append((i, "existing_control claims redundancy without stating what the copies do NOT share "
                           "(section 6B-2 REGISTER RULE)"))
        for other in e.get("coupled_with", []):
            back = [x for x in entries if x["id"] == other]
            if not back:
                errs.append((i, "coupled_with names a missing entry %r" % other))
            elif i not in back[0].get("coupled_with", []):
                errs.append((i, "coupling to %s is not symmetric: the pair must be registered from both sides "
                               "(section 3B-W composition rule)" % other))
        if e.get("proposed_control") and not e.get("control_preconditions"):
            errs.append((i, "a proposed control with no stated preconditions: the control's own failure modes are "
                           "entries, not footnotes (section 3B-W)"))
        for pre in e.get("control_preconditions", []):
            if pre.get("entry") and not [x for x in entries if x["id"] == pre["entry"]]:
                errs.append((i, "control precondition names a missing entry %r" % pre["entry"]))
        for c in e.get("citations", []):
            if c.get("status") not in CITATION_STATUS:
                errs.append((i, "citation without a legal status: %r" % c.get("ref", "")[:40]))
        if e.get("evidence_class") == "TRANSPORTED":
            t = e.get("transport") or {}
            if not t.get("source_domain") or not t.get("why_it_carries"):
                errs.append((i, "TRANSPORTED without a named source domain and a why-it-carries justification (step 3)"))
            if t.get("rests_on_analogy") is not False:
                errs.append((i, "transport rests on analogy: rejected at review (step 3 transport rule)"))
        if e["status"] == "RATED" and control_is(e, "NONE") and not e.get("requirement"):
            errs.append((i, "existing_control NONE with no requirement stated (step 6)"))
    n = len(entries)
    proj = sum(1 for e in entries if e["evidence_class"] == "PROJECTED")
    frac = round(proj / n, 3) if n else 0
    if frac > hdr["projected_cap"]:
        errs.append(("<register>", "PROJECTED fraction %.3f exceeds the stated cap %.2f: the register is a "
                                   "speculation list wearing a register's format (F_D)" % (frac, hdr["projected_cap"])))
    for k, v in (("entries", n), ("projected_entries", proj), ("projected_fraction", frac),
                 ("unrated_parts", sum(1 for e in entries if e["status"] == "UNRATED_PART")),
                 ("detection_none_or_unbounded", sum(1 for e in entries if has_detection_gap(e)))):
        if hdr.get(k) != v:
            errs.append(("<header>", "header %s says %r, recomputed %r" % (k, hdr.get(k), v)))
    return errs


def audit(path=STORE, frac=0.2, seed=13):
    """F_C: audit a random fraction of entries against the mandatory fields and report the rejection rate.
    Author-run, which F_G says is the weak case; the rate is reported with that caveat attached."""
    hdr, entries = load(path)
    rng = random.Random(seed)
    k = max(1, round(frac * len(entries)))
    sample = rng.sample(sorted(entries, key=lambda e: e["id"]), k)
    rejected = []
    for e in sample:
        empty = [f for f in MANDATORY if not str(e.get(f) or "").strip()]
        if empty:
            rejected.append({"id": e["id"], "empty": empty, "filed_as": e["status"]})
    full = [e["id"] for e in entries if [f for f in MANDATORY if not str(e.get(f) or "").strip()]]
    return {"sampled": [e["id"] for e in sample], "n_sampled": k, "of": len(entries), "seed": seed,
            "rejected": rejected, "rejection_rate": round(len(rejected) / k, 3),
            "whole_register_rejected": full, "whole_register_rejection_rate": round(len(full) / len(entries), 3),
            "sample_caveat": ("the 20 percent sample missed %d of the %d rejectable entries, so the sampled rate "
                              "understates the register: read the whole-register rate beside it"
                              % (len(full) - len(rejected), len(full))) if len(rejected) < len(full) else
                             "the sample contains every rejectable entry in the register",
            "caveat": "the audit was run by the register's author against the author's own field definitions. "
                      "F_G is the test that would make it evidence, and F_G is NOT RUN."}


def report(path=STORE):
    hdr, entries = load(path)
    R = rated(entries)
    dist = {}
    for e in entries:
        dist[e["reconstruction"]] = dist.get(e["reconstruction"], 0) + 1
    claiming = [e for e in entries if e["reconstruction"] != "NOT_APPLICABLE"]
    by_section = {}
    for e in entries:
        by_section.setdefault(e["section"], []).append(e["id"])
    gap = [e["id"] for e in entries if has_detection_gap(e)]
    reqs = [{"id": e["id"], "title": e["title"], "requirement": e["requirement"]}
            for e in R if control_is(e, "NONE") and e.get("requirement")]
    partial_reqs = [{"id": e["id"], "title": e["title"], "requirement": e["requirement"]}
                    for e in R if control_is(e, "PARTIAL") and e.get("requirement")]
    cites = [(c.get("status"), c.get("ref")) for e in entries for c in e.get("citations", [])]
    return {"entries": len(entries), "rated": len(R), "unrated_parts": len(entries) - len(R),
            "reconstruction_distribution": dist,
            "reconstruction_headline": "Of the %d entries that make a reconstruction claim, PARTIAL is modal (%d) and "
                                       "NOT ONE scores YES. PARTIAL means enough of the record exists to rebuild "
                                       "something approximate and not enough to identify the object, which looks like "
                                       "adequacy from inside and is the class most likely to be under-reported. "
                                       "%d further entries govern use or a control rather than rebuild and are scored "
                                       "NOT_APPLICABLE with a stated reason."
                                       % (len(claiming), dist.get("PARTIAL", 0), dist.get("NOT_APPLICABLE", 0)),
            "coupled_pairs": sorted({tuple(sorted((e["id"], o))) for e in entries for o in e.get("coupled_with", [])}),
            "proposed_controls": [{"id": e["id"], "proposed": e["proposed_control"],
                                   "preconditions": [p.get("entry") or p.get("note") for p in e.get("control_preconditions", [])]}
                                  for e in entries if e.get("proposed_control")],
            "by_section": by_section, "detection_gap_entries": gap,
            "detection_gap_note": "these are the high-priority set: they cannot generate the evidence that would make "
                                  "fixing them mandatory",
            "requirements_where_no_control_exists": reqs,
            "requirements_where_control_is_partial": partial_reqs,
            "null_set": hdr["null_set"],
            "hop_accounting": hdr["hop_budget"],
            "length_watch": hdr["length_watch"],
            "volume_and_correlation": {"volume": hdr["volume_accounting"], "correlation": hdr["independence_correction"]},
            "shock_exposure": hdr["shock_recut"],
            "entries_with_a_real_detection_channel": [e["id"] for e in entries if not has_detection_gap(e)],
            "citations": {"verified_this_session": sum(1 for s, _ in cites if s == "VERIFIED_2026-09-13"),
                          "from_memory_unverified": sum(1 for s, _ in cites if s == "FROM_MEMORY_UNVERIFIED")},
            "projected_fraction": hdr["projected_fraction"], "projected_cap": hdr["projected_cap"]}


def falsifiers(path=STORE):
    hdr, entries = load(path)
    transports = [e for e in entries if e["evidence_class"] == "TRANSPORTED"]
    survived = [e["id"] for e in transports if (e.get("transport") or {}).get("rests_on_analogy") is False
                and (e.get("transport") or {}).get("why_it_carries")]
    a = audit(path)
    return {
        "F_A_bridge_transport_valid": {
            "status": "PASS" if survived else "FAIL -> cut the transport section and run on 3A alone",
            "transported_entries": len(transports), "survived_justification": survived,
            "reads": "each transported entry states an abstract structure (a record insufficient to rebuild the "
                     "object) rather than a resemblance between domains. The two highest-value transports are the "
                     "retained reference sample (D-201) and the stamped validity envelope (D-202): both are cheap, "
                     "both are mandatory in their home domain, neither exists here."},
        "F_B_prior_art": {
            "status": "CHECKED, NOT REDUNDANT, SCOPED TO THE RESIDUAL",
            "catalogues_that_exist_and_are_harm_scoped": [
                "MIT AI Risk Repository: 1700+ risks from 74 frameworks, 7 domains / 24 subdomains, causal taxonomy "
                "(entity, intentionality, timing). Durability and reconstructability are not a domain.",
                "AI Incident Database and the MIT AI Incident Tracker: 1300+ reported incidents classified by harm "
                "type (10 harm categories). Incident-sourced by construction, so it cannot hold a mode with "
                "detection_channel NONE.",
                "Microsoft / Berkman Klein Failure Modes in Machine Learning (arXiv 1911.11034): intentional and "
                "unintentional failure modes, security-scoped."],
            "adjacent_work_that_covers_part_of_the_residual": [
                "Sculley et al. Hidden Technical Debt in ML Systems (2015): mechanism-level and closest in spirit; no "
                "detection-channel field, no reconstruction score, not a register.",
                "ML Test Score (Breck et al. 2017): a rubric of controls, which is the requirement set rather than the "
                "failure enumeration.",
                "ReproScore (arXiv 2605.13275, 2026): readiness versus outcome for RESEARCH SOFTWARE artifacts, "
                "measured over 423 repositories. Closest measured anchor for D-102 and D-105; scope is artifacts, not "
                "deployed objects.",
                "Documentation templates (Model Cards, Datasheets, Data Statements, FactSheets): they add fields; none "
                "enumerates what happens when the fields are absent, and none is mandatory."],
            "residual_this_register_occupies": "a mechanism-level enumeration scoped to durability and "
                                               "reconstructability, carrying a detection channel (permitted to be "
                                               "NONE) and a reconstruction score, for a fixed deployment class.",
            "caveat": "the prior-art check was four targeted searches on one day. It establishes that the major "
                      "catalogues are harm-scoped; it does not establish that no durability catalogue exists anywhere."},
        "F_C_unbounded_scope": {"status": "AUDITED", "sampled_rejection_rate": a["rejection_rate"],
                                "sample": a["sampled"], "rejected_in_sample": a["rejected"],
                                "whole_register_rejection_rate": a["whole_register_rejection_rate"],
                                "whole_register_rejected": a["whole_register_rejected"],
                                "sample_caveat": a["sample_caveat"], "caveat": a["caveat"]},
        "F_D_projection_inflation": {
            "status": "UNDER CAP, NARROWLY",
            "projected_fraction": hdr["projected_fraction"], "cap": hdr["projected_cap"],
            "reads": "one third of the register is projection. That is under the stated cap and close enough to it "
                     "that the next projected entry added without a measured or transported anchor should displace "
                     "one instead."},
        "F_E_the_enumeration_is_not_the_mechanism": {
            "status": "STATED, AND THE HONEST ANSWER IS MOSTLY NOTHING",
            "forcing_functions_that_exist": [
                "EU AI Act Article 12 (automatic logging over the system lifetime) and Article 26 (deployer retention "
                "of logs, minimum six months), plus Annex IV technical documentation. Real, binding, and scoped to the "
                "Act's high-risk categories. The six-month floor is shorter than every reconstruction question here.",
                "FDA Predetermined Change Control Plan, final guidance 2024-12-03: a pre-authorised modification "
                "protocol with an impact assessment. This is as-built drift control with teeth, for AI-enabled "
                "medical device software functions only."],
            "what_would_make_this_binding": "attributable, expensive failure. Neither exists for the fixed deployment "
                                            "class, because entry D-000 removes attribution and distributes the cost. "
                                            "Publishing the register changes nothing on its own, and this deliverable "
                                            "does not claim otherwise.",
            "the_cheapest_available_lever": "procurement. A buyer can require D-201 (retained reference sample), D-202 "
                                            "(stamped envelope) and D-204 (bill of materials) as delivery conditions "
                                            "without any regulator acting, because all three are artifacts rather than "
                                            "behaviours."},
        "F_F_artifact_present_assumption": {
            "status": "CHECKED PER ENTRY",
            "reads": "the classical lost-technology cases retained the object and lost the documentation, which is "
                     "why reconstruction was possible. Here the object is usually not retained either. D-207 is the "
                     "one entry where the object IS retained and the reader is lost, and it names what and where. "
                     "D-201 and D-301 are the opposite case and are worded as WAS NEVER CAPTURED, not WILL BE LOST.",
            "entries_that_assume_something_recoverable_exists": ["D-207 (the deposit's bytes)",
                                                                 "D-105 (a retained artifact to probe)",
                                                                 "DUR-003 (an object still being carried at hop N)",
                                                                 "DUR-004 (the object is present and under load)"],
            "the_inverse_case": "DUR-004 is where the classical intuition inverts. Pyramids: object retained, load "
                                "off, comprehension gap harmless. Stranded: object retained, load ON, comprehension "
                                "gap IS the liability. A surviving artifact is not a recoverable technology, and in "
                                "this case it is a system that works and cannot be changed.",
            "substrate_correction": "D-207 no longer reads as decay. The bits do not rot; the READER is gone. Intact "
                                    "and unreadable is a distinct state from decayed and it is worse, because it "
                                    "reads as retained."},
        "F_I_independence": {
            "status": "PASS" if (hdr.get("volume_accounting") and hdr.get("independence_correction")
                                and any(e["id"] == "DUR-005" for e in entries)) else
                      "FAIL: the volume argument appears without its correlation correction",
            "volume_present": bool(hdr.get("volume_accounting")),
            "correlation_present": bool(hdr.get("independence_correction")),
            "correlation_entry": "DUR-005 (correlated substrate and dependency shock)",
            "reads": "the expected-count form (objects x hops x per-hop probability) is carried in the header ONLY "
                     "beside the correction that objects share hops, so the two modes are never reported as one. "
                     "VOLUME gives a steady individually-invisible rate (DUR-003); CORRELATION gives synchronous "
                     "block losses that defeat redundancy counted as independent (DUR-005). No values for objects, "
                     "hops or probability are supplied: only the hop-count order of magnitude, which is the "
                     "operator's estimate and is labelled as such.",
            "register_rule_enforced": "validate refuses any entry claiming redundancy as a control without stating "
                                      "what the copies do not share"},
        "F_G_reader_precondition_blindness": {
            "status": "NOT RUN",
            "why": "the test requires a reader outside the domain, who is not available to this session. Running it "
                   "on the author would reproduce exactly the blindness it tests for.",
            "packaged": "outsider_test.md: the field definitions plus five entries stripped of their classifications, "
                        "for an outside reader to classify. Disagreement on a field means that field is "
                        "underspecified, and the field definition is what gets fixed.",
            "known_weak_definitions": ["onset: 'drift' versus 'dormant-until-triggered' is a judgement call on any "
                                       "mode that both accumulates and needs a trigger (D-203, D-205)",
                                       "reconstruction PARTIAL versus NO: the boundary is 'approximately rebuild' "
                                       "versus 'identify', which is stated in the header and not operationalised",
                                       "existing_control PARTIAL: means the mechanism exists somewhere, not that this "
                                       "deployment uses it"]},
        "F_H_event_definition": {"status": "DEFINED BEFORE ANY COUNT", "definition": hdr["event_definition_F_H"],
                                 "counts_present_in_this_deliverable": "entry counts, citation counts and the "
                                                                       "reconstruction distribution only. No failure "
                                                                       "count appears anywhere."},
    }


# ---- coverage audit: the work order mapped to artifacts, with GAP detection ------------------------
# Each row: (section, what the order asks for, entry ids that carry it, header keys that carry it, code hooks).
# A row is a GAP when it names no artifact, or names one that is not in the store.
COVERAGE = [
    ("0 non-goals", "state the non-goals and the durability-only scope", [], ["non_goals", "deployment_class"], []),
    ("1 entry 0", "the detection gap itself, and a detection_channel field permitted to be NONE", ["D-000"],
     ["detection_none_or_unbounded", "detection_gap_definition"], ["has_detection_gap"]),
    ("2 schema", "the 13 fields; a missing field is an UNRATED PART, filed not discarded", ["D-401", "D-402"],
     ["unrated_parts"], ["FIELDS", "MANDATORY", "validate"]),
    ("2 projection cap", "PROJECTED may not exceed a stated fraction", [], ["projected_fraction", "projected_cap"],
     ["validate"]),
    ("3A variance", "run-to-run variance: a reported number does not identify the object", ["D-101"], [], []),
    ("3A versions", "software and dependency versions unstated, so re-execution is impossible in principle", ["D-102"], [], []),
    ("3A leakage", "data leakage across fields, corrected results erasing claimed superiority", ["D-103"], [], []),
    ("3A significance", "no agreed significance measure, so point estimates ship without a distribution", ["D-104"], [], []),
    ("3A compounding", "the defect is not visible from reading the report", ["D-106"], [], []),
    ("3B structural", "as-built drift and undocumented field modification", ["D-203"], [], []),
    ("3B structural", "load rating LOST", ["DUR-007"], [], []),
    ("3B structural", "inspection interval unset", ["D-208"], [], []),
    ("3B aviation", "configuration control and part traceability", ["D-204"], [], []),
    ("3B aviation", "latent fault dormant until an unusual load combination", ["D-205"], [], []),
    ("3B pressure vessel", "stamped validity envelope and certified test conditions", ["DUR-002", "DUR-002-N1"], [], []),
    ("3B pressure vessel", "material provenance, including what was excluded", ["D-302"], [], []),
    ("3B pharmaceutical", "retained reference sample", ["DUR-001", "DUR-001-N1", "DUR-001-N2"], [], []),
    ("3B pharmaceutical", "batch records: what was actually done, with deviations dispositioned", ["DUR-006"], [], []),
    ("3B pharmaceutical", "custody chain", ["D-206"], [], []),
    ("3B nuclear transport", "continuous custody, documented handoff at every stop", ["D-206"], [], []),
    ("3B archive", "format obsolescence, dependency on a reader that no longer exists", ["D-207"], [], []),
    ("3B transport rule", "every transported entry states why the mechanism carries; analogy is rejected", [],
     [], ["validate", "falsifiers:F_A"]),
    ("3B-W DUR-001", "worked entry, schema filled, with its proposed control", ["DUR-001"], [], []),
    ("3B-W DUR-002", "worked entry, schema filled, with its return contract", ["DUR-002"], [], []),
    ("3B-W DUR-003", "migration attrition", ["DUR-003"], [], []),
    ("3B-W DUR-004", "stranded under load", ["DUR-004"], [], []),
    ("3B-W composition", "DUR-001 and DUR-002 registered as a coupled pair", ["DUR-001", "DUR-002"],
     ["composition_rule"], ["validate"]),
    ("3B-W control failures", "the controls' own failure modes as entries, not footnotes",
     ["DUR-001-N1", "DUR-001-N2", "DUR-002-N1"], [], ["validate"]),
    ("3C near-miss", "walk reconstruction backwards; everything found is PROJECTED unless a transport anchors it",
     ["D-301", "D-302", "D-303", "D-304"], [], []),
    ("5 load rating", "as-built, material provenance, load rating, inspection interval, as-built drift",
     ["D-102", "D-302", "DUR-002", "D-208", "D-203"], [], []),
    ("5 silent substitution", "cross-reference the existing marker rather than re-derive", ["D-203", "DUR-001"], [], []),
    ("6 custody axis", "fidelity and custody never collapsed", [], ["fidelity_vs_custody"], []),
    ("6 proprietary boundary", "a path through one commercial entity is UNBOUNDED and NO by default", ["D-301"], [], []),
    ("6B hop budget", "account in hops, not years", [], ["hop_budget"], ["emit"]),
    ("6B-1 volume", "the expected-count form, with the system and operator levels kept apart", ["DUR-003"],
     ["volume_accounting"], []),
    ("6B-2 correlation", "objects share hops; correlation needs its own entry", ["DUR-005"],
     ["independence_correction"], ["falsifiers:F_I"]),
    ("6B-2 register rule", "redundancy as a control must state what the copies do not share", ["DUR-005"],
     ["independence_correction"], ["REDUNDANCY_WORDS", "validate"]),
    ("6B-3 shock re-cut", "carrier low; substrate and dependency high and scheduled", ["D-207"], ["shock_recut"], []),
    ("6B-3 substrate", "the bits do not rot, the reader is gone; intact and unreadable reads as retained", ["D-207"], [], []),
    ("operator 2026-09-13", "degradation vs regress as a class boundary; per-hop instrumentation reaches only the first",
     ["DUR-003", "DUR-008"], ["degradation_vs_regress"], []),
    ("operator 2026-09-13", "the arrest: freeze what must survive a hop, from outside the generating system",
     ["DUR-008", "DUR-008-N1"], ["degradation_vs_regress"], []),
    ("7 F_A..F_I", "every falsifier answered with a status", [], [], ["falsifiers"]),
    ("Step 5", "reconstruction distribution as a headline", [], [], ["report"]),
    ("Step 6", "requirement set for every entry with no control", [], [], ["report"]),
    ("Step 7", "the null set: modes checked and found already controlled", [], ["null_set"], []),
]


def coverage(path=STORE):
    hdr, entries = load(path)
    ids = {e["id"] for e in entries}
    rows, gaps = [], []
    src = open(os.path.abspath(__file__)).read()
    for section, ask, eids, hkeys, hooks in COVERAGE:
        missing_e = [i for i in eids if i not in ids]
        missing_h = [k for k in hkeys if k not in hdr]
        missing_c = [c for c in hooks if c.split(":")[-1] not in src]
        status = "COVERED"
        if not (eids or hkeys or hooks):
            status = "GAP: nothing in the register carries this"
        elif missing_e or missing_h or missing_c:
            status = "GAP: missing %s" % ", ".join(missing_e + missing_h + missing_c)
        rows.append({"section": section, "asks_for": ask, "entries": eids, "header_keys": hkeys,
                     "code": hooks, "status": status})
        if status != "COVERED":
            gaps.append(rows[-1])
    # every entry should be reachable from some coverage row, or the register has content the order did not ask for
    claimed = {i for _, _, eids, _, _ in COVERAGE for i in eids}
    unmapped = sorted(ids - claimed)
    return {"rows": rows, "gaps": gaps, "n_rows": len(rows), "n_gaps": len(gaps),
            "entries_not_mapped_to_any_order_section": unmapped,
            "limit": hdr.get("coverage_limit"),
            "reads": "a GAP is a named mechanism with no entry. Entries not mapped to an order section are either "
                     "supporting entries derived from one (D-105 readiness, D-403+ if any) or scope this register "
                     "added on its own, and either way they should be justified rather than assumed."}


def emit(path=STORE):
    hdr, entries = load(path)
    rep = report(path)
    L = ["# Durability and reconstructability failure-mode register", "",
         "BUILD PRODUCT of `failure_register.py emit`; never hand-edit. The store is `register.jsonl`.", "",
         "```", "artifact      %s" % hdr["artifact"], "deployment class", "  %s" % hdr["deployment_class"], "",
         "NON-GOALS"]
    for g in hdr["non_goals"]:
        L.append("  - %s" % g)
    L += ["", "entries %d (rated %d, unrated parts %d) | projected %.1f%% of a %.0f%% cap | detection gap %d entries"
          % (rep["entries"], rep["rated"], rep["unrated_parts"], 100 * hdr["projected_fraction"],
             100 * hdr["projected_cap"], len(rep["detection_gap_entries"])),
          "reconstruction  %s" % "  ".join("%s %d" % (k, v) for k, v in sorted(rep["reconstruction_distribution"].items())),
          "citations  verified this session %d | from memory, unverified %d"
          % (rep["citations"]["verified_this_session"], rep["citations"]["from_memory_unverified"]), "```", "",
          "FIDELITY and CUSTODY are separate axes. " + hdr["fidelity_vs_custody"], "",
          "EVENT DEFINITION (F_H). " + hdr["event_definition_F_H"], ""]
    sec_names = {"0": "Entry 0 - the detection gap itself", "3A": "3A MEASURED",
                 "3B-W": "3B-W WORKED ENTRIES - the two priority transports and the failure modes of their controls",
                 "3B": "3B TRANSPORTED", "3C": "3C PROJECTED and UNRATED PARTS"}
    for sec in ("0", "3A", "3B-W", "3B", "3C"):
        L += ["## %s" % sec_names[sec], ""]
        for e in [x for x in entries if x["section"] == sec]:
            L.append("### %s  %s%s" % (e["id"], e["title"], "  [UNRATED PART]" if e["status"] == "UNRATED_PART" else ""))
            L.append("")
            L.append("- mechanism: %s" % e["mechanism"])
            L.append("- load condition: %s" % e["load_condition"])
            L.append("- onset: %s | evidence: %s | reconstruction: %s" % (e["onset"], e["evidence_class"], e["reconstruction"]))
            L.append("- detection channel: %s" % (e["detection_channel"] or "EMPTY (unrated part)"))
            L.append("- detection latency: %s" % (e["detection_latency"] or "EMPTY (unrated part)"))
            L.append("- attribution: %s" % e["attribution"])
            L.append("- consequence: %s" % e["consequence"])
            L.append("- existing control: %s" % (e["existing_control"] or "EMPTY (unrated part)"))
            L.append("- validity range: %s" % (e["validity_range"] or "EMPTY (unrated part)"))
            if e.get("transport"):
                t = e["transport"]
                L.append("- transported from %s: %s" % (t["source_domain"], t["home_practice"]))
                L.append("- why it carries: %s" % t["why_it_carries"])
            if e.get("reconstruction_trajectory"):
                L.append("- reconstruction trajectory: %s" % e["reconstruction_trajectory"])
            if e.get("redundancy_not_shared"):
                L.append("- redundant copies do NOT share: %s" % e["redundancy_not_shared"])
            if e.get("reconstruction_note"):
                L.append("- reconstruction note: %s" % e["reconstruction_note"])
            if e.get("proposed_control"):
                L.append("- PROPOSED control: %s" % e["proposed_control"])
            for p in e.get("control_preconditions", []):
                L.append("- control precondition: %s%s" % (p.get("note", ""),
                                                           " (entry %s)" % p["entry"] if p.get("entry") else ""))
            if e.get("coupled_with"):
                L.append("- coupled with: %s (neither control works alone)" % ", ".join(e["coupled_with"]))
            if e.get("supersedes"):
                L.append("- supersedes: %s (operator-supplied worked entry, section 3B-W)" % e["supersedes"])
            if e.get("requirement"):
                L.append("- minimum artifact that would close it: %s" % e["requirement"])
            if e.get("cross_reference"):
                L.append("- cross-reference (not re-derived): %s" % "; ".join(e["cross_reference"]))
            for c in e.get("citations", []):
                L.append("- citation [%s]: %s%s" % (c["status"], c["ref"], " (%s)" % c["url"] if c.get("url") else ""))
            if e.get("note"):
                L.append("- note: %s" % e["note"])
            L.append("")
    L += ["## Requirement set (step 6)", "", "Modes with no existing control, and the minimum artifact that would close each:", ""]
    for r in rep["requirements_where_no_control_exists"]:
        L.append("- **%s %s** -> %s" % (r["id"], r["title"], r["requirement"]))
    L += ["", "Modes with a partial control, where the mechanism exists and nothing attaches it:", ""]
    for r in rep["requirements_where_control_is_partial"]:
        L.append("- **%s %s** -> %s" % (r["id"], r["title"], r["requirement"]))
    L += ["", "## Null set (step 7): modes checked and found already controlled", ""]
    for n in rep["null_set"]:
        L.append("- **%s** %s" % (n["id"], n["mode"]))
        L.append("    - %s (%s)" % (n["why_controlled"], n["control_status"]))
        L.append("    - residual: %s" % n["residual"])
    L += ["", "## Timeframe and volume accounting (section 6B)", "", "```"]
    hb = hdr["hop_budget"]
    L.append("HOP BUDGET (order of magnitude; the operator's estimate, not a measurement)")
    for k, v in hb["budget"].items():
        L.append("  %-26s %s" % (k, v))
    L.append("  %s" % hb["consequence"])
    L.append("")
    L.append("VOLUME (6B-1)      %s" % hdr["volume_accounting"]["form"])
    L.append("  system level     %s" % hdr["volume_accounting"]["system_level"])
    L.append("  operator level   %s" % hdr["volume_accounting"]["operator_level"])
    L.append("  no values supplied for objects, hops or probability: %s" % hdr["volume_accounting"]["no_values"])
    L.append("")
    L.append("CORRELATION (6B-2) %s" % hdr["independence_correction"]["correction"])
    L.append("  register rule    %s" % hdr["independence_correction"]["register_rule"])
    L.append("")
    L.append("SHOCK RE-CUT (6B-3)")
    for k, v in hdr["shock_recut"]["classes"].items():
        L.append("  %-6s %-18s %s" % (k, v["name"], v["exposure"]))
    L.append("  %s" % hdr["shock_recut"]["scheduled_note"])
    L.append("  %s" % hdr["shock_recut"]["substrate_correction"])
    L += ["```", "", "## Headline", "", rep["reconstruction_headline"], ""]
    open(os.path.join(HERE, "REGISTER.md"), "w").write("\n".join(L) + "\n")

    # F_G test sheet: five entries stripped of their classifications, for an outside reader
    fg = falsifiers(path)["F_G_reader_precondition_blindness"]
    pick = [e for e in entries if e["id"] in ("D-102", "D-202", "D-203", "D-302", "D-401")]
    T = ["# F_G reader-precondition test (NOT RUN)", "",
         "Hand this to someone outside the domain. They classify each of the five entries on the four fields below,",
         "using only the definitions given. Disagreement with the register's own classification means the FIELD",
         "DEFINITION is underspecified, and the definition is what gets fixed, not the reader.", "",
         "Status: NOT RUN. " + fg["why"], "",
         "## Field definitions, as they must stand without asking the author", "",
         "- **onset**: immediate (present from the moment of deployment) | drift (accumulates while in service) | "
         "dormant-until-triggered (present from the start, expresses only on a particular condition)",
         "- **detection channel**: the signal that would reveal this, or NONE if no signal would. NONE is an answer.",
         "- **reconstruction**: YES (the object can be rebuilt and identified from the retained record) | PARTIAL "
         "(something approximate can be rebuilt; the object cannot be identified) | NO",
         "- **evidence class**: MEASURED (a study established it) | TRANSPORTED (the mechanism is established in "
         "another domain and the abstract structure carries) | PROJECTED (no anchor)", "",
         "## Known-weak definitions (the reader is not told these in advance)", ""]
    for w in fg["known_weak_definitions"]:
        T.append("- %s" % w)
    T += ["", "## Entries to classify", ""]
    for e in pick:
        T.append("### %s" % e["id"])
        T.append("")
        T.append("mechanism: %s" % e["mechanism"])
        T.append("")
        T.append("load condition: %s" % e["load_condition"])
        T.append("")
        T.append("consequence: %s" % e["consequence"])
        T.append("")
        T.append("onset: ______  detection channel: ______  reconstruction: ______  evidence class: ______")
        T.append("")
    open(os.path.join(HERE, "outsider_test.md"), "w").write("\n".join(T) + "\n")
    return os.path.join(HERE, "REGISTER.md"), os.path.join(HERE, "outsider_test.md")


def selftest():
    errs = validate()
    assert errs == [], errs
    hdr, entries = load()
    # the register is short by design: a long one is a warning sign (section 8). The guard is a TRIPWIRE, and the
    # length is reported with its growth accounting rather than silently accommodated.
    assert len(entries) <= 35, len(entries)
    lw = hdr["length_watch"]
    assert lw["entries"] == len(entries) and lw["growth"]["rev 5"] == len(entries)
    assert "no longer short" in lw["status"] and "displace" in lw["status"]
    assert "No entry was self-generated" in lw["accounting"]
    # entry 0 is the detection gap and it is first
    assert entries[0]["id"] == "D-000" and entries[0]["detection_channel"] == "NONE"
    # every section is populated and measured entries exist to set the floor
    secs = {e["section"] for e in entries}
    assert secs == {"0", "3A", "3B-W", "3B", "3C"}
    assert sum(1 for e in entries if e["evidence_class"] == "MEASURED") >= 5
    # projection cap holds and is reported
    assert hdr["projected_fraction"] <= hdr["projected_cap"]
    # F_A: at least one transport survives without appeal to resemblance
    f = falsifiers()
    assert f["F_A_bridge_transport_valid"]["status"] == "PASS"
    assert all((e.get("transport") or {}).get("rests_on_analogy") is False
               for e in entries if e["evidence_class"] == "TRANSPORTED")
    # F_C audit: the two UNRATED PARTS are the only rejectable entries, and the rate is computed not asserted
    a = audit(frac=1.0)
    assert set(a["whole_register_rejected"]) == {"D-401", "D-402"}
    assert {r["id"] for r in a["rejected"]} == {"D-401", "D-402"}
    assert all(r["filed_as"] == "UNRATED_PART" for r in a["rejected"])            # filed, not discarded
    assert a["rejection_rate"] == round(2 / len(entries), 3)
    # F_G is NOT RUN and says so
    assert f["F_G_reader_precondition_blindness"]["status"] == "NOT RUN"
    # the 20 percent sample can miss the rejectable entries; the whole-register rate is reported beside it
    a20 = audit()
    assert a20["whole_register_rejection_rate"] >= a20["rejection_rate"] or a20["sample_caveat"]
    assert "sample_caveat" in f["F_C_unbounded_scope"]
    # F_H: no failure count anywhere; only entry, citation and distribution counts
    assert "EVENT" in hdr["event_definition_F_H"] and "fidelity" in hdr["event_definition_F_H"]
    # F_E does not claim publishing is sufficient
    fe = f["F_E_the_enumeration_is_not_the_mechanism"]
    assert "changes nothing on its own" in fe["what_would_make_this_binding"]
    assert len(fe["forcing_functions_that_exist"]) == 2
    # step 7 null set is non-empty: a register that finds everything broken is advocating
    assert len(hdr["null_set"]) >= 3
    for n in hdr["null_set"]:
        assert n["residual"] and n["why_controlled"]
    # step 5 headline: PARTIAL is modal
    rep = report()
    d = rep["reconstruction_distribution"]
    assert "YES" not in d and d["PARTIAL"] == max(v for k, v in d.items() if k != "NOT_APPLICABLE")
    assert d.get("NOT_APPLICABLE", 0) == 4
    assert len(rep["entries_with_a_real_detection_channel"]) >= 1                  # DUR-004 at minimum
    # every RATED entry with no control states a requirement (step 6)
    for e in rated(entries):
        if control_is(e, "NONE"):
            assert e.get("requirement")
    assert len(rep["requirements_where_no_control_exists"]) >= 6          # the prefix match, not equality
    assert {"D-000", "D-104", "D-205", "D-301", "D-304", "DUR-001", "DUR-001-N2", "DUR-002-N1"} \
        <= {r["id"] for r in rep["requirements_where_no_control_exists"]}
    # custody entries whose path runs through one firm are NO / UNBOUNDED by the section 6 rule
    d301 = [e for e in entries if e["id"] == "D-301"][0]
    assert d301["reconstruction"] == "NO" and "UNBOUNDED" in d301["detection_latency"]
    # section 3B-W: the two priority transports, their coupling, and the three control-failure entries
    by_id = {e["id"]: e for e in entries}
    for i in ("DUR-001", "DUR-002", "DUR-001-N1", "DUR-001-N2", "DUR-002-N1"):
        assert i in by_id, i
    assert by_id["DUR-001"]["supersedes"] == "D-201" and by_id["DUR-002"]["supersedes"] == "D-202"
    assert "D-201" not in by_id and "D-202" not in by_id                         # superseded, not duplicated
    # composition: the pair is registered from both sides
    assert by_id["DUR-001"]["coupled_with"] == ["DUR-002"] and by_id["DUR-002"]["coupled_with"] == ["DUR-001"]
    assert ("DUR-001", "DUR-002") in rep["coupled_pairs"]
    # DUR-002 governs use, not rebuild, and says so instead of scoring a rebuild it does not measure
    assert by_id["DUR-002"]["reconstruction"] == "NOT_APPLICABLE" and "load rating" in by_id["DUR-002"]["reconstruction_note"]
    # the sharp carried disciplines, each asserted in the entry text rather than in prose here
    assert "UNRATED" in by_id["DUR-002"]["consequence"] or "unrated" in by_id["DUR-002"]["consequence"]
    assert "OUT_OF_ENVELOPE" in by_id["DUR-002"]["detection_channel"] and "confidence" in by_id["DUR-002"]["detection_channel"]
    assert "distinct" in by_id["DUR-002-N1"]["requirement"]                      # blank is not wide
    assert "IDENTITY" in by_id["DUR-001"]["reconstruction_note"] and "DUR-001-N2" in by_id["DUR-001"]["reconstruction_note"]
    # a proposed control carries its own failure modes as entries, not footnotes
    for i in ("DUR-001", "DUR-002"):
        assert by_id[i]["proposed_control"] and by_id[i]["control_preconditions"]
        assert any(p.get("entry") for p in by_id[i]["control_preconditions"])
    # DUR-002's control is PARTIAL, not NONE: the null-set discipline applied inside an entry
    assert control_is(by_id["DUR-002"], "PARTIAL") and not control_is(by_id["DUR-002"], "NONE")
    # DUR-001-N2 keeps identity and procedure reproducibility separate and points at their anchors
    n2 = by_id["DUR-001-N2"]
    assert "D-101" in json.dumps(n2["cross_reference"]) and "D-102" in json.dumps(n2["cross_reference"])
    assert "never summed" in n2["requirement"] or "not summed" in n2["requirement"]
    # rev 3: DUR-003 migration attrition, DUR-004 stranded under load, DUR-005 correlated shock
    for i in ("DUR-003", "DUR-004", "DUR-005"):
        assert i in by_id, i
    # DUR-003 is not DUR-001 and not D-207: carried-forward, not unidentifiable and not unreadable
    assert "no longer being carried" in by_id["DUR-003"]["note"] and "DUR-001" in by_id["DUR-003"]["note"]
    assert by_id["DUR-003"]["reconstruction_trajectory"] and by_id["DUR-003"]["reconstruction"] == "PARTIAL"
    assert "value" in by_id["DUR-003"]["mechanism"]                               # the per-hop selection filter
    # DUR-004 is the one entry with a detection channel that is weak but real, and it is measurable today
    assert not has_detection_gap(by_id["DUR-004"]), by_id["DUR-004"]["detection_channel"]
    assert by_id["DUR-004"]["id"] in rep["entries_with_a_real_detection_channel"]
    assert by_id["DUR-004"]["reconstruction"] == "NO" and "comprehension" in by_id["DUR-004"]["reconstruction_note"]
    assert "bus" in by_id["DUR-004"]["detection_channel"].lower()
    # DUR-005 carries the redundancy rule and points at the existing instrument rather than re-deriving it
    assert by_id["DUR-005"]["redundancy_not_shared"]
    assert "effective-redundancy-audit" in json.dumps(by_id["DUR-005"]["cross_reference"])
    assert "N_eff" in by_id["DUR-005"]["requirement"]
    # the REGISTER RULE bites: a synthetic entry claiming redundancy with nothing stated is rejected
    import copy, tempfile
    bad = copy.deepcopy(by_id["D-207"])
    bad["id"] = "SYNTH-1"; bad["existing_control"] = "PARTIAL: redundant copies are kept in two buckets"
    bad.pop("redundancy_not_shared", None)
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tf:
        tf.write(json.dumps(hdr) + "\n")
        for x in entries + [bad]:
            tf.write(json.dumps(x) + "\n")
    ve = validate(tf.name)
    assert any(i == "SYNTH-1" and "do NOT share" in m for i, m in ve), ve
    os.unlink(tf.name)
    # 6B-3: the substrate correction is in D-207's own text, not only in the falsifier prose
    assert "do not rot" in by_id["D-207"]["mechanism"] or "does not rot" in by_id["D-207"]["mechanism"]
    assert "reads as retained" in by_id["D-207"]["consequence"]
    # F_I: volume and correlation appear together or neither
    assert f["F_I_independence"]["status"] == "PASS"
    assert hdr["volume_accounting"]["no_values"] and hdr["hop_budget"]["estimate_owner"]
    # rev 4: the coverage audit runs clean, and the two gaps it found are closed
    c = coverage()
    assert c["n_gaps"] == 0, c["gaps"]
    assert "DUR-006" in by_id and "DUR-007" in by_id
    # DUR-006 is the batch record: execution, not intent, with deviations dispositioned
    assert "deviation" in by_id["DUR-006"]["requirement"] and "batch record" in by_id["DUR-006"]["requirement"]
    assert "retention" in by_id["DUR-006"]["detection_channel"] or "retained" in by_id["DUR-006"]["detection_channel"]
    # DUR-007 is the rating lost, not the object lost, and its requirement is re-rate or restrict
    assert by_id["DUR-007"]["reconstruction"] == "NO" and "rating record" in by_id["DUR-007"]["reconstruction_note"]
    assert "UNRATED" in by_id["DUR-007"]["requirement"] and "restrict" in by_id["DUR-007"]["requirement"]
    assert by_id["DUR-007"]["transport"]["rests_on_analogy"] is False
    # the unmapped set is small and known: coverage is an audit, not a rubber stamp
    assert len(c["entries_not_mapped_to_any_order_section"]) <= 4, c["entries_not_mapped_to_any_order_section"]
    # rev 5: the degradation/regress class boundary
    for i in ("DUR-008", "DUR-008-N1"):
        assert i in by_id, i
    dr = hdr["degradation_vs_regress"]
    assert "DUR-003" in dr["degradation"] and "DUR-008" in dr["regress"]
    assert "not touch" in dr["why_it_is_a_class_boundary"] or "does not touch" in dr["why_it_is_a_class_boundary"]
    # the regress entry says its NONE is not the ordinary NONE, and that no per-hop instrument reaches it
    r8 = by_id["DUR-008"]
    assert "not the ordinary NONE" in r8["detection_channel"] and "OUTSIDE" in r8["detection_channel"]
    assert "per-hop instrumentation" in r8["mechanism"] or "per-hop instrumentation" in r8["note"]
    assert r8["evidence_class"] == "PROJECTED" and "lowest weight" in r8["evidence_note"]   # widest consequence, weakest anchor
    assert "own score is subject to the mechanism it describes" in r8["reconstruction_note"]
    # the arrest is what must survive, not how work is done, and the externality is a precondition entry
    assert "not HOW the work is done" in json.dumps(r8["control_preconditions"])
    assert any(p.get("entry") == "DUR-008-N1" for p in r8["control_preconditions"])
    assert "UNFROZEN" in by_id["DUR-008-N1"]["requirement"]
    # the register records that its own coverage result is bounded by the same mechanism
    assert "never 'no mechanism" in hdr["coverage_limit"]
    assert coverage()["limit"] == hdr["coverage_limit"]
    assert "coverage" in json.dumps(r8["cross_reference"])
    # the cited section was not supplied, and the entries say so rather than implying a document
    assert "NOT supplied" in json.dumps(r8["citations"]) and "6C-7" in json.dumps(r8["citations"])
    # citations carry a status and the unverified ones are visible
    assert rep["citations"]["verified_this_session"] >= 6 and rep["citations"]["from_memory_unverified"] >= 6
    # emissions are generated, not hand-written
    md, ot = emit()
    assert os.path.exists(md) and os.path.exists(ot)
    body = open(md).read()
    assert "BUILD PRODUCT" in body and "UNRATED PART" in body and "Null set" in body
    assert "EMPTY (unrated part)" in body                                        # empty is distinct from NONE
    print("failure_register selftest ok")


def main(argv):
    if not argv:
        print(__doc__); return 0
    cmd = argv[0]
    if cmd == "validate":
        errs = validate()
        for i, m in errs:
            print("%-12s %s" % (i, m))
        hdr, entries = load()
        print("register.jsonl: %d entries, %d failing" % (len(entries), len({i for i, _ in errs})))
        return 1 if errs else 0
    if cmd == "audit":
        print(json.dumps(audit(), indent=1)); return 0
    if cmd == "report":
        print(json.dumps(report(), indent=1)); return 0
    if cmd == "falsifiers":
        print(json.dumps(falsifiers(), indent=1)); return 0
    if cmd == "coverage":
        c = coverage()
        for r in c["rows"]:
            print("%-24s %-8s %s" % (r["section"], "OK" if r["status"] == "COVERED" else "GAP",
                                     r["asks_for"] if r["status"] == "COVERED" else r["status"] + " | " + r["asks_for"]))
        print("\n%d rows, %d gaps" % (c["n_rows"], c["n_gaps"]))
        print("LIMIT: %s" % c["limit"])
        if c["entries_not_mapped_to_any_order_section"]:
            print("entries not mapped to an order section: %s" % ", ".join(c["entries_not_mapped_to_any_order_section"]))
        return 1 if c["n_gaps"] else 0
    if cmd == "emit":
        for p in emit():
            print(p)
        return 0
    if cmd == "selftest":
        selftest(); return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
