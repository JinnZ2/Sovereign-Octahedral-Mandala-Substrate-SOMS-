"""
playground.py

Demonstrates the four kernel refusals via example manifests.

Reading this file teaches the kernel faster than reading kernel_check.py
and manifest.example.json separately. Each example is a manifest plus a
short description; running this script prints what kernel_check reports
for each. Passing examples show kernel-consistency; failing examples show
what each refusal catches and the message it produces.

Run: python agaasdenton/playground.py

Stdlib only.
"""

import copy
import sys
from pathlib import Path

# Allow running from anywhere in the repo
sys.path.insert(0, str(Path(__file__).parent))

from kernel_check import run_checks


BASE_MANIFEST = {
    "name": "playground_base",
    "shape": "process",
    "has_action": True,
    "is_static": False,
    "metrology": {
        "probability_vector": {"behaves_as_declared": 0.9, "edge_case_exists": 0.1},
        "temporal_scope": "kernel v1, current",
        "regime": "agaasdenton brace, playground example",
        "provenance": "playground.py example manifest",
    },
    "envelope": {
        "fits": ["demonstrating kernel-consistency"],
        "refuses": ["being used as actual brace infrastructure", "claiming universality"],
    },
    "seed_physics": {
        "conservation": {"applies": False, "reason": "structural example, no energy"},
        "thermodynamic_directionality": {"applies": False, "reason": "structural example"},
        "scale_regime": {"applies": True, "regime": "manifest scale"},
        "coupling_cascade": {"applies": False, "reason": "standalone example"},
    },
}


def base(**overrides):
    m = copy.deepcopy(BASE_MANIFEST)
    for k, v in overrides.items():
        m[k] = v
    return m


# Refusal 1: frame — verb requires action
_fail_verb = base(shape="verb", has_action=False)

# Refusal 1: frame — artifact must be static
_fail_artifact = base(shape="artifact", has_action=False, is_static=False)

# Refusal 2: metrology — placeholder value
_meta_placeholder = copy.deepcopy(BASE_MANIFEST["metrology"])
_meta_placeholder["provenance"] = "TODO"
_fail_metro_placeholder = base(metrology=_meta_placeholder)

# Refusal 2: metrology — probability_vector does not sum to ~1
_meta_prob = copy.deepcopy(BASE_MANIFEST["metrology"])
_meta_prob["probability_vector"] = {"a": 0.4, "b": 0.3}
_fail_metro_prob = base(metrology=_meta_prob)

# Refusal 3: envelope — fits='all' (no real scope)
_fail_envelope_universal = base(envelope={"fits": ["all"], "refuses": ["nothing-in-particular"]})

# Refusal 3: envelope — refuses is empty (no real refusal)
_fail_envelope_no_refusal = base(envelope={"fits": ["a real scope"], "refuses": []})

# Refusal 4: seed_physics — missing a required constraint
_sp_missing = copy.deepcopy(BASE_MANIFEST["seed_physics"])
del _sp_missing["coupling_cascade"]
_fail_seed_missing = base(seed_physics=_sp_missing)


EXAMPLES = [
    ("passing_extension",
     "A complete, kernel-consistent extension manifest.",
     base()),

    ("fail_frame_verb_without_action",
     "Refusal 1 (frame): shape='verb' but has_action=false.",
     _fail_verb),

    ("fail_frame_artifact_not_static",
     "Refusal 1 (frame): shape='artifact' but is_static=false.",
     _fail_artifact),

    ("fail_metrology_placeholder",
     "Refusal 2 (metrology): provenance='TODO' — placeholders are refused.",
     _fail_metro_placeholder),

    ("fail_metrology_probability_sum",
     "Refusal 2 (metrology): probability_vector sums to 0.7, not ~1.0.",
     _fail_metro_prob),

    ("fail_envelope_universal_fit",
     "Refusal 3 (envelope): fits=['all'] — no real scope is no envelope.",
     _fail_envelope_universal),

    ("fail_envelope_no_refusal",
     "Refusal 3 (envelope): refuses=[] — no refusal is no envelope.",
     _fail_envelope_no_refusal),

    ("fail_seed_physics_missing_constraint",
     "Refusal 4 (seed_physics): coupling_cascade declaration absent.",
     _fail_seed_missing),
]


def main():
    for name, description, manifest in EXAMPLES:
        result = run_checks(manifest)
        verdict = "PASS" if result["passed"] else "FAIL"
        print(f"[{verdict}] {name}")
        print(f"        {description}")
        for r in result["results"]:
            mark = "ok  " if r["passed"] else "FAIL"
            print(f"          {mark} {r['check']}: {r['message']}")
        print()


if __name__ == "__main__":
    main()
