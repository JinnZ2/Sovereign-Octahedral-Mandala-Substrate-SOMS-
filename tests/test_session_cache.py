"""Tests for octahedral_session_cache.py — constraint-coherent caching."""

import json
import time
import pytest
from pathlib import Path

from src.octahedral_session_cache import (
    OctState, CacheEntry, InvalidationGraph, SessionCache,
)


# ============================================================================
# OctState
# ============================================================================

class TestOctState:
    def test_key_deterministic(self):
        s1 = OctState(axes=(1, 0, 0, 0, 0, -1), source_repo="test")
        s2 = OctState(axes=(1, 0, 0, 0, 0, -1), source_repo="test")
        assert s1.key() == s2.key()

    def test_key_differs_by_repo(self):
        s1 = OctState(axes=(1, 0, 0, 0, 0, -1), source_repo="a")
        s2 = OctState(axes=(1, 0, 0, 0, 0, -1), source_repo="b")
        assert s1.key() != s2.key()

    def test_key_differs_by_axes(self):
        s1 = OctState(axes=(1, 0, 0, 0, 0, -1))
        s2 = OctState(axes=(0, 1, 0, 0, 0, -1))
        assert s1.key() != s2.key()

    def test_distance_zero(self):
        s = OctState(axes=(1, 0, 0.5, -0.5, 0.3, -1))
        assert s.distance(s) == 0.0

    def test_distance_linf(self):
        s1 = OctState(axes=(1.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        s2 = OctState(axes=(1.0, 0.0, 0.0, 0.0, 0.0, 0.5))
        assert s1.distance(s2) == pytest.approx(0.5)

    def test_roundtrip_dict(self):
        s = OctState(axes=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6), source_repo="r")
        d = s.to_dict()
        s2 = OctState.from_dict(d)
        assert s2.axes == s.axes
        assert s2.source_repo == s.source_repo
        assert s2.timestamp == s.timestamp

    def test_key_is_16_hex(self):
        s = OctState(axes=(0, 0, 0, 0, 0, 0))
        key = s.key()
        assert len(key) == 16
        int(key, 16)  # should not raise


# ============================================================================
# CacheEntry
# ============================================================================

class TestCacheEntry:
    def test_not_expired(self):
        e = CacheEntry(
            state_snapshot=OctState(axes=(0,) * 6),
            payload="test",
            ttl_seconds=3600,
        )
        assert not e.expired

    def test_expired(self):
        e = CacheEntry(
            state_snapshot=OctState(axes=(0,) * 6),
            payload="test",
            created=time.time() - 7200,
            ttl_seconds=3600,
        )
        assert e.expired

    def test_touch(self):
        e = CacheEntry(
            state_snapshot=OctState(axes=(0,) * 6),
            payload="test",
        )
        old_time = e.last_accessed
        old_count = e.access_count
        time.sleep(0.01)
        e.touch()
        assert e.last_accessed >= old_time
        assert e.access_count == old_count + 1


# ============================================================================
# InvalidationGraph
# ============================================================================

class TestInvalidationGraph:
    @pytest.fixture
    def graph(self):
        return InvalidationGraph()

    def test_six_vertices(self, graph):
        assert len(graph.adjacency) == 6

    def test_all_connected(self, graph):
        """In the octahedral graph, every vertex should be reachable from any other."""
        for start in range(6):
            affected = graph.affected_axes(start)
            assert len(affected) == 6, f"From axis {start}, only reached {affected}"

    def test_affected_includes_self(self, graph):
        for ax in range(6):
            assert ax in graph.affected_axes(ax)

    def test_12_edges(self, graph):
        # Count undirected edges
        edge_count = sum(len(v) for v in graph.adjacency.values()) // 2
        assert edge_count == 12

    def test_no_duplicate_neighbors(self, graph):
        for ax, neighbors in graph.adjacency.items():
            assert len(neighbors) == len(set(neighbors))


# ============================================================================
# SessionCache — core operations
# ============================================================================

class TestSessionCacheCore:
    @pytest.fixture
    def cache(self):
        return SessionCache(max_entries=10, tolerance=0.05)

    @pytest.fixture
    def state(self):
        return OctState(axes=(1.0, -0.3, 0.7, -0.7, 0.3, -1.0), source_repo="test")

    def test_put_returns_key(self, cache, state):
        key = cache.put(state, payload={"result": 42})
        assert isinstance(key, str)
        assert len(key) == 16

    def test_get_hit(self, cache, state):
        key = cache.put(state, payload="data")
        result = cache.get(key)
        assert result == "data"
        assert cache.stats["hits"] == 1

    def test_get_miss(self, cache):
        result = cache.get("nonexistent_key")
        assert result is None
        assert cache.stats["misses"] == 1

    def test_get_validates_live_state(self, cache, state):
        key = cache.put(state, payload="data")
        # Live state within tolerance
        live_close = OctState(axes=(1.01, -0.31, 0.69, -0.71, 0.31, -0.99))
        assert cache.get(key, live_state=live_close) == "data"
        # Live state beyond tolerance
        live_far = OctState(axes=(2.0, -0.3, 0.7, -0.7, 0.3, -1.0))
        assert cache.get(key, live_state=live_far) is None

    def test_ttl_expiry(self, cache, state):
        key = cache.put(state, payload="data", ttl=0.01)
        time.sleep(0.02)
        assert cache.get(key) is None

    def test_lru_eviction(self):
        cache = SessionCache(max_entries=3, tolerance=0.05)
        keys = []
        for i in range(5):
            s = OctState(axes=(float(i), 0, 0, 0, 0, 0))
            keys.append(cache.put(s, payload=f"v{i}"))
        # First two should be evicted
        assert cache.get(keys[0]) is None
        assert cache.get(keys[1]) is None
        # Last three should remain
        assert cache.get(keys[2]) == "v2"
        assert len(cache.store) == 3

    def test_access_count_increments(self, cache, state):
        key = cache.put(state, payload="data")
        cache.get(key)
        cache.get(key)
        cache.get(key)
        assert cache.store[key].access_count == 3


# ============================================================================
# SessionCache — invalidation
# ============================================================================

class TestSessionCacheInvalidation:
    @pytest.fixture
    def cache(self):
        return SessionCache(max_entries=100, tolerance=0.05)

    def test_invalidate_axis_removes_drifted(self, cache):
        state = OctState(axes=(1.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        key = cache.put(state, payload="data")
        # Axis 0 drifts way beyond tolerance
        drifted = OctState(axes=(2.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        removed = cache.invalidate_axis(0, drifted)
        assert removed >= 1
        assert cache.get(key) is None

    def test_invalidate_axis_preserves_valid(self, cache):
        state = OctState(axes=(1.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        key = cache.put(state, payload="data")
        # Axis 0 drifts only slightly
        close = OctState(axes=(1.01, 0.0, 0.0, 0.0, 0.0, 0.0))
        removed = cache.invalidate_axis(0, close)
        assert removed == 0
        assert cache.get(key) == "data"

    def test_invalidate_repo(self, cache):
        s1 = OctState(axes=(0,) * 6, source_repo="repo_a")
        s2 = OctState(axes=(1,) * 6, source_repo="repo_b")
        k1 = cache.put(s1, payload="a")
        k2 = cache.put(s2, payload="b")
        removed = cache.invalidate_repo("repo_a")
        assert removed == 1
        assert cache.get(k1) is None
        assert cache.get(k2) == "b"


# ============================================================================
# SessionCache — persist / restore
# ============================================================================

class TestSessionCachePersist:
    @pytest.fixture
    def cache(self, tmp_path):
        return SessionCache(max_entries=100, tolerance=0.05,
                            persist_dir=str(tmp_path / "cache"))

    def test_persist_creates_file(self, cache):
        state = OctState(axes=(0.5,) * 6, source_repo="test")
        cache.put(state, payload={"x": 1})
        path = cache.persist("sess1")
        assert Path(path).exists()

    def test_persist_valid_json(self, cache):
        state = OctState(axes=(0.5,) * 6)
        cache.put(state, payload=[1, 2, 3])
        path = cache.persist("sess2")
        data = json.loads(Path(path).read_text())
        assert data["session_id"] == "sess2"
        assert len(data["entries"]) == 1

    def test_restore_roundtrip(self, cache):
        state = OctState(axes=(0.5,) * 6, source_repo="r")
        key = cache.put(state, payload="hello")
        cache.persist("sess3")

        # New cache, same persist dir
        cache2 = SessionCache(persist_dir=str(cache.persist_dir))
        loaded = cache2.restore("sess3")
        assert loaded == 1
        assert cache2.get(key) == "hello"

    def test_restore_skips_stale(self, cache):
        state = OctState(axes=(0.5,) * 6)
        cache.put(state, payload="data")
        cache.persist("sess4")

        # Restore with drifted live state
        cache2 = SessionCache(persist_dir=str(cache.persist_dir))
        drifted = OctState(axes=(5.0,) * 6)  # way off
        loaded = cache2.restore("sess4", live_state=drifted)
        assert loaded == 0

    def test_restore_nonexistent(self, cache):
        loaded = cache.restore("does_not_exist")
        assert loaded == 0

    def test_persist_non_serializable_payload(self, cache):
        state = OctState(axes=(0,) * 6)
        cache.put(state, payload=object())  # not JSON-serializable
        path = cache.persist("sess5")
        data = json.loads(Path(path).read_text())
        # Should be stored as str()
        assert isinstance(list(data["entries"].values())[0]["payload"], str)


# ============================================================================
# SessionCache — diagnostics
# ============================================================================

class TestSessionCacheStatus:
    def test_status_empty(self):
        cache = SessionCache()
        s = cache.status()
        assert s["entries"] == 0
        assert s["oldest"] is None

    def test_status_with_entries(self):
        cache = SessionCache()
        cache.put(OctState(axes=(0,) * 6), payload="a")
        cache.put(OctState(axes=(1,) * 6), payload="b")
        s = cache.status()
        assert s["entries"] == 2
        assert s["oldest"] is not None

    def test_clear(self):
        cache = SessionCache()
        cache.put(OctState(axes=(0,) * 6), payload="a")
        cache.clear()
        assert len(cache.store) == 0
