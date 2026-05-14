"""
Decision layer. Quorum-of-one is legal at N=1.
Same function, trivial case.
"""

from typing import Dict, List, Tuple

THERMAL_SAFETY_MARGIN = 5.0   # °C headroom before load-shift


def load_shift_recommendations(
        field_state: Dict[str, dict]
        ) -> List[Tuple[str, str]]:
    """
    Returns list of (pressured_node, cool_node) pairs.
    At N=1: returns [] if alone (nowhere to shift to);
            decide.py upstream still can throttle/sleep self.
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
    What a lone (or any) node can do for itself without peers.
    Throttle, sleep, alert — always available.
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
    Quorum-of-one is legal. Same function for any N.
    Returns True if majority of present votes are True.
    """
    if not votes:
        return False
    yes = sum(1 for v in votes.values() if v)
    return yes * 2 > len(votes)
