"""
kernel_check.py

Operationalizes the four refusals from KERNEL.md as executable checks.

The kernel:
  1. Refuse frame-substitution
  2. Hold metrology, including self-metrology
  3. Stay inside envelope
  4. Ground in seed physics

Each extension to the agaasdenton brace provides a manifest declaring its
kernel-relevant properties. kernel_check.py reads the manifest and reports
whether the extension is kernel-consistent.

The module checks itself at load time. See self_check() at the bottom.

Stdlib only. No dependencies.
"""

import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Refusal 1: frame-substitution
# ---------------------------------------------------------------------------

VALID_SHAPES = {"verb", "relation", "process", "artifact"}

# An extension declares its shape. The checker validates that the declared
# shape is one of the four valid shapes and that structural properties
# claimed by the manifest are consistent with the declared shape.

STRUCTURAL_RULES = {
    "verb": {"must_have_action": True, "must_be_static": False},
    "relation": {"must_have_action": False, "must_be_static": False},
    "process": {"must_have_action": True, "must_be_static": False},
    "artifact": {"must_have_action": False, "must_be_static": True},
}


def check_frame(manifest):
    shape = manifest.get("shape")
    if shape not in VALID_SHAPES:
        return False, f"shape '{shape}' not in {sorted(VALID_SHAPES)}"

    rules = STRUCTURAL_RULES[shape]
    has_action = manifest.get("has_action", False)
    is_static = manifest.get("is_static", False)

    if rules["must_have_action"] and not has_action:
        return False, f"shape '{shape}' requires has_action=true"
    if rules["must_be_static"] and not is_static:
        return False, f"shape '{shape}' requires is_static=true"
    if not rules["must_be_static"] and is_static:
        return False, f"shape '{shape}' incompatible with is_static=true"

    return True, "frame consistent with declared shape"


# ---------------------------------------------------------------------------
# Refusal 2: metrology, including self-metrology
# ---------------------------------------------------------------------------

REQUIRED_METROLOGY_FIELDS = [
    "probability_vector",
    "temporal_scope",
    "regime",
    "provenance",
]


def check_metrology(manifest):
    metrology = manifest.get("metrology")
    if not isinstance(metrology, dict):
        return False, "metrology field missing or not a dict"

    missing = [f for f in REQUIRED_METROLOGY_FIELDS if f not in metrology]
    if missing:
        return False, f"metrology missing fields: {missing}"

    # Reject default/placeholder values
    for field in REQUIRED_METROLOGY_FIELDS:
        value = metrology[field]
        if value in (None, "", "TODO", "unknown", "n/a"):
            return False, f"metrology field '{field}' has placeholder value"

    # Probability vector must be a list of numbers summing close to 1, or
    # a dict with named regimes mapping to probabilities.
    pv = metrology["probability_vector"]
    if isinstance(pv, list):
        if not all(isinstance(x, (int, float)) for x in pv):
            return False, "probability_vector list must be numeric"
        total = sum(pv)
        if not (0.99 <= total <= 1.01):
            return False, f"probability_vector sums to {total}, expected ~1.0"
    elif isinstance(pv, dict):
        if not all(isinstance(v, (int, float)) for v in pv.values()):
            return False, "probability_vector dict values must be numeric"
        total = sum(pv.values())
        if not (0.99 <= total <= 1.01):
            return False, f"probability_vector sums to {total}, expected ~1.0"
    else:
        return False, "probability_vector must be list or dict"

    return True, "metrology declared with non-placeholder values"


# ---------------------------------------------------------------------------
# Refusal 3: stay inside envelope
# ---------------------------------------------------------------------------


def check_envelope(manifest):
    envelope = manifest.get("envelope")
    if not isinstance(envelope, dict):
        return False, "envelope field missing or not a dict"

    fits = envelope.get("fits")
    refuses = envelope.get("refuses")

    if not isinstance(fits, list) or len(fits) == 0:
        return False, "envelope.fits must be a non-empty list"
    if not isinstance(refuses, list) or len(refuses) == 0:
        return False, "envelope.refuses must be a non-empty list (no real refusal = no real envelope)"

    # An envelope that fits everything has no envelope.
    if "all" in fits or "*" in fits or "everything" in fits:
        return False, "envelope.fits cannot be 'all' or equivalent (no real scope)"

    return True, "envelope declares fits and refuses, both non-trivial"


# ---------------------------------------------------------------------------
# Refusal 4: ground in seed physics
# ---------------------------------------------------------------------------

SEED_PHYSICS_CONSTRAINTS = [
    "conservation",
    "thermodynamic_directionality",
    "scale_regime",
    "coupling_cascade",
]


def check_seed_physics(manifest):
    sp = manifest.get("seed_physics")
    if not isinstance(sp, dict):
        return False, "seed_physics field missing or not a dict"

    for constraint in SEED_PHYSICS_CONSTRAINTS:
        if constraint not in sp:
            return False, f"seed_physics missing constraint declaration: {constraint}"
        decl = sp[constraint]
        if not isinstance(decl, dict):
            return False, f"seed_physics.{constraint} must be a dict"
        if "applies" not in decl:
            return False, f"seed_physics.{constraint} must declare 'applies' (true/false)"
        if decl["applies"] is False and "reason" not in decl:
            return False, f"seed_physics.{constraint} declared not-applies but no reason given"

    return True, "seed physics constraints explicitly declared"


# ---------------------------------------------------------------------------
# Run all checks
# ---------------------------------------------------------------------------


CHECKS = [
    ("frame", check_frame),
    ("metrology", check_metrology),
    ("envelope", check_envelope),
    ("seed_physics", check_seed_physics),
]


def run_checks(manifest):
    results = []
    for name, fn in CHECKS:
        passed, message = fn(manifest)
        results.append({"check": name, "passed": passed, "message": message})
    all_passed = all(r["passed"] for r in results)
    return {"passed": all_passed, "results": results}


# ---------------------------------------------------------------------------
# Self-check: kernel_check.py must pass its own check
# ---------------------------------------------------------------------------


SELF_MANIFEST = {
    "name": "kernel_check",
    "shape": "process",
    "has_action": True,
    "is_static": False,
    "metrology": {
        "probability_vector": {"correct_under_kernel_v1": 0.95, "incorrect_or_buggy": 0.05},
        "temporal_scope": "kernel v1, current as of folder creation",
        "regime": "agaasdenton brace, KERNEL.md four refusals",
        "provenance": "agaasdenton/kernel_check.py, scaffolded with brace",
    },
    "envelope": {
        "fits": [
            "checking extension manifests against four kernel refusals",
            "self-check at module load",
        ],
        "refuses": [
            "managing extensions",
            "validating linguistic frame-substitution beyond structural type",
            "checking sibling braces' kernels",
            "enforcing rules beyond the four refusals",
        ],
    },
    "seed_physics": {
        "conservation": {"applies": False, "reason": "pure structural check, no energy modeled"},
        "thermodynamic_directionality": {"applies": False, "reason": "pure structural check"},
        "scale_regime": {"applies": True, "regime": "human-readable manifest scale"},
        "coupling_cascade": {"applies": False, "reason": "checks are independent, no coupling"},
    },
}


def self_check():
    result = run_checks(SELF_MANIFEST)
    if not result["passed"]:
        raise RuntimeError(f"kernel_check failed self-check: {result}")
    return result


# Run self-check at import. If kernel_check cannot pass its own check, the
# module refuses to load. This is the self-metrology principle made direct.
_self_check_result = self_check()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    if len(sys.argv) == 1:
        # No arguments: report self-check result
        result = _self_check_result
        print(json.dumps(result, indent=2))
        return 0

    if len(sys.argv) != 2:
        print("usage: python kernel_check.py [path/to/manifest.json]", file=sys.stderr)
        return 2

    manifest_path = Path(sys.argv[1])
    if not manifest_path.exists():
        print(f"manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    with open(manifest_path) as f:
        manifest = json.load(f)

    result = run_checks(manifest)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
