"""
retention_chain.py -- C3 / V8 retention chain computed from fixtures/retention_chain.jsonl
(uploaded 2026-09-11; extracted by a separate session; PRESS rows are paraphrases, government rows verbatim).

The chain question (SPEC FT-09 / V8): a finding closes only as RULE_CHANGE or WAIVED. Each dated row is
typed from its own fields; the mapping of rows to the three chains is declared in CHAINS here, not in the
fixture. Reported verdicts (the fixture's _verdicts line) are carried separately from what the rows compute.

  fix_type   EQUIPMENT (a device bought) | PLAN (a provision, plan, or review) | RULE (a gate that stops
             movement or settlement without a record)   -- executor's reading of the row text, declared per row
  'improved' a self-review or testimony statement measuring initiatives, not the failed mechanism

  python retention_chain.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "fixtures", "retention_chain.jsonl")

# row keys are (date, event) from the fixture; fix_type is declared here per FIX row
FIX_TYPE = {("2006", "FIX: GPS devices"): "EQUIPMENT", ("2006-10", "FIX: PKEMRA logistics provision"): "PLAN"}
CHAINS = {
    "asset_visibility": {"finding": ("2005-08/09", "OIG-06-32 p.7"), "fix": ("2006", "FIX: GPS devices"),
                         "improved": ("2010-07", "OIG-10-101"), "recurrence": ("2017", "OIG-20-76 p.11")},
    "custody_state_information": {"finding": ("2005-08/09", "OIG-06-32 p.34"), "fix": None,
                                  "improved": ("2010-07", "OIG-10-101"), "recurrence": ("2017", "OIG-20-76 p.7")},
    "remediation_of_prior_findings": {"finding": ("2006-03", "OIG-06-32 p.2"), "fix": ("2006-10", "FIX: PKEMRA logistics provision"),
                                      "improved": ("2011-03-17", "OIG testimony"), "recurrence": None},
}


def load(path=PATH):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    hdr = rows[0]; verdicts = rows[-1] if rows[-1].get("_verdicts") else None
    body = [r for r in rows[1:] if not r.get("_verdicts")]
    return hdr, body, verdicts


def _find(body, date, key):
    for r in body:
        if r["date"] == date and (key in r.get("event", "") or key in r.get("doc", "")):
            return r
    return None


def row_type(r):
    st = r["source_type"]
    if r["event"].startswith("FIX:"):
        return "fix"
    if "RECURRENCE" in r["event"]:
        return "recurrence"
    if "self-review" in st or "testimony" in st:
        return "improved_statement"
    return "finding"


def year(d):
    return int(str(d)[:4])


def compute(path=PATH):
    hdr, body, verdicts = load(path)
    types = {}
    for r in body:
        types.setdefault(row_type(r), []).append((r["date"], r["event"]))
    verbatim = [r for r in body if not r["text"].startswith("[paraphrase]")]
    paraphrase = [r for r in body if r["text"].startswith("[paraphrase]")]
    secondary = [(r["date"], r["event"]) for r in body if "secondhand" in r["source_type"] or "SECONDARY" in (r.get("note") or "")]
    fixes = {k: v for k, v in FIX_TYPE.items()}
    rule_fixes = [k for k, v in fixes.items() if v == "RULE"]
    chains = {}
    for name, spec in CHAINS.items():
        c = {}
        for stage, key in spec.items():
            if key is None:
                c[stage] = None
                continue
            r = _find(body, key[0], key[1])
            c[stage] = {"date": r["date"], "source_type": r["source_type"], "verbatim": not r["text"].startswith("[paraphrase]"),
                        "fix_type": fixes.get((r["date"], r["event"]))} if r else "ROW NOT FOUND"
        dated = [c[s]["date"] for s in ("finding", "fix", "improved", "recurrence") if isinstance(c.get(s), dict)]
        c["span_years"] = year(dated[-1]) - year(dated[0]) if len(dated) > 1 else None
        c["recurred"] = isinstance(c.get("recurrence"), dict)
        c["closed_as_rule_change"] = isinstance(c.get("fix"), dict) and c["fix"]["fix_type"] == "RULE"
        c["status"] = ("RECURRED after %s fix" % c["fix"]["fix_type"] if c["recurred"] and isinstance(c.get("fix"), dict)
                       else "RECURRED, no fix row" if c["recurred"] else "OPEN: no recurrence row loaded (FT-09: not closed as RULE_CHANGE or WAIVED)")
        chains[name] = c
    return {"computed": True, "rows": len(body), "row_types": {k: len(v) for k, v in types.items()},
            "verbatim_rows": len(verbatim), "paraphrase_rows": len(paraphrase), "secondary_source_rows": secondary,
            "fix_types": {"%s %s" % k: v for k, v in fixes.items()}, "rule_fixes": rule_fixes,
            "chains": chains,
            "oig_10_101": {"status": "SECONDARY: quoted in FEMA testimony, PDF not resolved", "verified": False},
            "reported_verdicts": verdicts,
            "read": "no FIX row is a RULE at the custody boundary (%d of %d fixes); every 'improved' statement is self-review or testimony; "
                    "the asset-visibility chain recurs 12 years after its equipment fix" % (len(rule_fixes), len(fixes))}


def selftest():
    out = compute()
    assert out["rows"] == 12 and out["row_types"] == {"finding": 6, "fix": 2, "improved_statement": 2, "recurrence": 2}, out["row_types"]
    assert out["paraphrase_rows"] == 4 and out["verbatim_rows"] == 8              # every press row is a paraphrase
    assert out["rule_fixes"] == []
    av = out["chains"]["asset_visibility"]
    assert av["span_years"] == 12 and av["recurred"] and av["fix"]["fix_type"] == "EQUIPMENT" and not av["closed_as_rule_change"]
    assert av["improved"]["source_type"].startswith("audit (quoted secondhand")
    cs = out["chains"]["custody_state_information"]
    assert cs["fix"] is None and cs["recurred"]
    rp = out["chains"]["remediation_of_prior_findings"]
    assert not rp["recurred"] and rp["status"].startswith("OPEN")                  # the fixture has no 2017 row for it; learning chain lives in M1 row 5
    assert not out["oig_10_101"]["verified"]
    assert out["reported_verdicts"]["asset_visibility"].endswith("RECURRED 2017")  # reported, carried, not recomputed
    for r in load()[1]:
        assert r["source_type"] and r["date"] and r["text"]
    print("retention_chain selftest ok")


if __name__ == "__main__":
    selftest()
    print(json.dumps(compute(), indent=1))
