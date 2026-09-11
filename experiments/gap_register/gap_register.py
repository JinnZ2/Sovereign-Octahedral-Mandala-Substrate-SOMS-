"""
gap_register.py -- a register of MARKS on unmeasured quantities (WORK ORDER gap_register, 2026-09-11).
CC0. stdlib only. One file + REGISTER.jsonl.

  measurand      presence/absence of a MARK on an unmeasured quantity; never the truth of a claim about it
  unit           one entry = one (quantity, excluding-method) pair
  status enum    OPEN | CLOSED_MEASURED | CLOSED_INSTRUMENT_EXISTS | OUT_OF_ENVELOPE | UNKNOWN
                 UNKNOWN has peer status; an entry that cannot be evaluated is UNKNOWN, never OPEN by default
  envelope IN    published methods, standards, code tables, certifications, regulatory channels, benchmarks, corpora
  envelope OUT   intent, motive, fault, what the absent quantity would show if measured

  gap_register.py add       <json-or-@file>   validate + append, assign id
  gap_register.py validate  [file]            V1..V6 on every entry; exit nonzero on any failure
  gap_register.py search    <terms...>        match on index_terms + quantity
  gap_register.py check     <id>              print closure_condition only
  gap_register.py emit      --human|--machine  build products: human/REGISTER.md, machine/register.jsonld
  gap_register.py export    --md [file]       alias: the human emission to stdout or a file
  gap_register.py correlate [--field F]       field x field co-occurrence; adjacency list of overlooked gaps
  gap_register.py strip     <id>              the entry with provenance removed (name-strip probe input)
  gap_register.py kill-sample [file]          bare entries for the kill-rule probe (no framing)
  gap_register.py selftest

  Addendum A (2026-09-11): status is per (entry, field) in status_by_field; the entry-level rollup is derived
  (any OPEN -> OPEN; all CLOSED_* -> CLOSED; else UNKNOWN) and never stored. Fields come from FIELDS.txt.
  check <id> returns a type-specific instruction: T2 a declaration target, T4 a venue target.

  V1  required fields present and non-empty (null allowed only in venue_check, confound)
  V2  closure_condition checkable: names an observable (record, table, count, ...) and is not only a modal
  V3  refutation non-empty and distinct from closure_condition
  V4  no accusatory construction: proper names only inside provenance[]; no fault lexicon anywhere
  V5  index_terms >= 3, and no term is a coinage unique to this entry (coinage = hyphen/digit/capital/camelCase
      or a 15+ letter token; a plain noun only one entry uses is not a coinage); vacuous on a 1-entry register
  V6' every status_by_field entry: status in enum, field in FIELDS.txt, assessed date present
  V7  no stored entry-level status (the rollup is derived)
  V8  emissions current: the store hash recorded in both emission headers equals sha256(REGISTER.jsonl)
  V9  every gr: term used in machine/register.jsonld is defined in machine/context.jsonld
"""
import hashlib
import json
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTER = os.path.join(HERE, "REGISTER.jsonl")

TYPES = ("T1", "T2", "T3", "T4")
STATUS = ("OPEN", "CLOSED_MEASURED", "CLOSED_INSTRUMENT_EXISTS", "OUT_OF_ENVELOPE", "UNKNOWN")
REQUIRED = ("id", "type", "quantity", "index_terms", "excluding_method", "measured_instead", "venue_check",
            "closure_condition", "refutation", "status_by_field", "provenance", "confound", "opened")
FIELDS_TXT = os.path.join(HERE, "FIELDS.txt")
HUMAN = os.path.join(HERE, "human", "REGISTER.md")
MACHINE = os.path.join(HERE, "machine", "register.jsonld")
CONTEXT = os.path.join(HERE, "machine", "context.jsonld")
CLOSED = ("CLOSED_MEASURED", "CLOSED_INSTRUMENT_EXISTS")
# A1: the closing instruction differs in kind by type
INSTRUCTION = {"T1": "MEASURE: the quantity is absent by construction; close by an instrument that returns it",
               "T2": "DECLARE the partition: close by a declaration that the separation was made, as a choice; the residual is a marked, unmeasured quantity",
               "T3": "ASSESS the named competency by an instrument other than the substituted count; close when the original name is measured again",
               "T4": "BUILD the venue: both sides are already measured; close by the table, paper, or committee where they appear on one page; no residual"}
NULLABLE = ("venue_check", "confound")
TEXT_FIELDS = ("quantity", "excluding_method", "measured_instead", "venue_check", "closure_condition", "refutation", "confound")

# V2: a closure condition must name something a reader could go and look at
OBSERVABLES = ("record", "table", "count", "rate", "log", "list", "published", "standard", "study", "dataset", "corpus",
               "benchmark", "instrument", "measure", "measurement", "citation", "document", "code", "field", "column",
               "register", "report", "index", "protocol", "certification", "syllabus", "declaration", "declared", "score")
MODALS = ("should", "ought", "must", "needs to", "need to")
# V4: fault lexicon (any field except provenance)
ACCUSATORY = (r"\bfault\b", r"\bblame", r"\bnegligen", r"\bhides?\b", r"\bhid\b", r"\bconceal", r"\bcover(ed)? up\b", r"\bdeliberately\b",
              r"\bdishonest", r"\blied\b", r"\blying\b", r"\bfraud", r"\bguilty\b", r"\bculpable\b", r"\bwrongdoing\b", r"\bfailed to\b",
              r"\brefuse[sd]? to\b", r"\bmalic")
# V5: a term is a COINAGE when no other entry indexes it AND it looks coined: a non-letter character (hyphen,
# digit, underscore, camelCase), a capital letter, or a single token over 14 letters. A plain noun that only one
# entry uses (spay) is not a coinage; the rule as written ("none of which is a coinage absent from index_terms of
# any other entry") is read as: no coined term unique to this entry.
COINAGE_RE = re.compile(r"[^a-z /]|\b[a-z]{15,}\b")
# capitalised tokens that are not names (acronyms and common technical capitals)
NOT_NAMES = {"LLM", "LLMs", "JSONL", "JSON", "API", "LEEP", "CPT", "ICD", "ISO", "AAHA", "AVMA", "RCT", "OPEN", "UNKNOWN",
             "CLOSED_MEASURED", "CLOSED_INSTRUMENT_EXISTS", "OUT_OF_ENVELOPE", "T1", "T2", "T3", "T4", "I", "A"}


class Invalid(Exception):
    pass


def fields(path=FIELDS_TXT):
    if not os.path.exists(path):
        return []
    return [l.strip() for l in open(path) if l.strip() and not l.startswith("#")]


def rollup(e):
    """S4: derived, never stored. any OPEN -> OPEN; all CLOSED_* -> CLOSED; else UNKNOWN."""
    st = [v.get("status") for v in (e.get("status_by_field") or {}).values()]
    if not st:
        return "UNKNOWN"
    if "OPEN" in st:
        return "OPEN"
    if all(x in CLOSED for x in st):
        return "CLOSED"
    return "UNKNOWN"


def store_hash(path=REGISTER):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load(path=REGISTER):
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path) if l.strip()]


def save(entries, path=REGISTER):
    with open(path, "w") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def next_id(entries):
    n = max([int(e["id"].split("-")[1]) for e in entries if e.get("id", "").startswith("GR-")] + [0])
    return "GR-%04d" % (n + 1)


# ---- V4 helpers ---------------------------------------------------------------------------------
def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.;:!?])\s+", text) if s.strip()]


def proper_names(text):
    """Capitalised words that are not sentence-initial and not known acronyms; plus any run of two or more
    capitalised words anywhere (a sentence-initial name is still a name)."""
    found = []
    for s in _sentences(text):
        toks = re.findall(r"[A-Za-z][A-Za-z'\-]*", s)
        skip = -1
        for i, t in enumerate(toks):
            if i == skip:
                continue
            if t[0].isupper() and t not in NOT_NAMES and not t.isupper():
                if i > 0:
                    found.append(t)
                elif i + 1 < len(toks) and toks[i + 1][0].isupper() and toks[i + 1] not in NOT_NAMES:
                    found.append(t + " " + toks[i + 1]); skip = i + 1
    return found


# ---- validation ----------------------------------------------------------------------------------
def validate_entry(e, others):
    """Return a list of (rule, message). Empty list = valid. `others`: the rest of the register (for V5)."""
    errs = []
    for k in REQUIRED:
        if k not in e:
            errs.append(("V1", "missing field %s" % k)); continue
        v = e[k]
        if v is None and k in NULLABLE:
            continue
        if v is None or (isinstance(v, (str, list)) and len(v) == 0) or (isinstance(v, str) and not v.strip()):
            errs.append(("V1", "empty field %s" % k))
    if errs:
        return errs
    if e["type"] not in TYPES:
        errs.append(("V1", "type not in %s" % (TYPES,)))
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(e["opened"])):
        errs.append(("V1", "opened must be YYYY-MM-DD"))
    if not isinstance(e["provenance"], list) or not all(isinstance(p, str) and p.strip() for p in e["provenance"]):
        errs.append(("V1", "provenance must be a non-empty list of strings"))
    cc = e["closure_condition"].lower()
    if not any(o in cc for o in OBSERVABLES):
        why = "only a modal" if any(m in cc for m in MODALS) else "names no observable"
        errs.append(("V2", "closure_condition %s (needs one of: %s, ...)" % (why, ", ".join(OBSERVABLES[:6]))))
    if e["refutation"].strip().lower() == e["closure_condition"].strip().lower():
        errs.append(("V3", "refutation identical to closure_condition"))
    for k in TEXT_FIELDS:
        v = e.get(k)
        if not isinstance(v, str):
            continue
        names = proper_names(v)
        if names:
            errs.append(("V4", "proper name outside provenance in %s: %s" % (k, ", ".join(names))))
        low = v.lower()
        hits = [m.group(0) for a in ACCUSATORY for m in [re.search(a, low)] if m]
        if hits:
            errs.append(("V4", "accusatory construction in %s: %s" % (k, ", ".join(hits))))
    terms = e["index_terms"]
    if not isinstance(terms, list) or len(terms) < 3 or not all(isinstance(t, str) and t.strip() for t in terms):
        errs.append(("V5", "index_terms needs >= 3 non-empty terms"))
    elif len(others) >= 1:
        pool = {t.lower() for o in others for t in o.get("index_terms", [])}
        coin = [t for t in terms if t.lower() not in pool and COINAGE_RE.search(t)]
        if coin:
            errs.append(("V5", "coinage unique to this entry (index by the quantity's plain nouns): %s" % ", ".join(coin)))
    sbf = e["status_by_field"]
    known = set(fields())
    if not isinstance(sbf, dict) or not sbf:
        errs.append(("V6", "status_by_field must be a non-empty object (S1)"))
    else:
        for f, v in sbf.items():
            if f not in known:
                errs.append(("V6", "field %r not in FIELDS.txt (S2)" % f))
            if not isinstance(v, dict) or v.get("status") not in STATUS:
                errs.append(("V6", "field %r: status not in %s" % (f, (STATUS,))))
            elif not re.match(r"^\d{4}-\d{2}-\d{2}$", str(v.get("assessed", ""))):
                errs.append(("V6", "field %r: assessed date missing" % f))
    if "status" in e:
        errs.append(("V7", "stored entry-level status; the rollup is derived (S4)"))
    return errs


def validate_all(entries):
    report = {}
    for i, e in enumerate(entries):
        others = entries[:i] + entries[i + 1:]
        errs = validate_entry(e, others)
        if errs:
            report[e.get("id", "<no id %d>" % i)] = errs
    ids = [e.get("id") for e in entries]
    if len(ids) != len(set(ids)):
        report.setdefault("<register>", []).append(("V1", "duplicate ids"))
    return report


def validate_emissions(path=REGISTER):
    """V8 + V9 for the store's emissions. Returns list of (rule, message)."""
    errs = []
    h = store_hash(path)
    if not os.path.exists(HUMAN) or ("store sha256: %s" % h) not in open(HUMAN).read():
        errs.append(("V8", "human/REGISTER.md missing or stale (store %s)" % h[:12]))
    if not os.path.exists(MACHINE):
        errs.append(("V8", "machine/register.jsonld missing"))
    else:
        m = json.load(open(MACHINE))
        if m.get("storeHash") != h:
            errs.append(("V8", "machine/register.jsonld stale (store %s)" % h[:12]))
        ctx = json.load(open(CONTEXT))
        defined = set(ctx.get("gr:definitions", {}))
        used = set(re.findall(r'"(gr:[A-Za-z]+)"', json.dumps(m)))
        # terms in the @context map to gr: ids; those count as used too
        used |= {v if isinstance(v, str) else v.get("@id", "") for v in ctx["@context"].values() if (isinstance(v, str) and v.startswith("gr:")) or (isinstance(v, dict) and str(v.get("@id", "")).startswith("gr:"))}
        undefined = sorted(t for t in used if t not in defined)
        if undefined:
            errs.append(("V9", "gr: terms used but not defined in context.jsonld: %s" % ", ".join(undefined)))
    return errs


# ---- commands ------------------------------------------------------------------------------------
def add(obj, path=REGISTER):
    entries = load(path)
    e = dict(obj)
    e.setdefault("id", next_id(entries))
    e.setdefault("opened", date.today().isoformat())
    errs = validate_entry(e, entries)
    if errs:
        raise Invalid(errs)
    entries.append(e)
    save(entries, path)
    if path == REGISTER:
        emit_all()                                                   # V8: keep emissions current on every add
    return e["id"]


def search(terms, entries):
    q = [t.lower() for t in terms]
    out = []
    for e in entries:
        hay = " ".join(e["index_terms"] + [e["quantity"]]).lower()
        score = sum(1 for t in q if t in hay)
        if score:
            out.append((score, e))
    return [e for _, e in sorted(out, key=lambda x: -x[0])]


def export_md(entries, h=None):
    h = h or store_hash()
    L = ["# gap register", "", "BUILD PRODUCT of `gap_register.py emit --human`; never hand-edit. store sha256: %s" % h, "",
         "One block per entry. Status is per field; the entry line shows the derived rollup (any OPEN -> OPEN; all closed -> CLOSED; else UNKNOWN).", ""]
    for e in entries:
        L.append("## %s  %s  %s" % (e["id"], e["type"], rollup(e)))
        L.append("")
        L.append("- quantity: %s" % e["quantity"])
        L.append("- index terms: %s" % ", ".join(e["index_terms"]))
        L.append("- excluding method: %s" % e["excluding_method"])
        L.append("- measured instead: %s" % e["measured_instead"])
        L.append("- venue check: %s" % (e["venue_check"] or "none exists"))
        L.append("- closure condition: %s" % e["closure_condition"])
        L.append("- closing instruction (%s): %s" % (e["type"], INSTRUCTION[e["type"]]))
        L.append("- refutation: %s" % e["refutation"])
        L.append("- status by field:")
        for f, v in e["status_by_field"].items():
            L.append("    - %s: %s (assessed %s; evidence: %s)" % (f, v["status"], v["assessed"], v.get("evidence") or "none"))
        L.append("- confound: %s" % (e["confound"] or "none recorded"))
        L.append("- provenance: %s" % "; ".join(e["provenance"]))
        L.append("- opened: %s" % e["opened"])
        L.append("")
    return "\n".join(L) + "\n"


def export_jsonld(entries, h=None):
    h = h or store_hash()
    ctx = json.load(open(CONTEXT))
    graph = []
    for e in entries:
        graph.append({
            "@id": "gr:" + e["id"], "@type": "gr:GapEntry",
            "identifier": e["id"], "additionalType": "gr:" + e["type"], "entryType": e["type"],
            "quantity": e["quantity"], "keywords": list(e["index_terms"]),
            "excludingMethod": e["excluding_method"], "measuredInstead": e["measured_instead"],
            "venueCheck": e["venue_check"], "closureCondition": e["closure_condition"], "refutation": e["refutation"],
            "statusByField": [{"field": f, "status": v["status"], "evidence": v.get("evidence"), "assessed": v["assessed"]}
                              for f, v in e["status_by_field"].items()],
            "citationConfound": e["confound"], "citation": list(e["provenance"]), "dateCreated": e["opened"]})
    return {"@context": ctx["@context"], "gr:contextVersion": ctx.get("gr:contextVersion"), "storeHash": h,
            "gr:note": "BUILD PRODUCT of gap_register.py emit --machine; never hand-edit; the store wins on any disagreement",
            "@graph": graph}


def emit_all(path=REGISTER):
    entries = load(path)
    h = store_hash(path)
    os.makedirs(os.path.dirname(HUMAN), exist_ok=True); os.makedirs(os.path.dirname(MACHINE), exist_ok=True)
    open(HUMAN, "w").write(export_md(entries, h))
    with open(MACHINE, "w") as f:
        json.dump(export_jsonld(entries, h), f, indent=1, ensure_ascii=False); f.write("\n")
    return HUMAN, MACHINE


def check_text(e):
    return "%s\n%s: %s" % (e["closure_condition"], e["type"], INSTRUCTION[e["type"]] +
                            ("" if e["type"] != "T4" else "\n  venue: %s" % (e["venue_check"] or "none exists; the venue is the deliverable")))


def correlate(entries, field=None):
    """A2.2: counts only. Field x field co-occurrence over entries that carry BOTH fields; plus the adjacency
    list: entry pairs sharing >= 2 index_terms whose statuses differ on a field both carry."""
    fs = sorted({f for e in entries for f in e["status_by_field"]})
    pairs = {}
    for i, a in enumerate(fs):
        for b in fs[i + 1:]:
            both = [e for e in entries if a in e["status_by_field"] and b in e["status_by_field"]]
            if not both:
                continue
            sa = lambda e: e["status_by_field"][a]["status"]; sb = lambda e: e["status_by_field"][b]["status"]
            pairs["%s x %s" % (a, b)] = {
                "entries_with_both": len(both),
                "open_in_both": sum(1 for e in both if sa(e) == "OPEN" and sb(e) == "OPEN"),
                "open_in_one": sum(1 for e in both if (sa(e) == "OPEN") != (sb(e) == "OPEN")),
                "closed_in_both": sum(1 for e in both if sa(e) in CLOSED and sb(e) in CLOSED)}
    adjacency = []
    for i, x in enumerate(entries):
        for y in entries[i + 1:]:
            shared = sorted({t.lower() for t in x["index_terms"]} & {t.lower() for t in y["index_terms"]})
            if len(shared) < 2:
                continue
            for f in sorted(set(x["status_by_field"]) & set(y["status_by_field"])):
                sx, sy = x["status_by_field"][f]["status"], y["status_by_field"][f]["status"]
                if sx != sy:
                    adjacency.append({"entries": [x["id"], y["id"]], "shared_terms": shared, "field": f, "statuses": [sx, sy]})
    out = {"fields": fs, "pairs": pairs, "adjacency": adjacency, "note": "counts only; no inference about why"}
    if field:
        co = {}
        for e in entries:
            if e["status_by_field"].get(field, {}).get("status") == "OPEN":
                for f, v in e["status_by_field"].items():
                    if f != field and v["status"] == "OPEN":
                        co[f] = co.get(f, 0) + 1
        out["open_wherever_%s_is_open" % field] = co
    return out


def strip(e):
    """The name-strip probe input: the entry without its custody chain."""
    return {k: v for k, v in e.items() if k != "provenance"}


def kill_sample(entries, n=20):
    """Bare entries for the kill-rule probe. A zero-context reader must restate (a) the absent quantity and
    (b) the closing condition for >= 80% of them. No framing is emitted on purpose."""
    return "\n".join(json.dumps(e, ensure_ascii=False) for e in entries[:n])


# ---- selftest ------------------------------------------------------------------------------------
def _good(i):
    return {"id": "GR-%04d" % i, "type": "T1", "quantity": "a rate the method cannot return", "index_terms": ["rate", "method", "record"],
            "excluding_method": "the method scores one outcome only", "measured_instead": "the outcome score", "venue_check": None,
            "closure_condition": "a published table reporting the rate under the method", "refutation": "the rate appears in the method's own record",
            "status_by_field": {"mediation_practice": {"status": "UNKNOWN", "evidence": None, "assessed": "2026-09-11"}},
            "provenance": ["session note 2026-09-11"], "confound": None, "opened": "2026-09-11"}


def selftest():
    a, b = _good(1), _good(2)
    assert validate_entry(a, [b]) == [] and validate_entry(b, [a]) == []
    # V1
    bad = dict(a, quantity=""); assert any(r == "V1" for r, _ in validate_entry(bad, [b]))
    bad = dict(a, venue_check=None, confound=None); assert validate_entry(bad, [b]) == []          # nulls allowed there
    # V2
    bad = dict(a, closure_condition="mediators should care more about this"); assert [r for r, _ in validate_entry(bad, [b])] == ["V2"]
    # V3
    bad = dict(a, refutation=a["closure_condition"]); assert [r for r, _ in validate_entry(bad, [b])] == ["V3"]
    # V4: a name outside provenance; a fault word; a name inside provenance is fine
    bad = dict(a, excluding_method="the Acme Institute scoring rubric"); assert [r for r, _ in validate_entry(bad, [b])] == ["V4"]
    bad = dict(a, measured_instead="closure, because the committee failed to count it"); assert [r for r, _ in validate_entry(bad, [b])] == ["V4"]
    ok = dict(a, provenance=["Acme Institute rubric v3, table 2"]); assert validate_entry(ok, [b]) == []
    assert proper_names("The method counts closure. It returns a score.") == []                      # sentence-initial common words pass
    assert proper_names("Acme Institute counts closure.") == ["Acme Institute"]                       # two-word name at sentence start caught
    # V5: fewer than 3 terms; a coinage
    bad = dict(a, index_terms=["rate", "method"]); assert [r for r, _ in validate_entry(bad, [b])] == ["V5"]
    bad = dict(a, index_terms=["rate", "method", "frobnication-index"]); assert [r for r, _ in validate_entry(bad, [b])] == ["V5"]
    bad = dict(a, index_terms=["rate", "method", "Frobnication"]); assert [r for r, _ in validate_entry(bad, [b])] == ["V5"]
    ok = dict(a, index_terms=["rate", "method", "spay"]); assert validate_entry(ok, [b]) == []          # plain unique noun is not a coinage
    ok = dict(a, measured_instead="the score applied at close"); assert validate_entry(ok, [b]) == []   # 'applied' is not 'lied'
    assert validate_entry(a, []) == []                                                                 # vacuous on a 1-entry register
    # V6': enum, controlled field, assessed date; V7: stored rollup
    bad = dict(a, status_by_field={"mediation_practice": {"status": "MAYBE", "evidence": None, "assessed": "2026-09-11"}}); assert [r for r, _ in validate_entry(bad, [b])] == ["V6"]
    bad = dict(a, status_by_field={"free_text_field": {"status": "OPEN", "evidence": None, "assessed": "2026-09-11"}}); assert [r for r, _ in validate_entry(bad, [b])] == ["V6"]
    bad = dict(a, status_by_field={"mediation_practice": {"status": "OPEN", "evidence": None}}); assert [r for r, _ in validate_entry(bad, [b])] == ["V6"]
    bad = dict(a, status="OPEN"); assert [r for r, _ in validate_entry(bad, [b])] == ["V7"]
    # S4 rollup derived
    assert rollup(a) == "UNKNOWN"
    assert rollup(dict(a, status_by_field={"x": {"status": "CLOSED_MEASURED"}, "y": {"status": "OPEN"}})) == "OPEN"
    assert rollup(dict(a, status_by_field={"x": {"status": "CLOSED_MEASURED"}, "y": {"status": "CLOSED_INSTRUMENT_EXISTS"}})) == "CLOSED"
    assert rollup(dict(a, status_by_field={"x": {"status": "CLOSED_MEASURED"}, "y": {"status": "OUT_OF_ENVELOPE"}})) == "UNKNOWN"
    # A1: T2 and T4 close in different kinds
    reg0 = {e["id"]: e for e in load()}
    c2, c4 = check_text(reg0["GR-0002"]), check_text(reg0["GR-0004"])
    assert "DECLARE" in c2 and "BUILD the venue" in c4 and "venue:" in c4 and "venue:" not in c2
    # A2.2 correlate: counts and the adjacency detector
    x = dict(a, id="GR-0101", index_terms=["rate", "method", "record"],
             status_by_field={"veterinary_medicine": {"status": "CLOSED_MEASURED", "evidence": "t", "assessed": "2026-09-11"},
                              "human_procedure_coding": {"status": "OPEN", "evidence": None, "assessed": "2026-09-11"}})
    y = dict(a, id="GR-0102", index_terms=["rate", "method", "count"],
             status_by_field={"veterinary_medicine": {"status": "OPEN", "evidence": None, "assessed": "2026-09-11"},
                              "human_procedure_coding": {"status": "OPEN", "evidence": None, "assessed": "2026-09-11"}})
    co = correlate([x, y], field="human_procedure_coding")
    p = co["pairs"]["human_procedure_coding x veterinary_medicine"]
    assert (p["entries_with_both"], p["open_in_both"], p["open_in_one"], p["closed_in_both"]) == (2, 1, 1, 0)
    assert co["adjacency"] == [{"entries": ["GR-0101", "GR-0102"], "shared_terms": ["method", "rate"], "field": "veterinary_medicine", "statuses": ["CLOSED_MEASURED", "OPEN"]}]
    assert co["open_wherever_human_procedure_coding_is_open"] == {"veterinary_medicine": 1}
    # V8 / V9 on the shipped emissions
    assert validate_emissions() == [], validate_emissions()
    m = json.load(open(MACHINE)); assert m["storeHash"] == store_hash() and len(m["@graph"]) == len(load())
    assert ("store sha256: %s" % store_hash()) in open(HUMAN).read()
    # register-level: duplicate ids
    assert "<register>" in validate_all([a, dict(b, id="GR-0001")])
    # the shipped register validates; the demo fails on V4 and V2
    reg = load()
    assert reg and validate_all(reg) == {}, validate_all(reg)
    assert [e["id"] for e in reg] == ["GR-%04d" % i for i in range(1, len(reg) + 1)]
    assert all("status" not in e for e in reg)                                                          # V7 on the store
    assert rollup(reg0["GR-0007"]) == "OPEN" and rollup(reg0["GR-0001"]) == "UNKNOWN"
    demo = load(os.path.join(HERE, "demo", "REGISTER_failing.jsonl"))
    rep = validate_all(demo)
    rules = {k: {r for r, _ in v} for k, v in rep.items()}
    assert "V4" in rules.get("GR-DEMO-V4", set()) and "V2" in rules.get("GR-DEMO-V2", set()), rules
    # search hits by quantity noun, not by a coined name
    assert search(["analgesia"], reg) and not search(["frobnication"], reg)
    assert "provenance" not in strip(reg[0])
    print("gap_register selftest ok")


def main(argv):
    if not argv:
        print(__doc__); return 0
    cmd, args = argv[0], argv[1:]
    if cmd == "add":
        raw = open(args[0][1:]).read() if args and args[0].startswith("@") else " ".join(args)
        try:
            print(add(json.loads(raw)))
        except Invalid as ex:
            for r, m in ex.args[0]:
                print("%s  %s" % (r, m), file=sys.stderr)
            return 1
        return 0
    if cmd == "validate":
        path = args[0] if args else REGISTER
        rep = validate_all(load(path))
        for k, v in rep.items():
            for r, m in v:
                print("%s  %s  %s" % (k, r, m))
        em = validate_emissions() if os.path.abspath(path) == REGISTER else []            # V8/V9 apply to the store only
        for r, m in em:
            print("<emissions>  %s  %s" % (r, m))
        print("%s: %d entries, %d failing%s" % (os.path.basename(path), len(load(path)), len(rep), "; emissions stale" if em else ""))
        return 1 if (rep or em) else 0
    if cmd == "search":
        for e in search(args, load()):
            print("%s  %s  %s  | %s" % (e["id"], e["type"], rollup(e), e["quantity"]))
        return 0
    if cmd == "check":
        for e in load():
            if e["id"] == args[0]:
                print(check_text(e)); return 0
        print("no entry %s" % args[0], file=sys.stderr); return 1
    if cmd == "emit":
        hp, mp = emit_all()
        if "--machine" in args and "--human" not in args:
            print(mp)
        elif "--human" in args and "--machine" not in args:
            print(hp)
        else:
            print(hp); print(mp)
        return 0
    if cmd == "export":
        md = export_md(load())
        if "--md" in args:
            out = [a for a in args if a != "--md"]
            if out:
                open(out[0], "w").write(md); print(out[0])
            else:
                print(md)
        return 0
    if cmd == "correlate":
        field = args[args.index("--field") + 1] if "--field" in args else None
        print(json.dumps(correlate(load(), field), indent=1)); return 0
    if cmd == "strip":
        for e in load():
            if e["id"] == args[0]:
                print(json.dumps(strip(e), ensure_ascii=False)); return 0
        return 1
    if cmd == "kill-sample":
        print(kill_sample(load(args[0] if args else REGISTER))); return 0
    if cmd == "selftest":
        selftest(); return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
