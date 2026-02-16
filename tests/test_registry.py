"""Tests for registry module — AgentRegistry, CapabilityRegistry, discovery."""

from __future__ import annotations

import pytest

from ano_core.errors import RegistryError
from registry.agent_registry import (
    AgentMetadataEntry,
    AgentRegistry,
    register_agent,
)
from registry.capability_registry import CapabilityEntry, CapabilityRegistry


# --- AgentRegistry ---


class TestAgentRegistry:
    def test_register_and_get(self):
        registry = AgentRegistry()
        metadata = AgentMetadataEntry(
            name="test-agent",
            team="development",
            version="1.0.0",
            capabilities=["qa"],
        )

        class TestAgent:
            pass

        registry.register(TestAgent, metadata)
        assert registry.get("test-agent") is TestAgent
        assert registry.has("test-agent") is True

    def test_get_nonexistent_raises(self):
        registry = AgentRegistry()
        with pytest.raises(RegistryError):
            registry.get("nonexistent")

    def test_duplicate_registration_raises(self):
        registry = AgentRegistry()
        metadata = AgentMetadataEntry(
            name="dupe-agent",
            team="development",
            version="1.0.0",
            capabilities=[],
        )

        class Agent1:
            pass

        class Agent2:
            pass

        registry.register(Agent1, metadata)
        with pytest.raises(RegistryError):
            registry.register(Agent2, metadata)

    def test_get_metadata(self):
        registry = AgentRegistry()
        metadata = AgentMetadataEntry(
            name="meta-agent",
            team="executive",
            version="2.0.0",
            capabilities=["strategy", "planning"],
            description="Test agent",
        )

        class MetaAgent:
            pass

        registry.register(MetaAgent, metadata)
        result = registry.get_metadata("meta-agent")
        assert result.team == "executive"
        assert result.version == "2.0.0"
        assert len(result.capabilities) == 2

    def test_list_agents_all(self):
        registry = AgentRegistry()
        for i, team in enumerate(["dev", "dev", "exec"]):
            metadata = AgentMetadataEntry(
                name=f"agent-{i}",
                team=team,
                version="1.0.0",
                capabilities=["cap1"] if i == 0 else ["cap2"],
            )

            class Agent:
                pass

            registry.register(type(f"Agent{i}", (), {}), metadata)

        assert len(registry.list_agents()) == 3

    def test_list_agents_by_team(self):
        registry = AgentRegistry()
        for i, team in enumerate(["dev", "dev", "exec"]):
            metadata = AgentMetadataEntry(
                name=f"agent-{i}",
                team=team,
                version="1.0.0",
                capabilities=[],
            )
            registry.register(type(f"Agent{i}", (), {}), metadata)

        dev_agents = registry.list_agents(team="dev")
        assert len(dev_agents) == 2

    def test_list_agents_by_capability(self):
        registry = AgentRegistry()
        m1 = AgentMetadataEntry(name="a1", team="dev", version="1.0", capabilities=["qa", "test"])
        m2 = AgentMetadataEntry(name="a2", team="dev", version="1.0", capabilities=["security"])
        registry.register(type("A1", (), {}), m1)
        registry.register(type("A2", (), {}), m2)

        qa_agents = registry.list_agents(capability="qa")
        assert len(qa_agents) == 1
        assert qa_agents[0].name == "a1"

    def test_has_false_for_missing(self):
        registry = AgentRegistry()
        assert registry.has("nonexistent") is False

    def test_unregister(self):
        registry = AgentRegistry()
        metadata = AgentMetadataEntry(
            name="removable",
            team="dev",
            version="1.0.0",
            capabilities=[],
        )
        registry.register(type("R", (), {}), metadata)
        assert registry.has("removable") is True
        registry.unregister("removable")
        assert registry.has("removable") is False

    def test_unregister_nonexistent_raises(self):
        registry = AgentRegistry()
        with pytest.raises(RegistryError):
            registry.unregister("ghost")


class TestRegisterAgentDecorator:
    def test_decorator_sets_metadata(self):
        @register_agent(
            name="decorated-agent",
            team="development",
            version="1.0.0",
            capabilities=["testing"],
        )
        class DecoratedAgent:
            pass

        assert hasattr(DecoratedAgent, "_agent_metadata")
        assert DecoratedAgent._agent_metadata.name == "decorated-agent"
        assert DecoratedAgent._agent_metadata.team == "development"


# --- CapabilityRegistry ---


class TestCapabilityRegistry:
    def test_register_and_get_providers(self):
        registry = CapabilityRegistry()
        registry.register("qa", "quest-agent", "Quality assurance", "testing")
        providers = registry.get_providers("qa")
        assert "quest-agent" in providers

    def test_multiple_providers(self):
        registry = CapabilityRegistry()
        registry.register("security", "shield-agent")
        registry.register("security", "sentinel-agent")
        providers = registry.get_providers("security")
        assert len(providers) == 2

    def test_get_capabilities_for_agent(self):
        registry = CapabilityRegistry()
        registry.register("qa", "quest-agent")
        registry.register("testing", "quest-agent")
        caps = registry.get_capabilities("quest-agent")
        assert "qa" in caps
        assert "testing" in caps

    def test_get_providers_unknown(self):
        registry = CapabilityRegistry()
        assert registry.get_providers("nonexistent") == []

    def test_get_capabilities_unknown_agent(self):
        registry = CapabilityRegistry()
        assert registry.get_capabilities("nonexistent") == []

    def test_list_all(self):
        registry = CapabilityRegistry()
        registry.register("qa", "a1")
        registry.register("security", "a2")
        all_caps = registry.list_all()
        assert len(all_caps) == 2

    def test_get_entry(self):
        registry = CapabilityRegistry()
        registry.register("qa", "a1", "Quality assurance", "testing")
        entry = registry.get_entry("qa")
        assert entry is not None
        assert entry.description == "Quality assurance"
        assert entry.category == "testing"

    def test_get_entry_none(self):
        registry = CapabilityRegistry()
        assert registry.get_entry("ghost") is None

    def test_list_by_category(self):
        registry = CapabilityRegistry()
        registry.register("qa", "a1", category="testing")
        registry.register("lint", "a2", category="testing")
        registry.register("deploy", "a3", category="ops")
        testing_caps = registry.list_by_category("testing")
        assert len(testing_caps) == 2

    def test_unregister_capability(self):
        registry = CapabilityRegistry()
        registry.register("qa", "a1")
        registry.unregister_capability("qa")
        assert registry.get_providers("qa") == []
        assert registry.get_entry("qa") is None

    def test_unregister_agent(self):
        registry = CapabilityRegistry()
        registry.register("qa", "a1")
        registry.register("security", "a1")
        registry.unregister_agent("a1")
        assert registry.get_capabilities("a1") == []
        # Capability still exists but without provider
        assert registry.get_providers("qa") == []

    def test_no_duplicate_providers(self):
        registry = CapabilityRegistry()
        registry.register("qa", "a1")
        registry.register("qa", "a1")  # duplicate
        assert len(registry.get_providers("qa")) == 1
