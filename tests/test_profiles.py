"""Tests for profiles module — ProfileRegistry, load_profile, feature flags."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from profiles.loader import (
    IntegrationHook,
    PolicyPreset,
    ProfileRegistry,
    load_profile,
)


class TestPolicyPreset:
    def test_create(self):
        preset = PolicyPreset(
            name="municipal",
            description="Municipal government",
            org_types=["municipal"],
            regulatory_contexts=["public_records", "procurement"],
        )
        assert preset.name == "municipal"
        assert len(preset.org_types) == 1

    def test_defaults(self):
        preset = PolicyPreset(name="base", description="Base")
        assert preset.org_types == []
        assert preset.config == {}


class TestIntegrationHook:
    def test_create(self):
        hook = IntegrationHook(
            name="test-hook",
            hook_type="notification",
            factory=lambda: None,
            priority=10,
        )
        assert hook.name == "test-hook"
        assert hook.priority == 10


class TestProfileRegistry:
    def test_agent_class_registration(self):
        registry = ProfileRegistry()

        class MyAgent:
            pass

        registry.register_agent_class("my-agent", MyAgent)
        assert registry.get_agent_class("my-agent") is MyAgent

    def test_agent_class_not_found(self):
        registry = ProfileRegistry()
        assert registry.get_agent_class("nonexistent") is None

    def test_list_agent_classes(self):
        registry = ProfileRegistry()
        registry.register_agent_class("a1", type("A1", (), {}))
        registry.register_agent_class("a2", type("A2", (), {}))
        classes = registry.list_agent_classes()
        assert len(classes) == 2

    def test_config_defaults(self):
        registry = ProfileRegistry()
        registry.set_config_defaults({"timeout": 300, "max_agents": 3})
        assert registry.get_config("timeout") == 300
        assert registry.get_config("max_agents") == 3

    def test_config_defaults_dont_overwrite(self):
        registry = ProfileRegistry()
        registry.set_config("timeout", 600)
        registry.set_config_defaults({"timeout": 300})
        assert registry.get_config("timeout") == 600  # Not overwritten

    def test_config_fallback(self):
        registry = ProfileRegistry()
        assert registry.get_config("missing", "default") == "default"

    def test_policy_preset_registration(self):
        registry = ProfileRegistry()
        preset = PolicyPreset(name="test", description="Test preset")
        registry.register_policy_preset(preset)
        result = registry.get_policy_preset("test")
        assert result is not None
        assert result.description == "Test preset"

    def test_policy_preset_not_found(self):
        registry = ProfileRegistry()
        assert registry.get_policy_preset("ghost") is None

    def test_list_policy_presets(self):
        registry = ProfileRegistry()
        for name in ["base", "municipal", "enterprise"]:
            registry.register_policy_preset(
                PolicyPreset(name=name, description=name)
            )
        presets = registry.list_policy_presets()
        assert len(presets) == 3

    def test_hook_registration(self):
        registry = ProfileRegistry()
        hook = IntegrationHook(
            name="audit",
            hook_type="notification",
            factory=lambda: None,
            priority=5,
        )
        registry.register_hook(hook)
        hooks = registry.get_hooks("notification")
        assert len(hooks) == 1
        assert hooks[0].name == "audit"

    def test_hooks_sorted_by_priority(self):
        registry = ProfileRegistry()
        for name, priority in [("low", 1), ("high", 10), ("mid", 5)]:
            registry.register_hook(IntegrationHook(
                name=name,
                hook_type="notification",
                factory=lambda: None,
                priority=priority,
            ))
        hooks = registry.get_hooks("notification")
        assert hooks[0].name == "high"
        assert hooks[1].name == "mid"
        assert hooks[2].name == "low"

    def test_hooks_empty_type(self):
        registry = ProfileRegistry()
        assert registry.get_hooks("nonexistent") == []

    def test_feature_flags(self):
        registry = ProfileRegistry()
        registry.set_feature("audit_trail", enabled=True)
        assert registry.has_feature("audit_trail") is True
        assert registry.has_feature("nonexistent") is False

    def test_disable_feature(self):
        registry = ProfileRegistry()
        registry.set_feature("audit_trail", enabled=True)
        registry.set_feature("audit_trail", enabled=False)
        assert registry.has_feature("audit_trail") is False

    def test_metadata(self):
        registry = ProfileRegistry()
        registry.set_metadata("profile_name", "minimal")
        assert registry.get_metadata("profile_name") == "minimal"
        assert registry.get_metadata("missing", "fallback") == "fallback"

    def test_summary(self):
        registry = ProfileRegistry()
        registry.set_metadata("profile_name", "test")
        registry.set_metadata("profile_version", "1.0")
        registry.register_agent_class("a1", type("A", (), {}))
        registry.register_policy_preset(PolicyPreset(name="p1", description="x"))
        registry.set_feature("f1")
        summary = registry.summary()
        assert summary["profile_name"] == "test"
        assert summary["agent_classes"] == 1
        assert summary["policy_presets"] == 1
        assert summary["features_enabled"] == 1


class TestLoadProfile:
    def test_load_minimal(self):
        registry = load_profile("minimal")
        assert registry.get_metadata("profile_name") is not None

    def test_load_unknown_falls_back(self):
        """Unknown profile should fall back to minimal with warning."""
        registry = load_profile("nonexistent_profile")
        # Should still return a valid registry (minimal base)
        assert isinstance(registry, ProfileRegistry)

    @patch.dict(os.environ, {"ANO_FEATURES": "+custom_feature,-audit_trail"})
    def test_feature_overrides_from_env(self):
        registry = load_profile("minimal")
        assert registry.has_feature("custom_feature") is True
        assert registry.has_feature("audit_trail") is False

    def test_default_profile_from_env(self):
        with patch.dict(os.environ, {"ANO_PROFILE": "minimal"}):
            registry = load_profile()
            assert isinstance(registry, ProfileRegistry)
