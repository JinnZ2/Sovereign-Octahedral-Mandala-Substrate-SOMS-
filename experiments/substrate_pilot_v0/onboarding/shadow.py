"""
Phase 0 SHADOW — divergence between the legacy ledger and the substrate ledger
per operational period. Reads legacy CSV exports; writes nothing to legacy.

  python shadow.py legacy_inventory.csv legacy_receipts.csv substrate_root/

Divergence classes (the residual: what the legacy record is not holding):
  MISSING_STATE     legacy shows movement, substrate has no C1 record (FT-01)
  UNKNOWN_LOCATION  legacy location is a relabelled loss (FT-02)
  NO_RECEIPT        legacy marks delivered, no receiver mark (FT-05)
  UNIT_MISMATCH     legacy counts boxes/pounds, need declared in kcal etc. (FT-07)
  MONEY_AHEAD       legacy invoice paid, no receipt (FT-11)
Exit: 4 periods reconciled, every divergence classified.
"""
import csv
import json
import os
import sys
from collections import Counter


def load_substrate(root, copy="primary"):
    p = os.path.join(root, copy, "ledger.jsonl")
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p) if l.strip()]


def divergence(inventory_rows, receipt_rows, events):
    unit_ids = {e["unit_id"] for e in events if e["type"] == "UNIT"}
    receipted = {e["unit_id"] for e in events if e["type"] == "RECEIPT"}
    classes = Counter()
    detail = []
    for r in inventory_rows:
        uid = r.get("unit_id") or r.get("sku")
        loc = (r.get("location") or "").strip().lower()
        if uid not in unit_ids:
            classes["MISSING_STATE"] += 1
            detail.append({"unit": uid, "class": "MISSING_STATE"})
        if loc.startswith("unknown"):
            classes["UNKNOWN_LOCATION"] += 1
            detail.append({"unit": uid, "class": "UNKNOWN_LOCATION"})
        if (r.get("unit") or "").lower() in ("lb", "lbs", "pounds", "box", "boxes", "cases"):
            classes["UNIT_MISMATCH"] += 1
    for r in receipt_rows:
        uid = r.get("unit_id")
        if (r.get("status") or "").lower() == "delivered" and uid not in receipted:
            classes["NO_RECEIPT"] += 1
            detail.append({"unit": uid, "class": "NO_RECEIPT"})
        if (r.get("paid") or "").lower() in ("y", "yes", "true", "1") and uid not in receipted:
            classes["MONEY_AHEAD"] += 1
            detail.append({"unit": uid, "class": "MONEY_AHEAD"})
    return {"classes": dict(classes), "detail": detail}


def main(argv):
    if len(argv) != 4:
        print(__doc__)
        return 2
    inv = list(csv.DictReader(open(argv[1])))
    rec = list(csv.DictReader(open(argv[2])))
    ev = load_substrate(argv[3])
    print(json.dumps(divergence(inv, rec, ev), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
