"""
V2 / V10 — load LOCUS-coded fixtures, validate every row against the V1 schema,
print the tally per LOCUS beside each other. Second-grader slots are present and
empty; no tally is citable until they are filled (the header says so).

  python locus_tally.py [fixtures/*.jsonl]
"""
import glob
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ledger import check_locus, parse_locus, LOCUS_DEFINITIONS  # noqa: E402


def load(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    header = rows[0] if rows and "_header" in rows[0] else {}
    body = [r for r in rows if "_header" not in r]
    for r in body:
        if r.get("locus"):
            check_locus(r["locus"], r.get("site_record") or r["site"])   # V1: SITE is the record fact
    return header, body


def top_level(locus):
    """regime = every component is a regime axis; physical_damage = only damage;
    mixed = damage AND at least one regime axis."""
    parts = parse_locus(locus)
    dmg = "physical_damage" in parts
    reg = any(p != "physical_damage" for p in parts)
    return "mixed" if dmg and reg else "physical_damage" if dmg else "regime"


def regime_axes(locus):
    return {p for p in parse_locus(locus) if p != "physical_damage"}


def tally(body, key="locus"):
    rows = [r for r in body if r.get(key)]          # pending stubs (locus None) are not tallied
    t = Counter(top_level(r[key]) for r in rows)
    return {"n": len(rows), "coarse": {k: t.get(k, 0) for k in ("regime", "mixed", "physical_damage")},
            "by_locus": dict(Counter(r[key] for r in rows)),
            "by_site": dict(Counter(r["site" if key == "locus" else "second_grader_site"] for r in rows)),
            "second_grader_rows": sum(1 for r in body if r.get("second_grader_locus") is not None),
            "disagreements": sum(1 for r in body if r.get("disagreement"))}


def agreement(body):
    """Two-grader agreement, computed from the rows, not restated."""
    rows = [r for r in body if r.get("second_grader_locus")]
    if not rows:
        return None
    n = len(rows)
    site = sum(1 for r in rows if r["site"] == r["second_grader_site"])
    any1 = sum(1 for r in rows if regime_axes(r["locus"]))
    any2 = sum(1 for r in rows if regime_axes(r["second_grader_locus"]))
    t1 = [top_level(r["locus"]) for r in rows]
    t2 = [top_level(r["second_grader_locus"]) for r in rows]
    top = sum(1 for a, b in zip(t1, t2) if a == b)
    po = top / n
    classes = ("regime", "mixed", "physical_damage")
    pe = sum((t1.count(c) / n) * (t2.count(c) / n) for c in classes)
    kappa = (po - pe) / (1 - pe) if pe < 1 else None
    pure1 = t1.count("physical_damage"); pure2 = t2.count("physical_damage")
    exact = overlap = disjoint = 0
    for r in rows:
        a, b = regime_axes(r["locus"]), regime_axes(r["second_grader_locus"])
        if not a:
            continue                       # rows with no regime axis in grader 1 are not sub-axis comparable
        if a == b:
            exact += 1
        elif a & b:
            overlap += 1
        else:
            disjoint += 1
    moved_to_damage = sum(1 for a, b in zip(t1, t2) if a != "physical_damage" and b == "physical_damage")
    return {"n": n, "site_agree": site, "any_regime_component": [any1, any2], "top_level_agree": top,
            "top_level_observed": round(po, 3), "top_level_expected": round(pe, 3), "kappa": round(kappa, 3),
            "pure_physical_damage_rows": [pure1, pure2],
            "sub_axis": {"comparable": exact + overlap + disjoint, "exact": exact, "overlap": overlap, "disjoint": disjoint},
            "rows_moved_to_physical_damage_by_grader2": moved_to_damage,
            "N-1_fires": moved_to_damage >= 3}


# ------------------------------------------------------------------ multi-grader analysis (round 1)
def _pairs(seq):
    return [(seq[i], seq[j]) for i in range(len(seq)) for j in range(i + 1, len(seq))]


def three_way(body):
    rows = [r for r in body if r.get("graders")]
    if not rows:
        return None
    graders = list(rows[0]["graders"]["round1"])
    out = {"graders": graders, "n": len(rows)}
    loc = {g: [r["graders"]["round1"][g]["locus"] for r in rows] for g in graders}
    out["any_regime_component"] = {g: sum(1 for l in loc[g] if regime_axes(l)) for g in graders}
    out["pure_physical_damage"] = {g: sum(1 for l in loc[g] if top_level(l) == "physical_damage") for g in graders}
    out["top_level_tally"] = {g: dict(Counter(top_level(l) for l in loc[g])) for g in graders}
    out["pairwise_top_level_agree"] = {"%s-%s" % (a, b): sum(1 for x, y in zip(loc[a], loc[b]) if top_level(x) == top_level(y))
                                       for a, b in _pairs(graders)}
    dmg = {g: ["physical_damage" in parse_locus(l) for l in loc[g]] for g in graders}
    out["damage_flag_unanimous_no_rows"] = [r["row"] for i, r in enumerate(rows) if not any(dmg[g][i] for g in graders)]
    out["damage_flag_unanimous_yes_rows"] = [r["row"] for i, r in enumerate(rows) if all(dmg[g][i] for g in graders)]
    maj = {}
    for i, r in enumerate(rows):
        votes = Counter()
        for g in graders:
            for ax in regime_axes(loc[g][i]):
                votes[ax] += 1
        top = [ax for ax, c in votes.items() if c >= 2]
        maj[r["row"]] = top[0] if len(top) == 1 else (top if top else None)
    out["sub_axis_majority"] = maj
    out["sub_axis_majority_counts"] = dict(Counter(v if isinstance(v, str) else ("none" if v is None else "tie") for v in maj.values()))
    # graded site vs record fact (instrument fix): unspecified counts as agreeing with the record
    out["site_vs_record_mismatches"] = {
        g: [r["row"] for r in rows if r["graders"]["round1"][g].get("site") not in (None, r["site_record"])] for g in graders}
    return out


def round2(body):
    rows = []
    for r in body:
        for sub, g in (r.get("graders", {}).get("round2") or {}).items():
            rows.append((sub, g))
    if not rows:
        return None
    a = [parse_locus(g["gpt"]) for _, g in rows]
    b = [parse_locus(g["deepseek"]) for _, g in rows]
    exact = overlap = disjoint = 0
    jac = []
    disjoint_rows = []
    for (sub, _), x, y in zip(rows, a, b):
        sx, sy = set(x), set(y)
        jac.append(len(sx & sy) / len(sx | sy))
        if sx == sy:
            exact += 1
        elif sx & sy:
            overlap += 1
        else:
            disjoint += 1
            disjoint_rows.append(sub)
    n = len(rows)
    # kappa over label SETS as categories
    ca, cb = [frozenset(x) for x in a], [frozenset(y) for y in b]
    po = exact / n
    cats = set(ca) | set(cb)
    pe = sum((ca.count(c) / n) * (cb.count(c) / n) for c in cats)
    kappa = (po - pe) / (1 - pe) if pe < 1 else None
    custody_both = sum(1 for x, y in zip(a, b) if any(p.startswith("regime.custody") for p in x) and any(p.startswith("regime.custody") for p in y))
    dmg = [sum(1 for x in a if "physical_damage" in x), sum(1 for y in b if "physical_damage" in y)]
    return {"n": n, "exact": exact, "overlap": overlap, "disjoint": disjoint, "disjoint_rows": disjoint_rows,
            "mean_jaccard": round(sum(jac) / n, 3), "kappa_label_sets": round(kappa, 3),
            "observed": round(po, 3), "expected": round(pe, 3),
            "custody_in_both": custody_both, "physical_damage_rows": dmg,
            "label_tally": {"gpt": dict(Counter("+".join(sorted(x)) for x in a)), "deepseek": dict(Counter("+".join(sorted(y)) for y in b))}}


# ------------------------------------------------------------------ V10b report-type split + retention
def report_type_split(body, sources):
    rows = [r for r in body if r.get("doc_type")]
    if not rows:
        return None
    out = {"by_doc_type": {}, "stated_cause_codable": 0, "stated_cause_pending": 0}
    for dt in ("audit", "review", "self-review"):
        sub = [r for r in rows if r["doc_type"] == dt and r.get("locus")]
        t = Counter(top_level(r["locus"]) for r in sub)
        dmg_any = sum(1 for r in sub if "physical_damage" in parse_locus(r["locus"]))
        out["by_doc_type"][dt] = {"coded_rows": len(sub), "top_level": dict(t),
                                  "damage_component_share": round(dmg_any / len(sub), 2) if sub else None,
                                  "kinds": dict(Counter(r["row_kind"] for r in sub))}
    out["stated_cause_codable"] = sum(1 for r in rows if r["row_kind"] == "stated_cause" and r.get("locus"))
    out["stated_cause_pending"] = sum(1 for r in rows if r["row_kind"] == "stated_cause" and not r.get("locus"))
    out["evaluable"] = out["stated_cause_codable"] > 0
    out["null_check"] = ("NOT EVALUABLE: no coded stated-cause rows; extraction pending" if not out["evaluable"] else "see by_doc_type")
    ret = [r for r in rows if r.get("doc_id") == "K3" and r.get("recurred_in_M1") is not None]
    out["retention_K3_to_M1"] = dict(Counter(str(r["recurred_in_M1"]).split(" ")[0] for r in ret))
    ret_all = [r for r in rows if r.get("row_kind") == "mechanism_finding" and r.get("recurred_in_M1") is not None]
    out["retention_all_katrina_rows_to_M1"] = dict(Counter(str(r["recurred_in_M1"]).split(" ")[0] for r in ret_all))
    return out


def main(paths):
    out = {}
    for p in paths:
        header, body = load(p)
        out[os.path.basename(p)] = {"header": header.get("_header"), "titles_verified": header.get("titles_verified"),
                                    "coverage": header.get("coverage"), "tally_citable": header.get("tally_citable", False),
                                    "tally": tally(body),
                                    "tally_grader2": tally(body, key="second_grader_locus") if any(r.get("second_grader_locus") for r in body) else None,
                                    "agreement": agreement(body),
                                    "three_way": three_way(body), "round2": round2(body),
                                    "report_type_split": report_type_split(body, None)}
    names = list(out)
    print("%-28s" % "" + "".join("%-26s" % n[:25] for n in names))
    for k in ("regime", "mixed", "physical_damage"):
        print("%-28s" % k + "".join("%-26s" % out[n]["tally"]["coarse"].get(k, 0) for n in names))
    print("%-28s" % "rows" + "".join("%-26s" % out[n]["tally"]["n"] for n in names))
    print("%-28s" % "second-grader rows" + "".join("%-26s" % out[n]["tally"]["second_grader_rows"] for n in names))
    print("%-28s" % "citable" + "".join("%-26s" % (str(out[n]["tally_citable"])[:25]) for n in names))
    for n in names:
        if out[n]["tally_grader2"]:
            g2 = out[n]["tally_grader2"]["coarse"]; a = out[n]["agreement"]
            print()
            print("%s  grader 2: regime %d | mixed %d | physical_damage %d" % (n, g2["regime"], g2["mixed"], g2["physical_damage"]))
            print("  SITE %d/%d | any regime component %d/%d vs %d/%d | top level %d/%d kappa %.3f "
                  "(observed %.3f, expected %.3f) | pure physical_damage %d vs %d | sub-axis exact %d overlap %d disjoint %d of %d"
                  % (a["site_agree"], a["n"], a["any_regime_component"][0], a["n"], a["any_regime_component"][1], a["n"],
                     a["top_level_agree"], a["n"], a["kappa"], a["top_level_observed"], a["top_level_expected"],
                     a["pure_physical_damage_rows"][0], a["pure_physical_damage_rows"][1],
                     a["sub_axis"]["exact"], a["sub_axis"]["overlap"], a["sub_axis"]["disjoint"], a["sub_axis"]["comparable"]))
            print("  N-1 fires: %s (grader 2 moved %d rows to physical_damage)" % (a["N-1_fires"], a["rows_moved_to_physical_damage_by_grader2"]))
        tw = out[n]["three_way"]
        if tw:
            print("  THREE-WAY %s: any regime %s | pure damage %s | pairwise top level %s" % (
                tw["graders"], tw["any_regime_component"], tw["pure_physical_damage"], tw["pairwise_top_level_agree"]))
            print("    damage unanimous NO rows %s | unanimous YES rows %s | sub-axis majority %s" % (
                tw["damage_flag_unanimous_no_rows"], tw["damage_flag_unanimous_yes_rows"], tw["sub_axis_majority_counts"]))
            print("    graded site vs record mismatches: %s" % {g: len(v) for g, v in tw["site_vs_record_mismatches"].items()})
        r2 = out[n]["round2"]
        if r2:
            print("  ROUND 2 (V1 definitions, SITE supplied, n=%d): exact %d | overlap %d | disjoint %d %s | mean Jaccard %.3f | kappa(label sets) %.3f (obs %.3f, exp %.3f) | custody in both %d | physical_damage rows %s" % (
                r2["n"], r2["exact"], r2["overlap"], r2["disjoint"], r2["disjoint_rows"], r2["mean_jaccard"], r2["kappa_label_sets"],
                r2["observed"], r2["expected"], r2["custody_in_both"], r2["physical_damage_rows"]))
        rt = out[n]["report_type_split"]
        if rt:
            print("  V10b report-type split: %s | stated-cause coded %d, pending %d | retention K3-sourced->M1 %s, all recalled rows->M1 %s" % (
                {k: (v["coded_rows"], v["damage_component_share"]) for k, v in rt["by_doc_type"].items()},
                rt["stated_cause_codable"], rt["stated_cause_pending"], rt["retention_K3_to_M1"], rt["retention_all_katrina_rows_to_M1"]))
            print("    %s" % rt["null_check"])
    print()
    print("LOCUS definitions (V1):")
    for k, v in LOCUS_DEFINITIONS.items():
        print("  %-18s %s" % (k, v))
    print()
    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(HERE, "fixtures", "*_locus.jsonl")))
    main(paths)
