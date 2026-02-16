"""
ANO Settings and Configuration

Provides centralized configuration management with environment variable support,
TOML overlay, and feature flag detection.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AnoProfile(str, Enum):
    """Available ANO deployment profiles."""

    MINIMAL = "minimal"
    MSR = "msr"


class AnoSettings(BaseSettings):
    """
    ANO framework settings.

    Loads from environment variables and optional TOML configuration file.
    Environment variables take precedence over TOML values.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Profile and features
    ANO_PROFILE: AnoProfile = Field(
        default=AnoProfile.MINIMAL,
        description="Deployment profile (minimal | msr)",
    )
    ANO_FEATURES: str = Field(
        default="",
        description="Comma-separated feature flags",
    )
    ANO_ENV: str = Field(
        default="development",
        description="Environment tier (development | test | production)",
    )

    # Debug and logging
    ANO_DEBUG: bool = Field(default=False, description="Enable debug mode")
    ANO_LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG | INFO | WARNING | ERROR | CRITICAL)",
    )

    # LLM configuration
    ANTHROPIC_API_KEY: Optional[str] = Field(
        default=None,
        description="Anthropic API key for Claude models",
    )
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        description="OpenAI API key for GPT models",
    )
    DEFAULT_LLM_PROVIDER: str = Field(
        default="anthropic",
        description="Default LLM provider (anthropic | openai)",
    )
    DEFAULT_LLM_MODEL: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Default LLM model identifier",
    )

    # Optional TOML configuration file
    ANO_CONFIG_FILE: Optional[str] = Field(
        default=None,
        description="Path to TOML configuration file",
    )

    @property
    def features(self) -> frozenset[str]:
        """Parse ANO_FEATURES into a frozenset of feature flags."""
        if not self.ANO_FEATURES:
            return frozenset()
        return frozenset(
            flag.strip() for flag in self.ANO_FEATURES.split(",") if flag.strip()
        )

    def has_feature(self, flag: str) -> bool:
        """Check if a feature flag is enabled."""
        return flag in self.features


def load_settings() -> AnoSettings:
    """
    Load ANO settings from environment and optional TOML file.

    TOML configuration provides defaults that can be overridden by
    environment variables.

    Returns:
        AnoSettings instance with merged configuration
    """
    base_settings = AnoSettings()

    # If TOML config file specified, overlay values
    if base_settings.ANO_CONFIG_FILE:
        config_path = Path(base_settings.ANO_CONFIG_FILE)
        if config_path.exists():
            try:
                import tomli

                with open(config_path, "rb") as f:
                    toml_data = tomli.load(f)

                # Merge TOML data with environment (env vars take precedence)
                # Only update fields that aren't already set from environment
                for key, value in toml_data.items():
                    if key.upper() not in os.environ:
                        setattr(base_settings, key.upper(), value)
            except ImportError:
                # tomli not installed, skip TOML loading
                pass
            except Exception as e:
                # Log warning but continue with env-only settings
                import logging

                logging.warning(f"Failed to load TOML config: {e}")

    return base_settings


# Module-level singleton
settings = load_settings()
