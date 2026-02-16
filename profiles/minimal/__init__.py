"""
Minimal Profile

Base profile with permissive defaults and core agents.
This is always loaded first, and other profiles layer on top.
"""

from typing import TYPE_CHECKING

from ano_core.logging import get_agent_logger

if TYPE_CHECKING:
    from profiles.loader import ProfileRegistry, PolicyPreset

logger = get_agent_logger(__name__)


def register(registry: "ProfileRegistry") -> None:
    """
    Register minimal profile: core agents + permissive defaults.

    Args:
        registry: ProfileRegistry to populate
    """
    from profiles.loader import PolicyPreset

    logger.info("Registering minimal profile")

    # Set configuration defaults
    registry.set_config_defaults({
        "max_concurrent_agents": 3,
        "default_llm_provider": "anthropic",
        "default_llm_model": "claude-sonnet-4-5-20250929",
        "agent_timeout_seconds": 300,
        "log_agent_calls": True,
        "policy_enforcement": False,
        "pipeline_retry_attempts": 1,
        "enable_memory_persistence": True,
        "memory_base_dir": "/tmp/ano-memory",
    })

    # Register base policy preset (permissive)
    registry.register_policy_preset(
        PolicyPreset(
            name="base",
            description="Permissive baseline — no specific policy constraints",
        )
    )

    # Set profile metadata
    registry.set_metadata("profile_name", "minimal")
    registry.set_metadata("profile_version", "1.0.0")
    registry.set_metadata("profile_description", "Base profile with permissive defaults")

    # Agent classes will be registered when agent modules are implemented
    # For now, this profile just sets up the configuration foundation
    #
    # Future agent registrations would look like:
    # from agents.ceo.agent import CEOAdvisorAgent
    # registry.register_agent_class("ceo-advisor", CEOAdvisorAgent)

    logger.info("Minimal profile registration complete")
