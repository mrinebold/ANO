"""
ANO Environment Tier Detection and Restrictions

Provides environment detection (development, test, production) and
tier-specific operational restrictions for safe multi-tier deployments.
"""

from dataclasses import dataclass
from enum import Enum


class EnvironmentTier(str, Enum):
    """
    Deployment environment tiers.

    Maps to the three-tier system used across ANO deployments:
    - DEVELOPMENT: Local development, full access, rapid iteration
    - TEST: Validation environment, approval-gated destructive operations
    - PRODUCTION: Deployment-only, heavily restricted operations
    """

    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


def detect_environment() -> EnvironmentTier:
    """
    Detect the current environment tier from ANO_ENV setting.

    Returns:
        EnvironmentTier enum value

    Raises:
        ValueError: If ANO_ENV contains an invalid tier name
    """
    from ano_core.settings import settings

    env = settings.ANO_ENV.lower()

    try:
        return EnvironmentTier(env)
    except ValueError:
        # Default to development for unknown values
        return EnvironmentTier.DEVELOPMENT


@dataclass(frozen=True)
class TierRestrictions:
    """
    Operational restrictions for an environment tier.

    Defines which operations are allowed, blocked, and whether approval
    is required for sensitive actions.
    """

    allowed_operations: list[str]
    blocked_operations: list[str]
    requires_approval: bool
    max_concurrent_agents: int


def get_tier_restrictions(tier: EnvironmentTier) -> TierRestrictions:
    """
    Get operational restrictions for a given environment tier.

    Args:
        tier: The environment tier to get restrictions for

    Returns:
        TierRestrictions with tier-appropriate limits and controls
    """
    if tier == EnvironmentTier.DEVELOPMENT:
        return TierRestrictions(
            allowed_operations=[
                "agent_execute",
                "policy_attach",
                "policy_detach",
                "pipeline_run",
                "database_read",
                "database_write",
                "database_delete",
                "llm_call",
                "file_read",
                "file_write",
                "external_api_call",
            ],
            blocked_operations=[],
            requires_approval=False,
            max_concurrent_agents=10,
        )

    elif tier == EnvironmentTier.TEST:
        return TierRestrictions(
            allowed_operations=[
                "agent_execute",
                "policy_attach",
                "pipeline_run",
                "database_read",
                "database_write",
                "llm_call",
                "file_read",
                "file_write",
                "external_api_call",
            ],
            blocked_operations=[
                "database_delete",  # Prevent accidental data loss in test
            ],
            requires_approval=True,  # Approval required for write operations
            max_concurrent_agents=5,
        )

    else:  # PRODUCTION
        return TierRestrictions(
            allowed_operations=[
                "agent_execute",
                "policy_attach",
                "pipeline_run",
                "database_read",
                "llm_call",
                "file_read",
            ],
            blocked_operations=[
                "database_write",
                "database_delete",
                "file_write",
                "policy_detach",  # Don't allow bypassing policies in prod
            ],
            requires_approval=True,
            max_concurrent_agents=3,  # Limited concurrency in production
        )
