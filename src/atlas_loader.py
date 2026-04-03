"""Atlas loader — reads mounted fieldlink data for the constraint agent."""

import json
from pathlib import Path
from typing import Dict, List

_ATLAS_ROOT = Path(__file__).resolve().parent.parent / "atlas" / "remote"

# Polyhedral duality pairs (vertices <-> faces) give +0.15 resonance bonus
DUAL_PAIRS = {
    "SHAPE.CUBE": "SHAPE.OCTA",
    "SHAPE.OCTA": "SHAPE.CUBE",
    "SHAPE.DODECA": "SHAPE.ICOSA",
    "SHAPE.ICOSA": "SHAPE.DODECA",
}

# Bridge connections give +0.08 resonance bonus
BRIDGE_PAIRS = {
    ("SHAPE.TETRA", "SHAPE.CUBE"),
    ("SHAPE.CUBE", "SHAPE.TETRA"),
    ("SHAPE.TETRA", "SHAPE.DODECA"),
    ("SHAPE.DODECA", "SHAPE.TETRA"),
}

# Map seed IDs to synergy graph aliases
SYNERGY_ALIASES = {
    "SHAPE.OCTA": "OCTA_STATE",
    "SHAPE.TETRA": "SILICON_LAT",
    "SHAPE.CUBE": "CRYSTAL_LATTICE",
    "SHAPE.DODECA": "ROSETTA_SHAPE",
    "SHAPE.ICOSA": "BIOGRID2",
}


def _load_json(path: Path):
    """Load a JSON file, returning empty dict/list on failure."""
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def load_seed_catalog() -> Dict[str, dict]:
    """Load seed catalog keyed by shape_id (e.g. SHAPE.OCTA)."""
    data = _load_json(_ATLAS_ROOT / "rosetta" / "seed_catalog.json")
    return {s["shape_id"]: s for s in data.get("seeds", [])}


def load_bridge_map() -> Dict[str, dict]:
    """Load bridges keyed by shape ID."""
    data = _load_json(_ATLAS_ROOT / "rosetta" / "bridges.json")
    return {entry["shape"]: entry for entry in data.get("map", [])}


def load_synergy_graph() -> Dict[str, List[tuple]]:
    """Load Living-Intelligence synergies as adjacency list with weights."""
    data = _load_json(_ATLAS_ROOT / "living-intelligence" / "synergies.json")
    if not data:
        return {}
    graph: Dict[str, List[tuple]] = {}
    for edge in data.get("edges", []):
        src, tgt = edge["source"], edge["target"]
        weight = edge.get("weight", 0.5)
        graph.setdefault(src, []).append((tgt, weight))
        graph.setdefault(tgt, []).append((src, weight))
    return graph


def load_expander_rules() -> List[dict]:
    """Load Living-Intelligence inference rules."""
    data = _load_json(_ATLAS_ROOT / "living-intelligence" / "expander_rules.json")
    return data if isinstance(data, list) else []


def jaccard(a: list, b: list) -> float:
    """Jaccard similarity between two lists."""
    sa, sb = set(a), set(b)
    union = sa | sb
    if not union:
        return 0.0
    return len(sa & sb) / len(union)
