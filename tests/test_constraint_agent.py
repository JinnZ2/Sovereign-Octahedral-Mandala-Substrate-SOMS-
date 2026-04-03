"""Tests for ConstraintAgent lifecycle — bloom, explore, compress, serialize."""

import pytest
from fractions import Fraction

from src.constraint_agent import (
    ConstraintAgent, AgentState, ResourceBudget, GeometricMap,
)


class TestAgentState:
    def test_all_states(self):
        states = [s.value for s in AgentState]
        assert "compressed" in states
        assert "expanding" in states
        assert "exploring" in states
        assert "contracting" in states


class TestResourceBudget:
    def test_default_not_depleted(self):
        budget = ResourceBudget()
        assert budget.is_depleted()  # zero compute = depleted

    def test_funded_not_depleted(self):
        budget = ResourceBudget(compute=100, energy=Fraction(1, 1))
        assert not budget.is_depleted()

    def test_zero_energy_depleted(self):
        budget = ResourceBudget(compute=100, energy=Fraction(0, 1))
        assert budget.is_depleted()


class TestGeometricMap:
    def test_record_resonance(self):
        gm = GeometricMap()
        gm.record_resonance("SHAPE.OCTA", 0.85)
        assert "SHAPE.OCTA" in gm.resonances
        assert gm.resonances["SHAPE.OCTA"] == Fraction(0.85).limit_denominator(10000)

    def test_record_relationship(self):
        gm = GeometricMap()
        gm.record_relationship("A", "B")
        gm.record_relationship("A", "C")
        gm.record_relationship("A", "B")  # duplicate
        assert gm.relationships["A"] == ["B", "C"]

    def test_record_energy_flow(self):
        gm = GeometricMap()
        gm.record_energy_flow("A", "B", Fraction(1, 10))
        assert ("A", "B") in gm.energy_flows


class TestConstraintAgentLifecycle:
    def test_initial_state(self):
        agent = ConstraintAgent(seed_id="SHAPE.OCTA")
        assert agent.state == AgentState.COMPRESSED
        assert agent.seed_id == "SHAPE.OCTA"

    def test_should_expand_with_resources(self):
        agent = ConstraintAgent(seed_id="SHAPE.OCTA")
        agent.set_resource_budget(compute=100, energy=1.0)
        assert agent.should_expand()

    def test_should_not_expand_without_resources(self):
        agent = ConstraintAgent(seed_id="SHAPE.OCTA")
        assert not agent.should_expand()

    def test_bloom_transitions_to_exploring(self):
        agent = ConstraintAgent(seed_id="SHAPE.OCTA")
        agent.set_resource_budget(compute=1000, energy=1.0)
        agent.bloom(depth=1)
        assert agent.state == AgentState.EXPLORING

    def test_bloom_discovers_entities(self):
        agent = ConstraintAgent(seed_id="SHAPE.OCTA")
        agent.set_resource_budget(compute=1000, energy=1.0)
        discovered = agent.bloom(depth=1)
        assert isinstance(discovered, list)
        assert len(discovered) > 0

    def test_explore_records_flows(self):
        agent = ConstraintAgent(seed_id="SHAPE.OCTA")
        agent.set_resource_budget(compute=1000, energy=1.0)
        agent.bloom(depth=1)
        summary = agent.explore()
        assert "energy_flows_recorded" in summary

    def test_compress_returns_to_compressed(self):
        agent = ConstraintAgent(seed_id="SHAPE.OCTA")
        agent.set_resource_budget(compute=1000, energy=1.0)
        agent.bloom(depth=1)
        agent.compress()
        assert agent.state == AgentState.COMPRESSED
        assert agent.compression_ratio == Fraction(1, 1)

    def test_full_lifecycle(self):
        """COMPRESSED -> bloom -> EXPLORING -> compress -> COMPRESSED -> re-bloom."""
        agent = ConstraintAgent(seed_id="SHAPE.OCTA")
        agent.set_resource_budget(compute=1000, energy=1.0)

        # First cycle
        discovered = agent.bloom(depth=2)
        assert agent.state == AgentState.EXPLORING
        agent.explore()
        agent.compress()
        assert agent.state == AgentState.COMPRESSED

        # Re-expand with prior map
        agent.set_resource_budget(compute=500, energy=0.5)
        rediscovered = agent.bloom(depth=1, seed_map=agent.map)
        assert agent.state == AgentState.EXPLORING


class TestSerializeDeserialize:
    def test_round_trip(self):
        agent = ConstraintAgent(
            seed_id="SHAPE.OCTA",
            home_families=["air", "structure"]
        )
        agent.set_resource_budget(compute=1000, energy=1.0)
        agent.bloom(depth=1)
        agent.explore()

        data = agent.serialize()
        restored = ConstraintAgent.deserialize(data)

        assert restored.seed_id == agent.seed_id
        assert restored.home_families == agent.home_families
        assert restored.state == agent.state
        assert len(restored.map.resonances) == len(agent.map.resonances)


class TestCorruptionDetection:
    def test_no_corruption_for_valid_ref(self):
        agent = ConstraintAgent(seed_id="SHAPE.OCTA")
        agent.set_resource_budget(compute=1000, energy=1.0)
        agent.bloom(depth=1)
        # CUBE is dual to OCTA, should not be corrupt
        assert not agent.detect_corruption("Align SHAPE.CUBE")

    def test_no_entity_no_corruption(self):
        agent = ConstraintAgent(seed_id="SHAPE.OCTA")
        assert not agent.detect_corruption("some random text")


class TestExpanderRules:
    def test_returns_list(self):
        agent = ConstraintAgent(seed_id="SHAPE.OCTA")
        agent.set_resource_budget(compute=1000, energy=1.0)
        agent.bloom(depth=2)
        result = agent.check_expander_rules()
        assert isinstance(result, list)
