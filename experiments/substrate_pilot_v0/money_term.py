"""
money_term.py -- MONEY_TERM declaration tool (ROLLUP A7; SPEC BND row "money/token only at declared
boundary (R-09 revised)", Phase 3 token rules, Phase 4 MONEY_TERM scope declaration, FT-11).

  record   {id, quantity, denominated_in: money|token|<declared unit>, stands_for: <measurand id or None>,
            boundary: donor|grant|none, scope: {what, whose_need, period} or None, token: {...} or None}
  registry {id: record}  -- measurands and money terms; a measurand record has denominated_in = its own unit
  gate(record, registry) -> (verdict, reasons)
     NATIVE          denominated in a declared unit, not money or token
     DECLARED        money or token at a declared boundary with a scope declaration; a token also
                     satisfies R-09 (need-issued, non-convertible, reset per period, no interest,
                     declared override committee)
     PROXY_UNROOTED  money or token standing for a need or quantity with no declaration rooting it in a
                     native measurand (or the token breaks an R-09 rule)
     CIRCULAR        the root chain (stands_for ...) returns to the record, or passes through a record
                     the money term is used to explain

Three worked cases live in CASES; their classification is the executor's reading of the cited
sources and is marked so. Nothing here fetches; the citations are locators.

  python money_term.py            # selftest + the three cases
"""
import json
import sys

VERDICTS = ("NATIVE", "DECLARED", "PROXY_UNROOTED", "CIRCULAR")
MONEY_LIKE = ("money", "token")
R09 = {"need_issued": True, "convertible": False, "reset_per_period": True, "interest": False}   # + override_committee named


def _root_chain(record, registry):
    seen, cur = [], record
    while cur is not None and cur.get("stands_for"):
        nxt = cur["stands_for"]
        if nxt in seen or nxt == record["id"]:
            return seen + [nxt], True
        seen.append(nxt)
        cur = registry.get(nxt)
    return seen, False


def r09_check(token):
    fails = [k for k, want in R09.items() if token.get(k) != want]
    if not token.get("override_committee"):
        fails.append("override_committee")
    return fails


def gate(record, registry):
    reasons = []
    den = record.get("denominated_in")
    if den not in MONEY_LIKE:
        return "NATIVE", ["denominated in a declared unit: %s" % den]
    chain, cyc = _root_chain(record, registry)
    explains = record.get("explains")
    if cyc:
        return "CIRCULAR", ["root chain returns to the record: %s" % " -> ".join([record["id"]] + chain)]
    if explains and explains in chain:
        return "CIRCULAR", ["root chain passes through %s, which the term is used to explain: %s" % (explains, " -> ".join([record["id"]] + chain))]
    if den == "token":
        fails = r09_check(record.get("token") or {})
        if fails:
            return "PROXY_UNROOTED", ["token breaks R-09: %s" % ", ".join(fails)]
    if record.get("boundary") in ("donor", "grant") and record.get("scope") and all(record["scope"].get(k) for k in ("what", "whose_need", "period")):
        rooted = chain and registry.get(chain[-1], {}).get("denominated_in") not in MONEY_LIKE
        if rooted:
            return "DECLARED", ["scope declared at the %s boundary; rooted in %s" % (record["boundary"], chain[-1])]
        reasons.append("scope declared but the root is not a native measurand")
    if not chain:
        reasons.append("no stands_for: the money term names no measurand")
    elif registry.get(chain[-1], {}).get("denominated_in") in MONEY_LIKE:
        reasons.append("root %s is itself money-denominated" % chain[-1])
    else:
        reasons.append("rooted in %s but no boundary/scope declaration" % chain[-1])
    return "PROXY_UNROOTED", reasons


# ---- worked cases (executor's reading; citations are locators, not fetched here) -----------------
CASES = {
    "obermeyer_cost_as_need": {
        "source": "Obermeyer, Powers, Vogeli, Mullainathan, Science 366:447 (2019): a care-management algorithm used past health-care cost as the label for health need",
        "registry": {
            "health_need": {"id": "health_need", "denominated_in": "active chronic conditions", "stands_for": None},
            "past_cost": {"id": "past_cost", "denominated_in": "money", "stands_for": "health_need", "boundary": "none", "scope": None},
        },
        "record": "past_cost", "expected": "PROXY_UNROOTED",
        "read": "cost stands for need with no declaration of the mapping; the mapping differed by group (less spent on Black patients at equal need), so the proxy was unrooted where it mattered",
    },
    "solow_cost_share": {
        "source": "Solow, Rev. Econ. Stat. 39:312 (1957): output elasticities set equal to factor cost shares; the residual explains the part of output growth the shares do not",
        "registry": {
            "output_value": {"id": "output_value", "denominated_in": "money", "stands_for": None},
            "cost_share": {"id": "cost_share", "denominated_in": "money", "stands_for": "output_value", "boundary": "none", "scope": None,
                           "explains": "output_value"},
        },
        "record": "cost_share", "expected": "CIRCULAR",
        "read": "the weights are shares of the same money quantity whose growth they are used to decompose; the residual is defined by them",
    },
    "choice_system_token": {
        "source": "Prendergast, JEP 31(4):145 (2017): Feeding America's Choice System; shares issued by need, non-convertible, pool reset daily, no interest, override by the organization",
        "registry": {
            "pantry_need": {"id": "pantry_need", "denominated_in": "declared nutrition units per person-day", "stands_for": None},
            "choice_share": {"id": "choice_share", "denominated_in": "token", "stands_for": "pantry_need", "boundary": "grant",
                             "scope": {"what": "allocation priority among pantries", "whose_need": "pantry catchment, poverty-weighted", "period": "daily"},
                             "token": {"need_issued": True, "convertible": False, "reset_per_period": True, "interest": False, "override_committee": "Feeding America allocation staff"}},
        },
        "record": "choice_share", "expected": "DECLARED",
        "read": "a token that satisfies every R-09 rule and declares what it stands for; the SPEC Phase 3 model",
    },
}


def run_cases():
    out = {}
    for name, c in CASES.items():
        v, reasons = gate(c["registry"][c["record"]], c["registry"])
        out[name] = {"verdict": v, "expected": c["expected"], "match": v == c["expected"], "reasons": reasons}
    return out


def selftest():
    res = run_cases()
    assert all(r["match"] for r in res.values()), res
    reg = {"units": {"id": "units", "denominated_in": "meals", "stands_for": None}}
    assert gate(reg["units"], reg)[0] == "NATIVE"
    # a token missing one R-09 rule is not DECLARED
    c = json.loads(json.dumps(CASES["choice_system_token"]))
    c["registry"]["choice_share"]["token"]["convertible"] = True
    v, why = gate(c["registry"]["choice_share"], c["registry"])
    assert v == "PROXY_UNROOTED" and "convertible" in why[0]
    # money at a boundary with scope but rooted in money -> not DECLARED
    reg = {"m1": {"id": "m1", "denominated_in": "money", "stands_for": "m2", "boundary": "grant", "scope": {"what": "x", "whose_need": "y", "period": "z"}},
           "m2": {"id": "m2", "denominated_in": "money", "stands_for": None}}
    assert gate(reg["m1"], reg)[0] == "PROXY_UNROOTED"
    reg["m2"]["stands_for"] = "m1"
    assert gate(reg["m1"], reg)[0] == "CIRCULAR"
    print("money_term selftest ok")


if __name__ == "__main__":
    selftest()
    for k, v in run_cases().items():
        print("%-26s %-15s %s" % (k, v["verdict"], "; ".join(v["reasons"])))
