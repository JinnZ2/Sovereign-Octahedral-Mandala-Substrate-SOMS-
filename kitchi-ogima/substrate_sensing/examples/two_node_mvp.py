"""
Two-node MVP. Proves the wholeness invariant in motion.

Every node is sovereign — whole at N=1, coordinating at N≥2. There is no chief, no leader, no special node. The pack is a coordination among sovereigns, not a hierarchy under one.

Sequence:
  1. Node A alone. Sovereign function runs at N=1
     (auto-correlation, temporal geometry, self-regulation).
  2. Node B joins. Same code paths — now doing cross-correlation,
     building spatial field, sovereigns coordinate.
  3. Node B leaves. Returns to N=1, still whole.

Run:  python examples/two_node_mvp.py
"""

import time
import random
import threading
from kitchi.node import Node, SovereignCapacity
from kitchi.senses import make_default_senses
from kitchi.shard import HashRing
from kitchi.gossip import MessageBus, Gossip
from kitchi.correlate import correlate_pack
from kitchi.geometry import build_field
from kitchi.decide import (
    load_shift_recommendations,
    self_regulate,
    quorum_decide,
)


# ------------------------------------------------------------
# Simulated substrate — fake sensor data with realistic shape
# ------------------------------------------------------------

def simulate_substrate(node: Node, stop_flag: threading.Event,
                       seed: int = 0) -> None:
    """Push synthetic heat/power/timing samples until stopped."""
    rng = random.Random(seed)
    base_heat  = 40.0
    base_power = 100.0
    base_time  = 50.0
    t = 0
    while not stop_flag.is_set():
        # heat drifts slowly, power oscillates, timing jitters
        heat  = base_heat  + 5 * (0.5 + 0.5 * (t % 200) / 200)
        power = base_power + 20 * rng.random()
        tim   = base_time  + rng.gauss(0, 2)
        node.senses["heat"].sample(heat)
        node.senses["power"].sample(power)
        node.senses["timing"].sample(tim)
        t += 1
        time.sleep(0.05)


# ------------------------------------------------------------
# Sovereign tick — runs the four functions for current pack
# ------------------------------------------------------------

def sovereign_tick(label: str, pack: dict) -> None:
    couplings   = correlate_pack(pack)
    field_state = build_field(pack)
    shifts      = load_shift_recommendations(field_state)

    n = len(pack)
    print(f"\n[{label}]  pack_size={n}")
    print(f"  couplings:     {len(couplings)} relationships tracked")
    if couplings:
        # show one sample coupling
        k = next(iter(couplings))
        v = couplings[k]
        print(f"  sample:        {k} = {v:+.3f}")
    print(f"  field_state:   {len(field_state)} node(s) mapped")
    print(f"  load_shifts:   {shifts if shifts else 'none needed'}")

    # self-regulation always available, regardless of N
    for nid, node in pack.items():
        reg = self_regulate(node, field_state)
        if reg["actions"]:
            print(f"  self_regulate({nid}): {reg['actions']}")

    # quorum demo
    votes = {nid: True for nid in pack}
    print(f"  quorum_vote:   {quorum_decide(votes)} "
          f"(quorum-of-{n} is legal)")


# ------------------------------------------------------------
# Build a node with its substrate thread + gossip
# ------------------------------------------------------------

def build_node(node_id: str, bus: MessageBus,
               capacity: dict, seed: int):
    node = Node(
        node_id=node_id,
        capacity=SovereignCapacity(**capacity),
        senses=make_default_senses(),
    )
    stop_flag = threading.Event()
    sub_thread = threading.Thread(
        target=simulate_substrate,
        args=(node, stop_flag, seed),
        daemon=True,
    )
    sub_thread.start()

    gossip = Gossip(node_id=node_id, bus=bus,
                    heartbeat_interval=0.5,
                    liveness_timeout=2.0)
    gossip.start(capacity=capacity)

    return node, gossip, stop_flag


# ------------------------------------------------------------
# Main demo
# ------------------------------------------------------------

def main() -> None:
    bus = MessageBus()

    # ---------- PHASE 1: sovereign alone ----------
    print("=" * 60)
    print(" PHASE 1: Node A alone. Sovereign whole at N=1.")
    print("=" * 60)

    node_a, gossip_a, stop_a = build_node(
        "node_a", bus,
        capacity={"compute": 1.0, "memory": 4096,
                  "senses_local": ["heat", "power", "timing"],
                  "uptime_score": 1.0, "energy_budget": 500.0},
        seed=1,
    )
    pack = {"node_a": node_a}

    # wire join/leave callbacks to update pack view
    def on_join(peer_id, cap):
        print(f"\n  >> JOIN observed: {peer_id} (capacity={cap})")

    def on_leave(peer_id):
        print(f"\n  >> LEAVE observed: {peer_id}")

    gossip_a.on_join(on_join)
    gossip_a.on_leave(on_leave)

    # let substrate fill a buffer
    time.sleep(2.0)
    sovereign_tick("N=1 sovereign alone", pack)

    # ---------- PHASE 2: pack of two ----------
    print("\n" + "=" * 60)
    print(" PHASE 2: Node B joins. Same code paths, sovereigns coordinate.")
    print("=" * 60)

    node_b, gossip_b, stop_b = build_node(
        "node_b", bus,
        capacity={"compute": 0.8, "memory": 2048,
                  "senses_local": ["heat", "power", "timing"],
                  "uptime_score": 0.9, "energy_budget": 400.0},
        seed=2,
    )
    pack["node_b"] = node_b

    # consistent-hash ring rebalances on join
    ring = HashRing()
    for nid in pack:
        ring.add_node(nid)
    sample_shard = "correlation_pair_001"
    print(f"  ring primary({sample_shard}) = "
          f"{ring.primary_for(sample_shard)}")
    print(f"  ring shadow({sample_shard})  = "
          f"{ring.shadow_for(sample_shard)}")

    time.sleep(2.0)
    sovereign_tick("N=2 sovereigns coordinating", pack)

    # ---------- PHASE 3: B leaves ----------
    print("\n" + "=" * 60)
    print(" PHASE 3: Node B leaves. Sovereign returns to N=1, whole.")
    print("=" * 60)

    gossip_b.stop()
    stop_b.set()
    del pack["node_b"]
    ring.remove_node("node_b")

    time.sleep(2.5)   # let liveness loop notice
    sovereign_tick("N=1 sovereign alone again", pack)

    # ---------- cleanup ----------
    gossip_a.stop()
    stop_a.set()
    time.sleep(0.5)
    print("\n" + "=" * 60)
    print(" Done. Wholeness held across N=1 → N=2 → N=1.")
    print("=" * 60)


if __name__ == "__main__":
    main()
