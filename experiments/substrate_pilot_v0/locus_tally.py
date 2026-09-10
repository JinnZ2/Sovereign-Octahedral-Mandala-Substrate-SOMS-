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
from ledger import check_locus, parse_locus  # noqa: E402


def load(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    header = rows[0] if rows and "_header" in rows[0] else {}
    body = [r for r in rows if "_header" not in r]
    for r in body:
        check_locus(r["locus"], r["site"])                      # V1: raises SchemaError on a bad row
    return header, body


def tally(body):
    t = Counter()
    for r in body:
        parts = parse_locus(r["locus"])
        if len(parts) > 1:
            t["mixed"] += 1
        elif parts[0] == "physical_damage":
            t["physical_damage"] += 1
        else:
            t["regime"] += 1
    by_locus = Counter(r["locus"] for r in body)
    by_site = Counter(r["site"] for r in body)
    second = sum(1 for r in body if r.get("second_grader_locus") is not None)
    disagreements = sum(1 for r in body if r.get("disagreement"))
    return {"n": len(body), "coarse": dict(t), "by_locus": dict(by_locus), "by_site": dict(by_site),
            "second_grader_rows": second, "disagreements": disagreements}


def main(paths):
    out = {}
    for p in paths:
        header, body = load(p)
        out[os.path.basename(p)] = {"header": header.get("_header"), "titles_verified": header.get("titles_verified"),
                                    "coverage": header.get("coverage"), "tally_citable": header.get("tally_citable", False),
                                    "tally": tally(body)}
    names = list(out)
    print("%-28s" % "" + "".join("%-26s" % n[:25] for n in names))
    for k in ("regime", "mixed", "physical_damage"):
        print("%-28s" % k + "".join("%-26s" % out[n]["tally"]["coarse"].get(k, 0) for n in names))
    print("%-28s" % "rows" + "".join("%-26s" % out[n]["tally"]["n"] for n in names))
    print("%-28s" % "second-grader rows" + "".join("%-26s" % out[n]["tally"]["second_grader_rows"] for n in names))
    print("%-28s" % "citable" + "".join("%-26s" % out[n]["tally_citable"] for n in names))
    print()
    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    paths = sys.argv[1:] or sorted(glob.glob(os.path.join(HERE, "fixtures", "*_locus.jsonl")))
    main(paths)
