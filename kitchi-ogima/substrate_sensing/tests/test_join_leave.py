"""
Gossip-layer tests. Prove join/leave wholeness.
Run:  python -m pytest tests/test_join_leave.py -v
"""

import time
import pytest
from kitchi.gossip import MessageBus, Gossip


class TestGossipBasics:

    def test_lone_node_runs_without_peers(self):
        bus = MessageBus()
        g = Gossip("solo", bus, heartbeat_interval=0.1,
                   liveness_timeout=0.5)
        g.start(capacity={"compute": 1.0})
        time.sleep(0.3)
        assert g.alive_peers() == set()    # no peers, still healthy
        g.stop()

    def test_two_nodes_discover_each_other(self):
        bus = MessageBus()
        a = Gossip("a", bus, heartbeat_interval=0.1,
                   liveness_timeout=0.5)
        b = Gossip("b", bus, heartbeat_interval=0.1,
                   liveness_timeout=0.5)
        a.start(capacity={"compute": 1.0})
        b.start(capacity={"compute": 0.5})
        time.sleep(0.4)
        assert "b" in a.alive_peers()
        assert "a" in b.alive_peers()
        a.stop()
        b.stop()

    def test_leave_detected_by_explicit_message(self):
        bus = MessageBus()
        a = Gossip("a", bus, heartbeat_interval=0.1,
                   liveness_timeout=2.0)
        b = Gossip("b", bus, heartbeat_interval=0.1,
                   liveness_timeout=2.0)
        leave_events = []
        a.on_leave(lambda nid: leave_events.append(nid))
        a.start(capacity={})
        b.start(capacity={})
        time.sleep(0.3)
        b.stop()
        time.sleep(0.3)
        assert "b" in leave_events
        a.stop()

    def test_leave_detected_by_heartbeat_timeout(self):
        """If a node dies silently, liveness loop must notice."""
        bus = MessageBus()
        a = Gossip("a", bus, heartbeat_interval=0.1,
                   liveness_timeout=0.4)
        b = Gossip("b", bus, heartbeat_interval=0.1,
                   liveness_timeout=0.4)
        leave_events = []
        a.on_leave(lambda nid: leave_events.append(nid))
        a.start(capacity={})
        b.start(capacity={})
        time.sleep(0.3)
        # simulate silent death: stop b's threads without sending leave
        b._running = False
        bus.unsubscribe("b")
        time.sleep(0.8)
        assert "b" in leave_events
        a.stop()

    def test_capacity_update_fires_callback(self):
        bus = MessageBus()
        a = Gossip("a", bus, heartbeat_interval=0.1,
                   liveness_timeout=1.0)
        b = Gossip("b", bus, heartbeat_interval=0.1,
                   liveness_timeout=1.0)
        events = []
        a.on_capacity_change(lambda nid, cap: events.append((nid, cap)))
        a.start(capacity={"compute": 1.0})
        b.start(capacity={"compute": 0.5})
        time.sleep(0.3)
        b.announce_capacity({"compute": 0.2, "reason": "battery_low"})
        time.sleep(0.3)
        assert any(nid == "b" and cap.get("compute") == 0.2
                   for nid, cap in events)
        a.stop()
        b.stop()


class TestGossipWholeness:
    """Gossip itself must be whole at N=1."""

    def test_n1_callbacks_fire_on_first_peer(self):
        bus = MessageBus()
        a = Gossip("a", bus, heartbeat_interval=0.1,
                   liveness_timeout=1.0)
        joins = []
        a.on_join(lambda nid, cap: joins.append(nid))
        a.start(capacity={})
        time.sleep(0.2)
        # still alone — no joins yet, but a is fully running
        assert joins == []
        # peer arrives
        b = Gossip("b", bus, heartbeat_interval=0.1,
                   liveness_timeout=1.0)
        b.start(capacity={})
        time.sleep(0.3)
        assert "b" in joins
        a.stop()
        b.stop()
