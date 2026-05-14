"""
Field assembly.
N=1: temporal gradient over own senses (1D geometry in time).
N≥2: spatial gradient across nodes.
Same function, same return shape.
"""

from typing import Dict
from statistics import mean


def temporal_gradient(values: list) -> float:
    """Simple slope estimate over a window."""
    if len(values) < 2:
        return 0.0
    n = len(values)
    xs = list(range(n))
    mx, my = mean(xs), mean(values)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, values))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den if den else 0.0


def build_field(pack: Dict[str, "Node"],
                window: int = 64) -> Dict[str, dict]:
    """
    Returns per-node field state.
    At N=1: only temporal gradients (geometry-in-time).
    At N≥2: temporal + spatial-coupling info.
    """
    field_state: Dict[str, dict] = {}
    for nid, node in pack.items():
        per_sense = {}
        for sname, ch in node.senses.items():
            recent = ch.recent(window)
            per_sense[sname] = {
                "latest":    recent[-1] if recent else None,
                "gradient":  temporal_gradient(recent),
                "headroom":  ch.baseline - (recent[-1] if recent else 0),
            }
        field_state[nid] = per_sense
    return field_state
