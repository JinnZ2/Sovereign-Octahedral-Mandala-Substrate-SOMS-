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
  gap_register.py export    --md [file]       flat markdown, one entry per block
  gap_register.py strip     <id>              the entry with provenance removed (name-strip probe input)
  gap_register.py kill-sample [file]          bare entries for the kill-rule probe (no framing)
  gap_register.py selftest

  V1  required fields present and non-empty (null allowed only in venue_check, confound)
  V2  closure_condition checkable: names an observable (record, table, count, ...) and is not only a modal
  V3  refutation non-empty and distinct from closure_condition
  V4  no accusatory construction: proper names only inside provenance[]; no fault lexicon anywhere
  V5  index_terms >= 3, and no term is a coinage unique to this entry (coinage = hyphen/digit/capital/camelCase
      or a 15+ letter token; a plain noun only one entry uses is not a coinage); vacuous on a 1-entry register
  V6  status in the enum
"""
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
            "closure_condition", "refutation", "status", "provenance", "confound", "opened")
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
    if e["status"] not in STATUS:
        errs.append(("V6", "status not in %s" % (STATUS,)))
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


def export_md(entries):
    L = ["# gap register", "", "One block per entry. Status is the mark's status, not a claim about the quantity.", ""]
    for e in entries:
        L.append("## %s  %s  %s" % (e["id"], e["type"], e["status"]))
        L.append("")
        L.append("- quantity: %s" % e["quantity"])
        L.append("- index terms: %s" % ", ".join(e["index_terms"]))
        L.append("- excluding method: %s" % e["excluding_method"])
        L.append("- measured instead: %s" % e["measured_instead"])
        L.append("- venue check: %s" % (e["venue_check"] or "none exists"))
        L.append("- closure condition: %s" % e["closure_condition"])
        L.append("- refutation: %s" % e["refutation"])
        L.append("- confound: %s" % (e["confound"] or "none recorded"))
        L.append("- provenance: %s" % "; ".join(e["provenance"]))
        L.append("- opened: %s" % e["opened"])
        L.append("")
    return "\n".join(L)


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
            "status": "UNKNOWN", "provenance": ["session note 2026-09-11"], "confound": None, "opened": "2026-09-11"}


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
    # V6
    bad = dict(a, status="MAYBE"); assert [r for r, _ in validate_entry(bad, [b])] == ["V6"]
    # register-level: duplicate ids
    assert "<register>" in validate_all([a, dict(b, id="GR-0001")])
    # the shipped register validates; the demo fails on V4 and V2
    reg = load()
    assert reg and validate_all(reg) == {}, validate_all(reg)
    assert [e["id"] for e in reg] == ["GR-%04d" % i for i in range(1, len(reg) + 1)]
    assert all(e["status"] != "OPEN" or e["provenance"] for e in reg)
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
        print("%s: %d entries, %d failing" % (os.path.basename(path), len(load(path)), len(rep)))
        return 1 if rep else 0
    if cmd == "search":
        for e in search(args, load()):
            print("%s  %s  %s  | %s" % (e["id"], e["type"], e["status"], e["quantity"]))
        return 0
    if cmd == "check":
        for e in load():
            if e["id"] == args[0]:
                print(e["closure_condition"]); return 0
        print("no entry %s" % args[0], file=sys.stderr); return 1
    if cmd == "export":
        md = export_md(load())
        if "--md" in args:
            out = [a for a in args if a != "--md"]
            if out:
                open(out[0], "w").write(md); print(out[0])
            else:
                print(md)
        return 0
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
