"""
Telegram Authentication and Authorization

Tier-based access control for Telegram bot users.
"""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class TierConfig:
    """Configuration for a single access tier."""

    name: str
    level: int  # higher = more access
    features: List[str] = field(default_factory=list)


class TelegramAuth:
    """Tier-based access control for Telegram bot users."""

    def __init__(self, tiers: Optional[List[TierConfig]] = None):
        """
        Initialize authentication handler.

        Args:
            tiers: List of tier configurations. If None, uses default tiers.
        """
        self.tiers = tiers or self.default_tiers()

        # Build tier lookup maps
        self._tier_by_name: dict[str, TierConfig] = {
            tier.name: tier for tier in self.tiers
        }
        self._tier_levels: dict[str, int] = {
            tier.name: tier.level for tier in self.tiers
        }

    def check_access(self, user_tier: str, required_feature: str) -> bool:
        """
        Check if a user tier has access to a feature.

        Args:
            user_tier: User's tier name
            required_feature: Feature name or required tier name

        Returns:
            True if user has access, False otherwise
        """
        # Get user's tier config
        tier_config = self._tier_by_name.get(user_tier)
        if not tier_config:
            return False

        # Check if required_feature is a feature name
        if required_feature in tier_config.features:
            return True

        # Check if required_feature is a tier name (hierarchical check)
        required_level = self._tier_levels.get(required_feature, float('inf'))
        user_level = tier_config.level

        return user_level >= required_level

    def get_default_tier(self) -> str:
        """
        Get the default tier name (lowest level).

        Returns:
            Default tier name
        """
        if not self.tiers:
            return "free"

        default = min(self.tiers, key=lambda t: t.level)
        return default.name

    @staticmethod
    def default_tiers() -> List[TierConfig]:
        """
        Get default tier configuration.

        Returns:
            List of default tiers (free, basic, premium)
        """
        return [
            TierConfig(
                "free",
                0,
                ["help", "start", "info"]
            ),
            TierConfig(
                "basic",
                1,
                ["help", "start", "info", "query", "analyze"]
            ),
            TierConfig(
                "premium",
                2,
                ["help", "start", "info", "query", "analyze", "export", "custom"]
            ),
        ]
