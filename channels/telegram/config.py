"""
Telegram Configuration

Configuration dataclass for Telegram bot settings.
"""

import os
from dataclasses import dataclass


@dataclass
class TelegramConfig:
    """Configuration for Telegram bot."""

    bot_token: str
    webhook_secret: str = ""
    webhook_url: str = ""
    rate_limit_per_minute: int = 10
    max_message_length: int = 4096
    parse_mode: str = "Markdown"

    @classmethod
    def from_env(cls) -> "TelegramConfig":
        """
        Load configuration from environment variables.

        Expected environment variables:
            TELEGRAM_BOT_TOKEN: Required - Telegram bot API token
            TELEGRAM_WEBHOOK_SECRET: Optional - Secret token for webhook validation
            TELEGRAM_WEBHOOK_URL: Optional - URL where webhook is hosted
            TELEGRAM_RATE_LIMIT: Optional - Max messages per minute (default: 10)
            TELEGRAM_MAX_MESSAGE_LENGTH: Optional - Max message length (default: 4096)
            TELEGRAM_PARSE_MODE: Optional - Default parse mode (default: Markdown)

        Returns:
            TelegramConfig instance

        Raises:
            ValueError: If TELEGRAM_BOT_TOKEN is not set
        """
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        return cls(
            bot_token=bot_token,
            webhook_secret=os.getenv("TELEGRAM_WEBHOOK_SECRET", ""),
            webhook_url=os.getenv("TELEGRAM_WEBHOOK_URL", ""),
            rate_limit_per_minute=int(os.getenv("TELEGRAM_RATE_LIMIT", "10")),
            max_message_length=int(os.getenv("TELEGRAM_MAX_MESSAGE_LENGTH", "4096")),
            parse_mode=os.getenv("TELEGRAM_PARSE_MODE", "Markdown"),
        )
