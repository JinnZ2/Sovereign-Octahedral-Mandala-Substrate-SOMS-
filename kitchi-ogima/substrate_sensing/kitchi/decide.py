"""
Decision layer.

Naming note: 'quorum' here means **agreement among sovereigns**,
not a vote under a chief. Quorum-of-one is fully legal — a lone
sovereign decides for itself. This is not a degenerate case;
it is the base case.
"""

from typing import Dict, List, Tuple

THERMAL_SAFETY_MARGIN = 5.0   # °C headroom before load-shift


def load_shift_recommendations(
        field_state: Dict[str, dict]
        ) -> List[Tuple[str, str]]:
    """
    Suggest (pressured_node, cool_node) pairs.
    At N=1: returns []. The lone sovereign self-regulates instead.
    """
    pressured, cool = [], []
    for nid, senses in field_state.items():
        heat = senses.get("heat", {})
        headroom = heat.get("headroom", float("inf"))
        if headroom is None:
            continue
        if headroom < THERMAL_SAFETY_MARGIN:
            pressured.append(nid)
        elif headroom > THERMAL_SAFETY_MARGIN * 2:
            cool.append(nid)
    return [(p, c) for p in pressured for c in cool[:1]]


def self_regulate(node: "Node",
                  field_state: Dict[str, dict]) -> dict:
    """
    A sovereign's authority over its own resources.
    Always available, regardless of pack size.
    Never requires permission from another node.
    """
    own = field_state.get(node.node_id, {})
    heat = own.get("heat", {}).get("headroom", float("inf"))
    actions = []
    if heat < THERMAL_SAFETY_MARGIN:
        actions.append("throttle")
    if heat < 0:
        actions.append("emergency_sleep")
    return {"node": node.node_id, "actions": actions}


def quorum_decide(votes: Dict[str, bool]) -> bool:
    """
    Agreement among sovereigns. Not a vote under a chief.
    Quorum-of-one is legal: a lone sovereign decides for itself.
    Same function for every N.
    """
    if not votes:
        return False
    yes = sum(1 for v in votes.values() if v)
    return yes * 2 > len(votes)
