"""
ANO Core Runtime Layer

Provides the foundational types, settings, error handling, and utilities
for the Adaptive Network of Orchestrators framework.
"""

from ano_core.settings import AnoSettings, load_settings, settings
from ano_core.types import (
    AgentContext,
    AgentInput,
    AgentMetadata,
    AgentOutput,
    OrgProfile,
    PolicyReport,
    PolicyViolation,
)
from ano_core.errors import (
    ANOError,
    AgentExecutionError,
    ChannelError,
    ConfigurationError,
    LLMBackendError,
    PolicyViolationError,
    RegistryError,
)
from ano_core.environment import (
    EnvironmentTier,
    TierRestrictions,
    detect_environment,
    get_tier_restrictions,
)
from ano_core.logging import get_agent_logger, setup_logging

__version__ = "0.1.0"

__all__ = [
    # Settings
    "AnoSettings",
    "load_settings",
    "settings",
    # Types
    "AgentContext",
    "AgentInput",
    "AgentMetadata",
    "AgentOutput",
    "OrgProfile",
    "PolicyReport",
    "PolicyViolation",
    # Errors
    "ANOError",
    "AgentExecutionError",
    "ChannelError",
    "ConfigurationError",
    "LLMBackendError",
    "PolicyViolationError",
    "RegistryError",
    # Environment
    "EnvironmentTier",
    "TierRestrictions",
    "detect_environment",
    "get_tier_restrictions",
    # Logging
    "get_agent_logger",
    "setup_logging",
]
