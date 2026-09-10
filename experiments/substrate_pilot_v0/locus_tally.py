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
        check_locus(r["locus"], r["site"])                      # V1: raises SchemaError on a bad row
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
    rows = [r for r in body if r.get(key)]
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


def main(paths):
    out = {}
    for p in paths:
        header, body = load(p)
        out[os.path.basename(p)] = {"header": header.get("_header"), "titles_verified": header.get("titles_verified"),
                                    "coverage": header.get("coverage"), "tally_citable": header.get("tally_citable", False),
                                    "tally": tally(body),
                                    "tally_grader2": tally(body, key="second_grader_locus") if any(r.get("second_grader_locus") for r in body) else None,
                                    "agreement": agreement(body)}
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
