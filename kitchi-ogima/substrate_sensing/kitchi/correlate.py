"""
Correlation works at every N.
N=1: auto-correlate across sense channels of the lone node.
N≥2: cross-correlate same sense across node pairs.
Same function, smaller input set at N=1.
"""

from typing import Dict, List, Tuple
from statistics import mean, pstdev


def pearson(xs: List[float], ys: List[float]) -> float:
    """Pearson correlation, returns 0.0 on degenerate input."""
    if len(xs) < 2 or len(xs) != len(ys):
        return 0.0
    mx, my = mean(xs), mean(ys)
    sx, sy = pstdev(xs), pstdev(ys)
    if sx == 0 or sy == 0:
        return 0.0
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / len(xs)
    return cov / (sx * sy)


def correlate_pack(pack: Dict[str, "Node"],
                   window: int = 64) -> Dict[Tuple, float]:
    """
    Returns coupling map.
    Keys:
      N=1: (node_id, sense_a, sense_b)   — auto-correlation
      N≥2: (node_a, node_b, sense)        — cross-correlation
    Same return type, same semantics, no mode switch.
    """
    couplings: Dict[Tuple, float] = {}
    node_ids = sorted(pack.keys())

    if len(node_ids) == 1:
        # Auto-correlation across own sense channels
        nid = node_ids[0]
        node = pack[nid]
        sense_names = sorted(node.senses.keys())
        for i, sa in enumerate(sense_names):
            for sb in sense_names[i + 1:]:
                xs = node.senses[sa].recent(window)
                ys = node.senses[sb].recent(window)
                # align lengths
                n = min(len(xs), len(ys))
                couplings[(nid, sa, sb)] = pearson(xs[-n:], ys[-n:])
        return couplings

    # Cross-correlation across node pairs
    for i, a in enumerate(node_ids):
        for b in node_ids[i + 1:]:
            shared_senses = set(pack[a].senses) & set(pack[b].senses)
            for sense in sorted(shared_senses):
                xs = pack[a].senses[sense].recent(window)
                ys = pack[b].senses[sense].recent(window)
                n = min(len(xs), len(ys))
                couplings[(a, b, sense)] = pearson(xs[-n:], ys[-n:])
    return couplings
