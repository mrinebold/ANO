"""
Profile Loader

Single toggle point for all profile-dependent behavior. Core code reads from
ProfileRegistry, never checks which profile is active.
"""

from __future__ import annotations

import importlib
import os
from dataclasses import dataclass, field
from typing import Any, Callable

from ano_core.logging import get_agent_logger

logger = get_agent_logger(__name__)


@dataclass
class PolicyPreset:
    """
    A named policy configuration preset.

    Defines organization types, regulatory contexts, and policy configuration
    that can be applied to agent execution.
    """

    name: str
    description: str
    org_types: list[str] = field(default_factory=list)
    regulatory_contexts: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationHook:
    """
    An integration hook for extending ANO functionality.

    Allows profiles to register custom LLM providers, storage backends,
    notification systems, or communication channels.
    """

    name: str
    hook_type: str
    factory: Callable[..., Any]
    priority: int = 0


PROFILE_MODULES = {
    "minimal": "profiles.minimal",
    "msr": "plugins.msr",
}


class ProfileRegistry:
    """
    Central registry that profiles populate.

    Core code reads from here, never checks which profile is active.
    This provides a clean abstraction layer between profile configuration
    and runtime behavior.
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._agent_classes: dict[str, type] = {}
        self._config: dict[str, Any] = {}
        self._policy_presets: dict[str, PolicyPreset] = {}
        self._hooks: dict[str, list[IntegrationHook]] = {}
        self._features: set[str] = set()
        self._metadata: dict[str, Any] = {}

    # Agent class registry

    def register_agent_class(self, name: str, cls: type) -> None:
        """
        Register an agent class.

        Args:
            name: Agent name
            cls: Agent class
        """
        if name in self._agent_classes:
            logger.warning(
                f"Overwriting existing agent class registration for '{name}'"
            )
        self._agent_classes[name] = cls
        logger.debug(f"Registered agent class: {name}")

    def get_agent_class(self, name: str) -> type | None:
        """
        Get an agent class by name.

        Args:
            name: Agent name

        Returns:
            Agent class or None if not found
        """
        return self._agent_classes.get(name)

    def list_agent_classes(self) -> dict[str, type]:
        """Get all registered agent classes."""
        return self._agent_classes.copy()

    # Configuration

    def set_config_defaults(self, defaults: dict[str, Any]) -> None:
        """
        Set configuration defaults.

        Existing values are preserved; only missing keys are added.

        Args:
            defaults: Default configuration values
        """
        for key, value in defaults.items():
            if key not in self._config:
                self._config[key] = value
                logger.debug(f"Set config default: {key} = {value}")

    def get_config(self, key: str, fallback: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            fallback: Fallback value if key not found

        Returns:
            Configuration value or fallback
        """
        return self._config.get(key, fallback)

    def set_config(self, key: str, value: Any) -> None:
        """
        Set a configuration value (overrides existing).

        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
        logger.debug(f"Set config: {key} = {value}")

    # Policy presets

    def register_policy_preset(self, preset: PolicyPreset) -> None:
        """
        Register a policy preset.

        Args:
            preset: PolicyPreset to register
        """
        if preset.name in self._policy_presets:
            logger.warning(
                f"Overwriting existing policy preset: {preset.name}"
            )
        self._policy_presets[preset.name] = preset
        logger.debug(f"Registered policy preset: {preset.name}")

    def get_policy_preset(self, name: str) -> PolicyPreset | None:
        """
        Get a policy preset by name.

        Args:
            name: Preset name

        Returns:
            PolicyPreset or None if not found
        """
        return self._policy_presets.get(name)

    def list_policy_presets(self) -> dict[str, PolicyPreset]:
        """Get all registered policy presets."""
        return self._policy_presets.copy()

    # Integration hooks

    def register_hook(self, hook: IntegrationHook) -> None:
        """
        Register an integration hook.

        Args:
            hook: IntegrationHook to register
        """
        if hook.hook_type not in self._hooks:
            self._hooks[hook.hook_type] = []

        self._hooks[hook.hook_type].append(hook)
        # Sort by priority (higher priority first)
        self._hooks[hook.hook_type].sort(key=lambda h: h.priority, reverse=True)

        logger.debug(
            f"Registered hook: {hook.name} ({hook.hook_type}, priority={hook.priority})"
        )

    def get_hooks(self, hook_type: str) -> list[IntegrationHook]:
        """
        Get all hooks of a specific type, ordered by priority.

        Args:
            hook_type: Type of hook to retrieve

        Returns:
            List of IntegrationHooks (empty if none registered)
        """
        return self._hooks.get(hook_type, []).copy()

    # Feature flags

    def set_feature(self, name: str, enabled: bool = True) -> None:
        """
        Enable or disable a feature.

        Args:
            name: Feature name
            enabled: Whether the feature is enabled
        """
        if enabled:
            self._features.add(name)
            logger.debug(f"Enabled feature: {name}")
        else:
            self._features.discard(name)
            logger.debug(f"Disabled feature: {name}")

    def has_feature(self, name: str) -> bool:
        """
        Check if a feature is enabled.

        Args:
            name: Feature name

        Returns:
            True if feature is enabled
        """
        return name in self._features

    # Metadata

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set profile metadata.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self._metadata[key] = value
        logger.debug(f"Set metadata: {key} = {value}")

    def get_metadata(self, key: str, fallback: Any = None) -> Any:
        """
        Get profile metadata.

        Args:
            key: Metadata key
            fallback: Fallback value if key not found

        Returns:
            Metadata value or fallback
        """
        return self._metadata.get(key, fallback)

    # Summary

    def summary(self) -> dict[str, Any]:
        """
        Get a summary of the registry state.

        Returns:
            Dictionary with counts and profile info
        """
        return {
            "profile_name": self.get_metadata("profile_name", "unknown"),
            "profile_version": self.get_metadata("profile_version", "unknown"),
            "agent_classes": len(self._agent_classes),
            "policy_presets": len(self._policy_presets),
            "hooks": sum(len(hooks) for hooks in self._hooks.values()),
            "features_enabled": len(self._features),
            "config_keys": len(self._config),
        }


def load_profile(profile_name: str | None = None) -> ProfileRegistry:
    """
    Load a profile into a ProfileRegistry.

    Process:
    1. Always load minimal first as base layer
    2. If profile != minimal, layer requested profile on top
    3. If profile module not found, warn + continue with minimal
    4. Apply ANO_FEATURES environment variable overrides

    Args:
        profile_name: Name of profile to load (default: from ANO_PROFILE env var or "minimal")

    Returns:
        ProfileRegistry with profile configuration loaded
    """
    registry = ProfileRegistry()

    # Determine which profile to load
    if profile_name is None:
        profile_name = os.getenv("ANO_PROFILE", "minimal")

    logger.info(f"Loading profile: {profile_name}")

    # Always load minimal first as base
    try:
        minimal_module = importlib.import_module("profiles.minimal")
        if hasattr(minimal_module, "register"):
            minimal_module.register(registry)
            logger.info("Loaded minimal profile as base layer")
        else:
            logger.warning("profiles.minimal has no register() function")
    except ImportError as e:
        logger.error(f"Failed to load minimal profile: {e}")
        raise

    # If requesting a different profile, layer it on top
    if profile_name != "minimal":
        if profile_name not in PROFILE_MODULES:
            logger.warning(
                f"Unknown profile '{profile_name}', available profiles: "
                f"{', '.join(PROFILE_MODULES.keys())}. Continuing with minimal."
            )
        else:
            try:
                module_path = PROFILE_MODULES[profile_name]
                profile_module = importlib.import_module(module_path)
                if hasattr(profile_module, "register"):
                    profile_module.register(registry)
                    logger.info(f"Loaded {profile_name} profile")
                else:
                    logger.warning(f"{module_path} has no register() function")
            except ImportError as e:
                logger.warning(
                    f"Failed to load profile '{profile_name}': {e}. "
                    f"Continuing with minimal."
                )

    # Apply ANO_FEATURES environment variable overrides
    features_env = os.getenv("ANO_FEATURES", "")
    if features_env:
        for feature_spec in features_env.split(","):
            feature_spec = feature_spec.strip()
            if not feature_spec:
                continue

            if feature_spec.startswith("-"):
                # Disable feature
                feature_name = feature_spec[1:]
                registry.set_feature(feature_name, enabled=False)
                logger.info(f"Disabled feature via ANO_FEATURES: {feature_name}")
            else:
                # Enable feature
                feature_name = feature_spec.lstrip("+")
                registry.set_feature(feature_name, enabled=True)
                logger.info(f"Enabled feature via ANO_FEATURES: {feature_name}")

    # Log summary
    summary = registry.summary()
    logger.info(
        f"Profile loaded: {summary['profile_name']} v{summary['profile_version']} - "
        f"{summary['agent_classes']} agents, "
        f"{summary['policy_presets']} presets, "
        f"{summary['hooks']} hooks, "
        f"{summary['features_enabled']} features"
    )

    return registry
