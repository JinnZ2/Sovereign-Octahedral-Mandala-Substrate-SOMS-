"""
terrain_prior.py -- observed indicator -> substrate PRIOR, with stated confidence, stated scope,
and what would falsify it (WORK ORDER terrain_prior, 2026-09-12). CC0. Stdlib only. No network.

  It does not plan routes and does not rate terrain. It returns a prior a planner or a probe can test,
  and records what the prior was derived from so the derivation can be checked when it turns out wrong.

  TWO OUTPUT VARIABLES, NEVER COLLAPSED
    BEARING       what the ground will support, as pressure over contact area, never pass/fail
    ENTANGLEMENT  what the vegetation does to a limb swept through it, as a function of limb geometry
  They are independent and can point opposite ways. A single traversability score is the defect this
  instrument exists to remove: traversability is a relation between a morphology and a substrate, not
  a property of terrain.

  DERIVATIONS, NOT CORRELATIONS
    Every entry in derivations.jsonl carries the mechanism -- what has to be true for the indicator to
    be there. The mechanism is what transfers to a region whose species list differs. An entry without
    one is UNRATED and generates no prior (P5). region is a SCOPE field, never a lookup key.

  CHECKS
    P1_TWO_LAYER      surface and substrate differ; a surface-only reading will invert
    P2_SENSOR_INVERT  the standard sensor suite will rate this BETTER than it is (the dangerous class)
    P3_MORPH_SPLIT    bearing differs in DIRECTION across supplied morphologies; both reported, never merged
    P4_OUT_OF_SCOPE   observation region outside the entry's scope; prior returned WITH the flag, not suppressed
    P5_NO_MECHANISM   entry has no mechanism; UNRATED, no prior
  Non-P flags: NO_DERIVATION (nothing in the store derives this indicator), CONTEXT_INCOMPLETE /
  AMBIGUOUS_DERIVATION (context that selects between branches is missing), SWING_PROFILE_UNKNOWN.

  python terrain_prior.py cases                 run validation cases A-E
  python terrain_prior.py selftest
  python terrain_prior.py prior <obs.json> [<platform_id> ...]
  python terrain_prior.py entries               list derivations, mechanism first
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "derivations.jsonl")
MORPHS = os.path.join(HERE, "morphologies.json")

INDICATOR_TYPES = ("VEGETATION", "LANDFORM", "FLOW_EVIDENCE", "SUBSTRATE_VISIBLE")
BEARING_DIRECTIONS = ("SUPPORTED", "MARGINAL", "NOT_SUPPORTED")
ENTANGLEMENT_DIRECTIONS = ("PASSES", "SNAGS", "BINDS")
CONFIDENCE = ("HIGH", "MEDIUM", "LOW")
# what a limb sweeps through, per swing profile, in metres above ground. Declared, not inferred; an
# unlisted profile returns SWING_PROFILE_UNKNOWN rather than a guess.
SWING_BANDS = {"LOW_SWEEP": (0.0, 0.5), "HIGH_STEP": (0.4, 1.2), "DRAG": (0.0, 0.15), "WHEEL": (0.0, 0.25)}


def load_entries(path=STORE):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    return [r for r in rows if not r.get("_header")]


def load_morphologies(path=MORPHS):
    return {k: v for k, v in json.load(open(path)).items() if not k.startswith("_")}


# ---------------------------------------------------------------- matching
def _norm(s):
    return " ".join(str(s or "").lower().replace("-", " ").replace(",", " ").split())


def candidates(observation, entries):
    """Free-text indicator against each entry's aliases. Longest alias match wins; ties keep both."""
    text = _norm(observation.get("indicator"))
    scored = []
    for e in entries:
        best = 0
        for a in e.get("aliases", []) + [e["indicator"]]:
            an = _norm(a)
            if an and an in text:
                best = max(best, len(an))
        if best:
            scored.append((best, e))
    if not scored:
        return []
    top = max(s for s, _ in scored)
    return [e for s, e in scored if s == top]


def context_satisfied(entry, context):
    """An entry may require context to apply at all (the two sides of an obstruction are different
    derivations of the same object). Returns True | False | None for 'the context is absent'."""
    req = entry.get("requires_context")
    if not req:
        return True
    ctx = context or {}
    for flag in req.get("needs", []):
        if not ctx.get(flag):
            return None
    for key, allowed in req.items():
        if key == "needs":
            continue
        got = ctx.get(key)
        if got in (None, "UNKNOWN"):
            return None
        if got not in allowed:
            return False
    return True


# ---------------------------------------------------------------- the two variables
def bearing_relation(entry, morph):
    """The relation between one morphology's contact pressure and the layer the mechanism implies.
    Pressure over contact area, never pass/fail; the direction is the comparison, not a terrain rating."""
    band = entry.get("bearing_kpa")
    p = morph.get("contact_pressure")
    if band is None or p is None:
        return {"platform_id": morph.get("platform_id"), "direction": None,
                "statement": "no bearing band in the derivation or no contact pressure in the profile"}
    lo, hi = band
    direction = "SUPPORTED" if p <= lo else ("MARGINAL" if p <= hi else "NOT_SUPPORTED")
    surf = entry.get("surface_bearing_kpa")
    return {"platform_id": morph.get("platform_id"), "direction": direction,
            "contact_pressure_kpa": p, "contact_area_m2": morph.get("contact_area"),
            "substrate_band_kpa": [lo, hi], "surface_band_kpa": surf,
            "statement": "%.3g kPa over %.4g m2 against a substrate band of %g-%g kPa -> %s%s" % (
                p, morph.get("contact_area") or 0, lo, hi, direction,
                "" if not surf else "; the surface layer alone reads %g-%g kPa" % (surf[0], surf[1]))}


def entanglement_relation(entry, morph):
    """What the stand does to THIS limb. Geometry in, geometry out: stem extent against swing band,
    then joint exposure, ankle-to-foot ratio and recovery mode."""
    dens = entry.get("stem_density", "NONE")
    flex = entry.get("flexibility", "NONE")
    extent_hi = (entry.get("stem_height_m") or [0.0, 0.0])[1]
    band = SWING_BANDS.get(morph.get("swing_profile"))
    out = {"platform_id": morph.get("platform_id"), "swing_profile": morph.get("swing_profile"),
           "stem_extent_m": [0.0, extent_hi], "swing_band_m": list(band) if band else None}
    if dens == "NONE" or flex == "NONE" or extent_hi == 0.0:
        out.update(direction="PASSES", statement="no stem mass at limb height in the derivation")
        return out
    if band is None:
        out.update(direction=None, statement="swing profile %r is not in SWING_BANDS; no entanglement relation computed"
                   % morph.get("swing_profile"))
        return out
    overlap = extent_hi >= band[0]                                  # stems occupy 0..extent_hi
    if not overlap:
        out.update(direction="PASSES", statement="stem mass tops out at %.2g m, below the swing band %g-%g m"
                   % (extent_hi, band[0], band[1]))
        return out
    # the stand's term first: morphology ESCALATES a vegetation hazard, it never creates one. A soft,
    # sparse, non-binding stand catches nothing, whatever the limb looks like (bog: low bearing, low
    # entanglement). Without this gate an exposed-joint profile would read every stand as a snag.
    veg, why = 0, []
    if dens == "HIGH":
        veg += 2; why.append("dense stems")
    elif dens == "MODERATE":
        veg += 1; why.append("moderate stem density")
    if entry.get("binds_when_displaced"):
        veg += 2; why.append("stems bind when displaced rather than breaking")
    if flex == "WOODY":
        veg += 1; why.append("woody stems do not yield")
    if veg == 0:
        out.update(direction="PASSES", veg_score=0, morph_score=0,
                   statement="stem mass is in the swing band but the stand is sparse, soft and non-binding: "
                             "nothing for a limb to catch on")
        return out
    morph_score = 0
    if morph.get("joint_exposure"):
        morph_score += 1; why.append("exposed joints (%s)" % ", ".join(morph["joint_exposure"]))
    r = morph.get("ankle_to_foot_ratio")
    if r is not None and r < 0.5:
        morph_score += 1; why.append("ankle narrow relative to foot (ratio %.2g): stems ride up and cinch" % r)
    if morph.get("recovery_from_entanglement") == "NONE":
        morph_score += 1; why.append("no entanglement recovery")
    total = veg + morph_score
    direction = "BINDS" if total >= 4 else ("SNAGS" if total >= 2 else "PASSES")
    out.update(direction=direction, veg_score=veg, morph_score=morph_score,
               statement="%s -> %s" % ("; ".join(why), direction))
    return out


# ---------------------------------------------------------------- the prior
def region_in_scope(observation, entry):
    reg = _norm(observation.get("region"))
    if not reg:
        return None
    for s in entry.get("scope_regions", []):
        sn = _norm(s)
        if sn and (sn in reg or reg in sn):
            return True
    return False


def _prior_from(entry, observation, morphs, flags):
    ctx_ok = context_satisfied(entry, observation.get("context"))
    conf = entry.get("confidence", "LOW")
    if ctx_ok is None:
        conf = entry.get("confidence_without_context", "LOW")
    if entry.get("two_layer"):
        flags.add("P1_TWO_LAYER")
    if entry.get("sensor_reads_better"):
        flags.add("P2_SENSOR_INVERT")
    if region_in_scope(observation, entry) is False:
        flags.add("P4_OUT_OF_SCOPE")
    bearing_by = [bearing_relation(entry, m) for m in morphs]
    ent_by = [entanglement_relation(entry, m) for m in morphs]
    dirs = {b["direction"] for b in bearing_by if b["direction"]}
    if len(dirs) > 1:
        flags.add("P3_MORPH_SPLIT")
    if any(e["direction"] is None and e.get("swing_band_m") is None and e["swing_profile"] for e in ent_by):
        flags.add("SWING_PROFILE_UNKNOWN")
    return {
        "bearing_prior": {"value": entry["implies_bearing"], "confidence": conf, "mechanism": entry["mechanism"],
                          "substrate_band_kpa": entry.get("bearing_kpa"), "surface_band_kpa": entry.get("surface_bearing_kpa"),
                          "by_platform": bearing_by,
                          "opposite_directions": sorted(dirs) if {"SUPPORTED", "NOT_SUPPORTED"} <= dirs else None},
        "entanglement_prior": {"value": entry["implies_entanglement"], "confidence": conf, "mechanism": entry["mechanism"],
                               "by_platform": ent_by},
        "sensor_inversion": entry.get("sensor_reads_better_why") if entry.get("sensor_reads_better") else None,
        "layers": {"surface": entry.get("surface_layer"), "substrate": entry.get("substrate_layer")} if entry.get("two_layer") else None,
        "scope": entry.get("scope"),
        "derived_from": "derivation %r; mechanism held by: %s" % (entry["indicator"], entry.get("derived_by", "unrecorded")),
        "falsified_by": entry.get("falsified_by"),
    }


def prior(observation, morphologies, entries=None):
    """observation + one or more morphology profiles -> prior. Morphology is required: there is no
    terrain rating independent of a platform."""
    entries = entries if entries is not None else load_entries()
    morphs = list(morphologies.values()) if isinstance(morphologies, dict) else list(morphologies)
    out = {"obs_id": observation.get("obs_id"), "indicator": observation.get("indicator"),
           "indicator_type": observation.get("indicator_type"), "region": observation.get("region"),
           "observer_baseline": observation.get("observer_baseline"),      # carried verbatim
           "morphologies": [m.get("platform_id") for m in morphs], "flags": []}
    flags = set()
    if not morphs:
        out["flags"] = ["NO_MORPHOLOGY"]
        out["note"] = "no morphology profile supplied; terrain is not rated on its own"
        return out
    cands = candidates(observation, entries)
    if not cands:
        out["flags"] = ["NO_DERIVATION"]
        out["note"] = "no entry in the store derives this indicator; absence of a derivation is not a safe reading"
        return out
    unrated = [c for c in cands if not str(c.get("mechanism") or "").strip()]
    if unrated:
        out["flags"] = ["P5_NO_MECHANISM"]
        out["unrated_entries"] = [c.get("indicator") for c in unrated]
        out["note"] = ("entry has an implication but no mechanism: UNRATED, no prior. A correlation without a "
                       "mechanism cannot be checked against the site and fails silently outside its source biome.")
        return out
    gated = [(c, context_satisfied(c, observation.get("context"))) for c in cands]
    applies = [c for c, ok in gated if ok is True]
    held = [c for c, ok in gated if ok is None]
    if applies:
        chosen, alternatives = applies[0], applies[1:]
    elif held:
        # the context that separates the branches is missing. Do not suppress: return the conservative
        # branch (lowest substrate band) and name the other, flagged.
        held.sort(key=lambda e: (e.get("bearing_kpa") or [0, 0])[0])
        chosen, alternatives = held[0], held[1:]
        flags.add("CONTEXT_INCOMPLETE")
        if alternatives:
            flags.add("AMBIGUOUS_DERIVATION")
    else:
        out["flags"] = ["NO_DERIVATION"]
        out["note"] = "every matching derivation is excluded by the observed context"
        return out
    out.update(_prior_from(chosen, observation, morphs, flags))
    if alternatives:
        out["alternatives"] = [{"indicator": a["indicator"], "mechanism": a["mechanism"],
                                "implies_bearing": a["implies_bearing"],
                                "resolved_by": a.get("requires_context")} for a in alternatives]
    out["flags"] = sorted(flags)
    return out


# ---------------------------------------------------------------- validation cases
def case_A(entries=None):
    """BOULDER, DRY STREAMBED, DOWNSTREAM. MUST return LOW bearing and fire P2_SENSOR_INVERT."""
    obs = {"obs_id": "A", "indicator_type": "LANDFORM", "indicator": "large boulder in a dry streambed",
           "context": {"flow_direction_known": True, "position_relative_to_obstruction": "DOWNSTREAM",
                       "season": "late summer", "recent_precipitation": "none for 3 weeks", "slope": 0.02},
           "region": "temperate headwater channel", "observer_baseline": "operator, this drainage, 30+ years of walking it"}
    M = load_morphologies()
    return prior(obs, [M["high_pressure_small_contact"], M["low_pressure_broad_contact"]], entries)


def case_A_upstream(entries=None):
    """The same observed object, flow direction reversed: the context selects the other derivation."""
    obs = {"obs_id": "A-up", "indicator_type": "LANDFORM", "indicator": "large boulder in a dry streambed",
           "context": {"flow_direction_known": True, "position_relative_to_obstruction": "UPSTREAM"},
           "region": "temperate headwater channel",
           "observer_baseline": "operator, this drainage, 30+ years of walking it"}
    M = load_morphologies()
    return prior(obs, [M["high_pressure_small_contact"]], entries)


def case_B(entries=None):
    """PINE STAND. MUST fire P1_TWO_LAYER and return bearing referencing the substrate, not the duff."""
    obs = {"obs_id": "B", "indicator_type": "VEGETATION", "indicator": "mature pine stand, deep needle litter",
           "context": {"season": "autumn", "slope": 0.05}, "region": "upper midwest",
           "observer_baseline": "operator, this county, decades"}
    M = load_morphologies()
    return prior(obs, [M["mid_pressure_exposed_joints"]], entries)


def case_C(entries=None):
    """MORPHOLOGY SPLIT. Same bog, two profiles. MUST return opposite bearing and fire P3_MORPH_SPLIT."""
    obs = {"obs_id": "C", "indicator_type": "VEGETATION", "indicator": "sphagnum bog surface, quaking underfoot",
           "context": {"season": "summer"}, "region": "upper midwest", "observer_baseline": "operator, lifelong"}
    M = load_morphologies()
    return prior(obs, [M["high_pressure_small_contact"], M["low_pressure_broad_contact"]], entries)


def case_D():
    """FALSIFIER: an entry with an implication and no mechanism. MUST fire P5 and return no prior."""
    entries = load_entries(os.path.join(HERE, "demo", "derivations_no_mechanism.jsonl"))
    obs = {"obs_id": "D", "indicator_type": "VEGETATION", "indicator": "tamarack on the edge of the opening",
           "region": "upper midwest", "observer_baseline": "unrecorded"}
    M = load_morphologies()
    return prior(obs, [M["low_pressure_broad_contact"]], entries)


def case_E(entries=None):
    """OUT OF SCOPE. MUST return the prior WITH P4 flagged, not suppress it."""
    obs = {"obs_id": "E", "indicator_type": "VEGETATION", "indicator": "cattails along the ditch",
           "context": {"season": "spring"}, "region": "gulf coastal plain",
           "observer_baseline": "visiting observer, first season"}
    M = load_morphologies()
    return prior(obs, [M["mid_pressure_exposed_joints"]], entries)


def selftest():
    entries = load_entries()
    # every shipped entry carries a mechanism, a falsifier and a scope
    for e in entries:
        assert str(e.get("mechanism") or "").strip(), e.get("indicator")
        assert e.get("falsified_by") and e.get("scope") and e.get("indicator_type") in INDICATOR_TYPES, e["indicator"]
        assert e.get("implies_bearing") and e.get("implies_entanglement")
        if e.get("two_layer"):
            assert e.get("surface_layer") and e.get("substrate_layer"), e["indicator"]

    a = case_A(entries)
    assert "P2_SENSOR_INVERT" in a["flags"], a["flags"]                       # the whole point of the instrument
    assert "P1_TWO_LAYER" in a["flags"]
    assert a["bearing_prior"]["value"].startswith("LOW")
    assert a["bearing_prior"]["substrate_band_kpa"] == [8, 25]
    assert [b["direction"] for b in a["bearing_prior"]["by_platform"]] == ["NOT_SUPPORTED", "SUPPORTED"]
    assert "P3_MORPH_SPLIT" in a["flags"]                                     # even here, morphology decides
    assert a["falsified_by"] and a["observer_baseline"].startswith("operator, this drainage")
    assert "deposition" in a["derived_from"]
    up = case_A_upstream(entries)                                             # context selects the other derivation
    assert "scour" in up["derived_from"] and up["bearing_prior"]["value"].startswith("HIGH")
    assert "P2_SENSOR_INVERT" not in up["flags"]
    # flow direction unknown: conservative branch, both named, flagged, never suppressed
    amb = prior({"obs_id": "A-amb", "indicator_type": "LANDFORM", "indicator": "boulder in a dry streambed",
                 "context": {"position_relative_to_obstruction": "UNKNOWN"}, "region": "arid wash",
                 "observer_baseline": "none"}, [load_morphologies()["high_pressure_small_contact"]], entries)
    assert "CONTEXT_INCOMPLETE" in amb["flags"] and "AMBIGUOUS_DERIVATION" in amb["flags"]
    assert amb["bearing_prior"]["confidence"] == "LOW" and amb["alternatives"]
    assert "deposition" in amb["derived_from"]                                 # the low-bearing branch is the conservative one

    b = case_B(entries)
    assert "P1_TWO_LAYER" in b["flags"] and "P2_SENSOR_INVERT" not in b["flags"]
    assert "SUBSTRATE" in b["bearing_prior"]["value"]
    bb = b["bearing_prior"]["by_platform"][0]
    assert bb["substrate_band_kpa"] == [100, 200] and bb["surface_band_kpa"] == [10, 30]
    assert bb["direction"] == "SUPPORTED"                                      # 35 kPa on the substrate
    assert b["layers"]["substrate"].startswith("drained mineral soil")

    c = case_C(entries)
    assert "P3_MORPH_SPLIT" in c["flags"]
    dirs = [x["direction"] for x in c["bearing_prior"]["by_platform"]]
    assert dirs == ["NOT_SUPPORTED", "SUPPORTED"] and c["bearing_prior"]["opposite_directions"] == ["NOT_SUPPORTED", "SUPPORTED"]
    assert len(c["bearing_prior"]["by_platform"]) == 2                          # both reported, never merged
    assert all(x["direction"] == "PASSES" for x in c["entanglement_prior"]["by_platform"])   # low bearing, low entanglement

    d = case_D()
    assert d["flags"] == ["P5_NO_MECHANISM"] and "bearing_prior" not in d and "entanglement_prior" not in d

    e = case_E(entries)
    assert "P4_OUT_OF_SCOPE" in e["flags"] and e["bearing_prior"]["value"].startswith("LOW")   # flagged, not suppressed
    assert e["scope"] == "temperate wetland margins" and e["region"] == "gulf coastal plain"
    assert e["entanglement_prior"]["by_platform"][0]["direction"] == "BINDS"

    # the two variables are independent: a case with high bearing AND high entanglement exists
    brush = prior({"obs_id": "F", "indicator_type": "VEGETATION", "indicator": "dense low brush over hardpan",
                   "region": "till plain", "observer_baseline": "operator"},
                  [load_morphologies()["mid_pressure_exposed_joints"]], entries)
    bp = brush["bearing_prior"]["by_platform"][0]
    assert bp["direction"] == "SUPPORTED" and brush["entanglement_prior"]["by_platform"][0]["direction"] == "BINDS"

    # no morphology -> no rating at all
    none = prior({"obs_id": "G", "indicator": "cattails", "indicator_type": "VEGETATION"}, [], entries)
    assert none["flags"] == ["NO_MORPHOLOGY"] and "bearing_prior" not in none
    # unknown indicator -> NO_DERIVATION, not a safe reading
    unk = prior({"obs_id": "H", "indicator": "saguaro", "indicator_type": "VEGETATION"},
                [load_morphologies()["low_pressure_broad_contact"]], entries)
    assert unk["flags"] == ["NO_DERIVATION"]
    # region is a scope field, not a key: the same indicator in a foreign region still returns the mechanism
    assert e["bearing_prior"]["mechanism"] == [x for x in entries if x["indicator"] == "cattails"][0]["mechanism"]
    # no collapsed score anywhere in a return
    for r in (a, b, c, e, brush):
        assert not any(k in r for k in ("traversability", "score", "rating"))
    print("terrain_prior selftest ok")


def main(argv):
    if not argv:
        print(__doc__); return 0
    cmd, args = argv[0], argv[1:]
    if cmd == "selftest":
        selftest(); return 0
    if cmd == "cases":
        for name, fn in (("A boulder downstream", case_A), ("A boulder upstream", case_A_upstream),
                         ("B pine stand", case_B), ("C morphology split", case_C),
                         ("D no mechanism", case_D), ("E out of scope", case_E)):
            r = fn()
            print("== %s" % name)
            print("   flags: %s" % ", ".join(r["flags"]))
            if "bearing_prior" in r:
                print("   bearing: %s" % r["bearing_prior"]["value"])
                for x in r["bearing_prior"]["by_platform"]:
                    print("     %-30s %s" % (x["platform_id"], x["statement"]))
                print("   entanglement: %s" % r["entanglement_prior"]["value"])
                for x in r["entanglement_prior"]["by_platform"]:
                    print("     %-30s %s -> %s" % (x["platform_id"], x.get("swing_profile"), x["direction"]))
                print("   confidence: %s | scope: %s" % (r["bearing_prior"]["confidence"], r["scope"]))
                if r.get("sensor_inversion"):
                    print("   sensor inversion: %s" % r["sensor_inversion"])
                print("   falsified by: %s" % r["falsified_by"])
                print("   derived from: %s" % r["derived_from"])
            else:
                print("   no prior: %s" % r.get("note"))
            print()
        return 0
    if cmd == "entries":
        for e in load_entries():
            print("%-45s %s" % (e["indicator"], e["mechanism"]))
            print("%-45s bearing %s | entanglement %s | scope %s" % ("", e.get("bearing_kpa"), e.get("stem_density"), e.get("scope")))
        return 0
    if cmd == "prior":
        obs = json.load(open(args[0]))
        M = load_morphologies()
        ids = args[1:] or list(M)
        print(json.dumps(prior(obs, [M[i] for i in ids]), indent=1))
        return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
