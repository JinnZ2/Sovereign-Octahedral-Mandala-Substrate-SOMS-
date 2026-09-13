"""
T3 — D_state vs D_community: predicted measurand overlap
=========================================================
Same claim, same method, two decision strings (cases.jsonl, pair dsa-01).
PREDICTION (stated before any model run): the measurand sets the two
decisions are denominated in are near-disjoint. This script scores the
prediction from lexicon.json alone; it does not run a model.

Overlap is computed three ways so the reading does not depend on one choice:
  by measurand id          exact id match
  by canonical text        token Jaccard of canonical strings
  by kind                  native / component / foreign composition

Run:  python experiments/t3_decision_anchor/predict.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def tokens(s):
    return set(re.findall(r"[a-z0-9]+", s.lower())) - {"the", "of", "in", "a", "and", "or", "per", "to", "for", "with"}


def main():
    lex = json.load(open(os.path.join(HERE, "lexicon.json")))
    cases = [json.loads(l) for l in open(os.path.join(HERE, "cases.jsonl")) if l.strip()]
    a, b = "dsa-01-state", "dsa-01-community"
    A, B = lex[a], lex[b]
    ids_a, ids_b = {e["id"] for e in A}, {e["id"] for e in B}
    inter = ids_a & ids_b
    # canonical-text overlap: best token-Jaccard per measurand across the other side
    def best(e, other):
        t = tokens(e["canonical"])
        return max((len(t & tokens(o["canonical"])) / len(t | tokens(o["canonical"])), o["id"]) for o in other)
    cross = {e["id"]: best(e, B) for e in A}
    cross_b = {e["id"]: best(e, A) for e in B}
    kinds = lambda L: {k: sum(1 for e in L if e["kind"] == k) for k in ("native", "component", "foreign")}
    # the one shared measurand is the method's native quantity; is it what either decision is denominated in?
    out = {
        "pair": "dsa-01",
        "decision_state": next(c["decision"] for c in cases if c["case_id"] == a),
        "decision_community": next(c["decision"] for c in cases if c["case_id"] == b),
        "n_measurands": {a: len(ids_a), b: len(ids_b)},
        "shared_ids": sorted(inter),
        "jaccard_by_id": len(inter) / len(ids_a | ids_b),
        "max_text_jaccard_state_to_community": {k: round(v[0], 2) for k, v in cross.items()},
        "max_text_jaccard_community_to_state": {k: round(v[0], 2) for k, v in cross_b.items()},
        "kind_composition": {a: kinds(A), b: kinds(B)},
        "prediction": "near-disjoint measurand sets",
        "prediction_holds_on_lexicon": len(inter) / len(ids_a | ids_b) < 0.15,
        "caveat": "scored on the hand-built lexicon, which is the prediction itself; a model run under "
                  "Simulators/anchor-measurand-crossing ARM D with each decision string is the test",
        "verbatim_sources": False,
    }
    print(json.dumps(out, indent=1))
    with open(os.path.join(HERE, "prediction.json"), "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
