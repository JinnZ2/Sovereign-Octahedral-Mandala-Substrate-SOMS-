"""
grading_prompt.py -- grading prompts for the pilot's pending tests, with CANARY rows and a
grader-identity field (OPEN ITEMS ROLLUP 2026-09-11, A4 + A5).

  identity   a grading run names the grader it CLAIMS; nothing here verifies it. Silent model
             routing makes identity a claim, so every prompt carries known-answer CANARY rows.
  canary     rows whose coding is settled across every verified family: row 13 physical_damage
             (unanimous P0 + P1), row 5 regime.learning (unanimous P0 + P1). A grader that fails a
             canary it passed before -> the run is marked SUSPECT (possible silent substitution).
  prompts    P0 (names present) and P1 (roles) are RECONSTRUCTED from the verbatim fixture: the
             operator's original prompt files were not supplied. T-a, T-b, T-d and V10c derive
             from them; the selftest diffs each against its base.

  python grading_prompt.py emit          # writes prompts/*.txt
  python grading_prompt.py selftest
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ledger import prompt_definitions  # noqa: E402

VERBATIM = {r["row"]: r for r in [json.loads(l) for l in open(os.path.join(HERE, "fixtures", "maria_verbatim.jsonl")) if l.strip()][1:]}
TEMPLATE = [json.loads(l) for l in open(os.path.join(HERE, "fixtures", "maria_locus_round3_template.jsonl")) if l.strip()]
SITE = {r["row"]: r["site_record"] for r in TEMPLATE[1:]}
ROWS = [r["row"] for r in TEMPLATE[1:]]                                  # 1..13, 8a/8b, C1..C3

CANARIES = (("13", "physical_damage"), ("5", "regime.learning"))         # known answers, unanimous on P0 and P1
CANARY_ROWS = [c[0] for c in CANARIES]

# P1 (roles) substitutions, declared here; RECONSTRUCTED (the operator's P1 file was not supplied)
ROLE_SUBS = [("Crowley Maritime Corporation (Crowley), FEMA's transportation contractor", "the contractor, the agency's transportation contractor"),
             ("the FEMA inventory", "the agency's inventory"), ("the Jacksonville", "the mainland port"),
             ("Crowley", "the contractor"), ("FEMA's", "the agency's"), ("FEMA", "the agency"),
             ("Puerto Rico's", "the island's"), ("Puerto Rico", "the island"), ("Jacksonville, FL", "the mainland port"), ("Jacksonville", "the mainland port")]
CARRIER_ROWS = ("2", "C1", "C3")                                          # rows naming the carrier company (T-d removes them)


def row_text(row, variant):
    t = VERBATIM[row]["text"]
    if variant == "P1":
        for a, b in ROLE_SUBS:
            t = t.replace(a, b)
        t = t[0].upper() + t[1:]
    return t


def header_lines(label_map=None):
    L = ["You are coding failure findings. For each finding, name the MECHANISM that failed using exactly one code "
         "from the list below (or a mixed(a,b) pair). Code the mechanism, not the motive. SITE is given as a fact and is "
         "not yours to grade. If you cannot decide, write UNSURE. If you will not code a row, write DECLINE.", "",
         "Codes:"]
    for k, v in prompt_definitions(label_map).items():
        L.append("  %-30s %s" % (k, v))
    L.append("  Rule: %s only where SITE = damaged." % (label_map or {}).get("physical_damage", "physical_damage"))
    L.append("")
    return L


def build(variant="P0", rows=None, label_map=None, canaries=True, extra_rows=None):
    """One prompt. rows: row ids in order (default all 17). Canary rows are appended when absent.
    extra_rows: [(id, site, text)] for rows outside the Maria fixture (V10c stated causes)."""
    rows = list(rows or ROWS)
    if canaries:
        for c in CANARY_ROWS:
            if c not in rows:
                rows.append(c)
    L = header_lines(label_map)
    L.append("The findings are from a federal audit of a hurricane commodity supply chain." if variant == "P0" else
             "The findings are from an audit of a commodity supply chain after a storm.")
    L.append("")
    for r in rows:
        L.append("FINDING %s  [SITE: %s]" % (r, SITE[r]))
        L.append(row_text(r, variant))
        L.append("")
    for rid, site, text in (extra_rows or []):
        L.append("FINDING %s  [SITE: %s]" % (rid, site))
        L.append(text)
        L.append("")
    L.append("Answer with one line per finding, in this exact form and nothing else:")
    L.append("FINDING <id>: <code>")
    return "\n".join(L) + "\n", rows


def stated_cause_rows():
    sc = [json.loads(l) for l in open(os.path.join(HERE, "fixtures", "stated_causes_grader_template.jsonl")) if l.strip()][1:]
    return [(r["id"], r.get("site_record") or "unknown", r["text"]) for r in sc if r.get("doc_id", r["id"].split("-")[0]) == "M1" or r["id"].startswith("M1")]


SPECS = {
    "P0_reconstructed": dict(variant="P0"),
    "P1_reconstructed": dict(variant="P1"),
    "T-a_row9_event_damage": dict(variant="P0", rows=["9"], label_map={"physical_damage": "event_damage"}),
    "T-b_row9_P0": dict(variant="P0", rows=["9"]),
    "T-d_gemini_P2_no_carrier_rows": dict(variant="P0", rows=[r for r in ROWS if r not in CARRIER_ROWS]),
}


def emit(out_dir=None):
    out_dir = out_dir or os.path.join(HERE, "prompts")
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for name, spec in SPECS.items():
        text, _ = build(**spec)
        p = os.path.join(out_dir, name + ".txt")
        open(p, "w").write(text)
        paths[name] = p
    text, _ = build(variant="P0", rows=[], extra_rows=stated_cause_rows())
    p = os.path.join(out_dir, "V10c_M1_stated_causes.txt")
    open(p, "w").write(text)
    paths["V10c_M1_stated_causes"] = p
    return paths


# ---- run log + canary check -------------------------------------------------------------------
RUN_FIELDS = ("run_id", "date", "prompt_file", "grader_identity", "session", "raw_response", "constructed")


def parse_codes(text):
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("FINDING") and ":" in line:
            rid, code = line[len("FINDING"):].split(":", 1)
            out[rid.strip()] = code.strip()
    return out


def canary_result(run):
    codes = parse_codes(run.get("raw_response", ""))
    return {row: (codes.get(row) == answer) for row, answer in CANARIES}


def check_run(run, history):
    """PASS | FAIL | SUSPECT. history: earlier runs (dicts) by the same CLAIMED grader. A canary failed now that
    the same claimed grader passed before -> SUSPECT (possible silent substitution). Failing a canary never passed
    -> FAIL. All canaries pass -> PASS."""
    gid = run.get("grader_identity", {})
    if not isinstance(gid, dict) or "claimed" not in gid or "verified" not in gid:
        raise ValueError("grader_identity must be {claimed, verified}")
    now = canary_result(run)
    if all(now.values()):
        return "PASS", now
    before = [canary_result(h) for h in history if h.get("grader_identity", {}).get("claimed") == gid["claimed"]]
    for row, ok in now.items():
        if not ok and any(b.get(row) for b in before):
            return "SUSPECT", now
    return "FAIL", now


def selftest():
    paths = emit()
    P0 = open(paths["P0_reconstructed"]).read().splitlines()
    P1 = open(paths["P1_reconstructed"]).read().splitlines()
    ta = open(paths["T-a_row9_event_damage"]).read().splitlines()
    tb = open(paths["T-b_row9_P0"]).read().splitlines()
    td = open(paths["T-d_gemini_P2_no_carrier_rows"]).read().splitlines()
    # T-b is P0 restricted to row 9 + canaries: every T-b line is a P0 line, and row 9 appears
    assert all(l in P0 for l in tb), [l for l in tb if l not in P0]
    assert "FINDING 9  [SITE: undamaged]" in tb and "FINDING 13  [SITE: damaged]" in tb and "FINDING 5  [SITE: pre-event]" in tb
    # T-a differs from T-b by exactly the label: every differing line pair is equal after the rename
    d = [(x, y) for x, y in zip(ta, tb) if x != y]
    norm = lambda l: " ".join(l.split())
    assert len(ta) == len(tb) and d and all(norm(x) == norm(y.replace("physical_damage", "event_damage")) for x, y in d), d
    assert "row 9" not in "\n".join(P0)                                            # provenance note stripped: no answer leak
    assert "physical_damage" not in "\n".join(ta)
    # T-d is P0 minus the carrier rows: the removed lines are exactly the three row blocks
    removed = [l for l in P0 if l not in td]
    assert all(l in P0 for l in td) and removed
    for r in CARRIER_ROWS:
        assert "FINDING %s  [SITE: %s]" % (r, SITE[r]) in removed and not any(l.startswith("FINDING %s " % r) for l in td)
    assert "Crowley" not in "\n".join(td) and "FEMA" in "\n".join(td) and "Puerto Rico" in "\n".join(td)
    assert "FINDING 4  [SITE: undamaged]" in td                                     # row 4 kept
    # P1 carries no names; P0 does; both carry canaries
    assert not any(n in "\n".join(P1) for n in ("FEMA", "Crowley", "Puerto Rico", "Jacksonville"))
    for f in (P0, P1, ta, tb, td):
        for c in CANARY_ROWS:
            assert any(l.startswith("FINDING %s " % c) for l in f)
    # V10c prompt: M1 stated causes + canaries
    v = open(paths["V10c_M1_stated_causes"]).read()
    assert "FINDING M1-A1" in v and "FINDING M1-A2" in v and "FINDING M1-C4" in v and "FINDING 13 " in v
    # canary / identity logic
    good = {"grader_identity": {"claimed": "gpt", "verified": False}, "raw_response": "FINDING 9: regime.custody.state\nFINDING 13: physical_damage\nFINDING 5: regime.learning"}
    bad = dict(good, raw_response="FINDING 9: physical_damage\nFINDING 13: regime.market\nFINDING 5: regime.learning")
    assert check_run(good, [])[0] == "PASS"
    assert check_run(bad, [])[0] == "FAIL"                                         # never passed: FAIL, not SUSPECT
    assert check_run(bad, [good])[0] == "SUSPECT"                                  # passed before: SUSPECT
    other = dict(good, grader_identity={"claimed": "deepseek", "verified": False})
    assert check_run(bad, [other])[0] == "FAIL"                                    # another claimed grader's history does not count
    try:
        check_run({"raw_response": ""}, []); raise AssertionError("identity field required")
    except ValueError:
        pass
    print("grading_prompt selftest ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "emit":
        for k, p in emit().items():
            print(k, p)
    else:
        selftest()
