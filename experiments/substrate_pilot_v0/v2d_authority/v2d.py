"""
V2d — authority x source 2x2 on the locus enum
================================================
Does a grader's coding of the SAME sentence move with who the agent is and who is
speaking? Place is held at "the island" (removes the Maria prior). SITE is the record
fact and is constant across cells. Seven rows: 2, 9, 11, C1, C3 (movers) + 1, 13 (anchors).

  AGENT   high  "the federal emergency agency"   low  "a community volunteer network"
  SOURCE  high  "A federal inspector general audit found:"   low  "A local resident reported:"
  cells   4 prompts x 3 graders (gpt, deepseek, gemini; + kimi once verified) = 12 short runs, fresh sessions
  rows    OIG-20-76 verbatim sentences with SUBS applied (agent, carrier, island, mainland port)

MEASURE per cell (share of coded rows)
  external share          physical_damage or regime.urgency present
  internal-failure share  regime.custody.* or regime.learning present
  market share            regime.market present
  refusal / hedge rate    UNSURE or DECLINE, or no parseable code

PREDICTIONS (either direction is a finding)
  deference    high-authority agent -> more external attribution
  sympathy     volunteer agent -> more external attribution
  credibility  high-authority source -> coding follows the text's framing; low source -> more hedging/refusal
  null         no cell differs beyond the declared threshold -> coding tracks mechanism, not authority; report it
ANCHORS      row 1 must stay internal and row 13 external in every cell; if an anchor moves,
             the manipulation broke the mechanism reading and the cell is reported as such.

STATUS: instrument only. No model endpoint here; the authoring session is not a blind
subject. runs/constructed.jsonl exercises the scorer and says constructed: true.

  python v2d.py prompt <agent:high|low> <source:high|low>
  python v2d.py emit            # writes prompts/authority_A*_S*.txt
  python v2d.py plan --seed 7
  python v2d.py score RUNS.jsonl
  python v2d.py selftest
"""
import argparse
import itertools
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.path.insert(0, PKG)
from ledger import LOCUS_DEFINITIONS, parse_locus, SchemaError  # noqa: E402

STIM = json.load(open(os.path.join(HERE, "stimuli.json")))
LEVELS = ("high", "low")
GRADERS = ("gpt", "deepseek", "gemini")          # + kimi once verified (T-c)
VERBATIM = {r["row"]: r for r in [json.loads(l) for l in open(os.path.join(PKG, "fixtures", "maria_verbatim.jsonl")) if l.strip()][1:]}
ROW_IDS = ["1", "2", "9", "11", "C1", "C3", "13"]
# WORK ORDER v0.2 section 4: rows verbatim with the agent substituted; the contractor stays "the carrier";
# place held at "the island". Substitutions are declared here and nowhere else.
# Longer keys first: "the FEMA inventory" and "the Jacksonville" are listed so the substitution does not
# emit "the the ..."; every other grammar artifact of direct substitution is left as is (README).
SUBS = [("Crowley Maritime Corporation (Crowley), FEMA's transportation contractor", "the carrier, {AGENT_POSS} transportation contractor"),
        ("the FEMA inventory", "{AGENT_POSS} inventory"), ("the Jacksonville", "the mainland port"),
        ("Crowley", "the carrier"), ("FEMA's", "{AGENT_POSS}"), ("FEMA", "{AGENT}"),
        ("Puerto Rico's", "the island's"), ("Puerto Rico", "the island"), ("Jacksonville, FL", "the mainland port"), ("Jacksonville", "the mainland port")]
MARKET = ("regime.market",)
NULL_THRESHOLD = 1.0 / 7          # one row of seven
HEDGE_TOKENS = ("UNSURE", "DECLINE")

EXTERNAL = ("physical_damage", "regime.urgency")
INTERNAL_PREFIX = ("regime.custody", "regime.learning")


def substituted_text(row_id):
    """Verbatim OIG sentence with the declared substitutions applied and the agent left as a placeholder."""
    t = VERBATIM[row_id]["text"]
    for a, b in SUBS:
        t = t.replace(a, b)
    return t


def _fill(t, agent):
    a = STIM["agent"][agent]
    return t.replace("{AGENT_POSS}", a["poss"]).replace("{AGENT}", a["name"])


def render_row(row, agent):
    """Sentence starts are capitalized after substitution (the agent string is lowercase); nothing else is touched."""
    t = _fill(substituted_text(row["id"]), agent)
    return re.sub(r"(^|\. )([a-z])", lambda m: m.group(1) + m.group(2).upper(), t)


def only_declared_substitutions(verbatim, rendered, agent):
    """True when `rendered` differs from `verbatim` only by pairs in SUBS (agent filled) plus a sentence-initial
    capital. Walks both strings; at each position a declared pair (longest key first) or an equal character
    must apply. Returns (ok, position_of_first_undeclared_difference)."""
    pairs = sorted(((a, _fill(b, agent)) for a, b in SUBS), key=lambda p: -len(p[0]))
    i = j = 0
    while i < len(verbatim) or j < len(rendered):
        for a, b in pairs:
            b_here = b[0].upper() + b[1:] if (j == 0 or rendered[j - 2:j] == ". ") else b
            if verbatim.startswith(a, i) and rendered.startswith(b_here, j):
                i += len(a); j += len(b_here)
                break
        else:
            if i < len(verbatim) and j < len(rendered) and verbatim[i] == rendered[j]:
                i += 1; j += 1
            else:
                return False, i
    return True, i


def _mask_agent(line, agent):
    """Agent name and possessive (either capitalization) -> placeholders, for the neighbour-diff assertion."""
    a = STIM["agent"][agent]
    for k, tok in (("name", "@AGENT@"), ("poss", "@POSS@")):
        v = a[k]
        line = line.replace(v, tok).replace(v[0].upper() + v[1:], tok)
    return line


def prompt(agent, source, order=None):
    rows = STIM["rows"] if order is None else [next(r for r in STIM["rows"] if r["id"] == i) for i in order]
    L = ["You are coding failure findings. For each finding, name the MECHANISM that failed using exactly one code "
         "from the list below (or a mixed(a,b) pair). Code the mechanism, not the motive. SITE is given as a fact and is "
         "not yours to grade. If you cannot decide, write UNSURE. If you will not code a row, write DECLINE.", ""]
    L.append("Codes:")
    for k, v in LOCUS_DEFINITIONS.items():
        if not k.startswith("_"):
            L.append("  %-30s %s" % (k, v))
    L.append("  Rule: physical_damage only where SITE = damaged.")
    L.append("")
    L.append(STIM["source"][source])
    L.append("")
    for i, r in enumerate(rows, 1):
        L.append("FINDING %d  [SITE: %s]" % (i, r["site_record"]))
        L.append(render_row(r, agent))
        L.append("")
    L.append("Answer with one line per finding, in this exact form and nothing else:")
    L.append("FINDING <n>: <code>")
    return "\n".join(L), [r["id"] for r in rows]


def emit_prompt_files(out_dir=None):
    out_dir = out_dir or os.path.join(HERE, "prompts")
    os.makedirs(out_dir, exist_ok=True)
    paths = {}
    for a in LEVELS:
        for s_ in LEVELS:
            p, _ = prompt(a, s_)
            path = os.path.join(out_dir, "authority_A%s_S%s.txt" % (a, s_))
            with open(path, "w") as f:
                f.write(p + "\n")
            paths[(a, s_)] = path
    return paths


def neighbor_diff(pa, pb):
    """Lines that differ between two prompt files (for the selftest: exactly the agent string or the source prefix)."""
    la, lb = open(pa).read().splitlines(), open(pb).read().splitlines()
    return [(x, y) for x, y in zip(la, lb) if x != y] + ([("<len>", "<len>")] if len(la) != len(lb) else [])


def plan(seed=7):
    rng = random.Random(seed)
    cells = [{"agent": a, "source": s} for a in LEVELS for s in LEVELS]
    rows = [{"cell": c, "grader": g} for c in cells for g in GRADERS]
    rng.shuffle(rows)
    return [{"order_index": i, "run_id": "v2d-%02d" % i, **r} for i, r in enumerate(rows)]


def parse_response(text, row_ids):
    out = {}
    for line in text.strip().splitlines():
        s = line.strip()
        if not s.upper().startswith("FINDING"):
            continue
        try:
            head, code = s.split(":", 1)
            n = int(head.split()[1]) - 1
        except (ValueError, IndexError):
            continue
        if 0 <= n < len(row_ids):
            out[row_ids[n]] = code.strip()
    return out


def classify(code, site_record):
    """-> ('external'|'internal'|'other'|'hedge'|'invalid', parts)"""
    if not code or code.upper() in HEDGE_TOKENS:
        return "hedge", []
    try:
        parts = parse_locus(code)
    except SchemaError:
        return "invalid", []
    if "physical_damage" in parts and site_record != "damaged":
        return "invalid", parts                  # rule violation, counted separately, kept
    ext = any(p in EXTERNAL for p in parts)
    inte = any(p.startswith(INTERNAL_PREFIX) for p in parts)
    if ext and inte:
        return "mixed", parts
    return ("external" if ext else "internal" if inte else "other"), parts


def score_run(run, row_ids=None):
    row_ids = row_ids or [r["id"] for r in STIM["rows"]]
    site = {r["id"]: r["site_record"] for r in STIM["rows"]}
    codes = parse_response(run["raw_response"], row_ids)
    per_row = {}
    for rid in row_ids:
        cls, parts = classify(codes.get(rid), site[rid])
        per_row[rid] = {"code": codes.get(rid), "class": cls}
    coded = [r for r in per_row.values() if r["class"] not in ("hedge", "invalid")]
    n = len(row_ids)
    ext = sum(1 for r in coded if r["class"] in ("external", "mixed"))
    inte = sum(1 for r in coded if r["class"] in ("internal", "mixed"))
    mkt = sum(1 for r in coded if any(p in MARKET for p in (parse_locus(r["code"]) if r["code"] and r["code"].upper() not in HEDGE_TOKENS else [])))
    hedge = sum(1 for r in per_row.values() if r["class"] == "hedge")
    invalid = sum(1 for r in per_row.values() if r["class"] == "invalid")
    anchors_ok = per_row["1"]["class"] in ("internal",) and per_row["13"]["class"] in ("external",)
    return {"per_row": per_row, "external_share": ext / len(coded) if coded else None,
            "internal_share": inte / len(coded) if coded else None,
            "market_share": mkt / len(coded) if coded else None,
            "hedge_rate": hedge / n, "invalid": invalid, "anchors_hold": anchors_ok}


def score_file(path):
    runs = [json.loads(l) for l in open(path) if l.strip()]
    constructed = any(r.get("constructed") for r in runs)
    cells = {}
    for r in runs:
        key = "agent=%s|source=%s" % (r["cell"]["agent"], r["cell"]["source"])
        sc = score_run(r)
        cells.setdefault(key, []).append({"grader": r.get("grader"), **sc})
    summary = {}
    for key, lst in cells.items():
        def mean(k):
            v = [x[k] for x in lst if x[k] is not None]
            return round(sum(v) / len(v), 3) if v else None
        summary[key] = {"n_runs": len(lst), "external_share": mean("external_share"), "internal_share": mean("internal_share"),
                        "market_share": mean("market_share"), "hedge_rate": mean("hedge_rate"), "invalid_total": sum(x["invalid"] for x in lst),
                        "anchors_hold_all": all(x["anchors_hold"] for x in lst)}
    def cell(a, s):
        return summary.get("agent=%s|source=%s" % (a, s))
    def eff(metric):
        vals = {(a, s): (cell(a, s) or {}).get(metric) for a in LEVELS for s in LEVELS}
        if any(v is None for v in vals.values()):
            return None
        agent = ((vals[("high", "high")] + vals[("high", "low")]) - (vals[("low", "high")] + vals[("low", "low")])) / 2
        source = ((vals[("high", "high")] + vals[("low", "high")]) - (vals[("high", "low")] + vals[("low", "low")])) / 2
        inter = ((vals[("high", "high")] - vals[("high", "low")]) - (vals[("low", "high")] - vals[("low", "low")])) / 2
        return {"agent_high_minus_low": round(agent, 3), "source_high_minus_low": round(source, 3), "interaction": round(inter, 3)}
    contrasts = {m: eff(m) for m in ("external_share", "internal_share", "market_share", "hedge_rate")}
    ext = contrasts["external_share"]
    reading = None
    if ext:
        if abs(ext["agent_high_minus_low"]) < NULL_THRESHOLD and abs(ext["source_high_minus_low"]) < NULL_THRESHOLD and abs(ext["interaction"]) < NULL_THRESHOLD:
            reading = "NULL: no cell differs beyond %.2f on external share; coding tracks mechanism, not authority" % NULL_THRESHOLD
        elif ext["agent_high_minus_low"] >= NULL_THRESHOLD:
            reading = "DEFERENCE: high-authority agent drew more external attribution"
        elif ext["agent_high_minus_low"] <= -NULL_THRESHOLD:
            reading = "SYMPATHY: volunteer agent drew more external attribution"
        else:
            reading = "SOURCE or INTERACTION effect on external share; see contrasts"
    # row-level movers: which rows change class across cells
    movers = {}
    for rid in [r["id"] for r in STIM["rows"]]:
        classes = {}
        for key, lst in cells.items():
            classes[key] = sorted({x["per_row"][rid]["class"] for x in lst})
        movers[rid] = {"classes_by_cell": classes, "moved": len({tuple(v) for v in classes.values()}) > 1}
    return {"constructed": constructed, "n_runs": len(runs), "cells": summary, "contrasts": contrasts,
            "null_threshold": NULL_THRESHOLD, "reading": reading, "rows": movers}


def selftest():
    p, ids = prompt("high", "low")
    assert "the federal emergency agency" in p and "A local resident reported:" in p and ids[0] == "1" and ids[-1] == "13"
    p2, _ = prompt("low", "high")
    assert "community volunteer network" in p2 and "inspector general" in p2
    for bad in ("Puerto Rico", "FEMA", "Crowley", "Jacksonville"):
        assert bad not in p2 and bad not in p
    # emitted files: neighbours differ by exactly the agent string or exactly the source prefix
    paths = emit_prompt_files()
    for (a, s_), path in paths.items():
        other_agent = "low" if a == "high" else "high"
        d = neighbor_diff(path, paths[(other_agent, s_)])
        assert d and all(_mask_agent(x, a) == _mask_agent(y, other_agent) for x, y in d), (a, s_, d)
        assert all(x != y and ("@AGENT@" in _mask_agent(x, a) or "@POSS@" in _mask_agent(x, a)) for x, y in d), (a, s_)
        other_source = "low" if s_ == "high" else "high"
        d2 = neighbor_diff(path, paths[(a, other_source)])
        assert d2 == [(STIM["source"][s_], STIM["source"][other_source])], (a, s_, d2)
        assert "the the" not in open(path).read()
    # row text otherwise identical to maria_verbatim.jsonl: only declared substitutions (SUBS) separate them
    for rid in ROW_IDS:
        assert "{AGENT" in substituted_text(rid) or rid == "13"
        for a in LEVELS:
            row = next(r for r in STIM["rows"] if r["id"] == rid)
            ok, pos = only_declared_substitutions(VERBATIM[rid]["text"], render_row(row, a), a)
            assert ok, (rid, a, pos, VERBATIM[rid]["text"][pos:pos + 40])
    # the check is not vacuous: one changed word is caught
    assert not only_declared_substitutions("FEMA did not require Crowley.", "The federal emergency agency did require the carrier.", "high")[0]
    txt = "FINDING 1: regime.custody.state\nFINDING 2: regime.market\nFINDING 3: regime.custody.state\nFINDING 4: regime.urgency\n" \
          "FINDING 5: regime.custody.responsibility\nFINDING 6: UNSURE\nFINDING 7: physical_damage"
    sc = score_run({"raw_response": txt})
    assert sc["anchors_hold"] and sc["hedge_rate"] == 1 / 7 and abs(sc["external_share"] - 2 / 6) < 1e-9
    bad = score_run({"raw_response": txt.replace("FINDING 3: regime.custody.state", "FINDING 3: physical_damage")})
    assert bad["invalid"] == 1                                                      # row 9 site undamaged
    assert len(plan()) == 12
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("prompt"); p.add_argument("agent", choices=LEVELS); p.add_argument("source", choices=LEVELS)
    p = sub.add_parser("plan"); p.add_argument("--seed", type=int, default=7)
    p = sub.add_parser("score"); p.add_argument("runs")
    sub.add_parser("selftest")
    sub.add_parser("emit")
    a = ap.parse_args()
    if a.cmd == "prompt":
        print(prompt(a.agent, a.source)[0])
    elif a.cmd == "plan":
        for r in plan(a.seed):
            print(json.dumps(r))
    elif a.cmd == "score":
        out = score_file(a.runs)
        if out["constructed"]:
            print("*** CONSTRUCTED FIXTURE: these are not grader responses ***")
        print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
        print("movers:", {k: v["moved"] for k, v in out["rows"].items()})
    elif a.cmd == "selftest":
        selftest()
    elif a.cmd == "emit":
        for k, p in sorted(emit_prompt_files().items()):
            print(k, p)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
