"""
Wholeness invariant: every chief function must work at every
legal pack size, including N=1, using the same code path.
Run with:  python -m pytest tests/test_invariants.py -v
"""

import pytest
from kitchi.node import Node, ChiefCapacity
from kitchi.senses import make_default_senses
from kitchi.shard import HashRing
from kitchi.correlate import correlate_pack
from kitchi.geometry import build_field
from kitchi.decide import (
    load_shift_recommendations,
    self_regulate,
    quorum_decide,
)


# ---------- helpers ----------

def _make_node(name: str, fill: bool = True) -> Node:
    node = Node(node_id=name, senses=make_default_senses())
    if fill:
        # populate with synthetic data so correlation has signal
        for i in range(128):
            node.senses["heat"].sample(40.0 + i * 0.01)
            node.senses["power"].sample(100.0 + i * 0.5)
            node.senses["timing"].sample(50.0 + (i % 7))
    return node


# ---------- N=1 invariants ----------

class TestWholenessAtN1:
    """A lone kitchi must be whole, not waiting."""

    def setup_method(self):
        self.node = _make_node("solo")
        self.pack = {"solo": self.node}

    def test_perceive_works_alone(self):
        snapshot = self.node.read_all()
        assert set(snapshot.keys()) == {"heat", "power", "timing"}
        assert all(v is not None for v in snapshot.values())

    def test_correlate_returns_auto_correlation(self):
        couplings = correlate_pack(self.pack)
        # At N=1, keys are (node_id, sense_a, sense_b) — auto-correlation
        assert len(couplings) > 0
        for key in couplings:
            assert len(key) == 3
            assert key[0] == "solo"
            assert key[1] != key[2]   # distinct sense pair

    def test_geometry_returns_temporal_field(self):
        field_state = build_field(self.pack)
        assert "solo" in field_state
        for sense in ("heat", "power", "timing"):
            assert sense in field_state["solo"]
            assert "gradient" in field_state["solo"][sense]

    def test_self_regulate_available(self):
        field_state = build_field(self.pack)
        result = self_regulate(self.node, field_state)
        assert result["node"] == "solo"
        assert "actions" in result   # may be [], which is fine

    def test_quorum_of_one_is_legal(self):
        assert quorum_decide({"solo": True}) is True
        assert quorum_decide({"solo": False}) is False

    def test_shard_ring_with_one_node(self):
        ring = HashRing()
        ring.add_node("solo")
        # all shards resolve to solo; no shadow available
        assert ring.primary_for("shard_a") == "solo"
        assert ring.shadow_for("shard_a") is None

    def test_no_mode_switch_in_code_paths(self):
        """
        The same functions used at N=1 must be used at N≥2.
        This test checks they don't crash when called with N=1.
        If any function raises on N=1, the wholeness invariant
        is broken.
        """
        correlate_pack(self.pack)
        build_field(self.pack)
        load_shift_recommendations(build_field(self.pack))
        self_regulate(self.node, build_field(self.pack))


# ---------- N=2 invariants ----------

class TestWholenessAtN2:
    """Two-node pack: same functions, cross-correlation begins."""

    def setup_method(self):
        self.a = _make_node("a")
        self.b = _make_node("b")
        self.pack = {"a": self.a, "b": self.b}

    def test_correlate_returns_cross_correlation(self):
        couplings = correlate_pack(self.pack)
        # At N≥2, keys are (node_a, node_b, sense)
        assert len(couplings) > 0
        for key in couplings:
            assert len(key) == 3
            assert key[0] != key[1]

    def test_shadow_exists_at_n2(self):
        ring = HashRing()
        ring.add_node("a")
        ring.add_node("b")
        primary = ring.primary_for("shard_a")
        shadow = ring.shadow_for("shard_a")
        assert primary in ("a", "b")
        assert shadow in ("a", "b")
        assert primary != shadow

    def test_quorum_works(self):
        assert quorum_decide({"a": True, "b": True}) is True
        assert quorum_decide({"a": True, "b": False}) is False


# ---------- N=6 invariants ----------

class TestWholenessAtN6:
    """Six nodes: octahedral SOMS target. Same functions still."""

    def setup_method(self):
        self.pack = {f"n{i}": _make_node(f"n{i}") for i in range(6)}

    def test_correlate_scales(self):
        couplings = correlate_pack(self.pack)
        # 6 choose 2 = 15 pairs, × 3 senses = 45 correlations
        assert len(couplings) == 15 * 3

    def test_ring_distributes(self):
        ring = HashRing()
        for nid in self.pack:
            ring.add_node(nid)
        # spot-check: shadow always differs from primary
        for shard in (f"shard_{i}" for i in range(20)):
            assert ring.primary_for(shard) != ring.shadow_for(shard)


# ---------- continuity across sizes ----------

class TestNoDegenerateModes:
    """
    The same function, called at N=1, 2, 6, must not raise
    and must return the documented shape.
    """

    @pytest.mark.parametrize("n", [1, 2, 3, 6])
    def test_correlate_no_crash(self, n):
        pack = {f"n{i}": _make_node(f"n{i}") for i in range(n)}
        result = correlate_pack(pack)
        assert isinstance(result, dict)

    @pytest.mark.parametrize("n", [1, 2, 3, 6])
    def test_build_field_no_crash(self, n):
        pack = {f"n{i}": _make_node(f"n{i}") for i in range(n)}
        result = build_field(pack)
        assert len(result) == n
